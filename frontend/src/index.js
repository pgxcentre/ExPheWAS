import '@babel/polyfill';
import * as d3 from 'd3';
import 'bootstrap';
import 'datatables.net';

import 'datatables.net-dt/css/jquery.dataTables.css';

import '../scss/custom.scss';
import { URL_PREFIX, API_URL, DT_API_URL, ICD10_URL, UNIPROT_URL } from './config';
import { formatP, formatNumber, getUrlParam } from './utils';

// This is a shim for d3 events to work with webpack
// https://github.com/d3/d3-zoom/issues/32#issuecomment-229889310
d3.getEvent = () => require("d3-selection").event;

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


async function radialGTEX(id) {
  // Gettting the data
  let data = await api_call(`/gene/${id}/gtex`);

  if (data.length === 0) {
    console.log(`No GTEx data for '${id}'`);
    return;
  }

  let height = 400;
  let width = height;
  let barHeight = height / 2 - 40;

  let formatNumber = d3.format('s');

  let color = {
    "Adipose - Subcutaneous":                     "#ff6600",
    "Adipose - Visceral (Omentum)":               "#ffaa00",
    "Adrenal Gland":                              "#33dd33",
    "Artery - Aorta":                             "#ff5555",
    "Artery - Coronary":                          "#ffaa99",
    "Artery - Tibial":                            "#ff0000",
    "Bladder":                                    "#aa0000",
    "Brain - Amygdala":                           "#eeee00",
    "Brain - Anterior cingulate cortex (BA24)":   "#eeee00",
    "Brain - Caudate (basal ganglia)":            "#eeee00",
    "Brain - Cerebellar Hemisphere":              "#eeee00",
    "Brain - Cerebellum":                         "#eeee00",
    "Brain - Cortex":                             "#eeee00",
    "Brain - Frontal Cortex (BA9)":               "#eeee00",
    "Brain - Hippocampus":                        "#eeee00",
    "Brain - Hypothalamus":                       "#eeee00",
    "Brain - Nucleus accumbens (basal ganglia)":  "#eeee00",
    "Brain - Putamen (basal ganglia)":            "#eeee00",
    "Brain - Spinal cord (cervical c-1)":         "#eeee00",
    "Brain - Substantia nigra":                   "#eeee00",
    "Breast - Mammary Tissue":                    "#33cccc",
    "Cells - Cultured fibroblasts":               "#aaeeff",
    "Cells - EBV-transformed lymphocytes":        "#cc66ff",
    "Cervix - Ectocervix":                        "#ffcccc",
    "Cervix - Endocervix":                        "#ccaadd",
    "Colon - Sigmoid":                            "#eebb77",
    "Colon - Transverse":                         "#cc9955",
    "Esophagus - Gastroesophageal Junction":      "#8b7355",
    "Esophagus - Mucosa":                         "#552200",
    "Esophagus - Muscularis":                     "#bb9988",
    "Fallopian Tube":                             "#ffcccc",
    "Heart - Atrial Appendage":                   "#9900ff",
    "Heart - Left Ventricle":                     "#660099",
    "Kidney - Cortex":                            "#22ffdd",
    "Kidney - Medulla":                           "#33ffc2",
    "Liver":                                      "#6bbb66",
    "Lung":                                       "#99ff00",
    "Minor Salivary Gland":                       "#99bb88",
    "Muscle - Skeletal":                          "#aaaaff",
    "Nerve - Tibial":                             "#ffd700",
    "Ovary":                                      "#ffaaff",
    "Pancreas":                                   "#995522",
    "Pituitary":                                  "#aaff99",
    "Prostate":                                   "#dddddd",
    "Skin - Not Sun Exposed (Suprapubic)":        "#0000ff",
    "Skin - Sun Exposed (Lower leg)":             "#7777ff",
    "Small Intestine - Terminal Ileum":           "#555522",
    "Spleen":                                     "#778855",
    "Stomach":                                    "#ffdd99",
    "Testis":                                     "#aaaaaa",
    "Thyroid":                                    "#006600",
    "Uterus":                                     "#ff66ff",
    "Vagina":                                     "#ff5599",
    "Whole Blood":                                "#ff00bb"
  };

  let svg = d3.select('#geneGTEX')
      .attr('width', width)
      .attr('height', height)
    .append('g')
      .attr('transform', `translate(${width / 2},${height / 2})`);

  let extent = d3.extent(data, d => d.value);

  let barScale = d3.scaleLinear()
      .domain(extent)
      .range([0, barHeight]);

  let keys = data.map(d => d.tissue);

  let numBars = keys.length;

  let x = d3.scaleLinear()
      .domain(extent)
      .range([0, -barHeight]);

  let xAxis = d3.axisLeft()
      .scale(x)
      .ticks(3)
      .tickFormat(formatNumber);

  let circles = svg.selectAll('circle')
          .data(x.ticks(3))
        .enter().append('circle')
          .attr('r', d => barScale(d))
          .style('fill', 'none')
          .style('stroke', 'black')
          .style('stroke-dasharray', '2,2')
          .style('stroke-width','.5px');

  let arc = d3.arc()
      .startAngle((d, i) => (i * 2 * Math.PI) / numBars)
      .endAngle((d, i) => ((i + 1) * 2 * Math.PI) / numBars)
      .innerRadius(0);

  // Tooltip
  d3.select('#tooltipGTEX')
    .style('position', 'fixed')
    .style('z-index', 20)
    .style('opacity', 0);

  let segments = svg.selectAll('path')
          .data(data)
        .enter().append('path')
          .each(d => d.outerRadius = 0)
          .style('fill', d => d.tissue in color? color[d.tissue]: "#000000")
          .attr('d', arc)
          .on('mouseover', d => {
            d3.select('#tooltipGTEX')
              .html(`${d.tissue}: ${d.value}<br />Nb samples: ${d.nb_samples}`)
              .transition()
              .duration(200)
              .style('opacity', 1);
          })
          .on('mouseout', d => {
            d3.select('#tooltipGTEX')
              .style('opacity', 0);
          })
          .on('mousemove', d => {
            let evt = d3.getEvent();
            let bbox = evt.target.getBBox();

            d3.select('#tooltipGTEX')
              .style('left', evt.pageX + 20 + 'px')
              .style('top', evt.pageY - 20 + 'px');
          });

  segments.transition(d3.easeElastic).duration(500)
    .attrTween('d', (d, index) => {
      let i = d3.interpolate(d.outerRadius, barScale(+d.value));
      return t => {
        d.outerRadius = i(t);
        return arc(d,index);
      }
    });

  svg.append('circle')
      .attr('r', barHeight)
      .classed('outer', true)
      .style('fill', 'none')
      .style('stroke', 'black')
      .style('stroke-width','1.5px');

  let lines = svg.selectAll('line')
      .data(keys)
    .enter().append('line')
      .attr('y2', -barHeight - 20)
      .style('stroke', 'black')
      .style('stroke-width','.5px')
      .attr('transform', (d, i) => `rotate(${(i * 360 / numBars)})`);

  svg.append('g')
    .attr('class', 'x axis')
    .call(xAxis);
}


window.pages = {
  mainOutcomeList,
  mainOutcomeResults,
  mainGeneResults,
  mainGeneList,
  radialGTEX
}
