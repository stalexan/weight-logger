// ContainerPanel component, to display table and graph panels.

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
import { React, useState } from "react";
import PropTypes from 'prop-types';
 
// Local imports
import EntryGraphPanel from "./EntryGraphPanel";
import EntryTablePanel from "./EntryTablePanel";
import LoginPanel from "./LoginPanel";

// CSS imports
import './ContainerPanel.css';
 
export default function ContainerPanel(props) {
  // Weight entries.
  const [entries, setEntries] = useState([]);

  // Display login prompt if user is not logged in.
  if (!props.token) {
    return (
      <div id="container-panel-div">
        <LoginPanel saveToken={props.saveToken} />
      </div>
    );
  }

  // Otherwise, if user is logged in, display app.
  let panelElem = null;
  switch (props.visiblePanel) {
    case "table":
        panelElem = <EntryTablePanel token={props.token}
            entries={entries} setEntries={setEntries}
            user={props.user} forgetUser={props.forgetUser} />;
        break;
    case "graph":
        panelElem = <EntryGraphPanel token={props.token}
            entries={entries} user={props.user} forgetUser={props.forgetUser} />;
  }
  return (
    <div id="container-panel-div">
      {panelElem}
    </div>
  );
}

ContainerPanel.propTypes = {
  forgetUser: PropTypes.func,
  saveToken: PropTypes.func,
  token: PropTypes.string,
  user: PropTypes.object,
  visiblePanel: PropTypes.string,
}
