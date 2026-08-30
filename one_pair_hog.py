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


def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)


def bernoulli(p, n):
    return (torch.rand(n) < p).float()


def xor(a, b):
    return (a - b).abs()


def build_indices_labels(seed, labels):
    # Exact IPG/DomainBed RNG order: shuffle, label flip, then color flip per environment.
    seed_all(seed)
    perm = torch.randperm(len(labels))
    shuffled_labels = labels[perm]
    train_idx, val_idx = [], []
    noisy_by_env, global_indices = [], []
    for i, e in enumerate(ENVS):
        idx = perm[i::3]
        raw_y = shuffled_labels[i::3]
        y = (raw_y < 5).float()
        y = xor(y, bernoulli(LABEL_NOISE, len(y))).long()
        _colors = xor(y.float(), bernoulli(e, len(y)))
        global_indices.append(idx)
        noisy_by_env.append(y)
    y_train, y_val = [], []
    for i in range(2):
        n = len(global_indices[i])
        n_train = math.ceil(n * TRAIN_FRAC)
        q = torch.randperm(n, generator=torch.Generator().manual_seed(42))
        train_idx.append(global_indices[i][q[:n_train]])
        val_idx.append(global_indices[i][q[n_train:]])
        y_train.append(noisy_by_env[i][q[:n_train]])
        y_val.append(noisy_by_env[i][q[n_train:]])
    return (torch.cat(train_idx).numpy(), torch.cat(y_train).numpy(),
            torch.cat(val_idx).numpy(), torch.cat(y_val).numpy(),
            global_indices[2].numpy(), noisy_by_env[2].numpy())


def infer_swap_from_one_pair(image):
    # Same supervision object used by IPG: one underlying image shown in each channel.
    image = image.astype(np.float32) / 255.0
    z = np.zeros_like(image)
    left = np.stack([image, z])
    right = np.stack([z, image])
    scores=[]
    for perm in itertools.permutations(range(2)):
        a=left[list(perm)]; b=right[list(perm)]
        residual=float(np.mean((a-right)**2)+np.mean((b-left)**2))
        scores.append((residual,perm))
    scores.sort()
    return scores[0][1], scores


def compile_quotient(images_u8, learned_perm):
    # Construct colored observations, then apply the group sum I + learned_perm.
    # Alternating colors are used solely to certify invariance over both orbit elements.
    x = images_u8.astype(np.float32) / 255.0
    n = len(x)
    colors = np.arange(n) % 2
    colored = np.zeros((n, 2, 28, 28), dtype=np.float32)
    colored[np.arange(n), colors] = x
    projected = colored + colored[:, list(learned_perm)]
    if not np.array_equal(projected[:, 0], projected[:, 1]):
        raise RuntimeError('Compiled representation is not invariant')
    if not np.array_equal(projected[:, 0], x):
        raise RuntimeError('Compiled quotient does not equal grayscale oracle')
    return projected[:, 0]


def compute_hog(images):
    out=[]
    for image in images:
        out.append(hog(image, orientations=9, pixels_per_cell=(4,4),
                       cells_per_block=(2,2), block_norm='L2-Hys', feature_vector=True))
    return np.asarray(out, dtype=np.float32)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--seeds',default='0,1,2,3,4'); p.add_argument('--out',default='results')
    args=p.parse_args(); seeds=[int(x) for x in args.seeds.split(',')]
    Path(args.out).mkdir(parents=True,exist_ok=True)
    t0=time.time()
    tr=MNIST('mnist_data',train=True,download=True); te=MNIST('mnist_data',train=False,download=True)
    images=np.concatenate([tr.data.numpy(),te.data.numpy()]); labels=torch.cat([tr.targets,te.targets])
    learned_perm, scores=infer_swap_from_one_pair(images[0])
    projected_images=compile_quotient(images, learned_perm)
    feats=compute_hog(projected_images)
    rows=[]
    for seed in seeds:
        ti,yt,vi,yv,xi,yx=build_indices_labels(seed,labels)
        best=None
        for C in [0.003,0.01,0.03,0.1,0.3,1.0]:
            model=LinearSVC(C=C,dual='auto',max_iter=5000,random_state=seed)
            model.fit(feats[ti],yt)
            val=accuracy_score(yv,model.predict(feats[vi]))
            if best is None or val>best[0]: best=(val,C,model)
        val,C,model=best
        test=accuracy_score(yx,model.predict(feats[xi]))
        row={'seed':seed,'pair_budget':1,'learned_perm':list(learned_perm),
             'identity_residual':scores[1][0],'swap_residual':scores[0][0],
             'quotient_equals_grayscale_oracle':True,
             'selected_C':C,'validation_accuracy':val,'test_accuracy':test}
        rows.append(row); print('RESULT',json.dumps(row,sort_keys=True),flush=True)
    acc=np.array([r['test_accuracy'] for r in rows])
    summary={'n_seeds':len(rows),'pair_budget':1,'mean_accuracy':float(acc.mean()),
             'std_accuracy':float(acc.std(ddof=1)),'min_accuracy':float(acc.min()),
             'max_accuracy':float(acc.max()),'seconds':time.time()-t0,'rows':rows}
    Path(args.out,'summary.json').write_text(json.dumps(summary,indent=2))
    print('SUMMARY',json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__': main()
