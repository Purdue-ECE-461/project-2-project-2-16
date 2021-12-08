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

    raise Exception("time out")


def GitRequest(owner, repo):
    address = f"https://api.github.com/repos/{owner}/{repo}"
    # api.github.com/user/repos
    r = requests.get(address, headers=headers, params=params)
    return r.json()


def get_ramp_up(json):
    try:
        hasWiki = json['has_wiki']
        if hasWiki is False:
            return 0
        else:
            return 1
    except:
        return 0


def get_bus_factor(json):
    watch = json["watchers"]
    print("Watcers: " + str(watch))
    if watch > 1000:
        return 1
    
    return watch / 1000
    #contri_url = json['contributors_url']
    #r = requests.get(contri_url)
    #print(r.json())
    #print("bus factor score: " + str(len(r.json())))
    #return len(r.json())
    return .5


def get_responsive_score(json):
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
    have_license = json['license']
    if have_license is None:
        return 0
    else:
        return 1


def get_correctness(json, git_url, repo_name):
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
    return get_dep(jsonData)

def calculator(json_dict, url, repo, git_url, jsonData):
    try:
        ramp_up_score = get_ramp_up(json_dict)
    except:
        raise Exception("Ramp up error")
    # correctness_score = get_correctness(json) #this calls another program, and test the test case
    try:
        bus_factor = get_bus_factor(json_dict)
    except:
        raise Exception("bus factor error")

    #time out the correctness function, because it uses ML regression, it might take too long
    try:
        correctness = get_correctness(json_dict, git_url, repo)
    except Exception as exc:
        correctness = 0.5

    try:
        responsive_score = get_responsive_score(json_dict)
    except:
        raise Exception("response error")
    try:
        lic = get_license(json_dict)
    except:
        raise Exception("license error")

    try:
        dep_score = get_dep_score(jsonData)
    except:
        raise Exception("Dep error")

    # asdfasdf
    try:
        net = sum([weights["ramp-up"] * ramp_up_score, weights["correct"] * correctness, weights["bus-factor"] * bus_factor, weights["maintainer"] * responsive_score, weights["license"] * lic, weights["dependencies"] * dep_score])
        results[url] = [net, ramp_up_score, correctness, bus_factor, responsive_score, lic, dep_score]
    except Exception as e:
        raise Exception("Net score error", str(e))
    pass


def url_to_user(url):
    try:
        if 'github' in url:
            s = url.split("/")
            return s[-2], s[-1], url  ##user, repo
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


        pass


def set_print_ordered():

    scoreList = list(results.items())
    scoreList.sort(key=lambda x:x[1][0])
   # sorted_values = sorted(results.values(), key=lambda x: x[0])[::-1]  # Sort the values adopted from :https://stackabuse.com/how-to-sort-dictionary-by-value-in-python/
    #print(scoreList)

    # for i in sorted_values:
    #     for k in results.keys():
    #         if results[k] == i:
    #             sorted_dict[k] = results[k]
    #             break

    # max_list = [0, 0, 0, 0, 0]
    # for key in sorted_dict:
    #     for j in range(1, 6):
    #         if max_list[j - 1] < sorted_dict[key][j]:
    #             max_list[j - 1] = sorted_dict[key][j]

    # for key in sorted_dict:
    #     for j in range(1, 5):
    #         if max_list[j - 1] == 0:
    #             sorted_dict[key][j] = 1
    #         else:
    #             sorted_dict[key][j] = sorted_dict[key][j] / max_list[j - 1]

    # for key in sorted_dict:
    #     sorted_dict[key][0] = sorted_dict[key][0] / sum(weights.values())

    return scoreList

def print_score():
    sorted_list = set_print_ordered()

    for x in sorted_list:
        print(x[0] + " %.2f %.2f %.2f %.2f %.2f %.2f" % (x[1][0], x[1][1], x[1][2], x[1][3], x[1][4], x[1][5]))

    # print("URL NET_SCORE RAMP_UP_SCORE CORRECTNESS_SCORE BUS_FACTOR_SCORE RESPONSIVE_MAINTAINER_SCORE LICENSE_SCORE")
    # for key in sorted_dict:
    #     print(key, end=" ")
    #     for i in sorted_dict[key]:
    #         print(i, end=" ")
    #     print("")

def get_score(user_input, jsonData):
    fp = open(user_input, "r")
    urls = fp.readlines()
    print("stripped urls")
    for url in urls:
        url = url.strip()
        results[url] = []
        owner, repo, git_url= url_to_user(url)
        json = GitRequest(owner, repo)
        print("completed json request for repo: " + repo)
        calculator(json, url, repo, git_url, jsonData)
        print("calculated score for repo: " + repo)

    print_score()

def scoreUrl(url, jsonData):
    url = url.strip()
    results[url] = []
    try:
        owner, repo, git_url = url_to_user(url)
    except Exception as e:
        raise Exception("Url to user fail", str(e), str(url), str(type(url)))
    try:
        json = GitRequest(owner, repo)
    except Exception as e:
        raise Exception("GitRequest fail", str(e))
    try:
        calculator(json, url, repo, git_url, jsonData)
    except:
        raise Exception("calculator error")

    #print_score()

    return results[url]

def getScores():
    return results