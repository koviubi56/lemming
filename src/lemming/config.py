"""
Lemming is a tool for formatting and linting code.

Copyright (C) 2022-2024  Koviubi56

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
import os
import pathlib
import secrets
import shlex
import subprocess
import sys
from collections.abc import Iterable
from typing import cast

import pydantic
from typing_extensions import NamedTuple, Self, TypeVar

from . import logger

try:
    import tomllib  # novermin
except Exception:  # noqa: BLE001
    import tomli as tomllib  # type: ignore[no-redef]

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


class WhatToQuiet(NamedTuple):
    """What things should not be able to write to stdout and stderr."""

    commands: bool
    pip: bool


class FormatterOrLinter(pydantic.BaseModel):
    """
    An ABC for formatters and linters.

    Args:
        name (str, optional): The name of the formatter/linter. Only used to
            specify which formatter/linter to run. Defaults to packages[0].
        packages (list[str]): The packages' names (optionally versions
            with "==x.y.z") to install with pip.
    """

    name: str = ""
    packages: list[str]

    @pydantic.model_validator(mode="after")
    def _validate_name(self, _: object) -> Self:
        if self.name == "":
            try:
                self.name = self.packages[0]
            except IndexError:
                name = secrets.token_hex(2)
                logger.warning(
                    "A formatter or linter does not have packages nor a name!"
                    " Please provide a name for it! Its name will be set to"
                    f" {name!r} for this run."
                )
                self.name = name
        return self

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

        Args:
            command (str): The command to run.
            paths_to_check (Iterable[pathlib.Path]): The paths to check.
            quiet (bool): Don't let the command write to stdout and stderr

        Returns:
            bool: `exit_status == 0`
        """
        command = self.replace_command(command, paths_to_check)

        splitted = shlex.split(command, posix=os.name != "nt")
        logger.info(f"Running command {splitted!r}")
        quiet_kwargs = (
            {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
            if quiet
            else {}
        )
        completed_process = cast(
            subprocess.CompletedProcess[str],
            subprocess.run(  # type: ignore[call-overload]
                splitted,
                shell=False,  # noqa: S603
                check=False,
                **quiet_kwargs,
            ),
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
        with logger.indent:
            return self.run_command(
                "{pyexe} -m pip install -U {packages}", [], quiet
            )


class Formatter(FormatterOrLinter):
    """
    A formatter.

    Args:
        packages (List[str]): The packages' names (optionally versions
            with "==x.y.z") to install with pip.
        format_command (str): The command to use to format the code (with the
            `format` subcommand)
        check_command (str | None, optional): The command to use to check
            the code (with the `check` subcommand). Defaults to None.
        allow_nonzero_on_format (bool, optional): Whether or not to allow the
            formatter to return a non-zero exit status when formatting.
            Defaults to False.
    """

    format_command: str
    check_command: str | None = None
    allow_nonzero_on_format: bool = False

    def run_format(
        self,
        paths_to_check: Iterable[pathlib.Path],
        what_to_quiet: WhatToQuiet,
    ) -> bool:
        """
        Format the code.

        Args:
            paths_to_check (Iterable[pathlib.Path]): The paths to format.
            what_to_quiet (WhatToQuiet): What to quiet.

        Returns:
            bool: `exit_status == 0`
        """
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
            logger.info(f"Successfully ran (format) formatter {self.name}!")
        else:
            logger.error(
                f"Could not run (format) formatter {self.name};"
                f" ({self.format_command!r})! (NOTE: The format_command"
                " command is expected to modify/format the code and return"
                " zero. This is DIFFERENT from check_command. If you still"
                " want to allow this, set allow_nonzero_on_format=true for"
                " this formatter.)"
            )
        return success

    def run_check(
        self,
        paths_to_check: Iterable[pathlib.Path],
        what_to_quiet: WhatToQuiet,
    ) -> bool:
        """
        Check the code.

        Args:
            paths_to_check (Iterable[pathlib.Path]): Paths to check.
            what_to_quiet (WhatToQuiet): What to quiet.

        Returns:
            bool: `exit_status == 0`
        """
        if not self.check_command:
            logger.warning(
                f"The formatter {self.name} does NOT have a check_command!"
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
            logger.info(f"Successfully ran (check) formatter {self.name}!")
        else:
            logger.error(
                f"Could not run (check) formatter {self.name}"
                f" ({self.check_command!r})! (NOTE: The check_command command"
                " is expected to CHECK that the code is up to standards. If"
                " the code is ok, the command should return 0; otherwise it"
                " should return non-zero.)"
            )
        return success


class Linter(FormatterOrLinter):
    """
    A linter.

    Args:
        packages (List[str]): The packages' names (optionally versions
            with "==x.y.z") to install with pip.
        command (str): The command to use to lint the code
        run_first (bool, optional): Whether or not to run this linter before
            all other linters and formatters.
    """

    command: str
    run_first: bool = False

    def run(
        self,
        paths_to_check: Iterable[pathlib.Path],
        what_to_quiet: WhatToQuiet,
    ) -> bool:
        """
        Lint the code.

        Args:
            paths_to_check (Iterable[pathlib.Path]): Paths to lint.
            what_to_quiet (WhatToQuiet): What to quiet.

        Returns:
            bool: `exit_status == 0`
        """
        install_success = self.install(what_to_quiet.pip)
        if not install_success:
            logger.error(
                f"Could not install packages {self.packages}! See"
                " pip's output for more information."
            )
            return False

        success = self.run_command(
            self.command, paths_to_check, what_to_quiet.commands
        )
        if success:
            logger.info(f"Successfully ran linter {self.name}!")
        else:
            logger.error(
                f"Linter {self.name} failed! See the linter's output for more"
                " information!"
            )
        return success


class Config(pydantic.BaseModel):
    """
    The configuration.

    Args:
        formatters (list[Formatter], optional): The formatters. Default
            factory is list.
        linters (list[Linter], optional): The linters. Default factory is list.
        fail_fast (bool, optional): Whether or not to immediately quit when a
            formatter or linter fails.
    """

    formatters: list[Formatter] = pydantic.Field(default_factory=list)
    linters: list[Linter] = pydantic.Field(default_factory=list)
    fail_fast: bool = True

    def get_first_linters(self) -> list[Linter]:
        """
        Get the first linters.

        Returns:
            list[Linter]: Get linters, where `linter.run_first is True`
        """
        return [linter for linter in self.linters if linter.run_first]

    def get_other_linters(self) -> list[Linter]:
        """
        Get the other linters.

        Returns:
            list[Linter]: Get linters, where `linter.run_first is False`
        """
        return [linter for linter in self.linters if not linter.run_first]


def get_config_dot_lemming(file: pathlib.Path) -> Config:
    """
    Get the config from `file`.

    Args:
        file (pathlib.Path): The config file to read from. Must use
            the `.lemming.toml` syntax (not the `pyproject.toml` syntax).

    Returns:
        Config: The configuration.
    """
    return Config.model_validate(
        tomllib.loads(file.read_text(encoding="utf-8"))
    )


def get_config_pyproject(pyproject: pathlib.Path) -> Config:
    """
    Get the config from `pyproject`.

    Args:
        pyproject (pathlib.Path): The config file to read from. Must use the
            `pyproject.toml` syntax (not the `.lemming.toml` syntax).

    Raises:
        ValueError: If the config file does not contain a tool.lemming key.

    Returns:
        Config: The configuration.
    """
    config_text = pyproject.read_text(encoding="utf-8")
    pyproject_config = tomllib.loads(config_text)
    try:
        lemming_config = pyproject_config["tool"]["lemming"]
    except KeyError as exception:
        raise CONFIG_HAS_NO_LEMMING_STUFF from exception
    return Config.model_validate(lemming_config)


def get_config(_folder: os.PathLike[str] | str) -> Config:
    """
    Get the configuration from `_folder` or a parent folder recursively.

    Args:
        _folder (os.PathLike[str] | str): The folder to use.

    Raises:
        FileNotFoundError: If no `pyproject.toml` nor `.lemming.toml` file was
            found in `_folder` and its parents.

    Returns:
        Config: The configuration.
    """
    folder = pathlib.Path(_folder)
    config_file = folder / CONFIG_FILE_NAME
    if config_file.exists():
        return get_config_dot_lemming(config_file)
    pyproject = folder / "pyproject.toml"
    if pyproject.exists():
        return get_config_pyproject(pyproject)
    # recursion... recursion recursion...
    if folder.parent == folder:
        raise CONFIG_FILE_NOT_FOUND_EXC from None
    return get_config(folder.parent)
