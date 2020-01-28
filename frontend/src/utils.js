import { API_URL } from './config';


// Maps analysis types to human readable labels.
export const ANALYSIS_LABELS = {
  SELF_REPORTED: "Self-reported diseases",
  CV_ENDPOINTS: "Algo. defined CV endpoints",
  CONTINUOUS_VARIABLE: "Continuous variables",
  ICD10_RAW: "Hospit. or death ICD10 code (code as-is)",
  ICD10_3CHAR: "Hospit. or death ICD10 code (3 chars)",
  ICD10_BLOCK: "Hospit. or death ICD10 code (blocks)"
}


export function formatP(p) {
  if (p === null || p === undefined) {
    return 'NA';
  }
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


export async function api_call(endpoint) {
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
