# Loon（私有）

老沫自用的 Loon 分流规则合集，一个仓库放全部。作者：Tanin4527。

> 本仓库为 **Private**，仅自用。所有规则只含域名与 IP 段，不含任何节点、订阅或账号信息。
> 私有仓的 raw 地址需要登录态，Loon 一般拉不到，规则下载后本地导入 / 复制进配置最稳。

## 文件

- `Meta.list` — Meta 全家桶分流清单（Facebook / Instagram / Threads / WhatsApp / Messenger / Oculus / Meta AI），无策略版，引用时用 `policy=` 指定策略组。
- `LinuxDO.list` — LINUX DO 直连，`linux.do` / `linuxdo.org` 及全部子站走 DIRECT，含其直连 DoH。

## 自动更新（每周）

GitHub Action（`.github/workflows/update-rules.yml`）每周一凌晨 03:00（北京时间）自动运行，一次跑完两个更新脚本，有变化才提交：

- `scripts/update_meta.py`：从 RIPEstat 抓 Meta 的 AS32934 实时公布 IP 段、合并去重，与 `scripts/meta_domains.txt` 的核心域名一起重新生成 `Meta.list`。
- `scripts/update_linuxdo.py`：从证书透明日志（crt.sh）抓 `linux.do` / `linuxdo.org` 最新子站清单，重新生成 `LinuxDO.list`；抓取源异常时中止、不动旧文件。

## Loon 用法

在 `[Remote Rule]` 里引用，或把清单内容复制进本地 `[Rule]`：

```
https://raw.githubusercontent.com/Tanin4527/Loon/main/Meta.list, policy=<你的策略组>, tag=Meta, enabled=true
https://raw.githubusercontent.com/Tanin4527/Loon/main/LinuxDO.list, policy=DIRECT, tag=LINUX DO, enabled=true
```

LinuxDO 那条放在规则最前面；解析 `linux.do` 的 DNS 用 `https://ld.ddd.oaifree.com/query-dns`（`oaifree.com` 已在清单里走 DIRECT）。
