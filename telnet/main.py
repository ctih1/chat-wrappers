import asyncio
import telnetlib3
import time
import requests


async def shell(
    reader: telnetlib3.TelnetReaderUnicode, writer: telnetlib3.TelnetWriterUnicode
):
    ip = writer.get_extra_info("peername")[0]
    print(f"New connection from {ip}")

    writer.write("\r\nHello and thank you for connecting to my Telnet server!\r\n")
    writer.write("Type a message to send out (max 255 characters)\r\n")
    writer.write(">> ")

    try:
        text = (await reader.readline()).strip()
    except Exception as e:
        print(e)
        return

    print(f"Receveid text {text}")

    writer.write(f'\r\nYou typed: "{text}"')
    writer.write("\r\n\r\nCorrect? (y/n + enter): ")

    response = (await reader.readline()).strip()

    print(f"Received repsonse {response}")

    if response == "y":
        writer.write("\r\nContacting da sophisticated API...")

        try:
            res = await asyncio.to_thread(
                requests.post,
                "http://192.168.32.88:3001/api/chat",
                json={"source": "telnet", "ip": ip, "text": text},
                timeout=8,
            )
        except Exception as e:
            writer.write("\r\nFailed to send message, request failed. Oops!")
            writer.close()
            return

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
    server = await telnetlib3.create_server(port=6023, host="0.0.0.0", shell=shell)  # type: ignore
    server2 = await telnetlib3.create_server(
        port=6024, host="0.0.0.0", shell=shell, line_mode=True  # type: ignore ,line_mode=True suggested by chatgpt since I couldn't find a way to enable local echo as it wasnt documented I think
    )
    loop = asyncio.get_event_loop()
    asyncio.create_task(server.wait_for_client())
    asyncio.create_task(server2.wait_for_client())
    print("Started both servers")
    while True:
        await asyncio.sleep(1)


asyncio.run(main())
