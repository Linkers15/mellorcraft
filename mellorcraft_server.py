#!/usr/bin/env python3
"""MellorCraft multiplayer host.

Serves the HTML client on TCP port 8000 and hosts the multiplayer WebSocket
service on TCP port 8765. The server owns shared world edits, time, players,
mobs, dropped items, PvP, permissions, and persistence.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import random
import re
import socket
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    from websockets.asyncio.server import serve
    from websockets.exceptions import ConnectionClosed
except ImportError:  # websockets 10/11 compatibility
    from websockets.server import serve  # type: ignore
    from websockets.exceptions import ConnectionClosed  # type: ignore

HTTP_PORT = 8000
WEBSOCKET_PORT = 8765
DAY_LENGTH_SECONDS = 600.0
PROTOCOL_VERSION = 4
SUPPORTED_PROTOCOLS = (4, 3, 2)
WORLD_HEIGHT = 100
PORTAL_BLOCK = 31
AIR_BLOCK = 0
RAW_MEAT_ITEM = 106
MOB_CAP_PER_DIMENSION = 25
MAX_INVENTORY_SLOTS = 30
MAX_STACK_SIZE = 100
ALLOWED_SKINS = {"steve", "alex", "mellorite", "ember", "frost", "forest"}
SWORD_DAMAGE = {202: 4.0, 212: 5.0, 222: 6.0, 232: 5.0, 242: 8.0, 252: 10.0}
MOB_DEFINITIONS: dict[str, dict[str, Any]] = {
    "PIG": {"health": 10.0, "damage": 0.0, "hostile": False, "dropMeat": True},
    "COW": {"health": 10.0, "damage": 0.0, "hostile": False, "dropMeat": True},
    "CAMEL": {"health": 20.0, "damage": 0.0, "hostile": False, "dropMeat": True},
    "BEAR": {"health": 30.0, "damage": 3.0, "hostile": True, "dropMeat": True},
    "ZOMBIE": {"health": 20.0, "damage": 1.0, "hostile": True, "dropMeat": False},
    "SKELETON": {"health": 20.0, "damage": 1.0, "hostile": True, "dropMeat": False},
    "RED_ALT_ZOMBIE": {"health": 40.0, "damage": 3.0, "hostile": True, "dropMeat": False},
    "MELLOR_BOSS": {"health": 200.0, "damage": 5.0, "hostile": True, "dropMeat": False},
}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_ -]{1,20}$")
ENTITY_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
SCRIPT_DIR = Path(__file__).resolve().parent
CLIENT_FILENAME = "mellorcraft_multiplayer.html"
SAVE_FILENAME = "mellorcraft_world.json"


@dataclass
class PlayerState:
    id: str
    username: str
    skin: str
    x: float = 0.5
    y: float = 50.0
    z: float = 0.5
    yaw: float = 0.0
    pitch: float = 0.0
    dimension: int = 0
    health: float = 10.0
    gamemode: str = "survival"
    heldItem: int = 0
    selectedSlot: int = 0
    inventory: list[dict[str, int]] = field(
        default_factory=lambda: [{"id": 0, "count": 0} for _ in range(MAX_INVENTORY_SLOTS)]
    )
    isOperator: bool = False


@dataclass
class MobState:
    id: str
    typeKey: str
    x: float
    y: float
    z: float
    dimension: int
    health: float
    maxHealth: float
    bodyRotation: float = 0.0
    headRotation: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0


@dataclass
class DroppedItemState:
    id: str
    itemId: int
    count: int
    x: float
    y: float
    z: float
    dimension: int
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    age: float = 0.0


class MellorCraftWorld:
    def __init__(self, save_path: Path, requested_seed: int | None = None) -> None:
        self.save_path = save_path
        self.seed = requested_seed if requested_seed is not None else random.randint(0, 2_147_483_646)
        self.world_time = 0.25
        self.blocks: dict[str, int] = {}
        self.players: dict[str, PlayerState] = {}
        self.connections: dict[str, Any] = {}
        self.client_protocols: dict[str, int] = {}
        self.operators: set[str] = set()
        self.player_profiles: dict[str, dict[str, Any]] = {}
        self.mobs: dict[str, MobState] = {}
        self.items: dict[str, DroppedItemState] = {}
        self.mob_hosts: dict[int, str | None] = {0: None, 1: None, 2: None}
        self.damage_locks: dict[str, float] = {}
        self.attack_cooldowns: dict[str, float] = {}
        self.mob_attack_cooldowns: dict[str, float] = {}
        self.mob_environment_cooldowns: dict[str, float] = {}
        self.last_tick = time.monotonic()
        self.dirty = False
        self.load()

    @staticmethod
    def block_key(dimension: int, x: int, y: int, z: int) -> str:
        return f"{dimension},{x},{y},{z}"

    @staticmethod
    def parse_block_key(key: str) -> tuple[int, int, int, int]:
        dimension, x, y, z = (int(part) for part in key.split(",", 3))
        return dimension, x, y, z

    def tick(self) -> float:
        now = time.monotonic()
        elapsed = max(0.0, min(now - self.last_tick, 5.0))
        self.last_tick = now
        self.world_time += elapsed / DAY_LENGTH_SECONDS
        return elapsed

    @staticmethod
    def profile_key(username: str) -> str:
        return username.strip().casefold()

    @staticmethod
    def sanitize_inventory(value: Any) -> list[dict[str, int]] | None:
        if not isinstance(value, list):
            return None
        inventory: list[dict[str, int]] = []
        for entry in value[:MAX_INVENTORY_SLOTS]:
            if not isinstance(entry, dict):
                inventory.append({"id": 0, "count": 0})
                continue
            try:
                item_id = max(0, min(255, int(entry.get("id", 0))))
                count = max(0, min(MAX_STACK_SIZE, int(entry.get("count", 0))))
            except (TypeError, ValueError):
                item_id, count = 0, 0
            if item_id == 0 or count == 0:
                item_id, count = 0, 0
            inventory.append({"id": item_id, "count": count})
        while len(inventory) < MAX_INVENTORY_SLOTS:
            inventory.append({"id": 0, "count": 0})
        return inventory

    @staticmethod
    def public_player_state(player: PlayerState) -> dict[str, Any]:
        return {
            "id": player.id, "username": player.username, "skin": player.skin,
            "x": player.x, "y": player.y, "z": player.z,
            "yaw": player.yaw, "pitch": player.pitch, "dimension": player.dimension,
            "health": player.health, "gamemode": player.gamemode,
            "heldItem": player.heldItem, "isOperator": player.isOperator,
        }

    @staticmethod
    def player_profile(player: PlayerState) -> dict[str, Any]:
        return {
            "username": player.username, "skin": player.skin,
            "x": player.x, "y": player.y, "z": player.z,
            "yaw": player.yaw, "pitch": player.pitch, "dimension": player.dimension,
            "health": player.health, "gamemode": player.gamemode,
            "heldItem": player.heldItem, "selectedSlot": player.selectedSlot,
            "inventory": [{"id": slot["id"], "count": slot["count"]} for slot in player.inventory],
        }

    def remember_player(self, player: PlayerState) -> None:
        self.player_profiles[self.profile_key(player.username)] = self.player_profile(player)
        self.dirty = True

    def restored_player(self, player_id: str, username: str, skin: str, is_operator: bool) -> tuple[PlayerState, bool]:
        profile = self.player_profiles.get(self.profile_key(username))
        player = PlayerState(id=player_id, username=username, skin=skin, isOperator=is_operator)
        if not isinstance(profile, dict):
            return player, False
        player.x = max(-2_000_000.0, min(2_000_000.0, finite_number(profile.get("x"), player.x)))
        player.y = max(-100.0, min(1000.0, finite_number(profile.get("y"), player.y)))
        player.z = max(-2_000_000.0, min(2_000_000.0, finite_number(profile.get("z"), player.z)))
        player.yaw = finite_number(profile.get("yaw"), player.yaw)
        player.pitch = max(-math.pi / 2, min(math.pi / 2, finite_number(profile.get("pitch"), player.pitch)))
        player.dimension = bounded_int(profile.get("dimension"), 0, 2, player.dimension)
        player.health = max(0.0, min(10.0, finite_number(profile.get("health"), player.health)))
        saved_mode = str(profile.get("gamemode", "survival"))
        player.gamemode = saved_mode if saved_mode in {"survival", "creative", "spectator"} else "survival"
        if not is_operator and player.gamemode != "survival":
            player.gamemode = "survival"
        player.heldItem = bounded_int(profile.get("heldItem"), 0, 255, player.heldItem)
        player.selectedSlot = bounded_int(profile.get("selectedSlot"), 0, 8, player.selectedSlot)
        inventory = self.sanitize_inventory(profile.get("inventory"))
        if inventory is not None:
            player.inventory = inventory
            selected = player.inventory[player.selectedSlot]
            player.heldItem = selected["id"] if selected["count"] > 0 else 0
        return player, True

    def load(self) -> None:
        if not self.save_path.exists():
            return
        try:
            raw = json.loads(self.save_path.read_text(encoding="utf-8"))
            self.seed = int(raw.get("seed", self.seed)) % 2_147_483_647
            self.world_time = float(raw.get("worldTime", self.world_time))
            blocks = raw.get("blocks", {})
            if isinstance(blocks, dict):
                self.blocks = {str(k): int(v) for k, v in blocks.items()}
            operators = raw.get("operators", [])
            if isinstance(operators, list):
                self.operators = {str(name).strip().casefold() for name in operators if str(name).strip()}
            profiles = raw.get("playerProfiles", {})
            if isinstance(profiles, dict):
                for key, entry in profiles.items():
                    if not isinstance(entry, dict):
                        continue
                    username = str(entry.get("username", key)).strip()[:20]
                    if not USERNAME_PATTERN.fullmatch(username):
                        continue
                    inventory = self.sanitize_inventory(entry.get("inventory"))
                    normalized = dict(entry)
                    normalized["username"] = username
                    normalized["inventory"] = inventory or [{"id": 0, "count": 0} for _ in range(MAX_INVENTORY_SLOTS)]
                    self.player_profiles[self.profile_key(username)] = normalized
            for entry in raw.get("mobs", []):
                try:
                    type_key = str(entry["typeKey"])
                    if type_key not in MOB_DEFINITIONS:
                        continue
                    definition = MOB_DEFINITIONS[type_key]
                    mob = MobState(
                        id=str(entry["id"]), typeKey=type_key,
                        x=float(entry["x"]), y=float(entry["y"]), z=float(entry["z"]),
                        dimension=max(0, min(2, int(entry.get("dimension", 0)))),
                        health=max(0.1, min(float(definition["health"]), float(entry.get("health", definition["health"])))),
                        maxHealth=float(definition["health"]),
                        bodyRotation=float(entry.get("bodyRotation", 0.0)),
                        headRotation=float(entry.get("headRotation", 0.0)),
                    )
                    self.mobs[mob.id] = mob
                except (KeyError, TypeError, ValueError):
                    continue
            print(
                f"Loaded shared world: seed={self.seed}, edits={len(self.blocks)}, "
                f"operators={len(self.operators)}, players={len(self.player_profiles)}, mobs={len(self.mobs)}"
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"Warning: could not load {self.save_path.name}: {exc}")

    def save(self) -> None:
        self.tick()
        profiles = dict(self.player_profiles)
        for player in self.players.values():
            profiles[self.profile_key(player.username)] = self.player_profile(player)
        payload = {
            "formatVersion": 4,
            "seed": self.seed,
            "worldTime": self.world_time,
            "blocks": self.blocks,
            "operators": sorted(self.operators),
            "playerProfiles": profiles,
            "mobs": [asdict(mob) for mob in self.mobs.values()],
            "savedAtUnix": time.time(),
        }
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=self.save_path.name + ".", suffix=".tmp", dir=self.save_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, separators=(",", ":"), sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.save_path)
            self.dirty = False
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def block_snapshot(self) -> list[dict[str, int]]:
        return [
            {"dimension": d, "x": x, "y": y, "z": z, "blockType": block_type}
            for key, block_type in self.blocks.items()
            for d, x, y, z in [self.parse_block_key(key)]
        ]

    def player_snapshot(self) -> list[dict[str, Any]]:
        return [self.public_player_state(player) for player in self.players.values()]

    def mob_snapshot(self) -> list[dict[str, Any]]:
        return [asdict(mob) for mob in self.mobs.values()]

    def item_snapshot(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.items.values()]

    def recompute_mob_hosts(self) -> bool:
        changed = False
        for dimension in (0, 1, 2):
            old = self.mob_hosts.get(dimension)
            eligible = [
                player.id for player in self.players.values()
                if player.dimension == dimension and player.health > 0 and player.gamemode != "spectator"
            ]
            new = old if old in eligible else (eligible[0] if eligible else None)
            if new != old:
                self.mob_hosts[dimension] = new
                changed = True
        return changed


class ClientRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(SCRIPT_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", ""}:
            self.path = f"/{CLIENT_FILENAME}"
        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"HTTP {self.address_string()}: {fmt % args}")


world: MellorCraftWorld


def finite_number(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def bounded_int(value: Any, minimum: int, maximum: int, default: int = 0) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def unique_username(requested: str) -> str:
    base = requested.strip()
    used = {player.username.casefold() for player in world.players.values()}
    if base.casefold() not in used:
        return base
    for suffix in range(2, 1000):
        candidate = f"{base[: max(1, 20 - len(str(suffix)) - 1)]}_{suffix}"
        if candidate.casefold() not in used:
            return candidate
    return f"Player_{uuid.uuid4().hex[:6]}"


async def send_json(websocket: Any, payload: dict[str, Any]) -> None:
    await websocket.send(json.dumps(payload, separators=(",", ":")))


async def broadcast(payload: dict[str, Any], exclude_id: str | None = None, minimum_protocol: int = 1) -> None:
    if not world.connections:
        return
    encoded = json.dumps(payload, separators=(",", ":"))
    dead: list[str] = []
    for player_id, websocket in list(world.connections.items()):
        if player_id == exclude_id or world.client_protocols.get(player_id, 1) < minimum_protocol:
            continue
        try:
            await websocket.send(encoded)
        except ConnectionClosed:
            dead.append(player_id)
        except Exception as exc:
            print(f"Broadcast failure for {player_id}: {exc}")
            dead.append(player_id)
    for player_id in dead:
        world.connections.pop(player_id, None)
        player = world.players.pop(player_id, None)
        if player is not None:
            world.remember_player(player)
        world.client_protocols.pop(player_id, None)


async def broadcast_mob_hosts() -> None:
    await broadcast(
        {"type": "mob_hosts", "hosts": {str(k): v for k, v in world.mob_hosts.items()}},
        minimum_protocol=3,
    )


async def handle_block_change(player_id: str, data: dict[str, Any]) -> None:
    x = bounded_int(data.get("x"), -2_000_000, 2_000_000)
    y = bounded_int(data.get("y"), 0, WORLD_HEIGHT - 1)
    z = bounded_int(data.get("z"), -2_000_000, 2_000_000)
    dimension = bounded_int(data.get("dimension"), 0, 2)
    block_type = bounded_int(data.get("blockType"), 0, 255)
    previous_type = bounded_int(data.get("previousType"), 0, 255)

    target_dimensions = [dimension]
    if dimension in (0, 1) and (block_type == PORTAL_BLOCK or previous_type == PORTAL_BLOCK):
        target_dimensions = [0, 1]

    for target_dimension in target_dimensions:
        world.blocks[world.block_key(target_dimension, x, y, z)] = block_type
        await broadcast({
            "type": "block_update", "playerId": player_id, "dimension": target_dimension,
            "x": x, "y": y, "z": z, "blockType": block_type,
        })
    world.dirty = True


async def damage_player(
    victim: PlayerState,
    damage: float,
    source_name: str,
    dx: float,
    dz: float,
    vertical: float = 4.0,
) -> None:
    if victim.gamemode != "survival" or victim.health <= 0:
        return
    now = time.monotonic()
    if now < world.damage_locks.get(victim.id, 0.0):
        return
    victim.health = max(0.0, victim.health - max(0.0, damage))
    world.damage_locks[victim.id] = now + 0.45
    horizontal = math.hypot(dx, dz)
    if horizontal < 0.01:
        dx, dz, horizontal = 0.0, -1.0, 1.0
    knockback_x = (dx / horizontal) * 8.0
    knockback_z = (dz / horizontal) * 8.0
    websocket = world.connections.get(victim.id)
    if websocket is not None:
        await send_json(websocket, {
            "type": "player_hit", "health": victim.health, "attacker": source_name,
            "knockback": {"x": knockback_x, "z": knockback_z, "vertical": vertical, "duration": 0.35},
        })
    await broadcast({"type": "player_damaged", "playerId": victim.id, "health": victim.health})


async def handle_player_attack(attacker_id: str, data: dict[str, Any]) -> None:
    attacker = world.players.get(attacker_id)
    victim = world.players.get(str(data.get("targetId", "")))
    if attacker is None or victim is None or attacker.id == victim.id:
        return
    now = time.monotonic()
    if now < world.attack_cooldowns.get(attacker.id, 0.0):
        return
    world.attack_cooldowns[attacker.id] = now + 0.4
    if attacker.gamemode == "spectator" or attacker.dimension != victim.dimension:
        return
    dx, dy, dz = victim.x - attacker.x, victim.y - attacker.y, victim.z - attacker.z
    if math.sqrt(dx * dx + dy * dy + dz * dz) > 4.5:
        return
    await damage_player(victim, SWORD_DAMAGE.get(attacker.heldItem, 1.0), attacker.username, dx, dz)


async def spawn_dropped_item(item_id: int, count: int, x: float, y: float, z: float, dimension: int, vx: float = 0.0, vy: float = 0.0, vz: float = 0.0) -> DroppedItemState:
    item = DroppedItemState(
        id=uuid.uuid4().hex, itemId=bounded_int(item_id, 1, 255, 1), count=bounded_int(count, 1, 100, 1),
        x=x, y=y, z=z, dimension=bounded_int(dimension, 0, 2), vx=vx, vy=vy, vz=vz,
    )
    world.items[item.id] = item
    await broadcast({"type": "item_spawned", "item": asdict(item)}, minimum_protocol=3)
    return item


async def remove_mob(
    mob_id: str,
    *,
    reason: str = "despawn",
    killer_id: str | None = None,
) -> None:
    """Remove a shared mob without confusing despawning with a kill.

    Loot is intentionally generated only for a server-validated player kill.
    Distance despawns, void cleanup, admin cleanup, and environmental deaths
    remove the mob silently. This matches the original single-player behavior,
    where raw meat is awarded from the player's mob attack path.
    """
    mob = world.mobs.pop(mob_id, None)
    if mob is None:
        return
    definition = MOB_DEFINITIONS[mob.typeKey]
    player_kill = reason == "player_kill" and killer_id is not None and killer_id in world.players
    await broadcast(
        {"type": "mob_removed", "mobId": mob.id, "reason": reason},
        minimum_protocol=3,
    )
    if player_kill and definition.get("dropMeat"):
        await spawn_dropped_item(RAW_MEAT_ITEM, 1, mob.x, mob.y + 0.4, mob.z, mob.dimension)
    if mob.typeKey == "MELLOR_BOSS" and player_kill:
        await broadcast({"type": "system", "message": "The Mellor Boss was defeated!"})
    world.dirty = True


async def handle_mob_spawn(player_id: str, data: dict[str, Any]) -> None:
    dimension = bounded_int(data.get("dimension"), 0, 2)
    if world.mob_hosts.get(dimension) != player_id:
        return
    if sum(1 for mob in world.mobs.values() if mob.dimension == dimension) >= MOB_CAP_PER_DIMENSION:
        return
    type_key = str(data.get("typeKey", ""))
    if type_key not in MOB_DEFINITIONS:
        return
    requested_id = str(data.get("id", ""))
    mob_id = requested_id if ENTITY_ID_PATTERN.fullmatch(requested_id) and requested_id not in world.mobs else uuid.uuid4().hex
    definition = MOB_DEFINITIONS[type_key]
    mob = MobState(
        id=mob_id, typeKey=type_key,
        x=max(-2_000_000.0, min(2_000_000.0, finite_number(data.get("x")))),
        y=max(-100.0, min(1000.0, finite_number(data.get("y"), 50.0))),
        z=max(-2_000_000.0, min(2_000_000.0, finite_number(data.get("z")))),
        dimension=dimension, health=float(definition["health"]), maxHealth=float(definition["health"]),
        bodyRotation=finite_number(data.get("bodyRotation")), headRotation=finite_number(data.get("headRotation")),
    )
    world.mobs[mob.id] = mob
    world.dirty = True
    await broadcast({"type": "mob_spawned", "mob": asdict(mob)}, minimum_protocol=3)


async def handle_mob_update(player_id: str, data: dict[str, Any]) -> None:
    updates = data.get("mobs", [])
    if not isinstance(updates, list):
        return
    for entry in updates[:80]:
        if not isinstance(entry, dict):
            continue
        mob = world.mobs.get(str(entry.get("id", "")))
        if mob is None or world.mob_hosts.get(mob.dimension) != player_id:
            continue
        mob.x = max(-2_000_000.0, min(2_000_000.0, finite_number(entry.get("x"), mob.x)))
        mob.y = max(-100.0, min(1000.0, finite_number(entry.get("y"), mob.y)))
        mob.z = max(-2_000_000.0, min(2_000_000.0, finite_number(entry.get("z"), mob.z)))
        mob.bodyRotation = finite_number(entry.get("bodyRotation"), mob.bodyRotation)
        mob.headRotation = finite_number(entry.get("headRotation"), mob.headRotation)
        mob.vx = max(-30.0, min(30.0, finite_number(entry.get("vx"), mob.vx)))
        mob.vy = max(-50.0, min(50.0, finite_number(entry.get("vy"), mob.vy)))
        mob.vz = max(-30.0, min(30.0, finite_number(entry.get("vz"), mob.vz)))
    if updates:
        world.dirty = True


async def handle_mob_environment_damage(player_id: str, data: dict[str, Any]) -> None:
    mob = world.mobs.get(str(data.get("mobId", "")))
    if mob is None or world.mob_hosts.get(mob.dimension) != player_id:
        return
    now = time.monotonic()
    if now < world.mob_environment_cooldowns.get(mob.id, 0.0):
        return
    world.mob_environment_cooldowns[mob.id] = now + 0.2
    amount = max(0.0, min(10.0, finite_number(data.get("amount"))))
    if amount <= 0:
        return
    mob.health = max(0.0, mob.health - amount)
    await broadcast({"type": "mob_damaged", "mobId": mob.id, "health": mob.health}, minimum_protocol=3)
    if mob.health <= 0:
        await remove_mob(mob.id, reason="environment")


async def handle_mob_attack(attacker_id: str, data: dict[str, Any]) -> None:
    attacker = world.players.get(attacker_id)
    mob = world.mobs.get(str(data.get("mobId", "")))
    if attacker is None or mob is None or attacker.gamemode == "spectator" or attacker.dimension != mob.dimension:
        return
    now = time.monotonic()
    cooldown_key = f"mob:{attacker.id}"
    if now < world.attack_cooldowns.get(cooldown_key, 0.0):
        return
    world.attack_cooldowns[cooldown_key] = now + 0.4
    dx, dy, dz = mob.x - attacker.x, mob.y - attacker.y, mob.z - attacker.z
    if math.sqrt(dx * dx + dy * dy + dz * dz) > 4.5:
        return
    damage = SWORD_DAMAGE.get(attacker.heldItem, 1.0)
    mob.health = max(0.0, mob.health - damage)
    horizontal = math.hypot(dx, dz) or 1.0
    knockback = {"x": dx / horizontal * 8.0, "z": dz / horizontal * 8.0, "vertical": 4.0, "duration": 0.3}
    await broadcast({
        "type": "mob_damaged", "mobId": mob.id, "health": mob.health,
        "knockback": knockback, "attackerId": attacker.id,
    }, minimum_protocol=3)
    if mob.health <= 0:
        await remove_mob(mob.id, reason="player_kill", killer_id=attacker.id)


async def handle_mob_attack_player(player_id: str, data: dict[str, Any]) -> None:
    mob = world.mobs.get(str(data.get("mobId", "")))
    victim = world.players.get(str(data.get("targetId", "")))
    if mob is None or victim is None or world.mob_hosts.get(mob.dimension) != player_id:
        return
    definition = MOB_DEFINITIONS[mob.typeKey]
    if not definition["hostile"] or victim.dimension != mob.dimension:
        return
    now = time.monotonic()
    if now < world.mob_attack_cooldowns.get(mob.id, 0.0):
        return
    dx, dy, dz = victim.x - mob.x, victim.y - mob.y, victim.z - mob.z
    if math.sqrt(dx * dx + dy * dy + dz * dz) > 2.2:
        return
    world.mob_attack_cooldowns[mob.id] = now + 1.25
    await damage_player(victim, float(definition["damage"]), definition.get("name", mob.typeKey.replace("_", " ").title()), dx, dz)


async def handle_drop_item(player_id: str, data: dict[str, Any]) -> None:
    player = world.players.get(player_id)
    if player is None or player.gamemode == "spectator" or player.health <= 0:
        return
    item_id = bounded_int(data.get("itemId"), 1, 255)
    if item_id <= 0:
        return
    look_x = -math.sin(player.yaw)
    look_z = -math.cos(player.yaw)
    await spawn_dropped_item(
        item_id, 1,
        player.x + look_x * 0.8, player.y + 1.1, player.z + look_z * 0.8,
        player.dimension, look_x * 3.5, 1.2, look_z * 3.5,
    )


async def handle_client_message(player_id: str, data: dict[str, Any]) -> None:
    message_type = data.get("type")
    player = world.players.get(player_id)
    if player is None:
        return

    if message_type == "player_update":
        player.x = max(-2_000_000.0, min(2_000_000.0, finite_number(data.get("x"), player.x)))
        player.y = max(-100.0, min(1000.0, finite_number(data.get("y"), player.y)))
        player.z = max(-2_000_000.0, min(2_000_000.0, finite_number(data.get("z"), player.z)))
        player.yaw = finite_number(data.get("yaw"), player.yaw)
        player.pitch = max(-math.pi / 2, min(math.pi / 2, finite_number(data.get("pitch"), player.pitch)))
        player.dimension = bounded_int(data.get("dimension"), 0, 2, player.dimension)
        if time.monotonic() >= world.damage_locks.get(player.id, 0.0):
            player.health = max(0.0, min(10.0, finite_number(data.get("health"), player.health)))
        player.heldItem = bounded_int(data.get("heldItem"), 0, 255)
        if world.client_protocols.get(player_id, 1) >= 4:
            inventory = world.sanitize_inventory(data.get("inventory"))
            if inventory is not None:
                player.inventory = inventory
            player.selectedSlot = bounded_int(data.get("selectedSlot"), 0, 8, player.selectedSlot)
            selected = player.inventory[player.selectedSlot]
            player.heldItem = selected["id"] if selected["count"] > 0 else 0
        world.dirty = True
        if world.recompute_mob_hosts():
            await broadcast_mob_hosts()
        return

    if message_type == "block_change":
        await handle_block_change(player_id, data)
    elif message_type == "attack_player" and world.client_protocols.get(player_id, 1) >= 2:
        await handle_player_attack(player_id, data)
    elif message_type == "attack_mob" and world.client_protocols.get(player_id, 1) >= 3:
        await handle_mob_attack(player_id, data)
    elif message_type == "mob_attack_player" and world.client_protocols.get(player_id, 1) >= 3:
        await handle_mob_attack_player(player_id, data)
    elif message_type == "mob_spawn" and world.client_protocols.get(player_id, 1) >= 3:
        await handle_mob_spawn(player_id, data)
    elif message_type == "mob_update" and world.client_protocols.get(player_id, 1) >= 3:
        await handle_mob_update(player_id, data)
    elif message_type == "mob_environment_damage" and world.client_protocols.get(player_id, 1) >= 3:
        await handle_mob_environment_damage(player_id, data)
    elif message_type == "mob_remove" and world.client_protocols.get(player_id, 1) >= 3:
        mob = world.mobs.get(str(data.get("mobId", "")))
        if mob is not None and world.mob_hosts.get(mob.dimension) == player_id:
            requested_reason = str(data.get("reason", "despawn"))
            reason = requested_reason if requested_reason in {"despawn", "void", "admin"} else "despawn"
            await remove_mob(mob.id, reason=reason)
    elif message_type == "drop_item" and world.client_protocols.get(player_id, 1) >= 3:
        await handle_drop_item(player_id, data)
    elif message_type == "request_boss_spawn" and world.client_protocols.get(player_id, 1) >= 3:
        if player.dimension == 2 and not any(m.typeKey == "MELLOR_BOSS" and m.dimension == 2 for m in world.mobs.values()):
            definition = MOB_DEFINITIONS["MELLOR_BOSS"]
            mob = MobState(uuid.uuid4().hex, "MELLOR_BOSS", 0.0, 52.0, 10.0, 2, definition["health"], definition["health"])
            world.mobs[mob.id] = mob
            world.dirty = True
            await broadcast({"type": "mob_spawned", "mob": asdict(mob)}, minimum_protocol=3)
    elif message_type == "chat":
        message = str(data.get("message", "")).strip()[:200]
        if message:
            await broadcast({"type": "chat", "username": player.username, "message": message})
    elif message_type == "request_gamemode" and world.client_protocols.get(player_id, 1) >= 2:
        mode = str(data.get("gamemode", ""))
        if not player.isOperator:
            await send_json(world.connections[player_id], {"type": "error", "message": "Only server operators can switch gamemode."})
        elif mode in {"survival", "creative", "spectator"}:
            player.gamemode = mode
            if mode != "survival":
                player.health = 10.0
            await send_json(world.connections[player_id], {"type": "gamemode_update", "gamemode": mode})
            await broadcast({"type": "system", "message": f"{player.username} changed gamemode to {mode}."})
    elif message_type == "set_time":
        if world.client_protocols.get(player_id, 1) >= 2 and not player.isOperator:
            await send_json(world.connections[player_id], {"type": "error", "message": "Only server operators can set the world time."})
            return
        hour = finite_number(data.get("hour"), -1.0)
        if 0.0 <= hour <= 24.0:
            world.tick()
            world.world_time = math.floor(world.world_time) + hour / 24.0
            world.dirty = True
            await broadcast({"type": "system", "message": f"{player.username} set the time to {hour:g}:00"})
    elif message_type == "respawn":
        player.x = finite_number(data.get("x"), player.x)
        player.y = finite_number(data.get("y"), player.y)
        player.z = finite_number(data.get("z"), player.z)
        player.dimension = bounded_int(data.get("dimension"), 0, 2)
        player.health = 10.0
        world.damage_locks[player.id] = time.monotonic() + 2.0


async def websocket_handler(websocket: Any, *_args: Any) -> None:
    player_id: str | None = None
    try:
        print(f"WebSocket connection attempt from {getattr(websocket, 'remote_address', None)}")
        raw_join = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        try:
            join = json.loads(raw_join)
        except json.JSONDecodeError:
            await send_json(websocket, {"type": "error", "message": "Invalid join message."})
            return
        try:
            client_protocol = int(join.get("protocol", -1))
        except (TypeError, ValueError):
            client_protocol = -1
        if join.get("type") != "join" or client_protocol not in SUPPORTED_PROTOCOLS:
            message = f"Client/server protocol mismatch (client {client_protocol}, server {PROTOCOL_VERSION})."
            await send_json(websocket, {
                "type": "error", "message": message, "serverProtocol": PROTOCOL_VERSION,
                "supportedProtocols": list(SUPPORTED_PROTOCOLS),
            })
            try:
                await websocket.close(code=4002, reason="Client/server protocol mismatch")
            except Exception:
                pass
            return

        requested_username = str(join.get("username", "")).strip()
        if not USERNAME_PATTERN.fullmatch(requested_username):
            await send_json(websocket, {"type": "error", "message": "Invalid username."})
            return
        skin = str(join.get("skin", "steve"))
        if skin not in ALLOWED_SKINS:
            skin = "steve"

        player_id = uuid.uuid4().hex
        username = unique_username(requested_username)
        player, restored = world.restored_player(
            player_id, username, skin, username.casefold() in world.operators
        )
        world.players[player_id] = player
        world.connections[player_id] = websocket
        world.client_protocols[player_id] = client_protocol
        world.tick()
        world.recompute_mob_hosts()

        await send_json(websocket, {
            "type": "welcome", "protocol": PROTOCOL_VERSION, "negotiatedProtocol": client_protocol,
            "clientId": player_id, "username": username, "seed": world.seed,
            "worldTime": world.world_time, "dayLength": DAY_LENGTH_SECONDS,
            "isOperator": player.isOperator, "blocks": world.block_snapshot(),
            "playerState": world.player_profile(player) if restored and client_protocol >= 4 else None,
            "players": world.player_snapshot(),
            "mobs": world.mob_snapshot() if client_protocol >= 3 else [],
            "items": world.item_snapshot() if client_protocol >= 3 else [],
            "mobHosts": {str(k): v for k, v in world.mob_hosts.items()} if client_protocol >= 3 else {},
        })
        await broadcast({"type": "player_joined", "player": world.public_player_state(player)}, exclude_id=player_id)
        await broadcast_mob_hosts()
        print(f"WebSocket joined: {username} ({player_id[:8]}) protocol={client_protocol}")

        async for raw_message in websocket:
            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError:
                await send_json(websocket, {"type": "error", "message": "Malformed JSON message."})
                continue
            if isinstance(data, dict):
                await handle_client_message(player_id, data)
    except asyncio.TimeoutError:
        try:
            await send_json(websocket, {"type": "error", "message": "Join timed out."})
        except Exception:
            pass
    except ConnectionClosed:
        pass
    except Exception as exc:
        print(f"WebSocket handler error: {exc}")
    finally:
        if player_id is not None:
            player = world.players.pop(player_id, None)
            if player is not None:
                world.remember_player(player)
            world.connections.pop(player_id, None)
            world.client_protocols.pop(player_id, None)
            world.damage_locks.pop(player_id, None)
            world.attack_cooldowns.pop(player_id, None)
            hosts_changed = world.recompute_mob_hosts()
            if player is not None:
                print(f"WebSocket left: {player.username} ({player_id[:8]})")
                await broadcast({"type": "player_left", "playerId": player_id})
            if hosts_changed:
                await broadcast_mob_hosts()


async def world_broadcast_loop() -> None:
    while True:
        await asyncio.sleep(0.1)
        world.tick()
        hosts_changed = world.recompute_mob_hosts()
        await broadcast({
            "type": "world_state", "worldTime": world.world_time,
            "players": world.player_snapshot(),
            "mobs": world.mob_snapshot(), "items": world.item_snapshot(),
            "mobHosts": {str(k): v for k, v in world.mob_hosts.items()},
        })
        if hosts_changed:
            await broadcast_mob_hosts()


async def item_loop() -> None:
    previous = time.monotonic()
    while True:
        await asyncio.sleep(0.05)
        now = time.monotonic()
        dt = min(0.1, now - previous)
        previous = now
        removed: list[str] = []
        for item in list(world.items.values()):
            item.age += dt
            item.x += item.vx * dt
            item.y += item.vy * dt
            item.z += item.vz * dt
            item.vx *= max(0.0, 1.0 - dt * 3.0)
            item.vz *= max(0.0, 1.0 - dt * 3.0)
            item.vy *= max(0.0, 1.0 - dt * 4.0)
            if item.age > 300.0:
                removed.append(item.id)
                continue
            if item.age < 0.75:
                continue
            for player in world.players.values():
                if player.dimension != item.dimension or player.health <= 0 or player.gamemode == "spectator":
                    continue
                dx, dy, dz = player.x - item.x, (player.y + 0.8) - item.y, player.z - item.z
                if dx * dx + dy * dy + dz * dz <= 2.25:
                    websocket = world.connections.get(player.id)
                    if websocket is not None:
                        await send_json(websocket, {"type": "give_item", "itemId": item.itemId, "count": item.count})
                    removed.append(item.id)
                    break
        for item_id in set(removed):
            if world.items.pop(item_id, None) is not None:
                await broadcast({"type": "item_removed", "itemId": item_id}, minimum_protocol=3)


async def save_loop() -> None:
    while True:
        await asyncio.sleep(5.0)
        if world.dirty:
            try:
                world.save()
            except OSError as exc:
                print(f"Could not save world: {exc}")


def start_http_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), ClientRequestHandler)
    thread = threading.Thread(target=server.serve_forever, name="MellorCraftHTTP", daemon=True)
    thread.start()
    return server


def local_ip_address() -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return str(probe.getsockname()[0])
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


def find_player_by_username(username: str) -> PlayerState | None:
    wanted = username.strip().casefold()
    return next((player for player in world.players.values() if player.username.casefold() == wanted), None)


async def set_operator(username: str, enabled: bool) -> str:
    cleaned = username.strip()
    if not cleaned:
        return "Usage: /op <username>" if enabled else "Usage: /deop <username>"
    player = find_player_by_username(cleaned)
    canonical = player.username if player is not None else cleaned
    key = canonical.casefold()
    if enabled:
        world.operators.add(key)
    else:
        world.operators.discard(key)
    world.dirty = True
    if player is not None:
        player.isOperator = enabled
        if not enabled and player.gamemode != "survival":
            player.gamemode = "survival"
            player.health = 10.0
            await send_json(world.connections[player.id], {"type": "gamemode_update", "gamemode": "survival"})
        await send_json(world.connections[player.id], {"type": "permission_update", "isOperator": enabled})
        await broadcast({"type": "system", "message": f"{player.username} {'is now' if enabled else 'is no longer'} a server operator."})
        return f"{'Opped' if enabled else 'Deopped'} connected player {player.username}."
    return f"{'Added' if enabled else 'Removed'} offline operator entry for {canonical}."


async def process_console_command(line: str) -> str:
    command = line.strip()
    if not command:
        return ""
    parts = command.split(maxsplit=1)
    name = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ""
    if name == "/op":
        return await set_operator(argument, True)
    if name == "/deop":
        return await set_operator(argument, False)
    if name == "/ops":
        return "Operators: " + (", ".join(sorted(world.operators)) if world.operators else "none")
    if name == "/list":
        names = [p.username + (" [OP]" if p.isOperator else "") for p in world.players.values()]
        return f"Players ({len(names)}): " + (", ".join(names) if names else "none")
    if name == "/mobs":
        counts = {dim: sum(1 for mob in world.mobs.values() if mob.dimension == dim) for dim in (0, 1, 2)}
        return f"Mobs: overworld={counts[0]}, alternate={counts[1]}, boss={counts[2]}"
    if name in {"/help", "help"}:
        return "Console commands: /op <username>, /deop <username>, /ops, /list, /mobs, /help"
    return "Unknown console command. Type /help."


def console_reader(loop: asyncio.AbstractEventLoop) -> None:
    while not loop.is_closed():
        try:
            line = input("server> ")
        except (EOFError, KeyboardInterrupt):
            return
        try:
            future = asyncio.run_coroutine_threadsafe(process_console_command(line), loop)
            result = future.result(timeout=5.0)
            if result:
                print(result)
        except Exception as exc:
            print(f"Console command failed: {exc}")


async def run_websocket_server() -> None:
    loop = asyncio.get_running_loop()
    threading.Thread(target=console_reader, args=(loop,), name="MellorCraftConsole", daemon=True).start()
    async with serve(
        websocket_handler, "0.0.0.0", WEBSOCKET_PORT,
        max_size=512 * 1024, ping_interval=20, ping_timeout=20,
    ):
        tasks = [
            asyncio.create_task(world_broadcast_loop()),
            asyncio.create_task(item_loop()),
            asyncio.create_task(save_loop()),
        ]
        try:
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                task.cancel()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Host a MellorCraft multiplayer world.")
    parser.add_argument("--seed", type=int, help="Seed used only when creating a new world save.")
    parser.add_argument("--reset-world", action="store_true", help="Delete the current shared-world save before starting.")
    return parser.parse_args()


def main() -> None:
    global world
    args = parse_args()
    client_path = SCRIPT_DIR / CLIENT_FILENAME
    save_path = SCRIPT_DIR / SAVE_FILENAME
    if not client_path.exists():
        raise SystemExit(f"Missing client file: {client_path}")
    if args.reset_world and save_path.exists():
        save_path.unlink()
    seed = None if args.seed is None else abs(args.seed) % 2_147_483_647
    world = MellorCraftWorld(save_path, requested_seed=seed)
    http_server = start_http_server()
    ip = local_ip_address()

    print("\nMellorCraft multiplayer server is running")
    print(f"  Host PC:       http://127.0.0.1:{HTTP_PORT}")
    print(f"  Other devices: http://{ip}:{HTTP_PORT}")
    print(f"  WebSocket:     ws://{ip}:{WEBSOCKET_PORT}")
    print(f"  Protocol:      {PROTOCOL_VERSION} (accepts {', '.join(map(str, SUPPORTED_PROTOCOLS))})")
    print(f"  World seed:    {world.seed}")
    print(f"  Save file:     {save_path.name}")
    print("Console commands: /op <username>, /deop <username>, /ops, /list, /mobs, /help")
    print("Press Ctrl+C to stop.\n")
    try:
        asyncio.run(run_websocket_server())
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        http_server.shutdown()
        http_server.server_close()
        try:
            world.save()
        except OSError as exc:
            print(f"Final save failed: {exc}")


if __name__ == "__main__":
    main()
