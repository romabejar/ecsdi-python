# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent

Agent que implementa la interacció amb l'usuari


@author: bejar
"""
import random

import sys
from AgentUtil.ACLMessages import get_agent_info, send_message, build_message, get_message_properties
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

# Flask stuff
app = Flask(__name__, template_folder='../Templates')

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente Administrativo
AdministrativeAgent = Agent('AdministrativeAgent',
                          agn.AdministrativeAgent,
                          'http://%s:%d/comm' % (hostname, port),
                          'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:%d/Register' % (dhostname, dport),
                       'http://%s:%d/Stop' % (dhostname, dport))


# Global dsgraph triplestore
dsgraph = Graph()

# Plan
plan_dia_list = []

# Plan viaje
plan_viaje = []

def get_count():
    global mss_cnt
    if not mss_cnt:
        mss_cnt = 0
    mss_cnt += 1
    return mss_cnt


# HTML contendra la informacion de preferencias y restricciones
# para el plan de viaje
@app.route("/")
def browser_root():
    return render_template('submitForm.html')

@app.route("/cerca", methods=['POST'])
def browser_cerca():
    """
    Permite la comunicacion con el agente 
    """
    logger.info("Enviando peticion de busqueda")

    # Content of the message
    contentResult = ECSDI['peticion_de_plan' + str(get_count())]

    # Graph creation
    gr = Graph()
    gr.add((contentResult, RDF.type, ECSDI.peticion_de_plan))

    # Obtenemos los datos del formulario, ciudad a visitar y fechas disponibles
    originCity = request.form.get('originCity')
    destinationCity = request.form.get('destinationCity')
    initDate = request.form.get('initDate')
    finDate = request.form.get('finDate')

    logger.info(originCity)
    if originCity:
        city = ECSDI['ciudad' + str(get_count())]
        gr.add((city, RDF.type, ECSDI.ciudad))
        gr.add((city, ECSDI.nombre, Literal(originCity, datatype=XSD.string)))
        # Add restriccio to content
        gr.add((contentResult, ECSDI.tiene_como_destino, URIRef(city)))

        # imprimimos el grafo
        logger.info(gr)

    planificador = get_agent_info(agn.PlannerAgent, DirectoryAgent, AdministrativeAgent,get_count())
    gresp = send_message(build_message(gr, perf=ACL.request, sender=AdministrativeAgent.uri, receiver=planificador.uri, msgcnt=get_count(),
                          content=contentResult), planificador.address)



    logger.info("Grafo respuesta")
    logger.info(gresp)
    print gresp
    activitats_matrix = []

    for item in gresp.subjects(RDF.type, ECSDI.actividad):
        logger.info(1)
        activitats = [gresp.value(subject=item, predicate=ECSDI.tipo_de_actividad)]
        activitats_matrix.append(activitats)

    return render_template('activities.html', actividades= activitats_matrix)


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion del agente
    """
    return "Hola"


def tidyup():
    """
    Acciones previas a parar el agente

    """
    pass


def agentbehavior1():
    """
    Un comportamiento del agente

    :return:
    """

if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1)
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port, debug=True)

    # Esperamos a que acaben los behaviors
    ab1.join()
    logger.info('The End')