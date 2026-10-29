# AGENTS.md — shadowrocket-ai-direct

Instructions for coding agents working on this repository.

## What this project is

Searchable Shadowrocket setup for routing core AI traffic via a dedicated `固定家宽` group and domestic sites via `DIRECT`. Public artifacts must never embed private subscription nodes, IPs, UUIDs, or passwords.

The distribution is two-layer:

- `kidstudio.conf` (and the identical legacy alias `ai-direct.conf`) is a **thin shell**: `[General]`, four proxy groups, a short LAN/plain-DNS rule block, five remote rule-set references, `GEOIP,CN`, `FINAL`. Keep it under ~50 KB / 200 lines.
- `rulesets/*.list` carry the bulk data: `core-ai.list`, `hongkong.list`, `direct-extra.list`, `china-domains.list` (DOMAIN-SET), `china-ips.list`.

Domestic coverage is vendored, not linked upstream: ChinaMax domain suffixes (`data/china-domains.txt`) and ChinaIPs IPv4 ranges (`data/china-ips.txt`) are snapshots in this repo, compiled into **our own** `rulesets/` files. The config must only reference the rolling `raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/...` URLs — never upstream third-party rule sets, and never re-inline the bulk tables into the conf (that re-creates a 4.4 MB file whose update would flatten locally chosen nodes).

## Source of truth and publish path

- Edit reviewable sources under `data/` and `rules/`, then run `python3 scripts/build.py`. It writes `kidstudio.conf`, `ai-direct.conf`, and the five files in `rulesets/`.
- Never hand-edit `kidstudio.conf`, `ai-direct.conf`, or anything under `rulesets/`; they are generated. `--check` catches drift.
- Validate with `python3 scripts/build.py --check` and `python3 -m unittest discover -s test -v`.
- **Publish only via Git** (commit → `main`, optionally tag a Release). Rolling URLs:

  ```text
  https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/kidstudio.conf
  https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/rulesets/core-ai.list
  https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/rulesets/hongkong.list
  https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/rulesets/direct-extra.list
  https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/rulesets/china-domains.list
  https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/rulesets/china-ips.list
  ```

- **Do not upload or sync this config to Cloudflare R2** (or any other object-store mirror). R2 distribution is retired; GitHub Raw / Releases are the only distribution channels agents should use or document.

## Proxy groups (do not regress)

| Group | Expected shape |
| --- | --- |
| `香港节点` | `url-test` **with** `policy-regex-filter=香港` |
| `固定家宽` | `url-test` **without** any `policy-regex-filter` (user picks/家宽 nodes in the app) |
| `核心AI` | `fallback` → `固定家宽`, `REJECT` |
| `🐟 漏网之鱼` | `select,PROXY` (Shadowrocket built-in `PROXY`) |

Never reintroduce `美国VPS`, a custom `PROXY =` group, or private `*-NODE` placeholders in public files.

## Rule-set format rules

- RULE-SET files list rules only (`DOMAIN,` / `DOMAIN-SUFFIX,` / `IP-CIDR,<cidr>,no-resolve`), **no policy column**; the policy lives in the config line that references the set.
- DOMAIN-SET (`china-domains.list`) is a byte-identical copy of the vendored snapshot: `.example.com` = suffix, `example.com` = exact.
- Rule order in `[Rule]`: `DST-PORT,53,REJECT` → LAN → `core-ai.list`(核心AI) → `hongkong.list`(香港节点) → `direct-extra.list`(DIRECT) → `china-domains.list`(DIRECT) → `china-ips.list`(DIRECT) → `GEOIP,CN,DIRECT` → `FINAL,🐟 漏网之鱼`. `core-ai` must stay ahead of `hongkong` so `DOMAIN,js.stripe.com` keeps routing to 核心AI. Do not use `DOMAIN-KEYWORD` in `hongkong.list`.
- Dedupe with `dict.fromkeys`; canonicalize IPs with `ipaddress`.

- `rules/hongkong.list` is the source for `rulesets/hongkong.list` (香港节点): exchanges, brokers, wallets, cross-border payments and market-data sites. Front it only with `DOMAIN-SUFFIX` entries; treat the listed domain facts as reviewed data — fix obvious syntax errors, do not rewrite domains without being asked.

## Privacy hard rules

- No personal subscription URLs, node hostnames, IPs, UUID/password, or NODE aliases in `kidstudio.conf` / `ai-direct.conf` / `rulesets/` / docs examples meant as paste-ready private configs.
- Prefer generic wording in README/AGENTS; keep personal `kid.conf` / RESIP nodes out of this repo.

## Typical change flow

1. Change `data/base.conf`, `rules/*.list`, `data/china-domains.txt` or `data/china-ips.txt` (update the matching `data/sources.json` sha256 when either ChinaMax or ChinaIPs snapshot bytes change).
2. `python3 scripts/build.py && python3 scripts/build.py --check && python3 -m unittest discover -s test -v`
3. Commit the sources **and** the regenerated `rulesets/` + conf files, push to `main`. Tag a Release when the change should be pinned (e.g. `v1.2.x`).
4. Tell the maintainer to refresh rules in Shadowrocket with「使用配置」(recompile), **not**「更新配置」(whole-file overwrite, which discards locally picked nodes). Do not push to R2.
