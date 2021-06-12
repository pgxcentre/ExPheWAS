import '@babel/polyfill';
import * as d3 from 'd3';
import 'bootstrap';
import 'datatables.net';

import 'datatables.net-dt/css/jquery.dataTables.css';

import '../scss/custom.scss';
import { URL_PREFIX, API_URL, DT_API_URL, ICD10_URL, UNIPROT_URL } from './config';
import { api_call, formatP, formatNumber, getUrlParam, ANALYSIS_LABELS, ANALYSIS_SUBSETS } from './utils';
import radialGTEX from './radial_plot';
import qq from './qq_plot';
import atcTree from './atc_tree';
import documentation from './documentation';


// This is a shim for d3 events to work with webpack
// https://github.com/d3/d3-zoom/issues/32#issuecomment-229889310
d3.getEvent = () => require("d3-selection").event;


function mainOutcomeList() {
  $('#app #outcomes')
    .DataTable({
      deferRender: true,
      ajax: {
        url: `${API_URL}/outcome`,
        dataSrc: ""
      },
      columns: [
        {data: 'id'},                   // 0
        {data: 'analysis_type'},        // 1
        {data: 'available_subsets'},    // 2
        {data: 'label'}                 // 3
      ],
      columnDefs: [
        {
          targets: 0,
          render: (outcome, type, row, meta) => {
            return `<a href="${URL_PREFIX}/outcome/${outcome}?analysis_type=${row.analysis_type}&analysis_subset=BOTH">${outcome}</a>`;
          }
        },
        {
          targets: 2,
          orderable: false,
          searchable: false,
          render: (subsets, type, row, meta) => {
            if (subsets === null)
              return '<span class="badge badge-warning">No results</span>';

            return subsets.sort().map(d => {
              return `
                <a href="${URL_PREFIX}/outcome/${row.id}?analysis_subset=${d}&analysis_type=${row.analysis_type}" class="badge analysis-badge analysis-${d}">
                  ${ANALYSIS_SUBSETS[d]}
                </a>
              `;
            }).join(' ');
          }
        },
        {
          targets: 1,
          render: (analysis, type, row, meta) => ANALYSIS_LABELS[analysis]
        }
      ]
  });
}


async function mainOutcomeResults(id) {
  // Add the ATC tree
  atcTree(id);

  let analysis_subset = getUrlParam("analysis_subset", "BOTH");
  let analysis_type = getUrlParam("analysis_type", null);

  let urlParam = `?analysis_subset=${analysis_subset}`;
  if (analysis_type !== null)
    urlParam += `&analysis_type=${analysis_type}`;

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
        {data: 'n_components'}  // 5
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
          targets: [2, 3, 4, 5],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'asc']]
  });
}


function geneResultBinaryOutcomeTable(o) {
  $(`#app #${o.id}`)
    .DataTable({
      deferRender: true,
      data: o.data.filter(d => d.analysis_type === o.analysis_type),
      columns: [
        {'data': 'outcome_id'},                // 0
        {'data': 'outcome_label'},             // 1
        {'data': 'n_cases'},                   // 2
        {'data': 'n_controls'},                // 3
        {'data': 'n_excluded_from_controls'},  // 4
        {'data': 'static_nlog10p'},            // 5
        {'data': 'p'},                         // 6
        {'data': 'bonf'},                      // 7
        {'data': 'q'},                         // 8
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            let urlParam = `?analysis_subset=${o.analysis_subset}`
            urlParam += `&analysis_type=${o.analysis_type}`;

            return `<a href="${URL_PREFIX}/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: 1,
          width: "25%"
        },
        {
          targets: [6, 7, 8],
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: 5,
          render: function(nlog10p, type, row, meta) {
            return nlog10p.toFixed(2);
          }
        },
        {
          targets: [2, 3, 4],
          render: function(n, type, row, meta) {
            return n.toLocaleString();
          }
        },
        {
          targets: [2, 3, 4, 5, 6, 7, 8],
          className: 'dt-body-right'
        }
      ],
      order: [[5, 'desc']]
  });
}

async function mainGeneResults(id) {
  // Add the GTEx radial plot.
  radialGTEX(id);

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

  let analysis_subset = getUrlParam("analysis_subset", "BOTH");
  let urlParam = `?analysis_subset=${analysis_subset}`;

  let data = await api_call(`/gene/${id}/results${urlParam}`);

  // Add the gene QQ plot as a measure of pleiotropy.
  qq(data);

  // Total number of results
  let n_results = data.length;

  $('#app #geneResultsContinuous')
    .DataTable({
      deferRender: true,
      data: data.filter(d => d.analysis_type === 'CONTINUOUS_VARIABLE'),
      columns: [
        {'data': 'outcome_id'},     // 0
        {'data': 'outcome_label'},  // 1
        {'data': 'n'},              // 2
        {'data': 'static_nlog10p'}, // 3
        {'data': 'p'},              // 4 (p)
        {'data': 'bonf'},           // 5 (bonf)
        {'data': 'q'},              // 6
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            urlParam = urlParam + `&analysis_type=CONTINUOUS_VARIABLE`;
            return `<a href="${URL_PREFIX}/outcome/${outcome}${urlParam}">${outcome}</a>`;
          }
        },
        {
          targets: [4, 5, 6],
          render: function(p, type, row, meta) { return formatP(p); }
        },
        {
          targets: 3,
          render: function(numeric_value, type, row, meta) {
            return numeric_value.toFixed(2);
          }
        },
        {
          targets: 2,
          render: function(numeric_value, type, row, meta) {
            return numeric_value.toLocaleString();
          }
        },
        {
          targets: [2, 3, 4, 5, 6],
          className: 'dt-body-right'
        }
      ],
      order: [[3, 'desc']]
  });

  geneResultBinaryOutcomeTable({
    id: 'geneResultsCVEndpoints',
    analysis_type: 'CV_ENDPOINTS',
    analysis_subset: analysis_subset,
    data: data,
  });

  geneResultBinaryOutcomeTable({
    id: 'geneResultsSelfReported',
    analysis_type: 'SELF_REPORTED',
    analysis_subset: analysis_subset,
    data: data,
  });

  geneResultBinaryOutcomeTable({
    id: 'geneResultsPhecodes',
    analysis_type: 'PHECODES',
    analysis_subset: analysis_subset,
    data: data,
  });
}


function mainGeneList() {
  $('#app #genes')
    .DataTable({
      processing: true,
      serverSide: true,
      ajax: `${DT_API_URL}/gene`,
      columns: [
        {data: "ensembl_id"},             // 0
        {data: null},                     // 1
        {data: "name"},                   // 2
        {data: "description"},            // 3
        {data: "chrom"},                  // 4
        {data: "start"},                  // 5
        {data: "end"},                    // 6
        {data: "positive_strand"}         // 7
      ],
      columnDefs: [
        {
          targets: 0,
          render: (ensembl_id, type, row, meta) => {
            let a = `<a href="${URL_PREFIX}/gene/${ensembl_id}?analysis_subset=BOTH">`;
            a += ensembl_id + "</a>";
            return a;
          }
        },
        {
          targets: 1,
          orderable: false,
          searchable: false,
          render: (a, type, row, meta) => {
            let ensembl_id = row.ensembl_id;
            let baseUrl = `${URL_PREFIX}/gene/${ensembl_id}`;
            let subsets = ["BOTH", "FEMALE_ONLY", "MALE_ONLY"];

            let linkForSubset = (subset, href_only) => {
              let link = `${baseUrl}?analysis_subset=${subset}`;
              if (href_only === true)
                return link;

              let a = `<a href="${link}" class="badge analysis-badge analysis-${subset}">`;
              a += ANALYSIS_SUBSETS[subset];
              a += "</a>";
              return a;
            };

            let badges = subsets.map(linkForSubset);
            return badges.join(" ");
          }
        },
        {
          targets: [5, 6],
          render: (position, type, row, meta) => formatNumber(position)
        },
        {
          targets: [4, 5, 6],
          searchable: false,
          className: 'dt-body-right'
        },
        {
          targets: 7,
          searchable: false,
          render: (pstrand, type, row, meta) => pstrand? '+': '-'
        }
      ],
      order: [[4, 'asc'], [5, 'asc']]
  });
}


window.pages = {
  mainOutcomeList,
  mainOutcomeResults,
  mainGeneResults,
  mainGeneList,
  documentation
}
