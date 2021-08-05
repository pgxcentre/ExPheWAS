import 'chosen-js';
import 'bootstrap4c-chosen/dist/css/component-chosen.min.css'

import { ANALYSIS_LABELS, BIOTYPES, api_call, formatNumber, formatP,
         formatEffect } from './utils';
import { DT_API_URL } from './config';
import scatter_plot from './scatter_plot';


let lastEvent = Date.now();


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
        { 
          targets: 1,
          width: '12%',
          className: 'symbol'
        },
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

  let curEvent = Date.now();
  if (curEvent - lastEvent < 1000) {
    // 1s cooldown for for submission.
    return false;
  }
  lastEvent = curEvent;

  // Clear old errors and results.
  document.getElementById('errors').innerHTML = '';
  document.getElementById('results').innerHTML = '';
  document.getElementById('mr_plot').innerHTML = '';
  document.getElementById('mr_plot_legend').style.display = 'none';

  let errors = [];
  let error = (name, message) => { errors.push({name, message}); };
  let formData = new FormData(document.getElementById('cisMRForm'));

  // Get the selected gene.
  let gene;
  let geneSymbol;
  let selectedRow = document.getElementsByClassName('selected');
  if (selectedRow.length > 1) {
    throw 'More than one element with class selected.'
  }
  else if (selectedRow.length == 0) {
    error(
      'NoGeneSelected',
      'No gene was selected for cis-MR analysis. Select a gene by clicking ' +
      'in the gene table.'
    );
  } else {
    gene = selectedRow[0].querySelector('.ensembl-id').innerHTML;
    geneSymbol = selectedRow[0].querySelector('.symbol').innerHTML;
  }

  let config = {
    analysis_subset: formData.get('analysisSubset'),
    exposure_type: formData.get('exposureType'),
    exposure_id: formData.get('exposureId'),
    outcome_type: formData.get('outcomeType'),
    outcome_id: formData.get('outcomeId'),
    ensembl_id: gene
  };

  if (formData.get('disablePCPruning') === "on") {
    config['disable_pruning'] = true;
  }

  // Client side validation.
  if (config.exposure_type == config.outcome_type &&
      config.exposure_id == config.outcome_id) {
    error(
      'ExposureIsOutcome',
      'The exposure and outcome are the same phenotype.'
    );
  }

  if (errors.length) {
    throw errors;
  }

  // URI encode.
  let queryParams = Object.entries(config).map(
    ([k, v]) => `${k}=${encodeURIComponent(v)}`
  ).join('&');

  let results = await api_call(`/cisMR?${queryParams}`);

  if (results.error) {
    error('ServerSideError', results.error);
    throw errors;
  } else {
    displayMRResults(results, geneSymbol)
  }

  document.getElementById("results").scrollIntoView({'behavior': 'smooth'});
}


function displayMRResults(results, geneSymbol) {
  let resultsDiv = document.getElementById('results');
  let effect = formatEffect(
    results.ivw_beta,
    results.ivw_se,
    false,  // flip
    results.outcome_is_binary  // to_odds_ratio
  );

  let content = (
    `<h2>cis-MR Results</h2>
     <p>
      MR estimate of the effect of '${results.exposure_label}' on 
      '${results.outcome_label}' based on genetic variants close to the gene 
      <i>${geneSymbol}</i>.
     </p>
     <p>Inverse variance weighted (IVW) effect and 95% confidence interval:</p>
       <p><span id="ivw-effect">${effect}</span></p>
     <p>MR P-value : <span id="ivw-p">${formatP(results.wald_p)}</span></p>
     <p>
       The association P-value for the exposure is
       <b>${formatP(Math.pow(10, -results.exposure_nlog10p))}</b>. The strength of this
       association is one of the MR assumptions. In general, <u>values above
       ${formatP(0.05 / 2000)} should be met with skepticism </u>unless supported by prior data.
       This suggested threshold accounts for 2,000 association tests which is
       approximately the number of phenotypes included in ExPheWas.
     </p>
     <p>
       <small>If the selected outcome is binary, the MR estimate is presented
       on the odds ratio scale by exponentiating the estimate from the log-odds
       scale.</small>
     </p>`
  );
  resultsDiv.innerHTML = content;

  let plot = scatter_plot(
    document.getElementById("mr_plot"),
    results.summary_stats.map(d => { return {
      x: d.exposure_beta,
      xerr: 1.96 * d.exposure_se,
      y: d.outcome_beta,
      yerr: 1.96 * d.outcome_se,
      // color: d.weight,
      id: d.term,
      markerSize: d.pruned? 1: 3
    }}),
    { xLabel: 'Effect of PC on exposure', yLabel: 'Effect of PC on outcome' }
  );

  // Add the IVW fit line.
  plot.svg.append('line')
    .attr('x1', plot.scales.x(plot.scales.minX))
    .attr('x2', plot.scales.x(plot.scales.maxX))
    .attr('y1', plot.scales.y(results.ivw_beta * plot.scales.minX))
    .attr('y2', plot.scales.y(results.ivw_beta * plot.scales.maxX))
    .attr('stroke', 'red')

  // Add the null lines.
  plot.svg.append('line')
    .attr('x1', plot.scales.x(plot.scales.minX))
    .attr('x2', plot.scales.x(plot.scales.maxX))
    .attr('y1', plot.scales.y(0))
    .attr('y2', plot.scales.y(0))
    .attr('stroke', '#888888')
    .attr('stroke-dasharray', '4');

  plot.svg.append('line')
    .attr('x1', plot.scales.x(0))
    .attr('x2', plot.scales.x(0))
    .attr('y1', plot.scales.y(plot.scales.minY))
    .attr('y2', plot.scales.y(plot.scales.maxY))
    .attr('stroke', '#888888')
    .attr('stroke-dasharray', '4');

  document.getElementById("mr_plot_legend").style.display = 'block';
}


function displayErrors(errors) {
  console.log(errors);
  let errorP = document.getElementById('errors');
  for (let i = 0; i < errors.length; i++) {
    errorP.innerHTML += `<li>${errors[i].message}</li>`;
  }
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
  document.getElementById("cisMRForm").addEventListener(
    'submit',
    (...args) => {
      handleSubmit(...args).catch((errors) => displayErrors(errors));
    }
  );
}
