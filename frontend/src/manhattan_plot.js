import * as d3 from 'd3';

import { iteratorReduce } from './utils';


const test_data = {
  config: {
    width: 700,
    height: 200,
    minimumY: 2
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
    top: 0, right: 0, bottom: 0, left: 60
  };
  data.config.margins = margins;

  const svg = d3.select(svgElem)
    .attr('width', data.config.width)
    .attr('height', data.config.height);

  const scatterG = svg
    .append('g')
      .attr('transform', `translate(${margins.left}, 0)`);

  const bandsG = svg
    .append('g')
      .attr(
        'transform',
        `translate(${margins.left}, ${data.config.height - trackHeight(annotationDepth)})`
      );

  let xScales = plotBands(data, bandsG);

  let yScale = d3.scaleLinear()
    .range([0, data.config.height - trackHeight(annotationDepth)])
    .domain([
      Math.max(...data.data.map(o => o.y)) + 1,
      0
    ]);

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

  scatterG
    .selectAll('.pt')
    .data(data.data)
    .enter()
    .filter(d => data.config.minimumY !== undefined? (d.y >= data.config.minimumY): true)
    .append('circle')
    .attr('cx', d => xScales[d.band](d.x))
    .attr('cy', d => yScale(d.y))
    .attr('r', 4)
    .attr('fill', d => colorMap[d.band]);

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
        parentWidth = data.config.margins.left + data.config.width;
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
