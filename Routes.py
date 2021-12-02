from flask import Flask, request, Response
from ApplicationService import *
from google.cloud import storage
import zipfile
import base64

app = Flask(__name__)

packageList = dict() # maps String id to {name, version, id}
actionHistory = dict() # maps String id to [(date, action)],...

appService = ApplicationService()

# IDs are always unique strings, and different versions of the same package will have unique IDs
# Names can be duplicates, IDs cannot
# If a method isn't specified, it is a GET method
    
def checkIfFileExists(id):
    #storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
    storageClient = storage.Client()
    bucketName = "ece-461-project-2-registry"
    bucket = storageClient.bucket(bucketName)
    fileToCheck = bucket.blob(id)

    return fileToCheck.exists()

@app.route("/test")
def hello_world():
    return 'Hello World!'

@app.route("/package/<id>")
def getPackage(id):
    # Gets the package from google cloud storage and returns the info about it in metadata
    # Returns the actual compressed file in the content field as an encrypted base 64 string
    try:
        storageClient = storage.Client()
        bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(bucketName)
        fileToCheck = bucket.blob(id + ".zip")

        if (fileToCheck.exists()):
            downloadPath = str(os.path.join(os.getcwd(), "Downloads"))
            downloadFile = str(os.path.join(downloadPath, id + ".zip"))

            if not os.path.exists(downloadPath):
                os.makedirs(downloadPath)
                
            fileToDownload = fileToCheck # name of storage object goes here
            fileToDownload.download_to_filename(downloadFile) # path to local file

            #newFile = str(os.path.join(downloadPath, id))

            with open(downloadFile, "rb") as fptr:
                data = fptr.read()
                encodedStr = base64.b64encode(data)

            unzipPath = str(os.path.join(downloadPath, id))

            with zipfile.ZipFile(downloadFile, "r") as zipRef:
                zipRef.extractall(unzipPath)

            try:
                jsonFile = str(os.path.join(unzipPath, "package.json"))
                fptr = open(jsonFile)
                jsonData = json.load(fptr)
                repoUrl = jsonData["homepage"]
            except:
                repoUrl = "No URL Found."

            actionHistory[id].append((datetime.now(), "GET"))
            raise Exception("after appending actionHistory")
        
            return {'metadata': {"Name": packageList[id]["Name"], "Version": packageList[id]["Version"], "ID": id}, "data": {"Content": encodedStr, "URL": repoUrl, "JSProgram": "if (process.argv.length === 7) {\nconsole.log('Success')\nprocess.exit(0)\n} else {\nconsole.log('Failed')\nprocess.exit(1)\n}\n"}}, 200
        else:
            return {'code': -1, 'message': "An error occurred while retrieving package"}, 500
    except Exception as e:
        return {'code': -1, 'message': "An exception occurred while retrieving package", 'exception': str(e)}, 500

@app.route("/package/<id>", methods=['PUT'])
def putPackage(id):
    # Updates a currently existing package with the data from the request
    try:
        res = request.get_json(force=True)
        storageClient = storage.Client()
        bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(bucketName)
        fileToCheck = bucket.blob(id + ".zip")

        if (fileToCheck.exists()):
            if (res["metadata"]["Name"] != packageList[id]["Name"] or res["metadata"]["Version"] != packageList[id]["Version"] or res["metadata"]["ID"] != packageList[id]["ID"]):
                return 400
            delPackageVers(id) # delete old package

            newDir = "new_zips"
            newPath = str(os.path.join(os.getcwd(), newDir))

            if not os.path.exists(newPath):
                os.makedirs(newPath)

            newFile = str(os.path.join(newPath, id + ".zip"))

            zipEncodedStr = res["data"]["Content"]
            zipDecoded = base64.b64decode(zipEncodedStr)

            with open(newFile, 'wb') as fptr:
                fptr.write(zipDecoded)
   
            files = []
            files.append(newFile)
            appService.upload(files)
            actionHistory[id].append((datetime.now(), "UPDATE"))
            
            return 200

        return 400
    except Exception as e:
        return {"exception": str(e)}, 400

@app.route("/package/<id>", methods=['DELETE'])
def delPackageVers(id):
    try:
        storageClient = storage.Client()
        #storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
        bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(bucketName)
        if (packageList.has_key(id)):
            blob = bucket.blob(id)
            blob.delete()
            return 200
        return 400
    except Exception as e:
        return {"exception": str(e)}, 400
        

@app.route("/package/<id>/rate", methods=["GET"])
def ratePackage(id):
    try:
        if (checkIfFileExists(id)):
            storageClient = storage.Client()
            #storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
            bucketName = "ece-461-project-2-registry"
            bucket = storageClient.bucket(bucketName)
            downloadPath = str(os.path.join(os.getcwd(), "Downloads"))

            if not os.path.exists(downloadPath):
                os.makedirs(downloadPath)

            fileToDownload = bucket.blob(id)
            fileDownloadPath = str(os.path.join(downloadPath, id))
            fileToDownload.download_to_filename(fileDownloadPath)
            
            res = appService.rate(id)

            actionHistory[id].append((datetime.now(), "RATE"))

            return {"RampUp": res[0][1], "Correctness": res[0][2], "BusFactor": res[0][3], "ResponsiveMaintainer": res[0][4], "LicenseScore": res[0][5], "GoodPinningPractice": "Test"}, 200
        return 400
    except Exception as e:
        return {"exception": str(e)}, 500

@app.route("/package/byName/<name>", methods=['GET'])
def getPackageByName(name):
    try:
        jsonOut = []
        for id, info in packageList.items():
            if (info["Name"] == name):
                for y in actionHistory[id]:
                    jsonOut.append({"Date": y[0], "PackageMetadata": info, "Action": y[1]})
        
        if not jsonOut:
            return 400
        
        return jsonOut, 200
        
    except Exception as e:
        return {'code': -1, 'message': "An unexpected error occurred", "exception": str(e)}, 500

@app.route("/package/byName/<name>", methods=['DELETE'])
def delAllPackageVers(name):
    try:
        storageClient = storage.Client()
        bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(bucketName)
        deleted = False

        for id, info in packageList.items():
            if (info["Name"] == name):
                actionHistory.pop(id)
                packageList.pop(id)
                blob = bucket.blob(id)
                blob.delete()
                deleted = True

        if deleted:
            return 200
        
        return 400
    except Exception as e:
        return {"exception": str(e)}, 400

@app.route("/package", methods=['POST'])
def createPackage():
    try:
        data = request.get_json(force=True)
        encString = data["data"]["Content"]
        zipDecoded = base64.b64decode(encString)

        newDir = "new_zips"
        newPath = str(os.path.join(os.getcwd(), newDir))

        id = data["metadata"]["Name"] + data["metadata"]["Version"]

        if not os.path.exists(newPath):
            os.makedirs(newPath)
        
        if id in packageList:
            return 403

        newFile = str(os.path.join(newPath, data["metadata"]["Name"] + data["metadata"]["Version"] + ".zip"))

        with open(newFile, 'wb') as fptr:
            fptr.write(zipDecoded)

        
        if "Content" in data["data"]: # Creation
            files = []
            files.append(newFile)
            appService.upload(files)
            
            packageList[id] = {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id}
            actionHistory[id] = []
            actionHistory[id].append((datetime.now(), "CREATE"))

        else: # Ingestion
            if (appService.ingest(newFile)):
                packageList[id] = {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id}
                actionHistory[id] = []
                actionHistory[id].append((datetime.now(), "CREATE"))
            else:
                return 403

        return {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id}, 201
        
    except Exception as e:
        return {"Exception": str(e)}, 400

@app.route("/packages", methods=['POST'])
def listPackages():
    try:
        offset = request.args.get('offset')
    except:
        offset = 0
    totalPackages = len(packageList)
    # need to check what happens if offset isn't provided
    page = 5 * offset
    # sorted dict? return by name?
    return {'offset': {"offsetAct": offset}}

@app.route("/reset", methods=['DELETE'])
def reset():
    for x in packageList:
        delPackageVers(x)
    
    packageList.clear()
    actionHistory.clear()
    appService.reset()



if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)


