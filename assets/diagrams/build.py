"""Build the profile banner and case-study architecture diagrams as light and dark SVGs.

Run from the repository root: python assets/diagrams/build.py
Each spec places nodes on a column/row grid; edges route orthogonally through the gaps.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Helvetica,Arial,sans-serif"
NW, NH, GX, GY, PAD, TOP = 168, 66, 60, 40, 32, 64

THEMES = {
    "dark": dict(bg="#0B1220", panel="#111B2E", ink="#F2F5FA", sub="#A9B4C7", mute="#7C89A1",
                 edge="#52617D", box="#2A3A57",
                 kinds=dict(model="#818CF8", det="#2DD4BF", human="#FBBF24", refuse="#F87171",
                            store="#94A3B8", io="#CBD5E1")),
    "light": dict(bg="#FFFFFF", panel="#F6F8FB", ink="#0B1220", sub="#3A4659", mute="#66738A",
                  edge="#9AA6B8", box="#C9D3E1",
                  kinds=dict(model="#4F46E5", det="#0D9488", human="#B45309", refuse="#DC2626",
                             store="#64748B", io="#334155")),
}
LEGEND = [("model", "Model interprets"), ("det", "Deterministic code"), ("human", "Human decision"),
          ("refuse", "Refusal"), ("store", "State / evidence"), ("io", "Input / output")]

SPECS = {
    "graphforge": dict(
        title="GraphForge: the typed graph IR drives the canvas, runtime and export",
        nodes=[("canvas", 0, 0, "io", "Visual canvas", "edits the graph IR"),
               ("assist", 0, 1, "model", "Graph assistant", "drafts a Blueprint"),
               ("ir", 1, 0, "det", "Typed graph IR", "single source of truth"),
               ("bp", 1, 1, "det", "Typed Blueprint", "pure compile to IR"),
               ("val", 2, 0, "det", "Validate + compile", "before anything runs"),
               ("export", 2, 1, "io", "Python export", "runs outside the product"),
               ("run", 3, 0, "det", "LangGraph runtime", "real streaming execution"),
               ("tools", 3, 1, "det", "Tools and MCP", "MCP allowlist, timeouts"),
               ("hitl", 4, 0, "human", "Human interrupt", "approve or edit, resume"),
               ("ckpt", 4, 1, "store", "Checkpoints", "replay and time travel")],
        edges=[("canvas", "ir"), ("assist", "bp", "proposal"), ("bp", "ir"), ("ir", "val"), ("ir", "export"),
               ("val", "run"), ("run", "tools"), ("run", "hitl"), ("run", "ckpt")],
        boxes=[]),
    "mandate-guard": dict(
        title="Mandate Guard: clauses become predicates, deterministic code decides",
        nodes=[("clause", 0, 0, "io", "Restriction clause", "natural language"),
               ("parse", 1, 0, "model", "Tiered parser", "grammar first, then LLM"),
               ("pred", 2, 0, "det", "Structured predicate", "grounding + roundtrip"),
               ("hold", 2, 1, "io", "Complete holdings", "no sampling, no subset"),
               ("eval", 3, 0, "det", "Pure evaluator", "aggregate + threshold"),
               ("review", 4, 0, "human", "Source-linked review", "reviewer is accountable"),
               ("audit", 4, 1, "store", "Hash-chained audit", "tamper-evident JSONL")],
        edges=[("clause", "parse"), ("parse", "pred"), ("pred", "eval"), ("hold", "eval"),
               ("eval", "review"), ("eval", "audit")],
        boxes=[(["pred", "hold", "eval"], "Decision function: no model inside")]),
    "conductor": dict(
        title="Conductor: assistance and action run on separate, governed paths",
        nodes=[("assist", 4, 0, "model", "Assistant", "advisory, provider-routed"),
               ("intake", 0, 1, "io", "Intake channels", "mail · forms · upload"),
               ("iw", 1, 1, "det", "Intake worker", "normalise, attach evidence"),
               ("case", 2, 1, "store", "Case + evidence", "PostgreSQL"),
               ("flow", 3, 1, "det", "Durable workflow", "checkpointed worker"),
               ("bench", 4, 1, "human", "Operator workbench", "review and decide"),
               ("audit", 3, 2, "store", "Audit history", "every step recorded"),
               ("act", 4, 2, "det", "Action worker", "deterministic, idempotent")],
        edges=[("intake", "iw"), ("iw", "case"), ("case", "flow"), ("flow", "bench"), ("flow", "audit"),
               ("bench", "assist", "ask"), ("bench", "act", "request"), ("act", "audit")],
        boxes=[(["assist", "bench", "act"], "Policy-gated action")]),
    "redactor": dict(
        title="Redactor: every input is transformed or refused, never passed through",
        nodes=[("files", 0, 0, "io", "Files or folders", "nested, scanned, mixed"),
               ("cls", 1, 0, "det", "Assurance check", "transform or refuse"),
               ("refuse", 1, 1, "refuse", "Refuse with reason", "nothing copied unchanged"),
               ("engine", 2, 0, "det", "Python engine", "detect · transform"),
               ("safe", 3, 0, "io", "Safe mode", "irreversible output"),
               ("rt", 3, 1, "io", "Roundtrip mode", "protected output"),
               ("evid", 4, 0, "store", "Evidence ledger", "verify before publish"),
               ("map", 4, 1, "store", "Encrypted map", "stays on this machine"),
               ("restore", 4, 2, "human", "Explicit restore", "rejects unknown tokens")],
        edges=[("files", "cls"), ("cls", "refuse", "unsupported"), ("cls", "engine", "supported"),
               ("engine", "safe"), ("engine", "rt"), ("safe", "evid"), ("rt", "map"), ("map", "restore")],
        boxes=[(["cls", "refuse", "engine", "safe", "rt", "evid", "map", "restore"],
                "Hard-offline: no network, telemetry or cloud OCR")]),
    "relay": dict(
        title="Relay Desktop: local transcription first, cloud cleanup only when allowed",
        nodes=[("cap", 0, 0, "io", "Local capture", "microphone or audio file"),
               ("asr", 1, 0, "model", "CPU speech model", "on-device"),
               ("tx", 2, 0, "io", "Live transcript", "usable with no network"),
               ("gate", 3, 1, "det", "Offline policy gate", "blocks cloud before socket"),
               ("clean", 3, 0, "model", "Optional cleanup", "local or approved provider"),
               ("hist", 4, 0, "store", "History + export", "meeting workflows")],
        edges=[("cap", "asr"), ("asr", "tx"), ("tx", "clean"), ("gate", "clean", "allow / refuse"),
               ("clean", "hist")],
        boxes=[(["cap", "asr", "tx"], "Local path")]),
    "enterprise-automation": dict(
        title="Enterprise automation tools: explicit contracts around uncertain work",
        nodes=[("art", 0, 0, "io", "Requirements", "or automation XML"),
               ("engine", 1, 0, "det", "Engine client", "validate · generate · package"),
               ("build", 2, 0, "det", "Review, build, tests", "31 platform rules"),
               ("rel", 3, 0, "io", "Validated release", "importable package"),
               ("docs", 0, 1, "io", "Scanned documents", "PDF, images"),
               ("ocr", 1, 1, "det", "OCR + layout", "CPU-first, no admin"),
               ("ext", 2, 1, "model", "Classify + extract", "schema-bound"),
               ("conf", 3, 1, "det", "Confidence gate", "per-document threshold"),
               ("res", 4, 1, "io", "Structured result", "stable JSON contract"),
               ("human", 4, 2, "human", "Review station", "low-confidence documents")],
        edges=[("art", "engine"), ("engine", "build"), ("build", "rel"), ("docs", "ocr"), ("ocr", "ext"),
               ("ext", "conf"), ("conf", "res", "confident"), ("conf", "human", "uncertain"), ("human", "res")],
        boxes=[]),
}


def geometry(spec):
    cols = 1 + max(n[1] for n in spec["nodes"])
    rows = 1 + max(n[2] for n in spec["nodes"])
    w = PAD * 2 + cols * NW + (cols - 1) * GX
    h = TOP + PAD + rows * NH + (rows - 1) * GY + 64
    pos = {n[0]: (PAD + n[1] * (NW + GX), TOP + 8 + n[2] * (NH + GY)) for n in spec["nodes"]}
    return w, h, pos


def route(a, b):
    """Return (path, direction, tip, label anchor) for an edge from node a to node b."""
    (ax, ay), (bx, by) = a, b
    if ax == bx:  # same column: vertical
        x = ax + NW / 2
        y0, y1 = (ay + NH, by) if by > ay else (ay, by + NH)
        return f"M{x} {y0}V{y1}", "down" if by > ay else "up", (x, y1), (x + 7, (y0 + y1) / 2 + 4, "start")
    y1, y2 = ay + NH / 2, by + NH / 2
    if bx < ax:  # backwards along a row
        return f"M{ax} {y1}H{bx + NW}", "left", (bx + NW, y1), ((ax + bx + NW) / 2, y1 - 7, "middle")
    if y1 == y2:
        return f"M{ax + NW} {y1}H{bx}", "right", (bx, y2), ((ax + NW + bx) / 2, y1 - 7, "middle")
    xm, r, s = bx - GX / 2, 8, 1 if y2 > y1 else -1
    d = (f"M{ax + NW} {y1}H{xm - r}Q{xm} {y1} {xm} {y1 + s * r}"
         f"V{y2 - s * r}Q{xm} {y2} {xm + r} {y2}H{bx}")
    return d, "right", (bx, y2), (xm - 6, (y1 + y2) / 2 + 4, "end")


def arrow(kind, tip, color):
    x, y = tip
    pts = {"right": f"{x - 7},{y - 4.5} {x},{y} {x - 7},{y + 4.5}",
           "left": f"{x + 7},{y - 4.5} {x},{y} {x + 7},{y + 4.5}",
           "down": f"{x - 4.5},{y - 7} {x},{y} {x + 4.5},{y - 7}",
           "up": f"{x - 4.5},{y + 7} {x},{y} {x + 4.5},{y + 7}"}[kind]
    return f'<polygon points="{pts}" fill="{color}"/>'


def build(name, spec, t):
    w, h, pos = geometry(spec)
    k = t["kinds"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
         f'role="img" aria-labelledby="t"><title id="t">{escape(spec["title"])}</title>',
         f'<rect width="{w}" height="{h}" rx="14" fill="{t["panel"]}"/>',
         f'<text x="{PAD}" y="{PAD + 8}" font-family="{FONT}" font-size="15" font-weight="600" '
         f'fill="{t["sub"]}">{escape(spec["title"])}</text>']
    for ids, text in spec["boxes"]:
        xs = [pos[i][0] for i in ids]
        ys = [pos[i][1] for i in ids]
        x0, y0, x1, y1 = min(xs) - 12, min(ys) - 22, max(xs) + NW + 12, max(ys) + NH + 12
        o.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="12" fill="none" '
                 f'stroke="{t["box"]}" stroke-width="1.5" stroke-dasharray="5 5"/>')
        o.append(f'<text x="{x0 + 12}" y="{y0 + 14}" font-family="{FONT}" font-size="11" '
                 f'letter-spacing=".4" fill="{t["mute"]}">{escape(text.upper())}</text>')
    for e in spec["edges"]:
        d, kind, tip, (lx, ly, anchor) = route(pos[e[0]], pos[e[1]])
        o.append(f'<path d="{d}" fill="none" stroke="{t["edge"]}" stroke-width="1.6"/>')
        o.append(arrow(kind, tip, t["edge"]))
        if len(e) > 2:
            o.append(f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-family="{FONT}" font-size="11" '
                     f'fill="{t["mute"]}">{escape(e[2])}</text>')
    for nid, _, _, kind, title, sub in spec["nodes"]:
        x, y = pos[nid]
        o.append(f'<rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="10" fill="{t["bg"]}" '
                 f'stroke="{k[kind]}" stroke-opacity=".55"/>')
        o.append(f'<rect x="{x}" y="{y + 12}" width="3" height="{NH - 24}" rx="1.5" fill="{k[kind]}"/>')
        o.append(f'<text x="{x + 14}" y="{y + 27}" font-family="{FONT}" font-size="14" font-weight="600" '
                 f'fill="{t["ink"]}">{escape(title)}</text>')
        o.append(f'<text x="{x + 14}" y="{y + 47}" font-family="{FONT}" font-size="12" '
                 f'fill="{t["mute"]}">{escape(sub)}</text>')
    used = {n[3] for n in spec["nodes"]}
    lx, ly = PAD, h - 26
    for kind, text in LEGEND:
        if kind not in used:
            continue
        o.append(f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2" fill="{k[kind]}"/>')
        o.append(f'<text x="{lx + 16}" y="{ly}" font-family="{FONT}" font-size="11.5" fill="{t["mute"]}">{text}</text>')
        lx += 30 + len(text) * 6.6
    o.append("</svg>")
    (OUT / f"{name}-{'dark' if t is THEMES['dark'] else 'light'}.svg").write_text("\n".join(o), encoding="utf-8")


def hero(name, t):
    """Profile banner: name, positioning and the governed-flow motif. Metrics stay in Markdown."""
    k, w, h = t["kinds"], 1280, 300
    mono = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
         'aria-labelledby="t"><title id="t">Samad Shareef: Applied AI Engineer, AI and Automation Architect. '
         'Models interpret, policy decides, humans approve, actions are audited.</title>',
         f'<defs><pattern id="g" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" '
         f'fill="none" stroke="{t["box"]}" stroke-opacity=".35"/></pattern></defs>',
         f'<rect width="{w}" height="{h}" rx="18" fill="{t["panel"]}"/>',
         f'<rect x="700" y="0" width="580" height="{h}" fill="url(#g)"/>',
         f'<text x="64" y="86" font-family="{mono}" font-size="17" letter-spacing="2.5" fill="{k["det"]}">'
         'APPLIED AI · AUTOMATION ARCHITECTURE</text>',
         f'<text x="60" y="160" font-family="{FONT}" font-size="66" font-weight="700" fill="{t["ink"]}">Samad Shareef</text>',
         f'<text x="64" y="212" font-family="{FONT}" font-size="27" fill="{t["sub"]}">Governed agents, local-first AI,</text>',
         f'<text x="64" y="246" font-family="{FONT}" font-size="27" fill="{t["sub"]}">and enterprise automation.</text>']
    steps = [("Model", "interprets", "model"), ("Policy", "decides", "det"), ("Human", "approves", "human"),
             ("Action", "is audited", "store")]
    y = 150
    for i, (a, b, kind) in enumerate(steps):
        cx = 790 + i * 132
        if i:
            o.append(f'<path d="M{cx - 88} {y}H{cx - 54}" stroke="{t["edge"]}" stroke-width="2"/>')
            o.append(arrow("right", (cx - 50, y), t["edge"]))
        o.append(f'<rect x="{cx - 50}" y="{y - 50}" width="100" height="100" rx="16" fill="{t["bg"]}" '
                 f'stroke="{k[kind]}" stroke-opacity=".6"/>')
        o.append(f'<circle cx="{cx}" cy="{y - 16}" r="7" fill="{k[kind]}"/>')
        o.append(f'<text x="{cx}" y="{y + 14}" text-anchor="middle" font-family="{FONT}" font-size="18" '
                 f'font-weight="600" fill="{t["ink"]}">{a}</text>')
        o.append(f'<text x="{cx}" y="{y + 34}" text-anchor="middle" font-family="{FONT}" font-size="13" '
                 f'fill="{t["mute"]}">{b}</text>')
    o.append("</svg>")
    (OUT.parent / f"hero-{name}.svg").write_text("\n".join(o), encoding="utf-8")


if __name__ == "__main__":
    for name, spec in SPECS.items():
        for theme in THEMES.values():
            build(name, spec, theme)
    for name, theme in THEMES.items():
        hero(name, theme)
