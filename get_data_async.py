#! /usr/bin/env python3


import asyncio
import websockets

from tvDatafeed import TvDatafeed

tv = TvDatafeed()


async def send_messages(websocket, messages):
    print("sending messages")

    for message in messages:
        await websocket.send(message)
        print(f"Sent: {message}")


async def receive_messages(websocket):
    print("receiving messages")

    messages = []

    while True:
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"Received: {message}")
            messages.append(message)
            await asyncio.sleep(1)
        except asyncio.TimeoutError:
            print("No messages received in 10 seconds. Closing connection.")
            await websocket.close()
            break
        except websockets.exceptions.ConnectionClosed:
            print("Error: Connection closed.")
        except Exception as e:
            print(f"Error: {e}")

    return messages


async def get_multi_financial_data(symbols: list[str]):

    tv.create_connection()

    tv.send_set_auth_token()
    tv.send_quote_create_session_msg()

    send_task = send_messages(tv.ws, symbols)
    receive_task = receive_messages(tv.ws)

    received_messages = await asyncio.gather(send_task, receive_task)

    print("Final received messages:", received_messages[1])


symbols = [
    tv.format_symbol(symbol="BATS", exchange="LSE"),
    tv.format_symbol(symbol="IMB", exchange="LSE"),
    tv.format_symbol(symbol="JEMA", exchange="LSE"),
    tv.format_symbol(symbol="NWG", exchange="LSE"),
]


async def main():
    await get_multi_financial_data(symbols)


asyncio.run(main())
