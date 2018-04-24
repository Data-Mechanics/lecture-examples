from tqdm import tqdm
import json
import jsonschema
from flask import Flask, jsonify, abort, make_response, request
import pymongo

nations = json.load(open("nations.json"))["nations"]

def interpolateData(year):
    return [{
        "name": d["name"],
        "region": d["region"],
        "income": interpolateValues(d["income"], year),
        "population": interpolateValues(d["population"], year),
        "lifeExpectancy": interpolateValues(d["lifeExpectancy"], year)
      } for d in nations]

def interpolateValues(values, year):
    ys = [y for (y,v) in values if y >= year]
    i = [y for (y,v) in values].index(ys[0])
    year_next = values[i][0]
    data_next = values[i][1]
    if i == 0:
        return data_next;
    elif i > 0:
        year_prev = values[i-1][0]
        data_prev = values[i-1][1]
        a = (year - year_next) / (year_prev - year_next)
        return data_next*(1-a) + data_prev*a

print("Populating database...")
client = pymongo.MongoClient()
db = client.local
db.nations.remove({})
for year in tqdm(range(1800,2006)):
    db.nations.insert({"_id": year, "data": interpolateData(year)})
    
app = Flask(__name__)

def get_client():
    return open('nations.html','r').read()

@app.route('/nations.js', methods=['GET'])
def get_nations():
    return open('nations.js','r').read()

@app.route('/year/<int:year>', methods=['GET'])
def get_year(year):
    for result in db.nations.find({"_id":year}):
        return jsonify(result["data"])

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found.'}), 404)

if __name__ == '__main__':
    app.run(debug=True)
