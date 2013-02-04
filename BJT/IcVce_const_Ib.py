#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Graphic Gummmel-Poon
# Author: Malyugin Platon
# Changed: 25-jan-2013


import sys
import time
import math
import os
from scipy.interpolate import spline
import ConfigParser
from copy import deepcopy

config = ConfigParser.ConfigParser()

sys.path.append("../lib/")



import agilent as ag
from graphics import *

Uce_RANGES = []
Ib_RANGES = []

GRAPH_Y = []
GRAPH_X = []

#Measurement value
Measurements = dict(
    Uce   = 0.0,
    Uce_m = 0.0,
    Ic   = 0.0,
    Ube   = 0.0,
    Ib   = 0.0,
    Ib_m = 0.0,
    Temp = 0.0
)

try:
    cfg_file = sys.argv[1];
    print "Reading config file: %s" % (cfg_file)

except:
    print "Usage: ",sys.argv[0]," config_file.cfg"
    sys.exit(1)

read_cfg = config.read(cfg_file)

# Проверка считывания конфигурационного файла
if len(read_cfg) != 1:
    print "Couldn't read config file: %s" % (cfg_file)
    sys.exit(1);

# Section: Agilent
agilent_name = config.get('Agilent','name')

# Initialize agilent
if ag.agilent_init(agilent_name):
    print "Agilent initialized"
    ag.stop_output("all")
else:
    print "exited...."
    sys.exit(1)

BASE_TYPE = config.get('Device','base')



# Ube
_Ib = config.get('Agilent','Ib')
Ib_RANGES = ag.get_source_range(_Ib)
# Uce
_Uce = config.get('Agilent','Uce')
Uce_RANGES = ag.get_source_range(_Uce)

# Section: Device
devname = config.get('Device','name')


out_dir = ""
if config.getboolean('Device','create_dir_date'):
    dirname = "%02d.%02d.%04d" % (time.localtime()[2],time.localtime()[1],time.localtime()[0]) 
    if not os.path.isdir(dirname):
        #print "Directory "+str(device_name)+ " is existed";
        #sys.exit(1)
        os.mkdir(dirname,0777)
    out_dir = dirname+"/"

if config.getboolean('Device','create_dir_device'):
    dirname = out_dir+devname
    if not os.path.isdir(dirname):
        #print "Directory "+str(device_name)+ " is existed";
        #sys.exit(1)
        os.mkdir(dirname,0777)
    out_dir = dirname+"/"


outfile = config.get('Device','outfile')

if len(outfile) == 0:
    outfile = "IdsVds.txt"

if os.path.isfile( out_dir + outfile):
    rewrite = config.getboolean('Device','rewrite')

    if not rewrite:
        print "Rewrite file denied"
        exit()

SAVE_DEBUG = config.getboolean('Device','save_debug')

fmeasure = open(out_dir + "tsunami_out.txt", "w")
fdbg     = open(out_dir + outfile, "w")

# Section: Measure
MEASURE_DELAY      = config.getfloat('Measure','delay')          # Задержка перед каждым измерением (сек)
MEASURE_COUNT      = config.getint('Measure','count')
MEASURE_MAX_FAILED = config.getint('Measure','max_failed')

# Section: Graphic
INCLUDE_GRAPHICS   = config.getboolean('Graphic','enable')
INTERPOLATED       = config.getboolean('Graphic','spline')

# TODO: move to config
if config.has_option( 'Agilent', 'channel_Ube' ):
    CHANNEL_UBE = config.getint( 'Agilent', 'channel_Ube' )
else:
    CHANNEL_UBE = 1
if config.has_option( 'Agilent', 'channel_Uce' ):
    CHANNEL_UCE = config.getint( 'Agilent', 'channel_Uce' )
else:
    CHANNEL_UCE = 2


# Количество 
COUNT_CURRENT_SATURATION = 0

def _write_measure(init=False):
    global fmeasure
    if init:
        fmeasure.write("@COLS:Ube,Ib,Uce,Ic\n")
    else:
        fmeasure.write( "%.2f\t%.2e\t%.2f\t%.2e\n" % (meas("Ube",2),meas("Ib"),meas("Uce",2),meas("Ic")) )

def _log(_log):
    global fdbg

    print _log
    fdbg.write(str(_log)+"\n")

def meas(name,rnd = -1):
    global Measurements

    if name in Measurements:

        _measure = float(Measurements[name]) 
        if rnd != -1:
            _measure = round(_measure,rnd)

        return _measure

    return -1

def re_measure(cycle=1):
    global Measurements

    if ag.temperature() >= 50.0:
        print "High temperature! Cooler!!!!"
        ag.stop_output("all")
        ag.state_output()
        while ag.temperature() >= 40.0:
            print "Current Temperature: %.2f, Delay: %d sec" % ( ag.temperature(),60 * MEASURE_DELAY )
            print "Delay"
            for sec in xrange( 12 * MEASURE_DELAY ):
                print "%d, " % (sec*5),
                time.sleep(5)

        ag.start_output("all")
    

    Ube  = Ib = Ib_m = Uce = Uce_m = Ic = Temp = 0.0


    for i in xrange(cycle):
        # Impulse measure
        time.sleep( MEASURE_DELAY )

        Ib    += ag.source_value(CHANNEL_UBE,'c')
        Ib_m  += ag.measure(CHANNEL_UBE,'c')
        Ube   += ag.measure(CHANNEL_UBE,'v')
        Ic    += ag.measure(CHANNEL_UCE,'c')
        Uce   += ag.source_value(CHANNEL_UCE,'v')
        Uce_m += ag.measure(CHANNEL_UCE,'v')
        Temp  += ag.temperature()

    Measurements['Ib']    = Ib    / float(cycle)
    Measurements['Ib_m']  = Ib_m  / float(cycle)
    Measurements['Ube']   = Ube   / float(cycle)
    Measurements['Ic']    = Ic    / float(cycle)
    Measurements['Uce']   = Uce   / float(cycle)
    Measurements['Uce_m'] = Uce_m / float(cycle)
    Measurements['Temp']  = Temp  / float(cycle)
    
def execute():
    global GRAPH_X,GRAPH_Y,COUNT_CURRENT_SATURATION,INCLUDE_GRAPHICS

    no_inc = False 

    #if ag.check_error( meas('Uds') , meas('Uds_m'), 0.03 ):
    #    ag.up_range(  )
    #    time.sleep( MEASURE_DELAY )
    #    re_measure()
    if not ag.set_good_range( CHANNEL_UBE, 'v' ):
        print "Can't set good range for CH Ube"
    if not ag.set_good_range( CHANNEL_UCE, 'c' ):
        print "Can't set good range for CH Uce"    

    # if round(meas('Ic'),3) == 0.120:
    #     if COUNT_CURRENT_SATURATION > 2:
    #         return False
    #     else:
    #         COUNT_CURRENT_SATURATION += 1
    
    # if round(meas('Ib'),3) == 0.120:
    #     if COUNT_CURRENT_SATURATION > 2:
    #         return False
    #     else:
    #         COUNT_CURRENT_SATURATION += 1        

    re_measure( MEASURE_COUNT )
    
    if not ag.check_error( meas('Uce',2), meas('Uce_m',2), 0.06 ):
        no_inc = True
    if not ag.check_error( meas('Ib'), meas('Ib_m'), meas('Ib')*0.1 ):
        no_inc = True    
    


    if INCLUDE_GRAPHICS and no_inc == False:
        if BASE_TYPE == "p":
            GRAPH_X += [meas('Uce')]
            GRAPH_Y += [meas('Ic')]
        elif BASE_TYPE == "n":
            GRAPH_X += [-meas('Uce')]
            GRAPH_Y += [-meas('Ic')]

    # Uds,Uds_m,Ugs,Ugs_m,Ubs,Ubs_m, Ids

    _smile = ":D"
    if no_inc == True:
        _smile = "o_O"

    buf = "%s\t%.2f\t%.2e\t%.2e\t%.2f\t%.2f\t%.2e\t%.2f" % (_smile, 
        meas('Ube'),meas('Ib'),meas('Ib_m'),meas('Uce'), \
        meas('Uce_m'),meas('Ic'),meas('Temp') )
    _log(buf)

    if no_inc == False:
        _write_measure()
    
    
    return True

if INCLUDE_GRAPHICS:
    plt.figure(1,figsize=(18, 9), dpi=80, facecolor='w', edgecolor='k')

style = 0

# 

_write_measure(True)
ag.start_output('all')
for Ib in Ib_RANGES:
    ag.source(CHANNEL_UBE,'c',Ib)
    GRAPH_Y = []
    GRAPH_X = []
    style += 1

    title = "Ib=%.2e" % (Ib)
    _log(title)
    _log("  \tUbe\tIb        \tIb_m      \tUce\tUce_m\tIc\t        Temp")
    
    for Uce in Uce_RANGES:
        ag.source(CHANNEL_UCE,'v',Uce)
        
        if not execute():
            _log("Error in execute")


    if INCLUDE_GRAPHICS:
        if len(GRAPH_X) > 0:
            _GRAPH_X = deepcopy(GRAPH_X)
            _GRAPH_X.sort()
            _GRAPH_Y = []
            for x in _GRAPH_X:
                i=0
                for _x in GRAPH_X:
                    if x == _x:
                        _GRAPH_Y += [ GRAPH_Y[i] ]
                        break
                    i+=1

            plt.plot( _GRAPH_X, _GRAPH_Y, get_style_plot(style,False),label=title )
            

    time.sleep( 0.5 )
ag.stop_output('all')

fdbg.close()
fmeasure.close()
#fdbg.close()
if INCLUDE_GRAPHICS:
    plt.title('Output I-V')
    plt.xlabel('Uce, V')
    plt.ylabel('Ic, A')
    plt.grid(True)
    plt.legend(loc = 'lower right')
    plt.savefig(out_dir+'out_iv.png')
    plt.show()








