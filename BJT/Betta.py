#!/usr/bin/env python
#-*- coding: utf-8 -*-

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


Ue_RANGES = []
Uc_RANGES = []

stop_measure = False

# Для графиков
IV_I = []
IV_V = []

GRAPH_2_Y = []
GRAPH_2_X = []



#Measurement value
Measurements = dict(
    Uc   = 0.0,
    Uc_m = 0.0,
    Ic   = 0.0,
    Ue   = 0.0,
    Ue_m = 0.0,
    Ib   = 0.0,
    Temp = 0.0
)

PrevMeasurements = deepcopy(Measurements)
 
# BANNER
print """
Welcome to Betta measurement.

Channel (CH1) : Ube   (Voltage Base-Emitter)
Channe2 (CH2) : Uce   (Voltage Collector-Emitter)

Author: Malyugin Platon (Last change: 16-jan-2013)

The shortest answer is doing the thing / Ernest Hemingway

------------------------------------------------------

"""   


try:
    cfg_file = sys.argv[1];
    print "Reading config file: %s" % (cfg_file)
    #if(len(sys.argv) == 3):
    #    if sys.argv[2].lower() in ["y","yes"]:
    #        force_rewrite = True
except:
    print "Usage: ",sys.argv[0]," config_file.cfg"
    sys.exit(1)

read_cfg = config.read(cfg_file)

# Проверка считывания конфигурационного файла
if len(read_cfg) != 1:
    print "Can't read config_file: %s" % (cfg_file)
    sys.exit(0)

# Section: Agilent
agilent_name = config.get('Agilent','name')

# Initialize agilent
if ag.agilent_init(agilent_name):
    print "Agilent initialized"
    ag.stop_output("all")
else:
    print "exited...."
    sys.exit(1)

# Set Ue_RANGES

_Ue = config.get('Agilent','Ue')
try:

    if len(_Ue.split(',')) != 1:
        # 1,2,3,4
        __Ue = _Ue.split(',')
        for ___Ue in __Ue:
            Ue_RANGES += [ float(___Ue) ]

    elif len(_Ue.split(';')) != 1:
        # 1;2;0.1
        __Ue = _Ue.split(';')
        __Ue_start = float(__Ue[0])
        __Ue_end   = float(__Ue[1])
        __Ue_step  = float(__Ue[2])

        Ue_RANGES = ag.drange(__Ue_start,__Ue_end,__Ue_step)

    else:
        # const
        Ue_RANGES = [ float(_Ue) ]

except ValueError:
    print "ValueError"
    sys.exit(1)

except:
    print "Fatal error"
    sys.exit(1)


# Set Uc_RANGES
_Uc = config.get('Agilent','Uc')
try:

    if len(_Uc.split(',')) != 1:
        # 1,2,3,4
        __Uc = _Uc.split(',')
        for ___Uc in __Uc:
            Uc_RANGES += [ float(___Uc) ]

    elif len(_Uc.split(';')) != 1:
        # 1;2;0.1
        __Uc = _Uc.split(';')
        __Uc_start = float(__Uc[0])
        __Uc_end   = float(__Uc[1])
        __Uc_step  = float(__Uc[2])

        Uc_RANGES = ag.drange(__Uc_start,__Uc_end,__Uc_step)

    else:
        # const
        Uc_RANGES = [ float(_Uc) ]

except ValueError:
    print "ValueError"
    sys.exit(1)

except:
    print "Fatal error"
    sys.exit(1)


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
    outfile = "Betta.txt"

if os.path.isfile( out_dir + outfile):
    rewrite = config.getboolean('Device','rewrite')

    if not rewrite:
        print "Rewrite file denied"
        exit()


SAVE_DEBUG = config.getboolean('Device','save_debug')

fmeasure = open(out_dir + outfile, "w")
fdbg     = open(out_dir + "debug_" +outfile, "w")

# Section: Measure
MEASURE_DELAY      = config.getfloat('Measure','delay')          # Задержка перед каждым измерением (сек)
MEASURE_COUNT      = config.getint('Measure','count')
MEASURE_MAX_FAILED = config.getint('Measure','max_failed')

# Section: Graphic
INCLUDE_GRAPHICS   = config.getboolean('Graphic','enable')
INTERPOLATED       = config.getboolean('Graphic','spline')

    
def write2file(file_handle,text,echo=False):
    if echo == True:
        print text
    
    file_handle.write(text+"\n")


    
def re_measure(cycle=1):
    Temp = Uc = Uc_m = Ic = Ue = Ue_m = Ib = 0.

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
        

    for i in xrange(cycle):
        time.sleep( MEASURE_DELAY )
        Ic      += ag.measure(2,"cur")
        Ib      += ag.measure(1,"cur")      
        Uc      += ag.source_value(2,"volt")
        Uc_m    += ag.measure(2,"volt")
        Ue      += ag.source_value(1,"volt")
        Ue_m    += ag.measure(1,"volt")
        Temp    += ag.temperature()

        

    cycle = float(cycle)
    Measurements["Temp"] = Temp / cycle
    Measurements["Uc"]   = Uc   / cycle
    Measurements["Uc_m"] = Uc_m / cycle
    Measurements["Ic"]   = Ic   / cycle
    Measurements["Ue"]   = Ue   / cycle
    Measurements["Ue_m"] = Ue_m / cycle
    Measurements["Ib"]   = Ib   / cycle
    
    
error_sat = 0    
def execute():

    global IV_I,IV_V,Measurements,stop_measure,error_sat,GRAPH_2_X,GRAPH_2_Y,PrevMeasurements

    # Задержка между измерениями  
    # time.sleep( DELAY_MEASURE )

    if error_sat >= 1:
        return False

    re_measure()
    

    no_inc = False

    try:
        Ue_check = round(Measurements["Ue_m"],2)
        # Выставляем оптимальный диапазон
        #print "@CH1 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ib"] ) )
        if not(abs(Ue_check) < 0.04+abs(Measurements["Ue"]) and abs(Ue_check) > abs(Measurements["Ue"])-0.04):
            next_range = ag.next_range(ag.get_range(1,"c"),"c")
            ag.set_range( 1,"c",next_range)
            time.sleep(MEASURE_DELAY*2)
            re_measure()
            
            #Ue_check = round(Measurements["Ue_m"],2)  
            

        Uc_check = round(Measurements["Uc_m"],2)
        # Выставляем оптимальный диапазон
        #print "@CH1 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ib"] ) )
        if not(abs(Uc_check) < 0.04+abs(Measurements["Uc"]) and abs(Uc_check) > abs(Measurements["Uc"])-0.04):
            next_range = ag.next_range(ag.get_range(2,"c"),"c")
            ag.set_range( 2,"c",next_range)
            time.sleep(MEASURE_DELAY*2)
            re_measure()
            
            #Uc_check = round(Measurements["Uc_m"],2)  
                 


        prev_range = ""
        while ag.get_good_range( "c", Measurements["Ib"] ) != ag.get_range(1,"c"):
            if prev_range == "":
                ag.set_range( 1,"c",ag.get_good_range( "c",Measurements["Ib"] ) )
                prev_range = ag.get_good_range( "c",Measurements["Ib"] )
            else:
                rng_good = ag.get_good_range( "c",Measurements["Ib"] )
                if ag.get_range_num(rng_good,"c") < ag.get_range_num(prev_range,"c"):
                    break
                else:
                    ag.set_range( 1,"c",rng_good )
                    prev_range = rng_good
            print "@CH1 New range: %s , Ib = %.2e" % (ag.get_good_range( "c", Measurements["Ib"] ), Measurements["Ib"] )
            re_measure()

        prev_range = ""
        while ag.get_good_range( "c", Measurements["Ic"] ) != ag.get_range(2,"c"):
            if prev_range == "":
                ag.set_range( 2,"c",ag.get_good_range( "c",Measurements["Ic"] ) )
                prev_range = ag.get_good_range( "c",Measurements["Ic"] )
            else:
                rng_good = ag.get_good_range( "c",Measurements["Ic"] )
                if ag.get_range_num(rng_good,"c") < ag.get_range_num(prev_range,"c"):
                    break
                else:
                    ag.set_range( 2,"c",rng_good )
                    prev_range = rng_good
            print "@CH2 New range: %s , Ib = %.2e" % (ag.get_good_range( "c", Measurements["Ib"] ), Measurements["Ib"] )
            re_measure()

        #while ag.get_good_range( "c", Measurements["Ib"] ) != ag.get_range(1,"c"):
        #    ag.set_range( 1,"c",ag.get_good_range( "c",Measurements["Ib"] ) )
        #    print "@CH1 New range: %s , Ib = %.2e" % (ag.get_good_range( "c", Measurements["Ib"] ), Measurements["Ib"] )
        #    re_measure()
        
        #print "@CH2 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ic"] ) )
        
        #while ag.get_good_range( "c", Measurements["Ic"] ) != ag.get_range(2,"c"):
        #    ag.set_range( 2,"c",ag.get_good_range( "c",Measurements["Ic"] ) )
            #print "@CH2 New range: %s , Ib = %.2e" % (ag.get_good_range( "c", Measurements["Ic"] ), Measurements["Ic"] )
        #    re_measure()
        
        #if not(abs(Uc_check) < 0.02+abs(Measurements["Uc"]) and abs(Uc_check) > abs(Measurements["Uc"])-0.02):
        #    next_range = ag.next_range(ag.get_range(2,"c"),"c")
        #    ag.set_range( 2,"c",next_range)
        #    re_measure()    

        #Uc_check = round(Measurements["Uc_m"],2)
        #assert(abs(Uc_check) < 0.02+abs(Measurements["Uc"]) and abs(Uc_check) > abs(Measurements["Uc"])-0.02)
        
        
        if round(Measurements["Ic"],3) == 0.120:
            if error_sat >= 1:
                return False
            else:
                error_sat += 1
        


        re_measure(MEASURE_COUNT)

        

        Ue       = Measurements["Ue"]
        Ue_meas  = Measurements["Ue_m"]
        Ib         = Measurements["Ib"]
        Uc         = Measurements["Uc"]
        Uc_meas     = Measurements["Uc_m"]
        Ic         = Measurements["Ic"]
        Temp     = Measurements["Temp"]


        

        Uc_check = round(Uc_meas,2)
        if not(abs(Uc_check) < 0.04+abs(Uc) and abs(Uc_check) > abs(Uc)-0.04):
            no_inc = True  

        Ue_check = round(Ue_meas,2)
        if not(abs(Ue_check) < 0.04+abs(Ue) and abs(Ue_check) > abs(Ue)-0.04):
            no_inc = True
        # if Ib < 0 or Ic < 0:

            
        #if Measurements["Ib"] < 0.00:
        #    raise ValueError
        
        
        #if Measurements["Ib"] < LastMeasurements["Ib"]:

        if Ib != 0.0:
            B = Ic / Ib
        else:
            B = float("-inf")
        
        #if B > 0:    

        write2file(fdbg,"%.2f\t%.2f\t%.2e\t%.2f\t%.2f\t%.2e\t%.2f\t%.2f" % (Ue,Ue_meas,Ib,Uc,Uc_meas,Ic,B,Temp),True)
        write2file(fmeasure,"%.2f\t%.2e\t%.2f\t%.2e" % (Ue,Ib,Uc,Ic))     
        
        
        
    except AssertionError:
        pass
        #stop_measure = True
        #print "Stop measure"
        #print "Uc:%.2f" % ( round(Measurements["Uc_m"],2) )
        #print "Current range CH2: %s" % ( ag.get_range(2,"c") )
        #return False
    except ValueError:
        ag.stop_output(1)
        time.sleep( MEASURE_DELAY )
        ag.start_output(1)
        print "Value Error"
        return False
    else:
        if Ib != 0.0:
            B = Ic/Ib
        else:
            B = float("-inf")

        if B >= 1.0 and no_inc == False:
            
            if PrevMeasurements["Ib"] > Ib:
                #no_inc = True
                print "FUUU upper"
            else:
                IV_I += [B]
                IV_V += [Ue]
                GRAPH_2_X += [Ic]
                GRAPH_2_Y += [B]

                PrevMeasurements = deepcopy(Measurements)

        elif no_inc == True:
            ag.stop_output("all")
            time.sleep(2)
            ag.start_output("all")

        # LastMeasurements = Measurements
        
        return True
    
    finally:
        pass
        #ag.debug()

    return True

if INCLUDE_GRAPHICS: 
    plt.figure(1,figsize=(18, 9), dpi=80, facecolor='w', edgecolor='k')





print "Current temperature: %.2f" % ( ag.temperature() )

write2file( fmeasure,"@COLS:Ue,Ib,Uc,Ic" ) # Записываем как будут располагаться колонки





style = 0


for Uc in Uc_RANGES:
	  
    style+=1;
    label_uc = "Uc=%.2f" % (Uc)
    IV_I = []
    IV_V = []
    GRAPH_2_Y = []
    GRAPH_2_X = []
    # Инициализация
    if abs(Uc) > 2 and abs(Uc) <=20:
        ag.initialize(2,"v","R20V",Uc)
    elif abs(Uc) <= 2:
        ag.initialize(2,"v","R2V",Uc)
    
    Ue_max = max(Ue_RANGES)
    if abs(Ue_max) > 2 and abs(Ue_max) <=20:
        ag.initialize(1,"v","R20V",Uc)
    elif abs(Ue_max) <= 2:
        ag.initialize(1,"v","R2V",Uc)
        
    ag.initialize(1,"c","R1uA")
    ag.initialize(2,"c","R1uA")
   
    
    
    # Задаём источник постоянного напряжения
    ag.source(2,"v",Uc)  
    
    
      
    
    write2file(fdbg,"@Uc=%.2f" % (Uc),True)
    write2file(fdbg,"Forward I-V",True)
    write2file(fdbg,"Ue\tUe_meas\tIb\t\tUc\tUc_meas\tIc\t\tBetta\tTemp",True)
    
    
    ag.start_output(2)
    
    for Ue in Ue_RANGES:
        stop_measure = False
        ag.source(1,"volt",Ue)
        ag.start_output(1)  
        failed = 0
        if not execute():
            #print "Stop_measure: "+str(stop_measure)
            if stop_measure:
                break;
        #while not execute() and failed < MAX_FAILED:
        #    failed+=1                    #Функция измерения
        ag.stop_output(1)
        time.sleep( 1 )
            
            
    if INCLUDE_GRAPHICS:    
        plt.subplot(211)
        if INTERPOLATED:
            spline_IV_V = IV_V
            spline_IV_I = spline(IV_V,IV_I,spline_IV_V)
            plt.plot(spline_IV_V,spline_IV_I,get_style_plot(style,True),label=label_uc)
        else:
            plt.plot(IV_V,IV_I,get_style_plot(style,True),label=label_uc)    
        plt.subplot(212)
        if INTERPOLATED:
            spline_GRAPH_2_X = GRAPH_2_X
            spline_GRAPH_2_Y = spline(GRAPH_2_X,GRAPH_2_Y,spline_GRAPH_2_X)
            plt.plot(spline_GRAPH_2_X,spline_GRAPH_2_Y,get_style_plot(style,True),label=label_uc)
        else:
            plt.plot(GRAPH_2_X,GRAPH_2_Y,get_style_plot(style,True),label=label_uc)    
    
    ag.stop_output("all")
    time.sleep( 3*MEASURE_DELAY )

    
    
fmeasure.close()
fdbg.close()


if INCLUDE_GRAPHICS:
    plt.subplot(211)
    plt.title("Measure Betta versus Ube")
    plt.xlabel("Ube, V")
    plt.ylabel("Betta")
    plt.grid(True)
    plt.legend(loc="upper left")
    plt.subplot(212)
    plt.title("Measure Betta versus Ic")
    plt.xlabel("Ic [LOG], A")
    plt.xscale('log')
    plt.ylabel("Betta")
    plt.grid(True)
    plt.legend(loc="upper left")
    plt.savefig(out_dir + "plot_betta.png")


    plt.show()