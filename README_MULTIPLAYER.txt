MellorCraft Multiplayer v1.3.2
==============================

Files
-----
mellorcraft_multiplayer.html  Multiplayer HTML client
mellorcraft_server.py         HTTP + WebSocket host
requirements.txt              Python dependency
mellorcraft_world.json        Created automatically after the server runs

Host setup
----------
1. Keep mellorcraft_multiplayer.html and mellorcraft_server.py in this folder.
2. Install Python 3.10 or newer, then open Command Prompt / Terminal here.
3. Install the WebSocket dependency once:

   python -m pip install -r requirements.txt

4. Start the host:

   python mellorcraft_server.py

5. Open the address printed by the server. On the host PC this is normally:

   http://127.0.0.1:8000

   Other computers and phones on the same network should open the LAN address
   printed by the server, such as http://192.168.1.50:8000.

Important update note
---------------------
Player-profile saving uses multiplayer protocol 4. Replace BOTH the HTML client
and Python server. The server terminal should print:

   Protocol:      4 (accepts 4, 3, 2)

Protocol 3 clients can still use shared mobs and dropped items, but only a
protocol 4 client receives its saved position, view angle, dimension, selected
hotbar slot, and complete inventory when it rejoins.

World options
-------------
Create a new world with a chosen seed (only used when no save exists):

   python mellorcraft_server.py --seed 12345

Delete the saved world, including saved player profiles, and start over:

   python mellorcraft_server.py --reset-world --seed 12345

Changes in v1.3.2
-----------------
- Mobile has a Drop Selected Item button (the box-with-arrow icon), positioned
  directly above the Mine button. It performs the same action as pressing Q.
- Mobile chat is positioned below and visually separated from the upper-left
  information panel so the messages no longer overlap the HUD.
- Opening the Escape/Settings menu no longer freezes the local player in midair.
  Survival gravity, collision, knockback, and multiplayer position updates keep
  running while movement controls remain disabled behind the menu.
- The server remembers each player by username after disconnecting.
- Rejoining restores position, yaw, pitch, dimension, inventory, and selected
  hotbar slot. Health and authorized gamemode state are also retained.
- Connected and disconnected player profiles are written under
  "playerProfiles" in mellorcraft_world.json during autosaves and the final
  save when the server is stopped with Ctrl+C.

Desktop controls
----------------
Q     Drop one item from the selected hotbar slot
G     Eat raw meat
T     Open chat

Dropped items are shared through the server and may be picked up by any nearby
survival or creative player after the short pickup delay.

Mobile mode
-----------
The client automatically detects Android, iPhone, iPad, iPod, Kindle/Silk, and
other mobile browser user agents. Mobile devices receive:

- Left-side floating joystick for movement
- Right-side swipe area for looking
- Jump, mine, place, fly-down, and item-drop buttons
- Settings, chat, eat, inventory, crafting, and creative buttons
- Mobile-sized hotbar, health, menus, chat, and sensitivity setting

Desktop browsers retain the normal mouse-and-keyboard interface.

Shared mechanics
----------------
- Server-owned world seed and day/night clock
- Persistent placed and broken blocks in every dimension
- Portal blocks mirrored between dimensions 0 and 1, never dimension 2
- Shared player positions, rotations, dimensions, usernames, skins, and health
- Persistent player position, angle, dimension, selected slot, and inventory
- Shared mobs, mob movement, health, attacks, deaths, and meat drops
- Shared dropped item entities and pickup
- PvP damage and knockback
- Multiplayer chat
- Nametags visible only within 32 blocks (two chunks)
- Locator bar for players in the same dimension
- Server operators and protected gamemode switching

Server console
--------------
/op <username>       Give operator permission
/deop <username>     Remove operator permission
/ops                 List operators
/list                List connected players
/mobs                Show mob totals by dimension
/help                Show server commands

Network / firewall
------------------
Allow Python through the host firewall on private networks. TCP ports 8000 and
8765 must be reachable by clients. This server is intended for a trusted LAN; it
does not provide accounts, TLS encryption, moderation, or Internet hardening.
