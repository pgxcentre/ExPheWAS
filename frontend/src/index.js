import "@babel/polyfill";
import * as d3 from 'd3';
import * as dt from 'datatables.net';


import { API_URL } from "./config";


async function get_outcomes() {
  let outcomes;

  try {
    let response = await fetch(`${API_URL}/api/outcome`);
    outcomes = await response.json();
  }
  catch (err) {
    console.log(err);
  }

  return outcomes;
}


async function main() {
  let outcomes = await get_outcomes();

  $('#app #outcomes')
    .DataTable( {
      data: outcomes,
      columns: [
          { data: 'id' },
          { data: 'label' }
      ]
  } );

}

main();
