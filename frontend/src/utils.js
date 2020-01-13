export function formatP(p) {
  return p < 0.001? p.toExponential(1): p.toFixed(3);
}

export function formatNumber(num) {
  return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
}
