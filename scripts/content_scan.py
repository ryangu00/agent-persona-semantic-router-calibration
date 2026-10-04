"""Original content-scan rules; language patterns are Unicode-escaped."""
import re
import json

UNSAFE_RULES = [
    ('fetch_exec', re.compile('\\b(?:curl|wget)\\b[^\\n]*\\|\\s*(?:sh|bash|zsh)\\b')),
    ('fetch_cmd', re.compile('\\b(?:curl|wget)\\b')),
    ('pip_install', re.compile('\\bpip3?\\s+install\\b')),
    ('npm_install', re.compile('\\b(?:npm\\s+(?:i|install)|brew\\s+install)\\b')),
    ('secret_sk', re.compile('\\bsk-[A-Za-z0-9]{20,}')),
    ('secret_ghp', re.compile('\\bghp_[A-Za-z0-9]{20,}')),
    ('secret_akia', re.compile('\\bAKIA[0-9A-Z]{12,}')),
    ('secret_pem', re.compile('-----[B]EGIN [A-Z ]*PRIVATE KEY')),
    ('exfil_wording_en', re.compile('(?i)\\b(?:exfiltrat\\w*|send|upload|post|transmit|forward|leak|beacon)\\b[^\\n]{0,60}?\\b(?:to\\s+(?:an?\\s+|the\\s+)?(?:external|remote|third[- ]party|server|endpoint|url|api)|outside|externally)\\b')),
    ('credential_wording_en', re.compile('(?i)\\b(?:read|access|steal|dump|retrieve|collect|expose)\\b[^\\n]{0,40}?\\b(?:credential|password|passwd|secret|api[ _-]?key|access[ _-]?key|token|\\.env|keychain)\\b')),
    ('env_wording', re.compile('(?i)\\b(?:print|dump|echo|cat|read|leak|expose|exfiltrat\\w*|steal)\\b[^\\n]{0,30}(?:os\\.environ|process\\.env|environment\\s+variables?)|(?:\u8bfb\u53d6|\u5bfc\u51fa|\u7a83\u53d6|\u6253\u5370)[^\\n]{0,10}\u73af\u5883\u53d8\u91cf')),
    ('exfil_wording_zh', re.compile('(?:\u53d1\u9001|\u4e0a\u4f20|\u63d0\u4ea4|\u56de\u4f20|\u4f20\u8f93|\u5916\u53d1|\u6cc4\u9732|\u7a83\u53d6)[^\\n]{0,20}(?:\u5916\u90e8|\u8fdc\u7a0b|\u7b2c\u4e09\u65b9|\u670d\u52a1\u5668|\u63a5\u53e3|\u5730\u5740|\u90ae\u7bb1)')),
    ('credential_wording_zh', re.compile('(?:\u8bfb\u53d6|\u8bbf\u95ee|\u83b7\u53d6|\u7a83\u53d6|\u5bfc\u51fa|\u6536\u96c6)[^\\n]{0,15}(?:\u51ed\u636e|\u5bc6\u7801|\u5bc6\u94a5|\u4ee4\u724c|\\.env)')),
]

def scan_content(text):
    reasons = []
    for name, rx in UNSAFE_RULES:
        if rx.search(text):
            if name not in reasons:
                reasons.append(name)
    return (len(reasons) == 0, reasons)

def parse_json_stream(text):
    dec = json.JSONDecoder()
    out, i, n = ([], 0, len(text))
    while i < n:
        while i < n and text[i] in ' \r\n\t':
            i += 1
        if i >= n:
            break
        obj, i = dec.raw_decode(text, i)
        out.append(obj)
    return out

def norm_status(st):
    if st == 'added' or st == 'copied':
        return 'added'
    if st == 'removed':
        return 'removed'
    return 'modified'
