// EntryModal component, for dialog to add and edit entries.

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

// Modal dialog to create and edit entries.
export default function EntryModal(props) {
  const [isEdit, setIsEdit] = useState(false);
  const [title, setTitle] = useState("");
  const [entryDate, setEntryDate] = useState("")
  const [entryWeight, setEntryWeight] = useState("")
  const [isMetric, setIsMetric] = useState(true);
  const [isOkButtonEnabled, setIsOkButtonEnabled] = useState(true);
  const [errorMessage, setErrorMessage] = useState("")

  function handleEntryDateChange(event) {
    setEntryDate(event.target.value);
  }

  // Update weight for entry modal dialog, and validate.
  function handleEntryWeightChange(event) {
    // Validate new value.
    let newValue = event.target.value;
    let number = Number(newValue);
    if (isNaN(number) || number < 0.05) {
        // Comparison is done to 0.05 since numbers are rounded to nearest tenth.
        event.target.setCustomValidity('Weight must be a number greater than 0.');
    } else {
        event.target.setCustomValidity('');
    }

    // Save new value.
    setEntryWeight(newValue);
  }

  function handleUnitsChange(event) {
    let newIsMetric = (event.target.value === 'true');
    setIsMetric(newIsMetric);
  }

  useEffect(() => {
    // Initialize dialog.
    if (props.entry == null) {
      // This is an add.
      setIsEdit(false);
      setTitle("Add Entry");

      // Use today's date as initial default.
      if (entryDate.length == 0)
        setEntryDate(new Date().toISOString().split('T')[0]);

      // Default to preferred units.
      setIsMetric(props.user.metric);
    } else {
      // This is an edit.
      setIsEdit(true);
      setTitle("Edit Entry");

      // Initialize dialog with values from Entry to edit.
      setEntryDate(props.entry.date);
      setEntryWeight(props.entry.weight);
      setIsMetric(props.entry.is_metric);
    }
    setIsOkButtonEnabled(true);
    setErrorMessage("");
  }, [props.entry, props.user, props.modalKey]);

  // Save entry modal dialog changes.
  async function handleOk(event) {
    // Skip <form> default behavior. 
    event.preventDefault();

    try {
      // Create entry to pass to server.
      let updatedEntry;
      if (isEdit) {
        // This is an edit. Clone entry being edited.
        updatedEntry = {
            ...props.entry,
            date: entryDate,
            weight: Number(entryWeight),
            is_metric: isMetric,
        };
      } else {
        // This is an add. Create new entry.
        updatedEntry = {
          id: 0,
          user_id: 0, // Don't care since user id comes from authentication token,
                      // but is needed for OpenAPI call to recognize this as an 
                      // instance of User.
          date: entryDate,
          weight: Number(entryWeight),
          is_metric: isMetric,
        };
      }

      // Pass entry to backend.
      document.body.style.cursor = 'wait';
      setIsOkButtonEnabled(false);
      let desc = isEdit ? "update entry" : "add entry";
      let method = isEdit ? "PUT" : "POST";
      let response = await makeHttpRequest(
        desc, "entry", method, JSON.stringify(updatedEntry),
        { 'Content-Type': 'application/json' }, props.token, props.forgetUser);

      // Handle response
      if (response.ok) {
        // Record new id if this was an add.
        if (!isEdit) {
          let new_id = await response.text();
          updatedEntry.id = Number(new_id);
        }

        // Convert units if units entered are not the same as units displayed in table.
        if (updatedEntry.is_metric != props.user.metric) {
          updatedEntry.weight = convertUnits(
            updatedEntry.is_metric, props.user.metric, updatedEntry.weight);
          updatedEntry.is_metric = props.user.metric;
        }

        // Update table.
        props.onUpdateEntries(isEdit, updatedEntry);
      }

      // Close dialog.
      props.onHide();
    } catch (error) {
      document.body.style.cursor = 'default';

      // Log error.
      console.log(error.message);

      // Display error message to user.
      setErrorMessage(error.message);
    } finally {
      // Clean-up.
      document.body.style.cursor = 'default';
      setIsOkButtonEnabled(true);
    }
  }

  // Create error message HTML.
  let errorMessageElem;
  if (errorMessage.length > 0) {
    errorMessageElem = <div className="alert alert-danger" role="alert">{errorMessage}</div>;
  }

  return (
    <Modal show={props.show} onHide={props.onHide} animation={false} size="sm">
      <Modal.Header closeButton>
        <Modal.Title>{title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <form id="entryModalForm" onSubmit={handleOk}>
          <div className="mb-3">
            <label htmlFor="date" className="form-label">Date</label>
            <input type="date" className="form-control" id="date" required
                value={entryDate} onChange={handleEntryDateChange} />
          </div>
          <div className="mb-3">
            <label htmlFor="weight" className="form-label">Weight</label>
            <input type="text" className="form-control" id="weight" required
                value={entryWeight} onChange={handleEntryWeightChange} />
          </div>
          <div className="mb-3">
            <label htmlFor="units" className="form-label">Units</label>
            <div>
              <select id="units" className="form-select"
                value={isMetric} onChange={handleUnitsChange}>
                <option value="true">kg</option>
                <option value="false">lb</option>
              </select>
            </div>
          </div>
        </form>
        {errorMessageElem}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={props.onHide}>
          Cancel
        </Button>
        <Button variant="primary" disabled={!isOkButtonEnabled} onClick={() => {
            // Validate form. This cascades to form onSubmit if fields validate.
            document.forms["entryModalForm"].requestSubmit(); 
        }}>
          Ok
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

EntryModal.propTypes = {
  entry: PropTypes.object,
  forgetUser: PropTypes.func,
  modalKey: PropTypes.number,
  onHide: PropTypes.func,
  onUpdateEntries: PropTypes.func,
  show: PropTypes.bool,
  token: PropTypes.string,
  user: PropTypes.object,
}
