// LoginPanel component, for user login.

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
import { React, useState } from 'react';
import PropTypes from 'prop-types';

// Local imports
import { makeHttpRequest } from '../shared';
import PasswordInput from './PasswordInput';
import UserModal from './UserModal';

// CSS imports
import './LoginPanel.css';

export default function LoginPanel(props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isSignInButtonEnabled, setIsSignInButtonEnabled] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  // Modal dialog to sign up.
  const [signUpModalIsVisible, setSignUpModalIsVisible] = useState(false);
  const [signUpModalKey, setSignUpModalKey] = useState(0);

  function showSignUpModal() {
    // Show dialog.
    setSignUpModalKey((key) => key + 1); // Cause dialog to reinitialize.
    setSignUpModalIsVisible(true);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    try {
        // Get authentication token.
        document.body.style.cursor = 'wait';
        setIsSignInButtonEnabled(false);
        let response = await makeHttpRequest(
          "login", "token", "POST", 
          `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
          { 'Content-Type': 'application/x-www-form-urlencoded' }, null, null);

        // Handle response.
        if (response.ok) {
          // Save authentication token.
          let token = await response.json();
          props.saveToken(token);
        } else {
          throw Error("Incorrect username or password.");
        }
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      // Clean-up.
      document.body.style.cursor = 'default';
      setIsSignInButtonEnabled(true);
    }
  }

  // Is there an error message to display?
  let messageElement = errorMessage ? 
    <p className="alert alert-danger mb-4">{ errorMessage }</p> :
    null;

  return (
    <div id="login-panel-div" className="text-center">
      { messageElement }
      <form onSubmit={handleSubmit} autoComplete="on">
        <p className="h3 mb-3">Please sign in</p>
        <div className="form-floating">
          <input type="text" 
            className="form-control"
            id="username-input"
            placeholder="Username"
            autoComplete="on"
            onChange={event => setUsername(event.target.value)} />
          <label htmlFor="username-input">Username</label>
        </div>
        <PasswordInput id="password-input" label="Password" autoComplete="on"
            password={password} setPassword={setPassword} />
        <button name="signInButton" className="w-100 btn btn-lg btn-secondary" type="submit"
          disabled={!isSignInButtonEnabled}>Sign In</button>
      </form>
      <hr />
      <button className="w-100 btn btn-lg btn-secondary"
        onClick={() => { showSignUpModal(); }}>Sign Up</button>

      {/* Modal dialog to sign up. */}
      <UserModal
        isForSettings={false}
        show={signUpModalIsVisible}
        modalKey={signUpModalKey}
        onHide={ () => setSignUpModalIsVisible(false) } />
    </div>
  )
}

LoginPanel.propTypes = {
  saveToken: PropTypes.func,
}
