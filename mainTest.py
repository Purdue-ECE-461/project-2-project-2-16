from ApplicationService import *
import sys

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


if __name__ == '__main__':
    main()