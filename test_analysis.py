import sys
import requests
from FileParser import FileParser

def main():
    fp = FileParser(sys.argv[1])
    #for repos in fp.list_of_repos:
    #    print(repos.repo)
    #print(fp.GitHub_URLS[0])
    #json = GitRequest(cloudinary, cloudinary_npm)
    #r = requests.get('https://api.github.com/user',  auth=('user', 'pass'))
    r = requests.get('https://api.github.com/cloudinary/cloudinary_npm',  auth=('user', 'pass'))
    #https://github.com/cloudinary/cloudinary_npm

    print(r.json()['devDependencies'])
    
    # Tried pipdeptree?
    
    # Get dependencies (Drew advice):
    # Use requests
    # Call npm api
        # Maybe get entire module or the dependencies
            # Module --> url
    
    # All nppm modules have "package.json" which lists dependencies
        # https://github.com/jashkenas/underscore/blob/master/package.json

    # package lock . json ??   Single dependency tree (don't usae)
    # json.load:    json -> python object (dictionary for package.json)

    # ApplicationService.py > rate() > bottom paragraph
        # Drew's attempt at getting the package.json file


    #urlFile = sys.argv[1]
    #results = {}

    #fp = open(urlFile, "r")
    #urls = fp.readlines()
    #fp.close()
    #for url in urls:
    #    url = url.strip()
        

        #print(url)
        #results[url] = []
        #owner, repo, git_url = url_to_user(url)
        #json = GitRequest(owner, repo)
        #result = calculator(json, url, repo, git_url)


    

if __name__ == '__main__':
    main()