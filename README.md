MellorCraft v1.8.0 mobile performance + armor-slot pass
========================================================
- Kept the restored v1.7.1 mobile controls and device-detection path intact while optimizing the heavier v1.8.0 renderer around it. No gameplay systems, textures, mobs, weather, drops, crafting, flowers, armor, or multiplayer features are disabled.
- Mobile block/mob textures now use native 16x16 atlas tiles instead of storing each logical texel as a duplicated 2x2 area. With nearest-neighbor sampling the artwork is unchanged, while the mobile GPU texture-atlas footprint is reduced from 512x512 to 256x256 (75% fewer atlas texels). Desktop retains the 32x32 physical atlas tiles.
- Lower-end mobile hardware uses a more conservative internal framebuffer default (55% on lower-end iOS and 60% on other lower-end mobile hardware). Higher-end mobile defaults are also reduced moderately to account for v1.8.0 texture sampling. The existing Resolution setting is preserved.
- Added a mobile adaptive-resolution governor. Under sustained low FPS it reduces only the internal WebGL framebuffer in small steps; when sustained headroom returns it slowly restores resolution. UI resolution and every gameplay/rendering feature remain enabled.
- Removed the full block raycast that previously ran on every right-side touch-move event while looking around. The normal throttled selection raycast still runs, and active mining still refreshes its raycast immediately.
- Reduced lower-end-mobile chunk/remesh CPU burst budgets and slowed non-critical HUD/player-overlay polling. Rain particle/splash counts and the flat-cloud horizon are also reduced on lower-end mobile while weather itself remains active.
- The texture atlas is now bound once per render pass instead of being rebound for each textured mesh. Fully textured terrain also uses a constant color attribute instead of fetching an unused per-vertex RGB buffer, reducing mobile WebGL driver work and vertex bandwidth.
- The mobile Armor slot is explicitly fixed at 50x50 pixels with a non-shrinking flex basis, matching the normal touch-sized inventory slot instead of being squeezed by the armor-effect text.
- Dedicated multiplayer remains protocol 12.

v1.8.0 mobile-controls startup restoration
------------------------------------------
- Restored the v1.7.1 mobile startup ordering: `gameStarted` is set before `initGame()` runs its mobile-control visibility update. A later dedicated-server startup hardening change had moved that assignment until after `initGame()`, which caused `#mobileControls` to be explicitly hidden on every phone/tablet even though device detection and touch handlers were correct.
- The v1.7.1 mobile CSS, touch-zone/joystick markup, and touch handler implementation remain unchanged, except the obsolete direct Craft button stays hidden because v1.8.0 uses Inventory plus placed Crafting Tables for crafting.
- A successful startup now performs one additional `updateMobileControlsVisibility()` after the loading screen is dismissed, and failed startup explicitly hides mobile controls again.

MellorCraft v1.8.0 — v1.7.1 mobile logic + permanent account skins
======================================================================
- Reverted MellorCraft mobile-device detection to the exact logic used in v1.7.1: the original mobile user-agent test plus the proven `MacIntel` + multi-touch iPad desktop-mode check. All v1.8.0 gameplay, textures, accounts, crafting, drops, flowers, armor, and protocol-12 networking remain intact.
- Removed the newer layered mobile heuristics (`userAgentData.mobile`, `navigator.standalone`, coarse-pointer, phone-screen-size, and extra Mac/iPhone inference) so the mobile-controls decision once again follows the v1.7.1 path.
- Dedicated-server skins are now permanent account properties. Skin is selected only while creating an account; the Sign In form hides/disables the skin selector.
- The protocol-12 `welcome` message now includes the authenticated account's saved skin, and the client immediately adopts that server-authoritative skin before the world starts. A saved player profile also reinforces the same account skin on restore.
- Verified persistence by creating an account with Ember, disconnecting, then signing in while deliberately transmitting Forest: the server, restored player state, and account file all remained Ember.
- Dedicated multiplayer remains protocol 12.

MellorCraft v1.8.0 — protocol 12 restored-player startup fix
==============================================================
- Fixed a dedicated-server startup hang affecting existing accounts after `world_ready`. Restoring a saved player profile was still rebuilding the complete textured Crafting and Creative catalogs during `initGame()`, even though both menus are hidden at startup. Those expensive lists now render only when their menus are opened.
- Dedicated startup now reports `World loaded. Preparing game...` and `World loaded. Initializing game...` as explicit stages. `gameStarted` is set only after initialization succeeds.
- A dedicated client sends `client_ready` only after initialization completes and the loading screen is dismissed; the Python server logs `Client ready: <username> (...)` so operators can distinguish a successful world transfer from a successfully started browser client.
- Startup failure reporting is now fail-safe: if browser initialization throws, the client shows the actual exception on the account screen and sends `client_start_error` to the Python console as `Client startup failed: ...`. Menu-audio failures can no longer mask the real error behind the old loading text.
- Dedicated multiplayer protocol is now 12 and accepts only protocol 12, preventing older protocol-11 clients/servers from silently pairing with this corrected startup path.

MellorCraft v1.8.0 protocol 11 startup hotfix
----------------------------------------------
- Fixed another dedicated-server join failure that could leave the client on **“World loaded. Starting game...”** even after the server had completed the world transfer.
- The root cause was a browser-dependent synchronous exception in menu-music cleanup: resetting `currentTime` on an `Audio` element whose MP3 source had not loaded could throw before the loading screen was hidden and before the existing startup error handler began.
- Audio shutdown is now non-throwing, the loading-screen transition itself is inside the guarded startup path, and a stale startup-in-progress flag is cleared when an authenticated `world_ready` arrives without a started game.
- Dedicated multiplayer now uses **protocol 11** so this corrected client cannot silently pair with an older protocol-11 server build.
- The protocol-11 server was verified through account signup -> `welcome` -> `world_ready`. A client regression harness with deliberately throwing `Audio.pause()` / `currentTime` operations still reached `initGame()` and removed the loading screen.

MellorCraft v1.8.0
=========================================================



v1.8.0 server-startup, item-drop, and inventory-preview hotfix
----------------------------------------------------------------
- Dedicated multiplayer now uses **protocol 11**. Pages opened from `http://SERVER-IP:8000` always connect back to that exact host on WebSocket port 8765 instead of accidentally reusing a different server address saved earlier by the standalone client.
- Removed the `requestAnimationFrame()` dependency from the final `world_ready` -> game-start transition. The client schedules initialization directly, resets stale startup guards before a dedicated join, and therefore cannot remain at **“World loaded. Starting game...”** merely because animation frames are being throttled.
- Block icons in the hotbar, Inventory, Creative, Crafting, and Furnace now use the **side face** of placeable blocks rather than the overhead face. Saplings and flowers use transparent profile sprites with visible stems/leaves/petals instead of appearing as full square blocks.
- Survival mining no longer deposits the block directly into inventory. The resulting block/item drop appears at the mined position with a small upward pop, follows gravity, and settles on the nearest solid surface below. Creative mining continues to produce no collectible drop.
- Dropped-item pickup is now capacity-aware and all-or-nothing. If the player's inventory cannot hold the entire dropped stack, walking over it leaves the item in the world. Dedicated-server and browser-hosted worlds apply the same rule.
- Picking up an item no longer writes a “Picked up ...” line into the in-game chat.
- Dyeing a sheep now consumes exactly one dye after the authoritative recolor succeeds in local, LAN-hosted, LAN-guest, and dedicated-server play. Dyeing placed wool continues to consume one dye in Survival.

v1.8.0 startup, armor, dye, and server-control pass
-----------------------------------------------------
- Fixed the post-stream startup stall at **“World loaded. Starting game...”**. Dedicated multiplayer now uses **protocol 11**. Streamed block edits are cleared before transfer, preserved through `initGame()`, and inserted directly into the chunk-edit map instead of being erased at startup. Game initialization is scheduled directly after `world_ready` without depending on an animation-frame callback, and startup exceptions return to the account page with the actual error rather than leaving the loading text onscreen forever.
- Added `/stop` to the dedicated-server console. It saves the active world, shuts down the WebSocket/background tasks cleanly, closes the HTTP server, and exits the Python process so the command prompt returns.
- Added `/hunger <0-20>` to the in-game operator command set, parallel to `/health`; the new value is synchronized immediately in multiplayer.
- Added **Light Gray, Gray, Black, and Brown** flowers/dyes, completing all eleven sheep/wool dye colors used by MellorCraft. Dyes recolor sheep and placed wool.
- Greatly reduced flower density outside Flower Forest: ordinary Forest, Plains, Savanna, and Jungle flower attempts are now only about **0.15%-0.30% per eligible grass column**. Flower Forest remains intentionally dense.
- Inventory crafting now shows only recipes costing **fewer than 5 total ingredient items**. Recipes costing **5 or more** are hidden entirely until a placed Crafting Table is opened.
- Added equipable **Iron, Gold, Diamond, and Mellorite Armor Sets**, each crafted from 8 of its material at a Crafting Table. They reduce incoming damage by 20%, 40%, 60%, and 80% respectively. After reduction, positive damage is rounded **up to the nearest half-heart** so combat never stores tiny fractional damage values. Armor is saved and synchronized in browser-hosted and dedicated multiplayer profiles.


v1.8.0 streamed-world, flowers, wool, and crafting pass
----------------------------------------------------------
- Fixed dedicated-server worlds that could remain on the loading screen after authentication. Dedicated multiplayer now uses **protocol 11**: authentication returns the world metadata first, saved block edits stream in bounded batches with visible progress, and the client starts only after an explicit `world_ready` message. The client primes streamed edits directly into its chunk-edit map instead of replaying one giant snapshot at startup. A large-world stress test with 120,000 saved block edits completed the authenticated stream successfully.
- Added a rare **Flower Forest** biome. It uses forest terrain/trees but generates dense red, orange, yellow, blue, white, pink, purple, light gray, gray, black, and brown flowers. Plains, ordinary Forests, Savannas, and Jungles also generate smaller biome-specific mixes of those flowers.
- Added eleven matching dyes. One flower crafts into one dye. Clicking a sheep with a dye recolors its fleece; its future wool drop matches the new color.
- Wool is now placeable as a block. White, black, gray, light gray, brown, pink, red, orange, yellow, blue, and purple wool blocks retain the corresponding wool item when mined. Clicking placed wool with one of the flower dyes recolors it in place.
- Removed the obsolete duplicate **Mellorite** crystal entry and the unnamed/Unknown chest entry from Creative, while preserving the real Mellorite material, ore, storage block, and tool tier. Obsolete bucket-family IDs from earlier experimental builds are removed from the client and Creative inventory, and IDs 109-111 are purged from legacy inventories, dropped items, and Furnace state when older worlds are loaded.
- **E now opens Inventory.** Inventory contains a searchable recipe list for recipes using fewer than five total ingredient items. Search matches recipe names, result names, categories, and ingredient names; clicking an available result crafts it immediately.
- A **Crafting Table** costs four planks, can be placed, and opens its full searchable crafting menu when used. Recipes consuming five or more total ingredient items are only craftable from a placed Crafting Table.
- The Seed Map recognizes Flower Forest using the same rare-biome selection rule as the game client.

v1.8.0 account-handshake + server-console hotfix
-----------------------------------------------------
- Fixed the dedicated-server account join hang. The release now ships a matching **protocol 11** `mellorcraft_server.py` that actually performs Sign In / Sign Up before loading the authenticated player profile.
- Added a second client-side authentication/world-load timeout. If a WebSocket opens but the server never sends the world welcome message, the account page now reports the failure and becomes usable again instead of remaining on “Creating account and loading world...” forever.
- Reworked the interactive Python server console so incoming HTTP/WebSocket/save logs temporarily clear the prompt and then redraw the exact command being typed. Logs no longer split or erase a partially entered command. Arrow-key history, left/right cursor movement, Backspace, Ctrl+A, Ctrl+E, and Ctrl+U are supported in an interactive terminal.
- Typing an argument-requiring command by itself now prints its usage (for example, `/tp`, `/ban`, `/op`, `/gamemode`, and `/account`).
- `/help` now prints the complete server-console command list with usage and a short description for every command.
- The release ZIP now includes the dedicated server, LAN relay, requirements file, client, download page, seed map, and README together so the protocol-11 client cannot accidentally be distributed without its matching server.

v1.8.0 texture, inventory, and server-account pass
----------------------------------------------------
- Fixed **Terracotta** so it uses a softly mottled fired-clay texture instead of the brick mortar pattern.
- Corrected side-face UV orientation for directional block faces. Grass side textures now keep the green edge at the top on +X, -X, +Z, and -Z faces instead of appearing rotated on some sides.
- Added one cached **256x256 UI item atlas** with a 16x16 cell for every numerical block/item ID. Placeable blocks reuse their world texture, while coal, ingots, gems, sticks, food, wool, dyes, flowers, apples, music discs, and all tool/weapon tiers have dedicated pixel art.
- The same item textures are now used in the gameplay hotbar, Crafting menu, Inventory and inventory hotbar, Creative item list and Creative hotbar, and every Furnace slot/inventory cell. Non-placeable items no longer fall back to emoji/text-only icons in those interfaces.
- Dedicated multiplayer now uses **protocol 11** and requires a per-server account before a username can enter the world. The client presents **Sign In / Sign Up**, username, password, and skin fields both when connecting from a standalone client and when opening the page served directly by `mellorcraft_server.py`.
- Server passwords are stored only as random-salt **PBKDF2-HMAC-SHA256** verifiers (210,000 iterations), and usernames are matched case-insensitively. An authenticated username is the identity used to restore its saved profile and operator status, preventing another client from simply typing an operator's name.
- Existing pre-account player/operator names are reserved. The server owner can claim one safely from the console with `/account setpassword "Player Name" password`; `/account list` and `/account delete "Player Name"` are also available. A single account cannot be connected twice simultaneously.
- Opening the dedicated server's HTTP root now redirects directly to the account page for that server. Browser-hosted LAN/relay worlds retain their existing relay protocol; the account requirement applies to the dedicated Python server.
- Added a third **Play in Browser** card to the download page linking directly to `https://linkers15.github.io/mellorcraft/mellorcraft.html`.
- World format remains 11. Browser/exported saves now identify themselves as v1.8.0.

**Security note:** accounts prevent simple username/operator impersonation and passwords are protected at rest, but the default local server still uses plain HTTP/WebSocket transport. Passwords can therefore be observed by someone able to intercept that network traffic. For Internet-facing servers, place MellorCraft behind HTTPS/WSS (for example, a TLS reverse proxy) rather than exposing the default ports directly.

v1.8.0 texture atlas hotfix
-----------------------------
- Fixed the atlas Y-coordinate mapping. The atlas was uploaded without WebGL Y-flipping but the UV helper inverted the whole atlas again, causing faces to sample unrelated rows. This was the source of black block faces, incorrect materials such as leaf faces sampling brick-like textures, and missing/wrong mob textures.
- Atlas UVs now use the same top-to-bottom coordinate space as the generated canvas, so every block face and mob part samples its intended tile.
- Unused atlas tiles are now transparent and the shader falls back to the normal vertex color when a tile is missing, preventing future custom/unknown types from rendering as solid black.

v1.8.0 texture update
---------------------
- Added 16x16 pixel textures for every block, including the Oak, Acacia, Spruce, Jungle, sapling, legacy liquid, utility, ore, portal, and special block IDs. Top/side/bottom variants remain available where the block needs them.
- Added textures to mobs and remote players. Mob texture UVs are quantized against world-space model dimensions so one visible texture square is approximately the same 1/16-block size as one square on a full block texture.
- Textures use a single shared WebGL atlas and the existing chunk/entity vertex buffers. Enabling textures does not create per-block textures, per-pixel geometry, or extra draw calls for individual block faces.
- The atlas stores each logical 16x16 texture at 2x nearest-neighbor resolution for crisp sampling, uses no mipmap generation, and is uploaded once at startup.
- Added a **Block & Mob Textures** setting. Textures default on for v1.8.0 and can be disabled instantly to use the original color-only fallback renderer on lower-end devices.
- World format 11 remains unchanged. Dedicated multiplayer advances to protocol 11 in the current dedicated-server build above; browser-hosted relay networking keeps its existing protocol.

v1.7.1 water rollback + mob/network fixes
------------------------------------------
- Removed the experimental water expansion completely from active gameplay: no Ocean or River generation, no water/flow simulation, no boats, and no Salmon/Shark aquatic mobs. Terrain generation is restored to the stable pre-water v1.7.1 system.
- The Seed Map is restored to the pre-water terrain generator as well, so it no longer displays river/ocean hydrology from the experimental builds.
- Kept the Customized-world terrain blending fix that prevents the former 50+ block biome-junction cliffs.
- Kept default Overworld spawning at block coordinate **0,0**.
- Kept seed-dependent ravines and mega-caves. Mega-cave placement and shape rolls now include the world seed instead of repeating in the same locations on every seed.
- Kept the Bear and Camel model fix: their head/neck geometry is built into the body mesh so the head cannot visually detach during movement.
- Kept the new natural-mob spawn distribution. Spawn attempts are spread around all active players from exactly **2 to 6 chunks** away and reject crowded chunks or positions too close to another natural mob.
- Kept distance-based natural-mob cleanup. A non-boss mob despawns as soon as it becomes more than **7 chunks away from every active player**, freeing space under the mob cap for replacement spawns in the 2–6 chunk band. Browser-hosted worlds and the dedicated server both enforce this rule.
- Kept the multiplayer yaw correction and fixed remote head pitch again: remote heads now use the same pitch sign as the local camera, so positive pitch looks up and negative pitch looks down for observers.
- Multiplayer protocol 6 and world format 11 remain unchanged.

Hardcore death and administration pass
--------------------------------------
- Browser-saved Hardcore worlds now show a **Main Menu** button on the death screen instead of Respawn. Using it permanently deletes that browser world before returning to the main menu, and a LAN-hosted Hardcore world closes for connected guests when its host deletes it.
- Dedicated-server Hardcore deaths now permanently add that username to the world's `bannedPlayers` list and disconnect the player. Banned usernames are rejected on later joins, including after server restarts.
- Relay-hosted browser worlds persist the same `bannedPlayers` list in the browser world save. A Hardcore death by a relay guest bans that username, disconnects the guest, and rejects later attempts to rejoin that world.
- Added `/ban <username>` and `/kill <username>` administration commands. Dedicated-server operators can use both; relay-world operators can use `/ban` and `/kill`, while the existing host-only restrictions remain for the other relay server-management commands.
- `/kill` uses the normal death rules. In Hardcore, killing a remote/server player therefore bans that player as part of the death.
- Browser/exported world saves and dedicated-server saves now use world format 11 for the persistent ban list; older worlds load with an empty ban list.


Furnace shared-inventory fix
----------------------------
- Furnace inventory now uses the exact same shared move / merge / swap routine as the normal Inventory screen instead of maintaining a separate transfer implementation.
- Ingredient, Fuel, Output, and player-inventory stacks can be selected and moved back out using the same select-source / select-destination behavior as Inventory. Ingredient/Fuel still enforce valid-item rules and Output remains read-only as a destination.
- Fixed the singleplayer furnace tick bug that normalized into a temporary state object and discarded the updated burn/progress values. Fuel time and cooking progress now actually decrement, one item cooks in 10 seconds, and the output is produced normally.
- The furnace status now shows the 10-second cooking countdown separately from remaining fuel time, e.g. `Cooking: 8.0s • Fuel: 78.0s`, instead of presenting the 80-second coal burn duration as though it were the cooking timer.


Furnace pointer-transfer hotfix
--------------------------------
- Furnace transfers now use one capture-phase Pointer Events controller for the entire furnace panel instead of separate child touch/click handlers. This prevents gameplay touch handlers, synthesized clicks, or child element updates from swallowing the second tap.
- The intended two-step behavior remains: select an inventory item then Ingredient/Fuel, or select Ingredient/Fuel then the inventory item.
- The transfer hint now changes after the first selection so it is immediately visible whether the furnace registered the tap.
- Pointer movement is ignored as a transfer when the user is scrolling the furnace inventory, so normal mobile vertical scrolling remains available.


Furnace two-step selection hotfix
---------------------------------
- Furnace input is now explicit: tap/click an inventory stack and then **Ingredient** or **Fuel**, or select the furnace slot first and then tap/click the inventory stack.
- The first selection stays highlighted until a compatible second selection completes the transfer, preventing automatic routing to the wrong furnace slot.
- Tapping the same selected, occupied Ingredient/Fuel slot a second time returns that slot to the player inventory; Output remains a direct collect action.
- The two-step selection uses the same persistent touch controls on mobile and mouse/keyboard controls on desktop.


Furnace ignition hotfix
-----------------------
- Furnaces now ignite immediately when both a valid ingredient and valid fuel are present, rather than waiting for a later simulation tick to notice the completed input pair.
- Inserting Iron Ore + Coal (and all other supported recipe/fuel combinations) consumes one fuel item, starts the fuel countdown, and begins the 10-second cooking timer immediately.
- The same ignition state is synchronized to LAN guests and dedicated multiplayer so the local UI does not remain stuck on “No fuel burning.”


Furnace interaction hotfix
--------------------------
- Furnace inventory slots are now persistent DOM controls instead of being destroyed and recreated every render frame. This fixes ingredient/fuel transfers failing on touch and mouse input.
- Furnace progress and fuel countdown updates no longer rebuild the clickable inventory grid.
- Furnace inventory slots support tap/click and keyboard activation, and cooked output remains capped to the normal stack size.

Client variants
---------------
- `mellorcraft.html` is the standard client and loads its MP3 soundtrack files from the same directory.
- `mellorcraft_embedded_audio.html` is the optional self-contained client when present in a release bundle.


v1.7.0 mobile/sapling polish
-----------------------------
- Fixed the mobile Furnace menu so ingredient/fuel/output slots, inventory slots, and the Close button respond directly to touch instead of relying on delayed synthetic click events. The furnace panel now sits above gameplay touch layers while retaining vertical scrolling.
- Planted Oak, Acacia, Spruce, and Jungle saplings now mature after roughly 45–120 seconds while their chunk is loaded. Growth uses the matching wood/leaves family, retries later if there is not enough room, and produces species-specific tree shapes.
- Saplings are treated like narrow custom geometry for face culling: adjacent wall/glass faces remain rendered behind them, preventing saplings from creating see-through holes into neighboring blocks.
- Mobile Creative categories can now be swiped horizontally through the full ten-column item grid, and the Creative hotbar also supports horizontal touch scrolling while the menu keeps its normal vertical scroll.

v1.7.0 world generator pass
---------------------------
- **Create World** now offers **Normal**, **Customized**, and **Flat** world types. Existing worlds default to Normal and keep their current terrain generator.
- Customized worlds can independently enable/disable caves and ravines, set mineshaft concentration, toggle individual Overworld biomes, and assign each enabled biome a relative concentration weight. Customized biome regions use broad seeded cells with blended terrain heights so high/low terrain transitions remain gradual.
- Customized and Flat worlds can independently toggle Mansions, Outposts, Cabins, and Dungeons and set a 0–100% spawn chance for each structure type.
- Flat worlds provide an editable bottom-to-top layer stack. Each layer can use any block type and a custom thickness; the total generated height is limited to 199 blocks. Flat worlds also choose one biome and can optionally generate caves, ravines, mineshafts, vegetation, and structures.
- World-generator settings are saved in exported browser worlds; current saves use world format 11 and are sent to LAN guests. The dedicated server preserves and sends `worldGen` data when it is present in a world save, while older saves remain Normal worlds.
- Cabins, Mansions, and Outposts now choose their construction wood from the biome at the structure center: Savanna uses Acacia, Taiga uses Spruce, Jungle uses Jungle wood, and all other biomes use Oak. Mountain cabins therefore use Oak as the requested fallback.

v1.7.0 finishing pass
---------------------
- Removed the experimental block/mob texture renderer from active use. MellorCraft is back on the stable color-based block renderer; mobs keep their species-specific geometry without texture sampling.
- Leaving any active world now returns directly to the main menu after the save/disconnect completes instead of returning to the initial Start page. LAN-host loss and dedicated-server disconnects use the same main-menu return path.
- Furnaces continue cooking when their menu is closed. Press **E** or **Escape**, tap/click **Close**, or leave the furnace screen while smelting continues. A furnace contributes warm point light while it is actively cooking a valid ingredient.
- Added four tree families: **Oak**, **Acacia**, **Spruce**, and **Jungle**. Existing legacy Wood/Leaves/Planks IDs are treated as Oak so older saves remain compatible.
- Natural trees now use Oak in plains/forests, Acacia in savannas, Spruce in taigas, and Jungle wood in jungles. Each family has matching logs, leaves, planks, and a placeable non-cubic sapling model.
- Each log crafts into four matching planks. Existing recipes that require planks accept any of the four plank families. All logs/planks can be used as furnace fuel.
- Mining any leaf block now uses the requested drop table: **10% apple**, **60% nothing**, **20% matching sapling**, **8% one stick**, and **2% two sticks**. Apples restore 4 hunger points.
- The lightweight classic weather model remains active: 0–200 pressure directly controls cloud/rain/fog bands, cloud base remains Y=200, and cloud tiles drift with the pressure map while fading in/out.


v1.7.0 update
-------------
- Expanded the Overworld mob roster with sheep (four wool colors), goats, rabbits, foxes, and spiders. Pigs, cows, camels, bears, and all new animals now have visible facial details.
- Natural spawning is biome-aware. The default mob cap is now 30; passive mobs populate the surface while hostile mobs favor caves during the day and can also spawn on the surface at night.
- Zombies and skeletons burn in daylight only with direct sky exposure, so cave mobs survive daytime. Skeletons now use ranged arrow attacks.
- Added Peaceful, Easy, Normal, Hard, and Hardcore world difficulty. Hostile damage scales with difficulty, Peaceful removes/prevents normal hostile mobs, and Hardcore disables respawning after death.
- Added a 20-point hunger system displayed as ten food pips beside health on desktop and below health on mobile. Sprinting and repeated jumping increase hunger drain; sufficient hunger slowly regenerates fractional hearts.
- Sprint with a double-tap of W on desktop or the new Sprint control on mobile.
- Mob food drops are species-specific: porkchop, beef, mutton, rabbit, fox, and camel meat, with the requested random drop counts and raw/cooked hunger values. Sheep also drop one wool item matching their color.
- Removed direct smelting recipes from the Crafting menu. A Furnace is now crafted from eight cobblestone, opened by right-clicking it (or the mobile Place action), and cooks one item every 10 seconds using an ingredient and fuel slot. Ores, glass/brick inputs, and raw meats are furnace recipes.
- Browser world format 10 (dedicated servers preserve the same generator field) and multiplayer protocol 6 synchronize the v1.7.0 survival systems while retaining compatibility with older v1.6.x world data.

v1.6.1 update
-------------
- Opening the client now shows a single Start button before the main menu. Pressing it unlocks browser audio and immediately starts a random menu track.
- Singleplayer keeps one Import World button beside Create World. Each saved world now has Play, Edit, Delete, and Export JSON actions; export uses the browser save-file picker when available and a forced-download fallback elsewhere.
- Create World now opens a World Settings menu, and every saved browser world has an Edit action. Per-world rules cover Daylight Cycle, Weather Cycle, Keep Inventory, Mob Spawning, PvP, Mob Cap, and Day Length; exports and imports preserve them.
- Browser hosts, relay LAN hosts, and dedicated Python hosts synchronize those rules authoritatively. Hosts can list, query, or change them at runtime with `/gamerule [rule] [value]`, including from the Python console.
- Disabling Weather Cycle now clears rain, clouds, and weather fog instead of freezing the current storm. Each world's pressure-map seed and movement phase are saved and restored, including dedicated-server worlds.
- Dawn, dusk, sun brightness, cloud shadowing, and ambient light now blend continuously. Direct sunlight is temporally smoothed, preventing the repeated flashes that could occur around sunrise, sunset, and first world creation.
- Rain now renders as one depth-tested WebGL line batch instead of projecting and stroking every drop on a full-resolution Canvas2D overlay. Terrain, trees, and roofs occlude the rain through the existing depth buffer, eliminating per-drop line-of-sight rays while preserving world-space ground splashes.
- Mobile rain uses a smaller fixed particle budget, a reusable interleaved GPU buffer, and cached loaded-column impact heights. The lightweight non-shader cloud ceiling uses WebGL instancing when supported, reducing overcast rendering from many tile draw calls to one.
- The shader fog overlay renders at a reduced mobile resolution with fewer mist and distant-bank samples. Distant storm banks remain continuously tracked, while cached weighted sight probes fade fully blocked fog to zero and preserve a proportional visible fraction behind partial cover without flashing.
- Cave detection now disables both the Canvas atmospheric overlay and the WebGL distance-fog pass. Above ground, a smoothed multi-column sky-exposure sample removes the baseline fog beneath complete cover and scales it beneath partial shelter; directional distant banks still use their independent terrain line-of-sight samples.
- Nighttime fog now inherits the current sky and ambient brightness in both the WebGL depth-fog pass and the atmospheric overlay, preventing bright gray fog after sunset.
- Multiplayer protocol 5 and world format 8 remain compatible with v1.6.0 saves and hosts.


v1.6.0 update
-------------
- Added a panorama-style main menu with separate Singleplayer, Multiplayer, and Settings pages.
- Singleplayer shows every browser save with Play, Edit, Delete, and Export JSON actions, plus Create World and one shared Import World control.
- Multiplayer supports direct dedicated-server connections and relay world discovery.
- Settings uses the original six player colors. Render distance, volume, FOV, and look sensitivity appear on the main-menu Settings page and persist in browser storage.
- Protocol 5 synchronizes a moving, server-authoritative localized pressure map. Pressure bands provide clear, overcast, light-rain, moderate-rain, and heavy-rain weather with progressively stronger fog and precipitation. Clouds use a continuously drifting, world-anchored ceiling out to 500 blocks; each tile contains four touching chunk-wide cloud blocks, fully covering overcast and rainy pressure regions without player-relative snapping.
- Cloud rendering evaluates every nearby pressure tile even when the player is currently beneath clear sky, so storm banks remain visible on the 500-block horizon. Distance fog is always present and thickens with rain. Rain uses fast world-space vertical drops, checks overhead blocks to stay out of caves, and produces short ground-impact splashes.
- Weather regions use twice the previous horizontal noise scale, producing broader storms and clear areas. Heavy-rain fog limits useful visibility to roughly three chunks below the cloud deck, while players above cloud level receive no rain. With Lightweight Shader enabled, clouds gain saved Thickness, Density, and Detail controls and render as layered self-contained voxel volumes.
- Local rain now adds an explicit atmospheric haze, while projected fog banks reveal rainy weather beneath distant clouds up to the 500-block horizon. Shader clouds use translucent, lit, offset voxel layers; cloud pressure along the sun ray attenuates terrain sunlight, sun glow, and sun rays, fully hiding the sun beneath dense cover.
- Fog uses a horizon-weighted depth veil plus slowly moving mist layers instead of a uniform gray screen tint. Rain sheltering is column-local: a lone roof no longer disables the surrounding storm, drops find and splash on the highest terrain, canopy, or constructed roof in each column, and only players genuinely below the terrain surface suppress the outdoor rain layer.
- Distant fog banks, world-space rain streaks, and rain splashes now require a cached terrain line of sight; the shader sun retains its stricter terrain-and-cloud visibility ray. Every rain band now starts with dense fog, with moderate and heavy rain increasing toward a roughly three-chunk visibility limit.
- Fog now grows continuously from nearly imperceptible at pressure 39 to near-whiteout conditions at pressure 1. Distant fog banks retain a softly occluded minimum instead of blinking when terrain sight tests fluctuate. The pressure field is advected by the exact cloud drift vector, preventing stationary cloud tiles from appearing and disappearing beneath an independently moving map.
- Standard clouds now sit at Y=150. Shader clouds use rounded low-poly volumetric puffs; pressure below 10 builds tall cumulonimbus columns whose height increases as pressure falls. In-game Settings now includes **Return to Main Menu**, which saves before closing active connections and reloading the menu.
- Shader-cloud opacity and puff overlap are increased for denser volumes. Rain-bearing clouds now reduce direct sunlight to near zero and fully hide the sun disc and rays. The world-space rain radius is doubled from 34 to 68 blocks, with a doubled particle budget on desktop and mobile.
- Performance fallback: disabling Lightweight Shader now disables all fog passes and volumetric cloud puffs. The client uses one flat block-cloud tile per weather cell instead, and mobile limits that lightweight cloud horizon to 224 blocks. Shader mode retains the full 500-block volumetric weather rendering.
- Remote players animate while walking and render synchronized, clamped head pitch without sideways head rotation.
- Ore bottoms now use the ore appearance instead of stone.
- Damage-hit notices and other-player gamemode-change notices no longer clutter chat.
- `Mossline Haven.mp3`, `Driftwood Camp.mp3`, and `Forest Dawn.mp3` join random menu and in-game ambient playback. Menu playback is attempted immediately, stops on world entry, and a fresh in-game track begins.


v1.5.0 update
-------------
- The separate singleplayer and multiplayer pages are now one `mellorcraft.html` client. Its start menu can create a browser world, join a saved browser world, discover and join a relay world, or connect directly to a multiplayer server using separate IP and port fields.
- Relay and dedicated-server connections now use matching IP and port fields. Players never need to type `ws://`; relay ports default to 8000, dedicated-server ports default to 8765, and secure pages select `wss://` internally when required. Older saved combined addresses are migrated automatically.
- Torches no longer cull the complete wall, floor, glass, or terrain face beside their narrow model. Supporting surfaces remain closed, preventing spectator-like views into adjacent blocks.
- Portal transitions now reuse the active terrain worker and loaded dimension caches instead of deleting every GPU chunk buffer and rebuilding the worker in one frame. Portal block batches inspect loaded terrain only, preventing hidden destination chunks from generating synchronously. Mobile clients reclaim old-dimension meshes in tiny post-render batches.
- Crouching is available with Shift on desktop and a dedicated mobile button. It lowers the viewpoint, slows movement, and hides the crouched player's nametag and locator marker from other browser, relay, and dedicated-server clients. Settings can choose Hold or Toggle behavior.
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

World game rules
----------------
Create World and Edit World open the browser World Settings screen. Game rules are
stored inside the world JSON and are shared with relay guests and dedicated-server
players. The supported rules are `doDaylightCycle`, `doWeatherCycle`,
`keepInventory`, `doMobSpawning`, `pvp`, `mobCap` (0-200), and `dayLength`
(60-3600 seconds).

In an operator's in-game chat, a browser relay host's chat, or the dedicated
server's Python console, use:

   /gamerule
   /gamerule keepInventory false
   /gamerule mobCap 20
   /gamerule dayLength 900

Using only a rule name reports its current value. Boolean values accept
`true`/`false`, `on`/`off`, `yes`/`no`, or `1`/`0`.

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
- Ocean, Beach, and River biomes are generated alongside Plains, Forest, Taiga, Stony Peaks, Jungle, Savanna, deserts, Badlands, and all three Mountain biomes. Swamp remains unavailable in new generation.
- Ocean water sits at Y=45. Ocean floors are sealed against cave and ravine carving. Rivers use seeded continuous channels whose surface descends from higher inland elevations to Y=45 at the ocean boundary.
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

Export World downloads the selected save as JSON, using the system save dialog
where the browser supports it. The shared Import World button beside Create World
restores a save or transfers it to another browser. Browser storage is tied to the
page origin, so direct-file and web-served copies may have separate save collections.

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
Shift       Crouch / fly downward
Left click  Break / attack
Right click Place / use block / dye sheep or wool
Q           Drop selected item
G           Eat raw meat
T           Chat
E           Inventory
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
8765 must be reachable. Dedicated v1.8.0 servers use protocol 11 and require a
server account before a username is admitted. Account passwords are salted and
hashed on disk, but the default HTTP/WebSocket transport is not encrypted. Use
HTTPS/WSS through a TLS reverse proxy before exposing a server to the Internet.

`server_accounts.json` stores the server-wide account registry. Keep that file
private and back it up with the world saves. For a privileged identity from an old
pre-account world, assign the account from the server console with
`/account setpassword "Player Name" password` before that player signs in.

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
- Dimension transitions clear stale queue work, reuse the existing terrain worker and loaded caches, and request the destination nearest-first before control resumes.
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
