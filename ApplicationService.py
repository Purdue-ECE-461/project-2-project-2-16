'''Application service provides helper functionality for the flask API in Routes.py'''
import os
import zipfile
import json
from analysis import scoreUrl
from google.cloud import storage

class ApplicationService:
    '''Application service provides helper functionality for the flask API in Routes.py'''
    def __init__(self):
        self.bucket_name = "ece-461-project-2-registry"

    def upload(self, packageList, debloat_bool = False):
        '''Uploads a file to our registry in GCS'''
        if debloat_bool:
            print("Debloat")
        # take a list of packages and upload them to the registry with an optional debloat param
        # upload files one at a time or in a zip? *I'm thinking a zip*
        #storage_client = storage.Client.from_service_account_json("./google-cloud-creds.json")
        storage_client = storage.Client()
        #bucket_name = "ece-461-project-2-registry"
        bucket = storage_client.bucket(self.bucket_name)
        for package in packageList:
            split_string = package.split("/")
            file_upload = bucket.blob(split_string[-1]) # name of storage object goes here
            file_upload.upload_from_filename(package) # path to local file

    def update(self, packageList, debloat_bool = False):
        '''Update a file in the GCS registry'''
        if debloat_bool:
            print("Debloat")
        # update a list of packages in registry with an optional debloat parameter
        storage_client = storage.Client()
        #bucket_name = "ece-461-project-2-registry"
        bucket = storage_client.bucket(self.bucket_name)
        for p in packageList:
            split_string = p.split("/")
            file_check = bucket.blob(split_string[-1])
            if file_check.exists():
                self.upload(p)

    def rate(self, packageList):
        '''Rate packages in registry'''
        try:
        # score a list of packages (zip files)
            results = []
            current_dir = os.getcwd()
            new_dir = "unzipped_repo"
            new_path = os.path.join(current_dir, new_dir)
            if not os.path.exists(new_path):
                os.makedirs(new_path)

            for package in packageList:
                results_for_repo = dict()
                key = package.split("/")[-1][:-4]

                try:
                    with zipfile.ZipFile(package, "r") as zip_ref:
                        file_list = zip_ref.namelist()
                        split_dir = file_list[0].split("/")
                        zip_ref.extractall(new_path)
                        unzip_filepath = os.path.join(new_path, split_dir[0])
                except Exception as exc:
                    raise Exception("Read in rate error", str(package)) from exc
                # error if package.json does not exist            
                packageJsonPath = os.path.join(unzip_filepath, "package.json")
                try:
                    with open(packageJsonPath, "r") as fptr:
                        jsonData = json.load(fptr)
                except:
                    raise Exception(os.listdir(new_path + "/underscore-master"))
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
                    raise Exception("score Url does not work", str(e), repoUrl)
                results_for_repo[key] = score
                results.append(results_for_repo)          
            return results
        except Exception as e:
            raise Exception("rate error", str(e), e.args)
        
    def download(self, packageList):
        # download a list of packages from the existing repo
        storage_client = storage.Client()
        #bucket_name = "ece-461-project-2-registry"
        bucket = storage_client.bucket(self.bucket_name)
        downloadPath = str(os.path.join(os.getcwd(), "Downloads"))

        if not os.path.exists(downloadPath):
            os.makedirs(downloadPath)

        for x in packageList:
            split_string = x.split("/")
            fileToDownload = bucket.blob(split_string[-1]) # name of storage object goes here
            print(downloadPath + "/" + split_string[-1])
            fileToDownload.download_to_filename(downloadPath + "/" + split_string[-1]) # path to local file
        pass

    def fetchHistory(self, packageList):
        # get history (of this registry) for each package in the package list
        pass

    def ingest(self, packageList):
        # ingest a module into the registry
        # score repo, if net score > x, upload
        try:
            results = self.rate(packageList)
            filesToUpload = []
            for i, p in enumerate(packageList):
                id = p.split("/")[-1][:-4]
                if results[i][id][0] > .5: # ingest score
                    filesToUpload.append(p)
            
            if not filesToUpload:
                return False

            self.upload(filesToUpload)
        except Exception as e:
            raise Exception("ingest fail", str(e))
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
