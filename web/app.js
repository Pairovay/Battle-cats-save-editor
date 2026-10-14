"use strict";

/* =====================================================================
   Utilities
   ===================================================================== */
const TOKEN = new URLSearchParams(location.search).get("t") || "";

const api = {
  async req(method, path, body) {
    const res = await fetch(path, {
      method,
      headers: { "X-Token": TOKEN, "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    let data = {};
    try { data = await res.json(); } catch (_) { /* empty body */ }
    if (!res.ok || data.ok === false) {
      const err = new Error(data.error || `Error ${res.status}`);
      err.status = res.status;
      throw err;
    }
    return data;
  },
  get(path) { return this.req("GET", path); },
  post(path, body) { return this.req("POST", path, body || {}); },
};

function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "style" && typeof v === "object") {
        for (const [prop, val] of Object.entries(v)) {
          if (prop.startsWith("--")) el.style.setProperty(prop, val);
          else el.style[prop] = val;
        }
      }
      else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
      else if (k === "value" || k === "checked" || k === "disabled" || k === "indeterminate") el[k] = v;
      else el.setAttribute(k, v === true ? "" : v);
    }
  }
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

const fmt = (n) => (typeof n === "number" ? numberFormat().format(n) : "—");
const pad3 = (n) => String(n).padStart(3, "0");
const norm = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
const clear = (el) => { while (el.firstChild) el.firstChild.remove(); return el; };
const fileName = (path) => String(path || "").split(/[\\/]/).pop();

function segsEl(segs, cls) {
  const wrap = h("span", { class: cls || "" });
  for (const [text, style] of segs || []) {
    if (!style || style === "p") wrap.append(text);
    else if (style.startsWith("#")) wrap.append(h("span", { style: { color: style } }, text));
    else wrap.append(h("span", { class: "t-" + style }, text));
  }
  return wrap;
}
const segsText = (segs) => (segs || []).map((s) => s[0]).join("");

function toast(text, kind = "", ms = 4200) {
  const el = h("div", { class: "toast " + kind }, icon(kind === "err" ? "warning" : kind === "ok" ? "check" : "info"), h("div", null, text));
  document.getElementById("toasts").append(el);
  setTimeout(() => { el.style.transition = "opacity .3s"; el.style.opacity = "0"; setTimeout(() => el.remove(), 320); }, ms);
}

function imgOr(src, fallback) {
  const img = h("img", { src, alt: "", loading: "lazy" });
  img.addEventListener("error", () => { if (fallback) img.replaceWith(fallback()); else img.remove(); }, { once: true });
  return img;
}

/** Appends log lines and only follows the bottom if the user was already there. */
function appendLogLines(container, entries) {
  if (!entries.length) return;
  const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 32;
  for (const e of entries) container.append(h("div", { class: "ln" }, segsEl(e.segs)));
  if (atBottom) container.scrollTop = container.scrollHeight;
}

/* =====================================================================
   Fixed data
   ===================================================================== */
const RARITY_COLORS = ["#9aa0a6", "#26a9b8", "#43a047", "#1e63d6", "#f08c00", "#b23bd6"];
const rarityName = (i) => (i >= 0 && i < RARITY_COLORS.length ? t("rarity_" + i) : "—");
const TRAITS = [
  [0, "#df5526"], [1, "#7fa94c"], [2, "#363636"], [3, "#8f8e8c"], [4, "#c4a925"], [5, "#2fb19d"], [6, "#9b34d6"],
  [7, "#3d6fa0"], [8, "#7c8a33"], [9, "#7d889c"], [10, "#c2185b"], [11, "#6a1b9a"], [12, "#e67e22"], [13, "#795548"],
];
const traitName = (id) => t("trait_" + id);
// data key -> [icon file number (assets/effects/eN.png) or null, is it an immunity?]
const EFFECTS = {
  LongRangeAttack: [19], OmniDirectionalAttack: [null], StrongAgainst: [null], SuperDamage: [null], ExtremeDamage: [null],
  Resilient: [24], SuperResilient: [33], BlowOff: [9], StopMoving: [39], SlowDown: [12], DecreaseAttackPower: [null],
  Critical: [4], Wave: [17], SmallWave: [null], RagingWaves: [null], Curse: [34], ZombieKiller: [null], WitchKiller: [null],
  ApostleKiller: [null], SuperLifeFormSpecialEffect: [null], SuperBeastSlayer: [null], BarrierBreaker: [42],
  DevilShieldPenetration: [null], AllOutBlow: [null], SoulAttack: [null], AgainstTheCastle: [5], MoneyX2: [11],
  IncreaseAttackPower: [null], SurviveOnlyOnce: [null], AttackInvalid: [null], MetalChar: [21], VibrationStopper: [null],
  InvalidWave: [18, true], DisableRagingWave: [null, true], DisableBlast: [null, true], StopMotionBlast: [null, true],
  DisableToSlowMovement: [13, true], AttackPowerReductionDisabled: [null, true], DisableWarp: [37, true],
  AncientCurseNullification: [8, true],
};
const effectName = (key) => (EFFECTS[key] ? t("eff_" + key) : key);
const BATTLE_ITEMS = ["Speed Up", "Treasure Radar", "Rich Cat", "Cat CPU", "Cat Jobs", "Sniper the Cat"];
const regionName = (cc) => (["en", "jp", "kr", "tw"].includes(cc) ? t("region_" + cc) : cc);
// Features whose result is worth reading calmly (their dialog stays open).
const KEEP_OPEN = new Set(["save_upload", "upload_items", "unban_account", "export_save", "save_save_file", "convert_region", "convert_version", "inquiry_code"]);

/* =====================================================================
   Global state
   ===================================================================== */
const S = {
  home: null,
  session: null,
  sessionVersion: -1,
  job: null,
  prompt: null,
  waitingFile: false,
  logs: [],
  logNext: 0,
  menu: null,
  overview: null,
  cats: null,       // array of [id, unlocked, base, plus, currentForm, unlockedForms, fourthForm, guide, talentCount, talentSum]
  catMeta: null,    // data read by BCSFE (names, rarity, forms)
  catStatic: null,  // data shipped in assets (targets, abilities, images)
  route: "home",
  search: "",
};
const catFilters = loadFilters();

function loadFilters() {
  const base = { q: "", state: "all", rar: [], traits: [], effects: [], forms: "", all: false, sort: "id", open: false };
  try { return Object.assign(base, JSON.parse(localStorage.getItem("catFilters") || "{}"), { q: "" }); } catch (_) { return base; }
}
function saveFilters() {
  try { localStorage.setItem("catFilters", JSON.stringify(catFilters)); } catch (_) { /* no storage available */ }
}
const selection = new Set();
let lastClicked = null;

/* =====================================================================
   State polling
   ===================================================================== */
let pollTimer = null;
let pollInFlight = false;
let pollAgain = false;
async function poll() {
  if (pollInFlight) { pollAgain = true; return; }
  pollInFlight = true;
  clearTimeout(pollTimer);
  try {
    const st = await api.get(`/api/state?since=${S.logNext}`);
    applyState(st);
  } catch (e) {
    if (e.status === 403) { pollInFlight = false; showFatal(t("fatal_session")); return; }
  }
  pollInFlight = false;
  if (pollAgain) { pollAgain = false; poll(); return; }
  const busy = S.job && S.job.status === "running";
  pollTimer = setTimeout(poll, busy ? 220 : 1200);
}

function applyState(st) {
  const fresh = (st.logs || []).filter((e) => e.i >= S.logNext);
  if (fresh.length) {
    S.logs.push(...fresh);
    if (S.logs.length > 4000) S.logs.splice(0, S.logs.length - 4000);
  }
  S.logNext = st.next;
  const prevSession = S.session;
  S.session = st.session;
  S.prompt = st.prompt;
  S.waitingFile = st.waiting_file;
  const prevJob = S.job;
  S.job = st.job;

  const loadedChanged = !!prevSession !== !!st.session;
  const versionChanged = st.session && st.session.version !== S.sessionVersion;
  if (loadedChanged) {
    S.menu = null; S.overview = null; S.cats = null; S.catMeta = null; selection.clear(); metaRequested = false;
    if (!st.session) { S.route = "home"; }
  }
  if (versionChanged) {
    S.sessionVersion = st.session.version;
    onSessionChanged(loadedChanged);
  } else if (loadedChanged) {
    renderAll();
  } else {
    renderSaveChip();
  }
  Task.update(prevJob);
  LogDrawer.update();
}

async function onSessionChanged(loadedChanged) {
  if (!S.session) { renderAll(); return; }
  const hadMeta = !!S.catMeta;
  try {
    if (!S.menu || loadedChanged) S.menu = (await api.get("/api/menu")).menu;
    S.overview = (await api.get("/api/overview")).overview;
    if (S.route === "cats") await loadCats();
  } catch (e) { toast(e.message, "err"); }
  if (loadedChanged) { renderAll(); return; }
  renderNav();
  renderSaveChip();
  if (S.route === "cats" && catsDom && catsDom.grid.isConnected && hadMeta === !!S.catMeta) refreshCatGrid();
  else if (S.route === "home" || S.route === "cats" || S.route.startsWith("cat:")) renderView();
}

/* =====================================================================
   Sidebar and top bar
   ===================================================================== */
function navItem(route, label, iconName, extra) {
  const active = S.route === route;
  return h("button", { class: "nav-item" + (active ? " active" : ""), onclick: () => navigate(route) },
    icon(iconName), h("span", null, label), extra ? h("span", { class: "count" }, extra) : null);
}

function renderNav() {
  const nav = clear(document.getElementById("nav"));
  nav.append(navItem("home", S.session ? t("nav_overview") : t("nav_home"), "home"));
  if (S.session) {
    const ov = S.overview;
    nav.append(navItem("cats", t("nav_cats"), "cat", ov ? `${ov.cats_unlocked}/${ov.cats_total}` : null));
    nav.append(h("div", { class: "nav-section" }, t("nav_bcsfe_features")));
    for (const cat of S.menu || []) {
      if (cat.key === "editor") continue;
      nav.append(navItem("cat:" + cat.key, cat.label, cat.icon, String(cat.features.length)));
    }
  }
  nav.append(h("div", { class: "nav-section" }, t("nav_editor")));
  nav.append(navItem("settings", t("nav_settings"), "gear"));
  nav.append(h("button", { class: "nav-item", onclick: () => LogDrawer.open() }, icon("terminal"), h("span", null, t("nav_log"))));
}

function renderSaveChip() {
  const foot = clear(document.getElementById("side-foot"));
  const s = S.session;
  if (!s) {
    foot.append(h("div", { class: "save-chip" },
      h("div", { class: "row" }, icon("info", "sm"), h("span", { class: "title" }, t("no_save_open"))),
      h("div", { class: "sub" }, S.home ? t("versions", { bcsfe: S.home.bcsfe_version, gui: S.home.gui_version }) : "")));
    return;
  }
  foot.append(h("div", { class: "save-chip" },
    h("div", { class: "row" }, h("span", { class: "dot" + (s.dirty ? " dirty" : "") }),
      h("span", { class: "title" }, s.dirty ? t("unsaved_changes") : t("all_saved"))),
    h("div", { class: "sub" }, `${(s.cc || "").toUpperCase()} · v${s.gv} · ${s.inquiry || t("no_code")}`),
    h("div", { class: "actions" },
      h("button", { class: "btn sm primary", onclick: () => runFeature(["save_management", "save_save"]) }, icon("save", "sm"), t("save")),
      h("button", { class: "btn sm dark", title: t("close_save_hint"), onclick: closeSave }, icon("logout", "sm"), t("close")))));
}

function setTitle(title, sub) {
  document.getElementById("page-title").textContent = title;
  document.getElementById("page-sub").textContent = sub || "";
  document.title = S.route === "home" && !S.session ? "Battle Cats Save Editor" : `${title} · Battle Cats Save Editor`;
}

function renderTopActions() {
  const box = clear(document.getElementById("topbar-actions"));
  if (!S.session) return;
  const input = h("input", {
    type: "search", placeholder: t("search_features"), value: S.search,
    oninput: (e) => { S.search = e.target.value; if (S.search.trim()) { if (S.route !== "search") { S.route = "search"; renderAll(true); } else renderView(); } else if (S.route === "search") navigate("home"); },
  });
  box.append(h("div", { class: "searchbox" }, icon("search", "sm"), input));
  box.append(h("button", { class: "btn", onclick: () => runFeature(["save_management", "save_upload"]), title: t("save_upload_hint") }, icon("upload"), t("save_upload")));
  box.append(h("button", { class: "btn primary", onclick: () => runFeature(["save_management", "save_save"]), title: "Ctrl+S" }, icon("save"), t("save")));
  if (S.route === "search") setTimeout(() => { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }, 0);
}

function navigate(route) {
  if (route === S.route && route !== "cats") return;
  S.route = route;
  if (route !== "search") S.search = "";
  if (route === "cats") enterCats();
  if (route === "home" && S.session) refreshOverview();
  renderAll();
}

function renderAll(keepFocus) {
  document.documentElement.lang = LANG();
  renderNav();
  renderSaveChip();
  if (!keepFocus) renderTopActions();
  renderView();
}

function isBusy() { return !!(S.job && S.job.status === "running"); }

/* =====================================================================
   Views
   ===================================================================== */
function renderView() {
  if (S.route !== "cats") document.body.classList.remove("has-actionbar");
  const view = document.getElementById("view");
  const routeKey = (S.session ? "s:" : "n:") + S.route;
  const keepScroll = view.dataset.route === routeKey ? view.scrollTop : 0;
  view.dataset.route = routeKey;
  view.classList.remove("no-pad");
  clear(view);
  if (!S.session && S.route !== "settings") renderWelcome(view);
  else if (S.route === "home") renderDashboard(view);
  else if (S.route === "cats") renderCats(view);
  else if (S.route === "settings") renderSettings(view);
  else if (S.route === "search") renderSearch(view);
  else if (S.route.startsWith("cat:")) renderCategory(view, S.route.slice(4));
  else renderDashboard(view);
  view.scrollTop = keepScroll;
}

/* ---------------- Welcome (no save open) ---------------- */
function renderWelcome(view) {
  setTitle(t("nav_home"), t("welcome_sub"));
  view.classList.add("no-pad");
  const home = S.home || {};
  const card = (iconName, title, text, onclick, featured) =>
    h("button", { class: "load-card" + (featured ? " featured" : ""), onclick },
      h("div", { class: "lc-icon" }, icon(iconName, "lg")), h("h3", null, title), h("p", null, text));

  const cards = [
    card("cloud", t("load_codes"), t("load_codes_desc"), openDownloadDialog, true),
    card("open", t("load_file"), t("load_file_desc"), () => startLoad({ method: "file" })),
  ];
  if (home.documents_save) cards.push(card("folder", t("load_documents"), t("load_documents_desc"), () => startLoad({ method: "documents" })));
  cards.push(card("phone", t("load_adb"), t("load_adb_desc"), () => startLoad({ method: "adb" })));
  cards.push(card("export", t("load_json"), t("load_json_desc"), () => startLoad({ method: "json" })));

  view.append(h("div", { class: "welcome" },
    h("div", { class: "hero" }, h("div", { class: "hero-inner" },
      h("img", { class: "logo", src: "assets/ui/title.png", alt: "The Battle Cats Save Editor" }),
      h("div", { class: "tagline" }, t("tagline", { version: home.bcsfe_version || "" })))),
    h("div", { class: "load-grid" }, cards),
    h("div", { class: "welcome-foot" },
      h("div", { class: "card tips" },
        h("h3", null, icon("info", "sm"), t("codes_howto_title")),
        h("ol", null,
          h("li", null, t("codes_howto_1")),
          h("li", null, t("codes_howto_2")),
          h("li", null, t("codes_howto_3")),
          h("li", null, t("codes_howto_4")))),
      h("div", { class: "card tips" },
        h("h3", null, icon("shield", "sm"), t("before_start_title")),
        h("ul", null,
          h("li", null, t("before_start_1")),
          h("li", null, t("before_start_2")),
          h("li", null, t("data_folder"), ": ", h("span", { title: home.data_dir || "" }, home.data_dir || "—"))))),
    h("div", { class: "credits" }, t("credits"))));
}

/* ---------------- Overview (save open) ---------------- */
function featureIcon(name, size) {
  if (name && name.startsWith("item:")) return imgOr(`assets/items/${name.slice(5)}.png`, () => icon("box", size));
  return icon(name, size);
}

async function refreshOverview() {
  try { S.overview = (await api.get("/api/overview")).overview; if (S.route === "home") renderView(); renderNav(); } catch (e) { /* retried later */ }
}

function renderDashboard(view) {
  const s = S.session;
  setTitle(t("nav_overview"), s.path ? t("open_file", { name: fileName(s.path) }) : "");
  const ov = S.overview;
  view.append(h("div", { class: "save-banner" },
    h("div", { class: "sb-icon" }, h("img", { src: "assets/ui/Icon.png", alt: "" })),
    h("div", { class: "sb-main" },
      h("h2", null, t("save_title", { code: s.inquiry || "" })),
      h("div", { class: "meta" },
        h("span", { class: "pill" }, t("region") + ": " + regionName(s.cc)),
        h("span", { class: "pill" }, t("game_version") + ": " + s.gv),
        h("span", { class: "pill" }, s.dirty ? "● " + t("unsaved_changes") : "✓ " + t("saved"))),
      h("div", { class: "path", title: s.path || "" }, t("file") + ": " + (s.path || "—")),
      s.backup ? h("div", { class: "path", title: s.backup }, t("backup") + ": " + s.backup) : null),
    h("div", { class: "sb-actions" },
      h("button", { class: "btn primary", onclick: () => runFeature(["save_management", "save_save"]) }, icon("save"), t("save")),
      h("button", { class: "btn dark", onclick: () => runFeature(["save_management", "save_upload"]) }, icon("upload"), t("save_upload")),
      h("button", { class: "btn dark", onclick: () => runFeature(["save_management", "save_save_file"]) }, icon("save-as"), t("save_as")))));

  if (!ov) { view.append(h("div", { class: "empty" }, h("div", { class: "spinner big" }))); return; }

  view.append(h("div", { class: "section-title" }, h("h2", null, t("resources")), h("span", { class: "muted" }, t("resources_hint"))));
  view.append(h("div", { class: "grid resources" }, ov.resources.map((r) =>
    h("button", { class: "card res feature", onclick: () => runFeature(r.feature) },
      r.flag === "ban" ? h("span", { class: "badge ban", title: t("ban_risk_hint") }, icon("warning", "sm"), t("risk")) : null,
      h("div", { class: "r-top" }, h("div", { class: "r-icon" }, featureIcon(r.icon)), h("div", { class: "r-label" }, r.label)),
      h("div", { class: "r-value" }, fmt(r.value))))));

  const strip = (title, sub, items, feature, editLabel) => h("div", { class: "card strip" },
    h("div", { class: "s-title" }, h("h3", null, title), h("p", null, sub)),
    h("div", { class: "s-items" }, items),
    h("button", { class: "btn", onclick: () => runFeature(feature) }, icon("level", "sm"), editLabel));

  view.append(h("div", { class: "section-title" }, h("h2", null, t("items"))));
  const grid = h("div", { class: "grid", style: { gap: "12px" } });
  grid.append(strip("Catseyes", t("catseyes_desc"),
    (ov.catseyes.length ? ov.catseyes : [0, 0, 0, 0, 0, 0]).slice(0, 6).map((v, i) =>
      h("div", { class: "mini" }, h("img", { src: `assets/items/Cateye${i}.png`, alt: "" }), h("b", null, fmt(v)), h("span", null, t("catseye_" + i)))),
    ["items", "catseyes"], t("edit_catseyes")));
  grid.append(strip(t("battle_items"), t("battle_items_desc"),
    ov.battle_items.map((v, i) => h("div", { class: "mini" }, h("img", { src: `assets/items/Item${i}.png`, alt: "" }), h("b", null, fmt(v)), h("span", null, BATTLE_ITEMS[i] || `#${i}`))),
    ["items", "battle_items"], t("edit_items")));
  view.append(grid);

  const pct = ov.cats_total ? Math.round((ov.cats_unlocked / ov.cats_total) * 100) : 0;
  view.append(h("div", { class: "section-title" }, h("h2", null, t("nav_cats"))));
  view.append(h("div", { class: "card stat-cats" },
    h("div", { class: "cats-img" }, [0, 25, 42].map((id) => imgOr(`assets/cats/u${pad3(id + 1)}-${id === 0 ? 3 : 1}.png`))),
    h("div", { class: "nums" },
      h("div", { class: "num" }, h("b", null, `${fmt(ov.cats_unlocked)} / ${fmt(ov.cats_total)}`), h("span", null, t("cats_unlocked")), h("div", { class: "progress" }, h("div", { style: { width: pct + "%" } }))),
      h("div", { class: "num" }, h("b", null, fmt(ov.cats_true_form)), h("span", null, t("cats_true_form")))),
    h("button", { class: "btn primary lg", onclick: () => navigate("cats") }, icon("cat"), t("open_cat_editor"))));

  view.append(h("div", { class: "section-title" }, h("h2", null, t("shortcuts"))));
  const quick = [
    ["items", "catfruit"], ["items", "talent_orbs"], ["items", "battle_items_endless"], ["levels", "clear_story"],
    ["levels", "story_treasures"], ["gamototo", "ototo_cat_cannon"], ["save_management", "export_save"], ["fixes", "fix_time_errors"],
  ];
  view.append(featureGrid(quick.map(findFeature).filter(Boolean)));
}

function findFeature(path) {
  for (const cat of S.menu || []) for (const f of cat.features) if (f.path[0] === path[0] && f.path[1] === path[1]) return f;
  return null;
}

function featureCard(f) {
  return h("button", { class: "feature", onclick: () => runFeature(f.path), title: f.original ? t("in_bcsfe", { name: f.original }) : "" },
    h("div", { class: "f-icon" }, featureIcon(f.icon, "lg")),
    h("div", null, h("h3", null, f.label), f.desc ? h("p", null, f.desc) : null,
      f.original && f.original !== f.label ? h("div", { class: "orig" }, f.original) : null,
      f.flag === "ban" ? h("span", { class: "badge ban" }, icon("warning", "sm"), t("ban_risk")) :
        f.flag === "warn" ? h("span", { class: "badge warn" }, icon("info", "sm"), t("advanced")) : null));
}
function featureGrid(list) { return h("div", { class: "grid features" }, list.map(featureCard)); }

/* ---------------- Category ---------------- */
function renderCategory(view, key) {
  const cat = (S.menu || []).find((c) => c.key === key);
  if (!cat) { navigate("home"); return; }
  setTitle(cat.label, cat.desc);
  if (key === "cats_special_skills") {
    view.append(h("div", { class: "notice info" }, icon("info"),
      h("div", null, t("cats_category_tip"), " ",
        h("button", { class: "btn sm", style: { marginLeft: "6px" }, onclick: () => navigate("cats") }, icon("cat", "sm"), t("open_visual_editor")))));
  }
  if (key === "save_management") {
    view.append(h("div", { class: "notice" }, icon("warning"), h("div", null, t("upload_notice"))));
  }
  view.append(featureGrid(cat.features));
}

/* ---------------- Search ---------------- */
function renderSearch(view) {
  const q = norm(S.search.trim());
  setTitle(t("search"), t("search_results", { q: S.search.trim() }));
  const found = [];
  for (const cat of S.menu || []) for (const f of cat.features) {
    if ([f.label, f.desc, f.original, cat.label].some((x) => norm(x).includes(q))) found.push(f);
  }
  if (!found.length) { view.append(h("div", { class: "empty" }, icon("search"), h("div", null, t("search_none")))); return; }
  view.append(featureGrid(found));
}

/* ---------------- Settings ---------------- */
function renderSettings(view) {
  setTitle(t("nav_settings"), t("settings_sub"));
  const opts = [
    { option: "config", label: t("opt_config"), desc: t("opt_config_desc"), icon: "gear" },
    { option: "manage_game_data", label: t("opt_game_data"), desc: t("opt_game_data_desc"), icon: "database" },
    { option: "update_external", label: t("opt_update_external"), desc: t("opt_update_external_desc"), icon: "refresh" },
  ];
  view.append(h("div", { class: "grid features" }, opts.map((o) =>
    h("button", { class: "feature", onclick: () => runEditorOption(o.option) },
      h("div", { class: "f-icon" }, icon(o.icon, "lg")), h("div", null, h("h3", null, o.label), h("p", null, o.desc))))));
  const home = S.home || {};
  view.append(h("div", { class: "section-title" }, h("h2", null, t("language"))));
  const langs = home.languages || { en: "English", es: "Español" };
  view.append(h("div", { class: "card", style: { padding: "16px 18px" } },
    h("p", { class: "muted", style: { margin: "0 0 12px" } }, t("language_desc")),
    h("div", { class: "seg" }, Object.entries(langs).map(([code, label]) =>
      h("button", { class: home.language === code ? "on" : "", onclick: () => setLanguage(code) }, label)))));
  view.append(h("div", { class: "section-title" }, h("h2", null, t("information"))));
  view.append(h("div", { class: "card", style: { padding: "16px 18px" } }, h("dl", { class: "kv" },
    h("dt", null, t("bcsfe_version")), h("dd", null, home.bcsfe_version || "—"),
    h("dt", null, t("gui_version")), h("dd", null, home.gui_version || "—"),
    h("dt", null, t("data_folder")), h("dd", null, home.data_dir || "—"),
    h("dt", null, t("saves_folder")), h("dd", null, home.saves_dir || "—"))));
}

async function setLanguage(code) {
  if (isBusy()) { toast(t("wait_task"), "warn"); return; }
  try {
    const res = await api.post("/api/settings", { language: code });
    S.home = res.home;
    S.menu = null;
    toast(t("language_changed"), "ok");
    renderAll();
    poll();
  } catch (e) { toast(e.message, "err"); }
}

/* =====================================================================
   Tasks: running BCSFE features
   ===================================================================== */
async function startJob(path, body) {
  if (isBusy()) { toast(t("wait_task"), "warn"); return null; }
  try {
    const res = await api.post(path, body);
    S.job = res.job;
    Task.open(res.job, body);
    poll();
    return res.job;
  } catch (e) {
    toast(e.message, "err");
    return null;
  }
}
const runFeature = (featPath) => startJob("/api/feature", { path: featPath });
const runEditorOption = (option) => startJob("/api/editor", { option });
const startLoad = (body) => startJob("/api/load", body);

const Task = {
  el: null, jobId: null, promptId: null, consoleEl: null, renderedLogs: 0, meta: null,

  open(job, meta) {
    this.close();
    this.jobId = job.id;
    this.promptId = null;
    this.renderedLogs = 0;
    this.meta = meta || {};
    this.statusEl = h("span", { class: "status-pill" });
    this.closeBtn = h("button", { class: "btn ghost icon-only", title: t("close"), onclick: () => this.onClose() }, icon("close"));
    this.qEl = h("div");
    this.consoleEl = h("div", { class: "console" });
    this.footEl = h("div", { class: "modal-foot" });
    this.modal = h("div", { class: "modal" },
      h("div", { class: "modal-head" }, h("h2", null, job.title), this.statusEl, this.closeBtn),
      h("div", { class: "modal-body" }, this.qEl, this.consoleEl),
      this.footEl);
    this.el = h("div", { class: "modal-backdrop" }, this.modal);
    document.getElementById("modal-root").append(this.el);
    this.update(null);
  },

  close() {
    if (this.el) this.el.remove();
    this.el = null; this.jobId = null; this.promptId = null;
  },

  onClose() {
    const job = S.job;
    if (job && job.id === this.jobId && job.status === "running") {
      if (S.prompt) api.post("/api/cancel").then(poll).catch(() => {});
      else toast(t("task_still_running"), "warn");
      return;
    }
    this.close();
  },

  jobLogs() {
    const job = S.job;
    if (!job) return [];
    return S.logs.filter((e) => e.i >= job.log_start);
  },

  appendLogs() {
    const logs = this.jobLogs();
    if (logs.length < this.renderedLogs) { clear(this.consoleEl); this.renderedLogs = 0; }
    appendLogLines(this.consoleEl, logs.slice(this.renderedLogs));
    this.renderedLogs = logs.length;
  },

  update(prevJob) {
    const job = S.job;
    // A task started without this window knowing (e.g. after a reload): open it.
    if (!this.el && job && job.status === "running" && (!prevJob || prevJob.id !== job.id || prevJob.status !== "running")) {
      this.open(job);
    }
    if (!this.el || !job || job.id !== this.jobId) return;
    this.appendLogs();
    const prompt = S.prompt;
    clear(this.statusEl);
    if (job.status === "running") {
      if (prompt) {
        this.statusEl.append(icon("info", "sm"), t("waiting_answer"));
        if (prompt.id !== this.promptId) { this.promptId = prompt.id; this.renderPrompt(prompt); }
      } else {
        this.statusEl.append(h("span", { class: "spinner" }), S.waitingFile ? t("pick_file_window") : t("working"));
        if (this.promptId !== "work") { this.promptId = "work"; this.renderWorking(); }
        else if (this.waitingNoteFor !== S.waitingFile) this.renderWorking();
      }
    } else if (this.promptId !== "done") {
      this.promptId = "done";
      this.finish(job);
    }
  },

  renderWorking() {
    this.waitingNoteFor = S.waitingFile;
    clear(this.qEl).append(h("div", { class: "waiting" }, h("div", { class: "spinner big" }),
      h("div", null, S.waitingFile ? t("file_window_open") : t("working_long"))));
    clear(this.footEl);
    this.consoleEl.style.maxHeight = "";
  },

  finish(job) {
    const logs = this.jobLogs();
    const ok = job.status === "done";
    clear(this.statusEl).append(icon(ok ? "check" : "warning", "sm"), ok ? t("completed") : t("error"));
    const lines = logs.map((e) => segsText(e.segs)).filter((x) => x.trim());
    const important = logs.some((e) => e.segs.some((s) => s[1] === "e" || s[1] === "w"));
    const featKey = this.meta && this.meta.path ? this.meta.path[this.meta.path.length - 1] : "";
    const last = lines.length ? lines[lines.length - 1] : t("done");
    const codes = this.findCodes(lines);

    if (job.status === "cancelled") {
      this.close();
      toast(t("task_stopped"), "warn");
      return;
    }
    if (job.kind === "load" && ok && S.session) {
      this.close();
      toast(t("save_loaded"), "ok");
      navigate("home");
      return;
    }
    if (ok && !important && !codes && !KEEP_OPEN.has(featKey) && (lines.length <= 4 || job.kind === "cats_meta" || job.kind === "cats")) {
      this.close();
      toast(last, "ok");
      return;
    }
    clear(this.qEl);
    if (codes) {
      this.qEl.append(h("div", { class: "result ok" }, h("div", { class: "r-ic" }, icon("check", "lg")),
        h("div", null, h("h3", null, t("save_uploaded")), h("p", { class: "muted" }, t("enter_codes_in_game")))));
      for (const [label, value] of [[t("transfer_code"), codes.transfer], [t("confirmation_code"), codes.confirm]]) {
        this.qEl.append(h("div", { class: "field" }, h("label", null, label),
          h("div", { class: "row" }, h("input", { class: "input big", readonly: true, value }),
            h("button", { class: "btn", onclick: () => { navigator.clipboard.writeText(value).then(() => toast(t("copied"), "ok")); } }, t("copy")))));
      }
    } else {
      this.qEl.append(h("div", { class: "result " + (ok ? "ok" : "err") },
        h("div", { class: "r-ic" }, icon(ok ? "check" : "warning", "lg")),
        h("div", null, h("h3", null, ok ? t("finished") : t("error_title")),
          h("p", { class: "muted" }, ok ? (important ? t("check_messages") : last)
            : t("feature_failed", { error: job.error || t("unknown_error") })))));
    }
    clear(this.footEl).append(
      h("div", { class: "left" }, h("button", { class: "btn ghost", onclick: () => navigator.clipboard.writeText(lines.join("\n")).then(() => toast(t("messages_copied"), "ok")) }, t("copy_messages"))),
      h("button", { class: "btn primary", onclick: () => this.close(), autofocus: true }, t("close")));
    this.footEl.querySelector(".btn.primary").focus();
  },

  findCodes(lines) {
    // BCSFE prints the codes in English or, with the bundled translation, in Spanish.
    const text = lines.join("\n");
    const tc = /(?:Transfer Code|Código de transferencia):\s*(\S+)/i.exec(text);
    const cc = /(?:Confirmation Code|Código de confirmación):\s*(\S+)/i.exec(text);
    return tc && cc ? { transfer: tc[1], confirm: cc[1] } : null;
  },

  send(value) {
    const id = S.prompt ? S.prompt.id : null;
    if (id === null) return;
    clear(this.footEl);
    clear(this.qEl).append(h("div", { class: "waiting" }, h("div", { class: "spinner big" }), h("div", null, t("applying"))));
    this.promptId = "work";
    api.post("/api/answer", { id, value }).then(poll).catch((e) => toast(e.message, "err"));
  },
  cancel() {
    clear(this.footEl);
    this.promptId = "work";
    api.post("/api/cancel").then(poll).catch(() => {});
  },

  renderPrompt(p) {
    const q = clear(this.qEl);
    const foot = clear(this.footEl);
    this.consoleEl.style.maxHeight = ["select", "multi", "edit_ints"].includes(p.kind) ? "120px" : "";
    const cancelBtn = h("button", { class: "btn", onclick: () => this.cancel() }, t("cancel"));
    const text = segsText(p.text).trim();
    if (text && !["edit_int", "edit_str"].includes(p.kind)) q.append(h("div", { class: "question" }, segsEl(p.text)));
    const builder = Prompts[p.kind] || Prompts.text;
    builder(p, q, foot, cancelBtn);
    const stop = h("button", { class: "btn ghost", title: t("stop_task_hint"), onclick: () => { clear(foot); api.post("/api/stop").then(poll).catch(() => {}); } }, icon("close", "sm"), t("stop_task"));
    const left = foot.querySelector(".left");
    if (left) left.prepend(stop); else foot.prepend(h("div", { class: "left" }, stop));
  },
};

/* ---------------- One widget per prompt kind ---------------- */
const Prompts = {
  select(p, q, foot, cancelBtn) {
    const opts = p.options || [];
    const many = opts.length > 10;
    const list = h("div", { class: "options" + (!many && opts.length <= 6 && opts.every((o) => segsText(o).length < 26) ? " two" : "") });
    const items = opts.map((o, i) => {
      const b = h("button", { class: "option", onclick: () => Task.send(i) }, h("span", { class: "num" }, i + 1), segsEl(o));
      b.dataset.text = norm(segsText(o));
      return b;
    });
    list.append(...items);
    if (many) {
      const input = h("input", { type: "search", placeholder: t("filter_options"), oninput: (e) => {
        const v = norm(e.target.value);
        for (const it of items) it.classList.toggle("hidden", v && !it.dataset.text.includes(v));
      } });
      q.append(h("div", { class: "list-tools" }, h("div", { class: "searchbox" }, icon("search", "sm"), input)));
      q.append(h("div", { class: "list-scroll" }, list));
      setTimeout(() => input.focus(), 30);
    } else {
      q.append(list);
      setTimeout(() => items[0] && items[0].focus(), 30);
    }
    foot.append(cancelBtn);
  },

  multi(p, q, foot, cancelBtn) {
    const opts = p.options || [];
    const chosen = new Set();
    const count = h("span", { class: "muted" });
    const items = opts.map((o, i) => {
      const b = h("button", { class: "option", onclick: () => { chosen.has(i) ? chosen.delete(i) : chosen.add(i); refresh(); } },
        h("span", { class: "chk" }, icon("check")), segsEl(o));
      b.dataset.text = norm(segsText(o));
      return b;
    });
    const visible = () => items.map((it, i) => [it, i]).filter(([it]) => !it.classList.contains("hidden"));
    const allBtn = h("button", { class: "btn sm", onclick: () => {
      const vis = visible();
      const allOn = vis.every(([, i]) => chosen.has(i));
      for (const [, i] of vis) allOn ? chosen.delete(i) : chosen.add(i);
      refresh();
    } }, t("select_all"));
    const ok = h("button", { class: "btn primary", onclick: () => Task.send([...chosen].sort((a, b) => a - b)) }, icon("check", "sm"), t("ok"));
    function refresh() {
      items.forEach((it, i) => it.classList.toggle("on", chosen.has(i)));
      count.textContent = t("n_of_m_selected", { n: chosen.size, m: opts.length });
      const vis = visible();
      allBtn.textContent = vis.length && vis.every(([, i]) => chosen.has(i)) ? t("unselect_all") : t("select_all");
      ok.disabled = chosen.size === 0;
    }
    const input = h("input", { type: "search", placeholder: t("filter"), oninput: (e) => {
      const v = norm(e.target.value);
      for (const it of items) it.classList.toggle("hidden", v && !it.dataset.text.includes(v));
      refresh();
    } });
    q.append(h("div", { class: "list-tools" }, h("div", { class: "searchbox" }, icon("search", "sm"), input), allBtn));
    q.append(h("div", { class: "list-scroll" }, h("div", { class: "options" }, items)));
    refresh();
    foot.append(h("div", { class: "left" }, count), cancelBtn, ok);
    setTimeout(() => input.focus(), 30);
  },

  int(p, q, foot, cancelBtn) {
    const input = h("input", { class: "input big", type: "number", min: p.min, max: p.max, value: p.default !== null && p.default !== undefined ? p.default : "" });
    const ok = h("button", { class: "btn primary", onclick: submit }, icon("check", "sm"), t("ok"));
    function submit() {
      const v = input.value.trim();
      if (v === "" && (p.default === null || p.default === undefined)) { input.classList.add("invalid"); return; }
      Task.send(v === "" ? "" : Math.min(Math.max(parseInt(v, 10), p.min), p.max));
    }
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
    input.addEventListener("input", () => input.classList.toggle("invalid", input.value !== "" && (isNaN(parseInt(input.value, 10)) || +input.value < p.min || +input.value > p.max)));
    q.append(h("div", { class: "row" }, input,
      h("button", { class: "btn", onclick: () => { input.value = p.min; input.focus(); } }, t("min")),
      p.show_max !== false ? h("button", { class: "btn", onclick: () => { input.value = p.max; input.focus(); } }, icon("max", "sm"), t("max")) : null));
    q.append(h("div", { class: "hint muted", style: { marginTop: "8px", fontSize: "13px" } }, t("between", { min: fmt(p.min), max: fmt(p.max) })));
    foot.append(cancelBtn, ok);
    setTimeout(() => { input.focus(); input.select(); }, 30);
  },

  edit_int(p, q, foot, cancelBtn) {
    q.append(h("div", { class: "q-name" }, segsEl(p.name)));
    q.append(h("div", { class: "q-current" }, t("current_value") + ": ", h("b", null, fmt(p.current)), p.show_max ? ` · ${t("maximum")}: ${fmt(p.max)}` : ""));
    const input = h("input", { class: "input big", type: "number", min: 0, max: p.max, value: p.current });
    const ok = h("button", { class: "btn primary", onclick: submit }, icon("check", "sm"), t("apply"));
    function submit() {
      const raw = input.value.trim();
      const v = parseInt(raw, 10);
      if (raw === "" || isNaN(v)) { input.classList.add("invalid"); return; }
      Task.send(Math.min(Math.max(v, 0), p.max));
    }
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
    const quick = (label, value) => h("button", { class: "btn sm", onclick: () => { input.value = value; input.focus(); } }, label);
    q.append(h("div", { class: "row" }, input, h("button", { class: "btn", onclick: () => { input.value = p.max; input.focus(); } }, icon("max", "sm"), t("maximum"))));
    const steps = [100, 1000, 10000, 100000].filter((n) => n < p.max);
    q.append(h("div", { class: "row wrap", style: { marginTop: "10px" } }, quick("0", 0), steps.map((n) => quick(fmt(n), n))));
    foot.append(cancelBtn, ok);
    setTimeout(() => { input.focus(); input.select(); }, 30);
  },

  text(p, q, foot, cancelBtn) {
    const input = h("input", { class: "input", type: "text", value: p.current || "" });
    const ok = h("button", { class: "btn primary", onclick: () => Task.send(input.value) }, icon("check", "sm"), t("ok"));
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") Task.send(input.value); });
    q.append(input);
    foot.append(cancelBtn, ok);
    setTimeout(() => input.focus(), 30);
  },

  edit_str(p, q, foot, cancelBtn) {
    q.append(h("div", { class: "q-name" }, segsEl(p.name)));
    q.append(h("div", { class: "q-current" }, t("current_value") + ": ", h("b", null, p.current || "—")));
    Prompts.text(p, q, foot, cancelBtn);
  },

  yesno(p, q, foot, cancelBtn) {
    const yes = h("button", { class: "btn primary", onclick: () => Task.send(true) }, icon("check"), t("yes"));
    q.append(h("div", { class: "yesno" }, h("button", { class: "btn", onclick: () => Task.send(false) }, icon("close"), t("no")), yes));
    foot.append(cancelBtn);
    setTimeout(() => yes.focus(), 30);
  },

  range(p, q, foot, cancelBtn) {
    const input = h("input", { class: "input", type: "text", placeholder: t("range_placeholder") });
    const ok = h("button", { class: "btn primary", onclick: () => Task.send(input.value) }, icon("check", "sm"), t("ok"));
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") Task.send(input.value); });
    q.append(h("div", { class: "row" }, input, h("button", { class: "btn", onclick: () => Task.send("__all__") }, t("all"))));
    q.append(h("div", { class: "muted", style: { fontSize: "13px", marginTop: "8px" } }, t("range_help", { min: p.min, max: p.max })));
    foot.append(cancelBtn, ok);
    setTimeout(() => input.focus(), 30);
  },

  edit_ints(p, q, foot, cancelBtn) {
    const rows = (p.items || []).map((it, i) => {
      const input = h("input", { type: "number", min: 0, max: it.max, value: it.value });
      const tr = h("tr", null, h("td", { class: "name" }, segsEl(it.name)),
        h("td", { class: "cur" }, t("current_and_max", { value: fmt(it.value), max: fmt(it.max) })), h("td", null, input));
      input.addEventListener("input", () => tr.classList.toggle("changed", input.value !== String(it.value)));
      tr.dataset.text = norm(segsText(it.name));
      return { tr, input, it, i };
    });
    const table = h("table", { class: "ints-table" }, h("tbody", null, rows.map((r) => r.tr)));
    const setAll = (fn) => rows.forEach((r) => { if (!r.tr.classList.contains("hidden")) { r.input.value = fn(r.it); r.input.dispatchEvent(new Event("input")); } });
    const tools = h("div", { class: "list-tools" });
    if (rows.length > 8) {
      tools.append(h("div", { class: "searchbox" }, icon("search", "sm"), h("input", { type: "search", placeholder: t("filter"), oninput: (e) => {
        const v = norm(e.target.value);
        rows.forEach((r) => r.tr.classList.toggle("hidden", v && !r.tr.dataset.text.includes(v)));
      } })));
    }
    tools.append(h("button", { class: "btn sm", onclick: () => setAll((it) => it.max) }, icon("max", "sm"), t("all_to_max")),
      h("button", { class: "btn sm", onclick: () => setAll(() => 0) }, t("all_to_zero")),
      h("button", { class: "btn sm ghost", onclick: () => setAll((it) => it.value) }, t("restore")));
    if (p.total_max) q.append(h("div", { class: "notice info" }, icon("info"), h("div", null, t("sum_limit", { max: fmt(p.total_max) }))));
    q.append(tools, h("div", { class: "list-scroll" }, table));
    const ok = h("button", { class: "btn primary", onclick: () => Task.send(rows.map((r) => {
      const v = parseInt(r.input.value, 10);
      return isNaN(v) ? r.it.value : Math.min(Math.max(v, 0), r.it.max);
    })) }, icon("check", "sm"), t("apply_changes"));
    foot.append(cancelBtn, ok);
  },
};

/* =====================================================================
   Own dialogs
   ===================================================================== */
function modal({ title, body, foot, wide, onClose }) {
  const close = () => { el.remove(); document.removeEventListener("keydown", onKey); if (onClose) onClose(); };
  const onKey = (e) => { if (e.key === "Escape" && document.getElementById("modal-root").lastElementChild === el) close(); };
  const el = h("div", { class: "modal-backdrop", onmousedown: (e) => { if (e.target === el) close(); } },
    h("div", { class: "modal" + (wide ? " wide" : "") },
      h("div", { class: "modal-head" }, h("h2", null, title), h("button", { class: "btn ghost icon-only", onclick: close, title: t("close") }, icon("close"))),
      h("div", { class: "modal-body" }, body),
      foot ? h("div", { class: "modal-foot" }, foot(close)) : null));
  document.addEventListener("keydown", onKey);
  document.getElementById("modal-root").append(el);
  return close;
}

function confirmDialog({ title, text, ok, danger = false }) {
  return new Promise((resolve) => {
    let answered = false;
    modal({
      title,
      body: h("div", { class: "question", style: { marginBottom: 0 } }, text),
      onClose: () => { if (!answered) resolve(false); },
      foot: (c) => [
        h("button", { class: "btn", onclick: c }, t("cancel")),
        h("button", { class: "btn " + (danger ? "danger" : "primary"), onclick: () => { answered = true; c(); resolve(true); } }, ok || t("ok")),
      ],
    });
  });
}

function openDownloadDialog() {
  const codes = (S.home && S.home.country_codes) || ["en", "jp", "kr", "tw"];
  const tc = h("input", { class: "input", placeholder: t("transfer_placeholder"), autocomplete: "off", spellcheck: "false" });
  const cc = h("input", { class: "input", placeholder: t("confirmation_placeholder"), autocomplete: "off", inputmode: "numeric" });
  const region = h("select", { class: "input" }, codes.map((c) => h("option", { value: c }, regionName(c))));
  const submit = (close) => {
    tc.classList.toggle("invalid", !tc.value.trim());
    cc.classList.toggle("invalid", !cc.value.trim());
    if (!tc.value.trim() || !cc.value.trim()) return;
    close();
    startLoad({ method: "codes", transfer_code: tc.value.trim(), confirmation_code: cc.value.trim(), cc: region.value });
  };
  const close = modal({
    title: t("download_title"),
    body: h("div", null,
      h("div", { class: "notice" }, icon("warning"), h("div", null, t("download_notice"))),
      h("div", { class: "field" }, h("label", null, t("transfer_code")), tc, h("span", { class: "hint" }, t("transfer_hint"))),
      h("div", { class: "field" }, h("label", null, t("confirmation_code")), cc),
      h("div", { class: "field" }, h("label", null, t("game_region")), region, h("span", { class: "hint" }, t("region_hint")))),
    foot: (c) => [h("button", { class: "btn", onclick: c }, t("cancel")), h("button", { class: "btn primary", onclick: () => submit(c) }, icon("cloud", "sm"), t("download"))],
  });
  for (const el of [tc, cc]) el.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(close); });
  setTimeout(() => tc.focus(), 30);
}

async function closeSave() {
  if (isBusy()) { toast(t("wait_task"), "warn"); return; }
  if (S.session && S.session.dirty) {
    const ok = await confirmDialog({ title: t("close_save"), text: t("close_save_confirm"), ok: t("close_without_saving"), danger: true });
    if (!ok) return;
  }
  try { await api.post("/api/close"); } catch (e) { toast(e.message, "err"); }
  S.route = "home";
  poll();
}

const LogDrawer = {
  consoleEl: null, rendered: 0,
  open() {
    this.consoleEl = h("div", { class: "console" });
    this.rendered = 0;
    const close = modal({
      title: t("nav_log"), wide: true,
      body: h("div", { class: "log-drawer" }, this.consoleEl),
      foot: (c) => [
        h("div", { class: "left" }, h("span", { class: "muted" }, t("log_desc"))),
        h("button", { class: "btn", onclick: () => navigator.clipboard.writeText(S.logs.map((e) => segsText(e.segs)).join("\n")).then(() => toast(t("log_copied"), "ok")) }, t("copy")),
        h("button", { class: "btn primary", onclick: c }, t("close")),
      ],
      onClose: () => { this.consoleEl = null; },
    });
    this.update();
    this.consoleEl.scrollTop = this.consoleEl.scrollHeight;
    return close;
  },
  update() {
    if (!this.consoleEl) return;
    if (!S.logs.length) { clear(this.consoleEl).append(h("div", { class: "ln" }, t("log_empty"))); this.rendered = -1; return; }
    if (this.rendered < 0 || this.rendered > S.logs.length) { clear(this.consoleEl); this.rendered = 0; }
    appendLogLines(this.consoleEl, S.logs.slice(this.rendered));
    this.rendered = S.logs.length;
  },
};

function showFatal(text) {
  clear(document.getElementById("modal-root")).append(h("div", { class: "modal-backdrop" }, h("div", { class: "modal" },
    h("div", { class: "modal-head" }, h("h2", null, t("disconnected"))), h("div", { class: "modal-body" }, text))));
}

/* =====================================================================
   Visual cat editor
   ===================================================================== */
async function loadStatic() {
  if (S.catStatic) return;
  try { S.catStatic = await (await fetch("assets/catdata.json")).json(); } catch (_) { S.catStatic = {}; }
}

async function loadCats() {
  const res = await api.get("/api/cats");
  S.cats = res.cats;
  S.catMeta = res.meta || null;
}

let metaRequested = false;
async function enterCats() {
  await loadStatic();
  try {
    await loadCats();
    if (!S.catMeta && !metaRequested && !isBusy()) {
      metaRequested = true;
      startJob("/api/cats/meta", {});
    }
  } catch (e) { toast(e.message, "err"); }
  if (S.route === "cats") renderView();
}

function catName(id, form) {
  const m = S.catMeta && S.catMeta[id];
  const st = S.catStatic && S.catStatic[id];
  const f = Math.min(form, 3);
  if (m && m.n) { for (let k = f; k >= 0; k--) if (m.n[k]) return m.n[k]; }
  if (st && st.n) { for (let k = Math.min(f, 2); k >= 0; k--) if (st.n[k]) return st.n[k]; }
  return t("cat_n", { id });
}
function catNames(id) {
  const m = S.catMeta && S.catMeta[id];
  const st = S.catStatic && S.catStatic[id];
  return [...((m && m.n) || []), ...((st && st.n) || [])].filter(Boolean);
}
function catRarity(id) {
  const m = S.catMeta && S.catMeta[id];
  if (m && typeof m.r === "number") return m.r;
  const st = S.catStatic && S.catStatic[id];
  return st ? st.r : -1;
}
function catTotalForms(id) {
  const m = S.catMeta && S.catMeta[id];
  if (m && m.f) return m.f;
  const st = S.catStatic && S.catStatic[id];
  if (st && st.n) return st.n[2] ? 3 : 2;
  return 3;
}
function catImgSrc(id, form) {
  const st = S.catStatic && S.catStatic[id];
  if (!st) return null;
  for (let k = Math.min(form, 2); k >= 0; k--) {
    const c = st.img[k];
    if (c === "u") return `assets/cats/u${pad3(id + 1)}-${k + 1}.png`;
    if (c === "i") return `assets/cats/i${pad3(id + 1)}-${k + 1}.png`;
  }
  return null;
}
function catMaxForm(c) {
  const [, , base, , cf, uf, ff] = c;
  if (ff > 0) return 3;
  if (uf >= 3) return 2;
  return Math.max(cf, base >= 10 ? 1 : 0);
}

function parseIdQuery(q) {
  if (!/^[\d\s,\-]+$/.test(q)) return null;
  const ids = new Set();
  for (const part of q.split(/[\s,]+/).filter(Boolean)) {
    const m = /^(\d+)-(\d+)$/.exec(part);
    if (m) { for (let i = +m[1]; i <= Math.min(+m[2], +m[1] + 5000); i++) ids.add(i); }
    else if (/^\d+$/.test(part)) ids.add(+part);
  }
  return ids;
}

function filteredCats() {
  const f = catFilters;
  const q = f.q.trim();
  const idSet = q ? parseIdQuery(q) : null;
  const nq = norm(q);
  const out = [];
  for (const c of S.cats || []) {
    const id = c[0];
    if (f.state === "owned" && !c[1]) continue;
    if (f.state === "locked" && c[1]) continue;
    if (q) {
      if (idSet) { if (!idSet.has(id)) continue; }
      else if (!catNames(id).some((n) => norm(n).includes(nq))) continue;
    }
    if (f.rar.length && !f.rar.includes(catRarity(id))) continue;
    if (f.forms === "tf" && !(c[5] >= 3)) continue;
    if (f.forms === "no_tf" && !(catTotalForms(id) >= 3 && c[5] < 3)) continue;
    if (f.forms === "fourth" && !(c[6] > 0)) continue;
    if (f.forms === "fourth_avail" && !(catTotalForms(id) >= 4 && !c[6])) continue;
    const st = S.catStatic && S.catStatic[id];
    if (f.traits.length) {
      const tr = (st && st.t) || [];
      if (f.all ? !f.traits.every((x) => tr.includes(x)) : !f.traits.some((x) => tr.includes(x))) continue;
    }
    if (f.effects.length) {
      const ef = (st && st.e) || [];
      if (f.all ? !f.effects.every((x) => ef.includes(x)) : !f.effects.some((x) => ef.includes(x))) continue;
    }
    out.push(c);
  }
  const sorters = {
    id: (a, b) => a[0] - b[0],
    name: (a, b) => catName(a[0], a[4]).localeCompare(catName(b[0], b[4]), LANG()),
    level: (a, b) => (b[2] + b[3]) - (a[2] + a[3]) || a[0] - b[0],
    rarity: (a, b) => catRarity(b[0]) - catRarity(a[0]) || a[0] - b[0],
  };
  out.sort(sorters[f.sort] || sorters.id);
  return out;
}

let catsDom = null;
function renderCats(view) {
  setTitle(t("cat_editor"), t("cat_editor_sub"));
  view.classList.add("no-pad");
  if (!S.cats || !S.catStatic) {
    view.append(h("div", { class: "empty" }, h("div", { class: "spinner big", style: { margin: "0 auto 12px" } }), t("loading_cats")));
    return;
  }
  const f = catFilters;
  const searchInput = h("input", { type: "search", placeholder: t("cat_search"), value: f.q,
    oninput: (e) => { f.q = e.target.value; refreshCatGrid(); } });
  const seg = h("div", { class: "seg" }, [["all", t("filter_all")], ["owned", t("filter_unlocked")], ["locked", t("filter_locked")]].map(([k, label]) =>
    h("button", { class: f.state === k ? "on" : "", onclick: () => { f.state = k; saveFilters(); renderView(); } }, label)));
  const sort = h("select", { class: "input", style: { width: "auto" }, onchange: (e) => { f.sort = e.target.value; saveFilters(); refreshCatGrid(); } },
    [["id", t("sort_id")], ["name", t("sort_name")], ["level", t("sort_level")], ["rarity", t("sort_rarity")]].map(([k, l]) => h("option", { value: k, selected: f.sort === k ? true : null }, l)));
  const activeFilters = f.rar.length + f.traits.length + f.effects.length + (f.forms ? 1 : 0);
  const filterBtn = h("button", { class: "btn" + (f.open ? " primary" : ""), onclick: () => { f.open = !f.open; saveFilters(); renderView(); } },
    icon("filter", "sm"), t("filters"), activeFilters ? h("span", { class: "badge", style: { marginLeft: "2px" } }, activeFilters) : null);

  const toolbar = h("div", { class: "cats-toolbar" },
    h("div", { class: "row wrap" }, h("div", { class: "searchbox" }, icon("search", "sm"), searchInput), seg, filterBtn, sort,
      !S.catMeta ? h("button", { class: "btn sm", title: t("provisional_names_hint"), onclick: () => startJob("/api/cats/meta", {}) }, icon("refresh", "sm"), t("provisional_names")) : null),
    f.open ? renderFilterPanel() : null);

  const countEl = h("span");
  const metaBar = h("div", { class: "cats-meta-bar" }, countEl, h("span", { class: "spacer" }),
    h("button", { class: "btn sm", onclick: () => { for (const c of filteredCats()) selection.add(c[0]); refreshCatGrid(); } }, icon("check", "sm"), t("select_visible")),
    h("button", { class: "btn sm ghost", onclick: () => { selection.clear(); refreshCatGrid(); } }, t("clear_selection")));
  toolbar.append(metaBar);

  const grid = h("div", { class: "cat-grid" });
  const scroll = h("div", { class: "cats-scroll" }, grid);
  const bar = h("div", { class: "action-bar hidden" });
  view.append(h("div", { class: "cats-view" }, toolbar, h("div", { class: "cats-wrap" }, scroll, bar)));
  catsDom = { grid, countEl, bar, scroll };
  refreshCatGrid();
  if (document.activeElement === document.body && f.q) searchInput.focus();
}

function renderFilterPanel() {
  const f = catFilters;
  const toggle = (arr, v) => { const i = arr.indexOf(v); i >= 0 ? arr.splice(i, 1) : arr.push(v); saveFilters(); renderView(); };
  const chip = (on, label, onclick, color, img) => h("button", { class: "chip" + (on ? " on" : ""), onclick, style: color ? { "--chip": color, "--chip-ink": "#fff" } : null, "aria-pressed": on ? "true" : "false" },
    img ? h("img", { src: img, alt: "" }) : color ? h("span", { class: "sw" }) : null, label);
  const rarNames = (S.catMeta && S.catMeta["-1"] && S.catMeta["-1"].rarity_names) || [];
  const effKeys = Object.keys(EFFECTS);
  const effChip = (k) => chip(f.effects.includes(k), effectName(k), () => toggle(f.effects, k), null, EFFECTS[k][0] ? `assets/effects/e${EFFECTS[k][0]}.png` : null);
  return h("div", { class: "filters" },
    h("div", { class: "f-label" }, t("rarity")),
    h("div", { class: "chips" }, RARITY_COLORS.map((color, i) => chip(f.rar.includes(i), rarityName(i), () => toggle(f.rar, i), color, null)),
      rarNames.slice(RARITY_COLORS.length).map((n, j) => chip(f.rar.includes(RARITY_COLORS.length + j), n, () => toggle(f.rar, RARITY_COLORS.length + j)))),
    h("div", { class: "f-label" }, t("forms")),
    h("div", { class: "chips" }, [["tf", t("form_tf")], ["no_tf", t("form_tf_missing")], ["fourth", t("form_fourth")], ["fourth_avail", t("form_fourth_missing")]].map(([k, l]) =>
      chip(f.forms === k, l, () => { f.forms = f.forms === k ? "" : k; saveFilters(); renderView(); }))),
    h("div", { class: "f-label" }, t("target")),
    h("div", { class: "chips" }, TRAITS.map(([id, color]) => chip(f.traits.includes(id), traitName(id), () => toggle(f.traits, id), color))),
    h("div", { class: "f-label" }, t("ability")),
    h("div", { class: "chips" }, effKeys.filter((k) => !EFFECTS[k][1]).map(effChip)),
    h("div", { class: "f-label" }, t("immunity")),
    h("div", { class: "chips" }, effKeys.filter((k) => EFFECTS[k][1]).map(effChip)),
    h("div", { class: "f-label" }, ""),
    h("div", { class: "row wrap" },
      h("label", { class: "row", style: { gap: "6px", cursor: "pointer" } }, h("input", { type: "checkbox", checked: f.all, onchange: (e) => { f.all = e.target.checked; saveFilters(); refreshCatGrid(); } }),
        t("match_all")),
      h("span", { class: "spacer", style: { flex: 1 } }),
      h("button", { class: "btn sm", onclick: () => { Object.assign(f, { rar: [], traits: [], effects: [], forms: "", all: false }); saveFilters(); renderView(); } }, t("clear_filters"))),
    h("div", { class: "f-label" }, ""),
    h("div", { class: "muted", style: { fontSize: "12px" } }, t("filters_note")));
}

function catCard(c) {
  const [id, unlocked, base, plus, cf] = c;
  const rar = catRarity(id);
  const src = catImgSrc(id, cf);
  const total = catTotalForms(id);
  const maxForm = catMaxForm(c);
  const dots = [];
  for (let k = 0; k < Math.max(total, maxForm + 1); k++) dots.push(h("i", { class: (unlocked && k <= maxForm ? "on" : "") + (unlocked && k === cf ? " cur" : "") }));
  const card = h("div", { class: "cat-card" + (unlocked ? "" : " locked") + (selection.has(id) ? " sel" : ""), tabindex: "0", style: { "--rar": RARITY_COLORS[rar] || "#ccc" }, title: catNames(id)[0] || "" },
    h("span", { class: "rar" }),
    h("span", { class: "tick" }, icon("check")),
    unlocked ? null : h("span", { class: "lockic", title: t("locked") }, icon("lock")),
    h("div", { class: "img" }, src ? imgOr(src, () => h("span", { class: "ph" }, "#" + id)) : h("span", { class: "ph" }, "#" + id)),
    h("div", { class: "name" }, catName(id, cf)),
    h("div", { class: "sub" }, h("span", null, "#" + id), h("span", { class: "forms" }, dots),
      h("span", { class: "lv" + (unlocked ? "" : " off") }, unlocked ? t("level_short", { base, plus: plus ? " +" + plus : "" }) : t("locked"))),
    h("button", { class: "btn sm ghost icon-only more", title: t("details"), onclick: (e) => { e.stopPropagation(); openCatDetail(id); } }, icon("info", "sm")));
  card.addEventListener("click", (e) => onCatClick(e, id));
  card.addEventListener("dblclick", () => openCatDetail(id));
  card.addEventListener("keydown", (e) => { if (e.key === " " || e.key === "Enter") { e.preventDefault(); onCatClick(e, id); } });
  card.dataset.id = id;
  return card;
}

let visibleCats = [];
function catCountText() {
  return t("showing_cats", { n: fmt(visibleCats.length), m: fmt((S.cats || []).length) }) + (selection.size ? " · " + t("n_selected", { n: fmt(selection.size) }) : "");
}

function refreshCatGrid() {
  if (!catsDom) return;
  visibleCats = filteredCats();
  const { grid, countEl } = catsDom;
  clear(grid);
  if (!visibleCats.length) {
    grid.append(h("div", { class: "empty", style: { gridColumn: "1 / -1" } }, icon("cat"), h("div", null, t("no_cats_match"))));
  } else {
    const frag = document.createDocumentFragment();
    for (const c of visibleCats) frag.append(catCard(c));
    grid.append(frag);
  }
  countEl.textContent = catCountText();
  renderActionBar();
}

function onCatClick(e, id) {
  if (e.shiftKey && lastClicked !== null) {
    const ids = visibleCats.map((c) => c[0]);
    const a = ids.indexOf(lastClicked), b = ids.indexOf(id);
    if (a >= 0 && b >= 0) for (const x of ids.slice(Math.min(a, b), Math.max(a, b) + 1)) selection.add(x);
  } else if (selection.has(id)) selection.delete(id);
  else selection.add(id);
  lastClicked = id;
  for (const el of catsDom.grid.children) if (el.dataset.id) el.classList.toggle("sel", selection.has(+el.dataset.id));
  catsDom.countEl.textContent = catCountText();
  renderActionBar();
}

function popMenu(anchor, items) {
  document.querySelectorAll(".menu-pop").forEach((m) => m.remove());
  const r = anchor.getBoundingClientRect();
  const menu = h("div", { class: "menu-pop" }, items.map(([label, hint, fn, danger]) =>
    h("button", { class: danger ? "danger" : "", onclick: () => { menu.remove(); fn(); } }, h("div", null, h("div", null, label), hint ? h("div", { class: "hint" }, hint) : null))));
  document.body.append(menu);
  const mh = menu.offsetHeight, mw = menu.offsetWidth;
  menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - mw - 8)) + "px";
  menu.style.top = (r.top - mh - 8 > 8 ? r.top - mh - 8 : r.bottom + 8) + "px";
  setTimeout(() => document.addEventListener("mousedown", function away(e) { if (!menu.contains(e.target)) { menu.remove(); document.removeEventListener("mousedown", away); } }), 0);
}

function catActionItems(ids) {
  const n = ids.length;
  const act = (action, title, params) => () => catAction(action, ids, title, params);
  return {
    forms: [
      [t("give_tf"), t("only_if_has"), act("true_form", t("give_tf"))],
      [t("force_tf"), t("even_if_not"), act("true_form", t("force_tf"), { force: true })],
      [t("remove_tf"), null, act("remove_true_form", t("remove_tf")), true],
      [t("give_fourth"), t("only_if_has"), act("fourth_form", t("give_fourth"))],
      [t("force_fourth"), t("even_if_not"), act("fourth_form", t("force_fourth"), { force: true })],
      [t("remove_fourth"), null, act("remove_fourth_form", t("remove_fourth")), true],
    ],
    talents: [
      [t("talents_max"), t("talents_max_hint"), act("talents_max", t("talents_max"))],
      [t("talents_edit"), n > 1 ? t("talents_edit_many", { n }) : t("talents_edit_one"), act("talents_edit", t("talents_edit"))],
      [t("talents_remove"), null, act("talents_remove", t("talents_remove")), true],
    ],
    guide: [
      [t("guide_add"), t("guide_add_hint"), act("guide_unlock", t("guide_add"))],
      [t("guide_remove"), null, act("guide_remove", t("guide_remove")), true],
    ],
  };
}

function renderActionBar() {
  const bar = catsDom.bar;
  clear(bar);
  document.body.classList.toggle("has-actionbar", selection.size > 0);
  if (!selection.size) { bar.classList.add("hidden"); return; }
  bar.classList.remove("hidden");
  const ids = [...selection];
  const items = catActionItems(ids);
  const menuBtn = (label, iconName, list) => {
    const b = h("button", { class: "btn sm dark", title: label, onclick: () => popMenu(b, list) }, icon(iconName, "sm"), h("span", { class: "lbl" }, label), icon("chevron-down", "sm"));
    return b;
  };
  bar.append(
    h("span", { class: "count" }, t("n_selected", { n: fmt(ids.length) })),
    h("span", { class: "sep" }),
    h("button", { class: "btn sm primary", onclick: () => catAction("unlock", ids, t("unlock_cats")) }, icon("unlock", "sm"), t("unlock")),
    h("button", { class: "btn sm dark", title: t("change_level"), onclick: () => openLevelDialog(ids) }, icon("level", "sm"), h("span", { class: "lbl" }, t("level_btn"))),
    menuBtn(t("forms"), "star", items.forms),
    menuBtn(t("talents"), "orb", items.talents),
    menuBtn(t("guide"), "book", items.guide),
    h("button", { class: "btn sm dark", title: t("remove_cats"), onclick: () => removeCats(ids) }, icon("lock", "sm"), h("span", { class: "lbl" }, t("remove"))),
    h("span", { class: "sep" }),
    h("button", { class: "btn sm ghost icon-only", style: { color: "#fbeed2" }, title: t("clear_selection_esc"), onclick: () => { selection.clear(); refreshCatGrid(); } }, icon("close", "sm")));
}

async function removeCats(ids) {
  const ok = await confirmDialog({ title: t("remove_cats"), text: t("remove_cats_confirm", { n: fmt(ids.length) }), ok: t("remove"), danger: true });
  if (ok) catAction("remove", ids, t("remove_cats"));
}

function catAction(action, ids, title, params) {
  return startJob("/api/cats/action", { action, ids, title: `${title} (${ids.length})`, params: params || {} });
}

function openLevelDialog(ids) {
  const one = ids.length === 1 ? (S.cats || []).find((c) => c[0] === ids[0]) : null;
  const mk = (initial) => {
    const st = { mode: initial === null ? "keep" : "set" };
    const input = h("input", { class: "input big", type: "number", min: 0, value: initial === null ? "" : initial });
    const seg = h("div", { class: "seg" });
    const draw = () => {
      clear(seg).append(...[["set", t("mode_number")], ["max", t("maximum")], ["keep", t("mode_keep")]].map(([k, l]) =>
        h("button", { class: st.mode === k ? "on" : "", onclick: () => { st.mode = k; draw(); } }, l)));
      input.disabled = st.mode !== "set";
      if (st.mode === "set") setTimeout(() => input.focus(), 0);
    };
    input.addEventListener("input", () => { if (st.mode !== "set") { st.mode = "set"; draw(); } });
    draw();
    st.value = () => (st.mode === "keep" ? "keep" : st.mode === "max" ? "max" : input.value.trim() === "" ? "keep" : Math.max(0, parseInt(input.value, 10) || 0));
    st.input = input; st.seg = seg;
    return st;
  };
  const base = mk(one ? one[2] : 50);
  const plus = mk(one ? one[3] : null);
  const apply = (close) => {
    const params = { base: base.value(), plus: plus.value() };
    if (params.base === "keep" && params.plus === "keep") { toast(t("no_level_change"), "warn"); return; }
    close();
    catAction("upgrade", ids, t("change_level"), params);
  };
  modal({
    title: ids.length === 1 ? t("level_of", { name: catName(ids[0], one ? one[4] : 0) }) : t("level_of_n", { n: fmt(ids.length) }),
    body: h("div", null,
      h("div", { class: "level-box" },
        h("div", { class: "lb" }, h("h4", null, t("level")), base.input, base.seg),
        h("div", { class: "lb" }, h("h4", null, t("plus_level")), plus.input, plus.seg)),
      h("div", { class: "notice info", style: { marginTop: "14px", marginBottom: 0 } }, icon("info"), h("div", null, t("level_note")))),
    foot: (c) => [h("button", { class: "btn", onclick: c }, t("cancel")), h("button", { class: "btn primary", onclick: () => apply(c) }, icon("check", "sm"), t("apply"))],
  });
}

function openCatDetail(id) {
  const c = (S.cats || []).find((x) => x[0] === id);
  if (!c) return;
  const [, unlocked, base, plus, cf, uf, ff, guide, talN, talSum] = c;
  const total = catTotalForms(id);
  let shown = Math.min(cf, 2);
  const imgBox = h("div", { class: "big-img" });
  const nameEl = h("div", { class: "q-name", style: { marginTop: "10px" } });
  const tabs = h("div", { class: "form-tabs" });
  const formNames = [t("form_normal"), t("form_evolved"), t("form_true"), t("form_ultra")];
  const draw = () => {
    const src = catImgSrc(id, shown);
    clear(imgBox).append(src ? imgOr(src, () => h("span", { class: "ph" }, "#" + id)) : h("span", { class: "ph", style: { fontSize: "28px" } }, "#" + id));
    nameEl.textContent = catName(id, shown);
    clear(tabs).append(...Array.from({ length: Math.max(total, 2) }, (_, k) => h("button", { class: "chip" + (k === shown ? " on" : ""), onclick: () => { shown = k; draw(); } }, formNames[k] || `#${k + 1}`)));
  };
  draw();
  const rar = catRarity(id);
  const st = S.catStatic && S.catStatic[id];
  const traits = ((st && st.t) || []).map(traitName);
  const effects = ((st && st.e) || []).map(effectName);
  const formNow = !unlocked ? "—" : ff > 0 ? t("form_ultra") : uf >= 3 ? t("form_true") : cf >= 1 ? t("form_evolved") : t("form_normal");
  const items = catActionItems([id]);
  const act = (label, iconName, fn, cls) => h("button", { class: "btn " + (cls || ""), onclick: () => { closeFn(); fn(); } }, icon(iconName, "sm"), label);
  const closeFn = modal({
    title: t("cat_n", { id }), wide: true,
    body: h("div", { class: "cat-detail" },
      h("div", null, imgBox, nameEl, tabs),
      h("div", null,
        h("dl", { class: "kv" },
          h("dt", null, t("status")), h("dd", null, unlocked ? t("unlocked") : t("locked")),
          h("dt", null, t("rarity")), h("dd", null, rarityName(rar)),
          h("dt", null, t("level")), h("dd", null, unlocked ? `${base} + ${plus}` : "—"),
          h("dt", null, t("current_form")), h("dd", null, formNow),
          h("dt", null, t("cat_forms")), h("dd", null, String(total)),
          h("dt", null, t("talents")), h("dd", null, talN ? t("talents_summary", { n: talN, sum: talSum }) : t("none")),
          h("dt", null, t("cat_guide")), h("dd", null, guide ? t("claimed") : t("not_claimed")),
          traits.length ? [h("dt", null, t("targets")), h("dd", null, traits.join(", "))] : null,
          effects.length ? [h("dt", null, t("abilities")), h("dd", null, effects.join(", "))] : null),
        h("div", { class: "quick-actions" },
          unlocked ? act(t("remove_cat"), "lock", () => removeCats([id]), "danger") : act(t("unlock"), "unlock", () => catAction("unlock", [id], t("unlock_cats")), "primary"),
          act(t("change_level") + "…", "level", () => openLevelDialog([id])),
          act(t("form_true"), "star", items.forms[0][2]),
          act(t("remove_tf"), "star", items.forms[2][2]),
          act(t("talents_max"), "orb", items.talents[0][2]),
          act(t("talents_edit") + "…", "orb", items.talents[1][2]),
          act(t("form_ultra"), "star", items.forms[3][2]),
          guide ? act(t("guide_remove"), "book", items.guide[1][2]) : act(t("guide_add"), "book", items.guide[0][2])))),
  });
}

/* =====================================================================
   Start-up
   ===================================================================== */
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
    e.preventDefault();
    if (S.session && !isBusy()) runFeature(["save_management", "save_save"]);
  }
  if (S.route === "cats" && !document.querySelector(".modal-backdrop") && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) {
    if (e.key === "Escape" && selection.size) { selection.clear(); refreshCatGrid(); }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "a") { e.preventDefault(); for (const c of visibleCats) selection.add(c[0]); refreshCatGrid(); }
  }
});

window.addEventListener("beforeunload", (e) => {
  if (S.session && S.session.dirty) { e.preventDefault(); e.returnValue = ""; }
});
// Only when the window really closes (not if the user decides to stay).
window.addEventListener("pagehide", () => {
  navigator.sendBeacon(`/api/bye?t=${encodeURIComponent(TOKEN)}`);
});

(async function start() {
  if (!TOKEN) { showFatal(t("fatal_no_token")); return; }
  try { S.home = await api.get("/api/home"); } catch (e) { showFatal(t("fatal_connect", { error: e.message })); return; }
  renderAll();
  poll();
})();
