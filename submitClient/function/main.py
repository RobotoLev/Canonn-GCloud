from flask import current_app
from flask import request, jsonify
from flask_cors import CORS
from flask import Flask, g
import paramiko
from paramiko import RSAKey
from sshtunnel import SSHTunnelForwarder

import localpackage.dbutils
from localpackage.dbutils import setup_sql_conn
from localpackage.dbutils import get_cursor
from localpackage.dbutils import close_mysql
from paramiko import RSAKey
from sshtunnel import SSHTunnelForwarder
import functions_framework

import pymysql
import socket

import json
import requests
from math import sqrt
import logging
from os import getenv
import functions_framework
from functools import wraps
from flask import url_for
import uuid
import base64
import logging
import traceback


app = current_app
CORS(app)


app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

# get tunnel config from the environment
app.tunnel_config = {
    "host": getenv("TUNNEL_HOST", None),
    "keyfile": getenv("TUNNEL_KEY", None),
    "user": getenv("TUNNEL_USER", "tunneluser"),
    "local_port": int(getenv("MYSQL_PORT", "3308")),
    "remote_port": int(getenv("TUNNEL_PORT", "3306")),
}

# This should identify the instance so I can see if the crashed instance is being closed
app.canonn_cloud_id = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("utf-8")


def wrap_route(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # going to run the route and close down connections if it fails
        try:
            route_name = url_for(f.__name__, **kwargs)
            # Print route and instance id
            print(f"Route: {route_name} {app.canonn_cloud_id}")
            return f(*args, **kwargs)
        except Exception as e:
            # Log the error
            stack_trace = traceback.format_exc()
            logging.error(f"An error occurred: {str(e)}")
            logging.error(stack_trace)
            # close mysql
            close_mysql()
            return "I'm sorry Dave I'm afraid I can't do that", 500

    return decorated_function


@app.before_request
def before_request():
    setup_sql_conn()


def insertReport(request):
    cmdr = (request.get("cmdr"),)
    client = (request.get("client"),)
    if request.get("beta") == True:
        beta = "Y"
    else:
        beta = "N"
    if request.get("autoupdate") == True:
        autoupdate = "N"
    else:
        autoupdate = "Y"

    with get_cursor() as cursor:
        if request.get("date"):
            sql = """
            insert ignore into client_reports values (%s,%s,%s,%s,%s)
            """
            cursor.execute(
                sql, (cmdr, client, request.get("date"), autoupdate, beta)
            )
        else:
            sql = """
            insert ignore into client_reports values (%s,%s,date(now()),%s,%s)
            """
            cursor.execute(sql, (cmdr, client, autoupdate, beta))


@app.route("/", methods=["POST"])
@wrap_route
def root():
    print(json.dumps(request.json))
    insertReport(request.json)
    return json.dumps(request.json)


@functions_framework.http
def payload(request):

    return "404 not found", 404
