# Shadowrocket AI Direct

面向在中国大陆使用 **ChatGPT / OpenAI / Codex、Claude、Gemini** 的 Shadowrocket 用户：核心 AI 使用独立出口，国内网站与常见应用资源优先直连，其他流量走默认代理。规则合并在一份可搜索的 `.conf` 中，无运行时远程规则集、脚本或 HTTPS 解密依赖。

**需要自备可用节点。配置不附带节点、订阅、密码，也不会把普通节点变成住宅 IP。** 出口地区、运营商、服务支持范围和账号状态仍由使用者自行确认。目标是减少错误分流与绕路，不承诺“全解锁”“永不封号”“任何情况下零泄漏”或固定提速幅度。

## 获取配置

滚动更新地址（`main`）：

```text
https://raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/kidstudio.conf
```

旧版 `ai-direct.conf` URL 保留为同内容兼容入口；新导入统一使用 `kidstudio.conf`。

首次使用建议先阅读本页，再从 [Releases](https://github.com/gdkiddd/shadowrocket-ai-direct/releases) 获取固定版本。GitHub Raw 不可达时，可以在已具备可用代理的环境下载，或在 Releases 下载后通过系统分享菜单导入；不需要使用不明镜像。

| 流量 | 策略 |
| --- | --- |
| 核心 AI、相关认证与必要共享资源、公开的 OpenAI 语音 IP | `核心AI` → `固定家宽`（在 App 内自行选择/测速家宽节点，无正则筛选） |
| 需走香港线路的指定规则（如部分金融） | `香港节点`（按节点名正则「香港」自动测速） |
| 局域网、国内域名表、`.cn`、常见国内 AI、微软办公与更新例外 | `DIRECT` |
| 其他目的 IP 命中中国 GeoIP | `DIRECT` |
| 其余流量 | `🐟 漏网之鱼` → Shadowrocket 内置 `PROXY` |
| 未被接管的普通明文 DNS（53 端口） | `REJECT` |

代理分组为 `香港节点` / `固定家宽` / `核心AI` / `🐟 漏网之鱼`。**开源配置只含分组与规则，不写入任何订阅链接、节点地址、UUID 或个人 IP**。`香港节点` 用正则「香港」测速选取；`固定家宽` **不设正则**，在 Shadowrocket 里手动挑选或测速家宽节点；`🐟 漏网之鱼` 直接使用内置 `PROXY`（首页当前选中的代理），配置内不再单独建 `PROXY` / `美国VPS` 分组。

国内域名表来自带许可证的上游快照，包含部分国际服务的直连例外；“国内优先”并不等同于仅按域名后缀判断。GeoIP 是兜底，未知 CDN、海外托管资源仍可能走代理。Google 搜索、GitHub 等未单独列入例外的服务走默认代理；微软也没有整站全部直连。

## 首次配置：按顺序操作

1. **备份原配置。** 在 Shadowrocket 中保留旧文件。新配置有问题时直接切回旧文件，不要删除原订阅。
2. **准备节点（不要把真实订阅节点写进开源配置）。** 先导入你自己的节点订阅。`固定家宽` 无正则筛选，在分组里自行选定稳定住宅/家宽出口（TCP；语音还需 UDP）。`香港节点` 仍用正则「香港」选取。订阅刷新可能重置名称，优先用本地副本。
3. **导入配置 URL。** 底部“配置”→ 右上角“＋”→ 填入上面的 Raw 地址并下载；点击下载后的 `kidstudio.conf` →“使用配置”。不要把配置 URL 填进首页的节点订阅栏。
4. **选择分组。** 在 `固定家宽` 中选定家宽节点，确认 `核心AI` 指向 `固定家宽`；`🐟 漏网之鱼` 指向内置 `PROXY`。
5. **全局路由选“配置”。** 首页默认节点选一个有效日常代理（内置 `PROXY` 会用它）；带 `#proxy` 的 DNS 使用代理解析路径，不能仅凭分组名称断言它一定跟随 `核心AI`。
6. **开启 UDP 规则转发。** “设置”→“UDP”→“启用转发”打开，允许端口留空。关闭它会让 UDP 绕过配置直连。这是每台设备的应用设置，导入 `.conf` 不会自动开启。
7. **检查隧道。** 支持该选项的版本，在“设置”→“隧道”开启“包括所有网络”，保留正常局域网访问；不要开启会让默认路由绕开隧道的代理兼容模式。不同系统版本文字可能略有区别。
8. **macOS 优先使用 TUN 模式。** 在提供该选项的版本中，进入“设置”→“代理”→“代理类型”，选择 **None（TUN Mode）**。这里的 None 表示不设置系统 HTTP 代理，仍需保持 Shadowrocket VPN 已连接、全局路由为“配置”。iOS 或其他版本若没有此入口，不必寻找同名开关，按其 VPN 隧道方式连接即可。
9. **连接后验收。** 按下文检查域名规则、实际日志和出口。每台设备都要检查，不能把一台设备的结果当作全部设备的结果。

订阅节点、别名、分组选择、UDP 转发、隧道开关属于不同层次。只有复制配置文件，不能完整复制一台设备的运行环境。

## HTTP 与 TUN 怎么选

本配置推荐 macOS 使用 **TUN 模式**，让网页、App、CLI 和媒体请求尽量统一进入规则分流。TUN 在网络层接管隧道覆盖的流量；系统 HTTP 代理依赖应用遵守代理设置，不能单独覆盖所有应用或 UDP。隧道排除路由、应用自身代理和其他 VPN 仍可能改变实际路径。

切换为 TUN 不会自动把流量全部直连，也不会自动固定 AI 出口：在 `固定家宽` 里选好稳定家宽节点，首页默认代理选日常节点（供内置 `PROXY` / 漏网之鱼使用），国内命中规则走 `DIRECT`。需要保持同一个出口 IP，还取决于节点供应商是否提供固定 IP；节点名称带“家宽”不能证明住宅属性。HTTP 模式有明确兼容需求时也可使用，并应单独验证应用的实际路径。

**TUN 本身不保证 DNS 不泄漏。** 本配置仍依靠分流加密 DNS、普通 DNS 接管及拒绝回落等设置。每台设备导入后都需完成下方验收；手动指定本机 HTTP 代理地址的 CLI 或浏览器扩展，还要检查其独立设置是否与当前模式一致。

## 自动更新与回滚

- “设置”→“更新”→“配置”→ 开启“自动后台更新”；当前界面的间隔单位为天，可选 **1 天**。具体以安装版本的界面为准。
- 想立即获取新版，在“配置”中点击该远程配置，使用“更新配置”或“更新”，完成后确认它仍是当前使用配置。
- 自动更新是客户端定时拉取，不是即时推送。重启设备或手动结束应用后，重新打开 Shadowrocket，恢复后台任务；系统调度和 GitHub CDN 缓存也可能延迟更新。
- 更新后检查 `固定家宽` 是否仍选着可用家宽节点、`核心AI` 是否指向 `固定家宽`、首页默认代理是否有效。配置更新会覆盖文件内的本地修改。需要个性化规则时请 Fork 后维护自己的 URL。
- 更新后的连通性异常时切回备份，或从 Release 下载上一版本。固定版本 URL 不会跟随 `main` 自动更新。
- 本机改动不会自动上传到 GitHub；维护者提交并发布后，其他设备才会拉取到新版。

## DNS、UDP、IPv6 的取舍

采用**分流加密 DNS**：已匹配国内直连规则的域名使用阿里 DoH，默认/备用境外解析使用 Cloudflare 与 Google DoH，并标记 `#proxy`。这样有利于国内 CDN 就近解析；国内 DNS 服务商仍能看到这些国内查询。加密防止普通链路上的明文旁观，不会让解析服务商失去可见性。

通配接管 UDP 53 后，再以端口规则拒绝未接管的明文 DNS，覆盖普通程序自行指定公共 DNS 的常见旁路。TCP-only DNS 应用可能因此不能解析，请让它使用系统解析或受管理的 DoH。此规则不覆盖应用自行通过 HTTPS 访问的 DoH、局域网排除路由、系统特殊流量或独立 VPN；不对 TLS 流量解密。

| 文件设置 | 默认值与作用 |
| --- | --- |
| `bypass-system` | `true`，保留系统兼容性；系统旁路不等于所有流量都经过规则 |
| `skip-proxy` | localhost、`.local` 和 RFC1918 私网；避免本地设备访问绕远 |
| `tun-excluded-routes` | 私网、回环、链路本地 IPv4；这些路径不在完整隧道接管承诺内 |
| `dns-server` | Cloudflare `1.1.1.1` 与 Google `8.8.8.8` DoH，均带 `#proxy` |
| `fallback-dns-server` | `1.0.0.1` 与 `8.8.4.4` DoH，均带 `#proxy` |
| `direct-dns-server` | 阿里 `223.5.5.5` 与 `223.6.6.6` DoH |
| `dns-fallback-system` | `false`，不主动退回系统 DNS |
| `dns-direct-system` | `false`，直连解析不直接改用系统 DNS |
| `dns-direct-fallback-proxy` | `false`，不为直连失败自动切换代理连接 |
| `hijack-dns` | `*:53`，统一接管隧道可见的普通 UDP DNS |
| `ipv6` / `prefer-ipv6` | 均为 `false`；减少双栈路径差异，但可能牺牲部分国内 IPv6 性能，不能视为系统 IPv6 总开关 |
| `private-ip-answer` | `true`，允许正常私网 DNS 回答，便于局域网服务；不提供 DNS rebinding 防护保证 |
| `icmp-auto-reply` | `true`；ping 能通不代表远端 HTTPS 服务真实可用 |
| `udp-policy-not-supported-behaviour` | `REJECT`；节点不支持 UDP 时不回落直连 |
| `block-quic` | `all-proxy`；限制代理路径 QUIC，国内直连不受此项统一限制 |

`[Host]` 只保留 localhost 与微信本地回环映射；没有个人内网记录。配置不包含 `[MITM]`、证书、URL 重写或脚本，也不要求安装根证书。

### WebRTC 与语音

“设置 → UDP → 禁用 STUN”属于独立应用开关，模板不能控制。关注浏览器真实 IP 暴露时可开启并进行 WebRTC 检测；它也可能影响实时语音、视频会议和 P2P。OpenAI 的官方语音说明要求 UDP 3478（可使用 TCP 443 回退），因此不要把“禁用 STUN”宣传成对语音完全无影响。

语音异常时，先确认节点 UDP 支持、UDP 转发开启、语音 IP 规则仍有效，再评估 STUN 策略。若决定允许 STUN，应重新验证 WebRTC 出口，不要直接关闭 UDP 转发。

## 覆盖范围

- ChatGPT 网页/应用、OpenAI API、Codex 与 Sora 的核心域名、上传与静态资源、部分认证/支付/挑战资源、官方语音 IPv4 快照。
- Claude 网页/应用、Anthropic API 与 Claude Code 相关核心域名。
- Gemini 网页、AI Studio、Gemini API、CLI 入口，以及 Antigravity、NotebookLM 和相关语音域名。Google 通用登录与 OAuth、DeepMind 官网及 Google Labs 走默认代理。
- 常见国内网站/应用 CDN 及微软 Office、Outlook、登录、下载和更新的直连例外。

共享域名会影响其他使用同一域名的服务，例如 Cloudflare 验证、Stripe 脚本。Google 登录与 OAuth 是多个产品共用的认证入口，按默认代理处理，即使由 Gemini 等 AI 服务跳转过去也不会改走 `核心AI`。Google 图片/头像 CDN、第三方工具、外链、MCP、下载镜像以及各云平台托管 API 可能走 `PROXY`。本项目优先保持核心会话出口一致，**不承诺页面产生的每一条连接都走 `核心AI`**。新域名和服务端 IP 会变化，请按日志提交最小规则补充，避免添加整个云厂商或宽泛关键词。

### 国内 AI 直连策略

已知国内 AI 服务统一使用 DIRECT：DeepSeek、Kimi / Moonshot、MiniMax / 海螺、智谱 / GLM / Z.ai、通义 / Qwen、豆包 / 扣子 / 即梦、文心、腾讯混元 / 元宝、讯飞星火、百川、零一万物、阶跃、商汤日日新、天工、可灵。网页、API 和已知资源域名采用后缀规则，清单见 `rules/direct.list`。国内厂商的国际站（如 Z.ai、Coze）也按本策略直连，但其海外部署可能导致连接失败或较慢；必要时由使用者在自己的 Fork 中调整。

“全部直连”是路由策略，无法自动识别尚未收录的新品牌或新资源域名；发现遗漏后按实际域名补充，不用宽泛 AI 关键词判断国别。

## 验收与排错

先在“配置 → 测试规则”检查以下样本，再临时开启“数据 → 代理 / DNS”的日志并实际访问。规则测试只验证匹配结果，不证明连接出口、住宅属性或服务登录成功。

| 样本 | 预期 |
| --- | --- |
| `chatgpt.com`、`api.openai.com`、`files.oaiusercontent.com` | AI |
| `claude.ai`、`api.anthropic.com`、`platform.claude.com` | AI |
| `gemini.google.com`、`generativelanguage.googleapis.com` | AI |
| `antigravity.google.com`、`aiplatform.googleapis.com` | AI |
| `res.wx.qq.com`、`i0.hdslb.com`、`vfiles.gtimg.cn` | DIRECT |
| `outlook.office365.com`、`officecdn.microsoft.com` | DIRECT |
| `github.com`、`www.google.com`、`example.org` | 🐟 漏网之鱼（内置 PROXY） |

实际验证时确认：核心 AI 日志选中了预期节点；国内页面的图片/视频请求也为 DIRECT；国外随机测试域名没有被发送到大陆解析器；国内域名使用配置的国内加密解析。DNS 检测网站出现国内解析器需要结合查询类别判断，国内查询使用国内 DNS 是本方案的预期行为。

如果站点提供出口回显，可以对照实际 IP、地区及运营商。单凭节点名称或 IP 归属不能证明住宅线路，HTTP 403 也不单独等于路由失败。不要公开真实 IP、节点地址、访问日志或账户截图。验收完成后关闭临时日志。

可使用 [BrowserLeaks DNS 测试](https://browserleaks.com/dns) 检查浏览器发出的随机域名查询，再对照 SR 的 DNS 日志。页面显示的公网 IP 是网页连接出口，DNS 服务器列表是解析出口，两者应分别判断。如果检测站在个人规则中被设为 DIRECT，页面可能显示本地公网 IP；这不能单独证明 DNS 泄漏。解析服务器的 IPv6 地址也不等于本机存在 IPv6 旁路。

常见问题：

- **刚导入无法访问境外**：检查 `固定家宽` 是否已选节点、`香港节点` 正则是否匹配、`核心AI` 是否还选着 REJECT、首页默认代理、全局路由是否为“配置”。
- **节点测速通过，但国内外网页都打不开**：CONNECT 测试不能替代真实网页请求。先对照 DNS 日志与连接日志；macOS 若本机 HTTP 代理入口超时，而 TUN 路径正常，可改用上述 None（TUN Mode）后刷新网页。保持 VPN 连接与“配置”路由，再实测国内外网页，不能仅凭这一症状判定为 DNS 故障。
- **新版域名仍落到默认代理**：仓库或云端更新不代表本机已生效。手动更新远程配置，确认当前选中的是新版，再检查实际连接日志。
- **国内图片或视频慢**：查看具体资源域名，不只看网站主页；有些 CDN 使用海外地址。为确认可直连的域名添加精确规则，再测，避免整段云网络直连。
- **微软服务直连失败**：各地区线路不同。Fork 后移除 `rules/direct.list` 中相应例外，并检查国内上游表是否还有同域规则，再构建；或添加优先级更高的精确 PROXY 规则。
- **AI 登录地区不一致**：检查 `核心AI` / `固定家宽`、共享登录域名、应用缓存和真实出口；固定家宽请固定选稳定节点，避免测速频繁换地区。
- **自定义 API 网关/第三方云平台**：按自己的公开网关域名补规则，不要上传 API Key 或完整带鉴权参数的 URL。
- **版本兼容**：配置面向支持上述指令的 Shadowrocket；不能直接用于 Clash、Surge 或 sing-box。导入后必须检查编译错误和实际连接。

## 维护与测试

仓库结构：

```text
kidstudio.conf                可导入的长配置文件
AGENTS.md                     给编码助手的仓库约定（只推 Git、固定家宽无正则等）
data/base.conf                通用设置与代理分组（香港节点可正则；固定家宽无正则；无私有节点）
data/china-domains.txt         带归属信息的固定国内域名快照
data/openai-voice-cidrs.txt    官方语音 IPv4 快照
data/sources.json              来源版本与摘要
rules/ai.list                  核心 AI 域名
rules/direct.list              国内与微软直连补充
scripts/build.py               无网络、无第三方依赖的确定性构建
test/test_config.py            分流顺序、DNS、防误匹配与隐私格式检查
```

```bash
python3 scripts/build.py
python3 scripts/build.py --check
python3 -m unittest discover -s test -v
```

修改源文件后重新生成 `kidstudio.conf`，提交源文件与产物。CI 只做静态回归，不连接真实节点，也不等于 iOS/macOS 实机验收。首个公开模板未替换任何现有设备的配置；使用者需要按上面的步骤完成自己网络环境的验收。

提交 Issue 时只提供公开域名、脱敏的规则命中结果、系统/客户端版本和复现步骤。不要上传个人配置、订阅链接、凭证或原始流量。来源、固定版本和许可证详见 [SOURCES.md](SOURCES.md)。

