import os
import requests
from dotenv import load_dotenv

class GitHubFetcher:
    """
    Handles fetching user and repository data from the GitHub API.
    Uses a personal access token if provided for higher rate limits.
    """
    def __init__(self, token=None):
        load_dotenv()
        self.token = token or os.getenv('GITHUB_TOKEN')
        # print('Loaded token:', self.token)  # Debug print (remove/comment for production)
        self.base_url = 'https://api.github.com'
        self.headers = {'Authorization': f'token {self.token}'} if self.token else {}

    def get_user_profile(self, username):
        """
        Fetches the public profile information for a given GitHub username.
        Returns a dict with user details.
        """
        url = f'{self.base_url}/users/{username}'
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_user_repos(self, username):
        """
        Fetches all public repositories for a given GitHub username.
        Returns a list of repository dicts.
        """
        repos = []
        page = 1
        while True:
            url = f'{self.base_url}/users/{username}/repos?per_page=100&page={page}'
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        return repos

    def get_repo_languages(self, username, repo_name):
        """
        Fetches the language breakdown for a specific repository.
        Returns a dict mapping language names to bytes of code.
        """
        url = f'{self.base_url}/repos/{username}/{repo_name}/languages'
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()