// App component

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

// React imports
import { useEffect, React, useState } from "react";

// Local imports
import { makeHttpRequest } from './shared';
import Navbar from "./components/Navbar";
import ContainerPanel from "./components/ContainerPanel";
import useToken from './useToken';

// CSS imports
import './App.css';
 
export default function App() {
  // Authentication
  const { token, saveToken } = useToken();
  const [user, setUser] = useState(null);

  // Navigation
  let PANEL_NAME_TABLE = "table"
  const [visiblePanel, setVisiblePanel] = useState(PANEL_NAME_TABLE);

  function forgetUser() {
    saveToken(null);
    setUser(null);
  }

  function saveTokenAndInit(token) {
    saveToken(token)

    // Display table panel after login.
    setVisiblePanel(PANEL_NAME_TABLE)
  }

  // Fetch user details from server.
  useEffect(() => {
    async function getUser() {
      // Get user.
      try {
        // Fetch user.
        let response = await makeHttpRequest(
          "get user", "user", "GET", null,
          {}, token, forgetUser);

        // Handle response.
        if (response.ok) {
          // Display user.
          let userReturned = await response.json();
          setUser(userReturned);
        }
      } catch (error) {
        console.log(error.message);
      }
    }

    // Get user details if user has logged in.
    if (token)
       getUser(); // Lets useEffect() return and getUser() is run later asynchronously.
  }, [token]);

  return (
    <main>
      <Navbar id="navbar" setVisiblePanel={setVisiblePanel}
        token={token} saveToken={saveTokenAndInit}
        user={user} setUser={setUser} forgetUser={forgetUser} />
      <ContainerPanel id="container-panel" visiblePanel={visiblePanel} 
        token={token} saveToken={saveTokenAndInit} user={user} forgetUser={forgetUser} />
    </main>
  );
}
