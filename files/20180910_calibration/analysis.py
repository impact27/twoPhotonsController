# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure, plot, imshow, show
fix_S = 37.76
fix_P= 113.3
S = np.array([ 37.76666667,  39.75438596,  41.96296296,  44.43137255,
        47.20833333,  50.35555556,  53.95238095,  58.1025641 ,
        62.94444444,  68.66666667,  75.53333333,  83.92592593,
        94.41666667, 107.9047619 , 125.88888889, 151.06666667,
       188.83333333, 251.77777778, 377.66666667, 755.33333333])

P = np.array([113.3  , 107.635, 101.97 ,  96.305,  90.64 ,  84.975,  79.31 ,
        73.645,  67.98 ,  62.315,  56.65 ,  50.985,  45.32 ,  39.655,
        33.99 ,  28.325,  22.66 ,  16.995,  11.33 ,   5.665])


vary_P = np.array([[7, 79.35],
          [8, 57.5],
          [9, 53.7],
          [10, 35],
          [11, 17.7],
          [12, 4.6],
          [13, 1.6]])

vary_S = np.array([[12, 89.1],
          [13, 81.9],
          [14, 70.3],
          [15, 54],
          [16, 43.5],
          [17, 24.1],
          [18, 5.5],
          [19, 1.8]])

vary_P[:, 0] = P[np.array(vary_P[:, 0], dtype=int)]
vary_S[:, 0] = S[np.array(vary_S[:, 0], dtype=int)]

vary_P[:, 1] *= -3/95
vary_S[:, 1] *= -3/95

#%%
def plotfit(x, y):
    fit = np.polyfit(x, y, 1)
    plot(x, np.poly1d(fit)(x))
figure()
plot(vary_P[:, 1], vary_P[:, 0], 'x')
plotfit(vary_P[:, 1], vary_P[:, 0])
plt.xlabel("Z offset")
plt.ylabel("Laser Power")
figure()
plot(vary_P[:, 1], vary_P[:, 0]**2, 'x')
plotfit(vary_P[:, 1], vary_P[:, 0]**2)
plt.xlabel("Z offset")
plt.ylabel("Laser Power ^2")
figure()
plt.plot(vary_S[:, 1], 1/vary_S[:, 0], 'x')
plotfit(vary_S[:, 1], 1/vary_S[:, 0])
plt.xlabel("Z offset")
plt.ylabel("1 / Speed")

figure()
plt.plot(vary_S[:, 1], fix_P**2/vary_S[:, 0], 'x')
plot(vary_P[:, 1], vary_P[:, 0]**2 / fix_S, 'x')

#%%
width_S = np.array([3.5, 2.65, 2.79, 2.69, 2.72, 2.49, 2.35, 2.55, 2.69, 2.45, 2.45,
 2.41, 2.72, 2.42, 2.14, 1.56, 1.12, 0.92, 0.55, 0.31])
figure()
plt.plot(1/S, width_S, 'x')
plt.plot(0, 0, 'x')
plt.xlabel("1 / Speed")
plt.ylabel("Channel Width")
#%%
width_P = np.asarray([3.29, 2.58, 2.49, 2.31, 2.71, 2.58, 2.53, 2.22, 1.82, 
                      1.24, 0.93, 0.8, 0.36, 0, 0, 0, 0, 0, 0, 0, ])
figure()
plt.plot(P, width_P, 'x')
plt.xlabel("Laser Power")
plt.ylabel("Channel Width")
figure()
plt.plot(P**2, width_P, 'x')
plt.xlabel("Laser Power ^2")
plt.ylabel("Channel Width")