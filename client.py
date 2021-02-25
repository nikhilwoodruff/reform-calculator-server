import requests
import json

DATA = {
    "situation": {
        "people": {
            "p1": {
                "age": {2020: 25},
                "earnings": {2020: 35000},
                "income_tax": {2020: None},
                "NI": {2020: None}
            }
        }
    },
    "parameters": {
        "taxes/income_tax/allowances/personal_allowance/amount": 0
    }
}

print(json.loads(requests.post("http://localhost:5000/calculate", json=DATA).content))