"""Validate public release files; --seal records their SHA256 checksums."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = {'README.md', 'LICENSE.md', 'CITATION.cff', '.gitignore', '.gitattributes'}
FOLDERS = {'data', 'baselines', 'results', 'docs', 'scripts', 'tests', '.github'}
MANIFEST = ROOT / 'release_manifest.json'


def validate(seal=False):
    files = []
    for path in ROOT.rglob('*'):
        relative = path.relative_to(ROOT)
        if path.is_dir() or any(part in {'.git', '__pycache__', '.pytest_cache'} for part in relative.parts):
            continue
        if path == MANIFEST:
            continue
        if relative.parts[0] not in FOLDERS and relative.as_posix() not in ALLOWLIST:
            raise ValueError('Unexpected release file: ' + relative.as_posix())
        text = path.read_text(encoding='utf-8')
        patterns = [r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', r'\bR_[A-Za-z0-9]+\b',
                    r'\b[0-9a-f]{16}_abs\d+\b', r'(?i)\b[A-Z]:[\\/]',
                    r'github\.azc\.ext\.hp\.com', r'gh[pousr]_[A-Za-z0-9]{20,}']
        # Do not treat the scanner's own regex examples as exposed data.
        if relative.parts[0] not in {'scripts', 'tests'} and any(re.search(p, text) for p in patterns):
            raise ValueError('Potential private content in ' + relative.as_posix())
        files.append(path)
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    if seal:
        MANIFEST.write_text(json.dumps({'version': '1.0.0', 'sha256': hashes}, indent=2) + '\n', encoding='utf-8')
    else:
        expected = json.loads(MANIFEST.read_text(encoding='utf-8'))['sha256']
        if expected != hashes:
            raise ValueError('Release content does not match manifest')
    print(f'Validated {len(files)} public files; no prohibited direct identifiers detected.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    validate(parser.parse_args().seal)
