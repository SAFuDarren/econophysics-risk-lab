import csv,json,math,sys,unittest
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations,product
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from econophysics.model import Parameters,components,conditional_moments,aggregate_orders
from econophysics.physics_inference import finite_er_moments

class ModelTests(unittest.TestCase):
 def test_same_activity_tenfold_variance(self):
  p=Parameters(n=100,a=.1)
  a=conditional_moments([1]*100,p);b=conditional_moments([10]*10,p)
  self.assertEqual(a['mean_V'],b['mean_V']);self.assertAlmostEqual(a['var_V'],16);self.assertAlmostEqual(b['var_V'],160)
  self.assertAlmostEqual(b['var_r']/a['var_r'],10)
 def test_chain_star_complete_law(self):
  def law(edges):
   sizes=[len(g) for g in components(4,edges)];out={}
   for acts in product([-1,0,1],repeat=len(sizes)):
    probability=F(1)
    for x in acts:probability*=F(1,10) if x else F(4,5)
    pair=(sum(s*x for s,x in zip(sizes,acts)),sum(s*abs(x) for s,x in zip(sizes,acts)))
    out[pair]=out.get(pair,F(0))+probability
   return out
  a=law([(0,1),(1,2),(2,3)]);b=law([(0,1),(0,2),(0,3)])
  self.assertEqual(a,b);self.assertEqual(sum(a.values()),1);self.assertEqual(len(a),3)
 def test_finite_er_recurrence_against_graph_enumeration(self):
  n=4;edges=list(combinations(range(n),2))
  for p in [F(0),F(1,4),F(1,2),F(3,4),F(1)]:
   s2=s3=F(0)
   for bits in product([0,1],repeat=len(edges)):
    active=[e for e,on in zip(edges,bits) if on];prob=p**sum(bits)*(1-p)**(len(edges)-sum(bits))
    sizes=[len(g) for g in components(n,active)]
    s2+=prob*sum(s*s for s in sizes);s3+=prob*sum(s**3 for s in sizes)
   got=finite_er_moments(n,float(p*(n-1)))
   self.assertAlmostEqual(got['s2'],float(s2),places=11);self.assertAlmostEqual(got['s3'],float(s3),places=11)
 def test_all_orders_inactive(self):self.assertEqual(aggregate_orders([4],[0],Parameters(n=4)),(0,0))

class FrozenEvidenceTests(unittest.TestCase):
 def rows(self,name):
  with (ROOT/'results/tables'/name).open() as f:return list(csv.DictReader(f))
 def test_phase_workload(self):
  rows=self.rows('simulation_study_v1/phase_summary.csv');self.assertEqual(len(rows),27);self.assertEqual(sum(int(r['graphs']) for r in rows),1080)
 def test_all_forecast_scores_and_dates(self):
  rows=self.rows('forecast_v1/test_predictions.csv');dates=sorted({r['target_date'] for r in rows});self.assertEqual(len(dates),183)
  self.assertEqual((dates[0],dates[-1]),('2026-04-01','2026-09-30'))
  for r in rows:self.assertAlmostEqual((math.log(float(r['actual_rv']))-float(r['log_prediction']))**2,float(r['log_mse']),places=11)
  for model in {r['model'] for r in rows}:self.assertEqual(sum(r['model']==model for r in rows),183)
 def test_forecast_skill_reference(self):
  r=self.rows('forecast_v1/test_predictions.csv');loss={m:sum(float(x['log_mse']) for x in r if x['model']==m)/183 for m in ['Persistence','HAR','HAR+All']}
  self.assertAlmostEqual(100*(1-loss['HAR+All']/loss['Persistence']),31.20400030806677,places=9)
  self.assertEqual(round(100*(1-loss['HAR+All']/loss['HAR']),2),2.26)
 def test_delta_and_interval(self):
  row=next(x for x in self.rows('real_market_v1/market_metrics.csv') if x['source']=='Market H2' and x['metric']=='delta' and x['day_block_length']=='7')
  self.assertAlmostEqual(float(row['estimate']),-8.18148346674896);self.assertLess(float(row['ci_high']),0)
 def test_curve_strict_monotonicity(self):
  rows=self.rows('depth_study_v1/finite_er_curve.csv');self.assertEqual(len(rows),107)
  self.assertTrue(all(float(a['s2'])<float(b['s2']) for a,b in zip(rows,rows[1:])))

if __name__=='__main__':unittest.main()
