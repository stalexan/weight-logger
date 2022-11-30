// useToken() hook for managing JWT authentication token.

/* Copyright 2022 Sean Alexandre
 *
 * This file is part of Weight Logger.
 *
 * Weight Logger is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option)
 * any later version.
 *
 * Weight Logger is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * Weight Logger. If not, see <https://www.gnu.org/licenses/>.
 */

import { useState } from 'react';

export default function useToken() {
  let TOKEN_KEY = 'token';

  const getToken = () => {
    // Retrieve authorization token from local storage. The token returned from
    // the backend after logging in is saved to localStorage as a JSON string
    // that is an object with a token property that holds the token; e.g. "{
    // token: 'test123' }"
    const tokenString = localStorage.getItem(TOKEN_KEY);
    const tokenObject = JSON.parse(tokenString);
    return tokenObject?.token
  };
   
  const [token, setToken] = useState(getToken());

  const saveToken = tokenObject => {
    if (tokenObject) {
        // Save token to localStorage and to application state.
        localStorage.setItem(TOKEN_KEY, JSON.stringify(tokenObject)); // Local storage
        setToken(tokenObject.token);                                  // Application state
    } else {
        // Delete token from localStorage and application state.
        localStorage.removeItem(TOKEN_KEY); // Local storage
        setToken(null);                     // Application state
    }
  };

  return { token, saveToken };
}
