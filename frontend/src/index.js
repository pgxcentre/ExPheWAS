import "@babel/polyfill";
import * as d3 from 'd3';
import * as dt from 'datatables.net';


import { API_URL } from "./config";


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


async function mainOutcomeList() {
  $('#app #outcomes')
    .DataTable({
      data: await api_call('/outcome'),
      columns: [
        {data: 'id'},
        {data: 'label'}
      ],
      columnDefs: [
        {
          targets: 0,
          render: function(data, type, row, meta) {
            return `<a href="/outcome/${data}">${data}</a>`;
          }
        },
        {
          targets: 1,
          render: function (data, type, row, meta) {
            return `<a href="/outcome/${row.id}">${data}</a>`;
          }
        }
      ]
  });
}


async function mainOutcomeResults(id) {
  $('#app #outcomeResults')
    .DataTable({
      data: await api_call(`/outcome/${id}/results`),
      columns: [
        {data: 'analysis'},
        {data: 'gene'},
        {data: 'p'},
        {data: 'variance_pct'}
      ]
  });
}


window.pages = {
  mainOutcomeList,
  mainOutcomeResults
}
