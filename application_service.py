'''Application service provides helper functionality for the flask API in Routes.py'''
import os
import zipfile
import json
from google.cloud import storage
from analysis import scoreUrl

class ApplicationService:
    '''Application service provides helper functionality for the flask API in Routes.py'''
    def __init__(self):
        self.bucket_name = "ece-461-project-2-registry"

    def upload(self, package_list, debloat_bool = False):
        '''Uploads a file to our registry in GCS'''
        if debloat_bool:
            print("Debloat")
        # take a list of packages and upload them to the registry with an optional debloat param
        # upload files one at a time or in a zip? *I'm thinking a zip*
        #storage_client = storage.Client.from_service_account_json("./google-cloud-creds.json")
        storage_client = storage.Client()
        #bucket_name = "ece-461-project-2-registry"
        bucket = storage_client.bucket(self.bucket_name)
        for package in package_list:
            split_string = package.split("/")
            file_upload = bucket.blob(split_string[-1]) # name of storage object goes here
            file_upload.upload_from_filename(package) # path to local file

    def update(self, package_list, debloat_bool = False):
        '''Update a file in the GCS registry'''
        if debloat_bool:
            print("Debloat")
        # update a list of packages in registry with an optional debloat parameter
        storage_client = storage.Client()
        #bucket_name = "ece-461-project-2-registry"
        bucket = storage_client.bucket(self.bucket_name)
        for package in package_list:
            split_string = package.split("/")
            file_check = bucket.blob(split_string[-1])
            if file_check.exists():
                self.upload(package)

    def rate(self, package_list):
        '''Rate packages in registry'''
        try:
        # score a list of packages (zip files)
            results = []
            current_dir = os.getcwd()
            new_dir = "unzipped_repo"
            new_path = os.path.join(current_dir, new_dir)
            if not os.path.exists(new_path):
                os.makedirs(new_path)

            for package in package_list:
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
                package_json_path = os.path.join(unzip_filepath, "package.json")
                with open(package_json_path, "r", encoding="utf-8") as fptr:
                    json_data = json.load(fptr)
                repo_url = json_data["repository"]["url"]
                split_url = repo_url.split("/")
                author = split_url[-2]
                repo = split_url[-1]
                if ".git" in repo:
                    repo = repo[:-4]

                repo_url = "https://github.com/" + author + "/" + repo
                score = scoreUrl(repo_url, author, repo, json_data)
                results_for_repo[key] = score
                results.append(results_for_repo)
            return results
        except Exception as exc:
            raise Exception("rate error", str(exc), exc.args) from exc

    def download(self, package_list):
        '''Downloads a package from registry in GCS'''
        # download a list of packages from the existing repo
        storage_client = storage.Client()
        bucket = storage_client.bucket(self.bucket_name)
        download_python = str(os.path.join(os.getcwd(), "Downloads"))

        if not os.path.exists(download_python):
            os.makedirs(download_python)

        for package in package_list:
            split_string = package.split("/")
            file_download = bucket.blob(split_string[-1]) # name of storage object goes here
            print(download_python + "/" + split_string[-1])
            file_download.download_to_filename(download_python + "/" + split_string[-1])

    def ingest(self, package_list):
        '''Ingests a module into the registry'''
        # ingest a module into the registry
        # score repo, if net score > x, upload
        results = self.rate(package_list)
        files_upload = []
        for i, package in enumerate(package_list):
            package_id = package.split("/")[-1][:-4]
            if results[i][package_id][0] > .5: # ingest score
                files_upload.append(package)

        if not files_upload:
            return False

        self.upload(files_upload)

        return True
