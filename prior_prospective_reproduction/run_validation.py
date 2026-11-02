#!/usr/bin/env python3
"""Independent survey-WLS checks, finite differences, Markov arithmetic tests."""
import sys, math,json
from pathlib import Path
import numpy as np,pandas as pd
from patsy import dmatrix
from scipy.stats import t as tdist
import statsmodels.api as sm
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run_analysis import load,SRC,cluster_scores,survey_var,estimate_payer,exposure_factor,SPONT
OUT=HERE/'results'

def wls_adjusted(d,pay,roster,prior=False,winsor=None):
 y=d['cost_'+pay].to_numpy(float)
 if winsor:
  cap=np.quantile(y,winsor);y=y.clip(0,cap)
 w=d.w.to_numpy(float);w/=w.mean()
 form='1 + remitted + age_c + age_c2 + C(sex) + C(race_grp) + C(pov) + C(edu_grp) + C(ins) + C(region) + C(assess_year) + baseline_phq'
 if prior:
  d=d.assign(logprior=np.log1p(d['pre_'+pay]));form+=' + logprior'
 xdf=dmatrix(form,d,return_type='dataframe');X=np.asarray(xdf,float)
 if np.linalg.matrix_rank(X)!=X.shape[1]:return {'error':'rank deficiency'}
 H=X.T@(w[:,None]*X);b=np.linalg.solve(H,X.T@(w*y))
 assert np.allclose(b,sm.WLS(y,X,weights=w).fit().params,atol=1e-6,rtol=1e-8)
 resid=y-X@b
 scores=(w*resid)[:,None]*X
 u=cluster_scores(d,scores,roster)
 v,design=survey_var(u,roster)
 V=np.linalg.solve(H,np.linalg.solve(H,v).T).T
 idx=list(xdf.columns).index('remitted');val=-b[idx];se=np.sqrt(max(V[idx,idx],0));tcrit=tdist.ppf(.975,design['df_design'])
 return {'estimate':val,'se':se,'ci_low':val-tcrit*se,'ci_high':val+tcrit*se,'r2':float(sm.WLS(y,X,weights=w).fit().rsquared),'n':len(d),'cap':cap if winsor else None}

def run():
 cohort,T,roster,rates,meta=load();lst=[]
 for pay in SRC:
  dom=cohort if pay=='all' else cohort[cohort[pay]==1]
  for sp,kwargs in [('survey_WLS_core',{}),('survey_WLS_plus_prior',{'prior':True}),('survey_WLS_winsor99',{'winsor':.99})]:
   r=wls_adjusted(dom,pay,roster,**kwargs);r.update({'payer':pay,'spec':sp})
   lst.append(r)
   print(pay,sp,r,flush=True)
 d=pd.DataFrame(lst);d.to_csv(OUT/'linear_robustness.csv',index=False)
 # Numerical / analytical validation of five-year Markov calculation vs explicit state propagation
 def explicit(pr,pp):
  P=np.array([[1-pr,pr],[1-pp,pp]])
  a=np.array([1.,0.]);b=np.array([0.,1.]);v=0
  for k in range(5):
   v+=(b[1]-a[1])/(1.03)**(k+.5)
   a=a@P;b=b@P
  return v
 for pR in [.03,.15,.2373854,.49]:
  for pP in [.50,.62,.88]:
   assert np.isclose(explicit(pR,pP),exposure_factor(pR,pP),atol=1e-12)
 # Audit vs previously generated primary result
 main=pd.read_csv(OUT/'credits_100_75_50.csv')
 for pay in SRC:
  x=main[main.population==pay].set_index('recognition_pct')
  assert np.allclose([x.loc[75,'credit'],x.loc[50,'credit']],[.75*x.loc[100,'credit'],.5*x.loc[100,'credit']])
  assert x.loc[100,'spontaneous_rate_fixed']==SPONT
  assert np.allclose([x.loc[75,'uncertainty_low'],x.loc[50,'uncertainty_high']],
                     [.75*x.loc[100,'uncertainty_low'],.5*x.loc[100,'uncertainty_high']])
 (OUT/'validation.json').write_text(json.dumps({'Markov_closed_form_vs_explicit':'passed, 12 parameter cases',
   'linear_vs_statsmodels_WLS':'passed for all fitted checks','scaling_100_75_50':'passed',
   'remission_data_rows':len(cohort),'case_rate_non_causal':True},indent=2))

if __name__=='__main__':run()
