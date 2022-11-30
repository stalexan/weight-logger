// ConfirmModal component, to display confirmation message with OK/Cancel buttons.

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
import { React } from "react";
import PropTypes from 'prop-types';

// 3rd party imports
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';

// Modal dialog with an OK and Cancel button to confirm an operation.
export default function ConfirmModal(props) {
  return (  
    <Modal show={props.show} onHide={props.onCancel} animation={false} size="sm">
      <Modal.Header closeButton>
        <Modal.Title>{props.title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>{props.message}</Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={props.onCancel}>
          Cancel
        </Button>
        <Button variant="primary" onClick={props.onOK}>
          Ok
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

ConfirmModal.propTypes = {
  onCancel: PropTypes.func,
  onOK: PropTypes.func,
  message: PropTypes.string,
  show: PropTypes.bool,
  title: PropTypes.string,
}
