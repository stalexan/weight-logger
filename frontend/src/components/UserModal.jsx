// UserModal component, for changing user settings.

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
import { convertUnits, makeHttpRequest } from '../shared';

// Modal dialog to create and edit user.
export default function UserModal(props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState();
  const [metric, setMetric] = useState(true);
  const [goalWeight, setGoalWeight] = useState(0);
  const [isOkButtonEnabled, setIsOkButtonEnabled] = useState(true);
  const [serverErrorMessage, setServerErrorMessage] = useState("")

  useEffect(() => {
    // Initialize dialog.
    if (props.user) {
        setUsername(props.user.username);
        setMetric(props.user.metric);
        setGoalWeight(props.user.goal_weight);
    } else {
        setUsername("");
        setMetric(true);
        setGoalWeight(80);
    }
    setIsOkButtonEnabled(true);
    setServerErrorMessage("");
  }, [props.modalKey]);

  // Close dialog.
  function closeModal() {
    props.onHide();
  }

  async function handleUpdateUser() {
    // Were updates made?
    let updatesWereMade = 
        username != props.user.username ||
        metric != props.user.metric ||
        goalWeight != props.user.goal_weight;
    if (!updatesWereMade) {
      closeModal();
      return true;
    }

    // Create updated user.
    let updatedUser = {...props.user};
    updatedUser.username = username;
    updatedUser.metric = metric;
    updatedUser.goal_weight = goalWeight;
    
    let success = false;
    try {
      // Apply updates.
      document.body.style.cursor = 'wait';
      setIsOkButtonEnabled(false);
      let response = await makeHttpRequest(
        "update user", "user", "PUT", JSON.stringify(updatedUser),
        { 'Content-Type': 'application/json' }, props.token, props.forgetUser);

      // Handle response
      if (response.ok) {
        success = true;
        updatedUser = await response.json();
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

    if (success) {
        props.setUser(updatedUser);
        closeModal();
    }
  }

  async function handleSignUp() {
    let success = false;
    try {
      // Add new user.
      document.body.style.cursor = 'wait';
      setIsOkButtonEnabled(false);
      /*
      let newUser = {
        id: 0,
        username: username,
        metric: metric,
        units_name: "",
        goal_weight: goalWeight,
        password: password,
      };
      let newUser = {
        "id": 0,
        "username": "string",
        "metric": true,
        "units_name": "string",
        "goal_weight": 0,
        "password": "string"
      };
      */
      let newUser = {
        "id": 0,
        "username": username,
        "metric": metric,
        "units_name": "",
        "goal_weight": goalWeight,
        "password": password 
      };
      let response = await makeHttpRequest(
        "add user", "user", "POST", JSON.stringify(newUser),
        { 'Content-Type': 'application/json' }, null, null);

      // Handle response
      success = response.ok;
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
  }

  // Handle OK click.
  async function handleOnSubmit(event) {
    // Skip <form> default behavior. 
    event.preventDefault();

    return props.isForSettings ?
        await handleUpdateUser() :
        await handleSignUp();
  }

  function handleRetypePasswordChange(event) {
    // Read new value.
    const target = event.target;
    let value = target.value;

    // Validate.
    if (value === password) {
        target.setCustomValidity('');
    } else {
        target.setCustomValidity('Passwords must match.');
    }
  }

  function handleGoalWeightChange(event) {
    // Read new value.
    const target = event.target;
    let value = target.value;

    // Validate.
    let number = Number(value);
    if (isNaN(number) || number < 0.05) {
        // Comparison is done to 0.05 since weight entries are rounded to nearest tenth.
        target.setCustomValidity('Goal weight must be a number greater than 0.');
    } else {
        target.setCustomValidity('');
    }

    // Save update.
    setGoalWeight(value);
  }

  // Create server error message HTML.
  let serverErrorMessageElem;
  if (serverErrorMessage.length > 0) {
    serverErrorMessageElem = <div className="alert alert-danger" role="alert">{serverErrorMessage}</div>;
  }

  function onUnitsChange(event) {
    // Convert units.
    let toMetric = (event.target.value === 'true');
    console.log("goalWeight: " + goalWeight);
    let newGoalWeight = convertUnits(metric, toMetric, goalWeight);
    console.log("newGoalWeight: " + newGoalWeight);

    // Save new values.
    setMetric(toMetric);
    setGoalWeight(newGoalWeight);
  }

  // Create password fields if this dialog is for sign up.
  let passwordDiv = null;
  if (!props.isForSettings) {
    passwordDiv = 
      <div>
        <div className="mb-3">
          <label htmlFor="password-input">Password</label>
          <input type="password" 
            required
            className="form-control" 
            id="password-input" 
            placeholder="Password"
            onChange={event => setPassword(event.target.value)} />
        </div>
        <div className="mb-3">
          <label htmlFor="password-input">Retype password</label>
          <input type="password" 
            required
            className="form-control" 
            id="retype-password-input" 
            placeholder="Retype password"
            onChange={handleRetypePasswordChange} />
        </div>
      </div>;
  }

  return (  
    <Modal show={props.show} onHide={() => { closeModal(); }} animation={false} size="sm">
      <Modal.Header closeButton>
        <Modal.Title>{props.isForSettings ? "Settings" : "Sign Up"}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <form id="userModalForm" onSubmit={handleOnSubmit}>
          <div className="mb-3">
            <label htmlFor="username" className="form-label">Username</label>
            <input type="text" required className="form-control" id="username"
              value={username} onChange={(event) => {setUsername(event.target.value);}} />
          </div>
          {passwordDiv}
          <div className="mb-3">
            <label htmlFor="units" className="form-label">Units</label>
            <div>
              <select id="units" className="form-select"
                value={metric} onChange={onUnitsChange}>
                <option value="true">Metric (kg)</option>
                <option value="false">English (lb)</option>
              </select>
            </div>
          </div>
          <div className="mb-3">
            <label htmlFor="goalWeight" className="form-label">Goal Weight</label>
            <input type="text" className="form-control" id="goalWeight" required
                value={goalWeight} onChange={handleGoalWeightChange} />
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
          document.forms["userModalForm"].requestSubmit(); 
        }}>
          Ok
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

UserModal.propTypes = {
  forgetUser: PropTypes.func,
  isForSettings: PropTypes.bool,
  modalKey: PropTypes.number,
  onHide: PropTypes.func,
  setUser: PropTypes.func,
  show: PropTypes.bool,
  token: PropTypes.string,
  user: PropTypes.object,
}
