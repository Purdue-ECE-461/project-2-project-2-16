'''
Calculates scores for packages
'''
import requests
import subprocess
import os
import signal
from requests.models import encode_multipart_formdata
import json
from datetime import datetime
from dotenv import load_dotenv
from dep_func import *

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # a back-up token just in case
results = dict()  # follow this format: {url: [net, ramp, corr, bus, respon, responsive, license], ...}

headers = {
    'content-type': 'application/json',
    'Accept-Charset': 'UTF-8',
    'Authorization': f'token {GITHUB_TOKEN}'}

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
    '''
    Raises time out exception
    '''
    raise Exception("time out")


def GitRequest(owner, repo):
    '''
    Returns json of GitHub repo
    '''
    address = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(address, headers=headers, params=params)
    return r.json()

def get_ramp_up(json):
    '''
    Calculates Ramp_Up Score
    '''
    try:
        hasWiki = json['has_wiki']
        if hasWiki is False:
            return 0
        else:
            return 1
    except:
        return 0

def get_bus_factor(json):
    '''
    Calculates Bus_Factor Score
    '''
    try:
        watch = json["watchers_count"]
        if watch > 1000:
            return 1     
        return watch / 1000
    except:
        raise Exception("Json: ", json)
    return .5

def get_responsive_score(json):
    '''
    Calculates Responsiveness Score
    '''
    last_day = json["updated_at"]
    last_day = last_day.replace("T", " ")
    last_day = last_day.replace("Z", " ")
    now = datetime.now().day
    last_day = datetime.strptime(last_day, "%Y-%m-%d %H:%M:%S ").day  # 2021-10-03T04:24:26Z
    day_delta = now - last_day
    score = 1 - 0.1 * day_delta
    if score < 0:
        score = 0
    return score

def get_license(json):
    '''
    Calculates License Score
    '''
    have_license = json['license']
    if have_license is None:
        return 0
    else:
        return 1

def get_correctness(json, git_url, repo_name):
    '''
    Calculates Correctness Score
    '''
    stars = json["stargazers_count"]    
    scoreValue = 0
    if stars > 1000:
        scoreValue = .5
    elif stars > 500:
        scoreValue = .3
    elif stars > 250:
        scoreValue = .2
    elif stars > 50:
        scoreValue = .1

    tempStarNum = stars - 1000
    if tempStarNum >= 500:
        scoreValue = scoreValue + ((tempStarNum / 500) / 10)
    if scoreValue > 1:
        scoreValue = 1

    return scoreValue

def get_dep_score(jsonData):
    '''
    Calls get_dep for Dependency Score
    '''
    return get_dep(jsonData)

def calculator(json_dict, url, repo, git_url, jsonData):
    '''
    Get's all of the scores
    '''
    try:
        ramp_up_score = get_ramp_up(json_dict)
    except Exception as e:
        raise Exception("Ramp up error", str(e))
    try:
        bus_factor = get_bus_factor(json_dict)
    except Exception as e:
        raise Exception("bus factor error", str(e))

    #time out the correctness function, because it uses ML regression, it might take too long
    try:
        correctness = get_correctness(json_dict, git_url, repo)
    except Exception as exc:
        correctness = 0.5

    try:
        responsive_score = get_responsive_score(json_dict)
    except Exception as e:
        raise Exception("response error", str(e))
    try:
        lic = get_license(json_dict)
    except Exception as e:
        raise Exception("license error", str(e))

    try:
        dep_score = get_dep_score(jsonData)
    except Exception as e:
        raise Exception("Dep error", str(e))

    try:
        net = sum([weights["ramp-up"] * ramp_up_score, weights["correct"] * correctness, weights["bus-factor"] * bus_factor, weights["maintainer"] * responsive_score, weights["license"] * lic, weights["dependencies"] * dep_score])
        results[url] = [net, ramp_up_score, correctness, bus_factor, responsive_score, lic, dep_score]
    except Exception as e:
        raise Exception("Net score error", str(e))

def url_to_user(url):
    '''
    Gets user and repo from URL
    '''
    try:
        if 'github' in url:
            s = url.split("/")
            return s[-2], s[-1], url    #user, repo
        else:
            page = requests.get(url)
            for line in page.text.splitlines():
                if "\"repository\":" in line:
                    temp = line.split("\"")
                    for i in temp:
                        if "github" in i:
                            return url_to_user(i)
    except Exception as e:
        raise Exception("Uncaught exception in url to user", str(e))

def set_print_ordered():
    '''
    Set the print order
    '''
    scoreList = list(results.items())
    return scoreList.sort(key=lambda x:x[1][0])

def print_score():
    '''
    Print all scores
    '''
    sorted_list = set_print_ordered()
    for x in sorted_list:
        print(x[0] + " %.2f %.2f %.2f %.2f %.2f %.2f" % (x[1][0], x[1][1], x[1][2], x[1][3], x[1][4], x[1][5]))

def get_score(user_input, jsonData):
    '''
    Calls print_score to print the scores
    '''
    fp = open(user_input, "r")
    urls = fp.readlines()
    print("stripped urls")
    for url in urls:
        url = url.strip()
        results[url] = []
        owner, repo, git_url= url_to_user(url)
        json = GitRequest(owner, repo)
        print(json)
        print("completed json request for repo: " + repo)
        print("calculated score for repo: " + repo)
    print_score()

def scoreUrl(url, owner, repo, jsonData):
    '''
    Get's the scores for a URL
    '''
    results[url] = []
    try:
        json = GitRequest(owner, repo)
    except Exception as e:
        raise Exception("GitRequest fail", str(e))
    try:
        calculator(json, url, repo, url, jsonData)
    except Exception as e:
        raise Exception("calculator error", str(e))
    return results[url]

def getScores():
    '''
    Returns the scores
    '''
    return results