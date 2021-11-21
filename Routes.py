from flask import Flask, request
from ApplicationService import *
from google.cloud import storage
#from your_orm import Model, Column, Integer, String, DateTime
import sys

app = Flask(__name__)

history = dict() # maps String id to [(name, version, id),...]

appService = ApplicationService()

    
def checkIfFileExists(id):
    storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
    bucketName = os.getenv("BUCKET_NAME")
    bucket = storageClient.bucket(bucketName)
    fileToCheck = bucket.blob(id + ".zip")

    return fileToCheck.exists()

@app.route("/package/<id>")
def getPackage(id):
        if (checkIfFileExists(id)):
            return {'metadata': {"Name": id + ".zip", "Version": "1.0.0", "ID": id}}, 200
        else:
            return {'metadata': "None"}, 400

@app.route("/package/<id>", methods=['PUT'])
def putPackage(id):
    data = request.get_data()
    if (checkIfFileExists(id)):
        #update hist dict with new data
        pass

    return data

@app.route("/package/<id>", methods=['DELETE'])
def delPackageVers(id):
    if (checkIfFileExists(id)):
        history[id][1] -= 1
        if history[id][1] <= 0:
            history.pop(id)
    
    pass

@app.route("/package/<id>/rate", methods=["GET"])
def ratePackage(id):
    # transform id to github url/filename
    res = appService.rate() # rate the file from id
    pass

@app.route("/package/byName/<name>", methods=['GET'])
def getPackageByName(name):
    jsonOut = dict()
    for x in history:
        if history[x][0][0] == name:
            for x in history[x]:
                # return all versions
                pass
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
    # need to check what happens if offset isn't provided
    return {'offset': {"offsetAct": offset}}



if __name__ == '__main__':
    app.run(debug=True)


