// PasswordModal component, for changing a user password.

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
import { React, useEffect, useState } from "react";
import PropTypes from 'prop-types';

// 3rd party imports
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';

// Local imports
import { makeHttpRequest } from '../shared';
import PasswordInput from './PasswordInput';

// Modal dialog to change password.
export default function PasswordModal(props) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [retypePassword, setRetypePassword] = useState("");
  const [passwordsMatch, setPasswordsMatch] = useState(true);
  const [isOkButtonEnabled, setIsOkButtonEnabled] = useState(true);
  const [errorMessage, setErrorMessage] = useState("")

  // Close dialog.
  function closeModal() {
    props.onHide();
  }

  useEffect(() => {
    // Initialize dialog.
    setCurrentPassword("");
    setNewPassword("");
    setRetypePassword("");
    setPasswordsMatch(true);
    setIsOkButtonEnabled(true);
    setErrorMessage("");
  }, [props.modalKey]);

  // Create error message HTML.
  let errorMessageElem;
  let errorMessageId = "error-message";
  if (errorMessage)
    errorMessageElem = <div id={errorMessageId} className="alert alert-danger" role="alert">{errorMessage}</div>;

  // Handle OK click.
  async function handleOnSubmit(event) {
    // Skip <form> default behavior. 
    event.preventDefault();

    // Check that passwords match.
    if (newPassword == retypePassword) {
      setPasswordsMatch(true);
    } else {
      setPasswordsMatch(false);
      setErrorMessage("Passwords must match.");
      return false; // Let user correct error.
    }

    let success = false;
    try {
      // Change password.
      document.body.style.cursor = 'wait';
      setIsOkButtonEnabled(false);
      let urlSuffix = 'password/?' +
        `current_password=${encodeURIComponent(currentPassword)}&` +
        `new_password=${encodeURIComponent(newPassword)}`;
      let response = await makeHttpRequest(
        "change password", urlSuffix, "PUT", null,
        {}, props.token, props.forgetUser);

      // Handle response
      if (response.ok) {
        success = true;
      } else if (response.status == 401) {
        // Client sent an invalid token. Close dialog to display login prompt.
        closeModal();
      }
    } catch (error) {
      // Log error.
      console.log(error.message);

      // Display error in modal dialog.
      setErrorMessage(error.message);
    } finally {
      // Clean-up.
      document.body.style.cursor = 'default';
      setIsOkButtonEnabled(true);
    }

    if (success)
        closeModal();

    return success;
  }

  return (  
    <Modal show={props.show} onHide={() => { closeModal(); }} animation={false} size="sm">
      <Modal.Header closeButton>
        <Modal.Title>Change Password</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <form id="passwordForm" onSubmit={handleOnSubmit}>
          <div className="mb-3">
            <PasswordInput id="current-password-input" label="Current Password" 
              password={currentPassword} setPassword={setCurrentPassword} />
          </div>
          <div className="mb-3">
            <PasswordInput id="new-password-input" label="New Password" 
              password={newPassword} setPassword={setNewPassword} />
          </div>
          <div className="mb-3">
            <PasswordInput id="retype-password-input" label="Retype New Password" 
              password={retypePassword} setPassword={setRetypePassword}
              errorMessageId={passwordsMatch ? "" : errorMessageId} />
          </div>
        </form>
        {errorMessageElem}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={() => { closeModal(); }}>
          Cancel
        </Button>
        <Button variant="primary" disabled={!isOkButtonEnabled} onClick={() => {
            // Validate form. This cascades to form onSubmit if fields validate.
            document.forms["passwordForm"].requestSubmit(); 
        }}>
          Ok
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

PasswordModal.propTypes = {
  forgetUser: PropTypes.func,
  modalKey: PropTypes.number,
  onHide: PropTypes.func,
  show: PropTypes.bool,
  token: PropTypes.string,
}
