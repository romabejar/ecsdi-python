"""
API KEY GOOGLE PLACES = AIzaSyCyjudYWWbnReJa3LdTgfnQXgLxIyXvLSk
"""
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

# Definimos los parametros de la linea de comandos
parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost', help="Host del agente")
parser.add_argument('--port', type=int, help="Puerto de comunicacion del agente")
parser.add_argument('--acomm', help='Direccion del agente con el que comunicarse')
parser.add_argument('--aport', type=int, help='Puerto del agente con el que comunicarse')
parser.add_argument('--messages', nargs='+', default=[], help="mensajes a enviar")

app = Flask(__name__)

@app.route("/")
def isAlive():
    text = 'Hi i\'m AgExtActividades o/, if you wanna party go to <a href= /place?location=Barcelona,%20Spain&keyword=Discoteca&type=night_club>here</a>'
    return text


@app.route("/place")
def getPlaces():
    """
    /place?location=loc&keyword=key&type=type
    :return:
    """

if __name__ == '__main__':

    # parsing de los parametros de la linea de comandos
    args = parser.parse_args()

    # Ponemos en marcha el servidor
    app.run(host=args.host, port=args.port)

    print 'The End'