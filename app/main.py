import click
import concurrent.futures
import os
from git import Repo
from github import Github, Auth
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from termcolor import colored, cprint


BANNER = """
____   ____ __       __     ___   _________              __   __     
\   \ /   /|__|__  _|__| __| _/  /   _____/ ____  __ ___/  |_|  |__  
 \   Y   / |  \  \/ /  |/ __ |   \_____  \ /  _ \|  |  \   __\  |  \ 
  \     /  |  |\   /|  / /_/ |   /        (  <_> )  |  /|  | |   Y  \\
   \___/   |__| \_/ |__\____ |  /_______  /\____/|____/ |__| |___|  /
                            \/          \/                        \/
                            by d33n0b
"""


def print_banner():
    print(BANNER)


def format_date(date):
    return date.strftime("%B %Y")


def get_contributor(git, contributor, commits):
    username = contributor.author.login
    real_name = contributor.author.name
    user = git.get_user(username)
    created_at = user.created_at
    events = list(git.get_user(username).get_public_events())

    user_commits = [
        commit
        for commit in commits
        if commit.author is not None and commit.author.name == real_name
    ]

    return {
        "username": username,
        "real_name": real_name,
        "email": user.email,
        "created_at": created_at,
        "events": events,
        "commits": user_commits,
    }


def print_contributor(contributor_data):
    username = contributor_data["username"]
    real_name = contributor_data["real_name"]
    created_at = contributor_data["created_at"]
    events = contributor_data["events"]
    commits = contributor_data["commits"]
    email = contributor_data["email"]

    cprint(
        f"Username: {username} ({real_name} / {email})", "white", attrs=["underline"]
    )

    current_date = datetime.now(timezone.utc)

    # calculate the difference in months
    difference = relativedelta(current_date, created_at)
    months_difference = difference.years * 12 + difference.months

    created_fmt = format_date(created_at)
    if months_difference < 6:
        print(
            f"Account Created: {created_fmt} {colored(f'({months_difference} months ago)', 'red')}"
        )
    elif months_difference < 12:
        print(
            f"Account Created: {created_fmt} {colored(f'({months_difference} months ago)', 'yellow')}"
        )
    else:
        print(
            f"Account Created: {created_fmt} {colored(f'({months_difference} months ago)', 'green')}"
        )

    if len(events) == 0:
        print(
            f"First Account Event: {colored('No Public Events!', 'yellow', attrs={'bold'})}"
        )
    else:
        first_event = events[len(events) - 1]
        first_fmt = format_date(created_at)
        if first_event.created_at < created_at:
            print(f"First Account Event: {colored(first_fmt, 'red')}")
        else:
            print(f"First Account Event: {first_fmt}")

    total_commits = len(commits)
    if total_commits > 0:
        print(f"Total Commits: {total_commits}")
        first_commit = commits[-1]
        print(f"First Commit: {format_date(first_commit.authored_datetime)}")
        last_commit = commits[0]
        print(f"Last Commit: {format_date(last_commit.authored_datetime)}")

        first_commit_date = first_commit.authored_datetime
        difference = relativedelta(first_commit_date, created_at)
        months_difference = difference.years * 12 + difference.months

        if months_difference < 6:
            print(
                f"Started contributing: {colored(f'{months_difference} months', 'red')} after account creation!"
            )
        elif months_difference < 12:
            print(
                f"Started contributing: {colored(f'{months_difference} months', 'yellow')} after account creation!"
            )
        else:
            print(
                f"Started contributing: {colored(f'{months_difference} months', 'green')} after account creation."
            )

    else:
        print(f"No commits by {username} found in the repository.")

    print("")


def check_contributors(git, repo, local_repo):
    contributors = list(repo.get_stats_contributors())
    commits = list(local_repo.iter_commits())

    for contributor in contributors:
        c = get_contributor(git, contributor, commits)
        if len(c["commits"]) > 0:
            print_contributor(c)

    # futures = []
    # with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    #    for contributor in contributors:
    #        futures.append(executor.submit(get_contributor, git, contributor, commits))
    # for future in futures:
    #    contributor = future.result()
    #    if len(contributor.commits) > 0:
    #        print_contributor(contributor)


@click.command()
@click.option(
    "--repo",
    prompt="Target repository",
    help="The repository to scan.",
)
@click.option(
    "--token",
    prompt="Token envar",
    is_flag=False,
    flag_value="GITHUB_TOKEN",
    default="GITHUB_TOKEN",
    help="The name of the environment variable containing the GitHub auth token.",
)
@click.option(
    "--url",
    prompt="GitHub URL",
    is_flag=False,
    flag_value="https://api.github.com",
    default="https://api.github.com",
    help="The URL to the GitHub instance.",
)
def main(repo, token, url):
    print_banner()

    token = os.environ[token].strip()
    auth = Auth.Token(token)
    git = Github(base_url=url, auth=auth)
    local_repo = Repo(repo)
    repo_url = local_repo.remote().url.split("@")[1].split(":")[1].split(".git")[0]

    print(
        f"Target repository: {colored(repo, 'green')} ({colored(local_repo.remote().url, 'light_green')})\n"
    )

    online_repo = git.get_repo(repo_url)

    check_contributors(git, online_repo, local_repo)


if __name__ == "__main__":
    main()
