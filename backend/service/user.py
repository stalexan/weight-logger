#!/usr/bin/env python3

""" This file contains the User and related classes. """

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
from datetime import datetime, timedelta
from http import HTTPStatus
import logging

# 3rd party imports
# pylint: disable=no-name-in-module
from getpass import getpass
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, Identity
from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Local imports
from .database import AlchemyBase, Database
from .entry import WeightLogEntryRow
from .error import WeightLogError
from .token import Token
from .util import determine_units_name, lookup_key

USERNAME_MAX_LEN: int = 32
PASSWORD_MAX_LEN: int = 128

ACCESS_TOKEN_ENCODE_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class UserRow(AlchemyBase): # type: ignore
    """ Data for a user persisted to the users table. """

    __tablename__ = "users"

    id = Column('id', Integer(), Identity(start=100, cycle=True), primary_key=True)
    username = Column(String(USERNAME_MAX_LEN), unique=True)
    metric = Column(Boolean())
    goal_weight = Column(Float())
    password = Column(String(PASSWORD_MAX_LEN))

    def __repr__(self) -> str:
        return f'[{self.id}, {self.username}, {self.metric}, {self.goal_weight}, {self.password}]'

class User(BaseModel):
    """ Weight log entry """

    id: int
    username: str
    metric: bool
    units_name: str
    goal_weight: float
    password: str

    def determine_units_name(self) -> None:
        """ Initialize User instance. """
        self.units_name = determine_units_name(self.metric)

    def flatten(self) -> list[int | str | bool | float]:
        """ Create list of attribute values. """
        return [
            self.id,
            self.username,
            self.units_name,
            self.goal_weight,
            self.password
            ]

def create_user_from_row(row: UserRow) -> User:
    """ Create a User from a UserRow. """

    user = User(
        id = row.id,
        username = row.username,
        metric = row.metric,
        units_name = "",
        goal_weight = row.goal_weight,
        password = row.password)
    user.determine_units_name()
    return user

def create_row_from_user(user: User) -> UserRow:
    """ Create a UserRow from a User. """

    # id is not set so that it will be generated automatically by database.
    return UserRow(
        username = user.username,
        metric = user.metric,
        goal_weight = user.goal_weight,
        password = user.password)

class UserManager():
    """ Manages users. """

    database: Database
    crypt_context: CryptContext

    # Token signing key
    token_key: str

    def __init__(self, database: Database):
        self.database = database
        self.crypt_context = CryptContext(schemes=["argon2"])

        # Lookup token signing key.
        EXPECTED_TOKEN_LEN: int = 64 # 64 chars * 4 bits = 256 bits. # pylint: disable=invalid-name
        self.token_key: str = lookup_key("TOKEN_KEY")
        if len(self.token_key) != EXPECTED_TOKEN_LEN:
            raise WeightLogError(f'TOKEN_KEY is {len(self.token_key)} chars long ' +
                f'versus {EXPECTED_TOKEN_LEN}.')

    @staticmethod
    def prompt_for_password() -> str:
        """ Prompt for user password. """

        password: str = getpass("New password: ")
        if len(password) == 0:
            raise WeightLogError('Password is blank')
        password2: str = getpass("Retype new password: ")
        if password != password2:
            raise WeightLogError('Passwords do not match')
        password2 = ""

        return password

    def check_and_hash_password(self, password: str) -> str:
        """ Check password length and return password hash. """

        # Check password complexity.
        # FUTURE-TODO: More checks.
        if len(password) == 0:
            raise WeightLogError('Password is empty')

        # Hash password.
        return self.crypt_context.hash(password)

    def add_user(self, username: str, metric: bool, goal_weight: float, password: str):
        """ Adds user to database. """

        # Check username length.
        if len(username) > USERNAME_MAX_LEN:
            raise WeightLogError(f'Maximum length for username is {USERNAME_MAX_LEN}')

        # Check and hash password.
        password = self.check_and_hash_password(password)

        # Add user.
        try:
            with self.database.Session.begin() as session:
                row: UserRow = UserRow(
                    username = username,
                    metric = metric,
                    goal_weight = goal_weight,
                    password = password)
                session.add(row)
        except IntegrityError as ex:
            raise WeightLogError(f'User {username} already exists') from ex
        except SQLAlchemyError as ex:
            raise WeightLogError(f'Unable to add user: {ex}') from ex

    def delete_user(self, username: str) -> None:
        """ Deletes user from database. """

        try:
            with self.database.Session.begin() as session:
                # Find user row to delete.
                user_row = session.query(UserRow).filter(UserRow.username == username).first()
                if user_row is None:
                    raise WeightLogError(f'User {username} not found')
                user_id = user_row.id

                # Delete entries for this user.
                rows = session.query(WeightLogEntryRow).filter(WeightLogEntryRow.user_id == user_id)
                for row in rows:
                    session.delete(row)

                # Delete user row.
                session.delete(user_row)
        except SQLAlchemyError as ex:
            raise WeightLogError(f'Unable to delete user: {ex}') from ex

    def change_password(self, user_id: int, new_password: str) -> None:
        """ Change user password. """

        # Check and hash password.
        new_password = self.check_and_hash_password(new_password)

        try:
            with self.database.Session.begin() as session:
                # Find user.
                row = session.query(UserRow).filter(UserRow.id == user_id).first()
                if row is None:
                    raise WeightLogError(f'User ID {user_id} not found')

                # Update password.
                row.password = new_password
        except SQLAlchemyError as ex:
            raise WeightLogError(f'Unable to change password: {ex}') from ex

    def update_user(self, authenticated_user_id: int, updated_user: User) -> User:
        """ Update user (username, metric, and goal_weight). """
        try:
            with self.database.Session.begin() as session:
                # Find user.
                row = session.query(UserRow).filter(UserRow.id == authenticated_user_id).first()
                if row is None:
                    raise WeightLogError(f'User ID {authenticated_user_id} not found')

                # Update username.
                new_username: str = updated_user.username
                if len(new_username) > 0 and new_username != row.username:
                    # Make sure username is not already in use.
                    if not self.get_user_from_username(new_username) is None:
                        raise WeightLogError(
                            f'Username {new_username} is already in use.',
                            status = HTTPStatus.BAD_REQUEST)

                    row.username = new_username

                # Update metric.
                row.metric = updated_user.metric
                updated_user.determine_units_name()

                # Round goal weight to nearest tenth.
                updated_user.goal_weight = round(updated_user.goal_weight, 1)

                # Update goal weight.
                row.goal_weight = updated_user.goal_weight

        except SQLAlchemyError as ex:
            raise WeightLogError(f'Unable to update user: {ex}') from ex

        return updated_user

    def get_user_from_username(self, username: str) -> User | None:
        """ Returns specified user. """
        try:
            with self.database.Session.begin() as session:
                # Find user row.
                row = session.query(UserRow).filter(UserRow.username == username).first()
                if row is None:
                    return None # User not found.

                # Return user
                return create_user_from_row(row)
        except SQLAlchemyError as ex:
            raise WeightLogError(f'Unable to retrieve user with username {username}: {ex}') from ex

    def get_user_from_id(self, user_id: int) -> User | None:
        """ Returns specified user. """

        try:
            with self.database.Session.begin() as session:
                # Find user row.
                row = session.query(UserRow).filter(UserRow.id == user_id).first()
                if row is None:
                    return None # User not found.

                # Return user
                return create_user_from_row(row)
        except SQLAlchemyError as ex:
            raise WeightLogError(f'Unable to retrieve user with id {user_id}: {ex}') from ex

    def get_users(self) -> list[User]:
        """ Returns all users. """

        try:
            with self.database.Session.begin() as session:
                # Find user rows.
                rows = session.query(UserRow)
                if rows is None:
                    raise WeightLogError('No users not found')

                # Return users
                return [create_user_from_row(row) for row in rows]
        except SQLAlchemyError as ex:
            raise WeightLogError(f'Unable to retrieve users: {ex}') from ex

    @staticmethod
    def create_credentials_error() -> WeightLogError:
        """ Create WeightLogError for credentials error. """
        return WeightLogError(
            message = "Could not validate credentials",
            status = HTTPStatus.UNAUTHORIZED)

    def authenticate_user(self, user: User, password: str) -> bool:
        """ Authenticate user. """
        return self.crypt_context.verify(password, user.password)

    def create_access_token(self, username: str, password: str) -> Token:
        """ Create access token for user authentication. """

        # Find user.
        user: User | None = self.get_user_from_username(username)
        if user is None:
            raise UserManager.create_credentials_error()

        # Authenticate user.
        if not self.authenticate_user(user, password):
            raise UserManager.create_credentials_error()

        # Create access token.
        expires = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        data = { "sub": str(user.id), "exp": expires }
        data_encoded = jwt.encode(data, self.token_key, algorithm=ACCESS_TOKEN_ENCODE_ALGORITHM)
        return Token(token=data_encoded)

    def get_user_from_token(self, token: str) -> User:
        """ Looks up user from authentication token passed in from client. """

        # Decode token
        try:
            payload = jwt.decode(token, self.token_key, algorithms=[ACCESS_TOKEN_ENCODE_ALGORITHM])
        except ExpiredSignatureError as ex:
            logging.info("Token has expired")
            raise UserManager.create_credentials_error() from ex
        except JWTError as ex:
            logging.warning("Failed to decode token %s", token)
            raise UserManager.create_credentials_error() from ex

        # Get user id string from token
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            logging.warning("Key sub not found in token %s", str(payload))
            raise UserManager.create_credentials_error()

        # Cast to user id to int
        try:
            user_id: int = int(user_id_str)
        except ValueError as ex:
            logging.warning("Failed to parse user id %s in token %s", user_id_str, str(payload))
            raise UserManager.create_credentials_error() from ex

        # Lookup user.
        user: User | None = self.get_user_from_id(user_id)
        if user is None:
            logging.warning("User %s not found for token %s", user_id, str(payload))
            raise UserManager.create_credentials_error()

        return user
