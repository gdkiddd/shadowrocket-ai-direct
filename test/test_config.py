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


class ConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / 'kidstudio.conf').read_text()
        cls.rules = [l for l in cls.text.split('[Rule]\n')[1].split('[Host]')[0].splitlines()
                     if l and not l.startswith('#')]
        # Pre-index rule types so route() stays fast against the ~130k-rule table
        # while keeping first-match-wins order across rule types.
        cls.exact, cls.suffix, cls.ports, cls.cidrs, cls.final = {}, {}, [], [], None
        for i, line in enumerate(cls.rules):
            t, *parts = line.split(',')
            if t == 'DOMAIN':
                cls.exact.setdefault(parts[0], (i, parts[1]))
            elif t == 'DOMAIN-SUFFIX':
                cls.suffix.setdefault(parts[0], (i, parts[1]))
            elif t == 'DST-PORT':
                cls.ports.append((i, int(parts[0]), parts[1]))
            elif t == 'IP-CIDR':
                cls.cidrs.append((i, ipaddress.ip_network(parts[0]), parts[1]))
            elif t == 'FINAL':
                cls.final = (i, parts[0])

    def route(self, host='', ip=None, port=443):
        # Small policy-order regression model, not a Shadowrocket emulator.
        hits = []
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
        self.assertEqual(self.final[0], len(self.rules) - 1, 'No final rule')
        return self.final[1]

    def test_reproducible(self):
        self.assertEqual(self.text, builder.build())
        self.assertEqual(self.text, (ROOT / 'ai-direct.conf').read_text())

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

    def test_config_structure(self):
        self.assertEqual(re.findall(r'^\[([^]]+)\]', self.text, re.M),
                         ['General', 'Proxy Group', 'Rule', 'Host'])
        self.assertEqual(len(self.rules), len(set(self.rules)))
        self.assertEqual(self.rules[-2:], ['GEOIP,CN,DIRECT', 'FINAL,🐟 漏网之鱼'])
        self.assertLess(len(self.rules), 200000)
        for rule in self.rules:
            t, *args = rule.split(',')
            self.assertIn(t, ['DOMAIN', 'DOMAIN-SUFFIX', 'DST-PORT', 'IP-CIDR', 'GEOIP', 'FINAL'])
            if t in ['DOMAIN', 'DOMAIN-SUFFIX']:
                self.assertRegex(args[0], r'^[a-z0-9_.-]+$')
            if t == 'IP-CIDR':
                ipaddress.ip_network(args[0])
            self.assertIn(args[0] if t == 'FINAL' else args[1], ['核心AI', 'PROXY', 'DIRECT', 'REJECT', '香港节点', '固定家宽', '🐟 漏网之鱼'])

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
        import re as _re
        m=_re.search(r'^固定家宽 = (.+)$', self.text, _re.M)
        self.assertIsNotNone(m)
        self.assertNotIn('policy-regex-filter', m.group(1))
        self.assertIn('核心AI = fallback,固定家宽,REJECT', self.text)
        self.assertIn('🐟 漏网之鱼 = select,PROXY', self.text)
        self.assertNotIn('美国VPS', self.text)
        self.assertNotIn('PROXY =', self.text.split('[Proxy Group]')[1].split('[Rule]')[0])
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
        self.assertNotRegex(self.text, r'(?im)^(?:password|token|secret|ca-p12|ca-passphrase)\s*=')
        self.assertNotRegex(self.text, r'(?i)(?:ss|vmess|vless|trojan)://|/Users/|/home/')
        self.assertNotIn('RULE-SET,', self.text)
        self.assertNotIn('DOMAIN-SET,', self.text)
        self.assertNotIn('server:system', self.text)

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

