import Spline from 'cubic-spline';

export default function qvalue(ps) {

  let data = ps.map((p, idx) => { return {idx, p}; });
  console.log(data);

  data.sort((a, b) => a.p - b.p);

  let lambdas = [];
  let pi_0s = [];
  for (var lambda = 0.05; lambda <= 0.96; lambda += 0.05) {

    // Compute n p-values greater than lambda.
    let n_gt = data.reduce((acc, val, ) => val.p > lambda? acc + 1: acc, 0);

    let cur_pi0 = n_gt / (data.length * (1 - lambda));

    lambdas.push(lambda);
    pi_0s.push(cur_pi0);

  }

  // Fit spline.
  const spline = new Spline(lambdas, pi_0s);
  
  console.log(lambdas);
  console.log(pi_0s);
  window.spline = spline;
  let pi0 = spline.at(1);
  console.log(pi0);

}
