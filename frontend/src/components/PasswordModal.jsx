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

// Modal dialog to change password.
export default function PasswordModal(props) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [retypePassword, setRetypePassword] = useState("");
  const [showPasswordsMustMatchMessage, setShowPasswordsMustMatchMessage] = useState(false);
  const [isOkButtonEnabled, setIsOkButtonEnabled] = useState(true);
  const [serverErrorMessage, setServerErrorMessage] = useState("")

  // Close dialog.
  function closeModal() {
    props.onHide();
  }

  useEffect(() => {
    // Initialize dialog.
    setCurrentPassword("");
    setNewPassword("");
    setRetypePassword("");
    setShowPasswordsMustMatchMessage(false);
    setIsOkButtonEnabled(true);
    setServerErrorMessage("");
  }, [props.modalKey]);

  // Create "passwords must match" message HTML.
  let retypeElem;
  if (showPasswordsMustMatchMessage)
    // Show "must match" message.
    retypeElem = 
      <div>
        <input type="password" required className="form-control is-invalid" id="retypePassword" aria-describedby="retypePasswordFeedback"
           value={retypePassword} onChange={(event) => {setRetypePassword(event.target.value);}} />
        <div id="retypePasswordFeedback" className="invalid-feedback">Passwords must match.</div>
      </div>
  else
    // No message needed.
    retypeElem = <input type="password" required className="form-control" id="retypePassword"
      value={retypePassword} onChange={(event) => {setRetypePassword(event.target.value);}} />

  // Create server error message HTML.
  let serverErrorMessageElem;
  if (serverErrorMessage.length > 0) {
    serverErrorMessageElem = <div className="alert alert-danger" role="alert">{serverErrorMessage}</div>;
  }

  // Handle OK click.
  async function handleOnSubmit(event) {
    // Skip <form> default behavior. 
    event.preventDefault();

    // Check that passwords match.
    if (newPassword != retypePassword) {
      setShowPasswordsMustMatchMessage(true);
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
      setServerErrorMessage(error.message);
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
            <label htmlFor="currentPassword" className="form-label">Current Password</label>
            <input type="password" required className="form-control" id="currentPassword"
              value={currentPassword} onChange={(event) => {setCurrentPassword(event.target.value);}} />
          </div>
          <div className="mb-3">
            <label htmlFor="newPassword" className="form-label">New Password</label>
            <input type="password" required className="form-control" id="newPassword"
              value={newPassword} onChange={(event) => {setNewPassword(event.target.value);}} />
          </div>
          <div className="mb-3">
            <label htmlFor="retypePassword" className="form-label">Retype New Password</label>
            {retypeElem}
          </div>
        </form>
        {serverErrorMessageElem}
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
