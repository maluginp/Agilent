#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import time
import math
import os
import agilent as ag

from graphics import *

# CHANNEL 1 - Ube, Ib
# CHANNEL 2 - Uce, Ic

INCLUDE_GRAPHICS = True
SAVE_DEBUG         = True
MAX_FAILED         = 5
# Настройки
DELAY_MEASURE   = 1           # Задержка перед каждым измерением (сек)
Ue_START        = 0.0
Ue_END          = -10.0
Ue_STEP         = 0.1
Ue_RANGES       = ag.drange(Ue_START,Ue_END,Ue_STEP)

print Ue_RANGES
Uc_RANGES       = [1,2,4,6,8]


force_rewrite = False

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
    Ue_m = 0.0,
    Ib   = 0.0,
    Temp = 0.0
    )
    
LastMeasurements = dict()

try:
    out_file = sys.argv[1];
    if(len(sys.argv) == 3):
        if sys.argv[2].lower() in ["y","yes"]:
            force_rewrite = True
except:
    print "Usage: ",sys.argv[0]," outfile (without extension) force(default \"no\")"
    sys.exit(1)



ag.stop_output("all")

out_file=out_file+"_in_rvrs"

if os.path.isfile(out_file+".txt") and force_rewrite == False:
    print out_file+".txt exists!"
    prompt = raw_input("Rewrite file? (y-yes,n-no)> ")
    
    if not ( prompt.lower() in  ["y","yes"]):
        exit()




    
fmeasure = open(out_file+".txt", "w")
fdbg     = open(out_file+"_dbg.txt", "w")


    
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
            print "Current Temperature: %.2f, Delay: %d sec" % ( ag.temperature(),60 * DELAY_MEASURE )
            print "Delay"
            for sec in xrange( 12 * DELAY_MEASURE ):
                print "%d, " % (sec*5),
                time.sleep(5)

        ag.start_output("all")
            
        

    for i in xrange(cycle):
        time.sleep( DELAY_MEASURE )
        
        Temp    += ag.temperature()
        Uc      += ag.source_value(2,"volt")
        Uc_m    += ag.measure(2,"volt")
        Ic      += ag.measure(2,"cur")
        Ue      += ag.source_value(1,"volt")
        Ue_m    += ag.measure(1,"volt")
        Ib      += ag.measure(1,"cur")

        

    cycle = float(cycle)
    Measurements["Temp"] = Temp / cycle
    Measurements["Uc"]   = Uc   / cycle
    Measurements["Uc_m"] = Uc_m / cycle
    Measurements["Ic"]   = Ic   / cycle
    Measurements["Ue"]   = Ue   / cycle
    Measurements["Ue_m"] = Ue_m / cycle
    Measurements["Ib"]   = Ib   / cycle
    
    
    
def execute():

    global IV_I,IV_V,Measurements,stop_measure

    # Задержка между измерениями  
    # time.sleep( DELAY_MEASURE )

    re_measure()
    

    try:
        Uc_check = round(Measurements["Uc_m"],2)
        # Выставляем оптимальный диапазон
        #print "@CH1 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ib"] ) )
        
        if not(abs(Uc_check) < 0.02+abs(Measurements["Uc"]) and abs(Uc_check) > abs(Measurements["Uc"])-0.02):
            next_range = ag.next_range(ag.get_range(2,"c"),"c")
            ag.set_range( 2,"c",next_range)
            re_measure()
        
        while ag.get_good_range( "c", Measurements["Ib"] ) != ag.get_range(1,"c"):
            ag.set_range( 1,"c",ag.get_good_range( "c",Measurements["Ib"] ) )
            #print "@CH1 New range: %s , Ib = %.2e" % (ag.get_good_range( "c", Measurements["Ib"] ), Measurements["Ib"] )
            re_measure()
        
        #print "@CH2 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ic"] ) )
        
        while ag.get_good_range( "c", Measurements["Ic"] ) != ag.get_range(2,"c"):
            ag.set_range( 2,"c",ag.get_good_range( "c",Measurements["Ic"] ) )
            #print "@CH2 New range: %s , Ib = %.2e" % (ag.get_good_range( "c", Measurements["Ic"] ), Measurements["Ic"] )
            re_measure()
            
        Uc_check = round(Measurements["Uc_m"],2)
        assert(abs(Uc_check) < 0.02+abs(Measurements["Uc"]) and abs(Uc_check) > abs(Measurements["Uc"])-0.02)
        
        
            
        # Проводим измерения
        re_measure(5)
            
            
        #if Measurements["Ib"] < 0.00:
        #    raise ValueError
        
        
        #if Measurements["Ib"] < LastMeasurements["Ib"]:
        #    raise ValueError 

        

        
        Ue       = Measurements["Ue"]
        Ue_meas  = Measurements["Ue_m"]
        Ib         = Measurements["Ib"]
        Uc         = Measurements["Uc"]
        Uc_meas     = Measurements["Uc_m"]
        Ic         = Measurements["Ic"]
        Temp     = Measurements["Temp"]
        
            
        write2file(fdbg,"%.2f\t%.2f\t%.2e\t%.2f\t%.2f\t%.2e\t%.2f" % (Ue,Ue_meas,Ib,Uc,Uc_meas,Ic,Temp),True)
        write2file(fmeasure,"%.2f\t%.2e\t%.2f\t%.2e" % (Ue,Ib,Uc,Ic))     

        
    except AssertionError:
        stop_measure = True
        print "Stop measure"
        print "Uc:%.2f" % ( round(Measurements["Uc_m"],2) )
        return False
    except ValueError:
        ag.stop_output(1)
        time.sleep( DELAY_MEASURE )
        ag.start_output(1)
        print "Value Error"
        return False
    else:
        IV_I += [Ib]
        IV_V += [Ue]
        LastMeasurements = Measurements
        
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


for Uc in Uc_RANGES:
	  
    style+=1;
    label_uc = "Uc=%.2f" % (Uc)
    IV_I = []
    IV_V = []
    
    # Инициализация
    if abs(Uc) > 2 and abs(Uc) <=20:
        ag.initialize(2,"v","R20V",Uc)
    elif abs(Uc) <= 2:
        ag.initialize(2,"v","R2V",Uc)
    
    Ue_min = min(Ue_RANGES)
    if abs(Ue_min) > 2 and abs(Ue_min) <= 20:
        ag.initialize(1,"v","R20V",Uc)
    elif abs(Ue_min) <= 2:
        ag.initialize(1,"v","R2V",Uc)
        
    ag.initialize(1,"c","R1uA")
    ag.initialize(2,"c","R1uA")
   
    
    
    # Задаём источник постоянного напряжения
    ag.source(2,"v",Uc)  
    
    
      
    
    write2file(fdbg,"@Uc=%.2f" % (Uc),True)
    write2file(fdbg,"Forward I-V",True)
    write2file(fdbg,"Ue\tUe_meas\tIb\t\tUc\tUc_meas\tIc\t\tTemp",True)
    
    
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
        plt.plot(IV_V,IV_I,get_style_plot(style),label=label_uc)    
    
    
    ag.stop_output("all")
    time.sleep( 5*DELAY_MEASURE )

    
    
fmeasure.close()
fdbg.close()


if INCLUDE_GRAPHICS:
    plt.title("Reverse mode")
    plt.xlabel("Ue, V")
    plt.ylabel("Ib, A")
    plt.grid(True)
    plt.legend(loc="lower right")
    plt.savefig(out_file+"_plot.png")
   # plt.show()