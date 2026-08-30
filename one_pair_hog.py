import argparse, itertools, json, math, random, time
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score
from sklearn.svm import LinearSVC
from skimage.feature import hog
from torchvision.datasets import MNIST

ENVS = [0.1, 0.2, 0.9]
LABEL_NOISE = 0.25
TRAIN_FRAC = 0.8
C_GRID = [0.003,0.01,0.03,0.1,0.3,1.0]


def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)


def bernoulli(p, n): return (torch.rand(n) < p).float()
def xor(a, b): return (a - b).abs()


def build_split(seed, labels):
    # Exact IPG/DomainBed RNG order: global shuffle, label flip, color flip per environment.
    seed_all(seed)
    perm = torch.randperm(len(labels)); shuffled_labels = labels[perm]
    env_idx, env_y, env_c = [], [], []
    for i, e in enumerate(ENVS):
        idx = perm[i::3]; raw_y = shuffled_labels[i::3]
        y = xor((raw_y < 5).float(), bernoulli(LABEL_NOISE, len(raw_y))).long()
        colors = xor(y.float(), bernoulli(e, len(y))).long()
        env_idx.append(idx); env_y.append(y); env_c.append(colors)
    pieces = {'train': [[],[],[]], 'val': [[],[],[]]}
    for i in range(2):
        n=len(env_idx[i]); n_train=math.ceil(n*TRAIN_FRAC)
        q=torch.randperm(n,generator=torch.Generator().manual_seed(42))
        for name,sel in [('train',q[:n_train]),('val',q[n_train:])]:
            pieces[name][0].append(env_idx[i][sel]); pieces[name][1].append(env_y[i][sel]); pieces[name][2].append(env_c[i][sel])
    train=tuple(torch.cat(v).numpy() for v in pieces['train'])
    val=tuple(torch.cat(v).numpy() for v in pieces['val'])
    test=(env_idx[2].numpy(),env_y[2].numpy(),env_c[2].numpy())
    return train,val,test


def infer_swap_from_one_pair(image):
    # One training image rendered once in each channel: the exact 'perfect pair' object used by IPG.
    image=image.astype(np.float32)/255.0; z=np.zeros_like(image)
    left=np.stack([image,z]); right=np.stack([z,image]); scores=[]
    for perm in itertools.permutations(range(2)):
        p=list(perm)
        residual=float(np.mean((left[p]-right)**2)+np.mean((right[p]-left)**2))
        scores.append((residual,perm))
    scores.sort(); return scores[0][1],scores


def certify_quotient(images_u8, learned_perm):
    # Apply the group sum I+g to both orbit elements; both become the grayscale image.
    x=images_u8.astype(np.float32)/255.0; n=len(x); colors=np.arange(n)%2
    colored=np.zeros((n,2,28,28),dtype=np.float32); colored[np.arange(n),colors]=x
    projected=colored+colored[:,list(learned_perm)]
    if not np.array_equal(projected[:,0],projected[:,1]): raise RuntimeError('non-invariant quotient')
    if not np.array_equal(projected[:,0],x): raise RuntimeError('quotient differs from grayscale oracle')


def compute_hog(images):
    return np.asarray([hog(im,orientations=9,pixels_per_cell=(4,4),cells_per_block=(2,2),block_norm='L2-Hys',feature_vector=True) for im in images],dtype=np.float32)


def colored_features(base,idx,colors):
    z=np.zeros((len(idx),base.shape[1]*2),dtype=np.float32); rows=np.arange(len(idx)); d=base.shape[1]; f=base[idx]
    m=colors==0; z[rows[m],:d]=f[m]; z[rows[~m],d:]=f[~m]
    return z


def select_and_score(xtr,ytr,xv,yv,xt,yt,seed):
    best=None
    for C in C_GRID:
        model=LinearSVC(C=C,dual='auto',max_iter=5000,random_state=seed); model.fit(xtr,ytr)
        val=accuracy_score(yv,model.predict(xv))
        if best is None or val>best[0]: best=(val,C,model)
    val,C,model=best; return val,accuracy_score(yt,model.predict(xt)),C


def main():
    p=argparse.ArgumentParser(); p.add_argument('--seeds',default='0,1,2,3,4'); p.add_argument('--out',default='results')
    a=p.parse_args(); seeds=[int(x) for x in a.seeds.split(',')]; Path(a.out).mkdir(parents=True,exist_ok=True); t0=time.time()
    tr=MNIST('mnist_data',train=True,download=True); te=MNIST('mnist_data',train=False,download=True)
    images=np.concatenate([tr.data.numpy(),te.data.numpy()]); labels=torch.cat([tr.targets,te.targets])
    base_feats=compute_hog(images.astype(np.float32)/255.0); rows=[]
    for seed in seeds:
        (ti,yt,tc),(vi,yv,vc),(xi,yx,xc)=build_split(seed,labels)
        # Pair is drawn strictly from the training split.
        pair_index=int(ti[0]); learned_perm,scores=infer_swap_from_one_pair(images[pair_index])
        certify_quotient(images[[ti[0],vi[0],xi[0]]],learned_perm)
        erm=select_and_score(colored_features(base_feats,ti,tc),yt,colored_features(base_feats,vi,vc),yv,colored_features(base_feats,xi,xc),yx,seed)
        compiled=select_and_score(base_feats[ti],yt,base_feats[vi],yv,base_feats[xi],yx,seed)
        row={'seed':seed,'pair_budget':1,'pair_source':'training','pair_global_index':pair_index,
             'learned_perm':list(learned_perm),'identity_residual':scores[1][0],'swap_residual':scores[0][0],
             'quotient_equals_grayscale_oracle':True,
             'erm_validation_accuracy':erm[0],'erm_test_accuracy':erm[1],'erm_C':erm[2],
             'compiled_validation_accuracy':compiled[0],'compiled_test_accuracy':compiled[1],'compiled_C':compiled[2]}
        rows.append(row); print('RESULT',json.dumps(row,sort_keys=True),flush=True)
    ea=np.array([r['erm_test_accuracy'] for r in rows]); ca=np.array([r['compiled_test_accuracy'] for r in rows])
    summary={'n_seeds':len(rows),'pair_budget':1,'erm_mean_accuracy':float(ea.mean()),'erm_std_accuracy':float(ea.std(ddof=1)),
             'compiled_mean_accuracy':float(ca.mean()),'compiled_std_accuracy':float(ca.std(ddof=1)),
             'compiled_min_accuracy':float(ca.min()),'compiled_max_accuracy':float(ca.max()),
             'mean_gain_points':float(100*(ca-ea).mean()),'seconds':time.time()-t0,'rows':rows}
    Path(a.out,'summary.json').write_text(json.dumps(summary,indent=2)); print('SUMMARY',json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__': main()
