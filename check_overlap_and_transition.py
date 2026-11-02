import sys
import numpy as np
import pandas as pd
sys.path.insert(0,'/mnt/data/MEPS_final_NPVoC_2026-10-28/code')
from run_final import annual_data
from enhanced_loader import load_extended
A,_=annual_data()
base=A.loc[A.year.between(2019,2023),['id','panel','year','phq_pos','weight']].copy()
nxt=A[['id','panel','year','phq_pos']].copy();nxt.year-=1;nxt=nxt.rename(columns={'phq_pos':'next_phq_pos'})
pairs=base.merge(nxt,on=['id','panel','year'],validate='one_to_one')
L=load_extended()
ids=set(zip(L.DUPERSID.astype(str).str.strip(),L.PANEL))
positive=pairs.loc[pairs.phq_pos.eq(1)].copy()
positive['in_longitudinal_source']=[(x,y) in ids for x,y in zip(positive.id,positive.panel)]
print('two_year_positive_pairs',len(positive),'in_fourwave_source',positive.in_longitudinal_source.sum())
# Those who pass the four-wave analytic subset: reproduce masks except unused design merge.
mask=L.SAQRDS2468.eq(1)&L.LSAQWT.gt(0)&L.AGEY1X.between(18,85)&L.SEX.isin([1,2])&L.RACETHX.ge(1)
for phq in ['PHQ22','PHQ24','PHQ26','PHQ28']:mask &= L[phq].between(0,6)
for j in range(1,5):
 mask &= L[f'AGEY{j}X'].between(18,85)&L[f'INSCOVY{j}'].between(1,3)
 for c in ['TOTEXP','TOTPRV','TOTMCR','TOTMCD']:
  mask &= L[f'{c}Y{j}'].ge(0)
S=L.loc[mask].copy()
ids_eligible=set(zip(S.DUPERSID.astype(str).str.strip(),S.PANEL))
positive['eligible_fourwave']=[(x,y) in ids_eligible for x,y in zip(positive.id,positive.panel)]
print('two_year_positive_pairs_from_fourwave_eligible_people',int(positive.eligible_fourwave.sum()),'share',float(positive.eligible_fourwave.mean()))
states=S[['PHQ22','PHQ24','PHQ26','PHQ28']].ge(3).to_numpy(dtype=int);w=S.LSAQWT.to_numpy()
for j in range(1,3):
 r=(states[:,j]==0)&states[:,:j].any(axis=1)
 immediate=r&(states[:,j-1]==1)
 remote=r&~(states[:,j-1]==1)
 print('R transitions wave j=',j,'all',r.sum(),'immediate',immediate.sum(),'remote',remote.sum(), 'weighted share remote',float(w[remote].sum()/w[r].sum()))
