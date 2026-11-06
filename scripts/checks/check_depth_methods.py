#!/usr/bin/env python3
"""Independent finite graph enumeration and exact third-order moment checks."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
from fractions import Fraction as F
import argparse,json,math,sys
ROOT=PROJECT_ROOT;sys.path.insert(0,str(ROOT/'src'))
from econophysics.physics_inference import finite_er_moments,scale_invariant_joint
from check_theory_foundations import graph_profiles,law,expectation


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'results/checks/depth_study_v1/method_checks.json');args=p.parse_args()
    results=[]
    def check(name,valid):
        results.append({'check':name,'passed':bool(valid)})
        if not valid:raise AssertionError(name)
    for n in (2,3,4):
        for edge in [F(0),F(1,4),F(1,2),F(3,4),F(1)]:
            profiles=graph_profiles(n,edge);expected2=sum(w*sum(s*s for s in profile) for profile,w in profiles.items());expected3=sum(w*sum(s**3 for s in profile) for profile,w in profiles.items())
            numeric=finite_er_moments(n,float(edge*(n-1)))
            check(f'exact graph enumeration S2 N={n},p={edge}',math.isclose(numeric['s2'],float(expected2),rel_tol=1e-14,abs_tol=1e-14))
            check(f'exact graph enumeration S3 N={n},p={edge}',math.isclose(numeric['s3'],float(expected3),rel_tol=1e-14,abs_tol=1e-14))
            for q in (F(1,5),F(2,5),F(1,2),F(4,5)):
                pmf={}
                for profile,w in profiles.items():
                    for key,prob in law(profile,q).items():pmf[key]=pmf.get(key,F(0))+w*prob
                ex=lambda fn:expectation(pmf,fn);em=q*n;v2=ex(lambda x,m:(m-em)**2);v3=ex(lambda x,m:(m-em)**3);r2=ex(lambda x,m:x*x);cross=ex(lambda x,m:x*x*(m-em))
                check(f'volume third moment N={n},p={edge},q={q}',v3==q*(1-q)*(1-2*q)*expected3)
                check(f'network independent joint invariant N={n},p={edge},q={q}',(1-q)*v3*r2==(1-2*q)*cross*v2)
    f={'return_std':2.,'mean_abs_return':1.,'abs_return_q95':3.,'abs_return_q99':4.,'zero_return_fraction':.1,'volume_mean':30.,'volume_std':5.,'volume_q95':40.,'corr_volume_abs_return':.4}
    for factor in (.1,.5,1.,2.,100.):
        ff=dict(f)
        for key in ('return_std','mean_abs_return','abs_return_q95','abs_return_q99'):ff[key]*=factor
        check(f'scale invariant representation factor={factor}',all(abs(a-b)<1e-14 for a,b in zip(scale_invariant_joint(f),scale_invariant_joint(ff))))
    report={'status':'pass','checks':results,'count':len(results),'exact_fraction_moment_tests':True,'finite_ER_solver_compared_with_independent_exhaustive_graphs':True,'member_review':'not_run'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(f'{len(results)} depth method checks passed')


if __name__=='__main__':main()
