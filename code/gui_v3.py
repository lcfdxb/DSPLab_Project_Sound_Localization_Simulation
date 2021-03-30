import numpy as np
import math
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('TKAgg')
import tkinter as Tk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,NavigationToolbar2Tk) 

from InputGen import *
from CoreAlgr import *

# global variables
filename = 'test01.wav'
wav = load_wave(filename)
SNR = 10
sound_src = [2,2] # source position
Mic_Array_D = 2# diameter of array
mic0 = [0,0] #center
mic1 = [Mic_Array_D/2,0] #right
mic2 = [0,Mic_Array_D/2] #top
mic3 = [-Mic_Array_D/2,0] #left
mic4 = [0,-Mic_Array_D/2] #botton
micX,micY = zip(mic0,mic1,mic2,mic3,mic4)
s_mic = [10,10,10,10,10]
c_mic = 'blue'
map_size = [-5,5,-5,5]

# ui
root = Tk.Tk()
root.title('2D Sound Localization Simulator')

my_fig = plt.figure(1,figsize=(10,5))
my_plot = my_fig.add_subplot(1, 2, 1)
my_plot.set_title('map')
my_plot.grid()
my_plot.set_xlim(map_size[:2])
my_plot.set_ylim(map_size[2:])
# plot axis line
my_plot.plot(map_size[:2],[0,0],'black',linewidth=0.5)
my_plot.plot([0,0],map_size[2:],'black',linewidth=0.5)
# plot mic array
my_plot.plot(micX,micY,ls='',marker = 'D',markersize = 3,color = c_mic,label='mic')
# handle for src positon plot, so we only need to update src point
est_sample_plot = my_plot.plot([],[],'yx',label='est sample')[0]
src_plot = my_plot.plot(sound_src[0],sound_src[1],'ro',label='source')[0]
est_plot = my_plot.plot([],[],'kx',label='estimation median')[0]

wav_plot = my_fig.add_subplot(1, 2, 2)
wav_plot_line = wav_plot.plot(wav)[0]
wav_plot.grid()
wav_plot.set_title('wave file and each block\nFile:%s'%filename.split('/')[-1])
wav_plot.set_ylim([-1,1])

# gcc_plot = my_fig.add_subplot(1, 3, 3)
# gcc_plot.set_title('GCC cross-correlation plot')
# RB_var = Tk.IntVar()
# RB_var.set(1)
# RB1 = Tk.Radiobutton(root, text="Mic0 & Mic1", variable=RB_var, value=1)
# RB2 = Tk.Radiobutton(root, text="Mic0 & Mic2", variable=RB_var, value=2)
# RB3 = Tk.Radiobutton(root, text="Mic0 & Mic3", variable=RB_var, value=3)
# RB4 = Tk.Radiobutton(root, text="Mic0 & Mic4", variable=RB_var, value=4)

# Turn fig into a Tkinter widget
my_canvas = FigureCanvasTkAgg(my_fig, master = root)
toolbar = NavigationToolbar2Tk(my_canvas, root)

W1 = my_canvas.get_tk_widget()
# my_fig.canvas.draw()
toolbar.update()

X_location = Tk.DoubleVar()
X_location.set(sound_src[0])
Y_location = Tk.DoubleVar()
Y_location.set(sound_src[1])
x = X_location.get()
y = Y_location.get()

location_src = Tk.StringVar()
location_src.set("Source location is %s"%sound_src)
location_est = Tk.StringVar()
location_est.set("Estimate location is ")

def get_dist(micX,micY,sound_src):
    """
    return the distance array based on XY of mic and source positon
    Output: distance array from mic0-4 to source, (nchannel,)
    """
    dist = np.zeros(len(micX))
    for i in range(len(dist)):
        dist[i] = np.sqrt((micX[i]-sound_src[0])**2+(micY[i]-sound_src[1])**2)
    return dist

def updateLocation(event):
    """
    Callback for updating source location 
    """
    global sound_src
    x = X_location.get()
    y = Y_location.get()
    sound_src = [x,y] 
    src_plot.set_xdata([x])
    src_plot.set_ydata([y])
    my_fig.canvas.draw()
    location_src.set("Source location is %s"%sound_src)

# test code
def run():
    global SNR
    if len(wav)==0:
        print('Load or Record wave file first!')
    else :
        dist = get_dist(micX,micY,sound_src)
        print('dist=%s'%dist)
        SNR = float(Text_SNR.get())
        input_wav = gen_input(wav, dist, SNR)
        BlockNum = int(input_wav.shape[1]/BlockLen)
        e_x_list_trust = []
        e_y_list_trust = []
        drop_cnt = 0
        est_plot.set_xdata([])
        est_plot.set_ydata([])
        for i in range(BlockNum):
            start = i*BlockLen
            delay_array,drop_sign = delay_estimate_array(input_wav[:,start:start+BlockLen],ax=None)#,plt_num=RB_var.get())
            if drop_sign:
                # e_x,e_y = source_pos_estimate(delay_array,Mic_Array_D)
                # location_est.set("Estimate location is [%.3f,%.3f] and can't be trust"%(e_x,e_y))
                drop_cnt += 1
            else:
                e_x,e_y = source_pos_estimate(delay_array,Mic_Array_D)
                e_x_list_trust.append(e_x)
                e_y_list_trust.append(e_y)
                est_sample_plot.set_xdata([e_x_list_trust])
                est_sample_plot.set_ydata([e_y_list_trust])
                # location_est.set("Estimate location is [%.3f,%.3f]"%(e_x,e_y))
            wav_plot.set_xlim([start,start+BlockLen])
            my_fig.canvas.draw()
            toolbar.update()
        e_x_med = np.median(e_x_list_trust)
        e_y_med = np.median(e_y_list_trust)
        est_plot.set_xdata(e_x_med)
        est_plot.set_ydata(e_y_med)
        my_plot.legend()
        location_est.set("Estimate location is [%.3f,%.3f], drop %d block out of %d"%(e_x_med,e_y_med,drop_cnt,BlockNum))
        print('e_x:%s'%e_x_list_trust)
        print('e_y:%s'%e_y_list_trust)
        my_fig.canvas.draw()
        toolbar.update()
        

def load_wave_gui():
    global wav,filename
    filename = Tk.filedialog.askopenfilename()
    wav = load_wave(filename)
    wav_plot_line.set_ydata(wav)
    wav_plot_line.set_xdata(range(len(wav)))
    wav_plot.set_xlim([0,len(wav)])
    wav_plot.set_title('wave file and each block\nFile:%s'%filename.split('/')[-1])
    my_fig.canvas.draw()

def record_wave_gui():
    global wav
    wav = record_wave(5)
    wav_plot_line.set_ydata(wav)
    wav_plot_line.set_xdata(range(len(wav)))
    wav_plot.set_xlim([0,len(wav)])
    wav_plot.set_title('wave file and each block\nFile: record')
    my_fig.canvas.draw()

S1 = Tk.Scale(root,
  length = 200, orient = Tk.HORIZONTAL, from_ = map_size[0], to = map_size[1], resolution = 0.1,
  command = updateLocation,
  label = 'Source Pos X',
  variable = X_location)

S2 = Tk.Scale(root,
  length = 200, orient = Tk.HORIZONTAL, from_ = map_size[2], to = map_size[3], resolution = 0.1,
  command = updateLocation,
  label = 'Source Pos Y',
  variable = Y_location)

# start_var = Tk.DoubleVar()
# S3 = Tk.Scale(root,
#   length = 200, orient = Tk.HORIZONTAL, from_ = 0, to = len(wav)-1, resolution = 1,
#   label = 'Start sample',
#   variable = start_var)

Text_SNR = Tk.StringVar()
Text_SNR.set('%f'%SNR)
E_SNR = Tk.Entry(root,textvariable = Text_SNR)
L_SNR = Tk.Label(root, text='SNR')
B1 = Tk.Button(root, text = 'load', command = load_wave_gui)
B2 = Tk.Button(root,text = 'record',command = record_wave_gui)
B3 = Tk.Button(root,text = 'run',command = run)
L4 = Tk.Label(root, textvariable = location_src )
L5 = Tk.Label(root, textvariable = location_est )


W1.pack(side=Tk.TOP)
S1.pack(side=Tk.TOP)
S2.pack(side=Tk.TOP)
# S3.pack(side=Tk.TOP)
L_SNR.pack(side=Tk.TOP)
E_SNR.pack(side=Tk.TOP)
B1.pack(side=Tk.TOP)
B2.pack(side=Tk.TOP)
B3.pack(side=Tk.TOP)
L4.pack(side=Tk.TOP)
L5.pack(side=Tk.TOP)

# RB1.pack(side=Tk.LEFT)
# RB2.pack(side=Tk.LEFT)
# RB3.pack(side=Tk.LEFT)
# RB4.pack(side=Tk.LEFT)


CONTINUE = True
while CONTINUE:
    root.update()