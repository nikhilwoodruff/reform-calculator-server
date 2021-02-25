import flask
import json
import dpath
from openfisca_uk import CountryTaxBenefitSystem
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.indexed_enums import Enum
from openfisca_core import periods
from openfisca_core.model_api import Reform
from functools import reduce

app = flask.Flask(__name__)

def openfisca_calculate(tax_benefit_system, input_data):
    simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data)

    requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)
    computation_results = {}

    for computation in requested_computations:
        path = computation[0]
        entity_plural, entity_id, variable_name, period = path.split('/')
        variable = tax_benefit_system.get_variable(variable_name)
        result = simulation.calculate(variable_name, period)
        population = simulation.get_population(entity_plural)
        entity_index = population.get_index(entity_id)

        if variable.value_type == Enum:
            entity_result = result.decode()[entity_index].name
        elif variable.value_type == float:
            entity_result = float(str(result[entity_index]))  # To turn the float32 into a regular float without adding confusing extra decimals. There must be a better way.
        elif variable.value_type == str:
            entity_result = str(result[entity_index])
        else:
            entity_result = result.tolist()[entity_index]

        dpath.util.new(computation_results, path, entity_result)

    dpath.merge(input_data, computation_results)

    return input_data

@app.route("/calculate", methods=["POST"])
def calculate():
    situation = flask.request.json["situation"]
    system = CountryTaxBenefitSystem()
    if "parameters" in flask.request.json:
        params = flask.request.json["parameters"]
        def modify_params(parameters):
            for param in params:
                value = params[param]
                node = parameters
                for child in param.split("/"):
                    node = node.children[child]
                node.update(periods.period("2020-01-01"), value=value)
            return parameters
        class reform(Reform):
            def apply(self):
                self.modify_parameters(modifier_function=modify_params)
        system = reform(system)
    return flask.jsonify(openfisca_calculate(system, situation))

app.run()