import { API_URL } from './config';


export function formatP(p) {
  if (p > 1) {
    return 1;
  }
  return (p < 0.001) && (p != 0)? p.toExponential(1): p.toFixed(3);
}


export function formatNumber(num) {
  return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
}


function getUrlVars() {
  var vars = {};
  var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m, key, value) {
    vars[key] = value;
  });
  return vars;
}

export function getUrlParam(parameter, defaultvalue) {
  var urlparameter = defaultvalue;
  if(window.location.href.indexOf(parameter) > -1) {
    urlparameter = getUrlVars()[parameter];
  }
  return urlparameter;
}


export async function p2q(p) {
  // API call to get the q values.
  let res = await fetch(
    `${API_URL}/qvalue`, {
      method: 'POST',
      body: JSON.stringify(p)
    }
  );

  let data = await res.json();

  if (data.error === undefined) {
    return data;
  }
  else {
    console.log(data);
    return null;
  }

}
