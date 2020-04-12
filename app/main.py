import hashlib
import hmac
import json
import os
import sys
from datetime import datetime

import requests
from fastapi import BackgroundTasks, FastAPI, HTTPException
from git import Repo

secret_path = "/s/webhook_secret"
api_key_path = "/s/api_key"
git_url_path = "/s/git_url"
zerotier_network_path = "/s/network_id"

secret = open(secret_path).readline().rstrip()
api_key = open(api_key_path).readline().rstrip()
git_url = open(git_url_path).readline().rstrip()
zerotier_network = open(zerotier_network_path).readline().rstrip()


ssh_cmd = 'ssh -o StrictHostKeyChecking=no -i /s/ssh_key'
git_dir = "/git"

zerotier_url = f"https://my.zerotier.com/api/network/{zerotier_network}/member"
headers = {"Authorization": f"Bearer {api_key}"}

app = FastAPI(redoc_url=None)

@app.post("/hook/{token}")
async def webhook(token: str, background_tasks: BackgroundTasks):
    if not (hashlib.sha256(bytes(token, 'utf-8')).digest() == hashlib.sha256(bytes(secret, 'utf-8')).digest()):
        raise HTTPException(403, detail="Invalid Secret")
    background_tasks.add_task(synczerotier)

def synczerotier():
    if not os.path.isdir(git_dir):
        git_repo = Repo.init(git_dir)
        origin = git_repo.create_remote('origin', git_url)
        with git_repo.git.custom_environment(GIT_SSH_COMMAND=ssh_cmd):
            origin.fetch()
            git_repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
            origin.pull()

    config = createzerotierconfig()

    record_file_path = os.path.join(git_dir, "records.tf")
    records_file = open(record_file_path, "w")
    records_file.write(config)
    records_file.close()

    repo = Repo(git_dir)
    repo.index.add("records.tf")
    repo.index.commit(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    with repo.git.custom_environment(GIT_SSH_COMMAND=ssh_cmd):
        repo.remotes.origin.push()


def createzerotierconfig():
    r = requests.get(zerotier_url, headers=headers).json()

    hosts = []

    for i in r:
        if i["config"]["authorized"] == True:
            new_dict = {}
            new_dict["name"] = i["name"]
            new_dict["ip"] = i["config"]["ipAssignments"]
            hosts.append(new_dict)

    records = []

    for j in hosts:
        name = j["name"]
        for ip in j["ip"]:
            records.append(
                f"resource \"cloudflare_record\" \"{name}\"" 
                "{\n"
                "  zone_id = var.cloudflare_zone_id\n"
                f"  name    = \"{name}.zt\"\n"
                f"  value   = \"{ip}\"\n"
                "  type    = \"A\"\n"
                "}\n\n"
            )

    return("".join(records))
