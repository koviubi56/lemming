"""
Lemming is a tool for formatting and linting code.

Copyright (C) 2022  Koviubi56

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
# SPDX-License-Identifier: GPL-3.0-or-later
# TODO: fail fast turn on/off
import os
import pathlib
import shlex
import subprocess  # noqa: S404
import sys
from typing import (
    AnyStr,
    Iterable,
    List,
    Mapping,
    MutableSequence,
    Optional,
    Protocol,
    Union,
)

from confz import ConfZ, ConfZFileSource
from confz.exceptions import ConfZFileException
from typing_extensions import NamedTuple, Self, TypeAlias, TypeVar

from . import logger

try:
    import tomllib  # novermin
except Exception:  # noqa: BLE001
    import tomli as tomllib

CONFIG_FILE_NAME = ".lemming.toml"
CONFIG_FILE_NOT_FOUND_EXC = FileNotFoundError(
    f"No config file was found. Please provide a {CONFIG_FILE_NAME}"
    " file, or an [tool.lemming] entry in the pyproject.toml file!"
)
CONFIG_HAS_NO_LEMMING_STUFF = ValueError(
    "The found pyproject.toml file has no tool.lemming key!"
    # we don't actually check for "tool.lemming" key.
    # we search for config["tool"]["lemming"]
)
T = TypeVar("T")


class _PathLike(Protocol):
    def __fspath__(self) -> AnyStr:
        ...


PathLike: TypeAlias = Union[_PathLike, AnyStr]


class WhatToQuiet(NamedTuple):
    commands: bool
    pip: bool


def assert_dict_keys(
    dictionary: Iterable[T], keys: MutableSequence[T]
) -> None:
    """
    Assert that `dictionary`'s keys are in `keys`

    Args:
        dictionary (Iterable[Any, Any]): The dictionary to check.
        keys (MutableSequence[Any]): The keys that are allowed.

    Raises:
        ValueError: If a key is found within `dictionary` but not within
        `keys`.
    """
    logger.debug(f"Making sure that dict {dictionary!r} only has key {keys!r}")
    with logger.ctxmgr:
        for key in dictionary:
            if key not in keys:
                logger.error(
                    f"Key {key!r} cannot be found within {keys}. Invalid"
                    " config!"
                )
                raise ValueError(
                    f"config {dictionary!r} cannot have key {key!r}"
                )
            keys.remove(key)


class FormatterOrLinter(ConfZ):
    """
    An ABC for formatters and linters.

    Args:
        packages (List[str]): The packages' name (optionally versions
        with "==x.y.z") to install with pip.
    """

    # it's actually Iterable, but that introduces some bugs
    packages: List[str]

    def replace_command(
        self,
        command: str,
        paths_to_check: Iterable[pathlib.Path],
    ) -> str:
        r"""
        Return the command with {pyexe}, {path}, and {packages} being replaced.

        | Old        | New              |
        | ---------- | ---------------- |
        | {pyexe}    | sys.executable   |
        | {path}     | paths_to_check\* |
        | {packages} | self.packages\*  |

        \*: `" ".join()` will be used

        Args:
            command (str): The command.
            paths_to_check (Iterable[pathlib.Path]): Paths to check.

        Returns:
            str: The new command.
        """
        return (
            command.strip()
            .replace("{pyexe}", sys.executable)
            .replace("{path}", " ".join(map(str, paths_to_check)))
            .replace("{packages}", " ".join(self.packages))
        )

    def run_command(
        self,
        command: str,
        paths_to_check: Iterable[pathlib.Path],
        quiet: bool,
    ) -> bool:
        """
        Run command `command`.
        Also replaces these:
        - `{pyexe}` -> `sys.executable`

        In `self.args` `{path}` be replaced by `paths_to_check`.

        Args:
            command (str): The command to run.
            paths_to_check (Iterable[pathlib.Path]): The paths to check.
            quiet (bool): Don't let the command write to stdout and stderr

        Returns:
            bool: `exit_status == 0`
        """
        command = self.replace_command(command, paths_to_check)

        splitted = shlex.split(command, posix=os.name != "nt")
        logger.debug(f"Running command {splitted!r}")
        completed_process = subprocess.run(  # noqa: S603
            splitted,
            check=False,
            capture_output=quiet,
            shell=False,
        )
        exit_status = completed_process.returncode
        if exit_status == 0:
            logger.info(f"Successfully ran command {command!r}")
            return True
        logger.error(
            f"Command {command!r} returned non-zero exit status {exit_status}"
        )
        return False

    def install(self, quiet: bool) -> bool:
        """
        Install the packages.

        Args:
            quiet (bool): Don't let `pip` write to stdout and stderr.

        Returns:
            bool: `exit_status == 0`
        """
        logger.info(f"Installing {self.packages}")
        with logger.ctxmgr:
            return self.run_command(
                "{pyexe} -m pip install -U {packages}", [], quiet
            )


class Formatter(FormatterOrLinter):
    format_command: str
    check_command: Optional[str] = None
    allow_nonzero_on_format: bool = False

    def run_format(
        self,
        paths_to_check: Iterable[pathlib.Path],
        what_to_quiet: WhatToQuiet,
    ) -> bool:
        install_success = self.install(what_to_quiet.pip)
        if not install_success:
            logger.error(
                f"Could not install the packages {self.packages}! See"
                " pip's output for more information."
            )
            return False

        success = self.run_command(
            self.format_command, paths_to_check, what_to_quiet.commands
        )
        if success or self.allow_nonzero_on_format:
            logger.info(
                f"Successfully ran (format) formatter {self.packages}!"
            )
        else:
            logger.error(
                f"Could not run (format) formatter ({self.packages};"
                f" {self.format_command!r})! (NOTE: The format_command command"
                " is expected to modify/format the code and return zero. This"
                " is DIFFERENT from check_command. If you still want to allow"
                " this, set allow_nonzero_on_format=true for this formatter.)"
            )
        return success

    def run_check(
        self,
        paths_to_check: Iterable[pathlib.Path],
        what_to_quiet: WhatToQuiet,
    ) -> bool:
        if not self.check_command:
            logger.warning(
                f"The formatter {self.packages} does NOT have a check_command!"
                " Skipping..."
            )
            return True

        install_success = self.install(what_to_quiet.pip)
        if not install_success:
            logger.error(
                f"Could not install the packages {self.packages}! See"
                " pip's output for more information."
            )
            return False

        success = self.run_command(
            self.check_command, paths_to_check, what_to_quiet.commands
        )
        if success:
            logger.info(f"Successfully ran (check) formatter {self.packages}!")
        else:
            logger.error(
                f"Could not run (check) formatter ({self.packages};"
                f" {self.format_command!r})! (NOTE: The check_command command"
                " is expected to CHECK that the code is up to standards. If"
                " the code is ok, the command should return 0; otherwise it"
                " should return non-zero.)"
            )
        return success

    @classmethod
    def from_dict(cls, dict_: Mapping[str, Union[str, bool]]) -> Self:
        assert_dict_keys(
            dict_,
            [
                "packages",
                "format_command",
                "check_command",
                "allow_nonzero_on_format",
            ],
        )
        return cls(**dict_)


class Linter(FormatterOrLinter):
    command: str
    run_first: bool = False

    def run(
        self,
        paths_to_check: Iterable[pathlib.Path],
        what_to_quiet: WhatToQuiet,
    ) -> bool:
        install_success = self.install(what_to_quiet.pip)
        if not install_success:
            logger.error(
                f"Could not install linter {self.packages}! See"
                " pip's output for more information."
            )

        success = self.run_command(
            self.command, paths_to_check, what_to_quiet.commands
        )
        if success:
            logger.info(f"Successfully ran linter {self.packages}!")
        else:
            logger.error(
                "Linting failed! See the linter's output for more"
                " information!"
            )
        return success

    @classmethod
    def from_dict(cls, dict_: Mapping[str, Union[str, bool]]) -> Self:
        assert_dict_keys(
            dict_,
            ["packages", "command", "run_first"],
        )
        return cls(**dict_)


class Config(ConfZ):
    formatters: List[Formatter]
    linters: List[Linter]
    # ^ also modify within read_config_file()

    def get_first_linters(self) -> List[Linter]:
        return [linter for linter in self.linters if linter.run_first]

    def get_other_linters(self) -> List[Linter]:
        return [linter for linter in self.linters if not linter.run_first]


def get_config_dot_lemming(folder: pathlib.Path) -> Config:
    return Config(ConfZFileSource(file=".lemming.toml", folder=folder))


def get_config_pyproject(pyproject: pathlib.Path) -> Config:
    config_text = pyproject.read_text(encoding="utf-8")
    pyproject_config = tomllib.loads(config_text)
    try:
        lemming_config = pyproject_config["tool"]["lemming"]
    except KeyError as exception:
        raise CONFIG_HAS_NO_LEMMING_STUFF from exception
    return Config(**lemming_config)


def get_config(folder: PathLike) -> None:
    folder = pathlib.Path(folder)
    try:
        # try .lemming.toml
        return get_config_dot_lemming(folder)
    except ConfZFileException:
        # try pyproject.toml
        pyproject = folder / "pyproject.toml"
        if not pyproject.exists():
            # recursion... recursion recursion...
            if folder.parent == folder:
                raise CONFIG_FILE_NOT_FOUND_EXC from None
            return get_config(folder.parent)
        return get_config_pyproject(pyproject)
