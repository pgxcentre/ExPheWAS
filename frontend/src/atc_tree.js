// Adapted from: https://bl.ocks.org/d3noob/43a860bc0024792f8803bba8ca0d5ecd

import { api_call, formatP } from './utils';
import { ATC_API_URL } from './config';
import * as d3 from 'd3';


function addColorScale(svg, scale, legendText) {
  let rectSize = 15;

  // p-values to display in the legend.
  let p = [1e-8, 1e-4, 1e-2, 0.05, 0.5, 1.0];

  let colors = p.map(scale);

  let plot = svg.append('g');

  plot
    .append('g')
    .attr('transform', 'translate(0, 10)')
    .append('text')
    .attr('id', 'atc-legend-title')
    .attr('font-family', 'sans-serif')
    .attr('font-size', '14px')
    .text(legendText)

  let g = plot
    .attr('transform', `translate(10, 10)`)
    .selectAll('g.color-legend')
    .data(p)
    .enter()
    .append('g')
    .attr('class', 'color-legend')
    .attr('transform', (_, i) => `translate(15, ${i * (rectSize + 10) + 30})`);

  g
    .append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', rectSize)
    .attr('height', rectSize)
    .attr('fill', d => scale(d))
    .style('stroke', '#000000')
    .style('stroke-width', '1px');

  g
    .append('text')
    .attr('x', rectSize + 7)
    .attr('y', rectSize - 3)
    .attr('font-family', 'sans-serif')
    .attr('font-size', '13px')
    .text(d => d);
}


export default async function atcTree(id) {
  // The legend text
  let legendText = 'P-value (Fisher\'s exact)';

  // Getting the data
  let treeData = await api_call(`${ATC_API_URL}/${id}`);

  // Set the dimensions and margins of the diagram
  let margin = {top: 20, right: 0, bottom: 30, left: 90};
  let height = 500 - margin.top - margin.bottom;

  // Detect width based on SVG.
  let width = document.getElementById('atc-tree').clientWidth - margin.left - margin.right;

  // append the svg object to the body of the page
  // appends a 'group' element to 'svg'
  // moves the 'group' element to the top left margin
  let svg = d3.select('#atc-tree')
      .on('mouseout', () => d3.select('#tooltip-atc-tree').style('opacity', 0) )
      .attr('height', height + margin.top + margin.bottom);

  let plot = svg
    .append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

  let pattern = plot
    .append('defs')
    .append('pattern')
      .attr('id', 'diagonalHatch')
      .attr('patternUnits', 'userSpaceOnUse')
      .attr('width', 4)
      .attr('height', 4);

  pattern
    .append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', 4)
      .attr('height', 4)
      .attr('fill', 'white');

  pattern
    .append('path')
      .attr('d', 'M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2')
      .attr('stroke', '#000000')
      .attr('stroke-width', 1)
      .attr('fill', 'transparent');

  let i = 0;
  let duration = 750;
  let root;

  // Create a colorscale for enrichment p-values.
  let pColorScale = d3.scaleLinear()
    .domain([0, 0.01, 0.05, 0.1, 1])
    .range(['#DC3545', '#F3856E', '#FFE28E', '#FFF4D3', '#EDE7E3'])
    .unknown('#FFFFFF');

  addColorScale(svg, pColorScale, legendText);

  // declares a tree layout and assigns the size
  let treemap = d3.tree().size([height, width]);

  // Assigns parent, children, height, depth
  root = d3.hierarchy(treeData, d => d.children);
  root.x0 = height / 2;
  root.y0 = 0;

  // Collapse after the second level
  root.children.forEach(collapse);

  update(root);

  // Collapse the node and all it's children
  function collapse(d) {
    if(d.children) {
      d._children = d.children;
      d._children.forEach(collapse);
      d.children = null;
    }
  }

  function update(source) {
    // Assigns the x and y position for the nodes
    let treeData = treemap(root);

    // Compute the new tree layout.
    let nodes = treeData.descendants();
    let links = treeData.descendants().slice(1);

    // Normalize for fixed-depth.
    // ATC has 5 levels so we / 5
    nodes.forEach(d => d.y = d.depth * width / 5);

    // ****************** Nodes section ***************************

    // Update the nodes...
    let node = plot.selectAll('g.node')
      .data(nodes, d => d.id || (d.id = ++i));

    // Enter any new modes at the parent's previous position.
    let nodeEnter = node.enter().append('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${source.y0}, ${source.x0})`)
      .on('click', click);

    // Tooltip
    d3.select('#tooltip-atc-tree')
      .style('position', 'fixed')
      .style('z-index', 20)
      .style('opacity', 0);

    // Add Circle for the nodes
    nodeEnter.append('circle')
      .attr('class', d => d.data.children === undefined? 'node leaf': 'node')
      .attr('r', 0)
      .attr('stroke', '#666666')
      .attr('stroke-width', '2px')
      .on('mouseover', d => {
        let description = d.data.description === ''? '': `- ${d.data.description}`;
        d3.select('#tooltip-atc-tree')
          .html(`
            <h6>${d.data.code} ${description}</h6>
            <p>P-value: ${formatP(d.data.data.p)}</p>
            <p>NES: ${formatP(d.data.data.enrichment_score)}</p>
            <p>N drug target genes: ${d.data.data.set_size}</p>

          `)
          .style('opacity', 1);
      })
      .on('mouseout', d => {
        d3.select('#tooltip-atc-tree')
          .style('opacity', 0);
      })
      .on('mousemove', d => {
        let evt = d3.getEvent();

        d3.select('#tooltip-atc-tree')
          .style('left', evt.clientX + 20 + 'px')
          .style('top', evt.clientY - 20 + 'px')
          .style('opacity', 1);
      });

    // Add labels for the nodes
    nodeEnter.append('text')
      .attr('dy', '.35em')
      .attr('x', d  => d.children || d._children ? -13 : 13)
      .attr('text-anchor', d => d.children || d._children ? 'end' : 'start')
      .attr('font-size', '12px')
      .attr('font-family', 'arial, sans-serif')
      .text(d => d.data.code);

    // UPDATE
    let nodeUpdate = nodeEnter.merge(node);

    // Transition to the proper position for the node
    nodeUpdate.transition()
      .duration(duration)
      .attr('transform', d => `translate(${d.y}, ${d.x})`);

    // Update the node attributes and style
    nodeUpdate.select('circle.node')
      .attr('r', 9)
      .attr('fill', d => {
        if (d.data.code == 'ATC') {
          // There is no data for the root node.
          return 'url(#diagonalHatch)';
        }

        return d.data.data.p === null? 'url(#diagonalHatch)': pColorScale(d.data.data.p)
      })
      .attr('stroke', d => {
        if (d.data.code == 'ATC') return;

        let min_p  = d.data.data.min_p_children;

        return min_p === null? '': pColorScale(min_p);
      })
      .attr('cursor', 'pointer');

    // Remove any exiting nodes
    let nodeExit = node.exit().transition()
      .duration(duration)
      .attr('transform', d => `translate(${source.y}, ${source.x})`)
      .remove();

    // On exit reduce the node circles size to 0
    nodeExit.select('circle')
      .attr('r', 0);

    // On exit reduce the opacity of text labels
    nodeExit.select('text')
      .style('fill-opacity', 1e-6);

    // ****************** links section ***************************

    // Update the links...
    let link = plot.selectAll('path.link')
      .data(links, d => d.id);

    // Enter any new links at the parent's previous position.
    let linkEnter = link.enter().insert('path', 'g')
      .attr('class', 'link')
      .style('fill', 'none')
      .style('stroke', '#cccccc')
      .style('stroke-width', '2px')
      .attr('d', d => {
        var o = {x: source.x0, y: source.y0};
        return diagonal(o, o);
      });

    // UPDATE
    let linkUpdate = linkEnter.merge(link);

    // Transition back to the parent element position
    linkUpdate.transition()
      .duration(duration)
      .attr('d', d => diagonal(d, d.parent));

    // Remove any exiting links
    let linkExit = link.exit().transition()
      .duration(duration)
      .attr('d', d => {
        var o = {x: source.x, y: source.y};
        return diagonal(o, o);
      })
      .remove();

    // Store the old positions for transition.
    nodes.forEach(d => {
      d.x0 = d.x;
      d.y0 = d.y;
    });

    // Creates a curved (diagonal) path from parent to the child nodes
    function diagonal(s, d) {
      let path = `M ${s.y} ${s.x}
              C ${(s.y + d.y) / 2} ${s.x},
                ${(s.y + d.y) / 2} ${d.x},
                ${d.y} ${d.x}`;

      return path;
    }

    // Toggle children on click.
    function click(d) {
      if (d.children) {
          d._children = d.children;
          d.children = null;
        } else {
          d.children = d._children;
          d._children = null;
        }
      update(d);
    }
  }

  // Changing the enrichment algorithm
  d3.select('#atc-algorithm-select')
    .on('change', async function() {
      // Getting the selection
      let select = document.getElementById('atc-algorithm-select');
      let selection = select.options[select.selectedIndex].value;

      // Changing the tree
      let treeData = await api_call(`${ATC_API_URLS[selection]}/${id}`);
      root = d3.hierarchy(treeData, d => d.children);
      root.x0 = height / 2;
      root.y0 = 0;
      root.children.forEach(collapse);
      update(root);

      // Changing the legend's text
      document.getElementById('atc-legend-title').innerHTML = legendText[selection];
    });
}
