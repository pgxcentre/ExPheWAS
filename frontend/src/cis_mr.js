import 'chosen-js';
import 'bootstrap4c-chosen/dist/css/component-chosen.min.css'

import { ANALYSIS_LABELS, BIOTYPES, api_call, formatNumber } from './utils';
import { DT_API_URL } from './config';


function createGeneTable() {
  let table = $('#genes')
    .DataTable({
      processing: true,
      serverSide: true,
      ajax: `${DT_API_URL}/gene`,
      columns: [
        {data: "ensembl_id"},             // 0
        {data: "name"},                   // 1
        {data: "description"},            // 2
        {data: "biotype"},                // 3
        {data: "chrom"},                  // 4
        {data: "start"},                  // 5
        {data: "end"},                    // 6
      ],
      columnDefs: [
        { targets: 0, className: 'ensembl-id' },
        { targets: 1, width: '12%' },
        {
          targets: 3,
          render: biotype => BIOTYPES[biotype],
          width: '12%'
        },
        { targets: [5, 6], render: formatNumber },
        { targets: [4, 5, 6], searchable: false, className: 'dt-body-right' },
      ],
      order: [[4, 'asc'], [5, 'asc']]
  });

  $('#genes tbody').on('click', 'tr', function () {
    if ($(this).hasClass('selected')) {
      $(this).removeClass('selected');
    }
    else {
      table.$('tr.selected').removeClass('selected');
      $(this).addClass('selected');
    }
  });
}


function handleVariableTypeChange(all_outcomes, e) {
  let varType = e.target.value;
  let id = e.target.id;

  let targetId = id.replace('Type', '');

  // Populate the options.
  // Get the possible outcomes.
  let outcomes = all_outcomes.filter(d => d.analysis_type == varType);

  // Populate the options.
  let options = outcomes.map(d => {
    let el = document.createElement('option');
    el.textContent = `${d.label} (${d.id})`;
    el.value = d.id;

    return el;
  });

  // Clear the current options.
  let selectElem = document.getElementById(targetId);
  while (selectElem.options.length) selectElem.remove(0);

  // Add the new options.
  for (let i = 0; i < options.length; i++) {
    selectElem.appendChild(options[i]);
  }

  $(`#${targetId}`).trigger('chosen:updated');

}


async function handleSubmit(event) {
  event.preventDefault();

  let formData = new FormData(document.getElementById('cisMRForm'));

  // Get the selected gene.
  let selectedRow = document.getElementsByClassName('selected');
  if (selectedRow.length > 1) {
    throw 'More than one element with class selected.'
  }
  else if (selectedRow.length == 0) {
    console.log('No gene selected...');
  }

  let gene = selectedRow[0].querySelector('.ensembl-id').innerHTML;

  let config = {
    analysis_subset: formData.get('analysisSubset'),
    exposure_type: formData.get('exposureType'),
    exposure_id: formData.get('exposureId'),
    outcome_type: formData.get('outcomeType'),
    outcome_id: formData.get('outcomeId'),
    ensembl_id: gene
  };

  // URI encode.
  let queryParams = Object.entries(config).map(
    ([k, v]) => `${k}=${encodeURIComponent(v)}`
  ).join('&');

  let results = await api_call(`/cisMR?${queryParams}`);

  document.getElementById('results').innerHTML = JSON.stringify(
    results, null, 2
  );

}


export default async function cisMR() {
  let all_outcomes = api_call('/outcome');

  // Create the gene list.
  createGeneTable();

  all_outcomes = await all_outcomes;
  let handler = e => handleVariableTypeChange(all_outcomes, e);

  $('#exposureType').chosen().change(handler);
  $('#outcomeType').chosen().change(handler);

  $('#exposure').chosen();
  $('#outcome').chosen();

  // Trigger initial loading.
  $('#exposureType').trigger('change');
  $('#outcomeType').trigger('change');

  // Form submit handler.
  document.getElementById("cisMRForm").addEventListener('submit', handleSubmit);
}
