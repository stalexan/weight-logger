#!/usr/bin/env python3

""" Admin functions shared by backend and wl-admin. """

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
from argparse import ArgumentParser

def config_parser_for_add_user(parser: ArgumentParser) -> None:
    """ Add command line arguments needed for add user. """
    parser.add_argument('-e', '--english', action='store_true',
        help='Use English units (lb) for weight (lb). Default is metric (kg).')
    parser.add_argument('-g', '--goal', type=float, required=True, help='Goal weight.')
    parser.add_argument("username")
