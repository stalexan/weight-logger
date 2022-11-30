#!/usr/bin/env python3

""" Utility methods for Weight Log. """

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
import os

# Local imports
from .error import WeightLogError

keys: dict[str,str] = {}

def load_keys_from_file(file_name: str) -> None:
    # pylint: disable=line-too-long
    """
    Load keys from file.

    Entries are stored as environment variables, but not
    loaded as environment variables for better security, from
    [Why you shouldn't use ENV variables for secret data](<https://blog.diogomonica.com/2017/03/27/why-you-shouldnt-use-env-variables-for-secret-data/).
    """

    try:
        # Read keys file.
        with open(file_name, "r", encoding="utf-8") as config_file:
            contents: str = config_file.read()

        quote_chars = ['\"', '\'']
        for (i, line) in enumerate(contents.split('\n')):
            # Parse line into name and value.
            line = line.strip()
            if len(line) == 0:
                continue
            parts: list[str] = line.split("=")
            if len(parts) != 2:
                raise WeightLogError(f'Unexpected key entry on line {i + 1} of {file_name}')
            key_name: str = parts[0].strip()
            key_value: str = parts[1].strip()

            # Remove any outer quotes from value.
            for quote_char in quote_chars:
                if len(key_value) > 1 and \
                    key_value.startswith(quote_char) and \
                    key_value.endswith(quote_char):
                    key_value = key_value[1 : len(key_value) - 1]
                    break

            # Save key
            keys[key_name] = key_value
    except OSError as ex:
        raise WeightLogError(f'Could not load keys from {file_name}') from ex

def load_keys() -> None:
    """ Load keys. """
    load_keys_from_file('/keys/keys-backend.env')
    load_keys_from_file('/keys/keys-database.env')

def lookup_key(key_name: str) -> str:
    """ Lookup key. """
    key_value = keys.get(key_name)
    if key_value is None:
        raise WeightLogError(f'Key {key_name} not found')
    return key_value

def lookup_env_var(env_var: str) -> str | None:
    """ Lookup environment variable and return as string. """
    env_var_value = os.getenv(env_var)
    if env_var_value is None:
        return None
    return env_var_value

def lookup_env_var_int(env_var: str) -> int:
    """ Lookup environment variable and return as integer. """
    env_var_value_str = lookup_env_var(env_var)
    if env_var_value_str is None:
        env_var_value_str = ''
    try:
        env_var_value = int(env_var_value_str)
        return env_var_value
    except ValueError as ex:
        raise WeightLogError(f'Could not convert environment variable {env_var} ' + \
            'to an integer') from ex

KG_PER_LB: float = 0.45359237

def convert_to_metric(lbs: float) -> float:
    """ Convert lbs to kg. """
    return round(lbs * KG_PER_LB, 1)

def convert_to_english(kilograms: float) -> float:
    """ Convert kg to lbs. """
    return round(kilograms/ KG_PER_LB, 0)

def determine_units_name(metric: bool) -> str:
    """ Determine units name. """
    return "kg" if metric else "lb"
