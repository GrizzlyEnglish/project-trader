import json

def load_symbol_parameters(fileName = "params.json"):
    with open(fileName, "r") as jsonfile:
        data = json.load(jsonfile)

    return data