'''Supporting class that helps run the API in Routes.py'''
import os
import zipfile
import json
from google.cloud import storage
from analysis import scoreUrl

class ApplicationService:
    '''Application Service has helper functions that support the flask API in Routes.py'''
    def __init__(self):
        self.registry = None
        self.logger = None
        self.scorer = None
        self.auth_service = None
        self.bucket_name = "ece-461-project-2-registry"

    def upload(self, packageList, debloat_bool = False):
        '''Uploads a list of packages to google cloud storage'''
        if debloat_bool:
            print("Debloat")
        # take a list of packages and upload them all to the registry with an option debloat param
        # upload files one at a time or in a zip? *I'm thinking a zip*
        #storage_client = storage.Client.from_service_account_json("./google-cloud-creds.json")
        storage_client = storage.Client()
        #bucket_name = "ece-461-project-2-registry"
        bucket = storage_client.bucket(self.bucket_name)
        for package in packageList:
            split_string = package.split("/")
            file_to_upload = bucket.blob(split_string[-1]) # name of storage object goes here
            file_to_upload.upload_from_filename(package) # path to local fil
            
    def update(self, packageList, debloat_bool = False):
        '''Updates an existing package in google cloud storage registry'''
        if debloat_bool:
            print("Debloat")
        # update a list of packages in registry with an optional debloat parameter
        storage_client = storage.Client()
        #bucket_name = "ece-461-project-2-registry"
        bucket = storage_client.bucket(self.bucket_name)
        for p in packageList:
            splitString = p.split("/")
            fileToCheck = bucket.blob(splitString[-1])
            if fileToCheck.exists():
                self.upload(p)       

    def rate(self, packageList):
        '''Rates an existing module in our code registry'''
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
                key = p.split("/")[-1][:-4]

                with zipfile.ZipFile(p, "r") as zipRef:
                    fileList = zipRef.namelist()
                    splitDir = fileList[0].split("/")
                    zipRef.extractall(newPath)
                    unzipFilePath = os.path.join(newPath, splitDir[0])
                # error if package.json does not exist
                
                packageJsonPath = os.path.join(unzipFilePath, "package.json")
                with open(packageJsonPath, "r", encoding="utf-8") as fptr:
                    jsonData = json.load(fptr)

                repoUrl = jsonData["repository"]["url"]
                splitUrl = repoUrl.split("/")
                author = splitUrl[-2]
                repo = splitUrl[-1]
                if ".git" in repo:
                    repo = repo[:-4]
                repoUrl = "https://github.com/" + author + "/" + repo
                try:
                    score = scoreUrl(repoUrl, author, repo, jsonData)
                except Exception as e:
                    raise Exception("score Url does not work") from e
                resultsForRepo[key] = score
                results.append(resultsForRepo)
                

            
            return results
        except Exception as e:
            raise Exception("rate error") from e
        

    def download(self, packageList):
        '''Downloads a module from our code registry'''
        # download a list of packages from the existing repo
        storage_client = storage.Client()
        #bucket_name = "ece-461-project-2-registry"
        bucket = storage_client.bucket(self.bucket_name)
        downloadPath = str(os.path.join(os.getcwd(), "Downloads"))

        if not os.path.exists(downloadPath):
            os.makedirs(downloadPath)

        for x in packageList:
            splitString = x.split("/")
            fileToDownload = bucket.blob(splitString[-1]) # name of storage object goes here
            print(downloadPath + "/" + splitString[-1])
            fileToDownload.download_to_filename(downloadPath + "/" + splitString[-1]) # path to local file
        


    def fetchHistory(self, packageList):
        # get history (of this registry) for each package in the package list
        pass

    def ingest(self, packageList):
        # ingest a module into the registry
        # score repo, if net score > x, upload
        results = self.rate(packageList)
        filesToUpload = []
        for i, p in enumerate(packageList):
            pack_id = p.split("/")[-1][:-4]
            if results[i][pack_id][0] > .5: # ingest score
                filesToUpload.append(p)
        
        if not filesToUpload:
            return False

        self.upload(filesToUpload)

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


