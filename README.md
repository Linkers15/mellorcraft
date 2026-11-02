MellorCraft v1.8.4 — Visual Terrain LOD Fix
==========================================

CURRENT HOTFIX (version remains 1.8.4)

FIXED: DISTANT TERRAIN PATCHWORK / FLOATING-LOOKING SLABS
- Distant Overworld terrain now follows the actual generated surface height at
  every column. It no longer decides whether entire 2x2/4x4/8x8 voxel volumes
  are solid based on a few corner samples: that was the cause of unnatural
  floating snowy patches, huge square ledges, and dark cliffs in the screenshot.
- Ground surfaces are greedily merged into faces only where their height and
  block material match. Adjacent cliff faces are also merged for efficiency.
- Balanced/Fast simplify only *nearly flat* patches (respectively 2x2 and 4x4
  adaptive areas). Ravines and steep slopes retain their actual contours.
- No surface smoothing is applied to the ground directly beneath trees, cacti,
  flowers, saved edits, or structures, preventing decorations from floating.
- Other dimensions retain their 3D floating rock geometry; the Timeless Void
  still has the previous approximately 50% rock density.

RENDER DISTANCES AND FEATURES
- High-resolution distance remains configurable up to 64 chunks.
- Extended distance remains optional and must exceed high-resolution distance;
  /rd and /edrd commands are unchanged (maximum extended distance 96 chunks).
- Distant texture resolutions are still High 8x8, Balanced 4x4, Fast 2x2.
- Exact tree, cactus, structure and player-edit placements are still emitted.
  This preserves recognizable scene landmarks.
- Saves, server and relay protocols, climates, snow, caves, and drops are unchanged.

VALIDATION AND PERFORMANCE NOTE
- JavaScript syntax, existing climate/weather/cave/Timeless Void tests, server
  drop tests and new 1x1 terrain coverage/height anchoring/chunk masking tests
  passed. Distant meshes produced ~7256 / 7228 / 6987 quads in the synthetic
  High/Balanced/Fast test; counts vary considerably with terrain.
- Following real terrain heights may create more distant faces than the prior
  broken coarse-voxel approximation. Exact FPS and visual appearance have NOT
  been verified in an interactive WebGL session here. Try 12-16 high-res and
  32 extended with Balanced detail before raising the distances.
- Back up valuable worlds before switching builds; save-format compatibility
  is retained. For a fair comparison use the same seed and camera location.

------------------------------------------------------------------------
HISTORICAL v1.8.4 NOTES (older LOD method below is superseded)
------------------------------------------------------------------------

MellorCraft v1.8.4 — Coarse Extended Terrain + 64-Chunk High Resolution
======================================================================

CURRENT BUILD (version remains 1.8.4)

GEOMETRY-BASED EXTENDED DETAIL
- Replaced the expensive per-block distant terrain mesh with actual lower-detail
  geometry derived from the same seeded voxel chunks as the playable world.
- Ordinary natural terrain (stone, grass, dirt, sand, snow, common stone
  variants, and liquids) is pooled into larger voxel cells. This simplifies
  rocky slopes and cave surfaces instead of just lowering texture resolution.
- Non-terrain features such as tree trunks/leaves, cacti, flowers, cabins,
  mansions, building materials and special blocks retain their source position
  and shape. Explicit saved edits also remain represented at source positions.
- Quality settings adjust BOTH terrain geometry AND block texture atlas:
    High:     2x2 horizontal terrain cells / 8x8 texture pixels
    Balanced: 4x4 horizontal terrain cells / 4x4 texture pixels (default)
    Fast:     8x8 horizontal terrain cells / 2x2 texture pixels
  Vertical detail for natural terrain is grouped in 2-block cells.
- Individual distant chunks transition to their full meshes as they are
  generated. Tile face masks are prevented from merging across chunk
  boundaries; exposed boundary sides are retained to avoid disappearing seams.
- This intentionally does NOT preserve every natural block in the distance.
  Thin natural ledges, small cave openings and fine terrain detail may be
  simplified. Distinctive structures and placed blocks remain recognizable.

TWO INDEPENDENT RENDER DISTANCES
- High-resolution distance is selectable from 2 to 64 chunks in Settings or
  with /rd <2-64>. The previous hidden desktop 16-chunk mesh cap is removed.
- Extended distance is optional, ranges from high-res+1 to 96 chunks, and can
  be changed with /edrd <n> or /edrd off (no operator permissions required).
- Increasing the high-res value automatically raises the saved extended value
  if necessary, preserving extended > high-res whenever extension is enabled.
- These settings are saved locally; no world save or protocol changes.
- At high values (especially 32-64 full-resolution chunks), memory and GPU
  demands can be substantial. New chunk requests are queued in bounded batches
  rather than all at once. The selected radius is honored progressively, but
  very large worlds can take time to populate and may exceed device resources.

REGRESSIONS / VALIDATION
- Targeted test scenes generated ~2,898 / 1,241 / 584 distant quads at the
  High / Balanced / Fast settings, while retaining original cactus, tree,
  building, glass and edit geometry. These figures are sample-dependent.
- Existing climate/seed-map, mega-cave, Timeless Void, snow, ravine-fog and
  dedicated-server dropped-item tests passed. JS and Python syntax passed.
- No interactive WebGL/FPS benchmark has been completed. Test with a new world
  and back up valuable saves before setting very large render distances.

------------------------------------------------------------------------
PREVIOUS v1.8.4 CHANGELOG (earlier rendering rules below may be superseded)
------------------------------------------------------------------------

MellorCraft 1.8.4 — Hotbar, Dynamic Drops & Exact Extended Chunks
=================================================================

CURRENT BUILD — retains version number 1.8.4, climate changes, irregular
mega-caves, and ~50% Timeless Void rock concentration.

CONTROLS
- Mouse wheel forward/back switches among the 9 hotbar slots during gameplay.
  Menu lists, inventory, chat, and settings continue to scroll normally.
- /rd controls high-resolution range; /edrd controls optional extended range.

DROPPED-ITEM SUPPORT
- Previously dropped items now check whether the supporting voxel has been
  removed and fall to the next actual floor. Applies to mined blocks and Q
  drops. The dedicated host validates client-reported replacement floors.
- Browser/LAN authoritative host and Python dedicated server both updated.

EXTENDED RENDERING
- Replaced height-only tiles plus a separate vegetation generator with tiles
  meshed from the SAME fully generated 16x16 voxel chunks as nearby terrain.
- All exposed generated block types (terrain, underground cave surfaces,
  flowers, cacti, tree blocks, structures, ores and saved block edits) are
  included. Chunk masking prevents cactus/terrain from disappearing at the
  high-resolution transition. Geometry remains at block scale; quality affects
  texture resolution ONLY: 8x8, 4x4 (default), 2x2 pixels per tile.
- Worker generates exact voxel face masks; coplanar matching blocks are greedily
  merged within each chunk and textures repeat per world block in shader.
- Full-resolution chunks replace the matching subset of exact distant tiles.

PERFORMANCE NOTE
- This is more geometrically expensive than the former height-only distant
  terrain. At 32-64 chunks, exact tiles load progressively and may take longer
  to populate or use more GPU memory, depending on terrain and hardware.
  Performance/FPS at these settings has not been verified interactively.
- Distant stair, glass and flower blocks retain their source block IDs and
  atlas textures; some special block shapes/transparency are approximated
  by opaque voxels in the distant mesh until their full-detail chunk loads.

TESTING
- JavaScript syntax, Python compile, climate/weather/mega-cave tests,
  deterministic exact-voxel mesh and texture-only LOD tests, chunk-substitution
  and saved-edit checks, and server dropped-item support regression passed.
- Headless browser/WebGL visual testing was not available. Please back up saves
  and test in an ordinary desktop browser before deploying to a shared server.

-----------------------------------------------------------------------------

MellorCraft v1.8.4 — High-Resolution + Extended Render Distance Revision
============================================================================

VERSION: 1.8.4 (per request; this incorporates the climate/weather work from the
previously distributed build labeled 1.8.5, without advancing the version).

TWO SEPARATE RENDER DISTANCES
- High-resolution distance: 2–16 chunks on desktop (2–4/5/10 on mobile,
  depending on the device cap). /rd <n> adjusts this local client setting.
- Optional Extended Render Distance: choose a number GREATER than the high-res
  radius, up to 64 chunks. Enable in either Settings menu, or use
  /edrd <n> to set and enable it without operator permission.
- /edrd off disables extension while preserving the selected extended value.
- Both settings persist in local browser storage; they are never world rules.
- When extended mode is disabled, the high-resolution radius is the visible
  range; lightweight placeholder tiles remain near generating chunks.

REAL DISTANT DECORATIONS + TEXTURES
- Distant trees, flowers, and cacti now follow the actual chunk decoration
  generator, at the same deterministic positions and with the same species.
  The former invented tree-per-chunk silhouettes are gone.
- Distant block-geometry is batched and distant leaves are grouped on a small
  voxel grid to reduce draw calls and triangles. The farther mesh is still
  a visual proxy, NOT fully simulated voxel chunks, and structures/edits
  outside the high-resolution radius are not displayed by those proxies.
- The distant texture atlas is genuinely reduced per original 16x16 block tile:
    High: 8 texture pixels per side, 4-block terrain sampling
    Balanced: 4 pixels per side, 8-block terrain sampling
    Fast: 2 pixels per side, 16-block terrain sampling
  Original nearby texture detail remains unchanged.
- Retains terrain skirts and mesh replacement guards to reduce void flashes.
  A stale worker result cannot replace a differently configured tile.

WORLD GENERATION
- Mega-cave boundaries now have two scales of 3D shape warping and overlapping
  lobes, breaking up spherical outlines without changing cave frequencies.
- Timeless Void: air versus solid rock uses a zero-centered noise threshold
  with low-frequency, region-dependent offsets. Seeded sampling measured ~49%
  solid blocks in the unmodified interior (bedrock, structures, ores excluded),
  with small natural regional differences. Density is approximate, not an
  enforced exact 50% for each finite area.
- Retains all four large climate groups, sensible biome boundaries,
  cold-only mountain ranges, snowstorms and open-ravine fog from the previous
  build. The seed map uses matching biome functions.

COMPATIBILITY & TESTING
- World save format 12, dedicated multiplayer protocol 16, and relay protocol 1
  remain unchanged. Existing saved block edits should be preserved; newly
  generated Timeless Void terrain and mega-caves can differ from earlier builds.
- Tests: JS syntax, Python compilation, exact vs full-chunk decoration comparison
  on sampled test chunks, three LOD levels, near/far seam masking, climate-map
  agreement and weather logic. Actual interactive WebGL/FPS testing remains
  necessary on supported hardware.
- Back up saved worlds before testing world-generation changes. Use a NEW
  test world to evaluate the revised cave/alt-dimensional distribution.

----------------------------------------------------------------------------
PREVIOUS RELEASE NOTES (historical; some prior render-distance behavior below is
superseded by this revision)
----------------------------------------------------------------------------

Inherited climate/weather improvements (included in v1.8.4)
=========================================================================

CLIMATE AND WEATHER NOTES

DISTANT RENDERING
- Added deterministic lightweight distant tree meshes: oak, spruce, jungle and
  acacia silhouettes with block-like textured trunks and leaf canopies.
  Tree density decreases progressively with LOD detail to preserve frame rate
  at long render distances (64 chunks remains supported).
- Added downward overlap skirts at tile borders and transitions to full chunks,
  reducing flashes of sky/void and see-through terrain at mismatched LOD heights.
- Existing tiles remain visible while replacement detail samples arrive, avoiding
  temporary blank terrain during quality switches.
- Full-detail chunks still own gameplay, edits, collisions, trees and structures.
  Distant trees are visual approximations and are not collidable.

NEW NORMAL-WORLD CLIMATE GENERATION
- Four broad climate regions follow gently warped temperature/moisture fields:
  Cold: Low/Mid/High Mountains, Taiga, Snowy Plains.
  Temperate: Forest, Flower Forest, Plains.
  Warm: Jungle, Savanna.
  Arid: Barren Desert, Cactus Desert, Badlands.
- Regions extend around 1,000 blocks in typical spans (terrain noise can vary).
  The familiar 88-block provinces now subdivide these large climate regions,
  rather than independently mixing unrelated biomes.
- Ecotones favor forest/taiga and plains/snowy-plains transitions, with savannas
  bridging warm regions and desert country. Mountain planning requires at least
  7 of 9 surrounding 230-block climate probes to be cold; mountain surfaces
  themselves do not render as mountain biomes outside cold regions.
- The standard height generator now uses the same macroclimate map as the biome
  chooser. Customized/flat world biome selection remains configurable.
- The seed map shares the normal-world climate and mountain algorithms.

WEATHER
- A storm passing through cold regions produces snow instead of rain.
  Snowflakes are drawn as small six-vertex shapes and fall much more slowly
  than rain, with sideways drift. No rain splashes are drawn for snow.
- Existing local-pressure storm strength, clouds, and fog remain unchanged.
- Fog and precipitation now use the actual loaded overhead column for cover;
  open ravines can show storm fog even below the nominal surface elevation.
- The seed-map weather readout labels cold-region precipitation as snow.

SAVE & SERVER COMPATIBILITY
- Save format 12, dedicated-server protocol 16, relay protocol 1 unchanged.
  Existing worlds still open, but regenerated/previously unmodified terrain
  can change near region boundaries. Back up worlds before upgrading; a new
  test world is recommended for judging climate placement and FPS.
- The climate-aware generator changes terrain relative to the original early 1.8.4 build.
  Structure logic and the 200-block above-zero height limit are preserved.

VALIDATION
- Passed JS syntax checks (main client and seed map), Python syntax checks,
  LOD geometry/replacement tests, climate/seed-map parity across three seeds,
  mountain climate restrictions, and snow/ravine-fog logic checks.
- Interactive WebGL/FPS testing could not be completed in this container:
  Chromium headless startup timed out in its graphics environment. Please
  validate distant seams, FPS at 32/64 chunks, and storms in an actual browser.

==========================================================================
HISTORICAL 1.8.4 CHANGELOG
==========================================================================

MellorCraft 1.8.4 — Chunk Border Occlusion & Distant Terrain LOD
================================================================

CHANGE 1 — UNGENERATED CHUNK GAPS
- Meshing now treats unseen or unmeshed neighboring chunks as unknown/opaque,
  not empty air, so it does not expose cutaway faces/underground ores and caves.
- Once a neighboring chunk's first real mesh is completed, existing border
  meshes are scheduled for rebuilding with the correct actual shared faces.
- Separate, temporary low-resolution terrain surface tiles cover still-pending
  chunks while full chunks stream in, reducing visible holes in the horizon.
  Proxies are approximate and do not include edits, structures, vegetation or
  underground features; they are replaced by real meshes as those load.

CHANGE 2 — RENDER DISTANCES THROUGH 64 CHUNKS
- The render-distance control (in the main menu and pause settings) and /rd
  command now allow values 2 through 64.
- The nearest 16 chunks of terrain use the original full voxel renderer on
  desktop. On mobile, the existing hardware-dependent full-chunk cap (4, 5,
  or 10) continues to apply for performance and distant proxies cover the rest.
- Terrain beyond the full-detail radius uses lightweight height-based surface
  tiles of 4x4 chunks. No voxel array, cave carving, underground ore meshes, or
  near-field block interactions are computed for these distant-only tiles.
- Added configurable Distant Terrain Detail settings in the main menu and
  pause menu: High (4-block sample cells), Balanced (8, default), Fast (16).
  Terrain meshes and settings are generated progressively and stored only while
  they remain near the player; this reduces the high-distance resource cost.
- Terrain height comes from the seeded height/biome generator; edits,
  structures, trees and underground details are only shown with full meshes.
- The camera clipping plane expands with selected render distance.
- Both world-generation workers are seeded identically; changing LOD quality
  rebuilds distant tiles without changing the world or the save.

COMPATIBILITY
- Save format 12, dedicated-server protocol 16, relay protocol 1, original
  terrain generation and all other 1.8.3 mechanics are unchanged.
- The seed map uses the same world generation as 1.8.3 and is version-labeled.
- Large render distances are graphics/CPU intensive even with LOD; 16–32 is a
  sensible starting point. Distant previews are visual only, not collision or
  server-authoritative world edits.
- The new performance system depends on browser Web Workers. If disabled by
  security policy/browser restrictions, the normal nearby world remains playable
  but distant proxy terrain will not generate.

TESTING
- JavaScript/Python syntax checks and targeted LOD geometry unit tests have
  been run. Browser GPU smoke testing was blocked by the test environment's
  WebGL/browser navigation restrictions; full interactive FPS profiling across
  hardware and all weather/dimension/multiplayer modes has not been performed.

================================================================
HISTORICAL 1.8.3 NOTES (AS PROVIDED)
================================================================

MellorCraft 1.8.3 — Classic Mountains, Snowy Plains & Spruce Treeline
========================================================================

CURRENT BUILD — supersedes the older mountain-height/performance changes in
historical release notes below. The game version remains 1.8.3.

TERRAIN ROLLBACK / WORLD HEIGHT
- Restored the mountain-region generator and mountain-height formula from the
  pre-"Mobs & Mountains" 1.8.3 Forest/Structures/Portals release. This restores
  its original peak count, ridges, altitude caps, mountain distribution, and
  mountain details rather than merely reducing the new generator's frequency.
- The Overworld again uses 248 internal voxel layers, corresponding to 200
  nonnegative displayed Y levels (0 through 199) plus 48 underground layers
  (Y=-48 through -1). The Timeless Void's 50-layer height is unchanged.
- The newer 256-layer allocation, extra mountain octaves, and Stony Peaks
  ridge-height computations are removed. Custom terrain returns to the old
  Y=190 generated-terrain cap; user-placed blocks may reach displayed Y=199.

SNOWY PLAINS
- Replaced biome ID 8 (formerly Stony Peaks) with Snowy Plains in the normal,
  custom, flat, and seed-map biome lists. No Stony Peaks terrain remains.
- Eligible climate provinces that would have become Taiga receive a fixed,
  seed-based 50/50 decision: Taiga or Snowy Plains. The decision is made per
  province (not per block or chunk), preserving sensible biome shapes.
- Snowy Plains have snow-covered surfaces, ordinary cold rolling elevations,
  no natural trees, and rabbits rather than mountain goats as passive wildlife.
- Legacy customized-world Stony Peaks settings are mapped to Snowy Plains
  settings, including the old flat-world biome selection.

LOW MOUNTAIN TREELINE
- Low Mountain biomes occasionally produce spruce trees on their lower slopes.
  Planting chance decreases gradually from 3.5% at Y<=103 to zero at Y>=122;
  Mid/High Mountains and Snowy Plains remain treeless. The tree shapes use the
  existing Taiga spruce trunk/leaves and randomized planting windows.
- Skips the biome-canopy footprint check when a planting position is not
  otherwise eligible, reducing unnecessary work in most chunks.

RETAINED FEATURES
- Independent docile/hostile mob caps and all recent multiplayer, portal,
  mansion, Alt Maze, stair, cabin, seed-map, and relay fixes remain intact.
- Save format 12, dedicated-server protocol 16, and relay protocol 1 remain.
  The client, map, and server all use the restored heights.

IMPORTANT WORLD BACKUPS
- Back up all saves before opening them in this rollback. Worlds built in the
  256-layer edition may have player positions, custom blocks, or structures at
  displayed Y>=200 that no longer fit inside the active world. Such edits may
  remain in save data but cannot be reached in the reduced-height world.
- World-generation differences affect previously unedited/generated terrain;
  visiting old and new chunks can expose terrain seams. For the most accurate
  assessment of the restored performance and biomes, create a new test world.

TESTS
- Syntax checks for JS/Python, previous structure/relay/portal/mob-cap tests,
  and game/seed-map biome/height agreement across 3 seeds. Snowy Plains made up
  51% of sampled Taiga+Snowy Plains provinces in the deterministic sample.
- The original mountain functions match the last pre-lag release.
- Interactive WebGL/FPS profiling was not performed; perceived frame-rate
  improvement is not guaranteed by the source rollback alone.

============================================================================
HISTORICAL CHANGELOG (some later superseded features described below)
============================================================================

MellorCraft 1.8.3 — Terrain Performance, Stair and Cabin Hotfix
================================================================

Changes relative to the preceding 1.8.3 Mobs/Mountains build
--------------------------------------------------------------

PERFORMANCE
- The new mountain-range terrain routines were evaluating expensive octave
  noise for peaks and ridges far outside their influence. They now use
  precomputed range bounds and cheap distance checks to skip irrelevant
  noise calls; peak trigonometry is precomputed and intermediate allocations
  are reduced. The same optimized functions are used by chunk workers and
  the seed map. Memory retained for the per-column mountain cache is bounded
  more tightly (90,000 versus 220,000 positions).
- In a Node.js 22 benchmark generating biome and height data for 9,216
  terrain columns near a fixed seed, the previous version took about
  0.86–0.95 s, and this update took about 0.38 s (~2.2–2.5x faster).
  This is an algorithm benchmark, not an FPS measurement. Interactive
  WebGL testing with different render distances/hardware is still needed.

WORLD GENERATION
- Mountain-range activation probability is reduced from 38% to 26% per
  candidate planning cell. Mountain chains, unclipped summits and Stony
  Peaks height generation remain supported; the game and seed map agree.
- Forest weighting is slightly higher, without increasing the approved
  88-block climate-province size. The extra promotion of eligible temperate
  plains changes from 11.5% to 17%. Tree placement in Forest biome goes
  from 8% to 9.2%, and Flower Forest from 5.5% to 6.2%.

STAIR MOVEMENT
- Auto-step detection now tests the whole player's collision footprint,
  including stair blocks in an adjacent cell. This makes the raised halves
  of all four directional stair blocks eligible for stepping when approached
  along a correctly aligned continuous stair flight.
- Automatic climbing for stairs is limited to one block above feet, rather
  than allowing accidental 1.5-block climbs beside stairs.

SNOW CABINS
- Closed the triangular gaps underneath both gable ends of cabin roofs
  with matching wood planks. Natural cabin generation and /place cabin
  both receive the fix; the one doorway and glass windows remain.

COMPATIBILITY / TESTING
- Version remains 1.8.3. No change to save format 12, dedicated protocol 16
  or relay protocol 1. Alt Maze floor plans and the 256-layer world are retained.
- Tests include generation, biome/seed-map parity, structure layouts,
  companion dimension portals, multiplayer saves, dedicated-server mob caps,
  targeted four-direction stair and cabin-gable checks, and syntax checks.
- Back up existing worlds. Regenerated terrain can reflect changed mountain
  and forest distribution; saved block edits remain unchanged.
- Full interactive desktop/mobile performance testing was not performed.

===========================================================================

MellorCraft 1.8.3 — Separate mob caps, mountain ranges & taller world
======================================================================

Changes relative to the preceding 1.8.3 Forest/Structures/Portals release
---------------------------------------------------------------------------

MOB SPAWNING
- Replaced the single shared mob population limit with two independent,
  per-dimension caps: docileCap (18 by default) and hostileCap (12 by default).
  Animals cannot consume the slots reserved for enemies, including at night
  when players remain stationary. Bosses are exempt from these ordinary caps.
- Create/Edit World now has separate Docile Mob Cap and Hostile Mob Cap fields.
  Operators can change them with /gamerule docileCap <0-200> and
  /gamerule hostileCap <0-200>, including from the dedicated server console.
  The old /mobcap shortcut now explains the replacement commands.
- Authoritative dedicated servers and browser-hosted relay worlds enforce
  the appropriate cap for each mob category; night and cave spawn attempts
  no longer test the combined population. Peaceful still disallows enemies.
- For worlds saved with the old mobCap rule, the previous limit is migrated
  to 60% docile and 40% hostile (30 -> 18/12). Mob count defaults preserve
  a similar total while ensuring independent capacity.

MOUNTAINS / TERRAIN HEIGHT
- Normal-world mountains now favor connected chains of 3-5 distinct summits
  instead of isolated peaks, joined by irregular ridges, without changing
  the approved 88-block climate-province scale or 420-block range grid.
- Increased the Overworld voxel allocation from 248 to 256 layers. The
  displayed-Y origin stays +48 internal layers, retaining Y=-48 bedrock
  and providing internal layers through Y=255 (displayed Y=207). The
  generator safely limits natural terrain to displayed Y=205 so the sky
  remains above the tallest mountain. Existing saved block coordinates
  are unchanged; old 248-stride legacy chunk-edits are still understood.
- Removed forced flat ceilings at 130, 160, and 190 on mountain biomes.
  Individual summits may rise past displayed Y=190 with irregular crests.
- Stony Peaks have their own jagged 100-145 elevation profile with smooth
  transitions at cold-dry province boundaries, no longer flat at low Y.
  The updated seed map matches the client height algorithm.

TESTING & COMPATIBILITY
- JavaScript/Python syntax, existing biome/maze/mansion/seed-map/relay/
  structure-command/portal tests, independent cap enforcement, terrain
  summits, and client/seed-map equality regression checks are included.
- Release remains version 1.8.3, save format 12, dedicated protocol 16,
  relay protocol 1. No changes to approved Alt Maze layouts.
- Backup existing worlds before upgrading: regenerated unmodified terrain
  may change near mountain ranges and Stony Peaks, but saved block edits
  retain their coordinates. Taller chunks add modest memory cost.
- Interactive WebGL gameplay/multiplayer load testing was not performed.

============================================================================

MellorCraft 1.8.3 — Forest frequency, every structure command, linked portals
============================================================================

Changes relative to MellorCraft 1.8.3 Stair/Biome/Mansion Fix
---------------------------------------------------------------

FORESTS
- Forest and Flower Forest provinces now occur approximately twice as often in
  the default Normal world generator. Across five sampled seeds, forest province
  frequency was about 2.0x the preceding build. Seed map and game use identical
  province selection. The province grid size remains 88 blocks; forests are NOT
  made larger by scaling up the biome map.
- Customized world biome weights are not overridden. The mansion spawning chance
  is unchanged; more qualifying forest terrain should yield more mansions.

STRUCTURE COMMANDS
- /locate <structure> finds the nearest procedurally generated structure using
  the same deterministic seed, biome restrictions, and structure-priority rules
  as terrain generation. It reports X/Y/Z, dimension, and horizontal distance.
- /place <structure> builds that structure at/near the player's position using
  the corresponding procedural materials and room layouts. Use these names:
    mansion, outpost, cabin, dungeon, alt_maze, boss_shrine, boss_arena
  Aliases such as "maze", "shrine", and "arena" are also accepted.
- Normal/Overworld only: mansion, outpost, cabin, dungeon.
  Timeless Void only: alt_maze, boss_shrine. Boss Dimension only: boss_arena.
  /locate can search for a structure in any of the three dimensions.
- Both commands remain operator commands, like the original /place.
  They are entered in the game's chat command interface, not in the separate
  Python dedicated-server console.
- Large manual placements send shared block edits in bounded batches of 256
  instead of transmitting tens of thousands of separate WebSocket messages.

PAIRED PORTAL REMOVAL
- When an Overworld portal is used to create/activate a counterpart in the
  Timeless Void, its two actual positions are registered as a portal pair.
  This accounts for a different Alt-Dimension Y (normally 30) and any displaced
  X/Z required to create a safe landing.
- Mining either member removes the registered counterpart without awarding
  another portal item. Removal is enforced in local/browser-hosted worlds and
  by the dedicated Python server (including block-batch updates).
- Portal associations are saved in browser-world and dedicated-server saves,
  without changing format version 12 or dedicated/relay protocol versions.
- Existing portal blocks from older worlds do not automatically acquire an
  association based solely on matching coordinates. Use/traverse the portal
  once in this build to register its pair. Independently placed, unlinked
  portal blocks are never removed just because X/Z happens to match.

VALIDATION
- The prior 1.8.3 biome, maze, mansion, seed-map, torch-lighting, multiplayer,
  and relay regression suites pass.
- Added /place and /locate tests for all seven structure types, plus checks for
  bounded multiplayer structure batches.
- Added dedicated-server portal tests for persistence, mining from either
  dimension, and preserving unrelated blocks with matching coordinates.
- Interactive desktop/mobile WebGL gameplay has not been fully playtested here.

WORLD COMPATIBILITY
- Version stays 1.8.3; save format remains 12, dedicated protocol 16, and
  relay protocol 1. Back up worlds before upgrading. Only procedurally
  regenerated (unmodified) terrain receives the new forest distribution.


============================================================================

MellorCraft v1.8.3 — Stair, Biome, Mansion & Spectator Corrections
====================================================================

THIS PACKAGE REMAINS VERSION 1.8.3

- Alt Maze stairwell: The second-floor atrium now has a continuous solid
  floor, except for intentional openings around the lower stair flight.
  Both wooden stair flights rise from the floor surface and end at exactly
  the same height as their next-floor landings; support blocks and clear
  headroom are maintained. Player movement detects rising stair blocks at
  feet level or one voxel higher and can step up without pressing Jump.
- Smaller biomes: The jittered climate-province grid is 88 blocks (was 175)
  and climate noise now varies at a higher, equally scaled X/Z frequency.
  Mountain regions shrink from a 680-block to a 420-block planning grid,
  with correspondingly shorter chains and smaller individual peaks.
  Both the game and seed map use the same generation equations. Related
  biome climates remain grouped; taiga remains present and desert strips
  are avoided in sampled seeds.
- Spectator privacy: Players in spectator gamemode do not appear in
  in-world nametags or the multiplayer locator bar.
- Two-story mansions: The mansion retains its original 12-block height
  (local Y=0 through 11). A complete floor at local Y=6 separates the two
  accessible stories. A supported wooden stair flight reaches the upper
  landing. Each floor contains EXACTLY 15 ore display blocks, chosen from
  room interiors independently of the stairwell, atrium, or corridors.
  Each story has independently randomized side corridors; only the
  central hallway follows one of the three established patterns.
- All previous 1.8.3 changes are included: hidden 9-Mellorite maze room,
  faster seed map and filters, secure relay guest saves, dimmer torches,
  WebSocket scheme selectors, and the earlier multiplayer fixes.

TESTING

    node tests/test_183_structures.js
    node tests/test_stairs_mansions_spectator.js
    node tests/test_alt_maze_chunks.js
    node tests/test_biomes_hotfix.js
    node tests/test_183.js
    node tests/test_seed_map_runtime.js
    node tests/test_torch_floor_lighting.js
    python tests/test_183_backend.py

Automated checks cover 225 seeded mansion/maze layouts, both sets of stairs,
15 ores on each of two mansion floors, 9 intact special-room ores, and
spectator nametag/locator suppression. A full browser/WebGL playtest was
not performed; manually verify feel of stair movement on desktop and mobile.

Compatibility: Still save format 12, dedicated protocol 16 and relay protocol
1. Changed biomes, mountain sizes, and structure generation affect newly
regenerated terrain. Existing saved block edits may preserve older portions.
Back up existing worlds before upgrading.

-------------------------------------------------------------------------------

MellorCraft 1.8.3 — Alt Maze & Torch Lighting Update
===================================================

LATEST FIXES (VERSION REMAINS 1.8.3)

- Fixed overlapping Alt Mazes. Their centers now have enough separation that
  the 41x41 structures and front approach cannot overwrite another maze's
  hidden Mellorite chamber. This changes maze positions in newly generated
  Alt Dimension terrain for the same seed.
- The three possible layouts apply ONLY to the main, centered hallway spine
  and branch. Outside that core, mansion hallways are randomly routed per
  building; Alt Maze side corridors are independently randomized per floor.
  Seeded spanning routes ensure all ordinary rooms remain connected.
- The secret nine-Mellorite-ore room can now spawn in many different outer
  rooms and on any of the three floors, rather than only four corners. Its
  choice is made before random corridors are carved, and chamber blocks take
  priority over hallways and decorations during generation. The chamber
  remains sealed (no connecting doorway), as previously requested; mine
  through its walls to enter. It contains all nine intact ore blocks and no
  torches/crafting tables/chests.
- Corrected torch light selection in multi-level buildings. The old selection
  only considered horizontal coordinates and could spend all four shader
  lights on a different floor. Lighting now favors torches near the player's
  elevation and location, regardless of the material underneath the torch.
  The four-point-light WebGL budget is retained for performance.
- Updated the seed map's Alt Maze markers and Mellorite chamber tooltips to
  match the revised world generation and room placement.
- Version stays 1.8.3. Save format 12 and both multiplayer protocols remain
  unchanged. Existing saved terrain edits may preserve older structures;
  back up the world and test freshly generated terrain for the new layout.

TESTS

    node tests/test_183_structures.js
    node tests/test_alt_maze_chunks.js
    node tests/test_torch_floor_lighting.js
    node tests/test_seed_map_runtime.js
    node tests/test_183.js
    node tests/test_biomes_hotfix.js
    python tests/test_183_backend.py
    python -m py_compile mellorcraft_relay.py mellorcraft_server.py

225 structure layouts and randomized routing connectivity were checked;
seven actual generated Alt Mazes retained nine special-room ores each, and
62 seed-map markers matched game-side maze/chamber positions. WebGL rendering
has not been manually playtested, so lighting quality should be checked
in-game on both desktop and mobile.

-------------------------------------------------------------------------------

MellorCraft 1.8.3 — Biome and Structure Corrections
====================================================

LATEST FIXES (VERSION REMAINS 1.8.3)

- Reduced the normal-world climate province size from 380 to 175 blocks and
  adjusted the climate frequencies/edge warp together. This keeps broad,
  irregular biome shapes and climate-related neighbors without the oversized
  patches from the previous 1.8.3 build. The seed map uses identical equations.
- Added the missing name for the Chest block (ID 23). Decorative chests in
  mansions and Alt Mazes no longer display as "Unknown" when targeted/collected.
- Mansions and Alt Mazes now each have exactly three deterministic central
  hallway configurations. Main doors and atriums stay centered; side passages
  are selected per structure seed, preserving room and ore display positions.
- Rebuilt the Alt Maze's hidden 9-Mellorite-ore room as an actual sealed 3x3
  ore chamber on one of three floors. It is chosen outside hallways, atrium,
  stairwells, and landings; its walls have no doorway and the room has no
  torches, crafting tables, or chests to replace the nine ores.
- Replaced the two solid-brick Alt Maze stair flights with directional oak
  stair blocks and continuous supporting masonry. Each ascends toward a solid
  upper-level landing; headroom remains clear.
- Centered the maze's entrance corridor at X 19–21 and removed decorations
  that obstructed the atrium's centerline.
- Added a level, cleared entrance apron beyond the front doorway of both
  buildings. During terrain generation this overrides dirt/stone/Timeless Void
  cave material immediately outside the front door; the forced mansion
  placement command uses the same doorway geometry.
- No version, saved-world format, dedicated multiplayer protocol, or relay
  protocol increase. Prior 1.8.3 lighting, network, and seed-map speed/features
  are retained. Changes affect newly generated/unmodified structure areas;
  back up saved worlds before upgrading.

VALIDATION

    node tests/test_183_structures.js
    node tests/test_seed_map_runtime.js
    node tests/test_183.js
    node tests/test_biomes_hotfix.js
    python tests/test_183_backend.py
    python -m py_compile mellorcraft_server.py mellorcraft_relay.py

Geometry tests cover 25 structure coordinate seeds (all three variants),
closed ore-room walls, nine intact ore blocks, named/valid decoration blocks,
stair supports/landings, and carved exterior entrances. Biome climate checks
run for five world seeds. Interactive gameplay and visual browser testing have
not been completed. Existing saved edits may preserve portions of older
structures, so a new seed/unmodified area is best for verifying layouts.

-------------------------------------------------------------------------------

MellorCraft v1.8.3 — Lighting, Fast Seed Map, Atriums & Stairwells
====================================================================

CHANGES FROM THE v1.8.3 BIOME HOTFIX

- Torches are substantially dimmer, with smaller radii and lower light power
  in both normal and lightweight-shader rendering. Shader settings now start
  with 85% torch brightness and 80% range, and old saved brightness values are
  capped at the new limits. Existing placed torches need not be replaced.
- The Timeless Void has increased ambient visibility (0.20 to 0.34), somewhat
  brighter biome-colored fog/sky, and lighter long-distance fog (0.04 to 0.024
  with shaders enabled). It remains intentionally gloomy.
- Seed map zoom and pan now use adaptive-resolution, batched terrain sampling;
  painted map pixels are drawn through an image raster rather than one canvas
  rectangle per 4 pixels. The interface stays responsive as the map is drawn,
  and playing the weather animation reuses the base terrain raster.
- Open "Filter biomes & structures" on the seed map to turn *each* Overworld
  and Alt biome or each structure marker on/off, plus Show All/Hide All controls.
  Dungeons are now an optional surface-map marker (off by default because
  their underground locations can be expensive to calculate). Hidden biomes
  appear charcoal. Distant zoom levels intentionally use coarser map samples.
- In multiplayer's relay join pane, ws:// vs wss:// is labeled more clearly;
  pasting a full address automatically selects the matching scheme. The
  dropdown was present in v1.8.3; it is now more discoverable.
- Procedural mansions now have a *single* 3-block-wide front doorway leading
  through a foyer to a larger central atrium. A deterministic branching network
  of room doors and extra loops ensures all reachable ore rooms connect to
  the atrium. Mansions now have skylights, pillars, warm lamps, chests, tables,
  and ore displays. /place mansion uses the same geometry as world generation.
- Procedural Alt Mazes now have one front doorway, a central atrium, varied
  connected room routes, galleries at upper levels and exactly two supported,
  straight stair flights in fixed atrium locations (ground->second and
  second->third). Random floating stair rooms are gone. Loot is kept outside
  the atrium and the seed-map hint matches the relocated special ore room.
- Chunk workers generate the same mansion and Alt Maze layout functions as
  the main thread, so edges and rooms stay consistent across chunk borders.
- Existing v1.8.3 world format (12), dedicated multiplayer protocol (16), and
  relay protocol (1) remain unchanged. Saves should be backed up before any
  upgrade; regenerated unedited areas containing structures will use the new
  layouts, while saved player block edits remain authoritative.

TESTS

    node tests/test_183_structures.js
    node tests/test_seed_map_runtime.js
    node tests/test_183.js
    node tests/test_biomes_hotfix.js
    python tests/test_183_backend.py
    python -m py_compile mellorcraft_server.py mellorcraft_relay.py

Automated syntax, geometry, connectivity, map-runtime (mock canvas), and prior
multiplayer regression tests pass. Real interactive browser/WebGL and mobile
playtesting were not possible in this environment. The exact wall-clock
speedup in your browser is not yet measured; coarser zoom levels involve far
fewer biome samples, and each frame has a time budget.

-------------------------------------------------------------------------------

MellorCraft v1.8.3 — Biome/ESP Hotfix
=======================================

- Replaced narrow continuous-temperature/moisture biome bands in NORMAL worlds
  with jittered, irregular 380-block climate provinces. A province's entire
  biome is chosen using temperature and moisture sampled at its center. This
  produces substantial patches of desert rather than many long narrow strips.
- Related climate conditions drive neighboring province assignments: deserts
  favor nearby savanna/badlands, with cool forest/plains transitions before
  taiga. Taiga remains limited to cold, sufficiently moist provinces.
- The seed map uses the exact same province selection as the game and terrain
  generation workers. Custom and flat world generation remain unchanged.
- Climate sampling and compatibility rules were checked on five large seeded
  regions: no tested desert regions had extreme long/thin shapes or directly
  touched jungle, forest, taiga, or stony peaks. This is a sampled regression,
  not a guarantee for every possible seed and world location.
- Removed ESP entirely: the /esp command, help entry, toggle variable, and
  through-distance rendering override no longer exist in the shipped client.
  As with any browser game, a modified client cannot be fully prevented from
  implementing its own visualization cheats.
- Existing normal worlds retain the same seed and saved block edits, but
  unedited regenerated terrain may show new biome/vegetation boundaries. Back
  up worlds before upgrading; for seamless new terrain, start a new world.
- Save format 12 and both multiplayer protocols stay unchanged. No Python
  backend changes were needed for these client-side fixes.

New regression suite: `node tests/test_biomes_hotfix.js`, plus the existing
`node tests/test_183.js` and `python tests/test_183_backend.py`.

MellorCraft v1.8.3 — Biome, Save, Mob Spawning, Death and WebSocket Fixes
===============================================================================

Changes from v1.8.2
-------------------

- Flowers and saplings no longer brown grass merely by occupying the block above
  it; solid blocks continue to block grass and exposed dirt can still spread.
- Normal-world biome climate sampling now includes two-dimensional coordinate
  warping and a second local moisture layer, reducing artificial stripe-shaped
  deserts/badlands/savannas. Taiga has a stricter cold/moisture requirement,
  making it less prevalent. The bundled seed map uses matching biome rules.
- Browser-hosted relay worlds save each guest's inventory, position, equipment,
  health, hunger, and respawn settings. Guest saves are keyed by a secret 256-bit
  browser-held token, rather than claimable by entering someone else's username.
  Guest profiles are written on disconnect and on normal host autosaves.
- The initial 1.8.3 release allowed /help, /rd and /esp for non-operators;
  /esp is removed in the subsequent biome hotfix. World-affecting/admin commands
  remain permission-gated.
- Nighttime mob spawning now periodically checks for too few hostile mobs near
  stationary players. If the mob cap is filled with passive mobs, only a distant
  passive mob may be replaced to reserve a hostile spawn slot. Peaceful mode,
  the mob-spawning game rule and mob cap remain respected.
- Death is saved immediately for browser-hosted worlds and sent immediately to
  multiplayer hosts. Reconnecting restores zero health and a death screen;
  player_update messages cannot turn dead players alive. Only the normal
  respawn action restores health (unless the world uses Hardcore).
- Dedicated server and relay join/host screens now each offer ws:// or wss://.
  The scheme selection is saved. Explicit ws:// or wss:// typed into an address
  continues to take precedence. HTTPS pages default to wss://.

Compatibility and important usage notes
---------------------------------------

- Save format remains 12, the dedicated multiplayer protocol remains 16, and
  relay protocol remains 1. Use the 1.8.3 client with the 1.8.3 relay because
  relay guests must provide a valid persistent identity token.
- Back up world saves before upgrading. Changed biome rules affect newly
  generated/regenerated terrain in existing seeds; previously saved block edits
  are retained. You might see biome changes at old/new generation boundaries.
- Each relay guest's identity token is stored in localStorage in the browser,
  scoped to the relay address, world name/seed, and username. Returning guests
  should use the same browser profile, relay address, world, and username.
  Clearing browser storage or changing device may lose access to the old guest
  character. This is a bearer identity, not a password-protected account, so
  protect browser storage and prefer encrypted wss:// for remote servers.
- Existing anonymous v1.8.2 relay guest profiles were not saved and cannot
  be recovered retroactively. Any older unverified username-only profiles are
  deliberately not attached to newly authenticated relay guests.
- wss:// requires a TLS-enabled WebSocket endpoint, often via a reverse proxy;
  simply switching the selector does not enable TLS in the Python scripts.
  On HTTPS pages, browsers generally block unencrypted ws:// mixed content.
- Hardcore death restrictions do not convert a password-free relay into a
  durable account service; players with a different new identity are treated
  as new players. Dedicated server logins remain password-authenticated.

Tests
-----

- `node tests/test_183.js` covers soil ticks, game/seed-map biome parity,
  websocket schemes, unprivileged /rd, saved guest identities, death snapshots,
  and stationary-player nighttime hostile replenishment.
- `python tests/test_183_backend.py` covers relay handshake/token forwarding,
  guest messaging, dedicated death preservation, and legitimate respawn.
- The inline HTML JavaScript passes Node syntax checks and both Python
  backends pass Python syntax checks. An interactive browser/WebGL smoke test
  could not be completed in the restricted test-browser environment, so
  gameplay on desktop and mobile should still receive a hands-on playtest.

To run
------

- Dedicated server: `python mellorcraft_server.py` (serves HTTP 8000 and WebSocket 8765).
- Relay: `python mellorcraft_relay.py --port 8000`.
- Standalone game: open `mellorcraft.html` directly, or serve the folder and open
  `index.html` to play or download the client.

===============================================================================

Previous release history follows.

MellorCraft v1.8.2 — Grass Growth, Universal Pause Settings, Relay Identities + Host Console
=======================================================================================

Changes from the attached v1.8.1 release:

GRASS AND DIRT
- Grass blocks with a block directly above them slowly change to dirt. Any non-air block directly above counts as cover.
- Exposed dirt can slowly become grass if a neighboring horizontal block is grass at the same elevation.
- Random ticks run only in actively loaded areas around players, with extra attention to blocks players recently placed/removed. Unloaded areas do not advance until loaded.
- Conversion uses normal block edits: terrain remesh, world autosave, shared relay sync and dedicated-server block synchronization all receive the changes.
- Dedicated servers rely on connected clients to produce these random soil ticks, since dedicated server stores block edits and clients generate procedural terrain. Ticks occur near active players, not in empty chunks.

SETTINGS
- Look sensitivity, render distance, master volume, FOV, and resolution are all editable in the in-game pause menu on desktop and mobile.
- Resolution now scales the WebGL framebuffer on both desktop and mobile (40–100%), and persists locally as `mellorcraftMobileResolution`; mobile adaptive scaling remains in effect below the selected cap.
- Texture and shader controls remain accessible when paused.

RELAY IDENTITY / AUTHORIZATION
- Relay guests explicitly enter a username and pick one of six skins before joining. Usernames are 1–20 A–Z, 0–9, underscore or hyphen; names already in use are rejected case-insensitively.
- No relay password or account database is created. Relay guests enter a fresh session; for safety, older profile inventories and permanent operator privileges cannot be claimed merely by reusing an unauthenticated username. Dedicated-server login/password behavior is unchanged.
- The browser world host's chat supports relay console-only commands: /help, /save, /stop, /seed, /list, /ops, /op, /deop, /ban, /kill, /mobs, /gamerule, /gamemode <player> <mode>, and /tp <player> <target> or <x> <y> <z> <dimension 1-3>.
- /stop saves and closes only the host's shared world, without stopping the relay process (which may be serving other worlds). /account intentionally reports that password-free relay sessions have no accounts.
- Console-only management actions are authorized against the actual host connection, not against a username. Guests cannot spoof host commands or automatically get operator rights by using old saved names. Operators explicitly designated by the host may still use the pre-existing /ban and /kill commands.
- Dedicated server remains on protocol 16; relay protocol stays 1, with identity validation on relay join. Use the updated client together with the updated relay for consistent behavior.

TESTING
- Run `python mellorcraft_relay.py --port 8000` for hosted browser worlds, OR `python mellorcraft_server.py` for a dedicated server.
- Open `index.html` using the same web server/static host as before, or open the standalone `mellorcraft.html` directly.
- Back up worlds and other files before upgrading; v1.8.2 retains v1.8.1 format 12 and world-height layout.

===============================================================================

MellorCraft v1.8.1 — Terrain fidelity and colored beds correction
=================================================================

This v1.8.1 package supersedes the previous v1.8.1 playtest ZIP. Use the matching
mellorcraft.html and mellorcraft_server.py; dedicated protocol is **16**.

RESTORED SURFACE AND ACTUAL DEEPER UNDERGROUND
- Normal Overworld surface heights use the original v1.8.0 getHeight() algorithm,
  with no additional v1.8.1 rolling/cliff terms. Existing original mountain shapes
  and elevation differences remain unchanged. The original surface Y appears in
  the HUD and in /tp. Custom/flat heights also keep their old displayed levels.
- The Overworld now has 248 internal voxel layers instead of 200. There are 48
  additional layers below old Y=0 (down to displayed Y=-48, where bedrock lies).
  The engine translates Overworld internal voxel Y to displayed Y by subtracting 48.
  Other dimensions retain their existing coordinate systems.
- Only the underground is extended with additional caves and chambers. Ravine
  placement and displayed ravine depth have not been extended.
- Deepslate (block 157) transitions gradually from rare near displayed Y=20,
  to common in deeper underground and fully replacing ordinary stone at Y=-32.
  Ore generation still takes priority. Rare granite and diorite can appear only
  where there is not deepslate; andesite, limestone, and slate no longer generate.
- Retains background chunk workers and adds memoization of large underground
  cavern region parameters. Internal column storage increases by 24% (200 to 248
  voxels high), so actual peak memory and worldgen cost may rise modestly.

BEDS AND RESPAWN
- Replaced craftable respawn blocks with 11 colored beds: red, white, black,
  gray, light gray, brown, pink, orange, yellow, blue, and purple.
- Craft a bed using exactly 3 oak planks + 3 wool pieces all of one color.
  Both sheep-dropped wool items and placed wool blocks are accepted.
- Each generated snow cabin contains one deterministically chosen colored bed,
  rather than an ore block; existing cabin exterior improvements remain.
- Beds have partial-height geometry and collision. Neighboring wall faces are
  preserved when meshing beside beds, eliminating missing-wall see-through gaps.
- Right-click/tap a placed bed to set your respawn location. Respawns use a
  free adjacent floor spot when available and do not remove overhead walls.
- Legacy placed respawn blocks and saved inventory items convert to red beds.

SAVE MIGRATION & COMPATIBILITY
- Save format version is now 12. Older Overworld blocks, players, mob positions,
  drops, furnaces and respawn points are translated upward by 48 internal voxels
  *once*, leaving their displayed physical elevations unchanged. Alt/Boss
  dimension locations remain untouched. Existing blocks/structures are preserved.
- Back up all worlds and player files before upgrading; reverting to the old
  200-layer client/server after migration is not supported without backups.
- Do not combine the new client with previous v1.8.1 servers: protocol 16 is
  required on both ends.

OTHER v1.8.1 PLAYTEST CHANGES RETAINED
- Bounded 3–10-block iron veins, less coal, stronger coal texture contrast,
  high-Y diamonds rarer; ore overrides granite and diorite.
- Fixed furnace lighting and returned contents on breaking; torch lighting is
  continuous in loaded terrain; cave mobs and dungeon spawners are improved.
- Corrected long-distance teleports, faster sprint-flight, stronger Mellorite boss,
  downhill mob movement and mobile crafting Close behavior.
- Fewer outposts/cabins, adjusted mansion frequency, detailed snow cabins and
  directional half-block oak stairs.

VALIDATION
- Node syntax check for extracted inline JavaScript; Python syntax checks.
- tests/test_worker_generation.js checks 169 sampled normal-world surface heights
  against the original v1.8.0 height function, generates a full new-world chunk,
  and checks real negative-Y caverns, deepslate and cabin-bed color selection.
- tests/test_beds.js checks 11 recipes and wall-face culling protection.
- tests/test_save_migration.py checks one-time legacy save conversion on server.
- Additional terrain, ore, furnace and boss regression tests are included.
- An interactive browser gameplay smoke test could not run in this environment;
  mobile camera and multiplayer movement merit a follow-up hands-on check.

------------------------------------------------------------------------

MellorCraft v1.8.0 server account-lock + username rules
========================================================
- Server operators can now lock public account creation. The setting persists in `server_accounts.json` and can be changed live with `/account signup off` or `/account signup on`.
- Starting the dedicated server with `--lock-account-creation` immediately locks public Sign Up and persists that setting.
- When public signup is locked, Sign Up requests are rejected server-side even from modified clients. The normal client also reads `/server-policy.json`, hides the Sign Up button, and explains that the operator must create the account.
- Added `/account create <username> <password> <skin>` so the server console can create accounts directly. Valid skins are `steve`, `alex`, `mellorite`, `ember`, `frost`, and `forest`.
- `/account list` now also reports whether public account creation is enabled or locked. Existing `/account setpassword` and `/account delete` commands remain available.
- Dedicated-server usernames now allow only 1-20 letters, numbers, underscores, or hyphens. Spaces are rejected by both the client UI and the authoritative server validation.
- Account-file format advances to version 2 only to persist the signup policy; existing version-1 account files load with public signup enabled by default. Multiplayer protocol remains 13.

MellorCraft v1.8.0 HTTP connection-reset traceback fix
======================================================
- The dedicated HTTP server now suppresses expected client-disconnect socket exceptions such as `ConnectionResetError`, `BrokenPipeError`, `ConnectionAbortedError`, and Windows socket reset/abort codes (including WinError 10054) that can occur when a browser or Internet scanner closes a connection while `mellorcraft.html` is still being transmitted.
- These routine disconnects no longer produce multi-line `socketserver.py` tracebacks in the operator console.
- Genuine unexpected HTTP-server exceptions are still passed to Python's normal error handler and remain visible.
- With `--http-log`, routine disconnects are represented by a single concise line instead of a traceback. Quiet mode remains the default.
- This is server-only; multiplayer protocol remains 13 and no client update is required.

MellorCraft v1.8.0 quiet HTTP logging / scanner-noise fix
=========================================================
- The dedicated server's static HTTP endpoint is now quiet by default. Generic Internet scanner traffic, malformed HTTP/TLS/RDP probes, favicon requests, unsupported methods, and routine GET/HEAD request lines no longer flood or interrupt the live operator console.
- MellorCraft-specific logs remain visible, including WebSocket connection attempts, authenticated joins/leaves, `Client ready`, startup failures, commands, saves, and shutdowns.
- Added `--http-log` to restore verbose HTTP request/error logging when troubleshooting the web server.
- `/favicon.ico` returns 204 instead of a noisy 404. OPTIONS probes receive a harmless 204 response and POST receives 405 without the default Python 501 noise.
- The HTTP response banner no longer advertises the host Python version.
- This is a server-only logging/hardening change; dedicated multiplayer remains protocol 13 and existing v1.8.0 clients remain compatible.

MellorCraft v1.8.0 server disconnect + /tp fix
================================================

Dropped-item floor collision hotfix
----------------------------------
- Dropped block and mob items now use swept floor collision so delayed frames/server ticks cannot tunnel an item through the supporting block.
- Mob hosts report the support surface beneath mobs; mob loot uses that support height when it spawns.
- Browser-hosted worlds and dedicated servers apply the same anti-tunneling behavior.

- Dedicated multiplayer now uses protocol 13 so the corrected client/server pair cannot silently mix with protocol-12 builds.
- Fixed dedicated-server `/tp`: the client now handles the server's authoritative `teleport_position` packet, updates dimension/coordinates immediately, clears velocity and knockback, resets nearby chunk streaming, and applies a short portal cooldown so the player's next movement update cannot snap the teleport back.
- `/stop` now broadcasts a `server_shutdown` message after saving and before WebSocket/HTTP shutdown. Connected clients immediately leave gameplay and return to the server login screen.
- Unexpected dedicated-server WebSocket loss uses the same in-page exit path. Server-hosted clients no longer try to reload `http://SERVER-IP:8000` after that HTTP server has already gone offline.
- Leaving a stopped/offline server clears movement/touch/mining state, releases pointer lock, hides gameplay menus, removes remote-player state, and disables mobile controls while preserving the already-loaded login page for a later reconnect.
- The main render loop is now single-instance and idles while no world is active, allowing a player to reconnect after a server restart without creating duplicate animation loops.

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
