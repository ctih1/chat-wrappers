import json
from typing import Dict, List
from .authwrapper import ZTEAuthWrapper
from .types import SMSMessage, PhoneNumber, AuthError

def utf_16_decode(inp: str) -> str:
    return bytes.fromhex(inp).decode("utf-16-be")

class ZTEWrapper(ZTEAuthWrapper):
    def __init__(self, webui_address: str, password: str) -> None:
        super().__init__(webui_address, password)

    async def get_sms(self) -> Dict[PhoneNumber, List[SMSMessage]]:
        res = await self.request("GET", self.construct_url("goform_get_cmd_process", {
            "isTest": "false",
            "cmd": "sms_data_total",
            "page": "0",
            "data_per_page": "1500",
            "mem_store": "1",
            "tags": "10",
            "order_by": "order by id desc",
            "_": self.get_timestamp()
        }))

        jason = json.loads(await res.text())

        if jason.get("sms_data_total") == "" or jason.get("messages") is None:
            raise AuthError("Failed to retrieve data from SMS")

        results: Dict[PhoneNumber, List[SMSMessage]] = {}
        for message in jason["messages"]:
            phone_number = utf_16_decode(message["number"])

            if phone_number not in results:
                results[phone_number] = []

            results[phone_number].append(SMSMessage(
                content=utf_16_decode(message["content"]),
                tag=int(message["tag"]),
                id=int(message["id"])
            ))

        return results
