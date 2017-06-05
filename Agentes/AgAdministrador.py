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
from SPARQLWrapper import SPARQLWrapper, JSON


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



def resultado_plan_de_viaje():
    logger.info("\n ***************** \n Plan harcodeado \n ***************** ")

    # rpv = repues_plan_de_viaje
    rpv = Graph()
    respuesta_plan = ECSDI['respuesta_de_plan' + str(get_count())]
    rpv.add((respuesta_plan,RDF.type, ECSDI.respuesta_de_plan))


    plan_viaje = ECSDI['plan_de_viaje' + str(get_count())]
    rpv.add((plan_viaje, RDF.type, ECSDI.plan_de_viaje))
    rpv.add((plan_viaje, ECSDI.identificador_de_plan, Literal("111222333")))
    rpv.add((respuesta_plan, ECSDI.tiene_como_plan_de_viaje, URIRef(plan_viaje)))

    # ******************************************************************************
    # Alojamiento

    alojamiento = ECSDI['alojamiento' + str(get_count())]
    rpv.add((alojamiento, RDF.type, ECSDI.alojamiento))
    rpv.add((alojamiento, ECSDI.coste, Literal('500.20')))
    rpv.add((plan_viaje, ECSDI.como_alojamiento_del_plan, URIRef(alojamiento)))

    alojamientoCompania = ECSDI['compania' + str(get_count())]
    rpv.add((alojamientoCompania, RDF.type, ECSDI.compania))
    rpv.add((alojamientoCompania,ECSDI.nombre, Literal("AlojamientoCompania")))
    rpv.add((alojamiento, ECSDI.es_ofrecido_por, URIRef(alojamientoCompania)))

    localizacionAlojamiento = ECSDI['localizacion' + str(get_count())]
    rpv.add((localizacionAlojamiento, RDF.type, ECSDI.localizacion))
    rpv.add((localizacionAlojamiento, ECSDI.direccion, Literal('DireccionAlojamiento')))
    rpv.add((alojamiento, ECSDI.se_encuentra_en, URIRef(localizacionAlojamiento)))

    ciudadAlojamiento = ECSDI['ciudad' + str(get_count())]
    rpv.add((ciudadAlojamiento, RDF.type, ECSDI.ciudad))
    rpv.add((ciudadAlojamiento, ECSDI.nombre, Literal('ciudadAlojamiento')))
    rpv.add((localizacionAlojamiento, ECSDI.pertenece_a, URIRef(ciudadAlojamiento)))

    paisAlojamiento = ECSDI['pais' + str(get_count())]
    rpv.add((paisAlojamiento, RDF.type, ECSDI.pais))
    rpv.add((paisAlojamiento, ECSDI.nombre, Literal('PaisAlojamiento')))
    rpv.add((ciudadAlojamiento, ECSDI.esta_en, URIRef(paisAlojamiento)))

    periodoAlojamiento = ECSDI['periodo' + str(get_count())]
    rpv.add((periodoAlojamiento, RDF.type, ECSDI.periodo))
    rpv.add((periodoAlojamiento, ECSDI.dia_de_la_semana, Literal('periodoAlojamiento')))
    rpv.add((periodoAlojamiento, ECSDI.inicio, Literal('inicioAlojamiento')))
    rpv.add((periodoAlojamiento, ECSDI.fin, Literal('finAlojamiento')))
    rpv.add((alojamiento, ECSDI.tiene_como_horario, URIRef(periodoAlojamiento)))

    # ******************************************************************************
    # Transporte Ida

    transporteIda = ECSDI['transporte' + str(get_count())]
    rpv.add((transporteIda, RDF.type, ECSDI.transporte))
    rpv.add((plan_viaje, ECSDI.como_transporte_de_ida, URIRef(transporteIda)))
    rpv.add((transporteIda, ECSDI.salida, Literal('10:00')))
    rpv.add((transporteIda, ECSDI.llegada, Literal('12:00')))
    rpv.add((transporteIda, ECSDI.coste, Literal('1000.20')))

    transporteCompania = ECSDI['compania' + str(get_count())]
    rpv.add((transporteCompania, RDF.type, ECSDI.compania))
    rpv.add((transporteCompania, ECSDI.nombre, Literal("TransporteCompaniaIda")))
    rpv.add((transporteIda, ECSDI.es_ofrecido_por, URIRef(transporteCompania)))

    # ¿?
    periodoTransporte = ECSDI['periodo' + str(get_count())]
    rpv.add((periodoTransporte, RDF.type, ECSDI.periodo))
    rpv.add((periodoTransporte, ECSDI.dia_de_la_semana, Literal('periodoTransporteIda')))
    rpv.add((periodoTransporte, ECSDI.inicio, Literal('inicioTransporteIda')))
    rpv.add((periodoTransporte, ECSDI.fin, Literal('finTransporteIda')))
    rpv.add((transporteIda, ECSDI.tiene_como_horario, URIRef(periodoTransporte)))

    salidaTransporte = ECSDI['aeropuerto' + str(get_count())]
    rpv.add((salidaTransporte, RDF.type, ECSDI.aeropuerto))
    rpv.add((salidaTransporte, ECSDI.nombre, Literal('Nombre_Salida_AeropuertoIda')))
    rpv.add((transporteIda, ECSDI.sale_de, URIRef(salidaTransporte)))

    localizacionSalidaT = ECSDI['localizacion' + str(get_count())]
    rpv.add((localizacionSalidaT, RDF.type, ECSDI.localizacion))
    rpv.add((localizacionSalidaT, ECSDI.direccion, Literal('LocalizacionSalidaTIda')))
    rpv.add((salidaTransporte, ECSDI.se_encuentra_en, URIRef(localizacionSalidaT)))

    ciudadSalidaT = ECSDI['ciudad' + str(get_count())]
    rpv.add((ciudadSalidaT, RDF.type, ECSDI.ciudad))
    rpv.add((ciudadSalidaT, ECSDI.nombre, Literal('ciudadSalidaTIda')))
    rpv.add((localizacionSalidaT, ECSDI.pertenece_a, URIRef(ciudadSalidaT)))

    paisSalidaT = ECSDI['pais' + str(get_count())]
    rpv.add((paisSalidaT, RDF.type, ECSDI.pais))
    rpv.add((paisSalidaT, ECSDI.nombre, Literal('PaisSalidaTIda')))
    rpv.add((ciudadSalidaT, ECSDI.esta_en, URIRef(paisSalidaT)))

    llegadaTransporte = ECSDI['aeropuerto' + str(get_count())]
    rpv.add((llegadaTransporte, RDF.type, ECSDI.aeropuerto))
    rpv.add((llegadaTransporte, ECSDI.nombre, Literal('Nombre_Llegada_AeropuertoIda')))
    rpv.add((transporteIda, ECSDI.llega_a, URIRef(llegadaTransporte)))

    localizacionLlegadaT = ECSDI['localizacion' + str(get_count())]
    rpv.add((localizacionLlegadaT, RDF.type, ECSDI.localizacion))
    rpv.add((localizacionLlegadaT, ECSDI.direccion, Literal('LocalizacionLlegadaTIda')))
    rpv.add((llegadaTransporte, ECSDI.se_encuentra_en, URIRef(localizacionLlegadaT)))

    ciudadLlegadaT = ECSDI['ciudad' + str(get_count())]
    rpv.add((ciudadLlegadaT, RDF.type, ECSDI.ciudad))
    rpv.add((ciudadLlegadaT, ECSDI.nombre, Literal('ciudadLlegadaTIda')))
    rpv.add((localizacionLlegadaT, ECSDI.pertenece_a, URIRef(ciudadLlegadaT)))

    paisLlegadaT = ECSDI['pais' + str(get_count())]
    rpv.add((paisLlegadaT, RDF.type, ECSDI.pais))
    rpv.add((paisLlegadaT, ECSDI.nombre, Literal('PaisLlegadaTIda')))
    rpv.add((ciudadLlegadaT, ECSDI.esta_en, URIRef(paisLlegadaT)))

    # ______________________________________________________________________________
    # Transporte Vuelta

    transporteVuelta = ECSDI['transporte' + str(get_count())]
    rpv.add((transporteVuelta, RDF.type, ECSDI.transporte))
    rpv.add((plan_viaje, ECSDI.como_transporte_de_vuelta, URIRef(transporteVuelta)))
    rpv.add((transporteVuelta, ECSDI.salida, Literal('21:15')))
    rpv.add((transporteVuelta, ECSDI.llegada, Literal('23:30')))
    rpv.add((transporteVuelta, ECSDI.coste, Literal('2000.00')))

    transporteCompania = ECSDI['compania' + str(get_count())]
    rpv.add((transporteCompania, RDF.type, ECSDI.compania))
    rpv.add((transporteCompania, ECSDI.nombre, Literal("TransporteCompaniaVuelta")))
    rpv.add((transporteVuelta, ECSDI.es_ofrecido_por, URIRef(transporteCompania)))

    periodoTransporte = ECSDI['periodo' + str(get_count())]
    rpv.add((periodoTransporte, RDF.type, ECSDI.periodo))
    rpv.add((periodoTransporte, ECSDI.dia_de_la_semana, Literal('periodoTransporteVuelta')))
    rpv.add((periodoTransporte, ECSDI.inicio, Literal('inicioTransporteVuelta')))
    rpv.add((periodoTransporte, ECSDI.fin, Literal('finTransporteVuelta')))
    rpv.add((transporteVuelta, ECSDI.tiene_como_horario, URIRef(periodoTransporte)))

    salidaTransporte = ECSDI['aeropuerto' + str(get_count())]
    rpv.add((salidaTransporte, RDF.type, ECSDI.aeropuerto))
    rpv.add((salidaTransporte, ECSDI.nombre, Literal('Nombre_Salida_Aeropuerto_Vuelta')))
    rpv.add((transporteVuelta, ECSDI.sale_de, URIRef(salidaTransporte)))

    localizacionSalidaT = ECSDI['localizacion' + str(get_count())]
    rpv.add((localizacionSalidaT, RDF.type, ECSDI.localizacion))
    rpv.add((localizacionSalidaT, ECSDI.direccion, Literal('LocalizacionSalidaTVuelta')))
    rpv.add((salidaTransporte, ECSDI.se_encuentra_en, URIRef(localizacionSalidaT)))

    ciudadSalidaT = ECSDI['ciudad' + str(get_count())]
    rpv.add((ciudadSalidaT, RDF.type, ECSDI.ciudad))
    rpv.add((ciudadSalidaT, ECSDI.nombre, Literal('ciudadSalidaTVuelta')))
    rpv.add((localizacionSalidaT, ECSDI.pertenece_a, URIRef(ciudadSalidaT)))

    paisSalidaT = ECSDI['pais' + str(get_count())]
    rpv.add((paisSalidaT, RDF.type, ECSDI.pais))
    rpv.add((paisSalidaT, ECSDI.nombre, Literal('PaisSalidaTVuelta')))
    rpv.add((ciudadSalidaT, ECSDI.esta_en, URIRef(paisSalidaT)))

    llegadaTransporte = ECSDI['aeropuerto' + str(get_count())]
    rpv.add((llegadaTransporte, RDF.type, ECSDI.aeropuerto))
    rpv.add((llegadaTransporte, ECSDI.nombre, Literal('Nombre_Llegada_Aeropuerto_Vuelta')))
    rpv.add((transporteVuelta, ECSDI.llega_a, URIRef(llegadaTransporte)))

    localizacionLlegadaT = ECSDI['localizacion' + str(get_count())]
    rpv.add((localizacionLlegadaT, RDF.type, ECSDI.localizacion))
    rpv.add((localizacionLlegadaT, ECSDI.direccion, Literal('LocalizacionLlegadaTVuelta')))
    rpv.add((llegadaTransporte, ECSDI.se_encuentra_en, URIRef(localizacionLlegadaT)))

    ciudadLlegadaT = ECSDI['ciudad' + str(get_count())]
    rpv.add((ciudadLlegadaT, RDF.type, ECSDI.ciudad))
    rpv.add((ciudadLlegadaT, ECSDI.nombre, Literal('ciudadLlegadaTVuelta')))
    rpv.add((localizacionLlegadaT, ECSDI.pertenece_a, URIRef(ciudadLlegadaT)))

    paisLlegadaT = ECSDI['pais' + str(get_count())]
    rpv.add((paisLlegadaT, RDF.type, ECSDI.pais))
    rpv.add((paisLlegadaT, ECSDI.nombre, Literal('PaisLlegadaTVuelta')))
    rpv.add((ciudadLlegadaT, ECSDI.esta_en, URIRef(paisLlegadaT)))



    # ******************************************************************************
    # Plan diario
    plan_dia = ECSDI['plan_de_un_dia' + str(get_count())]
    rpv.add((plan_dia, RDF.type, ECSDI.plan_de_un_dia))
    rpv.add((plan_dia, ECSDI.data, Literal('21/11/2017')))
    rpv.add((plan_viaje, ECSDI.tiene_para_cada_dia, URIRef(plan_viaje)))

    # **************************************************************
    # Actividad de manana

    actividadManana = ECSDI['actividad' + str(get_count())]
    rpv.add((actividadManana, RDF.type, ECSDI.actividad))
    rpv.add((actividadManana, ECSDI.coste, Literal('costeManana')))
    rpv.add((plan_dia, ECSDI.tiene_como_actividades_de_manana, URIRef(actividadManana)))

    periodoManana = ECSDI['periodo' + str(get_count())]
    rpv.add((periodoManana, RDF.type, ECSDI.periodo))
    rpv.add((periodoManana, ECSDI.dia_de_la_semana, Literal("Manana")))
    rpv.add((periodoManana, ECSDI.inicio, Literal("09:00")))
    rpv.add((periodoManana, ECSDI.fin, Literal("10:00")))
    rpv.add((actividadManana, ECSDI.tiene_como_horario, URIRef(periodoManana)))

    localizacionManana = ECSDI['localizacion' + str(get_count())]
    rpv.add((localizacionManana, RDF.type, ECSDI.localizacion))
    rpv.add((localizacionManana, ECSDI.direccion, Literal("Direccion actividadManana")))
    rpv.add((actividadManana, ECSDI.se_encuentra_en, URIRef(localizacionManana)))

    ciudadManana = ECSDI['ciudad' + str(get_count())]
    rpv.add((ciudadManana, RDF.type, ECSDI.ciudad))
    rpv.add((ciudadManana, ECSDI.nombre, Literal('ciudadManana')))
    rpv.add((localizacionManana, ECSDI.pertenece_a, URIRef(ciudadManana)))

    paisManana = ECSDI['pais' + str(get_count())]
    rpv.add((paisManana, RDF.type, ECSDI.pais))
    rpv.add((paisManana, ECSDI.nombre, Literal('PaisManana')))
    rpv.add((ciudadManana, ECSDI.esta_en, URIRef(paisManana)))

    companiaManana = ECSDI['compania' + str(get_count())]
    rpv.add((companiaManana, RDF.type, ECSDI.compania))
    rpv.add((companiaManana, ECSDI.nombre, Literal("Compania Manana")))
    rpv.add((actividadManana, ECSDI.es_ofrecido_por, URIRef(companiaManana)))

    # **************************************************************
    # Actividad de tarde

    actividadTarde = ECSDI['actividad' + str(get_count())]
    rpv.add((actividadTarde, RDF.type, ECSDI.actividad))
    rpv.add((actividadTarde, ECSDI.coste, Literal('costeTarde')))
    rpv.add((plan_dia, ECSDI.tiene_como_actividades_de_tarde, URIRef(actividadTarde)))

    localizacionTarde = ECSDI['localizacion' + str(get_count())]
    rpv.add((localizacionTarde, RDF.type, ECSDI.localizacion))
    rpv.add((localizacionTarde, ECSDI.direccion, Literal("Direccion actividadTarde")))
    rpv.add((actividadTarde, ECSDI.se_encuentra_en, URIRef(localizacionTarde)))

    companiaTarde = ECSDI['compania' + str(get_count())]
    rpv.add((companiaTarde, RDF.type, ECSDI.compania))
    rpv.add((companiaTarde, ECSDI.nombre, Literal("Compania Tarde")))
    rpv.add((actividadTarde, ECSDI.es_ofrecido_por, URIRef(companiaTarde)))

    periodoTarde = ECSDI['periodo' + str(get_count())]
    rpv.add((periodoTarde, RDF.type, ECSDI.periodo))
    rpv.add((periodoTarde, ECSDI.dia_de_la_semana, Literal("Tarde")))
    rpv.add((periodoTarde, ECSDI.inicio, Literal("15:00")))
    rpv.add((periodoTarde, ECSDI.fin, Literal("16:00")))
    rpv.add((actividadTarde, ECSDI.tiene_como_horario, URIRef(periodoTarde)))

    ciudadTarde = ECSDI['ciudad' + str(get_count())]
    rpv.add((ciudadTarde, RDF.type, ECSDI.ciudad))
    rpv.add((ciudadTarde, ECSDI.nombre, Literal('ciudadTarde')))
    rpv.add((localizacionTarde, ECSDI.pertenece_a, URIRef(ciudadTarde)))

    paisTarde = ECSDI['pais' + str(get_count())]
    rpv.add((paisTarde, RDF.type, ECSDI.pais))
    rpv.add((paisTarde, ECSDI.nombre, Literal('PaisTarde')))
    rpv.add((ciudadTarde, ECSDI.esta_en, URIRef(paisTarde)))

    # **************************************************************
    # Actividad de noche

    actividadNoche = ECSDI['actividad' + str(get_count())]
    rpv.add((actividadNoche, RDF.type, ECSDI.actividad))
    rpv.add((actividadNoche, ECSDI.coste, Literal('costeNoche')))
    rpv.add((plan_dia, ECSDI.tiene_como_actividades_de_noche, URIRef(actividadNoche)))

    localizacionNoche = ECSDI['localizacion' + str(get_count())]
    rpv.add((localizacionNoche, RDF.type, ECSDI.localizacion))
    rpv.add((localizacionNoche, ECSDI.direccion, Literal("Direccion actividadNoche")))
    rpv.add((actividadNoche, ECSDI.se_encuentra_en, URIRef(localizacionNoche)))

    companiaNoche = ECSDI['compania' + str(get_count())]
    rpv.add((companiaNoche, RDF.type, ECSDI.compania))
    rpv.add((companiaNoche, ECSDI.nombre, Literal("Compania Noche")))
    rpv.add((actividadNoche, ECSDI.es_ofrecido_por, URIRef(companiaNoche)))

    periodoNoche = ECSDI['periodo' + str(get_count())]
    rpv.add((periodoNoche, RDF.type, ECSDI.periodo))
    rpv.add((periodoNoche, ECSDI.dia_de_la_semana, Literal("Noche")))
    rpv.add((periodoNoche, ECSDI.inicio, Literal("21:00")))
    rpv.add((periodoNoche, ECSDI.fin, Literal("22:00")))
    rpv.add((actividadNoche, ECSDI.tiene_como_horario, URIRef(periodoNoche)))

    ciudadNoche = ECSDI['ciudad' + str(get_count())]
    rpv.add((ciudadNoche, RDF.type, ECSDI.ciudad))
    rpv.add((ciudadNoche, ECSDI.nombre, Literal('ciudadNoche')))
    rpv.add((localizacionNoche, ECSDI.pertenece_a, URIRef(ciudadNoche)))

    paisNoche = ECSDI['pais' + str(get_count())]
    rpv.add((paisNoche, RDF.type, ECSDI.pais))
    rpv.add((paisNoche, ECSDI.nombre, Literal('PaisNoche')))
    rpv.add((ciudadNoche, ECSDI.esta_en, URIRef(paisNoche)))

    return rpv

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
    pLudica = request.form.get('ponderacionLudica')
    pCultural = request.form.get('ponderacionCultural')
    pFestiva = request.form.get('ponderacionFestiva')

    if originCity:
        cityOrg = ECSDI['ciudad' + str(get_count())]
        gr.add((cityOrg, RDF.type, ECSDI.ciudad))
        gr.add((cityOrg, ECSDI.nombre, Literal(originCity, datatype=XSD.string)))
        # Add restriccio to content
        gr.add((contentResult, ECSDI.tiene_como_origen, URIRef(cityOrg)))

    # TODO: Ralizar para todos los parametros
    if destinationCity:
        cityDes = ECSDI['ciudad' + str(get_count())]
        gr.add((cityDes, RDF.type, ECSDI.ciudad))
        gr.add((cityDes, ECSDI.nombre, Literal(destinationCity, datatype=XSD.string)))
        # Add restriccio to content
        gr.add((contentResult, ECSDI.tiene_como_destino, URIRef(cityDes)))

    if initDate:
        initD = ECSDI['inicioIda' + str(get_count())]
        gr.add((initD, ECSDI.data_de_ida, Literal(initDate, datatype=XSD.string)))
        # Add restriccio to content
        gr.add((contentResult, ECSDI.data_de_ida, URIRef(initD)))

    if finDate:
        finD = ECSDI['finVuelta' + str(get_count())]
        gr.add((finD, ECSDI.data_de_vuelta, Literal(finD, datatype=XSD.string)))
        # Add restriccio to content
        gr.add((contentResult, ECSDI.data_de_vuelta, URIRef(finD)))

    if pLudica:
        ponL = ECSDI['ponL'+ str(get_count())]
        gr.add((ponL, ECSDI.ponderacion_de_actividades_ludicas, Literal(ponL, datatype=XSD.string)))
        # Add restriccio to content
        gr.add((contentResult, ECSDI.ponderacion_de_actividades_ludicas, URIRef(finD)))

    if pCultural:
        ponC = ECSDI['ponC' + str(get_count())]
        gr.add((ponC, ECSDI.ponderacion_de_actividades_culturales, Literal(ponC, datatype=XSD.string)))
        # Add restriccio to content
        gr.add((contentResult, ECSDI.ponderacion_de_actividades_culturales, URIRef(finD)))

    if pFestiva:
        ponF = ECSDI['ponF' + str(get_count())]
        gr.add((ponF, ECSDI.ponderacion_de_actividades_festivas, Literal(ponF, datatype=XSD.string)))
        # Add restriccio to content
        gr.add((contentResult, ECSDI.ponderacion_de_actividades_festivas, URIRef(finD)))

    planificador = get_agent_info(agn.PlannerAgent, DirectoryAgent, AdministrativeAgent,get_count())
    gresp = send_message(build_message(gr, perf=ACL.request, sender=AdministrativeAgent.uri, receiver=planificador.uri, msgcnt=get_count(),
                           content=contentResult), planificador.address)

    originCity = request.form.get('originCity')
    destinationCity = request.form.get('destinationCity')
    initDate = request.form.get('initDate')
    finDate = request.form.get('finDate')
    pLudica = request.form.get('ponderacionLudica')
    pCultural = request.form.get('ponderacionCultural')
    pFestiva = request.form.get('ponderacionFestiva')
    logger.info("\n################################################################################### \n")
    logger.info(originCity)
    logger.info(destinationCity)
    logger.info(initDate)
    logger.info(finDate)
    logger.info(pLudica)
    logger.info(pCultural)
    logger.info(pFestiva)
    logger.info("\n################################################################################### \n")

    # Obtenemos los datos del plan de viaje

    resp = resultado_plan_de_viaje()
    #resp = gresp

    identificador = []
    datos_alojamiento = []

    # Obtenemos los datos del alojamiento
    for planUri in resp.subjects(RDF.type, ECSDI.plan_de_viaje):
        identificador.append(resp.value(subject=planUri, predicate=ECSDI.identificador_de_plan))

        for alojUri in resp.subjects(RDF.type, ECSDI.alojamiento):

            for companiaSIdaUri in resp.objects(subject=alojUri, predicate=ECSDI.es_ofrecido_por):
                datos_alojamiento.append(resp.value(subject=companiaSIdaUri, predicate=ECSDI.nombre))

            for localizacionUri in resp.objects(subject=alojUri, predicate=ECSDI.se_encuentra_en):
                datos_alojamiento.append(resp.value(subject=localizacionUri, predicate=ECSDI.direccion))

                for ciudadUri in resp.objects(subject=localizacionUri, predicate=ECSDI.pertenece_a):
                    datos_alojamiento.append(resp.value(subject=ciudadUri, predicate=ECSDI.nombre))
                    for paisUri in resp.objects(subject=ciudadUri, predicate=ECSDI.esta_en):
                        datos_alojamiento.append(resp.value(subject=paisUri, predicate=ECSDI.nombre))

            for periodUri in resp.objects(subject=alojUri, predicate=ECSDI.tiene_como_horario):
                datos_alojamiento.append(resp.value(subject=periodUri, predicate=ECSDI.inicio))
                datos_alojamiento.append(resp.value(subject=periodUri, predicate=ECSDI.fin))

        datos_alojamiento.append(resp.value(subject=alojUri, predicate=ECSDI.coste))

    # Obtenemos los datos del transporte
    datos_transporte_ida = []
    for planUri in resp.subjects(RDF.type, ECSDI.plan_de_viaje):
        for transIdaUri in resp.objects(subject=planUri, predicate=ECSDI.como_transporte_de_ida):

            # Compania
            for companiaSIdaUri in resp.objects(subject=transIdaUri, predicate=ECSDI.es_ofrecido_por):
                datos_transporte_ida.append(resp.value(subject=companiaSIdaUri, predicate=ECSDI.nombre))

            # Salida
            datos_transporte_ida.append(resp.value(subject=transIdaUri, predicate=ECSDI.salida))
            for aeroSIdaUri in resp.objects(subject=transIdaUri, predicate=ECSDI.sale_de):
                datos_transporte_ida.append(resp.value(subject=aeroSIdaUri, predicate=ECSDI.nombre))
                for locaSIdaUri in resp.objects(subject=aeroSIdaUri, predicate=ECSDI.se_encuentra_en):
                    datos_transporte_ida.append(resp.value(subject=locaSIdaUri, predicate=ECSDI.direccion))
                    for ciudadSIdaUri in resp.objects(subject=locaSIdaUri, predicate=ECSDI.pertenece_a):
                        datos_transporte_ida.append(resp.value(subject=ciudadSIdaUri, predicate=ECSDI.nombre))
                        for paisSIdaUri in resp.objects(subject=ciudadSIdaUri, predicate=ECSDI.esta_en):
                            datos_transporte_ida.append(resp.value(subject=paisSIdaUri, predicate=ECSDI.nombre))

            # Llegada
            datos_transporte_ida.append(resp.value(subject=transIdaUri, predicate=ECSDI.llegada))
            for aeroLIdaUri in resp.objects(subject=transIdaUri, predicate=ECSDI.llega_a):
                datos_transporte_ida.append(resp.value(subject=aeroLIdaUri, predicate=ECSDI.nombre))
                for locLIdaUri in resp.objects(subject=aeroLIdaUri, predicate=ECSDI.se_encuentra_en):
                    datos_transporte_ida.append(resp.value(subject=locLIdaUri, predicate=ECSDI.direccion))
                    for ciudadLIdaUri in resp.objects(subject=locLIdaUri, predicate=ECSDI.pertenece_a):
                        datos_transporte_ida.append(resp.value(subject=ciudadLIdaUri, predicate=ECSDI.nombre))
                        for paisLIdaUri in resp.objects(subject=ciudadLIdaUri, predicate=ECSDI.esta_en):
                            datos_transporte_ida.append(resp.value(subject=paisLIdaUri, predicate=ECSDI.nombre))

            datos_transporte_ida.append(resp.value(subject=transIdaUri, predicate=ECSDI.coste))

    datos_transporte_vuelta = []
    for planUri in resp.subjects(RDF.type, ECSDI.plan_de_viaje):
        for transVueUri in resp.objects(subject=planUri, predicate=ECSDI.como_transporte_de_vuelta):

            # Compania
            for companiaSIdaUri in resp.objects(subject=transVueUri, predicate=ECSDI.es_ofrecido_por):
                datos_transporte_vuelta.append(resp.value(subject=companiaSIdaUri, predicate=ECSDI.nombre))

            # Salida
            datos_transporte_vuelta.append(resp.value(subject=transVueUri, predicate=ECSDI.salida))
            for aeroSVueUri in resp.objects(subject=transVueUri, predicate=ECSDI.sale_de):
                datos_transporte_vuelta.append(resp.value(subject=aeroSVueUri, predicate=ECSDI.nombre))
                for locaSVueUri in resp.objects(subject=aeroSVueUri, predicate=ECSDI.se_encuentra_en):
                    datos_transporte_vuelta.append(resp.value(subject=locaSVueUri, predicate=ECSDI.direccion))
                    for ciudadSVueUri in resp.objects(subject=locaSVueUri, predicate=ECSDI.pertenece_a):
                        datos_transporte_vuelta.append(resp.value(subject=ciudadSVueUri, predicate=ECSDI.nombre))
                        for paisSVueUri in resp.objects(subject=ciudadSVueUri, predicate=ECSDI.esta_en):
                            datos_transporte_vuelta.append(resp.value(subject=paisSVueUri, predicate=ECSDI.nombre))

            # Llegada
            datos_transporte_vuelta.append(resp.value(subject=transVueUri, predicate=ECSDI.llegada))
            for aeroLVueUri in resp.objects(subject=transVueUri, predicate=ECSDI.llega_a):
                datos_transporte_vuelta.append(resp.value(subject=aeroLVueUri, predicate=ECSDI.nombre))
                for locaLVueUri in resp.objects(subject=aeroLVueUri, predicate=ECSDI.se_encuentra_en):
                    datos_transporte_vuelta.append(resp.value(subject=locaLVueUri, predicate=ECSDI.direccion))
                    for ciudadLVueUri in resp.objects(subject=locaLVueUri, predicate=ECSDI.pertenece_a):
                        datos_transporte_vuelta.append(resp.value(subject=ciudadLVueUri, predicate=ECSDI.nombre))
                        for paisLVueUri in resp.objects(subject=ciudadLVueUri, predicate=ECSDI.esta_en):
                            datos_transporte_vuelta.append(resp.value(subject=paisLVueUri, predicate=ECSDI.nombre))

            datos_transporte_vuelta.append(resp.value(subject=transVueUri, predicate=ECSDI.coste))

    # Obtenemos los datos del plan dia. Lista de actividades
    datos_plan_dia = []
    for planDiaUri in resp.subjects(RDF.type, ECSDI.plan_de_un_dia):

        # Actividades de manana
        actividades_manana = []
        actividades_manana.append(resp.value(subject=planDiaUri, predicate=ECSDI.data))

        for actividadMananaUri in resp.objects(subject=planDiaUri, predicate=ECSDI.tiene_como_actividades_de_manana):

            for periodActMananaUri in resp.objects(subject=actividadMananaUri, predicate=ECSDI.tiene_como_horario):
                actividades_manana.append(resp.value(subject=periodActMananaUri, predicate=ECSDI.inicio))
                actividades_manana.append(resp.value(subject=periodActMananaUri, predicate=ECSDI.fin))

            for locActMananaUri in resp.objects(subject=actividadMananaUri, predicate=ECSDI.se_encuentra_en):
                actividades_manana.append(resp.value(subject=locActMananaUri, predicate=ECSDI.direccion))
                for ciudActMananaUri in resp.objects(subject=locActMananaUri, predicate=ECSDI.pertenece_a):
                    actividades_manana.append(resp.value(subject=ciudActMananaUri, predicate=ECSDI.nombre))
                    for paisActMananaUri in resp.objects(subject=ciudActMananaUri, predicate=ECSDI.esta_en):
                        actividades_manana.append(resp.value(subject=paisActMananaUri, predicate=ECSDI.nombre))

            for compActMananaUri in resp.objects(subject=actividadMananaUri, predicate=ECSDI.es_ofrecido_por):
                actividades_manana.append(resp.value(subject=compActMananaUri, predicate=ECSDI.nombre))

            actividades_manana.append(resp.value(subject=actividadMananaUri, predicate=ECSDI.coste))

        datos_plan_dia.append(actividades_manana)

        # Actividades de tarde
        actividades_tarde = []
        actividades_tarde.append(resp.value(subject=planDiaUri, predicate=ECSDI.data))

        for actividadTardeUri in resp.objects(subject=planDiaUri, predicate=ECSDI.tiene_como_actividades_de_tarde):

            for periodActTardeUri in resp.objects(subject=actividadTardeUri, predicate=ECSDI.tiene_como_horario):
                actividades_tarde.append(resp.value(subject=periodActTardeUri, predicate=ECSDI.inicio))
                actividades_tarde.append(resp.value(subject=periodActTardeUri, predicate=ECSDI.fin))

            for locActTardeUri in resp.objects(subject=actividadTardeUri, predicate=ECSDI.se_encuentra_en):
                actividades_tarde.append(resp.value(subject=locActTardeUri, predicate=ECSDI.direccion))
                for ciudActTardeUri in resp.objects(subject=locActTardeUri, predicate=ECSDI.pertenece_a):
                    actividades_tarde.append(resp.value(subject=ciudActTardeUri, predicate=ECSDI.nombre))
                    for paisActTardeUri in resp.objects(subject=ciudActTardeUri, predicate=ECSDI.esta_en):
                        actividades_tarde.append(resp.value(subject=paisActTardeUri, predicate=ECSDI.nombre))

            for compActTardeUri in resp.objects(subject=actividadTardeUri, predicate=ECSDI.es_ofrecido_por):
                actividades_tarde.append(resp.value(subject=compActTardeUri, predicate=ECSDI.nombre))

            actividades_tarde.append(resp.value(subject=actividadTardeUri, predicate=ECSDI.coste))

        datos_plan_dia.append(actividades_tarde)

        # Actividade de noche
        actividades_noche = []
        actividades_noche.append(resp.value(subject=planDiaUri, predicate=ECSDI.data))

        for actividadNocheUri in resp.objects(subject=planDiaUri, predicate=ECSDI.tiene_como_actividades_de_noche):

            for periodActNocheUri in resp.objects(subject=actividadNocheUri, predicate=ECSDI.tiene_como_horario):
                actividades_noche.append(resp.value(subject=periodActNocheUri, predicate=ECSDI.inicio))
                actividades_noche.append(resp.value(subject=periodActNocheUri, predicate=ECSDI.fin))

            for locActNocheUri in resp.objects(subject=actividadNocheUri, predicate=ECSDI.se_encuentra_en):
                actividades_noche.append(resp.value(subject=locActNocheUri, predicate=ECSDI.direccion))
                for ciudActNocheUri in resp.objects(subject=locActNocheUri, predicate=ECSDI.pertenece_a):
                    actividades_noche.append(resp.value(subject=ciudActNocheUri, predicate=ECSDI.nombre))
                    for paisActNocheUri in resp.objects(subject=ciudActNocheUri, predicate=ECSDI.esta_en):
                        actividades_noche.append(resp.value(subject=paisActNocheUri, predicate=ECSDI.nombre))

            for compActNocheUri in resp.objects(subject=actividadNocheUri, predicate=ECSDI.es_ofrecido_por):
                actividades_noche.append(resp.value(subject=compActNocheUri, predicate=ECSDI.nombre))

            actividades_noche.append(resp.value(subject=actividadNocheUri, predicate=ECSDI.coste))

        datos_plan_dia.append(actividades_noche)

    return render_template('activities.html', identificador=identificador, datos_alojamiento=datos_alojamiento,
                           datos_transporte_ida=datos_transporte_ida, datos_transporte_vuelta=datos_transporte_vuelta,
                           datos_plan_dia=datos_plan_dia)


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