// Navbar component, for navigation header.

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

// 3rd party imports
import NavDropdown from 'react-bootstrap/NavDropdown';

// Local imports
import { makeHttpRequest } from '../shared';
import ConfirmModal from './ConfirmModal';
import PasswordModal from './PasswordModal';
import UserModal from './UserModal';

// CSS imports
import "bootstrap/dist/css/bootstrap.css";
import './Navbar.css';

export default function Navbar(props) {
  // Modal dialog to change password.
  const [passwordModalIsVisible, setPasswordModalIsVisible] = useState(false);
  const [passwordModalKey, setPasswordModalKey] = useState(0);

  // Modal dialog to change other user settings.
  const [settingsModalIsVisible, setSettingsModalIsVisible] = useState(false);
  const [settingsModalKey, setSettingsModalKey] = useState(0);

  // Modal dialog to confirm account deletion.
  const [confirmDeleteAccountModalIsVisible, setConfirmDeleteAccountModalIsVisible] = useState(false);

  function showPasswordModal() {
    // Show dialog.
    setPasswordModalKey((key) => key + 1); // Cause dialog to reinitialize.
    setPasswordModalIsVisible(true);
  }

  function showSettingsModal() {
    // Show dialog.
    setSettingsModalKey((key) => key + 1); // Cause dialog to reinitialize.
    setSettingsModalIsVisible(true);
  }

  async function deleteAccount() {
    try {
      // Delete current user.
      document.body.style.cursor = 'wait';
      let response = await makeHttpRequest(
          "delete user", 'user', "DELETE", null,
          {}, props.token, props.forgetUser);

      // Handle response.
      if (response.ok) {
        // Delete user token.
        props.forgetUser();
      }
    } catch (error) {
      document.body.style.cursor = 'default';

      // Log error.
      console.log(error.message);
    } finally {
      // Clean-up.
      document.body.style.cursor = 'default';
      setConfirmDeleteAccountModalIsVisible(false);
    }
  }

  // Create navigation links and dialogs if user has logged in.
  let navLinks;
  let modals;
  if (props.user) {
    navLinks = 
      <ul className="navbar-nav wl-navbar-nav">
        <li className="nav-item">
          <a className="wl-nav-link" onClick={() => props.setVisiblePanel("table")} >Table</a>
        </li>
        <li className="nav-item">
          <a className="wl-nav-link" onClick={() => props.setVisiblePanel("graph")} >Graph</a>
        </li>
        <NavDropdown id="wl-nav-dropdown" title={`${props.user.username}`} menuVariant="dark">
           <NavDropdown.Item onClick={() => showSettingsModal() }>Settings…</NavDropdown.Item>
           <NavDropdown.Item onClick={() => showPasswordModal() }>Change Password…</NavDropdown.Item>
           <NavDropdown.Item onClick={() => setConfirmDeleteAccountModalIsVisible(true) }>Delete Account…</NavDropdown.Item>
           <NavDropdown.Divider />
           <NavDropdown.Item onClick={() => { props.forgetUser(); }}>Logout</NavDropdown.Item>
        </NavDropdown>
      </ul>;
    modals = 
      <div>
        {/* Modal dialog to change user settings. */}
        <UserModal
          isForSettings={true}
          show={settingsModalIsVisible}
          modalKey={settingsModalKey}
          onHide={ () => setSettingsModalIsVisible(false) }
          token={props.token}
          user={props.user}
          setUser={props.setUser}
          forgetUser={props.forgetUser} />
   
        {/* Modal dialog to change password. */}
        <PasswordModal 
          show={passwordModalIsVisible} 
          modalKey={passwordModalKey}
          onHide={ () => setPasswordModalIsVisible(false) }
          token={props.token}
          forgetUser={props.forgetUser} />

        {/* Modal dialog to confirm account deletion. */}
        <ConfirmModal 
          title="Delete Account"
          message="Delete the current user's account, and all weight log entries for the account?"
          show={confirmDeleteAccountModalIsVisible}
          onOK={deleteAccount}
          onCancel={() => { setConfirmDeleteAccountModalIsVisible(false); }} />
      </div>;
  }

  return (
    <nav className="navbar navbar-expand-sm navbar-dark wl-navbar">
      <div className="navbar-brand wl-navbar-brand">Weight Logger</div>
      { navLinks }
      { modals }
    </nav>
 );
}

Navbar.propTypes = {
  forgetUser: PropTypes.func,
  setUser: PropTypes.func,
  setVisiblePanel: PropTypes.func,
  token: PropTypes.string,
  user: PropTypes.object,
}
