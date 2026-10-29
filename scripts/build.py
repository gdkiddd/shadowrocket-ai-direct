#!/usr/bin/env python3
"""Build the offline, searchable configuration from reviewable local sources."""
from pathlib import Path
import argparse
import ipaddress

ROOT = Path(__file__).resolve().parents[1]


def lines(path):
    return [s.strip() for s in (ROOT / path).read_text().splitlines()
            if s.strip() and not s.lstrip().startswith('#')]


def build():
    result = [(ROOT / 'data/base.conf').read_text().rstrip()]
    rules = []
    rules += [s + ',核心AI' for s in lines('rules/ai.list')]
    # Official OpenAI voice server IP snapshot; add before all geographic rules.
    rules += ['IP-CIDR,' + str(ipaddress.ip_network(s)) + ',核心AI,no-resolve'
              for s in lines('data/openai-voice-cidrs.txt')]
    rules += ['DOMAIN,localhost,DIRECT', 'DOMAIN-SUFFIX,local,DIRECT',
              'DOMAIN-SUFFIX,home.arpa,DIRECT']
    rules += ['IP-CIDR,' + s + ',DIRECT,no-resolve' for s in
              ['10.0.0.0/8', '127.0.0.0/8', '169.254.0.0/16',
               '172.16.0.0/12', '192.168.0.0/16']]
    rules += [s + ',DIRECT' for s in lines('rules/direct.list')]
    for domain in lines('data/china-domains.txt'):
        assert ',' not in domain and ' ' not in domain, domain
        if domain.startswith('.'):
            rules.append('DOMAIN-SUFFIX,' + domain[1:] + ',DIRECT')
        else:
            rules.append('DOMAIN,' + domain + ',DIRECT')
    # ChinaIPs snapshot; keeps GEOIP,CN as a coarse fallback only.
    rules += ['IP-CIDR,' + str(ipaddress.ip_network(s)) + ',DIRECT,no-resolve'
              for s in lines('data/china-ips.txt')]
    result += list(dict.fromkeys(rules))
    result += ['# IP geography is a fallback, not a guarantee for every CDN.',
               'GEOIP,CN,DIRECT', 'FINAL,🐟 漏网之鱼', '', '[Host]',
               'localhost = 127.0.0.1', 'localhost.weixin.qq.com = 127.0.0.1']
    return '\n'.join(result) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = ROOT / 'kidstudio.conf'
    text = build()
    if args.check:
        assert output.read_text() == text, 'Regenerate with python3 scripts/build.py'
        assert (ROOT / 'ai-direct.conf').read_text() == text, 'Legacy URL alias is stale'
        print('Generated configuration matches sources')
    else:
        output.write_text(text)
        (ROOT / 'ai-direct.conf').write_text(text)  # Keep existing imported URLs working.
        print(f'Built {output.name}: {len(text.encode())} bytes')

