import json
import math
import os
import sys
import subprocess

import requests

from common import char_matrix
from dating import sunday_at_start
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

skip_weeks_from_front = 2
skip_days_from_above = 1
commit_per_day_for_highlighted = 20
commit_per_day_for_shadow = 0

OWNER = "iamvinitk"
REPO_NAME = "text-on-github"
TOKEN = os.getenv("GITHUB_TOKEN")

CREATE_ENDPOINT = "https://api.github.com/user/repos"
DELETE_ENDPOINT = "https://api.github.com/repos/{owner}/{repo}"


def get_text_input():
    return "HIRE ME!"
    # if len(sys.argv) > 1:
    #     return sys.argv[1]
    # else:
    #     return input("Enter the text string: ")


def construct_printing_matrix(text_input):
    m, n = len(char_matrix['a']), len(char_matrix['a'][0])

    space_between_chars = 2

    printing_matrix = [[] for _ in range(m)]

    for ch in text_input:
        char_matrixForCh = char_matrix.get(ch, char_matrix['?'])
        for i in range(m):
            printing_matrix[i].extend(char_matrixForCh[i])
        for i in range(space_between_chars):
            for j in range(m):
                printing_matrix[j].append(' ')

    for i in range(m):
        print(''.join(printing_matrix[i]))

    return printing_matrix


def get_commit_dates(printing_matrix, start_date):
    commit_dates = []

    for j in range(len(printing_matrix[0])):
        reference_date = start_date + timedelta(days=skip_days_from_above)
        for i in range(len(printing_matrix)):
            if printing_matrix[i][j] == '*':
                commit_dates.append(reference_date)
            reference_date += timedelta(days=1)
        start_date += timedelta(weeks=1)
    return commit_dates


def run_git_command(cmd):
    result = subprocess.run(cmd, shell=True, check=True, text=True)
    return result


def do_the_commits(commit_dates, commit_per_day=1):
    count = 0
    for commit_date in commit_dates:
        for i in range(commit_per_day):
            formatted_date = commit_date.strftime("%a %b %d %H:%M %Y %z")
            formatted_date_with_timezone = formatted_date + " +0000"
            cmd = f'GIT_COMMITTER_DATE="{formatted_date_with_timezone}" GIT_AUTHOR_DATE="{formatted_date_with_timezone}" git commit --allow-empty -m "committing on {formatted_date_with_timezone}"'
            run_git_command(cmd)
            count += 1

            if count % 100 == 0:
                print(f"Commits done: {count}")
                cmd = 'git push origin main'
                run_git_command(cmd)
    print(f"Total commits done: {count}")
    cmd = 'git push origin main'
    run_git_command(cmd)


def run_command(command):
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e.output}")
        raise


def cleanup_repo(new_branch_name='temp-branch', commit_message='Initial commit', force_push=False):
    run_command(f'git checkout --orphan {new_branch_name}')
    run_command('git add .')
    run_command(f'git commit -m "{commit_message}"')

    if force_push:
        main_branch = 'main'  # Change this if your main branch is named differently
        run_command(f'git branch -M {new_branch_name} {main_branch}')
        run_command(f'git push -f origin {main_branch}')


def create_git_repo():
    run_command('rm -rf .git')
    run_command('git init')
    run_command('git add .')
    run_command('git commit -m "Initial commit"')
    run_command('git branch -M main')
    run_command('git remote add origin https://github.com/iamvinitk/text-on-github.git')
    print("Git repo initialized successfully")


def create_remote_repo(delete_existing=False):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # check if repo already exists
    response = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO_NAME}", headers=headers)
    if response.status_code == 200 and not delete_existing:
        print("Remote repo already exists")
        return

    else:
        print("Remote repo does not exist. Creating...")

    if delete_existing:
        try:
            response = requests.delete(f"https://api.github.com/repos/{OWNER}/{REPO_NAME}", headers=headers)
            response.raise_for_status()
            print("Remote repo deleted successfully")
        except requests.exceptions.HTTPError as e:
            print(f"Error deleting remote repo: {e}")
            raise

    data = {
        "name": REPO_NAME,
        "description": "Text on GitHub",
        "private": False
    }

    try:
        response = requests.post(CREATE_ENDPOINT, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print("Remote repo created successfully")
    except requests.exceptions.HTTPError as e:
        print(f"Error creating remote repo: {e}")
        raise


def get_commits():
    query = """
            query($userName:String!) {
              user(login: $userName){
                contributionsCollection {
                  contributionCalendar {
                    totalContributions
                    weeks {
                      contributionDays {
                        contributionCount
                        date
                      }
                    }
                  }
                }
              }
            }
            """

    variables = {
        "userName": OWNER
    }

    body = {
        "query": query,
        "variables": variables
    }

    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    response = requests.post("https://api.github.com/graphql", headers=headers, json=body)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching commits: {response.text}")
        return None


def find_highest_contributed_day(response):
    highest_contributed_day = None
    highest_contributions = 0

    for week in response["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for day in week["contributionDays"]:
            if day["contributionCount"] > highest_contributions:
                highest_contributions = day["contributionCount"]
                highest_contributed_day = day["date"]

    return highest_contributed_day, highest_contributions


def main():
    global commit_per_day_for_highlighted, commit_per_day_for_shadow

    create_git_repo()
    create_remote_repo(delete_existing=True)
    cleanup_repo(force_push=True)

    response = get_commits()
    highest_contributed_day = find_highest_contributed_day(response)
    print(highest_contributed_day)
    commit_per_day_for_highlighted = highest_contributed_day[1] * 3
    commit_per_day_for_shadow = math.floor(highest_contributed_day[1] * 1.5)

    printing_matrix = construct_printing_matrix(get_text_input().lower())
    print(printing_matrix)
    commit_dates_dark = get_commit_dates(printing_matrix, sunday_at_start + timedelta(weeks=skip_weeks_from_front))
    print(len(commit_dates_dark))
    do_the_commits(commit_dates_dark, commit_per_day_for_highlighted)

    # commit_dates_shadow = get_commit_dates(printing_matrix,
    #                                        sunday_at_start + timedelta(weeks=skip_weeks_from_front - 1))
    # do_the_commits(commit_dates_shadow, commit_per_day_for_shadow)


if __name__ == '__main__':
    main()
