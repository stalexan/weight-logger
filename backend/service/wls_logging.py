#!/usr/bin/env python3

""" Configures logging """

# Copyright 2022 Sean Alexandre
#
# This file is part of Weight Logger.
#
# Weight Logger is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Weight Logger is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# Weight Logger. If not, see <https://www.gnu.org/licenses/>.

# Standard library imports
import logging
import os
import sys

# 3rd party imports
from loguru import logger

LOG_LEVEL = logging.getLevelName(os.environ.get("LOG_LEVEL", "DEBUG"))
JSON_LOGS = os.environ.get("JSON_LOGS", "0") == "1"

class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages and send to Loguru sink.
    From loguru documentation here: <https://pypi.org/project/loguru/>
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller that generated logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_loguru():
    # pylint: disable=line-too-long
    """
    Setup loguru logging

    Code is from: [Unify Python logging for a Gunicorn/Uvicorn/FastAPI
    application](https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/#uvicorn-only-version)
    """

    # Intercept everything at the root logger.
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(LOG_LEVEL)

    # Remove every other logger's handlers # and propagate to root logger.
    # pylint error: "Instance of 'RootLogger' has no 'loggerDict' member (no-member)"
    # pylint: disable=no-member
    # pylint: disable=consider-iterating-dictionary
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Configure loguru.
    logger.configure(handlers=[{"sink": sys.stdout, "serialize": JSON_LOGS}])
