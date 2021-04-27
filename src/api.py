from flask import Flask, request, jsonify
from logging.handlers import RotatingFileHandler
from time import strftime
import traceback
import logging

from powerplant import PowerPlant
from algo import Algo

app = Flask(__name__)


@app.route('/productionplan', endpoint='productionplan' , methods=["POST"])
def get_production_plan():
    """
        Endpoint of the REST API that accepts a POST with a payload as we can 
        find in the 'example_payloads' directory.
        
        Returns a JSON following the same structure as in 'example_response.json'
        with the optimal 'p' power for each powerplant to obtain the value of 'load'.
    """

    # Get informations from the payload
    load = request.json["load"]
    PowerPlant.wind_percent = request.json["fuels"]["wind(%)"]
    prices_per_MWh = {
        "gasfired": request.json["fuels"]["gas(euro/MWh)"],
        "turbojet": request.json["fuels"]["kerosine(euro/MWh)"],
        "windturbine": 0
    }

    # Instanciate powerplant objects
    powerplants = []
    for powerplant in request.json["powerplants"]:
        pp = PowerPlant.create_pp(**powerplant)
        pp.compute_cost_per_MWh(prices_per_MWh)
        powerplants.append(pp)

    # Calculate the unit-commitment
    algo = Algo(powerplants, load)
    unit_commitment = algo.calc_unit_commitment()

    if unit_commitment:
        return jsonify(unit_commitment)
    return "WARNING: There is no possible configuration for the requested load"


@app.after_request
def after_request(response):
    """ Logging after every request. """
    # This avoids the duplication of registry in the log,
    # since that 500 is already logged via @app.errorhandler.
    if response.status_code != 500:
        ts = strftime('[%Y-%b-%d %H:%M]')
        logger.error('%s %s %s %s %s %s',
                      ts,
                      request.remote_addr,
                      request.method,
                      request.scheme,
                      request.full_path,
                      response.status)
    return response

    
@app.errorhandler(Exception)
def exceptions(e):
    """ Logging after every Exception. """
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                  ts,
                  request.remote_addr,
                  request.method,
                  request.scheme,
                  request.full_path,
                  tb)
    return "Internal Server Error", 500


if __name__ == "__main__":
    handler = RotatingFileHandler('log/api.log', maxBytes=10000, backupCount=3)        
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)
    app.run("localhost", port="8888")
