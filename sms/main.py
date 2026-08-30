import asyncio
from zte.src.zte_wrapper.wrapper import ZTEWrapper
from zte.src.zte_wrapper.authwrapper import zte_sha256_string
import json
import requests
import os
from flask import Flask, make_response
from dotenv import load_dotenv
from threading import Thread
from typing import Any

load_dotenv()

network_data = signal_data = None

loop = asyncio.get_event_loop()
app = Flask(__name__)
zte = ZTEWrapper(os.environ["IP"], os.environ["PASSWORD"])

with open("ids.json", "r") as f:
    ids: list = json.load(f)


def format_prometheus(key: str, desc: str, value: Any) -> str:
    line = f"# HELP {key} {desc}\n"
    line += f"# TYPE {key} gauge\n"
    line += f"{key} {value}\n"

    return line


@app.route("/metrics")
def metrics():
    if not network_data or not signal_data:
        return "Data not ready", 500

    lines = ""
    # fmt: off
    lines += format_prometheus("down_throughput", "Current upload throughput mbps", network_data.download_mbps)
    lines += format_prometheus("up_throughput", "Current upload throughput mbps", network_data.upload_mbps)
    lines += format_prometheus("month_download", "Monthly download in mib", network_data.monthly_download_megabytes)
    lines += format_prometheus("month_upload", "Monthly upload in mib", network_data.monthly_upload_megabytes)

    lines += format_prometheus("rssi_5g", "", signal_data.rssi_5g)
    lines += format_prometheus("rsrp_5g", "", signal_data.rsrp_5g)
    lines += format_prometheus("rsrq_5g", "", signal_data.rsrq_5g)

    lines += format_prometheus("rssi_4g", "", signal_data.rssi_lte)
    lines += format_prometheus("rsrp_4g", "", signal_data.rsrp_lte)
    lines += format_prometheus("rsrq_4g", "", signal_data.rsrq_lte)

    # fmt: on
    resp = make_response(lines, 200)
    resp.mimetype = "text/plain"
    return resp


async def sms_loop():
    global network_data, signal_data
    while True:
        try:
            print("Checking SMS...")
            sms = await zte.get_sms()

            network_data = await zte.get_network_details()
            signal_data = await zte.get_signal_strength()

            for number, messages in sms.items():
                for message in messages:
                    if message.id in ids:
                        continue

                    if not message.content.startswith("!"):
                        continue

                    print("Found new message")
                    r = requests.post(
                        "http://192.168.32.88:3001/api/chat",
                        json={
                            "source": "sms",
                            "ip": zte_sha256_string(number),
                            "text": message.content[1:],
                        },
                    )

                    if r.status_code == 200:
                        ids.append(message.id)

                        with open("ids.json", "w") as f:
                            json.dump(ids, f)
                    else:
                        print(r.status_code, r.json()["message"])
        except Exception as e:
            print(e)

        await asyncio.sleep(5)


t = Thread(target=asyncio.run, args=(sms_loop(),))
t.start()

app.run("0.0.0.0", 6060)
