import { API_URL } from './config';
import $ from 'jquery';


export default async function documentation() {

  $('#egModal').on('show.bs.modal', modalCallback);

}


async function modalCallback(event) {
    let button = $(event.relatedTarget); // Button that triggered the modal
    let endpoint = button.data('endpoint'); // Extract info from data-* attributes
    let reqURL = `${API_URL}${endpoint}`;  // URL to be used for the request.

    // Check if parameters were provided.
    let params = button.data('params');

    let method = button.data('method') || 'GET';
    
    let modal = $(this);

    // Reset results if needed.
    modal.find('.results').text('Loading...');

    // The endpoint may be parametrized. If it is the case we make
    // substitutions as needed.
    if (params !== undefined) {
      // Create URL encoded params.
      if (method == 'GET') {
        let chunks = [];
        for (const [k, v] of Object.entries(params)) {
          // Check if this parameter goes in the path or query string.
          let pathMatcher = new RegExp(`<${k}>`);
          if (reqURL.search(pathMatcher)) {
            reqURL = reqURL.replace(pathMatcher, v);
          } else {
            chunks.push(`${k}=${v}`);
          }
        }

        if (chunks.length >= 1) {
          reqURL = reqURL + '?' + chunks.join('&');
        }
      }
    }

    // Update the modal title.
    modal.find('.modal-title').text(`${method} ${API_URL}${endpoint}`);

    // Populate the modal example.
    let commandText;
    if (method == 'GET') {
      commandText = `curl http://${window.location.host}${reqURL}`;
    } else {
      // TODO
      commandText = `curl -X ${method} http://${window.location.host}${reqURL}`;
    }
    modal.find('.example-command').text(commandText);

    // Do the API call and show the results.
    let results = await apiCall(`${reqURL}`, method === 'GET'? undefined: params);

    // Strip the results if they are too long.
    if ($.isArray(results) && results.length > 3) {
      results = results.slice(0, 3);
      results.push('...');
    }

    modal.find('.results').text(JSON.stringify(results, null, 2));

}


async function apiCall(url, parameters, method='GET') {
  let config = {
    method: method,
    mode: 'no-cors'
  };

  if (parameters !== undefined) {
    if (method == 'POST') {
      config['body'] = parameters;
    }
    else {
      throw 'Parameters for non POST methods not implemented.';
    }
  }

  console.log('Fetching', url, config);
  const response = await fetch(url, config);
  let results = await response.json();
  return results;
}
