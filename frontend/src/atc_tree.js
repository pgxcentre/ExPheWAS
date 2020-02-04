// From: https://bl.ocks.org/d3noob/43a860bc0024792f8803bba8ca0d5ecd

import { api_call } from './utils';
import * as d3 from 'd3';


export default async function atcTree(id) {
  // Getting the data
  let treeData = await api_call(`/enrichment/atc/contingency/${id}`);

  // Set the dimensions and margins of the diagram
  let margin = {top: 20, right: 90, bottom: 30, left: 90};
  let width = 960 - margin.left - margin.right;
  let height = 500 - margin.top - margin.bottom;

  // append the svg object to the body of the page
  // appends a 'group' element to 'svg'
  // moves the 'group' element to the top left margin
  let svg = d3.select("#atc-tree")
      .on("mouseout", () => d3.select('#tooltip-atc-tree').style('opacity', 0) )
      .attr("width", width + margin.right + margin.left)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

  let i = 0;
  let duration = 750;
  let root;

  // Create a colorscale for enrichment p-values.
  let pColorScale = d3.scaleLinear()
    .domain([0, 0.01, 0.05, 0.1, 1])
    .range(["#FC802D", "#E8BB09", "#FCF12A", "#E8E5DE", "#F2F2F2"])
    .unknown("#FFFFFF");

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
    nodes.forEach(d => d.y = d.depth * 180);

    // ****************** Nodes section ***************************

    // Update the nodes...
    let node = svg.selectAll('g.node')
      .data(nodes, d => d.id || (d.id = ++i));

    // Enter any new modes at the parent's previous position.
    let nodeEnter = node.enter().append('g')
      .attr('class', 'node')
      .attr("transform", d => `translate(${source.y0}, ${source.x0})`)
      .on('click', click);

    // Tooltip
    d3.select('#tooltip-atc-tree')
      .style('position', 'fixed')
      .style('z-index', 20)
      .style('opacity', 0);

    // Add Circle for the nodes
    nodeEnter.append('circle')
      .attr('class', 'node')
      .attr('r', 0)
      // .style("fill", d => pColorScale(d.data.data))
      .on('mouseover', d => {
        let description = d.data.description === ''? '': `- ${d.data.description}`;
        d3.select('#tooltip-atc-tree')
          .html(`<h6>${d.data.code} ${description}</h6>`)
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
      .attr("dy", ".35em")
      .attr("x", d  => d.children || d._children ? -13 : 13)
      .attr("text-anchor", d => d.children || d._children ? "end" : "start")
      .text(d => d.data.code);

    // UPDATE
    let nodeUpdate = nodeEnter.merge(node);

    // Transition to the proper position for the node
    nodeUpdate.transition()
      .duration(duration)
      .attr("transform", d => `translate(${d.y}, ${d.x})`);

    // Update the node attributes and style
    nodeUpdate.select('circle.node')
      .attr('r', 9)
      .style("fill", d => {
        if (d.data.data === null)
          return "#767c85";

        return pColorScale(d.data.data);
      })
      .attr('cursor', 'pointer');

    // Remove any exiting nodes
    let nodeExit = node.exit().transition()
      .duration(duration)
      .attr("transform", d => `translate(${source.y}, ${source.x})`)
      .remove();

    // On exit reduce the node circles size to 0
    nodeExit.select('circle')
      .attr('r', 0);

    // On exit reduce the opacity of text labels
    nodeExit.select('text')
      .style('fill-opacity', 1e-6);

    // ****************** links section ***************************

    // Update the links...
    let link = svg.selectAll('path.link')
      .data(links, d => d.id);

    // Enter any new links at the parent's previous position.
    let linkEnter = link.enter().insert('path', "g")
      .attr("class", "link")
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
}
