// EntryTablePanel component, to display entry table.

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
import { React, createRef, useEffect, useState } from "react";
import PropTypes from 'prop-types';

// Local imports
import { makeHttpRequest } from '../shared';
import DelayableMessage from './DelayableMessage';
import EntryModal from './EntryModal';
import EntryTable from './EntryTable';
import ConfirmModal from './ConfirmModal';
import MessageModal from './MessageModal';

// CSS imports
import './EntryTablePanel.css';

export default function EntryTablePanel(props) {
  // Modal dialog to confirm entry deletion.
  const [confirmDeleteEntryModalIsVisible, setConfirmDeleteEntryModalIsVisible] = useState(false);
  const [entryToDelete, setEntryToDelete] = useState({});

  // Modal dialog to confirm deletion of all entries.
  const [confirmDeleteAllEntriesModalIsVisible, setConfirmDeleteAllEntriesModalIsVisible] = useState(false);

  // Modal dialog to edit and create entries.
  const [entryModalIsVisible, setEntryModalIsVisible] = useState(false);
  const [entryForModal, setEntryForModal] = useState(null);
  const [entryModalKey, setEntryModalKey] = useState(0);

  // Modal dialog to display a message.
  const [messageModalIsVisible, setMessageModalIsVisible] = useState(false);
  const [messageModalTitle, setModalMessageTitle] = useState("");
  const [messageModalMessage, setMessageModalMessage] = useState("");

  // Messages displayed in panel.
  const [panelMessage, setPanelMessage] = useState("");
  const [panelMessageDelay, setPanelMessageDelay] = useState(0);

  // Reference to input element used for CSV file upload.
  const fileInputElemRef = createRef();

  // Trigger reget of entries with entriesKey.
  const [entriesKey, setEntriesKey] = useState(0);

  // Show modal dialog to edit or create an entry.
  function handleShowEntryModal(entry) {
    // Show dialog.
    setEntryModalKey((key) => key + 1); // Cause dialog to reinitialize.
    setEntryForModal(entry);
    setEntryModalIsVisible(true);
  }

  // Show message in modal dialog.
  function showMessageModal(title, message) {
    setMessageModalIsVisible(true);
    setMessageModalMessage(message);
    setModalMessageTitle(title);
  }

  // Show message on main panel. Delay making message visible by delay seconds.
  function setPanelMessageAndDelay(message, delay) {
    setPanelMessage(message);
    setPanelMessageDelay(delay);
  }  

  // Fetch weight entries from server.
  useEffect(() => {
    async function getEntries() {
      try {
        // Fetch entries.
        setPanelMessageAndDelay("Fetching entries...", 0.5);
        let response = await makeHttpRequest(
          "fetch entries", "entries", "GET", null,
          {}, props.token, props.forgetUser);

        // Handle response.
        if (response.ok) {
          // Display entries.
          let entriesReturned = await response.json();
          setPanelMessageAndDelay("", 0);
          sortEntries(entriesReturned);
          props.setEntries(entriesReturned);
        } 
      } catch (error) {
        console.log(error.message);
        setPanelMessageAndDelay(error.message, 0);
      }
    }
    getEntries();
  }, [entriesKey, props.user?.metric]);

  // Display modal dialog to confirm entry deletion.
  function handleShowConfirmDeleteEntryModal(entry) {
    setEntryToDelete(entry);
    setConfirmDeleteEntryModalIsVisible(true);
  }

  // Close modal dialog that confirms entry deletion, without deleting.
  function handleDeleteEntryCancel() {
    setEntryToDelete({});
    setConfirmDeleteEntryModalIsVisible(false);
  }

  // Finish deleting entry. User has confirmed deletion.
  async function handleDeleteEntryConfirm() {
    // Delete entry.
    try {
      // Delete.
      document.body.style.cursor = 'wait';
      let entry = entryToDelete;
      let urlSuffix = `entry/${entry.date}`;
      let response = await makeHttpRequest(
          "delete entry", urlSuffix, "DELETE", null,
          {}, props.token, props.forgetUser);

      // Handle response.
      if (response.ok) {
        // Delete locally.
        props.setEntries((entries) => entries.filter((candidate) => candidate.id !== entry.id))
      }
    } catch (error) {
      document.body.style.cursor = 'default';

      // Log error.
      console.log(error.message);

      // Display error in modal dialog.
      showMessageModal("Error", error.message);
    } finally {
      // Clean-up.
      document.body.style.cursor = 'default';
      setEntryToDelete({});
      setConfirmDeleteEntryModalIsVisible(false);
    }
  }

  // Sort entries by date.
  function sortEntries(entries) {
    entries.sort((entry1, entry2) => entry1.date > entry2.date);
  }

  // Save content at url to file named fileName.
  function saveUrlContentToFile(url, fileName) {
    let elem = document.createElement("a");
    elem.style = "display: none";
    document.body.appendChild(elem);
    elem.href = url;
    elem.download = fileName;
    elem.click();
    elem.remove();
  }

  // Download entries as CSV.
  async function downloadEntriesCSV() {
    try {
      // Fetch entries CSV.
      document.body.style.cursor = 'wait';
      let response = await makeHttpRequest(
        "download entries CSV", "entries/csv", "GET", null,
        {}, props.token, props.forgetUser);

      // Handle response.
      if (response.ok) {
        // Save CSV to file.
        let csv = await response.text();
        let blob = new Blob([csv], {type: "text/csv"});
        let url = URL.createObjectURL(blob);
        saveUrlContentToFile(url, 'weight-log-entries.csv');
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.log(error.message);
      setPanelMessageAndDelay(error.message, 0);
    } finally {
      // Clean-up.
      document.body.style.cursor = 'default';
    }
  }

  // Delete all entries.
  async function deleteAllEntries() {
    try {
      // Delete.
      document.body.style.cursor = 'wait';
      let response = await makeHttpRequest(
          "delete all entries", 'entries', "DELETE", null,
          {}, props.token, props.forgetUser);

      // Handle response.
      if (response.ok) {
        // Delete locally.
        props.setEntries((entries) => {
            entries.length = 0;
            return entries;
        })
      }
    } catch (error) {
      document.body.style.cursor = 'default';

      // Log error.
      console.log(error.message);

      // Display error in modal dialog.
      showMessageModal("Error", error.message);
    } finally {
      // Clean-up.
      document.body.style.cursor = 'default';
      setConfirmDeleteAllEntriesModalIsVisible(false);
    }
  }

  // Update entries based on changes made in EntryModal.
  function handleUpdateEntries(isEdit, entry) {
    props.setEntries((entries) => {
      // Update entries collection.
      if (isEdit)
      {
        // Update local copy.
        let index = entries.findIndex((candidate) => candidate.id === entry.id);
        if (index != -1)
          entries[index] = entry;
      } else {
        // Add new entry.
        entries.push(entry);
      }
  
      sortEntries(entries);

      return entries;
    });
  }

  // Upload entries from CSV.
  async function uploadEntriesCSV() {
    // Is there a file to upload?
    if (fileInputElemRef.current.files.length === 0)
        return;

    // Prepare CSV file to upload.
    let formData = new FormData();
    let file = fileInputElemRef.current.files[0];
    formData.append('file', file, file.name);

    try {
      // Upload.
      document.body.style.cursor = 'wait';
      let response = await makeHttpRequest(
        "upload CSV", "entries/csv", "POST",
        formData, {},
        props.token, props.forgetUser);

      // Handle response.
      if (response.ok) {
        // Reget entries.
        setEntriesKey((key) => key + 1);
      }
    } catch (error) {
      console.log(error.message);
      setPanelMessageAndDelay(error.message, 0);
    } finally {
      // Clean-up.
      document.body.style.cursor = 'default';
    }
  }

  // Render panel contents.
  if (panelMessage.length) {
    // Just display message.
    return (<DelayableMessage message={panelMessage} delay={panelMessageDelay} />);
  } else if (props.user) {
    // Display entries table.
    return (
      <div id="panel-div">
        <div id="content-div">
          {/* Sidebar */}
          <nav id="sidebar-menu" className="bg-light">
            <button className="entry-button entry-button-for-sidebar"
                onClick={() => { handleShowEntryModal(null); }}>Add</button>
            <button className="entry-button entry-button-for-sidebar"
                onClick={() => { downloadEntriesCSV(); }}>Download</button>
            <input type="file" ref={fileInputElemRef} accept="text/csv"
                style={{display: 'none'}} onChange={() => { uploadEntriesCSV(); }} />
            <button className="entry-button entry-button-for-sidebar"
                onClick={() => { fileInputElemRef.current.click(); }}>Upload</button>
            <button className="entry-button entry-button-for-sidebar"
                onClick={() => { setConfirmDeleteAllEntriesModalIsVisible(true); }}>Delete All</button>
          </nav>
          
          {/* Table of entries */}
          <div disabled={true} id="table-div"> {/* Stretches to fill available width and place scrollbar on right */}
            <div> {/* For table to fit to content instead of expanding to fill available width. */}
              <EntryTable 
                entries={props.entries} 
                unitsName={props.user.units_name}
                onShowEntryModal={handleShowEntryModal} 
                onShowConfirmModal={handleShowConfirmDeleteEntryModal} />
            </div>
          </div>
        </div>

        {/* Modal dialog to confirm entry deletion. */}
        <ConfirmModal 
          title="Delete Entry"
          message={`Delete "${entryToDelete.date} ${entryToDelete.weight} kg?`}
          show={confirmDeleteEntryModalIsVisible}
          onOK={handleDeleteEntryConfirm}
          onCancel={handleDeleteEntryCancel} />

        {/* Modal dialog to confirm deletion of all entries. */}
        <ConfirmModal 
          title="Delete All Entries"
          message={"Delete all entries?"}
          show={confirmDeleteAllEntriesModalIsVisible}
          onOK={deleteAllEntries}
          onCancel={() => { setConfirmDeleteAllEntriesModalIsVisible(false); }} />

        {/* Modal dialog to display a message, with just an OK button.*/}
        <MessageModal 
          message={messageModalMessage}
          title={messageModalTitle}
          show={messageModalIsVisible}
          onHide={() => { setMessageModalIsVisible(false); }} />

        {/* Modal dialog to create and edit entries. */}
        <EntryModal
          show={entryModalIsVisible}
          modalKey={entryModalKey}
          entry={entryForModal}
          token={props.token}
          user={props.user}
          forgetUser={props.forgetUser}
          onHide={ () => { setEntryModalIsVisible(false); } } 
          onUpdateEntries={handleUpdateEntries} />
      </div>
    );
  }
}

EntryTablePanel.propTypes = {
  entries: PropTypes.array,
  forgetUser: PropTypes.func,
  setEntries: PropTypes.func,
  token: PropTypes. string,
  user: PropTypes.object,
}
