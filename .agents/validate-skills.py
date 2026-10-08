#!/usr/bin/env python3
"""Validate project skills in .agents/skills/ and print a skill index."""
import re, sys
from pathlib import Path

root = Path(__file__).resolve().parent / "skills"
errors = []
for d in sorted(p for p in root.iterdir() if p.is_dir()):
    f = d / "SKILL.md"
    if not f.is_file():
        errors.append(f"{d.name}: missing SKILL.md")
        continue
    m = re.match(r"---\n(.*?)\n---\n", f.read_text(encoding="utf-8"), re.S)
    meta = dict(
        (k.strip(), v.strip())
        for k, _, v in (l.partition(":") for l in (m.group(1).splitlines() if m else []))
        if k and not k.startswith(" ")
    )
    if not m:
        errors.append(f"{d.name}: SKILL.md lacks front matter")
    elif meta.get("name", "").strip("\"'") != d.name:
        errors.append(f"{d.name}: front matter 'name' must equal directory name")
    elif not meta.get("description"):
        errors.append(f"{d.name}: missing 'description'")
    else:
        print(f"- {d.name}: {meta['description'][:100]}")
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
