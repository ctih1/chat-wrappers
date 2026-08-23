import asyncio
import telnetlib3
import time
import requests

async def shell(reader: telnetlib3.TelnetReaderUnicode, writer: telnetlib3.TelnetWriterUnicode):
    writer.write("\r\nHello and thank you for connecting to my Telnet server!\r\n")
    writer.write("Type a message to send out (max 255 characters)\r\n")
    writer.write(">> ")
    ip = writer.get_extra_info("peername")[0]

    print(f"New connection from {ip}")

    text = ""

    while True:
        data = await reader.read(1)
        print(data.encode("utf-8"))
        if data in ["\x08", "\x7f"]:
            text = text[:-1]
        if data == "\x03":
            writer.close()
            break
        if data in ["\n", "\r"]:
            break
        if data == "":
            break
        else:
            text += data

        writer.echo(data)

    await writer.drain()

    writer.write(f"\r\nYou typed: \"{text}\"")
    writer.write("\r\n\r\nCorrect? (y/n + enter): ")

    response = (await reader.readline()).strip()
    writer.echo(response)

    if response == "y":
        writer.write("\r\nContacting da sophisticated API...")
        await writer.drain()

        res = requests.post("http://192.168.32.88:3001/api/chat", json={"source": "telnet", "ip": ip, "text": text})

        message = ""

        match res.status_code:
            case 200:
                message = "Published message!"
            case 403 | 401 | 429:
                message = res.json()["message"]
            case _:
                message = "Unknown error???"

        writer.write(f"\r\n{message}")
        writer.write("\r\nBuh-bye!\r\n")
    else:
        writer.write("\r\nCancelled, goodbye!!")

    writer.close()


async def main():
    server = await telnetlib3.create_server(port=6023, host="0.0.0.0", shell=shell) # type: ignore
    print("Started server")
    await server.wait_closed()


asyncio.run(main())
