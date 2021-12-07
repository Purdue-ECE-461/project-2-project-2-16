import requests
import re

class Repo:
    def __init__(self, author, repoName, url, githubUrl):
        self.url = url
        self.author = author
        self.repo = repoName
        self.netScore = 0
        self.rampUpScore = 0
        self.correctScore = 0
        self.busFactorScore = 0
        self.responsiveMaintainScore = 0
        self.licenseScore = 0
        self.githubUrl = githubUrl
        pass

    def printScores(self):
        print(self.url + " %.2f %.2f %.2f %.2f %.2f %.2f" % (self.netScore, self.rampUpScore, self.correctScore, self.busFactorScore, self.responsiveMaintainScore, self.licenseScore))
        return True

class FileParser:
    def __init__(self, fp):
        self.list_of_repos = []
        self.URLs = []
        self.GitHub_URLS = []

        self.create_list(fp)
        self.convert_to_github()
        self.strip_urls()
 
    def create_list(self, fp):
        # self.URLs <-- list of URLs
        try:
            file1 = open(fp, 'r')
            for line in file1.readlines():
                self.URLs.append(line.strip())
            file1.close()
        except Exception as e:
            self.logger.logToFile("Make sure the inputted test file exists and the path is correct.", "This error occurs in FileParser.py in the create_list function, probably due to an incorrect input file.")
            raise Exception('Failure in create_list in FileParser.py. Check that the passed in file exists.', e.args)

    def convert_to_github(self):
        # Converts npjms URLs to GitHub URLs
        try:
            for url in self.URLs:
                if "github.com" in url:
                    self.GitHub_URLS.append(url)
                else:
                    r = requests.get(url)
                    if "github.com" in r.text:
                        self.GitHub_URLS.append(re.search(r'"repository":"(.+?)",', r.text)[1])
                    else:
                        self.GitHub_URLS.append(None)
        except Exception as e:
            self.logger.logToFile("Npmjs URLs could not be converted to Github URLs", "In FileParser.py, the inputted URLs could not be parsed into Github URLs in the convert_to_github()")
            raise Exception("Npmjs URLs could not be parsed in FileParser.py. Check the npmjs URLs", e.args)

    def strip_urls(self):
        # Extracts Author and Repo Name from GitHub URLs
        try:
            for url, actualUrl in zip(self.GitHub_URLS, self.URLs):
                author, repo = url.split("github.com/",1)[1].split("/",1)
                self.list_of_repos.append(Repo(author, repo, actualUrl, url))
        except Exception as e:
            self.logger.logToFile("Author and repo could not be extracted from URL", "A url may not contain \"github.com\" and\or could not be split correctly")
            raise Exception("strip_urls failure in FileParser.py. No author/repo could be pulled from the given URL. Check URLs and try again.", e.args)