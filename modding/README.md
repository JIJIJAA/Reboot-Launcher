# Custom cosmetics for Reboot Launcher

Working notes and tooling for getting a custom character into a Fortnite
S0-14 private server. The running example is Toy Chica (FNaF), but nothing
here is specific to her.

## The short version

Granting a cosmetic is trivial. Making the client *render* it is the project.

The backend already hands out every stock cosmetic — 1901 characters, 2196
emotes, 1136 pickaxes — from `auth_backend/profiles/athena.json`. Adding one
more entry takes seconds (`add_custom_cosmetic.py` does it). But a template
ID the client cannot resolve to a cooked asset shows up as an invisible or
default character. Everything hard lives on the client side.

## What is in here

| File | What it does |
| --- | --- |
| `blender/build_toychica_blockout.py` | Generates a rigged proxy character, exports FBX + glTF |
| `blender/render_preview.py` | Renders turnarounds with Cycles on CPU (no GPU needed) |
| `add_custom_cosmetic.py` | Registers a template ID in **both** copies of the Athena profile |

Run the generator with Blender-as-a-module, no GUI required:

```bash
pip install bpy
python3 blender/build_toychica_blockout.py
```

## Two traps specific to this repo

**The profile is duplicated.** `auth_backend/profiles/athena.json` and
`gui/assets/backend/profiles/athena.json` are byte-identical. The GUI bundles
its own copy as a Flutter asset, so patching only the first one leaves the
launcher serving a stale profile with no visible error. `add_custom_cosmetic.py`
always writes both.

**The launcher rejects custom paks.** `common/lib/src/game/game_constants.dart`
lists `"Pak chunk signature verification failed!"` in `kCorruptedBuildErrors`,
and `game_metadata.dart` turns any match into `onBuildCorrupted()`. That is
exactly the line Fortnite prints when it mounts a pak whose signature does not
match, i.e. every custom pak. The launcher will abort your build the moment
your mod loads. This needs a "modding mode" that exempts that one string
before any custom pak can be tested.

## How custom a "custom skin" is

Effort spans two orders of magnitude depending on which of these you mean:

| Level | What it is | Needs cooking? | Rough effort |
| --- | --- | --- | --- |
| 0 | Unlock everything | no | already done |
| 1 | Swap: skin A uses skin B's assets | no | days |
| 2 | Retexture an existing skin | no, repack only | 1-3 weeks |
| 3 | New CID mixing existing CharacterParts | **yes** | 1-2 months |
| 4 | Fully original model | **yes** | months |

The hard boundary is between 2 and 3. Cooking new assets requires a UE4
editor matching the build's engine version (S0-14 is roughly UE 4.20-4.26).
Plenty of people can model; far fewer can cook an `AthenaCharacterItemDefinition`
that a 2018 build will load. **Validate the pipeline at level 1 or 2 before
investing in art**, or you risk producing a beautiful model you cannot ship.

## The asset chain

```
AthenaCharacter:CID_Custom_ToyChica      <- what the backend grants
   └─> CID_Custom_ToyChica               (AthenaCharacterItemDefinition)
        └─> CP_Custom_ToyChica_*         (CharacterParts: Head/Body/Hat/Face/Charm)
             └─> SkeletalMesh + Materials + Textures
                  └─> pakchunkNNN-WindowsClient.pak   (AES key is per build)
```

Every link must exist and be cooked for the target engine version. A missing
CharacterPart yields the default commando rather than an error message, which
makes debugging this chain miserable — change one link at a time.

## Skeleton requirements

Fortnite characters all share one skeleton so that emotes and animations
retarget. A custom mesh must be bound to a UE4-mannequin-derived hierarchy with
the stock bone names, or it will not animate:

```
root > pelvis > spine_01..03 > neck_01 > head
                             > clavicle_l/r > upperarm > lowerarm > hand
       pelvis > thigh_l/r > calf > foot > ball
```

The blockout generator emits exactly these 23 bones. **It omits the finger
chain** — fine for a proxy, not fine for a shipping skin, since weapons are
gripped via finger sockets. Add the full hand hierarchy before real art.

Scale and orientation matter as much as names: characters are ~180cm, forward
is +X, up is +Z. The FBX exporter flags in `build_toychica_blockout.py`
(`add_leaf_bones=False`, `primary_bone_axis="Y"`, `axis_forward="-Z"`,
`axis_up="Y"`) are the combination that imports upright into Unreal without
phantom bones.

## Tooling for the parts that need Windows

None of this runs on Linux or without the game files:

- **FModel** / **CUE4Parse** — browse and export from paks; needs the build's AES key
- **UE Viewer (umodel)** — mesh and animation export
- **Blender** + Fortnite-porting addons — editing
- **UE4 editor 4.2x** — cooking, the real gatekeeper
- **UnrealPak / repak** — repacking

## Status

Done:

- Rigged blockout generator with a verified FBX round-trip (23 bones, 6 material slots, 180cm)
- CPU-only preview renderer
- `AthenaCharacter:CID_Custom_ToyChica` registered in both profiles

Not done, and blocked without a Windows machine plus the game files:

- Cooking the item definition and character parts
- Packing and mounting a custom pak
- The launcher's modding mode for pak signature failures
- Anything requiring visual confirmation in-game

## Licensing note

Toy Chica belongs to Scott Cawthon / Steel Wool Studios. FNaF has an unusually
permissive fan-content policy, which is why it is a comfortable choice for a
personal or small private server. That comfort does not automatically extend to
redistributing character assets at scale on a public server — worth a second
look before this becomes a public project rather than a test.
