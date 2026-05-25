# c-compiler

Compilador experimental para un subconjunto de C/C-lite escrito en Python. Usa
PLY para el analizador lexico/sintactico, un AST con visitors y llvmlite para
generar codigo intermedio LLVM IR.

## Archivos principales

- `arbol.py`: nodos del AST y visitor base.
- `analisis.py`: lexer, parser, gramatica extendida e IR generator.
- `runtime.py`: utilidades para crear un motor JIT con llvmlite.
- `hello.py`: ejemplo minimo de generacion y ejecucion JIT.
- `examples/`: programas de prueba para la actividad.
- `REPORTE.md`: descripcion de las etapas del compilador.

## Requisitos

- Python 3.10 o superior
- `ply`
- `llvmlite`

Instalacion:

```bash
python -m pip install -r requirements.txt
```

## Uso

Generar LLVM IR del ejemplo embebido:

```bash
python analisis.py
```

Generar LLVM IR desde un archivo:

```bash
python analisis.py examples/factorial.c
```

Ejecutar el demo JIT independiente:

```bash
python hello.py
```

## Construcciones soportadas

- Tipos: `int`, `bool`/`boolean`, `float`, `char`, `void`.
- Declaraciones locales y globales simples.
- Asignaciones.
- Expresiones aritmeticas: `+`, `-`, `*`, `/`, `%`.
- Comparaciones: `==`, `!=`, `<`, `>`, `<=`, `>=`.
- Operadores logicos: `&&`, `||`, `!`.
- Bloques `{ ... }`.
- `if` / `else`.
- `while`.
- `for`.
- `do` / `while`.
- `switch`, `case`, `default`, `break`.
- Definicion y llamada a funciones.
- Llamadas recursivas.
- Llamada a `printf`.
- Conversion implicita basica entre enteros y flotantes en expresiones y asignaciones.

## Programas de prueba

- `examples/factorial.c`: recursion directa con factorial.
- `examples/fibonacci.c`: recursion doble con Fibonacci.
- `examples/taylor.c`: recursion para una aproximacion de serie de Taylor.
- `examples/control_flow.c`: `while`, `for`, `do/while` y `printf`.
- `examples/switch_printf.c`: `switch`, `case`, `default`, `break` y `printf`.
