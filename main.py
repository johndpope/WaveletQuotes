import urllib.request, urllib.error, urllib.parse
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from matplotlib.finance import candlestick_ochl
import matplotlib
import pylab
import pywt
matplotlib.rcParams.update({'font.size': 9})

def rsiFunc(prices, n=14):
    deltas = np.diff(prices)
    seed = deltas[:n+1]
    up = seed[seed>=0].sum()/n
    down = -seed[seed<0].sum()/n
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100./(1.+rs)

    for i in range(n, len(prices)):
        delta = deltas[i-1] # cause the diff is 1 shorter

        if delta>0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(n-1) + upval)/n
        down = (down*(n-1) + downval)/n

        rs = up/down
        rsi[i] = 100. - 100./(1.+rs)

    return rsi

def movingaverage(values,window):
    weigths = np.repeat(1.0, window)/window
    smas = np.convolve(values, weigths, 'valid')
    return smas # as a numpy array


def ExpMovingAverage(values, window):
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= weights.sum()
    a =  np.convolve(values, weights, mode='full')[:len(values)]
    a[:window] = a[window]
    return a


def computeMACD(x, slow=26, fast=12):
    """
    compute the MACD (Moving Average Convergence/Divergence) using a fast and slow exponential moving avg'
    return value is emaslow, emafast, macd which are len(x) arrays
    """
    emaslow = ExpMovingAverage(x, slow)
    emafast = ExpMovingAverage(x, fast)
    return emaslow, emafast, emafast - emaslow

def bytespdate2num(fmt, encoding='utf-8'):
    strconverter = mdates.strpdate2num(fmt)
    def bytesconverter(b):
        s = b.decode(encoding)
        return strconverter(s)
    return bytesconverter

def loadStock(stock):
    '''
        Use this to dynamically pull a stock:
    '''
    stockFile =[]
    try:
        print('Currently Pulling',stock)
        urlToVisit = 'http://chartapi.finance.yahoo.com/instrument/1.0/'+stock+'/chartdata;type=quote;range=10y/csv'
        print('URL', urlToVisit)
        try:
            sourceCode = urllib.request.urlopen(urlToVisit).read().decode()
            splitSource = sourceCode.split('\n')
            for eachLine in splitSource:
                splitLine = eachLine.split(',')
                if len(splitLine)==6:
                    if 'values' not in eachLine:
                        stockFile.append(eachLine)
        except Exception as e:
            print(str(e), 'failed to organize pulled data.')
    except Exception as e:
        print(str(e), 'failed to pull pricing data')
    return stockFile

def graphData(stock,MA1,MA2):
    stockFile = loadStock(stock)
    stockFile = stockFile[1:100]
    try:
        date, closep, highp, lowp, openp, volume = np.loadtxt(stockFile,delimiter=',', unpack=True,
                                                              converters={ 0: bytespdate2num('%Y%m%d')})
        x = 0
        y = len(date)
        newAr = []
        while x < y:
            appendLine = date[x],openp[x],highp[x],lowp[x],closep[x],volume[x]
            newAr.append(appendLine)
            x+=1

        Av1 = movingaverage(closep, MA1)
        Av2 = movingaverage(closep, MA2)
        print(closep)
        SP = len(date[MA2-1:])
        cA,cD = pywt.dwt(closep,'haar')
#SMA
#--------------------------------------
        fig = plt.figure(facecolor='#07000d')

        ax1 = plt.subplot2grid((6,4), (1,0), rowspan=4, colspan=4, axisbg='#07000d')
        candlestick_ochl(ax1, newAr[-SP:], width=.6, colorup='#53c156', colordown='#ff1717')

        Label1 = str(MA1)+' SMA'
        Label2 = str(MA2)+' SMA'
        newDate = date[-SP:]
        newDate = newDate[1::2]
        ax1.plot(newDate[-SP/2:],cA[-SP/2:],'#e1edf9',label=Label1, linewidth=1.5)
        ax1.plot(newDate[-SP/2:],cD[-SP/2:],'#4ee6fd',label=Label2, linewidth=1.5)

        ax1.grid(True, color='w')
        ax1.xaxis.set_major_locator(mticker.MaxNLocator(10))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.yaxis.label.set_color("w")
        ax1.spines['bottom'].set_color("#5998ff")
        ax1.spines['top'].set_color("#5998ff")
        ax1.spines['left'].set_color("#5998ff")
        ax1.spines['right'].set_color("#5998ff")
        ax1.tick_params(axis='y', colors='w')
        plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune='upper'))
        ax1.tick_params(axis='x', colors='w')
        plt.ylabel('Stock price and Volume')
        maLeg = plt.legend(loc=9, ncol=2, prop={'size':7},
                   fancybox=True, borderaxespad=0.)
        maLeg.get_frame().set_alpha(0.4)
        textEd = pylab.gca().get_legend().get_texts()
        pylab.setp(textEd[0:5], color = 'w')

        ax1.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='upper'))
        for label in ax1.xaxis.get_ticklabels():
            label.set_rotation(45)

        plt.suptitle(stock.upper(),color='w')
        plt.setp(ax1.get_xticklabels(), visible=True)

        # ax1.annotate('Big news!',(date[510],Av1[510]),
        #     xytext=(0.8, 0.9), textcoords='axes fraction',
        #     arrowprops=dict(facecolor='white', shrink=0.05),
        #     fontsize=14, color = 'w',
        #     horizontalalignment='right', verticalalignment='bottom')

        plt.subplots_adjust(left=.09, bottom=.14, right=.94, top=.95, wspace=.20, hspace=0)
        plt.show()
        # fig.savefig('example.png',facecolor=fig.get_facecolor())

    except Exception as e:
        print('main loop',str(e))

# while True:
#     stock = input('Stock to plot: ')
#     graphData(stock,10,50)

graphData('eurusd=x',10,50)
