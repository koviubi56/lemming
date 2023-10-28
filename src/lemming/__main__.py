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
import dataclasses
import pathlib
import sys
import time
from typing import List, Optional

import typer
from typing_extensions import Annotated, Self

from . import __version__, logger
from .config import (
    Config,
    Formatter,
    Linter,
    WhatToQuiet,
    get_config,
    get_config_dot_lemming,
    get_config_pyproject,
)

PRE_COMMIT_FILE = """#!/bin/sh
#!/usr/bin/env bash
# File generated by Lemming: https://github.com/koviubi56/lemming

set -euo pipefail
PYTHON='{}'

if [[ -n "${LEMMING_VERBOSE:-}" ]]; then
    exec $PYTHON -m lemming format --verbose $(pwd)
    ret_code=$?
else
    exec $PYTHON -m lemming format --quiet-pip "$(pwd)"
    ret_code=$?
fi
exit $ret_code
"""

app = typer.Typer(no_args_is_help=True)


@dataclasses.dataclass(frozen=True)
class Settings:
    """
    The settings.

    Args:
        what_to_quiet (WhatToQuiet): What to quiet.
        config (Config): The configuration.
        only (Optional[List[str]]): Only run these formatters/linters. If
        None, run all.
    """

    what_to_quiet: WhatToQuiet
    config: Config
    only: Optional[List[str]]

    def should_run(self, name: str) -> bool:
        """
        Should the formatter/linter with that name run?

        Args:
            name (str): The formatter's/linter's name

        Returns:
            bool: True if it should run, False otherwise
        """
        if not self.only:
            return True
        return name in self.only


class Timer:
    """A timer."""

    def __init__(self) -> None:
        """Create a Timer instance."""
        self.start = None
        self.time = None

    def __enter__(self) -> Self:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        assert self.start  # noqa: S101
        self.time = time.perf_counter() - self.start


def run_linter(
    linter: Linter, paths: List[pathlib.Path], settings: Settings
) -> bool:
    """
    Run `linter`.

    Args:
        linter (Linter): The linter to run.
        paths (List[pathlib.Path]): The paths to lint.
        settings (Settings): The settings.

    Raises:
        typer.Exit: If the linter failed and fail fast is True.

    Returns:
        bool: `exit_status == 0`
    """
    with logger.ctxmgr:
        with Timer() as linter_timer:
            success = linter.run(paths, settings.what_to_quiet)
            if not success:
                logger.error(
                    f"Could not run linter {linter.name}!"
                    " Please see the linter's output for more"
                    " details."
                )
                if settings.config.fail_fast:
                    raise typer.Exit(1)
                return False
        logger.info(f"Ran linter in {linter_timer.time} seconds")
        return True


def linter_first(paths: List[pathlib.Path], settings: Settings) -> bool:
    """
    Run the first linters.

    Args:
        paths (List[pathlib.Path]): The paths to lint.
        settings (Settings): The settings.

    Returns:
        bool: Whether or not all linters successfully ran.
    """
    logger.info("Running first linters")
    return_value = True
    with logger.ctxmgr:
        with Timer() as linters_timer:
            for linter in settings.config.get_first_linters():
                if not settings.should_run(linter.name):
                    logger.info(f"Skipping first linter {linter.name}")
                    continue
                logger.info(f"Running first linter {linter.name}")
                success = run_linter(linter, paths, settings)
                if not success:
                    return_value = False
        logger.info(f"Ran all (first) linters in {linters_timer.time} seconds")
        return return_value


def run_formatter(
    formatter: Formatter,
    paths: List[pathlib.Path],
    format_: bool,
    settings: Settings,
) -> bool:
    """
    Run `formatter`.

    Args:
        formatter (Formatter): The formatter to run.
        paths (List[pathlib.Path]): The paths to format/check.
        format_ (bool): Whether or not to format or check.
        settings (Settings): The settings.

    Raises:
        typer.Exit: If the formatter failed and fail fast is True.

    Returns:
        bool: `exit_status == 0`
    """
    with logger.ctxmgr:
        with Timer() as formatter_timer:
            if format_:
                success = formatter.run_format(paths, settings.what_to_quiet)
            else:
                success = formatter.run_check(paths, settings.what_to_quiet)

            if not success:
                logger.error(f"Could not run formatter {formatter.name}!")
                if settings.config.fail_fast:
                    raise typer.Exit(1)
                return False
        logger.info(f"Ran formatter in {formatter_timer.time} seconds")
        return True


def formatter(
    format_: bool, paths: List[pathlib.Path], settings: Settings
) -> bool:
    """
    Run all formatters.

    Args:
        format_ (bool): Whether or not to format or check.
        paths (List[pathlib.Path]): The paths to format/check.
        settings (Settings): The settings.

    Returns:
        bool: Whether or not all formatters successfully ran.
    """
    logger.info("Running formatters")
    return_value = True
    with logger.ctxmgr:
        with Timer() as formatters_timer:
            for formatter in settings.config.formatters:
                if not settings.should_run(formatter.name):
                    logger.info(f"Skipping formatter {formatter.name}")
                    continue
                logger.info(f"Running formatter {formatter.name}")
                success = run_formatter(formatter, paths, format_, settings)
                if not success:
                    return_value = False
        logger.info(f"Ran all formatters in {formatters_timer.time} seconds")
        return return_value


def linter_other(paths: List[pathlib.Path], settings: Settings) -> bool:
    """
    Run all other linters.

    Args:
        paths (List[pathlib.Path]): The paths to lint.
        settings (Settings): The settings.

    Returns:
        bool: Whether or not all other linters successfully ran.
    """
    logger.info("Running other linters")
    return_value = True
    with logger.ctxmgr:
        with Timer() as linters_timer:
            for linter in settings.config.get_other_linters():
                if not settings.should_run(linter.name):
                    logger.info(f"Skipping other linter {linter.name}")
                    continue
                logger.info(f"Running other linter {linter.name}")
                success = run_linter(linter, paths, settings)
                if not success:
                    return_value = False
        logger.info(f"Ran all other linters in {linters_timer.time} seconds")
        return return_value


def run(paths: List[pathlib.Path], format_: bool, settings: Settings) -> None:
    """
    Run all linters and formatters.

    Args:
        paths (List[pathlib.Path]): The paths to check.
        format_ (bool): Whether or not to format or check.
        settings (Settings): The settings.

    Raises:
        typer.Exit: If any formatter or linter failed and fail fast is False.
    """
    with Timer() as all_timer:
        success = True
        if linter_first(paths, settings) is False:
            success = False
        if formatter(format_, paths, settings) is False:
            success = False
        if linter_other(paths, settings) is False:
            success = False

        if not success:
            logger.error(
                "Failed, due to one or more linters/formatters failing. (HINT:"
                " Set fail_fast=true to disable this behavior)"
            )
            raise typer.Exit(1)
    logger.info(
        f"Successfully ran all formatters and linters in {all_timer.time}"
        " seconds with no errors. Good job!"
    )


def quiet_callback(value: bool) -> bool:
    """
    Increase the logger's threshold by 10 if `value`.

    Args:
        value (bool): Value.

    Returns:
        bool: `value`
    """
    if value:
        logger.threshold += 10
    return value


def verbose_callback(value: bool) -> bool:
    """
    Decrease the logger's threshold by 10 if `value`.

    Args:
        value (bool): Value.

    Returns:
        bool: `value`
    """
    if value:
        logger.threshold -= 10
    return value


def version_callback(value: bool) -> bool:
    """
    Print the version and exit if `value`.

    Raises:
        typer.Exit: if `value`

    Args:
        value (bool): Value.

    Returns:
        bool: `value`
    """
    if value:
        print(__version__)
        raise typer.Exit(0)
    return value


def both(
    quiet_commands: bool,
    quiet_pip: bool,
    verbose: bool,
    quiet: bool,
    config: Optional[pathlib.Path],
    only: Optional[List[str]],
) -> Settings:
    """
    Create the settings, and do some stuff with the given options.

    Args:
        quiet_commands (bool): Whether or not to stop the commands from
        writing to stdout and stderr.
        quiet_pip (bool): Whether ot not to stop pip from writing to stdout
        and stderr
        verbose (bool): Decrease the loggers threshold by 10 (done by the
        callback).
        quiet (bool): Increase the loggers threshold by 10 (done by the
        callback).
        config (Optional[pathlib.Path]): The configuration to use or None.
        only (Optional[List[str]]): Only run these formatters/linters. If
        None, run all.

    Raises:
        typer.Exit: If both verbose and quiet is passed.

    Returns:
        Settings: The settings.
    """
    if verbose and quiet:
        logger.critical("Verbose and quiet are mutually exclusive!")
        raise typer.Exit(2)
    if config:
        config_ = (
            get_config_pyproject(config)
            if config.name == "pyproject.toml"
            else get_config_dot_lemming(config.parent)
        )
    else:
        config_ = get_config(".")
    return Settings(
        what_to_quiet=WhatToQuiet(commands=quiet_commands, pip=quiet_pip),
        config=config_,
        only=only,
    )


@app.command("format")
def format_(
    paths: Annotated[List[pathlib.Path], typer.Argument(exists=True)],
    quiet_commands: Annotated[
        bool,
        typer.Option(
            ...,
            "--quiet-commands",
            "--qc",
            help="If passed the output of the formatters and linters will be"
            " hidden.",
        ),
    ] = False,
    quiet_pip: Annotated[
        bool,
        typer.Option(
            ...,
            "--quiet-pip",
            "--qp",
            help="If passed the output of pip will be hidden.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            callback=verbose_callback,
            help="When passed the logger's threshold will be decreased by 10"
            " (may be passed multiple times)",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            callback=quiet_callback,
            help="When passed the logger's threshold will be increased by 10"
            " (may be passed multiple times)",
        ),
    ] = False,
    config: Annotated[
        Optional[pathlib.Path],
        typer.Option(
            exists=True, dir_okay=False, help="The config file to use."
        ),
    ] = None,
    only: Annotated[
        Optional[List[str]],
        typer.Option(
            help="Only run these formatters/linters (may be passed multiple"
            " times)"
        ),
    ] = None,
) -> None:
    """Format your code and run linters."""
    run(
        paths,
        True,
        both(quiet_commands, quiet_pip, verbose, quiet, config, only),
    )


@app.command()
def check(
    paths: Annotated[List[pathlib.Path], typer.Argument(exists=True)],
    quiet_commands: Annotated[
        bool,
        typer.Option(
            ...,
            "--quiet-commands",
            "--qc",
            help="If passed the output of the formatters and linters will be"
            " hidden.",
        ),
    ] = False,
    quiet_pip: Annotated[
        bool,
        typer.Option(
            ...,
            "--quiet-pip",
            "--qp",
            help="If passed the output of pip will be hidden.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            callback=verbose_callback,
            help="When passed the logger's threshold will be decreased by 10"
            " (may be passed multiple times)",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            callback=quiet_callback,
            help="When passed the logger's threshold will be increased by 10"
            " (may be passed multiple times)",
        ),
    ] = False,
    config: Annotated[
        Optional[pathlib.Path],
        typer.Option(
            exists=True, dir_okay=False, help="The config file to use"
        ),
    ] = None,
    only: Annotated[
        Optional[List[str]],
        typer.Option(
            help="Only run these formatters/linters (may be passed multiple"
            " times)"
        ),
    ] = None,
) -> None:
    """Check the formatting of your code and run linters."""
    run(
        paths,
        False,
        both(quiet_commands, quiet_pip, verbose, quiet, config, only),
    )


def install_pre_commit(git_repository: pathlib.Path) -> None:
    """
    Install the pre-commit hook script.

    Args:
        git_repository (pathlib.Path): The root directory of the git
        repository.

    Raises:
        typer.Exit: If `git_repository` doesn't exist
        typer.Exit: If `git_repository/.git` doesn't exist
        typer.Exit: If writing to the pre-commit file failed.
    """
    if not git_repository.exists():
        logger.critical(f"Directory {git_repository} does not exist!")
        raise typer.Exit(1)
    git_directory = git_repository / ".git"
    if not git_directory.exists():
        logger.critical(f"Directory {git_repository} is not a git repository!")
        raise typer.Exit(1)
    pre_commit = git_directory / "hooks" / "pre-commit"
    if pre_commit.exists():
        logger.warning(
            f"pre-commit file {pre_commit} already exists! Overwriting..."
        )
    logger.info(f"Creating pre-commit git hook (it will use {sys.executable})")
    try:
        pre_commit.write_text(PRE_COMMIT_FILE.replace("{}", sys.executable))
    except OSError as exception:
        logger.critical("Could not write pre-commit file!", True)
        raise typer.Exit(1) from exception
    logger.info("Successfully written pre-commit!")


@app.command("pre-commit")
def pre_commit(
    git_repository: Annotated[
        pathlib.Path,
        typer.Option(
            default_factory=pathlib.Path.cwd,
            exists=True,
            file_okay=False,
            help="The root directory of the git repository to use. Defaults to"
            " the current working directory.",
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            callback=verbose_callback,
            help="When passed the logger's threshold will be decreased by 10"
            " (may be passed multiple times)",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            callback=quiet_callback,
            help="When passed the logger's threshold will be increased by 10"
            " (may be passed multiple times)",
        ),
    ] = False,
) -> None:
    """Install a pre-commit git hook which will run Lemming."""
    if verbose and quiet:
        logger.critical("Verbose and quiet are mutually exclusive!")
        raise typer.Exit(2)
    install_pre_commit(git_repository)


@app.callback()
def callback(
    _version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Print the version of Lemming and exit.",
            callback=version_callback,
        ),
    ] = False,
) -> None:
    """This function is only here for the version."""


def main() -> None:
    """Main."""
    return app()


if __name__ == "__main__":
    main()
