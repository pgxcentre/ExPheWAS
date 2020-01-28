import '@babel/polyfill';
import * as d3 from 'd3';
import 'bootstrap';
import 'datatables.net';

import 'datatables.net-dt/css/jquery.dataTables.css';

import '../scss/custom.scss';
import { URL_PREFIX, API_URL, DT_API_URL, ICD10_URL, UNIPROT_URL } from './config';
import { formatP, formatNumber, getUrlParam } from './utils';


async function api_call(endpoint) {
  let results;
  try {
    let response = await fetch(API_URL + endpoint);
    results = await response.json();
  }
  catch (err) {
    console.log(err);
  }

  return results;
}


function mainOutcomeList() {
  // Add active page styling.
  $('.nav-item.outcomes').addClass('active');

  $('#app #outcomes')
    .DataTable({
      deferRender: true,
      ajax: {
        url: `${API_URL}/outcome`,
        dataSrc: ""
      },
      columns: [
        {data: 'id'},                   // 0
        {data: 'available_variances'},  // 1
        {data: 'analysis_type'},        // 2
        {data: 'label'}                 // 3
      ],
      columnDefs: [
        {
          targets: 0,
          render: (outcome, type, row, meta) => {
            return `<a href="${URL_PREFIX}/outcome/${outcome}">${outcome}</a>`;
          }
        },
        {
          targets: 1,
          orderable: false,
          searchable: false,
          render: (variances, type, row, meta) => {
            if (variances === null)
              return '<span class="badge badge-warning">No results</span>';

            return variances.sort().map(d => `<a href="${URL_PREFIX}/outcome/${row['id']}?variance_pct=${d}" class="badge badge-primary">${d}%</a>`).join(' ');
          }
        }
      ]
  });
}


async function mainOutcomeResults(id) {
  let variance_pct = getUrlParam("variance_pct", 95);
  let urlParam = variance_pct != 95? `?variance_pct=${variance_pct}`: '';

  let data = await api_call(`/outcome/${id}/results${urlParam}`);

  $('#app #outcomeResults')
    .DataTable({
      data: data,
      deferRender: true,
      columns: [
        {data: 'gene'},         // 0
        {data: 'gene_name'},    // 1
        {data: 'p'},            // 2
        {data: 'q'},            // 3
        {data: 'bonf'},         // 4
        {data: 'n_components'}, // 5
        {data: 'variance_pct'}  // 6
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(ensg, type, row, meta) {
            return `<a href="${URL_PREFIX}/gene/${ensg}${urlParam}">${ensg}</a>`;
          }
        },
        {
          targets: [2, 3, 4],
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: [2, 3, 4, 5, 6],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });
}


async function mainGeneResults(id) {
  // Add smooth scrolling to the page.
  // Adapted from https://stackoverflow.com/questions/7717527/smooth-scrolling-when-clicking-an-anchor-link/18795112#18795112
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    // Check that it's not an empty anchor.
    if (anchor.getAttribute('href') === '#') {
      return;
    }

    anchor.addEventListener('click', function (e) {

      e.preventDefault();

      // Fix the URL.
      let href = this.getAttribute('href');

      window.history.pushState({}, '', href);

      document.querySelector(href).scrollIntoView({
        behavior: 'smooth'
      });

    });
  });

  let variance_pct = getUrlParam("variance_pct", 95);
  let urlParam = variance_pct != 95? `?variance_pct=${variance_pct}`: '';

  let data = await api_call(`/gene/${id}/results${urlParam}`);

  // Total number of results
  let n_results = data.length;

  $('#app #geneResultsContinuous')
    .DataTable({
      deferRender: true,
      data: data.filter(d => d.analysis_type === 'CONTINUOUS_VARIABLE'),
      columns: [
        {data: 'outcome_id'},     // 0
        {data: 'outcome_label'},  // 1
        {data: 'p'},              // 2
        {data: 'q'},              // 3
        {data: 'bonf'},           // 4
        {data: 'gof_meas'},       // 5
        {data: 'test_statistic'}, // 6
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="${URL_PREFIX}/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: [2, 3, 4],
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: [5, 6],
          render: function(numeric_value, type, row, meta) {
            return numeric_value.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4, 5, 6],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsCVEndpoints')
    .DataTable({
      deferRender: true,
      data: data.filter(d => d.analysis_type === 'CV_ENDPOINTS'),
      columns: [
        {data: 'outcome_id'},     // 0
        {data: 'outcome_label'},  // 1
        {data: 'p'},              // 2
        {data: 'q'},              // 3
        {data: 'bonf'},           // 4
        {data: 'gof_meas'}        // 5
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="${URL_PREFIX}/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: [2, 3, 4],
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 5,
          render: function(gof_meas, type, row, meta) {
            return gof_meas.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4, 5],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsSelfReported')
    .DataTable({
      deferRender: true,
      data: data.filter(d => d.analysis_type === 'SELF_REPORTED'),
      columns: [
        {data: 'outcome_id'},     // 0
        {data: 'outcome_label'},  // 1
        {data: 'p'},              // 2
        {data: 'q'},              // 3
        {data: 'bonf'},           // 4
        {data: 'gof_meas'}        // 5
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="${URL_PREFIX}/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: [2, 3, 4],
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 5,
          render: function(gof_meas, type, row, meta) {
            return gof_meas.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4, 5],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsICD10Block')
    .DataTable({
      deferRender: true,
      data: data.filter(d => d.analysis_type === 'ICD10_BLOCK'),
      columns: [
        {data: 'outcome_id'},     // 0
        {data: 'outcome_label'},  // 1
        {data: 'p'},              // 2
        {data: 'q'},              // 3
        {data: 'bonf'},           // 4
        {data: 'gof_meas'}        // 5
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="${URL_PREFIX}/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: 1,
          render: function(description, type, row, meta) {
            let icd10Code = row.outcome_id.split("-")[0];
            return `${description} <small>[<a target="_blank" href="${ICD10_URL}/${icd10Code}">link</a>]</small>`;
          }
        },
        {
          targets: [2, 3, 4],
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 5,
          render: function(gof_meas, type, row, meta) {
            return gof_meas.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4, 5],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsICD103Char')
    .DataTable({
      deferRender: true,
      data: data.filter(d => d.analysis_type === 'ICD10_3CHAR'),
      columns: [
        {data: 'outcome_id'},    // 0
        {data: 'outcome_label'}, // 1
        {data: 'p'},             // 2
        {data: 'q'},             // 3
        {data: 'bonf'},          // 4
        {data: 'gof_meas'}       // 5
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="${URL_PREFIX}/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: 1,
          render: function(description, type, row, meta) {
            return `${description} <small>[<a target="_blank" href="${ICD10_URL}/${row.outcome_id}">link</a>]</small>`;
          }
        },
        {
          targets: [2, 3, 4],
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 5,
          render: function(gof_meas, type, row, meta) {
            return gof_meas.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4, 5],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });
}


function mainGeneList() {
  // Add active page styling.
  $('.nav-item.genes').addClass('active');

  $('#app #genes')
    .DataTable({
      processing: true,
      serverSide: true,
      ajax: `${DT_API_URL}/gene`,
      columnDefs: [
        {
          targets: 0,
          render: (ensembl_id, type, row, meta) => {
            let available_variances = row['1'];

            if (available_variances === null)
              return ensembl_id;

            let max_variance = Math.max.apply(Math, available_variances.map(d => d[0]));
            return `<a title="Results for ${max_variance}%" href="${URL_PREFIX}/gene/${ensembl_id}?variance_pct=${max_variance}">${ensembl_id}</a>`;
          }
        },
        {
          targets: 1,
          orderable: false,
          searchable: false,
          render: (variances, type, row, meta) => {
            if (variances === null)
              return '<span class="badge badge-warning">No results</span>';

            return variances
              .sort(d => d[0])
              .map(d => `<a title="Explained by ${d[1]} components" href="${URL_PREFIX}/gene/${row['0']}?variance_pct=${d[0]}" class="badge badge-primary">${d[0]}%</a>`)
              .join(' ');
          }
        },
        {
          targets: [4, 5],
          render: (position, type, row, meta) => formatNumber(position)
        },
        {
          targets: [3, 4, 5],
          searchable: false,
          className: 'dt-body-right'
        },
        {
          targets: 6,
          searchable: false,
          render: (pstrand, type, row, meta) => pstrand? '+': '-'
        }
      ],
      order: [[3, 'asc'], [4, 'asc']]
  });
}


window.pages = {
  mainOutcomeList,
  mainOutcomeResults,
  mainGeneResults,
  mainGeneList
}
