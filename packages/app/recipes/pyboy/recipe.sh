#!/bin/bash

# Asegurarse que setuptools esté instalado antes de construir PyBoy
python3 -m pip install --upgrade pip setuptools

PYBOY_VERSION="2.3.0"  # O la que estés usando

build_python_package \
  --name "pyboy" \
  --version "$PYBOY_VERSION" \
  --url "https://files.pythonhosted.org/packages/source/p/pyboy/pyboy-${PYBOY_VERSION}.tar.gz"
