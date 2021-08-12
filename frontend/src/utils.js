import { API_URL } from './config';


// Maps analysis types to human readable labels.
export const ANALYSIS_LABELS = {
  SELF_REPORTED: "Self-reported diseases",
  CV_ENDPOINTS: "Algo. defined CV endpoints",
  CONTINUOUS_VARIABLE: "Continuous variables",
  PHECODES: "Phecodes",
}


export const ANALYSIS_SUBSETS = {
  BOTH: "All",
  MALE_ONLY: "Male",
  FEMALE_ONLY: "Female"
}


export const BIOTYPES = {
  lincRNA: "lincRNA",
  protein_coding: "Protein coding",
}


export function formatEffect(beta, se, flip=false, to_odds_ratio=false, prec=2) {
  if (flip)
    beta = -1 * beta;

  let z = 1.959964;

  let effect = beta;
  let lower = beta - z * se;
  let upper = beta + z * se;

  if (to_odds_ratio) {
    effect = Math.exp(effect);
    lower = Math.exp(lower);
    upper = Math.exp(upper);
  }

  return `${effect.toFixed(prec)} (${lower.toFixed(prec)}, ${upper.toFixed(prec)})`;

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
    if (value.indexOf('#') != -1) {
      value = value.split('#')[0]
    }

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
    console.log('API call error: ', err);
  }

  return results;
}


export function iteratorReduce(f, generator) {
  let value;

  for (const elem of generator) {
    if (value === undefined)
      value = elem;

    value = f(value, elem);
  }

  return value;
}
