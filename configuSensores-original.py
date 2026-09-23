"""
Project ConfigSensorPark2

Created on Feb 11 2023

@author: EPS

Version: 2.05        02/09/2023
"""

import can
from datetime import datetime # Biblioteca do python de Data e Hora
from mySQLcom import querySQL
import time
import threading
from threading import Thread, Event
import queue
import os
if os.name == 'nt':
    import msvcrt
else:
    import sys, select

totalSensores = 0                        # MAX 2047
consultaSensorNumero = -1
intervalo = 9
programa_todos = threading.Event()
programa_um = threading.Event()
mede_um = threading.Event()
consulta_um = threading.Event()
consulta_temp = threading.Event()
define_intervalo = threading.Event()
termina_thread = threading.Event()
bloqueia_thread = threading.Event()
doing_intervalo = threading.Event()
Dados_da_Thread = queue.Queue()
listSensores = []
config_sensor = 0xAA
le_conf_sensor = 0xAB
le_temp_sensor = 0xA5
mede_sensor = 0x00
bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=50000)

# ----------------------------------------------------------------------------------------------------------

# Returns True if a keypress is waiting to be read in stdin, False otherwise.
# Make sure to read() the waiting character(s) -- the function will keep returning True until you do!

def kbhit():
    if os.name == 'nt':
        if msvcrt.kbhit():
            tecla = msvcrt.getch()
            return True
        else:
            tecla = " "
            return False
    else:
        dr,dw,de = select.select([sys.stdin], [], [], 0)
        if dr != []:
            tecla = sys.stdin.read(1)
            return True
        else:
            tecla = " "
            return False

# ----------------------------------------------------------------------------------------------------------

# define a thread which takes input
class InputThread(threading.Thread):

    def __init__(self):
        super(InputThread, self).__init__()
        self.daemon = True
        self.last_user_input = None
        programa_todos.clear()
        programa_um.clear()
        mede_um.clear()
        consulta_um.clear()
        consulta_temp.clear()
        define_intervalo.clear()
        termina_thread.clear()
        bloqueia_thread.clear()

    def run(self):
        while True:
            if not(bloqueia_thread.is_set()):
                print("\nDigite Q (Quit) para sair")
                print("Digite I para definir (I)ntervalo de tempo (em segundos)")
                print("Digite M para (M)edir um sensor cadastrado")
                print("Digite C para (C)onsultar um sensor cadastrado")
                print("Digite T para consultar a (T)emperatura de um sensor cadastrado")
                print("Digite A para programar todos (All) os sensores cadastrados")
                print("Ou digite o numero do sensor para programar somente um sensor")
                self.last_user_input = input('Qual sua escolha:\n')
                if (self.last_user_input == 'Q'):
                    bloqueia_thread.set()
                    doing_intervalo.clear()
                    define_intervalo.clear()
                    programa_todos.set()
                    programa_um.set()
                    consulta_um.set()
                    consulta_temp.set()
                    mede_um.set()
                    
                elif (self.last_user_input == 'I'):
                    print("O intervalo atual é : ", intervalo)
                    self.last_user_input = input('Digite quantos segundos (min. 2, max. 60) : ')
                    if (self.last_user_input.isdigit() == True):
                        if ((int(self.last_user_input) > 1) and (int(self.last_user_input) < 61)):
                            bloqueia_thread.set()
                            Dados_da_Thread.put(int(self.last_user_input))
                            programa_todos.clear()
                            programa_um.clear()
                            mede_um.clear()
                            consulta_um.clear()
                            consulta_temp.clear()
                            doing_intervalo.clear()
                            define_intervalo.set()
                            
                elif (self.last_user_input == 'M'):
                    self.last_user_input = input('Digite o numero do sensor para consultar:\n')
                    if (self.last_user_input.isdigit() == True):
                        if ((int(self.last_user_input) > 0) and (int(self.last_user_input) < 2048)):
                            bloqueia_thread.set()
                            Dados_da_Thread.put(int(self.last_user_input))
                            programa_todos.clear()
                            programa_um.clear()
                            doing_intervalo.clear()
                            define_intervalo.clear()
                            consulta_temp.clear()
                            consulta_um.clear()
                            mede_um.set()
                            
                elif (self.last_user_input == 'C'):
                    self.last_user_input = input('Digite o numero do sensor para consultar:\n')
                    if (self.last_user_input.isdigit() == True):
                        if ((int(self.last_user_input) > 0) and (int(self.last_user_input) < 2048)):
                            bloqueia_thread.set()
                            Dados_da_Thread.put(int(self.last_user_input))
                            programa_todos.clear()
                            programa_um.clear()
                            doing_intervalo.clear()
                            define_intervalo.clear()
                            consulta_temp.clear()
                            mede_um.clear()
                            consulta_um.set()
                            
                elif (self.last_user_input == 'T'):
                    self.last_user_input = input('Digite o numero do sensor para consultar a temperatura:\n')
                    if (self.last_user_input.isdigit() == True):
                        if ((int(self.last_user_input) > 0) and (int(self.last_user_input) < 2048)):
                            bloqueia_thread.set()
                            Dados_da_Thread.put(int(self.last_user_input))
                            programa_todos.clear()
                            programa_um.clear()
                            doing_intervalo.clear()
                            define_intervalo.clear()
                            consulta_um.clear()
                            mede_um.clear()
                            consulta_temp.set()
                            
                elif (self.last_user_input == 'A'):
                    bloqueia_thread.set()
                    Dados_da_Thread.put(0)
                    programa_um.clear()
                    consulta_um.clear()
                    mede_um.clear()
                    consulta_temp.clear()
                    doing_intervalo.clear()
                    define_intervalo.clear()
                    programa_todos.set()
                    
                elif (self.last_user_input.isdigit() == True):
                    if ((int(self.last_user_input) > 0) and (int(self.last_user_input) < 2048)):
                        bloqueia_thread.set()
                        Dados_da_Thread.put(int(self.last_user_input))
                        programa_todos.clear()
                        consulta_um.clear()
                        mede_um.clear()
                        consulta_temp.clear()
                        doing_intervalo.clear()
                        define_intervalo.clear()
                        programa_um.set()
                        
                else:
                    programa_todos.clear()
                    programa_um.clear()
                    consulta_um.clear()
                    mede_um.clear()
                    consulta_temp.clear()
                    doing_intervalo.clear()
                    define_intervalo.clear()
                    
            if termina_thread.is_set():
                break

# ----------------------------------------------------------------------------------------------------------

def InitSensorVars():
    global totalSensores
    global listSensores
    global consultaSensorNumero
    
    consultaSensorNumero = -1
    Quantidades = querySQL('SELECT COUNT(*) FROM `sensores`')
    totalSensores = Quantidades[0][0]
    listSensores = []
    selectSensores = querySQL('SELECT numero FROM `sensores` ORDER BY `numero`')
    for x in selectSensores:
        listSensores.append(x[0])
        consultaSensorNumero = listSensores.index(x[0])
    print("\n")

# ----------------------------------------------------------------------------------------------------------

def EnviaComando(SensNum, SensCmd):
    global bus
    
    #canmsg = can.Message(arbitration_id=SensNum, data=[0, 0, SensCmd, 0, 0, 0, 0, 0], is_extended_id=False)
    canmsg = can.Message(arbitration_id=SensNum, data=[0x55, 0x55, SensCmd], is_extended_id=False)
    #canmsg = can.Message(arbitration_id=SensNum, data=[0, 0, SensCmd], is_extended_id=False)
    try:
        #print("Enviando mens. config Sensor", SensNum, "\n", canmsg)
        if (SensCmd == config_sensor):
            print("Enviando mens. programa Sensor", SensNum)
        elif (SensCmd == le_conf_sensor):
            print("Enviando mens. leitura Sensor", SensNum)
        elif (SensCmd == mede_sensor):
            print("Enviando mens. medir Sensor", SensNum)
        elif (SensCmd == le_temp_sensor):
            print("Enviando mens. leitura de Temperatura do Sensor", SensNum)
        bus.send(canmsg)
    except can.CanError:
        print("Erro na CAN em envia comando Sensor", SensNum)
        bus.flush_tx_buffer()

# ----------------------------------------------------------------------------------------------------------

def rec_and_query():
    """Receives all messages and prints them to the console until Q or Ctrl+C is pressed."""
    global consultaSensorNumero
    global bus
    global intervalo

    
    previousDateTimeCan = datetime.now()

    #bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=50000)
    with bus:
        try:
            
            while True:
                try:
                    msg = bus.recv(0.0)
                except can.CanError:
                    print("Erro Recebendo dados CAN!")
                
                if msg is not None:
                    #print(msg)
                    #print(msg.arbitration_id)
                    #print(msg.dlc)
                    #print("Can Msg Rec: ", msg.data)
                    numSensor = msg.arbitration_id
                    try:
                        position = listSensores.index(numSensor)
                        if position != 'None':
                            #print("Resposta Sensor: ", numSensor)
                            #print("Resposta Sensor: ", numSensor, ", ", msg.data[0], ", ", msg.data[1], ", ", msg.data[2])
                            num_int = int(round(msg.data[2] * 4.25))
                            if (msg.data[0] == 0x01) or (msg.data[0] == 0x11):
                                print("Resposta Sensor:", numSensor, ", Livre, Distancia medida:", num_int)
                            elif (msg.data[0] == 0x02) or (msg.data[0] == 0x12):
                                print("Resposta Sensor:", numSensor, ", Ocupado, Distancia medida:", num_int)
                            elif (msg.data[0] == 0x03) or (msg.data[0] == 0x13):
                                print("Resposta Sensor:", numSensor, ", Valor medido e programado:", num_int)
                                rasc = querySQL('UPDATE `sensores` SET `medicao`={} WHERE `numero`={} '.format(num_int, numSensor))
                            elif (msg.data[0] == 0x04) or (msg.data[0] == 0x14):
                                print("Resposta Sensor:", numSensor, ", Valor programado:", num_int)
                            if (msg.data[0] == 0x11) or (msg.data[0] == 0x12) or (msg.data[0] == 0x13) or (msg.data[0] == 0x14) or (msg.data[0] == 0x15):
                                print("Resposta Sensor:", numSensor, ", Temperatura medida:", int(msg.data[1])-50)
                                rasc = querySQL('UPDATE `sensores` SET `termometro`="S" WHERE `numero`={}'.format(numSensor))
                    except:
                        print("Dado recebido na CAN de sensor não instalado!")
                
                if ((programa_todos.is_set()) and not(programa_um.is_set()) and not(consulta_um.is_set()) and not(mede_um.is_set()) and not(consulta_temp.is_set())):
                    currentDateTime = datetime.now()
                    segundos = currentDateTime.second - previousDateTimeCan.second
                    if Dados_da_Thread.empty() != True:
                        rasc = Dados_da_Thread.get()
                        InitSensorVars()
                        if (consultaSensorNumero != -1):
                            consultaSensorNumero = 0
                    if segundos < 0:
                        segundos += 60
                    if segundos >= intervalo:
                        previousDateTimeCan = currentDateTime
                        QuantSens = querySQL('SELECT COUNT(*) FROM `sensores`')
                        if (totalSensores != QuantSens[0][0]):
                            InitSensorVars()
                            if (consultaSensorNumero != -1):
                                consultaSensorNumero = 0
                        if (consultaSensorNumero != -1):
                            if not(doing_intervalo.is_set()):
                                numSensor = listSensores[consultaSensorNumero]
                                EnviaComando(numSensor, config_sensor)
                                consultaSensorNumero += 1
                                if consultaSensorNumero >= totalSensores:
                                    consultaSensorNumero = 0
                                    doing_intervalo.set()
                            else:
                                doing_intervalo.clear()
                                programa_todos.clear()
                                bloqueia_thread.clear()
                        else:
                            programa_todos.clear()
                            doing_intervalo.clear()
                            bloqueia_thread.clear()
                    if kbhit():
                            #consultaSensorNumero = 0
                            programa_todos.clear()
                            doing_intervalo.clear()
                            bloqueia_thread.clear()

                elif (not(programa_todos.is_set()) and (programa_um.is_set()) and not(consulta_um.is_set()) and not(mede_um.is_set()) and not(consulta_temp.is_set())):
                    currentDateTime = datetime.now()
                    segundos = currentDateTime.second - previousDateTimeCan.second
                    if segundos < 0:
                        segundos += 60
                    if segundos >= intervalo:
                        previousDateTimeCan = currentDateTime
                        if not(doing_intervalo.is_set()):
                            if Dados_da_Thread.empty() != True:
                                numSensor = Dados_da_Thread.get()
                                EnviaComando(numSensor, config_sensor)
                                doing_intervalo.set()
                            else:
                                programa_um.clear()
                                doing_intervalo.clear()
                                bloqueia_thread.clear()
                        else:
                            programa_um.clear()
                            doing_intervalo.clear()
                            bloqueia_thread.clear()
                
                elif (not(programa_todos.is_set()) and not(programa_um.is_set()) and not (consulta_um.is_set()) and (mede_um.is_set()) and not(consulta_temp.is_set())):
                    currentDateTime = datetime.now()
                    segundos = currentDateTime.second - previousDateTimeCan.second
                    if segundos < 0:
                        segundos += 60
                    if segundos >= intervalo:
                        previousDateTimeCan = currentDateTime
                        if not(doing_intervalo.is_set()):
                            if Dados_da_Thread.empty() != True:
                                numSensor = Dados_da_Thread.get()
                                EnviaComando(numSensor, mede_sensor)
                                doing_intervalo.set()
                            else:
                                mede_um.clear()
                                doing_intervalo.clear()
                                bloqueia_thread.clear()
                        else:
                            mede_um.clear()
                            doing_intervalo.clear()
                            bloqueia_thread.clear()

                elif (not(programa_todos.is_set()) and not(programa_um.is_set()) and (consulta_um.is_set()) and not(mede_um.is_set()) and not(consulta_temp.is_set())):
                    currentDateTime = datetime.now()
                    segundos = currentDateTime.second - previousDateTimeCan.second
                    if segundos < 0:
                        segundos += 60
                    if segundos >= intervalo:
                        previousDateTimeCan = currentDateTime
                        if not(doing_intervalo.is_set()):
                            if Dados_da_Thread.empty() != True:
                                numSensor = Dados_da_Thread.get()
                                EnviaComando(numSensor, le_conf_sensor)
                                doing_intervalo.set()
                            else:
                                consulta_um.clear()
                                doing_intervalo.clear()
                                bloqueia_thread.clear()
                        else:
                            consulta_um.clear()
                            doing_intervalo.clear()
                            bloqueia_thread.clear()

                elif (not(programa_todos.is_set()) and not(programa_um.is_set()) and not(consulta_um.is_set()) and not(mede_um.is_set()) and (consulta_temp.is_set())):
                    currentDateTime = datetime.now()
                    segundos = currentDateTime.second - previousDateTimeCan.second
                    if segundos < 0:
                        segundos += 60
                    if segundos >= intervalo:
                        previousDateTimeCan = currentDateTime
                        if not(doing_intervalo.is_set()):
                            if Dados_da_Thread.empty() != True:
                                numSensor = Dados_da_Thread.get()
                                EnviaComando(numSensor, le_temp_sensor)
                                doing_intervalo.set()
                            else:
                                consulta_temp.clear()
                                doing_intervalo.clear()
                                bloqueia_thread.clear()
                        else:
                            consulta_temp.clear()
                            doing_intervalo.clear()
                            bloqueia_thread.clear()

                elif (define_intervalo.is_set()):
                    if Dados_da_Thread.empty() != True:
                        intervalo = Dados_da_Thread.get()
                        print("O novo intervalo é : ", intervalo)
                        define_intervalo.clear()
                        doing_intervalo.clear()
                        bloqueia_thread.clear()

                elif ((programa_todos.is_set()) and (programa_um.is_set()) and (consulta_um.is_set()) and (mede_um.is_set()) and (consulta_temp.is_set())):
                    print("Saindo!")
                    termina_thread.set()
                    it.join()
                    exit()

        except KeyboardInterrupt:
            #print("Saindo!")
            pass  # exit normally

# ----------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    InitSensorVars()

    #Subprocess ask user
    it = InputThread()
    it.start()

    rec_and_query()

    it.join(0.5)
