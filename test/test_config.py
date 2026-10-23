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

    def route(self, host='', ip=None, port=443):
        # Small policy-order regression model, not a Shadowrocket emulator.
        for line in self.rules:
            t, *parts = line.split(',')
            if t == 'DST-PORT' and int(parts[0]) == port:
                return parts[1]
            if t == 'DOMAIN' and host == parts[0]:
                return parts[1]
            if t == 'DOMAIN-SUFFIX' and (host == parts[0] or host.endswith('.' + parts[0])):
                return parts[1]
            if t == 'IP-CIDR' and ip and ipaddress.ip_address(ip) in ipaddress.ip_network(parts[0]):
                return parts[1]
            if t == 'FINAL':
                return parts[0]
        self.fail('No final rule')

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
                self.assertEqual(self.route(host), 'AI')
                self.assertEqual(self.route('api.' + host), 'AI')
                self.assertEqual(self.route(host + '.example.org'), 'PROXY')

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
                self.assertEqual(self.route(host), 'AI')

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
                self.assertEqual(self.route(host), 'PROXY')

    def test_plain_dns_fails_closed_before_geographic_rules(self):
        self.assertEqual(self.rules[0], 'DST-PORT,53,REJECT')
        for host in ['www.baidu.com', 'api.openai.com', 'example.org']:
            self.assertEqual(self.route(host, port=53), 'REJECT')

    def test_voice_ips_ai(self):
        for prefix in builder.lines('data/openai-voice-cidrs.txt'):
            self.assertEqual(self.route(ip=str(ipaddress.ip_network(prefix).network_address)), 'AI')

    def test_config_structure(self):
        self.assertEqual(re.findall(r'^\[([^]]+)\]', self.text, re.M),
                         ['General', 'Proxy Group', 'Rule', 'Host'])
        self.assertEqual(len(self.rules), len(set(self.rules)))
        self.assertEqual(self.rules[-2:], ['GEOIP,CN,DIRECT', 'FINAL,PROXY'])
        self.assertLess(len(self.rules), 6000)
        for rule in self.rules:
            t, *args = rule.split(',')
            self.assertIn(t, ['DOMAIN', 'DOMAIN-SUFFIX', 'DST-PORT', 'IP-CIDR', 'GEOIP', 'FINAL'])
            if t in ['DOMAIN', 'DOMAIN-SUFFIX']:
                self.assertRegex(args[0], r'^[a-z0-9_.-]+$')
            if t == 'IP-CIDR':
                ipaddress.ip_network(args[0])
            self.assertIn(args[0] if t == 'FINAL' else args[1], ['AI', 'PROXY', 'DIRECT', 'REJECT'])

    def test_dns_settings_and_groups(self):
        for key in ['dns-fallback-system', 'dns-direct-system', 'dns-direct-fallback-proxy', 'ipv6']:
            self.assertIn(key + ' = false', self.text)
        self.assertIn('hijack-dns = *:53', self.text)
        self.assertIn('udp-policy-not-supported-behaviour = REJECT', self.text)
        for line in self.text.splitlines():
            if line.startswith(('dns-server =', 'fallback-dns-server =')):
                self.assertTrue(all(u.strip().endswith('#proxy') for u in line.split(' = ')[1].split(',')))
        self.assertIn('AI = select,REJECT,AI-NODE,policy-select-name=REJECT', self.text)
        self.assertIn('PROXY = select,REJECT,PROXY-NODE,policy-select-name=REJECT', self.text)

    def test_public_artifact_has_no_credentials_or_personal_paths(self):
        self.assertNotRegex(self.text, r'(?im)^(?:password|token|secret|ca-p12|ca-passphrase)\s*=')
        self.assertNotRegex(self.text, r'(?i)(?:ss|vmess|vless|trojan)://|/Users/|/home/')
        self.assertNotIn('RULE-SET,', self.text)
        self.assertNotIn('DOMAIN-SET,', self.text)
        self.assertNotIn('server:system', self.text)

    def test_upstream_snapshot_hash(self):
        import hashlib
        info = json.loads((ROOT / 'data/sources.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT / 'data/china-domains.txt').read_bytes()).hexdigest(),
                         info['china']['sha256'])


if __name__ == '__main__':
    unittest.main()

