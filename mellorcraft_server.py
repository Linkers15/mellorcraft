#!/usr/bin/env python3
"""MellorCraft multiplayer host.

Serves the HTML client on TCP port 8000 and hosts the multiplayer WebSocket
service on TCP port 8765. The server owns shared world edits, time, players,
mobs, dropped items, PvP, permissions, and persistence.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import math
import os
import random
import re
import secrets
import shlex
import socket
import sys
import tempfile
import threading
import webbrowser
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
PROTOCOL_VERSION = 16
SUPPORTED_PROTOCOLS = (16,)
WORLD_HEIGHT = 248
PORTAL_BLOCK = 31
RESPAWN_BLOCK = 48
RED_BED = 93
BED_BLOCK_IDS = {48,93,94,95,96,97,98,99,153,154,155,156}
WORLD_Y_ORIGIN = 48
FURNACE_BLOCK = 22
AIR_BLOCK = 0
RAW_MEAT_ITEM = 106
RAW_PORKCHOP_ITEM = 112
RAW_BEEF_ITEM = 114
RAW_MUTTON_ITEM = 116
RAW_RABBIT_ITEM = 118
RAW_FOX_ITEM = 120
RAW_CAMEL_ITEM = 122
WHITE_WOOL_ITEM = 124
BLACK_WOOL_ITEM = 125
GRAY_WOOL_ITEM = 126
BROWN_WOOL_ITEM = 127
RAW_GOAT_ITEM = 128
COOKED_GOAT_ITEM = 129
LIGHT_GRAY_WOOL_ITEM = 130
PINK_WOOL_ITEM = 131
RED_DYE_ITEM = 133
ORANGE_DYE_ITEM = 134
YELLOW_DYE_ITEM = 135
BLUE_DYE_ITEM = 136
WHITE_DYE_ITEM = 137
PINK_DYE_ITEM = 138
PURPLE_DYE_ITEM = 139
LIGHT_GRAY_DYE_ITEM = 145
GRAY_DYE_ITEM = 146
BLACK_DYE_ITEM = 147
BROWN_DYE_ITEM = 148
IRON_ARMOR_ITEM = 149
GOLD_ARMOR_ITEM = 150
DIAMOND_ARMOR_ITEM = 151
MELLORITE_ARMOR_ITEM = 152
RED_WOOL_ITEM = 140
ORANGE_WOOL_ITEM = 141
YELLOW_WOOL_ITEM = 142
BLUE_WOOL_ITEM = 143
PURPLE_WOOL_ITEM = 144
MOB_CAP_PER_DIMENSION = 30
MAX_INVENTORY_SLOTS = 30
MAX_STACK_SIZE = 100
ALLOWED_SKINS = {"steve", "alex", "mellorite", "ember", "frost", "forest"}
SWORD_DAMAGE = {202: 4.0, 212: 5.0, 222: 6.0, 232: 5.0, 242: 8.0, 252: 10.0}
MOB_DEFINITIONS: dict[str, dict[str, Any]] = {
    "PIG": {"health": 10.0, "damage": 0.0, "hostile": False},
    "COW": {"health": 10.0, "damage": 0.0, "hostile": False},
    "CAMEL": {"health": 20.0, "damage": 0.0, "hostile": False},
    "BEAR": {"health": 30.0, "damage": 3.0, "hostile": True},
    "SHEEP_WHITE": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_BLACK": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_GRAY": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_LIGHT_GRAY": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_BROWN": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_PINK": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_RED": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_ORANGE": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_YELLOW": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_BLUE": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SHEEP_PURPLE": {"health": 10.0, "damage": 0.0, "hostile": False},
    "GOAT": {"health": 12.0, "damage": 0.0, "hostile": False},
    "RABBIT": {"health": 6.0, "damage": 0.0, "hostile": False},
    "FOX": {"health": 10.0, "damage": 0.0, "hostile": False},
    "SPIDER": {"health": 16.0, "damage": 1.5, "hostile": True},
    "ZOMBIE": {"health": 20.0, "damage": 1.0, "hostile": True},
    "SKELETON": {"health": 20.0, "damage": 1.0, "hostile": True},
    "RED_ALT_ZOMBIE": {"health": 40.0, "damage": 3.0, "hostile": True},
    "MELLOR_BOSS": {"health": 200.0, "damage": 5.0, "hostile": True},
}
MOB_LOOT: dict[str, list[tuple[int, int, int]]] = {
    "PIG": [(RAW_PORKCHOP_ITEM, 1, 3)], "COW": [(RAW_BEEF_ITEM, 1, 3)],
    "CAMEL": [(RAW_CAMEL_ITEM, 1, 2)], "GOAT": [(RAW_GOAT_ITEM, 1, 2)],
    "RABBIT": [(RAW_RABBIT_ITEM, 1, 2)], "FOX": [(RAW_FOX_ITEM, 1, 2)],
    "BEAR": [(RAW_MEAT_ITEM, 1, 2)],
    "SHEEP_WHITE": [(RAW_MUTTON_ITEM, 1, 2), (WHITE_WOOL_ITEM, 1, 1)],
    "SHEEP_BLACK": [(RAW_MUTTON_ITEM, 1, 2), (BLACK_WOOL_ITEM, 1, 1)],
    "SHEEP_GRAY": [(RAW_MUTTON_ITEM, 1, 2), (GRAY_WOOL_ITEM, 1, 1)],
    "SHEEP_LIGHT_GRAY": [(RAW_MUTTON_ITEM, 1, 2), (LIGHT_GRAY_WOOL_ITEM, 1, 1)],
    "SHEEP_BROWN": [(RAW_MUTTON_ITEM, 1, 2), (BROWN_WOOL_ITEM, 1, 1)],
    "SHEEP_PINK": [(RAW_MUTTON_ITEM, 1, 2), (PINK_WOOL_ITEM, 1, 1)],
    "SHEEP_RED": [(RAW_MUTTON_ITEM, 1, 2), (RED_WOOL_ITEM, 1, 1)],
    "SHEEP_ORANGE": [(RAW_MUTTON_ITEM, 1, 2), (ORANGE_WOOL_ITEM, 1, 1)],
    "SHEEP_YELLOW": [(RAW_MUTTON_ITEM, 1, 2), (YELLOW_WOOL_ITEM, 1, 1)],
    "SHEEP_BLUE": [(RAW_MUTTON_ITEM, 1, 2), (BLUE_WOOL_ITEM, 1, 1)],
    "SHEEP_PURPLE": [(RAW_MUTTON_ITEM, 1, 2), (PURPLE_WOOL_ITEM, 1, 1)],
}
FURNACE_RECIPES = {15: 101, 16: 102, 6: 24, 2: 25, 112: 113, 114: 115, 116: 117, 118: 119, 120: 121, 122: 123, 128: 129}
FURNACE_FUEL_SECONDS = {100: 80.0, 18: 800.0, 4: 15.0, 10: 15.0, 104: 5.0}
DIFFICULTY_DAMAGE_SCALE = {"peaceful": 0.0, "easy": 0.5, "normal": 1.0, "hard": 1.5, "hardcore": 1.5}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,20}$")
LEGACY_ACCOUNT_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_ -]{1,20}$")
ENTITY_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
SCRIPT_DIR = Path(__file__).resolve().parent
CLIENT_FILENAME = "mellorcraft.html"
LEGACY_SAVE_FILENAME = "mellorcraft_world.json"
WORLDS_DIRNAME = "worlds"
DEFAULT_WORLD_NAME = "World"
ACCOUNTS_FILENAME = "server_accounts.json"
PBKDF2_ITERATIONS = 210_000
RETIRED_ITEM_IDS = {109, 110, 111}  # legacy bucket, water bucket, lava bucket
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 128
WORLD_NAME_PATTERN = re.compile(r"^[A-Za-z0-9 _.-]{1,48}$")
DEFAULT_GAME_RULES: dict[str, bool | int | str] = {
    "doDaylightCycle": True,
    "doWeatherCycle": True,
    "keepInventory": True,
    "doMobSpawning": True,
    "pvp": True,
    "difficulty": "normal",
    "mobCap": MOB_CAP_PER_DIMENSION,
    "dayLength": int(DAY_LENGTH_SECONDS),
}
GAME_RULE_ORDER = tuple(DEFAULT_GAME_RULES)
BOOLEAN_GAME_RULES = {"doDaylightCycle", "doWeatherCycle", "keepInventory", "doMobSpawning", "pvp"}
GAME_RULE_ALIASES = {
    "daylightcycle": "doDaylightCycle", "dodaylightcycle": "doDaylightCycle",
    "weathercycle": "doWeatherCycle", "doweathercycle": "doWeatherCycle",
    "keepinventory": "keepInventory", "mobspawning": "doMobSpawning", "domobspawning": "doMobSpawning",
    "pvp": "pvp", "difficulty": "difficulty", "mobcap": "mobCap", "daylength": "dayLength",
}


def normalize_game_rules(value: Any) -> dict[str, bool | int | str]:
    raw = value if isinstance(value, dict) else {}
    normalized = dict(DEFAULT_GAME_RULES)
    for name in BOOLEAN_GAME_RULES:
        if name in raw:
            incoming = raw[name]
            if isinstance(incoming, str):
                lowered = incoming.strip().lower()
                if lowered in {"true", "on", "1", "yes"}:
                    normalized[name] = True
                elif lowered in {"false", "off", "0", "no"}:
                    normalized[name] = False
            else:
                normalized[name] = bool(incoming)
    difficulty = str(raw.get("difficulty", normalized["difficulty"])).strip().lower()
    normalized["difficulty"] = difficulty if difficulty in DIFFICULTY_DAMAGE_SCALE else "normal"
    for name, minimum, maximum in (("mobCap", 0, 200), ("dayLength", 60, 3600)):
        try:
            normalized[name] = max(minimum, min(maximum, round(float(raw.get(name, normalized[name])))))
        except (TypeError, ValueError):
            pass
    return normalized


def sanitize_furnace_state(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    ingredient_id = bounded_int(raw.get("ingredientId"), 0, 255)
    fuel_id = bounded_int(raw.get("fuelId"), 0, 255)
    output_id = bounded_int(raw.get("outputId"), 0, 255)
    ingredient_count = bounded_int(raw.get("ingredientCount"), 0, 100)
    fuel_count = bounded_int(raw.get("fuelCount"), 0, 100)
    output_count = bounded_int(raw.get("outputCount"), 0, 100)
    if ingredient_id in RETIRED_ITEM_IDS: ingredient_id, ingredient_count = 0, 0
    if fuel_id in RETIRED_ITEM_IDS: fuel_id, fuel_count = 0, 0
    if output_id in RETIRED_ITEM_IDS: output_id, output_count = 0, 0
    return {
        "ingredientId": ingredient_id, "ingredientCount": ingredient_count,
        "fuelId": fuel_id, "fuelCount": fuel_count,
        "outputId": output_id, "outputCount": output_count,
        "progress": max(0.0, min(10.0, finite_number(raw.get("progress")))), "burnTime": max(0.0, min(1000.0, finite_number(raw.get("burnTime")))),
    }


def inventory_capacity(inventory: list[dict[str, int]], item_id: int) -> int:
    capacity = 0
    for slot in inventory:
        sid = bounded_int(slot.get("id"), 0, 255)
        count = bounded_int(slot.get("count"), 0, MAX_STACK_SIZE)
        if count <= 0:
            capacity += MAX_STACK_SIZE
        elif sid == item_id:
            capacity += max(0, MAX_STACK_SIZE - count)
    return capacity


def inventory_can_fit(inventory: list[dict[str, int]], item_id: int, count: int) -> bool:
    return inventory_capacity(inventory, item_id) >= max(0, int(count))


def inventory_add(inventory: list[dict[str, int]], item_id: int, count: int) -> bool:
    count = max(0, int(count))
    if count <= 0:
        return True
    if not inventory_can_fit(inventory, item_id, count):
        return False
    for slot in inventory:
        if int(slot.get("id", 0)) == item_id and int(slot.get("count", 0)) < MAX_STACK_SIZE:
            add = min(MAX_STACK_SIZE - int(slot.get("count", 0)), count)
            slot["count"] = int(slot.get("count", 0)) + add
            count -= add
            if count <= 0:
                return True
    for slot in inventory:
        if int(slot.get("count", 0)) <= 0:
            slot["id"] = item_id
            slot["count"] = min(MAX_STACK_SIZE, count)
            count -= slot["count"]
            if count <= 0:
                return True
    return count <= 0


def difficulty_damage_scale() -> float:
    return float(DIFFICULTY_DAMAGE_SCALE.get(str(world.game_rules.get("difficulty", "normal")), 1.0)) if "world" in globals() else 1.0


ARMOR_PROTECTION = {IRON_ARMOR_ITEM: 0.20, GOLD_ARMOR_ITEM: 0.40, DIAMOND_ARMOR_ITEM: 0.60, MELLORITE_ARMOR_ITEM: 0.80}
def armor_adjusted_damage(amount: float, armor_id: int) -> float:
    raw = max(0.0, finite_number(amount))
    if raw <= 0.0: return 0.0
    reduced = raw * (1.0 - ARMOR_PROTECTION.get(int(armor_id), 0.0))
    return max(0.5, math.ceil((reduced - 1e-9) * 2.0) / 2.0)


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
    hunger: float = 20.0
    gamemode: str = "survival"
    heldItem: int = 0
    crouching: bool = False
    renderDistance: int = 6
    selectedSlot: int = 0
    armorId: int = 0
    inventory: list[dict[str, int]] = field(
        default_factory=lambda: [{"id": 0, "count": 0} for _ in range(MAX_INVENTORY_SLOTS)]
    )
    isOperator: bool = False
    originalSpawn: dict[str, Any] | None = None
    respawnPoint: dict[str, Any] | None = None


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
    groundY: float | None = None


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
    floorY: float | None = None


class MellorCraftWorld:
    def __init__(self, save_path: Path, requested_seed: int | None = None, world_name: str = DEFAULT_WORLD_NAME) -> None:
        self.save_path = save_path
        self.world_name = world_name
        self.seed = requested_seed if requested_seed is not None else random.randint(0, 2_147_483_646)
        self.world_time = 0.25
        self.weather_seed = random.randint(0, 2_147_483_646)
        self.weather_phase = 0.0
        self.game_rules = dict(DEFAULT_GAME_RULES)
        self.world_gen: dict[str, Any] = {"type": "normal"}
        self.boss_defeated = False
        self.blocks: dict[str, int] = {}
        self.players: dict[str, PlayerState] = {}
        self.connections: dict[str, Any] = {}
        self.client_protocols: dict[str, int] = {}
        self.client_device_classes: dict[str, str] = {}
        self.client_last_updates: dict[str, float] = {}
        self.operators: set[str] = set()
        self.banned_players: set[str] = set()
        self.player_profiles: dict[str, dict[str, Any]] = {}
        self.mobs: dict[str, MobState] = {}
        self.items: dict[str, DroppedItemState] = {}
        self.furnaces: dict[str, dict[str, Any]] = {}
        self.mob_hosts: dict[int, str | None] = {0: None, 1: None, 2: None}
        self.damage_locks: dict[str, float] = {}
        self.teleport_locks: dict[str, float] = {}
        self.attack_cooldowns: dict[str, float] = {}
        self.mob_attack_cooldowns: dict[str, float] = {}
        self.mob_environment_cooldowns: dict[str, float] = {}
        self.mob_out_of_range_since: dict[str, float] = {}
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
        if bool(self.game_rules["doDaylightCycle"]):
            self.world_time += elapsed / max(60.0, float(self.game_rules["dayLength"]))
        if bool(self.game_rules["doWeatherCycle"]):
            self.weather_phase += elapsed * 0.35
        if elapsed > 0 and (bool(self.game_rules["doDaylightCycle"]) or bool(self.game_rules["doWeatherCycle"])):
            self.dirty = True
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
            if item_id in RETIRED_ITEM_IDS or item_id == 0 or count == 0:
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
            "health": player.health, "hunger": player.hunger, "gamemode": player.gamemode,
            "heldItem": player.heldItem, "armorId": player.armorId, "crouching": player.crouching, "renderDistance": player.renderDistance, "isOperator": player.isOperator,
        }

    @staticmethod
    def player_profile(player: PlayerState) -> dict[str, Any]:
        return {
            "username": player.username, "skin": player.skin,
            "x": player.x, "y": player.y, "z": player.z,
            "yaw": player.yaw, "pitch": player.pitch, "dimension": player.dimension,
            "health": player.health, "hunger": player.hunger, "gamemode": player.gamemode,
            "heldItem": player.heldItem, "selectedSlot": player.selectedSlot, "armorId": player.armorId,
            "inventory": [{"id": slot["id"], "count": slot["count"]} for slot in player.inventory],
            "originalSpawn": dict(player.originalSpawn) if isinstance(player.originalSpawn, dict) else None,
            "respawnPoint": dict(player.respawnPoint) if isinstance(player.respawnPoint, dict) else None,
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
        player.hunger = max(0.0, min(20.0, finite_number(profile.get("hunger"), player.hunger)))
        saved_mode = str(profile.get("gamemode", "survival"))
        player.gamemode = saved_mode if saved_mode in {"survival", "creative", "spectator"} else "survival"
        if not is_operator and player.gamemode != "survival":
            player.gamemode = "survival"
        player.heldItem = bounded_int(profile.get("heldItem"), 0, 255, player.heldItem)
        player.selectedSlot = bounded_int(profile.get("selectedSlot"), 0, 8, player.selectedSlot)
        armor_id = bounded_int(profile.get("armorId"), 0, 255)
        player.armorId = armor_id if armor_id in ARMOR_PROTECTION else 0
        inventory = self.sanitize_inventory(profile.get("inventory"))
        if inventory is not None:
            player.inventory = inventory
            selected = player.inventory[player.selectedSlot]
            player.heldItem = selected["id"] if selected["count"] > 0 else 0
        original = profile.get("originalSpawn")
        if isinstance(original, dict):
            player.originalSpawn = {
                "x": finite_number(original.get("x"), player.x), "y": finite_number(original.get("y"), player.y),
                "z": finite_number(original.get("z"), player.z), "dimension": bounded_int(original.get("dimension"), 0, 2),
            }
        respawn = profile.get("respawnPoint")
        if isinstance(respawn, dict):
            player.respawnPoint = {
                "x": bounded_int(respawn.get("x"), -2_000_000, 2_000_000), "y": bounded_int(respawn.get("y"), 0, WORLD_HEIGHT - 1),
                "z": bounded_int(respawn.get("z"), -2_000_000, 2_000_000), "dimension": bounded_int(respawn.get("dimension"), 0, 2), "bedId": bounded_int(respawn.get("bedId"),0,255),
            }
        return player, True

    @staticmethod
    def legacy_chunk_edits_to_blocks(edits: Any) -> dict[str, int]:
        result: dict[str, int] = {}
        if not isinstance(edits, dict):
            return result
        chunk_size = 16
        for chunk_key, entries in edits.items():
            try:
                dimension, cx, cz = (int(part) for part in str(chunk_key).split(",", 2))
            except (TypeError, ValueError):
                continue
            if not isinstance(entries, list):
                continue
            for pair in entries:
                if not isinstance(pair, list) or len(pair) < 2:
                    continue
                try:
                    index, block_type = int(pair[0]), int(pair[1])
                    lz = index // (chunk_size * 200)
                    rem = index - lz * chunk_size * 200
                    y = rem // chunk_size
                    lx = rem - y * chunk_size
                    x, z = cx * chunk_size + lx, cz * chunk_size + lz
                    result[f"{dimension},{x},{y},{z}"] = block_type
                except (TypeError, ValueError):
                    continue
        return result

    def load(self) -> None:
        if not self.save_path.exists():
            return
        try:
            raw = json.loads(self.save_path.read_text(encoding="utf-8"))
            if int(raw.get('formatVersion',0) or 0)<12:
                # Shift only overworld internal coordinates. Preserve the visible
                # height (old voxel Y) and all non-overworld structures as-is.
                def migrate_point(entry):
                    if isinstance(entry,dict) and int(entry.get('dimension',0) or 0)==0:
                        for prop in ('y','highestY','groundY','floorY'):
                            if entry.get(prop) is not None:
                                try: entry[prop]=float(entry[prop])+WORLD_Y_ORIGIN
                                except (ValueError,TypeError): pass
                    return entry
                if not isinstance(raw.get('blocks'),dict):
                    raw['blocks']=self.legacy_chunk_edits_to_blocks(raw.get('chunkEdits'))
                relocated={}
                for key,typ in raw['blocks'].items():
                    try:
                        d,x,y,z=self.parse_block_key(key)
                        relocated[f'{d},{x},{y+(WORLD_Y_ORIGIN if d==0 else 0)},{z}']=RED_BED if int(typ)==RESPAWN_BLOCK else int(typ)
                    except (ValueError,TypeError): pass
                raw['blocks']=relocated
                for profile in list((raw.get('playerProfiles') or {}).values())+list((raw.get('lanPlayerProfiles') or {}).values()):
                    migrate_point(profile)
                    if isinstance(profile,dict):
                        migrate_point(profile.get('originalSpawn'))
                        migrate_point(profile.get('respawnPoint'))
                        if isinstance(profile.get('inventory'),list):
                            for slot in profile['inventory']:
                                if isinstance(slot,dict) and slot.get('id')==RESPAWN_BLOCK: slot['id']=RED_BED
                migrate_point(raw.get('playerState'))
                for entry in raw.get('mobs',[]): migrate_point(entry)
                for entry in raw.get('items',[]): migrate_point(entry)
                furnaces={}
                for key,value in (raw.get('furnaces') or {}).items():
                    try:
                        d,x,y,z=(int(v) for v in str(key).split(','))
                        key=f'{d},{x},{y+(WORLD_Y_ORIGIN if d==0 else 0)},{z}'
                    except (TypeError,ValueError): pass
                    furnaces[key]=value
                raw['furnaces']=furnaces
                raw['formatVersion']=12
                self.dirty=True
            self.world_name = str(raw.get("name", raw.get("worldName", self.world_name))).strip()[:48] or self.world_name
            self.seed = int(raw.get("seed", self.seed)) % 2_147_483_647
            self.world_time = float(raw.get("worldTime", self.world_time))
            self.weather_seed = int(raw.get("weatherSeed", self.weather_seed)) % 2_147_483_647
            self.weather_phase = float(raw.get("weatherPhase", self.weather_phase))
            self.game_rules = normalize_game_rules(raw.get("gameRules"))
            raw_world_gen = raw.get("worldGen")
            self.world_gen = dict(raw_world_gen) if isinstance(raw_world_gen, dict) else {"type": "normal"}
            self.boss_defeated = bool(raw.get("bossDefeated", False))
            blocks = raw.get("blocks")
            if not isinstance(blocks, dict):
                blocks = self.legacy_chunk_edits_to_blocks(raw.get("chunkEdits"))
            if isinstance(blocks, dict):
                self.blocks = {str(k): int(v) for k, v in blocks.items()}
            operators = raw.get("operators", [])
            if isinstance(operators, list):
                self.operators = {str(name).strip().casefold() for name in operators if str(name).strip()}
            banned_players = raw.get("bannedPlayers", [])
            if isinstance(banned_players, list):
                self.banned_players = {str(name).strip().casefold() for name in banned_players if str(name).strip()}
            profiles = raw.get("playerProfiles", {})
            if not isinstance(profiles, dict):
                profiles = {}
            legacy_profiles = raw.get("lanPlayerProfiles", {})
            if isinstance(legacy_profiles, dict):
                profiles = {**legacy_profiles, **profiles}
            legacy_player = raw.get("playerState")
            if isinstance(legacy_player, dict) and "player" not in profiles:
                profiles["player"] = {"username": "Player", "skin": "steve", **legacy_player}
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
                    if type_key not in MOB_DEFINITIONS or (self.boss_defeated and type_key == "MELLOR_BOSS"):
                        continue
                    definition = MOB_DEFINITIONS[type_key]
                    mob = MobState(
                        id=str(entry["id"]), typeKey=type_key, x=float(entry["x"]), y=float(entry["y"]), z=float(entry["z"]),
                        dimension=max(0, min(2, int(entry.get("dimension", 0)))),
                        health=max(0.1, min(float(definition["health"]), float(entry.get("health", definition["health"])))),
                        maxHealth=float(definition["health"]), bodyRotation=float(entry.get("bodyRotation", 0.0)),
                        headRotation=float(entry.get("headRotation", 0.0)), vx=float(entry.get("vx", 0.0)), vy=float(entry.get("vy", 0.0)), vz=float(entry.get("vz", 0.0)),
                        groundY=(finite_number(entry.get("groundY")) if entry.get("groundY") is not None else None),
                    )
                    self.mobs[mob.id] = mob
                except (KeyError, TypeError, ValueError):
                    continue
            for entry in raw.get("items", []):
                try:
                    loaded_item_id = bounded_int(entry.get("itemId"), 1, 255, 1)
                    if loaded_item_id in RETIRED_ITEM_IDS:
                        continue
                    item = DroppedItemState(
                        id=str(entry["id"]), itemId=loaded_item_id, count=bounded_int(entry.get("count"), 1, 100, 1),
                        x=finite_number(entry.get("x")), y=finite_number(entry.get("y")), z=finite_number(entry.get("z")),
                        dimension=bounded_int(entry.get("dimension"), 0, 2), vx=finite_number(entry.get("vx")), vy=finite_number(entry.get("vy")),
                        vz=finite_number(entry.get("vz")), age=max(0.0, finite_number(entry.get("age"))),
                        floorY=(finite_number(entry.get("floorY")) if entry.get("floorY") is not None else None),
                    )
                    self.items[item.id] = item
                except (KeyError, TypeError, ValueError):
                    continue
            raw_furnaces = raw.get("furnaces", {})
            if isinstance(raw_furnaces, dict):
                for key, value in raw_furnaces.items():
                    if isinstance(value, dict):
                        self.furnaces[str(key)] = sanitize_furnace_state(value)
            print(f"Loaded world '{self.world_name}': seed={self.seed}, edits={len(self.blocks)}, operators={len(self.operators)}, bans={len(self.banned_players)}, players={len(self.player_profiles)}, mobs={len(self.mobs)}")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"Warning: could not load {self.save_path.name}: {exc}")

    def save(self) -> None:
        self.tick()
        profiles = dict(self.player_profiles)
        for player in self.players.values():
            profiles[self.profile_key(player.username)] = self.player_profile(player)
        payload = {
            "format": "MellorCraftWorld", "formatVersion": 12, "version": "1.8.1", "name": self.world_name,
            "seed": self.seed, "worldTime": self.world_time, "weatherSeed": self.weather_seed, "weatherPhase": self.weather_phase,
            "bossDefeated": self.boss_defeated, "gameRules": self.game_rules, "worldGen": self.world_gen,
            "blocks": self.blocks, "operators": sorted(self.operators), "bannedPlayers": sorted(self.banned_players), "playerProfiles": profiles,
            "mobs": [asdict(mob) for mob in self.mobs.values()], "items": [asdict(item) for item in self.items.values()],
            "furnaces": self.furnaces,
            "updatedAt": int(time.time() * 1000),
        }
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=self.save_path.name + ".", suffix=".tmp", dir=self.save_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, separators=(",", ":"), sort_keys=True)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temp_name, self.save_path); self.dirty = False
        finally:
            if os.path.exists(temp_name): os.unlink(temp_name)

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
        now = time.monotonic()
        for dimension in (0, 1, 2):
            old = self.mob_hosts.get(dimension)
            eligible = [player.id for player in self.players.values()
                        if player.dimension == dimension and player.health > 0 and player.gamemode != "spectator"]
            active = [pid for pid in eligible if now - self.client_last_updates.get(pid, 0.0) <= 1.25]
            active_desktop = [pid for pid in active if self.client_device_classes.get(pid, "desktop") != "mobile"]
            desktop_eligible = [pid for pid in eligible if self.client_device_classes.get(pid, "desktop") != "mobile"]
            preferred = active_desktop or active or desktop_eligible or eligible
            new_host = old if old in preferred else (preferred[0] if preferred else None)
            if new_host != old:
                self.mob_hosts[dimension] = new_host
                changed = True
        return changed


_console_ui = None
_server_stop_event: asyncio.Event | None = None
HTTP_VERBOSE_LOGGING = False


def console_log(message: Any = "") -> None:
    """Print a server log without destroying an in-progress console command."""
    global _console_ui
    text = str(message)
    if _console_ui is not None:
        _console_ui.log(text)
    else:
        print(text)


class LiveServerConsole:
    """Small cross-platform console editor that redraws typed input after log lines."""
    PROMPT = "server> "

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.lock = threading.RLock()
        self.buffer: list[str] = []
        self.cursor = 0
        self.history: list[str] = []
        self.history_index: int | None = None
        self.active = False
        self.tty = bool(getattr(sys.stdin, "isatty", lambda: False)() and getattr(sys.stdout, "isatty", lambda: False)())
        self.last_render_width = len(self.PROMPT)

    def _clear_line_locked(self) -> None:
        if not self.tty:
            return
        if os.name == "nt":
            sys.stdout.write("\r" + (" " * max(self.last_render_width, len(self.PROMPT))) + "\r")
        else:
            sys.stdout.write("\r\x1b[2K")

    def _redraw_locked(self) -> None:
        if not self.active or not self.tty:
            return
        self._clear_line_locked()
        text = "".join(self.buffer)
        sys.stdout.write(self.PROMPT + text)
        self.last_render_width = len(self.PROMPT) + len(text)
        tail = len(text) - self.cursor
        if tail > 0:
            sys.stdout.write("\b" * tail if os.name == "nt" else f"\x1b[{tail}D")
        sys.stdout.flush()

    def log(self, message: str) -> None:
        with self.lock:
            if self.active and self.tty:
                self._clear_line_locked()
            sys.stdout.write(message.rstrip("\n") + "\n")
            if self.active and self.tty:
                self._redraw_locked()
            else:
                sys.stdout.flush()

    def _replace_buffer_locked(self, value: str) -> None:
        self.buffer = list(value)
        self.cursor = len(self.buffer)
        self._redraw_locked()

    def _history_move_locked(self, delta: int) -> None:
        if not self.history:
            return
        if self.history_index is None:
            self.history_index = len(self.history)
        self.history_index = max(0, min(len(self.history), self.history_index + delta))
        self._replace_buffer_locked("" if self.history_index == len(self.history) else self.history[self.history_index])

    def _submit_locked(self) -> str:
        line = "".join(self.buffer).strip()
        self._clear_line_locked()
        sys.stdout.write(self.PROMPT + "".join(self.buffer) + "\n")
        sys.stdout.flush()
        if line and (not self.history or self.history[-1] != line):
            self.history.append(line)
            self.history = self.history[-100:]
        self.history_index = None
        self.buffer = []
        self.cursor = 0
        self._redraw_locked()
        return line

    def _execute(self, line: str) -> None:
        if not line:
            return
        try:
            future = asyncio.run_coroutine_threadsafe(process_console_command(line), self.loop)
            result = future.result(timeout=10.0)
            if result:
                self.log(result)
        except Exception as exc:
            self.log(f"Console command failed: {exc}")

    def _handle_character(self, ch: str) -> str | None:
        with self.lock:
            if ch in {"\r", "\n"}:
                return self._submit_locked()
            if ch in {"\x08", "\x7f"}:
                if self.cursor > 0:
                    self.cursor -= 1
                    self.buffer.pop(self.cursor)
                    self._redraw_locked()
                return None
            if ch == "\x15":  # Ctrl+U
                self.buffer = []; self.cursor = 0; self._redraw_locked(); return None
            if ch == "\x04":  # Ctrl+D
                return "__EXIT__" if not self.buffer else None
            if ch == "\x01":  # Ctrl+A
                self.cursor = 0; self._redraw_locked(); return None
            if ch == "\x05":  # Ctrl+E
                self.cursor = len(self.buffer); self._redraw_locked(); return None
            if ch >= " " and ch != "\x7f":
                self.buffer.insert(self.cursor, ch)
                self.cursor += 1
                self._redraw_locked()
        return None

    def _run_windows(self) -> None:
        import msvcrt  # type: ignore
        with self.lock:
            self._redraw_locked()
        while not self.loop.is_closed():
            ch = msvcrt.getwch()
            if ch in {"\x00", "\xe0"}:
                code = msvcrt.getwch()
                with self.lock:
                    if code == "K" and self.cursor > 0:
                        self.cursor -= 1; self._redraw_locked()
                    elif code == "M" and self.cursor < len(self.buffer):
                        self.cursor += 1; self._redraw_locked()
                    elif code == "H": self._history_move_locked(-1)
                    elif code == "P": self._history_move_locked(1)
                continue
            line = self._handle_character(ch)
            if line == "__EXIT__": return
            if line is not None: self._execute(line)

    def _run_posix(self) -> None:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            with self.lock:
                self._redraw_locked()
            while not self.loop.is_closed():
                ch = sys.stdin.read(1)
                if not ch: return
                if ch == "\x1b":
                    second = sys.stdin.read(1)
                    third = sys.stdin.read(1) if second == "[" else ""
                    with self.lock:
                        if third == "D" and self.cursor > 0:
                            self.cursor -= 1; self._redraw_locked()
                        elif third == "C" and self.cursor < len(self.buffer):
                            self.cursor += 1; self._redraw_locked()
                        elif third == "A": self._history_move_locked(-1)
                        elif third == "B": self._history_move_locked(1)
                        elif third == "H": self.cursor = 0; self._redraw_locked()
                        elif third == "F": self.cursor = len(self.buffer); self._redraw_locked()
                    continue
                line = self._handle_character(ch)
                if line == "__EXIT__": return
                if line is not None: self._execute(line)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def run(self) -> None:
        self.active = True
        try:
            if not self.tty:
                while not self.loop.is_closed():
                    try:
                        line = input(self.PROMPT)
                    except (EOFError, KeyboardInterrupt):
                        return
                    self._execute(line)
                return
            if os.name == "nt": self._run_windows()
            else: self._run_posix()
        finally:
            with self.lock:
                self.active = False


class ServerAccountStore:
    def __init__(self, path: Path, worlds_dir: Path) -> None:
        self.path = path
        self.worlds_dir = worlds_dir
        self.accounts: dict[str, dict[str, Any]] = {}
        self.reserved_names: dict[str, str] = {}
        self.public_signup_enabled = True
        self.load()
        self.refresh_reserved_names()

    @staticmethod
    def key(username: str) -> str:
        return username.strip().casefold()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and "publicSignupEnabled" in raw:
                self.public_signup_enabled = bool(raw.get("publicSignupEnabled", True))
            source = raw.get("accounts", raw) if isinstance(raw, dict) else {}
            if not isinstance(source, dict):
                return
            for key, entry in source.items():
                if not isinstance(entry, dict):
                    continue
                username = str(entry.get("username", key)).strip()[:20]
                # Keep pre-v1.8 account records with spaces in memory so toggling the
                # signup policy cannot silently delete them from disk. New logins and
                # all newly-created accounts still use the stricter no-space rule.
                if not LEGACY_ACCOUNT_USERNAME_PATTERN.fullmatch(username):
                    continue
                salt = str(entry.get("salt", "")); verifier = str(entry.get("verifier", ""))
                if not salt or not verifier:
                    continue
                skin = str(entry.get("skin", "steve"))
                self.accounts[self.key(username)] = {
                    "username": username, "skin": skin if skin in ALLOWED_SKINS else "steve",
                    "salt": salt, "verifier": verifier,
                    "iterations": max(100_000, int(entry.get("iterations", PBKDF2_ITERATIONS))),
                }
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            console_log(f"Warning: could not load {self.path.name}: {exc}")

    def save(self) -> None:
        payload = {"format": "MellorCraftServerAccounts", "version": 2, "publicSignupEnabled": bool(self.public_signup_enabled), "accounts": self.accounts}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, separators=(",", ":"), sort_keys=True)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name): os.unlink(temp_name)

    def refresh_reserved_names(self) -> None:
        reserved: dict[str, str] = {}
        for _display, path in available_worlds(self.worlds_dir):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
            if not isinstance(raw, dict):
                continue
            for value in raw.get("operators", []):
                name = str(value).strip()[:20]
                if USERNAME_PATTERN.fullmatch(name): reserved[self.key(name)] = name
            profiles = raw.get("playerProfiles", {})
            if isinstance(profiles, dict):
                for key, entry in profiles.items():
                    name = str(entry.get("username", key) if isinstance(entry, dict) else key).strip()[:20]
                    if USERNAME_PATTERN.fullmatch(name): reserved[self.key(name)] = name
            legacy = raw.get("lanPlayerProfiles", {})
            if isinstance(legacy, dict):
                for key, entry in legacy.items():
                    name = str(entry.get("username", key) if isinstance(entry, dict) else key).strip()[:20]
                    if USERNAME_PATTERN.fullmatch(name): reserved[self.key(name)] = name
        current_world = globals().get("world")
        if current_world is not None:
            for key in getattr(current_world, "operators", set()):
                name = str(key).strip()[:20]
                if USERNAME_PATTERN.fullmatch(name): reserved[self.key(name)] = name
            for key, entry in getattr(current_world, "player_profiles", {}).items():
                name = str(entry.get("username", key) if isinstance(entry, dict) else key).strip()[:20]
                if USERNAME_PATTERN.fullmatch(name): reserved[self.key(name)] = name
        self.reserved_names = reserved

    @staticmethod
    def _derive(password: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)

    @staticmethod
    def _valid_password(password: str) -> bool:
        return PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH

    def signup(self, username: str, password: str, skin: str) -> tuple[dict[str, Any] | None, str | None]:
        if not self.public_signup_enabled:
            return None, "Account creation is locked on this server. Ask the server operator to create an account for you."
        self.refresh_reserved_names()
        key = self.key(username)
        if key in self.accounts:
            return None, "That username already has an account. Choose Sign In."
        if key in self.reserved_names:
            return None, "That username belongs to a legacy player/operator. The server owner must assign its password with /account setpassword."
        if not self._valid_password(password):
            return None, f"Password must be {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} characters."
        salt = secrets.token_bytes(16)
        verifier = self._derive(password, salt, PBKDF2_ITERATIONS)
        entry = {"username": username, "skin": skin if skin in ALLOWED_SKINS else "steve", "salt": salt.hex(), "verifier": verifier.hex(), "iterations": PBKDF2_ITERATIONS}
        self.accounts[key] = entry
        self.save()
        return entry, None

    def signin(self, username: str, password: str) -> tuple[dict[str, Any] | None, str | None]:
        entry = self.accounts.get(self.key(username))
        if entry is None:
            return None, "No account exists for that username on this server. Choose Sign Up if it is a new name."
        try:
            salt = bytes.fromhex(str(entry["salt"])); expected = bytes.fromhex(str(entry["verifier"])); iterations = int(entry.get("iterations", PBKDF2_ITERATIONS))
            actual = self._derive(password, salt, iterations)
        except (KeyError, ValueError, TypeError):
            return None, "This account record is damaged. Ask the server operator to reset its password."
        if not hmac.compare_digest(actual, expected):
            return None, "Incorrect password."
        return entry, None

    def create_account(self, username: str, password: str, skin: str) -> str:
        cleaned = username.strip()
        if not USERNAME_PATTERN.fullmatch(cleaned):
            return "Invalid username. Use 1-20 letters, numbers, _ or -; spaces are not allowed."
        if not self._valid_password(password):
            return f"Password must be {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} characters."
        if skin not in ALLOWED_SKINS:
            return "Invalid skin. Choose one of: " + ", ".join(sorted(ALLOWED_SKINS))
        key = self.key(cleaned)
        if key in self.accounts:
            return f"An account already exists for {self.accounts[key]['username']}."
        self.refresh_reserved_names()
        # Reserved legacy names are intentionally claimable only by the server operator.
        salt = secrets.token_bytes(16); verifier = self._derive(password, salt, PBKDF2_ITERATIONS)
        self.accounts[key] = {"username": cleaned, "skin": skin, "salt": salt.hex(), "verifier": verifier.hex(), "iterations": PBKDF2_ITERATIONS}
        self.save(); self.refresh_reserved_names()
        return f"Created account {cleaned} with skin {skin}."

    def set_public_signup(self, enabled: bool) -> str:
        self.public_signup_enabled = bool(enabled)
        self.save()
        return "Public account creation enabled." if self.public_signup_enabled else "Public account creation locked; only the server console can create accounts."

    def set_password(self, username: str, password: str, skin: str | None = None) -> str:
        cleaned = username.strip()
        if not USERNAME_PATTERN.fullmatch(cleaned): return "Invalid username. Use 1-20 letters, numbers, _ or -; spaces are not allowed."
        if not self._valid_password(password): return f"Password must be {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} characters."
        key = self.key(cleaned); previous = self.accounts.get(key, {})
        salt = secrets.token_bytes(16); verifier = self._derive(password, salt, PBKDF2_ITERATIONS)
        chosen_skin = skin if skin in ALLOWED_SKINS else str(previous.get("skin", "steve"))
        self.accounts[key] = {"username": str(previous.get("username", cleaned)), "skin": chosen_skin if chosen_skin in ALLOWED_SKINS else "steve", "salt": salt.hex(), "verifier": verifier.hex(), "iterations": PBKDF2_ITERATIONS}
        self.save(); self.refresh_reserved_names()
        return f"Password set for {self.accounts[key]['username']}."

    def delete(self, username: str) -> str:
        key = self.key(username)
        entry = self.accounts.pop(key, None)
        if entry is None: return f"No account exists for {username}."
        self.save(); return f"Deleted account for {entry['username']}."

    def list_text(self) -> str:
        if not self.accounts: return "Server accounts: none"
        return "Server accounts: " + ", ".join(sorted((str(v["username"]) for v in self.accounts.values()), key=str.casefold))


account_store: ServerAccountStore


class QuietThreadingHTTPServer(ThreadingHTTPServer):
    """Threading HTTP server that suppresses expected client disconnect noise.

    Browsers, scanners, mobile radios, and reverse proxies can close a socket after
    the server has begun sending a static file.  socketserver normally prints a full
    traceback for those routine disconnects.  Ignore only connection-abort errors;
    delegate every other exception to the standard handler so real server bugs are
    still visible.
    """

    _QUIET_WINERRORS = {64, 995, 10053, 10054, 10058}

    def handle_error(self, request: Any, client_address: Any) -> None:
        exc = sys.exc_info()[1]
        quiet = isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError))
        if isinstance(exc, OSError) and getattr(exc, "winerror", None) in self._QUIET_WINERRORS:
            quiet = True
        if quiet:
            if HTTP_VERBOSE_LOGGING:
                console_log(f"HTTP {client_address[0] if client_address else '?'}: client disconnected during response ({type(exc).__name__})")
            return
        super().handle_error(request, client_address)


class ClientRequestHandler(SimpleHTTPRequestHandler):
    """Static MellorCraft HTTP server with quiet-by-default request logging.

    Internet-facing game servers are routinely hit by generic scanners that send
    malformed HTTP, TLS, RDP, and arbitrary-method probes to every open port.
    Those probes are irrelevant to MellorCraft and previously flooded the live
    operator console.  Keep the HTTP service functional but suppress routine
    request/error noise unless --http-log is explicitly enabled.
    """

    # Do not advertise the host Python version to random scanners.
    server_version = "MellorCraftHTTP/1.8"
    sys_version = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(SCRIPT_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        clean_path = self.path.split("?", 1)[0]
        if clean_path == "/server-policy.json":
            payload = json.dumps({
                "publicSignupEnabled": bool(getattr(account_store, "public_signup_enabled", True)),
                "usernamePattern": "^[A-Za-z0-9_-]{1,20}$",
                "usernameHint": "1-20 letters, numbers, _ or -; no spaces",
            }, separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path in {"/", ""}:
            self.path = f"/{CLIENT_FILENAME}"
        elif clean_path == "/favicon.ico":
            # Browsers request this automatically.  A 204 avoids a pointless 404
            # and keeps the console quiet even in verbose mode.
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def do_OPTIONS(self) -> None:  # noqa: N802
        # Answer generic capability probes without invoking the default 501 path.
        self.send_response(204)
        self.send_header("Allow", "GET, HEAD, OPTIONS")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        # MellorCraft's static HTTP endpoint does not accept POST bodies.
        self.send_response(405)
        self.send_header("Allow", "GET, HEAD, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:
        if HTTP_VERBOSE_LOGGING:
            console_log(f"HTTP {self.address_string()}: {fmt % args}")

    def log_error(self, fmt: str, *args: Any) -> None:
        # BaseHTTPRequestHandler routes malformed request/version errors here.
        # Suppress them by default because they are overwhelmingly scanner noise.
        if HTTP_VERBOSE_LOGGING:
            console_log(f"HTTP {self.address_string()}: {fmt % args}")


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
            console_log(f"Broadcast failure for {player_id}: {exc}")
            dead.append(player_id)
    for player_id in dead:
        world.connections.pop(player_id, None)
        player = world.players.pop(player_id, None)
        if player is not None:
            world.remember_player(player)
        world.client_protocols.pop(player_id, None)
        world.client_device_classes.pop(player_id, None)
        world.client_last_updates.pop(player_id, None)


async def broadcast_mob_hosts() -> None:
    await broadcast(
        {"type": "mob_hosts", "hosts": {str(k): v for k, v in world.mob_hosts.items()}},
        minimum_protocol=3,
    )


def respawn_point_matches(point: Any, dimension: int, x: int, y: int, z: int) -> bool:
    return isinstance(point, dict) and bounded_int(point.get("dimension"), 0, 2) == dimension and bounded_int(point.get("x"), -2_000_000, 2_000_000) == x and bounded_int(point.get("y"), 0, WORLD_HEIGHT - 1) == y and bounded_int(point.get("z"), -2_000_000, 2_000_000) == z


async def reset_respawns_for_broken_block(dimension: int, x: int, y: int, z: int) -> None:
    changed = False
    for player in world.players.values():
        if not respawn_point_matches(player.respawnPoint, dimension, x, y, z):
            continue
        player.respawnPoint = None; changed = True
        ws = world.connections.get(player.id)
        if ws is not None:
            await send_json(ws, {"type": "respawn_point_update", "respawnPoint": None, "originalSpawn": player.originalSpawn, "message": "Your bed was broken. Respawn reset to your original world spawn."})
    for profile in world.player_profiles.values():
        if respawn_point_matches(profile.get("respawnPoint"), dimension, x, y, z):
            profile["respawnPoint"] = None; changed = True
    if changed:
        world.dirty = True


def valid_respawn_block(point: Any) -> dict[str, int] | None:
    if not isinstance(point, dict):
        return None
    p = {"x": bounded_int(point.get("x"), -2_000_000, 2_000_000), "y": bounded_int(point.get("y"), 0, WORLD_HEIGHT - 1), "z": bounded_int(point.get("z"), -2_000_000, 2_000_000), "dimension": bounded_int(point.get("dimension"), 0, 2), "bedId": bounded_int(point.get("bedId"),0,255)}
    saved=world.blocks.get(world.block_key(p["dimension"], p["x"], p["y"], p["z"]))
    if saved in BED_BLOCK_IDS or (saved is None and bounded_int(point.get('bedId'),0,255) in BED_BLOCK_IDS):
        return p
    return None


def player_respawn_position(player: PlayerState) -> dict[str, float | int]:
    p = valid_respawn_block(player.respawnPoint)
    if p is not None:
        return {"x": p["x"] + 0.5, "y": p["y"] + 1.01, "z": p["z"] + 0.5, "dimension": p["dimension"]}
    player.respawnPoint = None
    o = player.originalSpawn
    if isinstance(o, dict):
        return {"x": finite_number(o.get("x"), player.x), "y": finite_number(o.get("y"), player.y), "z": finite_number(o.get("z"), player.z), "dimension": bounded_int(o.get("dimension"), 0, 2)}
    return {"x": player.x, "y": player.y, "z": player.z, "dimension": player.dimension}


async def spill_furnace_contents(dimension: int, x: int, y: int, z: int) -> None:
    """Remove a broken furnace's persistent inventory and spill each stack once.

    The dedicated server, not clients, owns the contents while online.
    """
    key = f"{dimension},{x},{y},{z}"
    state = world.furnaces.pop(key, None)
    if state is None:
        return
    world.dirty = True
    for id_field, count_field in (("ingredientId", "ingredientCount"), ("fuelId", "fuelCount"), ("outputId", "outputCount")):
        item_id = int(state.get(id_field, 0))
        amount = int(state.get(count_field, 0))
        if item_id > 0 and amount > 0:
            await spawn_dropped_item(item_id, amount, x + .5, y + .65, z + .5, dimension,
                                     random.uniform(-.7, .7), 1.8, random.uniform(-.7, .7))
    await broadcast({"type": "furnace_removed", "key": key}, minimum_protocol=6)


async def handle_block_change(player_id: str, data: dict[str, Any]) -> None:
    x = bounded_int(data.get("x"), -2_000_000, 2_000_000)
    y = bounded_int(data.get("y"), 0, WORLD_HEIGHT - 1)
    z = bounded_int(data.get("z"), -2_000_000, 2_000_000)
    dimension = bounded_int(data.get("dimension"), 0, 2)
    block_type = bounded_int(data.get("blockType"), 0, 255)
    key = world.block_key(dimension, x, y, z)
    previous_type = world.blocks.get(key, bounded_int(data.get("previousType"), 0, 255))

    # Dimensions now have different vertical layouts. Mirroring a portal at the
    # same Y coordinate placed the Alt Y=30 portal underground in the Overworld,
    # corrupting terrain and causing repeated teleport loops. Portal changes are
    # therefore stored only in the explicitly requested dimension.
    world.blocks[key] = block_type
    if block_type != FURNACE_BLOCK and (previous_type == FURNACE_BLOCK or f"{dimension},{x},{y},{z}" in world.furnaces):
        await spill_furnace_contents(dimension, x, y, z)
    if previous_type in BED_BLOCK_IDS and block_type != previous_type:
        await reset_respawns_for_broken_block(dimension, x, y, z)
    await broadcast({
        "type": "block_update", "playerId": player_id, "dimension": dimension,
        "x": x, "y": y, "z": z, "blockType": block_type,
    })
    world.dirty = True


async def handle_block_batch(player_id: str, data: dict[str, Any]) -> None:
    raw_changes = data.get("changes", [])
    if not isinstance(raw_changes, list):
        return
    sanitized: list[dict[str, int]] = []
    for entry in raw_changes[:256]:
        if not isinstance(entry, dict):
            continue
        x = bounded_int(entry.get("x"), -2_000_000, 2_000_000)
        y = bounded_int(entry.get("y"), 0, WORLD_HEIGHT - 1)
        z = bounded_int(entry.get("z"), -2_000_000, 2_000_000)
        dimension = bounded_int(entry.get("dimension"), 0, 2)
        block_type = bounded_int(entry.get("blockType"), 0, 255)
        key = world.block_key(dimension, x, y, z); previous_type = world.blocks.get(key, AIR_BLOCK)
        world.blocks[key] = block_type
        if block_type != FURNACE_BLOCK and (previous_type == FURNACE_BLOCK or f"{dimension},{x},{y},{z}" in world.furnaces):
            await spill_furnace_contents(dimension, x, y, z)
        if previous_type in BED_BLOCK_IDS and block_type != previous_type:
            await reset_respawns_for_broken_block(dimension, x, y, z)
        sanitized.append({"dimension": dimension, "x": x, "y": y, "z": z, "blockType": block_type})
    if not sanitized:
        return
    world.dirty = True
    await broadcast({"type": "block_batch_update", "playerId": player_id, "changes": sanitized}, exclude_id=player_id)


async def ban_player_state(player: PlayerState, reason: str = "Banned by an operator.") -> None:
    key = world.profile_key(player.username)
    world.banned_players.add(key)
    world.operators.discard(key)
    world.dirty = True
    websocket = world.connections.get(player.id)
    if websocket is not None:
        try:
            await send_json(websocket, {"type": "banned", "message": reason})
        except Exception:
            pass
        try:
            await websocket.close(code=4003, reason=reason[:120])
        except Exception:
            pass


async def ban_username(username: str, reason: str = "Banned by an operator.") -> str:
    cleaned = username.strip()
    if not cleaned:
        return "Usage: /ban <username>"
    if not USERNAME_PATTERN.fullmatch(cleaned):
        return "Invalid username."
    player = next((p for p in world.players.values() if p.username.casefold() == cleaned.casefold()), None)
    canonical = player.username if player is not None else cleaned
    key = world.profile_key(canonical)
    world.banned_players.add(key)
    world.operators.discard(key)
    world.dirty = True
    if player is not None:
        await ban_player_state(player, reason)
    return f"Banned {canonical}."


async def force_kill_player(username: str) -> str:
    cleaned = username.strip()
    if not cleaned:
        return "Usage: /kill <username>"
    player = next((p for p in world.players.values() if p.username.casefold() == cleaned.casefold()), None)
    if player is None:
        return f"Player not found: {cleaned}"
    if player.health <= 0:
        return f"{player.username} is already dead."
    player.health = 0.0
    if not bool(world.game_rules["keepInventory"]):
        player.inventory = [{"id": 0, "count": 0} for _ in range(MAX_INVENTORY_SLOTS)]
        player.selectedSlot = 0
        player.heldItem = 0
        player.armorId = 0
        websocket = world.connections.get(player.id)
        if websocket is not None:
            await send_json(websocket, {"type": "inventory_reset", "message": "Your inventory was cleared on death."})
    websocket = world.connections.get(player.id)
    if websocket is not None:
        await send_json(websocket, {
            "type": "player_hit", "health": 0.0, "attacker": "Killed by an operator",
            "knockback": {"x": 0.0, "z": 0.0, "vertical": 0.0, "duration": 0.1},
        })
    await broadcast({"type": "player_damaged", "playerId": player.id, "health": 0.0})
    world.dirty = True
    if str(world.game_rules.get("difficulty", "normal")) == "hardcore":
        await ban_player_state(player, "You died in Hardcore and are banned from this server.")
    return f"Killed {player.username}."


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
    applied_damage = armor_adjusted_damage(damage, victim.armorId)
    victim.health = max(0.0, victim.health - applied_damage)
    world.dirty = True
    world.damage_locks[victim.id] = now + 0.45
    if victim.health <= 0 and not bool(world.game_rules["keepInventory"]):
        victim.inventory = [{"id": 0, "count": 0} for _ in range(MAX_INVENTORY_SLOTS)]
        victim.selectedSlot = 0
        victim.heldItem = 0
        victim.armorId = 0
        websocket = world.connections.get(victim.id)
        if websocket is not None:
            await send_json(websocket, {"type": "inventory_reset", "message": "Your inventory was cleared on death."})
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
    if victim.health <= 0 and str(world.game_rules.get("difficulty", "normal")) == "hardcore":
        await ban_player_state(victim, "You died in Hardcore and are banned from this server.")


async def handle_player_attack(attacker_id: str, data: dict[str, Any]) -> None:
    if not bool(world.game_rules["pvp"]):
        return
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


async def spawn_dropped_item(item_id: int, count: int, x: float, y: float, z: float, dimension: int, vx: float = 0.0, vy: float = 0.0, vz: float = 0.0, floor_y: float | None = None) -> DroppedItemState:
    item = DroppedItemState(
        id=uuid.uuid4().hex, itemId=bounded_int(item_id, 1, 255, 1), count=bounded_int(count, 1, 100, 1),
        x=x, y=y, z=z, dimension=bounded_int(dimension, 0, 2), vx=vx, vy=vy, vz=vz,
        floorY=(finite_number(floor_y) if floor_y is not None else None),
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
    if player_kill:
        # Mob hosts report the support surface beneath each mob. Use it for loot so a laggy physics tick
        # cannot let a drop tunnel through the block it was standing on. The fallback is the mob's feet.
        loot_floor = mob.groundY if mob.groundY is not None else max(0.18, mob.y + 0.18)
        for item_id, minimum, maximum in MOB_LOOT.get(mob.typeKey, []):
            await spawn_dropped_item(item_id, random.randint(minimum, maximum), mob.x, mob.y + 0.4, mob.z, mob.dimension,
                                     random.uniform(-0.7, 0.7), 1.0, random.uniform(-0.7, 0.7), loot_floor)
    if mob.typeKey == "MELLOR_BOSS" and player_kill:
        world.boss_defeated = True
        await broadcast({"type": "system", "message": "The Mellor Boss was defeated!"})
        await broadcast({"type": "boss_defeated", "bossDefeated": True}, minimum_protocol=3)
    world.dirty = True


async def handle_mob_spawn(player_id: str, data: dict[str, Any]) -> None:
    if not bool(world.game_rules["doMobSpawning"]):
        return
    dimension = bounded_int(data.get("dimension"), 0, 2)
    if world.mob_hosts.get(dimension) != player_id:
        return
    if sum(1 for mob in world.mobs.values() if mob.dimension == dimension) >= int(world.game_rules["mobCap"]):
        return
    type_key = str(data.get("typeKey", ""))
    if type_key not in MOB_DEFINITIONS:
        return
    requested_id = str(data.get("id", ""))
    mob_id = requested_id if ENTITY_ID_PATTERN.fullmatch(requested_id) and requested_id not in world.mobs else uuid.uuid4().hex
    definition = MOB_DEFINITIONS[type_key]
    if str(world.game_rules.get("difficulty", "normal")) == "peaceful" and definition.get("hostile") and type_key != "MELLOR_BOSS":
        return
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


DYE_TO_SHEEP = {
    RED_DYE_ITEM: "SHEEP_RED",
    ORANGE_DYE_ITEM: "SHEEP_ORANGE",
    YELLOW_DYE_ITEM: "SHEEP_YELLOW",
    BLUE_DYE_ITEM: "SHEEP_BLUE",
    WHITE_DYE_ITEM: "SHEEP_WHITE",
    PINK_DYE_ITEM: "SHEEP_PINK",
    PURPLE_DYE_ITEM: "SHEEP_PURPLE",
    LIGHT_GRAY_DYE_ITEM: "SHEEP_LIGHT_GRAY",
    GRAY_DYE_ITEM: "SHEEP_GRAY",
    BLACK_DYE_ITEM: "SHEEP_BLACK",
    BROWN_DYE_ITEM: "SHEEP_BROWN",
}

async def handle_dye_sheep(player_id: str, data: dict[str, Any]) -> None:
    player = world.players.get(player_id)
    mob = world.mobs.get(str(data.get("mobId", "")))
    dye_id = bounded_int(data.get("dyeId"), 0, 255)
    target_type = DYE_TO_SHEEP.get(dye_id)
    if player is None or mob is None or target_type is None or not mob.typeKey.startswith("SHEEP_"):
        return
    if player.dimension != mob.dimension or math.hypot(player.x - mob.x, player.z - mob.z) > 5.0 or abs((player.y + 0.9) - (mob.y + 0.6)) > 3.5:
        return
    selected = player.inventory[player.selectedSlot] if 0 <= player.selectedSlot < len(player.inventory) else {"id": 0, "count": 0}
    if player.gamemode != "creative":
        if selected.get("id") != dye_id or selected.get("count", 0) <= 0:
            return
        selected["count"] -= 1
        if selected["count"] <= 0:
            selected["id"] = 0
            selected["count"] = 0
        player.heldItem = selected["id"] if selected["count"] > 0 else 0
    consumed = player.gamemode != "creative"
    mob.typeKey = target_type
    definition = MOB_DEFINITIONS[target_type]
    mob.maxHealth = float(definition["health"])
    mob.health = min(mob.health, mob.maxHealth)
    world.dirty = True
    await broadcast({"type": "mob_dyed", "mobId": mob.id, "typeKey": target_type, "playerId": player_id, "dyeId": dye_id, "consumed": consumed}, minimum_protocol=8)


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
        if entry.get("groundY") is not None:
            candidate_ground = finite_number(entry.get("groundY"), mob.groundY if mob.groundY is not None else mob.y + 0.18)
            if -0.5 <= candidate_ground <= mob.y + 1.5:
                mob.groundY = candidate_ground
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
    if not definition["hostile"] or victim.dimension != mob.dimension or difficulty_damage_scale() <= 0:
        return
    now = time.monotonic()
    if now < world.mob_attack_cooldowns.get(mob.id, 0.0):
        return
    dx, dy, dz = victim.x - mob.x, victim.y - mob.y, victim.z - mob.z
    # The large Mellorite boss attacks through its wider hitbox; the 2.2
    # normal-mob sphere previously rejected almost every legitimate hit.
    reach = 4.0 if mob.typeKey == "MELLOR_BOSS" else 2.2
    if math.hypot(dx, dz) > reach or abs(dy) > (4.5 if mob.typeKey == "MELLOR_BOSS" else 2.2):
        return
    world.mob_attack_cooldowns[mob.id] = now + 1.25
    await damage_player(victim, float(definition["damage"]) * difficulty_damage_scale(), definition.get("name", mob.typeKey.replace("_", " ").title()), dx, dz)


async def handle_mob_projectile(player_id: str, data: dict[str, Any]) -> None:
    projectile = data.get("projectile")
    if not isinstance(projectile, dict):
        return
    mob = world.mobs.get(str(projectile.get("mobId", "")))
    if mob is None or mob.typeKey != "SKELETON" or world.mob_hosts.get(mob.dimension) != player_id:
        return
    clean = {
        "id": str(projectile.get("id", uuid.uuid4().hex))[:64], "mobId": mob.id, "targetId": str(projectile.get("targetId", ""))[:64],
        "x": finite_number(projectile.get("x"), mob.x), "y": finite_number(projectile.get("y"), mob.y + 1.3), "z": finite_number(projectile.get("z"), mob.z),
        "vx": max(-30.0, min(30.0, finite_number(projectile.get("vx")))), "vy": max(-30.0, min(30.0, finite_number(projectile.get("vy")))),
        "vz": max(-30.0, min(30.0, finite_number(projectile.get("vz")))), "dimension": mob.dimension, "age": 0.0,
    }
    await broadcast({"type": "mob_projectile", "projectile": clean}, exclude_id=player_id, minimum_protocol=6)


async def handle_mob_projectile_hit(player_id: str, data: dict[str, Any]) -> None:
    mob = world.mobs.get(str(data.get("mobId", "")))
    victim = world.players.get(str(data.get("targetId", "")))
    if mob is None or victim is None or mob.typeKey != "SKELETON" or world.mob_hosts.get(mob.dimension) != player_id:
        return
    if victim.dimension != mob.dimension or difficulty_damage_scale() <= 0:
        return
    if math.dist((mob.x, mob.y, mob.z), (victim.x, victim.y, victim.z)) > 24.0:
        return
    now = time.monotonic()
    key = f"arrow:{mob.id}"
    if now < world.mob_attack_cooldowns.get(key, 0.0):
        return
    world.mob_attack_cooldowns[key] = now + 0.55
    definition = MOB_DEFINITIONS[mob.typeKey]
    await damage_player(victim, float(definition["damage"]) * difficulty_damage_scale(), "Skeleton", victim.x - mob.x, victim.z - mob.z, vertical=2.0)


async def handle_furnace_update(player_id: str, data: dict[str, Any]) -> None:
    if world.client_protocols.get(player_id, 1) < 6:
        return
    key = str(data.get("key", ""))[:96]
    if not re.fullmatch(r"[0-2],-?\d+,-?\d+,-?\d+", key):
        return
    # Never recreate a furnace state after its block was removed. The block may
    # be procedurally present when no explicit world edit exists yet.
    try:
        dimension, x, y, z = (int(v) for v in key.split(','))
    except ValueError:
        return
    if world.blocks.get(world.block_key(dimension, x, y, z)) == AIR_BLOCK:
        return
    world.furnaces[key] = sanitize_furnace_state(data.get("state"))
    world.dirty = True
    await broadcast({"type": "furnace_state", "key": key, "state": world.furnaces[key]}, exclude_id=player_id, minimum_protocol=6)


def tick_furnaces(elapsed: float) -> None:
    if elapsed <= 0:
        return
    changed = False
    for state in world.furnaces.values():
        ingredient_id = int(state.get("ingredientId", 0)); count = int(state.get("ingredientCount", 0)); result = FURNACE_RECIPES.get(ingredient_id)
        if not result or count <= 0:
            state["progress"] = 0.0
            continue
        if int(state.get("outputCount", 0)) > 0 and int(state.get("outputId", 0)) != result:
            state["progress"] = 0.0
            continue
        burn = float(state.get("burnTime", 0.0))
        fuel_id = int(state.get("fuelId", 0)); fuel_count = int(state.get("fuelCount", 0))
        if burn <= 0 and fuel_count > 0 and fuel_id in FURNACE_FUEL_SECONDS:
            burn = FURNACE_FUEL_SECONDS[fuel_id]; fuel_count -= 1
            state["fuelCount"] = fuel_count; state["fuelId"] = fuel_id if fuel_count > 0 else 0; changed = True
        if burn > 0:
            used = min(elapsed, burn); burn -= used; state["burnTime"] = burn; state["progress"] = float(state.get("progress", 0.0)) + used
            while state["progress"] >= 10.0 and int(state.get("ingredientCount", 0)) > 0:
                state["progress"] -= 10.0; state["ingredientCount"] -= 1; state["outputId"] = result; state["outputCount"] = min(100, int(state.get("outputCount", 0)) + 1); changed = True
                if state["ingredientCount"] <= 0: state["ingredientId"] = 0
    if changed:
        world.dirty = True


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


async def handle_block_drop(player_id: str, data: dict[str, Any]) -> None:
    player = world.players.get(player_id)
    if player is None or player.gamemode == "spectator" or player.health <= 0:
        return
    item_id = bounded_int(data.get("itemId"), 1, 255)
    count = bounded_int(data.get("count"), 1, 4, 1)
    x = finite_number(data.get("x"), player.x)
    y = finite_number(data.get("y"), player.y + 0.5)
    z = finite_number(data.get("z"), player.z)
    dimension = bounded_int(data.get("dimension"), 0, 2, player.dimension)
    floor_y = finite_number(data.get("floorY"), y - 0.4)
    if item_id <= 0 or item_id in RETIRED_ITEM_IDS or dimension != player.dimension:
        return
    if math.dist((x, y, z), (player.x, player.y + 0.8, player.z)) > 8.0:
        return
    floor_y = max(-0.5, min(y, floor_y))
    await spawn_dropped_item(
        item_id, count, x, y, z, dimension,
        random.uniform(-0.7, 0.7), 1.8, random.uniform(-0.7, 0.7), floor_y,
    )


async def handle_client_message(player_id: str, data: dict[str, Any]) -> None:
    message_type = data.get("type")
    player = world.players.get(player_id)
    if player is None:
        return

    if message_type == "player_update":
        world.client_last_updates[player_id] = time.monotonic()
        teleport_locked = time.monotonic() < world.teleport_locks.get(player.id, 0.0)
        if not teleport_locked:
            player.x = max(-2_000_000.0, min(2_000_000.0, finite_number(data.get("x"), player.x)))
            player.y = max(-100.0, min(1000.0, finite_number(data.get("y"), player.y)))
            player.z = max(-2_000_000.0, min(2_000_000.0, finite_number(data.get("z"), player.z)))
            player.dimension = bounded_int(data.get("dimension"), 0, 2, player.dimension)
        player.yaw = finite_number(data.get("yaw"), player.yaw)
        player.pitch = max(-math.pi / 2, min(math.pi / 2, finite_number(data.get("pitch"), player.pitch)))
        if time.monotonic() >= world.damage_locks.get(player.id, 0.0):
            player.health = max(0.0, min(10.0, finite_number(data.get("health"), player.health)))
        player.hunger = max(0.0, min(20.0, finite_number(data.get("hunger"), player.hunger)))
        player.heldItem = bounded_int(data.get("heldItem"), 0, 255)
        player.crouching = bool(data.get("crouching", False))
        player.renderDistance = bounded_int(data.get("renderDistance"), 2, 32, player.renderDistance)
        if world.client_protocols.get(player_id, 1) >= 4:
            inventory = world.sanitize_inventory(data.get("inventory"))
            if inventory is not None:
                player.inventory = inventory
            player.selectedSlot = bounded_int(data.get("selectedSlot"), 0, 8, player.selectedSlot)
            armor_id = bounded_int(data.get("armorId"), 0, 255)
            player.armorId = armor_id if armor_id in ARMOR_PROTECTION else 0
            selected = player.inventory[player.selectedSlot]
            player.heldItem = selected["id"] if selected["count"] > 0 else 0
        world.dirty = True
        if player.health <= 0 and str(world.game_rules.get("difficulty", "normal")) == "hardcore":
            await ban_player_state(player, "You died in Hardcore and are banned from this server.")
            return
        if world.recompute_mob_hosts():
            await broadcast_mob_hosts()
        return

    if message_type == "block_change":
        await handle_block_change(player_id, data)
    elif message_type == "block_batch":
        await handle_block_batch(player_id, data)
    elif message_type == "attack_player" and world.client_protocols.get(player_id, 1) >= 2:
        await handle_player_attack(player_id, data)
    elif message_type == "attack_mob" and world.client_protocols.get(player_id, 1) >= 3:
        await handle_mob_attack(player_id, data)
    elif message_type == "dye_sheep" and world.client_protocols.get(player_id, 1) >= 8:
        await handle_dye_sheep(player_id, data)
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
    elif message_type == "mob_projectile" and world.client_protocols.get(player_id, 1) >= 6:
        await handle_mob_projectile(player_id, data)
    elif message_type == "mob_projectile_hit" and world.client_protocols.get(player_id, 1) >= 6:
        await handle_mob_projectile_hit(player_id, data)
    elif message_type == "furnace_update" and world.client_protocols.get(player_id, 1) >= 6:
        await handle_furnace_update(player_id, data)
    elif message_type == "drop_item" and world.client_protocols.get(player_id, 1) >= 3:
        await handle_drop_item(player_id, data)
    elif message_type == "block_drop" and world.client_protocols.get(player_id, 1) >= 10:
        await handle_block_drop(player_id, data)
    elif message_type == "request_boss_spawn" and world.client_protocols.get(player_id, 1) >= 3:
        if not world.boss_defeated and player.dimension == 2 and not any(m.typeKey == "MELLOR_BOSS" and m.dimension == 2 for m in world.mobs.values()):
            definition = MOB_DEFINITIONS["MELLOR_BOSS"]
            mob = MobState(uuid.uuid4().hex, "MELLOR_BOSS", 0.0, 52.0, 10.0, 2, definition["health"], definition["health"])
            world.mobs[mob.id] = mob
            world.dirty = True
            await broadcast({"type": "mob_spawned", "mob": asdict(mob)}, minimum_protocol=3)
    elif message_type == "set_original_spawn":
        point = data.get("point")
        if isinstance(point, dict):
            player.originalSpawn = {"x": finite_number(point.get("x"), player.x), "y": finite_number(point.get("y"), player.y), "z": finite_number(point.get("z"), player.z), "dimension": bounded_int(point.get("dimension"), 0, 2)}
            world.dirty = True
    elif message_type == "set_respawn_point":
        requested=data.get('point')
        if isinstance(requested,dict):
            d=bounded_int(requested.get('dimension'),0,2)
            x=bounded_int(requested.get('x'),-2_000_000,2_000_000)
            y=bounded_int(requested.get('y'),0,WORLD_HEIGHT-1)
            z=bounded_int(requested.get('z'),-2_000_000,2_000_000)
            requestedId=bounded_int(requested.get('bedId'),0,255)
            key=world.block_key(d,x,y,z)
            existing=world.blocks.get(key)
            nearby=d==player.dimension and math.dist((player.x,player.y,player.z),(x+.5,y+.5,z+.5))<=7
            if nearby and existing is None and requestedId in BED_BLOCK_IDS:
                requested=dict(requested,bedId=requestedId)
            elif existing in BED_BLOCK_IDS:
                requested=dict(requested,bedId=existing)
            else: requested=None
        point = valid_respawn_block(requested) if requested is not None else None
        if point is None:
            await send_json(world.connections[player_id], {"type": "error", "message": "That bed is no longer present."})
        else:
            player.respawnPoint = point; world.dirty = True
            await send_json(world.connections[player_id], {"type": "respawn_point_update", "respawnPoint": point, "originalSpawn": player.originalSpawn})
    elif message_type == "server_command":
        command = str(data.get("command", "")).strip()
        if not player.isOperator:
            await send_json(world.connections[player_id], {"type": "error", "message": "Only server operators can run server-management commands."})
        else:
            result = await process_console_command(command)
            if result:
                await send_json(world.connections[player_id], {"type": "system", "message": result})
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
        position = player_respawn_position(player)
        player.x = float(position["x"]); player.y = float(position["y"]); player.z = float(position["z"]); player.dimension = int(position["dimension"])
        player.health = 10.0; world.damage_locks[player.id] = time.monotonic() + 2.0; world.dirty = True
        await send_json(world.connections[player_id], {"type": "respawn_position", "position": position})


async def websocket_handler(websocket: Any, *_args: Any) -> None:
    player_id: str | None = None
    try:
        console_log(f"WebSocket connection attempt from {getattr(websocket, 'remote_address', None)}")
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
        auth_action = str(join.get("authAction", "signin")).strip().lower()
        password = str(join.get("password", ""))
        requested_skin = str(join.get("skin", "steve"))
        if requested_skin not in ALLOWED_SKINS:
            requested_skin = "steve"
        if auth_action == "signup":
            account, auth_error = account_store.signup(requested_username, password, requested_skin)
        elif auth_action == "signin":
            account, auth_error = account_store.signin(requested_username, password)
        else:
            account, auth_error = None, "Invalid authentication action."
        password = ""
        if account is None:
            await send_json(websocket, {"type": "error", "message": auth_error or "Authentication failed."})
            return
        username = str(account["username"])
        skin = str(account.get("skin", "steve"))
        key = world.profile_key(username)
        if any(existing.username.casefold() == key for existing in world.players.values()):
            await send_json(websocket, {"type": "error", "message": "That account is already signed in to this server."})
            return
        if key in world.banned_players:
            message = "You are banned from this server."
            await send_json(websocket, {"type": "banned", "message": message})
            try:
                await websocket.close(code=4003, reason=message)
            except Exception:
                pass
            return

        player_id = uuid.uuid4().hex
        player, restored = world.restored_player(
            player_id, username, skin, key in world.operators
        )
        world.players[player_id] = player
        world.connections[player_id] = websocket
        world.client_protocols[player_id] = client_protocol
        world.client_device_classes[player_id] = "mobile" if str(join.get("deviceClass", "desktop")).lower() == "mobile" else "desktop"
        world.client_last_updates[player_id] = time.monotonic()
        world.tick()
        world.recompute_mob_hosts()

        total_blocks = len(world.blocks)
        await send_json(websocket, {
            "type": "welcome", "protocol": PROTOCOL_VERSION, "negotiatedProtocol": client_protocol,
            "clientId": player_id, "username": username, "skin": skin, "accountAuthenticated": True, "seed": world.seed, "worldName": world.world_name,
            "worldTime": world.world_time, "weatherSeed": world.weather_seed, "weatherPhase": world.weather_phase,
            "dayLength": world.game_rules["dayLength"], "gameRules": world.game_rules, "worldGen": world.world_gen,
            "bossDefeated": world.boss_defeated, "streamedWorld": True, "blockCount": total_blocks,
            "isOperator": player.isOperator, "blocks": [],
            "playerState": world.player_profile(player) if restored and client_protocol >= 4 else None,
            "players": world.player_snapshot(),
            "mobs": world.mob_snapshot() if client_protocol >= 3 else [],
            "items": world.item_snapshot() if client_protocol >= 3 else [],
            "furnaces": world.furnaces if client_protocol >= 6 else {},
            "mobHosts": {str(k): v for k, v in world.mob_hosts.items()} if client_protocol >= 3 else {},
        })
        # Stream edits directly from the world dictionary. This avoids constructing a second
        # giant block list in memory and prevents established worlds from stalling at join.
        batch_size = 1200
        batch: list[dict[str, int]] = []
        loaded = 0
        for key, block_type in world.blocks.items():
            try:
                d, x, y, z = world.parse_block_key(key)
            except (TypeError, ValueError):
                continue
            batch.append({"dimension": d, "x": x, "y": y, "z": z, "blockType": int(block_type)})
            if len(batch) >= batch_size:
                loaded += len(batch)
                await send_json(websocket, {"type": "world_block_batch", "blocks": batch, "loaded": loaded, "total": total_blocks})
                batch = []
                await asyncio.sleep(0)
        if batch:
            loaded += len(batch)
            await send_json(websocket, {"type": "world_block_batch", "blocks": batch, "loaded": loaded, "total": total_blocks})
        await send_json(websocket, {"type": "world_ready", "blockCount": loaded})
        await broadcast({"type": "player_joined", "player": world.public_player_state(player)}, exclude_id=player_id)
        await broadcast_mob_hosts()
        console_log(f"WebSocket joined: {username} ({player_id[:8]}) protocol={client_protocol}")

        async for raw_message in websocket:
            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError:
                await send_json(websocket, {"type": "error", "message": "Malformed JSON message."})
                continue
            if isinstance(data, dict):
                if data.get("type") == "client_ready":
                    console_log(f"Client ready: {player.username} ({player_id[:8]})")
                    continue
                if data.get("type") == "client_start_error":
                    detail = str(data.get("message", "Unknown browser startup error"))[:500]
                    console_log(f"Client startup failed: {player.username} ({player_id[:8]}): {detail}")
                    continue
                await handle_client_message(player_id, data)
    except asyncio.TimeoutError:
        try:
            await send_json(websocket, {"type": "error", "message": "Join timed out."})
        except Exception:
            pass
    except ConnectionClosed:
        pass
    except Exception as exc:
        console_log(f"WebSocket handler error: {exc}")
    finally:
        if player_id is not None:
            player = world.players.pop(player_id, None)
            if player is not None:
                world.remember_player(player)
            world.connections.pop(player_id, None)
            world.client_protocols.pop(player_id, None)
            world.client_device_classes.pop(player_id, None)
            world.client_last_updates.pop(player_id, None)
            world.damage_locks.pop(player_id, None)
            world.teleport_locks.pop(player_id, None)
            world.attack_cooldowns.pop(player_id, None)
            hosts_changed = world.recompute_mob_hosts()
            if player is not None:
                console_log(f"WebSocket left: {player.username} ({player_id[:8]})")
                await broadcast({"type": "player_left", "playerId": player_id})
            if hosts_changed:
                await broadcast_mob_hosts()


async def world_broadcast_loop() -> None:
    while True:
        await asyncio.sleep(0.1)
        elapsed = world.tick()
        tick_furnaces(elapsed)
        if str(world.game_rules.get("difficulty", "normal")) == "peaceful":
            for mob_id, mob in list(world.mobs.items()):
                if MOB_DEFINITIONS.get(mob.typeKey, {}).get("hostile") and mob.typeKey != "MELLOR_BOSS":
                    world.mobs.pop(mob_id, None); world.dirty = True
        # Despawn natural mobs immediately once they are more than seven chunks from every active player.
        now = time.monotonic()
        for mob_id, mob in list(world.mobs.items()):
            if mob.typeKey == "MELLOR_BOSS":
                world.mob_out_of_range_since.pop(mob_id, None)
                continue
            visible = False
            for player in world.players.values():
                if player.dimension != mob.dimension or player.health <= 0 or player.gamemode == "spectator":
                    continue
                radius = 7.0 * 16.0
                dx, dz = mob.x - player.x, mob.z - player.z
                if dx * dx + dz * dz <= radius * radius:
                    visible = True
                    break
            if visible:
                world.mob_out_of_range_since.pop(mob_id, None)
            else:
                world.mob_out_of_range_since.pop(mob_id, None)
                await remove_mob(mob_id, reason="despawn")
        hosts_changed = world.recompute_mob_hosts()
        await broadcast({
            "type": "world_state", "worldTime": world.world_time, "weatherSeed": world.weather_seed, "weatherPhase": world.weather_phase,
            "gameRules": world.game_rules,
            "bossDefeated": world.boss_defeated,
            "players": world.player_snapshot(),
            "mobs": world.mob_snapshot(), "items": world.item_snapshot(), "furnaces": world.furnaces,
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
            if item.floorY is not None:
                floor_y = float(item.floorY)
                old_y = item.y
                item.vy -= 18.0 * dt
                item.x += item.vx * dt
                next_y = item.y + item.vy * dt
                item.z += item.vz * dt
                item.vx *= max(0.0, 1.0 - dt * 3.5)
                item.vz *= max(0.0, 1.0 - dt * 3.5)
                # Swept floor collision prevents a low-FPS / delayed server tick from tunneling through support.
                if (old_y >= floor_y and next_y <= floor_y) or next_y < floor_y:
                    item.y = floor_y
                    item.vy = 0.0
                    item.vx *= max(0.0, 1.0 - dt * 8.0)
                    item.vz *= max(0.0, 1.0 - dt * 8.0)
                else:
                    item.y = next_y
            else:
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
                    if not inventory_can_fit(player.inventory, item.itemId, item.count):
                        continue
                    if not inventory_add(player.inventory, item.itemId, item.count):
                        continue
                    selected = player.inventory[player.selectedSlot]
                    player.heldItem = selected["id"] if selected["count"] > 0 else 0
                    websocket = world.connections.get(player.id)
                    if websocket is not None:
                        await send_json(websocket, {"type": "give_item", "itemId": item.itemId, "count": item.count})
                    removed.append(item.id)
                    world.dirty = True
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
                console_log(f"Could not save world: {exc}")


def start_http_server() -> QuietThreadingHTTPServer:
    server = QuietThreadingHTTPServer(("0.0.0.0", HTTP_PORT), ClientRequestHandler)
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


DIMENSION_COMMAND_NAMES = {0: "Overworld", 1: "Timeless Void", 2: "Boss Dimension"}


async def set_player_gamemode(username: str, mode: str) -> str:
    player = find_player_by_username(username)
    if player is None:
        return f"Player not found: {username}"
    normalized = mode.strip().lower()
    if normalized not in {"survival", "creative", "spectator"}:
        return "Usage: /gamemode <player> <survival|creative|spectator>"
    player.gamemode = normalized
    if normalized != "survival":
        player.health = 10.0
    world.dirty = True
    websocket = world.connections.get(player.id)
    if websocket is not None:
        await send_json(websocket, {"type": "gamemode_update", "gamemode": normalized})
    return f"Set {player.username}'s gamemode to {normalized}."


async def teleport_player_to_position(player: PlayerState, x: float, y: float, z: float, dimension: int, description: str) -> str:
    player.x = max(-2_000_000.0, min(2_000_000.0, x))
    player.y = max(-100.0, min(1000.0, y))
    player.z = max(-2_000_000.0, min(2_000_000.0, z))
    player.dimension = max(0, min(2, int(dimension)))
    world.teleport_locks[player.id] = time.monotonic() + 1.5
    # Remote terrain can require multiple server/client chunk batches to stream.
    world.damage_locks[player.id] = max(world.damage_locks.get(player.id, 0.0), time.monotonic() + 4.0)
    world.dirty = True
    websocket = world.connections.get(player.id)
    message = f"Teleported to {description}."
    if websocket is not None:
        await send_json(websocket, {
            "type": "teleport_position",
            "position": {"x": player.x, "y": player.y, "z": player.z, "dimension": player.dimension},
            "message": message,
        })
    if world.recompute_mob_hosts():
        await broadcast_mob_hosts()
    return message


async def process_teleport_command(args: list[str]) -> str:
    if len(args) == 2:
        source = find_player_by_username(args[0])
        destination = find_player_by_username(args[1])
        if source is None:
            return f"Player not found: {args[0]}"
        if destination is None:
            return f"Player not found: {args[1]}"
        dim_name = DIMENSION_COMMAND_NAMES.get(destination.dimension, f"dimension {destination.dimension + 1}")
        result = await teleport_player_to_position(
            source, destination.x, destination.y, destination.z, destination.dimension,
            f"{destination.username} in {dim_name}",
        )
        await broadcast({"type": "system", "message": f"{source.username} was teleported to {destination.username} ({dim_name})."})
        return result

    if len(args) == 5:
        source = find_player_by_username(args[0])
        if source is None:
            return f"Player not found: {args[0]}"
        try:
            x, y, z = (float(args[i]) for i in (1, 2, 3))
            command_dimension = int(args[4])
        except (TypeError, ValueError):
            return "Usage: /tp <player> <x> <y> <z> <dimension 1|2|3>"
        if not all(math.isfinite(v) for v in (x, y, z)) or command_dimension not in {1, 2, 3}:
            return "Usage: /tp <player> <x> <y> <z> <dimension 1|2|3>"
        internal_dimension = command_dimension - 1
        dim_name = DIMENSION_COMMAND_NAMES[internal_dimension]
        actual_y = y + 48 if internal_dimension == 0 else y
        result = await teleport_player_to_position(source, x, actual_y, z, internal_dimension, f"{x:g}, {y:g}, {z:g} in {dim_name}")
        await broadcast({"type": "system", "message": f"{source.username} was teleported to {x:g}, {y:g}, {z:g} ({dim_name})."})
        return result

    return "Usage: /tp <player> <targetPlayer> OR /tp <player> <x> <y> <z> <dimension 1|2|3>"


def game_rule_text(name: str) -> str:
    value = world.game_rules[name]
    return str(value).lower() if isinstance(value, bool) else str(value)


async def process_gamerule_command(args: list[str]) -> str:
    if not args:
        return ", ".join(f"{name}={game_rule_text(name)}" for name in GAME_RULE_ORDER)
    alias = re.sub(r"[_\s-]", "", args[0]).lower()
    name = GAME_RULE_ALIASES.get(alias)
    if name is None:
        return "Unknown game rule. Available: " + ", ".join(GAME_RULE_ORDER)
    if len(args) == 1:
        return f"{name} = {game_rule_text(name)}"
    raw_value = args[1].lower()
    if name in BOOLEAN_GAME_RULES:
        if raw_value in {"true", "on", "1", "yes"}:
            value: bool | int | str = True
        elif raw_value in {"false", "off", "0", "no"}:
            value = False
        else:
            return f"Usage: /gamerule {name} <true|false>"
    elif name == "difficulty":
        if raw_value not in DIFFICULTY_DAMAGE_SCALE:
            return "Usage: /gamerule difficulty <peaceful|easy|normal|hard|hardcore>"
        value = raw_value
    else:
        minimum, maximum = (0, 200) if name == "mobCap" else (60, 3600)
        try:
            value = int(args[1])
        except ValueError:
            return f"Usage: /gamerule {name} <{minimum}-{maximum}>"
        if value < minimum or value > maximum:
            return f"Usage: /gamerule {name} <{minimum}-{maximum}>"
    world.game_rules[name] = value
    world.dirty = True
    await broadcast({"type": "game_rules", "gameRules": dict(world.game_rules)})
    return f"Set {name} to {game_rule_text(name)}."


COMMAND_HELP: tuple[tuple[str, str], ...] = (
    ("/help", "Show every server-console command."),
    ("/stop", "Save the world and shut down the server cleanly."),
    ("/list", "List connected players and operator status."),
    ("/ops", "List operator usernames."),
    ("/op <username>", "Grant operator status."),
    ("/deop <username>", "Remove operator status."),
    ("/ban <username>", "Ban a username from the current world/server."),
    ("/kill <username>", "Kill a connected player using normal death rules."),
    ("/mobs", "Show mob counts by dimension."),
    ("/gamerule", "List all game rules and current values."),
    ("/gamerule <rule> [value]", "Read or change a game rule."),
    ("/gamemode <player> <survival|creative|spectator>", "Change a connected player's gamemode."),
    ("/tp <player> <targetPlayer>", "Teleport one connected player to another."),
    ("/tp <player> <x> <y> <z> <dimension 1|2|3>", "Teleport a player to coordinates."),
    ("/account list", "List registered server accounts and public-signup status."),
    ("/account create <username> <password> <skin>", "Create a server account. Skins: steve, alex, mellorite, ember, frost, forest."),
    ("/account signup <on|off>", "Allow or lock public account creation."),
    ("/account setpassword <username> <password>", "Reset an account password."),
    ("/account delete <username>", "Delete a server account login. World player data is not deleted."),
)

COMMAND_USAGE = {
    "/ban": "Usage: /ban <username>",
    "/kill": "Usage: /kill <username>",
    "/op": "Usage: /op <username>",
    "/deop": "Usage: /deop <username>",
    "/gamemode": "Usage: /gamemode <player> <survival|creative|spectator>",
    "/gm": "Usage: /gamemode <player> <survival|creative|spectator>",
    "/tp": "Usage: /tp <player> <targetPlayer> OR /tp <player> <x> <y> <z> <dimension 1|2|3>",
    "/account": "Usage: /account <list|create|signup|setpassword|delete> ...",
}


def all_command_help() -> str:
    return "Console commands:\n" + "\n".join(f"  {usage:<58} {description}" for usage, description in COMMAND_HELP)


async def process_account_command(args: list[str]) -> str:
    if not args:
        return COMMAND_USAGE["/account"]
    sub = args[0].lower()
    if sub == "list":
        if len(args) != 1:
            return "Usage: /account list"
        status = "enabled" if account_store.public_signup_enabled else "locked"
        return account_store.list_text() + f"\nPublic account creation: {status}"
    if sub == "create":
        if len(args) != 4:
            return "Usage: /account create <username> <password> <skin>"
        return account_store.create_account(args[1], args[2], args[3].lower())
    if sub == "signup":
        if len(args) != 2 or args[1].lower() not in {"on", "off", "true", "false", "enable", "disable", "enabled", "disabled", "1", "0"}:
            return "Usage: /account signup <on|off>"
        enabled = args[1].lower() in {"on", "true", "enable", "enabled", "1"}
        return account_store.set_public_signup(enabled)
    if sub == "setpassword":
        if len(args) != 3:
            return "Usage: /account setpassword <username> <password>"
        return account_store.set_password(args[1], args[2])
    if sub == "delete":
        if len(args) != 2:
            return "Usage: /account delete <username>"
        if find_player_by_username(args[1]) is not None:
            return "That account is currently signed in. Disconnect the player before deleting it."
        return account_store.delete(args[1])
    return COMMAND_USAGE["/account"]


async def process_console_command(line: str) -> str:
    command = line.strip()
    if not command:
        return ""
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return f"Invalid command syntax: {exc}"
    if not tokens:
        return ""
    name = tokens[0].lower()
    args = tokens[1:]
    argument = " ".join(args)
    if not args and name in COMMAND_USAGE:
        return COMMAND_USAGE[name]
    if name == "/ban":
        return await ban_username(argument)
    if name == "/kill":
        return await force_kill_player(argument)
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
        return f"Mobs: overworld={counts[0]}, timeless_void={counts[1]}, boss={counts[2]}"
    if name == "/gamerule":
        return await process_gamerule_command(args)
    if name in {"/gamemode", "/gm"}:
        if len(args) != 2:
            return COMMAND_USAGE[name]
        return await set_player_gamemode(args[0], args[1])
    if name == "/tp":
        return await process_teleport_command(args)
    if name == "/account":
        return await process_account_command(args)
    if name in {"/help", "help"}:
        return all_command_help()
    if name == "/stop":
        try:
            world.save()
        except OSError as exc:
            return f"Could not save before stopping: {exc}"
        # Tell connected clients to leave gameplay before the HTTP/WebSocket services vanish.
        # This lets a server-hosted browser stay on its already-loaded login page instead of
        # trying to reload a URL that is about to become unavailable.
        try:
            await broadcast({"type": "server_shutdown", "message": "Server stopped by the operator. Your world state was saved."})
        except Exception:
            pass
        if _server_stop_event is not None:
            _server_stop_event.set()
        return "World saved. Stopping server..."
    return "Unknown console command. Type /help."


async def run_websocket_server() -> None:
    global _console_ui, _server_stop_event
    loop = asyncio.get_running_loop()
    _server_stop_event = asyncio.Event()
    _console_ui = LiveServerConsole(loop)
    threading.Thread(target=_console_ui.run, name="MellorCraftConsole", daemon=True).start()
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
            await _server_stop_event.wait()
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


def safe_world_filename(world_name: str) -> str:
    cleaned = world_name.strip()[:48]
    if not cleaned or not WORLD_NAME_PATTERN.fullmatch(cleaned):
        raise ValueError("World names may use letters, numbers, spaces, dots, dashes, and underscores.")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned).strip("._") or DEFAULT_WORLD_NAME
    return slug + ".json"


def available_worlds(worlds_dir: Path) -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    if not worlds_dir.exists():
        return result
    for path in sorted(worlds_dir.glob("*.json"), key=lambda item: item.name.casefold()):
        display_name = path.stem.replace("_", " ")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            display_name = str(raw.get("name", raw.get("worldName", display_name))).strip() or display_name
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
        result.append((display_name, path))
    return result


def choose_world_interactively(worlds_dir: Path) -> tuple[str, Path, int | None, bool]:
    worlds = available_worlds(worlds_dir)
    print("\nMellorCraft v1.8.1 World Selection")
    if worlds:
        print("Existing worlds:")
        for index, (name, path) in enumerate(worlds, 1):
            print(f"  {index}. {name}  ({path.name})")
    else:
        print("No named worlds exist yet.")
    print("  C. Create a new world")

    while True:
        choice = input("Load a world number or create [C]: ").strip()
        if worlds and choice.isdigit() and 1 <= int(choice) <= len(worlds):
            name, path = worlds[int(choice) - 1]
            open_game = input("Open the local game page after startup? [Y/n]: ").strip().lower() not in {"n", "no"}
            return name, path, None, open_game
        if choice.lower() in {"c", "create", "new"} or (not worlds and choice == ""):
            while True:
                name = input(f"World name [{DEFAULT_WORLD_NAME}]: ").strip() or DEFAULT_WORLD_NAME
                try:
                    path = worlds_dir / safe_world_filename(name)
                except ValueError as exc:
                    print(exc)
                    continue
                if path.exists():
                    print("A world with that file name already exists. Choose another name.")
                    continue
                break
            seed_text = input("Seed (blank for random): ").strip()
            try:
                seed = None if not seed_text else abs(int(seed_text)) % 2_147_483_647
            except ValueError:
                print("Invalid seed; a random seed will be used.")
                seed = None
            open_game = input("Open the local game page after startup? [Y/n]: ").strip().lower() not in {"n", "no"}
            return name, path, seed, open_game
        print("Enter an existing world number or C.")


def resolve_world(args: argparse.Namespace) -> tuple[str, Path, int | None, bool]:
    worlds_dir = SCRIPT_DIR / WORLDS_DIRNAME
    worlds_dir.mkdir(parents=True, exist_ok=True)

    legacy_path = SCRIPT_DIR / LEGACY_SAVE_FILENAME
    if legacy_path.exists() and not available_worlds(worlds_dir):
        migrated = worlds_dir / "Legacy_World.json"
        legacy_path.replace(migrated)
        print(f"Migrated {LEGACY_SAVE_FILENAME} to {migrated.relative_to(SCRIPT_DIR)}")

    if args.list_worlds:
        worlds = available_worlds(worlds_dir)
        if not worlds:
            print("No saved worlds.")
        for name, path in worlds:
            print(f"{name}: {path}")
        raise SystemExit(0)

    if args.create_world:
        name = args.create_world.strip()
        path = worlds_dir / safe_world_filename(name)
        if path.exists() and not args.reset_world:
            raise SystemExit(f"World already exists: {path.name}. Use --world to load it or --reset-world to replace it.")
        if args.reset_world and path.exists():
            path.unlink()
        seed = None if args.seed is None else abs(args.seed) % 2_147_483_647
        return name, path, seed, bool(args.open_browser)

    if args.world:
        requested = args.world.strip()
        matches = [(name, path) for name, path in available_worlds(worlds_dir) if name.casefold() == requested.casefold() or path.stem.casefold() == requested.casefold()]
        if matches:
            name, path = matches[0]
        else:
            name = requested
            path = worlds_dir / safe_world_filename(name)
        if args.reset_world and path.exists():
            path.unlink()
        seed = None if path.exists() or args.seed is None else abs(args.seed) % 2_147_483_647
        return name, path, seed, bool(args.open_browser)

    if not args.no_menu and os.isatty(0):
        return choose_world_interactively(worlds_dir)

    name = DEFAULT_WORLD_NAME
    path = worlds_dir / safe_world_filename(name)
    if args.reset_world and path.exists():
        path.unlink()
    seed = None if path.exists() or args.seed is None else abs(args.seed) % 2_147_483_647
    return name, path, seed, bool(args.open_browser)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Host a MellorCraft v1.8.1 multiplayer world.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--world", help="Load a named world, creating it if it does not exist.")
    group.add_argument("--create-world", metavar="NAME", help="Create a new named world.")
    parser.add_argument("--seed", type=int, help="Seed used only when creating a new world.")
    parser.add_argument("--reset-world", action="store_true", help="Delete the selected world's JSON before starting.")
    parser.add_argument("--list-worlds", action="store_true", help="List named world saves and exit.")
    parser.add_argument("--open-browser", action="store_true", help="Open the local game page after startup.")
    parser.add_argument("--no-menu", action="store_true", help="Skip the interactive world selection menu.")
    parser.add_argument("--http-log", action="store_true", help="Show verbose HTTP request/error logs (normally suppressed to hide Internet scanner noise).")
    parser.add_argument("--lock-account-creation", action="store_true", help="Disable public Sign Up; accounts must be created from the server console.")
    return parser.parse_args()


def main() -> None:
    global world, account_store, HTTP_VERBOSE_LOGGING
    args = parse_args()
    HTTP_VERBOSE_LOGGING = bool(args.http_log)
    client_path = SCRIPT_DIR / CLIENT_FILENAME
    if not client_path.exists():
        raise SystemExit(f"Missing client file: {client_path}")

    world_name, save_path, seed, open_game = resolve_world(args)
    world = MellorCraftWorld(save_path, requested_seed=seed, world_name=world_name)
    account_store = ServerAccountStore(SCRIPT_DIR / ACCOUNTS_FILENAME, SCRIPT_DIR / WORLDS_DIRNAME)
    if args.lock_account_creation and account_store.public_signup_enabled:
        account_store.set_public_signup(False)
    http_server = start_http_server()
    ip = local_ip_address()

    print("\nMellorCraft v1.8.1 multiplayer server is running")
    print(f"  World:         {world.world_name}")
    print(f"  Host PC:       http://127.0.0.1:{HTTP_PORT}")
    print(f"  Other devices: http://{ip}:{HTTP_PORT}")
    print(f"  WebSocket:     ws://{ip}:{WEBSOCKET_PORT}")
    print(f"  Protocol:      {PROTOCOL_VERSION} (accepts {', '.join(map(str, SUPPORTED_PROTOCOLS))})")
    print(f"  World seed:    {world.seed}")
    print(f"  Save file:     {save_path.relative_to(SCRIPT_DIR)}")
    print("Join this same world on the host PC using the Host PC address above.")
    print("Console: type /help to list all commands. Incoming logs will preserve what you are typing.")
    print(f"  HTTP logging:  {'verbose' if HTTP_VERBOSE_LOGGING else 'quiet (use --http-log for request logs)'}")
    print(f"  Accounts:      {(SCRIPT_DIR / ACCOUNTS_FILENAME).relative_to(SCRIPT_DIR)}")
    print(f"  Public signup: {'enabled' if account_store.public_signup_enabled else 'LOCKED (console-created accounts only)'}")
    print("Type /stop to save and shut down cleanly, or press Ctrl+C.\n")
    if open_game:
        try:
            webbrowser.open(f"http://127.0.0.1:{HTTP_PORT}")
        except Exception as exc:
            print(f"Could not open the browser automatically: {exc}")
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
