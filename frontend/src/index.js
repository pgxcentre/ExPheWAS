import '@babel/polyfill';
import * as d3 from 'd3';
import 'bootstrap';
import 'datatables.net';

import 'datatables.net-dt/css/jquery.dataTables.css';
import 'datatables.net-buttons-dt';
import 'datatables.net-buttons/js/buttons.html5.js';

import '../scss/custom.scss';
import { URL_PREFIX, API_URL, DT_API_URL, ICD10_URL, UNIPROT_URL } from './config';
import {
  api_call, formatP, formatNumber, getUrlParam, ANALYSIS_LABELS,
  ANALYSIS_SUBSETS, BIOTYPES
} from './utils';
import radialGTEX from './radial_plot';
import qq from './qq_plot';
import atcTree from './atc_tree';
import documentation from './documentation';
import cisMR from './cis_mr';
import manhattan_plot from './manhattan_plot';


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
            // Making sure to add the proper analysis subset in the link (if BOTH doesn't exist)
            let analysis_subset = "BOTH";
            if (!row.available_subsets.includes(analysis_subset))
              analysis_subset = row.available_subsets[0];

            return `<a href="${URL_PREFIX}/outcome/${outcome}?analysis_type=${row.analysis_type}&analysis_subset=${analysis_subset}">${outcome}</a>`;
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


async function createEnrichmentPlot(data, idToRemove=null) {

  const ENRICHMENT_DESCRIPTIONS = {
    'GO:MF': 'Gene Ontology - Molecular function'
  }

  const ENRICHMENT_COLORS = {
    'GO:MF': '#012F61',
    'GO:BP': '#024996',
    'GO:CC': '#025AB8',
    'HP': '#E03227',
  }

  // Keep genes with q <= 0.05.
  data = data.filter(o => o.q <= 0.05);

  if (data.length <= 5) {
    // Not computing enrichment analysis when under 5 genes are significant at
    // Q <= 0.05.
    return;
  }

  let response = await fetch(
    'https://biit.cs.ut.ee/gprofiler_beta/api/gost/profile/',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        organism: "hsapiens",
        query: data.map(o => o.gene),
        sources: ["GO:MF", "GO:BP", "GO:CC", "HP", "KEGG"]
      })
    }
  );

  let results = await response.json();

  if (results.result.length === 0) {
    // No enrichment results.
    console.log('No significant enrichment in g:Profiler.');
    return;
  }

  // Create bands from meta.
  let plotData = results.result.map(o => { return {
    band: o.source,
    x: o.source_order,
    y: -Math.log10(o.p_value),
    tooltip: {
      "Name": stringify(o.name),
      "Source": stringify(o.source),
      "ID": stringify(o.native),
      "Enrichment <i>P</i>": formatP(o.p_value),
      "Description": stringify(o.description),
    }
  }});

  let yMin = plotData[0].y;
  let yMax = plotData[0].y;
  for (const o of plotData) {
    if (o.y < yMin) yMin = o.y;
    if (o.y > yMax) yMax = o.y;
  }

  let plotConfig = {
    config: {
      width: document.getElementById('enrichment-box').parentNode.offsetWidth - 50,
      height: 200,
      minimumY: 2,
      yAxisDomain: [yMax + 0.5, yMin - 0.5],
      addTooltip: true
    },
    bands: [],
    data: plotData
  };

  for (const [name, meta] of Object.entries(results.meta.result_metadata)) {
    plotConfig.bands.push({
      name: name,
      description: ENRICHMENT_DESCRIPTIONS[name],
      color: ENRICHMENT_COLORS[name],
      size: meta.number_of_terms
    });
  }

  manhattan_plot(document.getElementById('enrichment-plot'), plotConfig);

  // Need to remove a div?
  if (idToRemove)
    document.getElementById(idToRemove).remove();

  // Showing the plot
  document.getElementById("enrichment-box").style.display = 'block';
}


function stringify(s) {
  s = s.replaceAll('"', '');
  s = JSON.stringify(s);
  return s.substring(1, s.length - 1);
}


async function mainOutcomeResults(id) {
  let analysis_subset = getUrlParam("analysis_subset", "BOTH");
  let analysis_type = getUrlParam("analysis_type", null);

  let urlParam = `analysis_subset=${analysis_subset}`;
  if (analysis_type !== null)
    urlParam += `&analysis_type=${analysis_type}`;

  let data = api_call(`/outcome/${id}/results?${urlParam}`);

  // Add the ATC tree
  atcTree(id);

  // Add the manhattan.
  data = await data;
  createEnrichmentPlot(data);

  $('#app #outcomeResults')
    .DataTable({
      data: data,
      deferRender: true,
      dom: "<'row'<'col-sm-12 col-md-6'lB><'col-sm-12 col-md-6'f>>" +
           "<'row'<'col-sm-12'tr>>" +
           "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
      buttons: [{
        extend: 'csv',
        text: 'Download as CSV',
        className: 'btn btn-link'
      }],
      columns: [
        {data: 'gene'},            // 0
        {data: 'gene_name'},       // 1
        {data: 'nlog10p'},         // 2
        {data: 'p'},               // 3
        {data: 'bonf'},            // 4
        {data: 'q'},               // 5
        {data: 'n_components'}     // 6
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(ensg, type, row, meta) {
            return `<a href="${URL_PREFIX}/gene/${ensg}?${urlParam}">${ensg}</a>`;
          }
        },
        {
          targets: 2,
          render: function(nlog10p, type, row, meta) {
            return nlog10p.toFixed(2);
          }
        },
        {
          targets: [3, 4, 5],
          render: function(p, type, row, meta) {
            return formatP(p);
          }
        },
        {
          targets: [2, 3, 4, 5, 6],
          className: 'dt-body-right'
        }
      ],
      order: [[2, 'desc']]
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
        {'data': 'nlog10p'},                   // 5
        {'data': 'p'},                         // 6
        {'data': 'bonf'},                      // 7
        {'data': 'q'},                         // 8
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            let urlParam = `analysis_subset=${o.analysis_subset}&analysis_type=${o.analysis_type}`;
            return `<a href="${URL_PREFIX}/outcome/${outcome}?${urlParam}">${outcome}</a>`;
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

async function mainGeneResults(id, has_results = true) {
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
  let urlParam = `analysis_subset=${analysis_subset}`;

  if (!has_results)
    return;

  let data = await api_call(`/gene/${id}/results?${urlParam}`);

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
        {'data': 'nlog10p'},        // 3
        {'data': 'p'},              // 4 (p)
        {'data': 'bonf'},           // 5 (bonf)
        {'data': 'q'},              // 6
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(outcome, type, row, meta) {
            let curUrlParam = urlParam + `&analysis_type=CONTINUOUS_VARIABLE`;
            return `<a href="${URL_PREFIX}/outcome/${outcome}?${curUrlParam}">${outcome}</a>`;
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
        {data: "biotype"},                // 4
        {data: "chrom"},                  // 5
        {data: "start"},                  // 6
        {data: "end"},                    // 7
        {data: "positive_strand"}         // 8
      ],
      createdRow: function(row, data, dataIndex) {
        if (!data.has_results) {
          $(row).addClass('dataTables-no-results');
        }
      },
      columnDefs: [
        {
          targets: 0,
          render: (ensembl_id, type, row, meta) => {
            // Skipping if no results in DB
            if (!row.has_results)
              return ensembl_id

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
            // Skipping if no results in DB
            if (!row.has_results)
              return null;

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
        { targets: 4, render: biotype => BIOTYPES[biotype] },
        {
          targets: [6, 7],
          render: (position, type, row, meta) => formatNumber(position)
        },
        {
          targets: [5, 6, 7],
          searchable: false,
          className: 'dt-body-right'
        },
        {
          targets: 8,
          searchable: false,
          render: (pstrand, type, row, meta) => pstrand? '+': '-'
        }
      ],
      order: [[5, 'asc'], [6, 'asc']]
  });
}


async function simpleQQPlotFromURL(url) {
  // We should have a valid URL to generate the QQ plot
  let data = await api_call(url);
  qq(data);
}

async function simpleManhattanFromURL(url) {
  // We should have a valid URL to generate the manhattan plot
  let data = await api_call(url);
  createEnrichmentPlot(data, 'enrichmentPlotLoading');
}


window.pages = {
  mainOutcomeList,
  mainOutcomeResults,
  mainGeneResults,
  mainGeneList,
  documentation,
  cisMR,
  atcTree,
  simpleQQPlotFromURL,
  simpleManhattanFromURL
}
