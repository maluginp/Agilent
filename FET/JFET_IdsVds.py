#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Output I-V
# Author: Malyugin Platon
# Changed: 25-jan-2013
# CH1: Ids, Uds
# CH2: Ugs
# CH3: Ubs
# Version: 0.01a

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

Ubs_RANGES = []
Uds_RANGES = []
Ugs_RANGES = []

GRAPH_Y = []
GRAPH_X = []

Measurements = dict(

    Ids   = 0.0,
    Uds   = 0.0,
    Uds_m = 0.0,
    Ugs   = 0.0,
    Ugs_m = 0.0,
    Ubs   = 0.0,
    Ubs_m = 0.0,
    Temp  = 0.0

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





# Uds

_Uds = config.get('Agilent','Uds')
Uds_RANGES = ag.get_source_range(_Uds)
#  Ugs
_Ugs = config.get('Agilent','Ugs')
Ugs_RANGES = ag.get_source_range(_Ugs)

#  Ubs
_Ubs = config.get('Agilent','Ubs')
Ubs_RANGES = ag.get_source_range(_Ubs)

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

#fmeasure = open(out_dir + outfile, "w")
fdbg     = open(out_dir + outfile, "w")

# Section: Measure
MEASURE_DELAY      = config.getfloat('Measure','delay')          # Задержка перед каждым измерением (сек)
MEASURE_COUNT      = config.getint('Measure','count')
MEASURE_MAX_FAILED = config.getint('Measure','max_failed')

# Section: Graphic
INCLUDE_GRAPHICS   = config.getboolean('Graphic','enable')
INTERPOLATED       = config.getboolean('Graphic','spline')

# TODO: move to config

CHANNEL_UDS = config.getint( 'Agilent', 'channel_Uds' )
CHANNEL_UGS = config.getint( 'Agilent', 'channel_Ugs' )
CHANNEL_UBS = config.getint( 'Agilent', 'channel_Ubs' )


# Количество 
COUNT_CURRENT_SATURATION = 0

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
    

    Ids = Uds = Uds_m = Ugs = Ugs_m = Ubs = Ubs_m = Temp = 0.0


    for i in xrange(cycle):
        # Impulse measure
        time.sleep( MEASURE_DELAY )
        _measures = deepcopy(ag.measure_all())

        Ids   += _measures['ch1']['curr']['meas'] 
        Uds   += _measures['ch1']['volt']['sour']
        Uds_m += _measures['ch1']['volt']['meas']
        Ugs   += _measures['ch2']['volt']['sour']
        Ugs_m += _measures['ch2']['volt']['meas']
        Ubs   += _measures['ch3']['volt']['sour']
        Ubs_m += _measures['ch3']['volt']['meas']

        Temp  += _measures['temp']

        

    Measurements['Ids']   = Ids   / float(cycle)
    Measurements['Uds']   = Uds   / float(cycle)
    Measurements['Uds_m'] = Uds_m / float(cycle)
    Measurements['Ugs']   = Ugs   / float(cycle)
    Measurements['Ugs_m'] = Ugs_m / float(cycle)
    Measurements['Ubs']   = Ubs   / float(cycle)
    Measurements['Ubs_m'] = Ubs_m / float(cycle)
    Measurements['Temp']  = Temp  / float(cycle)

    
def execute():
    global GRAPH_X,GRAPH_Y,COUNT_CURRENT_SATURATION,INCLUDE_GRAPHICS

    no_inc = False 

    #if ag.check_error( meas('Uds') , meas('Uds_m'), 0.03 ):
    #    ag.up_range(  )
    #    time.sleep( MEASURE_DELAY )
    #    re_measure()


    if not ag.set_good_range( CHANNEL_UDS, 'c' ):
        print "Can't set good range for channel UDS"
    if not ag.set_good_range( CHANNEL_UGS, 'c' ):
        print "Can't set good range for channel UGS"
    if not ag.set_good_range( CHANNEL_UBS, 'c' ):
        print "Can't set good range for channel UBS"

    if round(meas('Ids'),3) == 0.120:
        if COUNT_CURRENT_SATURATION > 1:
            return False
        else:
            COUNT_CURRENT_SATURATION += 1


    re_measure( MEASURE_COUNT )


    if not ag.check_error( meas('Uds',2), meas('Uds_m',2), 0.06 ):
        no_inc = True
    
    if not ag.check_error( meas('Ugs',2), meas('Ugs_m',2), 0.06 ):
        no_inc = True
    
    if not ag.check_error( meas('Ubs',2), meas('Ubs_m',2), 0.06 ):
        no_inc = True
        
    


    if INCLUDE_GRAPHICS and no_inc == False:
        GRAPH_X += [meas('Uds')]
        GRAPH_Y += [meas('Ids')]

    # Uds,Uds_m,Ugs,Ugs_m,Ubs,Ubs_m, Ids

    _smile = ":D"
    if no_inc == True:
        _smile = "o_O"


    buf = "%s\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2e\t%.2f" % (_smile, 
        meas('Uds'),meas('Uds_m'),meas('Ugs'),meas('Ugs_m'), \
        meas('Ubs'),meas('Ubs_m'),meas('Ids'),meas('Temp') )
    _log(buf)
    return True

if INCLUDE_GRAPHICS:
    plt.figure(1,figsize=(18, 9), dpi=80, facecolor='w', edgecolor='k')

style = 0

# 


ag.start_output('all')
for Ubs in Ubs_RANGES:
    ag.source(CHANNEL_UBS,'v',Ubs)
    for Ugs in Ugs_RANGES:
        ag.source(CHANNEL_UGS,'v',Ugs)
        GRAPH_Y = []
        GRAPH_X = []
        style += 1

        title = "Ugs=%.2f, Ubs=%.2f" % (Ugs,Ubs)
        _log(title)
        _log("  \tUds\tUds_m\tUgs\tUgs_m\tUbs\tUbs_m\tIds\t        Temp")

        for Uds in Uds_RANGES:
            ag.source(CHANNEL_UDS,'v',Uds)

            if not execute():
                _log("Error in execute")


        if INCLUDE_GRAPHICS:
            if len(GRAPH_X) > 0:
                plt.plot( GRAPH_X, GRAPH_Y, get_style_plot(style,True),label=title )

        time.sleep( 0.5 )
ag.stop_output('all')

fdbg.close()
#fmeasure.close()
#fdbg.close()
if INCLUDE_GRAPHICS:
    plt.title('Output I-V')
    plt.xlabel('Uds, V')
    plt.ylabel('Ids, A')
    plt.grid(True)
    plt.legend(loc = 'lower right')
    plt.savefig(out_dir+'out_iv.png')
    plt.show()








