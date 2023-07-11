# Lemming

[![Hits-of-Code](https://hitsofcode.com/github/koviubi56/lemming?branch=main)](https://hitsofcode.com/github/koviubi56/lemming/view?branch=main)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/d421571132f64a7dbd63fef92cf36e3e)](https://www.codacy.com/gh/koviubi56/lemming/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=koviubi56/lemming&amp;utm_campaign=Badge_Grade)
![CodeFactor Grade](https://img.shields.io/codefactor/grade/github/koviubi56/lemming)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![semantic-release](https://img.shields.io/badge/%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)
![GitHub](https://img.shields.io/github/license/koviubi56/lemming)
![PyPI](https://img.shields.io/pypi/v/python-lemming)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-lemming)
![PyPI - Format](https://img.shields.io/pypi/format/python-lemming)

**Lemming** is a tool for formatting and linting your code. With Lemming, everyone will use the same formatters and linters, with the same version.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install Lemming. _[Need more help?](https://packaging.python.org/en/latest/tutorials/installing-packages/)_

```bash
pip install python-lemming
```

## Requirements

Lemming requires Python 3.7

## Usage

### 1. Create the config

Lemming's config lives in these places:

- in the `.lemming.toml` file
- in the `pyproject.toml` file

Please note, that there must be a `lemming` or `tool.lemming` key in the config file.

The config looks like this:

```toml
fail_fast = false  # OPTIONAL, whether or not immediately quit in case of an error

[[formatters]]
packages = ["example"]  # REQUIRED, the package(s) to install with pip (might include versions with "==x.y.z")
format_command = "{pyexe} -m example {path}"  # REQUIRED, the command to run to format the code ({pyexe} will be replaced with the python executable, {path} with the path passed to Lemming (usually the current working directory: "."))
check_command = "{pyexe} -m example --check {path}"  # OPTIONAL, the command to run to check the code (stuff will be replaced just like in format_command)
allow_nonzero_on_format = true  # OPTIONAL, if true it is allowed for the format_command to return a non-zero exit status

[[linters]]
packages = ["example"]  # REQUIRED, same as for formatters
command = "{pyexe} -m example {path}"  # REQUIRED, the command to run to lint the code (stuff will be replaced just like in format_command)
run_first = true  # OPTIONAL, if true this linter will be ran BEFORE formatters, and linters with this being false. Defaults to false.
```

### 2. Run Lemming

After [installing](#installation) Lemming, run

```bash
lemming {format,check} .
```

If you choose format, the `format_command`s will be ran, but if you choose check, the `check_command`s will be ran. Linters will be ran in both cases.

You can also use Lemming as a GitHub workflow, like [this](.github/workflows/lemming.yml).

## CLI usage

```bash
 Usage: lemming [OPTIONS] COMMAND [ARGS]...

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version             -V                                       Print the version of Lemming and exit.                                                              │
│ --install-completion          [bash|zsh|fish|powershell|pwsh]  Install completion for the specified shell. [default: None]                                         │
│ --show-completion             [bash|zsh|fish|powershell|pwsh]  Show completion for the specified shell, to copy it or customize the installation. [default: None]  │
│ --help                                                         Show this message and exit.                                                                         │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ check                        Check the formatting of your code and run linters.                                                                                    │
│ format                       Format your code and run linters.                                                                                                     │
│ pre-commit                   Install a pre-commit git hook which will run Lemming.                                                                                 │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Check

```bash
 Usage: lemming check [OPTIONS] PATHS...

 Check the formatting of your code and run linters.

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    paths      PATHS...  [default: None] [required]                                                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --quiet-commands,--qc                If passed the output of the formatters and linters will be hidden.                         │
│ --quiet-pip,--qp                     If passed the output of pip will be hidden.                                                │
│ --verbose              -v            When passed the logger's threshold will be decreased by 10 (may be passed multiple times)  │
│ --quiet                -q            When passed the logger's threshold will be increased by 10 (may be passed multiple times)  │
│ --config                       FILE  The config file to use. [default: None]                                                    │
│ --help                               Show this message and exit.                                                                │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Format

```bash
 Usage: lemming format [OPTIONS] PATHS...

 Format your code and run linters.

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    paths      PATHS...  [default: None] [required]                                                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --quiet-commands,--qc                If passed the output of the formatters and linters will be hidden.                         │
│ --quiet-pip,--qp                     If passed the output of pip will be hidden.                                                │
│ --verbose              -v            When passed the logger's threshold will be decreased by 10 (may be passed multiple times)  │
│ --quiet                -q            When passed the logger's threshold will be increased by 10 (may be passed multiple times)  │
│ --config                       FILE  The config file to use. [default: None]                                                    │
│ --help                               Show this message and exit.                                                                │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Pre-commit

```bash
 Usage: lemming pre-commit [OPTIONS]

 Install a pre-commit git hook which will run Lemming.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --git-repository          DIRECTORY  The root directory of the git repository to use. Defaults to the current working directory. [default: (dynamic)]      │
│ --verbose         -v                 When passed the logger's threshold will be decreased by 10 (may be passed multiple times)                             │
│ --quiet           -q                 When passed the logger's threshold will be increased by 10 (may be passed multiple times)                             │
│ --help                               Show this message and exit.                                                                                           │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Support

Questions should be asked in the [Discussions tab](https://github.com/koviubi56/lemming/discussions/categories/q-a).

Feature requests and bug reports should be reported in the [Issues tab](https://github.com/koviubi56/lemming/issues/new/choose).

Security vulnerabilities should be reported as described in our [Security policy](https://github.com/koviubi56/lemming/security/policy) (in the [SECURITY.md](SECURITY.md) file).

## Contributing

[Pull requests](https://github.com/koviubi56/lemming/blob/main/CONTRIBUTING.md#pull-requests) are welcome. For major changes, please [open an issue first](https://github.com/koviubi56/lemming/issues/new/choose) to discuss what you would like to change.

Please make sure to add entries to [the changelog](CHANGELOG.md).

For more information, please read the [contributing guidelines](CONTRIBUTING.md).

## Authors and acknowledgments

A list of nice people who helped this project can be found in the [CONTRIBUTORS file](CONTRIBUTORS).

## License

[GNU GPLv3+](LICENSE)
