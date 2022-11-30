// MessageModal component, to display a message.

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

// Modal dialog to display a message.
export default function MessageModal(props) {
  return (
    <Modal show={props.show} onHide={props.onHide} animation={false}>
      <Modal.Header closeButton>
        <Modal.Title>{props.title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>{props.message}</Modal.Body>
      <Modal.Footer>
        <Button variant="primary" onClick={props.onHide}>
          Ok
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

MessageModal.propTypes = {
  onHide: PropTypes.func,
  message: PropTypes.string,
  show: PropTypes.bool,
  title: PropTypes.string,
}
