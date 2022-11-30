#!/usr/bin/env python3

""" This file contains the WeightLogEntry class and related classes. """

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
import datetime
from typing import List, Tuple

# 3rd party imports
# pylint: disable=no-name-in-module
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Identity, UniqueConstraint
from sqlalchemy import Boolean, Date, Float, Integer

# Local imports
from .database import AlchemyBase
from .error import WeightLogError
from .util import convert_to_english, convert_to_metric, determine_units_name

KG_STR: str = determine_units_name(True)
LB_STR: str = determine_units_name(False)

class WeightLogEntryRow(AlchemyBase): # type: ignore
    """ Data for weight log entry persisted to the entries table. """

    __tablename__ = "entries"

    id = Column('id', Integer(), Identity(start=100, cycle=True), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date())
    weight = Column(Float())
    metric = Column(Boolean())

    # User and date are unique.
    uc1 = UniqueConstraint(user_id, date, name='uc1')

    def __repr__(self) -> str:
        return f'[{self.id}, {self.user_id}, {self.date}, {self.weight}, {self.metric}]'


class WeightLogEntry(BaseModel):
    """ Weight log entry """

    id: int | None
    user_id: int
    date: datetime.date
    weight: float
    is_metric: bool

    @staticmethod
    def create_csv_header() -> str:
        """ Return CSV header. """
        return 'Date, Weight, Units'

    def format_as_csv(self) -> str:
        """ Return values formatted for CSV. """
        weight_formatted = f"{self.weight:,.1f}" if self.is_metric else f"{self.weight:,.0f}"
        return f'{self.date}, {weight_formatted}, {determine_units_name(self.is_metric)}'

def create_entry_from_row(row: WeightLogEntryRow, metric: bool) -> WeightLogEntry:
    """ Create a WeightLogEntry from a WeightLogEntryRow. """

    # Convert units.
    weight = row.weight
    if metric != row.metric:
        if metric:
            weight = convert_to_metric(weight)
        else:
            weight = convert_to_english(weight)

    return WeightLogEntry(
        id = row.id,
        user_id = row.user_id,
        date = row.date,
        weight = weight,
        is_metric = metric)

def parse_csv_header(csv: str) -> Tuple[List[str], int]:
    """ Parse and remove CSV header. """

    # Split CSV into lines.
    lines: List[str] = csv.split('\n')

    # Parse header.
    header_line = lines[0].strip()
    if len(header_line) == 0:
        raise WeightLogError('No column headers found.')
    headers: List[str] = header_line.split(',')

    # Check header.
    expected_headers: List[str] = ['Date', 'Weight', 'Units']
    col_count: int = len(expected_headers)
    if len(headers) != col_count:
        raise WeightLogError(f'Expected {col_count} columns but found {len(headers)}.')
    for header in enumerate(zip(expected_headers, headers)):
        column_no = header[0] + 1
        expected: str = header[1][0]
        actual: str = header[1][1].strip()
        if expected != actual:
            raise WeightLogError(
                f'Expected "{expected}" for column {column_no} header but found "{actual}".')

    # Remove header
    lines.pop(0)

    return (lines, col_count)

def parse_csv_date(value: str, line_no: int) -> datetime.date:
    """ Parse date from CSV file. """
    try:
        return datetime.datetime.strptime(value.strip(), "%Y-%m-%d")
    except ValueError as ex:
        raise WeightLogError(f'Unable to parse date "{value}" on line {line_no}.') from ex

def parse_csv_weight(value: str, line_no: int) -> float:
    """ Parse weight from CSV file. """
    try:
        return float(value.strip())
    except ValueError as ex:
        raise WeightLogError(f'Unable to parse weight "{value}" on line {line_no}.') from ex

def parse_csv_units(value: str, line_no: int) -> bool:
    """ Parse units from CSV file. """
    value = value.strip()
    if value == KG_STR:
        return True
    if value == LB_STR:
        return False
    raise WeightLogError(f'Unable to parse units "{value}" on line {line_no}.')

def create_entries_from_csv(user_id: int, csv: str) -> List[WeightLogEntry]:
    """ Parse CSV file contents in to entries. """

    # Parse header.
    lines: List[str]
    col_count: int
    (lines, col_count) = parse_csv_header(csv)

    # Parse entries.
    entries: List[WeightLogEntry] = []
    for line in enumerate(lines):
        # Find values on this line.
        line_no: int = line[0] + 2
        values_str = line[1].strip()
        if len(values_str) == 0:
            continue
        values = values_str.split(',')
        if len(values) != col_count:
            raise WeightLogError(
                f'Expected {col_count} values on line {line_no} but found {len(values)}.')

        # Parse values.
        date: datetime.date = parse_csv_date(values[0], line_no)
        weight: float = parse_csv_weight(values[1], line_no)
        is_metric: bool = parse_csv_units(values[2], line_no)

        # Create entry.
        entry: WeightLogEntry = WeightLogEntry(id = None, user_id = user_id,
            date = date, weight = weight, is_metric = is_metric)
        entries.append(entry)

    return entries

def create_row_from_entry(entry: WeightLogEntry) -> WeightLogEntryRow:
    """ Create a WeightLogEntryRow from a WeightLogEntry. """

    # id is not set so that it will be generated automatically by database.
    return WeightLogEntryRow(
        user_id = entry.user_id,
        date = entry.date,
        weight = entry.weight,
        metric = entry.is_metric)
