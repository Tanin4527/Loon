# Loon（私有）

老沫自用的 Loon 规则合集，一个仓库放全部。作者：Tanin4527。

> 本仓库为 **Private**，仅自用。所有规则只含域名与 IP 段，不含任何节点、订阅或账号信息：Meta 插件的策略用 Loon 的 `PROXY` 占位，安装时自选策略组。
> 私有仓的 raw 地址需要登录态，Loon 一般拉不到，插件/规则下载后本地导入最稳。

## 文件

- `Meta.plugin` — Meta 全家桶分流插件（Facebook / Instagram / Threads / WhatsApp / Messenger / Oculus / Meta AI），策略 `PROXY`。
- `Meta.list` — Meta 规则清单（无策略版），`[Remote Rule]` 引用时用 `policy=` 指定。
- `LinuxDO.list` — LINUX DO 直连，`linux.do` / `linuxdo.org` 及全部子站走 DIRECT，含其直连 DoH。

## 自动更新（每周）

GitHub Action（`.github/workflows/update-rules.yml`）每周一凌晨 03:00（北京时间）自动运行，一次跑完两个更新脚本，有变化才提交：

- `scripts/update_meta.py`：从 RIPEstat 抓 Meta 的 AS32934 实时公布 IP 段、合并去重，与 `scripts/meta_domains.txt` 的核心域名一起重新生成 `Meta.plugin` / `Meta.list`。
- `scripts/update_linuxdo.py`：从证书透明日志（crt.sh）抓 `linux.do` / `linuxdo.org` 最新子站清单，重新生成 `LinuxDO.list`；抓取源异常时中止、不动旧文件。

## Loon 用法

- Meta：把 `Meta.plugin` 本地导入 Loon，在插件里把 PROXY 选成你的策略组。
- LinuxDO：在 `[Remote Rule]` 里引用 `LinuxDO.list` 并把 policy 设为 DIRECT（私有仓拉不到时同样本地导入规则内容），放在规则最前面。解析 `linux.do` 的 DNS 用 `https://ld.ddd.oaifree.com/query-dns`（`oaifree.com` 已在清单里走 DIRECT）。
