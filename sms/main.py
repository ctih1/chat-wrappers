import asyncio
from src.zte_wrapper.wrapper import ZTEWrapper
from src.zte_wrapper.authwrapper import zte_sha256_string
import json
import requests
import os

z = ZTEWrapper(os.environ["IP"], os.environ["PASSWORD"])

with open("ids.json", "r") as f:
    ids: list = json.load(f)

async def main():
    while True:
        print("Loop ran")
        sms = await z.get_sms()
        for number, messages in sms.items():
            for message in messages:
                if message.id in ids:
                    continue

                if not message.content.startswith("!"):
                    continue
                
                print("Found message")
                r = requests.post("http://192.168.32.88:3001/api/chat", json={"source": "sms", "ip": zte_sha256_string(number), "text": message.content[1:]})
                if r.status_code == 200:
                    ids.append(message.id)

                    with open("ids.json", "w") as f:
                        json.dump(ids, f)
                else:
                    print(r.status_code, r.json()["message"])

        await asyncio.sleep(10)


asyncio.run(main())
