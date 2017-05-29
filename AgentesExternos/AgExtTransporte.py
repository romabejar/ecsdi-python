__author__ = 'bejar'

from flask import Flask, request, Response
from flask.json import jsonify
import json
import argparse
import requests
from requests import ConnectionError
from multiprocessing import Process
from googleplaces import GooglePlaces, types, lang
import string
from skyscanner.skyscanner import Flights



# Definimos los parametros de la linea de comandos
parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost', help="Host del agente")
parser.add_argument('--port', type=int,  help="Puerto de comunicacion del agente")
parser.add_argument('--acomm', help='Direccion del agente con el que comunicarse')
parser.add_argument('--aport', type=int, help='Puerto del agente con el que comunicarse')
parser.add_argument('--messages', nargs='+', default=[], help="mensajes a enviar")

app = Flask(__name__)

@app.route("/")
def isAlive():
    text = 'Hi i\'m AgExtTransporte o/, if you wanna travel go to <a href= /flights?country=UK&currency=GBP&locale=en-GB&originplace=SIN-sky&destinationplace=KUL-sky&outbounddate=2017-05-28&inbounddate=2017-05-31&adults=1>here</a>'
    return text


@app.route("/flights")
def getFlights():
    """
        calls to /browsequotes/v1.0/{country}/{currency}/{locale}/{originPlace}/{destinationPlace}/{outboundPartialDate}/{inboundPartialDate}
        :return:
        """
    apikey = 'ec979327405027392857443412271857'
    country = request.args["country"]
    currency = request.args["currency"]
    locale = request.args["locale"]
    originplace = request.args["originplace"]
    destinationplace = request.args["destinationplace"]
    outbounddate = request.args["outbounddate"]
    inbounddate = request.args["inbounddate"]

    baseURL = 'http://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/'
    requestURL = country+'/'+currency+'/'+locale+'/'+originplace+'/'+destinationplace+'/'+outbounddate+'/'+inbounddate+'?apikey='+apikey
    print baseURL+requestURL
    r = requests.get(baseURL+requestURL)
    print r.status_code
    return r.text

if __name__ == '__main__':

    # parsing de los parametros de la linea de comandos
    args = parser.parse_args()

    # Ponemos en marcha el servidor
    app.run(host=args.host, port=args.port)

    print 'The End'