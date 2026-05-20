# c-compiler

Experimental C compiler written in Python. The project is currently a small
prototype for learning and building the first pieces of a compiler pipeline:
lexing/parsing, an abstract syntax tree, LLVM IR generation, and JIT execution.

## What is included

- `arbol.py`: AST node definitions and visitor interfaces.
- `analisis.py`: PLY lexer/parser and an early LLVM IR generator experiment.
- `hello.py`: minimal llvmlite demo that builds LLVM IR for `main`, JIT-runs it,
  and emits an object file.
- `runtime.py`: helper functions for creating an LLVM execution engine and
  compiling LLVM IR.

## Requirements

- Python 3.10 or newer
- `ply`
- `llvmlite`
- `uv` for Python version and environment management, optional but recommended

## Python environment setup

The version should be Python 3.10 or newer.

### Using uv


Install the Python version you want to use:

```bash
uv python install 3.10
```

Pin that version for this project:

```bash
uv python pin 3.10
```

Create the virtual environment with the pinned Python version:

```bash
uv venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

Install the required libraries from `requirements.txt`:

```bash
uv pip install -r requirements.txt
```

Check the active Python version:

```bash
python --version
```

### Using venv and pip

If you have multiple Python versions installed, use the one that meets the
requirement when creating the environment. For example:

```bash
python3.10 -m venv .venv
```

If `python3.10` is not available, install or select a newer Python version.
With `pyenv`, one common flow is:

```bash
pyenv install 3.10.13
pyenv local 3.10.13
python --version
```

After confirming the version, create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies inside the active environment:

```bash
python -m pip install -r requirements.txt
```

## How to run

Run the LLVM demo:

```bash
python hello.py
```

This prints the generated LLVM IR, executes the generated `main` function with
the JIT engine, prints its result, and writes a `test.o` object file.

Run the parser/code generation experiment:

```bash
python analisis.py
```

`analisis.py` contains an embedded source snippet in the `data` variable. Edit
that string to try different small C-like programs as the parser evolves.

## Current status

This is an early prototype. The compiler does not yet accept full C; it is
building up support for simple declarations, assignments, arithmetic
expressions, relational expressions, AST traversal, and LLVM code generation.
