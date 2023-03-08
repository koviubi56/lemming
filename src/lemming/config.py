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
__all__ = [
    "read_toml_file",
    "read_config_file",
    "find_config_file",
    "read_config_file_dict",
]
try:
    import tomllib  # novermin
except Exception:  # noqa: BLE001
    import tomli as tomllib

import contextlib
import os
import pathlib
import shlex
import subprocess  # noqa: S404
import sys
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    MutableSequence,
    NamedTuple,
    Optional,
    TypeVar,
    cast,
)

import pydantic
from typing_extensions import Self

from . import logger

CONFIG_FILE_NAME = ".lemming.toml"
CONFIG_FILE_NOT_FOUND_EXC = FileNotFoundError(
    f"No config file was found. Please provide a {CONFIG_FILE_NAME}"
    " file, or an [tool.lemming] entry in the pyproject.toml file!"
)
T = TypeVar("T")


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


def read_toml_file(file: pathlib.Path) -> Dict[str, Any]:
    """
    Read the toml file `file`.

    Args:
        file (pathlib.Path): The toml file to read.

    Returns:
        dict[str, Any]: The read data
    """
    logger.debug(f"Reading toml file {file}")
    with file.open("rb") as fd:
        return cast(Dict[str, Any], tomllib.load(fd))  # type: ignore


def get_home() -> pathlib.Path:
    """
    Get $HOME.

    Returns:
        pathlib.Path: $HOME.
    """
    logger.debug("Getting $HOME")
    return pathlib.Path.home()


def get_xdg_config_home() -> Optional[pathlib.Path]:
    """
    Get $XDG_CONFIG_HOME or the default value or None. Return value will
    always be an existing directory (unless None).

    Returns:
        pathlib.Path | None: $XDG_CONFIG_HOME or the default value
        ($HOME/.config) or None
    """
    logger.debug("Getting $XDG_CONFIG_HOME")
    env_value = os.environ.get("XDG_CONFIG_HOME", "")
    logger.debug(f"$XDG_CONFIG_HOME={env_value!r}")
    if env_value.strip():
        rv = pathlib.Path(env_value)
        logger.debug(f"Path is {rv!r}")
        if rv.exists() and rv.is_dir():
            logger.debug("It's an existing directory, returning")
            return rv
        logger.debug("It isn't an existing directory, going with default")
    rv = get_home() / ".config"
    if rv.exists() and rv.is_dir():
        logger.debug("It's an existing directory, returning")
        return rv
    logger.debug("It isn't an existing directory, returning None")
    return None


def _xdg_config_dirs() -> str:
    logger.debug("Getting $XDG_CONFIG_DIRS (_xdg_config_dirs)")
    env_value = os.environ.get("XDG_CONFIG_DIRS", "")
    logger.debug(f"$XDG_CONFIG_DIRS={env_value}")
    return env_value if env_value.strip() else "/etc/xdg"


def _get_xdg_config_dirs() -> Generator[pathlib.Path, None, None]:
    logger.debug("Getting $XDG_CONFIG_DIRS (_get_xdg_config_dirs)")
    envvar = _xdg_config_dirs()
    logger.debug(f"$XDG_CONFIG_DIRS is {envvar}, splitting and iterating")
    with logger.ctxmgr:
        for part in envvar.split(":"):
            logger.debug(f"{part = !r}")
            with logger.ctxmgr:
                if not part.strip():
                    logger.debug("Empty, skip")
                    continue
                path = pathlib.Path(part)
                if path.exists() and path.is_dir():
                    yield path


def get_xdg_config_dirs() -> List[pathlib.Path]:
    """
    Get $XDG_CONFIG_DIRS. Return value will always be a list of existing
    directories.

    Returns:
        list[pathlib.Path]: $XDG_CONFIG_DIRS.
    """
    logger.debug("Getting $XDG_CONFIG_DIRS (get_xdg_config_dirs)")
    return list(_get_xdg_config_dirs())


def find_config_file(
    dir_: pathlib.Path,
    allow_recursion: bool = True,
    *,
    from_recursion: bool = False,
) -> pathlib.Path:
    """
    Find the config file.

    Args:
        dir (pathlib.Path): The directory to search in.
        allow_recursion (bool, optional): Allow recursion in parent
        directories. Defaults to True.
        from_recursion (bool, optional): True if this function is called by
        this function. Don't mess with this! Defaults to False.

    Raises:
        FileNotFoundError: If the config file wasn't found (even in parent
        directories)

    Returns:
        pathlib.Path: The config file
    """
    logger.debug(
        f"Finding config file ({dir_=!r}, {allow_recursion=!r},"
        f" {from_recursion=!r})"
    )
    # * check current directory
    if (file := (dir_ / CONFIG_FILE_NAME)).exists():
        logger.debug(
            f"{file} (current dir / {CONFIG_FILE_NAME}) exists, returning"
        )
        return file
    # * check .github directory
    if (gh := (dir_ / ".github")).exists() and (
        file := (gh / CONFIG_FILE_NAME)
    ).exists():
        logger.debug(
            f"{file} (current dir / .github / {CONFIG_FILE_NAME}) exists,"
            " returning"
        )
        return file
    # * check pyproject.toml
    if (file := (dir_ / "pyproject.toml")).exists():
        logger.debug(
            f"{file} (current dir / pyproject.toml) exists, returning"
        )
        return file
    # * check XDG_CONFIG_DIRS
    if not from_recursion:
        logger.debug("Not from recursion, checking $XDG_CONFIG_DIRS")
        with logger.ctxmgr:
            for directory in get_xdg_config_dirs():
                logger.debug(f"{directory = !r}")
                with contextlib.suppress(CONFIG_FILE_NOT_FOUND_EXC.__class__):
                    logger.debug(
                        f"Calling ourselves on {directory}, recursion!"
                    )
                    with logger.ctxmgr:
                        return find_config_file(
                            directory,
                            allow_recursion=False,
                            from_recursion=True,
                        )
    # * check XDG_CONFIG_HOME
    if (
        (not from_recursion)
        and (xdg_config_home := get_xdg_config_home())
        and (file := (xdg_config_home / CONFIG_FILE_NAME)).exists()
    ):
        logger.debug(
            f"{file} ($XDF_CONFIG_HOME / {CONFIG_FILE_NAME}) exists, returning"
        )
        return file
    # * recursion with parent directory
    if allow_recursion:
        parent = dir_.parent
        logger.debug(f"Nothing found, recursion with parent ({parent})")
        with logger.ctxmgr:
            if parent == dir_:
                logger.error(
                    "No more parent directories; config file is nowhere to be"
                    " found!"
                )
                raise CONFIG_FILE_NOT_FOUND_EXC
            return find_config_file(parent, from_recursion=True)
    logger.error(
        "Config file is nowhere to be found! (NOTE: allow_recursion is False)"
    )
    raise CONFIG_FILE_NOT_FOUND_EXC


class FormatterOrLinter(pydantic.BaseModel):
    """
    An "ABC" for formatters and linters.

    Args:
        packages (List[str]): The packages' name (optionally versions
        with "==x.y.z") to install with pip.
    """

    # it's actually Iterable, but that introduces some bugs
    packages: List[str]

    @staticmethod
    def get_pyexe() -> str:
        """
        The python executable.

        Returns:
            str: sys.executable
        """
        return sys.executable

    def run_command(
        self,
        cmd: str,
        paths_to_check: Iterable[pathlib.Path],
        quiet: bool,
    ) -> bool:
        """
        Run command `cmd`.
        Also replaces these:
        - `{pyexe}` -> `sys.executable`

        In `self.args` `{path}` be replaced by `paths_to_check`.

        Args:
            cmd (str): The command to run.
            paths_to_check (Iterable[pathlib.Path]): The paths to check.
            quiet (bool): Don't let the command write to stdout and stderr

        Returns:
            bool: `exit_status == 0`
        """
        cmd = cmd.strip()
        cmd = cmd.replace("{pyexe}", sys.executable)
        paths = " ".join(map(str, paths_to_check))
        cmd = cmd.replace("{path}", paths)
        packages = " ".join(self.packages)
        cmd = cmd.replace("{packages}", packages)

        splitted = shlex.split(cmd, posix=os.name != "nt")
        logger.debug(f"Running command {splitted!r}")
        completed_process = subprocess.run(  # noqa: S603
            splitted,
            check=False,
            capture_output=quiet,
        )
        exit_status = completed_process.returncode
        if exit_status == 0:
            logger.info(f"Successfully ran command {cmd!r}")
            return True
        logger.error(
            f"Command {cmd!r} returned non-zero exit status {exit_status}"
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

    def run(
        self,
        paths_to_check: Iterable[pathlib.Path],
        what_to_quiet: WhatToQuiet,
    ) -> bool:
        raise NotImplementedError


class Formatter(FormatterOrLinter):
    format_command: str
    check_command: Optional[str] = None
    allow_nonzero_on_format: bool = False

    def run_format(
        self,
        paths_to_check: Iterable[pathlib.Path],
        what_to_quiet: WhatToQuiet,
    ) -> bool:
        if not self.install(what_to_quiet.pip):
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
        if not self.install(what_to_quiet.pip):
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
    def from_dict(cls, dict_: Mapping[str, Any]) -> Self:
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
        if not self.install(what_to_quiet.pip):
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
    def from_dict(cls, dict_: Mapping[str, Any]) -> Self:
        assert_dict_keys(
            dict_,
            ["packages", "command", "run_first"],
        )
        return cls(**dict_)


class Config(pydantic.BaseModel):
    formatters: Iterable[Formatter]
    linters: Iterable[Linter]
    # ^ also modify within read_config_file()

    def get_first_linters(self) -> List[Linter]:
        return [linter for linter in self.linters if linter.run_first]

    def get_other_linters(self) -> List[Linter]:
        return [linter for linter in self.linters if not linter.run_first]


def read_config_file_dict(
    read_data: Mapping[str, Any], file: str = "<unknown file>"
) -> Dict[str, Any]:
    try:
        logger.debug('Searching for "lemming" key')
        data = read_data["lemming"]
    except KeyError:
        try:
            logger.debug('Not found, searching for "tool.lemming" key')
            data = read_data["tool"]["lemming"]
        except KeyError as exc:
            logger.error(
                'Neither "lemming" nor "tool.lemming" was found within the'
                f" config file ({file})!"
            )
            exc_ = ValueError(
                f'invalid config file {file}: doesn\'t have key "lemming" or'
                ' "tool.lemming"'
            )
            exc_.add_note(
                "NOTE: The config file isn't what you expected it to be? Check"
                " your .github directory, $XDG_CONFIG_HOME and"
                " $XDG_CONFIG_DIRS environment variables, and the parent"
                " directories."
            )
            raise exc_ from exc
    return data


def read_config_file(dictionary: Mapping[str, Any]) -> Config:
    logger.debug(f"Making dict {dictionary} a Config() object")
    with logger.ctxmgr:
        assert_dict_keys(dictionary, ["formatters", "linters"])
        logger.debug(f'Making formatters ({dictionary.get("formatters", [])})')
        formatters = [
            Formatter.from_dict(dict_)
            for dict_ in dictionary.get("formatters", [])
        ]
        logger.debug(f'Making linters ({dictionary.get("linters", [])})')
        linters = [
            Linter.from_dict(dict_) for dict_ in dictionary.get("linters", [])
        ]
        logger.debug(f"And making the Config({formatters=!r}, {linters=!r})")
        return Config(
            formatters=formatters,
            linters=linters,
        )
