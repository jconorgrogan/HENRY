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


def bernoulli(p, n):
    return (torch.rand(n) < p).float()


def xor(a, b):
    return (a - b).abs()


def build_split(seed, labels):
    # Exact IPG/DomainBed RNG order: shuffle, label flip, then color flip per environment.
    seed_all(seed)
    perm = torch.randperm(len(labels))
    shuffled_labels = labels[perm]
    env_idx, env_y, env_c = [], [], []
    for i, e in enumerate(ENVS):
        idx = perm[i::3]
        raw_y = shuffled_labels[i::3]
        y = (raw_y < 5).float()
        y = xor(y, bernoulli(LABEL_NOISE, len(y))).long()
        colors = xor(y.float(), bernoulli(e, len(y))).long()
        env_idx.append(idx); env_y.append(y); env_c.append(colors)

    pieces = {'train': [[],[],[]], 'val': [[],[],[]]}
    for i in range(2):
        n = len(env_idx[i]); n_train = math.ceil(n * TRAIN_FRAC)
        q = torch.randperm(n, generator=torch.Generator().manual_seed(42))
        for name, sel in [('train', q[:n_train]), ('val', q[n_train:])]:
            pieces[name][0].append(env_idx[i][sel])
            pieces[name][1].append(env_y[i][sel])
            pieces[name][2].append(env_c[i][sel])

    train = tuple(torch.cat(v).numpy() for v in pieces['train'])
    val = tuple(torch.cat(v).numpy() for v in pieces['val'])
    test = (env_idx[2].numpy(), env_y[2].numpy(), env_c[2].numpy())
    return train, val, test


def infer_swap_from_one_pair(image):
    # Same supervision object used by IPG: one underlying image shown in each channel.
    image = image.astype(np.float32) / 255.0
    z = np.zeros_like(image)
    left = np.stack([image, z]); right = np.stack([z, image])
    scores=[]
    for perm in itertools.permutations(range(2)):
        a=left[list(perm)]; b=right[list(perm)]
        residual=float(np.mean((a-right)**2)+np.mean((b-left)**2))
        scores.append((residual,perm))
    scores.sort()
    return scores[0][1], scores


def compile_quotient(images_u8, learned_perm):
    # Build both orbit elements and apply I + learned_perm. The output equals grayscale.
    x = images_u8.astype(np.float32) / 255.0
    n = len(x); colors = np.arange(n) % 2
    colored = np.zeros((n, 2, 28, 28), dtype=np.float32)
    colored[np.arange(n), colors] = x
    projected = colored + colored[:, list(learned_perm)]
    if not np.array_equal(projected[:, 0], projected[:, 1]):
        raise RuntimeError('Compiled representation is not invariant')
    if not np.array_equal(projected[:, 0], x):
        raise RuntimeError('Compiled quotient does not equal grayscale oracle')
    return projected[:, 0]


def compute_hog(images):
    return np.asarray([
        hog(image, orientations=9, pixels_per_cell=(4,4), cells_per_block=(2,2),
            block_norm='L2-Hys', feature_vector=True)
        for image in images
    ], dtype=np.float32)


def colored_features(base, idx, colors):
    # HOG of a zero channel is the zero vector, so concatenate the occupied channel.
    z = np.zeros((len(idx), base.shape[1]*2), dtype=np.float32)
    rows = np.arange(len(idx)); d = base.shape[1]
    f = base[idx]
    mask0 = colors == 0; mask1 = ~mask0
    z[rows[mask0], :d] = f[mask0]
    z[rows[mask1], d:] = f[mask1]
    return z


def select_and_score(xtr,ytr,xv,yv,xt,yt,seed):
    best=None
    for C in C_GRID:
        model=LinearSVC(C=C,dual='auto',max_iter=5000,random_state=seed)
        model.fit(xtr,ytr)
        val=accuracy_score(yv,model.predict(xv))
        if best is None or val>best[0]: best=(val,C,model)
    val,C,model=best
    return val, accuracy_score(yt,model.predict(xt)), C


def main():
    p=argparse.ArgumentParser(); p.add_argument('--seeds',default='0,1,2,3,4'); p.add_argument('--out',default='results')
    args=p.parse_args(); seeds=[int(x) for x in args.seeds.split(',')]
    Path(args.out).mkdir(parents=True,exist_ok=True)
    t0=time.time()
    tr=MNIST('mnist_data',train=True,download=True); te=MNIST('mnist_data',train=False,download=True)
    images=np.concatenate([tr.data.numpy(),te.data.numpy()]); labels=torch.cat([tr.targets,te.targets])
    learned_perm, scores=infer_swap_from_one_pair(images[0])
    projected_images=compile_quotient(images, learned_perm)
    base_feats=compute_hog(projected_images)
    rows=[]
    for seed in seeds:
        (ti,yt,tc),(vi,yv,vc),(xi,yx,xc)=build_split(seed,labels)
        # Same classifier family on original colored observations.
        erm = select_and_score(colored_features(base_feats,ti,tc),yt,
                               colored_features(base_feats,vi,vc),yv,
                               colored_features(base_feats,xi,xc),yx,seed)
        # One pair compiles the global quotient; all downstream examples use that projection.
        compiled = select_and_score(base_feats[ti],yt,base_feats[vi],yv,base_feats[xi],yx,seed)
        row={'seed':seed,'pair_budget':1,'learned_perm':list(learned_perm),
             'identity_residual':scores[1][0],'swap_residual':scores[0][0],
             'quotient_equals_grayscale_oracle':True,
             'erm_validation_accuracy':erm[0],'erm_test_accuracy':erm[1],'erm_C':erm[2],
             'compiled_validation_accuracy':compiled[0],
             'compiled_test_accuracy':compiled[1],'compiled_C':compiled[2]}
        rows.append(row); print('RESULT',json.dumps(row,sort_keys=True),flush=True)
    erm_acc=np.array([r['erm_test_accuracy'] for r in rows])
    comp_acc=np.array([r['compiled_test_accuracy'] for r in rows])
    summary={'n_seeds':len(rows),'pair_budget':1,
             'erm_mean_accuracy':float(erm_acc.mean()),'erm_std_accuracy':float(erm_acc.std(ddof=1)),
             'compiled_mean_accuracy':float(comp_acc.mean()),'compiled_std_accuracy':float(comp_acc.std(ddof=1)),
             'compiled_min_accuracy':float(comp_acc.min()),'compiled_max_accuracy':float(comp_acc.max()),
             'mean_gain_points':float(100*(comp_acc-erm_acc).mean()),
             'seconds':time.time()-t0,'rows':rows}
    Path(args.out,'summary.json').write_text(json.dumps(summary,indent=2))
    print('SUMMARY',json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__': main()
