#!/usr/bin/env python3
"""Independent technical checks; NEVER selects the headline estimate."""
from pathlib import Path
import json,os,math
import numpy as np,pandas as pd
import statsmodels.api as sm
from patsy import dmatrix
from run_final import annual_data,projection,OUT,PAYS,SPONT,R

def check(test,msg):
 if not test:raise AssertionError(msg)

def ppml_comparison():
 a,units=annual_data(); results=[]
 for name,(field,coverage) in PAYS.items():
  d=a if name=='All medical expenditures' else a.loc[a[coverage]].copy()
  t=d.loc[d.phq_pos==1].copy()
  form='1 + phq_pos + age_centered + age2 + C(sex) + C(race) + C(pov) + C(educgrp) + C(ins) + C(reggrp) + C(year)'
  Xf=dmatrix(form,d,return_type='dataframe',NA_action='raise');X=Xf.to_numpy(float)
  y=d[field].to_numpy(float);w=d.weight.to_numpy(float);w=w/w.mean()
  # Poisson quasi-MLE estimates a conditional mean of nonnegative spending.
  # A Poisson conditional variance is NOT assumed for valid mean-model inference.
  result=sm.GLM(y,X,family=sm.families.Poisson(link=sm.families.links.Log()),var_weights=w).fit(maxiter=160)
  check(result.converged,f'{name} PPML convergence')
  b=np.asarray(result.params,float)
  Xtar=dmatrix(Xf.design_info,t,return_type='dataframe').to_numpy(float)
  cols=list(Xf.columns);j=cols.index('phq_pos')
  x0=Xtar.copy();x1=Xtar.copy();x0[:,j]=0;x1[:,j]=1
  for jj,c in enumerate(cols):
   if c.startswith('C(year)[T.'):
    year=int(c.split('[T.')[1].split(']')[0]);x0[:,jj]=x1[:,jj]=float(year==2024)
  tw=t.weight.to_numpy(float)
  v=float(np.average(np.exp(np.clip(x1@b,-25,25))-np.exp(np.clip(x0@b,-25,25)),weights=tw))
  primary=pd.read_csv(OUT/'annual_primary_models.csv').set_index('payer').loc[name,'annual_diff_positive_minus_negative_2024usd']
  results.append({'payer':name,'two_part_primary':primary,'single_part_PPML_validation':v,
        'difference_PPML_vs_primary':v-primary,'PPML_positive':v>0,'n_fit':len(d)})
  print('INDEPENDENT',name,'PPML',round(v),'PRIMARY',round(primary),flush=True)
 tab=pd.DataFrame(results);tab.to_csv(OUT/'APPENDIX_independent_PPML.csv',index=False)
 return tab

def math_and_output_checks():
 base=pd.read_csv(OUT/'FINAL_100_75_50_AND_BREAKEVEN.csv')
 a=pd.read_csv(OUT/'annual_primary_models.csv')
 proj=pd.read_csv(OUT/'projected_five_year_contributions.csv')
 audit=json.loads((OUT/'AUDIT.json').read_text())
 check(len(base)==12,'4 payers x 3 levels')
 check(a.shape[0]==4,'4 primary models')
 check(len(proj)==20,'five subsequent years per payer')
 check(a.logit_converged.all() and a.gamma_converged.all(),'GLM convergence')
 f=audit['projection_factor']
 check(np.isclose(sum(audit['projection_per_year']),f,atol=1e-13),'sum discounted years')
 check(np.isclose(f,1.3017825757363608,atol=1e-8),'independent longitudinal reference')
 for _,r in base.iterrows():
  head=a.set_index('payer').loc[r.payer,'annual_diff_positive_minus_negative_2024usd']
  check(np.isclose(r.five_year_unadjusted_value_usd,head*f,atol=1e-7),'5yr math')
  check(np.isclose(r.signed_model_credit_usd,head*f*(1-SPONT)*r.recognition_pct/100,atol=1e-7),'credit math')
  check(np.isclose(r.nonnegative_payment_candidate_usd,max(0,r.signed_model_credit_usd),atol=1e-7),'no negative payments')
  check(0<=r.conditional_probability_valuation_exceeds_payment<=1,'prob bound')
  check(r['95_interval_signed_credit_low_usd']<r['95_interval_signed_credit_high_usd'],'positive CI width')
 for payer,group in base.groupby('payer'):
  g=group.set_index('recognition_pct')
  check(g.loc[100,'nonnegative_payment_candidate_usd']>g.loc[75,'nonnegative_payment_candidate_usd']>g.loc[50,'nonnegative_payment_candidate_usd'],'ordered payment levels')
  check(g.loc[100,'conditional_probability_valuation_exceeds_payment']<g.loc[75,'conditional_probability_valuation_exceeds_payment']<g.loc[50,'conditional_probability_valuation_exceeds_payment']+1e-12,'monotonic break-even probabilities')
 # Independent 2-state transition matrix vs closed-form in random cases.
 rng=np.random.default_rng(139)
 for _ in range(25):
  rates=rng.uniform(0.01,.99,size=2)
  T=np.array([[1-rates[0],rates[0]],[1-rates[1],rates[1]]])
  p0=np.array([1.,0.]);p1=np.array([0.,1.]);S=0
  for k in range(5):
   S+=(p1[1]-p0[1])/(1+R)**(k+.5)
   p0=p0@T;p1=p1@T
  v,_=projection(rates)
  check(np.allclose(v,S,atol=1e-12),'Markov independent matrix verification')
 return {'all_4_models_converged':True,'credits_checked':len(base), 'state_matrix_crosschecks':25,
         'observed_transition_two_year':audit['two_year_validation'],
         'modelled_postremission_years':5,
         'nonnegative_credits':True,'conditional_breakeven_not_ACO_breakeven':True}

if __name__=='__main__':
 print('MATH',json.dumps(math_and_output_checks()),flush=True)
 t=ppml_comparison()
 print('VALIDATION_FINISHED')
 (OUT/'VALIDATION.json').write_text(json.dumps({'math_checks':math_and_output_checks(),
        'PPML_tab':t.to_dict('records'),'ppml_purpose':'Independent expenditure mean check only, not used to choose credit'},indent=2))
