import collections

import git
import sys
import requests
from datetime import datetime
import subprocess
import os
import signal
import gitrisky
from collections import deque


gitAddr = "https://api.github.com/repos/"
##add weight in here in format: 'name' : weight
#Git_Token = "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"
Git_Token = "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"
#Git_Token = "ghp_nqp7EaHtK5SKzj5WEA2hRbsq6zeejjnnfuHwR"
#Git_Token = "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"

results = dict() #follow this format: {url: [net, ramp, corr, bus, respon, responsive, license], ...}

headers = {
    'content-type': 'application/json',
    'Accept-Charset': 'UTF-8',
    'Authorization': 'token %s' % Git_Token
}
weights = {
    'ramp-up': 0.1,
    'correct': 0.3,
    'maintainer': 0.3,
    'bus-factor': 0.1,
    'license': 0.1,
    'dependencies': 0.1
}

params = {
    "state": "open",
}

def handler(signum, frame): #adopted from https://stackoverflow.com/questions/492519/timeout-on-a-function-call

    raise Exception("time out")


def GitRequest(owner, repo):
    addr = gitAddr + owner + '/' + repo
    r = requests.get(addr, headers=headers, params=params)
    return r.json()

def get_ramp_up(json):
    size = json['size']
    hasWiki = json['has_wiki']
    if hasWiki is False:
        return 0
    else:
        return 1/size

def get_bus_factor(json):
    contri_url = json['contributors_url']
    r = requests.get(contri_url)
    return len(r.json())

def get_responsive_score(json):
    last_day = json["updated_at"]
    last_day = last_day.replace("T"," ")
    last_day = last_day.replace("Z", " ")
    now = datetime.now().day
    last_day = datetime.strptime(last_day, "%Y-%m-%d %H:%M:%S ").day #2021-10-03T04:24:26Z
    day_delta = now - last_day
    score = 1 - 0.1*day_delta
    if score < 0:
        score = 0
    if score > 0:
        score = 0
    return score

def get_license(json):
    have_license = json['license']
    if have_license is None:
        return 0
    else:
        return 1

def get_correctness(json,git_url,repo_name):
    dir = os.getcwd()
    dir = dir + "/cloned"
    try:
        os.mkdir(dir)
    except FileExistsError:
        pass
    os.chdir(dir)
    try:
        git.Git(dir).clone(git_url)
    except:
        pass
    os.chdir(repo_name)
    try:
        feedback = subprocess.check_output(["gitrisky", "train"])
    except Exception as e:
        return 0.5
    res = [int(i) for i in feedback.split() if i.isdigit()]
    total = res[0]
    bug = res[1]
    score = (total - bug) / total
    return score

def calculator(json_dict, url, repo, git_url):
    ramp_up_score = get_ramp_up(json_dict)
    #correctness_score = get_correctness(json) #this calls another program, and test the test case
    bus_factor = get_bus_factor(json_dict)

    #time out the correctness function, because it uses ML regression, it might take too long
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(120)
    try:
        correctness = get_correctness(json_dict, git_url, repo)
    except Exception as exc:
        correctness = 0.5

    responsive_score = get_responsive_score(json_dict)
    license = get_license(json_dict)

    net = sum([ramp_up_score, correctness, bus_factor, responsive_score, license])
    results[url] = [net, ramp_up_score, correctness, bus_factor, responsive_score, license]
    pass


def url_to_user(url):
    if 'github' in url:
        str = url.split("/")
        return str[-2], str[-1], url  ##user, repo
    else:
        page = requests.get(url)
        for line in page.text.splitlines():
            if "\"repository\":" in line:
                temp = line.split("\"")
                for i in temp:
                    if "github" in i:
                        return url_to_user(i)


        pass

def print_result(results):
    sorted_values = sorted(results.values(), reverse=True)  # Sort the values adopted from :https://stackabuse.com/how-to-sort-dictionary-by-value-in-python/
    sorted_dict = {}

    for i in sorted_values:
        for k in results.keys():
            if results[k] == i:
                sorted_dict[k] = results[k]
                break

    max_list = [0,0,0,0,0]
    for key in sorted_dict:
        for j in range(1,6):
            if max_list[j-1] < sorted_dict[key][j]:
                max_list[j-1] = sorted_dict[key][j]

    for key in sorted_dict:
        for j in range(1,5):
            if max_list[j-1] == 0:
                sorted_dict[key][j] = 1
            else:
                sorted_dict[key][j] = sorted_dict[key][j] / max_list[j-1]

    for key in sorted_dict:
        sorted_dict[key][0] = sorted_dict[key][0] / sum(weights.values())

    print("URL NET_SCORE RAMP_UP_SCORE CORRECTNESS_SCORE BUS_FACTOR_SCORE RESPONSIVE_MAINTAINER_SCORE LICENSE_SCORE")
    for key in sorted_dict:
        print(key, end=" ")
        for i in sorted_dict[key]:
            print(i, end=" ")
        print("")

if __name__ == '__main__':
    urlFile = sys.argv[1]
    fp = open(urlFile)
    urls = fp.readlines()
    for url in urls:
        url = url.strip()
        #print(url)
        results[url] = []
        owner, repo, git_url = url_to_user(url)
        json = GitRequest(owner, repo)
        result = calculator(json, url, repo, git_url)

    print_result(results)