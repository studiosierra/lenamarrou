"""Générateur du site Léna Marrou : une seule source, toutes les pages.
Usage : python3 build.py <dossier du site>
Règle de Léna : ne jamais parler d'ascenseur sur le site.
"""
import sys, os, pathlib, re, html as _html, shutil, unicodedata, datetime

NETLIFY = os.environ.get("NETLIFY") == "1"  # version autonome pour Netlify (pages complètes, formulaire actif)

OUT = pathlib.Path(sys.argv[1])
SRC = pathlib.Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
# Version « dépôt » : on copie les fichiers du site à côté du générateur dans le dossier de sortie
if OUT.resolve() != SRC.resolve():
    if (SRC / "assets").is_dir():
        shutil.copytree(SRC / "assets", OUT / "assets", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("._*", ".DS_Store"))
    else:  # dossier à plat, sans sous-dossier
        for f in SRC.iterdir():
            if not f.is_file() or f.name.startswith("."):
                continue
            ext = f.suffix.lower()
            dest = {".css": "assets", ".js": "assets", ".jpg": "assets/img", ".jpeg": "assets/img", ".png": "assets/img",
                    ".webp": "assets/img", ".mp4": "assets/video"}.get(ext)
            if dest:
                (OUT / dest).mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, OUT / dest / f.name)
    if (SRC / "photos-blog").is_dir():  # photos ajoutées par Léna dans Pages CMS
        shutil.copytree(SRC / "photos-blog", OUT / "photos-blog", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("._*", ".DS_Store"))
DOCTOLIB = "https://www.doctolib.fr/psychomotricien/aubagne/lena-marrou"
GOOGLE = "https://share.google/HbmKj3BRwNX8heagq"
TEL_TXT, TEL = "07 50 39 71 05", "tel:+33750397105"
MAIL = "lena.marrou@psychomotricien.eu"
INSTA = "https://www.instagram.com/lena.marrou/"

NAV = [("index.html", "Le cabinet"), ("mediation-equine.html", "Médiation équine"),
       ("equitherapie.html", "Équithérapie"), ("blog.html", "Mon blog"), ("contact.html", "Contact")]


def img(name, alt="", pos="", eager=False, cls="", sizes="(max-width: 760px) 100vw, 50vw"):
    if sizes == "320px": eager = True
    style = f' style="object-position:{pos}"' if pos else ""
    load = "" if eager else ' loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="assets/img/{name}-720.jpg" srcset="assets/img/{name}-720.jpg 720w, '
            f'assets/img/{name}.jpg 1400w" sizes="{sizes}" alt="{alt}"{style}{load}>')


def video(name, label=None, poster=None, slow=None, cls=""):
    aria = f' aria-label="{label}"' if label else ' aria-hidden="true"'
    p = f' poster="assets/img/{poster}"' if poster else ""
    s = f' data-slow="{slow}"' if slow else ""
    c = f' class="{cls}"' if cls else ""
    return f'<video{c} src="assets/video/{name}.mp4"{p}{s} autoplay muted loop playsinline preload="metadata"{aria}></video>'


def sticker(text, rot="-4deg", dl="0s", style=""):
    return f'<span class="sticker" style="--rot:{rot};--dl:{dl};{style}"><i></i>{text}</span>'


def marquee(items, dur="40s", rev=False, cls=""):
    inner = "".join(items)
    hidden = "".join(items).replace("<span ", '<span aria-hidden="true" ').replace("<div ", '<div aria-hidden="true" ')
    r = " rev" if rev else ""
    return f'<div class="marquee{r} {cls}" style="--dur:{dur}"><div class="marquee-track">{inner}{hidden}</div></div>'


def header(active, back=None):
    links = "\n".join(
        f'<a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{t}</a>' for h, t in NAV)
    return f'''<header class="top"><div class="top-in">
<div class="top-l">{f'<a class="top-back" href="{back}" aria-label="Retour">←</a>' if back else ""}<a class="brand" href="index.html">Léna Marrou<span>Psychomotricienne · Aubagne</span></a></div>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav">Menu</button>
<nav id="nav" class="nav" aria-label="Menu principal">
{links}
<a class="nav-cta" href="{DOCTOLIB}">Rendez-vous</a>
</nav>
</div></header>'''


def footer(dock_right=None):
    right = dock_right or (DOCTOLIB, "Rendez-vous")

    return f'''<footer class="foot"><div class="wrap">
<p class="foot-big">On en parle&nbsp;?</p>
<div class="foot-col">
<strong>Le cabinet</strong>
<span>219 Avenue de Verdun, 13400 Aubagne</span>
<span>Bâtiment I, dernière porte à gauche</span>
<span>Rez-de-chaussée, accès PMR</span>
<span>Du lundi au vendredi, de 8 h à 19 h</span>
</div>
<div class="foot-col">
<strong>Contact</strong>
<a href="{TEL}">{TEL_TXT}</a>
<a href="mailto:{MAIL}">{MAIL}</a>
<div class="foot-links"><a href="{INSTA}">Instagram</a><a href="contact.html">Formulaire</a><a href="mentions-legales.html">Mentions légales</a></div>
</div>
<div class="btns"><a class="btn btn-light" href="{DOCTOLIB}">Prendre rendez-vous <span class="arr">→</span></a></div>
<div class="foot-end"><small>© 2026 Léna Marrou, psychomotricienne · RPPS 10008419011</small><a class="sign" href="https://studiosierra-agence.fr" target="_blank" rel="noopener">Site réalisé par <img src="assets/img/studio-sierra.png" alt="Studio Sierra, image &amp; communication" width="101" height="36" loading="lazy"></a></div>
</div></footer>
<nav class="dock" aria-label="Contact rapide"><a href="{TEL}">Appeler</a><a href="{right[0]}">{right[1]}</a></nav>
<script src="assets/site.js"></script>'''


# ---------------------------------------------------------------- Articles du blog (écrits par Léna dans Pages CMS)
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def _slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "article"


def _front(text):
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return meta, body
    lines, body = m.group(1).split("\n"), m.group(2)
    i = 0
    while i < len(lines):
        mm = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", lines[i])
        i += 1
        if not mm:
            continue
        k, v = mm.group(1), mm.group(2).strip()
        if v in ("|", "|-", ">", ">-", "|+", ">+"):
            block = []
            while i < len(lines) and (lines[i].startswith(" ") or not lines[i].strip()):
                block.append(lines[i].strip()); i += 1
            v = ("\n" if v.startswith("|") else " ").join(block).strip()
        elif len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1].replace("\\\"", "\"").replace("''", "'")
        meta[k] = v
    return meta, body


def _inline(t):
    t = _html.escape(t, quote=False)
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)", lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}" loading="lazy">', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)|(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?!\w)", lambda m: f"<em>{m.group(1) or m.group(2)}</em>", t)
    t = re.sub(r" {2,}\n|\\\n", "<br>", t)
    return t


def _md(text):
    out, para, items, kind = [], [], [], None
    def flush():
        nonlocal para, items, kind
        if para:
            out.append("<p>" + _inline("\n".join(para)) + "</p>"); para = []
        if items:
            out.append(f"<{kind}>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + f"</{kind}>"); items = []; kind = None
    for line in text.replace("\r\n", "\n").split("\n"):
        s_ = line.strip()
        if not s_:
            flush(); continue
        h = re.match(r"^(#{1,6})\s+(.*)$", s_)
        if h:
            flush(); lvl = 2 if len(h.group(1)) <= 2 else 3
            out.append(f"<h{lvl}>{_inline(h.group(2))}</h{lvl}>"); continue
        li = re.match(r"^([-*+]|\d+[.)])\s+(.*)$", s_)
        if li:
            k = "ol" if li.group(1)[0].isdigit() else "ul"
            if para or (kind and kind != k): flush()
            kind = k; items.append(li.group(2)); continue
        if s_.startswith(">"):
            flush(); out.append("<blockquote><p>" + _inline(s_.lstrip("> ")) + "</p></blockquote>"); continue
        if items: flush()
        para.append(line.rstrip())
    flush()
    return "\n".join(out)


def _date_fr(d):
    try:
        y, m, j = (int(x) for x in d[:10].split("-"))
        return f"{j} {MOIS[m - 1]} {y}"
    except Exception:
        return ""


def _youtube(u):
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|embed/))([\w-]{6,})", u or "")
    return f"https://www.youtube-nocookie.com/embed/{m.group(1)}" if m else ""


def _instagram(u):
    m = re.search(r"instagram\.com/(?:[\w.]+/)?(p|reel|reels|tv)/([\w-]{5,})", u or "")
    if not m:
        return ""
    kind = "reel" if m.group(1) in ("reel", "reels") else ("tv" if m.group(1) == "tv" else "p")
    return f"https://www.instagram.com/{kind}/{m.group(2)}/embed/"


def load_posts():
    posts, files = [], []
    for folder in (SRC / "content" / "blog", SRC / "articles"):
        if folder.is_dir():
            files += sorted(folder.glob("*.md"))
    for f in files:
        if f.name.startswith("._"):
            continue
        meta, body = _front(f.read_text(encoding="utf-8"))
        titre = meta.get("titre") or meta.get("title") or ""
        if not titre or str(meta.get("brouillon", "")).lower() == "true":
            continue
        slug = _slug(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f.stem))
        posts.append({"titre": titre, "date": str(meta.get("date", ""))[:10], "resume": meta.get("resume", ""),
                      "image": meta.get("image", ""), "video": meta.get("video", ""),
                      "body": _md(body), "href": f"blog-{slug}.html"})
    posts.sort(key=lambda p: p["date"], reverse=True)
    if not posts:  # tant que Léna n'a rien publié, on garde le titre de son premier article
        posts = [{"titre": "Qu’est-ce qu’un bilan psychomoteur ?", "date": "2026-11-25", "resume": "", "image": "",
                  "video": "", "body": "", "href": "blog-bilan-psychomoteur.html"}]
    return posts


POSTS = load_posts()
CARD_BG = ["bg-lav", "bg-sky", "bg-mint", "bg-peach", "bg-straw", "bg-blue"]


def esc(t):
    return _html.escape(t).replace(" ?", "&nbsp;?").replace(" !", "&nbsp;!").replace(" :", "&nbsp;:").replace(" ;", "&nbsp;;")


def post_photo(p):
    if p["image"]:
        src = p["image"].lstrip("/")
        return f'<img src="{_html.escape(src)}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover">'
    return img("cabinet", "", "center")


def post_card(p, bg):
    when = _date_fr(p["date"])
    return (f'<a class="card {bg}" href="{p["href"]}" data-tilt><span class="lab">{when or "Article"}</span>'
            f'<span class="ti">{esc(p["titre"])}</span><span style="font-weight:800">Lire →</span></a>')


HEAD = '''<title>{title}</title>
{vfs}<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="assets/img/lena-cha-calin.jpg">
<meta name="theme-color" content="#FFFFFF">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Manrope:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="assets/site.css">'''


INTRO = '<div class="intro" aria-hidden="true"><i class="t"></i><i class="b"></i><span class="glow"><b class="g1"></b><b class="g2"></b><b class="g3"></b></span><span class="intro-txt"><span class="name">Léna Marrou</span><svg class="line" viewBox="0 0 520 26" preserveAspectRatio="none"><path d="M8 16 C 120 4, 220 24, 330 12 S 470 6, 512 14"/></svg><small>Psychomotricienne</small><em>Aubagne</em></span></div>'


def page(fname, title, desc, active, body, dock=None, is_index=False):
    head = HEAD.format(title=title, desc=desc, vfs="" if NETLIFY else '<meta name="claude:viewport-fit-sides" content="cover">\n')
    back = None if is_index else ("blog.html" if fname.startswith("blog-") else "index.html")
    if is_index and not NETLIFY:
        html = f'''{head}
<script>document.documentElement.classList.add("has-intro")</script>
{INTRO}
{header(active, back)}
<main>
{body}
</main>
{footer(dock)}
'''
    else:
        html = f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
{head}
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}</style>
{'<script>document.documentElement.classList.add("has-intro")</script>' if is_index else ""}
</head>
<body>
{INTRO if is_index else ""}
{header(active, back)}
<main>
{body}
</main>
{footer(dock)}
</body>
</html>
'''
    assert "ascenseur" not in html.lower(), fname
    (OUT / fname).write_text(html, encoding="utf-8")


FORMSPREE = "https://formspree.io/f/meagnlrr"
FORM_OPEN = (f'<form name="contact" method="POST" action="{FORMSPREE}" data-formspree>'
             '<input type="hidden" name="_subject" value="Nouvelle demande depuis le site">'
             '<input type="text" name="_gotcha" tabindex="-1" autocomplete="off" style="display:none">') if NETLIFY else '<form data-demo novalidate>'
FORM_NOTE = (f'<p class="form-note form-error" tabindex="-1" hidden>L’envoi n’a pas fonctionné. Réessayez dans un instant, ou écrivez à {MAIL}, ou appelez le {TEL_TXT}.</p>' if NETLIFY else
             f'<p class="form-note" tabindex="-1" hidden>Aperçu du site&nbsp;: l’envoi sera activé à la mise en ligne. En attendant, écrivez à {MAIL} ou appelez le {TEL_TXT}.</p>')

MOTIFS = [("L’écriture", "bg-cream"), ("La concentration en classe", "bg-blue"), ("L’agitation", "bg-mintp"),
          ("TDAH", "bg-peach"), ("Autisme", "bg-rose"), ("Dysgraphie", "bg-lav"), ("Impulsivité", "bg-sky"),
          ("Lenteur", "bg-straw"), ("Maladresse", "bg-mint"), ("Dyspraxie", "bg-peach"), ("Organisation", "bg-blue")]

REEL = [
    f'<div>{video("cha-resident", label="Un résident embrasse Cha")}</div>',
    f'<div>{img("ehpad-rire-portrait", "Une résidente rit contre la tête de Cha", sizes="320px")}</div>',
    f'<div>{img("lena-cha-calin", "Léna serre Cha dans ses bras", sizes="320px")}</div>',
    f'<div>{img("cha-chaussures", "Cha, chaussé, dans la salle commune d’un EHPAD", sizes="320px")}</div>',
    f'<div>{img("mains-pelage-2", "Des mains sur le chanfrein de Cha", sizes="320px")}</div>',
    f'<div>{img("cha-portrait", "Portrait de Cha sur la plage", sizes="320px")}</div>',
    f'<div>{img("main-pelage", "Une main de résidente sur Cha", sizes="320px")}</div>',
]

# ---------------------------------------------------------------- Accueil
page("index.html", "Léna Marrou psychomotricité",
     "Léna Marrou, psychomotricienne à Aubagne : bilan psychomoteur et rééducation psychomotrice pour enfants, adolescents, adultes et personnes âgées, au cabinet ou à domicile. TDAH, autisme, dysgraphie, dyspraxie, troubles de l’attention.",
     "index.html", f'''
<section class="hero-band">
<div class="hero">
<div class="layers cycle" data-parallax="0.25">
{video("cabinet-lumiere", poster="cabinet-lumiere-poster.jpg")}
{video("parcours-psychomoteur", poster="parcours-psychomoteur-poster.jpg")}
{video("cabinet-panorama", poster="cabinet-panorama-poster.jpg")}
</div>
<div class="veil"></div>
<div class="blob bg-lav" style="width:240px;height:240px;left:-60px;top:22%;opacity:.55" aria-hidden="true"></div>
<div class="blob bg-sky" style="width:180px;height:180px;right:12%;bottom:-50px;opacity:.5;animation-delay:-6s" aria-hidden="true"></div>
<div class="stickers" aria-hidden="true">
{sticker("Aubagne", "6deg", "0s")}
{sticker("Rez-de-chaussée · accès PMR", "-5deg", "-2s")}
</div>
<div class="hero-in">
<span class="eyebrow rise">Psychomotricienne à Aubagne</span>
<h1 class="h-hero" data-words>Développer ses capacités, nourrir ses apprentissages, renforcer sa confiance.</h1>
<p class="lead rise d2">J’accompagne les enfants, les adolescents, les adultes et les personnes âgées dans leur développement moteur, émotionnel et cognitif.</p>
<div class="btns rise d3">
<a class="btn btn-light" href="{DOCTOLIB}">Prendre rendez-vous <span class="arr">→</span></a>
</div>
<span class="scroll-cue rise d3"><b></b>Faites défiler</span>
</div>
</div>
</section>

<section aria-label="Ce qui amène les parents">
{marquee([f'<span class="word-chip {c}">{t}</span>' for t, c in MOTIFS], "36s")}
</section>

<section class="wrap me">
<div class="me-ph">
<div class="shape">{img("lena-portrait", "Portrait de Léna Marrou", "center 20%")}</div>
{sticker("Formée en médiation équine", "-6deg", "0s", "left:-10px;bottom:28px")}
{sticker("Bonjour&nbsp;!", "8deg", "-3s", "right:-6px;top:18px")}
</div>
<div class="stack">
<span class="eyebrow muted">Qui je suis</span>
<p class="statement" data-light>Je suis Léna, psychomotricienne diplômée d’État. Ce qui me passionne dans mon métier, c’est la richesse des rencontres, la diversité des parcours et la possibilité d’accompagner chacun dans ses besoins.</p>
</div>
</section>

<section id="pour-qui" class="wrap stack">
<span class="eyebrow muted">Pour qui</span>
<h2 class="h-l">Deux façons de travailler.</h2>
<div class="duo">
<a class="door" href="#comment" data-tilt>
{img("cabinet", "Le cabinet de Léna, lumineux, avec un canapé et une table de travail")}
<span class="door-in"><span class="tag">Au cabinet ou à domicile</span><h3>Enfants, adolescents, adultes, personnes âgées</h3><span>Écriture, concentration, agitation, TDAH, TSA, perte de mémoire, chutes à répétition&nbsp;: on fait le point, puis on avance ensemble. →</span></span>
</a>
<a class="door" href="mediation-equine.html" data-tilt>
{img("ehpad-rire", "Une résidente éclate de rire contre la tête de Cha")}
<span class="door-in"><span class="tag">Avec Cha</span><h3>Le cheval comme partenaire de rencontre, de partage et d’accompagnement.</h3><span>Médiation équine en EHPAD, MAS, FAM, soins palliatifs… →</span></span>
</a>
</div>
</section>

<section id="comment" class="wrap stack">
<span class="eyebrow muted">Comment ça se passe</span>
<h2 class="h-l">Du premier rendez-vous au suivi.</h2>
<div class="progress" data-progress><b></b></div>
<div class="steps">
<div class="step bg-mist" data-tilt><span class="n">01</span><h3>Le rendez-vous</h3><p>Vous m’appelez ou vous réservez directement sur Doctolib, au créneau qui vous arrange.</p></div>
<div class="step bg-blue" data-tilt><span class="n">02</span><h3>Le bilan</h3><p>Le bilan psychomoteur se déroule sur deux séances et débute par un temps d’échange (anamnèse) afin de mieux comprendre le parcours et les besoins de la personne. Il permet d’évaluer ses compétences, d’identifier ses éventuelles difficultés et de mettre en évidence ses ressources afin de pouvoir ensuite proposer un accompagnement adapté.</p></div>
<div class="step bg-mintp" data-tilt><span class="n">03</span><h3>Le compte rendu</h3><p>Le compte rendu du bilan est rédigé dans un délai de 2 à 3 semaines. Nous convenons ensuite d’un échange téléphonique afin de vous présenter les résultats, de vous en expliquer les conclusions et d’échanger ensemble sur les éventuelles préconisations.</p></div>
<div class="step bg-cream" data-tilt><span class="n">04</span><h3>Le suivi</h3><p>Des séances de 30 ou 45 minutes selon ses besoins, une fois par semaine.</p></div>
</div>
</section>

<section class="grow" aria-label="Le cabinet">
<div class="grow-pin">
<div class="grow-media">{video("cabinet-lumiere", label="Le cabinet de Léna, baigné de lumière", poster="cabinet-lumiere-poster.jpg")}</div>
<div class="grow-txt">
<span class="eyebrow">Le cabinet</span>
<p class="h-xl">Un lieu calme, plein de lumière.</p>
<p class="lead">«&nbsp;Une photographie des compétences et des difficultés de votre enfant.&nbsp;» C’est ici que tout commence.</p>
</div>
</div>
</section>

<section class="wrap stack">
<span class="eyebrow muted">Tarifs</span>
<h2 class="h-l">Clairs, dès le départ.</h2>
<div class="prices">
<div class="price bg-lav" data-tilt><b data-count="180" data-suffix="&nbsp;€">180&nbsp;€</b><span>Bilan, tout compris</span></div>
<div class="price bg-sky" data-tilt><b data-count="38" data-suffix="&nbsp;€">38&nbsp;€</b><span>Séance de 30 minutes</span></div>
<div class="price bg-mint" data-tilt><b data-count="45" data-suffix="&nbsp;€">45&nbsp;€</b><span>Séance de 45 minutes</span></div>
<div class="price bg-peach" data-tilt><b data-count="50" data-suffix="&nbsp;€">50&nbsp;€</b><span>Séances à domicile et équithérapie, 1 heure</span></div>
</div>
<div class="note">
<span class="pill">Certaines mutuelles prennent en charge le bilan et quelques séances</span>
<span class="pill">Conventionnée PCO 0–6 ans et 7–12 ans</span>
<span class="pill">Conventionnée Résodys</span>
<span class="pill">Accompagnement des personnes bénéficiant d’une notification MDPH</span>
</div>
</section>

<section class="wrap stack">
<span class="eyebrow muted">Ils en parlent</span>
<h2 class="h-l">Ce qu’en disent les familles.</h2>
<div class="reviews">
<figure class="review bg-lav" data-tilt><span class="q" aria-hidden="true">“</span><blockquote>Léna est une psychomotricienne douce, bienveillante et à l’écoute. Elle a su prendre le temps de comprendre les besoins de notre enfant et de s’adapter à elle, toujours dans le respect de son rythme. Grâce à son approche rassurante et aux activités proposées, elle a pu prendre confiance en elle et progresser. Un grand merci pour son accompagnement et sa patience&nbsp;!</blockquote><figcaption><strong>Loïc V.</strong><span>Parent · avis Google</span></figcaption></figure>
<figure class="review bg-sky" data-tilt><span class="q" aria-hidden="true">“</span><blockquote>Je tiens particulièrement à souligner le grand professionnalisme de Léna. Léna est une personne très empathique, à l’écoute, d’une grande bienveillance et qui sait s’adapter à chaque problématique pour un accompagnement en douceur et avec toujours autant d’efficacité. Une perle rare. Je la recommande les yeux fermés.</blockquote><figcaption><strong>Magali A.</strong><span>Praticienne en hypnose, elle lui adresse des patients · avis Google</span></figcaption></figure>
<figure class="review bg-mintp" data-tilt><span class="q" aria-hidden="true">“</span><blockquote>À la recherche d’une psychomotricienne professionnelle, talentueuse et à l’écoute&nbsp;? Ne cherchez plus, Léna est la personne qu’il vous faut&nbsp;! Très douce et attentionnée avec les personnes, elle sait vous mettre à l’aise et en confiance. Je recommande les yeux fermés.</blockquote><figcaption><strong>Florent</strong><span>Avis Google</span></figcaption></figure>
</div>
<a class="btn btn-soft" style="align-self:flex-start" href="{GOOGLE}">Voir tous ses avis sur Google <span class="arr">→</span></a>
</section>

<section class="wrap stack">
<span class="eyebrow muted">Où me trouver</span>
<h2 class="h-l">Dans un espace pluridisciplinaire, à Aubagne.</h2>
<div class="cab">
<div class="main">{video("cabinet-panorama", label="Vue d’ensemble du cabinet", poster="cabinet-panorama-poster.jpg")}{sticker("Rez-de-chaussée · accès PMR", "-3deg")}</div>
<div class="info bg-cream"><strong>219 Avenue de Verdun<br>13400 Aubagne</strong><span>Bâtiment I, dernière porte à gauche.</span><span>Du lundi au vendredi, de 8 h à 19 h.</span><a class="btn btn-dark" style="align-self:flex-start;margin-top:8px" href="{GOOGLE}">Itinéraire <span class="arr">→</span></a></div>
</div>
</section>

<section class="wrap stack">
<span class="eyebrow muted">Mon blog</span>
<h2 class="h-l">Des réponses simples.</h2>
<div class="cards">
{"".join(post_card(p, CARD_BG[i % 6]) for i, p in enumerate(POSTS[:3]))}
</div>
<a class="btn btn-soft" style="align-self:flex-start" href="blog.html">Tous les articles <span class="arr">→</span></a>
</section>

<section class="wrap">
<div class="cta bg-lav">
<div class="blob bg-sky" style="width:260px;height:260px;right:-80px;top:-80px;opacity:.7" aria-hidden="true"></div>
<div class="blob bg-peach" style="width:200px;height:200px;left:-60px;bottom:-70px;opacity:.8;animation-delay:-4s" aria-hidden="true"></div>
<h2 class="h-xl">Vous vous posez la question pour votre enfant ou un membre de votre famille&nbsp;?</h2>
<p class="lead">Le plus simple, c’est d’en parler.</p>
<div class="btns" style="justify-content:center">
<a class="btn btn-dark" href="{DOCTOLIB}">Prendre rendez-vous sur Doctolib <span class="arr">→</span></a>
<details class="reach">
<summary class="btn btn-light">Contact</summary>
<div class="reach-pop">
<span class="reach-num">{TEL_TXT}</span>
<div class="reach-btns">
<a class="btn btn-dark" href="{TEL}">Appeler</a>
<a class="btn btn-soft" href="https://wa.me/33750397105">WhatsApp</a>
<a class="btn btn-soft" href="sms:+33750397105">SMS</a>
</div>
</div>
</details>
<a class="btn btn-light" href="contact.html#autre">Poser une question</a>
</div>
</div>
</section>
''', is_index=True)

# ---------------------------------------------------------------- Médiation
page("mediation-equine.html", "Médiation équine · Léna Marrou psychomotricité",
     "Médiation équine en établissement avec Cha, autour d’Aubagne : EHPAD, MAS, FAM, soins palliatifs, hôpitaux de jour. Séances d’une heure, sur devis.",
     "mediation-equine.html", f'''
<section class="hero-band">
<div class="hero">
<div class="layers" data-parallax="0.25">{video("cha-mediation", poster="cha-mediation-poster.jpg")}</div>
<div class="veil"></div>
<div class="blob bg-sky" style="width:220px;height:220px;right:-60px;top:30%;opacity:.45" aria-hidden="true"></div>
<div class="hero-in">
<a class="back rise" style="background:rgba(255,255,255,.22);color:#fff" href="index.html">← Retour</a>
<span class="eyebrow rise">Médiation équine en établissement</span>
<h1 class="h-xxl" data-words>Cha vient jusqu’à vos résidents.</h1>
<p class="lead rise d2">Avec mon cheval, j’interviens dans les établissements autour d’Aubagne, dans le cadre de vos thérapies non médicamenteuses.</p>
<div class="btns rise d3">
<a class="btn btn-light" href="contact.html#devis">Demander un devis <span class="arr">→</span></a>
<a class="btn btn-line" href="#seance">Une séance, comment ça marche</a>
</div>
</div>
</div>
</section>

<section class="wrap narrow">
<p class="statement statement-s statement-blue center" data-light>Le cheval accueille chacun sans jugement. Par sa présence, sa taille et sa douceur, Cha peut devenir un véritable support de réassurance. Sa communication repose essentiellement sur le langage non verbal, invitant chacun à observer, écouter et ajuster ses comportements pour entrer en relation avec lui.</p>
</section>

<section id="seance" class="wrap stack">
<span class="eyebrow muted">Une séance</span>
<h2 class="h-l">Une heure avec Cha.</h2>
<div class="tiles">
<div class="tile bg-lav" data-tilt><span class="big" data-count="1" data-suffix="&nbsp;h">1&nbsp;h</span><p>Le temps d’une séance environ, au rythme des résidents.</p></div>
<div class="tile bg-sky" data-tilt><span class="big" data-count="20">20</span><p>Personnes maximum, c’est ce qui est recommandé afin de préserver la qualité des interactions et de permettre à chacun de profiter pleinement de la rencontre avec Cha.</p></div>
<div class="tile bg-mint" data-tilt><span class="t">À l’intérieur ou à l’extérieur</span><p>En fonction des conditions météorologiques et de vos besoins.</p></div>
<div class="tile bg-peach" data-tilt><span class="t">Propre et chaussé</span><p>Cha est soigneusement nettoyé et porte des chaussures, pour son confort et l’hygiène de l’établissement.</p></div>
</div>
</section>

<section class="grow" aria-label="Le contact avec Cha">
<div class="grow-pin">
<div class="grow-media">{img("mains-pelage-2", "Les mains d’une résidente sur le chanfrein de Cha", sizes="100vw")}</div>
<div class="grow-txt"><p class="h-xl">Des doigts qui se délient.</p><p class="lead">Pour sentir le pelage au creux de la main.</p></div>
</div>
</section>

<section class="wrap split">
<div class="ph blobby">{img("ehpad-rire-portrait", "Une résidente rit, front contre la tête de Cha")}</div>
<div class="stack">
<span class="eyebrow muted">Ce que j’observe</span>
<h2 class="h-m">La rencontre avec le cheval mobilise les sens et favorise les interactions.</h2>
<p class="muted" style="font-size:18px">Le contact avec le cheval, sa chaleur, son odeur, sa texture et sa présence sollicitent les perceptions sensorielles et peuvent faire émerger des souvenirs, des émotions et des sensations. Ces expériences peuvent contribuer à l’apaisement, à la mobilisation corporelle et à la valorisation de la personne.</p>
<ol class="list">
<li><b>01</b><span>Apaisement émotionnel</span></li>
<li><b>02</b><span>Mobilisation attentionnelle</span></li>
<li><b>03</b><span>Engagement corporel et moteur</span></li>
<li><b>04</b><span>Sollicitations sensori-motrices</span></li>
</ol>
</div>
</section>

<section class="band bg-sky">
<div class="blob bg-lav" style="width:320px;height:320px;left:-120px;top:-80px;opacity:.6" aria-hidden="true"></div>
<div class="blob bg-mint" style="width:260px;height:260px;right:-90px;bottom:-60px;opacity:.6;animation-delay:-5s" aria-hidden="true"></div>
<div class="band-in">
<div class="wrap stack" style="align-items:center;max-width:900px">
<span class="eyebrow">Médiation équine en établissement</span>
<h2 class="h-xxl" data-words>Voici Cha.</h2>
<p class="lead">C’est un cheval Zangersheide de 15 ans mesurant 1,70&nbsp;m. Il fait aussi du saut d’obstacles, du dressage et des balades. Chaussé et soigneusement nettoyé, il vient au contact des résidents, à l’intérieur des établissements.</p>
</div>
{marquee(REEL, "50s", cls="reel")}
<div class="stats">
<div><b data-count="1" data-suffix="&nbsp;h">1&nbsp;h</b><span>par séance environ</span></div>
<div><b data-count="20">20</b><span>personnes au maximum par séance recommandé</span></div>
<div><b data-count="35" data-suffix="&nbsp;km">35&nbsp;km</b><span>autour d’Aubagne</span></div>
<div><b data-count="20" data-prefix="+" data-suffix="&nbsp;M">+20&nbsp;M</b><span>de vues sur Instagram</span></div>
</div>
<div class="btns" style="justify-content:center">
<a class="btn btn-dark" href="contact.html#devis">Demander un devis <span class="arr">→</span></a>
</div>
</div>
</section>

<section class="wrap">
<div class="where bg-lav">
<div class="blob bg-sky" style="width:260px;height:260px;right:-90px;top:-90px;opacity:.7" aria-hidden="true"></div>
<div class="blob bg-peach" style="width:200px;height:200px;left:-70px;bottom:-80px;opacity:.7;animation-delay:-4s" aria-hidden="true"></div>
<span class="eyebrow">Où j’interviens</span>
<h2 class="h-l">Le cheval comme partenaire dans un accompagnement à visée thérapeutique.</h2>
<div class="chips">
<span class="chip">EHPAD</span><span class="chip">Résidences seniors</span><span class="chip">Accueils de jour</span><span class="chip">FAM</span><span class="chip">MAS</span><span class="chip">EEAP</span><span class="chip">SESSAD</span><span class="chip">CAMSP</span><span class="chip">Soins palliatifs</span><span class="chip">Hôpitaux de jour</span>
</div>
<p style="font-size:18px;font-weight:700">Jusqu’à 35 km autour d’Aubagne.</p>
</div>
</section>
''', dock=("contact.html#devis", "Devis"))

# ---------------------------------------------------------------- Équithérapie
page("equitherapie.html", "Équithérapie · Léna Marrou psychomotricité",
     "Séances individuelles d’équithérapie d’une heure avec Cha, cheval Zangersheide, près d’Aubagne, avec Léna Marrou, psychomotricienne.",
     "equitherapie.html", f'''
<section class="hero-band">
<div class="hero hero-equi" style="background:var(--mint-pale)">
<div class="layers" data-parallax="0.2">{img("equi-hero", "", pos="60% 30%", eager=True, cls="kb", sizes="100vw")}</div>
<div class="veil"></div>
<div class="stickers stickers-right" aria-hidden="true">{sticker("Aubagne", "5deg", "0s")}</div>
<div class="hero-in">
<a class="back rise" style="background:rgba(255,255,255,.22);color:#fff" href="index.html">← Retour</a>
<span class="eyebrow rise">Équithérapie</span>
<h1 class="h-xxl" data-words>Une heure avec Cha.</h1>
<p class="lead rise d2">Je suis psychomotricienne diplômée d’État, formée à la médiation équine. Les séances sont conduites par mes soins, directement aux écuries à Aubagne. Le cheval est intégré au projet thérapeutique comme support du travail psychomoteur, dans le respect des besoins et des capacités de chaque personne.</p>
<div class="btns rise d3"><a class="btn btn-light" href="contact.html#equitherapie">Demander un créneau <span class="arr">→</span></a></div>
</div>
</div>
</section>

<section class="wrap stack">
<span class="eyebrow muted">Infos pratiques</span>
<div class="tiles">
<div class="tile bg-lav" data-tilt><span class="big" data-count="1" data-suffix="&nbsp;h">1&nbsp;h</span><p>C’est la durée d’une séance, au rythme de chacun.</p></div>
<div class="tile bg-sky" data-tilt><span class="big" data-count="50" data-suffix="&nbsp;€">50&nbsp;€</span><p>C’est le prix d’une séance complète, aux écuries.</p></div>
<div class="tile bg-mint" data-tilt><span class="t">Le rendez-vous</span><p>Vous m’appelez ou bien vous m’écrivez. Nous discutons de vos besoins. On planifie ensemble une première séance.</p></div>
</div>
</section>

<section class="wrap stack">
<span class="eyebrow muted">Pourquoi le cheval</span>
<h2 class="h-l">Trois raisons, simplement.</h2>
<div class="tiles">
<div class="tile bg-mist" data-tilt><span class="t">Une relation sans jugement</span><p>Le cheval accueille les interactions sans jugement ni attente de performance. Cette particularité permet à chacun de prendre sa place dans la relation, à son rythme, sans crainte du regard de l’autre.</p></div>
<div class="tile bg-blue" data-tilt><span class="t">Un partenaire sécurisant</span><p>Par sa présence, son gabarit et sa sensibilité, Cha peut contribuer à créer un sentiment de sécurité. Sa présence offre un support à l’engagement corporel, émotionnel et relationnel.</p></div>
<div class="tile bg-cream" data-tilt><span class="t">Une communication non verbale et immédiate</span><p>Le cheval communique principalement par le langage corporel et réagit à son environnement ainsi qu’aux interactions. Ses réponses invitent à prendre conscience de sa posture, de ses gestes et de son positionnement, tout en développant les capacités d’observation, d’adaptation et d’ajustement relationnel.</p></div>
</div>
</section>

<section class="wrap split split-top">
<div class="ph blobby">{img("equi-pour-qui", "Une personne de dos tient un cheval à la longe, près d’un obstacle, sur la carrière", pos="45% 60%")}</div>
<div class="stack">
<span class="eyebrow muted">Les séances</span>
<h2 class="h-l">Pour qui&nbsp;?</h2>
<p class="muted" style="font-size:18px">Les séances peuvent s’adresser aux enfants, adolescents, adultes et personnes âgées présentant notamment les difficultés ou les troubles suivants&nbsp;:</p>
<ol class="list list-s">
<li><b>01</b><span>Trouble du spectre de l’autisme (TSA)</span></li>
<li><b>02</b><span>Trouble développemental de la coordination (TDC / dyspraxie)</span></li>
<li><b>03</b><span>Trouble du déficit de l’attention avec ou sans hyperactivité (TDAH)</span></li>
<li><b>04</b><span>Difficultés dans les interactions sociales et la communication</span></li>
<li><b>05</b><span>Sclérose en plaques (SEP)</span></li>
<li><b>06</b><span>Maladie de Parkinson</span></li>
<li><b>07</b><span>Séquelles d’accident vasculaire cérébral (AVC)</span></li>
<li><b>08</b><span>Troubles de la coordination, de l’équilibre et de la posture</span></li>
<li><b>09</b><span>Peur de la chute et difficultés à maintenir son équilibre</span></li>
<li><b>10</b><span>Troubles anxieux</span></li>
<li><b>11</b><span>Épisodes dépressifs</span></li>
<li><b>12</b><span>Personnes ayant vécu du harcèlement scolaire ou professionnel</span></li>
<li><b>13</b><span>Personnes ayant été confrontées à des violences physiques ou psychologiques</span></li>
</ol>
</div>
</section>

<section class="grow grow-long" aria-label="Léna et Cha dans l’eau">
<div class="grow-pin">
<div class="grow-media">{img("lena-cha-eau", "Léna, dans l’eau, front contre la tête de Cha", pos="50% 42%", sizes="100vw")}</div>
<div class="grow-txt"><p class="h-l">Le travail avec le cheval permet de solliciter différentes dimensions psychomotrices, sensorielles, émotionnelles et relationnelles.</p><p class="grow-p">Il favorise la conscience corporelle, les ajustements toniques et posturaux, l’équilibre ainsi que la coordination des mouvements. Les interactions avec l’animal offrent également des expériences sensorielles variées et permettent de travailler le repérage dans l’espace. La relation avec le cheval constitue un support pour développer la communication non verbale, la régulation émotionnelle et la confiance en soi. Enfin, les activités proposées encouragent l’autonomie, la prise d’initiative et la valorisation des capacités de chacun.</p></div>
</div>
</section>

<section class="wrap narrow">
<p class="statement statement-s statement-blue center" data-light>Chaque séance est construite en fonction des besoins, des capacités et des objectifs de chacun. Les axes de travail sont évolutifs et réadaptés au fil de l’accompagnement.</p>
</section>

<section class="wrap split">
<div class="ph blobby">{img("cha-montagne-centre", "Cha sellé, face aux montagnes")}</div>
<div class="stack">
<span class="eyebrow muted">Qui est Cha&nbsp;?</span>
<p class="statement statement-s" style="margin-inline:0" data-light>Cha est un cheval Zangersheide, âgé de 15 ans. Il mesure 1,70&nbsp;m au garrot.</p>
<p style="font-size:18px">Doté d’un tempérament calme, doux et attentif, il se distingue par sa sensibilité et sa proximité avec l’humain. Curieux et sociable, il manifeste un réel intérêt pour les interactions et s’adapte à la présence des personnes qui l’entourent.</p>
<p style="font-size:18px">Sa disponibilité relationnelle, sa patience et sa capacité à évoluer dans différents environnements en font un partenaire privilégié dans le cadre des séances d’équithérapie.</p>
<p style="font-size:18px">Au-delà de ses qualités, Cha occupe une place essentielle dans les accompagnements&nbsp;: il participe pleinement à la rencontre et aux interactions, chacun pouvant développer une relation avec lui à son propre rythme.</p>
</div>
</section>

''', dock=("contact.html#equitherapie", "Un créneau"))

# ---------------------------------------------------------------- Contact (formulaire unique)
page("contact.html", "Contact · Léna Marrou psychomotricité",
     "Écrire à Léna Marrou, psychomotricienne à Aubagne : bilan psychomoteur, séance de psychomotricité, médiation équine, séance à domicile, équithérapie ou toute autre question.",
     "contact.html", f'''
<section class="wrap stack" style="padding-top:56px">
<a class="back rise" href="index.html">← Retour</a>
<h1 class="h-xl" data-words>Une demande&nbsp;?</h1>
<p class="lead muted rise d2">Pour un rendez-vous au cabinet, le plus rapide reste <a href="{DOCTOLIB}">Doctolib</a>. Pour tout le reste, c’est ici.</p>
</section>

<section class="wrap">
<div class="form-wrap">
{FORM_OPEN}
<fieldset class="seg">
<legend>C’est pour…</legend>
<input type="radio" name="type" id="t-bilan" value="bilan"><label for="t-bilan">Bilan psychomoteur</label>
<input type="radio" name="type" id="t-seance" value="seance"><label for="t-seance">Séance de psychomotricité</label>
<input type="radio" name="type" id="t-devis" value="devis"><label for="t-devis">Médiation équine</label>
<input type="radio" name="type" id="t-dom" value="domicile"><label for="t-dom">Séance à domicile</label>
<input type="radio" name="type" id="t-equi" value="equitherapie"><label for="t-equi">Équithérapie</label>
<input type="radio" name="type" id="t-autre" value="autre"><label for="t-autre">Une autre question</label>
</fieldset>

<fieldset class="fields" data-for="bilan">
<label class="field" for="b-pour">Pour qui&nbsp;?<select id="b-pour" name="pour_qui"><option>Mon enfant</option><option>Moi-même</option><option>Un proche</option></select></label>
<label class="field" for="b-age">Date de naissance<input id="b-age" name="date_naissance" type="date"></label>
<label class="field full" for="b-msg">Votre message<textarea id="b-msg" name="message" rows="3"></textarea></label>
</fieldset>

<fieldset class="fields" data-for="seance">
<label class="field" for="s-pour">Pour qui&nbsp;?<select id="s-pour" name="pour_qui"><option>Mon enfant</option><option>Moi-même</option><option>Un proche</option></select></label>
<label class="field" for="s-age">Date de naissance<input id="s-age" name="date_naissance" type="date"></label>
<label class="field full" for="s-msg">Votre message<textarea id="s-msg" name="message" rows="3"></textarea></label>
</fieldset>

<fieldset class="fields" data-for="domicile">
<label class="field" for="h-pour">Pour qui&nbsp;?<select id="h-pour" name="pour_qui"><option>Mon enfant</option><option>Moi-même</option><option>Un proche</option></select></label>
<label class="field" for="h-ville">Ville<input id="h-ville" name="ville" autocomplete="address-level2"></label>
<label class="field full" for="h-msg">Votre message<textarea id="h-msg" name="message" rows="3"></textarea></label>
</fieldset>

<fieldset class="fields" data-for="equitherapie">
<label class="field" for="e-pour">Pour qui&nbsp;?<select id="e-pour" name="pour_qui"><option>Mon enfant</option><option>Moi-même</option><option>Un proche</option></select></label>
<label class="field" for="e-age">Date de naissance<input id="e-age" name="date_naissance" type="date"></label>
<label class="field full" for="e-but">Ce que vous aimeriez travailler<textarea id="e-but" name="objectif" rows="3"></textarea></label>
<label class="field full" for="e-dispo">Vos disponibilités<input id="e-dispo" name="disponibilites" placeholder="Par exemple : mercredi après-midi"></label>
</fieldset>

<fieldset class="fields" data-for="devis">
<label class="field" for="d-etab">Établissement<input id="d-etab" name="etablissement" autocomplete="organization"></label>
<label class="field" for="d-type">Type d’établissement<select id="d-type" name="type_etablissement"><option>EHPAD</option><option>Résidence seniors</option><option>Accueil de jour</option><option>FAM</option><option>MAS</option><option>EEAP</option><option>SESSAD</option><option>CAMSP</option><option>Soins palliatifs</option><option>Hôpital de jour</option><option>École ou autre</option></select></label>
<label class="field" for="d-ville">Ville<input id="d-ville" name="ville" autocomplete="address-level2"></label>
<label class="field full" for="d-msg">Votre projet<textarea id="d-msg" name="projet" rows="3"></textarea></label>
</fieldset>

<fieldset class="fields" data-for="autre">
<label class="field full" for="a-msg">Votre question<textarea id="a-msg" name="question" rows="4"></textarea></label>
</fieldset>

<fieldset class="fields">
<label class="field" for="c-nom">Votre nom<input id="c-nom" name="nom" autocomplete="name"></label>
<label class="field" for="c-mail">E-mail<input id="c-mail" name="email" type="email" autocomplete="email"></label>
<label class="field" for="c-tel">Téléphone<input id="c-tel" name="tel" type="tel" autocomplete="tel"></label>
</fieldset>

<button class="btn btn-dark" type="submit" style="align-self:flex-start">Envoyer ma demande <span class="arr">→</span></button>
{FORM_NOTE}
<p class="hint">Vos informations servent uniquement à vous répondre.</p>
</form>
</div>
</section>
''')

# ---------------------------------------------------------------- Blog
if POSTS:
    _f = POSTS[0]
    BLOG_LIST = f'''<section class="wrap stack">
<a class="feature" href="{_f["href"]}" data-tilt>
<span class="ph">{post_photo(_f)}</span>
<span class="tx">
<span class="badge">À la une</span>
<span class="h-m" style="font-family:var(--display);font-weight:800;letter-spacing:-.03em;line-height:1.02">{esc(_f["titre"])}</span>
{f'<span style="font-size:18px">{esc(_f["resume"])}</span>' if _f["resume"] else ""}
<span style="font-weight:800">Lire l’article →</span>
</span>
</a>
{'<div class="cards">' + "".join(post_card(p, CARD_BG[(i + 1) % 6]) for i, p in enumerate(POSTS[1:])) + '</div>' if len(POSTS) > 1 else ""}
</section>'''
else:
    BLOG_LIST = '<section class="wrap"><p class="lead muted">Les premiers articles arrivent bientôt.</p></section>'

page("blog.html", "Mon blog · Léna Marrou psychomotricité",
     "Les articles de Léna Marrou, psychomotricienne à Aubagne : bilan psychomoteur, TDAH, dysgraphie.",
     "blog.html", f'''
<section class="wrap stack" style="padding-top:56px">
<a class="back rise" href="index.html">← Retour</a>
<h1 class="h-xxl" data-words>Mon blog</h1>
<p class="lead muted rise d2">Mieux comprendre pour mieux accompagner.<br>Découvrir la psychomotricité, comprendre le développement et éclairer les questionnements des familles.</p>
</section>

{BLOG_LIST}
''')

# ---------------------------------------------------------------- Articles
for p in POSTS:
    video_html = ""
    if p["video"]:
        yt, ig = _youtube(p["video"]), _instagram(p["video"])
        if yt:
            video_html = f'<div class="ph" style="height:auto;aspect-ratio:16/9"><iframe src="{yt}" title="Vidéo" style="width:100%;height:100%;border:0" allow="encrypted-media; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>'
        elif ig:
            video_html = (f'<div class="insta"><iframe src="{ig}" title="Vidéo Instagram" allowtransparency="true" allowfullscreen loading="lazy"></iframe></div>'
                          f'<p><a class="btn btn-soft" href="{_html.escape(p["video"])}" target="_blank" rel="noopener">Voir sur Instagram <span class="arr">→</span></a></p>')
        else:
            video_html = f'<p><a class="btn btn-soft" href="{_html.escape(p["video"])}" target="_blank" rel="noopener">Voir la vidéo <span class="arr">→</span></a></p>'
    when = _date_fr(p["date"])
    photo = f'<div class="ph" style="height:auto;aspect-ratio:16/10">{post_photo(p)}</div>' if p["image"] else ""
    page(p["href"], f'{p["titre"]} · Léna Marrou',
         (p["resume"] or f'{p["titre"]} Un article de Léna Marrou, psychomotricienne à Aubagne.').replace('"', "'"),
         "blog.html", f'''
<section class="wrap prose article" style="padding-top:56px">
<a class="back rise" href="blog.html">← Mon blog</a>
<h1 class="h-l" data-words>{esc(p["titre"])}</h1>
{f'<div class="byline rise d2">{img("lena-portrait", "", "center 20%", eager=True, sizes="48px")}<span><strong style="color:var(--ink)">Léna Marrou</strong> · {when}</span></div>' if when and (p["body"] or p["image"]) else ""}
{photo}
{p["body"]}
{video_html}
</section>
''')

# ---------------------------------------------------------------- Mentions légales
page("mentions-legales.html", "Mentions légales · Léna Marrou psychomotricité",
     "Mentions légales du site de Léna Marrou, psychomotricienne à Aubagne.",
     "", f'''
<section class="wrap prose article" style="padding-top:56px">
<a class="back" href="index.html">← Retour</a>
<h1 class="h-l">Mentions légales</h1>
<h2>Éditrice du site</h2>
<p>Léna Marrou, psychomotricienne en exercice libéral.<br>219 Avenue de Verdun, bâtiment I, 13400 Aubagne.<br>RPPS&nbsp;: 10008419011.<br>SIRET&nbsp;: [à compléter en janvier 2027, avec le nouveau statut].<br>Contact&nbsp;: {MAIL} · {TEL_TXT}</p>
<h2>Hébergement</h2>
<p>Cloudflare, Inc., 101 Townsend Street, San Francisco, CA 94107, États-Unis (service Cloudflare Pages).</p>
<h2>Conception du site</h2>
<p>Studio Sierra, Marseille · <a href="https://studiosierra-agence.fr">studiosierra-agence.fr</a></p>
<h2>Photos et vidéos</h2>
<p>Les photos et vidéos appartiennent à Léna Marrou. Les personnes qui y apparaissent ont donné leur accord.</p>
<h2>Données personnelles</h2>
<p>Les informations envoyées par le formulaire sont transmises par le service Formspree et servent uniquement à répondre à votre demande. Vous pouvez demander leur suppression à {MAIL}.</p>
</section>
''')

# ---------------------------------------------------------------- Merci
page("merci.html", "Merci · Léna Marrou psychomotricité", "Votre demande est bien partie.", "", f'''
<section class="wrap narrow center stack" style="padding-top:96px;align-items:center">
<h1 class="h-xxl" data-words>Merci&nbsp;!</h1>
<p class="lead">Votre demande est bien partie. Je vous réponds dès que possible.</p>
<a class="btn btn-dark" href="index.html">Revenir à l’accueil <span class="arr">→</span></a>
</section>
''')

# ---------------------------------------------------------------- 404
page("404.html", "Page introuvable · Léna Marrou psychomotricité",
     "Cette page n’existe pas.", "", '''
<section class="wrap narrow center stack" style="padding-top:96px;align-items:center">
<h1 class="h-xxl" data-words>Oups.</h1>
<p class="lead">Cette page n’existe pas, ou elle a changé d’adresse.</p>
<a class="btn btn-dark" href="index.html">Revenir à l’accueil <span class="arr">→</span></a>
</section>
''')
print("ok", sorted(p.name for p in OUT.glob("*.html")))
