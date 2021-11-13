from google.cloud import storage
from dotenv import load_dotenv
import os
import zipfile
import json
from analysis import *

class ApplicationService:
    def __init__(self):
        self.registry = None
        self.logger = None
        self.scorer = None
        self.authService = None
        load_dotenv()
        pass

    def upload(self, packageList, debloatBool = False):
        # take a list of packages and upload them all to the registry with an optional debloat parameter
        # upload files one at a time or in a zip? *I'm thinking a zip*
        storageClient = storage.Client()
        bucketName = os.getenv("BUCKET_NAME")
        bucket = storageClient.bucket(bucketName)
        #zipRef = zipfile.ZipFile(zipFileName, 'w')
        #for p in packageList:
        #    zipRef.write(p)
        #zipRef.close()
        for x in packageList:
            splitString = x.split("/")
            fileToUpload = bucket.blob(splitString[-1]) # name of storage object goes here
            fileToUpload.upload_from_filename(x) # path to local file
        pass

    def update(self, packageList, debloatBool = False):
        # update a list of packages in registry with an optional debloat parameter
        pass

    def rate(self, packageList):
        # score a list of packages (zip files)
        results = []

        currentDir = os.getcwd()
        newDir = "unzipped_repo"
        newPath = os.path.join(currentDir, newDir)

        if not os.path.exists(newPath):
            os.makedirs(newPath)

        for p in packageList:
            resultsForRepo = dict()

            print(p)

            with zipfile.ZipFile(p, "r") as zipRef:
                zipRef.extractall(newPath)
                
            # error if package.json does not exist
            fileName = p.split("/")[-1]
            fileName = fileName[:-4]
            fptr = open(newPath + "/" + fileName + '/package.json')
            jsonData = json.load(fptr)
            repoUrl = jsonData["homepage"]
            score = scoreUrl(repoUrl)
            resultsForRepo[p] = score
            results.append(resultsForRepo)

        
        return results
        

    def download(self, packageList):
        # download a list of packages from the existing repo
        storageClient = storage.Client()
        bucketName = os.getenv("BUCKET_NAME")
        bucket = storageClient.bucket(bucketName)
        blob = bucket.blob(nameOfFileToDownload)
        blob.download_to_filename(destinationFile)
        pass

    def fetchHistory(self, packageList):
        # get history (of this registry) for each package in the package list
        pass

    def ingest(self, packageList):
        # ingest a module into the registry
        # score repo, if net score > x, upload
        results = ApplicationService.rate(packageList)
        for p in packageList:
            if results[p][0] > .5: # ingest score
                ApplicationService.upload(p)
                print("Module ingested.")
            else:
                print("Module was not trustworthy enough to be ingested.")
                print("Module scored: " + str(results[p][0]))
                print("Cutoff is: .5")
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


