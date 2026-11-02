#!/usr/bin/env python3
"""Reproducible PHQ2-remission-specific prospective MEPS analysis.

PRIMARY: 4-year special MEPS panels 2018-21, 2019-22. Cohort positive PHQ2
in wave t, outcome negative vs positive in wave t+1, expenditure in calendar
year t+2. Separate payer-population risk sets. Survey weighted two-part
Binomial/Gamma-log cost regressions, Maryland core covariates and baseline
PHQ2 severity; design PSU Taylor covariance with standardized prediction IF.
Five-year Markov projection from assessment, prior-positive R/P states.
A predetermined 53% literature based spontaneous-remission rate is a POLICY
pricing convention, not causal attribution. 100/75/50% recognition.
No person-level respondent data are exported.
"""
from __future__ import annotations
import hashlib,io,json,math,sys,time,warnings,zipfile,os
from pathlib import Path
import numpy as np,pandas as pd
from scipy.special import expit
from scipy.stats import t as tdist, norm
from patsy import dmatrix
import statsmodels.api as sm
HERE=Path(__file__).resolve().parent
from enhanced_loader import load_extended,read_aux
DATA=Path(os.environ.get('MEPS_DATA_DIR','/mnt/data'));OUT=HERE/'results';OUT.mkdir(exist_ok=True)
CPI={2018:251.107,2019:255.657,2020:258.811,2021:270.970,2022:292.655,2023:304.702,2024:313.689}
FILES={2019:'h216dta.zip',2020:'h224dta.zip',2021:'h233dta.zip'}
SRC={'all':'TOTEXP','private':'TOTPRV','Medicare':'TOTMCR','Medicaid':'TOTMCD'}
SPONT=.53;DISCOUNT=.03;SEED=20261028

def assert_finite(x,msg='finite'):
 assert np.isfinite(np.asarray(x)).all(),msg

def annual_covariates():
 frames=[]
 with zipfile.ZipFile(DATA/'MEPS.zip') as outer:
  for year,nested in FILES.items():
   with zipfile.ZipFile(io.BytesIO(outer.read('MEPS/'+nested))) as z:
    fname=next(n for n in z.namelist() if n.endswith('.dta'))
    r=pd.io.stata.StataReader(io.BytesIO(z.read(fname)),convert_categoricals=False)
    yy=str(year)[-2:]
    cols=['DUPERSID','PANEL','EDUCYR','PHQ242',f'POVCAT{yy}',f'REGION{yy}',f'INSCOV{yy}',f'PRVEV{yy}',f'MCREV{yy}',f'MCDEV{yy}']
    d=r.read(columns=cols)
    d.columns=['DUPERSID','PANEL','edu','phq_check','pov','region','ins_check','private','Medicare','Medicaid']
    d['assess_year']=year;d.DUPERSID=d.DUPERSID.astype(str).str.strip()
    assert not d[['DUPERSID','assess_year']].duplicated().any()
    frames.append(d)
 return pd.concat(frames,ignore_index=True)

def load():
 raw=load_extended()
 assert raw.DUPERSID.is_unique
 a=read_aux('h36u24dta.zip',['DUPERSID','PANEL','STRA9624','PSU9624']);a.DUPERSID=a.DUPERSID.astype(str).str.strip()
 assert not a[['DUPERSID','PANEL']].duplicated().any()
 raw=raw.merge(a,on=['DUPERSID','PANEL'],how='left',validate='one_to_one')
 assert raw.STRA9624.notna().all() and raw.PSU9624.notna().all()
 all_units=raw[['STRA9624','PSU9624']].drop_duplicates().rename(columns={'STRA9624':'stratum','PSU9624':'psu'}).astype(int).set_index(['stratum','psu']).sort_index()
 mask=(raw.SAQRDS2468==1)&raw.LSAQWT.gt(0)&raw.AGEY1X.between(18,85)&raw.SEX.isin([1,2])&raw.RACETHX.ge(1)
 for phq in ['PHQ22','PHQ24','PHQ26','PHQ28']:mask &=raw[phq].between(0,6)
 for t in range(1,5):
  mask&=raw[f'AGEY{t}X'].between(18,85)&raw[f'INSCOVY{t}'].between(1,3)
  for v in SRC.values():mask &=raw[f'{v}Y{t}'].ge(0)
 s=raw.loc[mask].copy()
 assert len(s)==4496 and s.DUPERSID.is_unique
 phq=['PHQ22','PHQ24','PHQ26','PHQ28'];p=s[phq].ge(3).to_numpy(dtype=int)
 # Person-level influence functions for progression among previously positive
 at=np.zeros((len(s),2));bt=np.zeros((len(s),2));counts=np.zeros((2,2),int)
 for t in range(3):
  prev_positive=p[:,t]==1
  prev_remitted=(p[:,t]==0)&(p[:,:t].any(axis=1) if t>0 else np.zeros(len(s),bool))
  for j,frm in enumerate((prev_remitted,prev_positive)):
   at[:,j]+=frm*s.LSAQWT.to_numpy(float)
   bt[:,j]+=(frm&(p[:,t+1]==1))*s.LSAQWT.to_numpy(float)
   for k in range(2):counts[j,k]+=np.count_nonzero(frm&(p[:,t+1]==k))
 rates=bt.sum(0)/at.sum(0)
 assert np.allclose(rates,[.23738540123965116,.4884411781316796],atol=1e-9)
 rt=(bt-at*rates)/at.sum(0)
 tr_units=cluster_scores(s,np.asarray(rt),all_units)
 # 2 transitions per four-wave person, no double count of same year outcome
 rows=[]
 for t in (1,2):
  d=s.loc[p[:,t-1]==1].copy()
  d['assess_year']=d.start_year+t
  d['baseline_phq']=d[phq[t-1]]
  d['remitted']=(d[phq[t]]<3).astype(int)
  d['age']=d[f'AGEY{t+1}X']
  d['ins']=d[f'INSCOVY{t+1}']
  d['sex']=d.SEX;d['race_original']=d.RACETHX
  d['stratum']=d.STRA9624.astype(int);d['psu']=d.PSU9624.astype(int)
  d['w']=d.LSAQWT
  d['outcome_year']=d.start_year+t+1
  for pay,v in SRC.items():
   d['cost_'+pay]=d[f'{v}Y{t+2}']*d['outcome_year'].map(lambda y:CPI[2024]/CPI[int(y)])
   d['pre_'+pay]=d[f'{v}Y{t}']*d['start_year'].add(t-1).map(lambda y:CPI[2024]/CPI[int(y)])
  rows.append(d[['DUPERSID','PANEL','assess_year','baseline_phq','remitted','age','ins','sex','race_original','stratum','psu','w','outcome_year']+[f'cost_{k}' for k in SRC]+[f'pre_{k}' for k in SRC]])
 cohort=pd.concat(rows,ignore_index=True)
 cov=annual_covariates();n_initial=len(cohort)
 cohort=cohort.merge(cov,on=['DUPERSID','PANEL','assess_year'],how='left',validate='many_to_one',indicator=True)
 no_join=int((cohort._merge!='both').sum());cohort=cohort.loc[cohort._merge=='both'].drop(columns=['_merge']).copy()
 assert (cohort['phq_check'].ge(3)==(cohort.remitted==0)).all() # followup PHQ check
 assert (cohort.ins==cohort.ins_check).all()
 for col in ['private','Medicare','Medicaid']:
  assert cohort[col].isin([1,2]).all(),(col,cohort[col].value_counts().to_dict())
 cohort['pov']=cohort.pov.astype(int)
 cohort['region']=cohort.region.astype(int).clip(lower=0)
 # Region negative flags coded as their own missing stratum to retain sample
 cohort.loc[~cohort.region.between(1,4),'region']=0
 cohort['edu_grp']=pd.cut(cohort.edu,[-999,-1,11,12,15,99],labels=['unknown','<12','12','13-15','16+']).astype(str)
 cohort['edu_missing']=(~cohort.edu.between(0,17)).astype(int)
 cohort['edu_year']=np.where(cohort.edu.between(0,17),cohort.edu,12)
 cohort['race_grp']=cohort.race_original.clip(upper=3).astype(int)
 cohort['age_c']=cohort.age-50
 cohort['age_c2']=cohort.age_c**2/100
 assert_finite(cohort[['baseline_phq','age_c','age_c2','w']]);assert cohort.w.gt(0).all()
 assert all(cohort[f'cost_{k}'].ge(0).all() for k in SRC)
 assert set(cohort.assess_year.unique())=={2019,2020,2021}
 assert len(cohort)>650 and no_join<20
 sample=[]
 for pay in SRC:
  dom=cohort if pay=='all' else cohort.loc[cohort[pay]==1]
  sample.append({'payer':pay,'n_person_transitions':len(dom),'n_distinct_people':dom.DUPERSID.nunique(),
                 'n_remitted':int(dom.remitted.sum()),'n_persistent':int((1-dom.remitted).sum()),
                 'weighted_remission_rate':float(np.average(dom.remitted,weights=dom.w)),
                 'weighted_observed_cost_remitters_2024dollars':float(np.average(dom.loc[dom.remitted==1,'cost_'+pay],weights=dom.loc[dom.remitted==1,'w'])),
                 'weighted_observed_cost_persistent_2024dollars':float(np.average(dom.loc[dom.remitted==0,'cost_'+pay],weights=dom.loc[dom.remitted==0,'w']))})
 pd.DataFrame(sample).to_csv(OUT/'sample_summary.csv',index=False)
 tr_summary={'R_to_P':rates[0],'P_to_P':rates[1],'unweighted_transitions_RP':counts.tolist(),
             'n_fourwave_completers':len(s),'n_index_eligible_before_annual_link':n_initial,
             'n_missing_annual_link':no_join,'n_index_eligible':len(cohort),
             'full_unit_roster':len(all_units),'rate_den_weighted':at.sum(0).tolist(),
             'rate_num_weighted':bt.sum(0).tolist()}
 return cohort,tr_units,all_units,rates,tr_summary

def cluster_scores(d,score,roster):
 """sum person-level estimating equation influences within HC-036 PSU, zero-fill domain PSUs"""
 score=np.asarray(score,dtype=float)
 if score.ndim==1:score=score[:,None]
 df=pd.DataFrame(score,columns=range(score.shape[1]));df['stratum']=d['STRA9624'].to_numpy(int) if 'STRA9624' in d else d.stratum.to_numpy(int)
 df['psu']=d['PSU9624'].to_numpy(int) if 'PSU9624' in d else d.psu.to_numpy(int)
 agg=df.groupby(['stratum','psu'],observed=True).sum().reindex(roster.index,fill_value=0)
 return agg.to_numpy(float)

def survey_var(U,roster):
 """PSU finite-population survey contrast variance: sum_h m_h/(m_h-1) * within-h centered cross-products."""
 groups=roster.reset_index()['stratum'].to_numpy(int); V=np.zeros((U.shape[1],U.shape[1])); ns=0;singles=0
 for h in np.unique(groups):
  us=U[groups==h];m=len(us)
  if m<2:singles+=1;continue
  x=us-us.mean(axis=0);V+=(m/(m-1))*x.T@x;ns+=1
 return (V+V.T)/2,{'n_psus':len(groups),'n_strata':len(np.unique(groups)),
                       'n_multi_psu_strata':ns,'n_singleton_strata':singles,'df_design':len(groups)-len(np.unique(groups))}

def estimate_payer(cohort,payer,roster,sensitivity=False):
 dom=cohort if payer=='all' else cohort.loc[cohort[payer]==1].copy()
 # One person may contribute two separate 12-month baseline->remission transitions.
 # Matching outcome is the succeeding calendar year's spending, not the remission year's.
 yy=dom['cost_'+payer].to_numpy(float); w=dom.w.to_numpy(float)
 w=w/w.mean()
 form=('1 + remitted + age_c + age_c2 + C(sex) + C(race_grp) + '
       'C(pov) + edu_year + C(ins) + C(region) + C(assess_year) + baseline_phq')
 if dom.edu_missing.nunique()>1:form+=' + edu_missing'
 if sensitivity:
  dom=dom.assign(logpre=np.log1p(dom['pre_'+payer]));form+=' + logpre'
 Xdf=dmatrix(form,dom,return_type='dataframe',NA_action='raise')
 X=np.asarray(Xdf,float);names=list(Xdf.columns);idx=names.index('remitted');z=(yy>0).astype(float);positive=yy>0
 assert positive.sum()>X.shape[1]+15,(payer,'too few positive outcomes',positive.sum(),X.shape[1])
 if np.linalg.matrix_rank(X)<X.shape[1]:
  raise RuntimeError(f'{payer}: rank deficient {np.linalg.matrix_rank(X)}, {X.shape[1]}')
 with warnings.catch_warnings():
  warnings.simplefilter('ignore')
  lb=sm.GLM(z,X,family=sm.families.Binomial(),var_weights=w).fit(maxiter=200)
  gg=sm.GLM(yy[positive]/1000,X[positive],family=sm.families.Gamma(link=sm.families.links.Log()),var_weights=w[positive]).fit(maxiter=800,tol=1e-8)
 if not(lb.converged and gg.converged):
  print('FAIL_DETAILS',payer,'binomial',lb.converged,'gamma',gg.converged,'n_positive',int(positive.sum()),'n_zero',int((~positive).sum()),'n_parameters',X.shape[1],'ins_groups',dom.ins.value_counts().to_dict(),'race_groups',dom.race_grp.value_counts().to_dict(),'regions',dom.region.value_counts().to_dict(),flush=True)
  raise RuntimeError(f'{payer}: nonconvergence')
 b=lb.params;g=gg.params
 T0=X.copy();T1=X.copy();T0[:,idx]=0.;T1[:,idx]=1.
 p0=expit(T0@b);p1=expit(T1@b)
 m0=1000*np.exp(np.clip(T0@g,-30,30));m1=1000*np.exp(np.clip(T1@g,-30,30))
 pred0=p0*m0;pred1=p1*m1
 # fixed case remission savings = persistent less remitted
 dif=pred0-pred1
 val=float(np.average(dif,weights=w));W=w.sum()
 gb=np.average(pred0[:,None]*(1-p0[:,None])*T0-pred1[:,None]*(1-p1[:,None])*T1,axis=0,weights=w)
 ggamma=np.average(pred0[:,None]*T0-pred1[:,None]*T1,axis=0,weights=w)
 p=expit(X@b)
 bscore=(w*(z-p))[:,None]*X
 bH=X.T@((w*p*(1-p))[:,None]*X)
 pos_m=1000*np.exp(np.clip(X[positive]@g,-30,30))
 gscore=np.zeros_like(bscore)
 gscore[positive]=(w[positive]*(yy[positive]/pos_m-1))[:,None]*X[positive]
 gH=X[positive].T@((w[positive]*(yy[positive]/pos_m))[:,None]*X[positive])
 assert np.linalg.matrix_rank(bH)==X.shape[1] and np.linalg.matrix_rank(gH)==X.shape[1]
 psi=bscore@np.linalg.solve(bH,gb)+gscore@np.linalg.solve(gH,ggamma)+(w/W)*(dif-val)
 assert_finite(psi,payer)
 units=cluster_scores(dom,psi,roster)
 V,design=survey_var(units,roster)
 se=math.sqrt(max(0,V[0,0]));tcrit=tdist.ppf(.975,design['df_design'])
 # Verify one equation matrix against statsmodels result, weighted scores and margin identities
 assert np.max(np.abs(bscore.sum(0)))<.1,(payer,'binomial score failure')
 assert np.max(np.abs(gscore.sum(0)))<.1,(payer,'gamma score failure')
 assert abs(np.average(pred0-pred1,weights=w)-val)<1e-7
 assert (np.array([p0,p1]).min()>=0) and (pred0>=0).all() and (pred1>=0).all()
 assert se>=0 and np.isfinite(se)
 out={'payer':payer,'specification':'Maryland_core_plus_baseline_PHQ2'+('_and_prior_spending' if sensitivity else ''),
      'n_person_transitions':len(dom),'n_unique_people':dom.DUPERSID.nunique(),
      'n_remit':int(dom.remitted.sum()),'n_persist':int((1-dom.remitted).sum()),
      'n_positive_expense':int(positive.sum()),'model_parameters':len(names),
      'mean_persistent_cf':float(np.average(pred0,weights=w)),
      'mean_remitted_cf':float(np.average(pred1,weights=w)),
      'adjusted_next_year_savings':val,'survey_se':se,
      'ci_lower':val-tcrit*se,'ci_upper':val+tcrit*se,
      'weighted_raw_difference':float(np.average(yy[dom.remitted==0],weights=w[dom.remitted==0])-
                                     np.average(yy[dom.remitted==1],weights=w[dom.remitted==1])),
      'binomial_coefficient_remission':float(b[idx]),'gamma_coefficient_remission':float(g[idx]),
      'condition_number':float(np.linalg.cond(X)),**design}
 return out,units

def exposure_factor(pR,pP,discount=DISCOUNT,horizon=5):
 """Prospective 1-year cost association times probability difference in prior-positive PHQ state.
 Baseline at annual remission assessment: P for comparator, R for remitted.
 Next-year cost difference conditional on that baseline is represented by 1.
 For following years, both follow R->P and P->P transition probabilities.
 """
 q=np.asarray(pP)-np.asarray(pR)
 k=np.arange(horizon)
 return np.sum(q[...,None]**k/(1+discount)**(k+.5),axis=-1)

def test_exposure():
 assert np.isclose(exposure_factor(.25,.25,discount=0),1)
 assert np.isclose(exposure_factor(0,1,discount=0),5)
 assert np.isclose(exposure_factor(.5,.5,discount=0),1)
 assert np.isclose(exposure_factor(.2,.6,discount=0),sum(.4**k for k in range(5)))
 assert exposure_factor(.2,.6,discount=.03)<exposure_factor(.2,.6,discount=0)
 assert np.allclose(exposure_factor(np.array([.2,.3]),np.array([.6,.7])),
                    [exposure_factor(.2,.6)]*2)


def run():
 test_exposure(); start=time.time()
 cohort,T,roster,rates,transition_meta=load();print('loaded',len(cohort),'transitions',rates,flush=True)
 outcomes=[];columns=[]
 for pay in SRC:
  a,unit=estimate_payer(cohort,pay,roster)
  outcomes.append(a);columns.append(unit)
  print('primary',pay,'n',a['n_person_transitions'],'delta',round(a['adjusted_next_year_savings']),
        'se',round(a['survey_se']),'CI',round(a['ci_lower']),round(a['ci_upper']),flush=True)
 pds=pd.DataFrame(outcomes);pds.to_csv(OUT/'cost_models_primary.csv',index=False)
 joint_U=np.hstack(columns+[T]); cov,design=survey_var(joint_U,roster)
 assert cov.shape==(6,6) and (np.linalg.eigvalsh(cov).min()>=-1e-6)
 cov0=cov.copy();np.savetxt(OUT/'joint_survey_covariance.csv',cov0,delimiter=',')
 est=np.array([a['adjusted_next_year_savings'] for a in outcomes]+list(rates))
 assert np.allclose(np.diag(cov0)[:4],pds.survey_se.to_numpy()**2,rtol=1e-8)
 diag=np.sqrt(np.diag(cov0));cor=cov0/np.outer(diag,diag)
 assert np.all(np.abs(cor)<=1+1e-8)
 # Repeated cohort and transition observations share PSUs: draws preserve survey covariance.
 ev,ec=np.linalg.eigh(cov0);ev=np.maximum(ev,0)
 rng=np.random.default_rng(SEED);draw=est+rng.normal(size=(200000,6))@(ec@np.diag(np.sqrt(ev))).T
 draw[:,4:]=np.clip(draw[:,4:],1e-5,1-1e-5)
 f=exposure_factor(rates[0],rates[1]);fd=exposure_factor(draw[:,4],draw[:,5]);
 assert 1<=f<=5
 table=[];components=[]
 for i,pay in enumerate(SRC):
  delta=float(est[i]);raw_savings=delta*f
  annual=pds.iloc[i];v=draw[:,i]*fd
  for recognition in (1.,.75,.5):
   case=raw_savings*(1-SPONT)*recognition
   ds=v*(1-SPONT)*recognition
   lo,hi=np.quantile(ds,[.025,.975])
   table.append({'population':pay,'recognition_pct':int(100*recognition),
     'five_year_value_before_spontaneous_adjustment':raw_savings,
     'spontaneous_rate_fixed':SPONT,'credit':case,'uncertainty_low':lo,'uncertainty_high':hi,
     'probability_positive_under_model':float(np.mean(ds>0)),
     'n_transitions':int(annual['n_person_transitions']),
     'uncertainty_type':'95% model-parameter interval, conditional on fixed spontaneous 53% and transition model'})
  for k in range(5):
   factor=(rates[1]-rates[0])**k/(1+DISCOUNT)**(k+.5)
   components.append({'population':pay,'future_year':k+1,'probability_positive_difference':(rates[1]-rates[0])**k,
        'year_pv_savings_2024dollars':delta*factor,'year_pv_case_credit_100pct':delta*factor*(1-SPONT)})
 result=pd.DataFrame(table);result.to_csv(OUT/'credits_100_75_50.csv',index=False)
 pd.DataFrame(components).to_csv(OUT/'year_by_year.csv',index=False)
 # Unadjusted comparisons, alternative direct one-year prospective age etc regression yields model sensitivity.
 checks=[]
 for pay in SRC:
  dom=cohort if pay=='all' else cohort.loc[cohort[pay]==1]
  gr=dom.groupby('remitted')
  m={k:np.average(g['cost_'+pay],weights=g.w) for k,g in gr}
  checks.append({'payer':pay,'raw_persistent_minus_remit':m[0]-m[1],
     'fit_estimate':float(pds.loc[pds.payer==pay,'adjusted_next_year_savings'].iloc[0]),
     'positive_case_rate_100':float(result.loc[(result.population==pay)&(result.recognition_pct==100),'credit'].iloc[0])})
 pd.DataFrame(checks).to_csv(OUT/'audit_group_checks.csv',index=False)
 eig0=np.linalg.eigvalsh(cov0)
 audit={'inputs':{n:hashlib.sha256((DATA/n).read_bytes()).hexdigest() for n in
           ['MEPS.zip','More MEPS.zip','h36u24dta.zip']},
   'sample':transition_meta,'design':design,'transition_rates':{'R_to_P':rates[0],'P_to_P':rates[1],
     'delta_risk':rates[1]-rates[0],
     '95_se_R_to_P':math.sqrt(cov0[-2,-2]),'95_se_P_to_P':math.sqrt(cov0[-1,-1])},
   'cost_and_transition_joint_covariance_matrix_order':list(SRC)+['R_to_P','P_to_P'],
   'cost_and_transition_joint_corr_matrix':np.round(cor,4).tolist(),
   'eigenvalues_covariance':eig0.tolist(),
   'exposure_years_discounted':f,'discount':DISCOUNT,
   'spontaneous_remission_rate_policy_input':SPONT,'simulations':len(draw),
   'case_credit_identity_all':all(abs(row.credit-row.five_year_value_before_spontaneous_adjustment*(1-SPONT)*row.recognition_pct/100)<1e-7 for row in result.itertuples()),
   'same_half_cycle_5_years_no_state_gap':True,
   'no_intervention_effectiveness_used':True,
   'no_bipolar_stratification_used':True,
   'primary_models_converged':True,
   'rank_model_primary_all':True,
   'expenditure_year_strictly_after_assessment':bool((cohort.outcome_year>cohort.assess_year).all()),
   'cost_source_not_exceed_total_approx':all(bool((cohort[f'cost_{k}']<=cohort.cost_all+1e-6).all()) for k in ['private','Medicare','Medicaid']),
   'elapsed_sec':time.time()-start,
   'method_limitations':['PHQ2 proxy not PHQ9 verified remission','52.999 percent published untreated clinical depression remission may not transfer to PHQ2 transitions','4-year complete-case cohort and 2018-2022 followup','5-year extrapolation beyond observed followup','not causal savings','observational selection and unmeasured confounding','spontaneous parameter fixed: uncertainty intervals conditional','mortality and differential nonresponse unmodeled']}
 (OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2,default=float))
 print('FINAL CREDITS',result.to_string(index=False,float_format=lambda x:f'{x:.2f}'),flush=True)
 print('DONE',time.time()-start,flush=True)

if __name__=='__main__':run()
