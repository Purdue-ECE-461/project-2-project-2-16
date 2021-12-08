from google.cloud import storage
from dotenv import load_dotenv
import os
import zipfile
import json
from analysis import *
from pathlib import Path

class ApplicationService:
    def __init__(self):
        self.registry = None
        self.logger = None
        self.scorer = None
        self.authService = None
        self.bucketName = "ece-461-project-2-registry"
        pass

    def upload(self, packageList, debloatBool = False):
        # take a list of packages and upload them all to the registry with an optional debloat parameter
        # upload files one at a time or in a zip? *I'm thinking a zip*
        #storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
        storageClient = storage.Client()
        #bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(self.bucketName)
        for x in packageList:
            splitString = x.split("/")
            fileToUpload = bucket.blob(splitString[-1]) # name of storage object goes here
            fileToUpload.upload_from_filename(x) # path to local file
        pass

    def update(self, packageList, debloatBool = False):
        # update a list of packages in registry with an optional debloat parameter
        storageClient = storage.Client()
        #bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(self.bucketName)
        bucket = storageClient.bucket(bucketName)
        for p in packageList:
            splitString = p.split("/")
            fileToCheck = bucket.blob(splitString[-1])
            if (fileToCheck.exists()):
                self.upload(p)
        pass

    def rate(self, packageList):
        try:
        # score a list of packages (zip files)
            results = []

            currentDir = os.getcwd()
            newDir = "unzipped_repo"
            newPath = os.path.join(currentDir, newDir)

            if not os.path.exists(newPath):
                os.makedirs(newPath)

            for p in packageList:
                resultsForRepo = dict()

                try:
                    with zipfile.ZipFile(p, "r") as zipRef:
                        fileList = zipRef.namelist()
                        splitDir = fileList[0].split("/")
                        zipRef.extractall(newPath)
                        unzipFilePath = os.path.join(newPath, splitDir[0])
                except:
                    raise Exception("Read in rate error")
                # error if package.json does not exist
                
                packageJsonPath = os.path.join(unzipFilePath, "package.json")
                try:
                    with open(packageJsonPath, "r") as fptr:
                        jsonData = json.load(fptr)
                except:
                    raise Exception(os.listdir(newPath + "/underscore-master"))

                repoUrl = jsonData["repository"]["url"]
                splitUrl = repoUrl.split("/")
                author = splitUrl[-2]
                repo = splitUrl[-1]
                repoUrl = "https://github.com/" + author + "/" + repo
                try:
                    score = scoreUrl(repoUrl, author, repo, jsonData)
                except Exception as e:
                    raise Exception("score Url does not work", str(e), repoUrl)
                resultsForRepo[p] = score
                results.append(resultsForRepo)
                

            
            return results
        except Exception as e:
            raise Exception("rate error", str(e), e.args)
        

    def download(self, packageList):
        # download a list of packages from the existing repo
        storageClient = storage.Client()
        #bucketName = "ece-461-project-2-registry"
        bucket = storageClient.bucket(self.bucketName)
        downloadPath = str(os.path.join(os.getcwd(), "Downloads"))

        if not os.path.exists(downloadPath):
            os.makedirs(downloadPath)

        for x in packageList:
            splitString = x.split("/")
            fileToDownload = bucket.blob(splitString[-1]) # name of storage object goes here
            print(downloadPath + "/" + splitString[-1])
            fileToDownload.download_to_filename(downloadPath + "/" + splitString[-1]) # path to local file
        pass


    def fetchHistory(self, packageList):
        # get history (of this registry) for each package in the package list
        pass

    def ingest(self, package):
        # ingest a module into the registry
        # score repo, if net score > x, upload
        results = self.rate(package)
        for p in package:
            if results[p][0] > .5: # ingest score
                self.upload(p)
                print("Module ingested.")
                return True
            else:
                print("Module was not trustworthy enough to be ingested.")
                print("Module scored: " + str(results[p][0]))
                print("Cutoff is: .5")
                return False
        pass

    def audit(self, packageList):
        # audit a list of packages of the current registry
        pass

    def search(self, urlString):
        # search the registry for a module
        pass

    def newUser(self, uploadPerm, downloadPerm, searchPerm, adminPerm):
        # creates a new user in the registry system
        pass

    def removeUser(self, userToDelete):
        # removes an existing user in the system
        pass

    def reset(self):
        # resets the registry to the starting state
        pass


