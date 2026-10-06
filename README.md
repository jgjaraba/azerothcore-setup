# azerothcore-setup
My configs and scripts for AzerothCore

## OpenCode workspace and project knowledge

- [`docs/project/README.md`](docs/project/README.md) — the durable knowledge
  base for this project. Read it first; it indexes the architecture, component
  and feature documentation, ADRs, identifier registry, debt register and
  durable learnings.
- OpenCode runs directly from this repository: `cd ~/azerothcore-setup && opencode`.
  Its project configuration is `opencode.jsonc`, agents are in `.opencode/agents/`,
  and durable instructions are in `AGENTS.md`.
- `scripts/agent/validate-opencode.sh` checks the active project configuration.

## Client setup

### 1. Download WotLK client
**Regular Client**

```https://www.chromiecraft.com/en/downloads```

**HD Client**

```https://discord.gg/UyjSg8wRcs```

### 2. Install server patch

Download [patch-Z.mpq (regular client)](client_patches/regular_client/patch-Z.mpq) or [patch-Z.mpq (hd client)](client_patches/hd_client/patch-Z.mpq)

#### 2.1 (HD Client only) Classic login screen

If you use HD client and want to see always the classic login screen, copy [loginui.lua](client_patches/loginui.lua) into your client `Interface` directory.

#### 2.2. Optional patchs
* [Classic Dungeon Maps](https://github.com/Trimitor/WDM-patch)

### 3. Addons

* [Questie](https://github.com/Aldori15/Questie) / [Questie experimental build](addons/Questie-335.zip)
* [AtlasLoot](https://github.com/Wrath-AddOns/AtlasLoot_ChromieCraft) / [AtlasLoot experimental build](addons/Atlasloot.zip)
* [Bagnon](https://github.com/RichSteini/Bagnon-3.3.5)
* [DungeonClear](https://github.com/jrad7/mod-dungeon-clear-addon)
* [MultiBot-Chatless](https://github.com/Wishmaster117/MultiBot-Chatless)
* [PlayerbotManager](https://github.com/Lichborne-AC/PlayerbotManager)
