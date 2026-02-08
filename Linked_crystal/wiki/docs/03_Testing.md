# Testing Guide

This document explains how to run tests for the Linked Crystal project.

## App (Client) Tests

The app tests are located in `Linked_crystal/app/tests`. They are organized into three categories:

- **Protocol**: Unit tests for packet serialization and dispatching logic.
- **Functional**: Integration and UI logic tests (mocked Kivy).
- **Resilience**: Tests for buffer management and reconnection.

### Prerequisites

You must have the virtual environment installed in the root of the repository:
```bash
./scripts/setup_env.sh # or similar if exists
```

### Running All Tests

To run all tests for the app with colored output and summary:

```bash
cd Linked_crystal/app
./run_tests.sh
```

Or using the standard command from the root of the repository:

```bash
PYTHONPATH=Linked_crystal/app/src .venv/bin/python3 -m unittest discover -s Linked_crystal/app/tests
```

Or if you are inside `Linked_crystal/app` (standard command):

```bash
PYTHONPATH=src ../../.venv/bin/python3 -m unittest discover -s tests
```

### Running Specific Categories

- **Protocol**: `PYTHONPATH=src ../../.venv/bin/python3 -m unittest discover -s tests/protocol`
- **Functional**: `PYTHONPATH=src ../../.venv/bin/python3 -m unittest discover -s tests/functional`
- **Resilience**: `PYTHONPATH=src ../../.venv/bin/python3 -m unittest discover -s tests/resilience`

## Server Tests

Server tests are written in Go and located in `Linked_crystal/server/src`.

### Running Tests

```bash
cd Linked_crystal/server/src
./run_tests.sh
```
