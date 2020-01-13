import "@babel/polyfill";
import * as d3 from 'd3';
import * as dt from 'datatables.net';


import { API_URL, ICD10_URL } from "./config";


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


async function mainOutcomeList() {
  $('#app #outcomes')
    .DataTable({
      data: await api_call('/outcome'),
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


async function mainOutcomeResults(id) {
  $('#app #outcomeResults')
    .DataTable({
      data: await api_call(`/outcome/${id}/results`),
      columns: [
        {data: 'gene'},
        {data: 'gene_name'},
        {data: 'p'},
        {data: 'variance_pct'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(ensg, type, row, meta) {
            return `<a href="/gene/${ensg}">${ensg}</a>`;
          }
        }
      ],
      order: [[2, 'asc']]
  });
}


async function mainGeneResults(id) {
  let data = await api_call(`/gene/${id}/results`);

  $('#app #geneResultsContinuous')
    .DataTable({
      data: data.filter(d => d.analysis_type === 'CONTINUOUS_VARIABLE'),
      columns: [
        {data: 'outcome_id'},
        {data: 'outcome_label'},
        {data: 'p'},
        {data: 'variance_pct'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}">${outcome}</a>`;
          }
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsCVEndpoints')
    .DataTable({
      data: data.filter(d => d.analysis_type === 'CV_ENDPOINTS'),
      columns: [
        {data: 'outcome_id'},
        {data: 'outcome_label'},
        {data: 'p'},
        {data: 'variance_pct'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}">${outcome}</a>`;
          }
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsSelfReported')
    .DataTable({
      data: data.filter(d => d.analysis_type === 'SELF_REPORTED'),
      columns: [
        {data: 'outcome_id'},
        {data: 'outcome_label'},
        {data: 'p'},
        {data: 'variance_pct'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}">${outcome}</a>`;
          }
        }
      ],
      order: [[2, 'asc']]
  });

  $('#app #geneResultsICD10Block')
    .DataTable({
      data: data.filter(d => d.analysis_type === 'ICD10_BLOCK'),
      columns: [
        {data: 'outcome_id'},
        {data: 'outcome_label'},
        {data: 'p'},
        {data: 'variance_pct'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}">${outcome}</a>`;
          }
        },
        {
          targets: 1,
          render: function(description, type, row, meta) {
            return `<a href="${ICD10_URL}/${row.id}">${description}</a>`;
          }
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
        {data: 'variance_pct'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            return `<a href="/outcome/${outcome}">${outcome}</a>`;
          }
        },
        {
          targets: 1,
          render: function(description, type, row, meta) {
            let icd10Code = description.split(" ")[0];
            return `<a href="${ICD10_URL}/${icd10Code}">${description}</a>`;
          }
        }
      ],
      order: [[2, 'asc']]
  });
}


async function mainGeneList() {
  let data = await api_call('/gene');

  data = data.map((d) => {
    let out = d;
    out.strand = out.positive_strand? '+': '-';
    out.uniprot_ids = out.uniprot_ids.join(', ');

    return out;
  });

  $('#app #genes')
    .DataTable({
      data: data,
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
