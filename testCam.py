from RedeSensoresCAN import RedeSensoresCAN


with RedeSensoresCAN(
    canal="can0",
    bitrate=50000,
) as rede:

    resposta = rede.medir(10)

    print(resposta)
