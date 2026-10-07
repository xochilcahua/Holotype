# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
import sys, json, glob, random, statistics as st
from collections import Counter
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from appdriver import App
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = """(cfg)=>{
  const axes=[...AXIS_GROUPS.technique,...AXIS_GROUPS.domain,...AXIS_GROUPS.sensory];
  let seed=31337; const rnd=()=>(seed=(seed*1103515245+12345)&0x7fffffff)/0x7fffffff;
  const dr=()=>{const r=rnd(); return r<0.5?1+Math.floor(rnd()*2): r<0.85?3+Math.floor(rnd()*3):6+Math.floor(rnd()*3)};
  const W=ART_FORMS.map(f=>cfg.prev?Math.max(0.5,PREVALENCE[f.id]||0.5):1), T=W.reduce((a,b)=>a+b,0);
  const pick=()=>{let t=rnd()*T,i=0; while(i<N-1&&(t-=W[i])>0)i++; return i};
  const sample=[];
  for(let p=0;p<cfg.people;p++){
    let wSum=0; const v={}; axes.forEach(a=>v[a]=0);
    const add=f=>{const w=dr(); wSum+=w; axes.forEach(a=>v[a]+=w*f[a])};
    const s=EFF[pick()];
    const near=EFF.map((f,i)=>{let q=0; for(const a of axes){const d=f[a]-s[a]; q+=d*d} return {f,i,d:Math.sqrt(q/axes.length)}}).sort((a,b)=>a.d-b.d);
    // n drawn log-uniform between nMin and nMax
    const n=Math.round(Math.exp(Math.log(cfg.nMin)+rnd()*(Math.log(cfg.nMax)-Math.log(cfg.nMin))));
    const win=near.slice(0,Math.max(cfg.width,Math.ceil(n*1.5))); const wt=win.map(x=>cfg.prev?W[x.i]:1);
    const tot=wt.reduce((a,b)=>a+b,0);
    for(let i=0;i<n;i++){let t=rnd()*tot,k=0; while(k<win.length-1&&(t-=wt[k])>0)k++; add(win[k].f)}
    axes.forEach(a=>v[a]/=wSum); sample.push(v);
  }
  const out={mean:{},sd:{},med:{}};
  axes.forEach(a=>{const vals=sample.map(v=>v[a]); const m=vals.reduce((x,y)=>x+y,0)/vals.length; out.mean[a]=m; out.sd[a]=Math.sqrt(vals.reduce((x,y)=>x+(y-m)*(y-m),0)/vals.length)||1; out.med[a]=medianOf(vals)});
  return out;
}"""
APPLY = """(r)=>{for(const a in r.mean){PEOPLE_MEAN[a]=r.mean[a];PEOPLE_SD[a]=r.sd[a];PEOPLE_MEDIAN[a]=r.med[a]}}"""
CLS = """(m)=>{state.mastery=m; const b=computeClassification(); return b?{g:b.genusId,z:[b.zProcess,b.zSoc,b.zForm].map(x=>+x.toFixed(2)),close:b.closeAxes.length}:null}"""
def evaluate(a, cfg, label):
    ref=a.ev(BUILD,cfg); a.ev(APPLY,ref)
    real={}
    for f in sorted(glob.glob(os.path.join(os.environ.get('HOLOTYPE_SESSIONS', os.path.join(ROOT,'tests','sample_sessions')),'*.json'))):
        d=json.load(open(f)); m={x['id']:x['rating'] for x in d['ratings']}
        real[d['name'][:6]]=a.ev(CLS,m)
    rows=a.ev("ART_FORMS.map(f=>[f.id, PREVALENCE[f.id]])")
    random.seed(21); res=[]
    for t in range(300):
        m={}
        for i,p in rows:
            if random.random()<p/100*0.6: m[i]=random.choices([1,2,3,4,5,6,7,8],[30,22,16,11,8,6,4,3])[0]
        if len(m)<4: continue
        res.append(a.ev(CLS,m))
    bits=[sum(r['g'][j]=='1' for r in res)/len(res) for j in (1,2,3)]
    print(f"{label:34s} ref a1 {ref['mean']['a1']:.3f}/{ref['sd']['a1']:.3f} d1 {ref['mean']['d1']:.3f}/{ref['sd']['d1']:.3f} a4 {ref['mean']['a4']:.3f}/{ref['sd']['a4']:.3f} | sim30 planned {bits[0]:.0%} collab {bits[1]:.0%} open {bits[2]:.0%} | real zSoc " + ' '.join(f"{k}:{v['z'][1]:+.2f}" for k,v in real.items()) + " | P " + ' '.join(f"{v['z'][0]:+.2f}" for v in real.values()))
if __name__=='__main__':
    a=App()
    evaluate(a,dict(prev=False,people=500,nMin=2,nMax=8,width=25),'old (flat, n 2-8)')
    evaluate(a,dict(prev=True,people=500,nMin=2,nMax=8,width=25),'prev, n 2-8  (what I shipped)')
    evaluate(a,dict(prev=True,people=500,nMin=4,nMax=60,width=25),'prev, n 4-60')
    evaluate(a,dict(prev=True,people=500,nMin=10,nMax=80,width=25),'prev, n 10-80')
    evaluate(a,dict(prev=False,people=500,nMin=4,nMax=60,width=25),'flat, n 4-60')
    a.close()
