import { api_call, formatP } from './utils';

import * as d3 from 'd3';
import * as d3fc from 'd3fc';
import { Delaunay } from 'd3-delaunay';

import * as qbeta from '@stdlib/stats/base/dists/beta/quantile';
import * as qchi2 from '@stdlib/stats/base/dists/chisquare/quantile';


const analysisTypeToColor = {
  "ICD10_3CHAR": "#3E5CBD",
  "ICD10_BLOCK": "#3E5CBD",
  "ICD10_RAW": "#3E5CBD",
  "CONTINUOUS_VARIABLE": "#339C62",
  "SELF_REPORTED": "#FCB605",
  "CV_ENDPOINTS": "#FF5E54"
};


/**
 * Return an array of ticks for a range with a maximum of maxTicks elements.
 **/
function rangeTicks(start, end, maxTicks = 10, addEnd = false) {

  let ticks = [];

  let possibleSteps = [1, 2, 5, 10, 20, 25, 40, 50, 75, 100];
  let step = possibleSteps.find(curStep => {
    return (end - start) / curStep < maxTicks;
  });

  for (let i = start; i <= (end - step); i += step) {
    ticks.push(i);
  }

  if (addEnd && (ticks[ticks.length - 1] != end)) {
    // if (ticks.length == maxTicks)
    //   ticks[ticks.length - 1] = end;
    // else
    ticks.push(end);
  }

  return ticks

}


function medianAssumeSorted(li, accessor) {
  if (accessor === undefined)
    accessor = x => x;

  if(li.length === 0) return undefined;

  var half = Math.floor(li.length / 2);

  if (li.length % 2)
    return accessor(li[half]);

  return (accessor(li[half - 1]) + accessor(li[half])) / 2.0;
}


export default async function qq(data) {

  // Try to infer available width.
  let fullWidth = document.getElementById('geneQQ').parentNode.clientWidth;

  const aspectRatio = 0.6;
  const width = 0.7 * fullWidth;
  const height = aspectRatio * width;

  data.sort((a, b) => a.p - b.p);

  let n = data.length;
  let xy = data.map((cur, i) => {
    return {
      _i: i,
      n: n,
      analysisType: cur.analysis_type,
      outcomeId: cur.outcome_id,
      outcomeLabel: cur.outcome_label,
      x: -Math.log10((i + 1) / n),  // Exoected
      y: -Math.log10(cur.p == 0? 1e-300: cur.p),  // Observed
      p: cur.p,
      c975: -Math.log10(qbeta(0.975, i + 1, n - i)),
      c025: -Math.log10(qbeta(0.025, i + 1, n - i)),
      color: analysisTypeToColor[cur.analysis_type]
    };
  });

  let maxX = 0;
  let maxY = 0;
  xy.forEach(cur => {
    if (cur.x > maxX)
      maxX = cur.x
    if (cur.y > maxY)
      maxY = cur.y
  });

  // Compute the lambda inflation factor.
  // lambda = median(chi2_obs) / median(chi2_exp)
  let medianPExpected = medianAssumeSorted(xy, (d) => 10 ** (-d.x));
  let medianPObserved = medianAssumeSorted(xy, (d) => d.p);

  let medianChiExpected = qchi2(1 - medianPExpected, 1);
  let medianChiObserved = qchi2(1 - medianPObserved, 1);

  let lambda = medianChiObserved / medianChiExpected;
  d3.select("#lambdaQQ").text(lambda.toFixed(2));

  // Setup plot margins.
  let margins = {
    top: 10,
    right: 30,
    bottom: 40,
    left: 40
  };

  // Create SVG for plot.
  const svg = d3.select('#geneQQ')
      .on('mouseout', () => {
        d3.select('#tooltipQQ')
          .style('opacity', 0);

        d3.select('.selected-pt').remove();
      })
      .attr('width', width + margins.left + margins.right)
      .attr('height', height + margins.top + margins.bottom)
    .append('g')
      .attr('transform', `translate(${margins.left}, ${margins.top})`);

  // Identify need for y-axis break.
  let breakAxis = {
    doBreak: false,
    from: 0,
    to: 0
  };
  for (let i = 0; i < xy.length - 1; i++) {

    // Distance to the next point.
    let d = xy[i].y - xy[i + 1].y;

    // Break if step larger than 50.
    if (d > 50) {
      breakAxis.doBreak = true;
      breakAxis.from = Math.ceil(xy[i + 1].y);
      breakAxis.to = Math.floor(xy[i].y);
    }

  }

  // X is expected.
  let xScale = d3.scaleLinear()
    .range([0, width])
    .domain([0, maxX]);

  // Y is observed with possibility of axis break.
  let yScale, yAxis;
  if (breakAxis.doBreak) {
    yScale = d3fc.scaleDiscontinuous(d3.scaleLinear())
      .discontinuityProvider(d3fc.discontinuityRange([breakAxis.from,
                                                      breakAxis.to]))
      .domain([0, maxY])
      .range([height, 0]);

    // Define tick values.
    // We will allocate 20 ticks proportionally to both ranges.
    const totalTicks = 15;
    let rng1Length = breakAxis.from;
    let rng2Length = maxY - breakAxis.to;
    let rngRatio = rng1Length / (rng1Length + rng2Length);
    let range1Ticks = Math.round(rngRatio * totalTicks);

    let rng1Ticks = rangeTicks(  // Range 1 ticks
      0,
      breakAxis.from,
      Math.max(3, range1Ticks),  // Target number of ticks.
      false
    );

    let rng2Ticks = rangeTicks(
      breakAxis.to + 10,
      maxY,
      Math.max(3, totalTicks - rng1Ticks.length),
      true
    );

    let tickValues = [...rng1Ticks, ...rng2Ticks];

    yAxis = d3.axisLeft(yScale)
      .tickValues(tickValues);

    // Axis break lines.
    let breakOffset = 2
    svg.append('line')
      .attr('x1', xScale(-0.02))
      .attr('y1', yScale(breakAxis.from) - breakOffset / 2)
      .attr('x2', xScale(0.02))
      .attr('y2', yScale(breakAxis.from) - breakOffset)
      .style('stroke', 'red')
      .style('stroke-width', 1)

    svg.append('line')
      .attr('x1', xScale(-0.02))
      .attr('y1', yScale(breakAxis.to) + breakOffset)
      .attr('x2', xScale(0.02))
      .attr('y2', yScale(breakAxis.to) + breakOffset / 2)
      .style('stroke', 'red')
      .style('stroke-width', 1)

    // Long indicator line.
    svg.append('line')
      .attr('x1', xScale(-0.02))
      .attr('y1', yScale(breakAxis.from - 0.1))
      .attr('x2', xScale(maxX))
      .attr('y2', yScale(breakAxis.from - 0.1))
      .style('stroke', '#444444')
      .style('stroke-width', 0.5)


  } else {
    yScale = d3.scaleLinear()
      .range([height, 0])
      .domain([0, maxY + 1]);

    yAxis = d3.axisLeft().scale(yScale);
  }

  let xAxis = d3.axisBottom().scale(xScale).ticks(5);

  // Voronoi and tooltip.
  const delaunay = Delaunay.from(
    xy,
    d => xScale(d.x),
    d => yScale(d.y)
  );

  const voronoi = delaunay.voronoi([0, 0, width, height]);

  d3.select('#tooltipQQ')
    .style('position', 'fixed')
    .style('z-index', '20')
    .style('opacity', 0);

  const svgRect = svg.node().getBoundingClientRect();
  d3.select('#geneQQ').on('mousemove', () => {
    let pos = d3.clientPoint(svg.node(), d3.event);
    let datum = xy[delaunay.find(...pos)];

    const tooltip = d3.select('#tooltipQQ');

    let p = datum.p == 0? '<1e-300': formatP(datum.p);

    tooltip
      .html(`
        Analysis type: ${datum.analysisType}<br />
        Outcome ID: ${datum.outcomeId}<br />
        Outcome: ${datum.outcomeLabel}<br />
        Association p-value: ${p}
      `)

    // Get tooltip dimension after writing html to position the box correctly.
    let ttRect = tooltip.node().getBoundingClientRect();
    let ttX = svgRect.x + xScale(datum.x) - ttRect.width - 5;
    let ttY = svgRect.y + yScale(datum.y) - ttRect.height - 5;

    tooltip
      .style('left', `${ttX}px`)
      .style('top', `${ttY}px`)
      .style('opacity', 1)

    // Highlight point.
    let hlCircle = svg.selectAll('.selected-pt')
      .data([datum]);

    hlCircle.exit().remove();

    hlCircle
      .enter()
      .append('circle')
      .attr('class', 'selected-pt')
      .attr('pointer-events', 'none');

    hlCircle
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', 5)
      .attr('stroke', 'black')
      .attr('fill', 'none');

  });

  // Axis
  svg.append('g')
    .attr('class', 'x axis')
    .attr('transform', `translate(0, ${height})`)
    .call(xAxis);

  svg.append('g')
    .attr('class', 'y axis')
    .call(yAxis);

  // 95% CI area.
  let area = d3.area()
    .x(d => xScale(d.x))
    .y0(d => yScale(d.c025))
    .y1(d => yScale(d.c975));

  svg.append('path')
    .datum(xy)
    .attr('class', 'area')
    .attr('d', area)
    .style('fill', '#CFE2E8')

  // Scatter
  svg.append('g')
    .selectAll('.pt')
    .data(xy)
    .enter()
    .append('circle')
    .attr('class', 'pt')
    .attr('fill', d => d.color)
    .attr('cx', d => xScale(d.x))
    .attr('cy', d => yScale(d.y))
    .attr('r', 1);

  // Identity line
  svg.append('g')
    .append('line')
    .attr('x1', xScale(Math.min(maxX, maxY)))
    .attr('y1', yScale(Math.min(maxX, maxY)))
    .attr('x2', xScale(0))
    .attr('y2', yScale(0))
    .style('stroke', 'black')
    .style('stroke-width', 1)
    .style('stroke-dasharray', '4 2')

  // Axis labels.
  // X
  svg.append('text')
    .attr('transform', `translate(${width / 2}, ${height + margins.top + 20})`)
    .style('text-anchor', 'middle')
    .attr('font-size', '0.8em')
    .text('Expected -log10(p)');

  // Y
  svg.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', 0 - height / 2)
    .attr('y', 0 - margins.left)
    .attr('dy', '1em')
    .style('text-anchor', 'middle')
    .attr('font-size', '0.8em')
    .text('Observed -log10(p)');
}
