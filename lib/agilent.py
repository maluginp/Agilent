#!/usr/bin/env python
#-*- coding: utf-8 -*-


# Class: Agilent
# Author: Malyugin Platon (@maluginp)
# Version: 0.2b


import sys
import time
import numpy
from copy import deepcopy

DEBUG_ENABLE = False

# CHANNEL 1 - Ube, Ib
# CHANNEL 2 - Uce, Ic

# Настройки
#DELAY_MEASURE = 2           # Задержка перед каждым измерением
#MAX_CHANNEL  = 2            # Количество задейственных каналов
#MAX_BREAKDOWN_FORWARD=0     # Количество предельных значений тока на 2-м канале


MAX_CHANNEL  = 3            # Количество задейственных каналов

CURRENT_RANGES = ["R1uA","R10uA","R100uA","R1mA","R10mA","R120mA"]

CURRENT_LIMITS = dict(
    R1uA   = 1e-6,
    R10uA  = 10e-6,
    R100uA = 100e-6,
    R1mA   = 1e-3,
    R10mA  = 10e-3,
    R120mA = 0.12
    )
    
VOLTAGE_RANGES = ["R2V","R20V"]

VOLTAGE_LIMITS = dict(
    R2V  = 2,
    R20V = 20
    )

from visa import *

#try:
#    get_instruments_list()
#except:
#    print "No devices found"
#    sys.exit()

agilent = 0
# Initialize Agilent
def agilent_init(name):
    global agilent
    try:
        _devices = get_instruments_list()
    except:
        print "All devices power off. \
         Please power on Agilent SMU to start measurements."
        return False
    else:
        if name in _devices:
            agilent = instrument(name)
            for ch in xrange(1,MAX_CHANNEL+1):
                initialize(ch,'v','R2V')
                initialize(ch,'c','R1uA')

            #print "Device initialized"
            return True
        else:
            print "Name %s don't found in a power on device" % (name)
            print "Agilent SMU devices:"
            for _dev in _devices:
                print _dev
            return False

# Up range
def next_range(current_range,mode):
    
    i = 0
    if mode in ["c","cur","curr"]:
    
        for range in CURRENT_RANGES:
            if i == len(CURRENT_RANGES)-1:
                return CURRENT_RANGES[i]
            if range == current_range:
                return CURRENT_RANGES[i+1]
            i+=1    
            
        return CURRENT_RANGES[len(CURRENT_RANGES)-1]
        
    elif mode in ["v","vol","volt"]:
    
        for range in VOLTAGE_RANGES:
            if i == len(VOLTAGE_RANGES)-1:
                return VOLTAGE_RANGES[i]
            if range == current_range:
                return VOLTAGE_RANGES[i+1]
            i+=1    
            
        return VOLTAGE_RANGES[len(VOLTAGE_RANGES)-1]

def set_limit_range(channel,mode,search_range):
    channel = int(channel)
    if mode in ["c","cur","curr"]:
        if search_range in CURRENT_RANGES:
            limit = CURRENT_LIMITS[search_range]
            agilent.write("CURR:LIM "+str(limit)+",(@"+str(channel)+")")
            print "NEW CURRENT LIMIT %.2e" % (limit)
    elif mode in ["v","vol","volt"]:
        if search_range in VOLTAGE_RANGES:
            limit = VOLTAGE_LIMITS[search_range]
            agilent.write("VOLT:LIM "+str(limit)+",(@"+str(channel)+")")
            print "NEW VOLTAGE LIMIT %.2e" % (limit)

# Get number of range
def get_range_num(range,mode):
    num = 0
    if mode in ["c","cur","curr"]:
        if range in CURRENT_RANGES:
            for rng in CURRENT_RANGES:
                if range == rng:
                    return num
                else:
                    num+=1
    elif mode in ["v","vol","volt"]:
        if range in VOLTAGE_RANGES:
            for rng in VOLTAGE_RANGES:
                if range == rng:
                    return num
                else:
                    num+=1
    return -1        

# Get current channel range 
def get_range(channel,mode):
    channel = int(channel)
    if not is_correct_channel(channel):
        _dbg( "Channel isn't correct: %d" % (channel) , "get_range()" )
        return

    range = ""
    if mode in ["c","cur","curr"]:
        range = agilent.ask("CURR:RANG? (@"+str(channel)+")")
    elif mode in ["v","vol","volt"]:
        range = agilent.ask("VOLT:RANG? (@"+str(channel)+")")

    _dbg( "Get range: %s, CH: %d, M: %s " % (range,channel,mode) , "get_range()" )
    return range

#     
def set_range(channel,mode,rang):
    channel = int(channel)
    
    if not is_correct_channel(channel):
        _dbg( "Channel isn't correct: %d" % (channel) , "set_range()" )
        return


    stop_output(channel)
    if mode in ["c","cur","curr"]:
        if rang in CURRENT_RANGES:
            initialize(channel,mode,rang)
    elif mode in ["v","vol","volt"]:
        if rang in VOLTAGE_RANGES:
            initialize(channel,mode,rang)
    _dbg( "Set range: %s, CH: %d, M: %s " % (rang,channel,mode) , "set_range()" )
    start_output( channel )
    time.sleep( 0.1 )

def up_range(channel,mode):   
    stop_output(channel)
    channel = int(channel)
    range = get_range(channel,mode)
    if mode in ["c","cur","curr"]:     
        if channel >= 1 and channel <= MAX_CHANNEL:
            
            agilent.write("CURR:RANG "+next_range(range,"curr")+", (@"+str(channel)+")")
            set_limit_range(channel,"c",get_range(channel,mode))
            print "Up range on CH(%d) to %s" % (channel,get_range(channel,mode))

    elif mode in ["v","vol","volt"]:
        if channel >= 1 and channel <= MAX_CHANNEL:
            agilent.write("CURR:RANG "+next_range(range,"curr")+", (@"+str(channel)+")")
            set_limit_range(channel,"v",get_range(channel,mode))
    else:
        print "source() error mode"
        sys.exit(1)
    start_output(channel)
 
def get_good_range(mode,value):  
    value = abs(value)
    if mode in ["c","cur","curr"]:
        for cur_range in CURRENT_RANGES:
            if value < (0.95*CURRENT_LIMITS[cur_range]):
                _dbg( "Value: %f , Good range: %s,  M: %s " % (value,cur_range,mode) , "get_good_range()" )
                return cur_range  
        _dbg( "Value: %f , Good range: %s,  M: %s " % (value,CURRENT_RANGES[len(CURRENT_RANGES)-1],mode) , "get_good_range()" )        
        return CURRENT_RANGES[len(CURRENT_RANGES)-1]
    elif mode in ["v","vol","volt"]:
        for volt_range in VOLTAGE_RANGES:
            if value < (0.95*VOLTAGE_LIMITS[volt_range]):
                _dbg( "Value: %f , Good range: %s,  M: %s " % (value,volt_range,mode) , "get_good_range()" )
                return volt_range  
        _dbg( "Value: %f , Good range: %s,  M: %s " % (value,VOLTAGE_RANGES[len(VOLTAGE_RANGES)-1],mode) , "get_good_range()" )
        return VOLTAGE_RANGES[len(VOLTAGE_RANGES)-1]
 
# ToDo: voltage_good_range
def set_good_range(channel,mode):
    
    _dbg( "START", "set_good_range()" )
    prev_range = ''
    count_jump = 0
    while True:
        current_range = get_range( channel, mode )      
        # time.sleep(0.3)
        value = measure( channel, mode )      
        good_range = get_good_range( mode, value )

        if current_range == good_range:
            _dbg( "Same current range and good range", "set_good_range()" )
            return True

        if get_range_num( prev_range, 'c' ) > get_range_num( good_range, 'c'):
            _dbg( "Jump down to %s from %s, CH:%d"  % (good_range,prev_range,channel),"set_good_range()")    
            if count_jump > 1:
                set_range( channel, mode, prev_range )
                _dbg( "Count jump qt 2, set uppper range: %s " % (prev_range), "set_good_range()" )
                return True
            else:
                count_jump += 1
        else:
            _dbg( "Range updated: %s, CH:%d " % (good_range,channel),"set_good_range()" )
            prev_range = good_range
            set_range( channel, mode, good_range )
            _dbg( "Test range CH:%d" % (channel), "set_good_range()" )
            continue
    return False

#! Initialize
def initialize(channel,mode,rang="",limit=0.0):
    _dbg( "Initialize channel %d, M:%s, R:%s, L:%f" % (channel,mode,rang,limit), "initialize()" )
    stop_output(channel)
    channel = int( channel )
    if mode in ["c","cur","curr"]: 
        if rang in CURRENT_RANGES:
            agilent.write("CURR:RANG "+rang+", (@"+str(channel)+")")
        else:
            rang = CURRENT_RANGES[len(CURRENT_RANGES)-1]
            agilent.write("CURR:RANG "+rang+", (@"+str(channel)+")")
        if limit > 0.0:
             agilent.write("CURR:LIM "+str(limit)+", (@"+str(channel)+")") 
        else:
             agilent.write("CURR:LIM "+str(CURRENT_LIMITS[rang])+", (@"+str(channel)+")") 
            
    elif mode in ["v","vol","volt"]:           
        if rang in VOLTAGE_RANGES:
            agilent.write("VOLT:RANG "+rang+", (@"+str(channel)+")")
        else:
            rang = VOLTAGE_RANGES[len(VOLTAGE_RANGES)-1]
            agilent.write("VOLT:RANG "+rang+", (@"+str(channel)+")")    
        if limit > 0.0:
             agilent.write("VOLT:LIM "+str(limit)+", (@"+str(channel)+")") 
        else:
             agilent.write("VOLT:LIM "+str(VOLTAGE_LIMITS[rang])+", (@"+str(channel)+")") 
    start_output(channel)


def stop_output(channel="all"):
    global agilent
    if channel == "all":
        for ch in xrange(1,MAX_CHANNEL+1):
            stop_output(ch) 
        return
    channel = int(channel)
    if not is_correct_channel(channel):
        _dbg( "Channel isn't correct: %d" % (channel) , "stop_output()" )
        return

    agilent.write("OUTP 0, (@"+str(channel)+")")

    if is_output(channel):
        _dbg( "Error!! Channel %d didn't stop output" % (channel), "stop_output()" )

def start_output(channel="all"):
    if channel == "all":
        for ch in xrange(1,MAX_CHANNEL+1):
            start_output(ch)
        return
        
    channel = int(channel)
    if not is_correct_channel(channel):
        _dbg( "Channel isn't correct: %d" % (channel) , "start_output()" )
        return

    agilent.write("OUTP 1, (@"+str(channel)+")")

    if not is_output(channel):
        _dbg( "Error!! Channel %d didn't start output" % (channel), "start_output()" )


def temperature():  
    Temp = round(float(agilent.ask("MEAS:TEMP?")),2)
    _dbg( "Current temperature:%0.2f" % (Temp) , "temperature()" )
    return Temp

def cooler(temp):
    current_temp = temperature()
    stop_output("all")
    
    if current_temp < temp:
        return

    start_time = time.time()
    print "Start Cooler"
    while temperature() >= temp:
        time.sleep(30)
        print "Cool %d. Time elapsed: %d" % (30,time.time()-start_time)
        

    start_output("all")


def source(channel,mode,value):
    channel = int(channel)
    if not is_correct_channel(channel):
        _dbg( "Channel isn't correct: %d" % (channel) , "source()" )
        return

    if not is_output(channel):
        _dbg( "CH %d stopped, started output" % (channel), "source()" )
        start_output(channel)
        time.sleep(0.1)

    good_range    = get_good_range(mode,value)
    current_range = get_range( channel, mode )  

    if good_range != current_range:
        set_range( channel,mode, good_range )

    if mode in ["c","cur","curr"]:      
        if channel >= 1 and channel <= MAX_CHANNEL:
            agilent.write("CURR "+str(value)+",(@"+str(channel)+")")

    elif mode in ["v","vol","volt"]:
        if channel >= 1 and channel <= MAX_CHANNEL:       
            agilent.write("VOLT "+str(value)+",(@"+str(channel)+")")



    else:
        print "source() error mode"
        print "> debug information:"
        print ">> CH:%d, Mode:%s, Value:%.2e" % (channel,mode,value)
        print "terminated..."
        sys.exit(1)        


        
    
def source_value(channel,mode):
    value = 0.0
    
    channel = int(channel)
    if not is_correct_channel(channel):
        _dbg( "Channel isn't correct: %d" % (channel) , "source_value()" )
        return

    if mode in ["c","cur","curr"]:
        if channel >= 1 and channel <= MAX_CHANNEL:
            value = float(agilent.ask("CURR? (@"+str(channel)+")"))

            
    elif mode in ["v","vol","volt"]:
        if channel >= 1 and channel <= MAX_CHANNEL:
            value = float(agilent.ask("VOLT? (@"+str(channel)+")"))

    else:
        print "source_value() error mode"
        print "> debug information:"
        print ">> CH:%d, Mode:%s" % (channel,mode)
        print "terminated..."
        sys.exit(1)


    return value

def measure(channel,mode):
    value = 0.0
    
    channel = int(channel)
    if not is_correct_channel(channel):
        _dbg( "Channel isn't correct: %d" % (channel) , "measure()" )
        return

    if mode in ["c","cur","curr"]:
        if channel >= 1 and channel <= MAX_CHANNEL:
            value = float(agilent.ask("MEAS:CURR? (@"+str(channel)+")"))
    elif mode in ["v","vol","volt"]:
        if channel >= 1 and channel <= MAX_CHANNEL:
            value = float(agilent.ask("MEAS:VOLT? (@"+str(channel)+")"))
    else:
        print "measure() error"
        print "> debug information:"
        print ">> CH:%d, Mode:%s" % (channel,mode)
        print "terminated..."
        sys.exit(1)
                
    return value
    
def measure_all():
    _measures = {}
    for ch in xrange(1,MAX_CHANNEL+1):
        _measures['ch'+str(ch)] = {}
        _measures['ch'+str(ch)]['volt'] = {}
        _measures['ch'+str(ch)]['curr'] = {}
        _measures['ch'+str(ch)]['volt']['meas'] = 0.0
        _measures['ch'+str(ch)]['curr']['sour'] = 0.0



    for ch in xrange(1,MAX_CHANNEL+1):
        _measures['ch'+str(ch)]['curr']['meas'] = measure(ch,'c')
        _measures['ch'+str(ch)]['curr']['sour'] = source_value(ch,'c')
        _measures['ch'+str(ch)]['volt']['meas'] = measure(ch,'v')
        _measures['ch'+str(ch)]['volt']['sour'] = source_value(ch,'v')
        
    _measures['temp'] = temperature()

    return _measures


def check_error(source,measure,error):
    _source  = abs(source)
    _measure = abs(measure)
    _error   = abs(error)

    if (_source + _error) >= _measure and (_source - _error) <= _measure:
        return True

    return False 

def set_max_channel(max_ch):
    global MAX_CHANNEL
    if max_ch >= 1 and max_ch <= 3:
        MAX_CHANNEL = max_ch
        return True
    
    return False



def drange(start, stop, step):

    range = numpy.arange( start, stop + step, step )
    return range
 

def get_source_range(ranges):

    src_range = []

    _ranges = []

    if len(ranges) < 0:
        return []

    if len(ranges.split('+')) != 1:
        _ranges = ranges.split('+')
    else:
        _ranges = [ranges]

    try:
        for _range in _ranges:

            if len(_range.split(',')) != 1:
                # 1,2,3,4

                __range = _range.split(',')
                for ___range in __range:
                    src_range += [ float(___range) ]

            elif len(_range.split(';')) != 1:

                # 1;2;0.1
                __range       = _range.split(';')
                
                __range_start = float(__range[0])
                __range_end   = float(__range[1])
                __range_step  = float(__range[2])
                
                if __range_start > __range_end:
                    _cycle = __range_start
                    src_range += [_cycle]
                    while _cycle > __range_end:
                        _cycle -= __range_step
                        src_range += [_cycle]
                else:
                    _cycle = __range_start
                    src_range += [_cycle]
                    while _cycle < __range_end:
                        _cycle += __range_step
                        src_range += [_cycle]
    
            else:
                # const

                src_range += [ float(_range) ]

    except ValueError:
        print "ValueError"
    except:
        print "Fatal error"
    else:
        return src_range   

    return []

def is_correct_channel(channel):
    global MAX_CHANNEL
    if channel >= 1 and channel <= MAX_CHANNEL:
        return True
    else:
        return False
def is_output(channel):
    ask = bool(agilent.ask("OUTP? (@"+str(channel)+")"))

    return ask

def reset():
    agilent.write("*RST")
    _dbg( "Execute reset", "reset()" )

def clear():
    agilent.write("*CLS")
    _dbg( "Execute clear", "clear()" )

def self_test():
    test = agilent.ask("*TST?")
    _dbg( "If returns a +0 the test pass, else it returns other numbers in correspond with the failure", "self_test()" )
    _dbg( "Self-test result: %s" % (test), "self_test()" )

def calibrate():
    test = agilent.ask("*CAL?")
    _dbg( "Returns a +0 if the test pass, else it returns a +1 if it fails.", "calibrate()" )
    _dbg( "Calibrate result: %s" % (test), "calibrate()" )

def errors():
    test = agilent.ask("SYST:ERR?")
    _dbg( "Errors:%s" % (test), "errors()" )

# Debug       
def state_output(channel="all"):

    if channel == "all":
        for ch in xrange(1,MAX_CHANNEL+1):
            state_output(ch) 
        return
        
    channel = int(channel)
    
    if channel >= 1 and channel <= MAX_CHANNEL:
       print "State output CH(%d): %s" % ( channel,agilent.ask("OUTP? (@"+str(channel)+")") )
       
def state_ranges(channel="all"):
    if channel == "all":
        for ch in xrange(1,MAX_CHANNEL+1):
            state_ranges(ch) 
        return
        
    channel = int(channel)
    if channel >= 1 and channel <= MAX_CHANNEL:
        print "State Volt range CH(%d): %s" % ( channel,agilent.ask("VOLT:RANG? (@"+str(channel)+")") )
        print "State Curr range CH(%d): %s" % ( channel,agilent.ask("CURR:RANG? (@"+str(channel)+")") )
        
def state_limits(channel="all"):
    if channel == "all":
        for ch in xrange(1,MAX_CHANNEL+1):
            state_limits(ch) 
        return
        
    channel = int(channel)
    
    if channel >= 1 and channel <= MAX_CHANNEL:
        print "State Volt limit CH(%d): %s" % ( channel,agilent.ask("VOLT:LIM? (@"+str(channel)+")") )
        print "State Curr limit CH(%d): %s" % ( channel,agilent.ask("CURR:LIM? (@"+str(channel)+")") )

def state_source(channel="all"):
    if channel == "all":
        for ch in xrange(1,MAX_CHANNEL+1):
            state_limits(ch) 
        return
        
    channel = int(channel)
    
    if channel >= 1 and channel <= MAX_CHANNEL:
        print "State Volt source CH(%d): %s" % ( channel,source_value(channel,"v") )
        print "State Curr source CH(%d): %s" % ( channel,source_value(channel,"c") )
        
def state_measure(channel="all"):
    
    if channel == "all":
        for ch in xrange(1,MAX_CHANNEL+1):
            state_limits(ch) 
        return
        
    channel = int(channel)
    
    if channel >= 1 and channel <= MAX_CHANNEL:
        print "State Volt measure CH(%d): %s" % ( channel,measure(channel,"v") )
        print "State Curr measure CH(%d): %s" % ( channel,measure(channel,"c") )    

def _dbg(log,module):
    global DEBUG_ENABLE
    if DEBUG_ENABLE:
        print "@%s: %s" % (module,log)

#DEBUG
def debug():
    print "#########################################"
    print "#  DEBUG  START                         #"
    print "#########################################"
    print "STATE_OUTPUT________________"
    state_output("all");
    print "STATE_RANGES________________"
    state_ranges("all")
    print "STATE_LIMITS________________"
    state_limits("all")
    print "STATE_SOURCE________________"
    state_source("all")
    print "STATE_MEASURE_______________"
    state_measure("all")
    print "#########################################"
    print "#  DEBUG  END                           #"
    print "#########################################"    
    
     #   print "Stop CH:"+str(channel)