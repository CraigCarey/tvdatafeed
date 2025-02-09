#! /usr/bin/env python3

import asyncio
import websockets


async def echo(websocket):
    async for message in websocket:
        print(f"Received: {message}")
        await websocket.send(message)


async def main():
    server = await websockets.serve(echo, "localhost", 8765)  # Await serve()
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()  # Keep server running


asyncio.run(main())  # Properly run the main event loop
