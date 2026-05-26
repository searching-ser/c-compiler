# Manual de usuario

## 1. Requisitos

Para ejecutar el proyecto se necesita:

- Python 3.10 o superior.
- `pip`.
- Las dependencias listadas en `requirements.txt`:
  - `ply`
  - `llvmlite`

## 2. Crear un entorno virtual

Desde la carpeta del repositorio:

```bash
python -m venv .venv
```

En Windows PowerShell, activar el entorno con:

```bash
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activacion, ejecutar una vez:

```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Despues volver a activar:

```bash
.\.venv\Scripts\Activate.ps1
```

## 3. Instalar dependencias

Con el entorno virtual activado:

```bash
python -m pip install -r requirements.txt
```

Verificar que las dependencias se instalaron:

```bash
python -m pip show ply llvmlite
```

## 4. Generar LLVM IR con el compilador

El archivo principal del compilador es:

```text
analisis.py
```

Para generar LLVM IR del ejemplo incluido dentro de `analisis.py`:

```bash
python analisis.py
```

Para generar LLVM IR desde un archivo de ejemplo:

```bash
python analisis.py examples/factorial.c
```

El resultado se imprime en la terminal como codigo LLVM IR.

## 5. Ejecutar los programas de prueba

El proyecto incluye cinco programas de prueba:

```text
examples/factorial.c
examples/fibonacci.c
examples/taylor.c
examples/control_flow.c
examples/switch_printf.c
```

Para probar cada uno:

```bash
python analisis.py examples/factorial.c
python analisis.py examples/fibonacci.c
python analisis.py examples/taylor.c
python analisis.py examples/control_flow.c
python analisis.py examples/switch_printf.c
```

Cada comando imprime el LLVM IR generado para ese programa.

## 6. Verificar que el IR generado sea valido

Opcionalmente, se puede validar que todos los ejemplos generen LLVM IR correcto
con este comando:

```bash
python -B -c "from pathlib import Path; from llvmlite import binding as llvm; from analisis import compile_source; llvm.initialize_native_target(); llvm.initialize_native_asmprinter(); [llvm.parse_assembly(compile_source(p.read_text())).verify() or print(p.name, 'OK') for p in sorted(Path('examples').glob('*.c'))]"
```

La salida esperada es:

```text
control_flow.c OK
factorial.c OK
fibonacci.c OK
switch_printf.c OK
taylor.c OK
```

## 7. Ejecutar el demo JIT

El archivo `hello.py` no usa la gramatica del compilador. Es un ejemplo
independiente para demostrar como se genera y ejecuta LLVM IR con llvmlite.

Para ejecutarlo:

```bash
python hello.py
```

La salida incluye el LLVM IR de una funcion equivalente a:

```c
int main() {
    return 5 + 3;
}
```

y despues imprime:

```text
main() = 8
```

## 8. Estructura de archivos

```text
analisis.py       Lexer, parser y generador LLVM IR.
arbol.py          Definicion de nodos del AST.
runtime.py        Funciones auxiliares para JIT con llvmlite.
hello.py          Demo independiente de llvmlite.
examples/         Programas de prueba.
README.md         Resumen general del proyecto.
REPORTE.md        Reporte tecnico del proyecto.
MANUAL_USUARIO.md Manual de uso del proyecto.
```

## 9. Notas importantes

- El compilador genera codigo intermedio LLVM IR; no genera un ejecutable final
  directamente.
- `printf` se declara como funcion externa de LLVM.
- Los ejemplos con recursion son `factorial.c`, `fibonacci.c` y `taylor.c`.
- El soporte de arreglos es basico y no incluye revision de rango en ejecucion.
