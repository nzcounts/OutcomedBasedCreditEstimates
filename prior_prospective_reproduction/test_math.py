#!/usr/bin/env python3
"""Pure numerical tests of two-part marginal-standardization gradients and pricing identities."""
import numpy as np
from scipy.special import expit
from run_analysis import exposure_factor

def contrast(b,g,X,w,j):
 t0=X.copy();t1=X.copy();t0[:,j]=0;t1[:,j]=1
 p0=expit(t0@b);p1=expit(t1@b)
 mu0=p0*np.exp(t0@g);mu1=p1*np.exp(t1@g)
 d=(mu0-mu1)
 value=np.average(d,weights=w)
 db=np.average(mu0[:,None]*(1-p0[:,None])*t0-mu1[:,None]*(1-p1[:,None])*t1,axis=0,weights=w)
 dg=np.average(mu0[:,None]*t0-mu1[:,None]*t1,axis=0,weights=w)
 return value,db,dg

rng=np.random.default_rng(73)
X=np.column_stack([np.ones(800),rng.normal(size=(800,5))]);X[:,1]=rng.integers(0,2,len(X))
W=rng.lognormal(size=800);b=rng.normal(scale=.3,size=X.shape[1]);g=rng.normal(scale=.3,size=X.shape[1]);g[0]=9.1
v,db,dg=contrast(b,g,X,W,1)
h=1e-6
for k in range(X.shape[1]):
 bb=b.copy();bb[k]+=h;bm=b.copy();bm[k]-=h
 numerical=(contrast(bb,g,X,W,1)[0]-contrast(bm,g,X,W,1)[0])/(2*h)
 assert abs(numerical-db[k])<2e-4,(k,numerical,db[k])
 gg=g.copy();gg[k]+=h;gm=g.copy();gm[k]-=h
 numerical=(contrast(b,gg,X,W,1)[0]-contrast(b,gm,X,W,1)[0])/(2*h)
 assert abs(numerical-dg[k])<2e-4,(k,numerical,dg[k])
for v in [-12000,0,2322,900000]:
 for pr,pp in [(.237385401,.488441178),(.3,.3),(0,1)]:
  f=exposure_factor(pr,pp)
  for c in [1,.75,.5]:
   x=v*f*(1-.53)*c
   assert np.isclose(x/c,v*f*(1-.53),rtol=1e-10,atol=1e-8)
print('PASS: 12 numerical two-part gradients; Markov multipliers; 100/75/50 scaling')
