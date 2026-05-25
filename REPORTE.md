# Reporte del compilador C-lite

## Proposito

El proyecto implementa un compilador pequeno para un subconjunto de C/C-lite.
La implementacion sigue la estructura trabajada en clase: primero se construye
un analizador lexico, despues un analizador sintactico que produce un arbol de
sintaxis abstracta, y finalmente un visitor que recorre ese arbol para generar
codigo intermedio LLVM IR.

## Analisis lexico

El lexer esta en `analisis.py` y fue construido con PLY. Reconoce
identificadores, literales enteros, flotantes, caracteres, cadenas y palabras
reservadas como `int`, `if`, `while`, `for`, `switch`, `return`, `true` y
`false`.

Tambien reconoce operadores compuestos como:

```c
== != <= >= && ||
```

Los comentarios de linea `//` y de bloque `/* ... */` se ignoran durante el
analisis lexico.

## Analisis sintactico

La gramatica implementada extiende la gramatica base de C-lite. El programa se
modela como una lista de declaraciones globales y funciones. Cada funcion tiene
tipo de retorno, parametros, declaraciones locales y statements.

Las construcciones principales son:

- Declaraciones de variables.
- Bloques.
- Asignaciones.
- `if` / `else`.
- `while`.
- `for`.
- `do` / `while`.
- `switch` / `case` / `default`.
- `break`.
- `return`.
- Llamadas a funciones.
- Expresiones con precedencia aritmetica, relacional y logica.

La precedencia se organiza de forma parecida a la gramatica de C-lite:

```text
Expression  -> Conjunction { || Conjunction }
Conjunction -> Equality { && Equality }
Equality    -> Relation [ == | != Relation ]
Relation    -> Addition [ < | > | <= | >= Addition ]
Addition    -> Term { + | - Term }
Term        -> Factor { * | / | % Factor }
Factor      -> UnaryOp Factor | Primary
```

## AST

El AST se define en `arbol.py`. Los nodos principales son:

- `Program`
- `Function`
- `Declaration`
- `Block`
- `Assignment`
- `IfStatement`
- `WhileStatement`
- `ForStatement`
- `DoWhileStatement`
- `SwitchStatement`
- `ReturnStatement`
- `Call`
- `Literal`
- `Variable`
- `BinaryOp`
- `UnaryOp`

Cada nodo implementa `accept(visitor)`, lo que permite separar la estructura del
programa de las operaciones sobre esa estructura. Esta decision permite tener un
visitor para evaluar expresiones, otro para analisis semantico y otro para
generar codigo.

## Analisis semantico basico

El generador de IR mantiene una tabla de simbolos por scope. Cuando entra a una
funcion o bloque crea un scope nuevo, y cuando sale lo elimina.

Con esta tabla se valida que una variable usada haya sido declarada antes. Para
las funciones, primero se declara la firma de todas las funciones y despues se
generan sus cuerpos. Esto permite llamadas recursivas como:

```c
return n * factorial(n - 1);
```

Tambien se realiza conversion implicita basica entre enteros y flotantes cuando
una expresion combina ambos tipos o cuando una asignacion requiere ajustar el
tipo del valor al tipo de la variable destino.

## Generacion de LLVM IR

La clase `IRGenerator` en `analisis.py` recorre el AST y produce un modulo LLVM.
Cada funcion se convierte en una funcion LLVM con un bloque `entry`. Las
variables locales se reservan con `alloca`, las asignaciones usan `store` y las
lecturas usan `load`.

Las expresiones aritmeticas se traducen a instrucciones como:

```llvm
add
sub
mul
sdiv
srem
fadd
fmul
```

Las comparaciones usan `icmp` para enteros y `fcmp` para flotantes. Las
estructuras de control se generan con bloques basicos y saltos condicionales.

## Soporte para printf

`printf` se declara como funcion externa variadica:

```llvm
declare i32 @printf(i8*, ...)
```

Cuando aparece una cadena literal, el compilador crea una constante global para
almacenarla y pasa a `printf` un apuntador al primer caracter. Por ejemplo:

```c
printf("factorial(5) = %d\n", result);
```

se traduce a una llamada LLVM a `printf` con la cadena y el valor de `result`.

## Recursion

La recursion funciona porque el compilador registra todas las firmas de
funciones antes de generar sus cuerpos. Asi, cuando el cuerpo de `factorial`
llama a `factorial`, el simbolo de la funcion ya existe en el modulo LLVM.

Se incluyen tres ejemplos recursivos:

- `examples/factorial.c`
- `examples/fibonacci.c`
- `examples/taylor.c`

## Reflexion personal

Este proyecto muestra como un compilador se construye por etapas pequenas. La
parte mas importante fue separar el problema: el lexer solo reconoce tokens, el
parser organiza esos tokens en una estructura, el AST representa el programa y
el generador de codigo traduce esa representacion a LLVM IR. Tambien fue util
ver que estructuras como `if`, `while`, `for` y recursion se reducen a bloques
basicos, saltos y llamadas de funcion en LLVM.

La implementacion todavia no es un compilador completo de C, pero ya cubre las
construcciones principales solicitadas y deja una base clara para agregar
arreglos mas completos, mas validaciones semanticas y generacion de ejecutables.
