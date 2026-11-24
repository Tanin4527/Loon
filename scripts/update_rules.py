#!/usr/bin/env python3
"""Weekly updater for this repo's Loon split-routing rule lists.

Author: Tanin4527. One file does both jobs:

1. Meta.list - Meta (AS32934 + AS63293) announced prefixes fetched live from
   RIPEstat (https://stat.ripe.net), collapsed to the exact announced
   union, combined with the curated core domains in META_DOMAINS below.
2. LinuxDO.list - current *.linux.do / *.linuxdo.org hostnames discovered
   from certificate transparency logs (crt.sh); DOMAIN-SUFFIX rules for
   both roots plus one explicit rule per single-level subdomain, and the
   oaifree DoH entries kept DIRECT.

Safety: suspiciously small results abort without touching the files, so
a bad run can never wipe a list. If a generated body (ignoring the date
stamp) is unchanged, the file is left untouched (no empty commits).
No node, subscription or account data is involved anywhere.
"""
import ipaddress
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_ASNS = ("AS32934", "AS63293")  # AS32934 main + AS63293 FACEBOOK-OFFNET (FNA edge)

# Meta curated core domains (no policy attached; edit here to add domains).
META_DOMAINS = """\
# === Meta / 公司主域 ===
DOMAIN-SUFFIX,meta.com
DOMAIN-SUFFIX,meta.ai
DOMAIN-SUFFIX,muse.ai
DOMAIN-SUFFIX,metaquest.com
DOMAIN-SUFFIX,accountkit.com
DOMAIN-SUFFIX,crowdtangle.com
DOMAIN-SUFFIX,workplace.com
DOMAIN-SUFFIX,expresswifi.com
DOMAIN-SUFFIX,freebasics.com
DOMAIN-SUFFIX,internet.org

# === Facebook ===
DOMAIN-SUFFIX,facebook.com
DOMAIN-SUFFIX,facebook.net
DOMAIN-SUFFIX,facebook.org
DOMAIN-SUFFIX,facebookmail.com
DOMAIN-SUFFIX,facebookbrand.com
DOMAIN-SUFFIX,fb.com
DOMAIN-SUFFIX,fb.me
DOMAIN-SUFFIX,fb.watch
DOMAIN-SUFFIX,fb.gg
DOMAIN-SUFFIX,fbcdn.net
DOMAIN-SUFFIX,fbcdn.com
DOMAIN-SUFFIX,fbsbx.com
DOMAIN-SUFFIX,fbaddins.com
DOMAIN-SUFFIX,fbworkmail.com
DOMAIN-KEYWORD,facebook

# === Instagram ===
DOMAIN-SUFFIX,instagram.com
DOMAIN-SUFFIX,cdninstagram.com
DOMAIN-SUFFIX,instagr.am
DOMAIN-SUFFIX,ig.me
DOMAIN-SUFFIX,instagram.net

# === Threads ===
DOMAIN-SUFFIX,threads.net
DOMAIN-SUFFIX,threads.com

# === Messenger ===
DOMAIN-SUFFIX,messenger.com
DOMAIN-SUFFIX,m.me

# === WhatsApp ===
DOMAIN-SUFFIX,whatsapp.com
DOMAIN-SUFFIX,whatsapp.net
DOMAIN-SUFFIX,whatsapp.biz
DOMAIN-SUFFIX,whatsappbrand.com
DOMAIN-SUFFIX,wa.me

# === Oculus / VR ===
DOMAIN-SUFFIX,oculus.com
DOMAIN-SUFFIX,oculuscdn.com"""


def strip_stamp(text):
    return re.sub(r"^# Version: .*$", "", text, flags=re.M)


def write_if_changed(path, content):
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if strip_stamp(old) == strip_stamp(content):
        print(f"unchanged {path.name}")
        return False
    path.write_text(content, encoding="utf-8")
    print(f"updated {path.name}")
    return True


# ---------------------------------------------------------------- Meta ---

def fetch_meta_prefixes():
    prefixes = []
    for asn in META_ASNS:
        url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn}"
        req = urllib.request.Request(url, headers={"User-Agent": "loon-rules-updater/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        prefixes += [p["prefix"] for p in data["data"]["prefixes"]]
    v4 = [ipaddress.ip_network(p) for p in prefixes if ":" not in p]
    v6 = [ipaddress.ip_network(p) for p in prefixes if ":" in p]
    if len(v4) < 10 or len(v6) < 1:
        raise SystemExit(f"Refusing to continue: suspicious prefix count v4={len(v4)} v6={len(v6)}")
    return (
        [str(n) for n in sorted(ipaddress.collapse_addresses(v4))],
        [str(n) for n in sorted(ipaddress.collapse_addresses(v6))],
    )


def build_meta_list(today):
    v4, v6 = fetch_meta_prefixes()
    ip_lines = [f"IP-CIDR,{p},no-resolve" for p in v4] + [f"IP-CIDR6,{p},no-resolve" for p in v6]
    return "\n".join([
        "# =========================================================================",
        "# Rule Name: Meta Split Routing",
        "# Author: Tanin4527",
        "# Target App: Loon / Surge / Quantumult X compatible (ruleset, no policy)",
        "# Purpose: Meta 全家桶 (Facebook / Instagram / Threads / WhatsApp /",
        "#          Messenger / Oculus / Meta AI) 域名与 IP 段清单。",
        "#          本文件不带策略, 由引用方指定 policy。IP 段每周由",
        "#          scripts/update_rules.py 从 RIPEstat (AS32934 + AS63293) 自动更新。",
        "# Usage (Loon):",
        "#   [Remote Rule]",
        "#   https://raw.githubusercontent.com/Tanin4527/Loon/main/Meta.list, policy=<你的策略组>, tag=Meta, enabled=true",
        f"# Version: {today} (auto)",
        "# =========================================================================",
        "",
        META_DOMAINS,
        "",
        "# === Meta IP 段 (AS32934 + AS63293, RIPEstat 每周自动抓取) ===",
        *ip_lines,
        "",
    ])


# ------------------------------------------------------------- LinuxDO ---

LINUXDO_ROOTS = ("linux.do", "linuxdo.org")
LINUXDO_MIN_NAMES = {"linux.do": 20, "linuxdo.org": 3}


def fetch_crt_names(root_domain):
    url = f"https://crt.sh/?q=%25.{root_domain}&output=json"
    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "loon-rules-updater/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.load(resp)
            names = set()
            for entry in data:
                for name in entry.get("name_value", "").split("\n"):
                    name = name.strip().lower().lstrip("*.")
                    if name == root_domain or name.endswith("." + root_domain):
                        names.add(name)
            return names
        except Exception as exc:  # crt.sh is slow/flaky; retry before giving up
            last_err = exc
            time.sleep(10 * (attempt + 1))
    raise SystemExit(f"crt.sh failed for {root_domain}: {last_err}")


def single_level(names, root_domain):
    keep = []
    for name in sorted(names):
        if name == root_domain:
            continue
        head = name[: -(len(root_domain) + 1)]
        if "." not in head and "cloudflare" not in name:
            keep.append(name)
    return keep


def build_linuxdo_list(today):
    discovered = {}
    for root_domain in LINUXDO_ROOTS:
        names = fetch_crt_names(root_domain)
        if len(names) < LINUXDO_MIN_NAMES[root_domain]:
            raise SystemExit(
                f"Refusing to continue: only {len(names)} names for {root_domain} "
                f"(expected >= {LINUXDO_MIN_NAMES[root_domain]}); keeping old file."
            )
        discovered[root_domain] = single_level(names, root_domain)
        print(f"{root_domain}: {len(names)} cert names, {len(discovered[root_domain])} single-level subdomains")

    lines = [
        "# =========================================================================",
        "# Rule Name: LINUX DO Direct",
        "# Author: Tanin4527",
        "# Target App: Loon / Surge / Quantumult X compatible",
        "# Purpose: Force DIRECT for LINUX DO (linux.do / linuxdo.org) and its DoH,",
        "#          so L站不走代理。配合 ECH / 安全 DNS 直连使用。",
        "# Source: certificate transparency logs (crt.sh), refreshed weekly by",
        "#         scripts/update_rules.py; DOMAIN-SUFFIX covers every",
        "#         subdomain whether it is listed below or not.",
        f"# Version: {today} (auto)",
        "# Usage (Loon):",
        "#   [Remote Rule]",
        "#   https://raw.githubusercontent.com/Tanin4527/Loon/main/LinuxDO.list, policy=DIRECT, tag=LINUX DO, enabled=true",
        "#   注意: 把这条放在 [Remote Rule] 最前面, 在 FINAL / GEOIP,CN 之前生效。",
        "# =========================================================================",
        "",
        "# === LINUX DO 主站及全部子站 (DOMAIN-SUFFIX 整段覆盖) ===",
        "DOMAIN-SUFFIX,linux.do,DIRECT",
        "DOMAIN,linux.do,DIRECT",
        "",
        "# === crt.sh 本周发现的 linux.do 子站 (显式清单, 后缀规则已覆盖) ===",
    ]
    lines += [f"DOMAIN,{host},DIRECT" for host in discovered["linux.do"]]
    lines += [
        "",
        "# === LINUX DO 备用域名及全部子站 ===",
        "DOMAIN-SUFFIX,linuxdo.org,DIRECT",
        "DOMAIN,linuxdo.org,DIRECT",
        "",
        "# === crt.sh 本周发现的 linuxdo.org 子站 ===",
    ]
    lines += [f"DOMAIN,{host},DIRECT" for host in discovered["linuxdo.org"]]
    lines += [
        "",
        "# === 直连 DoH (oaifree)，否则 DoH 本身走了代理会解析失败 ===",
        "DOMAIN-SUFFIX,oaifree.com,DIRECT",
        "DOMAIN,ld.ddd.oaifree.com,DIRECT",
        "",
        "# End of LINUX DO rules - place this RULE-SET at the VERY TOP of your [Rule] section",
        "",
    ]
    return "\n".join(lines)


def main():
    today = date.today().isoformat()
    changed = False
    changed |= write_if_changed(ROOT / "Meta.list", build_meta_list(today))
    changed |= write_if_changed(ROOT / "LinuxDO.list", build_linuxdo_list(today))
    print("CHANGED" if changed else "NO_CHANGE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
