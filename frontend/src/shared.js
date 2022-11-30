// Weight Log shared code.

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

// Configuration
export const HOMEPAGE = process.env.REACT_APP_WL_HOMEPAGE; // e.g. "https://www.foobar.com/weight-log"

let simulatedDelaySeconds = 0;

export function setSimulatedDelaySeconds(seconds) {
    simulatedDelaySeconds = seconds;
}

function simulateNetworkDelay() {
  return new Promise(resolve => {
    setTimeout(() => { resolve(null); }, simulatedDelaySeconds * 1000); 
  });
}

// Create Error from Response.
async function createHttpReponseError(response) {
  // Read detail.
  let detail = null;
  let contentType = response.headers.get('Content-Type');
  if (contentType == 'application/json') {
    let body = await response.json();
    detail = body?.detail;
  }

  // Create message.
  let message;
  if (response.status == 502) {
    message = "No response from server. (HTTP error 502)";
  } else if (response.status == 400 && detail) {
    // "Bad request". Problem was on client side and server has said what the problem is.
    message = detail;
  } else {
    message = `HTTP error ${response.status} ${response.statusText}, for "${response.url}".`;
    if (detail)
      message += ` Detail: ${detail}`;  
  }

  // Create Error.
  return Error(message);
}

export async function makeHttpRequest(desc, urlSuffix, method, body, headers, token, forgetUser) {
  // Add authorization header.
  if (token)
    headers["Authorization"] = `Bearer ${token}`;

  // Configure timeout.
  const TIMEOUT = 5; // seconds
  let controller = new AbortController();
  let timeoutId = setTimeout(() => controller.abort(), TIMEOUT * 1000);

  // Make request.
  let response;
  try {
    let url = `${HOMEPAGE}/backend/${urlSuffix}`;
    if (simulatedDelaySeconds > 0)
        await simulateNetworkDelay();
    response = await fetch(url, {
      method: method,
      headers: headers,
      body: body,
      signal: controller.signal,
    });
  } catch (error) {
    let baseMessage =  error.name == 'AbortError' ?
      "Request timed out." : error.message;
    throw Error(`Error attempting to ${desc}: ${baseMessage}`);
  } finally {
    clearTimeout(timeoutId);
  }

  // Handle response error.
  if (!response.ok) {
    if (response.status == 401) {
        if (forgetUser) {
          // Client sent an invalid token. Display login prompt.
          forgetUser();
        }
    } else {
      throw await createHttpReponseError(response);
    }
  }

  return response;
}

export function convertUnits(isMetric, toMetric, value) {
  // Have units changed?
  if (isMetric == toMetric)
    return value;

  // Convert.
  const KG_PER_LB = 0.45359237;
  let newValue = toMetric ?
     value * KG_PER_LB : // lb to kg
     value / KG_PER_LB;  // kg to lb

  // Round.
  newValue = newValue.toFixed(toMetric ? 1 : 0);

  return newValue;
}
