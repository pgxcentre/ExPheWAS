import * as d3 from 'd3';
import { Delaunay } from 'd3-delaunay';


import { iteratorReduce } from './utils';


const test_data = {
  config: {
    width: 700,
    height: 200,
    minimumY: 2,
    addTooltip: true
  },
  // Ordered x-axis bands.
  bands: [
    {
      name: "GO",
      description: "Gene ontology",
      color: "#024996",
      children: [
        {
          name: "GO:MF",
          description: "Gene ontology - Molecular function",
          size: 12281,
          color: "#012F61"
        },
        {
          name: "GO:BP",
          description: "Gene ontology - Biological process",
          size: 30458,
          color: "#024996"
        },
        {
          name: "GO:CC",
          description: "Gene ontology - Cellular components",
          size: 4459,
          color: "#025AB8"
        }
      ]
    },
    {
      name: "HP",
      description: "Human Phenotype Ontology",
      size: 15872,
      color: "#E03227"
    }
  ],
  // Data points.
  data: [
    {band: "GO:MF", x: 5, y: 3},
    {band: "GO:MF", x: 1000, y: 3.2},
    {band: "GO:CC", x: 100, y: 0.1},
    {band: "GO:CC", x: 213, y: 2},
    {band: "HP", x: 123, y: 2.1},
  ]
};


export default function manhattan_plot(parent, data) {
  if (data === undefined) {
    console.log('Using test data.');
    data = test_data;
  }

  const annotationDepth = iteratorReduce(
    (a, b) => a.depth > b.depth? a: b,
    depthFirstTraversal(data.bands)
  ).depth;

  // Setup SVG
  const svgElem = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  parent.appendChild(svgElem);

  const margins = {
    top: 10, right: 20, bottom: 0, left: 60
  };
  data.config.margins = margins;

  const svg = d3.select(svgElem)
    .attr('width', data.config.width)
    .attr('height', data.config.height);

  if (data.config.addTooltip) {
    svg
      .on('mouseout', () => {
        d3.select('#tooltip-enrichment')
          .style('opacity', 0);
        d3.select('.selected-pt').remove();
      });
  }

  const scatterG = svg
    .append('g')
      .attr('transform', `translate(${margins.left}, ${margins.top})`);

  const bandsG = svg
    .append('g')
      .attr(
        'transform',
        `translate(${margins.left}, ${data.config.height - trackHeight(annotationDepth)})`
      );

  let xScales = plotBands(data, bandsG);

  let yAxisDomain;
  if (data.config.yAxisDomain) {
    yAxisDomain = data.config.yAxisDomain;
  } else {
    yAxisDomain = [
      Math.max(...data.data.map(o => o.y)) + 1,
      0
    ];
  }

  let yScale = d3.scaleLinear()
    .range([0, data.config.height - trackHeight(annotationDepth) - margins.top - margins.bottom])
    .domain(yAxisDomain);

  const yAxis = d3.axisLeft().scale(yScale);

  let colorMap = {};
  for (let n of depthFirstTraversal(data.bands))
    colorMap[n.name] = n.color || 'black';

  scatterG.append('g')
    .attr('class', 'y axis')
    .attr('transform', 'translate(-10, 0)')
    .call(yAxis);

  scatterG
    .append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -data.config.height / 2)
    .attr('y', -45)
    .attr('font-family', 'Arial')
    .attr('font-size', '14px')
    .text(data.config.yLabel || '-log(P)');

  let plotData = data.data.filter(
    d => data.config.minimumY !== undefined? (d.y >= data.config.minimumY): true
  );

  scatterG
    .selectAll('.pt')
    .data(plotData)
    .enter()
    .append('circle')
    .attr('cx', d => xScales[d.band](d.x))
    .attr('cy', d => yScale(d.y))
    .attr('r', 4)
    .attr('fill', d => colorMap[d.band]);

  if (data.config.addTooltip) {
    addTooltip(svgElem, plotData, scatterG, xScales, yScale);
  }

}


function addTooltip(svg, data, scatterG, xScales, yScale) {
  const delaunay = Delaunay.from(
    data,
    d => xScales[d.band](d.x),
    d => yScale(d.y)
  );

  d3.select('#tooltip-enrichment')
    .style('width', '400px')
    .style('position', 'fixed')
    .style('z-index', '20')
    .style('opacity', 0);

  let d3Svg = d3.select(svg);
  d3Svg.on('mousemove', () => {
    let pos = d3.clientPoint(scatterG.node(), d3.event);
    let datum = data[delaunay.find(...pos)];

    // Highlight circle
    let hlCircle = scatterG.selectAll('.selected-pt')
      .data([datum]);

    hlCircle.exit().remove();

    hlCircle
      .enter()
      .append('circle')
      .attr('class', 'selected-pt')
      .attr('pointer-events', 'none');

    hlCircle
      .attr('cx', d => xScales[d.band](d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', 6)
      .attr('stroke', 'black')
      .attr('fill', 'none');

    // Tooltip
    if (hlCircle.node()) {
      const tooltip = d3.select('#tooltip-enrichment');
      let content = "";
      for (const [k, v] of Object.entries(datum.tooltip)) {
        content += `<p><b>${k}</b>: ${v}</p>`
      }
      tooltip.html(content);

      let ttRect = tooltip.node().getBoundingClientRect();
      let circleNode = hlCircle.node();
      let matrix = circleNode.getScreenCTM()
        .translate(+circleNode.getAttribute("cx"),
                   +circleNode.getAttribute("cy"));

      let ttLeft = matrix.e + 5;
      let ttTop = matrix.f - ttRect.height - 5;

      tooltip
        .style('left', `${ttLeft}px`)
        .style('top', `${ttTop}px`)
        .style('opacity', 1);
    }

  });

}


function plotBands(data, g) {
  let sizes = {};
  let maxDepth = 0;

  // Hash set sizes and dynamically compute higher levels.
  for (const node of breadthFirstTraversal(data.bands)) {
    if (node.size === undefined) {
      sizes[node.name] = {depth: node.depth, size: 0};
    } else {
      sizes[node.name] = {depth: node.depth, size: node.size};
    }

    if (node.parent_name !== undefined) {
      sizes[node.parent_name].size += node.size | 0;
    }

    if (node.depth > maxDepth)
      maxDepth = node.depth;
  }

  let levelSizes = {};
  for (const [name, meta] of Object.entries(sizes)) {
    // meta has depth and size.
    if (!(meta.depth in levelSizes)) {
      levelSizes[meta.depth] = {size: meta.size, n: 1};
    } else {
      levelSizes[meta.depth].size += meta.size;
      levelSizes[meta.depth].n += 1;
    }
  }

  let scales = {};
  let widths = {};
  for (let level = 1; level <= maxDepth; level++) {

    let x0 = 0;
    let y = 20 * maxDepth - (level - 1) * 20;
    let levelMarginWidth = 5 * (levelSizes[level].n - 1);

    for (let band of breadthFirstTraversal(data.bands)) {
      if (band.depth < level)
        continue;

      if (band.depth > level)
        break;

      let parentWidth;
      let curWidth;
      if (band.parent_name === undefined) {
        // First level. Total width is plot width.
        parentWidth = data.config.width - data.config.margins.left - data.config.margins.right;
        // parentWidth = data.config.margins.left + data.config.width;
        curWidth = (
          sizes[band.name].size / levelSizes[1].size *
          (parentWidth - levelMarginWidth)
        );
      } else {
        parentWidth = widths[band.parent_name];
        curWidth = (
          sizes[band.name].size / sizes[band.parent_name].size *
          (widths[band.parent_name] - levelMarginWidth)
        );
      }

      widths[band.name] = curWidth;

      g
        .append('rect')
        .datum(band)
        .attr('x', x0)
        .attr('y', y)
        .attr('width', curWidth)
        .attr('height', 15)
        .attr('fill', d => d.color || 'black')
        .attr('transform', 'translate(0, -15)');

      g
        .append('text')
        .datum(band)
        .attr('x', x0 + 2)
        .attr('y', y)
        .text(d => d.name)
        .attr('font-size', '10px')
        .attr('font-family', 'Arial, sans-serif')
        .attr('fill', 'white')
        .attr('dy', -3)
        .attr('text-length', curWidth);

      // Only create scales for leaves.
      if (!band.children) {
        scales[band.name] = d3.scaleLinear()
          .range([x0, x0 + curWidth])
          .domain([0, sizes[band.name].size]);
      }

      x0 = x0 + curWidth + 5;
    }

  }

  return scales;
}


function* breadthFirstTraversal(trees) {
  let queue = [...trees];

  while (queue.length > 0) {
    let cur = queue.shift();
    if (cur.depth === undefined)
      cur.depth = 1;

    yield cur

    if (cur.children !== undefined) {
      let children = cur.children.map(o => {
        o.depth = cur.depth + 1;
        o.parent_name = cur.name;

        return o
      });
      queue.push(...children);
    }
  }
}


function* depthFirstTraversal(trees) {

  function* traverse_tree(tree, depth) {
    tree.depth = depth;
    yield tree;

    if (tree.children !== undefined) {
      for (const subtree of tree.children) {
        subtree.parent_name = tree.name;
        yield* traverse_tree(subtree, depth + 1);
      }
    }
  };

  for (const tree of trees) {
    yield* traverse_tree(tree, 1);
  }

}


function trackHeight(depth) {
  // 15px height per track and 3px top and bottom margin.
  return (15 + 6) * depth;
}
