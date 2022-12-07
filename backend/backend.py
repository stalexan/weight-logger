#!/usr/bin/env python3

""" Run weight-log-service """

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
#import logging
import sys

# 3rd party imports
from fastapi import Depends, FastAPI, File, Path, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.responses import StreamingResponse

# Local imports
from service import Service
from service.entry import WeightLogEntry
from service.error import WeightLogError
from service.token import Token
from service.user import User

__version__: str = "1.0.1"

# Intialize service.
try:
    service = Service(use_loguru = True)
except WeightLogError as ex:
    print(f'ERROR: {ex}')
    sys.exit(ex.return_code)

# Define authentication endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Start server.
app = FastAPI()

# Configure CORS sharing
origins = [
    '*',
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """ Authenticate user and return token. """
    return service.login(form_data.username, form_data.password)

def get_user_from_token(token: str = Depends(oauth2_scheme)) -> User:
    """ Look up user from authentication token passed in from client. """
    return service.get_user_from_token(token)

@app.post("/user/")
async def add_user(new_user: User) -> None:
    """ Add user. """
    service.add_user(new_user)

@app.get("/user/", response_model=User)
async def get_user(
    user: User = Depends(get_user_from_token)) -> User:
    """ Return current user. """
    user.password = ""
    return user

@app.put("/user/", response_model=User)
async def update_user(
    updated_user: User,
    authenticated_user: User = Depends(get_user_from_token)) -> User:
    """ Update User. """
    return service.update_user(authenticated_user.id, updated_user)

@app.put("/password/")
async def change_password(
    current_password: str,
    new_password: str,
    user: User = Depends(get_user_from_token)) -> None:
    """ Change user password. """
    return service.change_password(user, current_password, new_password)

@app.post("/entry/")
async def add_entry(
    entry: WeightLogEntry,
    user: User = Depends(get_user_from_token)) -> int:
    """ Add WeightLogEntry to database. """
    entry.user_id = user.id
    service.add_entry(entry)
    return 0 if entry.id is None else entry.id

@app.put("/entry/")
async def update_entry(
    entry: WeightLogEntry,
    user: User = Depends(get_user_from_token)) -> None:
    """ Update WeightLogEntry. """
    entry.user_id = user.id
    service.update_entry(entry)

@app.delete("/entry/{entry_date}")
async def delete_entry(
    entry_date: datetime.date = Path(..., title="Date of entry to delete"),
    user: User = Depends(get_user_from_token)) -> None:
    """ Delete entry for given date. """
    service.delete_entry(user.id, entry_date)

@app.delete("/entries/")
async def delete_all_entries(user: User = Depends(get_user_from_token)) -> None:
    """ Delete all entries. """
    service.delete_all_entries(user.id)

@app.get("/entries/", response_model=list[WeightLogEntry])
async def get_entries(
    user: User = Depends(get_user_from_token)) -> list[WeightLogEntry]:
    """ Get entries. """
    return service.get_entries(user)

@app.get("/entries/csv")
async def get_entries_csv(
    user: User = Depends(get_user_from_token)) -> Response:
    """ Get entries. """
    return Response(
        content = service.get_entries_csv(user),
        media_type = "text/csv")

@app.post("/entries/csv")
async def add_entries_from_csv(
    file: bytes = File(),
    user: User = Depends(get_user_from_token)) -> None:
    """ Add entries that have been uploaded from a CSV file. """
    service.add_entries_from_csv(user.id, file)

@app.get("/entries/graph")
async def get_entries_graph(
    user: User = Depends(get_user_from_token)) -> StreamingResponse:
    """ Get entries graph. """
    return StreamingResponse(
        await service.get_entries_graph(user),
        media_type="image/png")
