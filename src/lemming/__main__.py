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
import argparse
import pathlib
import time
from typing import List, Literal, Tuple

import mylog
from confz import ConfZFileSource
from typing_extensions import Self

from . import __version__, config, logger

PARSER = argparse.ArgumentParser(
    description="Lemming is a tool for formatting and linting code.",
    prog="lemming",
)
PARSER.add_argument(
    "task",
    choices=("format", "check"),
    help="format the code with the formatters, or check the code with the"
    " formatters (linters will be ran in all cases)",
)
PARSER.add_argument(
    "path",
    action="append",
    type=pathlib.Path,
    help="the paths (files and directories) to check. These arguments will be"
    " passed to the formatters and linters as arguments where {path} is used",
)
PARSER.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="log more information",
)
PARSER.add_argument(
    "-q",
    "--quiet",
    action="count",
    help="log less information. Can be passed multiple times",
    default=0,
)
PARSER.add_argument(
    "--quiet-commands",
    action="store_true",
    help="don't let ran commands write to stdout and stderr. Use --quiet-pip"
    " to quiet `pip`",
)
PARSER.add_argument(
    "--quiet-pip",
    action="store_true",
    help="don't let pip write to stdout and stderr. Use --quiet-commands"
    " to quiet the formatters and linters",
)
PARSER.add_argument(
    "-c",
    "--config",
    default=None,
    help="the config file to use. If passed all other config files will be"
    " ignored",
)
PARSER.add_argument(
    "-V",
    "--version",
    action="version",
    help="print the program's version and exit",
    version=__version__,
)


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


def parse_args() -> argparse.Namespace:
    return PARSER.parse_args()


def _get_paths_to_check(args: argparse.Namespace) -> List[pathlib.Path]:
    paths_to_check = args.path
    logger.debug(f"{paths_to_check = !r}")
    if not (
        isinstance(paths_to_check, list)
        and all(isinstance(path, pathlib.Path) for path in paths_to_check)
    ):
        PARSER.error("invalid paths")
    return paths_to_check


def _set_logger(args: argparse.Namespace) -> None:
    verbose = args.verbose
    quiet = args.quiet
    logger.debug(f"{verbose = !r}")
    logger.debug(f"{quiet = !r}")
    if verbose and quiet:
        PARSER.error("cannot have both verbose and quiet")
    if quiet >= 4:
        logger.handlers = []
    elif quiet == 3:
        logger.threshold = mylog.Level.critical
    elif quiet == 2:
        logger.threshold = mylog.Level.error
    elif quiet == 1:
        logger.threshold = mylog.Level.warning
    if verbose:
        logger.threshold = mylog.Level.debug
    logger.debug(f"{logger.threshold = !r}")


def _get_what_to_quiet(args: argparse.Namespace) -> config.WhatToQuiet:
    return config.WhatToQuiet(args.quiet_commands, args.quiet_pip)


def _get_config_file(args: argparse.Namespace) -> pathlib.Path:
    config_file = args.config
    logger.debug(f"{config_file = !r}")
    if config_file is not None:
        config_file = pathlib.Path(config_file).resolve()
        if not config_file.exists():
            PARSER.error(f"config file {config_file} doesn't exist")
        if not config_file.is_file():
            PARSER.error(f"config file {config_file} isn't a file")
    logger.debug(f"{config_file = !r}")
    return config_file


def _get_configuration_configprovided(
    config_file: pathlib.Path,
) -> config.Config:
    logger.debug("config_file is provided, using that")
    return config.Config(ConfZFileSource(file=config_file))


def _get_configuration_confignotprovided() -> config.Config:
    logger.debug("config_file is None, searching for it")
    return config.get_config(".")


def _get_configuration(args: argparse.Namespace) -> config.Config:
    # sourcery skip: assign-if-exp, inline-immediately-returned-variable
    config_file = _get_config_file(args)

    if config_file:
        return _get_configuration_configprovided(config_file)
    return _get_configuration_confignotprovided()


def get_configuration() -> (
    Tuple[
        config.Config,
        List[pathlib.Path],
        config.WhatToQuiet,
        Literal["format", "check"],
    ]
):
    logger.debug("Parsing args")
    with logger.ctxmgr:
        args = parse_args()

        paths_to_check = _get_paths_to_check(args)

        _set_logger(args)

        configuration = _get_configuration(args)

        what_to_quiet = _get_what_to_quiet(args)

        task = args.task
    return configuration, paths_to_check, what_to_quiet, task


def _formatters(
    configuration: config.Config,
    paths_to_check: List[pathlib.Path],
    what_to_quiet: config.WhatToQuiet,
    task: Literal["format", "check"],
) -> bool:
    logger.info(f"Running formatters ({task})")
    with logger.ctxmgr:
        with Timer() as formatters_timer:
            for formatter in configuration.formatters:
                logger.info(f"Running formatter {formatter.packages} ({task})")
                with logger.ctxmgr:
                    with Timer() as formatter_timer:
                        if task == "format":
                            success = formatter.run_format(
                                paths_to_check, what_to_quiet
                            )
                        elif task == "check":
                            success = formatter.run_check(
                                paths_to_check, what_to_quiet
                            )
                        else:
                            PARSER.error(f"unknown task: {task!r}")

                        if not success:
                            logger.error(
                                "Could not run formatter"
                                f" {formatter.packages}!"
                            )
                            if configuration.fail_fast:
                                PARSER.exit(1, "\nFAILED!\n")
                            else:
                                return False
                    logger.info(
                        f"Ran formatter in {formatter_timer.time} seconds"
                    )
        logger.info(f"Ran all formatters in {formatters_timer.time} seconds")
        return True


def _run_linter(
    configuration: config.Config,
    paths_to_check: List[pathlib.Path],
    what_to_quiet: config.WhatToQuiet,
    linter: config.Linter,
) -> bool:
    with logger.ctxmgr:
        with Timer() as linter_timer:
            success = linter.run(paths_to_check, what_to_quiet)
            if not success:
                logger.error(
                    f"Could not run linter {linter.packages}!"
                    " Please see the linter's output for more"
                    " details."
                )
                if configuration.fail_fast:
                    PARSER.exit(1, "\nFAILED!\n")
                else:
                    return False
        logger.info(f"Ran linter in {linter_timer.time} seconds")
        return True


def _linters_first(
    configuration: config.Config,
    paths_to_check: List[pathlib.Path],
    what_to_quiet: config.WhatToQuiet,
) -> bool:
    logger.info("Running (first) linters")
    return_value = True
    with logger.ctxmgr:
        with Timer() as linters_timer:
            for linter in configuration.get_first_linters():
                logger.info(f"Running (first) linter {linter.packages}")
                success = _run_linter(
                    configuration, paths_to_check, what_to_quiet, linter
                )
                if not success:
                    return_value = False
        logger.info(f"Ran all (first) linters in {linters_timer.time} seconds")
        return return_value


def _linters_other(
    configuration: config.Config,
    paths_to_check: List[pathlib.Path],
    what_to_quiet: config.WhatToQuiet,
) -> bool:
    logger.info("Running (other) linters")
    return_value = True
    with logger.ctxmgr:
        with Timer() as linters_timer:
            for linter in configuration.get_other_linters():
                logger.info(f"Running (other) linter {linter.packages}")
                success = _run_linter(
                    configuration, paths_to_check, what_to_quiet, linter
                )
                if not success:
                    return_value = False
        logger.info(f"Ran all (other) linters in {linters_timer.time} seconds")
        return return_value


def main() -> None:
    with Timer() as all_timer:
        with Timer() as config_timer:
            (
                configuration,
                paths_to_check,
                what_to_quiet,
                task,
            ) = get_configuration()
        logger.debug(
            f"Got configuration {configuration} in {config_timer.time} seconds"
        )

        linter_first_success = _linters_first(
            configuration, paths_to_check, what_to_quiet
        )

        formatter_success = _formatters(
            configuration, paths_to_check, what_to_quiet, task
        )

        linter_other_success = _linters_other(
            configuration, paths_to_check, what_to_quiet
        )

        if not all(
            (linter_first_success, formatter_success, linter_other_success)
        ):
            logger.error(
                "Failed, due to one or more linters/formatters failing."
            )
            logger.error("HINT: Set fail_fast=true to disable this behavior")
            PARSER.exit(1, "\nFAILED\n")

    logger.info(
        f"Successfully ran all formatters and linters in {all_timer.time}"
        " seconds with no errors. Good job!"
    )
    if not what_to_quiet.pip:
        logger.info(
            "*!*!* HINT: Do you get overwhelmed by pip's output? Consider"
            " using the --quiet-pip argument for Lemming !*!*!"
        )


if __name__ == "__main__":
    main()
