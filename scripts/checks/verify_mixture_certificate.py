#!/usr/bin/env python3
"""Verify the exported mixture counterexample by exhaustive actions, without its generator."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
import argparse
from collections import defaultdict
import csv
from fractions import Fraction as F
import hashlib
from itertools import product
import json
import math
from pathlib import Path

ROOT=PROJECT_ROOT


def verify(folder, q):
    records=list(csv.DictReader((folder/'mixture_certificate.csv').open()))
    pmfs=[defaultdict(F),defaultdict(F)]
    weight_totals=[F(0),F(0)]
    latent_max=[F(0),F(0)]
    activity=[q/2,1-q,q/2]
    denominator=math.lcm(*(v.denominator for v in activity))
    numerators=[int(v*denominator) for v in activity]
    configurations=0
    for record in records:
        sizes=tuple(map(int,record['profile'].split('+')))
        assert sum(sizes)==10
        counts=defaultdict(int)
        for indices in product(range(3),repeat=len(sizes)):
            directions=[i-1 for i in indices]
            x=sum(s*d for s,d in zip(sizes,directions))
            m=sum(s*abs(d) for s,d in zip(sizes,directions))
            counts[abs(x),m]+=math.prod(numerators[i] for i in indices)
            configurations+=1
        for j,label in enumerate(('weight_A','weight_B')):
            weight=F(record[label]);assert weight>=0
            weight_totals[j]+=weight
            latent_max[j]+=weight*max(sizes)
            for state,count in counts.items():
                pmfs[j][state]+=weight*F(count,denominator**len(sizes))
    assert weight_totals==[1,1]
    assert pmfs[0]==pmfs[1] and sum(pmfs[0].values())==1
    for record in csv.DictReader((folder/'mixture_identical_pmf.csv').open()):
        state=int(record['abs_Q']),int(record['M'])
        assert pmfs[0].get(state,F(0))==F(record['probability_A'])==F(record['probability_B'])
    assert latent_max[0]!=latent_max[1]
    report={'status':'passed','kind':'MODEL_CHECK','method':'independent exhaustive action enumeration with integer probability counts',
            'q':str(q),'profiles':len(records),'action_configurations':configurations,
            'normalized_weights':True,'exact_equal_joint_laws':True,'exported_pmf_matches':True,
            'expected_largest_A':str(latent_max[0]),'expected_largest_B':str(latent_max[1]),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'member_review':'not_run'}
    (folder/'certificate_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=ROOT/'results/checks/theory_foundations_v1');p.add_argument('--q',type=F,default=F(1,5))
    args=p.parse_args();verify(args.folder,args.q)
