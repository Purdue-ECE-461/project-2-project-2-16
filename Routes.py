from re import S
from flask import Flask, request
from flask_cors import CORS, cross_origin
from ApplicationService import *
from google.cloud import storage
import zipfile
import base64
import re

app = Flask(__name__)
CORS(app)

actionHistory = dict() # maps String id to [(date, action)],...

appService = ApplicationService()

bucketName = "ece-461-project-2-registry"

# IDs are always unique strings, and different versions of the same package will have unique IDs
# Names can be duplicates, IDs cannot
# If a method isn't specified, it is a GET method
def createPackageListDict():
    try:
        storageClient = storage.Client()
        bucket = storageClient.bucket(bucketName)
        blobs = bucket.list_blobs()
        packageList = dict()
        for blob in blobs:
            name = str(blob.name)
            fileType = name [-4:]
            id = name[:-4]
            matchVersion = re.search("\d+\.\d+\.\d+", id)
            version = matchVersion.group()
            pkgName = id[:-(len(matchVersion.group()))]
            if fileType == ".zip":
                packageList[id] = {"Name": pkgName, "Version": version, "ID": id}

        return packageList
    except Exception as e:
        raise Exception("error in create package list dict")

    
def checkIfFileExists(id):
    try:
        storageClient = storage.Client()
        bucket = storageClient.bucket(bucketName)
        fileToCheck = bucket.blob(id + ".zip")

        return fileToCheck.exists()
    except:
        raise Exception("File check failed")

def updateHist(id, typeUpdate, packageList):
    try:
        storageClient = storage.Client()
        bucket = storageClient.bucket(bucketName)
        downloadPath = os.path.join(os.getcwd(), "Downloads")
        if not os.path.exists(downloadPath):
                os.makedirs(downloadPath)
        
        histFile = os.path.join(downloadPath, id + "history.json")
        fileToDownload = bucket.blob(id + "history.json")
        fileToDownload.download_to_filename(str(histFile))
        try:
            with open(histFile, "r") as fptr:
                listJson = json.load(fptr)
        except:
            raise Exception("could not load json")

        listJson.append({"User": {"name": "Default User", "isAdmin": True}, "Date": str(datetime.now()), "PackageMetadata": packageList[id], "Action": typeUpdate})

        try:
            with open(histFile, "w") as fptr:
                json.dump(listJson, fptr, indent=4)
        except:
            raise Exception("could not write json")

        files = []
        files.append(histFile)
        appService.upload(files)
    except Exception as e:
        raise Exception("update Hist failed", str(e))

@app.route("/package/<id>")
def getPackage(id):
    # Gets the package from google cloud storage and returns the info about it in metadata
    # Returns the actual compressed file in the content field as an encrypted base 64 string
    try:
        packageList = createPackageListDict()
        if (checkIfFileExists(id)):
            storageClient = storage.Client()
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
                with open(jsonFile, "r") as fptr:
                    jsonData = json.load(fptr.read())    
                repoUrl = jsonData["homepage"]
            except:
                repoUrl = "No URL Found."

            updateHist(id, "GET", packageList)
        
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
        if checkIfFileExists(id):
            if (res["metadata"]["Name"] != packageList[id]["Name"] or res["metadata"]["Version"] != packageList[id]["Version"] or res["metadata"]["ID"] != packageList[id]["ID"]):
                return {"Warning": "metadata of package did not match", "packageList": packageList}, 400
           
            storageClient = storage.Client()
            bucket = storageClient.bucket(bucketName)
            blob = bucket.blob(id + ".zip")
            blob.delete()

            newDir = "new_zips"
            newPath = os.path.join(os.getcwd(), newDir)

            if not os.path.exists(newPath):
                os.makedirs(newPath)

            newFile = os.path.join(newPath, id + ".zip")

            zipEncodedStr = res["data"]["Content"]
            newZipStr = zipEncodedStr + ((4 - (len(zipEncodedStr) % 4)) * "=")
            zipDecoded = base64.b64decode(newZipStr)

            with open(newFile, 'wb') as fptr:
                fptr.write(zipDecoded)
   
            files = []
            files.append(str(newFile))
            appService.upload(files)
            updateHist(id, "UPDATE", packageList)

            return {}, 200

        return {}, 400
    except Exception as e:
        return {"exception": str(e), "args": e.args}, 400

def delPackage(id):
    storageClient = storage.Client()
    bucket = storageClient.bucket(bucketName)
    blob = bucket.blob(id + ".zip")
    blob.delete()
    blob = bucket.blob(id + "history.json")
    blob.delete()
    pass

@app.route("/package/<id>", methods=['DELETE'])
def delPackageVers(id):
    try:
        packageList = createPackageListDict()
        if (checkIfFileExists(id)):
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
            bucket = storageClient.bucket(bucketName)
            fileToDownload = bucket.blob(id + ".zip")
            fileDownloadPath = str(os.path.join(downloadPath, id + ".zip"))
            fileToDownload.download_to_filename(fileDownloadPath)
            
            files = []
            files.append(fileDownloadPath)
            try:
                res = appService.rate(files)
            except Exception as e:
                raise Exception("rate fail", str(e))

            packageList = createPackageListDict()
            updateHist(id, "RATE", packageList)
            try:
                scoreDict = {"RampUp": res[0][id][1], "Correctness": res[0][id][2], "BusFactor": res[0][id][3], "ResponsiveMaintainer": res[0][id][4], "LicenseScore": res[0][id][5], "GoodPinningPractice": res[0][id][6]}
            except Exception as e:
                raise Exception("scoreDict fail", str(e), res[0])
            return scoreDict, 200
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
                downloadPath = os.path.join(os.getcwd(), "Downloads")
                downloadFile = os.path.join(downloadPath, id + "history.json")

                if not os.path.exists(downloadPath):
                    os.makedirs(downloadPath)
                    
                storageClient = storage.Client()
                bucket = storageClient.bucket(bucketName)
                fileToDownload = bucket.blob(id + "history.json")
                fileToDownload.download_to_filename(str(downloadFile)) # path to local file

                with open(downloadFile, "r") as fptr:
                    jsonOut.append(json.load(fptr))
            
        if not jsonOut:
            return {}, 400
        
        return json.dumps(jsonOut, indent=4), 200
        
    except Exception as e:
        return {'code': -1, 'message': "An unexpected error occurred", "exception": str(e)}, 500

@app.route("/package/byName/<name>", methods=['DELETE'])
def delAllPackageVers(name):
    try:
        deleted = False
        packageList = createPackageListDict()
        for id, info in packageList.items():
            if (info["Name"] == name):
                delPackage(id)
                deleted = True

        if deleted:
            return {}, 200
        
        return {}, 400
    except Exception as e:
        return {"exception": str(e), 'args': e.args}, 400

@app.route("/package", methods=['POST'])
@cross_origin()
def createPackage():
    packageList = createPackageListDict()
    try:
        data = request.get_json(force=True)
        encString = data["data"]["Content"]
        zipDecoded = base64.b64decode(encString)

        newDir = "new_zips"
        newPath = os.path.join(os.getcwd(), newDir)

        histDir = "hist"
        histPath = os.path.join(os.getcwd(), histDir)

        id = data["metadata"]["Name"] + data["metadata"]["Version"]

        if not os.path.exists(newPath):
            os.makedirs(newPath)

        if not os.path.exists(histPath):
            os.makedirs(histPath)

        if checkIfFileExists(id):
            return {"package": "exists", "packageList": packageList}, 403

        newFile = os.path.join(newPath, data["metadata"]["Name"] + data["metadata"]["Version"] + ".zip")
        newHistFile = os.path.join(histPath, data["metadata"]["Name"] + data["metadata"]["Version"] + "history.json")
    
        if "Content" in data["data"]: # Creation
            with open(newFile, 'wb') as fptr:
                fptr.write(zipDecoded)
            
            files = []
            files.append(str(newFile))

            histEntry = []
            histEntry.append({"User": {"name": "Default User", "isAdmin": True}, "Date": str(datetime.now()), "PackageMetadata": {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id}, "Action": "CREATE"})
            
            with open(newHistFile, "w") as fptr:
                try:
                    json.dump(histEntry, fptr, indent=4)
                except:
                    raise Exception("Json string fail")

            files.append(str(newHistFile))

            try:
                appService.upload(files)
            except:
                raise Exception("Upload failed")

        else: # Ingestion
            if appService.ingest(str(newFile)):
                actionHistory[id] = []
                actionHistory[id].append((datetime.now(), "CREATE"))
            else:
                return 403

        return {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id, "packageList": packageList}, 201
        
    except Exception as e:
        return {"Exception": str(e), "args": e.args}, 400

def splitVersionString(version):
    try:
        split = version.split('.')

        if len(split) == 1:
            return {"major": int(split[0]), "minor": 0, "patch": 0}
        elif len(split) == 2:
            return {"major": int(split[0]), "minor": int(split[1]), "patch": 0}
        elif len(split) == 3:
            return {"major": int(split[0]), "minor": int(split[1]), "patch": int(split[2])}
        else:
            raise Exception("Invalid version input. Version input was " + version)
    except Exception as e:
        raise Exception("splitVersion error", str(e))

def versionCheck(versionTestAgainst, versionToTest):
    
    if "-" in versionTestAgainst: # bounded version range\
        try:
            ranges = versionTestAgainst.split("-")
            if str(versionToTest) >= str(ranges[0]) and str(versionToTest) <= str(ranges[1]):
                return True
        except Exception as e:
            raise Exception("Bounded range error.", str(e))

    elif "^" in versionTestAgainst: # carat version range
        try:
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

            if str(versionToTest) >= str(lowVersion) and str(versionToTest) < str(highVersion):
                return True
        except Exception as e:
            raise Exception("Carat range error.", str(e))


    elif "~" in versionTestAgainst: # tilde version range
        try:
            lowRange = versionTestAgainst[1:]
            lowDict = splitVersionString(lowRange)
            highDict = splitVersionString(lowRange)
            if lowDict["minor"] > 0 or lowDict["patch"] > 0:
                highDict["minor"] = lowDict["minor"] + 1
            else:
                highDict["major"] = lowDict["major"] + 1
            
            lowVersion = str(lowDict["major"]) + "." + str(lowDict["minor"]) + "." + str(lowDict["patch"])
            highVersion = str(highDict["major"]) + "." + str(highDict["minor"]) + "." + str(highDict["patch"])

            if str(versionToTest) >= str(lowVersion) and str(versionToTest) < str(highVersion):
                return True
        except Exception as e:
            raise Exception("Tilde range error.", str(e))

    else: # exact version
        try:
            if str(versionToTest) == str(versionTestAgainst):
                return True
        except Exception as e:
            raise Exception("Exact range error.", str(e))

    return False

@app.route("/packages", methods=['POST'])
def listPackages():
    try:
        packageList = createPackageListDict()
        packages = packageList.items()
        try:
            offset = request.args.get('offset')
        except:
            offset = 1

        output = []

        data = request.get_json(force=True)
        # dataList = json.loads(data)
        # sort through and get all possible packages to print
        try:
            for dictReqs in data: # loop through all reqs
                for package in packages:
                    if package[1]["Name"] == dictReqs["Name"]:
                        if versionCheck(dictReqs["Version"], package[1]["Version"]):
                            output.append(package[1])
        except Exception as e:
            raise Exception("Data obtain error", str(e), "Type of package", str(type(packages)), "Type of dictReq", str(type(data[0])))

        totalOutputPages = len(output) // 5
        try:
            if int(offset) > totalOutputPages:
                offset = totalOutputPages
        except:
            raise Exception("compare error")

        startPackage = totalOutputPages * 5
        outputPage = []
        try:
            for x in range(startPackage, len(output)): # paginate the output
                outputPage.append(output[x])
        except Exception as e:
            raise Exception("Paginate error", str(e))

        return json.dumps(outputPage, indent=4), 200
    except Exception as e:
        return {"code": -1, "message": "An unexpected error occurred", "exception": str(e), "args": e.args}, 500

@app.route("/reset", methods=['DELETE'])
def reset():
    try:
        storageClient = storage.Client()
        bucket = storageClient.bucket(bucketName)
        blobs = bucket.list_blobs()
        for blob in blobs:
            blob.delete()
        
        actionHistory.clear()
        appService.reset()

        return {}, 200
    except Exception as e:
        return {"Exception": str(e), "args": e.args}, 401



if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)


