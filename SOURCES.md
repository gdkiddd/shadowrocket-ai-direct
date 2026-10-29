# 来源与许可证

本项目采用 **GPL-2.0-only**。完整许可条款见 [LICENSE](LICENSE)。分发修改版本时请保留许可证、来源说明并提供对应源文件。项目不提供代理节点，不属于任何 AI 服务或 Shadowrocket 官方项目。

## 国内域名与 IP 快照

- 作者：blackmatrix7 及其上游贡献者。
- 仓库：[blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)。
- 固定提交：`0b6897dc17e0c513d25449c935a9694818e32f0c`。
- 域名文件：[ChinaMax_Domain.list](https://github.com/blackmatrix7/ios_rule_script/blob/0b6897dc17e0c513d25449c935a9694818e32f0c/rule/Shadowrocket/ChinaMax/ChinaMax_Domain.list)，原样保存在 `data/china-domains.txt`；该文件头的更新时间属于上游，不等于本项目核验日期。
- IP 文件：[ChinaIPs.list](https://github.com/blackmatrix7/ios_rule_script/blob/0b6897dc17e0c513d25449c935a9694818e32f0c/rule/Shadowrocket/ChinaIPs/ChinaIPs.list)，仅提取其中的 `IP-CIDR` 网段（去注释、去重、保持上游顺序），存入 `data/china-ips.txt`。
- 上游声明 GPL-2.0；本仓库保留其完整 LICENSE。更早的来源可查上游文件与仓库历史。
- 构建时把前导点域名保留为 `DOMAIN-SET` 的后缀项，普通域名保留为精确项；IP 转换为 `IP-CIDR,<cidr>,no-resolve`，整体去重。

ChinaMax 是上游对大陆可直连站点的宽口径集合（约 11 万条域名后缀），ChinaIPs 是配套的大陆 IP 段集合（约 2 万条网段）。两者仍以离线快照保存在本仓库，构建后分别发布为 `rulesets/china-domains.list`（`DOMAIN-SET`）与 `rulesets/china-ips.list`（`RULE-SET`）。运行时 Shadowrocket 只拉取本仓库自己的 Raw 规则集，不请求上游 blackmatrix7 的表，也不在客户端临时抓取。

该表包含部分国际站点与国内 CDN 例外，不代表所有域名均属于中国，也不保证每个地区当前都能直连；`GEOIP,CN,DIRECT` 只作为兜底。主配置 `kidstudio.conf` 保持约 3 KB，只引用规则集，这样更新规则不会覆盖本地分组与手选节点。

## 核心 AI

`rules/ai.list` 按服务划分；只保留需要的域名事实，不复制网页正文。

- [OpenAI 官方网络建议](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)：核心域名、登录、静态资源、挑战、部分共享第三方资源、WebSocket 与语音要求。
- [OpenAI 官方语音地址](https://openai.com/chatgpt-voice.json)：2026-10-17 获取，IPv4 网段转换存入 `data/openai-voice-cidrs.txt`。上游会变化，版本时间和原始响应摘要见 `data/sources.json`。
- [Claude Code 官方网络配置](https://code.claude.com/docs/en/network-config)：Claude / Anthropic API 与认证需求。
- [Gemini API 官方参考](https://ai.google.dev/api)：`generativelanguage.googleapis.com`。
- [Gemini CLI 源码](https://github.com/google-gemini/gemini-cli)：CLI 服务入口参考。
- 兼容性补充参考 [上游 OpenAI.list](https://github.com/blackmatrix7/ios_rule_script/blob/933875d42861a7fdfd9f945cd18605d74fa7e943/rule/Shadowrocket/OpenAI/OpenAI.list) 与 [Claude.list](https://github.com/blackmatrix7/ios_rule_script/blob/933875d42861a7fdfd9f945cd18605d74fa7e943/rule/Shadowrocket/Claude/Claude.list)，同为 GPL-2.0。没有照搬覆盖全部 Google、全部 Cloudflare、全部 Sentry 或整段云厂商网络的宽泛规则。

登录、支付、验证及支持资源可能被其他服务共享。匹配相同域名的其他应用也会走 AI 分组。第三方 MCP、插件、链接访问、Vertex AI、Bedrock、Azure 及自定义 API 中转不在本项目的完整覆盖承诺内。

## 更新方式

`data/sources.json` 保存国内域名表、国内 IP 表的固定提交和 SHA-256（两者分别对应 `data/china-domains.txt`、`data/china-ips.txt` 的原始字节）。升级时先核对上游许可证及差异，更新本地快照和摘要，再运行构建与测试。不会定时自动抓取并发布未经审查的上游变化。`rules/direct.list` 只保留上游未覆盖或项目特别需要的直连例外（如国内 AI 与微软办公），与 ChinaMax 完全重复的后缀会被删除。

`rules/ai.list`、`rules/direct.list`、`data/base.conf`、`data/*.txt` 是可审查源文件；`kidstudio.conf`、`ai-direct.conf` 与 `rulesets/*.list` 是构建产物。维护记录以 Git 提交和 Release 为准。

客户端侧的更新边界：规则改动只影响 `rulesets/`，在 Shadowrocket 里对当前配置点「使用配置」/重新编译即可刷新规则集，本地手选的 `固定家宽` 节点与分组设置保留；点「更新配置」会整份覆盖 `kidstudio.conf`，把本地分组和节点选择一起压平，应避免。

## 规则集地址

```text
https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/rulesets/core-ai.list
https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/rulesets/direct-extra.list
https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/rulesets/china-domains.list
https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/rulesets/china-ips.list
```

`core-ai.list`、`direct-extra.list`、`china-ips.list` 为 Shadowrocket `RULE-SET` 格式，行内不带策略名；`china-domains.list` 为 `DOMAIN-SET`。策略由引用它们的配置行决定，规则集本身不含节点、订阅或凭证。

