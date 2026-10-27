# AGENTS.md — shadowrocket-ai-direct

Instructions for coding agents working on this repository.

## What this project is

Offline, searchable Shadowrocket config for routing core AI traffic via a dedicated `固定家宽` group and domestic sites via `DIRECT`. Public artifacts must never embed private subscription nodes, IPs, UUIDs, or passwords.

## Source of truth and publish path

- Edit reviewable sources under `data/` and `rules/`, then run `python3 scripts/build.py` (writes both `kidstudio.conf` and legacy alias `ai-direct.conf`).
- Validate with `python3 scripts/build.py --check` and `python3 -m unittest discover -s test -v`.
- **Publish only via Git** (commit → `main`, optionally tag a Release). Rolling URL:

  `https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/kidstudio.conf`

- **Do not upload or sync this config to Cloudflare R2** (or any other object-store mirror). R2 distribution is retired; GitHub Raw / Releases are the only distribution channels agents should use or document.

## Proxy groups (do not regress)

| Group | Expected shape |
| --- | --- |
| `香港节点` | `url-test` **with** `policy-regex-filter=香港` |
| `固定家宽` | `url-test` **without** any `policy-regex-filter` (user picks/家宽 nodes in the app) |
| `核心AI` | `fallback` → `固定家宽`, `REJECT` |
| `🐟 漏网之鱼` | `select,PROXY` (Shadowrocket built-in `PROXY`) |

Never reintroduce `美国VPS`, a custom `PROXY =` group, or private `*-NODE` placeholders in public files.

## Privacy hard rules

- No personal subscription URLs, node hostnames, IPs, UUID/password, or NODE aliases in `kidstudio.conf` / `ai-direct.conf` / docs examples meant as paste-ready private configs.
- Prefer generic wording in README/AGENTS; keep personal `kid.conf` / RESIP nodes out of this repo.

## Typical change flow

1. Change `data/base.conf`, `rules/*.list`, or `data/china-domains.txt` (update `data/sources.json` sha256 when the china domain snapshot bytes change).
2. `python3 scripts/build.py && python3 -m unittest discover -s test -v`
3. Commit and push to `main`. Tag a Release when the change should be pinned (e.g. `v1.1.x`).
4. Tell the maintainer to refresh the remote config in Shadowrocket (or re-import Raw URL). Do not push to R2.
