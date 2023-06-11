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
import pathlib
import time
from typing import Annotated, Optional, Self, TypedDict

import mylog

# SPDX-License-Identifier: GPL-3.0-or-later
import typer

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

app = typer.Typer(no_args_is_help=True)


class _Settings(TypedDict):
    what_to_quiet: WhatToQuiet
    config: Config


SETTINGS: _Settings


class Timer:
    def __init__(self) -> None:
        self.start = None
        self.time = None

    def __enter__(self) -> Self:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        assert self.start  # noqa: S101
        self.time = time.perf_counter() - self.start


def run_linter(linter: Linter, paths: list[pathlib.Path]) -> bool:
    with logger.ctxmgr:
        with Timer() as linter_timer:
            success = linter.run(paths, SETTINGS["what_to_quiet"])
            if not success:
                logger.error(
                    f"Could not run linter {linter.packages}!"
                    " Please see the linter's output for more"
                    " details."
                )
                if SETTINGS["config"].fail_fast:
                    raise typer.Exit(1)
                return False
        logger.info(f"Ran linter in {linter_timer.time} seconds")
        return True


def linter_first(paths: list[pathlib.Path]) -> bool:
    logger.info("Running first linters")
    return_value = True
    with logger.ctxmgr:
        with Timer() as linters_timer:
            for linter in SETTINGS["config"].get_first_linters():
                logger.info(f"Running first linter {linter.packages}")
                success = run_linter(linter, paths)
                if not success:
                    return_value = False
        logger.info(f"Ran all (first) linters in {linters_timer.time} seconds")
        return return_value


def run_formatter(
    formatter: Formatter, paths: list[pathlib.Path], format_: bool
) -> bool:
    with logger.ctxmgr:
        with Timer() as formatter_timer:
            if format_:
                success = formatter.run_format(
                    paths, SETTINGS["what_to_quiet"]
                )
            else:
                success = formatter.run_check(paths, SETTINGS["what_to_quiet"])

            if not success:
                logger.error(f"Could not run formatter {formatter.packages}!")
                if SETTINGS["config"].fail_fast:
                    raise typer.Exit(1)
                return False
        logger.info(f"Ran formatter in {formatter_timer.time} seconds")
        return True


def formatter(format_: bool, paths: list[pathlib.Path]) -> bool:
    logger.info("Running formatters")
    return_value = True
    with logger.ctxmgr:
        with Timer() as formatters_timer:
            for formatter in SETTINGS["config"].formatters:
                logger.info(f"Running formatter {formatter.packages}")
                success = run_formatter(formatter, paths, format_)
                if not success:
                    return_value = False
        logger.info(f"Ran all formatters in {formatters_timer.time} seconds")
        return return_value


def linter_other(paths: list[pathlib.Path]) -> bool:
    logger.info("Running other linters")
    return_value = True
    with logger.ctxmgr:
        with Timer() as linters_timer:
            for linter in SETTINGS["config"].get_other_linters():
                logger.info(f"Running other linter {linter.packages}")
                success = run_linter(linter, paths)
                if not success:
                    return_value = False
        logger.info(f"Ran all other linters in {linters_timer.time} seconds")
        return return_value


def run(paths: list[pathlib.Path], format_: bool) -> None:
    with Timer() as all_timer:
        success = True
        if linter_first(paths) is False:
            success = False
        if formatter(format_, paths) is False:
            success = False
        if linter_other(paths) is False:
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


def quiet_callback(value: bool) -> None:
    if value:
        logger.threshold += 10


def version_callback(value: bool) -> None:
    if value:
        print(__version__)
        raise typer.Exit(0)


@app.command("format")
def format_(
    paths: Annotated[list[pathlib.Path], typer.Argument(exists=True)]
) -> None:
    """Format your code and run linters."""
    run(paths, True)


@app.command()
def check(
    paths: Annotated[list[pathlib.Path], typer.Argument(exists=True)]
) -> None:
    """Check the formatting of your code and run linters."""
    run(paths, False)


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
    quiet_commands: Annotated[
        bool,
        typer.Option(
            help="If passed the output of the formatters and linters will be"
            " hidden.",
        ),
    ] = False,
    quiet_pip: Annotated[
        bool,
        typer.Option(
            help="If passed the output of pip will be hidden.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="If passed the logger's threshold will be set to debug.",
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
) -> None:
    if verbose:
        if quiet:
            logger.critical("Verbose and quiet are mutually exclusive!")
            raise typer.Exit(2)
        logger.threshold = mylog.Level.debug
    if config:
        config_ = (
            get_config_pyproject(config)
            if config.name == "pyproject.toml"
            else get_config_dot_lemming(config.parent)
        )
    else:
        config_ = get_config(".")
    global SETTINGS  # noqa: PLW0603
    SETTINGS = _Settings(
        what_to_quiet=WhatToQuiet(commands=quiet_commands, pip=quiet_pip),
        config=config_,
    )


if __name__ == "__main__":
    app()
