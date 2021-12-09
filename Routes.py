import datetime
import json
import os
from re import S
from dotenv import load_dotenv
from flask import Flask, request
from flask.scaffold import F
from flask_cors import CORS, cross_origin
from application_service import ApplicationService 
from google.cloud import storage
import zipfile
import base64
import re
import requests

app = Flask(__name__)
CORS(app)

app_service = ApplicationService()
BUCKET_NAME = "ece-461-project-2-registry"

# IDs are always unique strings, and different versions of the same package will have unique IDs
# Names can be duplicates, IDs cannot
# If a method isn't specified, it is a GET method
def create_package_list_dict():
    '''Creates a package dict with all files currently in registry in GCS'''
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = bucket.list_blobs()
        package_list = dict()
        for blob in blobs:
            name = str(blob.name)
            file_type = name [-4:]
            package_id = name[:-4]
            match_version = re.search(r"\d+\.\d+\.\d+", package_id)
            version = match_version.group()
            package_name = package_id[:-(len(match_version.group()))]
            if file_type == ".zip":
                package_list[package_id] = {"Name": package_name, "Version": version,
                "ID": package_id}

        return package_list
    except Exception as exc:
        raise Exception("error in create package list dict") from exc

def check_if_file_exists(package_id):
    '''Checks if the file currently exists in GCS'''
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        file_check = bucket.blob(package_id + ".zip")

        return file_check.exists()
    except Exception as exc:
        raise Exception("File check failed") from exc

def update_hist(package_id, type_update, package_list):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        download_path = os.path.join(os.getcwd(), "Downloads")
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        hist_file = os.path.join(download_path, package_id + "history.json")
        file_download = bucket.blob(package_id + "history.json")
        file_download.download_to_filename(str(hist_file))
        try:
            with open(hist_file, "r", encoding="utf-8") as fptr:
                list_json = json.load(fptr)
        except Exception as exc:
            raise Exception("could not load json") from exc

        list_json.append({"User": {"name": "Default User", "isAdmin": True},
        "Date": str(datetime.datetime.now()), "PackageMetadata": package_list[id], 
        "Action": type_update})

        try:
            with open(hist_file, "w", encoding="utf-8") as fptr:
                json.dump(list_json, fptr, indent=4)
        except Exception as exc:
            raise Exception("could not write json") from exc

        files = []
        files.append(hist_file)
        app_service.upload(files)
    except Exception as exc:
        raise Exception("update Hist failed") from exc

@app.route("/package/<id>")
def getPackage(package_id):
    # Gets the package from google cloud storage and returns the info about it in metadata
    # Returns the actual compressed file in the content field as an encrypted base 64 string
    try:
        package_list = create_package_list_dict()
        if (check_if_file_exists(package_id)):
            storage_client = storage.Client()
            bucket = storage_client.bucket(BUCKET_NAME)
            file_check = bucket.blob(package_id + ".zip")

            download_path = os.path.join(os.getcwd(), "Downloads")
            download_file = os.path.join(download_path, package_id + ".zip")

            if not os.path.exists(download_path):
                os.makedirs(download_path)

            file_download = file_check # name of storage object goes here
            file_download.download_to_filename(str(download_file)) # path to local file

            with open(download_file, "rb") as fptr:
                data = fptr.read()
                encoded_str = base64.b64encode(data)

            unzip_path = os.path.join(download_path, package_id)

            with zipfile.ZipFile(download_file, "r") as zip_ref:
                zip_ref.extractall(unzip_path)

            try:
                json_file = os.path.join(unzip_path, "package.json")
                with open(json_file, "r", encoding="utf-8") as fptr:
                    json_data = json.load(fptr.read())
                repo_url = json_data["homepage"]
            except Exception:
                repo_url = "No URL Found."

            update_hist(package_id, "GET", package_list)
        
            return {'metadata': {"Name": package_list[package_id]["Name"], "Version": package_list[package_id]["Version"], "ID": package_id}, "data": {"Content": encoded_str.decode('ascii'), "URL": repo_url, "JSProgram": "if (process.argv.length === 7) {\nconsole.log('Success')\nprocess.exit(0)\n} else {\nconsole.log('Failed')\nprocess.exit(1)\n}\n"}}, 200
        else:
            return {'code': -1, 'message': "An error occurred while retrieving package, package does not exist", "package_list": package_list}, 500
    except Exception as exc:
        return {'code': -1, 'message': "An exception occurred while retrieving package", 'exception': str(exc), 'args': exc.args}, 500

@app.route("/package/<id>", methods=['PUT'])
def putPackage(id):
    # Updates a currently existing package with the data from the request
    try:
        res = request.get_json(force=True)
        package_list = create_package_list_dict()
        if check_if_file_exists(id):
            if (res["metadata"]["Name"] != package_list[id]["Name"] or res["metadata"]["Version"] != package_list[id]["Version"] or res["metadata"]["ID"] != package_list[id]["ID"]):
                return {"Warning": "metadata of package did not match", "package_list": package_list}, 400
           
            storage_client = storage.Client()
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(id + ".zip")
            blob.delete()

            newDir = "new_zips"
            newPath = os.path.join(os.getcwd(), newDir)

            if not os.path.exists(newPath):
                os.makedirs(newPath)

            newFile = os.path.join(newPath, id + ".zip")

            zipencoded_str = res["data"]["Content"]
            newZipStr = zipencoded_str + ((4 - (len(zipencoded_str) % 4)) * "=")
            zipDecoded = base64.b64decode(newZipStr)

            with open(newFile, 'wb') as fptr:
                fptr.write(zipDecoded)
   
            files = []
            files.append(str(newFile))
            app_service.upload(files)
            update_hist(id, "UPDATE", package_list)

            return {}, 200

        return {}, 400
    except Exception as e:
        return {"exception": str(e), "args": e.args}, 400

def delPackage(id):
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(id + ".zip")
    blob.delete()
    blob = bucket.blob(id + "history.json")
    blob.delete()
    pass

@app.route("/package/<id>", methods=['DELETE'])
def delPackageVers(id):
    try:
        package_list = create_package_list_dict()
        if (check_if_file_exists(id)):
            delPackage(id)
            return {"Trace": "popped key " + id + " from package_list", "package_list": package_list}, 200
        return {}, 400
    except Exception as e:
        return {"exception": str(e), "args": e.args}, 500
        

@app.route("/package/<id>/rate", methods=["GET"])
def ratePackage(id):
    try:
        if (check_if_file_exists(id)):
            download_path = str(os.path.join(os.getcwd(), "Downloads"))

            if not os.path.exists(download_path):
                os.makedirs(download_path)

            storage_client = storage.Client()
            bucket = storage_client.bucket(BUCKET_NAME)
            file_download = bucket.blob(id + ".zip")
            filedownload_path = str(os.path.join(download_path, id + ".zip"))
            file_download.download_to_filename(filedownload_path)
            
            files = []
            files.append(filedownload_path)
            try:
                res = app_service.rate(files)
            except Exception as e:
                raise Exception("rate fail", str(e))

            package_list = create_package_list_dict()
            update_hist(id, "RATE", package_list)
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
        package_list = create_package_list_dict()
        for id, info in package_list.items():
            if (info["Name"] == name):
                download_path = os.path.join(os.getcwd(), "Downloads")
                download_file = os.path.join(download_path, id + "history.json")

                if not os.path.exists(download_path):
                    os.makedirs(download_path)
                    
                storage_client = storage.Client()
                bucket = storage_client.bucket(BUCKET_NAME)
                file_download = bucket.blob(id + "history.json")
                file_download.download_to_filename(str(download_file)) # path to local file

                with open(download_file, "r") as fptr:
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
        package_list = create_package_list_dict()
        for id, info in package_list.items():
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
    package_list = create_package_list_dict()
    try:
        data = request.get_json(force=True)

        newDir = "new_zips"
        newPath = os.path.join(os.getcwd(), newDir)

        histDir = "hist"
        histPath = os.path.join(os.getcwd(), histDir)

        id = data["metadata"]["Name"] + data["metadata"]["Version"]

        if not os.path.exists(newPath):
            os.makedirs(newPath)

        if not os.path.exists(histPath):
            os.makedirs(histPath)

        if check_if_file_exists(id):
            return {"package": "exists", "package_list": package_list}, 403

        newFile = os.path.join(newPath, data["metadata"]["Name"] + data["metadata"]["Version"] + ".zip")
        newhist_file = os.path.join(histPath, data["metadata"]["Name"] + data["metadata"]["Version"] + "history.json")
    
        if "Content" in data["data"]: # Creation
            encString = data["data"]["Content"]
            zipDecoded = base64.b64decode(encString)

            with open(newFile, 'wb') as fptr:
                fptr.write(zipDecoded)
            
            files = []
            files.append(str(newFile))

            histEntry = []
            histEntry.append({"User": {"name": "Default User", "isAdmin": True}, "Date": str(datetime.now()), "PackageMetadata": {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id}, "Action": "CREATE"})
            
            with open(newhist_file, "w") as fptr:
                try:
                    json.dump(histEntry, fptr, indent=4)
                except:
                    raise Exception("Json string fail")

            files.append(str(newhist_file))

            try:
                app_service.upload(files)
            except:
                raise Exception("Upload failed")

        else: # Ingestion
            try:
                splitStr = data["data"]["URL"].split("/")
                author, repo = splitStr[-2], splitStr[-1]
                url = "https://api.github.com/repos/" + author + "/" + repo + "/zipball"
                load_dotenv()
                GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

                headers = {
                    'Accept': 'application/vnd.github.v3+json',
                    'Authorization': f'token {GITHUB_TOKEN}'}
            except Exception as e:
                raise Exception("beginning ingest")

            try:
                r = requests.get(url, headers=headers, allow_redirects=True)
            except Exception as e:
                raise("Request fail", str(e))

            if r.status_code != 200:
               raise Exception("Could not get zip file of repo from GitHub.", "Code :" + str(r.status_code))

            try:
                with open(newFile, "wb") as fptr:
                    fptr.write(r.content)
            except Exception as e:
                raise Exception("write zip fail", str(e))

            try:
                files = []
                files.append(str(newFile))
                try:
                    res = app_service.rate(files)
                except Exception as e:
                    raise Exception("rate fail in ingest", str(e))

                if res[0][id][0] > .5:
                    histEntry = []
                    histEntry.append({"User": {"name": "Default User", "isAdmin": True}, "Date": str(datetime.now()), "PackageMetadata": {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id}, "Action": "INGEST"})
                    with open(newhist_file, "w") as fptr:
                        try:
                            json.dump(histEntry, fptr, indent=4)
                        except:
                            raise Exception("Json string fail")

                    files.append(str(newhist_file))

                    try:
                        app_service.upload(files)
                    except:
                        raise Exception("Upload failed")
                else:
                    return {"Package net score was not high enough. Score": res[0][id][0]}, 403
            except Exception as e:
                raise Exception("Ingest in Routes", str(e), "request=", str(r))

        return {"Name": data["metadata"]["Name"], "Version": data["metadata"]["Version"], "ID": id, "package_list": package_list}, 201
        
    except Exception as e:
        return {"Exception": str(e), "args": e.args}, 400

def compareVersionRanges(versionDictTest, lowDict, highDict, isBounded):
    if versionDictTest["major"] >= lowDict["major"] and versionDictTest["major"] < highDict["major"]:
        return True
    

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
            testDict = splitVersionString(versionToTest)
            lowDict = splitVersionString(ranges[0])
            highDict = splitVersionString(ranges[1])
            if testDict["major"] >= lowDict["major"] and testDict["major"] < highDict["major"]:
                return True
            elif testDict["major"] > highDict["major"] or testDict["major"] < lowDict["major"]:
                return False
            else:
                if testDict["minor"] < highDict["minor"]:
                    return True
                elif testDict["minor"] > highDict["minor"]:
                    return False
                else:
                    if testDict["patch"] <= highDict["patch"]:
                        return True
                    else:
                        return False
        except Exception as e:
            raise Exception("Bounded range error.", str(e))

    elif "^" in versionTestAgainst: # carat version range
        try:
            lowRange = versionTestAgainst[1:]
            lowDict = splitVersionString(lowRange)
            highDict = splitVersionString(lowRange)
            testDict = splitVersionString(versionToTest)

            if lowDict["major"] > 0:
                highDict["major"] = lowDict["major"] + 1
            elif lowDict["minor"] > 0:
                highDict["minor"] = lowDict["minor"] + 1
            else:
                highDict["patch"] = lowDict["patch"] + 1

            if testDict["major"] >= lowDict["major"] and testDict["major"] < highDict["major"]:
                return True
            elif testDict["major"] > highDict["major"] or testDict["major"] < lowDict["major"]:
                return False
            else:
                if testDict["minor"] < highDict["minor"]:
                    return True
                elif testDict["minor"] > highDict["minor"]:
                    return False
                else:
                    if testDict["patch"] < highDict["patch"]:
                        return True
                    else:
                        return False
        except Exception as e:
            raise Exception("Carat range error.", str(e))


    elif "~" in versionTestAgainst: # tilde version range
        try:
            lowRange = versionTestAgainst[1:]
            lowDict = splitVersionString(lowRange)
            highDict = splitVersionString(lowRange)
            testDict = splitVersionString(versionToTest)
            if lowDict["minor"] > 0 or lowDict["patch"] > 0:
                highDict["minor"] = lowDict["minor"] + 1
            else:
                highDict["major"] = lowDict["major"] + 1
            
            if lowDict["major"] > 0:
                highDict["major"] = lowDict["major"] + 1
            elif lowDict["minor"] > 0:
                highDict["minor"] = lowDict["minor"] + 1
            else:
                highDict["patch"] = lowDict["patch"] + 1

            if testDict["major"] >= lowDict["major"] and testDict["major"] < highDict["major"]:
                return True
            elif testDict["major"] > highDict["major"] or testDict["major"] < lowDict["major"]:
                return False
            else:
                if testDict["minor"] < highDict["minor"]:
                    return True
                elif testDict["minor"] > highDict["minor"]:
                    return False
                else:
                    if testDict["patch"] < highDict["patch"]:
                        return True
                    else:
                        return False
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
        package_list = create_package_list_dict()
        packages = package_list.items()
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
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = bucket.list_blobs()
        for blob in blobs:
            blob.delete()
        
        app_service.reset()

        return {}, 200
    except Exception as e:
        return {"Exception": str(e), "args": e.args}, 401



if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)


