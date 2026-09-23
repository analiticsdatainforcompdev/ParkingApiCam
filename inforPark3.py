"""
Project InforPark2

Created on Feb 27 2023

@author: EPS
Changed in Mar 02 2023 by Edilson Claudino da Silva
Version: 2.06  -  19/09/2023
"""

import can
from datetime import datetime # Biblioteca do python de Data e Hora
from mySQLcom import querySQL
import socket
import time
import subprocess
from threading import Thread
import os
import usbrelay_py

SpiderPort = 2101
mensSpider = [0x01, 0x02, 0x50, 0x01, 0x01, 0xDB, 0x01, 0x01, 0x80, 0x01, 0x01, 0x00, 0x08, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x03, 0x00, 0x00]
flagUpdatePaineis = False
ContadorTxdPaineis = -1

totalSensores = 0                        # MAX 2047
totalPaineis = 0                         # MAX 80
totalOcupadas = 0
consultaSensorNumero = -1
listSensores = []
listSensoresVal = []
listPaineis = []
listPaineisVal = []

flagAlarmes = False
flagCancAlarmPeriod = False
flagExisteRele = False
placaRele = usbrelay_py.board_details()
Temp_de_Alarme = 57
habilitarRebootCan =True

# ----------------------------------------------------------------------------------------------------------

def transmitePainel(ip, data : bytearray):

    #print(ip, data)

#Cria e abre um socket para o painel (ip e porta)
    try:
        client = socket.create_connection((ip,SpiderPort), timeout=3)
    except socket.error as err:
        print('Erro de conexão com painel:', ip, err)
        return(1)
#envia dados e fecha o socket
    try:
        client.sendall(data)
        time.sleep(0.1)
    except socket.error as err:
        print('Erro de envio de dados:', ip, err)
        return(1)
#Close socket        
    finally:
        client.close()
        time.sleep(0.1)

# ---------------------------------------------------------------------------------------------------------

def crc16(data : bytearray, length):
    crc = 0xFFFF
    for i in range(0, length):
        crc ^= data[i] << 8
        for j in range(0,8):
            if (crc & 0x8000) > 0:
                crc =(crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF

# ----------------------------------------------------------------------------------------------------------

def InitSensorVars():
    global totalSensores
    global totalPaineis
    global totalOcupadas
    global consultaSensorNumero
    global listSensores
    global listSensoresVal
    global listPaineis
    global listPaineisVal
    global flagUpdatePaineis
    global flagExisteRele
    global flagAlarmes
    global placasRele
    global Temp_de_Alarme
    
    if usbrelay_py.board_count()>0:
        flagExisteRele = True
        placasRele = usbrelay_py.board_details()
        usbrelay_py.board_control(placasRele[0][0],1,0)
        usbrelay_py.board_control(placasRele[0][0],2,0)

    totalOcupadas = 0
    consultaSensorNumero = -1
    Quantidades = querySQL('SELECT COUNT(*) FROM `sensores`')
    totalSensores = Quantidades[0][0]
    Quantidades = querySQL('SELECT COUNT(*) FROM `paineis`')
    totalPaineis = Quantidades[0][0]
    listSensores = []
    listSensoresVal = []
    listPaineis = []
    listPaineisVal = []
    selectPaineis = querySQL('SELECT `numero_painel` FROM `paineis` ORDER BY `numero_painel`')
    for y in selectPaineis:
        listPaineis.append(y[0])
        listPaineisVal.append(0)
    selectSensores = querySQL('SELECT numero FROM `sensores` ORDER BY `numero`')
    for x in selectSensores:
        selectLastStatus = querySQL('SELECT `status` FROM `movimentossensores` WHERE `status` < 3 AND `sensores_numero` = {} ORDER BY `nsr` DESC LIMIT 1'.format(x[0]))
        if (not selectLastStatus) == False:
            listSensores.append(x[0])
            listSensoresVal.append(selectLastStatus[0][0])
            if selectLastStatus[0][0] == '2':
                totalOcupadas += 1
            elif selectLastStatus[0][0] == '1':
                selectPaineis = querySQL('SELECT `paineis_numero_painel` FROM `sensores_has_paineis` WHERE `sensores_numero` = {}'.format(x[0]))
                for y in selectPaineis:
                    position = listPaineis.index(y[0])
                    listPaineisVal[position] += 1
                    flagUpdatePaineis = True
        else:
            listSensores.append(x[0])
            listSensoresVal.append('1')
            selectPaineis = querySQL('SELECT `paineis_numero_painel` FROM `sensores_has_paineis` WHERE `sensores_numero` = {}'.format(x[0]))
            for y in selectPaineis:
                position = listPaineis.index(y[0])
                listPaineisVal[position] += 1
                flagUpdatePaineis = True
        consultaSensorNumero = listSensores.index(x[0])
    print("Total de Vagas  =", totalSensores, " - Total de Vagas Ocupadas =", totalOcupadas, " - Total Livres =", (totalSensores - totalOcupadas))
    
    selectLastStatus = querySQL('SELECT `status` FROM `historicoAlarmes` ORDER BY `nmov` DESC LIMIT 1')
    if (not selectLastStatus) == False:
        if selectLastStatus[0][0] == 'A':
            if flagExisteRele == True:
                usbrelay_py.board_control(placasRele[0][0],1,1)
                usbrelay_py.board_control(placasRele[0][0],2,1)
            flagAlarmes = True
        else:
            flagAlarmes = False
    else:
        flagAlarmes = False
    
    selectLastStatus = querySQL('SELECT `Temp_de_Alarme` FROM `configuracaoNuvem`')
    Temp_de_Alarme = int(selectLastStatus[0][0])
    
    #print("Sensores",  end='')
    #for x in range (0, totalSensores, 1):
        #print(" -S", x + 1, "= ", listSensoresVal[x], sep='', end='')
    #print("")
    #print("Paineis ", end='')
    #for x in range (0, totalPaineis, 1):
        #print(" -P", x + 1, "= ", listPaineisVal[x], sep='', end='')
    #print("\n")

# ----------------------------------------------------------------------------------------------------------

def gravaHistoricoAlarmes(status, CPF, numsensor):

    hora = datetime.now().strftime("%H:%M:%S")
    data = datetime.now().strftime("%Y-%m-%d")
    querySQL('INSERT INTO historicoAlarmes (nmov, status, CPF, data_ativ_desativ, hora_ativ_desativ, numSensor, nuvem) VALUES (NULL, \'{}\', {}, \'{}\', \'{}\', \'{}\', \'N\')'.format(status, CPF, data, hora, numsensor))

# ----------------------------------------------------------------------------------------------------------

def gravaMovimentosSensores(selectCodSensor, status, medicao, temperatura):
    global flagUpdatePaineis

    hora = datetime.now().strftime("%H:%M:%S")
    data = datetime.now().strftime("%Y-%m-%d")
    if temperatura != '':
        querySQL('INSERT INTO movimentossensores (nsr, status, data, hora, nuvem, sensores_numero, medicao, temperatura) VALUES (NULL, {}, \'{}\', \'{}\', \'N\', {}, {}, {})'.format(status, data, hora, selectCodSensor, medicao, temperatura))
    else:
        querySQL('INSERT INTO movimentossensores (nsr, status, data, hora, nuvem, sensores_numero, medicao, temperatura) VALUES (NULL, {}, \'{}\', \'{}\', \'N\', {}, {}, NULL)'.format(status, data, hora, selectCodSensor, medicao))
    selectPaineis = querySQL('SELECT `paineis_numero_painel` FROM `sensores_has_paineis` WHERE `sensores_numero` = {}'.format(selectCodSensor))
    for z in selectPaineis:
        if status == 1:
            listPaineisVal[listPaineis.index(z[0])] += 1
            flagUpdatePaineis = True
        elif status == 2:
            if listPaineisVal[listPaineis.index(z[0])] > 0:
                listPaineisVal[listPaineis.index(z[0])] -= 1
                flagUpdatePaineis = True

# ----------------------------------------------------------------------------------------------------------

def rec_and_query():
    """Receives all messages and prints them to the console until Ctrl+C is pressed."""
    global consultaSensorNumero
    global totalOcupadas
    global flagUpdatePaineis
    global ContadorTxdPaineis
    global mensSpider
    global temperatura
    global flagAlarmes
    global flagCancAlarmPeriod
    global flagExisteRele
    global Temp_de_Alarme

    
    previousDateTimeCan = datetime.now()
    previousDateTimePainel = datetime.now()
    previousDateTimeAlarme = datetime.now()
    intervaloPaineis = False
    contador = 0

    with can.interface.Bus(bustype="socketcan", channel="can0", bitrate=50000) as bus:
        try:
            
            while True:
                try:
                    msg = bus.recv(0.0)
                except can.CanError:
                    print("Erro Recebendo dados CAN 1")
                    msg=None
                
                if msg is not None:
                    #print(msg)
                    #print(msg.arbitration_id, msg.data)
                    #print(msg.dlc)
                    #print(msg.data)
                    numSensor = msg.arbitration_id
                    try:
                        if ((msg.data[0] & 0x10) != 0):
                            temperatura = msg.data[1] - 50
                            selectLastTemp = querySQL('SELECT `temperatura` FROM `movimentossensores` WHERE `sensores_numero` = {} ORDER BY `nsr` DESC LIMIT 1'.format(numSensor))
                            if (not selectLastTemp) == False:
                                tempAnt = selectLastTemp[0][0]
                            if (temperatura) >= Temp_de_Alarme:
                                gravaHistoricoAlarmes('A', '00000000000', numSensor)
                                if flagAlarmes == False:
                                    flagAlarmes = True
                                    if (querySQL('SELECT `paineis_numero_painel` FROM `sensores_has_paineis` WHERE `sensores_numero` = {}'.format(numSensor))) != []:
                                        flagUpdatePaineis = True
                                        intervaloPaineis = True
                                    if flagExisteRele == True:
                                        usbrelay_py.board_control(placasRele[0][0],1,1)
                                        usbrelay_py.board_control(placasRele[0][0],2,1)
                        else:
                            temperatura = ''
                                
                        position = listSensores.index(numSensor)
                        #print(position, med_int)
                        if position != 'None':
                            med_int = int(round(msg.data[2] * 4.25))
                            if (((msg.data[0] & 0x0F) == 1) and (listSensoresVal[position] == '2')):
                                #print("Sensor:", numSensor, "Livre")
                                listSensoresVal[position] = '1'
                                if totalOcupadas > 0:
                                    totalOcupadas -= 1
                                gravaMovimentosSensores(numSensor, 1, med_int, temperatura)
                                print("Total de Vagas  =", totalSensores, " - Total de Vagas Ocupadas =", totalOcupadas, " - Total Livres =", (totalSensores - totalOcupadas))
                                #print("Sensores",  end='')
                                #for x in range (0, totalSensores, 1):
                                    #print(" -S", x + 1, "= ", listSensoresVal[x], sep='', end='')
                                #print("")
                                #print("Paineis ", end='')
                                #for x in range (0, totalPaineis, 1):
                                    #print(" -P", x + 1, "= ", listPaineisVal[x], sep='', end='')
                                #print("\n")
                            elif (((msg.data[0] & 0x0F) == 2) and (listSensoresVal[position] == '1')):
                                #print("Sensor:", numSensor, "Ocupado")
                                listSensoresVal[position] = '2'
                                if totalOcupadas < totalSensores:
                                    totalOcupadas += 1
                                gravaMovimentosSensores(numSensor, 2, med_int, temperatura)
                                print("Total de Vagas  =", totalSensores, " - Total de Vagas Ocupadas =", totalOcupadas, " - Total Livres =", (totalSensores - totalOcupadas))
                                #print("Sensores",  end='')
                                #for x in range (0, totalSensores, 1):
                                    #print(" -S", x + 1, "= ", listSensoresVal[x], sep='', end='')
                                #print("")
                                #print("Paineis ", end='')
                                #for x in range (0, totalPaineis, 1):
                                    #print(" -P", x + 1, "= ", listPaineisVal[x], sep='', end='')
                                #print("\n")
                            elif (msg.data[0] == 0x15):
                                gravaMovimentosSensores(numSensor, '5', '0', temperatura)
                                
                    except:
                        if habilitarRebootCan:
                            rebootCan()
                            
                        #print("Erro em dado recebido na CAN 2")

                        
                currentDateTime = datetime.now()
                segundos = currentDateTime.second - previousDateTimeCan.second
                if segundos < 0:
                    segundos += 60
                if segundos >= 5:
                    previousDateTimeCan = currentDateTime
                    QuantSens = querySQL('SELECT COUNT(*) FROM `sensores`')
                    QuantPans = querySQL('SELECT COUNT(*) FROM `paineis`')
                    if (totalSensores != QuantSens[0][0]) or (totalPaineis != QuantPans[0][0]):
                        InitSensorVars()
                    if (consultaSensorNumero != -1):

                        
                        # -- Validação do indice para não dar erro de ranger.
                        # -- Alteração em: 23/04/2026 07:18
                        # -- EdislonCsilva 

                        if consultaSensorNumero <  len(listSensores):
                            try:
                                numSensor = listSensores[consultaSensorNumero]
                                canmsg = can.Message(arbitration_id=numSensor, data=[0x55, 0x55, 0x00], is_extended_id=False)
                                bus.send(canmsg)
                                print("Pergunta status numsensor", numSensor)
                            except:
                                if(habilitarRebootCan):
                                    rebootCan()


                        
                        
                        consultaSensorNumero += 1
                        if consultaSensorNumero >= totalSensores:
                            consultaSensorNumero = 0;

                currentDateTime = datetime.now()
                segundos = currentDateTime.second - previousDateTimePainel.second
                if segundos < 0:
                    segundos += 60
                if segundos >= 10:
                    previousDateTimePainel = currentDateTime
                    intervaloPaineis = True
                    
                if (flagUpdatePaineis == True) and (intervaloPaineis == True):
                    if ContadorTxdPaineis < 0:
                        ContadorTxdPaineis = 0
                        ListaPaineis = querySQL('SELECT `numero_painel`, `ip` FROM `paineis`')
                    numeroPainel = ListaPaineis[ContadorTxdPaineis][0]
                    if flagAlarmes == False:
                        valor = listPaineisVal[listPaineis.index(numeroPainel)]
                    else:
                        valor = 0   
                    #print("Painel ", numeroPainel, "Valor ", valor)
                    for i in range (20, 12, -1):
                        digit = valor % 10
                        mensSpider[i] = digit + 0x30
                        valor = int((valor - digit) / 10)
                    crc = crc16(mensSpider, int(len(mensSpider)) - 2)
                    digit = crc % 256
                    mensSpider[23] = digit
                    digit = int((crc - digit) / 256)
                    mensSpider[22] = digit
                    datatoSend = bytearray(mensSpider)
                    #print(ListaPaineis[ContadorTxdPaineis][1],datatoSend)
                    transmitePainel(ListaPaineis[ContadorTxdPaineis][1], datatoSend)
                    ContadorTxdPaineis += 1
                    if ContadorTxdPaineis == totalPaineis:
                        flagUpdatePaineis = False
                        intervaloPaineis = False
                        ContadorTxdPaineis = -1

                if flagAlarmes == True:
                    currentDateTime = datetime.now()
                    segundos = currentDateTime.second - previousDateTimeAlarme.second
                    if segundos < 0:
                        segundos += 60
                    if segundos >= 5:
                        previousDateTimeAlarme = currentDateTime
                        selectLastAlarme = querySQL('SELECT `status` FROM `historicoAlarmes` ORDER BY `nmov` DESC LIMIT 1')
                        if selectLastAlarme[0][0] == 'D':
                            flagAlarmes = False
                            if (querySQL('SELECT `paineis_numero_painel` FROM `sensores_has_paineis` WHERE `sensores_numero` = {}'.format(numSensor))) != []:
                                flagUpdatePaineis = True
                                intervaloPaineis = True
                            if flagExisteRele == True:
                                usbrelay_py.board_control(placasRele[0][0],1,0)
                                usbrelay_py.board_control(placasRele[0][0],2,0)


        except KeyboardInterrupt:
            pass  # exit normally

# ----------------------------------------------------------------------------------------------------------




def rebootCan():
    try:
        
        print("#Error Restart")
        os.system('sudo ip link set can0 down')
        os.system('sudo ip link set can0 up type can bitrate 50000')

    except Exception as e:
        print("#Error: "+repr(e))


def check_ping(host):
    hostname = host
    response = os.system("ping -c 1 " + hostname)
    if response == 0:
      return True
    else:
      return False



def isInternet(name):
    minutos =30
    minutosParaSegundos =60
    while True:
        try:
            if(check_ping(name)==False):
                os.system('sudo reboot')
        except:
            pass

        time.sleep(minutos * minutosParaSegundos)

# ----------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    def execProcess():
        subprocess.call('python3 /home/inforcomp/project/firmware/update_master_api.py', shell = True)
        subprocess.call('python3 ./updateNuvem.py', shell = True)
  
    subPr = Thread(target=execProcess, args=())
    #subPr.start()
    InitSensorVars()
    rec_and_query()
    subPr.join()
