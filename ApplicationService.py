from google.cloud import storage
from dotenv import load_dotenv
import os
import zipfile

class ApplicationService:
    def __init__(self):
        self.registry = None
        self.logger = None
        self.scorer = None
        self.authService = None
        load_dotenv()
        pass

    def upload(packageList, debloatBool = False):
        # take a list of packages and upload them all to the registry with an optional debloat parameter
        # upload files one at a time or in a zip? *I'm thinking a zip*
        storageClient = storage.Client()
        bucketName = os.getenv("BUCKET_NAME")
        bucket = storageClient.bucket(bucketName)
        zipRef = zipfile.ZipFile(zipFileName, 'w')
        for p in packageList:
            zipRef.write(p)
        zipRef.close()
        fileToUpload = bucket.blob(packageListName) # name of storage object goes here
        fileToUpload.upload_from_filename(zipFilePath) # path to local file
        pass

    def update(packageList, debloatBool = False):
        # update a list of packages in registry with an optional debloat parameter
        pass

    def rate(packageList):
        # score a list of packages
        pass

    def download(packageList):
        # download a list of packages from the existing repo
        pass

    def fetchHistory(packageList):
        # get history (of this registry) for each package in the package list
        pass

    def ingest(packageList):
        # ingest a module into the registry
        pass

    def audit(packageList):
        # audit a list of packages of the current registry
        pass

    def search(urlString):
        # search the registry for a module
        pass

    def newUser(uploadPerm, downloadPerm, searchPerm, adminPerm):
        # creates a new user in the registry system
        pass

    def removeUser(userToDelete):
        # removes an existing user in the system
        pass

    def reset():
        # resets the registry to the starting state
        pass


