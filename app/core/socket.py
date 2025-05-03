from fastapi import WebSocket
import asyncio
from fastapi.concurrency import run_in_threadpool

def singleton(cls):
    instances = {}
    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance

@singleton
class SocketManager:
    def __init__(self):
        self.active_connections = {}
        self.connected_clients = set()

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.connected_clients.add(websocket)
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: int): 
        self.active_connections[user_id].remove(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connections in self.active_connections.values():
            await asyncio.gather(*[connection.send_text(message) for connection in connections])

    async def broadcast_to_all(self, message: str):
        for client in self.connected_clients:
            run_in_threadpool(client.send_text, message)

    async def broadcast_to_user(self, message: str, user_id: int):
        for client in self.active_connections[user_id]:
            run_in_threadpool(client.send_text, message)
