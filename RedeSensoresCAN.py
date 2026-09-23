from __future__ import annotations
import can
import time
from typing import Iterable, Union, Optional




class RedeSensoresCAN:
    """
    Classe para comunicação com sensores através da rede CAN.

    Protocolo utilizado:

        Comandos enviados:
            0xAA - Configurar/programar sensor
            0xAB - Ler configuração do sensor
            0xA5 - Ler temperatura
            0x00 - Medir sensor

        Formato da mensagem enviada:
            Byte 0: 0x55
            Byte 1: 0x55
            Byte 2: comando

        O ID CAN corresponde ao número do sensor.
    """

    COMANDO_CONFIGURAR = 0xAA
    COMANDO_LER_CONFIGURACAO = 0xAB
    COMANDO_LER_TEMPERATURA = 0xA5
    COMANDO_MEDIR = 0x00

    MIN_SENSOR = 1
    MAX_SENSOR = 2047

    def __init__(
        self,
        canal: str = "can0",
        bitrate: int = 50000,
        sensores: Optional[Iterable[int]] = None,
        timeout: float = 3.0,
        intervalo_envio: float = 0.05,
    ):
        """
        Inicializa a rede CAN.

        :param canal: Nome da interface CAN, normalmente can0.
        :param bitrate: Velocidade da rede CAN.
        :param sensores: Lista opcional dos sensores instalados.
        :param timeout: Tempo máximo aguardando uma resposta.
        :param intervalo_envio: Intervalo entre mensagens enviadas.
        """

        self.canal = canal
        self.bitrate = bitrate
        self.timeout = timeout
        self.intervalo_envio = intervalo_envio

        self.sensores = set()

        if sensores is not None:
            self.sensores = self._normalizar_sensores(sensores)

        self.bus = can.Bus(
            interface="socketcan",
            channel=self.canal,
            bitrate=self.bitrate,
        )

    # ------------------------------------------------------------------
    # Controle básico
    # ------------------------------------------------------------------

    def fechar(self):
        """Fecha a interface CAN."""
        if self.bus is not None:
            self.bus.shutdown()
            self.bus = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.fechar()

    # ------------------------------------------------------------------
    # Validação de sensores
    # ------------------------------------------------------------------

    def _validar_sensor(self, numero: int):
        """Valida o número de um sensor."""

        if not isinstance(numero, int):
            raise TypeError("O número do sensor deve ser inteiro.")

        if not self.MIN_SENSOR <= numero <= self.MAX_SENSOR:
            raise ValueError(
                "O sensor deve estar entre {} e {}.".format(
                    self.MIN_SENSOR, self.MAX_SENSOR
                )
            )

    def _normalizar_sensores(
        self,
        sensores: Union[int, Iterable[int]]
    ) -> list[int]:
        """
        Converte um sensor ou uma lista de sensores em uma lista padronizada.
        """

        if isinstance(sensores, int):
            lista = [sensores]
        else:
            lista = list(sensores)

        for sensor in lista:
            self._validar_sensor(sensor)

        return lista

    def definir_sensores(self, sensores: Iterable[int]):
        """Define ou substitui a lista de sensores instalados."""

        self.sensores = set(self._normalizar_sensores(sensores))

    # ------------------------------------------------------------------
    # Envio de comandos
    # ------------------------------------------------------------------

    def enviar_comando(self, sensor: int, comando: int) -> bool:
        """
        Envia um comando para um sensor.

        :param sensor: ID CAN/número do sensor.
        :param comando: Comando a ser enviado.
        :return: True se o envio foi realizado.
        """

        self._validar_sensor(sensor)

        mensagem = can.Message(
            arbitration_id=sensor,
            data=[0x55, 0x55, comando],
            is_extended_id=False,
        )

        try:
            self.bus.send(mensagem)

            print(
                "Comando 0x{:02X} enviado para o sensor {}".format(
                    comando, sensor
                )
            )

            return True

        except can.CanError as erro:
            print(
                "Erro ao enviar comando para o sensor {}: {}".format(
                    sensor, erro
                )
            )
            return False

    def enviar_para_varios(
        self,
        sensores: Union[int, Iterable[int]],
        comando: int,
        aguardar_resposta: bool = True,
    ) -> dict:
        """
        Envia o mesmo comando para um ou vários sensores.

        :param sensores: Número de um sensor ou lista de sensores.
        :param comando: Comando a ser enviado.
        :param aguardar_resposta: Define se deve aguardar respostas.
        :return: Dicionário com as respostas por sensor.
        """

        lista_sensores = self._normalizar_sensores(sensores)
        respostas = {}

        for sensor in lista_sensores:
            enviado = self.enviar_comando(sensor, comando)

            if not enviado:
                respostas[sensor] = {
                    "sensor": sensor,
                    "erro": "Falha no envio",
                }
                continue

            if aguardar_resposta:
                resposta = self.aguardar_resposta(sensor)
                respostas[sensor] = resposta
            else:
                respostas[sensor] = {
                    "sensor": sensor,
                    "enviado": True,
                }

            time.sleep(self.intervalo_envio)

        return respostas

    # ------------------------------------------------------------------
    # Recepção e interpretação
    # ------------------------------------------------------------------

    def aguardar_resposta(
        self,
        sensor: int,
        timeout: Optional[float] = None,
    ) -> dict:
        """
        Aguarda uma resposta CAN de determinado sensor.

        :param sensor: Número do sensor.
        :param timeout: Timeout opcional.
        :return: Resposta interpretada em formato de dicionário.
        """

        self._validar_sensor(sensor)

        tempo_limite = timeout if timeout is not None else self.timeout
        inicio = time.monotonic()

        while time.monotonic() - inicio < tempo_limite:
            restante = tempo_limite - (time.monotonic() - inicio)

            try:
                mensagem = self.bus.recv(timeout=max(0.01, restante))
            except can.CanError as erro:
                return {
                    "sensor": sensor,
                    "erro": "Erro ao receber mensagem: {}".format(erro),
                }

            if mensagem is None:
                continue

            # Ignora mensagens de outros sensores
            if mensagem.arbitration_id != sensor:
                continue

            return self.interpretar_resposta(mensagem)

        return {
            "sensor": sensor,
            "timeout": True,
            "mensagem": "Nenhuma resposta recebida",
        }

    def interpretar_resposta(self, mensagem: can.Message) -> dict:
        """
        Interpreta uma mensagem recebida do sensor.

        Formato esperado:

            data[0] - tipo da resposta
            data[1] - temperatura codificada
            data[2] - distância codificada
        """

        dados = list(mensagem.data)

        resultado = {
            "sensor": mensagem.arbitration_id,
            "dados_brutos": dados,
            "tipo": "desconhecido",
        }

        if len(dados) == 0:
            resultado["erro"] = "Mensagem sem dados"
            return resultado

        codigo_resposta = dados[0]

        # Distância
        if len(dados) > 2:
            distancia = int(round(dados[2] * 4.25))
            resultado["distancia"] = distancia

        # Temperatura
        if len(dados) > 1 and codigo_resposta in {
            0x11,
            0x12,
            0x13,
            0x14,
            0x15,
        }:
            resultado["temperatura"] = int(dados[1]) - 50

        # Interpretação do status
        if codigo_resposta in {0x01, 0x11}:
            resultado["tipo"] = "status"
            resultado["status"] = "livre"

        elif codigo_resposta in {0x02, 0x12}:
            resultado["tipo"] = "status"
            resultado["status"] = "ocupado"

        elif codigo_resposta in {0x03, 0x13}:
            resultado["tipo"] = "medicao_programada"
            resultado["status"] = "medição e programação recebidas"

        elif codigo_resposta in {0x04, 0x14}:
            resultado["tipo"] = "configuracao"
            resultado["status"] = "valor programado"

        elif codigo_resposta == 0x15:
            resultado["tipo"] = "temperatura"

        resultado["codigo_resposta"] = "0x{:02X}".format(codigo_resposta)

        return resultado

    # ------------------------------------------------------------------
    # Operações específicas
    # ------------------------------------------------------------------

    def medir(self, sensores):
        """
        Solicita uma medição para um sensor ou vários sensores.

        :param sensores: Um número ou uma lista de números.
        """

        return self.enviar_para_varios(
            sensores=sensores,
            comando=self.COMANDO_MEDIR,
        )

    def configurar(self, sensores):
        """
        Configura/programa um sensor ou vários sensores.

        Observação:
        No protocolo do código original, o comando de configuração
        não possui valor adicional. Ele apenas envia 0xAA.
        """

        return self.enviar_para_varios(
            sensores=sensores,
            comando=self.COMANDO_CONFIGURAR,
        )

    def ler_configuracao(self, sensores):
        """
        Consulta a configuração de um sensor ou vários sensores.
        """

        return self.enviar_para_varios(
            sensores=sensores,
            comando=self.COMANDO_LER_CONFIGURACAO,
        )

    def ler_temperatura(self, sensores):
        """
        Consulta a temperatura de um sensor ou vários sensores.
        """

        return self.enviar_para_varios(
            sensores=sensores,
            comando=self.COMANDO_LER_TEMPERATURA,
        )

    def consultar_status(self, sensores):
        """
        Solicita o status de ocupação dos sensores.

        O status normalmente será:

            livre
            ocupado
        """

        return self.enviar_para_varios(
            sensores=sensores,
            comando=self.COMANDO_MEDIR,
        )

    # ------------------------------------------------------------------
    # Operações em todos os sensores cadastrados
    # ------------------------------------------------------------------

    def configurar_todos(self):
        """Configura todos os sensores cadastrados."""

        if not self.sensores:
            raise ValueError("Nenhum sensor foi cadastrado.")

        return self.configurar(sorted(self.sensores))

    def medir_todos(self):
        """Mede todos os sensores cadastrados."""

        if not self.sensores:
            raise ValueError("Nenhum sensor foi cadastrado.")

        return self.medir(sorted(self.sensores))

    def consultar_status_todos(self):
        """Consulta o status de todos os sensores cadastrados."""

        if not self.sensores:
            raise ValueError("Nenhum sensor foi cadastrado.")

        return self.consultar_status(sorted(self.sensores))

    def consultar_temperatura_todos(self):
        """Consulta a temperatura de todos os sensores cadastrados."""

        if not self.sensores:
            raise ValueError("Nenhum sensor foi cadastrado.")

        return self.ler_temperatura(sorted(self.sensores))