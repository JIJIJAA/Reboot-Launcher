![Banner](https://i.imgur.com/p0P4tcI.png)

GUI and CLI Launcher for [Project Reboot](https://github.com/Milxnor/Project-Reboot-3.0/)

Join our [Discord](https://discord.gg/rebootmp)

Install the launcher easily from the [releases](https://github.com/Auties00/Reboot-Launcher/releases/) section

## 🚀 Plug-and-Play Setup

Reboot Launcher is designed to work out-of-the-box. No manual configuration, no DLL registration, no editing files.

### Requirements

- Windows 10 or later
- [Visual C++ Redistributable 2022 x64](https://aka.ms/vs/17/release/vc_redist.x64.exe) (included in the `dependencies/redist/` folder of the release package)
- A supported Fortnite build (Season 0–14)

### Quick Start

1. **Download** the latest release from the [releases](https://github.com/Auties00/Reboot-Launcher/releases/) page and unzip it.
2. *(First time only)* Run `dependencies/redist/VC_redist.x64.exe` to install the Visual C++ runtime.
3. **Open** `reboot_launcher.exe` — the launcher starts immediately, no installation needed.
4. Go to the **Play** tab, select a Fortnite version, and click **Launch Fortnite**. The backend starts automatically.

### LAN Multiplayer

Play with friends on the same local network without port-forwarding or external services.

#### As the Host

1. Open the launcher and go to the **Host** tab.
2. Select a Fortnite version and click **Start Hosting**.
3. In the **Share** section, click **Copy LAN IP** and send that IP to your friends.

#### As a Client (joining a LAN host)

**Option A – Automatic (recommended):**
1. Open the launcher and go to the **Backend** tab.
2. Switch the backend type to **Remote**.
3. Click **Scan LAN for Host** — the launcher will scan your local network and auto-fill the host's address.
4. Go to the **Play** tab and click **Launch Fortnite**.

**Option B – Manual:**
1. Open the launcher and go to the **Backend** tab.
2. Switch the backend type to **Remote**.
3. Enter the host's LAN IP (shared by the host via **Copy LAN IP**) in the **Host** field.
4. Go to the **Play** tab and click **Launch Fortnite**.

> **Tip:** Players can also join using the **Reboot Link** copied from the host's **Share → Link** button.

---

## Modules

- COMMON: Shared business logic for CLI and GUI modules
  
- CLI: Work in progress command line interface to host a Fortnite Server on a Windows VPS easily, developed in Dart
  
- GUI: Stable graphical user interface to play and host Fortnite S0-14

## Preview 

- GUI
  
![Registrazione 2025-03-24 194421](https://github.com/user-attachments/assets/f3452969-76ba-49e7-b707-42754bacad70)

- CLI
  
Coming soon!
