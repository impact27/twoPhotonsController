# -*- coding: utf-8 -*-
"""
Created on Thu May 11 13:45:52 2017

@author: quentinpeter
"""

import numpy as np
from matplotlib.pyplot import figure, plot, imshow
import matplotlib.pyplot as plt
from glob import glob
import re

fns = glob("ims/*.npy")
regexp = 'X(\d+\.?\d*) Y(\d+\.?\d*) Z(\d+\.?\d*)'
#%%
ims = []
infos = []
for fn in fns:
    infos.append(re.findall(regexp, fn)[0])
    ims.append(np.load(fn))

#%%
ims = np.asarray(ims)
infos = np.asarray(infos, dtype=float)
#%%
X = np.round(infos[:, 0])
Y = np.round(infos[:, 1])
Z = infos[:, 2]

i250250 = np.logical_and(X == 25500, Y == 25500)

z = Z[i250250]
sort = np.argsort(z)
z = z[sort]

d250250 = ims[i250250][sort]


#%%
def get_spot_size(imrange):
    return np.sum(imrange >= np.reshape(np.max(imrange, (1, 2)) / 10, (-1, 1, 1)),
                  (1, 2))


size = get_spot_size(d250250)


figure()
plot(z, np.max(d250250, (1, 2)))

figure()
plt.semilogy(z, size, 'x')
F = np.poly1d(np.polyfit(z, np.log(size), 2))
plt.plot(z, np.exp(F(z)))

z[np.argsorted(size)[:2]]
