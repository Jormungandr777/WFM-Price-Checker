"""
Warframe Market Price Checker  v1.4.1
pip install requests pillow beautifulsoup4 lxml

FILES:
  config.json   — auth, launches, settings  (replaces config.txt + launch_counter.json)
  app_cache.json — items + descriptions      (replaces items_cache.json + desc_cache.json)
  items.txt     — selected items (* prefix)
  img/          — cached item images (delete to re-download)

NOTE: delete app_cache.json to force full re-fetch of items and descriptions.
      delete img/ to re-download all images.
"""
import os, time, random, json, threading, tkinter as tk, webbrowser, re
from tkinter import ttk, messagebox
from pathlib import Path
try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False
import requests

# ── Constants ────────────────────────────────────────────────────
VERSION      = "1.5.2"
UA           = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0"
CONFIG_JSON  = "config.json"
APP_CACHE    = "app_cache.json"
ITEMS_FILE   = "items.txt"
IMG_DIR      = Path("img")
API          = "https://api.warframe.market/v2"
CDN          = "https://warframe.market/static/assets/"
IMG_SIZE     = (110, 110)
IMG_ZOOM     = (320, 320)   # hover popup size
IMG_DIR.mkdir(exist_ok=True)

# ── Settings defaults (overridden by config.json["settings"]) ────
_DEF_SETTINGS = {
    "refresh_every":   10,
    "fetch_delay_min": 2,
    "fetch_delay_max": 5,
    "top_sellers":     5,
}

WIKI            = "https://wiki.warframe.com/w"
FETCH_ALL_DELAY = 5.0   # secondi fissi tra item nel fetch-all

# ── Fonts ────────────────────────────────────────────────────────
F = dict(
    h1    = ("Segoe UI", 13, "bold"),
    h2    = ("Segoe UI", 10, "bold"),
    body  = ("Segoe UI", 9),
    small = ("Segoe UI", 8),
    tiny  = ("Segoe UI", 7),
    data  = ("Consolas", 9),
    datasm= ("Consolas", 8),
    mono  = ("Consolas", 26),
    spin  = ("Consolas", 56),
)

# ── Palette ──────────────────────────────────────────────────────
C = dict(
    bg      = "#07090f",
    bg2     = "#0c1018",
    bg3     = "#121820",
    bg4     = "#18222e",
    bg5     = "#1e2c3c",
    accent  = "#5bc8ff",
    gold    = "#d4982a",
    gold2   = "#8a6018",
    gold_hi = "#f0c060",
    gold_dim= "#2a1e08",
    text    = "#d8e8f8",
    dim     = "#304050",
    mid     = "#607898",
    muted   = "#8898b0",
    green   = "#00e676",
    green2  = "#004422",
    red     = "#ff4455",
    red_dim = "#220a0d",
    orange  = "#ffaa00",
    border  = "#141e2c",
    border2 = "#1c2a3c",
)

# ════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════
# Category system — tag reali verificati da API v2 + mapping
# augment mods per syndicate dalla wiki fandom
# ════════════════════════════════════════════════════════════════

# Mapping esatto nome_mod (lowercase) → syndicates
# Fonte: warframe.fandom.com/wiki/Warframe_Augment_Mods
_SYND_MODS = {
    "Steel Meridian": {
        "rubble heap","path of statues","tectonic fracture","ore gaze","titanic rumbler",
        "recrystalize","fireball frenzy","immolated radiance","healing flame","exothermic",
        "surging dash","radiant finish","furious javelin","chromatic blade",
        "biting frost","freeze force","ice wave impedance","chilling globe","icy avalanche",
        "dread ward","blood forge","blending talons",
        "gourmand","hearty nourishment","catapult","gastro",
        "accumulating whipclaw","venari bodyguard","pilfering strangledome",
        "wrath of ukko",
        "ballistic bullseye","muzzle flash","staggering shield","mesa's waltz",
        "pyroclastic flow","reaping chakram","safeguard","controlled slide","divine retribution",
        "abundant mutation","teeming virulence","larva burst","parasitic vitality","insatiable",
        "neutron star","antimatter absorb","escape velocity","molecular fission",
        "smite infusion","hallowed eruption","phoenix renewal","hallowed reckoning",
        "wrecking wall",
        "ironclad charge","iron shrapnel","piercing roar","reinforcing stomp",
        "revealing spores","venom dose","regenerative molt","contagion cloud",
        "prey of dynar","ulfrun's endurance",
        "vampiric grasp","the relentless lost",
    },
    "Red Veil": {
        "seeking shuriken","smoke shadow","fatal teleport","rising storm",
        "rubble heap","path of statues","tectonic fracture","ore gaze","titanic rumbler",
        "recrystalize","spectral spirit",
        "fireball frenzy","immolated radiance","healing flame","exothermic",
        "warrior's rest",
        "dread ward","blood forge","blending talons",
        "gourmand","hearty nourishment","catapult","gastro",
        "tribunal","warding thurible","lasting covenant",
        "accumulating whipclaw","venari bodyguard","pilfering strangledome",
        "valence formation","swift bite",
        "savior decoy","hushed invisibility","safeguard switch","irradiating disarm","damage decoy",
        "ballistic bullseye","muzzle flash","staggering shield","mesa's waltz",
        "soul survivor","creeping terrify","despoil","shield of shadows",
        "revealing spores","venom dose","regenerative molt","contagion cloud",
        "spellbound harvest","beguiling lantern","razorwing blitz","ironclad flight",
        "shock trooper","shocking speed","transistor shield","capacitance",
        "prey of dynar","ulfrun's endurance",
        "target fixation","airburst rounds","jet stream","funnel clouds","anchored glide",
    },
    "Arbiters of Hexis": {
        "seeking shuriken","smoke shadow","fatal teleport","rising storm",
        "elusive retribution","endless lullaby","reactive storm",
        "duality","calm & frenzy","peaceful provocation","energy transfer",
        "surging dash","radiant finish","furious javelin","chromatic blade",
        "warrior's rest",
        "shattered storm","mending splinters","spectrosiphon",
        "mach crash","thermal transfer",
        "coil recharge","cathode current",
        "tribunal","warding thurible","lasting covenant",
        "elemental sandstorm","negation swarm","desiccation's curse",
        "rift haven","rift torrent","cataclysmic continuum",
        "savior decoy","hushed invisibility","safeguard switch","irradiating disarm","damage decoy",
        "hall of malevolence","explosive legerdemain","total eclipse",
        "mind freak","pacifying bolts","chaos sphere","assimilate",
        "repair dispensary","temporal erosion","temporal artillery",
        "axios javelineers","intrepid stand",
        "shock trooper","shocking speed","transistor shield","capacitance",
        "celestial stomp","enveloping cloud","primal rage",
    },
    "New Loka": {
        "elusive retribution","endless lullaby","reactive storm",
        "duality","calm & frenzy","peaceful provocation","energy transfer",
        "shattered storm","mending splinters","spectrosiphon",
        "viral tempest","tidal impunity","rousing plunder","pilfering swarm",
        "wrath of ukko",
        "valence formation","swift bite",
        "greedy pull","magnetized discharge","counter pulse","fracturing crush",
        "mind freak","pacifying bolts","chaos sphere","assimilate",
        "smite infusion","hallowed eruption","phoenix renewal","hallowed reckoning",
        "partitioned mallet","conductor",
        "axios javelineers","intrepid stand",
        "spellbound harvest","beguiling lantern","razorwing blitz","ironclad flight",
        "pool of life","vampire leech","abating link","champion's blessing",
        "swing line","eternal war","prolonged paralysis","enraged","hysterical assault",
        "fused reservoir","critical surge",
        "celestial stomp","enveloping cloud","primal rage",
        "merulina guardian","loyal merulina","surging blades",
        "target fixation","airburst rounds","jet stream","funnel clouds","anchored glide",
    },
    "Cephalon Suda": {
        "sonic fracture","resonance","savage silence","resonating quake",
        "afterburn","everlasting ward","guardian armor","vexing retaliation","guided effigy",
        "biting frost","freeze force","ice wave impedance","chilling globe","icy avalanche",
        "balefire surge","blazing pillage","aegis gale",
        "viral tempest","tidal impunity","rousing plunder","pilfering swarm",
        "empowered quiver","piercing navigator","infiltrate","concentrated arrow",
        "rift haven","rift torrent","cataclysmic continuum",
        "hall of malevolence","explosive legerdemain","total eclipse",
        "pyroclastic flow","reaping chakram","safeguard","controlled slide","divine retribution",
        "neutron star","antimatter absorb","escape velocity","molecular fission",
        "partitioned mallet","conductor",
        "wrecking wall",
        "thrall pact","mesmer shield","blinding reave",
        "shadow haze","dark propagation",
        "tesla bank","photon repeater","repelling bastille",
        "fused reservoir","critical surge",
        "vampiric grasp","the relentless lost",
        "merulina guardian","loyal merulina","surging blades",
    },
    "The Perrin Sequence": {
        "sonic fracture","resonance","savage silence","resonating quake",
        "afterburn","everlasting ward","guardian armor","vexing retaliation","guided effigy",
        "spectral spirit",
        "mach crash","thermal transfer",
        "coil recharge","cathode current",
        "balefire surge","blazing pillage","aegis gale",
        "elemental sandstorm","negation swarm","desiccation's curse",
        "empowered quiver","piercing navigator","infiltrate","concentrated arrow",
        "greedy pull","magnetized discharge","counter pulse","fracturing crush",
        "soul survivor","creeping terrify","despoil","shield of shadows",
        "abundant mutation","teeming virulence","larva burst","parasitic vitality","insatiable",
        "repair dispensary","temporal erosion","temporal artillery",
        "thrall pact","mesmer shield","blinding reave",
        "ironclad charge","iron shrapnel","piercing roar","reinforcing stomp",
        "shadow haze","dark propagation",
        "pool of life","vampire leech","abating link","champion's blessing",
        "swing line","eternal war","prolonged paralysis","enraged","hysterical assault",
        "tesla bank","photon repeater","repelling bastille",
    },
}

def _has(tags, *keys):
    """True se almeno uno dei keys è nei tags (case-insensitive)."""
    tl = [t.lower() for t in tags]
    return any(k in tl for k in keys)

def _name_has(name, *subs):
    """True se almeno una delle subs è nel nome (case-insensitive)."""
    nl = name.lower()
    return any(s in nl for s in subs)

# ── Prime type lookup ──────────────────────────────────────────
# Weapon parts (tag "component"+"weapon"+"prime") mancano del tag
# primary/secondary/melee. Il tipo si ricava per nome usando i set
# come riferimento. Costruito a runtime una sola volta.
def _build_prime_type_map(item_meta):
    """Ritorna {name_prefix_lower: type_str} dai set prime."""
    m = {}
    for slug, meta in item_meta.items():
        tags = meta.get("tags", [])
        if "prime" in tags and "set" in tags:
            name = meta["name"].lower().replace(" set", "").strip()
            for t in ("primary", "secondary", "melee", "warframe", "sentinel"):
                if t in tags:
                    m[name] = t
                    break
    return m

# Viene popolato in App._finish_init dopo load_cache
_PRIME_TYPE_MAP: dict = {}

def _prime_type(name):
    """Ritorna il tipo (primary/secondary/melee/warframe/sentinel) di un
    item prime cercando per prefisso nel _PRIME_TYPE_MAP."""
    nl = name.lower()
    words = nl.split()
    for i in range(len(words), 1, -1):
        key = " ".join(words[:i])
        if key in _PRIME_TYPE_MAP:
            return _PRIME_TYPE_MAP[key]
    return None

def _build_categories():
    cats = []

    def _prime(n, t): return _name_has(n, " prime") or _has(t, "prime")
    def _mod(n, t):   return _has(t, "mod")

    # ── Prime ──────────────────────────────────────────────────
    # Tag reali API:
    #   Set:        [set, prime, warframe|primary|secondary|melee|sentinel]
    #   Main BP:    [blueprint, prime, warframe|primary|secondary|melee|sentinel]
    #   WF Parts:   [component, prime, warframe, blueprint]
    #   Wpn Parts:  [component, weapon, prime]  ← NO tipo-tag, serve _prime_type()
    #   Companions: solo set + blueprint, niente parti
    def _prime_wtype(n, t, wtype):
        """Matcha item prime di un dato tipo, esclusi i set (vanno in Prime->Sets)."""
        if not _prime(n, t): return False
        if _has(t, "set"): return False                  # sets → solo in Prime->Sets
        if _has(t, wtype): return True                   # main-bp / WF-parts / sentinel-bp
        if _has(t, "component"):                         # weapon/sentinel parts (no tipo-tag)
            return _prime_type(n) == wtype
        return False

    cats += [
        (("Prime", "All Prime"),   lambda n,t: _prime(n,t)),
        (("Prime", "Warframes"),   lambda n,t: _prime_wtype(n,t,"warframe")),
        (("Prime", "Primary"),     lambda n,t: _prime_wtype(n,t,"primary")),
        (("Prime", "Secondary"),   lambda n,t: _prime_wtype(n,t,"secondary")),
        (("Prime", "Melee"),       lambda n,t: _prime_wtype(n,t,"melee")),
        (("Prime", "Companions"),  lambda n,t: _prime_wtype(n,t,"sentinel") or (_prime(n,t) and _has(t,"companion","pet") and not _has(t,"set"))),
        (("Prime", "Sets"),        lambda n,t: _prime(n,t) and _has(t,"set")),
    ]

    # ── Mods ───────────────────────────────────────────────────
    # Escludi prime, pvp (Conclave), e augment syndicate (ora in Syndicate)
    def _synd_augment(n, t):
        nl = n.lower()
        return any(nl in mods for mods in _SYND_MODS.values())

    def _base_m(n, t):
        return _mod(n,t) and not _prime(n,t) and not _has(t,"pvp")

    def _general_m(n, t):
        return _base_m(n,t) and not _synd_augment(n,t) and not any([
            _has(t,"aura"),_has(t,"stance"),_has(t,"exilus"),
            _has(t,"augment"),_has(t,"archon"),
            _has(t,"arcane_enhancement","arcane_helmet"),
            _has(t,"riven_mod","veiled_riven")])

    cats += [
        (("Mods", "All Mods"),  _base_m),
        (("Mods", "Aura"),      lambda n,t: _base_m(n,t) and _has(t,"aura")),
        (("Mods", "Stance"),    lambda n,t: _base_m(n,t) and _has(t,"stance")),
        (("Mods", "Exilus"),    lambda n,t: _base_m(n,t) and _has(t,"exilus")),
        (("Mods", "Archon"),    lambda n,t: _base_m(n,t) and _has(t,"archon")),
        (("Mods", "Arcane"),    lambda n,t: _has(t,"arcane_enhancement","arcane_helmet")),
        (("Mods", "Riven"),     lambda n,t: _has(t,"riven_mod","veiled_riven")),
        (("Mods", "Requiem"),   lambda n,t: _has(t,"parazon")),
        (("Mods", "General"),   _general_m),
    ]

    # ── Syndicate Mods (6 classici, mapping esatto per nome) ───
    for synd_name, mod_set in _SYND_MODS.items():
        ms = mod_set   # capture
        cats.append((("Syndicate", synd_name, "Mods"),
                     lambda n, t, _ms=ms: n.lower() in _ms))

    # ── Syndicate Armi (tag "syndicate", non mod) ──────────────
    cats += [
        (("Syndicate", "Armi", "All"),
         lambda n,t: _has(t,"syndicate") and not _mod(n,t)),
        (("Syndicate", "Armi", "Primary"),
         lambda n,t: _has(t,"syndicate") and _has(t,"primary")),
        (("Syndicate", "Armi", "Secondary"),
         lambda n,t: _has(t,"syndicate") and _has(t,"secondary")),
        (("Syndicate", "Armi", "Melee"),
         lambda n,t: _has(t,"syndicate") and _has(t,"melee")),
    ]

    # ── Höllvania 1999 ─────────────────────────────────────────
    _ANTIVIRUS = {"anti-v","byteryte","computer cop","drive-duster",
                  "keep-clean","soft safe","trojan tracker","worm away"}
    _POTENCY   = {"immuno shield","instant secure","quick correct",
                  "threat blocker","turbo protect"}
    _H1999_ALL = _ANTIVIRUS | _POTENCY

    cats += [
        (("Hollvania 1999", "All"),       lambda n,t: n.lower() in _H1999_ALL),
        (("Hollvania 1999", "Antivirus"), lambda n,t: n.lower() in _ANTIVIRUS),
        (("Hollvania 1999", "Potency"),   lambda n,t: n.lower() in _POTENCY),
    ]

    # ── Relics ─────────────────────────────────────────────────
    cats += [
        (("Relics", "All Relics"), lambda n,t: _has(t,"relic")),
        (("Relics", "Lith"),       lambda n,t: _has(t,"relic") and _has(t,"lith")),
        (("Relics", "Meso"),       lambda n,t: _has(t,"relic") and _has(t,"meso")),
        (("Relics", "Neo"),        lambda n,t: _has(t,"relic") and _has(t,"neo")),
        (("Relics", "Axi"),        lambda n,t: _has(t,"relic") and _has(t,"axi")),
        (("Relics", "Requiem"),    lambda n,t: _has(t,"relic") and _has(t,"requiem")),
    ]

    # ── Crafting ───────────────────────────────────────────────
    cats += [
        (("Crafting", "Blueprints"),   lambda n,t: _has(t,"blueprint") and not _has(t,"relic")),
        (("Crafting", "Focus & Lens"), lambda n,t: _has(t,"focus","lens")),
        (("Crafting", "Forma & Misc"), lambda n,t: _name_has(
            n,"forma","orokin catalyst","orokin reactor","exilus adapter")),
    ]

    # ── Cosmetics ──────────────────────────────────────────────
    cats += [
        (("Cosmetics", "Captura"),  lambda n,t: _has(t,"scene")),
        (("Cosmetics", "Skins"),    lambda n,t: _has(t,"skin")),
        (("Cosmetics", "Emote"),    lambda n,t: _has(t,"emote")),
        (("Cosmetics", "Misc"),     lambda n,t: _has(t,"misc") and not _has(t,"relic")),
    ]

    return cats

CATEGORIES = _build_categories()






def _cat_match(name, tags, fn):
    try:    return fn(name, tags)
    except: return False


# ════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════
# API
# ════════════════════════════════════════════════════════════════

def load_config():
    """Carica config.json. Ritorna il dict completo {auth, launches, settings}."""
    if not os.path.exists(CONFIG_JSON):
        raise FileNotFoundError(
            f"'{CONFIG_JSON}' not found — create it with auth.jwt and auth.cf_clearance")
    with open(CONFIG_JSON, encoding="utf-8") as f:
        cfg = json.load(f)
    auth = cfg.get("auth", {})
    miss = [k for k in ("jwt", "cf_clearance") if not auth.get(k)]
    if miss: raise ValueError(f"Missing in config.json[auth]: {', '.join(miss)}")
    return cfg

def _cfg_settings(cfg):
    """Ritorna settings con fallback ai default."""
    s = _DEF_SETTINGS.copy()
    s.update(cfg.get("settings", {}))
    return s

def save_launches(n):
    """Aggiorna solo il campo launches in config.json."""
    with open(CONFIG_JSON, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["launches"] = n
    with open(CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def make_session(cfg):
    auth = cfg["auth"]
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json",
                       "platform": "pc", "language": "en",
                       "Authorization": f"Bearer {auth['jwt']}"})
    s.cookies.set("JWT",          auth["jwt"],          domain="warframe.market")
    s.cookies.set("cf_clearance", auth["cf_clearance"], domain="warframe.market")
    return s

def api_get(sess, path, timeout=15):
    r = sess.get(f"{API}/{path}", timeout=timeout)
    if r.status_code == 401: raise PermissionError("JWT expired")
    if r.status_code == 403: raise PermissionError("CF_CLEARANCE expired")
    r.raise_for_status()
    return r.json().get("data", {})

def fetch_username(sess):
    try:
        d = api_get(sess, "me", timeout=8)
        return d.get("ingameName") or d.get("ingame_name") or d.get("name")
    except Exception: return None

def fetch_item_cache(sess):
    items = api_get(sess, "items")
    lookup, names, meta = {}, [], {}
    for item in items:
        i18n = item.get("i18n",{}).get("en",{})
        name = i18n.get("name","") or item.get("name","")
        slug = item.get("slug","")
        if not (name and slug): continue
        lookup[name.lower().strip()] = slug
        names.append(name)
        meta[slug] = {"name": name, "tags": item.get("tags",[]),
                      "desc": i18n.get("description",""),
                      "icon": i18n.get("icon","")}
    return lookup, names, meta

def load_cache(sess, launch, refresh_every, log=None):
    """
    Carica app_cache.json che contiene lookup, names, meta e desc.
    Struttura app_cache:
      {
        "cached_at": "YYYY-MM-DD",
        "lookup":    {name_lower: slug},
        "names":     [name, ...],
        "items":     {slug: {name, tags, icon, desc, desc_fetched_at}}
      }
    """
    def _l(m):
        if log: log(m)
    need = not os.path.exists(APP_CACHE) or launch % refresh_every == 0
    if need:
        _l("Downloading item list..." if not os.path.exists(APP_CACHE)
           else f"Startup #{launch} — refreshing cache...")
        lu, names, meta = fetch_item_cache(sess)
        # Preserva desc già scaricate se il file esiste
        existing_items = {}
        if os.path.exists(APP_CACHE):
            try:
                old_data = json.load(open(APP_CACHE, encoding="utf-8"))
                existing_items = old_data.get("items", {})
            except Exception:
                pass
        # Merge: conserva desc e desc_fetched_at dal vecchio cache
        for slug, m in meta.items():
            if slug in existing_items:
                m["desc"]            = existing_items[slug].get("desc", m.get("desc",""))
                m["desc_fetched_at"] = existing_items[slug].get("desc_fetched_at","")
        import datetime
        data = {"cached_at": str(datetime.date.today()),
                "lookup": lu, "names": names, "items": meta}
        with open(APP_CACHE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        _l(f"{len(names)} items cached ✓")
    else:
        with open(APP_CACHE, encoding="utf-8") as f:
            data = json.load(f)
        lu    = data.get("lookup", {})
        names = data.get("names",  list(lu.keys()))
        meta  = data.get("items",  {})
        rem   = refresh_every - launch % refresh_every
        _l(f"Cache loaded ({len(names)} items) · refresh in {rem} startups")
    return lu, names, meta

def fetch_sellers(sess, slug, top=5):
    d = api_get(sess, f"orders/item/{slug}/top")
    return d.get("sell", [])[:top] if isinstance(d, dict) else None


# ── Persistence ───────────────────────────────────────────────────

def next_launch(cfg):
    """Incrementa launches in config.json e lo ritorna."""
    n = cfg.get("launches", 0) + 1
    save_launches(n)
    return n

def load_selected():
    if not os.path.exists(ITEMS_FILE): return set()
    with open(ITEMS_FILE, encoding="utf-8") as f:
        return {l[1:].strip() for l in f
                if l.strip().startswith("*") and l[1:].strip()}

def save_selected(all_names, selected):
    sel   = sorted(n for n in all_names if n in selected)
    unsel = [n for n in all_names if n not in selected]
    with open(ITEMS_FILE, "w", encoding="utf-8") as f:
        f.write("# Warframe Market — Selected Items (* = selected)\n\n")
        f.writelines(f"*{n}\n" for n in sel)
        if sel and unsel: f.write("\n")
        f.writelines(f"{n}\n" for n in unsel)

def load_desc_from_cache(item_meta):
    """
    Estrae le descrizioni da app_cache (item_meta) in un dict
    {name: desc_str} compatibile con self._desc_cache.
    Considera valide solo le desc con desc_fetched_at compilato.
    """
    desc_map = {}
    for slug, m in item_meta.items():
        name = m.get("name","")
        desc = m.get("desc","")
        fetched = m.get("desc_fetched_at","")
        if name and fetched:          # solo se già fetchata
            desc_map[name] = desc
    return desc_map

def save_desc_to_cache(slug, name, desc, item_meta):
    """
    Salva desc e timestamp in item_meta[slug] e riscrive app_cache.json.
    """
    import datetime
    if slug in item_meta:
        item_meta[slug]["desc"]            = desc
        item_meta[slug]["desc_fetched_at"] = str(datetime.date.today())
    try:
        with open(APP_CACHE, encoding="utf-8") as f:
            data = json.load(f)
        data["items"] = item_meta
        with open(APP_CACHE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
# UI primitives
# ════════════════════════════════════════════════════════════════

def lbl(parent, text="", font=None, fg=None, bg=None, **kw):
    return tk.Label(parent, text=text, font=font or F["body"],
                    fg=fg or C["text"], bg=bg or C["bg"], **kw)

def sep(parent, axis="x", color=None, size=1):
    kw = {"bg": color or C["border"]}
    if axis == "x": kw["height"] = size
    else:           kw["width"]  = size
    f = tk.Frame(parent, **kw); f.pack(fill=axis)
    return f

def badge(parent, text, fg, bg):
    f = tk.Frame(parent, bg=bg, padx=5, pady=2)
    tk.Label(f, text=text, font=F["tiny"], fg=fg, bg=bg).pack()
    return f


# ════════════════════════════════════════════════════════════════
# GlowBtn — pure Frame+Label, no Canvas (Python 3.13 safe)
# ════════════════════════════════════════════════════════════════

class GlowBtn(tk.Frame):
    THEMES = {
        "cyan":   (C["accent"],   "#041828", "#082a44"),
        "red":    (C["red"],      "#1c0508", "#2e080d"),
        "gold":   (C["gold_hi"],  "#1c1204", "#2e1e06"),
        "orange": (C["orange"],   "#1c0e00", "#2e1a00"),
    }

    def __init__(self, parent, text, cmd=None, w=200, h=32,
                 theme="cyan", bg=C["bg2"]):
        self._col, self._fill_n, self._fill_h = self.THEMES.get(
            theme, self.THEMES["cyan"])
        self._text = text
        self._cmd  = cmd
        self._on   = True
        self._bg   = bg

        super().__init__(parent, bg=self._col,
                         width=int(w), height=int(h), padx=1, pady=1)
        self.pack_propagate(False)

        self._inner = tk.Frame(self, bg=self._fill_n)
        self._inner.pack(fill="both", expand=True)

        self._top = tk.Frame(self._inner, bg=self._col, height=1)
        self._top.pack(fill="x", side="top")

        self._lbl = tk.Label(self._inner, text=self._text,
                             font=F["body"], fg=self._col,
                             bg=self._fill_n, cursor="hand2")
        self._lbl.pack(fill="both", expand=True)

        for w_ in (self, self._inner, self._top, self._lbl):
            w_.bind("<Enter>",    self._on_enter)
            w_.bind("<Leave>",    self._on_leave)
            w_.bind("<Button-1>", self._on_click)

    def _refresh(self, hover=False):
        if not self._on:
            col  = C["dim"]
            fill = self._bg
        else:
            col  = self._col
            fill = self._fill_h if hover else self._fill_n
        self.configure(bg=col)
        self._inner.configure(bg=fill)
        self._top.configure(bg=col)
        self._lbl.configure(fg=C["text"] if (hover and self._on) else col,
                            bg=fill)

    def _on_enter(self, _=None): self._refresh(hover=True)
    def _on_leave(self, _=None): self._refresh(hover=False)
    def _on_click(self, _=None):
        if self._cmd and self._on: self._cmd()

    def set_enabled(self, v):
        self._on = v
        self._refresh()


# ════════════════════════════════════════════════════════════════
# Spinner
# ════════════════════════════════════════════════════════════════

class Spinner(tk.Label):
    def __init__(self, parent, size=9, bg=C["bg2"]):
        super().__init__(parent, text="●", font=("Consolas", size),
                         fg=C["dim"], bg=bg)
        self._on = False

    def start(self): self._on = True;  self._spin()
    def stop(self):  self._on = False; self.configure(fg=C["dim"])

    def _spin(self):
        if not self._on: return
        self.configure(fg=C["accent"] if self.cget("fg")==C["dim"] else C["dim"])
        self.after(400, self._spin)


# ════════════════════════════════════════════════════════════════
# Overlay
# ════════════════════════════════════════════════════════════════

class Overlay(tk.Frame):
    SPIN = list("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
    BAR  = 28

    def __init__(self, parent):
        super().__init__(parent, bg=C["bg"], cursor="watch")
        self._i = 0; self._running = False; self._build()

    def _build(self):
        tk.Frame(self, bg=C["bg"]).pack(expand=True, fill="both")
        mid = tk.Frame(self, bg=C["bg"]); mid.pack()
        lbl(mid, "◈", F["spin"],   C["gold"],  C["bg"]).pack()
        lbl(mid, "WARFRAME  MARKET", ("Segoe UI",22,"bold"), C["text"], C["bg"]
            ).pack(pady=(2,0))
        lbl(mid, f"Price Checker  ·  v{VERSION}  ·  API v2",
            F["small"], C["muted"], C["bg"]).pack(pady=(4,32))
        row = tk.Frame(mid, bg=C["bg"]); row.pack()
        self._spin_lbl = lbl(row, self.SPIN[0], ("Consolas",14), C["accent"], C["bg"])
        self._spin_lbl.pack(side="left", padx=(0,12))
        self._step_lbl = lbl(row, "Initializing...", F["body"], C["mid"], C["bg"])
        self._step_lbl.pack(side="left")
        self._bar_lbl = lbl(mid, self._bar(0), ("Consolas",11), C["gold"], C["bg"])
        self._bar_lbl.pack(pady=(20,4))
        self._pct_lbl = lbl(mid, "", F["small"], C["dim"], C["bg"])
        self._pct_lbl.pack()
        tk.Frame(self, bg=C["bg"]).pack(expand=True, fill="both")

    def _bar(self, n):
        n = max(0, min(self.BAR, n))
        return f"[{'█'*n}{'░'*(self.BAR-n)}]"

    def step(self, text, prog=None, pct=""):
        self._step_lbl.configure(text=text)
        if prog is not None:
            self._bar_lbl.configure(text=self._bar(prog))
            self._pct_lbl.configure(text=pct)

    def start(self): self._running = True;  self._tick()
    def stop(self):  self._running = False

    def _tick(self):
        if not self._running: return
        self._i = (self._i+1) % len(self.SPIN)
        self._spin_lbl.configure(text=self.SPIN[self._i])
        self.after(80, self._tick)


# ════════════════════════════════════════════════════════════════
# App
# ════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WFM Price Checker")
        self.configure(bg=C["bg"])
        self.minsize(1280, 680)

        self.session       = None
        self.lookup        = {}
        self.all_names     = []
        self.item_meta     = {}
        self.results       = {}
        self._fetch_ts     = {}   # name -> time.time() of last successful fetch
        self._save_job     = None  # debounced save_selected job   # name -> time.time() of last successful fetch
        self.running       = False
        self._cancel_flag  = False
        self._settings    = _DEF_SETTINGS.copy()
        self.view_name     = None
        self._t0           = 0.0
        self._img_cache    = {}
        self._zoom_cache   = {}   # slug -> PhotoImage at IMG_ZOOM size
        self._zoom_popup   = None # active Toplevel or None
        self.selected      = set()
        self._desc_cache   = {}  # populated after item_meta is loaded
        self._wiki_pending = set()
        self._wiki_url     = ""
        self._market_url   = ""
        # current category filter: None = all, "__sel__" = selected only,
        # or a callable (name, tags) -> bool
        self._active_cat   = None

        self._style()
        self._build()
        self.after(100, self._start_init)

    # ── Style ─────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=C["bg"], foreground=C["text"],
                     fieldbackground=C["bg2"], bordercolor=C["border"],
                     troughcolor=C["bg2"], font=F["body"])
        for name in ("Cat", "Left", "Right"):
            s.configure(f"{name}.Treeview",
                        background=C["bg2"], foreground=C["text"],
                        fieldbackground=C["bg2"], rowheight=22, borderwidth=0)
            s.configure(f"{name}.Treeview.Heading",
                        background=C["bg3"], foreground=C["gold"],
                        relief="flat", font=F["small"], padding=(4,3))
            s.map(f"{name}.Treeview",
                  background=[("selected", C["bg5"])],
                  foreground=[("selected", C["accent"])])
        s.configure("Right.Treeview", rowheight=26)
        s.configure("TScrollbar", background=C["bg3"], troughcolor=C["bg2"],
                    arrowcolor=C["dim"], borderwidth=0, width=6)
        s.map("TScrollbar", background=[("active", C["bg5"])])

    # ════════════════════════════════════════════════════════════
    # Layout
    # ════════════════════════════════════════════════════════════

    def _build(self):
        self._build_header()
        sep(self, color=C["border2"])
        self._build_body()
        sep(self, color=C["border"])
        self._build_statusbar()

    # ── Header ────────────────────────────────────────────────────
    def _build_header(self):
        h = tk.Frame(self, bg=C["bg2"]); h.pack(fill="x")
        tk.Frame(h, bg=C["gold"], height=2).pack(fill="x")
        inner = tk.Frame(h, bg=C["bg2"]); inner.pack(fill="x", padx=18, pady=10)

        logo = tk.Frame(inner, bg=C["bg2"]); logo.pack(side="left")
        lbl(logo, "◈", ("Consolas",26), C["gold"], C["bg2"]).pack(
            side="left", padx=(0,12))
        tf = tk.Frame(logo, bg=C["bg2"]); tf.pack(side="left")
        lbl(tf, "WARFRAME MARKET", ("Segoe UI",15,"bold"), C["text"], C["bg2"]
            ).pack(anchor="w")
        lbl(tf, f"Price Checker  ·  API v2  ·  v{VERSION}",
            F["small"], C["muted"], C["bg2"]).pack(anchor="w")

        info = tk.Frame(inner, bg=C["bg2"]); info.pack(side="right")
        ur = tk.Frame(info, bg=C["bg2"]); ur.pack(anchor="e", pady=(0,3))
        lbl(ur, "USER  ", F["small"], C["muted"], C["bg2"]).pack(side="left")
        self.lbl_user = lbl(ur, "...", ("Segoe UI",9,"bold"), C["accent"], C["bg2"])
        self.lbl_user.pack(side="left")
        self.lbl_cache  = lbl(info, "", F["small"], C["muted"], C["bg2"])
        self.lbl_cache.pack(anchor="e")
        self.lbl_launch = lbl(info, "", F["small"], C["muted"], C["bg2"])
        self.lbl_launch.pack(anchor="e")

    # ── Body ──────────────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self, bg=C["bg"]); body.pack(fill="both", expand=True)
        self._build_cat_panel(body)
        sep(body, "y", color=C["border2"])
        self._build_left(body)
        sep(body, "y", color=C["border2"])
        self._build_right(body)

    # ── Category panel ────────────────────────────────────────────
    def _build_cat_panel(self, parent):
        cat_frame = tk.Frame(parent, bg=C["bg2"], width=196)
        cat_frame.pack(side="left", fill="y")
        cat_frame.pack_propagate(False)

        # Header
        ph = tk.Frame(cat_frame, bg=C["bg3"]); ph.pack(fill="x")
        tk.Frame(ph, bg=C["gold2"], height=1).pack(fill="x")
        lbl(ph, "  CATEGORIES", F["small"], C["gold"], C["bg3"]).pack(
            anchor="w", padx=4, pady=6)

        # Treeview
        tf = tk.Frame(cat_frame, bg=C["bg2"]); tf.pack(fill="both", expand=True)
        self.ctree = ttk.Treeview(tf, style="Cat.Treeview",
                                  show="tree", selectmode="browse")
        self.ctree.column("#0", width=188, stretch=True)
        csb = ttk.Scrollbar(tf, orient="vertical", command=self.ctree.yview)
        self.ctree.configure(yscrollcommand=csb.set)
        csb.pack(side="right", fill="y")
        self.ctree.pack(side="left", fill="both", expand=True)

        self.ctree.tag_configure("special", foreground=C["accent"],
                                 font=("Segoe UI", 8, "bold"))
        self.ctree.tag_configure("group",   foreground=C["gold"],
                                 font=("Segoe UI", 8, "bold"))
        self.ctree.tag_configure("subgroup",foreground=C["gold_hi"],
                                 font=F["tiny"])
        self.ctree.tag_configure("leaf",    foreground=C["muted"],
                                 font=F["tiny"])

        # Special entries
        self._iid_all = self.ctree.insert("","end", text="★  All Items",
                                           tags=("special",))
        self._iid_sel = self.ctree.insert("","end", text="☑  Selected",
                                           tags=("special",))

        # Build tree from CATEGORIES
        # group_nodes: key -> iid  (key = "Group" or "Group::Sub")
        group_nodes: dict = {}
        self._iid_fn: dict = {}   # iid -> filter_fn

        for path, fn in CATEGORIES:
            if len(path) == 1:
                iid = self.ctree.insert("","end", text=path[0], tags=("leaf",))
                self._iid_fn[iid] = fn

            elif len(path) == 2:
                g = path[0]
                if g not in group_nodes:
                    group_nodes[g] = self.ctree.insert(
                        "", "end", text=g, tags=("group",))
                iid = self.ctree.insert(
                    group_nodes[g], "end", text=path[1], tags=("leaf",))
                self._iid_fn[iid] = fn

            elif len(path) == 3:
                g, sub = path[0], path[1]
                gk = f"{g}::{sub}"
                if g not in group_nodes:
                    group_nodes[g] = self.ctree.insert(
                        "", "end", text=g, tags=("group",))
                if gk not in group_nodes:
                    group_nodes[gk] = self.ctree.insert(
                        group_nodes[g], "end", text=sub, tags=("subgroup",))
                iid = self.ctree.insert(
                    group_nodes[gk], "end", text=path[2], tags=("leaf",))
                self._iid_fn[iid] = fn

        self.ctree.bind("<<TreeviewSelect>>", self._on_cat_select)

    # ── Item list panel (middle) ──────────────────────────────────
    def _build_left(self, parent):
        left = tk.Frame(parent, bg=C["bg2"], width=258)
        left.pack(side="left", fill="y"); left.pack_propagate(False)

        ph = tk.Frame(left, bg=C["bg3"]); ph.pack(fill="x")
        tk.Frame(ph, bg=C["gold2"], height=1).pack(fill="x")
        phi = tk.Frame(ph, bg=C["bg3"]); phi.pack(fill="x", padx=10, pady=6)
        lbl(phi, "ITEM LIST", F["small"], C["gold"], C["bg3"]).pack(side="left")
        self.lbl_count = lbl(phi, "", F["tiny"], C["muted"], C["bg3"])
        self.lbl_count.pack(side="right")

        # Search bar
        sf = tk.Frame(left, bg=C["bg2"], padx=8, pady=5); sf.pack(fill="x")
        si = tk.Frame(sf, bg=C["bg3"], highlightthickness=1,
                      highlightbackground=C["border2"]); si.pack(fill="x")
        lbl(si, " ⌕", ("Segoe UI",11), C["muted"], C["bg3"]).pack(side="left")
        self.sv = tk.StringVar()
        self._search_job = None
        self.sv.trace_add("write", self._on_search_change)
        tk.Entry(si, textvariable=self.sv, bg=C["bg3"], fg=C["text"],
                 insertbackground=C["accent"], relief="flat", bd=0,
                 font=F["body"], highlightthickness=0
                 ).pack(side="left", fill="x", expand=True, pady=4, padx=4)
        clr = lbl(si, "✕", F["small"], C["muted"], C["bg3"],
                  cursor="hand2", padx=5)
        clr.pack(side="right")
        clr.bind("<Button-1>", lambda e: self.sv.set(""))

        lbl(left, "  ☑ = toggle  ·  name = view sellers",
            F["tiny"], C["dim"], C["bg2"]).pack(anchor="w", padx=4, pady=(0,2))
        sep(left, color=C["border2"])

        tf = tk.Frame(left, bg=C["bg2"]); tf.pack(fill="both", expand=True)
        self.ltree = ttk.Treeview(tf, style="Left.Treeview",
                                  columns=("chk","name"), show="headings",
                                  selectmode="browse")
        self.ltree.heading("chk",  text="")
        self.ltree.heading("name", text="NAME")
        self.ltree.column("chk",  width=26, stretch=False, anchor="center")
        self.ltree.column("name", width=210, stretch=True,  anchor="w")
        lsb = ttk.Scrollbar(tf, orient="vertical", command=self.ltree.yview)
        self.ltree.configure(yscrollcommand=lsb.set)
        lsb.pack(side="right", fill="y")
        self.ltree.pack(side="left", fill="both", expand=True)

        self.ltree.tag_configure("sel",   background=C["bg4"], foreground=C["text"])
        self.ltree.tag_configure("unsel", background=C["bg2"], foreground=C["dim"])
        self.ltree.tag_configure("ok",    foreground=C["green"])
        self.ltree.tag_configure("warn",  foreground=C["orange"])
        self.ltree.tag_configure("err",   foreground=C["red"])
        self.ltree.bind("<Button-1>", self._ltree_click)

        # Buttons
        sep(left, color=C["border2"])
        bf = tk.Frame(left, bg=C["bg2"], pady=8); bf.pack(fill="x")

        self.fetch_btn = GlowBtn(bf, "⟳  REFRESH SELECTED",
                                 cmd=self._start_fetch, w=214, h=28,
                                 theme="cyan", bg=C["bg2"])
        self.fetch_btn.pack(padx=20, pady=(0,4))

        self.fetchall_btn = GlowBtn(bf, "⟳  FETCH ALL  (5s delay)",
                                    cmd=self._start_fetch_all, w=214, h=24,
                                    theme="gold", bg=C["bg2"])
        self.fetchall_btn.pack(padx=20, pady=(0,4))

        self.cancel_btn = GlowBtn(bf, "⬛  CANCEL FETCH",
                                  cmd=self._cancel_fetch, w=214, h=24,
                                  theme="orange", bg=C["bg2"])
        self.cancel_btn.pack(padx=20, pady=(0,4))
        self.cancel_btn.set_enabled(False)

        self.clear_btn = GlowBtn(bf, "✕  CLEAR SELECTION",
                                 cmd=self._clear_selection, w=214, h=24,
                                 theme="red", bg=C["bg2"])
        self.clear_btn.pack(padx=20)

    # ── Right panel ───────────────────────────────────────────────
    def _build_right(self, parent):
        right = tk.Frame(parent, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)

        info = tk.Frame(right, bg=C["bg3"]); info.pack(fill="x")
        tk.Frame(info, bg=C["gold"], height=1).pack(fill="x", side="top")
        inner = tk.Frame(info, bg=C["bg3"]); inner.pack(fill="x", padx=14, pady=10)

        img_col = tk.Frame(inner, bg=C["bg3"]); img_col.pack(side="left", padx=(0,14))
        img_border = tk.Frame(img_col, bg=C["border2"], padx=1, pady=1)
        img_border.pack()
        img_bg = tk.Frame(img_border, bg=C["bg2"],
                          width=IMG_SIZE[0], height=IMG_SIZE[1])
        img_bg.pack(); img_bg.pack_propagate(False)
        self.img_lbl = tk.Label(img_bg, bg=C["bg2"],
                                text="◈", font=F["mono"], fg=C["border2"])
        self.img_lbl.pack(fill="both", expand=True)
        self.img_lbl.bind("<Enter>", self._img_hover_enter)
        self.img_lbl.bind("<Leave>", self._img_hover_leave)
        self.img_lbl.bind("<Motion>", self._img_hover_move)

        txt = tk.Frame(inner, bg=C["bg3"])
        txt.pack(side="left", fill="both", expand=True)
        self.lbl_title = lbl(txt, "← select an item to view details",
                             F["h1"], C["dim"], C["bg3"])
        self.lbl_title.pack(anchor="w")
        self.tags_frame = tk.Frame(txt, bg=C["bg3"])
        self.tags_frame.pack(anchor="w", pady=(4,0))
        self.lbl_sub = lbl(txt, "", F["small"], C["mid"], C["bg3"])
        self.lbl_sub.pack(anchor="w", pady=(3,0))
        self.lbl_desc = tk.Label(txt, text="", font=F["body"], fg=C["muted"],
                                 bg=C["bg3"], wraplength=560,
                                 justify="left", anchor="nw")
        self.lbl_desc.pack(anchor="w", fill="x", pady=(5,0))

        btn_row = tk.Frame(txt, bg=C["bg3"])
        btn_row.pack(anchor="w", pady=(8,2))
        self.wiki_btn   = GlowBtn(btn_row, "  ⬡  OPEN WIKI  ",
                                  cmd=self._open_wiki, w=138, h=26,
                                  theme="gold", bg=C["bg3"])
        self.market_btn = GlowBtn(btn_row, "  ◈  OPEN MARKET  ",
                                  cmd=self._open_market, w=150, h=26,
                                  theme="cyan", bg=C["bg3"])
        self.wiki_btn.pack(side="left", padx=(0,6))
        self.market_btn.pack(side="left")

        tk.Frame(right, bg=C["gold2"], height=1).pack(fill="x")

        tf = tk.Frame(right, bg=C["bg"], padx=12, pady=10)
        tf.pack(fill="both", expand=True)
        cols = ("rank","seller","platinum","qty","status")
        self.tree = ttk.Treeview(tf, style="Right.Treeview",
                                 columns=cols, show="headings",
                                 selectmode="browse")
        for col, label, w, anc in [
            ("rank",     " #",       44,  "center"),
            ("seller",   "  SELLER", 280, "w"),
            ("platinum", "PLATINUM", 110, "center"),
            ("qty",      "QTY",       70, "center"),
            ("status",   "STATUS",   150, "center"),
        ]:
            self.tree.heading(col, text=label, anchor=anc)
            self.tree.column(col, width=w, anchor=anc, stretch=(col=="seller"))
        tsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tsb.pack(side="left", fill="y")
        for tag, bg, fg in [
            ("row_a",  C["bg2"],    C["text"]),
            ("row_b",  C["bg3"],    C["text"]),
            ("ingame", C["bg2"],    C["green"]),
            ("online", C["bg2"],    C["accent"]),
            ("offline",C["bg2"],    C["dim"]),
            ("warn",   C["bg3"],    C["orange"]),
            ("err",    C["red_dim"],C["red"]),
            ("info",   C["bg2"],    C["mid"]),
        ]:
            self.tree.tag_configure(tag, background=bg, foreground=fg)

    # ── Statusbar ─────────────────────────────────────────────────
    def _build_statusbar(self):
        sb = tk.Frame(self, bg=C["bg2"]); sb.pack(fill="x")
        si = tk.Frame(sb, bg=C["bg2"]); si.pack(fill="x", padx=14, pady=5)
        self.spinner = Spinner(si, size=9, bg=C["bg2"])
        self.spinner.pack(side="left", padx=(0,7))
        self.lbl_log  = lbl(si, "Initializing...", F["small"], C["muted"], C["bg2"])
        self.lbl_log.pack(side="left", fill="x", expand=True)
        self.lbl_prog = lbl(si, "", F["datasm"], C["mid"], C["bg2"])
        self.lbl_prog.pack(side="right", padx=(0,8))
        # Auto-refresh toggle
        self._autoref_on = False
        self._autoref_job = None
        self.btn_autoref = tk.Label(si, text="⟳ AUTO", font=F["tiny"],
                                    fg=C["dim"], bg=C["bg3"],
                                    padx=6, pady=2, cursor="hand2",
                                    relief="flat")
        self.btn_autoref.pack(side="right", padx=(0,4))
        self.btn_autoref.bind("<Button-1>", self._toggle_autoref)

    # ════════════════════════════════════════════════════════════
    # Category selection
    # ════════════════════════════════════════════════════════════

    def _on_cat_select(self, _=None):
        sel = self.ctree.selection()
        if not sel: return
        iid = sel[0]
        if iid == self._iid_all:
            self._active_cat = None
        elif iid == self._iid_sel:
            self._active_cat = "__sel__"
        elif iid in self._iid_fn:
            self._active_cat = self._iid_fn[iid]
        else:
            return   # group node clicked, do nothing
        self._apply_filter()

    def _passes_cat(self, name):
        if self._active_cat is None:    return True
        if self._active_cat == "__sel__": return name in self.selected
        slug = self.lookup.get(name.lower().strip(), "")
        tags = self.item_meta.get(slug, {}).get("tags", [])
        return _cat_match(name, tags, self._active_cat)

    # ════════════════════════════════════════════════════════════
    # Item list
    # ════════════════════════════════════════════════════════════

    def _populate_ltree(self, names, selected, on_done=None):
        self.selected = set(selected)
        self.ltree.delete(*self.ltree.get_children())
        ordered = (sorted(n for n in names if n in self.selected) +
                   [n for n in names if n not in self.selected])
        total = len(ordered); CHUNK = 300

        def chunk(start):
            end = min(start + CHUNK, total)
            for name in ordered[start:end]:
                issel = name in self.selected
                self.ltree.insert("","end", iid=name,
                                  values=("☑" if issel else "☐", name),
                                  tags=("sel" if issel else "unsel",))
            done = end
            if hasattr(self,"overlay") and self.overlay.winfo_exists():
                self.overlay.step("Populating item list...",
                                  int(done/total*self.overlay.BAR),
                                  f"{done:,} / {total:,}")
            if done < total: self.after(1, lambda: chunk(done))
            else:
                if on_done: on_done()
        chunk(0)

    def _schedule_save(self):
        """Salva items.txt max una volta ogni 2s anche con click rapidi."""
        if self._save_job:
            self.after_cancel(self._save_job)
        self._save_job = self.after(2000,
            lambda: save_selected(self.all_names, self.selected))

    def _on_search_change(self, *_):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(120, self._apply_filter)

    def _apply_filter(self):
        q = self.sv.get().lower().strip()
        self.ltree.delete(*self.ltree.get_children())
        vs, vu = [], []
        for name in self.all_names:
            if q and q not in name.lower():  continue
            if not self._passes_cat(name):   continue
            (vs if name in self.selected else vu).append(name)
        vs.sort()
        for name in vs + vu:
            issel = name in self.selected
            base  = "sel" if issel else "unsel"
            rt    = self._result_tag(name)
            tags  = (base,) + ((rt,) if rt else ())
            self.ltree.insert("","end", iid=name,
                              values=("☑" if issel else "☐", name),
                              tags=tags)
        self.lbl_count.configure(
            text=f"{len(self.selected)} sel  ·  {len(vs)+len(vu)} shown",
            fg=C["accent"] if self.selected else C["muted"])

    def _ltree_click(self, event):
        if self.ltree.identify_region(event.x, event.y) != "cell": return
        col  = self.ltree.identify_column(event.x)
        item = self.ltree.identify_row(event.y)
        if not item: return
        if col == "#1": self._toggle_item(item)
        else:           self.view_name = item; self._show_detail(item)

    def _toggle_item(self, name):
        if not self.ltree.exists(name): return
        if name in self.selected:
            self.selected.discard(name); chk, base = "☐", "unsel"
        else:
            self.selected.add(name);    chk, base = "☑", "sel"
        rt   = self._result_tag(name)
        tags = (base,) + ((rt,) if rt else ())
        self.ltree.item(name, values=(chk, name), tags=tags)
        self._reorder_ltree()
        self.lbl_count.configure(
            text=f"{len(self.selected)} sel  ·  {len(self.ltree.get_children())} shown",
            fg=C["accent"] if self.selected else C["muted"])
        self._schedule_save()

    def _reorder_ltree(self):
        ids   = list(self.ltree.get_children())
        sel   = sorted(i for i in ids if self.ltree.item(i,"values")[0]=="☑")
        unsel = [i for i in ids if self.ltree.item(i,"values")[0]=="☐"]
        for idx, iid in enumerate(sel + unsel):
            self.ltree.move(iid, "", idx)

    def _result_tag(self, name):
        r = self.results.get(name)
        if r is None:                             return None
        if r == "error":                          return "err"
        if r == "notfound" or (isinstance(r,list) and not r): return "warn"
        return "ok"

    def _set_item_tag(self, name, result_tag):
        if not self.ltree.exists(name): return
        cur  = self.ltree.item(name, "tags")
        base = tuple(t for t in cur if t not in ("ok","warn","err"))
        self.ltree.item(name, tags=base + (result_tag,))

    def _clear_selection(self):
        if self.running: return
        self.selected.clear()
        for iid in self.ltree.get_children():
            cur  = self.ltree.item(iid, "tags")
            base = tuple(t for t in cur if t not in ("sel","unsel"))
            self.ltree.item(iid, values=("☐", iid), tags=("unsel",)+base)
        self.lbl_count.configure(
            text=f"0 sel  ·  {len(self.ltree.get_children())} shown",
            fg=C["muted"])
        self._schedule_save()
        self._log("Selection cleared")

    # ════════════════════════════════════════════════════════════
    # Detail panel
    # ════════════════════════════════════════════════════════════

    def _open_wiki(self):
        if self._wiki_url: webbrowser.open(self._wiki_url)

    def _open_market(self):
        if self._market_url: webbrowser.open(self._market_url)

    def _show_detail(self, name):
        self._destroy_zoom_popup()
        self.lbl_title.configure(text=name, fg=C["accent"])
        self.tree.delete(*self.tree.get_children())

        slug = self.lookup.get(name.lower().strip(), "")
        meta = self.item_meta.get(slug, {})

        self._wiki_url   = f"{WIKI}/{name.replace(' ','_')}"
        self._market_url = f"https://warframe.market/items/{slug}" if slug else ""

        for w in self.tags_frame.winfo_children(): w.destroy()
        TAG_C = {
            "mod":       (C["gold"],    C["gold_dim"]),
            "weapon":    (C["accent"],  C["bg4"]),
            "warframe":  (C["green"],   C["green2"]),
            "arcane":    (C["orange"],  C["bg4"]),
            "relic":     (C["muted"],   C["bg3"]),
            "syndicate": (C["gold_hi"], C["gold_dim"]),
            "prime":     (C["gold_hi"], C["gold_dim"]),
        }
        for t in meta.get("tags", [])[:5]:
            fg, bg = TAG_C.get(t, (C["mid"], C["bg3"]))
            badge(self.tags_frame, t.upper(), fg, bg).pack(
                side="left", padx=(0,4))

        if name in self._desc_cache:
            d = self._desc_cache[name]
            self.lbl_desc.configure(
                text=d if d else "No description found on wiki.",
                fg=C["muted"] if d else C["dim"])
        else:
            self.lbl_desc.configure(text="Loading description...", fg=C["dim"])

        self._load_item_image(slug, name)

        # Always fetch desc if missing; always fetch img if not on disk/cache
        need_desc = name not in self._desc_cache and name not in self._wiki_pending
        need_img  = (slug and slug not in self._img_cache
                     and not (IMG_DIR / f"{slug}.png").exists())
        if slug and (need_desc or need_img):
            self._wiki_pending.add(name)
            threading.Thread(target=self._fetch_wiki,
                             args=(name, slug), daemon=True).start()

        data   = self.results.get(name)
        MEDALS = ["◈","◇","△","▷","▽"]
        ST     = {"ingame":"● in-game","online":"● online","offline":"○ offline"}

        if data is None:
            self.lbl_sub.configure(
                text="no data  ·  ☑ select and press ⟳ REFRESH", fg=C["dim"])
            self.tree.insert("","end",
                values=("","  Press ⟳ REFRESH SELECTED to load prices","","",""),
                tags=("info",))
        elif data == "notfound":
            self.lbl_sub.configure(text="item not found in cache", fg=C["orange"])
            self.tree.insert("","end",
                values=("⚠","  Item not found","","",""), tags=("warn",))
        elif data == "error":
            self.lbl_sub.configure(
                text="fetch error — check credentials", fg=C["red"])
            self.tree.insert("","end",
                values=("✕","  API error","","",""), tags=("err",))
        elif not data:
            self.lbl_sub.configure(
                text="no sellers online right now", fg=C["orange"])
            self.tree.insert("","end",
                values=("—","  No online sellers","","",""), tags=("warn",))
        else:
            prices  = [s.get("platinum", 0) for s in data]
            avg_p   = round(sum(prices) / len(prices), 1)
            ts      = self._fetch_ts.get(name)
            if ts:
                delta = int(time.time() - ts)
                if delta < 60:    age = f"{delta}s ago"
                elif delta < 3600: age = f"{delta//60}m ago"
                else:              age = f"{delta//3600}h ago"
                age_str = f"  ·  fetched {age}"
            else:
                age_str = ""
            self.lbl_sub.configure(fg=C["green"],
                text=(f"{len(data)} seller{'s'*(len(data)>1)} online"
                      f"  ·  cheapest  {data[0]['platinum']} ⬡"
                      f"  ·  avg  {avg_p} ⬡"
                      f"{age_str}"))
            for i, s in enumerate(data):
                u  = s.get("user", {})
                st = u.get("status", "offline")
                self.tree.insert("","end",
                    tags=("row_a" if i%2==0 else "row_b",
                          st if st in ST else "offline"),
                    values=(f" {MEDALS[i] if i<5 else i+1}",
                            f"  {u.get('ingameName') or u.get('ingame_name','Unknown')}",
                            f"  {s.get('platinum','?')} ⬡",
                            f"  {s.get('quantity',1)}",
                            f"  {ST.get(st,st)}"))

    # ════════════════════════════════════════════════════════════
    # Wiki fetch
    # ════════════════════════════════════════════════════════════

    def _fetch_wiki(self, name, slug):
        """Fetch description from API and download image if missing."""
        # 1. Get description (also back-fills item_meta[slug]["icon"])
        desc = self._fetch_desc_from_api(slug)
        if name not in self._desc_cache or not self._desc_cache.get(name):
            self._desc_cache[name] = desc or ""
            save_desc_to_cache(slug, name, desc or "", self.item_meta)
        self._wiki_pending.discard(name)

        # 2. Update description label on main thread
        if self.view_name == name:
            self.after(0, lambda d=desc: self.lbl_desc.configure(
                text=d or "No description available.",
                fg=C["muted"] if d else C["dim"]))

        # 3. Download image if still missing after icon was back-filled
        img_path = IMG_DIR / f"{slug}.png"
        if not img_path.exists() and slug not in self._img_cache:
            icon = self.item_meta.get(slug, {}).get("icon", "")
            if icon:
                self._download_image(slug, icon, name)  # blocking, already in thread

    def _fetch_desc_from_api(self, slug):
        """GET /v2/items/<slug> -> description str.
        Also caches icon path into item_meta if missing (fixes stale cache)."""
        if not self.session or not slug:
            return ""
        try:
            r = self.session.get(f"{API}/items/{slug}", timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", {})
                en   = data.get("i18n", {}).get("en", {})
                # Back-fill icon into meta in case cache was built before icon support
                if slug in self.item_meta and not self.item_meta[slug].get("icon"):
                    self.item_meta[slug]["icon"] = en.get("icon", "")
                return en.get("description", "")
        except Exception:
            pass
        return ""

    # ════════════════════════════════════════════════════════════
    # Image
    # ════════════════════════════════════════════════════════════

    def _load_item_image(self, slug, name):
        """Show cached image immediately, then download from CDN if needed."""
        self.img_lbl.configure(image="", text="◈",
                               font=F["mono"], fg=C["border2"])
        self.img_lbl.image = None
        if not PIL_OK or not slug: return
        # 1. Already in memory cache
        if slug in self._img_cache:
            self._set_image(self._img_cache[slug]); return
        # 2. Already on disk
        img_path = IMG_DIR / f"{slug}.png"
        if img_path.exists():
            self._load_from_disk(slug, img_path); return
        # 3. Download from CDN in background thread
        icon = self.item_meta.get(slug, {}).get("icon", "")
        if icon and self.session:
            threading.Thread(target=self._download_image,
                             args=(slug, icon, name), daemon=True).start()

    def _download_image(self, slug, icon_path, name):
        """Download image from warframe.market CDN using plain HTTP (no API headers)."""
        try:
            url = CDN + icon_path
            # Use plain requests — NOT self.session which sends Accept:application/json
            r = requests.get(url, headers={"User-Agent": UA}, timeout=12)
            if r.status_code == 200 and len(r.content) > 500:
                img_path = IMG_DIR / f"{slug}.png"
                img_path.write_bytes(r.content)
                if self.view_name == name:
                    self.after(0, lambda p=img_path: self._load_from_disk(slug, p))
        except Exception:
            pass

    def _load_from_disk(self, slug, img_path):
        if not PIL_OK: return
        try:
            img = Image.open(img_path).convert("RGBA")
            # Normal thumbnail
            thumb = img.copy()
            thumb.thumbnail(IMG_SIZE, Image.LANCZOS)
            canvas = Image.new("RGBA", IMG_SIZE, (0,0,0,0))
            off = ((IMG_SIZE[0]-thumb.width)//2, (IMG_SIZE[1]-thumb.height)//2)
            canvas.paste(thumb, off)
            photo = ImageTk.PhotoImage(canvas)
            self._img_cache[slug] = photo
            # Zoom thumbnail (for hover popup)
            zoomed = img.copy()
            zoomed.thumbnail(IMG_ZOOM, Image.LANCZOS)
            zcanvas = Image.new("RGBA", IMG_ZOOM, (0,0,0,0))
            zoff = ((IMG_ZOOM[0]-zoomed.width)//2, (IMG_ZOOM[1]-zoomed.height)//2)
            zcanvas.paste(zoomed, zoff)
            self._zoom_cache[slug] = ImageTk.PhotoImage(zcanvas)
            self._set_image(photo)
        except Exception: pass

    def _set_image(self, photo):
        self.img_lbl.configure(image=photo, text="", bg=C["bg2"])
        self.img_lbl.image = photo

    # ── Hover zoom popup ──────────────────────────────────────────

    def _current_zoom_photo(self):
        """Return the zoom PhotoImage for the currently viewed item, or None."""
        if not self.view_name: return None
        slug = self.lookup.get(self.view_name.lower().strip(), "")
        return self._zoom_cache.get(slug)

    def _img_hover_enter(self, event):
        photo = self._current_zoom_photo()
        if not photo: return
        self._show_zoom_popup(event.x_root, event.y_root, photo)

    def _img_hover_leave(self, event):
        self._destroy_zoom_popup()

    def _img_hover_move(self, event):
        if self._zoom_popup and self._zoom_popup.winfo_exists():
            self._position_zoom_popup(event.x_root, event.y_root)

    def _show_zoom_popup(self, rx, ry, photo):
        self._destroy_zoom_popup()
        pop = tk.Toplevel(self)
        pop.overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=C["border2"])
        # 1px gold border frame
        border = tk.Frame(pop, bg=C["gold2"], padx=1, pady=1)
        border.pack()
        inner = tk.Frame(border, bg=C["bg2"]); inner.pack()
        lbl_z = tk.Label(inner, image=photo, bg=C["bg2"])
        lbl_z.pack()
        lbl_z.image = photo
        self._zoom_popup = pop
        self._position_zoom_popup(rx, ry)

    def _position_zoom_popup(self, rx, ry):
        if not self._zoom_popup or not self._zoom_popup.winfo_exists(): return
        sw = self.winfo_screenwidth()
        # prefer right of cursor, flip left if near screen edge
        offset_x = 16
        x = rx + offset_x
        if x + IMG_ZOOM[0] + 20 > sw:
            x = rx - IMG_ZOOM[0] - offset_x
        y = ry - IMG_ZOOM[1] // 2
        y = max(0, min(y, self.winfo_screenheight() - IMG_ZOOM[1] - 20))
        self._zoom_popup.geometry(f"+{x}+{y}")

    def _destroy_zoom_popup(self):
        if self._zoom_popup:
            try: self._zoom_popup.destroy()
            except Exception: pass
            self._zoom_popup = None

    # ════════════════════════════════════════════════════════════
    # Init
    # ════════════════════════════════════════════════════════════

    def _start_init(self):
        self.overlay = Overlay(self)
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.lift(); self.overlay.start()
        self._t0 = time.time(); self.spinner.start()
        threading.Thread(target=self._init_worker, daemon=True).start()

    def _init_worker(self):
        def step(text, prog=None, pct=""):
            self.after(0, lambda t=text, p=prog, x=pct:
                       self.overlay.step(t, p, x))
            self._log(text)
        try:
            step("Reading config...", 2)
            cfg      = load_config()
            settings = _cfg_settings(cfg)
            self.session = make_session(cfg)
            self._settings = settings

            launch = next_launch(cfg)
            rem    = settings["refresh_every"] - launch % settings["refresh_every"]
            self.after(0, lambda:
                self.lbl_launch.configure(text=f"startup #{launch}"))
            self.after(0, lambda:
                self.lbl_cache.configure(
                    text=f"cache refresh in {rem} startups"))

            step("Connecting to warframe.market...", 5)
            username = fetch_username(self.session)
            self.after(0, lambda: self.lbl_user.configure(
                text=username or "N/A",
                fg=C["green"] if username else C["orange"]))

            step("Loading item cache...", 8)
            self.lookup, self.all_names, self.item_meta = load_cache(
                self.session, launch, settings["refresh_every"],
                log=lambda m: step(m, 12, "downloading..."))

            # Popola desc_cache da app_cache (solo item già fetchati)
            self._desc_cache = load_desc_from_cache(self.item_meta)

            step(f"Sorting {len(self.all_names):,} items...", 20)
            selected = load_selected()
            ordered  = (sorted(n for n in self.all_names if n in selected) +
                        [n for n in self.all_names if n not in selected])

            step("Building UI...", 23)
            elapsed = time.time() - self._t0
            n_items = len(self.all_names)
            n_sel   = len(selected)

            def after_pop():
                self.lbl_count.configure(
                    text=f"{n_sel} sel  ·  {len(ordered)} shown")
                self._finish_init(elapsed, n_items)

            self.after(0, lambda: self._populate_ltree(
                ordered, selected, on_done=after_pop))

        except Exception as e:
            self._log(f"Error: {e}")
            self.after(0, lambda: (
                self.overlay.step(f"Error: {e}"),
                messagebox.showerror("Init Error", str(e))))
            self.after(0, lambda: self._finish_init(0, 0))

    def _finish_init(self, elapsed, n):
        self.spinner.stop(); self.overlay.stop()
        self.overlay.place_forget(); self.overlay.destroy()
        # Build prime type map from loaded item_meta
        global _PRIME_TYPE_MAP
        _PRIME_TYPE_MAP = _build_prime_type_map(self.item_meta)
        # Select "★ All Items" by default
        self.ctree.selection_set(self._iid_all)
        if n:
            self.lbl_log.configure(
                text=(f" ready  ·  {n:,} items  ·  startup {elapsed:.1f}s"
                      f"  ·  select items and press ⟳"),
                fg=C["green"])

    # ════════════════════════════════════════════════════════════
    # Fetch
    # ════════════════════════════════════════════════════════════

    def _start_fetch(self):
        if self.running or not self.session: return
        if not self.selected:
            self._log("No items selected — ☑ check some items first"); return
        queue = [n for n in self.all_names if n in self.selected]
        self._begin_fetch(queue)

    def _start_fetch_all(self):
        if self.running or not self.session: return
        queue = list(self.all_names)
        n = len(queue)
        eta_min = int(n * FETCH_ALL_DELAY / 60)
        self._log(f"Fetch all: {n:,} items · ETA ~{eta_min} min · cancel anytime")
        self._begin_fetch(queue, delay_override=FETCH_ALL_DELAY)

    def _begin_fetch(self, queue, delay_override=None):
        self.running      = True
        self._cancel_flag = False
        self.fetch_btn.set_enabled(False)
        self.fetchall_btn.set_enabled(False)
        self.cancel_btn.set_enabled(True)
        self.clear_btn.set_enabled(False)
        self.spinner.start()
        threading.Thread(target=self._fetch_worker,
                         args=(queue, delay_override), daemon=True).start()

    def _cancel_fetch(self):
        if not self.running: return
        self._cancel_flag = True
        self.cancel_btn.set_enabled(False)
        self._log("Cancelling...")

    def _fetch_worker(self, queue, delay_override=None):
        total = len(queue)
        for i, name in enumerate(queue):
            if self._cancel_flag:
                self._log("⬛ Fetch cancelled")
                break
            self.after(0, lambda v=i:
                self.lbl_prog.configure(text=f"{v+1}/{total}"))
            self._log(f"Fetching: {name}")
            slug = self.lookup.get(name.lower().strip())
            if not slug:
                self.results[name] = "notfound"
                self.after(0, lambda n=name: self._set_item_tag(n, "warn"))
            else:
                try:
                    sellers = fetch_sellers(self.session, slug, top=self._settings.get("top_sellers", 5))
                    self.results[name] = sellers if sellers else []
                    self._fetch_ts[name] = time.time()
                    tag = "ok" if sellers else "warn"
                    self.after(0, lambda n=name, t=tag:
                        self._set_item_tag(n, t))
                except PermissionError as e:
                    self._log(f"Auth error: {e}")
                    self.results[name] = "error"
                    self.after(0, lambda n=name:
                        self._set_item_tag(n, "err"))
                    break
                except Exception:
                    self.results[name] = "error"
                    self.after(0, lambda n=name:
                        self._set_item_tag(n, "err"))
            if self.view_name == name:
                self.after(0, lambda n=name: self._show_detail(n))
            if i < total-1 and not self._cancel_flag:
                if delay_override is not None:
                    d = delay_override
                else:
                    d = random.uniform(self._settings.get("fetch_delay_min",2),
                                       self._settings.get("fetch_delay_max",5))
                self._log(f"Waiting {d:.1f}s...  ({i+1}/{total} done)")
                time.sleep(d)

        self.after(0, lambda: self.lbl_prog.configure(text=""))
        if not self._cancel_flag:
            self._log("✓ Done  ·  click any item name to view sellers")
        self.after(0, self._fetch_done)

    def _fetch_done(self):
        self.running      = False
        self._cancel_flag = False
        self.spinner.stop()
        self.fetch_btn.set_enabled(True)
        self.fetchall_btn.set_enabled(True)
        self.cancel_btn.set_enabled(False)
        self.clear_btn.set_enabled(True)

    def _log(self, msg):
        self.after(0, lambda m=msg: self.lbl_log.configure(
            text=f" {m}", fg=C["muted"]))

    # ── Auto-refresh ──────────────────────────────────────────────

    AUTO_REF_INTERVAL = 5 * 60 * 1000   # 5 minuti in ms

    def _toggle_autoref(self, _=None):
        self._autoref_on = not self._autoref_on
        if self._autoref_on:
            self.btn_autoref.configure(fg=C["green"], bg=C["green2"],
                                       text="⟳ AUTO ON")
            self._log("Auto-refresh ON — ogni 5 min sui selected")
            self._schedule_autoref()
        else:
            self.btn_autoref.configure(fg=C["dim"], bg=C["bg3"],
                                       text="⟳ AUTO")
            if self._autoref_job:
                self.after_cancel(self._autoref_job)
                self._autoref_job = None
            self._log("Auto-refresh OFF")

    def _schedule_autoref(self):
        if not self._autoref_on: return
        self._autoref_job = self.after(self.AUTO_REF_INTERVAL, self._autoref_tick)

    def _autoref_tick(self):
        if not self._autoref_on: return
        if self.selected and not self.running:
            self._log("Auto-refresh: aggiornando selected...")
            self._start_fetch()
        elif self.running:
            self._log("Auto-refresh: fetch già in corso, skip")
        else:
            self._log("Auto-refresh: nessun item selezionato")
        self._schedule_autoref()   # ripianifica il prossimo tick


if __name__ == "__main__":
    App().mainloop()