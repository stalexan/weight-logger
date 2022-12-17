// PasswordInput component, for entering a password.

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
import showPasswordImage from './show-password.svg';
import hidePasswordImage from './hide-password.svg';

// CSS imports
import './PasswordInput.css';

// Input control to enter password.
export default function PasswordInput(props) {
  const [isPasswordShown, setIsPasswordShown] = useState(false);

  // Create input element.
  let className = "form-control";
  let ariaDescribedBy = "";
  if (props.errorMessageId) {
    className += " is-invalid";
    ariaDescribedBy = props.errorMessageId;
  }
  let inputElem = <input
    id="password-input" 
    type={isPasswordShown ? "text" : "password"}
    className={className}
    value={props.password}
    placeholder={props.label}
    aria-describedby={ariaDescribedBy}
    autoComplete={props.autoComplete}
    onChange={event => props.setPassword(event.target.value)} />

  // Create show/hide password image.
  let image;
  if (!props.errorMessageId)
    image = <img
      title={isPasswordShown ? "Hide password" : "Show password"}
      src={isPasswordShown ? hidePasswordImage : showPasswordImage}
      onClick={() => setIsPasswordShown(prevState => !prevState)} />

  return (
    <div id="password-div" className="form-floating">
      {inputElem}
      <label htmlFor="password-input">{props.label}</label>
      {image}
    </div>
  );
}

PasswordInput.propTypes = {
  autoComplete: PropTypes.string,
  errorMessageId: PropTypes.string,
  label: PropTypes.string,
  password: PropTypes.string,
  setPassword: PropTypes.func,
}
