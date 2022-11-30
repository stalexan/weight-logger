#!/usr/bin/env python3

""" This file contains common code for database access. """

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

# Stanard library imports
import logging
import os
from typing import Any

# 3rd party imports
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_SERIALIZABLE
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Local imports
from .error import WeightLogError
from .util import lookup_env_var, lookup_key

# Initialize SQLAlchemy
AlchemyBase = declarative_base() # type: ignore

# Schema version number
SCHEMA_NAME_MAX_LEN: int = 32
SCHEMA_VER_MAJOR: int = 1
SCHEMA_VER_MINOR: int = 1

class SchemaRow(AlchemyBase): # type: ignore
    """ Simple one row table to track schema version number for any future migrations. """

    __tablename__ = "schema"

    name = Column(String(SCHEMA_NAME_MAX_LEN), primary_key=True)
    major_ver = Column(Integer)
    minor_ver = Column(Integer)

    def __repr__(self) -> str:
        return f'[{self.name}, {self.major_ver}, {self.minor_ver}]'

class Database:
    """ Database management. """

    # Database name.
    db_name: str

    # Credentials.
    postgres_password: str
    db_user: str
    db_password: str

    # Engine holds SQLAlchemy database connection.
    engine: Any

    # Session creates sessions. The variable name is capitalized since it's
    # acting more as a class to create instances. See "Create session maker"
    # comment below, and reference to sample code.
    Session: Any

    def __init__(self):

        # Determine database name.
        candidate: str | None = lookup_env_var("DB_NAME")
        self.db_name = candidate if not candidate is None else "weight_log"

        # Lookup database connection info.
        self.postgres_password = lookup_key("POSTGRES_PASSWORD")
        self.db_user = f"{self.db_name}_user"
        self.db_password = lookup_key("DB_PASSWORD")

        # Create database if it doesn't exist.
        db_exists = self.create_database()

        # Connect SQLAlchemy to database.
        try:
            # Connect to database.
            # pylint: disable=line-too-long
            engine_url: str = f'postgresql://{self.db_user}:{self.db_password}@database/{self.db_name}'
            self.engine = create_engine(
                engine_url,
                execution_options = { "isolation_level": "REPEATABLE READ" })
            self.engine.connect()

            # Create session maker.
            # See <https://docs.sqlalchemy.org/en/14/orm/session_basics.html#using-a-sessionmaker>
            # pylint: disable=invalid-name
            self.Session = sessionmaker(bind=self.engine)

            # Create tables.
            if not db_exists:
                logging.info("Creating tables in %s", self.db_name)
                AlchemyBase.metadata.create_all(self.engine)
                self.create_schema_row()

        except SQLAlchemyError as ex:
            raise WeightLogError('Unable to start database session for database ' + \
                f'{self.db_name} user {self.db_user}: {str(ex)}') from ex

    def create_schema_row(self):
        """ Add schema row to record schema version. """
        try:
            with self.Session.begin() as session:
                # Add schema row.
                row: SchemaRow = SchemaRow(
                    name = "Weight Log",
                    major_ver = SCHEMA_VER_MAJOR,
                    minor_ver = SCHEMA_VER_MINOR)
                session.add(row)
        except SQLAlchemyError as ex:
            raise WeightLogError('Unable to create schema row') from ex

    def open_direct_connection(self, isolation_level, as_admin_user: bool = False):
        """ Connect directly to postgres using psycopg2 database, verus through SQLAlchemy. """
        try:
            # Prepare credentials.
            user: str
            password: str
            dbname: str
            if as_admin_user:
                user = 'postgres'
                password = self.postgres_password
                dbname = ''
            else:
                user = self.db_user
                password = self.db_password
                dbname = f"dbname='{self.db_name}'"

            # Connect.
            conn = psycopg2.connect(f"host='database' {dbname} user='{user}' password='{password}'")
            conn.set_isolation_level(isolation_level)
            return conn
        except psycopg2.Error as ex:
            raise WeightLogError('Could not connect to postgres database: ' + \
                str(ex)) from ex

    def create_database(self) -> bool:
        """ Create database if it doesn't exist.

        Returns
        -------
        bool
            True if database already exists, and did not need to be created.

        """

        # Connect to database. Use ISOLATION_LEVEL_AUTOCOMMIT for "CREATE DATABASE" to work.
        conn = self.open_direct_connection(ISOLATION_LEVEL_AUTOCOMMIT, as_admin_user=True)
        try:
            # Does application database exist?
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS result FROM pg_database " + \
                        f"WHERE datname='{self.db_name}';")
                    db_exists: bool = len(cur.fetchall()) == 1
            except psycopg2.Error as ex:
                raise WeightLogError(
                    f'Unable to determine if {self.db_name} exists: {str(ex)}') from ex

            # Create application database and database user.
            if not db_exists:
                logging.info('Database %s was not found', self.db_name)
                with conn.cursor() as cur:
                    try:
                        # Create database.
                        logging.info('Creating database %s', self.db_name)
                        cur.execute(f"CREATE DATABASE {self.db_name};")

                        # Create user.
                        logging.info('Creating database user %s', self.db_user)
                        cur.execute(f"CREATE USER {self.db_user} WITH PASSWORD " + \
                            f"'{self.db_password}';")
                        cur.execute(f"GRANT ALL ON DATABASE {self.db_name} TO {self.db_user};")
                    except psycopg2.Error as ex:
                        raise WeightLogError(f'Unable to create {self.db_name}: {str(ex)}') from ex
        finally:
            # Close pyscopg2 connection
            conn.close()

        return db_exists

    def restore(self, filename: str) -> None:
        """ Restore database using SQL from filename. """

        conn = self.open_direct_connection(ISOLATION_LEVEL_SERIALIZABLE, as_admin_user=False)
        execute_failed: bool = False
        try:
            with open(filename, "r", encoding="utf-8") as restore_file:
                with conn.cursor() as cur:
                    # Delete existing data.
                    logging.info('Deleting existing data for restore')
                    cur.execute('DELETE FROM entries;')
                    cur.execute('DELETE FROM users;')
                    cur.execute('DELETE FROM schema;')

                    # Restore.
                    logging.info('Restoring')
                    try:
                        cur.execute(restore_file.read())
                    except psycopg2.Error:
                        execute_failed = True
                        raise

                    # Commit changes.
                    conn.commit()
        except OSError as ex:
            raise WeightLogError(f'Unable to read file {filename}: {str(ex)}') from ex
        except psycopg2.Error as ex:
            message = 'Unable to restore database.'
            if execute_failed:
                message = message + f'\nThe SQL in {os.path.basename(filename)} ' + \
                    f'failed to run.\nSQL error: {str(ex)}'
            else:
                message = message + f'\n{str(ex)}'
            raise WeightLogError(message) from ex
        finally:
            # Close pyscopg2 connection
            conn.close()
