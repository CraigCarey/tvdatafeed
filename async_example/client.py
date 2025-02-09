#! /usr/bin/env python3

import asyncio
import websockets


async def send_messages(websocket, messages):
    print("sending messages")

    for message in messages:
        await websocket.send(message)
        print(f"Sent: {message}")


async def receive_messages(websocket):
    print("receiving messages")
    await asyncio.sleep(2)

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


async def main():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:

        messages = [
            "all",
            "work",
            "and",
            "no",
            "play",
            "makes",
            "Jack",
            "a",
            "dull",
            "boy",
        ]

        send_task = send_messages(websocket, messages)
        receive_task = receive_messages(websocket)

        received_messages = await asyncio.gather(send_task, receive_task)

        print("Final received messages:", received_messages[1])


asyncio.run(main())
