import json
import os
import sys
import time

from github import Github, InputGitAuthor, GithubException
from bs4 import BeautifulSoup

ballerina_bot_username = os.environ['BALLERINA_BOT_USERNAME']
ballerina_bot_token = os.environ[]'BALLERINA_BOT_TOKEN']
ballerina_bot_email = os.environ['BALLERINA_BOT_EMAIL']
ballerina_reviewer_bot_token = os.environ['BALLERINA_REVIEWER_BOT_TOKEN']

github = Github(ballerina_bot_token)

def main():
    repo = github.get_repo('ballerina-platform/ballerina-dev-website', ref='master')
    html_file = repo.get_contents('index.html')
    html_file = html_file.decoded_content.decode('utf-8')

    with open('index.html', 'w') as write_obj:
        write_obj.write(html_file)

    with open('index.html','r') as soup1:
        html_doc = soup1.read()
        soup = BeautifulSoup(html_doc, 'html.parser')

    with open('working_with_data.bal', 'r') as action_obj:
        action_bbe = action_obj.readlines()

    old_text = soup.find('div', {'id':'working-with-data'})

    with open('index.html','r') as read_obj:
        html_doc_lines = read_obj.readlines()

    with open('edited_index.html', 'a') as new_html:
        for line in html_doc_lines[0:old_text.code.sourceline]:
            new_html.write(line)
        for line in action_bbe[0:len(action_bbe)]:
            new_html.write(line)
        new_html.write("\n")
        for line in html_doc_lines[old_text.code.sourceline+len(old_text.code.string.strip().splitlines()):len(html_doc_lines)]:
            new_html.write(line)

    with open('edited_index.html', 'r') as commit_obj:
        updated_file = commit_obj.read()

    commit_message = 'Update Ballerina in Action samples'
    try:
        update = commit_file('index.html', updated_file, 'update-working-with-data', commit_message)[0]

        if update:
            pr_title = '[Automated] Update Ballerina in Action samples'
            pr_body = 'Update Ballerina in Action samples for source code changes in working with data'
            head_branch = 'update-working-with-data'
            open_pull_request(pr_title, pr_body, head_branch)

    except GithubException as e:
        print('Error occurred while committing changes to ballerina-dev-website', e)

# commit the changes
def commit_file(file_path, Updated_file_content, commit_branch, commit_message):
    try:
        author = InputGitAuthor(ballerina_bot_username, ballerina_bot_email)
        repo = github.get_repo('ballerina-platform/ballerina-dev-website', ref='master')
        remote_file = repo.get_contents(file_path)

        base = repo.get_branch('master')
        branch = commit_branch
        try:
            ref = f"refs/heads/" + branch
            repo.create_git_ref(ref=ref, sha=base.commit.sha)
        except GithubException:
            print("[Info] Unmerged '" + commit_branch + "' branch existed" )
            branch = commit_branch + '_tmp'
            ref = f"refs/heads/" + branch
            try:
                repo.create_git_ref(ref=ref, sha=base.commit.sha)
            except GithubException as e:
                print("[Info] Deleting '" + commit_branch + "' tmp branch existed" )
                if e.status == 422:  # already exist
                    repo.get_git_ref("heads/" + branch).delete()
                    repo.create_git_ref(ref=ref, sha=base.commit.sha)
        update = repo.update_file(
            file_path,
            commit_message,
            updated_file_content,
            remote_file.sha,
            branch=branch,
            author=author
        )
        if not branch == commit_branch:
            update_branch = repo.get_git_ref("heads/" + commit_branch)
            update_branch.edit(update["commit"].sha, force=True)
            repo.get_git_ref("heads/" + branch).delete()
        return True, update["commit"].sha
    except GithubException as e:
        raise e

# send a pull request
def open_pull_request(title, body, head_branch):
    try:
        repo = github.get_repo('ballerina-platform/ballerina-dev-website')

        created_pr = repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base='master'
        )

        # To stop intermittent failures due to API sync
        time.sleep(5)

        r_github = Github(ballerina_reviewer_bot_token)
        repo = r_github.get_repo('ballerina-platform/ballerina-dev-website')
        pr = repo.get_pull(created_pr.number)
        pr.create_review(event='APPROVE')

    except Exception as e:
        raise e
main()
