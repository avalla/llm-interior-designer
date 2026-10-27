# Structural checks for CI (plain Python, no FreeCAD):
# - skills follow the Agent Skills format (frontmatter name == folder, non-empty description <= 1024 chars)
# - .claude/skills is a symlink to .agents/skills
# - every evals/fixtures/*/expected.json is valid and well formed
# - relative links in Markdown files point to existing files
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
errors = []

for skill in sorted(glob.glob(".agents/skills/*/SKILL.md")):
    folder = os.path.basename(os.path.dirname(skill))
    text = open(skill).read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        errors.append("%s: missing frontmatter" % skill)
        continue
    meta = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    name, desc = meta.get("name", "").strip(), meta.get("description", "").strip()
    if name != folder:
        errors.append("%s: name '%s' differs from folder '%s'" % (skill, name, folder))
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        errors.append("%s: invalid name '%s'" % (skill, name))
    if not desc or len(desc) > 1024:
        errors.append("%s: description empty or longer than 1024 characters" % skill)

if not (os.path.islink(".claude/skills") and os.path.realpath(".claude/skills") == os.path.realpath(".agents/skills")):
    errors.append(".claude/skills must be a symlink to ../.agents/skills")

for exp in sorted(glob.glob("evals/fixtures/*/expected.json")):
    try:
        data = json.load(open(exp))
        for d in data["defects"]:
            assert {"id", "text", "engine", "keywords"} <= set(d), "missing keys in %s" % d.get("id")
            assert all(isinstance(g, list) and g for g in d["keywords"]), "empty keyword group in %s" % d["id"]
        if not os.path.exists(os.path.join(os.path.dirname(exp), "project.py")):
            errors.append("%s: fixture without project.py" % exp)
    except Exception as exc:  # noqa: BLE001 - report every malformed file
        errors.append("%s: %s" % (exp, exc))

for md in glob.glob("**/*.md", recursive=True):
    if md.startswith(("archive/", "evals/results/")) or "/output/" in md:
        continue
    for target in re.findall(r"\]\(([^)#\s]+)\)", open(md).read()):
        if re.match(r"[a-z]+://", target) or target.startswith("mailto:"):
            continue
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(md), target))):
            errors.append("%s: broken link %s" % (md, target))

print("\n".join(errors) if errors else "repository checks OK")
sys.exit(1 if errors else 0)
