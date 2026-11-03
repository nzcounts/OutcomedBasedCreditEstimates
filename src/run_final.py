#!/usr/bin/env python3
"""MEPS PHQ-2 symptom-state expenditure valuation under a fixed policy scenario.

Annual 2019-2024 cross-sectional two-part expenditure contrasts are standardized
to currently screen-positive adults in each payer population, in 2024 dollars.
Four-wave screen transitions inform five hypothetical future annual state rewards.
The negative state includes previously positive people beyond their first negative
screen. A clinical 12-month remission landmark is a projection assumption.
The model applies 3% midyear discounting and a fixed 53% policy adjustment.
Annual and transition covariance are simulated without cross-source covariance,
despite overlapping respondents. The two-year and PPML checks reuse source data.
These are conditional valuations, not identified clinical-remission savings.
"""
from __future__ import annotations
import os,io,zipfile,hashlib,json,math,warnings,time,sys
from pathlib import Path
import pandas as pd,numpy as np
import statsmodels.api as sm
from scipy.special import expit
from scipy.stats import t as student_t
from patsy import dmatrix
from enhanced_loader import load_extended,read_aux
ROOT=Path(os.environ.get('MEPS_DATA_DIR',str(Path(__file__).resolve().parents[1]/'data'/'raw')))
BASE=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('MEPS_OUTPUT_DIR',str(BASE/'results'/'primary')));OUT.mkdir(parents=True,exist_ok=True)
CPI={2019:255.657,2020:258.811,2021:270.970,2022:292.655,2023:304.702,2024:313.689}
YEAR_FILES={2019:'h216dta.zip',2020:'h224dta.zip',2021:'h233dta.zip',2022:'h243dta.zip',2023:'h251dta.zip',2024:'h256dta.zip'}
PAYS={'All medical expenditures':('total','ever_private'),
      'Medicare':('medicare','ever_medicare'),
      'Medicaid':('medicaid','ever_medicaid'),
      'Private insurance':('private','ever_private')}
SPONT=.53;R=.03;DRAWS=120000;SEED=20261028

def check(z,msg):
 if not z:raise AssertionError(msg)

def annual_data():
 frames=[];roster=[];aud=[]
 with zipfile.ZipFile(ROOT/'MEPS.zip') as outer:
  for year,nested in YEAR_FILES.items():
   with zipfile.ZipFile(io.BytesIO(outer.read('MEPS/'+nested))) as inner:
    nm=next(x for x in inner.namelist() if x.endswith('.dta'))
    rd=pd.io.stata.StataReader(io.BytesIO(inner.read(nm)),convert_categoricals=False);rd._ensure_open()
    yy=str(year)[-2:]
    colnames={
      'id':'DUPERSID','panel':'PANEL','age':('AGELAST' if 'AGELAST' in rd._varlist else f'AGE{yy}X'),
      'sex':'SEX','race':'RACETHX','pov':f'POVCAT{yy}','ins':f'INSCOV{yy}',
      'phq':'PHQ242','weight':f'SAQWT{yy}F','stratum':'VARSTR','psu':'VARPSU',
      'total':f'TOTEXP{yy}','private':f'TOTPRV{yy}','medicare':f'TOTMCR{yy}','medicaid':f'TOTMCD{yy}',
      'ever_private':f'PRVEV{yy}','ever_medicare':f'MCREV{yy}','ever_medicaid':f'MCDEV{yy}',
      'edu':'EDUCYR','region':f'REGION{yy}' }
    check(set(colnames.values()).issubset(rd._varlist),str((year,set(colnames.values())-set(rd._varlist))))
    d=rd.read(columns=list(colnames.values())).rename(columns={v:k for k,v in colnames.items()})
   d['year']=year;d.id=d.id.astype(str).str.strip()
   check(not d.id.duplicated().any(),f'duplicate {year}')
   roster.append(d[['stratum','psu']].drop_duplicates())
   good=(d.age.between(18,85)&d.phq.between(0,6)&d.weight.gt(0)&d.sex.isin([1,2])&d.race.ge(1)&d.pov.ge(1)&d.ins.ge(1)&d.region.between(1,4))
   audited={'year':year,'total_persons':len(d),'eligible_adults':int(good.sum()),'screen_positive':int(((d.phq>=3)&good).sum())}
   for c in ['total','private','medicare','medicaid']:
    check(d[c].ge(0).all(),f'negative {year} {c}')
    audited['total_'+c]=float(d.loc[good,c].sum())
    d[c]=d[c]*(CPI[2024]/CPI[year])
   check((d['total']+5>=d[['private','medicare','medicaid']].sum(axis=1)).all(),f'payers > total {year}')
   d=d.loc[good].copy()
   d['phq_pos']=(d.phq>=3).astype(int)
   d['race']=d.race.clip(1,6).astype(int)
   d['pov']=d.pov.clip(1,5).astype(int)
   d['ins']=d.ins.clip(1,3).astype(int)
   d['educgrp']=pd.cut(d.edu,[-np.inf,11.5,12.5,15.5,np.inf],labels=['less_hs','hs','some_college','college_plus']).astype('object').fillna('unknown')
   d.loc[d.edu<0,'educgrp']='unknown';d['educgrp']=d.educgrp.astype(str)
   d['reggrp']=d.region.where(d.region.between(1,4),5).astype(int)
   for cov in ['ever_private','ever_medicare','ever_medicaid']:d[cov]=d[cov].eq(1)
   d['age_centered']=(d.age-50)/20
   d['age2']=d.age_centered**2
   frames.append(d);aud.append(audited)
 all_=pd.concat(frames,ignore_index=True)
 units=pd.concat(roster).drop_duplicates().astype(int).set_index(['stratum','psu']).sort_index()
 check(len(all_)==77487,f'annual eligible after excluding 2 missing-region records != expected: {len(all_)}')
 check(int(all_.phq_pos.sum())==6604,'annual positive count')
 check(len(units)>300,'annual survey PSU roster')
 check(not all_[['year','id']].duplicated().any(),'annual duplicate keys')
 pd.DataFrame(aud).to_csv(OUT/'annual_sample_by_year.csv',index=False)
 return all_,units

def design_variance(unit_score,roster):
 """Stratified multistage ultimate-cluster variance with zero domain PSUs."""
 u=np.asarray(unit_score,float);group=roster.reset_index().stratum.to_numpy(int)
 check(len(u)==len(group),'PSU score dimension')
 v=np.zeros((u.shape[1],u.shape[1]));n_singleton=0
 for h in np.unique(group):
  x=u[group==h]
  if len(x)<2:n_singleton+=1;continue
  r=x-x.mean(0)
  v+=len(x)/(len(x)-1)*(r.T@r)
 v=(v+v.T)/2
 return v,{'n_psu':len(group),'n_strata':len(np.unique(group)),'n_singleton_strata':n_singleton,'df_design':len(group)-len(np.unique(group))}

def unit_sum(df,score,roster):
 z=np.asarray(score,float)
 if z.ndim==1:z=z[:,None]
 y=pd.DataFrame(z,columns=list(range(z.shape[1])))
 y['stratum']=df.stratum.to_numpy(int);y['psu']=df.psu.to_numpy(int)
 return y.groupby(['stratum','psu'],observed=True).sum().reindex(roster.index,fill_value=0).to_numpy(float)

def primary_model(data,roster,label,field,coverage):
 dom=data if label=='All medical expenditures' else data.loc[data[coverage]].copy()
 target=dom.loc[dom.phq_pos.eq(1)].copy()
 check(len(target)>150,f'{label} small baseline target')
 y=dom[field].to_numpy(float)
 w=dom.weight.to_numpy(float);w/=w.mean()
 z=(y>0).astype(float);positive=z==1
 # Maryland core age/square, sex, race, poverty, education, insurance,
 # Census region, year, symptom-state indicator. No expanded comorbidity.
 form='1 + phq_pos + age_centered + age2 + C(sex) + C(race) + C(pov) + C(educgrp) + C(ins) + C(reggrp) + C(year)'
 Xf=dmatrix(form,dom,return_type='dataframe',NA_action='raise');cols=list(Xf.columns)
 X=Xf.to_numpy(float);k=len(cols);j=cols.index('phq_pos')
 check(np.linalg.matrix_rank(X)==k,f'{label} design rank')
 check(min(np.count_nonzero(z),len(z)-np.count_nonzero(z))>k*2,f'{label} sparse spending positivity')
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',FutureWarning)
  logit=sm.GLM(z,X,family=sm.families.Binomial(),var_weights=w).fit(maxiter=150)
  gamma=sm.GLM(y[positive],X[positive],family=sm.families.Gamma(link=sm.families.links.Log()),var_weights=w[positive]).fit(maxiter=150)
 check(bool(logit.converged and gamma.converged),f'{label} GLM convergence')
 b=np.asarray(logit.params,float);g=np.asarray(gamma.params,float)
 p=expit(X@b);m=np.exp(np.clip(X[positive]@g,-30,30))
 sb=(w*(z-p))[:,None]*X
 sg=np.zeros_like(sb);sg[positive]=((w[positive]*(y[positive]/m-1))[:,None]*X[positive])
 H_b=X.T@((w*p*(1-p))[:,None]*X)
 H_g=X[positive].T@((w[positive]*(y[positive]/m))[:,None]*X[positive])
 print('HESSIAN',label,'COND',np.linalg.cond(H_b),np.linalg.cond(H_g),'ZERO',int((z==0).sum()),flush=True)
 check(np.linalg.cond(H_b)<1e11 and np.linalg.cond(H_g)<1e11,f'{label} Hessian illconditioned')
 scores_b=unit_sum(dom,sb,roster);scores_g=unit_sum(dom,sg,roster)
 # Target STANDARDIZED TO CURRENTLY SYMPTOMATIC PHQ-2 POSITIVES, not all adults.
 T=dmatrix(Xf.design_info,target,return_type='dataframe').to_numpy(float)
 t0=T.copy();t1=T.copy();t0[:,j]=0;t1[:,j]=1
 for ix,name in enumerate(cols):
  if name.startswith('C(year)[T.'):
   yy=int(name.split('[T.')[1].split(']')[0]);t0[:,ix]=t1[:,ix]=float(yy==2024)
 tw=target.weight.to_numpy(float);tw/=tw.mean();wt=tw.sum()
 def calc(bb,gg,derivative=False):
  p0=expit(t0@bb);p1=expit(t1@bb)
  mu0=np.exp(np.clip(t0@gg,-30,30));mu1=np.exp(np.clip(t1@gg,-30,30))
  v0=p0*mu0;v1=p1*mu1
  margin=float(np.dot(tw,v1-v0)/wt)
  if not derivative:return margin,(float(np.dot(tw,v0)/wt),float(np.dot(tw,v1)/wt)),v1-v0
  gb=((tw*v1*(1-p1))[:,None]*t1-(tw*v0*(1-p0))[:,None]*t0).sum(0)/wt
  gg=((tw*v1)[:,None]*t1-(tw*v0)[:,None]*t0).sum(0)/wt
  return margin,gb,gg,v1-v0
 delta,gb,gg,individual=calc(b,g,derivative=True)
 v_b=np.linalg.solve(H_b,gb);v_g=np.linalg.solve(H_g,gg)
 infl=scores_b@v_b+scores_g@v_g
 infl+=unit_sum(target,tw*(individual-delta)/wt,roster).reshape(-1)
 var,dsgn=design_variance(infl.reshape(-1,1),roster)
 se=math.sqrt(max(float(var[0,0]),0))
 check(np.isfinite([delta,se]).all() and se>0,f'{label} cost contrast finite')
 # Numerical verification of the standardized predictions / model IF derivatives.
 for coeff in [j,0,k-1]:
  eps=2e-6
  be=b.copy();be[coeff]+=eps
  ab=(calc(be,g)[0]-calc(b,g)[0])/eps
  check(np.isclose(ab,gb[coeff],rtol=3e-3,atol=.01),f'{label} logit finite difference {coeff}')
  ge=g.copy();ge[coeff]+=eps
  ag=(calc(b,ge)[0]-calc(b,g)[0])/eps
  check(np.isclose(ag,gg[coeff],rtol=3e-3,atol=.01),f'{label} gamma finite difference {coeff}')
 means=calc(b,g)[1]
 result={'payer':label,'n_model':len(dom),'n_index_screen_positive':len(target),'n_screen_negative_in_model':int((dom.phq_pos==0).sum()),
     'zero_spending_n':int((y==0).sum()),'n_model_parameters':k,'survey_psu_count':dsgn['n_psu'],
     'annual_depression_positive_cost_2024usd':means[1],
     'annual_remitted_state_cost_2024usd':means[0],
     'annual_diff_positive_minus_negative_2024usd':delta,'annual_diff_survey_se':se,
     'annual_diff_ci_low':delta-1.96*se,'annual_diff_ci_high':delta+1.96*se,
     'logit_converged':bool(logit.converged),'gamma_converged':bool(gamma.converged),
     'positive_spending_probability':float(np.average(z,weights=w)),
     'weighted_baseline_symptomatic_share':float(np.average(dom.phq_pos,weights=dom.weight)),
     'model_family':'survey-weighted two-part logit / Gamma log',
     'target_population':'PHQ2 positive at baseline among payer-covered adults'}
 return result, infl, dsgn

def longitudinal_4wave():
 raw=load_extended()
 aux=read_aux('h36u24dta.zip',['DUPERSID','PANEL','STRA9624','PSU9624'])
 aux.DUPERSID=aux.DUPERSID.astype(str).str.strip()
 raw=raw.merge(aux,on=['DUPERSID','PANEL'],how='left',validate='one_to_one')
 check(raw.STRA9624.notna().all(),'4yr missing PSU')
 roster=raw[['STRA9624','PSU9624']].drop_duplicates().rename(columns={'STRA9624':'stratum','PSU9624':'psu'}).astype(int).set_index(['stratum','psu']).sort_index()
 mask=raw.SAQRDS2468.eq(1)&raw.LSAQWT.gt(0)&raw.AGEY1X.between(18,85)&raw.SEX.isin([1,2])&raw.RACETHX.ge(1)
 for phq in ['PHQ22','PHQ24','PHQ26','PHQ28']:mask&=raw[phq].between(0,6)
 for j in range(1,5):
  mask&=raw[f'AGEY{j}X'].between(18,85)&raw[f'INSCOVY{j}'].between(1,3)
  for c in ['TOTEXP','TOTPRV','TOTMCR','TOTMCD']:
   mask&=raw[f'{c}Y{j}'].ge(0)
 s=raw.loc[mask].copy()
 check(len(s)>=4400,'4wave sample count')
 states=s[['PHQ22','PHQ24','PHQ26','PHQ28']].ge(3).to_numpy(dtype=int)
 wt=s.LSAQWT.to_numpy(float)
 at=np.zeros((len(s),2));bt=np.zeros((len(s),2));count=np.zeros((2,2),int)
 for j in range(3):
  # State R: observed screen negative following any positive screen in earlier waves;
  # state P: currently positive screen. A two-state Markov model after index-positive.
  pos=states[:,j]==1
  prior_remit=(states[:,j]==0)&(states[:,:j].any(1) if j>0 else np.zeros(len(s),bool))
  for i,at_risk in enumerate([prior_remit,pos]):
   at[:,i]+=at_risk*wt
   bt[:,i]+=(at_risk&(states[:,j+1]==1))*wt
   for v in [0,1]:count[i,v]+=int((at_risk&(states[:,j+1]==v)).sum())
 rates=bt.sum(0)/at.sum(0)
 inf=(bt-at*rates)/at.sum(0)
 s=s.assign(stratum=s.STRA9624.astype(int),psu=s.PSU9624.astype(int))
 vi,design=design_variance(unit_sum(s,inf,roster),roster)
 check(np.linalg.eigvalsh(vi).min()>-1e-9,'transitions variance PSD')
 check(np.allclose(rates,[.23738540123965116,.4884411781316796],atol=1e-10),'transition replication')
 return rates,vi,{'n_people_fourwave':len(s),'n_recorded_transitions':int(count.sum()),
      'n_postpositive_remitted_transitions':int(count[0].sum()),'n_positive_state_transitions':int(count[1].sum()),
      'counts':count.tolist(), 'survey':design,'p_R_to_P':float(rates[0]),'p_P_to_P':float(rates[1]),
      'se_R_to_P':float(np.sqrt(vi[0,0])),'se_P_to_P':float(np.sqrt(vi[1,1])),'correlation':float(vi[0,1]/np.sqrt(vi[0,0]*vi[1,1]))}

def two_year_audit(a):
 """Annual-year PHQ2 within standard two-year panels: descriptive check with overlapping samples.
 Does not use annual MEPS expenditure during the year remission was documented
 as downstream outcome. Transition estimates are not substituted for the primary
 four-year recurrence model because standard-panel weights do not adjust for
 the full four-year selection process and samples overlap.
 """
 base=a.loc[a.year.between(2019,2023),['id','panel','year','phq_pos','weight','stratum','psu']].copy()
 nxt=a[['id','panel','year','phq_pos']].copy()
 nxt.year-=1
 nxt=nxt.rename(columns={'phq_pos':'next_phq_pos'})
 pairs=base.merge(nxt,on=['id','panel','year'],validate='one_to_one',how='inner')
 check(pairs.id.notna().all(),'2year joined IDs')
 rates=[]
 for p in [0,1]:
  d=pairs.loc[pairs.phq_pos.eq(p)]
  rates.append({'from_positive':p,'n_pairs':len(d),'n_next_positive':int(d.next_phq_pos.sum()),
        'weighted_next_positive':float(np.average(d.next_phq_pos,weights=d.weight))})
 pd.DataFrame(rates).to_csv(OUT/'two_year_panel_transition_check.csv',index=False)
 return rates

def projection(rates,years=5):
 """Five years STARTING AFTER 12-month remission landmark (not treatment year).
 At the beginning of projected year 1, two hypothetical trajectories have states P
 and R; no matched-person comparison is estimated. Expected exposure difference in years j=1,...,5 is q**(j-1), with
 q = P(P->P)-P(R->P). Returns mid-year discounted annual state-year units.
 Within-year PHQ transitions are unobserved; annual state-reward convention.
 """
 p=np.asarray(rates,float)
 q=p[...,1]-p[...,0]
 factor=np.zeros_like(q,float)
 contributions=[]
 for k in range(years):
  v=np.power(q,k)/np.power(1+R,k+0.5)
  factor=factor+v
  contributions.append(v)
 return factor,contributions

def headline(a,roster):
 rates,cv,tr=longitudinal_4wave()
 annual=[];unit_if=[];audit={}
 for label,(field,cover) in PAYS.items():
  result,ifv,sg=primary_model(a,roster,label,field,cover)
  annual.append(result);unit_if.append(ifv);audit[label]=sg
  print('MODEL',label,'N',result['n_model'],'targetN',result['n_index_screen_positive'],
        'annualDiff',round(result['annual_diff_positive_minus_negative_2024usd']),
        'SE',round(result['annual_diff_survey_se']),flush=True)
 pd.DataFrame(annual).to_csv(OUT/'annual_primary_models.csv',index=False)
 # Cross-payer correlations in annual survey estimates are retained in the
 # empirical joint annual IF covariance (payers cover overlapping populations).
 costIF=np.column_stack(unit_if);cov,dsgn=design_variance(costIF,roster)
 check(np.linalg.eigvalsh(cov).min()>-1e-8,'joint payer covariance PSD')
 means=np.array([x['annual_diff_positive_minus_negative_2024usd'] for x in annual])
 rng=np.random.default_rng(SEED)
 vals,vec=np.linalg.eigh(cov)
 cost_draws=rng.standard_normal((DRAWS,4))@(vec@np.diag(np.sqrt(np.maximum(vals,0)))).T+means
 tr_eig,tr_vec=np.linalg.eigh(cv)
 transition_draws=rng.standard_normal((DRAWS,2))@(tr_vec@np.diag(np.sqrt(np.maximum(tr_eig,0)))).T+rates
 transition_draws=np.clip(transition_draws,1e-5,1-1e-5)
 fact,ann=projection(rates);f_draws,_=projection(transition_draws)
 check(fact>0,'5year factor positive')
 # assert exact state dynamics independent implementation for k=0..4
 T=np.array([[1-rates[0],rates[0]],[1-rates[1],rates[1]]])
 u=np.array([1.,0.]);v=np.array([0.,1.]);indep=[]
 for k in range(5):
  indep.append((v[1]-u[1])/((1+R)**(k+.5)))
  u=u@T;v=v@T
 check(np.allclose(ann,indep,atol=1e-14),'Markov matrix projection exact')
 records=[];annual_year=[]
 for i,x in enumerate(annual):
  lab=x['payer'];d=cost_draws[:,i]*f_draws
  fv=means[i]*fact
  rate=fv*(1-SPONT)
  nd=d*(1-SPONT)
  lo,hi=np.quantile(nd,[.025,.975]);
  annual_year.extend([{'payer':lab,'year_after_remission':j+1,'discounted_state_years':float(ann[j]),
     'projected_value_2024usd':float(means[i]*ann[j])} for j in range(5)])
  for alpha in [1.,.75,.5]:
   proposal=rate*alpha
   # Rates cannot be negative payable credits. Report signed estimate separately.
   payable=max(0.,proposal)
   p_be=float(np.mean(nd>=payable))
   records.append({'payer':lab,'recognition_pct':int(round(alpha*100)),
     'annual_symptom_state_diff_2024usd':float(means[i]),
     'annual_symptom_state_se_2024usd':float(x['annual_diff_survey_se']),
     'discounted_state_year_multiplier':float(fact),
     'five_year_unadjusted_value_usd':float(fv),
     'spontaneous_remission_assumption':SPONT,
     'spontaneous_adjusted_5y_value_usd':float(rate),
     'signed_model_credit_usd':float(proposal),
     'nonnegative_payment_candidate_usd':float(payable),
     '95_interval_signed_credit_low_usd':float(lo*alpha),
     '95_interval_signed_credit_high_usd':float(hi*alpha),
     'conditional_probability_valuation_exceeds_payment':p_be,
     'probability_savings_value_positive':float(np.mean(nd>0)),
     'confidence_conditional':'sampling and estimated transition rates, fixed spontaneous rate; model extrapolation, causal inference not included'})
 pd.DataFrame(records).to_csv(OUT/'FINAL_100_75_50_AND_BREAKEVEN.csv',index=False)
 pd.DataFrame(annual_year).to_csv(OUT/'projected_five_year_contributions.csv',index=False)
 pd.DataFrame(cov,index=list(PAYS),columns=list(PAYS)).to_csv(OUT/'joint_payer_survey_covariance.csv')
 pd.DataFrame(cv,index=['R_to_P','P_to_P'],columns=['R_to_P','P_to_P']).to_csv(OUT/'four_year_transition_covariance.csv')
 summary={'definition':__doc__,'sample_n_annual':len(a),'n_annual_screen_positive':int(a.phq_pos.sum()),
          'tr4':tr,'two_year_validation':two_year_audit(a),'projection_factor':float(fact),
          'projection_per_year':[float(x) for x in ann],'spontaneous_remission_rate':SPONT,'cpi_2024':CPI,
          'annual_design':dsgn,'annual_survey_compatibility':'pooled 2019-2024 VARSTR VARPSU, full PSU roster',
          'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['MEPS.zip','More MEPS.zip','h36u24dta.zip']},
          'assumption_warning':'conditional breakeven = P(estimated discount-adjusted valuation >= fixed proposed payment), NOT P(ACO financial surplus).'}
 (OUT/'AUDIT.json').write_text(json.dumps(summary,indent=2))
 # Strict arithmetic and nonnegativity checks.
 res=pd.DataFrame(records)
 for payer in PAYS:
  sub=res.loc[res.payer==payer].set_index('recognition_pct')
  for f in [.75,.5]:
   j=int(f*100)
   for col in ['signed_model_credit_usd','95_interval_signed_credit_low_usd','95_interval_signed_credit_high_usd']:
    check(np.isclose(sub.loc[j,col],sub.loc[100,col]*f,atol=1e-6),f'credit linear scale {payer} {col}')
  check(sub.nonnegative_payment_candidate_usd.ge(0).all(),'nonnegative payment')
  check((sub.conditional_probability_valuation_exceeds_payment>=0).all() and (sub.conditional_probability_valuation_exceeds_payment<=1).all(),'prob bounds')
 print('PRIMARY TABLE\n',res[['payer','recognition_pct','signed_model_credit_usd','95_interval_signed_credit_low_usd','95_interval_signed_credit_high_usd','conditional_probability_valuation_exceeds_payment']].to_string(index=False),flush=True)
 return res

def run():
 st=time.time();a,roster=annual_data();print('ANNUAL',len(a),'PSU',len(roster),flush=True)
 r=headline(a,roster)
 print('COMPLETED seconds',round(time.time()-st),flush=True)
 return r
if __name__=='__main__':run()
