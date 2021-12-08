import requests
import dotenv
import os

def main():
    dotenv.load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
   
    url = "https://api.github.com/repos/jashkenas/" + repo + "/zipball"

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token ' + token}

    r = requests.get(url, headers=headers, allow_redirects=True)

if __name__ == "__main__":
    main()