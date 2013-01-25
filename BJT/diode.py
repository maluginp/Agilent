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


Ud_RANGES = []

stop_measure = False

# Для графиков
IV_I = []
IV_V = []


#Measurement value
Measurements = dict(
    Ud   = 0.0,
    Ud_m = 0.0,
    Id   = 0.0,
    Temp = 0.0
    )
    
# BANNER
print """
Welcome to measure diode I-V

Channel (CH1) : Ud & Id

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



# Set Uc_RANGES
_Ud = config.get('Agilent','Ud')
try:

    if len(_Ud.split(',')) != 1:
        # 1,2,3,4
        __Ud = _Ud.split(',')
        for ___Ud in __Ud:
            Ud_RANGES += [ float(___Ud) ]

    elif len(_Ud.split(';')) != 1:
        # 1;2;0.1
        __Ud = _Ud.split(';')
        __Ud_start = float(__Ud[0])
        __Ud_end   = float(__Ud[1])
        __Ud_step  = float(__Ud[2])

        Ud_RANGES = ag.drange(__Ud_start,__Ud_end,__Ud_step)

    else:
        # const
        Ud_RANGES = [ float(_Ud) ]

except ValueError:
    print "ValueError"
    sys.exit(1)

except:
    print "Fatal error in Ud"
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
    outfile = "Diode.txt"

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
GRAPHIC_IMAGE_FILE = config.get('Graphic','imagename')

if len(GRAPHIC_IMAGE_FILE) == 0:
    GRAPHIC_IMAGE_FILE = "plot_diode.png"

def write2file(file_handle,text,echo=False):
    if echo == True:
        print text
    
    file_handle.write(text+"\n")


    
def re_measure(cycle=1):
    Temp = Ud = Ud_m = Id = 0.

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
        Ud      += ag.source_value(1,"volt")
        Ud_m    += ag.measure(1,"volt")
        Id      += ag.measure(1,"cur")


        

    cycle = float(cycle)
    Measurements["Temp"] = Temp / cycle
    Measurements["Ud"]   = Ud   / cycle
    Measurements["Ud_m"] = Ud_m / cycle
    Measurements["Id"]   = Id   / cycle
    
    
def execute():

    global IV_I,IV_V,Measurements,stop_measure

    # Задержка между измерениями  
    # time.sleep( MEASURE_DELAY )

    re_measure()
    

    try:
        Ud_check = round(Measurements["Ud_m"],2)
        # Выставляем оптимальный диапазон
        #print "@CH1 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ib"] ) )
        
        if not(abs(Ud_check) < 0.02+abs(Measurements["Ud"]) and abs(Ud_check) > abs(Measurements["Ud"])-0.02):
            next_range = ag.next_range(ag.get_range(1,"c"),"c")
            ag.set_range( 1,"c",next_range)
            re_measure()
        
        #while ag.get_good_range( "c", Measurements["Ib"] ) != ag.get_range(1,"c"):
        #    ag.set_range( 1,"c",ag.get_good_range( "c",Measurements["Ib"] ) )
            #print "@CH1 New range: %s , Ib = %.2e" % (ag.get_good_range( "c", Measurements["Ib"] ), Measurements["Ib"] )
        #    re_measure()
        
        #print "@CH2 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ic"] ) )
        prev_range = ""
        while ag.get_good_range( "c", Measurements["Id"] ) != ag.get_range(1,"c"):
            if prev_range == "":
                ag.set_range( 1,"c",ag.get_good_range( "c",Measurements["Id"] ) )
                prev_range = ag.get_good_range( "c",Measurements["Id"] )
            else:
                rng_good = ag.get_good_range( "c",Measurements["Id"] )
                if ag.get_range_num(rng_good,"c") < ag.get_range_num(prev_range,"c"):
                    break;
                else:
                    ag.set_range( 1, "c", rng_good )
                    prev_range = rng_good
            print "@CH1 New range: %s , Id = %.2e" % (ag.get_good_range( "c", Measurements["Id"] ), Measurements["Id"] )
            re_measure()
        

            
        # Проводим измерения
        re_measure(MEASURE_COUNT)
            
            
        #if Measurements["Ib"] < 0.00:
        #    raise ValueError
        
        
        #if Measurements["Ib"] < LastMeasurements["Ib"]:
        #    raise ValueError 

        Ud         = Measurements["Ud"]
        Ud_meas     = Measurements["Ud_m"]
        Id         = Measurements["Id"]
        Temp     = Measurements["Temp"]
        
        Ud_check = round(Measurements["Ud_m"],2)
        assert(abs(Ud_check) < 0.02+abs(Measurements["Ud"]) and abs(Ud_check) > abs(Measurements["Ud"])-0.02)
        assert(round(Id,3) != 0.120)

        if Ud > 0.0 and Id < 0.0:
            raise ValueError
            
        if Ud < 0.0 and Id > 0.0:
            raise ValueError
            
        write2file(fdbg,"%.2f\t%.2f\t%.2e\t%.2f" % (Ud,Ud_meas,Id,Temp),True)
        write2file(fmeasure,"%.2f\t%.2e\t" % (Ud,Id))     

        
        
    except AssertionError:
        stop_measure = True
        print "Stop measure"
        print "Ud:%.2f" % ( round(Measurements["Ud_m"],2) )
        return False
    except ValueError:
        ag.stop_output(1)
        time.sleep( MEASURE_DELAY )
        ag.start_output(1)
        print "Value Error"
        return False
    else:
        IV_I += [Id]
        IV_V += [Ud]
        #LastMeasurements = Measurements
        
        return True
    
    finally:
        pass
        #ag.debug()

    return True

if INCLUDE_GRAPHICS: 
    plt.figure(1,figsize=(18, 9), dpi=80, facecolor='w', edgecolor='k')





print "Current temperature: %.2f" % ag.temperature()

write2file( fmeasure,"@COLS:Ud,Id" ) # Записываем как будут располагаться колонки
write2file(fdbg,"Ud\tUd_meas\tId\t\tTemp",True)




style = 1

# Initial ranges
ag.initialize(1,"v","R2V") 
ag.initialize(1,"c","R1uA")

for Ud in Ud_RANGES:
    rang = ag.get_good_range( "v", Ud )
    if rang != ag.get_range(1,"v"):
        ag.initialize(1,"v",rang)

    ag.source(1,"v",Ud)

    ag.start_output(1) # Запускаем источник

    if not execute():
        #print "Stop_measure: "+str(stop_measure)
        if stop_measure:
            break
    
    ag.stop_output(1)
    time.sleep(0.5) 
 
if INCLUDE_GRAPHICS:
    plt.plot(IV_V,IV_I,get_style_plot(style,False),label=devname) 
    
fmeasure.close()
fdbg.close()

ag.stop_output("all")
#config.close()


if INCLUDE_GRAPHICS:
    plt.title("Id(Ud)")
    plt.xlabel("Ud, V")
    plt.ylabel("Id, A")
    plt.grid(True)
    #plt.legend(loc="lower right")

    plt.savefig(out_dir + GRAPHIC_IMAGE_FILE)
    plt.show()