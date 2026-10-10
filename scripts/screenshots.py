#!/usr/bin/env python3
"""Render the README screenshots into assets/screenshots/. Maintainers only, macOS only.

    python3 scripts/screenshots.py

Each screen is an HTML page in assets/screenshots/src/. Quick Look (qlmanage) renders it
and sips crops the 16:10 band. Terminal output is real: it comes from running the scripts
against examples/. Screens of third-party products (Gmail connector, Slack app settings)
are labeled as illustrations.
"""
import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "screenshots" / "src"
OUT = ROOT / "assets" / "screenshots"
SKILL = ROOT / "skills" / "security-launch-radar" / "scripts"
SIZE = 1600  # Quick Look renders a ~1024 px wide page and scales it to SIZE; we keep the centered 16:10 band


def e(s):
    return html.escape(s or "", quote=True)


def run(*args, cwd=ROOT):
    p = subprocess.run(["python3"] + [str(a) for a in args], cwd=cwd, capture_output=True, text=True)
    return (p.stdout + p.stderr).strip("\n")


CSS = """
*{box-sizing:border-box}
html,body{margin:0;width:1024px;height:1024px;background:#efe9e2;font-family:-apple-system,"Helvetica Neue",Arial,sans-serif}
body{display:flex;align-items:center;justify-content:center}
.band{width:1024px;height:640px;padding:28px 34px;display:flex;align-items:center;justify-content:center;position:relative}
.win{width:100%;height:100%;border-radius:12px;overflow:hidden;box-shadow:0 18px 40px rgba(28,25,22,.28);display:flex;flex-direction:column}
.bar{height:34px;flex:none;display:flex;align-items:center;gap:7px;padding:0 14px;font-size:12px}
.bar i{width:11px;height:11px;border-radius:50%;display:inline-block}
.bar i:nth-child(1){background:#ff5f57}.bar i:nth-child(2){background:#febc2e}.bar i:nth-child(3){background:#28c840}
.bar span{margin-left:10px}
.term{background:#15120f;color:#efe8e0}.term .bar{background:#262019;color:#a39a90}
.term pre{margin:0;padding:18px 22px;font:13px/1.6 Menlo,Monaco,monospace;white-space:pre-wrap;overflow:hidden;flex:1}
.c{color:#ef7d3c}.ok{color:#5cc08b}.err{color:#ff8f8f}.dim{color:#8a8178}.y{color:#e0c069}
.light{background:#fff;color:#1c1916}.light .bar{background:#f1ece6;color:#6b635b}
.url{flex:1;margin:0 70px;height:22px;border-radius:6px;background:#fff;color:#6b635b;font:12px/22px Menlo,monospace;text-align:center}
.tag{position:absolute;right:46px;bottom:38px;font:600 11px Menlo,monospace;letter-spacing:.08em;color:#6b635b;background:#fff;border:1px solid #ddd5ca;border-radius:999px;padding:3px 10px}
.cc{font:13px/1.55 Menlo,Monaco,monospace;padding:16px 22px;flex:1;overflow:hidden}
.cc .u{background:#2a241e;border-left:2px solid #8a8178;padding:5px 10px;margin:9px 0}
.cc .t{margin:8px 0}.cc .t b{color:#fff}.cc .o{color:#b8b0a6;white-space:pre;margin-left:4px}
.cc .s{margin:8px 0;display:flex;gap:8px}.cc .s div{white-space:pre-wrap}
.cc .wel{border:1px solid #ef7d3c;border-radius:6px;padding:6px 12px;display:inline-block;margin-bottom:6px}
"""


def page(name, body, tag=""):
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>%s</style></head><body><div class="band">%s%s</div></body></html>'
           % (CSS, body, '<span class="tag">%s</span>' % e(tag) if tag else ""))
    (SRC / ("%s.html" % name)).write_text(doc, encoding="utf-8")


def terminal(title, lines):
    """lines: list of (css_class, text). Commands get the 'c' class with a $ prompt."""
    body = "\n".join('<span class="%s">%s</span>' % (cls, e(t)) if cls else e(t) for cls, t in lines)
    return '<div class="win term"><div class="bar"><i></i><i></i><i></i><span>%s</span></div><pre>%s</pre></div>' % (e(title), body)


def claude(title, blocks):
    return '<div class="win term"><div class="bar"><i></i><i></i><i></i><span>%s</span></div><div class="cc">%s</div></div>' % (e(title), "".join(blocks))


def cc_user(t):
    return '<div class="u"><span class="dim">&gt;</span> %s</div>' % e(t)


def cc_tool(name, arg, out, ok=True):
    lines = out.split("\n")
    return ('<div class="t"><span class="%s">⏺</span> <b>%s</b>(<span class="dim">%s</span>)<div class="o"><span class="dim">⎿</span>  %s</div></div>'
            % ("ok" if ok else "err", e(name), e(arg), e("\n   ".join(l[:104] for l in lines))))


def cc_say(t):
    return '<div class="s"><span>⏺</span><div>%s</div></div>' % e(t)


def slack_mrkdwn(text):
    links = []

    def keep(m):
        links.append('<a style="color:#1264a3;text-decoration:none" href="#">%s</a>' % m.group(2))
        return "\x00%d\x00" % (len(links) - 1)

    text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", keep, text)
    text = re.sub(r"`([^`\n]+)`", r"<code style='font:700 11px Menlo,monospace;color:#e01e5a;background:#f6f6f6;border:1px solid #e1e1e1;border-radius:3px;padding:0 3px'>\1</code>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w])_([^_\n]+)_(?![\w])", r"<i>\1</i>", text)
    text = re.sub("\x00(\\d+)\x00", lambda m: links[int(m.group(1))], text)
    return text.replace("\n", "<br>")


def build_pages():
    SRC.mkdir(parents=True, exist_ok=True)
    fetch_out = (ROOT / "examples" / "fetch-output.txt").read_text(encoding="utf-8").strip()
    invalid = run(SKILL / "validate_radar.py", "--radar", "examples/radar-invalid.json", "--items", "examples/items-snapshot.json")
    valid = run(SKILL / "validate_radar.py", "--radar", "examples/radar-en.json", "--items", "examples/items-snapshot.json")
    with tempfile.TemporaryDirectory() as tmp:
        setup_out = run(ROOT / "setup.py", "--language", "pt-BR", "--email", "security@example.com", "--slack", cwd=tmp)
        rendered = run(SKILL / "render.py", "--radar", ROOT / "examples/radar-en.json", "--items", ROOT / "examples/items-snapshot.json",
                       "--config", ROOT / "examples/config-en.json", "--out", tmp).replace(tmp, "out")
    items = json.loads((ROOT / "examples" / "items-snapshot.json").read_text(encoding="utf-8"))
    radar = json.loads((ROOT / "examples" / "radar-en.json").read_text(encoding="utf-8"))

    listing = subprocess.run(["ls"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    listing = [x for x in listing if x not in ("out", "mockup")]
    skills = subprocess.run(["ls", ".claude/skills"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    pyver = subprocess.run(["python3", "--version"], capture_output=True, text=True).stdout.strip()
    rows = ["  ".join(listing[i:i + 7]) for i in range(0, len(listing), 7)]
    page("01-clone", terminal("~ · zsh", [
        ("c", "$ git clone https://github.com/<your-user>/aws-security-launch-radar-latam.git"), ("dim", "Cloning into 'aws-security-launch-radar-latam'..."),
        ("c", "$ cd aws-security-launch-radar-latam"), ("c", "$ ls")] + [("", r) for r in rows] + [
        ("c", "$ ls .claude/skills"), ("ok", skills),
        ("c", "$ python3 --version"), ("", pyver)]), "Step 1 · ls output is real")

    page("02-sources", terminal("aws-security-launch-radar-latam · zsh", [
        ("c", "$ python3 .claude/skills/security-launch-radar/scripts/fetch_feeds.py"), ("ok", fetch_out), ("", ""),
        ("dim", "# 3 sources reached: AWS What's New API, AWS blogs API, Security Bulletins RSS"),
        ("dim", "# old bulletins that AWS resurfaced this week are counted as 'updated', not new")]), "Step 2 · real output")

    page("03-gmail", '<div class="win light"><div class="bar"><i></i><i></i><i></i><div class="url">claude.ai/customize/connectors</div></div>'
         '<div style="padding:34px 44px;display:grid;gap:18px"><div style="font:700 24px -apple-system">Connectors</div>'
         '<div style="color:#6b635b">Connect the apps Claude can use in chats, Claude Code and routines.</div>'
         + "".join('<div style="display:flex;align-items:center;gap:14px;border:1px solid #e2ddd7;border-radius:10px;padding:14px 18px">'
                   '<div style="width:36px;height:36px;border-radius:8px;background:%s;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700">%s</div>'
                   '<div style="flex:1"><b>%s</b><div style="color:#6b635b;font-size:13px">%s</div></div>'
                   '<div style="border-radius:999px;padding:6px 14px;font-size:13px;font-weight:600;%s">%s</div></div>'
                   % (bg, ic, n, d, st, lab) for bg, ic, n, d, st, lab in [
                       ("#ea4335", "M", "Gmail", "Send email from your Gmail address", "background:#2f7d55;color:#fff", "Connected"),
                       ("#4285f4", "D", "Google Drive", "Read files you choose", "border:1px solid #ddd5ca", "Connect"),
                       ("#611f69", "S", "Slack", "Not needed: the radar posts through a webhook", "border:1px solid #ddd5ca", "Connect")])
         + '</div></div>', "Step 3 · illustration")

    page("04-slack-webhook", '<div class="win light"><div class="bar"><i></i><i></i><i></i><div class="url">api.slack.com/apps</div></div>'
         '<div style="display:flex;flex:1"><div style="width:220px;background:#f8f6f3;border-right:1px solid #e2ddd7;padding:22px;font-size:14px;line-height:2;color:#6b635b">'
         '<b style="color:#1c1916">Security Radar</b><br>Basic Information<br>App Home<br><span style="color:#1264a3;font-weight:600">Incoming Webhooks</span><br>OAuth &amp; Permissions</div>'
         '<div style="padding:28px 34px;flex:1;display:grid;gap:16px;align-content:start"><div style="font:700 22px -apple-system">Incoming Webhooks</div>'
         '<div style="display:flex;align-items:center;gap:10px"><b>Activate Incoming Webhooks</b><span style="background:#2f7d55;color:#fff;border-radius:999px;padding:2px 10px;font-size:12px">On</span></div>'
         '<div style="border:1px solid #e2ddd7;border-radius:10px;padding:16px"><div style="font-size:13px;color:#6b635b">Webhook URL for #security-radar</div>'
         '<div style="font:13px Menlo,monospace;margin-top:6px">https://hooks.slack.com/services/T000/B000/••••••••••••</div></div>'
         '<div style="background:#15120f;color:#efe8e0;border-radius:8px;padding:14px 16px;font:13px Menlo,monospace">$ export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...</div>'
         '<div style="color:#a66a00;font-size:13px">Keep it in an environment variable. Never in a file or in the repository.</div></div></div></div>',
         "Step 4 · illustration")

    page("05-setup", terminal("aws-security-launch-radar-latam · zsh", [
        ("c", "$ python3 setup.py"), ("", "AWS Security Weekly Radar setup"), ("", ""),
        ("y", "Report language: 1) English  2) Português (Brasil)  3) Español [1]: 2"),
        ("y", "Email recipients (comma-separated, empty to skip): security@example.com"),
        ("y", "Post to Slack too? (y/n) [n]: y"), ("", "")] + [("ok" if l.startswith("Saved") else "", l) for l in setup_out.split("\n")]),
        "Step 5 · real output")

    page("06-run", claude("claude · aws-security-launch-radar-latam", [
        '<div class="wel"><span class="c">✻</span> Welcome to <b>Claude Code</b></div>',
        cc_user("run the security radar"),
        cc_tool("Skill", "security-launch-radar", "Successfully loaded skill"),
        cc_tool("Bash", "python3 $SKILL/scripts/fetch_feeds.py", fetch_out[:104]),
        cc_say("%d security items: %d new bulletins and %d updates to older ones. Writing the radar in English."
               % (items["stats"]["total"], items["stats"]["bulletins_new"], items["stats"]["bulletins_updated"])),
        cc_tool("Bash", "python3 $SKILL/scripts/validate_radar.py", valid),
        cc_tool("Bash", "python3 $SKILL/scripts/render.py", rendered),
        cc_say("Preview ready: %d highlights, %d items under \"Also released\", %d bulletins. Send by email and Slack?"
               % (len(radar["highlights"]), len(radar["also_noted"]), len(radar["cves"]))),
        cc_user("go ahead")]), "Step 6 · real script output")

    email = (ROOT / "examples" / "email-en.html").read_text(encoding="utf-8")
    inner = re.search(r"<body[^>]*>(.*)</body>", email, re.S).group(1)
    inner = re.sub(r'<div style="display:none;[^"]*">.*?</div>', "", inner, count=1, flags=re.S)
    subject = re.search(r"<title>(.*?)</title>", email).group(1)
    inbox = "".join('<div style="padding:12px 14px;border-bottom:1px solid #eee;%s"><b style="font-size:13px">%s</b><div style="font-size:12px;color:#6b635b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">%s</div></div>'
                    % (st, f, s) for st, f, s in [("background:#eaf2ff", "Security Radar", subject), ("", "Platform team", "Sprint review notes"), ("", "Billing", "Your monthly invoice")])
    page("07-email", '<div class="win light"><div class="bar"><i></i><i></i><i></i><span>Inbox · security@example.com</span></div>'
         '<div style="display:flex;flex:1;min-height:0"><div style="width:250px;border-right:1px solid #e2ddd7">%s</div>'
         '<div style="flex:1;overflow:hidden;zoom:.82;background:#f5f6f8">%s</div></div></div>' % (inbox, inner), "Step 6 · real email")

    slack = json.loads((ROOT / "examples" / "slack-en.json").read_text(encoding="utf-8"))
    parts = []
    for b in slack["blocks"][:9]:
        if b["type"] == "header":
            parts.append('<div style="font:900 17px -apple-system">%s</div>' % e(b["text"]["text"]))
        elif b["type"] == "context":
            parts.append('<div style="color:#616061;font-size:12px">%s</div>' % slack_mrkdwn(b["elements"][0]["text"]))
        elif b["type"] == "section":
            parts.append('<div style="margin:6px 0;font-size:14px">%s</div>' % slack_mrkdwn(b["text"]["text"]))
        elif b["type"] == "divider":
            parts.append('<hr style="border:0;border-top:1px solid #ddd;margin:8px 0">')
    page("08-slack", '<div class="win light"><div class="bar" style="background:#3f0e40;color:#fff"><i></i><i></i><i></i><span># security-radar</span></div>'
         '<div style="display:flex;gap:10px;padding:16px 20px;overflow:hidden;flex:1"><div style="width:36px;height:36px;border-radius:6px;background:#232f3e;color:#ff9900;display:flex;align-items:center;justify-content:center;font-weight:800;flex:none">SR</div>'
         '<div style="min-width:0"><div><b>Security Radar</b> <span style="background:#e8e8e8;color:#616061;font-size:10px;font-weight:700;padding:1px 4px;border-radius:3px">APP</span> <span style="color:#616061;font-size:12px">8:00 AM</span></div>%s</div></div></div>'
         % "".join(parts), "Step 6 · real Slack payload")

    page("09-schedule", claude("claude · aws-security-launch-radar-latam", [
        cc_user("/schedule every Monday at 8am, run the security radar on this repo"),
        cc_say("Here is the routine. 8:00 America/Sao_Paulo = 11:00 UTC."),
        '<div style="border:1px solid #3a332c;border-radius:8px;padding:12px 16px;margin:8px 0;line-height:1.9">'
        '<span class="dim">name</span>      Security Radar weekly<br><span class="dim">schedule</span>  0 11 * * 1 (Mondays 11:00 UTC)<br>'
        '<span class="dim">repo</span>      github.com/&lt;your-user&gt;/aws-security-launch-radar-latam<br><span class="dim">prompt</span>    Use the security-launch-radar skill in scheduled mode.<br>'
        '<span class="dim">connectors</span> Gmail<br><span class="dim">env</span>       SLACK_WEBHOOK_URL (set in the cloud environment)</div>',
        cc_say("Create it?"), cc_user("yes"), cc_say("Created. Review, pause or run it at claude.ai/code/routines.")]), "Step 7 · illustration")

    page("10-validator", terminal("aws-security-launch-radar-latam · zsh", [
        ("c", "$ python3 .claude/skills/security-launch-radar/scripts/validate_radar.py --radar examples/radar-invalid.json")]
        + [("err", l) for l in invalid.split("\n")] + [("", ""), ("dim", "# nothing is rendered or sent; Claude fixes the draft and tries again (max 3)")]),
        "Validator · real output")


def render_pngs():
    with tempfile.TemporaryDirectory() as tmp:
        for src in sorted(SRC.glob("*.html")):
            subprocess.run(["qlmanage", "-t", "-s", str(SIZE), "-o", tmp, str(src)], capture_output=True)
            png = Path(tmp) / (src.name + ".png")
            if not png.exists():
                raise SystemExit("Quick Look did not render %s" % src.name)
            target = OUT / (src.stem + ".png")
            subprocess.run(["sips", "-c", str(SIZE * 10 // 16), str(SIZE), str(png), "--out", str(target)], capture_output=True)
            print("  wrote", target.relative_to(ROOT))


if __name__ == "__main__":
    if not shutil.which("qlmanage"):
        raise SystemExit("macOS only: needs qlmanage and sips")
    build_pages()
    render_pngs()
