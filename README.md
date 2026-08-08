MellorCraft v1.4.1
=========================================================


Mobile menu scrolling hotfix
----------------------------
- Mobile singleplayer no longer applies `touch-action: none` to the entire page.
- The start screen is now a native vertical scroll container on small displays, so Delete World and LAN Join controls remain reachable.
- Game Settings now uses native touch panning and momentum scrolling, allowing the Open to LAN controls at the bottom to be reached on phones.
- Gameplay canvas/joystick surfaces still suppress browser panning while the game itself is active.

Files
-----
mellorcraft_multiplayer.html   Multiplayer HTML client
mellorcraft_singleplayer.html  Browser-only singleplayer edition
mellorcraft_seed_map.html      Interactive seed and structure map
mellorcraft_server.py          HTTP + WebSocket multiplayer host
mellorcraft_relay.py           Singleplayer LAN relay (WebSocket, default port 8000)
requirements.txt               Python dependency
worlds/                        One JSON save per named multiplayer world


v1.4.1 respawn / shared-save / disconnect update
-----------------------------------------------
- Added the **Respawn Block**, a placeable block crafted from 5 Gold Ingots. Right-click/tap Place while targeting it to set your personal respawn point one block above it.
- Activating a Respawn Block clears the two blocks directly above it so the player cannot respawn inside terrain.
- Death and defeating the Mellorite Entity now return each player to their active Respawn Block. If that block is broken, the player's respawn is reset to that player's original deterministic world-spawn coordinates.
- Respawn points and original spawn coordinates are persisted per player in singleplayer, relay-hosted LAN worlds, and Python-server worlds.
- Relay world hosts can use the server-management commands `/op`, `/deop`, `/ops`, `/list`, and `/mobs` from in-game chat. Operator state is saved with the world.
- Browser-hosted worlds and Python-server worlds now write the same canonical `MellorCraftWorld` JSON schema (`formatVersion` 7): name, seed, time, boss state, block edits, operators, player profiles, mobs, dropped items, and timestamps. Both loaders retain compatibility with the older browser and server save layouts.
- A browser-exported world JSON can therefore be imported into singleplayer or placed in the Python server's `worlds` folder; Python-server JSON can likewise be imported into singleplayer.
- LAN guests are forced back to the world-selection screen when the world host or relay disappears. Multiplayer clients similarly return to the join screen when the Python server goes offline, preventing disconnected clients from continuing an unsaved phantom session.
- The relay now uses WebSocket keepalive timeouts so dead host connections are detected and closed more promptly.

v1.4.1 update
-------------
- Browser singleplayer worlds now have a red Delete World button with an irreversible confirmation prompt.
- Singleplayer gameplay now routes shared actions through an in-page authoritative integrated server. Mob melee damage, weapon damage, attack cooldowns, mob/player knockback, dropped items, mob hosting, PvP validation, and shared state use the same protocol behavior as multiplayer.
- A singleplayer world can be opened to LAN from Game Settings through `mellorcraft_relay.py`. The browser owning the save remains authoritative; the relay only discovers rooms and forwards protocol messages.
- Another singleplayer client can press Join World, enter the relay address, discover open worlds, and join one. The default relay address in the UI is `192.168.0.1:8000`.
- Mountain ranges keep their existing seeded outlines and heights, but their X/Z footprint is affine-scaled by `sqrt(1/2)`. This halves mountain land area and makes the same vertical ranges noticeably steeper. The seed map uses the identical rule.

Singleplayer LAN relay
----------------------
1. On a PC reachable by the players, install the existing dependency with `python -m pip install -r requirements.txt`.
2. Start `python mellorcraft_relay.py`. It listens on WebSocket port 8000 by default.
3. In the world-owning singleplayer client, open Game Settings, scroll to **Open Singleplayer World to LAN**, enter the relay IP/port, and choose **Open World to LAN**.
4. On another singleplayer client, choose **Join World**, enter the same relay IP/port, choose **Find Worlds on Relay**, select the world, and join it.

The relay is intended for a trusted local network and has no accounts, TLS, or Internet hardening. If the singleplayer page is loaded from an HTTPS site, the browser may block an insecure `ws://` LAN relay as mixed content; use the local HTML file or serve the page over HTTP on the LAN.

Mobile login hotfix
-------------------
- Fixed an iPhone Safari regression that prevented the username, server-address,
  and other start-screen fields from receiving focus.
- Document-wide touch-end cleanup now runs only while the game is active and only
  for touches owned by the movement/look controls.
- Start-screen inputs and selectors explicitly retain normal tap, selection, and
  text-entry behavior on mobile.
- The background terrain worker, smooth mobile chunk queue, portal safeguards,
  corrected mob facing, and Low Mountain border smoothing are unchanged.

Multiplayer setup
-----------------
1. Install Python 3.10 or newer.
2. Open Command Prompt or Terminal in this folder.
3. Install the dependency once:

   python -m pip install -r requirements.txt

4. Start the server:

   python mellorcraft_server.py

The interactive server menu can create a named world with a seed or load an
existing JSON world from the worlds folder. The host can join through the local
address printed by the server; other devices use the printed LAN address.

Useful server options
---------------------
Create a named world:

   python mellorcraft_server.py --create-world "My World" --seed 12345

Load a named world:

   python mellorcraft_server.py --world "My World"

List worlds:

   python mellorcraft_server.py --list-worlds

Reset one world:

   python mellorcraft_server.py --world "My World" --reset-world --seed 12345

Current world-generation rules
------------------------------
- The Overworld remains 200 blocks tall.
- Ocean, Beach, and Swamp biomes have been removed from new generation.
- Natural water and lava generation has been removed. Legacy liquid block edits
  are treated as air, and buckets are no longer available through normal
  crafting or the Creative inventory.
- Plains, Forest, Taiga, Stony Peaks, Jungle, Savanna, deserts, Badlands, and all
  three Mountain biomes remain available.
- Mountain-region occurrence remains at the v1.4.0 frequency. In v1.4.1 each seeded range keeps its shape and height bands while its horizontal footprint is compressed to 50% of its former land area, producing steeper slopes.
- Taiga and Stony Peaks remain centered near Y=80.
- Normal caves and varied ravines remain. Rare mega-caves are approximately
  92–168 blocks across and 30–56 blocks tall, with overlapping irregular lobes.
- Dungeons remain in the actual game but are intentionally hidden from the seed
  map.
- Mineshafts remain safely underground.
- Forest and Taiga trees remain common. Jungle and Savanna retain their distinct
  styles. Plains retain the sparse one-tree-per-plains-3x3-chunk-region target.

Spawn changes
-------------
New-player spawn no longer searches outward from coordinate 0,0. The seed first
selects one of the remaining biomes, then searches deterministic positions over
a wide area for a safe location in that biome. Across validation seeds, spawn
locations occurred in every remaining biome, including Low, regular, and High
Mountains.

Alt Dimension
-------------
- The Alt Dimension is exactly 50 blocks tall: Y=0 through Y=49.
- Y=0 and Y=49 are bedrock boundaries.
- Block placement, collision, chunk meshing, teleport searches, and mob placement
  all use the 50-block dimension limit.
- Alt Mazes occupy base Y through base Y+15 and are constrained to Y=4–38.
- Boss Shrines occupy base Y-5 through base Y+4 and are constrained to Y=2–44.
- Structures therefore cannot be cut off by the floor or ceiling.

Singleplayer edition
--------------------
Open mellorcraft_singleplayer.html in a modern browser. It uses the complete game
engine without the Python server. Named worlds autosave to browser storage and
include the seed, block edits, time, player state, inventory, mobs, and dropped
items.

You can also open the singleplayer edition online by opening linkers15.github.io/mellorcraft

Export World downloads the selected save as JSON. Import JSON World restores a
save or transfers it to another browser. Browser storage is tied to the page
origin, so direct-file and web-served copies may have separate save collections.

Seed map generator
------------------
Open mellorcraft_seed_map.html and enter the same numeric or text seed. Drag to
pan and use the mouse wheel to zoom. Views are available for the Overworld, Alt
Dimension, and Boss Dimension.

The seed map shows:
- All current biomes, including Mountain biomes at the revised frequency
- Mansions, Outposts, Cabins, Alt Mazes, Boss Shrines, and the Boss Arena
- Cabin loot block type in the nearby-structure tooltip
- Alt Maze base Y
- Mellorite-room coordinates relative to the Alt Maze center
- Mellorite-room floor number and absolute Y level

Dungeons and Mineshafts are intentionally excluded from the map, though both
continue to generate in the game.

Desktop controls
----------------
WASD        Move
Mouse       Look
Space       Jump / fly upward
Shift       Fly downward
Left click  Break / attack
Right click Place / use jukebox / set Respawn Block
Q           Drop selected item
G           Eat raw meat
T           Chat
E           Crafting
R           Inventory
C           Creative inventory
Esc         Settings / pause

Multiplayer persistence
-----------------------
Each named multiplayer world has its own JSON save. The server preserves block
edits, time, operators, mobs, dropped items, and player profiles including position, view angle,
dimension, health, gamemode, inventory, selected hotbar slot, original spawn, and Respawn Block location. Player physics
and position updates continue while the settings menu is open.

Network notes
-------------
Allow Python through the host firewall on private networks. TCP ports 8000 and
8765 must be reachable. The server is intended for a trusted local network and
does not provide accounts, TLS encryption, or Internet hardening.

Both the multiplayer HTML client and Python server use protocol 4. Replace both
files together when updating an older installation.

Mountain and Alt Dimension revision
-----------------------------------
- Mountain regions are no longer radial cones. Each seed creates irregular,
  rotated chains of two to four offset peaks joined by bent ridges.
- Low Mountain peaks range from Y=100-130, Medium Mountain peaks from Y=130-160,
  and High Mountain peaks from Y=161-190. A single range can contain mixed peak
  tiers and asymmetric outlines.
- The Alt Dimension remains 50 blocks high but restores its original open,
  cavern-heavy density.
- Entering the Alt Dimension creates a safe chamber and places the player at
  exactly Y=30 instead of searching downward from the ceiling.


iPhone performance and mob-facing revision
-------------------------------------------
- iPhone and iPad clients default to a 2-chunk render distance and cap the mobile
  slider at 5 chunks. Desktop settings are unchanged.
- iOS uses a reduced WebGL backing resolution, disables antialiasing, spaces
  synchronous chunk builds, shortens vertical chunk generation/meshing scans,
  and throttles HUD overlays and selection raycasts.
- Mobile touch state is reset after Safari gesture cancellation, page hiding,
  app switching, or focus loss so the movement joystick cannot remain stuck.
- The server prefers a connected desktop player as the shared mob simulator.
  A mobile client is used only when no eligible desktop client is in that dimension.
- Zombie, Skeleton, and Red Alt-Zombie models now rotate 180 degrees relative to
  their movement transform so their faces are on the forward side of the head.

- Saved block snapshots and remote block edits are now recorded without generating
  unloaded chunks, eliminating a major join-time freeze on long-running worlds.
- On iOS, surrounding procedural chunks are generated in a Web Worker. The main
  thread prepares only the current chunk, preserving responsive touch movement
  while the surrounding view loads progressively.


IPHONE, MOB FACING, AND PORTAL REPAIR
-------------------------------------
- iPhones default to a 2-chunk render distance, a reduced WebGL backing resolution, six nearby mobs, asynchronous chunk generation, and slower background chunk uploads. The render-distance slider can still be raised to 5 on iOS.
- Mobile Safari touch handling now disables page gestures and catches touch cancellation outside the original joystick zone, preventing a stale touch from disabling movement.
- Zombie, Skeleton, and Red Alt Zombie humanoid models receive the correct 180-degree model-facing correction.
- Alt portal arrivals are placed beside the portal at Y=30, never inside it.
- Portal blocks are no longer mirrored to the same Y coordinate in the other dimension. This prevents the Alt Y=30 portal from appearing underground in the Overworld.
- Dimension transitions clear stale meshes and chunk queues, restart the iPhone chunk worker, and load the destination chunk before control resumes.
- The Alt arrival chamber is sent as one block batch instead of hundreds of individual rebuilds.
- Entering an affected older world removes the specific legacy Y=30 Overworld portal created by the prior mirroring bug.

MOBILE SMOOTHNESS + BIOME BORDER FIX
------------------------------------
- Restores the iPhone Web Worker chunk generator and the efficient indexed chunk
  queue from the smooth mobile build. Nearby terrain is generated off the main
  browser thread so touch movement is not blocked by 200-block chunk generation.
- Keeps the safe Alt Dimension arrival/return and corrected humanoid mob facing.
- Low, Medium, and High Mountain labels no longer impose a sudden minimum Y level
  at their borders. Mountain terrain now rises continuously from neighboring land.


MOBILE RESOLUTION + BLOCK-FLASH HOTFIX
---------------------------------------
- Mobile Game Settings now include a Resolution slider from 40% to 100%.
  The setting changes the internal WebGL resolution immediately and is remembered
  by the browser. Lower values improve performance; higher values sharpen the image.
- iPhone login text fields are focused only after the touch finishes, preventing
  keyboard-induced layout movement from opening the shirt selector instead.
- Chunk remeshing now uses an atomic GPU-buffer swap. Mining, placing blocks, and
  receiving multiplayer block changes keep the existing chunk visible until its
  replacement is ready, eliminating the full-world flash.


MOBILE INPUT, MOBS, AND MOUNTAIN FIX
------------------------------------
- Mountain regions occur half as often as in the previous build.
- Mobile mining uses the exact current center-screen outlined block.
- Start-screen text fields use native Safari input handling.
- Mob hosting transfers away from inactive/backgrounded clients so mobs continue moving on mobile.


V1.3.2 RENDERER RESTORE
-----------------------
- Restored the original v1.3.2 face-by-face chunk renderer in multiplayer and singleplayer.
- Only block faces exposed to air or transparent blocks are sent to WebGL.
- Removed the later six-pass greedy-plane meshing rules.
- Retained asynchronous iPhone chunk generation, mobile resolution controls, atomic chunk swaps, and current gameplay fixes.
- Retained dimension-aware scan limits so the 200-block Overworld and 50-block Alt Dimension do not scan unused sky.

MOBILE POINTING-DIRECTION HOTFIX
--------------------------------
- iPhone camera rendering is performed before expensive chunk remeshing, so
  right-side look swipes remain visibly responsive while terrain is loading.
- Mobile yaw and pitch are transmitted immediately during look swipes, so other
  players see the correct pointing direction without waiting for a later frame.
- The restored v1.3.2 exposed-face renderer and all current gameplay fixes remain.


SINGLEPLAYER COMBAT + CAVE UPDATE
---------------------------------
- Hostile mobs in singleplayer survival now reliably damage the local player at physical melee range.
- Normal caves are slightly larger and use an additional broad connector field so tunnels/chambers interconnect more often.
- Mega-cave spawn probability is doubled from 13% to 26% per mega-cave region cell; their existing size range is unchanged.


ALT MAZE / RAVINE / ORE / BOSS REVISION
---------------------------------------
- Alt Maze stair rooms are open across both connected floors. Interior terracotta slabs no longer block stair headroom; only stair/landing blocks and ore loot remain in the stairwell interior.
- Trees and cacti require an intact generated surface block, preventing vegetation from floating over surface-open ravines.
- Coal and iron underground veins are half as common while remaining available throughout the underground height range.
- Maximum rare-ore generation heights are doubled: Mellorite below Y=16, Diamond below Y=24, Gold below Y=30.
- Boss victory returns players to the world's deterministic spawn point instead of coordinate 0,0.
- Boss defeat is now a persistent world property in both server JSON worlds and singleplayer browser/JSON worlds. Once defeated, the Mellor Boss does not respawn in that world.

IN-GAME CONFIRMATION HOTFIX
---------------------------
- Singleplayer no longer relies on the browser's native confirm() dialog for deleting
  or replacing worlds.
- Delete World now opens a MellorCraft in-game confirmation overlay with Cancel and
  Delete World buttons, so confirmation works consistently on mobile Safari, Chrome,
  Firefox, and desktop browsers.
- Replacing an existing named world uses the same in-game confirmation system.

Relay skin labels
-----------------
- The singleplayer LAN relay join screen now uses the same shirt-color labels as the multiplayer client: Blue, Green, Purple, Red, Light Blue, and Dark Green.
- The underlying skin IDs are unchanged for protocol compatibility.
