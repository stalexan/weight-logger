#!/usr/bin/env python3

""" cbr3 service """

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
import asyncio
from asyncio import Lock
import datetime
from enum import Enum
from http import HTTPStatus
import logging
from io import BytesIO
import os
from re import I
import sys
import time
from typing import Any, List

# 3rd party imports
from fastapi import FastAPI, HTTPException, Path
from matplotlib import pyplot
import sqlalchemy
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Local imports
from .database import Database
from .entry import AlchemyBase, WeightLogEntry, WeightLogEntryRow
from .entry import create_entry_from_row, create_entries_from_csv, create_row_from_entry
from .wls_logging import setup_loguru
from .error import WeightLogError
from .token import Token
from .user import User, UserManager
from .user import UserRow # Needed for users table to be created.
from .util import determine_units_name, load_keys

def log_http_exception(ex: HTTPException) -> None:
    """ Log the HTTPException that is about to be raised. """
    message: str = f"Raising HTTPException: {ex.detail}"
    if ex.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        logging.warning(message)
    else:
        logging.info(message)

def create_http_ex(message: str, status: HTTPStatus) -> HTTPException:
    """ Create HTTPException from string. """
    ex = HTTPException(status, detail=message)
    log_http_exception(ex)
    return ex

def create_http_ex_from_weight_log_error(ex: WeightLogError) -> HTTPException:
    """ Create HTTPException from WeightLogError. """
    http_ex = HTTPException(ex.status, detail=str(ex))
    log_http_exception(http_ex)
    return http_ex

class Service:
    """ Weight Log Service """

    database: Database
    user_manager: UserManager
    plot_lock: Lock

    def __init__(self, use_loguru: bool = False):
        # Initialize logging.
        if use_loguru:
            setup_loguru()

        # Load keys.
        load_keys()

        # Initialize database connection.
        self.database: Database = Database()

        # Initialize user manager.
        self.user_manager: UserManager = UserManager(self.database)

        # Initialize plot lock.
        self.plot_lock = Lock()

    def login(self, username: str, password: str) -> Token:
        """ Create authentication token for user login. """
        logging.info("User %s logging in", username)
        try:
            token: Token = self.user_manager.create_access_token(username, password)
            logging.info("User %s logged in", username)
            return token
        except WeightLogError as ex:
            raise create_http_ex_from_weight_log_error(ex) from ex

    def get_user_from_token(self, token: str) -> User:
        """ Looks up user from authentication token passed in from client. """
        try:
            return self.user_manager.get_user_from_token(token)
        except WeightLogError as ex:
            raise create_http_ex_from_weight_log_error(ex) from ex

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        """ Change user password. """
        try:
            # Check current password.
            if not self.user_manager.authenticate_user(user, current_password):
                raise create_http_ex("Current password is incorrect.", HTTPStatus.BAD_REQUEST)

            # Change password.
            self.user_manager.change_password(user.id, new_password)
        except WeightLogError as ex:
            raise create_http_ex_from_weight_log_error(ex) from ex

    def add_user(self, new_user: User) -> None:
        """ Add new user. """
        try:
            self.user_manager.add_user(new_user)
        except WeightLogError as ex:
            raise create_http_ex_from_weight_log_error(ex) from ex

    def delete_user(self, username: str) -> None:
        """ Delete user. """
        try:
            self.user_manager.delete_user(username)
        except WeightLogError as ex:
            raise create_http_ex_from_weight_log_error(ex) from ex

    def update_user(self, authenticated_user_id: int, updated_user: User) -> User:
        """ Update user (username, metric, and goal_weight). """
        try:
            return self.user_manager.update_user(authenticated_user_id, updated_user)
        except WeightLogError as ex:
            raise create_http_ex_from_weight_log_error(ex) from ex

    def get_entries(self, user: User) -> list[WeightLogEntry]:
        """ Return entries for specified user, sorted by date. """

        # Load rows for this user.
        with self.database.Session.begin() as session:
            rows = session.query(WeightLogEntryRow) \
                .filter(WeightLogEntryRow.user_id == user.id ) \
                .order_by(WeightLogEntryRow.date).all()

            entries: list[WeightLogEntry] = [
                create_entry_from_row(row, user.metric) for row in rows]

        return entries

    def get_entry_from_entry_id(self, entry_id: int) -> WeightLogEntry | None:
        """ Gets specified entry. """

        try:
            with self.database.Session.begin() as session:
                # Find entry row.
                row = session.query(WeightLogEntryRow). \
                    filter(WeightLogEntryRow.id == entry_id).first()
                if row is None:
                    return None # User not found.

                # Return WeightLogEntry
                return create_entry_from_row(row, row.metric)
        except SQLAlchemyError as ex:
            raise WeightLogError(f'Unable to retrieve entry with id {entry_id}: {ex}') from ex

    @staticmethod
    def query_for_entry_by_user_and_date(session, user_id: int, entry_date: datetime.date):
        """ Query for entry row by user and date. """
        return session.query(WeightLogEntryRow) \
            .filter(WeightLogEntryRow.user_id == user_id) \
            .filter(WeightLogEntryRow.date == entry_date) \
            .first()

    def get_entry_from_user_id(self, user_id: int,
        entry_date: datetime.date) -> WeightLogEntry | None:
        """ Gets specified entry. """

        try:
            with self.database.Session.begin() as session:
                # Find entry row.
                row = Service.query_for_entry_by_user_and_date(session, user_id, entry_date)
                if row is None:
                    return None # Entry not found.

                # Return WeightLogEntry
                return create_entry_from_row(row, row.metric)
        except SQLAlchemyError as ex:
            raise WeightLogError(f'Unable to retrieve entry with user id {user_id} and ' + \
                f'date {entry_date}: {ex}') from ex

    def get_entries_csv(self, user: User) -> str:
        """ Return entries for specified user formatted as CSV. """

        # Lookup entries for this user.
        entries: list[WeightLogEntry] = self.get_entries(user)

        # Format entries as CSV.
        newline: str = '\n'
        entries_csv = newline.join([entry.format_as_csv() for entry in entries])

        return WeightLogEntry.create_csv_header() + newline + entries_csv

    async def get_entries_graph(self, user: User) -> BytesIO:
        """ Return entries graphic. """

        # Prepare graph entries.
        entries: list[WeightLogEntry] = self.get_entries(user)
        dates: list[datetime.date] = [entry.date for entry in entries]
        weights: list[float] = [entry.weight for entry in entries]

        # Plot entries.
        buffer = BytesIO()
        if len(entries) > 0:
            # Lock since pylot has internal state that shouldn't be shared
            # between threads.
            async with self.plot_lock:
                # Plot entries.
                pyplot.figure(figsize=(8, 5), dpi=300) # Configure plot size.
                pyplot.plot(dates, weights) # Draw line graph.
                pyplot.scatter(dates, weights, s=10) # Add dots for each entry.

                # Plot goal.
                pyplot.plot(
                    [dates[0], dates[len(dates) - 1]],
                    [user.goal_weight, user.goal_weight],
                    linestyle = 'dashed',
                    color = 'green',
                    linewidth = 2)

                # Finish formatting.
                pyplot.xlabel('Date') # Set x-axis label.
                pyplot.ylabel(f'Weight ({user.units_name})') # Set y-axis label.
                pyplot.gcf().autofmt_xdate() # Pretty print dates on x-axis.
                pyplot.tight_layout() # Reduce margins.

                # Save to buffer.
                pyplot.savefig(buffer, format="png")
                buffer.seek(0)

        # Return buffer.
        return buffer

    def add_entry(self, entry: WeightLogEntry) -> None:
        """ Add WeightLogEntryRow to entries table. """

        try:
            # Round weight to nearest 10th.
            entry.weight = round(entry.weight, 1)

            with self.database.Session.begin() as session:
                # Add row for new entry.
                row: WeightLogEntryRow = create_row_from_entry(entry)
                session.add(row)

                # Get generated id to return to caller, through entry.
                session.flush()
                session.refresh(row)
                entry.id = row.id
                row_str: str = str(row)
        except IntegrityError as ex:
            logging.warning(str(ex))
            raise create_http_ex(
                f'Entry for date {entry.date} already exists.',
                HTTPStatus.BAD_REQUEST) from ex
        except SQLAlchemyError as ex:
            raise create_http_ex(
                f'Unable to add entry: {ex}',
                HTTPStatus.INTERNAL_SERVER_ERROR) from ex

        logging.info("Added row %s", row_str)

    def add_entries_from_csv(self, user_id: int, csv_bytes: bytes) -> None:
        """ Add entries from csv file. """

        # Decode bytes.
        try:
            csv: str = csv_bytes.decode("utf-8")
        except UnicodeError as ex:
            raise create_http_ex(
                'Unable to read string from CSV file.',
                HTTPStatus.BAD_REQUEST) from ex

        # Parse.
        entries: List[WeightLogEntry] = create_entries_from_csv(user_id, csv)

        # Save entries.
        try:
            with self.database.Session.begin() as session:
                for entry in entries:
                    # Is there already an entry for this date?
                    row = Service.query_for_entry_by_user_and_date(
                        session, entry.user_id, entry.date)
                    is_add: bool = row is None

                    if is_add:
                        # Add new entry.
                        row = create_row_from_entry(entry)
                    else:
                        # Update existing entry, if an update is needed.
                        if row.weight != entry.weight or row.metric != entry.is_metric:
                            row.weight = entry.weight
                            row.metric = entry.is_metric
                        else:
                            continue

                    # Log.
                    op_desc: str = "Added" if is_add else "Updated"
                    logging.info("%s row %s", op_desc, str(row))

                    # Save to transaction.
                    session.add(row)
        except SQLAlchemyError as ex:
            raise create_http_ex(
                f'Unable to save entry: {ex}',
                HTTPStatus.INTERNAL_SERVER_ERROR) from ex

    def update_entry(self, entry: WeightLogEntry) -> None:
        """ Update WeightLogEntryRow. """

        try:
            with self.database.Session.begin() as session:
                # Find row to update.
                row = session.query(WeightLogEntryRow) \
                    .filter(WeightLogEntryRow.id == entry.id) \
                    .first()
                if row is None:
                    raise create_http_ex(
                        f'Entry {entry.id} not found.',
                        HTTPStatus.BAD_REQUEST)

                # Update row.
                row.date = entry.date
                row.weight = entry.weight
                row.metric = entry.is_metric
                row_str = str(row)
                session.add(row)
        except IntegrityError as ex:
            raise create_http_ex(
                f'Entry for date {entry.date} already exists.',
                HTTPStatus.BAD_REQUEST) from ex
        except SQLAlchemyError as ex:
            raise create_http_ex(
                f'Unable to add entry: {ex}',
                HTTPStatus.INTERNAL_SERVER_ERROR) from ex

        logging.info("Update row %s", row_str)

    def delete_entry(self, user_id: int, entry_date: datetime.date) -> None:
        """ Delete WeightLogEntryRow with given date. """

        try:
            with self.database.Session.begin() as session:
                # Find row to delete.
                row = session.query(WeightLogEntryRow) \
                    .filter(WeightLogEntryRow.user_id == user_id) \
                    .filter(WeightLogEntryRow.date == entry_date) \
                    .first()
                if row is None:
                    raise create_http_ex(
                        f'Date {entry_date} not found.',
                        HTTPStatus.BAD_REQUEST)
                row_str = str(row)

                # Delete row.
                session.delete(row)
        except SQLAlchemyError as ex:
            raise create_http_ex(
                f'Unable to delete entry {row}: {ex}',
                HTTPStatus.INTERNAL_SERVER_ERROR) from ex

        logging.info("Deleted row %s", row_str)

    def delete_all_entries(self, user_id: int) -> None:
        """ Delete all entries for the specified user. """

        try:
            with self.database.Session.begin() as session:
                # Find rows to delete.
                rows = session.query(WeightLogEntryRow) \
                    .filter(WeightLogEntryRow.user_id == user_id)

                # Delete rows.
                if not rows is None:
                    for row in rows:
                        session.delete(row)
        except SQLAlchemyError as ex:
            raise create_http_ex(
                f'Unable to delete entries for user {user_id}: {ex}',
                HTTPStatus.INTERNAL_SERVER_ERROR) from ex

        logging.info("Deleted all entries for user %d", user_id)

    def has_data(self) -> bool:
        """ Returns True if database has data. """
        return len(self.user_manager.get_users()) > 0
