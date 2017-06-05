

__author__ = 'bejar'

"""
.. module:: FlaskAgent
FlaskAgent
*************
:Description: FlaskAgent
  Simple servicio web Flask que envia y recibe mensajes con otra instancia del mismo servicio.
  Se ha de invocar desde linea de comandos por ejemplo:
  python FlaskAgent.py --host localhost --port 9000 --acomm localhost --aport 9001 --messages a b c
  donde:
   --host es la maquina donde corre el servicio (por defecto localhost)
            si se usa el host 0.0.0.0 se podra ver el servicio desde otras maquinas
   --port es el puerto de escucha del servicio
   --acomm es la maquina donde esta el servicio al que se le enviaran mensajes
   --aport es el puerto donde escucha el servicio con el que nos vamos a comunicar
   --messages es una lista de mensajes que se enviaran
  para que funcione tiene que haber otra instancia del servicio en el host y puerto indicados.
  En la red de PCs de los aularios se pueden usar los puertos de 9000-10000 para comunicarse entre
  distintos pc's, se puede averiguar el nombre de la maquina en la que estamos haciendo por ejemplo
  uname -n
:Authors: bejar
    
:Version: 
:Created on: 18/02/2015 8:28 
"""
from skyscanner.skyscanner import FlightsCache
from AgentUtil.Agent import Agent
from AgentUtil.ACLMessages import get_message_properties, build_message, register_agent, send_message
from AgentUtil.OntoNamespaces import ACL, ECSDI
from flask import Flask, request
import argparse
import requests
from rdflib import Graph, Namespace, RDF, URIRef, Literal, XSD
from requests import ConnectionError
from multiprocessing import Process, Queue
from AgentUtil.Logging import config_logger
from AgentUtil.FlaskServer import shutdown_server
import socket



# Definimos los parametros de la linea de comandos
parser = argparse.ArgumentParser()
parser.add_argument('--open', help="Define si el servidor est abierto al exterior o no", action='store_true',
                    default=False)
parser.add_argument('--port', type=int, help="Puerto de comunicacion del agente")
parser.add_argument('--dhost', default=socket.gethostname(), help="Host del agente de directorio")
parser.add_argument('--dport', type=int, help="Puerto de comunicacion del agente de directorio")

# Logging
logger = config_logger(level=1)

# parsing de los parametros de la linea de comandos
args = parser.parse_args()

# Configuration stuff
if args.port is None:
    port = 9000
else:
    port = args.port

if args.open is None:
    hostname = '0.0.0.0'
else:
    hostname = socket.gethostname()

if args.dport is None:
    dport = 9081
else:
    dport = args.dport

if args.dhost is None:
    dhostname = socket.gethostname()
else:
    dhostname = args.dhost
    # Agent Namespace
    agn = Namespace("http://www.agentes.org#")

    # Message Count
    mss_cnt = 0

    # Data Agent
    # Datos del Agente
    AgGestordeTransporte = Agent('AgGestordeTransporte',
                        agn.AgGestordeTransporte,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))

    # Directory agent address
    DirectoryAgent = Agent('DirectoryAgent',
                           agn.Directory,
                           'http://%s:%d/Register' % (dhostname, dport),
                           'http://%s:%d/Stop' % (dhostname, dport))

    # Global triplestore graph
    dsGraph = Graph()

    # Queue
    queue = Queue()

    # Flask app
    app = Flask(__name__)


def get_count():
    global mss_cnt
    mss_cnt += 1
    return mss_cnt


def register_message():
    """
    Envia un mensaje de registro al servicio de registro
    usando una performativa Request y una accion Register del
    servicio de directorio
    :param gmess:
    :return:
    """

    logger.info('Nos registramos')

    gr = register_agent(AgGestordeTransporte, DirectoryAgent, AgGestordeTransporte.uri, get_count())
    return gr

@app.route("/")
def isalive():
    """
    Entrada del servicio para saber si esta en funcionamiento
    :return:
    """
    return 'alive'


def buscar_transportes_externamente(ciudadOrigen, ciudadDestino, inicioData, finData):


    # Creamos un array con 5 transportes vacios
    transporte_array = [1, 2, 3, 4, 5]
    # Esto seran las arrays con los valores aleatorios que se asignaran a las tripletas(basados en los atributos de un alojamiento de la ontologia)
    array_nombres_Companias = ["EmpresaT1","EmpresaT2","EmpresaT3","EmpresaT4", "EmpresaT5"]
    array_precios = ["78", "94", "230", "44", "10"]
    array_datetimes = ["07/06/2017;10:00","11/06/2017;14:00"]
    array_aeropuertos = ["Aeroport del Prat", "Aeropuerto Madrd-Barajas", "Aeropuerto de Salamanca", "Aeropuerto de Castellon", "Aeropuerto de Mallorca"]
    index = 0
    gr = Graph()
    content = ECSDI['respuesta_de_transporte' + str(get_count())]
    gr.add((content, RDF.type, ECSDI.respuesta_de_transporte))

    for trans in transporte_array:
        # TODO: Mirar ontologia que se necesita para representar un alojamiento
        # TODO: Aqui crear los objetos necesarios
        transporte = ECSDI['transporte' + str(get_count())]
        compania = ECSDI['compania' + str(get_count())]
        sale_de = ECSDI['aeropuerto'+str(get_count())]
        llega_a = ECSDI['aeropuerto'+str(get_count())]

        # TODO: Por cada sub-objeto de actividad crear sus tripletas que lo representan
        # Compania
        gr.add((compania, RDF.type, ECSDI.compania))
        gr.add((compania, ECSDI.nombre, Literal(array_nombres_Companias[index])))

        # Llega a
        gr.add((llega_a, RDF.type, ECSDI.aeropuerto))
        gr.add((llega_a, ECSDI.nombre, Literal(array_aeropuertos[index%2])))

        # Sale_de
        gr.add((sale_de, RDF.type, ECSDI.aeropuerto))
        gr.add((sale_de, ECSDI.nombre, Literal(array_aeropuertos[2])))


        # TODO: Crear las tripletas propias del alojamiento y linkar los objetos creados anteriormente
        # Transporte
        gr.add((transporte, RDF.type, ECSDI.transporte))
        gr.add((transporte, ECSDI.llega_a, URIRef(llega_a)))
        gr.add((transporte, ECSDI.sale_de, URIRef(sale_de)))
        gr.add((transporte, ECSDI.coste, Literal(array_precios[index])))
        gr.add((transporte, ECSDI.es_ofrecido_por, URIRef(compania)))
        gr.add((transporte, ECSDI.llegada, Literal(array_datetimes[1])))
        gr.add((transporte, ECSDI.salida, Literal(array_datetimes[0])))
        gr.add((content, ECSDI.se_constituye_de_transportes, URIRef(transporte)))
        index += 1
    #Devolvemos el grafo
    logger.info('DEVOLVEMOS EL GRAFO')
    transporte = gr.value(subject=content, predicate=ECSDI.se_constituye_de_transportes)
    juaskas = gr.value(subject=transporte, predicate=ECSDI.llegada)
    logger.info(juaskas)
    return gr

@app.route("/comm")
def communication():
    """
    Communication Entrypoint
    """
    logger.info('Peticion de informacion recibida')
    global dsGraph

    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    gr = Graph()
    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(),
                           ACL['not-understood'],
                           sender=AgGestordeTransporte.uri,
                           msgcnt=get_count())
    else:
        # Obtenemos la performativa
        if msgdic['performative'] != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(),
                               ACL['not-understood'],
                               sender=DirectoryAgent.uri,
                               msgcnt=get_count())
        else:

            content = msgdic['content']
            # Averiguamos el tipo de la accion
            accion = gm.value(subject=content, predicate=RDF.type)

            if accion == ECSDI.peticion_de_transportes:

                # ciudades
                origen = gm.value(subject=content, predicate=ECSDI.tiene_como_origen)
                destino = gm.value(subject=content, predicate=ECSDI.tiene_como_destino)
                # valores
                ciudadOrigen = gm.value(subject=origen, predicate=ECSDI.nombre)
                ciudadDestino = gm.value(subject=destino, predicate=ECSDI.nombre)

                # fechas
                fechaIda = gm.value(subject=content, predicate=ECSDI.tiene_como_periodo_susceptible_de_ida)
                fechaVuelta = gm.value(subject=content, predicate=ECSDI.tiene_como_periodo_susceptible_de_vuelta)
                #valores
                inicioData = gm.value(subject=fechaIda, predicate=ECSDI.inicio)
                finData = gm.value(subject=fechaVuelta, predicate=ECSDI.fin)


                logger.info("Mensaje peticion de transportes")

                gr = buscar_transportes_externamente(ciudadOrigen, ciudadDestino, inicioData, finData)


                gr = build_message(gr,
                                   ACL['inform-'],
                                   sender=AgGestordeTransporte.uri,
                                   msgcnt=mss_cnt,
                                   receiver=msgdic['sender'])


            else:
                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=get_count())
    return gr

@app.route("/Stop")
def stop():
    """
    Entrypoint to the agent
    :return: string
    """

    tidyUp()
    shutdown_server()
    return "Stopping server"

def tidyUp():
    """
    Previous actions for the agent.
    """

    global queue
    queue.put(0)

    pass


def agent_behaviour(queue):
    """
    Agent Behaviour in a concurrent thread.
    :param queue: the queue
    :return: something
    """

    gr = register_message()



if __name__ == '__main__':
    # ------------------------------------------------------------------------------------------------------
    # Run behaviors
    ab1 = Process(target=agent_behaviour, args=(queue,))
    ab1.start()

    # Run server
    app.run(host=hostname, port=port, debug=True)

    # Wait behaviors
    ab1.join()
    print('The End')