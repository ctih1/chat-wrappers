import asyncio
import json
import requests
import os
from dotenv import load_dotenv
from threading import Thread
from typing import Any
from hashlib import sha256
import time

load_dotenv()

with open("ids.json", "r") as f:
    ids: list = json.load(f)


def sms_loop():
    while True:
        try:
            print("Checking SMS...")
            res = requests.get(
                "http://192.168.32.88:6060/api/sms",
                cookies={
                    "Token": sha256(os.environ["API_KEY"].encode("utf-8")).hexdigest()
                },
            )

            if res.status_code != 200:
                print(f"Status {res.status_code}")
                time.sleep(5)
                continue

            smses = res.json()

            for number, messages in smses.items():
                for message in messages:
                    if message["id"] in ids:
                        continue

                    if not message["content"].startswith("!"):
                        continue

                    print(message["content"])

                    print("Found new message")

                    r = requests.post(
                        "http://192.168.32.88:3001/api/chat",
                        json={
                            "source": "sms",
                            "ip": sha256(number.encode("utf-8")).hexdigest(),
                            "text": message["content"][1:],
                        },
                    )

                    if r.status_code != 200:
                        print(r.status_code, r.json()["message"])

                    if r.status_code in [200, 400, 401]:
                        ids.append(message["id"])

                        with open("ids.json", "w") as f:
                            json.dump(ids, f)
        except Exception as e:
            print(e)

        time.sleep(5)


sms_loop()
