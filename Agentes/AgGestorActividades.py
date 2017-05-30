# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent

Agent que implementa la interacció amb l'usuari


@author: bejar
"""
import random

import json
import pprint
import argparse
from multiprocessing import Queue, Process
import sys
from AgentUtil.ACLMessages import get_agent_info, send_message, build_message, get_message_properties, register_agent
from AgentUtil.OntoNamespaces import ECSDI, ACL
from googleplaces import GooglePlaces
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
    AgGestorActividades = Agent('AgGestorActividades',
                        agn.AgGestorActividades,
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

    gr = register_agent(AgGestorActividades, DirectoryAgent, AgGestorActividades.uri, get_count())
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
        gr = build_message(Graph(), ACL['not-understood'], sender=AgGestorActividades.uri, msgcnt=get_count())
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

            if accion == ECSDI.peticion_de_actividades:

                localizacion = gm.value(subject=content, predicate=ECSDI.tiene_como_restriccion_de_localizacion)
                ciudad = gm.value(subject=localizacion, predicate=ECSDI.pertenece_a)
                miciudad = gm.value(subject=ciudad, predicate=ECSDI.nombre)

                logger.info('Lo he hecho bien')
                logger.info(miciudad)
                estaEnCache = False
                # Cache
                if estaEnCache:
                    return True
                else:
                    # Anadir mas parametros
                    restriccions_ciudad = {}
                    restriccions_ciudad['ciudadNombre='] = miciudad
                    #buscar_actividades(**restriccions_ciudad)

                    logger.info("Mensaje peticionn de plan")
                    logger.info(miciudad)

                    json_data = buscar_actividades_externamente("Barcelona", "Spain", 20000)
                    gr = Graph()

                    # Grafo donde retornaremos el resultado
                    # Hago bind de las ontologias que usaremos en el grafo

                    # gr.bind('myns_act', myns_act)
                    # gr.bind('myns_atr', myns_atr)
                    # gr.bind('myns_loc', myns_loc)
                    # gr.bind('myns_periodo', myns_periodo)
                    # gr.bind('myns_compania', myns_compania)


                    content = ECSDI['respuesta_de_actividades' + str(get_count())]
                    data_dict = json.loads(json_data)
                    index = 0
                    for place in data_dict:
                        index += 1
                        print place
                        act_obj = ECSDI['activity' + str(get_count())]
                        loc_obj = ECSDI['location' + str(get_count())]
                        periodo = ECSDI['period' + str(get_count())]
                        compania = ECSDI['company' + str(get_count())]

                        # Localizacion
                        gr.add((loc_obj, RDF.type, ECSDI.localizacion))
                        # gr.add((loc_obj, ECSDI.longitud, place.lat))  # Parsear de la llamada a la api
                        # gr.add((loc_obj, ECSDI.latitud, place.lng))  # Parsear de la llamada a la api

                        gr.add((loc_obj, ECSDI.longitud, Literal("41.39")))  # Parsear de la llamada a la api
                        gr.add((loc_obj, ECSDI.latitud, Literal("2.14")))  # Parsear de la llamada a la api

                        # Periodo
                        gr.add((periodo, RDF.type, ECSDI.periodo))
                        gr.add((periodo, ECSDI.inicio, Literal("11:00")))
                        gr.add((periodo, ECSDI.fin, Literal("12:50")))

                        # Compania
                        gr.add((compania, RDF.type, ECSDI.compania))
                        gr.add((compania, ECSDI.nombre, Literal("Roman Airlines")))
                        gr.add((compania, ECSDI.ofrece, URIRef(act_obj)))

                        # Actividad
                        gr.add((act_obj, RDF.type, ECSDI.activiad))
                        gr.add((act_obj, ECSDI.coste, Literal("15")))
                        gr.add((act_obj, ECSDI.se_encuentra_en, loc_obj))
                        gr.add((act_obj, ECSDI.tipo_de_actividad, Literal("Fiesta")))
                        gr.add((act_obj, ECSDI.tiene_como_horario, URIRef(periodo)))
                        gr.add((act_obj, ECSDI.es_ofrecido_por, URIRef(compania)))
                        gr.add((content, ECSDI.se_construye_de_actividades, URIRef(act_obj)))

                print index
                gr.serialize(destination='../data/compres', format='turtle')

                gr = build_message(gr,
                                   ACL['inform-'],
                                   sender=AgGestorActividades.uri,
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



def buscar_actividades_externamente(destinationCity="Barcelona", destinationCountry="Spain", radius=20000):
    logger.info(2)

    YOUR_API_KEY = 'AIzaSyCyjudYWWbnReJa3LdTgfnQXgLxIyXvLSk'
    google_places = GooglePlaces(YOUR_API_KEY)


    location = destinationCity + ", " + destinationCountry
    keyword = "Discoteca"
    type = "night_club"


    # You may prefer to use the text_search API, instead.
    query_result = google_places.nearby_search(
        location=location, keyword=keyword,
        radius=radius, types=type)
    # placestring = "Name: %s, GeoLoc: %s, Reference: %s, Phone: %s \n"(places[0].name, places[0].geo_location, places[0].reference, places[0].local_phone_number)

    resultado = {}
    i = 0
    for place in query_result.places:
        place_json = {}
        # Returned places from a query are place summaries.
        # print place.name
        # print place.geo_location
        # print place.reference
        place.get_details()
        place_json['name'] = place.name
        place_json['lat'] = float(place.geo_location['lat'])
        place_json['lng'] = float(place.geo_location['lng'])
        # place_json['reference'] = place.reference
        # place_json['details'] = place.details
        # The following method has to make a further API call.
        # Referencing any of the attributes below, prior to making a call to
        # get_details() will raise a googleplaces.GooglePlacesAttributeError.
        # print place.details # A dict matching the JSON response from Google.
        # print place.local_phone_number
        # print place.international_phone_number
        # print place.website
        # print place.url
        resultado[i] = place_json
        i = i + 1

    json_data = json.dumps(resultado)
    return json_data

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