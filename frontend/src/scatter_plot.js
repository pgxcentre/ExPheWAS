import * as d3 from 'd3';

/**
 * Allowed data fields:
 * x, y, xerr, yerr, id
 *
 **/
export default function scatter_plot(parent, data, config={}) {
  const fullWidth = parent.clientWidth;
  const width = 0.9 * fullWidth;
  const height = 0.6 * fullWidth;
  config.width = width;
  config.height = height;

  const COLOR = 'color' in data[0];

  let margins = {
    top: 10,
    right: 70,
    bottom: 40,
    left: 60
  };
  config.margins = margins;  // TODO Update instead.

  // Add space for a color legend if needed.
  if (COLOR)
    margins.top += 30;

  const svgElem = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  
  parent.appendChild(svgElem);

  const svg = d3.select(svgElem)
    .attr('width', width + margins.left + margins.right)
    .attr('height', height + margins.top + margins.bottom)
    .append('g')
      .attr('transform', `translate(${margins.left}, ${margins.top})`);

  const scales = buildScales(data, width, height, COLOR);

  // Axes
  addAxes(svg, scales, config);

  // Scatter plot!
  // Add error bars.
  const scatter = svg.append('g');
  if (data[0].xerr !== undefined) {
    scatter
      .selectAll('.xerr')
      .data(data)
      .enter()
      .append('line')
      .attr('class', 'xerr')
      .attr('x1', d => scales.x(d.x - d.xerr))
      .attr('x2', d => scales.x(d.x + d.xerr))
      .attr('y1', d => scales.y(d.y))
      .attr('y2', d => scales.y(d.y))
      .attr('stroke', '#dddddd')
  }

  if (data[0].yerr !== undefined) {
    scatter
      .selectAll('.yerr')
      .data(data)
      .enter()
      .append('line')
      .attr('class', 'yerr')
      .attr('x1', d => scales.x(d.x))
      .attr('x2', d => scales.x(d.x))
      .attr('y1', d => scales.y(d.y - d.yerr))
      .attr('y2', d => scales.y(d.y + d.yerr))
      .attr('stroke', '#dddddd')
  }

  // Draw data points.
  scatter
    .selectAll('.pt')
    .data(data)
    .enter()
    .append('circle')
    .attr('id', d => d.id? d.id: null)
    .attr('class', 'pt')
    .attr('fill', d => {
      if (COLOR) {
        return scales.color(d.color);
      } else { return '#ffffff'; }
    })
    .attr('cx', d => scales.x(d.x))
    .attr('cy', d => scales.y(d.y))
    .attr('stroke', '#000000')
    .attr('r', d => d.markerSize === undefined? 3: d.markerSize)

  return {svg, scales, config};

}

function addAxes(svg, scales, config) {
  const xAxis = d3.axisBottom().scale(scales.x);
  const yAxis = d3.axisLeft().scale(scales.y);

  svg.append('g')
    .attr('class', 'x axis')
    .attr('transform', `translate(0, ${config.height})`)
    .call(xAxis);

  svg.append('text')
    .attr(
      'transform',
      `translate(${config.width / 2}, ${config.height + config.margins.top + 20})`
    )
    .style('text-anchor', 'middle')
    .attr('font-size', '0.8em')
    .text(config.xLabel || 'X');

  svg.append('g')
    .attr('class', 'y axis')
    .call(yAxis);

  svg.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -config.height / 2)
    .attr('y', -config.margins.left)
    .attr('dy', '1em')
    .style('text-anchor', 'middle')
    .attr('font-size', '0.8em')
    .text(config.yLabel || 'Y');
}


function buildScales(data, width, height, color) {
  // Find extremums.
  let minX = 0;
  let maxX = 0;
  let minY = 0;
  let maxY = 0;
  let maxXerr = 0;
  let maxYerr = 0;

  for (let i = 0; i < data.length; i++) {
    let x = data[i].x;
    let y = data[i].y;

    if (x < minX) minX = x
    if (x > maxX) maxX = x

    if (y < minY) minY = y
    if (y > maxY) maxY = y

    if (data[i].xerr !== undefined && data[i].xerr > maxXerr)
      maxXerr = data[i].xerr;

    if (data[i].yerr !== undefined && data[i].yerr > maxYerr)
      maxYerr = data[i].yerr;
  }

  minX = minX - 1.1 * maxXerr;
  maxX = maxX + 1.1 * maxXerr;
  minY = minY - 1.1 * maxYerr;
  maxY = maxY + 1.1 * maxYerr;

  // Build scales.
  let xScale = d3.scaleLinear()
    .range([0, width])
    .domain([minX, maxX]);

  let yScale = d3.scaleLinear()
    .range([height, 0])
    .domain([minY, maxY]);

  let output = {x: xScale, y: yScale, minX, maxX, minY, maxY}

  if (color) {
    output.color = d3.scaleSequential(d3.interpolateOrRd).domain([0, 1]);
  }

  return output;
}
