# 来源与许可证

本项目采用 **GPL-2.0-only**。完整许可条款见 [LICENSE](LICENSE)。分发修改版本时请保留许可证、来源说明并提供对应源文件。项目不提供代理节点，不属于任何 AI 服务或 Shadowrocket 官方项目。

## 国内域名快照

- 作者：blackmatrix7 及其上游贡献者。
- 仓库：[blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)。
- 固定提交：`933875d42861a7fdfd9f945cd18605d74fa7e943`。
- 文件：[China_Domain.list](https://github.com/blackmatrix7/ios_rule_script/blob/933875d42861a7fdfd9f945cd18605d74fa7e943/rule/Shadowrocket/China/China_Domain.list)。
- 原样保存在 `data/china-domains.txt`；该文件头的更新时间属于上游，不等于本项目核验日期。
- 上游声明 GPL-2.0；本仓库保留其完整 LICENSE。更早的来源可查上游文件与仓库历史。
- 构建时把前导点域名转换为 `DOMAIN-SUFFIX`，普通域名转换为 `DOMAIN`，附加 `DIRECT` 并去重。

该表表示上游选择的大陆可直连站点，包含部分国际站点与国内 CDN 例外，不代表所有域名均属于中国，也不保证每个地区当前都能直连。项目不在设备运行时加载它的远程 URL。

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

`data/sources.json` 保存国内表的固定提交和 SHA-256。升级时先核对上游许可证及差异，更新本地快照和摘要，再运行构建与测试。不会定时自动抓取并发布未经审查的上游变化。

`rules/ai.list`、`rules/direct.list`、`data/base.conf` 是可审查源文件；`ai-direct.conf` 是可直接导入的合并产物。维护记录以 Git 提交和 Release 为准。

