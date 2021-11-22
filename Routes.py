from flask import Flask, request
from ApplicationService import *
from google.cloud import storage
#from your_orm import Model, Column, Integer, String, DateTime
import sys
import zipfile
import io

app = Flask(__name__)

history = dict() # maps String id to [{name, version, id},...]

appService = ApplicationService()

    
def checkIfFileExists(id):
    storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
    bucketName = os.getenv("BUCKET_NAME")
    bucket = storageClient.bucket(bucketName)
    fileToCheck = bucket.blob(id)

    return fileToCheck.exists()

@app.route("/package/<id>")
def getPackage(id):
    try:
        if (checkIfFileExists(id)):
            return {'metadata': {"Name": history[id][-1]["Name"], "Version": history[id][-1]["Version"], "ID": id}, "data": {"Content": "Stuff"}}, 200
        else:
            return {'code': -1, 'message': "An error occurred while retrieving package"}, 500
    except:
        return {'code': -1, 'message': "An error occurred while retrieving package"}, 500

@app.route("/package/<id>", methods=['PUT'])
def putPackage(id):
    try:
        res = request.get_json(force=True)
        if (checkIfFileExists(id)):
            #update hist dict with new data
            history[id].append({"Name": res["Data"]["metadata"]["Name"], "ID": res["Data"]["metadata"]["ID"], "Version": res["Data"]["metadata"]["Version"]})
            return 200

        return 400
    except:
        return 400

@app.route("/package/<id>", methods=['DELETE'])
def delPackageVers(id):
    try:
        if (checkIfFileExists(id)):
            history[id].pop(-1)
            if len(history[id]) == 0:
                history.pop(id)
            return 200
        return 400
    except:
        return 400
        

@app.route("/package/<id>/rate", methods=["GET"])
def ratePackage(id):
    try:
        if (checkIfFileExists(id)):
            storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
            bucketName = os.getenv("BUCKET_NAME")
            bucket = storageClient.bucket(bucketName)
            downloadPath = str(os.path.join(os.getcwd(), "Downloads"))

            if not os.path.exists(downloadPath):
                os.makedirs(downloadPath)

            fileToDownload = bucket.blob(id)
            fileToDownload.download_to_filename(downloadPath + "/" + id)
            
            res = appService.rate(id)

            return {"RampUp": res[0][1], "Correctness": res[0][2], "BusFactor": res[0][3], "ResponsiveMaintainer": res[0][4], "LicenseScore": res[0][5], "GoodPinningPractice": "Test"}, 200
        return 400
    except:
        return 500

@app.route("/package/byName/<name>", methods=['GET'])
def getPackageByName(name):
    try:
        jsonOut = []
        for x in history:
            if history[x][0]["Name"] == name:
                for x in history[x]:
                    jsonOut.append({"Date": datetime.now(), "PackageMetadata": x})
                    # return all versions
                    return jsonOut, 200
            else:
                return 400
    except:
        return {'code': -1, 'message': "An unexpected error occurred"}, 500

@app.route("/package/byName/<name>", methods=['DELETE'])
def delAllPackageVers(name):
    for x in history:
        if history[x][0]["Name"] == name:
            history.pop(x)
            return 200
    return 400

@app.route("/package", methods=['POST'])
def createPackage():
    try:
        data = request.get_json(force=True)
        bytes = data["data"]["Content"]

        currentDir = os.getcwd()
        newDir = "new_zips"
        newPath = os.path.join(currentDir, newDir)

        if not os.path.exists(newPath):
            os.makedirs(newPath)

        with zipfile.ZipFile(newPath + "/" + data["metadata"]["ID"], 'w') as zipRef:
            zipfile.ZipFile.writestr(zipRef, bytes)
            if checkIfFileExists(data["metadata"]["ID"]):
                return 403
            appService.upload(zipRef)

        # Add to history

        return {"Name": data["metadata"]["Name"], "Version": "1.0.0", "ID":data["metadata"]["ID"]}, 201
    except:
        return 400

@app.route("/packages", methods=['POST'])
def listPackages():
    try:
        offset = request.args.get('offset')
    except:
        offset = 0
    totalPackages = len(history)
    # need to check what happens if offset isn't provided
    page = 5 * offset
    # sorted dict? return by name?
    return {'offset': {"offsetAct": offset}}

@app.route("/reset", methods=['DELETE'])
def reset():
    history.clear()
    appService.reset()



if __name__ == '__main__':
    app.run(debug=True)


