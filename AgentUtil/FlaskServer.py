# -*- coding: utf-8 -*-
"""
File: AgentUtil
Diferentes funciones comunes a los agentes implementados en ECSDI
"""

__author__ = 'jara'

from flask import request


def shutdown_server():
    """
    Funcion que para el servidor web
    :raise RuntimeError:
    """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()