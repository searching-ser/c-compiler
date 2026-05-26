# Reporte del compilador C-lite

## 1. Proposito del proyecto

El proyecto implementa un compilador pequeno para un subconjunto de C-lite usando
Python. La solucion sigue la estructura vista en clase:

1. Analisis lexico con PLY.
2. Analisis sintactico con PLY/Yacc.
3. Construccion de un arbol de sintaxis abstracta (AST).
4. Recorrido del AST con el patron visitor.
5. Generacion de codigo intermedio LLVM IR con `llvmlite`.

El objetivo no es compilar todo el lenguaje C, sino cubrir la gramatica base de
C-lite y las extensiones pedidas en la actividad: funciones, llamadas,
recursion, `printf`, estructuras de control y conversiones simples de tipo.

Los archivos principales son:

- `analisis.py`: contiene el lexer, parser y generador de LLVM IR.
- `arbol.py`: define los nodos del AST.
- `runtime.py`: contiene funciones auxiliares para crear un motor JIT de LLVM.
- `hello.py`: ejemplo independiente de llvmlite y ejecucion JIT.
- `examples/`: programas de prueba.

## 2. Flujo general del compilador

El flujo completo del compilador es:

```text
Codigo fuente C-lite
        |
        v
Lexer de PLY
        |
        v
Tokens
        |
        v
Parser de PLY
        |
        v
AST
        |
        v
IRGenerator
        |
        v
LLVM IR
```

La funcion principal para usar el compilador es `compile_source` en
`analisis.py`. Esa funcion recibe el codigo fuente como texto, lo manda al
parser, obtiene el AST y despues lo pasa al visitor `IRGenerator`.

```python
def compile_source(source: str) -> str:
    root = parse(source)
    irgen = IRGenerator()
    root.accept(irgen)
    return str(irgen.module)
```

Cuando se ejecuta:

```bash
python analisis.py examples/factorial.c
```

el programa lee el archivo, genera el modulo LLVM y lo imprime en pantalla.

## 3. Analisis lexico

El analizador lexico esta en `analisis.py` y usa PLY Lex. Su trabajo es separar
el codigo fuente en tokens. Por ejemplo, para esta linea:

```c
result = factorial(5);
```

el lexer reconoce tokens como:

```text
ID, '=', ID, '(', INTLIT, ')', ';'
```

### 3.1 Palabras reservadas

Las palabras reservadas se guardan en el diccionario `reserved`. Esto permite
distinguir entre identificadores normales y palabras del lenguaje:

```python
reserved = {
    "int": "INT",
    "bool": "BOOL",
    "float": "FLOAT",
    "char": "CHAR",
    "void": "VOID",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "do": "DO",
    "switch": "SWITCH",
    "case": "CASE",
    "default": "DEFAULT",
    "break": "BREAK",
    "continue": "CONTINUE",
    "return": "RETURN",
    "true": "TRUE",
    "false": "FALSE",
}
```

La regla `t_ID` primero reconoce una palabra con forma de identificador y luego
consulta si esa palabra esta en `reserved`.

```python
def t_ID(t):
    r"[a-zA-Z_][a-zA-Z_0-9]*"
    t.type = reserved.get(t.value, "ID")
    return t
```

### 3.2 Literales

El lexer reconoce:

- Enteros: `10`, `123`.
- Flotantes: `1.0`, `.5`, `3.14`.
- Caracteres: `'a'`, `'\n'`.
- Cadenas: `"hola %d\n"`.
- Booleanos: `true`, `false`.

Las cadenas son necesarias para soportar llamadas a `printf`.

### 3.3 Comentarios

Se ignoran comentarios de linea y de bloque:

```c
// comentario de linea
/* comentario de bloque */
```

Esto permite probar programas mas naturales sin que el parser reciba tokens
innecesarios.

## 4. Analisis sintactico

El parser esta implementado con PLY Yacc. Las reglas `p_...` construyen nodos
del AST en vez de solo validar que el codigo sea correcto.

## 4.1 Estructura de programa

La regla principal es:

```python
def p_program(p):
    "program : external_list"
    p[0] = Program(p[1])
```

El programa se modela como una lista de elementos externos. Cada elemento puede
ser:

- Una funcion.
- Una declaracion global.

```python
def p_external(p):
    """
    external : function_definition
             | global_declaration
    """
    p[0] = p[1]
```

La gramatica de la imagen original parte de `int main()`, pero la extension de
funciones permite tener funciones antes de `main`. Por eso el programa completo
se representa como una lista de funciones y variables globales.

## 4.2 Funciones

Una funcion tiene:

- Tipo de retorno.
- Nombre.
- Lista de parametros.
- Bloque con declaraciones y statements.

La regla principal es:

```python
def p_function_definition(p):
    "function_definition : type ID '(' parameters_opt ')' compound_statement"
    block = p[6]
    p[0] = Function(p[2], p[1], p[4], block.declarations, block.statements)
```

Ejemplo:

```c
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}
```

se convierte en un nodo `Function` con nombre `factorial`, tipo de retorno
`int`, un parametro `n` y una lista de statements.

## 4.3 Declaraciones

Las declaraciones se construyen con:

```python
def p_declaration(p):
    "declaration : type declarator_list ';'"
```

Se soportan declaraciones simples:

```c
int x;
float result;
char c;
```

Tambien se soportan inicializaciones simples:

```c
int x = 10;
```

y arreglos:

```c
int a[3];
```

El soporte de arreglos es basico: el compilador puede reservar memoria para un
arreglo local y acceder a una posicion. No se implemento revision de rango en
tiempo de ejecucion.

## 4.4 Statements

La regla `p_statement` cubre las construcciones principales del lenguaje:

```python
statement : compound_statement
          | assignment ';'
          | call ';'
          | if_statement
          | while_statement
          | for_statement
          | do_while_statement
          | switch_statement
          | return_statement ';'
          | BREAK ';'
          | CONTINUE ';'
          | expression ';'
          | ';'
```

Esto cubre la gramatica base de C-lite y las estructuras adicionales pedidas en
la actividad.

## 4.5 Expresiones y precedencia

Las expresiones se organizan en niveles para respetar precedencia:

```text
Expression  -> Conjunction { || Conjunction }
Conjunction -> Equality { && Equality }
Equality    -> Relation [ == | != Relation ]
Relation    -> Addition [ < | > | <= | >= Addition ]
Addition    -> Term { + | - Term }
Term        -> Factor { * | / | % Factor }
Factor      -> UnaryOp Factor | Primary
Primary     -> Identifier | Literal | ( Expression ) | Call
```

Esto hace que:

```c
x = 2 + 3 * 4;
```

se interprete como:

```text
2 + (3 * 4)
```

y no como:

```text
(2 + 3) * 4
```

El parser construye nodos `BinaryOp` y `UnaryOp` para representar estas
operaciones.

## 5. Arbol de sintaxis abstracta

El AST esta en `arbol.py`. Cada clase representa una construccion del lenguaje.

Algunos nodos importantes son:

- `Program`: programa completo.
- `Function`: definicion de una funcion.
- `Parameter`: parametro de una funcion.
- `Declaration`: declaracion de variable.
- `Block`: bloque `{ ... }`.
- `Assignment`: asignacion.
- `IfStatement`: `if` y `else`.
- `WhileStatement`: ciclo `while`.
- `ForStatement`: ciclo `for`.
- `DoWhileStatement`: ciclo `do/while`.
- `SwitchStatement`: `switch`.
- `CaseStatement`: `case`.
- `DefaultStatement`: `default`.
- `BreakStatement`: `break`.
- `ContinueStatement`: `continue`.
- `ReturnStatement`: `return`.
- `Call`: llamada a funcion.
- `Literal`: literal entero, flotante, booleano, caracter o cadena.
- `Variable`: referencia a una variable.
- `ArrayRef`: referencia a una posicion de arreglo.
- `BinaryOp`: operacion binaria.
- `UnaryOp`: operacion unaria.

Todos los nodos heredan de `ASTNode`, que contiene:

```python
def accept(self, visitor: Visitor) -> Any:
    method = "visit_" + self.__class__.__name__.lower()
    return getattr(visitor, method)(self)
```

Esto implementa el patron visitor. El nodo no sabe como generar codigo; solo
llama al metodo adecuado del visitor.

## 6. Analisis semantico basico

El proyecto no tiene una fase semantica separada en otro archivo. En esta
implementacion, varias validaciones semanticas se hacen durante la generacion de
LLVM IR.

## 6.1 Tabla de simbolos

`IRGenerator` mantiene una pila de tablas de simbolos:

```python
self.symbol_tables = []
```

Cuando entra a una funcion o bloque, crea un scope nuevo:

```python
def push_scope(self) -> None:
    self.symbol_tables.append({})
```

Cuando sale, lo elimina:

```python
def pop_scope(self) -> None:
    self.symbol_tables.pop()
```

Cada simbolo guarda:

- Nombre.
- Apuntador LLVM donde vive la variable.
- Tipo.

```python
def define_symbol(self, name: str, ptr, type_name: str) -> None:
    self.symbol_tables[-1][name] = (ptr, type_name)
```

Si una variable se usa sin haber sido declarada, `find_symbol` lanza un error:

```python
raise NameError(f"Variable '{name}' was not declared")
```

## 6.2 Registro de funciones

Antes de generar los cuerpos, el visitor registra todas las funciones:

```python
def visit_program(self, node: Program) -> None:
    for item in node.declarations:
        if isinstance(item, Function):
            self.declare_function(item)
```

Despues genera el cuerpo de cada funcion. Esto es importante para la recursion:
cuando `factorial` llama a `factorial`, la funcion ya existe en el modulo LLVM.

## 6.3 Conversion implicita de tipos

La funcion `cast` convierte valores cuando es necesario:

- `int` a `float`: usa `sitofp`.
- `float` a `int`: usa `fptosi`.
- Enteros de diferente tamano: usa `zext` o `trunc`.

Esto permite expresiones como:

```c
float x;
x = 2 + 3.5;
```

El compilador promueve los operandos a `double` cuando una operacion combina
enteros y flotantes.

## 7. Generacion de LLVM IR

La generacion de codigo esta en la clase `IRGenerator` dentro de `analisis.py`.
El resultado es un modulo LLVM:

```python
self.module = ir.Module(name="prog")
```

## 7.1 Tipos LLVM

Los tipos del lenguaje se traducen asi:

```text
int, bool    -> i32
char         -> i8
float        -> double
void         -> void
```

La funcion encargada es `llvm_type`.

## 7.2 Funciones

Para cada funcion del AST se crea una funcion LLVM:

```python
fnty = ir.FunctionType(ret_type, arg_types)
func = ir.Function(self.module, fnty, name=node.name)
```

Luego se crea el bloque inicial:

```python
entry = func.append_basic_block("entry")
self.builder = ir.IRBuilder(entry)
```

Los parametros se guardan en variables locales con `alloca` y `store`. Esto
permite tratarlos igual que cualquier variable local.

## 7.3 Variables y asignaciones

Las variables locales se reservan con:

```python
builder.alloca(...)
```

Una asignacion:

```c
x = 10;
```

se traduce a:

```llvm
store i32 10, i32* %x
```

Cuando se usa una variable en una expresion, se genera un `load`:

```python
return self.builder.load(ptr, name=node.name)
```

## 7.4 Expresiones aritmeticas y logicas

Las operaciones binarias se generan en `visit_binaryop`.

Para enteros se usan instrucciones como:

```llvm
add
sub
mul
sdiv
srem
icmp
```

Para flotantes se usan:

```llvm
fadd
fsub
fmul
fdiv
fcmp
```

Ejemplo:

```c
return n * factorial(n - 1);
```

se traduce conceptualmente a:

1. Cargar `n`.
2. Calcular `n - 1`.
3. Llamar a `factorial(n - 1)`.
4. Multiplicar `n` por el resultado.
5. Retornar el valor.

## 7.5 If/else

Un `if` se genera con tres bloques:

```text
if.then
if.else
if.end
```

Si no hay `else`, el bloque falso salta directamente a `if.end`.

Ejemplo:

```c
if (n <= 1) {
    return 1;
}
```

genera una comparacion y un salto condicional (`cbranch`).

## 7.6 While

Un `while` se genera con:

```text
while.cond
while.body
while.end
```

El flujo es:

1. Saltar a `while.cond`.
2. Evaluar la condicion.
3. Si es verdadera, entrar a `while.body`.
4. Al final del cuerpo, regresar a `while.cond`.
5. Si es falsa, salir a `while.end`.

## 7.7 For

Un `for` se genera con:

```text
for.cond
for.body
for.step
for.end
```

La estructura:

```c
for (j = 0; j < 3; j = j + 1) {
    sum = sum + j;
}
```

se traduce a:

1. Ejecutar inicializacion.
2. Evaluar condicion.
3. Ejecutar cuerpo.
4. Ejecutar actualizacion.
5. Regresar a la condicion.

## 7.8 Do/while

El `do/while` primero ejecuta el cuerpo y despues revisa la condicion. Por eso
se generan bloques:

```text
do.body
do.cond
do.end
```

## 7.9 Switch

El `switch` usa la instruccion `switch` de LLVM. Para cada `case` se crea un
bloque y se agrega con:

```python
switch.add_case(...)
```

El `break` salta al bloque final del `switch`.

## 7.10 Break y continue

Para manejar `break` y `continue`, el generador usa pilas:

```python
self.break_stack = []
self.continue_stack = []
```

Cuando entra a un ciclo o switch, guarda el bloque al que debe saltar. Cuando
sale, lo quita. Esto permite soportar ciclos anidados.

## 8. Soporte de printf

`printf` no se implementa en Python. Se declara como funcion externa en LLVM:

```python
def declare_printf(self):
    int_type = ir.IntType(32)
    char_ptr = ir.IntType(8).as_pointer()
    fnty = ir.FunctionType(int_type, [char_ptr], var_arg=True)
    return ir.Function(self.module, fnty, name="printf")
```

La firma generada es:

```llvm
declare i32 @printf(i8*, ...)
```

Cuando el parser encuentra:

```c
printf("factorial(5) = %d\n", result);
```

se crea un nodo `Call`. En `visit_call`, si el nombre es `printf`, se genera una
llamada directa a la funcion externa:

```python
if node.name == "printf":
    args = [arg.accept(self) for arg in node.args]
    return self.builder.call(self.printf, args)
```

Las cadenas se almacenan como constantes globales con `global_string`. Eso
permite pasar a `printf` un apuntador `i8*` al inicio de la cadena.

## 9. Recursion

La recursion funciona porque todas las firmas de funciones se declaran antes de
generar cualquier cuerpo. Por ejemplo:

```c
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}
```

Cuando se genera el cuerpo de `factorial`, la funcion `factorial` ya existe en
`self.functions`, por lo que `visit_call` puede encontrarla y emitir:

```llvm
call i32 @factorial(i32 ...)
```

Los ejemplos recursivos incluidos son:

- `examples/factorial.c`
- `examples/fibonacci.c`
- `examples/taylor.c`

## 10. Programas de prueba

Se incluyen cinco programas:

### 10.1 `examples/factorial.c`

Demuestra recursion directa:

```c
result = factorial(5);
```

### 10.2 `examples/fibonacci.c`

Demuestra recursion multiple:

```c
return fibonacci(n - 1) + fibonacci(n - 2);
```

### 10.3 `examples/taylor.c`

Demuestra recursion con flotantes y llamadas entre funciones:

```c
return exp_taylor(x, n - 1) + power(x, n) / factorialf(n);
```

### 10.4 `examples/control_flow.c`

Demuestra:

- `while`
- `for`
- `do/while`
- `printf`

### 10.5 `examples/switch_printf.c`

Demuestra:

- `switch`
- `case`
- `default`
- `break`
- `printf`

## 11. Relacion con la gramatica de C-lite

La implementacion cubre la gramatica base:

- `Program`
- `Declarations`
- `Declaration`
- `Type`
- `Statements`
- `Statement`
- `Block`
- `Assignment`
- `IfStatement`
- `WhileStatement`
- `Expression`
- `Conjunction`
- `Equality`
- `Relation`
- `Addition`
- `Term`
- `Factor`
- `Primary`
- `Literal`

Tambien cubre las extensiones pedidas en la actividad:

- Definicion y llamada a funciones.
- `return`.
- Recursion.
- `printf`.
- `for`.
- `do/while`.
- `switch`.
- Conversion implicita basica de tipos.

## 12. Limitaciones conocidas

Esta implementacion es un compilador educativo, no un compilador completo de C.
Las principales limitaciones son:

- No genera un ejecutable final por si solo; imprime LLVM IR.
- `hello.py` demuestra JIT, pero no es el runner del compilador completo.
- Los arreglos tienen soporte basico, pero no implementan revision de rango en
  tiempo de ejecucion.
- No hay una fase semantica separada; las validaciones basicas se hacen durante
  la generacion de IR.
- No se implementan punteros, structs, strings como tipo de variable, ni libreria
  estandar completa de C.
- `printf` se maneja como llamada externa especial.

Estas limitaciones son consistentes con el alcance del proyecto: construir un
subconjunto funcional de C-lite y generar codigo intermedio.

## 13. Como ejecutar

Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

Generar LLVM IR para un ejemplo:

```bash
python analisis.py examples/factorial.c
```

Ejecutar el demo JIT independiente:

```bash
python hello.py
```
