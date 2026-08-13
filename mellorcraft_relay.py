#!/usr/bin/env python3
"""MellorCraft v1.5.0 singleplayer LAN relay.

The relay is intentionally world-agnostic. A browser that owns a singleplayer save
registers as the authoritative host. Other singleplayer clients discover that world
and the relay forwards game-protocol messages between guests and the host.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import socket
import uuid
from dataclasses import dataclass, field
from typing import Any

try:
    from websockets.asyncio.server import serve
    from websockets.exceptions import ConnectionClosed
except ImportError:
    from websockets.server import serve  # type: ignore
    from websockets.exceptions import ConnectionClosed  # type: ignore

DEFAULT_PORT = 8000
RELAY_PROTOCOL = 1

@dataclass
class Room:
    world_id: str
    world_name: str
    seed: int
    host: Any
    guests: dict[str, Any] = field(default_factory=dict)

rooms: dict[str, Room] = {}
connection_roles: dict[Any, tuple[str, str]] = {}

async def send_json(ws: Any, payload: dict[str, Any]) -> None:
    await ws.send(json.dumps(payload, separators=(",", ":")))

def lan_ip() -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return str(probe.getsockname()[0])
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()

def world_list() -> list[dict[str, Any]]:
    return [
        {"worldId": room.world_id, "worldName": room.world_name, "seed": room.seed,
         "players": 1 + len(room.guests)}
        for room in rooms.values()
    ]

async def host_message(ws: Any, room: Room, data: dict[str, Any]) -> None:
    kind = data.get("type")
    if kind == "host_send":
        guest_id = str(data.get("guestId", ""))
        guest = room.guests.get(guest_id)
        if guest is not None:
            await send_json(guest, {"type": "server_message", "payload": data.get("payload", {})})
    elif kind == "host_broadcast":
        exclude = str(data.get("excludeGuestId", ""))
        dead: list[str] = []
        for guest_id, guest in list(room.guests.items()):
            if guest_id == exclude:
                continue
            try:
                await send_json(guest, {"type": "server_message", "payload": data.get("payload", {})})
            except ConnectionClosed:
                dead.append(guest_id)
        for guest_id in dead:
            room.guests.pop(guest_id, None)

async def handler(ws: Any, *_args: Any) -> None:
    role = "viewer"
    room_id = ""
    guest_id = ""
    try:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await send_json(ws, {"type": "error", "message": "Malformed JSON."})
                continue
            if not isinstance(data, dict):
                continue
            kind = str(data.get("type", ""))

            if kind == "list_worlds" and role == "viewer":
                await send_json(ws, {"type": "worlds", "protocol": RELAY_PROTOCOL, "worlds": world_list()})
                continue

            if kind == "host_world" and role == "viewer":
                name = str(data.get("worldName", "World")).strip()[:48] or "World"
                seed = int(data.get("seed", 0) or 0)
                room_id = uuid.uuid4().hex[:12]
                room = Room(room_id, name, seed, ws)
                rooms[room_id] = room
                role = "host"
                connection_roles[ws] = (role, room_id)
                await send_json(ws, {"type": "hosted", "protocol": RELAY_PROTOCOL, "worldId": room_id})
                print(f'Opened "{name}" ({room_id})')
                continue

            if kind == "join_world" and role == "viewer":
                requested = str(data.get("worldId", ""))
                room = rooms.get(requested)
                if room is None:
                    await send_json(ws, {"type": "error", "message": "That LAN world is no longer open."})
                    continue
                guest_id = uuid.uuid4().hex
                room_id = requested
                room.guests[guest_id] = ws
                role = "guest"
                connection_roles[ws] = (role, room_id)
                await send_json(ws, {"type": "join_pending", "guestId": guest_id, "worldId": room_id})
                await send_json(room.host, {
                    "type": "guest_joined", "guestId": guest_id,
                    "username": str(data.get("username", "Player"))[:20],
                    "skin": str(data.get("skin", "steve"))[:20],
                    "deviceClass": "mobile" if str(data.get("deviceClass", "desktop")).lower() == "mobile" else "desktop",
                })
                print(f"Guest {guest_id[:8]} joined {room_id}")
                continue

            if role == "host":
                room = rooms.get(room_id)
                if room is not None:
                    await host_message(ws, room, data)
                continue

            if role == "guest" and kind == "client_message":
                room = rooms.get(room_id)
                if room is None:
                    await send_json(ws, {"type": "world_closed"})
                    continue
                await send_json(room.host, {"type": "guest_message", "guestId": guest_id, "payload": data.get("payload", {})})
                continue

            await send_json(ws, {"type": "error", "message": "Invalid relay command for this connection."})
    except ConnectionClosed:
        pass
    finally:
        connection_roles.pop(ws, None)
        if role == "host" and room_id:
            room = rooms.pop(room_id, None)
            if room is not None:
                for guest in list(room.guests.values()):
                    try:
                        await send_json(guest, {"type": "world_closed", "message": "The LAN world host disconnected."})
                        await guest.close(code=4001, reason="World host disconnected")
                    except Exception:
                        pass
                print(f"Closed {room_id}")
        elif role == "guest" and room_id and guest_id:
            room = rooms.get(room_id)
            if room is not None:
                room.guests.pop(guest_id, None)
                try:
                    await send_json(room.host, {"type": "guest_left", "guestId": guest_id})
                except Exception:
                    pass

async def main() -> None:
    parser = argparse.ArgumentParser(description="MellorCraft v1.5.0 singleplayer LAN relay")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="WebSocket relay port (default: 8000)")
    args = parser.parse_args()
    print("MellorCraft v1.5.0 Singleplayer LAN Relay")
    print(f"Relay: ws://127.0.0.1:{args.port}")
    print(f"LAN:   ws://{lan_ip()}:{args.port}")
    print("Keep this window open while singleplayer worlds are shared to LAN.")
    async with serve(handler, "0.0.0.0", args.port, max_size=32 * 1024 * 1024, ping_interval=10, ping_timeout=10):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nRelay stopped.")