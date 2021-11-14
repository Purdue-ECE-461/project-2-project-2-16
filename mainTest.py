from ApplicationService import *
from Server import *
import sys

def serverTest():
    server = Server()
    server.listen()

def main():
    if len(sys.argv) != 2:
        exit(1)
    else:
        appService = ApplicationService()
        packageList = sys.argv[1:]
        for p in packageList:
            print(p)
        appService.rate(packageList)
        print("Rate finished!")
        print("Trying to upload")
        appService.upload(packageList)
        print("Finished upload")
        print("Trying to download")
        appService.download(packageList)
        print("Finished download")


if __name__ == '__main__':
    main()