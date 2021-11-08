import zipfile

class Package:
    def __init__(self, zipFile):
        self.zipFile = zipFile
        self.isUnzipped = False
        pass

    def unzip(self):
        # make directory to unzip to
        with zipfile.ZipFile(self.zipFile, 'r') as zip_ref:
            zip_ref.extractall(directory_to_extract_to)

