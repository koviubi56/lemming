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

Lemming requires Python 3.8

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

```text
usage: lemming [-h] [-v] [-q] [--quiet-commands] [--quiet-pip] [-c CONFIG] [-V] {format,check} path

Lemming is a tool for formatting and linting code.

positional arguments:
  {format,check}        format the code with the formatters, or check the code with the formatters (linters will be ran in all cases)
  path                  the paths (files and directories) to check. These arguments will be passed to the formatters and linters as arguments where {path} is used

options:
  -h, --help            show this help message and exit
  -v, --verbose         log more information
  -q, --quiet           log less information. Can be passed multiple times
  --quiet-commands      don't let ran commands write to stdout and stderr. Use --quiet-pip to quiet `pip`
  --quiet-pip           don't let pip write to stdout and stderr. Use --quiet-commands to quiet the formatters and linters
  -c CONFIG, --config CONFIG
                        the config file to use. If passed all other config files will be ignored
  -V, --version         print the program's version and exit
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
