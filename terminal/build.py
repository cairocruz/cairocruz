"""Gera o README do perfil como uma sessão de terminal animada.

Cada comando vira um SVG em assets/term/. Todos compartilham uma linha do
tempo global (os `begin` do SMIL são absolutos), então, empilhados no README,
parecem um terminal só rodando de cima pra baixo.

Roda sem dependências: `python terminal/build.py` (GITHUB_TOKEN é opcional).
"""
import datetime as dt
import json
import os
import re
import urllib.request
from html import escape
from pathlib import Path

USER = os.environ.get("GH_USER", "cairocruz")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "term"

# ---------------------------------------------------------------- conteúdo
PROJECTS = [
    ("hubAgentsV2", "sistema multi-agente de análise de risco (TCC)"),
    ("Music.AI", "gera música com IA e vende no marketplace"),
    ("ttsAPI", "API que narra vídeo: TTS, ducking e legenda viral"),
    ("CornPipBot", "bot em JavaScript, onde tudo começou"),
]

ACHIEVEMENTS = [
    ("Bot Whisperer", "fiz o Blip conversar com o IBM Watson"),
    ("Edital Slayer", "agente n8n que lê edital de licitação sozinho"),
    ("No Middleman", "integração nativa Blip <-> Zendesk, sem API no meio"),
    ("Agent Smith", "sistema multi-agente rodando em produção"),
    ("Final Boss: TCC", "HubAgents V2, análise de risco multi-agente"),
    ("Coffee Overflow", "coffee_count estourou o int"),
]

# ---------------------------------------------------------------- visual
W = 880
CW = 9.2          # largura estimada do caractere (só pra animação de digitação)
LH = 21           # altura de linha
X0 = 22
FONT = "Consolas, 'SFMono-Regular', Menlo, 'DejaVu Sans Mono', 'Courier New', monospace"
BG = "#010409"
C = dict(g="#39d353", b="#58a6ff", c="#39c5cf", y="#e3b341", r="#ff7b72",
         m="#d2a8ff", t="#c9d1d9", d="#8b949e", w="#f0f6fc")
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
PROMPT = [("cairo@minerva", "g"), (":", "t"), ("~", "b"), ("$ ", "t")]

TYPE = 0.045      # segundos por caractere digitado
LINE = 0.05       # intervalo entre linhas de saída


class Seg:
    """Um pedaço do terminal (um SVG). `clock` é a linha do tempo global."""

    clock = 0.4

    def __init__(self, name, top=False, bottom=False):
        self.name, self.top, self.bottom = name, top, bottom
        self.els, self.defs = [], []
        self.y = (36 + 24) if top else 18

    # -- primitivas
    def _appear(self, t):
        return f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'

    @staticmethod
    def _spans(parts):
        return "".join(f'<tspan fill="{C[c]}">{escape(s)}</tspan>' for s, c in parts)

    def line(self, parts, x=X0, dt_=LINE, bold=False):
        if isinstance(parts, str):
            parts = [(parts, "t")]
        fw = ' font-weight="bold"' if bold else ""
        self.els.append(f'<text x="{x}" y="{self.y}" opacity="0"{fw}>'
                        f'{self._appear(Seg.clock)}{self._spans(parts)}</text>')
        Seg.clock += dt_
        self.y += LH

    def typed(self, parts, x=X0, speed=TYPE, pause_after=0.3):
        """Texto que aparece caractere a caractere (clipPath em degraus)."""
        n = sum(len(s) for s, _ in parts)
        cid = f"{self.name}-{len(self.defs)}"
        vals = ";".join(f"{i * CW:.1f}" for i in range(n + 1)) + f";{W}"
        dur = speed * (n + 1)
        self.defs.append(
            f'<clipPath id="{cid}"><rect x="{x}" y="{self.y - 16}" height="{LH}" width="0">'
            f'<animate attributeName="width" values="{vals}" calcMode="discrete" '
            f'begin="{Seg.clock:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>')
        self.els.append(f'<text x="{x}" y="{self.y}" clip-path="url(#{cid})">{self._spans(parts)}</text>')
        Seg.clock += dur + pause_after

    def cmd(self, text):
        self.gap(0.35)
        plen = sum(len(s) for s, _ in PROMPT)
        self.els.append(f'<text x="{X0}" y="{self.y}" opacity="0" font-weight="bold">'
                        f'{self._appear(Seg.clock)}{self._spans(PROMPT)}</text>')
        Seg.clock += 0.35
        self.typed([(text, "w")], x=X0 + plen * CW)
        self.y += LH

    def gap(self, k=0.5):
        self.y += LH * k

    def cursor(self):
        plen = sum(len(s) for s, _ in PROMPT)
        self.els.append(f'<text x="{X0}" y="{self.y}" opacity="0" font-weight="bold">'
                        f'{self._appear(Seg.clock)}{self._spans(PROMPT)}</text>')
        self.els.append(
            f'<rect x="{X0 + plen * CW:.1f}" y="{self.y - 15}" width="9" height="18" fill="{C["g"]}" opacity="0">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" '
            f'begin="{Seg.clock:.2f}s" repeatCount="indefinite"/></rect>')
        self.y += LH

    # -- saída
    def svg(self):
        h = int(self.y + (4 if self.bottom else -6))
        r = 10
        tr = r if self.top else 0
        br = r if self.bottom else 0
        bg = (f'<path d="M0 {tr} a{tr} {tr} 0 0 1 {tr} -{tr} H{W - tr} a{tr} {tr} 0 0 1 {tr} {tr} '
              f'V{h - br} a{br} {br} 0 0 1 -{br} {br} H{br} a{br} {br} 0 0 1 -{br} -{br} Z" fill="{BG}"/>')
        chrome = ""
        if self.top:
            chrome = (f'<path d="M0 {r} a{r} {r} 0 0 1 {r} -{r} H{W - r} a{r} {r} 0 0 1 {r} {r} V36 H0 Z" fill="#161b22"/>'
                      f'<circle cx="22" cy="18" r="6" fill="#ff5f56"/><circle cx="42" cy="18" r="6" fill="#ffbd2e"/>'
                      f'<circle cx="62" cy="18" r="6" fill="#27c93f"/>'
                      f'<text x="{W / 2}" y="23" fill="{C["d"]}" font-size="13" text-anchor="middle">cairo@minerva: ~ — zsh</text>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">'
                f'<defs>{"".join(self.defs)}</defs>{bg}'
                f'<g font-family="{FONT}" font-size="15" style="white-space:pre" xml:space="preserve">'
                f'{chrome}{"".join(self.els)}</g></svg>')

    def save(self):
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{self.name}.svg").write_text(self.svg(), encoding="utf-8")
        return f"assets/term/{self.name}.svg"


# ---------------------------------------------------------------- dados
def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": USER})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
    return body if raw else json.loads(body)


def contributions():
    html = get(f"https://github.com/users/{USER}/contributions", raw=True)
    days = {}
    for m in re.finditer(r'data-date="([\d-]+)" id="(contribution-day-component-\d+-\d+)" data-level="(\d)"', html):
        days[m.group(2)] = [m.group(1), int(m.group(3)), 0]
    for m in re.finditer(r'for="(contribution-day-component-\d+-\d+)"[^>]*>(\d+) contribution', html):
        if m.group(1) in days:
            days[m.group(1)][2] = int(m.group(2))
    cal = sorted((dt.date.fromisoformat(d), lvl, n) for d, lvl, n in days.values())
    return cal


def streaks(cal):
    cur = best = run = 0
    for _, _, n in cal:
        run = run + 1 if n else 0
        best = max(best, run)
    for i, (_, _, n) in enumerate(reversed(cal)):
        if n:
            cur += 1
        elif i > 0:          # hoje ainda sem commit não zera a sequência
            break
    return cur, best


def repo_data():
    repos = [r for r in get(f"https://api.github.com/users/{USER}/repos?per_page=100") if not r["fork"]]
    user = get(f"https://api.github.com/users/{USER}")
    langs = {}
    for r in repos:
        for k, v in get(r["languages_url"]).items():
            langs[k] = langs.get(k, 0) + v
    return {r["name"]: r for r in repos}, user, langs


# ---------------------------------------------------------------- sessão
def build():
    cal = contributions()
    repos, user, langs = repo_data()
    today = dt.date.today()
    total = sum(n for _, _, n in cal)
    cur, best = streaks(cal)
    blocks = []   # (path, link|None, alt)

    # 01 · boot
    s = Seg("01-boot", top=True)
    for svc, desc in [("coffee.service", "café quentinho"), ("network.target", "do cabo ao prompt"),
                      ("n8n.service", "workflows online"), ("langgraph-agents.target", "agentes acordados"),
                      ("rag-index.service", "base de conhecimento indexada")]:
        s.line([("[  ", "t"), ("OK", "g"), ("  ] ", "t"), ("Started ", "t"), (svc, "w"), (f" — {desc}", "d")], dt_=0.14)
    s.line([("[  ", "t"), ("OK", "g"), ("  ] ", "t"), ("Reached target ", "t"), ("Multi-Agent System", "g"), (".", "t")], dt_=0.3)
    s.gap(0.4)
    s.line([(f"Last login: {today:%a %b %d} from São Carlos, BR", "d")], dt_=0.3)
    blocks.append((s.save(), None, "boot: [OK] coffee.service, n8n.service, langgraph-agents.target"))

    # 02 · neofetch
    s = Seg("02-neofetch")
    s.cmd("neofetch")
    tux = ["      .---.", "     /     \\", "     \\.@-@./", "     /`\\_/`\\", "    //  _  \\\\",
           "   | \\     )|_", "  /`\\_`>  <_/ \\", "  \\__/'---'\\__/"]
    info = [[("cairo", "g"), ("@", "t"), ("minerva", "g")],
            [("-------------", "t")],
            [("Role", "g"), (": Data Scientist @ Minerva Foods", "t")],
            [("Host", "g"), (": São Carlos, SP · BR", "t")],
            [("Uptime", "g"), (": 4+ years in conversational AI", "t")],
            [("Kernel", "g"), (": python · langgraph · n8n", "t")],
            [("Packages", "g"), (": rag, evals, prompt-ops, multi-agent", "t")],
            [("Locale", "g"), (": pt-BR (native) · en", "t")],
            [("Coffee", "g"), (": ∞ cups", "t")]]
    y0 = s.y
    for i in range(max(len(tux), len(info))):
        s.y = y0 + i * LH
        if i < len(tux):
            s.els.append(f'<text x="{X0}" y="{s.y}" opacity="0" fill="{C["g"]}" font-weight="bold">'
                         f'{s._appear(Seg.clock)}{escape(tux[i])}</text>')
        if i < len(info):
            s.els.append(f'<text x="{X0 + 200}" y="{s.y}" opacity="0" font-weight="bold">'
                         f'{s._appear(Seg.clock)}{s._spans(info[i])}</text>')
        Seg.clock += LINE
    s.y = y0 + len(info) * LH
    for i, col in enumerate(["#484f58", C["r"], C["g"], C["y"], C["b"], C["m"], C["c"], C["w"]]):
        s.els.append(f'<rect x="{X0 + 200 + i * 26}" y="{s.y - 13}" width="26" height="16" fill="{col}" opacity="0">'
                     f'{s._appear(Seg.clock)}</rect>')
    Seg.clock += 0.2
    s.y += LH
    s.cmd("cat about.txt")
    for tag, txt in [("pt", "Ensino robô a trabalhar pra ninguém precisar fazer tarefa chata."),
                     ("pt", "Vim de infra de redes: entendo o sistema do cabo ao prompt."),
                     ("en", "I build multi-agent GenAI systems, from prototype to production."),
                     ("en", "Network infra background: I get systems end to end, cable to prompt.")]:
        s.line([(f"[{tag}] ", "d"), (txt, "t")])
    blocks.append((s.save(), None, "neofetch: Cairo Cruz, Data Scientist @ Minerva Foods, São Carlos"))

    # 03 · carreira
    s = Seg("03-career")
    s.cmd("git log --career --graph")
    for h, ref, msg, when, det in [
        ("7a3f9e1", "HEAD -> minerva-foods", "Mid-Level Data Scientist", "2026-04 → now",
         "multi-agent GenAI · LangGraph · n8n · RAG · evals"),
        ("4b2c8d0", "valecard", "Conversational AI Specialist", "2024-01 → 2026-03",
         "chatbot strategy lead · GenAI personas · agente n8n de editais"),
        ("91e5a6f", "blip", "Conversational AI Developer", "2021-12 → 2023-09",
         "IBM Watson bot · Blip <-> Zendesk nativo · CI/CD na Azure")]:
        s.line([("* ", "r"), (h, "y"), (" (", "y"), (ref, "c"), (") ", "y"), ("feat: ", "g"), (msg, "w"), (f"  {when}", "d")])
        s.line([("|  ", "r"), (det, "t")])
    s.line([("* ", "r"), ("0c0ffee", "y"), (" (", "y"), ("origin", "c"), (") ", "y"), ("init: ", "g"), ("infraestrutura de redes", "w")])
    blocks.append((s.save(), None, "git log: Minerva Foods, ValeCard, Blip"))

    # 04 · achievements
    s = Seg("04-achievements")
    s.cmd("./achievements --unlocked")
    s.typed([("Loading save file... ", "d"), ("[" + "█" * 24 + "] ", "g"), ("100%", "w")], speed=0.02, pause_after=0.15)
    s.y += LH
    for name, desc in ACHIEVEMENTS:
        s.line([("[", "t"), ("★", "y"), ("] ", "t"), (f"{name:<17}", "y"), (desc, "t")], dt_=0.1)
    s.line([(f"{len(ACHIEVEMENTS)}/{len(ACHIEVEMENTS)} unlocked · ", "d"), ("LVL 4+ ", "g"),
            ("XP ", "d"), ("█" * 18, "g"), ("░" * 6, "d")])
    blocks.append((s.save(), None, "achievements: Bot Whisperer, Edital Slayer, No Middleman, Agent Smith"))

    # 05 · stack
    s = Seg("05-stack")
    s.cmd("ls --color ~/stack")
    s.line([("agents/     rag/        evals/       prompts/     workflows/", "b")])
    s.line([("python*     fastapi*    langgraph*   langchain*   n8n*", "g")])
    s.line([("claude      openai      ibm-watson   blip         zendesk", "m")])
    s.line([("typescript  react       node         csharp       dotnet", "t")])
    s.line([("docker      azure       supabase     postgres     linux", "c")])
    blocks.append((s.save(), None, "stack: python, fastapi, langgraph, langchain, n8n, rag, docker, azure"))

    # 06 · projetos (uma imagem por linha, cada uma clicável)
    s = Seg("06-projects")
    s.cmd("ls -l ~/projects")
    s.line([(f"total {len(PROJECTS)}", "t"), ("   # clique num projeto pra abrir · click to open", "d")])
    blocks.append((s.save(), None, "ls -l ~/projects"))
    for i, (name, desc) in enumerate(PROJECTS):
        r = repos.get(name, {})
        lang = (r.get("language") or "-")[:10]
        upd = (r.get("pushed_at") or "")[:7]
        stars = r.get("stargazers_count", 0)
        s = Seg(f"06-project-{i}")
        s.y = 15
        s.line([("drwxr-xr-x  ", "d"), (f"★{stars:<3}", "y"), (f"{lang:<11}", "m"), (f"{upd:<9}", "d"),
                (f"{name + '/':<14}", "b"), (desc, "t")], dt_=0.1)
        s.y -= 1
        blocks.append((s.save(), f"https://github.com/{USER}/{name}", f"{name}: {desc}"))

    # 07 · contribuições
    s = Seg("07-contrib")
    s.cmd("gh contrib --graph --last-year")
    cell, gapc = 12, 3
    gx, gy = X0 + 34, s.y + 4
    weeks = []
    for d, lvl, n in cal:
        if not weeks or d.weekday() == 6:   # semana começa no domingo
            weeks.append([])
        weeks[-1].append((d, lvl))
    t0 = Seg.clock
    last_month = None
    for wi, wk in enumerate(weeks):
        tw = t0 + wi * 0.03
        m = wk[0][0].month
        if m != last_month and wk[0][0].day <= 7:
            s.els.append(f'<text x="{gx + wi * (cell + gapc)}" y="{gy - 2}" fill="{C["d"]}" font-size="11" opacity="0">'
                         f'{s._appear(tw)}{wk[0][0]:%b}</text>')
            last_month = m
        for d, lvl in wk:
            row = (d.weekday() + 1) % 7
            s.els.append(f'<rect x="{gx + wi * (cell + gapc)}" y="{gy + 6 + row * (cell + gapc)}" width="{cell}" '
                         f'height="{cell}" fill="{LEVELS[lvl]}" opacity="0">{s._appear(tw)}</rect>')
    for row, lab in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        s.els.append(f'<text x="{X0}" y="{gy + 16 + row * (cell + gapc)}" fill="{C["d"]}" font-size="11" opacity="0">'
                     f'{s._appear(t0)}{lab}</text>')
    Seg.clock = t0 + len(weeks) * 0.03 + 0.2
    s.y = gy + 6 + 7 * (cell + gapc) + 20
    lx = gx + len(weeks) * (cell + gapc) - 5 * (cell + gapc) - 40
    s.els.append(f'<text x="{lx - 8}" y="{s.y}" fill="{C["d"]}" font-size="11" text-anchor="end" opacity="0">'
                 f'{s._appear(Seg.clock)}less</text>')
    for i, col in enumerate(LEVELS):
        s.els.append(f'<rect x="{lx + i * (cell + gapc)}" y="{s.y - 10}" width="{cell}" height="{cell}" fill="{col}" '
                     f'opacity="0">{s._appear(Seg.clock)}</rect>')
    s.els.append(f'<text x="{lx + 5 * (cell + gapc) + 4}" y="{s.y}" fill="{C["d"]}" font-size="11" opacity="0">'
                 f'{s._appear(Seg.clock)}more</text>')
    s.line([(f"{total} contributions", "g"), (" in the last year", "t")])
    s.line([("streak atual/current: ", "d"), (f"{cur}d", "g"), ("   ·   maior/longest: ", "d"), (f"{best}d", "g")])
    blocks.append((s.save(), None, f"{total} contributions in the last year"))

    # 08 · stats
    s = Seg("08-stats")
    s.cmd("cairo-stats --langs")
    s.line([("repos ", "d"), (str(len(repos)), "w"), ("   stars ", "d"), (str(sum(r["stargazers_count"] for r in repos.values())), "w"),
            ("   followers ", "d"), (str(user.get("followers", 0)), "w"), ("   since ", "d"), (user.get("created_at", "")[:4], "w")])
    s.gap(0.3)
    tot = sum(langs.values()) or 1
    for name, size in sorted(langs.items(), key=lambda kv: -kv[1])[:6]:
        pct = size / tot * 100
        n = max(1, round(pct / 100 * 30))
        s.typed([(f"{name:<12}", "t"), ("█" * n, "g"), ("░" * (30 - n), "d"), (f" {pct:5.1f}%", "w")],
                speed=0.008, pause_after=0.05)
        s.y += LH
    blocks.append((s.save(), None, "linguagens mais usadas"))

    # 09 · fim
    s = Seg("09-bye", bottom=True)
    s.cmd('echo "valeu por passar aqui · thanks for stopping by"')
    s.line([("valeu por passar aqui · thanks for stopping by  ", "g"), ("c[_]", "y")], dt_=0.3)
    s.gap(0.35)
    s.cursor()
    blocks.append((s.save(), None, "valeu por passar aqui"))

    return blocks


def readme(blocks):
    rows = []
    for path, link, alt in blocks:
        img = f'<img align="left" width="100%" src="{path}" alt="{escape(alt)}" />'
        rows.append(f'<a href="{link}">{img}</a>' if link else img)
    return ("<!-- gerado por terminal/build.py: edite lá, não aqui -->\n"
            + "\n".join(rows) + "\n\n<br clear=\"left\"/>\n")


if __name__ == "__main__":
    for f in OUT.glob("*.svg"):
        f.unlink()
    b = build()
    (ROOT / "README.md").write_text(readme(b), encoding="utf-8", newline="\n")
    print(f"{len(b)} blocos, animacao total ~ {Seg.clock:.1f}s")
