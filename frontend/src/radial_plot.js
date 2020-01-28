// From https://bl.ocks.org/bricedev/8aaef92e64007f882267

import { api_call } from './utils';
import * as d3 from 'd3';


export default async function radialGTEX(id) {
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
      .on("mouseout", () => d3.select('#tooltipGTEX').style('opacity', 0) )
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
    .innerRadius(0)

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
          .style('stroke', '#444444')
          .style('stroke-width', '1px')
          .attr('d', arc)
          .on('mouseover', d => {
            d3.select('#tooltipGTEX')
              .html(`
                <h6>${d.tissue}</h6>
                Median TPM: ${d.value.toFixed(1)}<br />
                Nb samples: ${d.nb_samples}
              `)
              .style('opacity', 1);
          })
          .on('mouseout', d => {
            d3.select('#tooltipGTEX')
              .style('opacity', 0);
          })
          .on('mousemove', d => {
            let evt = d3.getEvent();

            d3.select('#tooltipGTEX')
              .style('left', evt.clientX + 20 + 'px')
              .style('top', evt.clientY - 20 + 'px')
              .style('opacity', 1);
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
      .style('stroke', '#cccccc')
      .style('stroke-width','.5px')
      .attr('transform', (d, i) => `rotate(${(i * 360 / numBars)})`);

  svg.append('g')
    .attr('class', 'x axis')
    .call(xAxis);
}
