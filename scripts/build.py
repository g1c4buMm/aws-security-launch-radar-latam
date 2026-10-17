#!/usr/bin/env python3
"""Build for the AWS Security Weekly Radar kit. Maintainers only; people using the kit never run it.

    python3 scripts/build.py           build everything
    python3 scripts/build.py --check   check that the repository matches the source (CI)

Single source:
- skills/<name>/                 the skill (SKILL.md, scripts, catalog)
- examples/items-snapshot.json   one real week of collected items
- examples/radar-<lang>.json     sample radars written against that snapshot
- examples/config-<lang>.json    one config per report language

Generated from the source:
- .claude/skills/<name>/         copy that Claude Code discovers
- examples/email-<lang>.html     rendered email, plus .txt, slack-<lang>.json and linkedin-<lang>.txt/.html

Checks:
- every sample radar validates; examples/radar-invalid.json is rejected for the expected reasons
- every script compiles; SKILL.md `name` matches its folder
- README and docs mention every script and language, and their relative links resolve
- no email address outside the fictional domains
"""
import filecmp
import importlib.util
import json
import py_compile
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = "--check" in sys.argv
SKILLS = ["security-launch-radar"]
LANGUAGES = ["en", "pt-BR", "es"]
SCRIPTS = ["fetch_feeds.py", "validate_radar.py", "render.py", "send_slack.py", "export_tracker.py", "update_kit_page.py", "setup.py"]
DOCS = ["README.md", "docs"]
FICTIONAL_DOMAINS = ("example.com", "your-company.com", "sua-empresa.com.br", "su-empresa.com")
INVALID_REASONS = ["unknown fields", "is a bulletin", "contains a URL", "not in items.json", "repeated"]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")

problems = []


def problem(msg):
    problems.append(msg)


def write(rel, content):
    """Write a generated file, or in --check mode report it if it differs."""
    path = ROOT / rel
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        return
    if CHECK:
        problem("out of date: %s (run python3 scripts/build.py)" % rel)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("  wrote", rel)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


# ---------------- skills ----------------

def tree_differs(a, b):
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__", ".DS_Store"])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return True
    return any(tree_differs(Path(a) / d, Path(b) / d) for d in cmp.common_dirs)


def sync_skill(name):
    src, dst = ROOT / "skills" / name, ROOT / ".claude" / "skills" / name
    head = (src / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
    m = re.search(r"^name:\s*(\S+)", head, re.M)
    if not m or m.group(1) != name:
        problem("skills/%s/SKILL.md: name must be '%s'" % (name, name))
    if dst.exists() and not tree_differs(src, dst):
        return
    if CHECK:
        problem("out of date: .claude/skills/%s (run python3 scripts/build.py)" % name)
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=IGNORE)
    print("  synced .claude/skills/%s" % name)


# ---------------- examples ----------------

def examples(scripts_dir):
    validate = load_module("validate_radar", scripts_dir / "validate_radar.py")
    render = load_module("render", scripts_dir / "render.py")
    items = load_json("examples/items-snapshot.json")
    for lang in LANGUAGES:
        radar = load_json("examples/radar-%s.json" % lang)
        config = load_json("examples/config-%s.json" % lang)
        if config.get("language") != lang:
            problem("examples/config-%s.json: language must be '%s'" % (lang, lang))
        errors = validate.validate(radar, items)
        if errors:
            problem("examples/radar-%s.json is invalid: %s" % (lang, "; ".join(errors)))
            continue
        c = render.context(radar, items, config)
        write("examples/email-%s.html" % lang, render.render_html(radar, c))
        write("examples/email-%s.txt" % lang, render.render_text(radar, c))
        write("examples/slack-%s.json" % lang, json.dumps(render.render_slack(radar, c), ensure_ascii=False, indent=1) + "\n")
        post, links = render.render_linkedin(radar, c)
        write("examples/linkedin-%s.txt" % lang, post + "\n")
        write("examples/linkedin-%s.html" % lang, render.render_linkedin_html(post, links, c))
        if render.li_len(post) > 3000 or "\u2014" in post:
            problem("examples/linkedin-%s.txt: over 3000 characters or has an em dash" % lang)
    errors = validate.validate(load_json("examples/radar-invalid.json"), items)
    for reason in INVALID_REASONS:
        if not any(reason in e for e in errors):
            problem("examples/radar-invalid.json: validator no longer reports '%s'" % reason)


# ---------------- checks ----------------

def compile_scripts():
    for path in list((ROOT / "skills").rglob("*.py")) + [ROOT / "setup.py", Path(__file__)]:
        try:
            py_compile.compile(str(path), doraise=True, cfile=str(ROOT / ".build-cache.pyc"))
        except py_compile.PyCompileError as exc:
            problem("does not compile: %s (%s)" % (path.relative_to(ROOT), exc.msg))
    (ROOT / ".build-cache.pyc").unlink(missing_ok=True)


def doc_files():
    files = []
    for entry in DOCS:
        p = ROOT / entry
        files += sorted(p.glob("*.md")) if p.is_dir() else [p]
    return files


def check_docs():
    files = doc_files()
    text = "\n".join(f.read_text(encoding="utf-8") for f in files)
    for name in SCRIPTS:
        if name not in text:
            problem("README/docs never mention %s" % name)
    for lang in LANGUAGES:
        if "`%s`" % lang not in text:
            problem("README/docs never mention the language code `%s`" % lang)
    for f in files + [ROOT / "ROADMAP.md", ROOT / "SECURITY.md", ROOT / "CHANGELOG.md", ROOT / "STATUS-QUO.md"]:
        if not f.exists():
            problem("missing %s" % f.relative_to(ROOT))
            continue
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", f.read_text(encoding="utf-8")):
            if re.match(r"[a-z]+:", target):
                continue
            if not (f.parent / target).exists():
                problem("%s: broken link to %s" % (f.relative_to(ROOT), target))


def check_no_personal_data():
    email = re.compile(r"[\w.+-]+@([\w-]+\.)+[\w-]+")
    skip = {".git", "out", "mockup", "node_modules", "assets"}
    for path in ROOT.rglob("*"):
        if path.is_dir() or skip.intersection(path.relative_to(ROOT).parts) or path.suffix in {".png", ".jpg", ".mp4", ".webm", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in email.finditer(text):
            addr = m.group(0)
            if not addr.endswith(FICTIONAL_DOMAINS) and not addr.endswith(("aws.amazon.com", "noreply@anthropic.com")):
                problem("%s: email outside the fictional domains: %s" % (path.relative_to(ROOT), addr))


def main():
    print("check" if CHECK else "build")
    for name in SKILLS:
        sync_skill(name)
        examples(ROOT / "skills" / name / "scripts")
    compile_scripts()
    check_docs()
    check_no_personal_data()
    if problems:
        print("\n%d problem(s):" % len(problems))
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
