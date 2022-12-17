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

Lemming requires Python 3.11

## Usage

### 1. Create the config

Lemming's config lives in these places:

- in the `.lemming.toml` file,
- in the `.github/.lemming.toml` file,
- in the `pyproject.toml` file,
- all of the above files in the parent directories, and in `$XDG_CONFIG_HOME`, and in `$XDG_CONFIG_DIRS`.

Please note, that there must be a `lemming` or `tool.lemming` key in the config file.

The config looks like this:

```toml
[[lemming.formatters]]
package = "example"  # REQUIRED, the package to run as `/path/to/python -m <package> <args>`
version = "1.2.3"  # OPTIONAL, defaults to the latest stable version
args = "--ignore=joe {path}"  # OPTIONAL, {path} will be replaced by the path passed to Lemming, or the current working directory by default
allow_nonzero = true  # OPTIONAL, only allowed for formatters. If true, the formatter is allowed to return a non-zero exit status. Defaults to false.
also_install = ["example-plugin"]  # OPTIONAL, these packages will also be installed
install_name = "python-example"  # OPTIONAL, the package to install. Defaults to the value of `package`

[[lemming.linters]]
# same as for formatters (except for `allow_nonzero`)
```

### 2. Run Lemming

After [installing](#installation) Lemming, run

```bash
lemming .
```

You can also use Lemming as a GitHub workflow, like [this](.github/workflows/lemming.yml).

## CLI usage

```text
usage: lemming [-h] [-v] [-q] [-c CONFIG] [-V] path

Lemming is a tool for formatting and linting code.

positional arguments:
  path                  the paths (files and directories) to check. these arguments will be passed to the formatters and linters as arguments where {path} is used

options:
  -h, --help            show this help message and exit
  -v, --verbose         log more information
  -q, --quiet           log less information. can be passed multiple times
  -c CONFIG, --config CONFIG
                        the config file to use. if passed all other config files will be ignored
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
