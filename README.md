# Loon

老沫自用的分流规则合集：一个仓、两套格式、一个自动抓取。作者：Tanin4527。

> 所有规则只含域名与 IP 段，不含任何节点、订阅或账号信息。仓库公开，raw 地址可直接订阅。

## 结构

- `Loon/` — Loon / Surge / Quantumult X 用的 `.list` 清单（无策略版，引用时用 `policy=` 指定策略组）。
- `Clash/` — Clash（mihomo）用的 `.yaml` rule-provider 文件，与 `Loon/` 同源同内容、只是格式不同。
- `scripts/update_rules.py` — 自动抓取（就这一个文件）：每周一凌晨 03:00（北京时间）由 GitHub Action 运行，一次抓取同时重新生成上面两套，抓取源异常时中止、不动旧文件。

## 清单

- **Meta** — Meta 全家桶（Facebook / Instagram / Threads / WhatsApp / Messenger / Oculus / Meta AI / Muse）；域名人工维护在脚本里，IP 段从 RIPEstat 抓 AS32934＋AS63293 全部公布段合并去重。
- **LinuxDO** — LINUX DO 直连，`linux.do` / `linuxdo.org` 及全部子站走 DIRECT，子站清单每周从证书透明日志（crt.sh）刷新，含其直连 DoH。
- **Manus** — Manus（含 Cue）分流，独立一份（Manus 现为独立公司，不并入 Meta 清单），静态域名：`manus.im` / `cue.im` / `manus.space`。

## Loon 用法

在 `[Remote Rule]` 里引用（LinuxDO 放最前面）：

```
https://raw.githubusercontent.com/Tanin4527/Loon/main/Loon/LinuxDO.list, policy=DIRECT, tag=LINUX DO, enabled=true
https://raw.githubusercontent.com/Tanin4527/Loon/main/Loon/Meta.list, policy=<你的策略组>, tag=Meta, enabled=true
https://raw.githubusercontent.com/Tanin4527/Loon/main/Loon/Manus.list, policy=<你的策略组>, tag=Manus, enabled=true
```

解析 `linux.do` 的 DNS 用 `https://ld.ddd.oaifree.com/query-dns`（`oaifree.com` 已在清单里走 DIRECT）。

## Clash 用法

配置里加 rule-providers，再在 rules 里引用（LinuxDO 放前面）：

```yaml
rule-providers:
  LinuxDO:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/Tanin4527/Loon/main/Clash/LinuxDO.yaml
    path: ./ruleset/LinuxDO.yaml
    interval: 86400
  Meta:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/Tanin4527/Loon/main/Clash/Meta.yaml
    path: ./ruleset/Meta.yaml
    interval: 86400
  Manus:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/Tanin4527/Loon/main/Clash/Manus.yaml
    path: ./ruleset/Manus.yaml
    interval: 86400

rules:
  - RULE-SET,LinuxDO,DIRECT
  - RULE-SET,Meta,<你的策略组>
  - RULE-SET,Manus,<你的策略组>
```
