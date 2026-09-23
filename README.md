# ParkingApiCam
from rede_sensores_can import RedeSensoresCAN


with RedeSensoresCAN(
    canal="can0",
    bitrate=50000,
) as rede:

    resposta = rede.medir(10)

    print(resposta)





from rede_sensores_can import RedeSensoresCAN


sensores = [1, 2, 3, 4, 5]

with RedeSensoresCAN(
    canal="can0",
    bitrate=50000,
) as rede:

    respostas = rede.medir(sensores)

    for numero_sensor, resposta in respostas.items():
        print(f"Sensor {numero_sensor}:")
        print(resposta)


