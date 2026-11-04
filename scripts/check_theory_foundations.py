#!/usr/bin/env python3
"""Exact rational checks for the theory addendum; no Monte Carlo or fitted labels."""
import argparse
from collections import defaultdict
import csv
from fractions import Fraction as F
import hashlib
from itertools import combinations, product
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from econophysics.model import Parameters, aggregate_orders, conditional_moments


def partitions(n, minimum=1):
    if n == 0:
        yield ()
    for s in range(minimum, n + 1):
        for tail in partitions(n - s, s):
            yield (s,) + tail


def law(profile, q):
    out = {(0, 0): F(1)}
    for s in profile:
        new = defaultdict(F)
        for (x, m), prob in out.items():
            for direction, weight in [(-1, q / 2), (0, 1 - q), (1, q / 2)]:
                new[x + s * direction, m + s * abs(direction)] += prob * weight
        out = dict(new)
    return out


def graph_profiles(n, p):
    edges = list(combinations(range(n), 2))
    out = defaultdict(F)
    for mask in product((0, 1), repeat=len(edges)):
        adjacency = [set() for _ in range(n)]
        for (i, j), active in zip(edges, mask):
            if active:
                adjacency[i].add(j)
                adjacency[j].add(i)
        remaining, sizes = set(range(n)), []
        while remaining:
            stack, component = [next(iter(remaining))], set()
            while stack:
                v = stack.pop()
                if v not in component:
                    component.add(v)
                    stack.extend(adjacency[v] - component)
            remaining -= component
            sizes.append(len(component))
        e = sum(mask)
        out[tuple(sorted(sizes))] += p ** e * (1 - p) ** (len(edges) - e)
    return dict(out)


def expectation(pmf, fn):
    return sum((prob * fn(x, m) for (x, m), prob in pmf.items()), F(0))


def null_vectors(matrix):
    """Exact reduced row elimination. Return a rational kernel basis and rank."""
    a = [row[:] for row in matrix]
    nrow, ncol, row, pivots = len(a), len(a[0]), 0, []
    for col in range(ncol):
        pivot = next((i for i in range(row, nrow) if a[i][col]), None)
        if pivot is None:
            continue
        a[row], a[pivot] = a[pivot], a[row]
        scale = a[row][col]
        a[row] = [v / scale for v in a[row]]
        for i in range(nrow):
            if i != row and a[i][col]:
                scale = a[i][col]
                a[i] = [v - scale * w for v, w in zip(a[i], a[row])]
        pivots.append(col)
        row += 1
        if row == nrow:
            break
    basis = []
    for free in sorted(set(range(ncol)) - set(pivots)):
        vector = [F(0)] * ncol
        vector[free] = F(1)
        for i, pivot in enumerate(pivots):
            vector[pivot] = -a[i][free]
        basis.append(vector)
    return basis, len(pivots)


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, condition, **detail):
        checks.append({'name': name, 'passed': bool(condition), **detail})
        if not condition:
            raise AssertionError(name)

    for n in (2, 3, 4):
        previous = None
        for p in (F(0), F(1, 4), F(1, 2), F(1)):
            profiles = graph_profiles(n, p)
            s2 = sum(w * sum(s ** 2 for s in sizes) for sizes, w in profiles.items())
            s3 = sum(w * sum(s ** 3 for s in sizes) for sizes, w in profiles.items())
            s4 = sum(w * sum(s ** 4 for s in sizes) for sizes, w in profiles.items())
            s22 = sum(w * sum(s ** 2 for s in sizes) ** 2 for sizes, w in profiles.items())
            check(f'ER monotonic N={n} p={p}', previous is None or s2 > previous)
            previous = s2
            if n == 3:
                check(f'N3 polynomial p={p}', s2 == 3 + 6 * (p + p*p - p**3))
            for q in (F(1, 5), F(2, 5), F(4, 5)):
                pmf = defaultdict(F)
                for sizes, weight in profiles.items():
                    for key, probability in law(sizes, q).items():
                        pmf[key] += weight * probability
                ex = lambda fn: expectation(pmf, fn)
                tag = f'N={n},p={p},q={q}'
                check('normalization ' + tag, sum(pmf.values()) == 1)
                check('support and symmetry ' + tag, all(abs(x) <= m <= n and (x-m)%2 == 0 and pmf.get((-x,m),F(0)) == w for (x,m),w in pmf.items()))
                check('mean Q ' + tag, ex(lambda x,m:x) == 0)
                check('mean M ' + tag, ex(lambda x,m:m) == q*n)
                check('variance Q ' + tag, ex(lambda x,m:x*x) == q*s2)
                vm = ex(lambda x,m:m*m)-(q*n)**2
                check('variance M ' + tag, vm == q*(1-q)*s2)
                check('covariance Q,M ' + tag, ex(lambda x,m:x*m) == 0)
                check('fourth moment ' + tag, ex(lambda x,m:x**4) == 3*q*q*s22 + q*(1-3*q)*s4)
                check('covariance Q2,M ' + tag, ex(lambda x,m:x*x*m)-q*s2*q*n == q*(1-q)*s3)
                check('positive abs covariance ' + tag, ex(lambda x,m:abs(x)*m)-ex(lambda x,m:abs(x))*q*n > 0)
                q_back = ex(lambda x,m:m)/n
                a_back = vm/(q_back*(1-q_back))
                check('moment inversion ' + tag, q_back == q and a_back == s2)

    for sizes in [(1,1,2), (1,2,3), (4,)]:
        params = Parameters(n=sum(sizes), a=.1, lambda_impact=.02, unit_order=3)
        moments = conditional_moments(sizes, params)
        check(f'production moments {sizes}', math.isclose(moments['var_V'], float(F(1,5)*F(4,5)*9*sum(s*s for s in sizes))))
        for actions in product((-1,0,1), repeat=len(sizes)):
            r,v = aggregate_orders(sizes, actions, params)
            check(f'production aggregation {sizes},{actions}', math.isclose(r, .02/sum(sizes)*sum(s*x for s,x in zip(sizes,actions)), abs_tol=1e-16) and v == 3*sum(s*abs(x) for s,x in zip(sizes,actions)))

    def er_law_2(p,q):
        return {key:(1-p)*law((1,1),q).get(key,F(0)) + p*law((2,),q).get(key,F(0)) for key in law((1,1),q)}
    counter_a = er_law_2(F(1,4), F(4,5))
    counter_b = er_law_2(F(3,7), F(7,10))
    marginal = lambda pmf: {x:sum(w for (xx,m),w in pmf.items() if xx==x) for x in range(-2,3)}
    check('N2 return-only exact equivalence', marginal(counter_a) == marginal(counter_b))
    check('N2 volume distinguishes', expectation(counter_a,lambda x,m:m) != expectation(counter_b,lambda x,m:m))

    n, q = 10, F(1,5)
    profiles = list(partitions(n))
    states = [(x,m) for m in range(n+1) for x in range(m%2,m+1,2)]
    columns = []
    for sizes in profiles:
        folded = defaultdict(F)
        for (x,m),w in law(sizes,q).items():
            folded[abs(x),m] += w
        columns.append([folded[key] for key in states])
    matrix = [list(row) for row in zip(*columns)]
    basis, rank = null_vectors(matrix)
    check('N10 dimension obstruction', len(profiles)==42 and len(states)==36 and bool(basis))
    # Pick the sparsest exact certificate; tie-break lexically for reproducibility.
    h = min(basis,key=lambda v:(sum(bool(x) for x in v),tuple(map(str,v))))
    check('kernel certificate', all(sum(x*y for x,y in zip(row,h))==0 for row in matrix) and sum(h)==0)
    mass = sum(x for x in h if x>0)
    plus = [max(x,F(0))/mass for x in h]
    minus = [max(-x,F(0))/mass for x in h]
    check('two valid different mixtures', sum(plus)==sum(minus)==1 and plus != minus)
    pmf_plus = [sum(x*y for x,y in zip(row,plus)) for row in matrix]
    pmf_minus = [sum(x*y for x,y in zip(row,minus)) for row in matrix]
    check('joint law exactly identical', pmf_plus == pmf_minus)
    with (output/'mixture_certificate.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(['profile','weight_A','weight_B'])
        writer.writerows(['+'.join(map(str,s)),str(a),str(b)] for s,a,b in zip(profiles,plus,minus) if a or b)
    with (output/'mixture_identical_pmf.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(['abs_Q','M','probability_A','probability_B'])
        writer.writerows([x,m,str(a),str(b)] for (x,m),a,b in zip(states,pmf_plus,pmf_minus))
    # Re-read serialized fractions and independently recompute to guard export mistakes.
    exported = list(csv.DictReader((output/'mixture_certificate.csv').open()))
    recomputed = [defaultdict(F),defaultdict(F)]
    for record in exported:
        sizes=tuple(map(int,record['profile'].split('+')))
        for (x,m),prob in law(sizes,q).items():
            for j,label in enumerate(('weight_A','weight_B')):
                recomputed[j][abs(x),m] += F(record[label])*prob
    check('serialized certificate rechecked', recomputed[0] == recomputed[1] and sum(recomputed[0].values()) == 1)
    # Verify one common singleton convolution; the general extension is inductive.
    for j in range(2):
        signed = defaultdict(F)
        for (x,m),prob in recomputed[j].items():
            signed[x,m] += prob/(2 if x else 1)
            if x: signed[-x,m] += prob/2
        folded = defaultdict(F)
        for (x,m),prob in signed.items():
            for d,w in [(-1,q/2),(0,1-q),(1,q/2)]:
                folded[abs(x+d),m+abs(d)] += prob*w
        recomputed[j]=folded
    check('common singleton extension', recomputed[0] == recomputed[1])
    pk=[0]*129;pk[0]=1
    for k in range(1,129):
        for total in range(k,129):pk[total]+=pk[total-k]
    report={'status':'passed','kind':'MODEL_CHECK','arithmetic':'exact rational except production float cross-checks',
            'check_count':len(checks),'checks':checks,
            'mixture_certificate':{'N':n,'q':str(q),'profile_count':len(profiles),'state_count':len(states),'exact_rank':rank,'kernel_dimension':len(basis),'nonzero_profiles':sum(bool(x) for x in h),'p128':pk[128]},
            'N2_counterexample':{'A':{'p':'1/4','q':'4/5'},'B':{'p':'3/7','q':'7/10'},'Q_pmf':{str(x):str(w) for x,w in marginal(counter_a).items()},'outside_primary_activity_grid':True},
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'limitations':['Small-N enumeration verifies identities, not their general proofs.','The general non-ER mixture obstruction is proved by dimension and common convolution.','No claim of novel theorem or completed independent member review.']}
    (output/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'results/checks/theory_foundations_v1')
    run(parser.parse_args().output)
