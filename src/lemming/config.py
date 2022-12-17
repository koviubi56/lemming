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
    import tomllib
except Exception:
    import tomli as tomllib

import contextlib
import os
import pathlib
import subprocess  # noqa: S404
import sys
from typing import Any, Generator, TypeVar, cast

import pydantic
from typing_extensions import Self

from . import logger

CONFIG_FILE_NAME = ".lemming.toml"
CONFIG_FILE_NOT_FOUND_EXC = FileNotFoundError(
    f"No config file was found. Please provide a {CONFIG_FILE_NAME}"
    " file, or an [tool.lemming] entry in the pyproject.toml file!"
)
POTENTIAL_ERRORS = {
    "No module named".casefold(): "HINT: It seems like that module doesn't"
    " exist with that name. If the module has to be ran with a separate name"
    " than the one that was used to install it, add the `install_name` option"
    " to the config.",
    "Permission denied: '.'".casefold(): "HINT: It seems like that the"
    " formatter/linter expects a file as an argument, and not a directory."
    " Lemming by default doesn't pass anything to the formatter/linter as"
    " arguments. You can add arguments with the `args` config key. You can"
    " also use `{path}` in the `args` config key, which will be replaced with"
    " the path that was passed to Lemming, or the current working directory by"
    " default.",
    "Usage:".casefold(): "HINT: It seems like that the formatter/linter"
    " expects arguments. You can pass the `args` config key to do that. Note,"
    " that `{path}` in the `args` config key will be replaced by the path that"
    " was passed to Lemming, or the current working directory by default.",
}
T = TypeVar("T")


def assert_dict_keys(dictionary: dict[Any, Any], keys: list[Any]) -> None:
    """
    Assert that `dictionary`'s keys are in `keys`

    Args:
        dictionary (dict[Any, Any]): The dictionary to check.
        keys (list[Any]): The keys that are allowed.

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


def read_toml_file(file: pathlib.Path) -> dict[str, Any]:
    """
    Read the toml file `file`.

    Args:
        file (pathlib.Path): The toml file to read.

    Returns:
        dict[str, Any]: The read data
    """
    logger.debug(f"Reading toml file {file}")
    with file.open("rb") as fd:
        return cast(dict[str, Any], tomllib.load(fd))  # type: ignore


def get_home() -> pathlib.Path:
    """
    Get $HOME.

    Returns:
        pathlib.Path: $HOME.
    """
    logger.debug("Getting $HOME")
    return pathlib.Path.home()


def get_xdg_config_home() -> pathlib.Path | None:
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


def get_xdg_config_dirs() -> list[pathlib.Path]:
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
    Does all of the work except the method .run().

    Args:
        package (str): The package's name. This will be used to install and
        run it!
        version (str | None, optional): The package's version. If None it will
        be the latest stable version. Defaults to None.
        args (str, optional): Arguments to the formatter/linter. Defaults
        to "".
        allow_nonzero (bool, optional): Allow non-zero exit status for
        formatters (not linters!). Defaults to False.
        install_name (str | None, optional): The package's name to install. If
        it's None, it defaults to `package`. Defaults to None.
    """

    package: str
    version: str | None = None
    args: str = ""
    allow_nonzero: bool = False
    also_install: list[str] = []
    install_name: str | None = None

    def get_version(self) -> str:
        """
        Get the version stuff.

        Returns:
            str: f"=={self.version}" if self.version else ""
        """
        return f"=={self.version}" if self.version else ""

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
        paths_to_check: list[pathlib.Path],
        quiet: bool,
    ) -> bool:
        """
        Run command `cmd`.
        Also replaces these:
        - `{pyexe}` -> `sys.executable`
        - `{package}` -> `self.package`
        - `{also_install}` -> `self.also_install`
        - `{args}` -> `self.args`

        In `self.args` `{path}` be replaced by `paths_to_check`.

        Args:
            cmd (str): The command to run.
            paths_to_check (list[pathlib.Path]): The paths to check.
            quiet (bool): Don't let the command write to stdout and stderr

        Returns:
            bool: `exit_status == 0`
        """
        cmd = cmd.strip()
        cmd = cmd.replace("{pyexe}", sys.executable)
        cmd = cmd.replace("{package}", self.package)
        cmd = cmd.replace("{args}", self.args)
        paths = " ".join(map(str, paths_to_check))
        cmd = cmd.replace("{path}", paths)
        also_install = " ".join(self.also_install)
        cmd = cmd.replace("{also_install}", also_install)

        logger.debug(f"Running command {cmd!r}")
        completed_process = subprocess.run(  # noqa: S603
            cmd, check=False, capture_output=quiet
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
        Install.
        Runs the following command: `{pyexe} -m pip install -U {package}`

        Args:
            quiet (bool): Don't let `pip` write to stdout and stderr.

        Returns:
            bool: `exit_status == 0`
        """
        logger.info(f"Installing {self.package} (and {self.also_install})")
        with logger.ctxmgr:
            return self.run_command(
                "{pyexe} -m pip install -U {package} {also_install}", [], quiet
            )

    def _run(self, paths_to_check: list[pathlib.Path], quiet: bool) -> bool:
        return self.run_command(
            "{pyexe} -m {package} {args}", paths_to_check, quiet
        )

    def run(
        self,
        paths_to_check: list[pathlib.Path],
        what_to_quiet: tuple[bool, bool],
    ) -> bool:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> Self:
        """
        Return `Self` from a dictionary.

        Args:
            dictionary (dict[str, Any]): The dictionary to use.

        Returns:
            Self: The new object from `dictionary`
        """
        assert_dict_keys(
            dictionary,
            [
                "package",
                "version",
                "args",
                "allow_nonzero",
                "also_install",
                "install_name",
            ],
        )
        return cls(**dictionary)


class Formatter(FormatterOrLinter):
    def run(
        self,
        paths_to_check: list[pathlib.Path],
        what_to_quiet: tuple[bool, bool],
    ) -> bool:
        if not self.install(what_to_quiet[1]):
            logger.error(
                f"Could not install formatter {self.package}! See"
                " pip's output for more information."
            )
        success = self._run(paths_to_check, what_to_quiet[0])
        if success or self.allow_nonzero:
            logger.info(f"Successfully ran formatter {self.package}!")
        else:
            logger.error(
                f"Could not run formatter {self.package} ({self.version = !r};"
                f" {self.args = !r}; {paths_to_check = !r})! (NOTE: Formatters"
                " are expected to MODIFY the code if the formatter finds a"
                " violation (not just simply check the code). Formatters are"
                " also expected to return a ZERO exit status even if the"
                " formatter had to modify a file. To allow this behavior"
                ' change "allow_nonzero" to true in the config file for this'
                " formatter.)"
            )
        return success


class Linter(FormatterOrLinter):
    def run(
        self,
        paths_to_check: list[pathlib.Path],
        what_to_quiet: tuple[bool, bool],
    ) -> bool:
        if not self.install(what_to_quiet[1]):
            logger.error(
                f"Could not install linter {self.package}! See"
                " pip's output for more information."
            )
        if self.allow_nonzero:
            logger.warning(
                '"allow_nonzero" is set to true in the config file! This'
                " attribute is only supported for formatters, not linters!"
                " Ignoring"
            )
        success = self._run(paths_to_check, what_to_quiet[0])
        if success:
            logger.info(f"Successfully ran linter {self.package}!")
        else:
            logger.error(
                "Linting failed! See the linter's output for more"
                " information!"
            )
        return success


class Config(pydantic.BaseModel):
    formatters: list[Formatter]
    linters: list[Linter]
    # ^ also modify within read_config_file()


def read_config_file_dict(
    read_data: dict[str, Any], file: str = "<unknown file>"
) -> dict[str, Any]:
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


def read_config_file(dictionary: dict[str, Any]) -> Config:
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
