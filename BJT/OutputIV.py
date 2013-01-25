#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import time
import math
import os
from scipy.interpolate import spline
import ConfigParser

config = ConfigParser.ConfigParser()

sys.path.append("../lib/")

import agilent as ag
from graphics import *


Uc_RANGES = []
Ib_RANGES = []


stop_measure = False

# Для графиков
IV_I = []
IV_V = []


#Measurement value
Measurements = dict(
    Uc   = 0.0,
    Uc_m = 0.0,
    Ic   = 0.0,
    Ue   = 0.0,
    Ib   = 0.0,
    Ib_m = 0.0,
    Temp = 0.0
    )
    
# BANNER
print """
Welcome to Output IV measuments

Channel (CH1) : Ube   (Voltage Base-Emitter)
Channe2 (CH2) : Uce   (Voltage Collector-Emitter)

Author: Malyugin Platon (Last change: 16-jan-2013)

Everything takes longer than you think / Murphy's law

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

_Ib = config.get('Agilent','Ib')
try:

    if len(_Ib.split(',')) != 1:
        # 1,2,3,4
        __Ib = _Ib.split(',')
        for ___Ib in __Ib:
            Ib_RANGES += [ float(___Ib) ]

    elif len(_Ib.split(';')) != 1:
        # 1;2;0.1
        __Ib = _Ib.split(';')
        __Ib_start = float(__Ib[0])
        __Ib_end   = float(__Ib[1])
        __Ib_step  = float(__Ib[2])

        Ib_RANGES = ag.drange(__Ib_start,__Ib_end,__Ib_step)

    else:
        # const
        Ib_RANGES = [ float(_Ib) ]

except ValueError:
    print "ValueError"
    sys.exit(1)

except:
    print "Fatal error IN Ib"
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
    print "Fatal error in Uc"
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
    Temp = Uc = Uc_m = Ic = Ue = Ib = Ib_m = 0.

    if ag.temperature() >= 50.0:
        print "Hi, temperature! Cool!"
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
        
        Temp    += ag.temperature()
        Uc      += ag.source_value(2,"volt")
        Uc_m    += ag.measure(2,"volt")
        Ic      += ag.measure(2,"cur")
        Ue      += ag.measure(1,"volt")
        Ib		+= ag.source_value(1,"c")
        Ib_m    += ag.measure(1,"cur")

        

    cycle = float(cycle)
    Measurements["Temp"] = Temp / cycle
    Measurements["Uc"]   = Uc   / cycle
    Measurements["Uc_m"] = Uc_m / cycle
    Measurements["Ic"]   = Ic   / cycle
    Measurements["Ue"]   = Ue   / cycle
    Measurements["Ib_m"] = Ib_m / cycle
    Measurements["Ib"]   = Ib   / cycle
    
    
    
def execute():

    global IV_I,IV_V,Measurements,stop_measure

    # Задержка между измерениями  
    # time.sleep( MEASURE_DELAY )

    re_measure()
    

    try:
        Uc_check = round(Measurements["Uc_m"],2)
        # Выставляем оптимальный диапазон
        #print "@CH1 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ib"] ) )
        
        if not(abs(Uc_check) < 0.02+abs(Measurements["Uc"]) and abs(Uc_check) > abs(Measurements["Uc"])-0.02):
            next_range = ag.next_range(ag.get_range(2,"c"),"c")
            ag.set_range( 2,"c",next_range)
            re_measure()
        
        #while ag.get_good_range( "c", Measurements["Ib"] ) != ag.get_range(1,"c"):
        #    ag.set_range( 1,"c",ag.get_good_range( "c",Measurements["Ib"] ) )
            #print "@CH1 New range: %s , Ib = %.2e" % (ag.get_good_range( "c", Measurements["Ib"] ), Measurements["Ib"] )
        #    re_measure()
        
        #print "@CH2 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ic"] ) )
        prev_range = ""
        while ag.get_good_range( "c", Measurements["Ic"] ) != ag.get_range(2,"c"):
            if prev_range == "":
                ag.set_range( 2,"c",ag.get_good_range( "c",Measurements["Ic"] ) )
                prev_range = ag.get_good_range( "c",Measurements["Ic"] )
            else:
                rng_good = ag.get_good_range( "c",Measurements["Ic"] )
                if ag.get_range_num(rng_good,"c") < ag.get_range_num(prev_range,"c"):
                    break;
                else:
                    ag.set_range( 2,"c",rng_good )
                    prev_range = rng_good
            print "@CH2 New range: %s , Ic = %.2e" % (ag.get_good_range( "c", Measurements["Ic"] ), Measurements["Ic"] )
            re_measure()
            
        Uc_check = round(Measurements["Uc_m"],2)
        assert(abs(Uc_check) < 0.02+abs(Measurements["Uc"]) and abs(Uc_check) > abs(Measurements["Uc"])-0.02)

        
            
        # Проводим измерения
        re_measure(MEASURE_COUNT)
            
            
        #if Measurements["Ib"] < 0.00:
        #    raise ValueError
        
        
        #if Measurements["Ib"] < LastMeasurements["Ib"]:
        #    raise ValueError 

        

        
        Ue       = Measurements["Ue"]
        Ib_meas  = Measurements["Ib_m"]
        Ib         = Measurements["Ib"]
        Uc         = Measurements["Uc"]
        Uc_meas     = Measurements["Uc_m"]
        Ic         = Measurements["Ic"]
        Temp     = Measurements["Temp"]
        
            
        write2file(fdbg,"%.2f\t%.2e\t%.2e\t%.2f\t%.2f\t%.2e\t%.2f" % (Ue,Ib,Ib_meas,Uc,Uc_meas,Ic,Temp),True)
        write2file(fmeasure,"%.2f\t%.2e\t%.2f\t%.2e" % (Ue,Ib,Uc,Ic))     

        
        
    except AssertionError:
        stop_measure = True
        print "Stop measure"
        print "Uc:%.2f" % ( round(Measurements["Uc_m"],2) )
        return False
    except ValueError:
        ag.stop_output(1)
        time.sleep( MEASURE_DELAY )
        ag.start_output(1)
        print "Value Error"
        return False
    else:
        IV_I += [Ic]
        IV_V += [Uc]
        #LastMeasurements = Measurements
        
        return True
    
    finally:
        pass
        #ag.debug()

    return True

if INCLUDE_GRAPHICS: 
    plt.figure(1,figsize=(18, 9), dpi=80, facecolor='w', edgecolor='k')





print "Current temperature: %.2f" % ag.temperature()

write2file( fmeasure,"@COLS:Ue,Ib,Uc,Ic" ) # Записываем как будут располагаться колонки





style = 0


for Ib in Ib_RANGES:
	  
    style+=1;
    label_ib = "Ib=%.2e" % (Ib)
    IV_I = []
    IV_V = []
    
    # Инициализация
    Uc_max = max(Uc_RANGES)
    if abs(Uc_max) > 2 and abs(Uc_max) <=20:
        ag.initialize(2,"v","R20V",Uc_max)
    elif abs(Uc_max) <= 2:
        ag.initialize(2,"v","R2V",Uc_max)
    
    rang = ag.get_good_range( "c", Ib )
    print "@CH1 range: %s , Ib = %.2e" % (rang, Ib )
    ag.initialize(1,"c",rang) 


    ag.initialize(1,"v","R2V") 
    ag.initialize(2,"c","R1uA")
   
    
    
    # Задаём источник постоянного тока
    ag.source(1,"c",Ib)  
    
    
      
    
    write2file(fdbg,"@Ib=%.2e" % (Ib),True)
    write2file(fdbg,"Forward I-V",True)
    write2file(fdbg,"Ue\tIb\t\tIb_m\t\tUc\tUc_meas\tIc\t\tTemp",True)
    
    
    ag.start_output(1) # Запускаем источник
    
    for Uc in Uc_RANGES:
        stop_measure = False
        ag.source(2,"volt",Uc)
        ag.start_output(2)  
        failed = 0
        if not execute():
            #print "Stop_measure: "+str(stop_measure)
            if stop_measure:
                break
        #while not execute() and failed < MAX_FAILED:
        #    failed+=1                    #Функция измерения
        ag.stop_output(2)
        time.sleep( 1 )
            
            
    if INCLUDE_GRAPHICS:    
        plt.plot(IV_V,IV_I,get_style_plot(style,False),label=label_ib)    
    
    
    ag.stop_output("all")
    time.sleep( 5*MEASURE_DELAY )

    
    
fmeasure.close()
fdbg.close()


if INCLUDE_GRAPHICS:
    plt.title("Ic(Uce) | Ib=const")
    plt.xlabel("Uce, V")
    plt.ylabel("Ic, A")
    plt.grid(True)
    plt.legend(loc="lower right")
    plt.savefig(out_dir + "plot_output_iv.png")
    plt.show()