#!/usr/bin/env python3
#
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

""" Custom exception for wl-admin """

class AdminError(Exception):
    """
    Custom exception for reporting Weight Log admin errors.
    """

    message: str
    return_code: int # For command line.

    def __init__(self, message: str, return_code = -1) -> None:
        super().__init__()
        self.message = message
        self.return_code = return_code

    def __str__(self) -> str:
        return self.message
