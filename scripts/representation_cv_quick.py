#!/usr/bin/env python3
"""Fast fixed-ridge OOF sanity check for P1 imagery representations."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from representation_cv import OutcomeSpec, P1_MODALITIES, load_new_from_fetch, prepare_spec_frame, build_pipeline

SEED=20260914


def metrics(y,p):
    return {"log_loss":float(log_loss(y,p,labels=[0,1])),"brier":float(brier_score_loss(y,p)),"auc":float(roc_auc_score(y,p))}


def run(spec,repeats=5):
    df, fs = prepare_spec_frame(spec)
    y=df[spec.outcome_col].astype(int).to_numpy(); n=len(y)
    cv=RepeatedStratifiedKFold(n_splits=5,n_repeats=repeats,random_state=SEED)
    pred={k:np.zeros((repeats,n)) for k in fs}; seen={k:np.zeros((repeats,n),dtype=bool) for k in fs}
    for si,(tr,te) in enumerate(cv.split(np.zeros(n),y)):
        r=si//5
        for name,cols in fs.items():
            pipe=build_pipeline(spec,name,cols)
            pipe.set_params(model__C=1.0)
            pipe.fit(df.iloc[tr],y[tr]); pred[name][r,te]=pipe.predict_proba(df.iloc[te])[:,1]; seen[name][r,te]=True
    assert all(v.all() for v in seen.values())
    avg={k:v.mean(0) for k,v in pred.items()}
    return {"cohort":spec.cohort,"outcome":spec.outcome,"n":n,"events":int(y.sum()),"metrics":{k:metrics(y,p) for k,p in avg.items()}}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-root',type=Path,required=True); ap.add_argument('--output',type=Path,default=Path('quick_results')); a=ap.parse_args()
    f,_=load_new_from_fetch(a.data_root)
    specs=[]
    for s in (1,2):
        sf=f.loc[f.study_id.eq(s)].copy(); specs.append(OutcomeSpec('P1',f'new_study_{s}','current_treatment',sf,P1_MODALITIES,'image','treatment'))
    sf=f.loc[f.study_id.eq(2)].copy(); specs.append(OutcomeSpec('P1','new_study_2','broad_diagnosed_or_suspected_NDD',sf,P1_MODALITIES,'image','ndd'))
    out=[run(s) for s in specs]; a.output.mkdir(parents=True,exist_ok=True); (a.output/'quick.json').write_text(json.dumps(out,indent=2)+'\n')
    for r in out:
        print('\n',r['cohort'],r['outcome'],'N',r['n'],'events',r['events'])
        for k,m in r['metrics'].items(): print(k, 'logloss',round(m['log_loss'],6),'brier',round(m['brier'],6),'auc',round(m['auc'],4))

if __name__=='__main__': main()
