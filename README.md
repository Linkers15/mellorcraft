MellorCraft v1.5.0
=========================================================


v1.5.0 update
-------------
- The separate singleplayer and multiplayer pages are now one `mellorcraft.html` client. Its start menu can create a browser world, join a saved browser world, discover and join a relay world, or connect directly to a multiplayer server using separate IP and port fields.
- Relay and dedicated-server connections now use matching IP and port fields. Players never need to type `ws://`; relay ports default to 8000, dedicated-server ports default to 8765, and secure pages select `wss://` internally when required. Older saved combined addresses are migrated automatically.
- Torches no longer cull the complete wall, floor, glass, or terrain face beside their narrow model. Supporting surfaces remain closed, preventing spectator-like views into adjacent blocks.
- The mobile Creative inventory now uses the full safe-area viewport with native vertical touch scrolling, so every block, material, tool, weapon, and hotbar slot remains reachable on small screens.
- Portal arrivals no longer generate the destination chunk synchronously on the gameplay thread. The destination is requested through the existing terrain worker while player simulation is briefly held, preventing portal-entry freezes without increasing per-frame work.
- Terrain generation now keeps only one worker request in flight and dynamically chooses the nearest current need for each next request. Mesh work is reprioritized around the player's latest chunk, stale far-away requests are discarded, and movement waits at an unready chunk edge instead of forcing synchronous generation.
- Mob navigation now looks slightly ahead of the body when crossing a ledge, allowing valid one-block ascents and configured safe descents instead of stopping where the mob's collision box first meets the height change.
- Forest, taiga, and jungle chunks retain the same 64 candidate planting columns and tree probabilities, but their planting windows shift independently in seeded X/Z positions so aligned chunk-by-chunk tree grids are no longer visible.
- Performance overhaul: player/network block edits now use a high-priority remesh lane that is processed before the next frame is drawn, so mined blocks no longer remain visibly stuck while normal terrain work is queued.
- Terrain generation now uses a Web Worker on all supported browsers, not only iOS, preventing new-chunk generation from blocking movement/look/rendering on desktop and Android.
- Chunk meshing no longer synchronously generates missing neighbor chunks and scans voxel memory in cache-friendly order; mobile background mesh builds use smaller frame budgets.
- Mob navigation/threat decisions are staggered and cached while collision/physics remain smooth every frame, substantially reducing the CPU cost of v1.5.0 pathfinding.
- Shader lighting caches nearby torches, reuses its shadow upload buffer, throttles heightfield uploads, and uses a smaller mobile shadow field. World rendering now uploads the static terrain model matrix once per frame instead of once per chunk.
- Fixed the mobile chat/command UI so long chat history can no longer push the text-entry controls out of reach. While chat is open on a phone, the history becomes its own scrollable region and the input stays anchored above the on-screen keyboard.
- Mobs now use bounded pathfinding when direct movement is blocked, avoid unsafe cliffs and configured hazards, slide around walls, and search for a nearby safe position if embedded or repeatedly stuck. Passive mobs also flee nearby hostile mobs.
- Glass is now rendered in a separate translucent pass: it is genuinely see-through, keeps a subtle blue tint, and suppresses hidden faces between adjacent glass blocks.
- Torches now render as slim wooden sticks with a visible flame instead of full cubes, and nearby surfaces receive warm point-light illumination.
- Added an optional extremely lightweight shader toggle in Game Settings. It draws a visible moving sun, applies a lightweight loaded-chunk heightfield (64x64 desktop / 40x40 mobile) for three-sample directional terrain shadows, strengthens sun contrast, and extends torch glow. The shader defaults off on mobile and on for desktop unless the player has saved a preference.
- Corrected the shader daylight path so its sun/shadow timing matches the existing 0.25 sunrise through 0.80 sunset clock. Shader mode now lowers the legacy full-day ambient term enough for directional sunlight and terrain shadows to actually be visible.
- The shader reuses the restored v1.3.2 exposed-face renderer: no greedy remeshing, full shadow maps, framebuffer passes, or texture packs were added.


Mobile menu scrolling hotfix
----------------------------
- Mobile singleplayer no longer applies `touch-action: none` to the entire page.
- The start screen is now a native vertical scroll container on small displays, so Delete World and LAN Join controls remain reachable.
- Game Settings now uses native touch panning and momentum scrolling, allowing the Open to LAN controls at the bottom to be reached on phones.
- Gameplay canvas/joystick surfaces still suppress browser panning while the game itself is active.

Files
-----
mellorcraft.html               Unified browser, relay, and multiplayer client
mellorcraft_seed_map.html      Interactive seed and structure map
mellorcraft_server.py          HTTP + WebSocket multiplayer host
mellorcraft_relay.py           Singleplayer LAN relay (WebSocket, default port 8000)
requirements.txt               Python dependency
worlds/                        One JSON save per named multiplayer world


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
3. In the world-owning client, open Game Settings, scroll to **Open Browser World to Relay**, enter the relay IP/port, and choose **Open World to LAN**.
4. On another client, use **Join a Relay World**, enter the same relay IP/port, choose **Find Worlds on Relay**, select the world, and join it.

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

Unified client
--------------
Open `mellorcraft.html` in a modern browser. Browser worlds use the complete game
engine without the Python server and autosave the seed, block edits, time, player
state, inventory, mobs, and dropped items. The same start menu can also join relay
worlds or a dedicated server using its `ws://` or `wss://` address.

You can also open the unified client online by opening linkers15.github.io/mellorcraft

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
Right click Place / use jukebox
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
edits, time, operators, mobs, and player profiles including position, view angle,
dimension, health, gamemode, inventory, and selected hotbar slot. Player physics
and position updates continue while the settings menu is open.

Network notes
-------------
Allow Python through the host firewall on private networks. TCP ports 8000 and
8765 must be reachable. The server is intended for a trusted local network and
does not provide accounts, TLS encryption, or Internet hardening.

The v1.5 multiplayer HTML client and Python server use protocol 5 for mod-aware joins.
An unmodded server also accepts supported older protocols; a modded server requires
protocol 5 plus the exact mod-set signature. Replace client and server together when
updating a modded installation.

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

Singleplayer host identity hotfix
---------------------------------
- The singleplayer start screen now asks for a player name and shirt color before creating or loading a local world.
- The six shirt-color choices exactly match the multiplayer client: Blue, Green, Purple, Red, Light Blue, and Dark Green.
- The selected identity is remembered in browser storage and is also used as the default identity when joining a relay world.
- When a local world is opened to LAN, the host advertises and synchronizes using the selected username and skin instead of always appearing as `Player` with the blue shirt.
- Browser-world player profiles are saved under the actual lower-cased username, matching the Python server's canonical `playerProfiles` behavior. The active singleplayer host is always added to the world's operator set under that username.

v1.5.0 sun LOS + mob AI revision
--------------------------------
- The shader sun disc now performs a cached line-of-sight test against already-rendered terrain height columns. Hills, mountains, roofs, trees, and other opaque loaded terrain hide the sun instead of allowing the DOM sun disc to draw through them. The test never generates chunks and is throttled for mobile performance.
- Mob navigation now prefers same-level ground before climbing, treats one block as the maximum upward step independently from safe-drop distance, and clamps long A* goals to the local search radius.
- Hostile chase logic is explicitly separate from passive flee logic. Bears and other hostile mobs clear stale wander paths when acquiring a player and use chase-biased local steering when a pathfinder detour would otherwise begin by moving strongly away.


v1.5.0 shader lighting revision
------------------------------
- Lightweight shader settings now expose independent controls for shadow strength, shadow softness, torch brightness, torch range, night darkness, and cave darkness. Settings persist in browser storage.
- Terrain shadows use additional near/far height probes plus two lateral penumbra probes, producing stronger contact shadows and softer edges without a heavyweight framebuffer shadow map.
- Cave lighting uses cached overhead/nearby sky-exposure samples from already-loaded chunk height data. Deep overburden darkens naturally, while cave mouths and sparse overhead cover admit more ambient light. No extra chunks are generated for lighting.
- Night ambient light is independently configurable and transitions smoothly through dawn/dusk.
- Torch light has a smoother warm falloff, configurable brightness/range, and remains additive so torches restore useful visibility in dark caves and at night.
- Mobile keeps the system lightweight: cave exposure is throttled/cached, shadow height uploads remain throttled, and only the three nearest torches are used (four on desktop).


v1.5.0 stronger sun/shadow + multiplayer administration update
--------------------------------------------------------------
- Shader Shadow Strength now defaults to 105% and is adjustable from 0-125%.
- New Sunray Strength setting (0-200%, default 125%) controls the LOS-aware sun rays/glow. Sun and rays remain hidden behind terrain.
- Dedicated multiplayer: `/gamemode <player> <survival|creative|spectator>` changes a named connected player's mode. `/gm` is an alias.
- Dedicated multiplayer: `/tp <player> <targetPlayer>` teleports a player directly to another player, including across dimensions.
- Dedicated multiplayer coordinate teleport: `/tp <player> <x> <y> <z> <dimension>`, where dimension is 1=Overworld, 2=Timeless Void, 3=Boss Dimension.
- Usernames containing spaces may be quoted in server commands, e.g. `/tp "Player One" "Player Two"`.
