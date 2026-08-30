import argparse, itertools, json, math, random, time
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score
from sklearn.svm import LinearSVC
from skimage.feature import hog
from torchvision.datasets import MNIST

ENVS=[0.1,0.2,0.9]; LABEL_NOISE=.25; TRAIN_FRAC=.8
C_GRID=[0.003,0.01,0.03,0.1,0.3,1.0]

def seed_all(s): random.seed(s); np.random.seed(s); torch.manual_seed(s)
def bernoulli(p,n): return (torch.rand(n)<p).float()
def xor(a,b): return (a-b).abs()

def build_split(seed,labels):
    seed_all(seed); perm=torch.randperm(len(labels)); shuffled=labels[perm]; ei=[]; ey=[]; ec=[]
    for i,e in enumerate(ENVS):
        idx=perm[i::3]; raw=shuffled[i::3]
        y=xor((raw<5).float(),bernoulli(LABEL_NOISE,len(raw))).long(); c=xor(y.float(),bernoulli(e,len(y))).long()
        ei.append(idx); ey.append(y); ec.append(c)
    pieces={'train':[[],[],[]],'val':[[],[],[]]}
    for i in range(2):
        n=len(ei[i]); nt=math.ceil(n*TRAIN_FRAC); q=torch.randperm(n,generator=torch.Generator().manual_seed(42))
        for name,sel in [('train',q[:nt]),('val',q[nt:])]:
            pieces[name][0].append(ei[i][sel]); pieces[name][1].append(ey[i][sel]); pieces[name][2].append(ec[i][sel])
    train=tuple(torch.cat(v).numpy() for v in pieces['train']); val=tuple(torch.cat(v).numpy() for v in pieces['val']); test=(ei[2].numpy(),ey[2].numpy(),ec[2].numpy())
    return train,val,test

def infer_swap_from_one_pair(image):
    image=image.astype(np.float32)/255.; z=np.zeros_like(image); left=np.stack([image,z]); right=np.stack([z,image]); scores=[]
    for perm in itertools.permutations(range(2)):
        p=list(perm); residual=float(np.mean((left[p]-right)**2)+np.mean((right[p]-left)**2)); scores.append((residual,perm))
    scores.sort(); return scores[0][1],scores

def certify_quotient(images_u8,perm):
    x=images_u8.astype(np.float32)/255.; n=len(x); colors=np.arange(n)%2; colored=np.zeros((n,2,28,28),dtype=np.float32); colored[np.arange(n),colors]=x
    projected=colored+colored[:,list(perm)]
    if not np.array_equal(projected[:,0],projected[:,1]): raise RuntimeError('non-invariant quotient')
    if not np.array_equal(projected[:,0],x): raise RuntimeError('quotient differs from grayscale oracle')

def compute_hog(images):
    return np.asarray([hog(im,orientations=9,pixels_per_cell=(4,4),cells_per_block=(2,2),block_norm='L2-Hys',feature_vector=True) for im in images],dtype=np.float32)

def colored_features(base,idx,colors):
    z=np.zeros((len(idx),base.shape[1]*2),dtype=np.float32); rows=np.arange(len(idx)); d=base.shape[1]; f=base[idx]; m=colors==0
    z[rows[m],:d]=f[m]; z[rows[~m],d:]=f[~m]; return z

def ncm_project(x,delta):
    denom=float(delta@delta)
    return x-np.outer((x@delta)/denom,delta).astype(np.float32)

def select_and_score(xtr,ytr,xv,yv,xt,yt,seed):
    best=None
    for C in C_GRID:
        model=LinearSVC(C=C,dual='auto',max_iter=5000,random_state=seed); model.fit(xtr,ytr); val=accuracy_score(yv,model.predict(xv))
        if best is None or val>best[0]: best=(val,C,model)
    val,C,model=best; return val,accuracy_score(yt,model.predict(xt)),C

def main():
    p=argparse.ArgumentParser(); p.add_argument('--seeds',default='0,1,2,3,4'); p.add_argument('--out',default='results'); a=p.parse_args(); seeds=[int(x) for x in a.seeds.split(',')]
    Path(a.out).mkdir(parents=True,exist_ok=True); t0=time.time(); tr=MNIST('mnist_data',train=True,download=True); te=MNIST('mnist_data',train=False,download=True)
    images=np.concatenate([tr.data.numpy(),te.data.numpy()]); labels=torch.cat([tr.targets,te.targets]); base=compute_hog(images.astype(np.float32)/255.); rows=[]
    for seed in seeds:
        (ti,yt,tc),(vi,yv,vc),(xi,yx,xc)=build_split(seed,labels); pair_index=int(ti[0]); perm,scores=infer_swap_from_one_pair(images[pair_index]); certify_quotient(images[[ti[0],vi[0],xi[0]]],perm)
        ctr=colored_features(base,ti,tc); cva=colored_features(base,vi,vc); cte=colored_features(base,xi,xc)
        erm=select_and_score(ctr,yt,cva,yv,cte,yx,seed)
        f=base[pair_index]; delta=np.concatenate([f,-f]).astype(np.float32)
        ncm=select_and_score(ncm_project(ctr,delta),yt,ncm_project(cva,delta),yv,ncm_project(cte,delta),yx,seed)
        compiled=select_and_score(base[ti],yt,base[vi],yv,base[xi],yx,seed)
        row={'seed':seed,'pair_budget':1,'pair_source':'training','pair_global_index':pair_index,'learned_perm':list(perm),
             'identity_residual':scores[1][0],'swap_residual':scores[0][0],'quotient_equals_grayscale_oracle':True,
             'erm_validation_accuracy':erm[0],'erm_test_accuracy':erm[1],'erm_C':erm[2],
             'ncm_validation_accuracy':ncm[0],'ncm_test_accuracy':ncm[1],'ncm_C':ncm[2],
             'compiled_validation_accuracy':compiled[0],'compiled_test_accuracy':compiled[1],'compiled_C':compiled[2]}
        rows.append(row); print('RESULT',json.dumps(row,sort_keys=True),flush=True)
    ea=np.array([r['erm_test_accuracy'] for r in rows]); na=np.array([r['ncm_test_accuracy'] for r in rows]); ca=np.array([r['compiled_test_accuracy'] for r in rows])
    summary={'n_seeds':len(rows),'pair_budget':1,
             'erm_mean_accuracy':float(ea.mean()),'erm_std_accuracy':float(ea.std(ddof=1)),
             'ncm_mean_accuracy':float(na.mean()),'ncm_std_accuracy':float(na.std(ddof=1)),
             'compiled_mean_accuracy':float(ca.mean()),'compiled_std_accuracy':float(ca.std(ddof=1)),
             'compiled_min_accuracy':float(ca.min()),'compiled_max_accuracy':float(ca.max()),
             'compiler_gain_over_erm_points':float(100*(ca-ea).mean()),'compiler_gain_over_ncm_points':float(100*(ca-na).mean()),
             'seconds':time.time()-t0,'rows':rows}
    Path(a.out,'summary.json').write_text(json.dumps(summary,indent=2)); print('SUMMARY',json.dumps(summary,sort_keys=True),flush=True)
if __name__=='__main__': main()
