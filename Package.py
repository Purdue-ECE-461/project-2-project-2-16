from flask import Flask, request
from ApplicationService import *
from google.cloud import storage
#from your_orm import Model, Column, Integer, String, DateTime
import sys

app = Flask(__name__)

@app.route("/package/<id>")
def getPackage(id):
        storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
        bucketName = os.getenv("BUCKET_NAME")
        bucket = storageClient.bucket(bucketName)
        fileToCheck = bucket.blob(id + ".zip")
        
        if (fileToCheck.exists()):
            return {'metadata': {"Name": id + ".zip", "Version": "1.0.0", "ID": id}}, 200
        else:
            return {'metadata': "None"}, 400

@app.route("/package/<id>", methods=['PUT'])
def putPackage(id):
    pass

@app.route("/package/<id>", methods=['DELETE'])
def delPackageVers(id):
    pass

@app.route("/package/<id>/rate", methods=["GET"])
def ratePackage(id):
    pass

@app.route("/package/byName/<name>", methods=['GET'])
def getPackageByName(name):
    pass

@app.route("/package/byName/<name>", methods=['DELETE'])
def delAllPackageVers(name):
    pass

@app.route("/package", methods=['POST'])
def createPackage():
    pass

@app.route("/packages", methods=['POST'])
def listPackages():
    offset = request.args.get('offset')
    return {'offset': {"offsetAct": offset}}
    
if __name__ == '__main__':
    app.run(debug=True)


