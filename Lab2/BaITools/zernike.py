import scipy
from scipy.special import gamma
import numpy as np

def zrf(n, m, r):
    R = 0
    for s in range((n-m)//2+1):
        num = (-1)**s * gamma(n-s+1)
        denom = gamma(s+1) * gamma((n+m)/2-s+1) * gamma((n-m)/2-s+1)
        R = R + num / denom * r**(n-2*s)
    return R


def zernike(fx, fy, i, wz):
    FX, FY = np.meshgrid(fx, fy)
    r = np.sqrt(FX**2 + FY**2)
    theta = np.arctan2(FY, FX)
    
    if len(i) != len(wz):
        raise ValueError('zernike:Matchinglength','i and wz must be the same length.')
    
    zernike_index = np.load('Lab4\zernike_index.npy')
    Z_sum = 0
    for ind in range(len(i)):
        n = zernike_index[i[ind]-1, 0]
        m = zernike_index[i[ind]-1, 1]
        if m == 0:
            Z = np.sqrt(n+1)*zrf(n,0,r)
        else:
            if i[ind] % 2 == 0:  # i is even
                Z = np.sqrt(2*(n+1))*zrf(n,m,r) * np.cos(m*theta)
            else: # i is odd
                Z = np.sqrt(2*(n+1))*zrf(n,m,r) * np.sin(m*theta)
        Z_sum += wz[ind]*Z

    unit_circle_mask = (FX**2 + FY**2 <= 1).astype(np.float64)
    Z_sum *= unit_circle_mask
    return Z_sum