class ApplicationService:
    def __init__(self):
        self.registry = None
        self.logger = None
        self.scorer = None
        self.authService = None
        pass

    def upload(packageList, debloatBool = False):
        # take a list of packages and upload them all to the registry with an optional debloat parameter
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


