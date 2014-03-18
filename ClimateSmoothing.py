# do some climate data filtering
# Based on: http://climatedatablog.wordpress.com/2014/03/15/r-code-for-simple-rss-graph/
from __future__ import division
import pandas as pd
from math import factorial
from mpl_toolkits.axes_grid.inset_locator import zoomed_inset_axes, mark_inset, inset_axes
import pylab
import numpy as np

# Make the smoothing functions
# based on: http://wiki.scipy.org/Cookbook/SignalSmooth
def smooth(x,window_len=12):
    """
    Standard running mean smoother. Does not add mirrored data to
    the ends of the input data. 
    Inputs:
        x: 1-D ndarray of data to be smoothed
        window_len: size of window for averaging
    Outputs:
        y: 1-D ndarray of smoothed data
        frontLen: index of where y's data starts, relative to x
        backLend: index of wheere y's data ends, relative to the end of x
    Example:
        index = np.array(range(10))
        x = np.array([1,1,2,3,5,5,6,7,8,8])
        y, frontLen, backLen = smooth(x,window_len=3)
        pylab.plot(index,x,'ok')
        pylab.plot(index[frontLen:-backLen],y,'-k')
        pylab.axis([-.2,9.2,.8,8.2])
    """
    w=np.ones(window_len,'d')
    y=np.convolve(x,w/w.sum(),mode='valid')
    # split it as evenly as possible, but put more space in the front
    # This introduces potential phase shifts that make the method
    # suitable for visualization only.
    lenDiff = len(x) - len(y)
    frontLen = np.floor(lenDiff/2)
    backLen = lenDiff - frontLen
    return y,frontLen,backLen

def CTRM(x,period=12):
    """
    Cascaded Triple Running Mean function.
    See: http://climatedatablog.wordpress.com/2014/03/15/r-code-for-simple-rss-graph/
        for the motivation and parameter selection used within.
    Inputs:
        x: 1-D ndarray of data to be smoothed
        period: size of window for averaging
    Outputs:
        y: 1-D ndarray of smoothed data
        frontLen: index of where y's data starts, relative to x
        backLend: index of wheere y's data ends, relative to the end of x
    """
    period2 = round(period/1.2067)
    period3 = round(period2/1.2067)
    newData,fl1,bl1 = smooth(x,window_len=period)
    newData,fl2,bl2 = smooth(newData,window_len=period2)
    newData,fl3,bl3 = smooth(newData,window_len=period3)
    return newData, int(fl1+fl2+fl3), int(bl1+bl2+bl3)

# http://wiki.scipy.org/Cookbook/SavitzkyGolay
# also based on the default settings for the R SG filter
# no derivatives. Modified to not need to mirror data at the ends
def SavitzkyGolayFilt(x,window_size,order=3):
    """
    Implements a single-pass Savitzky-Golay Filter.
    Code based on: http://wiki.scipy.org/Cookbook/SavitzkyGolay
    This version does not mirror the data at the ends. It uses the constant window
    size and shifts the number of left and right-hand points in the polynomial fitting
    based on where the smoothing is occurring.
    This version also does not compute any derivatives (pure smoothing)
    
    Inputs:
        x: 1-D ndarray of data to smooth
        window_size: an odd, positive integer of the window size to use in smoothing
        order: the order of the smoothing polynomial (default 3)
    Outputs:
        y: 1-D ndarray of smoothed data
            This array is the same size as x
    """
    if isinstance(x,pd.Series):
        y = np.array(x.tolist())
    else:
        y = x.copy()
    order_range = range(order+1)
    # we want to use the same window size, but vary it to the left or right as we get 
    # close to the edges
    yDummy = []
    half_window = (window_size -1) // 2
    for i in range(half_window):
        b = np.mat([[k**i for i in order_range] for k in range(-i, (window_size-i))])
        m = np.linalg.pinv(b).A[0] * factorial(0)
        v = np.convolve(m[::-1], y[:window_size], mode='valid')
        yDummy.extend(v)
    # now do the easy middle
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[0] * factorial(0)
    v = np.convolve( m[::-1], y, mode='valid')
    yDummy.extend(v)
    # do the end
    for i in range(half_window+1,window_size):
        b = np.mat([[k**i for i in order_range] for k in range(-i, window_size-i)])
        m = np.linalg.pinv(b).A[0] * factorial(0)
        v = np.convolve(m[::-1], y[-window_size:], mode='valid')
        yDummy.extend(v)
    return np.array(yDummy)

def SavitzkyGolay(x,period=12,order=3):
    """
    Implements a 5-pass Savitzky-Golay filter
    Based on: http://climatedatablog.wordpress.com/2014/03/15/r-code-for-simple-rss-graph/
    Inputs:
        x: 1-D ndarray of data to smooth
        period: a positive integer of the window size to use in smoothing
        order: the order of the smoothing polynomial (default 3)
    Outputs:
        y: 1-D ndarray of smoothed data
            This array is the same size as x
    """
    f1 = period * 2 + 1
    data = SavitzkyGolayFilt(x,f1,order)
    data = SavitzkyGolayFilt(data,f1,order)
    data = SavitzkyGolayFilt(data,f1,order)
    data = SavitzkyGolayFilt(data,f1,order)
    data = SavitzkyGolayFilt(data,f1,order)
    return data
    
# do the actual smoothing for RSS and HadCrut4 data types
# load the data
dataLoc = "http://data.remss.com/msu/graphics/TLT/time_series/RSS_TS_channel_TLT_Global_Land_And_Sea_v03_3.txt"
df = pd.read_table(dataLoc,sep="\s+",skiprows=5,header=None,names=["Year","Month","Anomaly"])
#dataLoc = "CTRM.csv"
#df = pd.read_csv(dataLoc)
# remove anomalies
df = df[df.Anomaly != -99.9]
df = df.reset_index(drop=True)
# make the date a decimal year
df["Date"] = df.Year + df.Month/12.0 - 1/24
# make the smoothed data
# CTRM at different periods
yr1LP,s1,e1 = CTRM(df.Anomaly,period=12)
yr5LP,s5,e5 = CTRM(df.Anomaly,period=12*5)
# S-G filter data
newData2 = SavitzkyGolay(df.Anomaly,period=12)

# Plot the data
fig = pylab.figure(figsize=(15,7))
ax = fig.add_subplot(111,axisbg="white")
# the data
ax.scatter(df.Date,df.Anomaly,s=15,marker='o',facecolor="1.0",lw=0.5,edgecolor="0.0")
ax.plot(df.Date[s1:-e1],yr1LP,'-y',label='Annual LP')
ax.plot(df.Date[s5:-e5],yr5LP,'-k',label='>5 yr LP')
ax.plot(df.Date,newData2,'-b',label='Annual SG',lw=1)

# plot formatting
ax.minorticks_on()
ax.grid(b=True,which="minor",axis='x')
ax.grid(b=False,which="minor",axis='y')
ax.set_xlim(1977,2015)
ax.set_xlabel("Year")
legend = ax.legend(loc=4)
legend.get_frame().set_facecolor("white")
ax.set_title("RSS Monthly Anomaly Smoothing by CTRM and Savitsky-Golay")
ax.set_ylabel("Anomaly")
pylab.show()

# HadCrut4 Data
# load the data
dataLoc = "http://www.metoffice.gov.uk/hadobs/hadcrut4/data/current/time_series/HadCRUT.4.2.0.0.monthly_ns_avg.txt"
# for some reason, usecols doesn't work not in IPython, so we name the columns to make sure that they work
df2 = pd.read_table(dataLoc,sep="\s+",header=None)
df2.rename(columns={0:"Year",1:"Anomaly"}, inplace=True)
# make the date a decimal year
df2["Date"] = df2["Year"].map(lambda x: eval(x[:4] + "+" + str(int(x[-2:])) + "/12.0 - 1/24.0"))

# make the CTRM data
yr1LP2,s12,e12 = CTRM(df2.Anomaly,period=12)
yr15LP2,s152,e152 = CTRM(df2.Anomaly,period=12*15)
yr75LP2,s752,e752 = CTRM(df2.Anomaly,period=12*30)
# make S-G filter data
yr15SG2 = SavitzkyGolay(df2.Anomaly,period=12*15)

# plot the data
fig = pylab.figure(figsize=(15,7))
ax = fig.add_subplot(111, axisbg='white')
ax.scatter(df2.Date,df2.Anomaly,s=15,marker='o',facecolor="1.0",lw=0.5,edgecolor="0.0")
ax.plot(df2.Date[s12:-e12],yr1LP2,'-y',label='Annual LP')
ax.plot(df2.Date[s152:-e152],yr15LP2,'-g',label='>15 yr LP')
ax.plot(df2.Date[s752:-e752],yr75LP2,'-b',label='>30 yr LP')
ax.plot(df2.Date,yr15SG2,'--r',label='S-G 15 yr')

# formatting the plot
ax.xaxis.set_minor_locator(pylab.MultipleLocator(5))
ax.yaxis.set_minor_locator(pylab.MultipleLocator(0.1))
ax.grid(b=True,which="minor",axis='x')
ax.grid(b=True,which="minor",axis='y')
ax.set_xticks(range(1850,2030,10))
ax.set_xlim(1843,2021)
ax.set_ylim(-1.03,0.89)
ax.set_xlabel("Year")
legend = ax.legend(loc="upper left",fontsize=14)
frame = legend.get_frame()
frame.set_facecolor('1.0')
ax.set_ylabel("Anomaly")

# adding an inset axis to view the downturn at the end better
inset_axes = zoomed_inset_axes(ax, 3, loc=4)
inset_axes.scatter(df2.Date,df2.Anomaly,s=15,marker='o',facecolor="1.0",lw=0.5,edgecolor="0.0")
inset_axes.plot(df2.Date[s12:-e12],yr1LP2,'-y',label='Annual LP')
inset_axes.plot(df2.Date[s152:-e152],yr15LP2,'-g',label='>15 yr LP')
inset_axes.plot(df2.Date[s752:-e752],yr75LP2,'-b',label='>30 yr LP')
inset_axes.plot(df2.Date,yr15SG2,'--r',label='S-G 15 yr')
x1, x2, y1, y2 = 2000, 2015, 0.3, 0.6
inset_axes.set_xlim(x1, x2)
inset_axes.set_ylim(y1, y2)
inset_axes.set_xticks([])
inset_axes.set_yticks([])
inset_axes.set_axis_bgcolor("1.0")
ax.set_title("HadCrut4 Monthly Anomaly Smoothing by CTRM and Savitsky-Golay")
mark_inset(ax, inset_axes, loc1=1, loc2=2, fc="none", ec="0.0");
pylab.show()
