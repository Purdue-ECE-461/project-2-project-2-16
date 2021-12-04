from re import S
from flask import Flask, request
from ApplicationService import *
from google.cloud import storage
import zipfile
import base64

app = Flask(__name__)

actionHistory = dict() # maps String id to [(date, action)],...

appService = ApplicationService()

# IDs are always unique strings, and different versions of the same package will have unique IDs
# Names can be duplicates, IDs cannot
# If a method isn't specified, it is a GET method
def createPackageListDict():
    try:
        storageClient = storage.Client()
        bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(bucketName)
        blobs = bucket.list_blobs()
        packageList = dict()
        for blob in blobs:
            name = str(blob.name)
            id = name[:-4]
            version = id[-5:]
            pkgName = id[:-5]
            packageList[id] = {"Name": pkgName, "Version": version, "ID": id}

        return packageList
    except Exception as e:
        raise Exception("error in create package list dict")

    
def checkIfFileExists(id):
    try:
        storageClient = storage.Client()
        bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(bucketName)
        fileToCheck = bucket.blob(id + ".zip")

        return fileToCheck.exists()
    except:
        raise Exception("File check failed")

@app.route("/package/<id>")
def getPackage(id):
    # Gets the package from google cloud storage and returns the info about it in metadata
    # Returns the actual compressed file in the content field as an encrypted base 64 string
    try:
        packageList = createPackageListDict()
        if (checkIfFileExists(id)):
            storageClient = storage.Client()
            bucketName = "ece-461-project-2-registry"
            bucket = storageClient.bucket(bucketName)
            fileToCheck = bucket.blob(id + ".zip")

            
            downloadPath = os.path.join(os.getcwd(), "Downloads")
            downloadFile = os.path.join(downloadPath, id + ".zip")

            if not os.path.exists(downloadPath):
                os.makedirs(downloadPath)
                
            fileToDownload = fileToCheck # name of storage object goes here
            fileToDownload.download_to_filename(str(downloadFile)) # path to local file

            with open(downloadFile, "rb") as fptr:
                data = fptr.read()
                encodedStr = base64.b64encode(data)

            unzipPath = os.path.join(downloadPath, id)

            with zipfile.ZipFile(downloadFile, "r") as zipRef:
                zipRef.extractall(unzipPath)

            try:
                jsonFile = os.path.join(unzipPath, "package.json")
                fptr = open(jsonFile)
                jsonData = json.load(fptr)
                repoUrl = jsonData["homepage"]
            except:
                repoUrl = "No URL Found."
        
            return {'metadata': {"Name": packageList[id]["Name"], "Version": packageList[id]["Version"], "ID": id}, "data": {"Content": encodedStr.decode('ascii'), "URL": repoUrl, "JSProgram": "if (process.argv.length === 7) {\nconsole.log('Success')\nprocess.exit(0)\n} else {\nconsole.log('Failed')\nprocess.exit(1)\n}\n"}}, 200
        else:
            return {'code': -1, 'message': "An error occurred while retrieving package, package does not exist", "packageList": packageList}, 500
    except Exception as e:
        return {'code': -1, 'message': "An exception occurred while retrieving package", 'exception': str(e), 'args': e.args}, 500

@app.route("/package/<id>", methods=['PUT'])
def putPackage(id):
    # Updates a currently existing package with the data from the request
    try:
        res = request.get_json(force=True)
        packageList = createPackageListDict()
        if (checkIfFileExists(id)):
            if (res["metadata"]["Name"] != packageList[id]["Name"] or res["metadata"]["Version"] != packageList[id]["Version"] or res["metadata"]["ID"] != packageList[id]["ID"]):
                return {"Warning": "metadata of package did not match", "packageList": packageList}, 400
            delPackage(id) # delete old package without removing package from history dictionaries

            newDir = "new_zips"
            newPath = os.path.join(os.getcwd(), newDir)

            if not os.path.exists(newPath):
                os.makedirs(newPath)

            newFile = os.path.join(newPath, id + ".zip")

            zipEncodedStr = res["data"]["Content"]
            zipDecoded = base64.b64decode(zipEncodedStr)

            with open(newFile, 'wb') as fptr:
                fptr.write(zipDecoded)
   
            files = []
            files.append(str(newFile))
            appService.upload(files)
            actionHistory[id].append((datetime.now(), "UPDATE"))
            os.remove(newFile)
            
            return {}, 200

        return {}, 400
    except Exception as e:
        return {"exception": str(e), "args": e.args}, 400

def delPackage(id):
    storageClient = storage.Client()
    bucketName = "ece-461-project-2-registry"
    bucket = storageClient.bucket(bucketName)
    blob = bucket.blob(id + ".zip")
    blob.delete()
    pass

@app.route("/package/<id>", methods=['DELETE'])
def delPackageVers(id):
    try:
        packageList = createPackageListDict()
        if (checkIfFileExists(id)):
            actionHistory.pop(id)
            delPackage(id)
            return {"Trace": "popped key " + id + " from packageList", "packageList": packageList}, 200
        return {}, 400
    except Exception as e:
        return {"exception": str(e), "args": e.args}, 500
        

@app.route("/package/<id>/rate", methods=["GET"])
def ratePackage(id):
    try:
        if (checkIfFileExists(id)):
            downloadPath = str(os.path.join(os.getcwd(), "Downloads"))

            if not os.path.exists(downloadPath):
                os.makedirs(downloadPath)

            storageClient = storage.Client()
            bucketName = "ece-461-project-2-registry"
            bucket = storageClient.bucket(bucketName)
            fileToDownload = bucket.blob(id + ".zip")
            fileDownloadPath = str(os.path.join(downloadPath, id + ".zip"))
            fileToDownload.download_to_filename(fileDownloadPath)
            
            files = []
            files.append(fileDownloadPath)
            res = appService.rate(files)

            actionHistory[id].append((datetime.now(), "RATE"))

            return {"RampUp": res[0][1], "Correctness": res[0][2], "BusFactor": res[0][3], "ResponsiveMaintainer": res[0][4], "LicenseScore": res[0][5], "GoodPinningPractice": "Test"}, 200
        return {}, 400
    except Exception as e:
        return {"exception": str(e), "args": e.args}, 500

@app.route("/package/byName/<name>", methods=['GET'])
def getPackageByName(name):
    try:
        jsonOut = []
        packageList = createPackageListDict()
        for id, info in packageList.items():
            if (info["Name"] == name):
                for y in actionHistory[id]:
                    jsonOut.append({"Date": y[0], "PackageMetadata": info, "Action": y[1]})
        if not jsonOut:
            return {}, 400
        
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

        packageList = createPackageListDict()
        for id, info in packageList.items():
            if (info["Name"] == name):
                actionHistory.pop(id)
                blob = bucket.blob(id + ".zip")
                blob.delete()
                deleted = True

        if deleted:
            return {}, 200
        
        return {}, 400
    except Exception as e:
        return {"exception": str(e), 'args': e.args}, 400

@app.route("/package", methods=['POST'])
def createPackage():
    packageList = createPackageListDict()
    try:
        data = request.get_json(force=True)
        encString = data["data"]["Content"]
        zipDecoded = base64.b64decode(encString)

        newDir = "new_zips"
        newPath = os.path.join(os.getcwd(), newDir)
        histPath = os.path.join(os.getcwd(), "hist")

        id = data["metadata"]["Name"] + data["metadata"]["Version"]

        if not os.path.exists(newPath):
            os.makedirs(newPath)

        if checkIfFileExists(id):
            return {"package": "exists", "packageList": packageList}, 403

        newFile = os.path.join(newPath, data["metadata"]["Name"] + data["metadata"]["Version"] + ".zip")
        newHistFile = os.path.join(histPath, data["metadata"]["Name"] + data["metadata"]["Version"] + ".txt")
    
        if "Content" in data["data"]: # Creation
            try:
                with open(newFile, 'wb') as fptr:
                    fptr.write(zipDecoded)
            except Exception as e:
                raise Exception("decode zip fail", str(e))
            
            files = []
            files.append(str(newFile))

            histEntry = []
            histEntry.append({"User": {"name": "Default User", "isAdmin": True}, "Date": datetime.now(), "PackageMetadata": {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id}, "Action": "CREATE"})
            try:
                if not os.path.exists(newHistFile):
                    fptr = open(newHistFile, 'x')
                else:
                    fptr = open(newHistFile, 'w')
            except Exception as e:
                raise Exception("opening fail", str(e))
            try:
                jsonString = json.dumps(histEntry)
            except:
                raise Exception("Json string fail")
            try:
                fptr.write(jsonString)
            except Exception as e:
                raise Exception("json write failed", str(e))

            files.append(str(newHistFile))

            try:
                appService.upload(files)
            except:
                raise Exception("Upload failed")

        else: # Ingestion
            if (appService.ingest(newFile)):
                actionHistory[id] = []
                actionHistory[id].append((datetime.now(), "CREATE"))
            else:
                return 403

        return {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id, "packageList": packageList}, 201
        
    except Exception as e:
        return {"Exception": str(e), "args": e.args}, 400

def splitVersionString(version):
    split = version.split('.')

    if len(split) == 1:
        return {"major": int(split[0]), "minor": 0, "patch": 0}
    elif len(split) == 2:
        return {"major": int(split[0]), "minor": int(split[1]), "patch": 0}
    else:
        return {"major": int(split[0]), "minor": int(split[1]), "patch": int(split[2])}

def versionCheck(versionTestAgainst, versionToTest):
    if "-" in versionTestAgainst: # bounded version range
        ranges = versionTestAgainst.split("-")
        if versionToTest >= ranges[0] and versionToTest <= ranges[1]:
            return True

    elif "^" in versionTestAgainst: # carat version range
        lowRange = versionTestAgainst[1:]
        lowDict = splitVersionString(lowRange)
        highDict = splitVersionString(lowRange)
        if lowDict["major"] > 0:
            highDict["major"] = lowDict["major"] + 1
        elif lowDict["minor"] > 0:
            highDict["minor"] = lowDict["minor"] + 1
        else:
            highDict["patch"] = lowDict["patch"] + 1

        lowVersion = str(lowDict["major"]) + "." + str(lowDict["minor"]) + "." + str(lowDict["patch"])
        highVersion = str(highDict["major"]) + "." + str(highDict["minor"]) + "." + str(highDict["patch"])

        if versionToTest >= lowVersion and versionToTest < highVersion:
            return True

    elif "~" in versionTestAgainst: # tilde version range
        lowRange = versionTestAgainst[1:]
        lowDict = splitVersionString(lowRange)
        highDict = splitVersionString(lowRange)
        if lowDict["minor"] > 0 or lowDict["patch"] > 0:
            highDict["minor"] = lowDict["minor"] + 1
        else:
            highDict["major"] = lowDict["major"] + 1
        
        lowVersion = str(lowDict["major"]) + "." + str(lowDict["minor"]) + "." + str(lowDict["patch"])
        highVersion = str(highDict["major"]) + "." + str(highDict["minor"]) + "." + str(highDict["patch"])

        if versionToTest >= lowVersion and versionToTest < highVersion:
            return True

    else: # exact version
        if versionToTest == versionTestAgainst:
            return True

    return False

@app.route("/packages", methods=['POST'])
def listPackages():
    packageList = createPackageListDict()
    packages = packageList.items()
    try:
        offset = request.args.get('offset')
    except:
        offset = 1

    output = []

    data = request.get_json(force=True)
    dataList = json.loads(data)
    for dictReqs in dataList: # loop through all reqs
        for package in packages:
            if package["Name"] == dictReqs["Name"]:
                if versionCheck(dictReqs["Version"], package["Version"]):
                    output.append(package)

    totalOutputPages = len(output) / 5
    if offset > totalOutputPages:
        offset = totalOutputPages

    startPackage = (totalOutputPages - 1) * 5
    outputPage = []
    for x in range(startPackage, len(output)):
        outputPage.append(output[x])

    return outputPage, 200

@app.route("/reset", methods=['DELETE'])
def reset():
    try:
        storageClient = storage.Client()
        bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(bucketName)
        blobs = bucket.list_blobs()
        for blob in blobs:
            blob.delete()
        
        actionHistory.clear()
        appService.reset()

        return {}, 200
    except Exception as e:
        return {"Exception": str(e)}, 401



if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)


