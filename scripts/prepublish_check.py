#!/usr/bin/env python3
"""Check Git-tracked source files before a public research-prototype release.

This is a conservative hygiene screen, not a guarantee that data are non-sensitive.
Review the final `git ls-files` list yourself before pushing.
"""
from __future__ import annotations
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {'README.md','README_FA.md','LICENSE','CITATION.cff','.gitignore',
            'SECURITY.md','pyproject.toml','docs/PREPUBLISH_AUDIT.md',
            '.github/workflows/ci.yml','tests/test_core.py'}
UNSAFE_ENDINGS = {'.pdf','.sqlite','.sqlite3','.db','.pt','.pth','.safetensors','.bin',
                  '.pem','.key','.p12','.pfx','.ckpt','.faiss','.zip'}
PATTERNS = {
    'private key header': re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),
    'GitHub personal access token': re.compile(rb'(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}'),
    'OpenAI-like secret token': re.compile(rb'\bsk-[A-Za-z0-9_-]{30,}\b'),
    'AWS access key': re.compile(rb'\bAKIA[0-9A-Z]{16}\b'),
}

def tracked_files() -> list[Path]:
    result = subprocess.run(['git','ls-files','-z'],cwd=ROOT,check=True,capture_output=True)
    return [ROOT / x.decode('utf-8') for x in result.stdout.split(b'\x00') if x]

def main() -> int:
    files=tracked_files()
    names={str(f.relative_to(ROOT)) for f in files}
    errors=[]
    for name in sorted(REQUIRED-names): errors.append('Required file absent: '+name)
    for f in files:
        name=str(f.relative_to(ROOT))
        if not f.is_file(): errors.append('Tracked file missing: '+name);continue
        if f.suffix.lower() in UNSAFE_ENDINGS: errors.append('Prohibited binary/private extension: '+name)
        if f.stat().st_size>5_000_000: errors.append('File larger than 5 MB: '+name)
        if name.startswith(('data/private/','data/raw/','data/uploads/','models/','checkpoints/')):
            errors.append('Private model or data path: '+name)
        if f.stat().st_size<=5_000_000:
            blob=f.read_bytes()
            for label,pat in PATTERNS.items():
                if pat.search(blob): errors.append(f'Possible {label}: {name}')
    if errors:
        print('PUBLICATION SAFETY CHECK FAILED')
        for problem in errors: print(' -',problem)
        return 1
    print(f'PASS: {len(files)} tracked files; required docs included; no known high-risk extension, oversized file or obvious token pattern.')
    print('Manual license, privacy and credential inspection is still necessary.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
