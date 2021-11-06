import git
import gitrisky
import os
import subprocess
import sys

def test_all():
    dir = os.getcwd()
    dir = dir + "/cloned"
    repo_name = "cloudinary_npm"

    try:
        os.mkdir(dir)
    except FileExistsError:
        pass

    os.chdir(dir)
    try:
        git.Git(dir).clone("https://github.com/cloudinary/cloudinary_npm")
    except:
        pass
    os.chdir(repo_name)
    try:
        feedback = subprocess.check_output(["gitrisky", "train"])
    except:
        score = 0
    res = [int(i) for i in feedback.split() if i.isdigit()]
    total = res[0]
    bug = res[1]
    score = (total - bug)/total

    print(score)
#git.Git("")
