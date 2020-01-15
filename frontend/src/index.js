import "@babel/polyfill";
import * as d3 from 'd3';
import * as dt from 'datatables.net';


import { API_URL, ICD10_URL, UNIPROT_URL } from "./config";
import { formatP, formatNumber, getUrlParam } from "./utils";


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
  $('#app #outcomes')
    .DataTable({
      ajax: {
        url: `${API_URL}/outcome`,
        dataSrc: ""
      },
      processing: true,
      columns: [
        {data: 'id'},
        {data: 'label'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}">${outcome}</a>`;
          }
        }
      ]
  });
}


function mainOutcomeResults(id) {
  let variance_pct = getUrlParam("variance_pct", 95);
  let urlParam = variance_pct != 95? `?variance_pct=${variance_pct}`: '';
  console.log(`urlParam='${urlParam}'`);

  $('#app #outcomeResults')
    .DataTable({
      ajax: {
        url: `${API_URL}/outcome/${id}/results${urlParam}`,
        dataSrc: ""
      },
      processing: true,
      columns: [
        {data: 'gene'},
        {data: 'gene_name'},
        {data: 'p'},
        {data: 'n_components'},
        {data: 'variance_pct'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(ensg, type, row, meta) {
            return `<a href="/gene/${ensg}${urlParam}">${ensg}</a>`;
          }
        },
        {
          targets: 2,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: [2, 3, 4],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });
}


async function mainGeneResults(id) {
  let variance_pct = getUrlParam("variance_pct", 95);
  let urlParam = variance_pct != 95? `?variance_pct=${variance_pct}`: '';

  let data = await api_call(`/gene/${id}/results${urlParam}`);

  // Total number of results
  let n_results = data.length;
  console.log(n_results);

  // Calculate the bonferonni corrected p (TODO: the q-value / FDR).
  data = data.map(d => {
    d.bonf = d.p * n_results;
    return d;
  });


  $('#app #geneResultsContinuous')
    .DataTable({
      data: data.filter(d => d.analysis_type === 'CONTINUOUS_VARIABLE'),
      columns: [
        {data: 'outcome_id'},     // 0
        {data: 'outcome_label'},  // 1
        {data: 'p'},              // 2
        {data: 'bonf'},           // 3
        {data: 'gof_meas'},       // 4
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: 2,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 3,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 4,
          render: function(gof_meas, type, row, meta) {
            return gof_meas.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsCVEndpoints')
    .DataTable({
      data: data.filter(d => d.analysis_type === 'CV_ENDPOINTS'),
      columns: [
        {data: 'outcome_id'},     // 0
        {data: 'outcome_label'},  // 1
        {data: 'p'},              // 2
        {data: 'bonf'},           // 3
        {data: 'gof_meas'}        // 4
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: 2,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 3,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 4,
          render: function(gof_meas, type, row, meta) {
            return gof_meas.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsSelfReported')
    .DataTable({
      data: data.filter(d => d.analysis_type === 'SELF_REPORTED'),
      columns: [
        {data: 'outcome_id'},     // 0
        {data: 'outcome_label'},  // 1
        {data: 'p'},              // 2
        {data: 'bonf'},           // 3
        {data: 'gof_meas'}        // 4
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: 2,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 3,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 4,
          render: function(gof_meas, type, row, meta) {
            return gof_meas.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsICD10Block')
    .DataTable({
      data: data.filter(d => d.analysis_type === 'ICD10_BLOCK'),
      columns: [
        {data: 'outcome_id'},     // 0
        {data: 'outcome_label'},  // 1
        {data: 'p'},              // 2
        {data: 'bonf'},           // 3
        {data: 'gof_meas'}        // 4
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: 1,
          render: function(description, type, row, meta) {
            return `<a href="${ICD10_URL}/${row.id}">${description}</a>`;
          }
        },
        {
          targets: 2,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 3,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 4,
          render: function(gof_meas, type, row, meta) {
            return gof_meas.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsICD103Char')
    .DataTable({
      data: data.filter(d => d.analysis_type === 'ICD10_3CHAR'),
      columns: [
        {data: 'outcome_id'},
        {data: 'outcome_label'},
        {data: 'p'},
        {data: 'bonf'},
        {data: 'gof_meas'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: 1,
          render: function(description, type, row, meta) {
            let icd10Code = description.split(" ")[0];
            return `<a href="${ICD10_URL}/${icd10Code}">${description}</a>`;
          }
        },
        {
          targets: 2,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 3,
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 4,
          render: function(gof_meas, type, row, meta) {
            return gof_meas.toFixed(1);
          }
        },
        {
          targets: [2, 3, 4],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });
}


function mainGeneList() {
  $('#app #genes')
    .DataTable({
      ajax: {
        url: `${API_URL}/gene`,
        dataSrc: data => {
          let out = data.map((d) => {

            d.strand = d.positive_strand? '+': '-';
            d.uniprot_ids = d.uniprot_ids.map(id => {
              return `<a href="${UNIPROT_URL}/${id}">${id}</a>`).join(', ');
            })

            return d;

          });

          return out;
        }
      },
      processing: true,
      columns: [
        {data: 'ensembl_id'},
        {data: 'name'},
        {data: 'uniprot_ids'},
        {data: 'chrom'},
        {data: 'start'},
        {data: 'end'},
        {data: 'strand'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(ensg, type, row, meta) {
            return `<a href="/gene/${ensg}">${ensg}</a>`;
          }
        },
        {
          targets: [4, 5],
          render: function(position, type, row, meta) {
            return formatNumber(position);
          }
        },
        {
          targets: [3, 4, 5],
          className: 'dt-body-right'
        }
      ]
  });
}


window.pages = {
  mainOutcomeList,
  mainOutcomeResults,
  mainGeneResults,
  mainGeneList
}
