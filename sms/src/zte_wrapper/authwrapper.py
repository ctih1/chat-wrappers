import asyncio
import aiohttp
from hashlib import sha256
import urllib.parse
import time
import json
from typing import Literal, Dict, Any
from copy import deepcopy

GOFORM_COMMANDS = Literal["goform_get_cmd_process", "goform_set_cmd_process"]
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "192.168.32.1",
    "Referer": "http://192.168.32.1/",
    "Sec-Gpc": "1",
    "User-Agent": "Mozilla",
    "X-Requested-With": "XMLHttpRequest"
}

def zte_sha256_string(input: str) -> str:
    return sha256(input.encode("UTF-8")).hexdigest().upper()

class ZTEAuthWrapper:
    def __init__(self, webui_address: str, password: str) -> None:
        self.address: str = webui_address
        self.__password = zte_sha256_string(password)
        self.__auth_code: str | None = None

        self.headers = HEADERS
        self.headers["Referer"] = f"http://{self.address}/"
        self.headers["Host"] = self.address

        self.session: aiohttp.ClientSession | None = None

    def construct_url(self, command: GOFORM_COMMANDS, args: Dict[str, Any]) -> str:
        base_url = f"http://{self.address}/goform/{command}/?"

        url = base_url + urllib.parse.urlencode({k:urllib.parse.quote(str(v)) for k,v in args.items()})

        return url

    def get_timestamp(self) -> int:
        return round(time.time()*1000)

    async def __get_ld(self) -> str:
        async with aiohttp.ClientSession() as session:
            res = await session.get(
                self.construct_url("goform_get_cmd_process", {
                    "isTest": "false",
                    "cmd": "LD",
                    "_": self.get_timestamp()
                }),
                headers=self.headers
            )

            return json.loads((await res.text())).get("LD") # json.loads instead of res.json() because the stupid API returns the stuff as text/html


    async def refresh_auth(self) -> str:
        ld_token: str = await self.__get_ld()
        hashed_password: str = zte_sha256_string(self.__password + ld_token)

        async with aiohttp.ClientSession() as session:
            res = await session.post(self.construct_url("goform_set_cmd_process", {}), data={"isTest": "false", "goformId": "LOGIN", "password": hashed_password}, headers=self.headers)
            self.__auth_code = str(res.cookies.get("stok"))

        return self.__auth_code

    async def request(self, method: Literal["GET", "POST"], *args, **kwargs) -> aiohttp.ClientResponse:
        if not self.session:
            self.session = aiohttp.ClientSession()

        await self.refresh_auth()

        headers = deepcopy(self.headers)
        headers["Cookie"] = f"stok=\"{self.__auth_code}\""

        if method == "GET":
            res = await self.session.get(*args, **kwargs, headers=headers)
        elif method == "POST":
            res = await self.session.post(*args, **kwargs, headers=headers)

        return res

    async def close(self) -> None:
        if self.session:
            await self.session.close()
