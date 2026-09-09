# Contributing to Ecrit

Thanks for your interest in contributing to Ecrit! This guide will help you get started.

## Prerequisites

- **Python 3.10+**
- **Rust 1.70+** (for the PyO3 native modules)
- **PySide6**

## Getting Started

1. **Fork** the repository and clone your fork:

   ```bash
   git clone https://github.com/<your-username>/Ecrit.git
   cd Ecrit
   ```

2. **Create a virtual environment** and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Build the Rust extension** (if modifying Rust code):

   ```bash
   maturin develop
   ```

4. **Create a branch** for your work:

   ```bash
   git checkout -b my-feature
   ```

## Running Tests

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v
```

The `QT_QPA_PLATFORM=offscreen` variable allows the PySide6 test suite to run without a display server.

## Submitting a Pull Request

1. Make sure all tests pass before pushing.
2. Keep commits focused and write clear commit messages.
3. Open a pull request against `main` with a description of your changes.
4. Link any related issues.

## Code Style

- Python: follow PEP 8. Use type hints where practical.
- Rust: run `cargo fmt` and `cargo clippy` before committing.

## Reporting Bugs & Requesting Features

Please use the [issue templates](https://github.com/FlintWave/Ecrit/issues/new/choose) when filing bugs or feature requests.

## License

By contributing, you agree that your contributions will be licensed under the [GPL-3.0 License](LICENSE).
