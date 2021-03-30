import numpy as np
from InputGen import *
from scipy.signal import find_peaks

from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('TKAgg')

# global variables
BlockLen = 4096 # 512:32ms per block for fs=16000
FFT_Point = BlockLen*2 # FFT points should >2*BlockLen-1 for linear cross correlation
block_drop_TH = 0.45 # if (2nd peak amp)/(1st peak amp) in gcc > th, drop this block
amp_drop_TH = 0.02 # drop block if average amp < th in any channel

def GCC_PATH(x1,x2,ax=None):
    """
    Use GCC_PATH to get delay
    Use Quinn's interpolation method to improve accurcy
    Not for using outside this file.
    Return:
        Delay estimation in sample
        (2nd peak amp)/(1st peak amp) for frame selection
    """
    # GCC_PATH
    X1 = np.fft.fft(x1,FFT_Point) # add zeros for fft
    X2 = np.fft.fft(x2,FFT_Point)
    G12 = X1*np.conjugate(X2)
    Rp12 = np.fft.fftshift(np.fft.ifft(G12/np.abs(G12)))
    Rp12_abs = np.abs(Rp12)

    # Find peaks
    peaks, properties = find_peaks(Rp12_abs,height=0.05, distance=3,prominence=0.15)
    if len(peaks)==1:
        max_point = peaks[0]
        sec_point = None
        sec_by_fst = 0
    elif len(peaks)==0:
        max_point = None
        sec_point = None
        sec_by_fst = 1
        return None,sec_by_fst
    else:
        ind = np.argsort(properties['peak_heights'])
        max_point = peaks[ind[-1]]
        sec_point = peaks[ind[-2]]
        sec_by_fst = Rp12_abs[sec_point]/Rp12_abs[max_point]

    # Quinn's method
    alp1 = np.real(Rp12[max_point+1]/Rp12[max_point])
    alp2 = np.real(Rp12[max_point-1]/Rp12[max_point])
    delta1 = alp1/(1-alp1)
    delta2 = -alp2/(1-alp2)
    if delta1>0 and delta2>0:
        delta = delta2
    else :
        delta = delta1
    delay_sample = (max_point-FFT_Point/2+delta)

    # plot and debug
    # print("est delay in sample: %f no delata:%f"%(delay_sample,delay_sample-delta))
    if ax != None:
        ax.clear()
        ax.plot(Rp12_abs)
        ax.plot(max_point,Rp12_abs[max_point],'xr')
        if sec_point!=None:
            ax.plot(sec_point,Rp12_abs[sec_point],'ob')
        # ax.set_title('sec_by_fst = %f'%sec_by_fst)
        ax.grid()
        ax.set_xlim([-50+BlockLen,50+BlockLen])
    # plt.show()
    return delay_sample,sec_by_fst

def GCC_SCOT(x1,x2,ax=None):
    """
    Use GCC_SCOT to get delay
    Use Quinn's interpolation method to improve accurcy
    Not for using outside this file.
    """
    # GCC_SCOT
    X1 = np.fft.fft(x1,FFT_Point) # add zeros for fft
    X2 = np.fft.fft(x2,FFT_Point)
    G12 = X1*np.conjugate(X2)
    G11 = X1*np.conjugate(X1)
    G22 = X2*np.conjugate(X2)
    Rs12 = np.fft.fftshift(np.fft.ifft(G12/np.sqrt(G11*G22)))
    Rs12_abs = np.abs(Rs12)
    max_point = np.argmax(Rs12_abs)

    # Quinn's method
    alp1 = np.real(Rs12[max_point+1]/Rs12[max_point])
    alp2 = np.real(Rs12[max_point-1]/Rs12[max_point])
    delta1 = alp1/(1-alp1)
    delta2 = -alp2/(1-alp2)
    if delta1>0 and delta2>0:
        delta = delta2
    else :
        delta = delta1
    delay_sample = (max_point-FFT_Point/2+delta)

    # print("est delay in sample: %f no delata:%f"%(delay_sample,delay_sample-delta))
    if ax != None:
        ax.clear()
        ax.plot(Rs12_abs)
        ax.plot(max_point,Rs12_abs[max_point],'xr')
        ax.grid()
        ax.set_xlim([-50+BlockLen,50+BlockLen])
    # plt.show()
    return delay_sample

def delay_estimate_array(wavs,ax=None,plt_num=1):
    """
    Input: wave matrix, (nchannel,nsample)
    Output: 
        relative delay time estimation array compares with channel 0, (nchannel,), unit: s
    """
    nchannel = wavs.shape[0]
    drop_sign = False
    delay_sample_array = np.zeros(nchannel)
    unsure_array = np.zeros(nchannel)
    for i in range(1,nchannel):
        if ax == None or i!=plt_num:
            delay_sample_array[i],unsure_array[i] = GCC_PATH(wavs[0,:],wavs[i,:])
        else:
            delay_sample_array[i],unsure_array[i] = GCC_PATH(wavs[0,:],wavs[i,:],ax=ax)
            ax=None
    # print('est delta delay sample: %s'%delay_sample_array)
    delay_time_array = delay_sample_array/fs
    if np.max(unsure_array)>block_drop_TH:
        drop_sign=True
    if np.sum(np.mean(np.abs(wavs),axis=1)<amp_drop_TH)>0:
        drop_sign=True
        print('silence drop!')
    return delay_time_array,drop_sign

def source_pos_estimate(delay_array, D):
    """
    Source Postion estimation for 5 mic diamond like array, with diameter D
    Input: 
        delay_array
            relative delay array compares with channel 0, (nchannel,), first element should be 0
        D
            diameter of mic array
    Output:
        estimated x,y positon of source.
    """
    r = (D**2 - SOUND_SPEED**2*np.sum(delay_array**2))/(2*SOUND_SPEED*np.sum(delay_array))
    theta = np.arctan2((delay_array[4]-delay_array[2])*(2*r+SOUND_SPEED*(delay_array[4]+delay_array[2])),
                      (delay_array[3]-delay_array[1])*(2*r+SOUND_SPEED*(delay_array[3]+delay_array[1]))
                     )
#     print('r = %f,theta= %f'%(r,theta))
    x = r*np.cos(theta)
    y = r*np.sin(theta)
    return x,y

# # test code
# dist = np.array([0,0.03])
# wav = load_wave('author.wav')
# g = gen_input(wav,dist,10)
# start = 4000
# GCC_PATH(g[0,start:start+BlockLen],g[1,start:start+BlockLen])
