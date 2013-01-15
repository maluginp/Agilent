#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import time
import math
import os

sys.path.append("../")

import agilent as ag

from graphics import *


# CHANNEL 1 - Ube, Ib
# CHANNEL 2 - Uce, Ic

INCLUDE_GRAPHICS = True
SAVE_DEBUG         = True
MAX_FAILED         = 5
# Настройки
DELAY_MEASURE   = 0.5          # Задержка перед каждым измерением (сек)
#I_START        = 0.00
#Ue_END          = 1.20
#Ue_STEP         = 0.1
#Ib_RANGES       = ag.drange(Ue_START,Ue_END,Ue_STEP)
Ib_RANGES       = [0.1e-6,0.2e-6,0.4e-6,0.6e-6,0.8e-6,1e-6,10e-6]

Uc_RANGES       = [5,10]


force_rewrite = False

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

out_file="Betta_Ib_"+out_file

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
    Temp = Uc = Uc_m = Ic = Ue = Ue_m = Ib = Ib_m = 0.

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
        Ib      += ag.source_value(1,"cur")
        Ib_m    += ag.measure(1,"cur")

        

    cycle = float(cycle)
    Measurements["Temp"] = Temp / cycle
    Measurements["Uc"]   = Uc   / cycle
    Measurements["Uc_m"] = Uc_m / cycle
    Measurements["Ic"]   = Ic   / cycle
    Measurements["Ue"]   = Ue   / cycle
    Measurements["Ue_m"] = Ue_m / cycle
    Measurements["Ib"]   = Ib   / cycle
    Measurements["Ib_m"] = Ib_m   / cycle
    
    
error_sat = 0    
def execute():

    global IV_I,IV_V,Measurements,stop_measure,error_sat,GRAPH_2_X,GRAPH_2_Y

    # Задержка между измерениями  
    # time.sleep( DELAY_MEASURE )

    if error_sat >= 1:
        return False

    re_measure()
    

    try:
        good_rng = ag.get_good_range("v",Measurements["Ue_m"])
        if ag.get_range(1,"v") != good_rng:
            ag.set_range( 1,"v",good_rng)
            print "@CH1 New range: %s , Ue = %.2f" % (good_rng, Measurements["Ue_m"] ) 

        #Ue_check = round(Measurements["Ue_m"],2)
        # Выставляем оптимальный диапазон
        #print "@CH1 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ib"] ) )
        #if not(abs(Ue_check) < 0.02+abs(Measurements["Ue"]) and abs(Ue_check) > abs(Measurements["Ue"])-0.02):
        #    next_range = ag.next_range(ag.get_range(1,"c"),"c")
        #    ag.set_range( 1,"c",next_range)
        #    time.sleep(DELAY_MEASURE*2)
        #    re_measure()
        #    
        #    Ue_check = round(Measurements["Ue_m"],2)  
        #    if not(abs(Ue_check) < 0.02+abs(Measurements["Ue"]) and abs(Ue_check) > abs(Measurements["Ue"])-0.02):
        #      print "FUCK"
        #      #print Ue_check
        #      return True
        #      #  

        Uc_check = round(Measurements["Uc_m"],2)
        # Выставляем оптимальный диапазон
        #print "@CH1 Good range: %s" % ( ag.get_good_range( "c", Measurements["Ib"] ) )
        if not(abs(Uc_check) < 0.02+abs(Measurements["Uc"]) and abs(Uc_check) > abs(Measurements["Uc"])-0.02):
            next_range = ag.next_range(ag.get_range(2,"c"),"c")
            ag.set_range( 2,"c",next_range)
            time.sleep(DELAY_MEASURE*2)
            re_measure()
            
            Uc_check = round(Measurements["Uc_m"],2)  
            if not(abs(Uc_check) < 0.02+abs(Measurements["Uc"]) and abs(Uc_check) > abs(Measurements["Uc"])-0.02):
              print "FUCK"
              #print Uc_check
              return True
              #print "FUCK"        


        #prev_range = ""
        #while ag.get_good_range( "c", Measurements["Ib"] ) != ag.get_range(1,"c"):
        #    if prev_range == "":
        #        ag.set_range( 1,"c",ag.get_good_range( "c",Measurements["Ib"] ) )
        #        prev_range = ag.get_good_range( "c",Measurements["Ib"] )
        #    else:
        #        rng_good = ag.get_good_range( "c",Measurements["Ib"] )
        #        if ag.get_range_num(rng_good,"c") < ag.get_range_num(prev_range,"c"):
        #            break
        #        else:
        #            ag.set_range( 1,"c",rng_good )
        #            prev_range = rng_good
        #    print "@CH1 New range: %s , Ib = %.2e" % (ag.get_good_range( "c", Measurements["Ib"] ), Measurements["Ib"] )
        #    re_measure()

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
            
        # Проводим измерения
        re_measure(3)
            
            
        #if Measurements["Ib"] < 0.00:
        #    raise ValueError
        
        
        #if Measurements["Ib"] < LastMeasurements["Ib"]:
        #    raise ValueError 

        

        
        Ue       = Measurements["Ue_m"]
        Ue_meas  = Measurements["Ue_m"]
        Ib         = Measurements["Ib"]
        Ib_meas  = Measurements["Ib_m"]
        Uc         = Measurements["Uc"]
        Uc_meas     = Measurements["Uc_m"]
        Ic         = Measurements["Ic"]
        Temp     = Measurements["Temp"]
        
        if Ib != 0.0:
            B = Ic / Ib
        else:
            B = float("-inf")
        
        #if B > 0:    
        write2file(fdbg,"%.2f\t%.2e\t%.2e\t%.2f\t%.2f\t%.2e\t%.2f\t%.2f" % (Ue,Ib,Ib_meas,Uc,Uc_meas,Ic,B,Temp),True)
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
        time.sleep( DELAY_MEASURE )
        ag.start_output(1)
        print "Value Error"
        return False
    else:
        if Ib != 0.0:
            B = Ic/Ib
        else:
            B = float("-inf")

        if B > 0:
            GRAPH_2_X += [Ib]
            GRAPH_2_Y += [B]

        LastMeasurements = Measurements
        
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
    GRAPH_2_Y = []
    GRAPH_2_X = []
    
    # Инициализация
    if abs(Uc) > 2 and abs(Uc) <=20:
        ag.initialize(2,"v","R20V",Uc)
    elif abs(Uc) <= 2:
        ag.initialize(2,"v","R2V",Uc)
    
    ag.initialize(1,"v","R20V",Uc)       
    ag.initialize(2,"c","R1uA")
    
    # Задаём источник постоянного напряжения
    ag.source(2,"v",Uc)  
    
    
      
    
    write2file(fdbg,"@Uc=%.2f" % (Uc),True)
    write2file(fdbg,"Forward I-V",True)
    write2file(fdbg,"Ue\tIb\t\tIb_m\t\tUc\tUc_meas\tIc\t\tBetta\tTemp",True)
    
    
    ag.start_output(2)
    
    for Ib in Ib_RANGES:
        stop_measure = False

        good_rng = ag.get_good_range("c",Ib)
        ag.initialize(1,"c",good_rng)
        ag.source(1,"c",Ib)
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
        plt.plot(GRAPH_2_X,GRAPH_2_Y,get_style_plot(style),label=label_uc)    
    
    ag.stop_output("all")
    time.sleep( 5*DELAY_MEASURE )

    
    
fmeasure.close()
fdbg.close()


if INCLUDE_GRAPHICS:
    plt.title("Measure Betta versus Ib")
    plt.xlabel("Ib[LOG]")
    plt.xscale('log')
    plt.ylabel("Betta")
    plt.grid(True)
    plt.legend(loc="upper left")
    plt.savefig(out_file+"_graphic.png")


    plt.show()