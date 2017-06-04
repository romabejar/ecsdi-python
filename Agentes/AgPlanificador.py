# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent

Agent que implementa la interacció amb l'usuari


@author: bejar
"""
import random
from multiprocessing import Queue, Process
import sys
from AgentUtil.ACLMessages import get_agent_info, send_message, build_message, get_message_properties, register_agent
from AgentUtil.OntoNamespaces import ECSDI, ACL
import argparse
import socket
from multiprocessing import Process
from flask import Flask, render_template, request
from rdflib import Graph, Namespace, RDF, URIRef, Literal, XSD
from AgentUtil.Agent import Agent
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Logging import config_logger


__author__ = 'bejar'

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
    PlannerAgent = Agent('PlannerAgent',
                        agn.PlannerAgent,
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

    gr = register_agent(PlannerAgent, DirectoryAgent, PlannerAgent.uri, get_count())
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

    gr = None

    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=PlannerAgent.uri, msgcnt=get_count())
    else:
        # Obtenemos la performativa
        if msgdic['performative'] != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(),
                               ACL['not-understood'],
                               sender=DirectoryAgent.uri,
                               msgcnt=get_count())
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia
            # de registro
            content = msgdic['content']
            # Averiguamos el tipo de la accion
            accion = gm.value(subject=content, predicate=RDF.type)

            if accion == ECSDI.peticion_de_plan:
                # ciudad -> ciudOrg
                # ciudadOrigen -> ciudadOrigen
                
                ciudOrg = gm.value(subject=content, predicate=ECSDI.tiene_como_destino)
                ciudadOrigen = gm.value(subject=ciudOrg, predicate=ECSDI.nombre)

                ciudDes = gm.value(subject=content, predicate=ECSDI.tiene_como_destino)
                ciudadDestino = gm.value(subject=ciudDes, predicate=ECSDI.nombre)

                inicioData = gm.value(subject=content,predicate=ECSDI.data_de_ida)
                finData = gm.value(subject=content,predicate=ECSDI.data_de_vuelta)
                ponderacionLudica = gm.value(subject=content,predicate=ECSDI.ponderacion_de_actividades_ludicas)
                ponderacionCulturales = gm.value(subject=content, predicate=ECSDI.ponderacion_de_actividades_culturales)
                ponderacionFestivas = gm.value(subject=content, predicate=ECSDI.ponderacion_de_actividades_festivas)


                # TODO: Recoger todos los parametros necesarios
                # Fechas entrada, salida, ciudad origen, alguna restriccion de concreta

                # Creacion de los parametros
                restriccions_actividades = {}
                #restriccions_actividades['ciudadOrigenNombre']=ciudadOrigen
                restriccions_actividades['ciudadDestinoNombre']=ciudadDestino
                restriccions_actividades['inicioData']=inicioData
                restriccions_actividades['finData']=finData
                restriccions_actividades['ponderacionLudica']=ponderacionLudica
                restriccions_actividades['ponderacionCulturales']=ponderacionCulturales
                restriccions_actividades['ponderacionFestivas']=ponderacionFestivas
                restriccions_vuelos = {}
                restriccions_alojamientos = {}

                gr_actividades = buscar_actividades(**restriccions_actividades)
                # Llamada a la funcion que busca las actividades entre las fechas establecidas

                gr = gr_actividades #Esto es temporal, para que se devuelva el grafo de actividades y poder ver algo
                logger.info("Grafo respuesta de actividades recibido")

                # TODO: Llamar al agente de vuelos con el grafo correspondiente
                # gr_vuelos = buscar_transporte(**restriccions_vuelos)
                logger.info("Grafo respuesta de vuelos recibido")

                # TODO: Llamar al agente de alojamiento con el grafo correspondiente
                gr_alojamiento= buscar_alojamiento(**restriccions_alojamientos)
                logger.info("Grafo respuesta de alojamiento recibido")

                # TODO: Crear la funcion de criba y pasarle los datos
            else:
                gr = build_message(Graph(),
                               ACL['not-understood'],
                               sender=DirectoryAgent.uri,
                               msgcnt=get_count())




    logger.info('Respondemos a la peticion')

    serialize = gr.serialize(format='xml')
    return serialize, 200



def buscar_actividades():
    content = ECSDI['peticion_de_actividades' + str(get_count())]

    ciudad = ECSDI['ciudad' + str(get_count())]
    localizacion = ECSDI['localizacion' + str(get_count())]

    grafo = Graph()

    grafo.add((ciudad, ECSDI.nombre, Literal(ciudad)))
    grafo.add((localizacion, ECSDI.pertenece_a, URIRef(ciudad)))
    grafo.add((content, RDF.type, ECSDI.peticion_de_actividades))
    grafo.add((content,ECSDI.tiene_como_restriccion_de_localizacion, URIRef(localizacion)))

    agente_actividades = get_agent_info(agn.AgGestorActividades, DirectoryAgent, PlannerAgent, get_count())

    gr = send_message(build_message(grafo,perf=ACL.request, sender=PlannerAgent.uri, receiver=agente_actividades.uri,
                                  msgcnt=get_count(),
                                  content=content), agente_actividades.address)



    return gr

def buscar_transporte(ciudadNombre='Barcelona'):

    # Creamos el contenido
    content = ECSDI['peticion_de_alojamiento' + str(get_count())]

    # Creamos los objetos necesarios para las tripletas del grafo
    ciudad = ECSDI['ciudad' + str(get_count())]
    localizacion = ECSDI['localizacion' + str(get_count())]

    #Creamos el grafo con las tripletas
    grafo = Graph()
    grafo.add((ciudad, RDF.Type, ECSDI.ciudad))
    grafo.add((localizacion, RDF.Type, ECSDI.localizacion))
    grafo.add((ciudad, ECSDI.nombre, Literal(ciudadNombre)))
    grafo.add((localizacion, ECSDI.pertenece_a, URIRef(ciudad)))
    grafo.add((content, RDF.type, ECSDI.peticion_de_alojamiento))
    grafo.add((content, ECSDI.tiene_como_restriccion_de_localizacion, URIRef(localizacion)))

    #Preguntamos por el agente que necesitamos
    agente_alojamiento = get_agent_info(agn.AgGestorAlojamiento, DirectoryAgent, PlannerAgent, get_count())

    #Enviamos el mensaje
    gr = send_message(build_message(grafo, perf=ACL.request, sender=PlannerAgent.uri, receiver=agente_alojamiento.uri,
                                    msgcnt=get_count(),
                                    content=content), agente_alojamiento.address)

    #Retornamos el grafo respuesta del mensaje

    return gr


def buscar_alojamiento(ciudadNombre='Barcelona'):
    #creamos el contenido

    #creamos los objetos necesarios para las tripletas del grafo

    #Creamos el grafo con las tripletas

    #Preguntamos por el agente que necesitamos

    #Enviamos el mensaje

    #Retornamos el grafo respuesta del mensaje
    return 0

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