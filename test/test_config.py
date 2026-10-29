import importlib.util
import ipaddress
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

POLICIES = ['核心AI', 'DIRECT', 'REJECT', '🐟 漏网之鱼', '香港节点', '固定家宽']
LAN_IPV4 = ['10.0.0.0/8', '127.0.0.0/8', '169.254.0.0/16',
            '172.16.0.0/12', '192.168.0.0/16']


def section(text, name):
    return text.split('[' + name + ']\n')[1].split('\n[')[0]


class ConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / 'kidstudio.conf').read_text()
        cls.rules = [l for l in section(cls.text, 'Rule').splitlines()
                     if l and not l.startswith('#')]
        # Expand RULE-SET / DOMAIN-SET against the locally generated files so
        # routing order can be checked without network access.
        cls.expanded = []
        for line in cls.rules:
            kind, *args = line.split(',')
            if kind in ('RULE-SET', 'DOMAIN-SET'):
                name = args[0].rsplit('/', 1)[-1]
                path = ROOT / 'rulesets' / name
                assert path.exists(), f'Missing generated set {path}'
                policy = args[1]
                for entry in path.read_text().splitlines():
                    entry = entry.strip()
                    if not entry or entry.startswith('#'):
                        continue
                    if kind == 'DOMAIN-SET':
                        cls.expanded.append(('DOMAIN-SET', entry, policy))
                    else:
                        cls.expanded.append((entry.split(',')[0], entry, policy))
            else:
                cls.expanded.append((kind, line, line.split(',')[-1]
                                     if kind == 'FINAL' else line.split(',')[2]))

        # Pre-index the expanded table (first match wins by original order).
        cls.exact, cls.suffix, cls.ports, cls.cidrs = {}, {}, [], []
        cls.final = None
        for i, (kind, raw, policy) in enumerate(cls.expanded):
            if kind == 'DST-PORT':
                cls.ports.append((i, int(raw.split(',')[1]), policy))
            elif kind == 'IP-CIDR':
                cls.cidrs.append((i, ipaddress.ip_network(raw.split(',')[1]), policy))
            elif kind == 'DOMAIN':
                cls.exact.setdefault(raw.split(',')[1].lower(), (i, policy))
            elif kind == 'DOMAIN-SUFFIX':
                cls.suffix.setdefault(raw.split(',')[1].lower(), (i, policy))
            elif kind == 'DOMAIN-SET':
                host = raw[1:] if raw.startswith('.') else raw
                cls.suffix.setdefault(host.lower(), (i, policy))
                if not raw.startswith('.'):
                    cls.exact.setdefault(host.lower(), (i, policy))
            elif kind == 'FINAL':
                cls.final = (i, policy)

    def route(self, host='', ip=None, port=443):
        # Small policy-order regression model, not a Shadowrocket emulator.
        # GEOIP,CN is intentionally not modelled; FINAL stands in for it here.
        hits = []
        host = host.lower()
        if host:
            if host in self.exact:
                hits.append(self.exact[host])
            labels = host.split('.')
            for n in range(len(labels)):
                hit = self.suffix.get('.'.join(labels[n:]))
                if hit:
                    hits.append(hit)
        hits += [(i, policy) for i, p, policy in self.ports if p == port]
        if ip:
            addr = ipaddress.ip_address(ip)
            hits += [(i, policy) for i, net, policy in self.cidrs if addr in net]
        if hits:
            return min(hits)[1]
        self.assertIsNotNone(self.final, 'No final rule')
        return self.final[1]

    def test_reproducible(self):
        self.assertEqual(self.text, builder.build())
        self.assertEqual(self.text, (ROOT / 'ai-direct.conf').read_text())
        generated = builder.build_rulesets()
        self.assertEqual(sorted(generated), sorted(
            p.name for p in (ROOT / 'rulesets').glob('*.list')))
        for name, text in generated.items():
            with self.subTest(ruleset=name):
                self.assertEqual(text, (ROOT / 'rulesets' / name).read_text())

    def test_conf_is_thin(self):
        lines = self.text.splitlines()
        self.assertLess(len(lines), 200, 'Config should stay a thin shell')
        self.assertLess(len(self.text.encode()), 50 * 1024, 'Config should stay small')
        # No bulk tables inline: the biggest rule class must be the LAN block.
        inline_types = [r.split(',')[0] for r in self.rules]
        self.assertLessEqual(inline_types.count('DOMAIN'), 1)
        self.assertLessEqual(inline_types.count('DOMAIN-SUFFIX'), 2)
        self.assertLessEqual(inline_types.count('IP-CIDR'), len(LAN_IPV4))

    def test_remote_rulesets_and_policies(self):
        raw = builder.RAW + '/rulesets/'
        expected = [
            f'RULE-SET,{raw}core-ai.list,核心AI',
            f'RULE-SET,{raw}direct-extra.list,DIRECT',
            f'DOMAIN-SET,{raw}china-domains.list,DIRECT',
            f'RULE-SET,{raw}china-ips.list,DIRECT',
        ]
        for line in expected:
            with self.subTest(rule=line):
                self.assertIn(line, self.rules)
        self.assertEqual([r for r in self.rules if r.split(',')[0] in
                          ('RULE-SET', 'DOMAIN-SET')], expected)
        # Order: core AI first, then direct exceptions, then the bulk sets.
        order = [self.rules.index(line) for line in expected]
        self.assertEqual(order, sorted(order))

    def test_rulesets_are_policy_free(self):
        for name in ['core-ai.list', 'direct-extra.list', 'china-ips.list']:
            with self.subTest(ruleset=name):
                entries = [l for l in (ROOT / 'rulesets' / name).read_text().splitlines()
                           if l and not l.startswith('#')]
                self.assertTrue(entries)
                for entry in entries:
                    fields = entry.split(',')
                    self.assertIn(fields[0], ['DOMAIN', 'DOMAIN-SUFFIX', 'IP-CIDR'])
                    self.assertNotIn(fields[-1], POLICIES)
                    self.assertLessEqual(len(fields), 3)
        domains = [l for l in (ROOT / 'rulesets' / 'china-domains.list').read_text().splitlines()
                   if l and not l.startswith('#')]
        self.assertTrue(domains)
        self.assertTrue(all(',' not in d for d in domains))

    def test_extended_google_ai(self):
        for host in ['antigravity.google', 'antigravity.google.com',
                     'antigravity-unleash.goog', 'gemini.google',
                     'codeassist.google', 'codeassist.google.com',
                     'geminicli.com', 'notebooklm.google',
                     'notebooklm.google.com', 'voice.telephony.goog']:
            with self.subTest(host=host):
                self.assertEqual(self.route(host), '核心AI')
                self.assertEqual(self.route('api.' + host), '核心AI')
                self.assertEqual(self.route(host + '.example.org'), '🐟 漏网之鱼')

    def test_domestic_ai(self):
        for host in ['api.deepseek.com', 'www.kimi.com', 'api.moonshot.ai',
                     'api.minimaxi.com', 'api.minimax.io', 'hailuoai.video',
                     'api.z.ai', 'open.bigmodel.cn', 'chatglm.cn', 'qwen.ai',
                     'qwenlm.ai', 'dashscope.aliyuncs.com', 'www.doubao.com',
                     'www.coze.cn', 'www.coze.com', 'jimeng.jianying.com',
                     'yiyan.baidu.com', 'qianfan.baidubce.com', 'yuanbao.tencent.com',
                     'hunyuan.tencent.com', 'spark-api.xf-yun.com',
                     'api.baichuan-ai.com', 'api.lingyiwanwu.com',
                     'api.stepfun.com', 'sensenova.cn', 'tiangong.cn', 'klingai.com']:
            with self.subTest(host=host):
                self.assertEqual(self.route(host), 'DIRECT')

    def test_core_ai_before_direct(self):
        for host in ['chatgpt.com', 'ws.chatgpt.com', 'api.openai.com',
                     'files.oaiusercontent.com', 'cdn.oaistatic.com',
                     'claude.ai', 'api.anthropic.com', 'platform.claude.com',
                     'gemini.google.com', 'share.gemini.google',
                     'gemini.gstatic.com', 'robinfrontend-pa.googleapis.com',
                     'webchannel-robinfrontend-pa.googleapis.com',
                     'generativelanguage.googleapis.com',
                     'daily-cloudcode-pa.googleapis.com',
                     'cloudcode-pa.googleapis.com', 'aicode.googleapis.com',
                     'antigravity.google.com', 'aiplatform.googleapis.com',
                     'challenges.cloudflare.com']:
            with self.subTest(host=host):
                self.assertEqual(self.route(host), '核心AI')

    def test_domestic_resources_and_microsoft(self):
        for host in ['res.wx.qq.com', 'i0.hdslb.com', 'upos-sz-mirrorcos.bilivideo.com',
                     'vfiles.gtimg.cn', 'www.taobao.com', 'www.douyin.com',
                     'outlook.office365.com', 'officecdn.microsoft.com',
                     'login.microsoftonline.com', 'example.cn']:
            with self.subTest(host=host):
                self.assertEqual(self.route(host), 'DIRECT')

    def test_unknown_and_google_are_proxy(self):
        for host in ['accounts.google.com', 'oauth2.googleapis.com',
                     'oauth2.mtls.googleapis.com', 'openidconnect.googleapis.com',
                     'deepmind.google', 'labs.google',
                     'example.org', 'www.google.com', 'github.com',
                     'copilot.microsoft.com', 'chatgpt.com.example.org',
                     'gemini.google.com.example.org']:
            with self.subTest(host=host):
                self.assertEqual(self.route(host), '🐟 漏网之鱼')

    def test_plain_dns_fails_closed_before_geographic_rules(self):
        self.assertEqual(self.rules[0], 'DST-PORT,53,REJECT')
        for host in ['www.baidu.com', 'api.openai.com', 'example.org']:
            self.assertEqual(self.route(host, port=53), 'REJECT')

    def test_voice_ips_ai(self):
        for prefix in builder.lines('data/openai-voice-cidrs.txt'):
            self.assertEqual(self.route(ip=str(ipaddress.ip_network(prefix).network_address)), '核心AI')

    def test_lan_and_china_ips_direct(self):
        for net in LAN_IPV4:
            self.assertEqual(self.route(ip=str(ipaddress.ip_network(net).network_address)), 'DIRECT')
        for ip in ['1.0.1.5', '220.181.38.148']:
            with self.subTest(ip=ip):
                self.assertEqual(self.route(ip=ip), 'DIRECT')
        for ip in ['8.8.8.8', '104.16.1.1']:
            with self.subTest(ip=ip):
                self.assertEqual(self.route(ip=ip), '🐟 漏网之鱼')

    def test_config_structure(self):
        self.assertEqual(re.findall(r'^\[([^]]+)\]', self.text, re.M),
                         ['General', 'Proxy Group', 'Rule', 'Host'])
        self.assertEqual(len(self.rules), len(set(self.rules)))
        self.assertEqual(self.rules[-2:], ['GEOIP,CN,DIRECT', 'FINAL,🐟 漏网之鱼'])
        for rule in self.rules:
            t, *args = rule.split(',')
            self.assertIn(t, ['DOMAIN', 'DOMAIN-SUFFIX', 'DST-PORT', 'IP-CIDR',
                              'RULE-SET', 'DOMAIN-SET', 'GEOIP', 'FINAL'])
            if t in ['DOMAIN', 'DOMAIN-SUFFIX']:
                self.assertRegex(args[0], r'^[a-z0-9_.-]+$')
            if t == 'IP-CIDR':
                ipaddress.ip_network(args[0])
            if t in ('RULE-SET', 'DOMAIN-SET'):
                self.assertRegex(args[0], r'^https://raw\.githubusercontent\.com/')
                self.assertRegex(args[0], r'\.list$')
            self.assertIn(args[0] if t == 'FINAL' else args[1], POLICIES)

    def test_dns_settings_and_groups(self):
        for key in ['dns-fallback-system', 'dns-direct-system', 'dns-direct-fallback-proxy', 'ipv6']:
            self.assertIn(key + ' = false', self.text)
        self.assertIn('hijack-dns = *:53', self.text)
        self.assertIn('udp-policy-not-supported-behaviour = REJECT', self.text)
        for line in self.text.splitlines():
            if line.startswith(('dns-server =', 'fallback-dns-server =')):
                self.assertTrue(all(u.strip().endswith('#proxy') for u in line.split(' = ')[1].split(',')))
        self.assertIn('香港节点 = url-test,', self.text)
        self.assertIn('policy-regex-filter=香港', self.text)
        self.assertIn('固定家宽 = url-test,', self.text)
        self.assertNotIn('policy-regex-filter=家宽|ISP|住宅', self.text)
        # 固定家宽 must not carry any policy-regex-filter
        m = re.search(r'^固定家宽 = (.+)$', self.text, re.M)
        self.assertIsNotNone(m)
        self.assertNotIn('policy-regex-filter', m.group(1))
        self.assertIn('核心AI = fallback,固定家宽,REJECT', self.text)
        self.assertIn('🐟 漏网之鱼 = select,PROXY', self.text)
        self.assertNotIn('美国VPS', self.text)
        self.assertNotIn('PROXY =', section(self.text, 'Proxy Group'))
        self.assertNotIn('家宽-NODE', self.text)
        self.assertNotIn('VPS-NODE', self.text)
        self.assertNotIn('PROXY-NODE', self.text)
        # Public artifact must not embed private subscription node names/IPs.
        self.assertNotIn('AT&T', self.text)
        self.assertNotIn('resip', self.text.lower())
        self.assertNotIn('12.104.15.', self.text)
        self.assertNotIn('CF-TROJAN', self.text)
        self.assertNotIn('ZGO-LA-', self.text)
        self.assertNotIn('WEBSHARE', self.text)

    def test_public_artifact_has_no_credentials_or_personal_paths(self):
        artifacts = [self.text, (ROOT / 'ai-direct.conf').read_text()]
        artifacts += [p.read_text() for p in (ROOT / 'rulesets').glob('*.list')]
        for text in artifacts:
            self.assertNotRegex(text, r'(?im)^(?:password|token|secret|ca-p12|ca-passphrase)\s*=')
            self.assertNotRegex(text, r'(?i)(?:ss|vmess|vless|trojan)://|/Users/|/home/')
            self.assertNotIn('server:system', text)
        # RULE-SET / DOMAIN-SET are expected now, but only over the rolling raw URL.
        for line in self.rules:
            if line.split(',')[0] in ('RULE-SET', 'DOMAIN-SET'):
                self.assertIn('raw.githubusercontent.com/gdkiddd/shadowrocket-ai-direct/main/', line)

    def test_upstream_snapshot_hash(self):
        import hashlib
        info = json.loads((ROOT / 'data/sources.json').read_text())
        for key, path in [('china', 'data/china-domains.txt'),
                          ('china_ips', 'data/china-ips.txt')]:
            with self.subTest(snapshot=key):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                                 info[key]['sha256'])


if __name__ == '__main__':
    unittest.main()
