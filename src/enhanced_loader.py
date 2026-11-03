"""Read user-supplied MEPS public use data and aggregate auxiliary files.

Only aggregated outputs should be published. Intermediate person-level tables remain in process.
"""
from __future__ import annotations
import io,zipfile,os
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(os.environ.get('MEPS_DATA_DIR',str(Path(__file__).resolve().parents[1]/'data'/'raw')))
ADDITIONAL=ROOT/'More MEPS.zip'
SPECIAL={2018:'h236dta.zip',2019:'h245dta (1).zip'}
CONDITIONS={2019:'h214dta.zip',2020:'h222dta.zip',2021:'h231dta.zip',2022:'h241dta.zip',2023:'h249dta.zip',2024:'h255dta.zip'}

def read_nested_outer(outer,member,columns=None):
    with zipfile.ZipFile(io.BytesIO(outer.read(member))) as nested:
        dta_files=[n for n in nested.namelist() if n.lower().endswith('.dta')]
        assert len(dta_files)==1,(member,dta_files)
        raw=io.BytesIO(nested.read(dta_files[0]))
        r=pd.io.stata.StataReader(raw,convert_categoricals=False)
        r._ensure_open()
        if columns is None:
            columns=r._varlist
        missing=set(columns).difference(r._varlist)
        if missing: raise ValueError(f'{member} missing columns: {sorted(missing)}')
        d=r.read(columns=columns)
    return d

def read_aux(filename,cols):
    with zipfile.ZipFile(ROOT/filename) as z:
        names=[n for n in z.namelist() if n.endswith('.dta')]
        assert len(names)==1
        # extraction into memory for seekable Stata input
        r=pd.io.stata.StataReader(io.BytesIO(z.read(names[0])),convert_categoricals=False)
        r._ensure_open()
        return r.read(columns=cols)

def load_conditions():
    frames=[]; audits=[]
    with zipfile.ZipFile(ADDITIONAL) as outer:
        for year,filename in CONDITIONS.items():
            d=read_nested_outer(outer,'More MEPS/'+filename,
                columns=['DUPERSID','PANEL','CONDIDX','ICD10CDX'] + (["ERCOND","HHCOND","IPCOND","OBCOND","OPCOND","RXCOND"] if year==2022 else []))
            assert d['CONDIDX'].is_unique,(year,'duplicate condition ids')
            d['DUPERSID']=d['DUPERSID'].astype(str).str.strip()
            initial=len(d)
            bad=np.zeros(len(d),dtype=bool)
            if year==2022:
                event=['ERCOND','HHCOND','IPCOND','OBCOND','OPCOND','RXCOND']
                bad=(d[event]==2).all(axis=1).to_numpy()
                d=d.loc[~bad].copy()
            icd=d['ICD10CDX'].astype(str).str.strip().str.upper()
            d['code_f31']=icd.str.startswith('F31')
            d['code_f32']=icd.str.startswith('F32')
            d['code_f33']=icd.str.startswith('F33')
            d['code_f34']=icd.str.startswith('F34')
            d['code_f32f33']=d['code_f32']|d['code_f33']
            d['code_any_f3']=icd.str.match(r'^F3[0-9]')
            d['year']=year
            audits.append({'year':year,'input_condition_records':initial,'excluded_2022_erroneous_event_unlinked':int(bad.sum()),
                           'retained_condition_records':len(d),'unique_people_with_conditions':d.DUPERSID.nunique(),
                           **{f'n_{c}_condition_records':int(d[c].sum()) for c in ['code_f31','code_f32','code_f33','code_f34','code_f32f33','code_any_f3']}})
            out=d.groupby(['year','DUPERSID'],as_index=False)[['code_f31','code_f32','code_f33','code_f34','code_f32f33','code_any_f3']].max()
            frames.append(out)
    c=pd.concat(frames,ignore_index=True)
    assert not c[['year','DUPERSID']].duplicated().any()
    return c,pd.DataFrame(audits)

def load_extended():
    cols=['DUPERSID','PANEL','YEARIND','SAQRDS2468','ALL9RDS','AGEY1X','SEX','RACETHX','VARSTR','VARPSU','LSAQWT','LONGWT']
    cols+=['PHQ22','PHQ24','PHQ26','PHQ28']
    for i in range(1,5):
        cols+=['AGEY'+str(i)+'X','INSCOVY'+str(i),'TOTEXPY'+str(i),'TOTPRVY'+str(i),'TOTMCRY'+str(i),'TOTMCDY'+str(i)]
    cols=list(dict.fromkeys(cols))
    out=[]
    with zipfile.ZipFile(ADDITIONAL) as z:
        for year,filename in SPECIAL.items():
            dat=read_nested_outer(z,'More MEPS/'+filename,cols)
            dat['start_year']=year
            dat['DUPERSID']=dat['DUPERSID'].astype(str).str.strip()
            assert dat['DUPERSID'].is_unique
            out.append(dat)
    all_=pd.concat(out,ignore_index=True)
    assert not all_[['DUPERSID','PANEL']].duplicated().any()
    return all_
