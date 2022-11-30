// DelayableMessage component, to display a message after a specified delay.

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

// Mesage that is shown only after optional delay.
export default function DelayableMessage(props) {
  const [show, setShow] = useState(props.delay === 0);

  useEffect(() => {
    if (!show) {
        const timeout = setTimeout(() => { setShow(true) }, props.delay * 1000);
        return () => clearTimeout(timeout);
    }
  }, [show, props.delay]);

  return show ? (<h5 className="m-3">{props.message}</h5>) : null;
}
 
DelayableMessage.propTypes = {
  delay: PropTypes.number,
  message: PropTypes.string,
}
