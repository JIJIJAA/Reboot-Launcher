#!/usr/bin/env python3
"""
Register a custom cosmetic in the Athena profile served by the backend.

The launcher ships two byte-identical copies of the profile: one used by the
standalone `auth_backend`, one bundled into the GUI's assets. Patching only
one of them is a silent failure - the launcher keeps serving the stale copy
and the item never shows up in the locker. This script always patches both.

Usage:
    python3 add_custom_cosmetic.py                       # adds the Toy Chica default
    python3 add_custom_cosmetic.py AthenaCharacter:CID_Custom_Foo
    python3 add_custom_cosmetic.py --list-custom
    python3 add_custom_cosmetic.py --remove AthenaCharacter:CID_Custom_Foo

Granting the item is the easy half. The client still has to resolve the
template ID to a real asset, which means the cooked item definition must be
mounted from a pak the game accepts. See modding/README.md.
"""

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROFILE_PATHS = [
    os.path.join(REPO_ROOT, "auth_backend", "profiles", "athena.json"),
    os.path.join(REPO_ROOT, "gui", "assets", "backend", "profiles", "athena.json"),
]

DEFAULT_TEMPLATE_ID = "AthenaCharacter:CID_Custom_ToyChica"

# Mirrors the shape the backend already uses for every stock skin.
def cosmetic_entry(template_id):
    return {
        "templateId": template_id,
        "attributes": {
            "max_level_bonus": 0,
            "level": 1,
            "item_seen": True,
            "xp": 0,
            "variants": [],
            "favorite": False,
        },
        "quantity": 1,
    }


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save(path, profile):
    # The stock files are two-space indented with NO trailing newline. Writing
    # one anyway rewrites all 3.4MB as a single diff hunk, so don't.
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(profile, handle, indent=2)


def add(template_id):
    for path in PROFILE_PATHS:
        if not os.path.exists(path):
            print(f"  !! missing: {path}")
            continue

        profile = load(path)
        items = profile["items"]
        if template_id in items:
            print(f"  = already present in {os.path.relpath(path, REPO_ROOT)}")
            continue

        items[template_id] = cosmetic_entry(template_id)
        # Bump the revision so the client refetches instead of trusting cache.
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1
        save(path, profile)
        print(f"  + added to {os.path.relpath(path, REPO_ROOT)} "
              f"({len(items)} items, rvn {profile['rvn']})")


def remove(template_id):
    for path in PROFILE_PATHS:
        if not os.path.exists(path):
            continue
        profile = load(path)
        if profile["items"].pop(template_id, None) is None:
            print(f"  = not present in {os.path.relpath(path, REPO_ROOT)}")
            continue
        profile["rvn"] = profile.get("rvn", 0) + 1
        save(path, profile)
        print(f"  - removed from {os.path.relpath(path, REPO_ROOT)}")


def list_custom():
    profile = load(PROFILE_PATHS[0])
    custom = [key for key in profile["items"] if "Custom" in key]
    print(f"{len(profile['items'])} items total, {len(custom)} custom:")
    for key in sorted(custom):
        print("  -", key)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("template_id", nargs="?", default=DEFAULT_TEMPLATE_ID)
    parser.add_argument("--remove", metavar="TEMPLATE_ID")
    parser.add_argument("--list-custom", action="store_true")
    args = parser.parse_args()

    if args.list_custom:
        list_custom()
    elif args.remove:
        print(f"Removing {args.remove}")
        remove(args.remove)
    else:
        if ":" not in args.template_id:
            parser.error("template id must look like AthenaCharacter:CID_Custom_Foo")
        print(f"Registering {args.template_id}")
        add(args.template_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
