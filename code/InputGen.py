# Function for 
# 1) record/load input wave file
# 2) generate noise-added input signal based on distance

import pyaudio
import wave
import struct
import numpy as np
from pathlib import Path

from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('TKAgg')

# global variables
channels = 1
fs = 16000
sample_format = pyaudio.paInt16
max_int_16 = 2**15-1
SOUND_SPEED = 343.0

def record_wave(seconds):
    i = 0
    while (Path.exists(Path('Rec_'+str(i).zfill(2)+'.wav'))):
        i += 1
    filename = 'Rec_'+str(i).zfill(2)+'.wav'
    p = pyaudio.PyAudio()
    print('Recording...')
    stream = p.open(format=sample_format,
                channels=channels,
                rate=fs,
                frames_per_buffer=fs,
                input=True)
    rec_sound = stream.read(fs*seconds)
    stream.stop_stream()
    stream.close()
    p.terminate()
    print(' Done..')
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(rec_sound)
    wf.close()
    rec_sound = np.array(struct.unpack('h' * fs*seconds, rec_sound))
    rec_sound = rec_sound/max_int_16  # normalize to [-1.1]
    return rec_sound

def load_wave(filename):
    wf = wave.open(filename, 'rb')
    CHANNELS        = wf.getnchannels()     # Number of channels
    RATE            = wf.getframerate()     # Sampling rate (frames/second)
    signal_length   = wf.getnframes()       # Signal length
    WIDTH           = wf.getsampwidth()     # Number of bytes per sample
    if CHANNELS != 1:
        raise Exception("Only support one channel wave files!")
    if WIDTH != 2:
        raise Exception("Only support 16 bit wave files!")
    if RATE != fs:
        raise Exception('Only support sample rate 16000!')
    wav = wf.readframes(signal_length) 
    wav = np.array(struct.unpack('h' * signal_length, wav))
    wav = wav/max_int_16 # normalize to [-1.1]
    return wav

def gen_input(wav, dist_array, snr):
    """
    Input: 
        wav         :np array, (n,), normalized to [-1,1]
        dist_array  :np array, (nchannels,), distance from each mic to source(in meter)
        snr         :Signal to noise rate in dB
    Output:
        np array, (nchannels,n-max_delay_sample), simulated input wave for each channel 
    Use linear interpolation for fraction delay
    """
    nchannel = len(dist_array)
    nsample = len(wav)
    # delay
    delay_sample_array = dist_array/SOUND_SPEED*fs
    max_delay_sample = int(np.ceil(np.max(delay_sample_array)))
    output = np.zeros((nchannel,nsample-max_delay_sample))
    delay_to_max_int = np.floor(max_delay_sample - delay_sample_array).astype(np.int32)
    delay_to_max_frac = max_delay_sample - delay_sample_array - delay_to_max_int
    print('delay gen in sample: %s'%delay_sample_array)
    print("delay gen delta in sample: %s"%np.array([delay_sample_array[0]-x for x in delay_sample_array]))
    for i_new,i_orig in enumerate(range(max_delay_sample,nsample)):
        for chn in range(nchannel):
            alpha = delay_to_max_frac[chn]
            output[chn,i_new] = wav[i_orig-delay_to_max_int[chn]]*(1-alpha)+wav[i_orig-delay_to_max_int[chn]-1]*alpha
    
    # add noise
    avg_signal_power_db = 10*np.log10(np.sum(wav**2)/nsample)
    noise_power_db = avg_signal_power_db - snr
    noise_power = 10**(noise_power_db/10)
    noise = np.random.normal(0,noise_power,output.shape)
    output += noise
    return output

# # test code
# plt.figure()
# dist = np.array([0,0.1,0.2])
# wav = load_wave('cosine_200_hz.wav')
# g = gen_input(wav,dist,100)
# for i in range(len(dist)):
#     plt.plot(g[i,:200],label='%d'%i)
# plt.legend()
# plt.grid()
# plt.show()