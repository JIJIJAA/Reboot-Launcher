# Reboot Launcher

GUI and CLI launcher for [Project Reboot](https://github.com/Milxnor/Project-Reboot-3.0/),
which lets people play and host Fortnite seasons 0-14 against a self-hosted
backend. Windows only.

## Layout

| Path | Language | Role |
| --- | --- | --- |
| `common/` | Dart | Shared logic for GUI and CLI: game launch, DLL injection, backend helpers |
| `gui/` | Flutter | The main app. `fluent_ui` (Windows UI 3), Windows-only |
| `cli/` | Dart | Work-in-progress CLI for hosting on a Windows VPS |
| `auth_backend/` | Node.js | Fortnite backend, a vendored fork of LawinServer (GPL-3.0) |
| `server_browser_backend/` | Dart | Server browser service |
| `modding/` | Python | Custom cosmetics tooling — see `modding/README.md` |

`gui/` and `cli/` both depend on `common/` through a path dependency.

## Things that will bite you

**The Athena profile exists twice.** `auth_backend/profiles/athena.json` and
`gui/assets/backend/profiles/athena.json` are byte-identical copies, because the
GUI bundles the backend as a Flutter asset. Editing one without the other means
the launcher serves a stale profile and nothing reports an error. Use
`modding/add_custom_cosmetic.py`, which patches both.

Those files are ~3.4MB of two-space-indented JSON **with no trailing newline**.
`json.dump(data, f, indent=2)` with no extra newline round-trips byte-exact;
anything else rewrites the whole file as one diff hunk.

**Flutter is pinned below 3.19.0.** `gui/pubspec.yaml` caps the SDK at
`<=3.19.0` deliberately — it is the last version supporting Windows 7/8/8.1,
which some users asked for (upstream issue #58). Do not bump it casually.

**Fortnite is driven by parsing stdout.** `common/lib/src/game/game_metadata.dart`
runs `handleGameOutput`, matching log lines against the string lists in
`game_constants.dart` to detect login, shutdown, match end, connection failure
and corrupt builds. These are brittle string matches against a closed-source
game — changing them changes runtime behaviour in ways no test will catch.

Note that `kCorruptedBuildErrors` contains `"Pak chunk signature verification
failed!"`, which also fires for legitimately modded paks. See
`modding/README.md`.

## Building

The GUI is a standard Flutter Windows app (`flutter build windows` from `gui/`);
it needs the Flutter SDK and Visual Studio build tools. The backend runs with
`node index.js` from `auth_backend/`. `SETUP.bat` installs the VC++ 2022 x64
redistributable that shipped builds require.

None of this builds or runs on Linux.

## Conventions

Dart code uses the existing formatting in each file; comments are in English and
sparse, usually explaining a workaround rather than restating the code. Vendored
code under `auth_backend/` is upstream LawinServer — keep local changes minimal
and obvious so upstream updates stay mergeable.
