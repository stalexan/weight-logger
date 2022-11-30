// EntryGraphPanel component, to display entry graph.

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

// Local imports
import { makeHttpRequest } from '../shared';
import DelayableMessage from './DelayableMessage';

// CSS imports
import './EntryGraphPanel.css';

export default function EntryGraphPanel(props) {
  // Image data. Saved as state since get requires authentication header.
  const [imageSource, setImageSource] = useState([]);

  // Messages displayed in panel.
  const FETCHING_GRAPH_MESSAGE = "Fetching graph...";
  const [panelMessage, setPanelMessage] = useState(FETCHING_GRAPH_MESSAGE);
  const [panelMessageDelay, setPanelMessageDelay] = useState(0.5);

  // Show message on main panel. Delay making message visible by delay seconds.
  function setPanelMessageAndDelay(message, delay) {
    setPanelMessage(message);
    setPanelMessageDelay(delay);
  }  

  // Fetch image.
  useEffect(() => {
    async function getImage() {
      try {
        // Fetch image.
        let response = await makeHttpRequest(
          "download entries CSV", "entries/graph", "GET", null,
          {}, props.token, props.forgetUser);

        // Handle response.
        if (response.ok) {
          // Load image data.
          let blob = await response.blob();

          // Base64 encode the image data and display.
          let reader = new FileReader();
          reader.onloadend = function () {
            setPanelMessageAndDelay("", 0);
            if (reader.result == "data:image/png;base64,")
                setImageSource(""); // Image is blank.
            else
                setImageSource(reader.result);
          }
          reader.readAsDataURL(blob); // Base64 encodes blob.
        }
      } catch (error) {
        console.log(error.message);
        setPanelMessageAndDelay(error.message, 0);
      }
    }
    getImage();
  }, [props.user, props.user?.goal_weight, props.entries]);

  // Render panel contents.
  if (!props.user) {
    // No user yet.
    return null;
  } else if (panelMessage.length) {
    // Just display message.
    return (<DelayableMessage message={panelMessage} delay={panelMessageDelay} />);
  } else {
    // Display graph.
    return (
      <div id="img-div">
        <img id="entries-graph" src={imageSource} />
      </div>
    )
  }
}

EntryGraphPanel.propTypes = {
  entries: PropTypes.array,
  forgetUser: PropTypes.func,
  token: PropTypes.string,
  user: PropTypes.object,
}
