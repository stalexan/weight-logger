// EntryTable, EntryRows, and EntryRow components, to display entries in table panel.

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

function EntryHiddenDecimal(props) {
  // Add hidden decimal to pad value for alignment, if value has no decimal point.
  let value = props.value;
  if ((value - Math.floor(value)) < Number.EPSILON)
    return <span className="hidden-decimal">.0</span>;
  return null;
}

EntryHiddenDecimal.propTypes = {
  value: PropTypes.number,
}

// One row of entry table.
function EntryRow(props) {
  return (  
    <tr>
      <td>{props.entry.date}</td>
      <td align="right">{props.entry.weight}<EntryHiddenDecimal value={props.entry.weight} /></td>
      <td>
        <div className="entry-buttons-div">
          <button className="entry-button entry-button-for-table" onClick={() => { props.editEntry(props.entry); }}>Edit</button>
          <span className="entry-button-separator">|</span>
          <button className="entry-button entry-button-for-table" onClick={() => { props.deleteEntry(props.entry); }}>Delete</button>
        </div>
      </td>
    </tr>
  );
}

EntryRow.propTypes = {
  editEntry: PropTypes.func,
  entry: PropTypes.object,
  deleteEntry: PropTypes.func,
  value: PropTypes.number,
}

// All rows of entries table.
function EntryRows(props) {
  return props.entries.map((entry) => {
    return (
      <EntryRow
        key={entry.id}
        entry={entry}
        editEntry={() => props.editEntry(entry)}
        deleteEntry={() => props.deleteEntry(entry)}
      />
    );
  });
}

// The entry table.
export default function EntryTable(props) {
  if (props.entries.length > 0) {
    return (
      <table id="entry-table" className="table table-striped table-sm">
        <thead>
          <tr>
            <th align="center" scope="col">Date</th>
            <th align="center" scope="col">Weight ({props.unitsName})</th>
          </tr>
        </thead>
        <tbody>
          <EntryRows 
            entries={props.entries} 
            editEntry={(entry) => props.onShowEntryModal(entry)} 
            deleteEntry={(entry) => props.onShowConfirmModal(entry)} />
        </tbody>
      </table>
    );
  }
}

EntryTable.propTypes = {
  entries: PropTypes.array,
  entry: PropTypes.object,
  onShowEntryModal: PropTypes.func,
  onShowConfirmModal: PropTypes.func,
  unitsName: PropTypes.string,
}

