# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent

Agent que implementa la interacció amb l'usuari


@author: bejar
"""

import argparse
import os.path
import socket
from multiprocessing import Process
from multiprocessing import Queue

from flask import Flask, request
from rdflib import Graph, Namespace, RDF, URIRef, Literal

from AgentUtil.ACLMessages import build_message, get_message_properties, register_agent
from AgentUtil.Agent import Agent
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Logging import config_logger
from AgentUtil.OntoNamespaces import ECSDI, ACL

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
    AgGestorAlojamiento = Agent('AgGestorAlojamiento',
                        agn.AgGestorAlojamiento,
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

    gr = register_agent(AgGestorAlojamiento, DirectoryAgent, AgGestorAlojamiento.uri, get_count())
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

    gr = Graph

    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=AgGestorAlojamiento.uri, msgcnt=get_count())
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

            if accion == ECSDI.peticion_de_alojamiento:

                # TODO: Check parametros ontologia
                # Peticion de alojamiento tiene
                # radio_de_restriccion_de_localizacion_en_km (float)
                # tiene_como_restriccion_de_localizacion (localizacion)

                # Localizacion
                # direccion (string)
                # pertenece_a (ciudad)

                # Ciudad
                # esta_en (Pais)
                # nombre (string)

                # Pais
                # nombre (string)
                localizacion = gm.value(subject=content, predicate=ECSDI.tiene_como_restriccion_de_localizacion)
                ciudad = gm.value(subject=localizacion, predicate=ECSDI.pertenece_a)
                nombreCiudad = gm.value(subject=ciudad, predicate=ECSDI.nombre)

                estaEnCache = False
                if os.path.exists('../data/alojamientos-'+str(nombreCiudad)):
                    estaEnCache = True

                # Cache
                if estaEnCache:
                    logger.info("Estaba en cache")
                    cacheGraph = open('../data/alojamientos-'+str(nombreCiudad))
                    gr = Graph()
                    gr.parse(cacheGraph, format='turtle')

                else:
                    # Anadir mas parametros
                    restriccions_alojamiento = {}
                    restriccions_alojamiento['ciudadNombre'] = nombreCiudad


                    logger.info("Mensaje peticion de alojamiento")

                    gr = buscar_alojamientos_externamente(**restriccions_alojamiento)


                gr.serialize(destination='../data/alojamientos-'+str(nombreCiudad), format='turtle')

                gr = build_message(gr,
                                   ACL['inform-'],
                                   sender=AgGestorAlojamiento.uri,
                                   msgcnt=mss_cnt,
                                   receiver=msgdic['sender'])


            else:
                gr = build_message(Graph(),
                                   ACL['not-understood'],
                                   sender=DirectoryAgent.uri,
                                   msgcnt=get_count())

    serialize = gr.serialize(format='xml')
    return serialize, 200

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



def buscar_alojamientos_externamente(ciudadNombre):

    # Creamos un array con cuatro alojamientos vacios
    alojamiento_array = [1, 2, 3, 4, 5]

    # Alojamiento
    # se_encuentra_en (localizacion)
    # coste
    # es_ofrecido_por(compañia)
    # tiene_como_horario(periodo)


    # Compania
    # nombre (string)

    # Periodo
    # dia_de_la_semana (string)
    # inicio (datetime)
    # fin    (datetime)

    # Esto seran las arrays con los valores aleatorios que se asignaran a las tripletas(basados en los atributos de un alojamiento de la ontologia)
    array_nombres_Companias = ["NH Hoteles","Hotel Maria","Hotel Carlos III","Hostal Pedro", "Hotel Buenavista"]
    array_precios = ["87", "65", "72", "77", "102"]
    array_dias_semana = ["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"]
    array_datetimes = ["07/06/2017","11/06/2017"]
    array_direcciones = ["Diagonal 54", "Aragon 23", "Plaza España", "Pablo Neruda 12", "Avenida del Canal 3"]

    index = 0
    gr = Graph()
    # TODO: Check onotologia this is right
    # Grafo donde retornaremos el resultado
    # Respuesta de alojamietno
    # se_constituye_de_alojamientos (alojamientos)
    content = ECSDI['respuesta_de_alojamiento' + str(get_count())]
    gr.add((content, RDF.type, ECSDI.respuesta_de_alojamiento))

    for alojamiento in alojamiento_array:
        # TODO: Mirar ontologia que se necesita para representar un alojamiento
        # TODO: Aqui crear los objetos necesarios
        alojamiento = ECSDI['alojamiento' + str(get_count())]
        compania = ECSDI['compania' + str(get_count())]
        periodo = ECSDI['periodo' + str(get_count())]
        localizacion = ECSDI['localizacion'+str(get_count())]
        ciudad_obj = ECSDI['ciudad'+str(get_count())]

        # TODO: Por cada sub-objeto de actividad crear sus tripletas que lo representan
        # Compania
        # print index
        gr.add((compania, RDF.type, ECSDI.compania))
        gr.add((compania, ECSDI.nombre, Literal(array_nombres_Companias[index])))

        # Periodo
        gr.add((periodo, RDF.type, ECSDI.periodo))
        gr.add((periodo, ECSDI.dia_de_la_semana, Literal(array_dias_semana[2])))
        gr.add((periodo, ECSDI.inicio, Literal(array_datetimes[0])))
        gr.add((periodo, ECSDI.fin, Literal(array_datetimes[1])))

        #Ciudad
        gr.add((ciudad_obj, RDF.type, ECSDI.ciudad))
        gr.add((ciudad_obj, ECSDI.nombre, Literal(ciudadNombre)))

        # Localizacion
        gr.add((localizacion, RDF.type, ECSDI.localizacion))
        gr.add((localizacion, ECSDI.direccion, Literal(array_direcciones[index])))
        gr.add((localizacion, ECSDI.pertenece_a, URIRef(ciudad_obj)))


        # TODO: Crear las tripletas propias del alojamiento y linkar los objetos creados anteriormente
        # Actividad
        gr.add((alojamiento, RDF.type, ECSDI.alojamiento))
        gr.add((alojamiento, ECSDI.se_encuentra_en, URIRef(localizacion)))
        gr.add((alojamiento, ECSDI.coste, Literal(array_precios[index])))
        gr.add((alojamiento, ECSDI.es_ofrecido_por, URIRef(compania)))
        gr.add((alojamiento, ECSDI.tiene_como_horario, URIRef(periodo)))
        gr.add((content, ECSDI.se_construye_de_alojamientos, URIRef(alojamiento)))
        index += 1
    #Devolvemos el grafo
    return gr

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