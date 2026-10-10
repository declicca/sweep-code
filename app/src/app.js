/*
 * Sweep — the app core (readable source, brief 01 step 3). Built by ops/build-assets.sh into assets/app.<hash>.js, like the
 * other modules. Recovered on 9 Oct 2026 from the minified bundle assets/app.708d6fa5c5.js: the function names are the original ones, the short
 * local names (e, t, a…) come from the old minifier and cannot be recovered. Edit this file, never assets/app.*.js.
 */
const ECON_SEED = [], ECON_PROFILES = [], INSTR = {
  NQ: {
    tick: .25,
    tickC: 500,
    name: "E-mini Nasdaq-100"
  },
  MNQ: {
    tick: .25,
    tickC: 50,
    name: "Micro Nasdaq-100"
  },
  ES: {
    tick: .25,
    tickC: 1250,
    name: "E-mini S&P 500"
  },
  MES: {
    tick: .25,
    tickC: 125,
    name: "Micro S&P 500"
  },
  YM: {
    tick: 1,
    tickC: 500,
    name: "E-mini Dow"
  },
  MYM: {
    tick: 1,
    tickC: 50,
    name: "Micro Dow"
  },
  RTY: {
    tick: .1,
    tickC: 500,
    name: "E-mini Russell 2000"
  },
  M2K: {
    tick: .1,
    tickC: 50,
    name: "Micro Russell 2000"
  },
  CL: {
    tick: .01,
    tickC: 1e3,
    name: "Crude Oil"
  },
  MCL: {
    tick: .01,
    tickC: 100,
    name: "Micro Crude Oil"
  },
  GC: {
    tick: .1,
    tickC: 1e3,
    name: "Gold"
  },
  MGC: {
    tick: .1,
    tickC: 100,
    name: "Micro Gold"
  },
  "6E": {
    tick: 5e-5,
    tickC: 625,
    name: "Euro FX"
  },
  M6E: {
    tick: 1e-4,
    tickC: 125,
    name: "Micro Euro FX"
  },
  ZN: {
    tick: .015625,
    tickC: 1562.5,
    name: "10-Year T-Note"
  },
  ZB: {
    tick: .03125,
    tickC: 3125,
    name: "30-Year T-Bond"
  },
  SI: {
    tick: .005,
    tickC: 2500,
    name: "Silver"
  },
  SIL: {
    tick: .005,
    tickC: 500,
    name: "Micro Silver"
  },
  NG: {
    tick: .001,
    tickC: 1e3,
    name: "Natural Gas"
  },
  HG: {
    tick: 5e-4,
    tickC: 1250,
    name: "Copper"
  },
  MBT: {
    tick: 5,
    tickC: 50,
    name: "Micro Bitcoin"
  },
  MET: {
    tick: .5,
    tickC: 5,
    name: "Micro Ether"
  }
}, INSTR_UNKNOWN = {
  tick: .01,
  tickC: 0,
  name: "Unknown symbol",
  unknown: !0
}, instOf = e => INSTR[e] || INSTR[String(e || "").toUpperCase().replace(/[FGHJKMNQUVXZ]\d{1,2}$/, "")] || INSTR_UNKNOWN, SESS = [ [ "asia", "Asia" ], [ "london", "London" ], [ "nyam", "New York AM" ], [ "nypm", "New York PM" ], [ "other", "Other" ] ], EMO = [ "Calm", "Confident", "Patient", "Focused", "FOMO", "Fearful", "Frustrated", "Angry", "Greedy", "Overconfident", "Revenge mindset", "Need to be right", "Trying to recover a loss", "Hesitant", "Impulsive" ], GRADES = [ "A", "B", "C", "D", "F" ], PST = [ [ "planned", "Planned" ], [ "requested", "Requested" ], [ "approved", "Approved" ], [ "paid", "Paid" ], [ "rejected", "Rejected" ] ], ECAT = [ [ "evaluation", "Evaluation fee" ], [ "activation", "Activation fee" ], [ "reset", "Reset fee" ], [ "platform", "Platform fee" ], [ "data", "Data fee" ], [ "other", "Other" ] ], DEFAULT_QS = [ [ "plan", "Was this trade part of my trading plan?", "Off-plan trade" ], [ "confirm", "Did I wait for confirmation?", "Entered without confirmation" ], [ "entry", "Was my entry valid?", "Invalid entry" ], [ "size", "Did I respect my maximum position size?", "Oversized position" ], [ "risk", "Did I define my risk before entering?", "Risk not defined before entry" ], [ "stop", "Did I respect my stop?", "Stop not respected" ], [ "widen", "Did I avoid moving my stop to increase risk?", "Moved stop to increase risk" ], [ "addloser", "Did I avoid adding to a losing trade?", "Added to a losing trade" ], [ "revenge", "Did I avoid revenge trading?", "Revenge trading" ], [ "chase", "Did I avoid chasing price?", "Chased price" ], [ "dll", "Did I respect my daily loss limit?", "Broke daily loss limit" ], [ "emotion", "Was my emotional state appropriate for trading?", "Traded in a poor emotional state" ], [ "exit", "Did I follow my exit plan?", "Did not follow exit plan" ] ], MIN_N = 5, COLS = [ "firms", "accounts", "trades", "journals", "weekly", "payouts", "expenses" ], $ = (e, t = document) => t.querySelector(e), $$ = (e, t = document) => [ ...t.querySelectorAll(e) ], esc = e => String(e ?? "").replace(/[&<>"']/g, t => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;"
}[t])), uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8), pad = e => String(e).padStart(2, "0"), ymd = e => `${e.getFullYear()}-${pad(e.getMonth() + 1)}-${pad(e.getDate())}`, _nyDay = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/New_York",
  year: "numeric",
  month: "2-digit",
  day: "2-digit"
}), todayStr = () => _nyDay.format(new Date(Date.now() + 216e5)), sessionOfTs = e => {
  e = String(e || "");
  const t = e.slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(t) && e.slice(11, 13) >= "18" ? ymdAdd(t, 1) : t;
}, wallTs = (e, t) => `${String(t || "").slice(0, 2) >= "18" ? ymdAdd(e, -1) : e} ${t}`, hasSessionDate = e => !!(e && (e.session_date || String(e.entry_time || "").slice(0, 5) < "18:00" || e.executions && e.executions[0] && String(e.executions[0].t || "").slice(0, 10) !== "" && String(e.executions[0].t).slice(0, 10) < e.date)), isEveTrade = e => !!e && String(e.entry_time || "").slice(0, 5) >= "18:00" && hasSessionDate(e), tradeWhen = e => {
  if (!e || !e.date) return "";
  const t = String(e.entry_time || "").slice(0, 5);
  if (!isEveTrade(e)) return [ fdate(e.date), t ].filter(Boolean).join(" · ");
  const a = fdate(e.date), n = +ymdAdd(e.date, -1).slice(8), L = typeof LANG == "string" ? LANG : "en";
  return L === "fr" ? `séance du ${a} · entré le ${n} à ${t}` : L === "es" ? `sesión del ${a} · entrada el ${n} a las ${t}` : `session of ${a} · entered on the ${n}th at ${t}`;
}, tradeTimeOf = e => {
  const t = String(e && e.entry_time || "").slice(0, 5);
  if (!isEveTrade(e)) return t;
  const n = +ymdAdd(e.date, -1).slice(8), L = typeof LANG == "string" ? LANG : "en";
  return L === "fr" ? `le ${n} à ${t}` : L === "es" ? `el ${n} a las ${t}` : `the ${n}th at ${t}`;
}, wallOfTrade = (e, t) => `${hasSessionDate(e) && String(t || "").slice(0, 2) >= "18" ? ymdAdd(e.date, -1) : e.date} ${t}`, ymdAdd = (e, t) => {
  const a = new Date(e + "T12:00:00Z");
  return a.setUTCDate(a.getUTCDate() + t), a.toISOString().slice(0, 10);
}, pd = e => new Date(e + "T12:00:00"), addDays = (e, t) => {
  const a = pd(e);
  return a.setDate(a.getDate() + t), ymd(a);
}, weekStart = e => {
  const t = pd(e);
  return t.setDate(t.getDate() - (t.getDay() + 6) % 7), ymd(t);
}, monthStart = e => e.slice(0, 7) + "-01", fdate = (e, t = {
  month: "short",
  day: "numeric"
}) => {
  if (!e) return "—";
  const a = (typeof LOC == "function" ? LOC() : "en-US") + JSON.stringify(t), n = fdate._c || (fdate._c = {});
  return (n[a] || (n[a] = new Intl.DateTimeFormat(typeof LOC == "function" ? LOC() : "en-US", t))).format(pd(e));
}, fdateL = e => fdate(e, {
  weekday: "short",
  month: "short",
  day: "numeric",
  year: "numeric"
});

function lsGet(e, t) {
  try {
    const a = localStorage.getItem(e);
    return a ? JSON.parse(a) : t;
  } catch {
    return t;
  }
}

function lsSet(e, t) {
  try {
    localStorage.setItem(e, JSON.stringify(t));
  } catch {}
}

function money(e, {sign: t = !0, dec: a} = {}) {
  if (e == null || !isFinite(e)) return "—";
  e = Math.round(e);
  const n = Math.abs(e) / 100, s = a ?? (Math.abs(e) % 100 ? 2 : 0);
  return (e < 0 ? "−" : t && e > 0 ? "+" : "") + moneyNum(((money._f || (money._f = {}))[s] || (money._f[s] = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: s,
    maximumFractionDigits: s
  }))).format(n));
}

function moneyNum(e, t = "") {
  const a = typeof LANG == "string" ? LANG : "en";
  if (a !== "fr" && a !== "es") return "$" + e + t;
  const n = a === "fr" ? " " : ".";
  return e.replace(/[,.]/g, s => s === "," ? "\0" : ",").replace(/\0/g, n) + (t ? " " + t : "") + " $";
}

const moneyU = e => money(e, {
  sign: !1
});

function moneyShort(e) {
  if (e == null) return "—";
  const t = Math.abs(e) / 100, a = e < 0 ? "−" : "";
  return t >= 1e3 ? a + moneyNum((t / 1e3).toFixed(t >= 1e4 ? 0 : 1), "k") : a + moneyNum(String(Math.round(t)));
}

const cls = e => e > 0 ? "pos" : e < 0 ? "neg" : "", pct = e => e == null || !isFinite(e) ? "—" : Math.round(e * 100) + "%", dpct = e => e == null ? "—" : Math.round(e) + "%", pf = e => e == null ? "—" : e === 1 / 0 ? "∞" : decl(e.toFixed(2)), rfmt = e => e == null || !isFinite(e) ? "—" : (e > 0 ? "+" : e < 0 ? "−" : "") + decl(Math.abs(e).toFixed(2)) + "R";

function decl(e) {
  return typeof LANG < "u" && LANG !== "en" ? String(e).replace(".", ",") : String(e);
}

function parseMoney(e) {
  if (e == null || (e = String(e).replace(/[^0-9.\-−]/g, "").replace("−", "-"), e === "" || e === "-")) return null;
  const t = parseFloat(e);
  return isFinite(t) ? Math.round(t * 100) : null;
}

function getPath(e, t) {
  return t.split(".").reduce((a, n) => a == null ? a : a[n], e);
}

function setPath(e, t, a) {
  const n = t.split(".");
  let s = e;
  for (let i = 0; i < n.length - 1; i++) (s[n[i]] == null || typeof s[n[i]] != "object") && (s[n[i]] = {}), 
  s = s[n[i]];
  a === void 0 ? delete s[n.at(-1)] : s[n.at(-1)] = a;
}

function sessionFor(e) {
  if (!e) return "other";
  const [t, a] = e.split(":").map(Number), n = t * 60 + a;
  return n >= 18 * 60 || n < 2 * 60 ? "asia" : n < 9 * 60 + 30 ? "london" : n < 12 * 60 ? "nyam" : n < 17 * 60 ? "nypm" : "other";
}

const sessName = e => (SESS.find(t => t[0] === e) || [ 0, "—" ])[1], S = {
  firms: [],
  accounts: [],
  trades: [],
  journals: [],
  weekly: [],
  payouts: [],
  expenses: [],
  settings: null,
  mode: "loading",
  uid: "local",
  me: null
};

let DB = null, ROOT = null, ASSETS = null, DL = null;

const LSK = "tj.data.v1";

function defaultSettings() {
  return {
    id: "settings",
    questions: DEFAULT_QS.map(([e, t, a]) => ({
      id: e,
      text: t,
      viol: a,
      active: !0
    })),
    setups: [],
    threshold: 90
  };
}

async function boot() {
  render();
  let e = !1;
  if (window.claude && typeof window.claude.use == "function") try {
    const [t, a] = await Promise.all([ claude.use("db"), claude.use("user") ]), n = a ? await a.id() : null;
    t && n && (DB = t, S.uid = n, ROOT = t.doc("data/users/" + n + "/journal"), S.mode = "cloud", 
    await subscribeAll(), e = !0), claude.use("assets").then(s => {
      ASSETS = s, scheduleRender();
    }).catch(() => {}), claude.use("downloads").then(s => {
      DL = s;
    }).catch(() => {});
  } catch (t) {
    console.warn("capabilities", t);
  }
  if (!e) try {
    const t = await fetch("api/data", {
      headers: {
        Accept: "application/json"
      },
      cache: "no-store"
    });
    if (t.status === 401 && (t.headers.get("content-type") || "").includes("application/json")) {
      S.mode = "signedout", render();
      return;
    }
    if (t.ok && (t.headers.get("content-type") || "").includes("application/json")) {
      const a = await t.json();
      COLS.forEach(n => S[n] = a[n] || []), S.settings = a.settings || null, a.user && typeof a.user == "object" ? (S.me = a.user, 
      S.uid = a.user.id, S.resetMethod = a.reset_method || "recovery") : S.uid = a.user || "owner", 
      S.mode = "server", ASSETS = serverAssets, e = !0, validateFilters();
    }
  } catch {}
  if (!e) {
    const t = lsGet(LSK, null);
    t && (COLS.forEach(a => S[a] = t[a] || []), S.settings = t.settings || null), S.mode = "local";
  }
  S.settings || (S.settings = defaultSettings()), ANIM = !0, render();
}

function subscribeAll() {
  const e = [], t = (a, n) => e.push(new Promise(s => {
    let i = !0;
    a.onSnapshot(o => {
      n(o), i ? (i = !1, s()) : scheduleRender();
    }, o => {
      console.warn(o), toast("Sync stopped: " + (o.message || o.code)), s();
    });
  }));
  return COLS.forEach(a => t(ROOT.collection(a), n => {
    S[a] = n.docs.map(s => ({
      ...s.data(),
      id: s.id
    }));
  })), t(ROOT.collection("meta").doc("settings"), a => {
    a.exists && (S.settings = {
      ...a.data(),
      id: "settings"
    });
  }), Promise.race([ Promise.all(e), new Promise(a => setTimeout(a, 9e3)) ]);
}

let authLostShown = !1;

function apiFetch(e, t = {}) {
  return fetch(e, {
    ...t,
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "fetch",
      ...t.headers || {}
    }
  }).then(a => (a.status === 401 && S.mode === "server" && !authLostShown && (authLostShown = !0, 
  toast("You were signed out. Reloading…", {
    ms: 4e3
  }), setTimeout(() => location.reload(), 1800)), a));
}

async function apiJSON(e, t = {}) {
  const a = await apiFetch(e, t.body !== void 0 ? {
    ...t,
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(t.body)
  } : t), n = await a.json().catch(() => ({}));
  if (!a.ok) {
    const s = new Error(n.error || "server error " + a.status);
    throw s.status = a.status, s.code = n.code, s.data = n, a.status === 402 && window.SweepBilling && SweepBilling.handleApiError(n), 
    s;
  }
  return n;
}

function validateFilters() {
  let e = !1;
  F.account !== "all" && !S.accounts.some(t => t.id === F.account) && (F.account = "all", 
  e = !0), F.firm !== "all" && !S.firms.some(t => t.id === F.firm) && (F.firm = "all", 
  e = !0), e && saveF();
}

function srvPath(e, t) {
  return "api/docs/" + (e === "settings" ? "meta/settings" : encodeURIComponent(e) + "/" + encodeURIComponent(t));
}

async function srvSend(e, t, a) {
  const n = await apiFetch(srvPath(e, t) + "?_method=" + (a ? "PUT" : "DELETE"), a ? {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(a)
  } : {
    method: "POST"
  });
  if (n.status === 402) {
    const s = await n.json().catch(() => ({})), i = new Error("upgrade required");
    throw i.status = 402, i.data = s, i;
  }
  if (!n.ok) {
    const s = new Error(n.status === 401 ? "your session expired — reload the page to sign in again" : n.status === 413 ? "record too large" : n.status === 507 ? "record limit reached for this account" : n.status === 403 ? "blocked by the server firewall (see README, ModSecurity)" : "server error " + n.status);
    throw s.code = "http_" + n.status, s;
  }
}

const serverAssets = {
  async upload(e) {
    const t = await apiFetch("api/uploads", {
      method: "POST",
      headers: {
        "Content-Type": e.type || "application/octet-stream"
      },
      body: e
    });
    if (!t.ok) throw new Error(t.status === 415 ? "use PNG, JPEG, GIF or WebP images" : t.status === 413 ? "image is too large for the server upload limit" : t.status === 507 ? "your screenshot storage is full" : "server error " + t.status);
    return t.json();
  },
  delete(e) {
    return apiFetch("api/uploads/" + encodeURIComponent(e) + "?_method=DELETE", {
      method: "POST"
    });
  }
}, blobSrc = e => S.mode === "server" ? "uploads/" + encodeURIComponent(e) : "/_blob/" + encodeURIComponent(e);

function saveLocal() {
  const e = {
    settings: S.settings
  };
  COLS.forEach(t => e[t] = S[t]), lsSet(LSK, e);
}

let savingN = 0;

function setSaving(e) {
  savingN += e;
  const t = $("#saving");
  t && (t.textContent = savingN > 0 ? "Saving…" : "Saved"), clearTimeout(setSaving.t), 
  savingN <= 0 && (setSaving.t = setTimeout(() => {
    t && (t.textContent = "");
  }, 1800));
}

const chains = {};

function refFor(e, t) {
  return e === "settings" ? ROOT.collection("meta").doc("settings") : ROOT.collection(e).doc(t);
}

function put(e, t, {silent: a} = {}) {
  t = JSON.parse(JSON.stringify(t));
  const n = (new Date).toISOString();
  t.user_id = S.uid, t.updated_at = n, t.created_at = t.created_at || n;
  const s = e === "settings" ? null : S[e].find(i => i.id === t.id) || null;
  if (e === "settings") S.settings = t; else {
    const i = S[e], o = i.findIndex(r => r.id === t.id);
    o >= 0 ? i[o] = t : i.push(t);
  }
  if (S.mode === "cloud") {
    const i = refFor(e, t.id), o = i.path;
    setSaving(1), chains[o] = (chains[o] || Promise.resolve()).then(() => i.set(t)).catch(r => toast(saveErr(r))).finally(() => setSaving(-1));
  } else if (S.mode === "server") {
    const i = e + "/" + t.id;
    setSaving(1), chains[i] = (chains[i] || Promise.resolve()).then(() => srvSend(e, t.id, t)).catch(o => {
      if (o.status === 402) {
        const r = S[e], c = r.findIndex(l => l.id === t.id);
        s ? c >= 0 && (r[c] = s) : c >= 0 && r.splice(c, 1), delete drafts[e + "/" + t.id], 
        scheduleRender(), window.SweepBilling && SweepBilling.handleApiError(o.data);
        return;
      }
      toast(saveErr(o));
    }).finally(() => setSaving(-1));
  } else saveLocal(), setSaving(0);
  return a || scheduleRender(), t;
}

function remove(e, t) {
  if (S[e] = S[e].filter(a => a.id !== t), S.mode === "cloud") {
    const a = refFor(e, t), n = a.path;
    setSaving(1), chains[n] = (chains[n] || Promise.resolve()).then(() => a.delete()).catch(s => toast(saveErr(s))).finally(() => setSaving(-1));
  } else if (S.mode === "server") {
    const a = e + "/" + t;
    setSaving(1), chains[a] = (chains[a] || Promise.resolve()).then(() => srvSend(e, t, null)).catch(n => toast(saveErr(n))).finally(() => setSaving(-1));
  } else saveLocal();
  scheduleRender();
}

async function bulkPut(e, t) {
  for (const a of t) {
    const n = JSON.parse(JSON.stringify(a)), s = (new Date).toISOString();
    if (n.user_id = S.uid, n.created_at = n.created_at || s, n.updated_at = s, S.mode === "server" && await srvSend(e, n.id, n), 
    S.mode === "cloud") try {
      await refFor(e, n.id).set(n);
    } catch (r) {
      if (r.code === "resource_exhausted") await new Promise(c => setTimeout(c, 1200)), 
      await refFor(e, n.id).set(n); else throw r;
    }
    if (e === "settings") {
      S.settings = n;
      continue;
    }
    const i = S[e], o = i.findIndex(r => r.id === n.id);
    o >= 0 ? i[o] = n : i.push(n);
  }
  S.mode === "local" && saveLocal();
}

async function bulkDel(e, t) {
  for (const a of t) S.mode === "cloud" ? await refFor(e, a).delete() : S.mode === "server" && await srvSend(e, a, null), 
  S[e] = S[e].filter(n => n.id !== a);
  S.mode === "local" && saveLocal();
}

function saveErr(e) {
  return e && e.code === "quota_exceeded" ? "Storage is full — delete some records to add more." : "Could not save: " + (e && e.message || "unknown error");
}

const drafts = {}, dtimers = {};

function getDoc(e, t) {
  return drafts[e + "/" + t] || (e === "settings" ? S.settings : S[e].find(a => a.id === t));
}

function editDoc(e, t, a, {delay: n = 0, init: s} = {}) {
  const i = e + "/" + t;
  let o = drafts[i];
  if (!o) {
    const c = getDoc(e, t);
    o = c ? structuredClone(c) : s ? s() : {
      id: t
    }, drafts[i] = o;
  }
  a(o), dtimers[i] && clearTimeout(dtimers[i].t);
  const r = () => {
    delete drafts[i], delete dtimers[i], put(e, o, {
      silent: !!n
    });
  };
  n ? (dtimers[i] = {
    t: setTimeout(r, n),
    flush: r
  }, setSaving(0)) : r();
}

function flushDrafts() {
  for (const e in dtimers) {
    const t = dtimers[e];
    clearTimeout(t.t), t.flush();
  }
}

addEventListener("pagehide", flushDrafts), document.addEventListener("visibilitychange", () => {
  document.visibilityState === "hidden" && flushDrafts();
});

const acct = e => S.accounts.find(t => t.id === e), firm = e => S.firms.find(t => t.id === e), acctName = e => {
  const t = acct(e);
  return t ? t.name : "—";
}, acctLabel = e => {
  const t = acct(e);
  if (!t) return "—";
  const a = firm(t.firm_id);
  return (a ? a.name + " — " : "") + t.name;
}, tickC = e => instOf(e.instrument).tickC, ticks = (e, t) => Math.round(Number(e) / instOf(t).tick), tNet = e => (e.pnl_c || 0) - (e.fees_c || 0);

function calcPnl(e, t, a, n, s) {
  if (t === "" || a === "" || t == null || a == null || !n) return null;
  const i = Number(t), o = Number(a);
  return !isFinite(i) || !isFinite(o) ? null : (ticks(o, s) - ticks(i, s)) * (e === "short" ? -1 : 1) * Math.round(Number(n)) * instOf(s).tickC;
}

function tRisk(e) {
  return e.risk_c > 0 ? e.risk_c : e.stop != null && e.stop !== "" && e.entry != null && e.entry !== "" && Math.abs(ticks(e.entry, e.instrument) - ticks(e.stop, e.instrument)) * tickC(e) * (e.contracts || 0) || null;
}

function tR(e) {
  if (e.r_mult != null && e.r_mult !== "" && isFinite(e.r_mult)) return Number(e.r_mult);
  const t = tRisk(e);
  return t ? tNet(e) / t : null;
}

function tDisc(e) {
  const t = e.discipline || {};
  let a = 0, n = 0;
  for (const s in t) t[s] === "y" ? (a++, n++) : t[s] === "n" && n++;
  return n ? a / n * 100 : null;
}

const tkey = e => e.date + " " + (e.entry_time || "99:99") + " " + (e.created_at || ""), sorted = e => e.slice().sort((t, a) => {
  const n = tkey(t), s = tkey(a);
  return n < s ? -1 : n > s ? 1 : 0;
});

function dayMap(e) {
  const t = new Map;
  for (const a of e) {
    let n = t.get(a.date);
    n || (n = {
      date: a.date,
      net: 0,
      n: 0,
      trades: [],
      dS: 0,
      dN: 0
    }, t.set(a.date, n)), n.net += tNet(a), n.n++, n.trades.push(a);
    const s = tDisc(a);
    s != null && (n.dS += s, n.dN++);
  }
  for (const a of t.values()) a.disc = a.dN ? a.dS / a.dN : null;
  return t;
}

function stats(e) {
  const t = {
    n: e.length,
    wins: 0,
    losses: 0,
    be: 0,
    gp: 0,
    gl: 0,
    net: 0,
    best: null,
    worst: null,
    rS: 0,
    rN: 0,
    dS: 0,
    dN: 0,
    qty: 0
  };
  for (const u of e) {
    const h = tNet(u);
    t.net += h, t.qty += u.contracts || 0, h > 0 ? (t.wins++, t.gp += h) : h < 0 ? (t.losses++, 
    t.gl += h) : t.be++, (!t.best || h > tNet(t.best)) && (t.best = u), (!t.worst || h < tNet(t.worst)) && (t.worst = u);
    const m = tR(u);
    m != null && (t.rS += m, t.rN++);
    const v = tDisc(u);
    v != null && (t.dS += v, t.dN++);
  }
  const a = t.wins + t.losses;
  t.wr = a ? t.wins / a : null, t.lr = a ? t.losses / a : null, t.pf = t.gl ? t.gp / -t.gl : t.gp > 0 ? 1 / 0 : null, 
  t.avgWin = t.wins ? t.gp / t.wins : null, t.avgLoss = t.losses ? t.gl / t.losses : null, 
  t.avg = t.n ? t.net / t.n : null, t.exp = a ? t.wr * (t.avgWin || 0) + t.lr * (t.avgLoss || 0) : null, 
  t.rr = t.avgWin != null && t.avgLoss ? t.avgWin / -t.avgLoss : null, t.avgR = t.rN ? t.rS / t.rN : null, 
  t.disc = t.dN ? t.dS / t.dN : null, t.avgQty = t.n ? t.qty / t.n : null;
  const n = dayMap(e);
  t.days = n, t.winDays = 0, t.lossDays = 0, t.bestDay = null, t.worstDay = null;
  for (const u of n.values()) u.net > 0 ? t.winDays++ : u.net < 0 && t.lossDays++, 
  (!t.bestDay || u.net > t.bestDay.net) && (t.bestDay = u), (!t.worstDay || u.net < t.worstDay.net) && (t.worstDay = u);
  let s = 0, i = null, o = 0, r = 0;
  for (const u of e) {
    const h = tNet(u);
    if (!h) continue;
    const m = h > 0 ? "W" : "L";
    m === i ? s++ : (i = m, s = 1), m === "W" ? o = Math.max(o, s) : r = Math.max(r, s);
  }
  t.streak = i ? {
    type: i,
    n: s
  } : null, t.maxWS = o, t.maxLS = r;
  let c = 0, l = 0, p = 0;
  for (const u of e) c += tNet(u), l = Math.max(l, c), p = Math.min(p, c - l);
  return t.maxDD = p, t;
}

function groupBy(e, t) {
  const a = new Map;
  for (const n of e) for (const s of [].concat(t(n))) s == null || s === "" || (a.has(s) || a.set(s, []), 
  a.get(s).push(n));
  return a;
}

function seq(e) {
  const t = {
    first: [],
    afterLoss: [],
    after2Loss: [],
    afterWin: [],
    beforeFirstLoss: [],
    afterFirstLoss: [],
    daysWithLoss: 0,
    restFirstLose: [],
    restFirstWin: [],
    firstLoseDays: 0,
    firstWinDays: 0,
    days: 0
  };
  for (const a of dayMap(e).values()) {
    const n = a.trades;
    t.days++;
    let s = -1;
    n.forEach((o, r) => {
      r === 0 && t.first.push(o);
      const c = n[r - 1], l = n[r - 2];
      c && (tNet(c) < 0 ? (t.afterLoss.push(o), l && tNet(l) < 0 && t.after2Loss.push(o)) : tNet(c) > 0 && t.afterWin.push(o)), 
      s < 0 && tNet(o) < 0 && (s = r);
    }), s >= 0 && (t.daysWithLoss++, t.beforeFirstLoss.push(...n.slice(0, s + 1)), t.afterFirstLoss.push(...n.slice(s + 1)));
    const i = n[0];
    tNet(i) < 0 ? (t.firstLoseDays++, t.restFirstLose.push(...n.slice(1))) : tNet(i) > 0 && (t.firstWinDays++, 
    t.restFirstWin.push(...n.slice(1)));
  }
  return t;
}

function violations(e) {
  return S.settings.questions.map(t => {
    const a = e.filter(s => (s.discipline || {})[t.id] === "n"), n = stats(a);
    return {
      q: t,
      n: a.length,
      pct: e.length ? a.length / e.length : null,
      net: n.net,
      avg: n.avg,
      avgLoss: n.avgLoss,
      largest: n.worst && tNet(n.worst) < 0 ? tNet(n.worst) : null,
      wr: n.wr
    };
  }).filter(t => t.n > 0).sort((t, a) => t.net - a.net);
}

function acctBalance(e) {
  const t = S.trades.filter(n => n.account_id === e.id).reduce((n, s) => n + tNet(s), 0), a = S.payouts.filter(n => n.account_id === e.id && n.status === "paid").reduce((n, s) => n + (s.amount_c || 0), 0);
  return (e.starting_balance_c || 0) + t - a;
}

const avgQty = e => e.length ? e.reduce((t, a) => t + (a.contracts || 0), 0) / e.length : null, F = Object.assign({
  period: "month",
  from: "",
  to: "",
  account: "all",
  firm: "all",
  session: "all",
  dir: "all",
  inst: "all"
}, lsGet("tj.filters", {})), U = Object.assign({
  eq: "daily",
  more: !1,
  sort: {
    k: "date",
    d: "desc"
  },
  q: "",
  result: "all",
  setup: "all",
  disc: "all",
  tag: "",
  an: "performance",
  bars: "day",
  editP: null,
  editE: null
}, lsGet("tj.ui", {})), saveF = () => lsSet("tj.filters", F), saveU = () => lsSet("tj.ui", U);

function periodRange() {
  const e = todayStr();
  switch (F.period) {
   case "today":
    return [ e, e ];

   case "week":
    {
      const t = weekStart(e);
      return [ t, addDays(t, 6) ];
    }

   case "month":
    return [ monthStart(e), e.slice(0, 7) + "-31" ];

   case "custom":
    return [ F.from || "0000", F.to || "9999" ];

   default:
    return [ "0000", "9999" ];
  }
}

function acctOK(e) {
  if (F.account !== "all" && e.account_id !== F.account) return !1;
  if (F.firm !== "all") {
    const t = acct(e.account_id);
    if (!t || t.firm_id !== F.firm) return !1;
  }
  return !0;
}

function ft({period: e = !0} = {}) {
  const [t, a] = periodRange();
  return mergeCopies(sorted(S.trades.filter(n => acctOK(n) && (!e || n.date >= t && n.date <= a) && (F.session === "all" || n.session === F.session) && (F.dir === "all" || n.direction === F.dir) && (!F.inst || F.inst === "all" || (n.instrument || "NQ") === F.inst) && (typeof mtypeOK != "function" || mtypeOK(n)))));
}

const SYNC_RE = /^(discipline|emo|review|setup|grade|shots|tags|notes)(\.|$)/, SHARED_FIELDS = [ "date", "direction", "entry", "exit", "entry_time", "exit_time", "session", "stop", "target", "setup", "grade", "planned_rr", "tags", "notes" ], copiesOf = e => e && e.copy_group ? S.trades.filter(t => t.copy_group === e.copy_group) : e ? [ e ] : [];

function siblings(e) {
  const t = getDoc("trades", e);
  return t && t.copy_group ? S.trades.filter(a => a.copy_group === t.copy_group && a.id !== e) : [];
}

function syncTrade(e, t, {delay: a = 0} = {}) {
  const n = getDoc("trades", e);
  if (!(!n || !n.copy_group)) for (const s of siblings(e)) editDoc("trades", s.id, i => {
    for (const o of t) {
      const r = getPath(n, o);
      setPath(i, o, r === void 0 ? void 0 : JSON.parse(JSON.stringify(r)));
    }
  }, {
    delay: a
  });
}

const mergeOn = () => S.settings && S.settings.mergeCopies !== !1 && F.account === "all";

function mergeCopies(e) {
  if (!mergeOn()) return e;
  const t = [], a = new Map;
  for (const n of e) {
    if (!n.copy_group) {
      t.push(n);
      continue;
    }
    const s = a.get(n.copy_group);
    if (!s) {
      const o = {
        ...n,
        _copies: [ n ],
        risk_c: tRisk(n) || null
      };
      if (typeof U != "undefined" && U.copyMode === "contract" && (n.contracts || 1) > 1) {
        const c = n.contracts || 1;
        o.pnl_c = Math.round((n.pnl_c || 0) / c), o.fees_c = Math.round((n.fees_c || 0) / c), 
        o.risk_c = o.risk_c != null ? Math.round(o.risk_c / c) : null, o.contracts = 1;
      }
      a.set(n.copy_group, o), t.push(o);
      continue;
    }
    s._copies.push(n);
  }
  return t;
}

const periodLabel = () => ({
  today: "today",
  week: "this week",
  month: "this month",
  all: "all time",
  custom: "the selected range"
}[F.period]);

function langPref() {
  return lsGet("tj.lang", "auto");
}

function detectLang() {
  const e = langPref();
  if (e === "fr" || e === "es" || e === "en") return e;
  for (const t of navigator.languages || [ navigator.language || "en" ]) {
    const a = String(t).slice(0, 2).toLowerCase();
    if (a === "fr" || a === "es") return a;
    if (a === "en") return "en";
  }
  return "en";
}

let LANG = detectLang();

const LOC = () => LANG === "fr" ? "fr-CA" : LANG === "es" ? "es" : "en-US";

document.documentElement.lang = LANG;

const I18N_D = () => (LANG === "fr" ? window.I18N_FR : LANG === "es" ? window.I18N_ES : null) || {}, plw = (e, t, a) => +e == 1 || LANG === "fr" && +e == 0 ? t : a, W = {
  trade: {
    fr: [ "trade", "trades" ],
    es: [ "operación", "operaciones" ]
  },
  account: {
    fr: [ "compte", "comptes" ],
    es: [ "cuenta", "cuentas" ]
  },
  day: {
    fr: [ "jour", "jours" ],
    es: [ "día", "días" ]
  },
  event: {
    fr: [ "annonce", "annonces" ],
    es: [ "evento", "eventos" ]
  },
  contract: {
    fr: [ "contrat", "contrats" ],
    es: [ "contrato", "contratos" ]
  },
  rule: {
    fr: [ "autre règle respectée", "autres règles respectées" ],
    es: [ "otra regla en orden", "otras reglas en orden" ]
  },
  loss: {
    fr: [ "perte", "pertes" ],
    es: [ "pérdida", "pérdidas" ]
  }
}, w = (e, t) => {
  const a = W[e][LANG];
  return `${t} ${plw(t, a[0], a[1])}`;
}, ord = e => LANG === "fr" ? +e == 1 ? "1er" : e + "e" : e + ".º", tr = e => LANG === "en" || e == null ? e : I18N_D()[e] || (trPattern(e) ?? e), T = (e, t) => LANG === "fr" ? e : t, I18N_PAT = [ [ /^(\d+) trades?$/, e => w("trade", e[1]) ], [ /^(\d+) accounts?$/, e => w("account", e[1]) ], [ /^(\d+) days?$/, e => w("day", e[1]) ], [ /^(\d+) events?$/, e => w("event", e[1]) ], [ /^([\d.]+) contracts?$/, e => w("contract", e[1]) ], [ /^(\d+) other rules? on track$/, e => w("rule", e[1]) ], [ /^(.+) won · (.+) lost$/, e => T(`${e[1]} gagnés · ${e[2]} perdus`, `${e[1]} ganadas · ${e[2]} perdidas`) ], [ /^(\d+) trades? · (\d+)% win rate$/, e => `${w("trade", e[1])} · ${T(`${e[2]} % de réussite`, `${e[2]}% de acierto`)}` ], [ /^(\d+) trades? · avg (.+)$/, e => `${w("trade", e[1])} · ${T("moy.", "prom.")} ${e[2]}` ], [ /^(\d+) trades? · (\d+)%$/, e => `${w("trade", e[1])} · ${e[2]}${T(" %", "%")}` ], [ /^(\d+) trades? ·$/, e => `${w("trade", e[1])} ·` ], [ /^(\d+)(st|nd|rd|th)$/, e => ord(e[1]) ], [ /^(\d+)(?:st|nd|rd|th) trade \((\d+) trades\): ([\d.]+) contracts$/, e => T(`${ord(e[1])} trade (${e[2]} trades) : ${e[3]} contrats`, `${ord(e[1])} operación (${e[2]} operaciones): ${e[3]} contratos`) ], [ /^(\d+) days with a loss$/, e => T(`${e[1]} jours avec une perte`, `${e[1]} días con pérdida`) ], [ /^(\d+) of (\d+)$/, e => T(`${e[1]} sur ${e[2]}`, `${e[1]} de ${e[2]}`) ], [ /^(\d+) trades without a completed checklist are excluded from this view\.$/, e => T(`${e[1]} trades sans checklist remplie sont exclus de cette vue.`, `${e[1]} operaciones sin checklist completa se excluyen de esta vista.`) ], [ /^(.+) (after|before) the release$/, e => T(`${e[1]} ${e[2] === "after" ? "après" : "avant"} la publication`, `${e[1]} ${e[2] === "after" ? "después de" : "antes de"} la publicación`) ], [ /^at the release$/, () => T("à la publication", "en la publicación") ], [ /^(\d+)% discipline$/, e => T(`${e[1]} % de discipline`, `${e[1]}% de disciplina`) ], [ /^Added (\d+) sample trades$/, e => T(`${e[1]} trades d'exemple ajoutés`, `${e[1]} operaciones de ejemplo añadidas`) ], [ /^(Asia|London|New York AM|New York PM|Mon|Tue|Wed|Thu|Fri|Sat|Sun): (.+)$/, e => `${tr(e[1])} : ${e[2]}`.replace(" :", LANG === "fr" ? " :" : ":") ], [ /^(Consistency|Discipline|Profit factor|Recovery|Win rate|Win \/ loss): (\d+)\/100$/, e => `${tr(e[1])}${LANG === "fr" ? " :" : ":"} ${e[2]}/100` ], [ /^Below (\d+)%$/, e => T(`Moins de ${e[1]} %`, `Menos de ${e[1]}%`) ], [ /^Discipline < (\d+)%$/, e => T(`Discipline < ${e[1]} %`, `Disciplina < ${e[1]}%`) ], [ /^Discipline ≥ (\d+)%$/, e => T(`Discipline ≥ ${e[1]} %`, `Disciplina ≥ ${e[1]}%`) ], [ /^Good process = discipline ≥ (\d+)%$/, e => T(`Bon processus = discipline ≥ ${e[1]} %`, `Buen proceso = disciplina ≥ ${e[1]}%`) ], [ /^Distance to the (.+) drawdown limit, currently at (.+)\.$/, e => T(`Distance jusqu'à la limite de drawdown (${e[1]}), actuellement à ${e[2]}.`, `Distancia hasta el límite de drawdown (${e[1]}), ahora en ${e[2]}.`) ], [ /^Gross profit ÷ gross loss\. Above 1\.0 (?:is|means) profitable\.$/, () => T("Profit brut ÷ perte brute. Au-dessus de 1,0, c'est rentable.", "Beneficio bruto ÷ pérdida bruta. Por encima de 1,0 es rentable.") ], [ /^(High|Medium) news in (.+)$/, e => T(`Annonce ${e[1] === "High" ? "élevée" : "moyenne"} dans ${e[2]}`, `Noticia ${e[1] === "High" ? "alta" : "media"} en ${e[2]}`) ], [ /^(High|Medium) news (.+) ago$/, e => T(`Annonce ${e[1] === "High" ? "élevée" : "moyenne"} il y a ${e[2]}`, `Noticia ${e[1] === "High" ? "alta" : "media"} hace ${e[2]}`) ], [ /^(High|Medium) impact · (.+)$/, e => `${tr(e[1] + " impact")} · ${e[2]}` ], [ /^(\w+) (Long|Short) · ([\d.]+) contracts?(.*)$/, e => `${e[1]} ${tr(e[2])} · ${w("contract", e[3])}${e[4].replace(" · avg ", T(" · moy. ", " · prom. ")).replace(/ · (\d+) open/, (t, a) => T(` · ${a} ouvert${a > 1 ? "s" : ""}`, ` · ${a} abierto${a > 1 ? "s" : ""}`))}` ], [ /^(\w+) · choose Buy or Sell$/, e => T(`${e[1]} · choisis Achat ou Vente`, `${e[1]} · elige Compra o Venta`) ], [ /^(.+) trades generated (\d+)% of your net profit (.+)\.$/, e => T(`Les trades ${tr(e[1])} ont généré ${e[2]} % de ton profit net ${tr(e[3])}.`, `Las operaciones de ${tr(e[1])} generaron el ${e[2]}% de tu beneficio neto ${tr(e[3])}.`) ], [ /^(.+) is your weakest session: (.+) over (\d+) trades\.$/, e => T(`${tr(e[1])} est ta pire session : ${e[2]} sur ${e[3]} trades.`, `${tr(e[1])} es tu peor sesión: ${e[2]} en ${e[3]} operaciones.`) ], [ /^Trades with Discipline ≥ (\d+)% generated (.+), while trades below (\d+)% generated (.+)\.$/, e => T(`Les trades avec une discipline ≥ ${e[1]} % ont généré ${e[2]}, contre ${e[4]} pour ceux sous ${e[3]} %.`, `Las operaciones con disciplina ≥ ${e[1]}% generaron ${e[2]}, frente a ${e[4]} las de menos de ${e[3]}%.`) ], [ /^Your most expensive rule violation is “(.+)”: (.+) across (\d+) trades\.$/, e => T(`Ton infraction la plus coûteuse est « ${tr(e[1])} » : ${e[2]} sur ${e[3]} trades.`, `Tu infracción más costosa es «${tr(e[1])}»: ${e[2]} en ${e[3]} operaciones.`) ], [ /^Your average loss (increases|decreases) (\d+)% after the first losing trade of the day \((.+) → (.+)\)\.$/, e => T(`Ta perte moyenne ${e[1] === "increases" ? "augmente" : "diminue"} de ${e[2]} % après le premier trade perdant de la journée (${e[3]} → ${e[4]}).`, `Tu pérdida promedio ${e[1] === "increases" ? "aumenta" : "disminuye"} un ${e[2]}% tras la primera operación perdedora del día (${e[3]} → ${e[4]}).`) ], [ /^Your average position size (increases|decreases) (\d+)% after two consecutive losses \((.+) → (.+) contracts\)\.$/, e => T(`Ta taille de position moyenne ${e[1] === "increases" ? "augmente" : "diminue"} de ${e[2]} % après deux pertes consécutives (${e[3]} → ${e[4]} contrats).`, `Tu tamaño de posición promedio ${e[1] === "increases" ? "aumenta" : "disminuye"} un ${e[2]}% tras dos pérdidas seguidas (${e[3]} → ${e[4]} contratos).`) ], [ /^(Long|Short) trades have a higher expectancy than (long|short) trades \((.+) vs (.+) per trade\)\.$/, e => T(`Les trades ${e[1].toLowerCase()} ont une meilleure espérance que les trades ${e[2]} (${e[3]} vs ${e[4]} par trade).`, `Las operaciones ${e[1] === "Long" ? "largas" : "cortas"} tienen mayor esperanza que las ${e[2] === "long" ? "largas" : "cortas"} (${e[3]} vs ${e[4]} por operación).`) ], [ /^When you enter feeling “(.+)”, your average trade is (.+) \((.+) total\)\.$/, e => T(`Quand tu entres en te sentant « ${tr(e[1])} », ton trade moyen est de ${e[2]} (${e[3]} au total).`, `Cuando entras sintiéndote «${tr(e[1])}», tu operación promedio es ${e[2]} (${e[3]} en total).`) ], [ /^On days your first trade loses, your remaining trades net (.+) \((.+) win rate\)\.$/, e => T(`Les jours où ton premier trade perd, tes trades suivants rapportent ${e[1]} (${e[2]} de réussite).`, `Los días en que tu primera operación pierde, las siguientes suman ${e[1]} (${e[2]} de acierto).`) ], [ /^Sample: (.+)$/, e => T("Échantillon : ", "Muestra: ") + trSample(e[1]) ], [ /^Small sample \((\d+) trades?\) — treat with caution$/, e => T(`Petit échantillon (${w("trade", e[1])}) — à prendre avec prudence`, `Muestra pequeña (${w("trade", e[1])}) — tomar con cautela`) ], [ /^Statistically supported observations from your trades\. Each needs at least (\d+) trades per group\.$/, e => T(`Observations statistiquement fondées sur tes trades. Chacune nécessite au moins ${e[1]} trades par groupe.`, `Observaciones con respaldo estadístico de tus operaciones. Cada una requiere al menos ${e[1]} operaciones por grupo.`) ], [ /^Not enough data yet\. Insights appear once there are at least (\d+) trades in each group being compared\.$/, e => T(`Pas assez de données pour l'instant. Les analyses apparaissent dès qu'il y a au moins ${e[1]} trades dans chaque groupe comparé.`, `Aún no hay suficientes datos. Los análisis aparecen cuando hay al menos ${e[1]} operaciones en cada grupo comparado.`) ], [ /^(Stop|Target) · (.+)$/, e => `${tr(e[1])} · ${e[2]}` ], [ /^(Entry|Exit|Exit at target|Exit at stop) ([\d.,]+)$/, e => `${tr(e[1])} ${e[2]}` ], [ /^Today · (.+)$/, e => `${tr("Today")} · ${e[1]}` ], [ /^Week of (.+)$/, e => T(`Semaine du ${e[1]}`, `Semana del ${e[1]}`) ], [ /^Within (\d+) min of high-impact news$/, e => T(`À moins de ${e[1]} min d'une annonce à impact élevé`, `A menos de ${e[1]} min de una noticia de impacto alto`) ], [ /^You would have avoided (\d+) trades that netted$/, e => T(`Tu aurais évité ${e[1]} trades qui ont rapporté`, `Habrías evitado ${e[1]} operaciones que sumaron`) ], [ /^Your entry ([\d:]+) ·$/, e => T(`Ton entrée ${e[1]} ·`, `Tu entrada ${e[1]} ·`) ], [ /^avg · (\d+)% win rate · (\d+) (days|trades)$/, e => T(`moy. · ${e[1]} % de réussite · ${e[2]} ${e[3] === "days" ? "jours" : "trades"}`, `prom. · ${e[1]}% de acierto · ${e[2]} ${e[3] === "days" ? "días" : "operaciones"}`) ], [ /^hours with (\d+)\+ trades$/, e => T(`heures avec ${e[1]}+ trades`, `horas con ${e[1]}+ operaciones`) ], [ /^max (\d+)%$/, e => T(`max ${e[1]} %`, `máx. ${e[1]}%`) ], [ /^vs (.+) actual$/, e => T(`vs ${e[1]} réel`, `vs ${e[1]} real`) ], [ /^vs (.+) overall$/, e => T(`vs ${e[1]} au total`, `vs ${e[1]} en general`) ], [ /^vs (\d+)% otherwise$/, e => T(`vs ${e[1]} % sinon`, `vs ${e[1]}% en otro caso`) ], [ /^· (\d+) of (\d+) answered$/, e => T(`· ${e[1]} sur ${e[2]} répondues`, `· ${e[1]} de ${e[2]} respondidas`) ], [ /^· (\d+)% win rate$/, e => T(`· ${e[1]} % de réussite`, `· ${e[1]}% de acierto`) ], [ /^([+−-]?\$[\d,.]+k?) today$/, e => T(`${e[1]} aujourd'hui`, `${e[1]} hoy`) ], [ /^Most frequent: (.+) \((\d+)×\)$/, e => T(`Plus fréquente : ${tr(e[1])} (${e[2]}×)`, `Más frecuente: ${tr(e[1])} (${e[2]}×)`) ], [ /^(Good morning|Good afternoon|Good evening)(, [^·]+)? · (.+)$/, e => `${tr(e[1])}${e[2] || ""} · ${e[3]}` ], [ /^Signed in as (.+) · administrator$/, e => T(`Connecté en tant que ${e[1]} · administrateur`, `Sesión iniciada como ${e[1]} · administrador`) ], [ /^Signed in as (.+)$/, e => T(`Connecté en tant que ${e[1]}`, `Sesión iniciada como ${e[1]}`) ], [ /^of (\d+) max$/, e => T(`sur ${e[1]} max`, `de ${e[1]} máx.`) ], [ /^P&L is calculated from prices \((\w+), \$(\d+(?:\.\d+)?)\/point\) unless you type your own\. Gross, before fees\.$/, e => T(`Le P&L est calculé à partir des prix (${e[1]}, ${e[2]} $/point) sauf si tu le saisis. Brut, avant frais.`, `El P&L se calcula a partir de los precios (${e[1]}, $${e[2]}/punto) salvo que lo escribas. Bruto, antes de comisiones.`) ], [ /^Position open: (\d+) contracts? — add the exit to close it\.$/, e => T(`Position ouverte : ${w("contract", e[1])} — ajoute la sortie pour la fermer.`, `Posición abierta: ${w("contract", e[1])} — añade la salida para cerrarla.`) ], [ /^The position is still open \((\d+) contracts?\)\. Add the exit\.$/, e => T(`La position est encore ouverte (${w("contract", e[1])}). Ajoute la sortie.`, `La posición sigue abierta (${w("contract", e[1])}). Añade la salida.`) ], [ /^Add (.+)\.$/, e => T(`Ajoute ${e[1].replace("an account", "un compte").replace("Buy or Sell", "Achat ou Vente").replace("the entry price", "le prix d'entrée")}.`, `Añade ${e[1].replace("an account", "una cuenta").replace("Buy or Sell", "Compra o Venta").replace("the entry price", "el precio de entrada")}.`) ], [ /^Oversized: (\d+) contracts, your maximum is (\d+)\.$/, e => T(`Position trop grosse : ${e[1]} contrats, ton maximum est ${e[2]}.`, `Sobredimensionada: ${e[1]} contratos, tu máximo es ${e[2]}.`) ], [ /^Copied to (\d+) accounts?$/, e => T(`Copié sur ${w("account", e[1])}`, `Copiado en ${w("account", e[1])}`) ], [ /^Deleted on (\d+) accounts$/, e => T(`Supprimé sur ${e[1]} comptes`, `Eliminado en ${e[1]} cuentas`) ], [ /^Imported (\d+) (trades|events|records)$/, e => T(`${e[1]} ${{
  trades: "trades",
  events: "annonces",
  records: "éléments"
}[e[2]]} importés`, `${e[1]} ${{
  trades: "operaciones",
  events: "eventos",
  records: "registros"
}[e[2]]} importados`) ], [ /^Importing (\d+) trades…$/, e => T(`Importation de ${e[1]} trades…`, `Importando ${e[1]} operaciones…`) ], [ /^Trade saved on (\d+) accounts$/, e => T(`Trade enregistré sur ${e[1]} comptes`, `Operación guardada en ${e[1]} cuentas`) ], [ /^Click the chart to set (\w+)$/, e => T(`Clique sur le graphique pour placer : ${tr(e[1][0].toUpperCase() + e[1].slice(1))}`, `Haz clic en el gráfico para fijar: ${tr(e[1][0].toUpperCase() + e[1].slice(1))}`) ], [ /^Set the (\w+) first$/, e => T(`Place d'abord : ${tr(e[1][0].toUpperCase() + e[1].slice(1))}`, `Fija primero: ${tr(e[1][0].toUpperCase() + e[1].slice(1))}`) ], [ /^Delete this trade on all (\d+) accounts\? This cannot be undone\.$/, e => T(`Supprimer ce trade sur les ${e[1]} comptes ? C'est irréversible.`, `¿Eliminar esta operación en las ${e[1]} cuentas? No se puede deshacer.`) ], [ /^Disable (.+)\? They are signed out and cannot sign in\. Their data is kept\.$/, e => T(`Désactiver ${e[1]} ? Il sera déconnecté et ne pourra plus se connecter. Ses données sont conservées.`, `¿Desactivar a ${e[1]}? Se cerrará su sesión y no podrá entrar. Sus datos se conservan.`) ], [ /^Reset the password of (.+)\? They will be signed out and need the new temporary password\.$/, e => T(`Réinitialiser le mot de passe de ${e[1]} ? Il sera déconnecté et devra utiliser le nouveau mot de passe temporaire.`, `¿Restablecer la contraseña de ${e[1]}? Se cerrará su sesión y necesitará la nueva contraseña temporal.`) ], [ /^Import (\d+) records\? (.+)$/, e => T(`Importer ${e[1]} éléments ? Les éléments ayant le même identifiant sont remplacés ; rien n'est supprimé. Les captures ne font pas partie des exports.`, `¿Importar ${e[1]} registros? Los registros con el mismo id se reemplazan; no se elimina nada. Las capturas no forman parte de las exportaciones.`) ], [ /^(Export failed|Upload failed|Sync stopped): (.*)$/, e => `${T({
  "Export failed": "Échec de l'export",
  "Upload failed": "Échec du téléversement",
  "Sync stopped": "Synchronisation arrêtée"
}[e[1]], {
  "Export failed": "Error al exportar",
  "Upload failed": "Error al subir",
  "Sync stopped": "Sincronización detenida"
}[e[1]])}${LANG === "fr" ? " :" : ":"} ${e[2]}` ], [ /^Uploading (.+)$/, e => T(`Téléversement ${e[1]}`, `Subiendo ${e[1]}`) ], [ /^More about (.+)$/, e => `${tr("More about")} ${e[1]}` ], [ /^Last (\d+) releases$/, e => T(`${e[1]} dernières publications`, `Últimas ${e[1]} publicaciones`) ], [ /^USD · (High|Medium) impact$/, e => `USD · ${tr(e[1] + " impact")}` ], [ /^(\d) of 4 done$/, e => T(`${e[1]} sur 4 complétées`, `${e[1]} de 4 completadas`) ], [ /^Delete all (\d+)$/, e => T(`Tout supprimer (${e[1]})`, `Eliminar todas (${e[1]})`) ], [ /^Copy to (\d*) ?accounts?$/, e => e[1] ? T(`Copier sur ${e[1]} compte${+e[1] > 1 ? "s" : ""}`, `Copiar a ${e[1]} cuenta${+e[1] > 1 ? "s" : ""}`) : T("Copier sur des comptes", "Copiar a cuentas") ], [ /^Copy this trade to other accounts$/, e => T("Copier ce trade sur d’autres comptes", "Copiar esta operación a otras cuentas") ], [ /^Same prices, times and (\d+) contracts? on each account; adjust a copy afterwards if its size differed\. Review, checklist and screenshots stay in sync\.$/, e => T(`Mêmes prix, mêmes heures et ${e[1]} contrat${+e[1] > 1 ? "s" : ""} sur chaque compte ; ajuste une copie ensuite si sa taille était différente. Le bilan, la checklist et les captures restent synchronisés.`, `Mismos precios, horas y ${e[1]} contrato${+e[1] > 1 ? "s" : ""} en cada cuenta; ajusta una copia después si su tamaño era distinto. La revisión, la checklist y las capturas se mantienen sincronizadas.`) ], [ /^This trade is already on every active account\.$/, e => T("Ce trade est déjà sur tous les comptes actifs.", "Esta operación ya está en todas las cuentas activas.") ], [ /^Copied to (\d+) accounts?$/, e => T(`Copié sur ${e[1]} compte${+e[1] > 1 ? "s" : ""}`, `Copiado a ${e[1]} cuenta${+e[1] > 1 ? "s" : ""}`) ], [ /^Deleted on (\d+) accounts$/, e => T(`Supprimé sur ${e[1]} comptes`, `Eliminado en ${e[1]} cuentas`) ], [ /^Welcome, (.+)$/, e => T(`Bienvenue, ${e[1]}`, `Bienvenido, ${e[1]}`) ], [ /^Last 14 days · (.+)$/, e => T(`14 derniers jours · ${e[1]}`, `Últimos 14 días · ${e[1]}`) ], [ /^(\d+) paused accounts?$/, e => T(`${e[1]} compte${e[1] > 1 ? "s" : ""} en pause`, `${e[1]} cuenta${e[1] > 1 ? "s" : ""} en pausa`) ], [ /^Show (\d+) trades?$/, e => T(`Voir ${e[1]} trades`, `Ver ${e[1]} operaciones`) ], [ /^Show (\d+) more$/, e => T(`Afficher ${e[1]} de plus`, `Mostrar ${e[1]} más`) ], [ /^(\d+) not shown$/, e => T(`${e[1]} non affichés`, `${e[1]} sin mostrar`) ], [ /^Economic data: (.+?) · updated (.+?) · Market data: (.+)$/, e => T(`Données économiques : ${tr(e[1])} · mis à jour ${e[2]} · Données de marché : ${tr(e[3])}`, `Datos económicos: ${tr(e[1])} · actualizado ${e[2]} · Datos de mercado: ${tr(e[3])}`) ], [ /^Economic data: (.+) · Market data: (.+)$/, e => T(`Données économiques : ${tr(e[1])} · Données de marché : ${tr(e[2])}`, `Datos económicos: ${tr(e[1])} · Datos de mercado: ${tr(e[2])}`) ], [ /^Previous revised: reported (.+) → now (.+)$/, e => T(`Précédent révisé : publié ${e[1]} → maintenant ${e[2]}`, `Anterior revisado: publicado ${e[1]} → ahora ${e[2]}`) ] ];

function trSample(e) {
  let t;
  return (t = e.match(/^(\d+) vs (\d+) trades$/)) ? T(`${t[1]} vs ${t[2]} trades`, `${t[1]} vs ${t[2]} operaciones`) : (t = e.match(/^(\d+) losses after a first loss$/)) ? T(`${t[1]} pertes après une première perte`, `${t[1]} pérdidas tras una primera pérdida`) : (t = e.match(/^(\d+) trades after two losses$/)) ? T(`${t[1]} trades après deux pertes`, `${t[1]} operaciones tras dos pérdidas`) : (t = e.match(/^(\d+) long, (\d+) short$/)) ? T(`${t[1]} long, ${t[2]} short`, `${t[1]} largas, ${t[2]} cortas`) : (t = e.match(/^(\d+) days, (\d+) trades$/)) ? T(`${t[1]} jours, ${t[2]} trades`, `${t[1]} días, ${t[2]} operaciones`) : tr(e);
}

function trPattern(e) {
  for (const [t, a] of I18N_PAT) {
    const n = e.match(t);
    if (n) try {
      return a(n);
    } catch {
      return null;
    }
  }
  return null;
}

const I18N_ATTRS = [ "placeholder", "title", "aria-label", "data-tip", "data-label" ];

function trText(e) {
  const t = e.match(/^(\s*)([\s\S]*?)(\s*)$/), a = t[2];
  if (!a) return null;
  if (!/[A-Za-z]/.test(a)) {
    const p = pctSp(a);
    return p !== a ? t[1] + p + t[3] : null;
  }
  const n = tr(a);
  return n !== a ? t[1] + pctSp(n) + t[3] : null;
}

function pctSp(e) {
  return e.replace(/(\d)%/g, "$1 %");
}

function translateTree(e) {
  if (LANG === "en" || !e) return;
  if (e.nodeType === 3) {
    const i = trText(e.nodeValue);
    i != null && (e.nodeValue = i);
    return;
  }
  if (e.nodeType !== 1 || e.closest && e.closest("script,style,[data-noi18n]")) return;
  const t = document.createTreeWalker(e, NodeFilter.SHOW_TEXT, {
    acceptNode: i => i.parentElement && i.parentElement.closest("script,style,textarea,[data-noi18n]") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
  }), a = [];
  let n;
  for (;n = t.nextNode(); ) a.push(n);
  for (const i of a) {
    const o = trText(i.nodeValue);
    o != null && (i.nodeValue = o);
  }
  const s = [ e, ...e.querySelectorAll("[" + I18N_ATTRS.join("],[") + "]") ];
  for (const i of s) for (const o of I18N_ATTRS) {
    if (!i.hasAttribute || !i.hasAttribute(o)) continue;
    const r = i.getAttribute(o), c = trText(r);
    c != null && i.setAttribute(o, c);
  }
}

if (LANG !== "en") {
  let e = new Set, t = !1;
  const a = () => {
    t = !1;
    const o = [ ...e ];
    e.clear();
    for (const r of o) r.isConnected && translateTree(r);
  };
  new MutationObserver(o => {
    for (const r of o) if (r.type === "characterData") e.add(r.target); else for (const c of r.addedNodes) e.add(c);
    !t && e.size && (t = !0, queueMicrotask(a));
  }).observe(document.documentElement, {
    childList: !0,
    subtree: !0,
    characterData: !0
  }), document.addEventListener("DOMContentLoaded", () => translateTree(document.body)), 
  document.body && translateTree(document.body);
  const n = window.confirm.bind(window), s = window.alert.bind(window), i = window.prompt.bind(window);
  window.confirm = o => n(tr(String(o))), window.alert = o => s(tr(String(o))), window.prompt = (o, r) => i(tr(String(o)), r);
}

function setLang(e) {
  lsSet("tj.lang", e), location.reload();
}

function niceTicks(e, t, a = 4) {
  const s = (t - e || 1) / a, i = Math.pow(10, Math.floor(Math.log10(s))), o = [ 1, 2, 2.5, 5, 10 ].map(c => c * i).find(c => c >= s) || 10 * i, r = [];
  for (let c = Math.ceil(e / o) * o; c <= t + 1e-9; c += o) r.push(c);
  return r;
}

function smoothPath(e) {
  if (e.length < 3) return e.map((o, r) => (r ? "L" : "M") + o[0].toFixed(1) + " " + o[1].toFixed(1)).join("");
  const t = e.length, a = [], n = [], s = [];
  for (let o = 0; o < t - 1; o++) a[o] = e[o + 1][0] - e[o][0], n[o] = (e[o + 1][1] - e[o][1]) / (a[o] || 1);
  s[0] = n[0], s[t - 1] = n[t - 2];
  for (let o = 1; o < t - 1; o++) s[o] = n[o - 1] * n[o] <= 0 ? 0 : 3 * (a[o - 1] + a[o]) / ((2 * a[o] + a[o - 1]) / n[o - 1] + (a[o] + 2 * a[o - 1]) / n[o]);
  let i = "M" + e[0][0].toFixed(1) + " " + e[0][1].toFixed(1);
  for (let o = 0; o < t - 1; o++) {
    const r = a[o] / 3;
    i += `C${(e[o][0] + r).toFixed(1)} ${(e[o][1] + s[o] * r).toFixed(1)} ${(e[o + 1][0] - r).toFixed(1)} ${(e[o + 1][1] - s[o + 1] * r).toFixed(1)} ${e[o + 1][0].toFixed(1)} ${e[o + 1][1].toFixed(1)}`;
  }
  return i;
}

function lineChart(e, {h: t = 230, label: a = "Cumulative P&L", lab: n = o => o, tone: s = "pos", w: i = 820} = {}) {
  if (e.length < 2) return '<div class="empty">Not enough data yet.</div>';
  const o = i, r = t, c = 52, l = 16, p = 16, u = 28, h = e.map(Y => Y.v);
  let m = Math.min(0, ...h), v = Math.max(0, ...h);
  m === v && (v = m + 100);
  const b = (v - m) * .08;
  m -= m < 0 ? b : 0, v += b;
  const E = Y => c + (o - c - l) * Y / (e.length - 1), R = Y => p + (r - p - u) * (1 - (Y - m) / (v - m));
  let x = niceTicks(m, v).map(Y => `<line class="grid" x1="${c}" x2="${o - l}" y1="${R(Y)}" y2="${R(Y)}"/><text x="${c - 10}" y="${R(Y) + 4}" text-anchor="end">${moneyShort(Y)}</text>`).join("");
  x += `<line class="zero" x1="${c}" x2="${o - l}" y1="${R(0)}" y2="${R(0)}"/>`;
  const C = Math.max(1, Math.ceil(e.length / (o < 600 ? 3 : 6)));
  e.forEach((Y, Q) => {
    Q > 0 && (Q % C === 0 || Q === e.length - 1) && !(Q !== e.length - 1 && e.length - 1 - Q < C / 2) && (x += `<text x="${E(Q)}" y="${r - 8}" text-anchor="${Q === e.length - 1 ? "end" : "middle"}">${esc(n(Y.label))}</text>`);
  });
  const g = e.map((Y, Q) => [ E(Q), R(Y.v) ]), P = smoothPath(g), O = R(Math.max(m, Math.min(0, v))).toFixed(1), H = P + `L${E(e.length - 1).toFixed(1)} ${O}L${E(0).toFixed(1)} ${O}Z`, J = e.at(-1), q = "g" + Math.random().toString(36).slice(2, 8), z = JSON.stringify(e.map((Y, Q) => [ +g[Q][0].toFixed(1), +g[Q][1].toFixed(1), n(Y.label), Y.v, Y.d ?? null ]));
  return `<div class="chartbox ${s}" data-w="${o}" data-pts='${esc(z)}'><svg class="chart" viewBox="0 0 ${o} ${r}" role="img" aria-label="${esc(a)}">\n    <defs><linearGradient id="${q}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgb(var(--${s}-rgb))" stop-opacity="${s === "neg" ? "0" : ".22"}"/><stop offset="1" stop-color="rgb(var(--${s}-rgb))" stop-opacity="${s === "neg" ? ".22" : "0"}"/></linearGradient></defs>\n    ${x}<path class="area" d="${H}" fill="url(#${q})"/><path class="ln glow" d="${P}"/><path class="ln draw" d="${P}" pathLength="1"/>\n    <circle class="endpt" cx="${g.at(-1)[0]}" cy="${g.at(-1)[1]}" r="4"/>\n    <line class="xh" x1="0" x2="0" y1="${p}" y2="${r - u}"/><circle class="xdot" r="5" cx="-10" cy="-10"/></svg><div class="ctip"></div></div>`;
}

function barChart(e, {h: t = 190, fmtV: a = moneyShort, color: n} = {}) {
  if (!e.length) return '<div class="empty">Not enough data yet.</div>';
  const s = 820, i = t, o = 58, r = 10, c = 10, l = 26, p = e.map(L => L.v || 0);
  let u = Math.min(0, ...p), h = Math.max(0, ...p);
  u === h && (h = u + 100);
  const m = L => c + (i - c - l) * (1 - (L - u) / (h - u)), v = (s - o - r) / e.length;
  let E = niceTicks(u, h).map(L => `<line class="grid" x1="${o}" x2="${s - r}" y1="${m(L)}" y2="${m(L)}"/><text x="${o - 8}" y="${m(L) + 4}" text-anchor="end">${a(L)}</text>`).join("");
  E += `<line class="zero" x1="${o}" x2="${s - r}" y1="${m(0)}" y2="${m(0)}"/>`;
  const R = Math.max(1, Math.ceil(e.length / 14));
  return e.forEach((L, x) => {
    const C = L.v || 0, g = o + x * v + v * .18, P = v * .64, O = Math.min(m(C), m(0)), H = Math.max(1, Math.abs(m(C) - m(0)));
    E += `<rect class="${n || (C >= 0 ? "bp" : "bn")}" x="${g}" y="${O}" width="${P}" height="${H}" rx="1.5"><title>${esc(L.title || L.label)}: ${esc(L.tv || a(C))}</title></rect>`, 
    x % R === 0 && (E += `<text x="${o + x * v + v / 2}" y="${i - 8}" text-anchor="middle">${esc(L.label)}</text>`);
  }), `<svg class="chart" viewBox="0 0 ${s} ${i}" role="img">${E}</svg>`;
}

function equitySeries(e, t) {
  const a = new Map;
  for (const i of e) {
    const o = t === "weekly" ? weekStart(i.date) : t === "monthly" ? i.date.slice(0, 7) : i.date;
    a.set(o, (a.get(o) || 0) + tNet(i));
  }
  let n = 0;
  const s = [ {
    label: "",
    v: 0
  } ];
  for (const [i, o] of a) n += o, s.push({
    label: i,
    v: n,
    d: o
  });
  return s;
}

const eqLab = e => t => t ? e === "monthly" ? pd(t + "-01").toLocaleDateString(LOC(), {
  month: "short",
  year: "2-digit"
}) : e === "weekly" ? "Wk " + fdate(t) : fdate(t) : "Start", tip = (e, t) => `<span data-tip="${esc(t)}" tabindex="0">${e}</span>`;

function dcell(e) {
  return e == null ? '<span class="faint">—</span>' : `<span class="dcell">${Math.round(e)}%<span class="dbar"><b style="width:${Math.round(e)}%"></b></span></span>`;
}

function dirTag(e) {
  return e === "long" ? '<span class="tag-l">Long</span>' : e === "short" ? '<span class="tag-s">Short</span>' : "—";
}

const fpx = e => e == null || e === "" ? "—" : Number(e).toFixed(2), isPhone = () => (window.__mqP || (window.__mqP = matchMedia("(max-width: 600px)"))).matches;

function tradeRows(e) {
  return e.map(t => {
    const a = tNet(t), n = [ tradeWhen(t), acctLabel(t.account_id) ].filter(Boolean).map(esc).join(" · ");
    return `<a class="trow" href="#trade/${t.id}"><span class="trow-dir ${t.direction}">${t.direction === "long" ? "L" : "S"}</span><span class="trow-main"><b>${esc(t.instrument || "NQ")} ${t.direction === "long" ? "Long" : "Short"} · ${t.contracts || 0}</b><small>${n}</small></span><span class="trow-pnl ${cls(a)}">${money(a)}</span><span class="trow-go" aria-hidden="true">›</span></a>`;
  }).join("");
}

function tradeTable(e, {compact: t = !1, sortable: a = !1, page: n = 0} = {}) {
  if (!e.length) return '<div class="empty">No trades match these filters.</div>';
  const s = n && e.length > n ? e.length - n : 0;
  s && (e = e.slice(0, n));
  const i = s ? `<div class="more-row"><button class="btn sm" data-act="more-trades">Show ${Math.min(100, s)} more</button><span class="muted">${s} not shown</span></div>` : "";
  if (isPhone()) return `<div class="tlist">${tradeRows(e)}</div>${i}`;
  const o = (l, p, u) => a ? `<th data-sort="${l}" class="${u ? "num" : ""}">${p}${U.sort.k === l ? U.sort.d === "asc" ? " ↑" : " ↓" : ""}</th>` : `<th class="${u ? "num" : ""}">${p}</th>`, r = t ? `<tr>${o("time", "Time")}<th>Account</th><th>Session</th><th>Dir</th><th class="num">Qty</th><th class="num">Entry</th><th class="num">Exit</th><th class="num">P&amp;L</th><th class="num">R</th><th class="num">Discipline</th><th>Setup</th></tr>` : `<tr>${o("date", "Date")}${o("time", "Time")}${o("account", "Account")}${o("session", "Session")}${o("dir", "Dir")}${o("qty", "Qty", 1)}<th class="num">Entry</th><th class="num">Exit</th>${o("pnl", "P&amp;L", 1)}${o("r", "R", 1)}${o("disc", "Discipline", 1)}${o("setup", "Setup")}</tr>`, c = e.map(l => {
    const p = tNet(l);
    return `<tr data-href="#trade/${l.id}" tabindex="0">${t ? "" : `<td>${fdate(l.date)}</td>`}<td class="muted">${esc(tradeTimeOf(l) || "—")}</td><td>${esc(acctLabel(l.account_id))}${l._copies && l._copies.length > 1 ? ` <span class="pill" title="${esc(l._copies.map(u => acctLabel(u.account_id)).join(" · "))}">+${l._copies.length - 1}</span>` : ""}</td><td class="muted">${sessName(l.session)}</td><td>${dirTag(l.direction)}</td><td class="num">${l.contracts || "—"}</td><td class="num muted">${fpx(l.entry)}</td><td class="num muted">${fpx(l.exit)}</td><td class="num ${cls(p)}">${money(p)}</td><td class="num">${rfmt(tR(l))}</td><td class="num">${dcell(tDisc(l))}</td><td class="muted">${esc(l.setup || "")}</td></tr>`;
  }).join("");
  return `<div class="scroll-x"><table class="tbl"><thead>${r}</thead><tbody>${c}</tbody></table></div>${i}`;
}

function acctTable(e, {totals: t = !1} = {}) {
  if (!e.length) return '<div class="empty">No accounts yet. <a href="#accounts">Add an account</a></div>';
  e = acctSortBreachLast(e);
  const a = todayStr(), n = weekStart(a), s = monthStart(a), i = () => ({
    bal: 0,
    today: 0,
    week: 0,
    month: 0,
    all: 0,
    n: 0,
    w: 0,
    l: 0
  }), o = i(), r = e.map(l => {
    const p = S.trades.filter(m => m.account_id === l.id), u = i();
    u.bal = acctBalance(l);
    for (const m of p) {
      const v = tNet(m);
      u.all += v, u.n++, v > 0 ? u.w++ : v < 0 && u.l++, m.date === a && (u.today += v), 
      m.date >= n && (u.week += v), m.date >= s && (u.month += v);
    }
    for (const m in o) o[m] += u[m];
    const h = firm(l.firm_id);
    return `<tr data-href="#account/${l.id}" tabindex="0" ${billFrozen(l.id) ? 'data-frozen class="is-frozen"' : ""}><td>${esc(l.name)}${billBadge(l.id)}${l.status === "archived" ? ' <span class="pill">Archived</span>' : ""}${acctLine(l)}</td><td class="muted">${esc(h ? h.name : "—")}</td><td class="num">${moneyU(u.bal)}</td><td class="num ${cls(u.today)}" data-sfx="${{
      en: " today",
      fr: " aujourd'hui",
      es: " hoy"
    }[LANG]}">${money(u.today)}</td><td class="num ${cls(u.week)}">${money(u.week)}</td><td class="num ${cls(u.month)}">${money(u.month)}</td><td class="num ${cls(u.all)}">${money(u.all)}</td><td class="num">${u.n}</td><td class="num">${pct(u.w + u.l ? u.w / (u.w + u.l) : null)}</td></tr>`;
  }).join(""), c = t && e.length > 1 ? `<tr class="total"><td>All accounts</td><td></td><td class="num">${moneyU(o.bal)}</td><td class="num ${cls(o.today)}" data-sfx="${{
    en: " today",
    fr: " aujourd'hui",
    es: " hoy"
  }[LANG]}">${money(o.today)}</td><td class="num ${cls(o.week)}">${money(o.week)}</td><td class="num ${cls(o.month)}">${money(o.month)}</td><td class="num ${cls(o.all)}">${money(o.all)}</td><td class="num">${o.n}</td><td class="num">${pct(o.w + o.l ? o.w / (o.w + o.l) : null)}</td></tr>` : "";
  return `<div class="scroll-x"><table class="tbl acct-tbl"><thead><tr><th>Account</th><th>Prop firm</th><th class="num">${tip("Balance", "Starting balance + net P&L − paid payouts")}</th><th class="num">Today</th><th class="num">This week</th><th class="num">This month</th><th class="num">All time</th><th class="num">Trades</th><th class="num">Win rate</th></tr></thead><tbody>${r}${c}</tbody></table></div>`;
}

function groupTable(e, t, {min: a = MIN_N, label: n = o => o, showDisc: s = !0, showR: i = !0} = {}) {
  const o = [ ...t ].map(([r, c]) => ({
    k: r,
    s: stats(c)
  }));
  return o.length ? `<div class="scroll-x"><table class="tbl"><thead><tr><th>${e}</th><th class="num">Trades</th><th class="num">Net P&amp;L</th><th class="num">Win rate</th><th class="num">Avg trade</th><th class="num">${tip("Profit factor", "Gross profit ÷ gross loss")}</th>${i ? '<th class="num">Avg R</th>' : ""}${s ? '<th class="num">Discipline</th>' : ""}</tr></thead><tbody>${o.map(({k: r, s: c}) => `<tr class="${c.n < a ? "thin" : ""}" ${c.n < a ? `title="Small sample (${c.n} trades) — treat with caution"` : ""}><td>${esc(n(r))}</td><td class="num">${c.n}</td><td class="num ${c.n < a ? "" : cls(c.net)}">${money(c.net)}</td><td class="num">${pct(c.wr)}</td><td class="num">${money(c.avg)}</td><td class="num">${pf(c.pf)}</td>${i ? `<td class="num">${rfmt(c.avgR)}</td>` : ""}${s ? `<td class="num">${dcell(c.disc)}</td>` : ""}</tr>`).join("")}</tbody></table></div>` : '<div class="empty">Not enough data yet.</div>';
}

function opts(e, t) {
  return e.map(([a, n]) => `<option value="${esc(a)}" ${String(a) === String(t) ? "selected" : ""}>${esc(n)}</option>`).join("");
}

function filterBar({period: e = !0, session: t = !0, dir: a = !0, trades: n = !1} = {}) {
  if (isMobileUI()) return mFilterBar({
    period: e,
    session: t,
    dir: a,
    trades: n
  });
  const s = S.firms.slice().sort((c, l) => c.name.localeCompare(l.name)), i = S.accounts.filter(c => F.firm === "all" || c.firm_id === F.firm), o = [ ...new Set(S.trades.map(c => c.instrument || "NQ")) ].sort(), r = F.account !== "all" || F.firm !== "all" || F.session !== "all" || F.dir !== "all" || F.inst && F.inst !== "all";
  return `<div class="fbars">${e ? '<div class="fbar fb-period">' : ""}\n   ${e ? `<div class="seg" role="group" aria-label="Period">${[ [ "today", "Today" ], [ "week", "This week" ], [ "month", "This month" ], [ "all", "All time" ], [ "custom", "Custom" ] ].map(([c, l]) => `<button data-act="period" data-v="${c}" class="${F.period === c ? "on" : ""}">${l}</button>`).join("")}</div>\n   ${F.period === "custom" ? `<input type="date" data-filter="from" value="${F.from}" aria-label="From"><span class="muted">to</span><input type="date" data-filter="to" value="${F.to}" aria-label="To">` : ""}` : ""}\n   ${e ? "</div>" : ""}<div class="fbar fb-sel">\n   <select data-filter="firm" aria-label="Prop firm">${opts([ [ "all", "All prop firms" ], ...s.map(c => [ c.id, c.name ]) ], F.firm)}</select>\n   <select data-filter="account" aria-label="Account">${opts([ [ "all", "All accounts" ], ...i.map(c => [ c.id, acctLabel(c.id) ]) ], F.account)}</select>\n   ${o.length > 1 || F.inst && F.inst !== "all" ? `<select data-filter="inst" aria-label="Instrument">${opts([ [ "all", "All instruments" ], ...o.map(c => [ c, c ]) ], F.inst || "all")}</select>` : ""}\n   ${t ? `<select data-filter="session" aria-label="Session">${opts([ [ "all", "All sessions" ], ...SESS ], F.session)}</select>` : ""}\n   ${a ? `<select data-filter="dir" aria-label="Direction">${opts([ [ "all", "Long & short" ], [ "long", "Long" ], [ "short", "Short" ] ], F.dir)}</select>` : ""}\n   ${r ? '<button class="link" data-act="clear-filters">Clear filters</button>' : ""}\n  </div></div>`;
}

function checklist(e, t) {
  const a = S.settings.questions.filter(o => o.active || (t.discipline || {})[o.id]), n = tDisc(t), s = t.discipline || {}, i = Object.values(s).filter(o => o).length;
  return `<div class="score"><b>${n == null ? "—" : Math.round(n) + "%"}</b><span class="muted">${tip("Discipline score", "Rules respected ÷ applicable rules. N/A answers are excluded.")}${i ? ` · ${i} of ${a.length} answered` : ""}</span><span style="flex:1"></span><button class="btn sm" data-act="all-yes" data-id="${t.id}">Mark rest as Yes</button></div>\n   <div class="qlist" style="margin-top:8px">${a.map(o => `<div class="q"><span>${esc(o.text)}</span><div class="seg yn" role="group" aria-label="${esc(o.text)}">${[ [ "y", "Yes" ], [ "n", "No" ], [ "na", "N/A" ] ].map(([r, c]) => `<button class="${r} ${s[o.id] === r ? "on" : ""}" data-act="set" data-col="${e}" data-id="${t.id}" data-path="discipline.${o.id}" data-v="${r}">${c}</button>`).join("")}</div></div>`).join("")}</div>`;
}

function chipsFor(e, t, a, n, s) {
  return s = s || [], `<div class="chips">${n.map(i => `<button class="chip ${s.includes(i) ? "on" : ""}" data-act="toggle" data-col="${e}" data-id="${t}" data-path="${a}" data-v="${esc(i)}">${esc(i)}</button>`).join("")}</div>`;
}

function segFor(e, t, a, n, s, i = "") {
  return `<div class="seg ${i}" role="group">${n.map(([o, r]) => `<button class="${esc(o)} ${String(s) === String(o) ? "on" : ""}" data-act="set" data-col="${e}" data-id="${t}" data-path="${a}" data-v="${esc(o)}">${esc(r)}</button>`).join("")}</div>`;
}

function bindTA(e, t, a, n, {rows: s = 2, ph: i = ""} = {}) {
  return `<textarea rows="${s}" data-bind="${e}|${t}|${a}" placeholder="${esc(i)}">${esc(n || "")}</textarea>`;
}

function bindIn(e, t, a, n, {type: s = "text", ph: i = "", kind: o = ""} = {}) {
  return `<input type="${s}" data-bind="${e}|${t}|${a}" ${o ? `data-kind="${o}"` : ""} value="${esc(n ?? "")}" placeholder="${esc(i)}">`;
}

function insights(e) {
  const t = [], a = S.settings.threshold || 90, n = x => x.reduce((C, g) => C + tNet(g), 0), s = e.filter(x => tDisc(x) != null), i = s.filter(x => tDisc(x) >= a), o = s.filter(x => tDisc(x) < a);
  if (i.length >= MIN_N && o.length >= MIN_N) {
    const x = n(i), C = n(o);
    t.push({
      w: Math.abs(x - C),
      tone: C < x ? "dc" : "neg",
      text: `Trades with Discipline ≥ ${a}% generated ${money(x)}, while trades below ${a}% generated ${money(C)}.`,
      n: `${i.length} vs ${o.length} trades`
    });
  }
  const r = violations(e)[0];
  r && r.n >= 3 && r.net < 0 && t.push({
    w: -r.net,
    tone: "neg",
    text: `Your most expensive rule violation is “${r.q.viol}”: ${money(r.net)} across ${r.n} trades.`,
    n: `${r.n} trades`
  });
  const c = seq(e), l = c.beforeFirstLoss.filter(x => tNet(x) < 0), p = c.afterFirstLoss.filter(x => tNet(x) < 0);
  if (l.length >= MIN_N && p.length >= MIN_N) {
    const x = l.reduce((P, O) => P + tNet(O), 0) / l.length, C = p.reduce((P, O) => P + tNet(O), 0) / p.length, g = (C - x) / Math.abs(x);
    Math.abs(g) >= .15 && t.push({
      w: Math.abs(C - x) * p.length,
      tone: g < 0 ? "neg" : "pos",
      text: `Your average loss ${g < 0 ? "increases" : "decreases"} ${Math.round(Math.abs(g) * 100)}% after the first losing trade of the day (${money(x)} → ${money(C)}).`,
      n: `${p.length} losses after a first loss`
    });
  }
  const u = avgQty(e), h = avgQty(c.after2Loss);
  if (c.after2Loss.length >= MIN_N && u) {
    const x = (h - u) / u;
    Math.abs(x) >= .15 && t.push({
      w: Math.abs(x) * 1e4,
      tone: x > 0 ? "neg" : "dc",
      text: `Your average position size ${x > 0 ? "increases" : "decreases"} ${Math.round(Math.abs(x) * 100)}% after two consecutive losses (${u.toFixed(1)} → ${h.toFixed(1)} contracts).`,
      n: `${c.after2Loss.length} trades after two losses`
    });
  }
  const m = groupBy(e, x => x.session), v = stats(e);
  if (v.gp > 0 && e.length >= 10) {
    let x = null;
    for (const [g, P] of m) {
      const O = stats(P);
      P.length >= MIN_N && O.net > 0 && (!x || O.net > x.net) && (x = {
        k: g,
        net: O.net,
        n: P.length
      });
    }
    if (x && v.net > 0) {
      const g = x.net / v.net;
      g >= .5 && t.push({
        w: x.net * .5,
        tone: "dc",
        text: `${sessName(x.k)} trades generated ${Math.round(Math.min(g, 9.99) * 100)}% of your net profit ${periodLabel()}.`,
        n: `${x.n} trades`
      });
    }
    let C = null;
    for (const [g, P] of m) {
      const O = stats(P);
      P.length >= MIN_N && O.net < 0 && (!C || O.net < C.net) && (C = {
        k: g,
        net: O.net,
        n: P.length
      });
    }
    C && t.push({
      w: -C.net,
      tone: "neg",
      text: `${sessName(C.k)} is your weakest session: ${money(C.net)} over ${C.n} trades.`,
      n: `${C.n} trades`
    });
  }
  const b = e.filter(x => x.direction === "long"), E = e.filter(x => x.direction === "short");
  if (b.length >= 10 && E.length >= 10) {
    const x = stats(b), C = stats(E);
    if (x.exp != null && C.exp != null && Math.abs(x.exp - C.exp) >= 1e3) {
      const g = x.exp > C.exp;
      t.push({
        w: Math.abs(x.exp - C.exp) * 5,
        tone: "dc",
        text: `${g ? "Long" : "Short"} trades have a higher expectancy than ${g ? "short" : "long"} trades (${money(g ? x.exp : C.exp)} vs ${money(g ? C.exp : x.exp)} per trade).`,
        n: `${b.length} long, ${E.length} short`
      });
    }
  }
  const R = groupBy(e, x => x.emo && x.emo.before || []);
  let L = null;
  for (const [x, C] of R) {
    if (C.length < MIN_N) continue;
    const g = stats(C);
    g.avg < 0 && (!L || g.avg < L.avg) && (L = {
      k: x,
      avg: g.avg,
      net: g.net,
      n: C.length
    });
  }
  if (L && t.push({
    w: -L.net,
    tone: "neg",
    text: `When you enter feeling “${L.k}”, your average trade is ${money(L.avg)} (${money(L.net)} total).`,
    n: `${L.n} trades`
  }), c.firstLoseDays >= MIN_N && c.restFirstLose.length >= MIN_N) {
    const x = stats(c.restFirstLose);
    x.net < 0 && t.push({
      w: -x.net,
      tone: "neg",
      text: `On days your first trade loses, your remaining trades net ${money(x.net)} (${pct(x.wr)} win rate).`,
      n: `${c.firstLoseDays} days, ${x.n} trades`
    });
  }
  return t.sort((x, C) => C.w - x.w);
}

function insightList(e, t = 99) {
  const a = insights(e).slice(0, t);
  return a.length ? `<ul class="ins">${a.map(n => `<li class="t-${n.tone}"><div>${esc(n.text)}<small>Sample: ${esc(n.n)}</small></div></li>`).join("")}</ul>` : `<div class="empty">Not enough data yet. Stats appear once there are at least ${MIN_N} trades in each group being compared.</div>`;
}

const isMobileUI = () => (window.__mqM || (window.__mqM = matchMedia("(max-width: 860px)"))).matches, FSPEC = {
  period: !0,
  session: !0,
  dir: !0,
  trades: !1
};

function filterDefs({session: e, dir: t, trades: a}) {
  const n = S.firms.slice().sort((c, l) => c.name.localeCompare(l.name)), s = S.accounts.filter(c => F.firm === "all" || c.firm_id === F.firm), i = [ ...new Set(S.trades.map(c => c.instrument || "NQ")) ].sort(), o = S.settings.threshold || 90, r = [ {
    k: "firm",
    src: "F",
    label: "Prop firm",
    all: "all",
    opts: [ [ "all", "All prop firms" ], ...n.map(c => [ c.id, c.name ]) ]
  }, {
    k: "account",
    src: "F",
    label: "Account",
    all: "all",
    opts: [ [ "all", "All accounts" ], ...s.map(c => [ c.id, acctLabel(c.id) ]) ]
  } ];
  if ((i.length > 1 || F.inst && F.inst !== "all") && r.push({
    k: "inst",
    src: "F",
    label: "Instrument",
    all: "all",
    opts: [ [ "all", "All instruments" ], ...i.map(c => [ c, c ]) ]
  }), e && r.push({
    k: "session",
    src: "F",
    label: "Session",
    all: "all",
    opts: [ [ "all", "All sessions" ], ...SESS ]
  }), t && r.push({
    k: "dir",
    src: "F",
    label: "Side",
    all: "all",
    opts: [ [ "all", "Long & short" ], [ "long", "Long" ], [ "short", "Short" ] ]
  }), a) {
    const c = [ ...new Set(S.trades.map(p => p.setup).filter(Boolean)) ].sort(), l = [ ...new Set(S.trades.flatMap(p => p.tags || [])) ].sort();
    r.push({
      k: "result",
      src: "U",
      label: "Result",
      all: "all",
      opts: [ [ "all", "Wins & losses" ], [ "win", "Winning" ], [ "loss", "Losing" ], [ "be", "Breakeven" ] ]
    }), r.push({
      k: "setup",
      src: "U",
      label: "Setup",
      all: "all",
      opts: [ [ "all", "All setups" ], ...c.map(p => [ p, p ]) ]
    }), r.push({
      k: "disc",
      src: "U",
      label: "Discipline",
      all: "all",
      opts: [ [ "all", "Any discipline" ], [ "hi", `Discipline ≥ ${o}%` ], [ "lo", `Discipline < ${o}%` ], [ "none", "Checklist not done" ] ]
    }), l.length && r.push({
      k: "tag",
      src: "U",
      label: "Tags",
      all: "",
      opts: [ [ "", "All tags" ], ...l.map(p => [ p, p ]) ]
    });
  }
  return r.map(c => ({
    ...c,
    val: (c.src === "F" ? F[c.k] : U[c.k]) ?? c.all
  }));
}

function mFilterBar(e) {
  Object.assign(FSPEC, e);
  const a = filterDefs(e).filter(i => String(i.val) !== String(i.all)), n = {
    en: [ [ "today", "Today" ], [ "week", "Week" ], [ "month", "Month" ], [ "all", "All" ], [ "custom", "Custom" ] ],
    fr: [ [ "today", "Jour" ], [ "week", "Semaine" ], [ "month", "Mois" ], [ "all", "Tout" ], [ "custom", "Dates" ] ],
    es: [ [ "today", "Hoy" ], [ "week", "Semana" ], [ "month", "Mes" ], [ "all", "Todo" ], [ "custom", "Fechas" ] ]
  }[LANG];
  return `<div class="mfb">\n    ${e.period ? `<div class="mseg" role="tablist" aria-label="Period" data-noi18n><span class="mseg-thumb" style="--i:${Math.max(0, n.findIndex(i => i[0] === F.period))}"></span>${n.map(([i, o]) => `<button role="tab" data-act="period" data-v="${i}" class="${F.period === i ? "on" : ""}" aria-selected="${F.period === i}">${o}</button>`).join("")}</div>\n      ${F.period === "custom" ? `<div class="mdates"><input type="date" data-filter="from" value="${F.from}" aria-label="From"><span class="muted">→</span><input type="date" data-filter="to" value="${F.to}" aria-label="To"></div>` : ""}` : ""}\n    <div class="mfb-row">${e.trades ? `<label class="msearch"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4-4"/></svg><input type="search" id="search" data-ui="q" value="${esc(U.q)}" placeholder="Search trades" enterkeyhint="search"></label>` : ""}\n      <button class="fbtn ${a.length ? "has" : ""}" data-act="fsheet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M7 12h10M10 18h4"/></svg><span>Filters</span>${a.length ? `<b>${a.length}</b>` : ""}</button></div>\n    ${a.length ? `<div class="mchips">${a.map(i => `<button class="mchip" data-act="fclear" data-k="${i.src}:${i.k}" aria-label="Remove filter"><span>${esc((i.opts.find(o => String(o[0]) === String(i.val)) || [ "", i.val ])[1])}</span><i aria-hidden="true">×</i></button>`).join("")}</div>` : ""}\n  </div>`;
}

function fsheetHtml() {
  const e = filterDefs(FSPEC);
  return `<div class="fs-head"><h2>Filters</h2>${e.filter(a => String(a.val) !== String(a.all)).length ? '<button class="link" data-act="freset">Reset</button>' : ""}</div>\n   <div class="fs-list">${e.map(a => `<label class="fs-row"><span>${a.label}</span><span class="fs-val"><select data-native ${a.src === "F" ? `data-filter="${a.k}"` : `data-ui="${a.k}"`} aria-label="${a.label}">${opts(a.opts, a.val)}</select><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 4l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span></label>`).join("")}</div>\n   ${FSPEC.trades ? '<a class="btn fs-import" href="#import" data-act="fsheet-close">Import CSV</a>' : ""}\n   <button class="btn primary fs-done" data-act="fsheet-close">${FSPEC.trades ? `Show ${fsCount()} trades` : "Done"}</button>`;
}

function fsCount() {
  const e = $(".tstats div:nth-child(3) b");
  return e ? e.textContent : "";
}

function openFSheet() {
  let e = $("#fSheet");
  if (!e) {
    e = document.createElement("aside"), e.id = "fSheet", e.className = "evp fsh", e.setAttribute("aria-label", "Filters"), 
    e.innerHTML = '<div class="evp-in fs-in"></div>', document.body.append(e);
    const t = document.createElement("div");
    t.id = "fScrim", t.className = "evp-scrim", t.addEventListener("click", closeFSheet), 
    document.body.append(t), swipeDismiss(e, {
      scroller: () => e.querySelector(".evp-in"),
      onClose: closeFSheet,
      ignore: "select"
    });
  }
  e.querySelector(".fs-in").innerHTML = fsheetHtml(), requestAnimationFrame(() => {
    e.classList.add("open"), $("#fScrim").classList.add("open"), document.body.classList.add("evp-lock");
  });
}

function closeFSheet() {
  const e = $("#fSheet");
  e && (e.classList.remove("open"), $("#fScrim").classList.remove("open"), document.body.classList.remove("evp-lock"));
}

function refreshFSheet() {
  const e = $("#fSheet");
  e && e.classList.contains("open") && setTimeout(() => {
    e.querySelector(".fs-in").innerHTML = fsheetHtml();
  }, 60);
}

document.addEventListener("change", e => {
  e.target.closest("#fSheet") && refreshFSheet();
});

const ONB_FIRMS = [ "Apex Trader Funding", "Topstep", "Lucid Trading", "Tradeify", "Take Profit Trader", "MyFundedFutures", "Alpha Futures", "Personal account" ];

function onboarding() {
  const e = [ ...new Set([ ...S.firms.map(s => s.name), ...ONB_FIRMS ]) ], t = S.me ? esc(S.me.username) : "", a = (s, i, o) => `<li class="${o ? "on" : ""}"><span>${s}</span>${i}</li>`, n = s => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${s}</svg>`;
  return `<div id="billBanner" class="bill-banner"></div><div class="onb">\n   <section class="onb-main">\n    <p class="onb-eyebrow">${t ? `Welcome, ${t}` : "Welcome to Sweep"}</p>\n    <h2 class="onb-title">Let's set up your first account.</h2>\n    <p class="onb-sub">Every trade belongs to an account. Add the prop firm account (or personal account) you trade, and log your first trade right after.</p>\n    <ol class="onb-steps">${a(1, "Add an account", !0)}${a(2, "Log a trade", !1)}${a(3, "Review it", !1)}</ol>\n    <form data-form="account" data-onb="1" class="onb-form" autocomplete="off">\n      <input type="hidden" name="firm" value="__new"><input type="hidden" name="created" value="${todayStr()}">\n      <label class="f"><span>Prop firm</span><input name="firmName" list="onbFirms" required placeholder="Search or type a firm"><datalist id="onbFirms">${e.map(s => `<option value="${esc(s)}">`).join("")}</datalist></label>\n      <div class="chips onb-chips">${ONB_FIRMS.slice(0, 6).map(s => `<button type="button" class="chip" data-act="onb-firm" data-v="${esc(s)}">${esc(s)}</button>`).join("")}<button type="button" class="chip" data-act="onb-firm" data-v="Personal account">Personal account</button></div>\n      <div class="onb-row">\n        <label class="f"><span>Account name</span><input name="name" required placeholder="e.g. 50K evaluation"></label>\n        <label class="f"><span>Starting balance</span><input name="start" inputmode="decimal" required placeholder="$50,000"></label>\n      </div>\n      <div class="chips onb-chips">${[ 25e3, 5e4, 1e5, 15e4 ].map(s => `<button type="button" class="chip" data-act="onb-bal" data-v="${s}">$${s / 1e3}K</button>`).join("")}</div>\n      <p class="help onb-help">Drawdown, profit target and daily loss limit can be added later in Accounts.</p>\n      <div class="onb-actions"><button class="btn primary" type="submit">Create account</button><button type="button" class="link" data-act="demo">Explore with sample data first</button><span class="err" data-err></span></div>\n    </form>\n   </section>\n   <aside class="onb-side">\n    <h3>What Sweep does for you</h3>\n    <div class="onb-feat">${n('<path d="M9 11l3 3 8-8"/><path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9"/>')}<div><b>Build the habits</b><span>A discipline checklist on every trade, and automatic checks: added to a loser, oversized, stop not respected, risk limit exceeded.</span></div></div>\n    <div class="onb-feat">${n('<path d="M4 19V5"/><path d="M4 19h16"/><path d="M8 15l3-4 3 2 5-6"/>')}<div><b>Find your edge</b><span>Performance score, P&amp;L by session, setup and day, and patterns to watch after a loss.</span></div></div>\n    <div class="onb-feat">${n('<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><path d="M7 15h3"/>')}<div><b>Get paid</b><span>Every prop account with its rules, payouts and expenses. Net = payouts − expenses, kept even after an account ends.</span></div></div>\n    <div class="onb-tip">${n('<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>')}<span>On your phone, add Sweep to your home screen: Safari → Share → Add to Home Screen.</span></div>\n   </aside>\n  </div>`;
}

function kpiRow(e) {
  const t = (a, n, s = "", i = "") => `<div><div class="lbl">${a}</div><div class="val ${s}">${n}</div>${i ? `<div class="sub">${i}</div>` : ""}</div>`;
  return `<div class="kpis">${t("Net P&amp;L", cu(e.net), cls(e.net))}${t(tip("Win rate", "Winning trades ÷ (winning + losing trades). Breakeven trades are excluded."), pct(e.wr), "", e.n ? `${e.wins}W · ${e.losses}L${e.be ? ` · ${e.be} BE` : ""}` : "")}${t("Total trades", e.n)}${t(tip("Profit factor", "Gross profit ÷ gross loss. Above 1.0 means profitable."), pf(e.pf))}${t("Average win", money(e.avgWin), e.avgWin ? "pos" : "")}${t("Average loss", money(e.avgLoss), e.avgLoss ? "neg" : "")}</div>`;
}

function metricsGrid(e) {
  const t = (n, s, i = "") => `<div><span>${n}</span><span class="${i}">${s}</span></div>`, a = n => n ? `${money(n.net)} <span class="faint">${fdate(n.date)}</span>` : "—";
  return `<div class="metrics surface">${t("Gross profit", money(e.gp), e.gp ? "pos" : "")}${t("Gross loss", money(e.gl), e.gl ? "neg" : "")}${t("Winning trades", e.wins)}${t("Losing trades", e.losses)}\n  ${t("Average trade", money(e.avg), cls(e.avg))}${t(tip("Expectancy", "Win rate × average win − loss rate × average loss: what an average trade is expected to make."), money(e.exp), cls(e.exp))}${t(tip("Average R", "Average realized R multiple, where risk is known."), rfmt(e.avgR))}${t(tip("Avg win / avg loss", "Reward-to-risk actually achieved."), e.rr == null ? "—" : decl(e.rr.toFixed(2)))}\n  ${t("Best trade", e.best ? money(tNet(e.best)) : "—", e.best ? cls(tNet(e.best)) : "")}${t("Worst trade", e.worst ? money(tNet(e.worst)) : "—", e.worst ? cls(tNet(e.worst)) : "")}${t("Best day", a(e.bestDay), e.bestDay ? cls(e.bestDay.net) : "")}${t("Worst day", a(e.worstDay), e.worstDay ? cls(e.worstDay.net) : "")}\n  ${t("Winning days", e.winDays)}${t("Losing days", e.lossDays)}${t("Current streak", e.streak ? `${e.streak.n} ${e.streak.type === "W" ? "win" : "loss"}${e.streak.n > 1 ? e.streak.type === "W" ? "s" : "es" : ""}` : "—", e.streak ? e.streak.type === "W" ? "pos" : "neg" : "")}${t(tip("Maximum drawdown", "Largest peak-to-trough decline in cumulative P&L over the selected trades."), money(e.maxDD), e.maxDD ? "neg" : "")}</div>`;
}

function vDashboard() {
  if (!S.accounts.length) return onboarding();
  const e = todayStr(), t = mergeCopies(sorted(S.trades.filter(h => h.date === e && acctOK(h)))), a = stats(t), n = ft(), s = stats(n), i = (h, m, v = "") => `<div><span>${h}</span><span class="${v}">${m}</span></div>`, o = `<section class="surface"><div class="today">\n     <div class="pair hero-pnl">${a.n ? `<button class="hero-share" data-act="share" data-k="day" data-id="${todayStr()}" aria-label="Share today"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg></button>` : ""}<span class="lbl">Today</span><span class="val ${cls(a.net)}">${a.n ? cu(a.net) : "$0"}</span>${a.n && a.net < 0 ? `<a class="down-note" href="#journal/${todayStr()}">Down day. Review it while it's fresh.</a>` : ""}</div>\n     <div class="pair hero-disc">${ring(a.disc, {
    size: 74,
    stroke: 5
  })}<div><span class="lbl">${tip("Discipline", "Average discipline score of today’s trades")}</span><span class="val dc">${a.disc == null ? "—" : cu(a.disc, "pct")}</span></div></div>\n     <div class="minor">${i("Trades", a.n)}${i("Win rate", pct(a.wr))}${i("Best trade", a.best ? money(tNet(a.best)) : "—", a.best ? cls(tNet(a.best)) : "")}${i("Worst trade", a.worst ? money(tNet(a.worst)) : "—", a.worst ? cls(tNet(a.worst)) : "")}<div><span>Journal</span><span><a href="#journal/${e}">${S.journals.find(h => h.id === e) ? "Open" : "Start"}</a></span></div></div>\n   </div><div class="today-trades">${t.length ? tradeTable(t, {
    compact: !0
  }) : '<div class="empty">No trades today. <button class="link" data-act="add-trade">Add a trade</button></div>'}</div></section>`, r = equitySeries(n, U.eq), c = S.mode === "server" && S.me && !S.me.email && !S.me.has_recovery && S.resetMethod !== "off" ? '<div class="surface pad row" style="margin-bottom:16px"><span>Add an email so you can reset your password if you forget it.</span><a class="btn sm" href="#settings" style="margin-left:auto">Add email</a></div>' : "", l = S.accounts.filter(h => h.status !== "archived" && (F.firm === "all" || h.firm_id === F.firm) && (F.account === "all" || h.id === F.account)), p = (new Date).getHours(), u = `<p class="greet">${p < 12 ? "Good morning" : p < 18 ? "Good afternoon" : "Good evening"}${S.me ? ", " + esc(S.me.username) : ""} · ${fdate(todayStr(), {
    weekday: "long",
    month: "long",
    day: "numeric"
  })}</p>`;
  {
    const h = weekStart(todayStr());
    billNudge(S.trades.filter(m => acctOK(m) && m.date >= h && !m.demo).reduce((m, v) => m + tNet(v), 0));
  }
  return `<div id="billBanner" class="bill-banner"></div>${u}${c}${o}\n  ${newsWidget()}\n  <section class="sec"><div class="sec-h"><h2>Accounts</h2><a class="link" href="#accounts">Manage</a></div>${l.length ? `<div class="acards">${l.map(accountCard).join("")}</div>` : '<div class="surface empty">No active accounts.</div>'}</section>\n  <section class="sec">${filterBar()}${kpiRow(s)}\n    <div style="margin-top:8px"><button class="link" data-act="toggle-more">${U.more ? "Hide" : "Show"} more metrics</button></div>\n    ${U.more ? `<div style="margin-top:10px">${metricsGrid(s)}</div>` : ""}</section>\n  <section class="sec cols">\n    <div><div class="sec-h"><h2>Equity curve</h2><div class="seg">${[ [ "daily", "Daily" ], [ "weekly", "Weekly" ], [ "monthly", "Monthly" ] ].map(([h, m]) => `<button data-act="eq" data-v="${h}" class="${U.eq === h ? "on" : ""}">${m}</button>`).join("")}</div></div>\n      <div class="surface pad">${n.length ? lineChart(r, {
    lab: eqLab(U.eq)
  }) : `<div class="empty">No trades ${periodLabel()}.</div>`}</div></div>\n    <div><div class="sec-h"><h2>Performance score</h2></div><div class="surface">${scoreBlock(n)}</div></div>\n  </section>\n  <section class="sec"><div class="sec-h"><h2>Patterns to watch</h2><a class="link" href="#analytics/insights">All stats</a></div><div class="surface">${insightList(n, 4)}</div></section>\n  <section class="sec"><div class="sec-h"><h2>Recent trades</h2><a class="link" href="#trades">All trades</a></div><div class="surface">${n.length ? tradeTable(n.slice(-8).reverse()) : `<div class="empty">${S.trades.length ? `No trades ${periodLabel()}.` : 'No trades yet. <button class="link" data-act="add-trade">Add your first trade</button>'}</div>`}</div></section>\n`;
}

function vTrades() {
  if (!S.accounts.length) return onboarding();
  const e = S.settings.threshold || 90;
  let t = ft();
  const a = [ ...new Set(S.trades.map(r => r.setup).filter(Boolean)) ].sort(), n = [ ...new Set(S.trades.flatMap(r => r.tags || [])) ].sort();
  U.result === "win" ? t = t.filter(r => tNet(r) > 0) : U.result === "loss" ? t = t.filter(r => tNet(r) < 0) : U.result === "be" && (t = t.filter(r => tNet(r) === 0)), 
  U.setup !== "all" && (t = t.filter(r => r.setup === U.setup)), U.disc === "hi" ? t = t.filter(r => tDisc(r) != null && tDisc(r) >= e) : U.disc === "lo" ? t = t.filter(r => tDisc(r) != null && tDisc(r) < e) : U.disc === "none" && (t = t.filter(r => tDisc(r) == null)), 
  U.tag && (t = t.filter(r => (r.tags || []).includes(U.tag)));
  const s = (U.q || "").trim().toLowerCase();
  s && (t = t.filter(r => [ r.setup, r.notes, acctLabel(r.account_id), (r.tags || []).join(" "), sessName(r.session), r.direction, r.date, ...Object.values(r.review || {}) ].join(" ").toLowerCase().includes(s)));
  const i = {
    date: tkey,
    time: r => r.entry_time || "",
    account: r => acctLabel(r.account_id),
    session: r => r.session || "",
    dir: r => r.direction || "",
    qty: r => r.contracts || 0,
    pnl: tNet,
    r: r => tR(r) ?? -1e9,
    disc: r => tDisc(r) ?? -1,
    setup: r => r.setup || ""
  }[U.sort.k] || tkey;
  t.sort((r, c) => {
    const l = i(r), p = i(c);
    return (l < p ? -1 : l > p ? 1 : 0) * (U.sort.d === "asc" ? 1 : -1);
  });
  const o = stats(t);
  return isMobileUI() ? `${filterBar({
    trades: !0
  })}\n  <div class="tstats"><div><span>Net P&amp;L</span><b class="${cls(o.net)}">${money(o.net, {
    dec: 0
  })}</b></div><div><span>Win rate</span><b>${pct(o.wr)}</b></div><div><span>Trades</span><b>${o.n}</b></div></div>\n  <div class="surface">${S.trades.length ? tradeTable(t, {
    sortable: !0,
    page: U.tlimit || 100
  }) : '<div class="empty">No trades yet. Log your first session to start tracking. <button class="link" data-act="add-trade">Add a trade</button></div>'}</div>` : `${filterBar()}\n  <div class="fbar">\n    <input type="text" id="search" data-ui="q" value="${esc(U.q)}" placeholder="Search notes, setups, tags…  ( / )" style="width:260px">\n    <select data-ui="result" aria-label="Result">${opts([ [ "all", "Wins & losses" ], [ "win", "Winning" ], [ "loss", "Losing" ], [ "be", "Breakeven" ] ], U.result)}</select>\n    <select data-ui="setup" aria-label="Setup">${opts([ [ "all", "All setups" ], ...a.map(r => [ r, r ]) ], U.setup)}</select>\n    <select data-ui="disc" aria-label="Discipline">${opts([ [ "all", "Any discipline" ], [ "hi", `Discipline ≥ ${e}%` ], [ "lo", `Discipline < ${e}%` ], [ "none", "Checklist not done" ] ], U.disc)}</select>\n    ${n.length ? `<select data-ui="tag" aria-label="Tag">${opts([ [ "", "All tags" ], ...n.map(r => [ r, r ]) ], U.tag)}</select>` : ""}\n    <a class="btn sm" href="#import">Import CSV</a>\n    <span class="muted tsum" style="margin-left:auto">${o.n} trades · <span class="${cls(o.net)}">${money(o.net)}</span> · ${pct(o.wr)} win rate</span>\n  </div>\n  <div class="tstats"><div><span>Net P&amp;L</span><b class="${cls(o.net)}">${money(o.net, {
    dec: 0
  })}</b></div><div><span>Win rate</span><b>${pct(o.wr)}</b></div><div><span>Trades</span><b>${o.n}</b></div></div>\n  <div class="surface">${S.trades.length ? tradeTable(t, {
    sortable: !0,
    page: U.tlimit || 100
  }) : '<div class="empty">No trades yet. Log your first session to start tracking. <button class="link" data-act="add-trade">Add a trade</button></div>'}</div>`;
}

function vTrade(e) {
  const t = getDoc("trades", e);
  if (!t) return '<div class="empty">This trade no longer exists. <a href="#trades">Back to trades</a></div>';
  const a = sorted(S.trades), n = a.findIndex(g => g.id === e), s = a[n - 1], i = a[n + 1], o = tNet(t), r = tR(t), c = tRisk(t), l = t.emo || {}, p = t.review || {}, u = (g, P) => `<div><span>${g}</span><span>${P}</span></div>`, h = [ [ "why_in", "Why I entered" ], [ "well", "What went well" ], [ "wrong", "What went wrong" ], [ "lesson", "Main lesson" ] ], m = [ [ "thesis", "Trade thesis" ], [ "why_out", "Why I exited" ], [ "differently", "What I would do differently" ] ], v = t.shots || [], b = copiesOf(t), E = S.settings.questions.filter(g => g.active), R = Object.values(t.discipline || {}).filter(Boolean).length, L = [ [ "chk", "Discipline checklist", E.length && R >= E.length ], [ "psy", "Psychology", !!(l.before || []).length ], [ "notes", "Notes", [ ...h, ...m ].some(([g]) => (p[g] || "").trim()) ], [ "shots", "Screenshots", v.length > 0 ] ], x = L.filter(g => g[2]).length, C = (g, P, O, H, J = "") => `<section class="rstep" id="rs-${P}"><div class="rstep-h"><span class="rnum ${L[g - 1][2] ? "ok" : ""}">${L[g - 1][2] ? "✓" : g}</span><h2>${O}</h2>${J}</div><div class="surface pad">${H}</div></section>`;
  return `<div class="tr-top"><a class="link back" href="#trades">‹ Trades</a><span style="flex:1"></span>\n      <div class="seg tr-nav">${s ? `<a href="#trade/${s.id}" title="Previous trade (K)" aria-label="Previous trade">‹</a>` : '<span class="dis">‹</span>'}${i ? `<a href="#trade/${i.id}" title="Next trade (J)" aria-label="Next trade">›</a>` : '<span class="dis">›</span>'}</div>\n      ${aiBtn("ai-feedback", "AI feedback", `data-id="${t.id}"`)}\n      <button class="btn sm" data-act="edit-trade" data-id="${t.id}">Edit trade</button>\n      <details class="menu"><summary class="btn sm" aria-label="More actions">⋯</summary><div class="menu-pop">\n        <button data-act="share" data-k="trade" data-id="${t.id}">Share trade card</button>\n        <button data-act="copy-open" data-id="${t.id}">Copy to accounts</button>\n        ${b.length > 1 ? `<button class="danger" data-act="del-trade" data-id="${t.id}">Delete this copy</button><button class="danger" data-act="del-trade-all" data-id="${t.id}">Delete all ${b.length}</button>` : `<button class="danger" data-act="del-trade" data-id="${t.id}">Delete</button>`}\n      </div></details></div>\n  ${copyPanel(t, b)}${b.length > 1 ? `<div class="surface pad row" style="margin-bottom:14px"><span class="muted">${tip(`Logged on ${b.length} accounts`, "Checklist, emotions, review, setup, grade, tags and screenshots stay in sync on every copy. Contracts, P&L and fees are per account.")}</span>${b.map(g => `<a href="#trade/${g.id}" class="chip ${g.id === t.id ? "on" : ""}" style="text-decoration:none">${esc(acctLabel(g.account_id))} · <span class="${cls(tNet(g))}">${money(tNet(g))}</span></a>`).join("")}<span class="muted" style="margin-left:auto">Total <b class="${cls(b.reduce((g, P) => g + tNet(P), 0))}">${money(b.reduce((g, P) => g + tNet(P), 0))}</b></span></div>` : ""}\n  <section class="surface"><div class="th-head">\n     <div><div class="lbl">${dirTag(t.direction)} · ${t.contracts} ${t.instrument || "NQ"} · ${esc(acctLabel(t.account_id))}</div><div class="big ${cls(o)}">${money(o)}</div></div>\n     <div><div class="lbl">R multiple</div><div style="font-size:18px">${rfmt(r)}</div></div>\n     <div><div class="lbl">Discipline</div><div style="font-size:18px" class="dc">${dpct(tDisc(t))}</div></div>\n     <div><div class="lbl">Grade</div>${segFor("trades", t.id, "grade", GRADES.map(g => [ g, g ]), t.grade)}</div>\n  </div>\n  <div class="tr-chart"><div class="tk-bar"><b>${esc(t.instrument || "NQ")}</b><span class="muted">· ${isEveTrade(t) ? esc(tradeWhen(t)) : fdate(t.date, {
    weekday: "short",
    month: "short",
    day: "numeric"
  })}</span><span style="flex:1"></span><div class="seg">${[ 1, 3, 5, 15 ].map(g => `<button data-act="tr-tf" data-v="${g}" class="${(U.trtf || 1) === g ? "on" : ""}">${g}m</button>`).join("")}</div></div><div class="tchart" id="tradeChart" data-tf="${U.trtf || 1}"></div></div>\n  ${(t.auto_flags || []).length ? `<div class="flags">${t.auto_flags.map(g => `<span class="flag">${esc((AUTO_RULES[g] || {}).label || g)}</span>`).join("")}<span class="help">Detected from the executions — counted in Discipline and rule violations.</span></div>` : ""}\n  <div class="facts">${u("Date", fdate(t.date, {
    month: "short",
    day: "numeric",
    year: "numeric"
  }))}${u("Time", `${esc(tradeTimeOf(t) || "—")} – ${esc(t.exit_time || "—")}`)}${isEveTrade(t) ? u({
    fr: "Séance",
    es: "Sesión"
  }[LANG] || "Session day", esc(tradeWhen(t))) : ""}${u("Duration", fdur(tDur(t)))}${u("Session", sessName(t.session))}${u("Setup", esc(t.setup || "—"))}\n     ${u("Entry", fpx(t.entry))}${u("Exit", fpx(t.exit))}${u("Stop", fpx(t.stop))}${u("Target", fpx(t.target))}\n     ${u("Gross P&amp;L", money(t.pnl_c))}${u("Fees", money(t.fees_c ? -t.fees_c : 0))}${u("Risk", c ? moneyU(c) : "—")}${u("Planned R:R", t.planned_rr ? esc(t.planned_rr) : "—")}\n     ${u("Tags", (t.tags || []).length ? esc(t.tags.join(", ")) : "—")}${u("Notes", t.notes ? `<span class="muted" style="white-space:normal;text-align:right">${esc(t.notes)}</span>` : "—")}</div><div style="height:8px"></div></section>\n  <div class="rprog"><div><b>Review</b><span class="muted">${x} of 4 done</span></div><div class="rprog-steps">${L.map(([g, P, O], H) => `<a href="#rs-${g}" data-act="jump" data-v="rs-${g}" class="${O ? "ok" : ""}"><span>${O ? "✓" : H + 1}</span>${P}</a>`).join("")}</div></div>\n  <div class="tr-grid">\n    <div class="tr-main">\n      ${C(1, "chk", "Discipline checklist", checklist("trades", t))}\n      ${C(2, "psy", "Psychology", `<div class="prompt"><label>Emotional state</label>${chipsFor("trades", t.id, "emo.before", EMO, l.before)}</div>\n        <div class="fgrid" style="margin-top:6px">${[ [ "confidence", "Confidence" ], [ "execution", "Execution quality" ] ].map(([g, P]) => `<div class="f"><span>${P}</span>${segFor("trades", t.id, "emo." + g, [ 1, 2, 3, 4, 5 ].map(O => [ O, O ]), l[g])}</div>`).join("")}</div>`)}\n      ${C(3, "notes", "Notes", `${h.map(([g, P]) => `<div class="prompt"><label>${P}</label>${bindTA("trades", t.id, "review." + g, p[g])}</div>`).join("")}\n        <details class="more"><summary>More questions</summary>${m.map(([g, P]) => `<div class="prompt"><label>${P}</label>${bindTA("trades", t.id, "review." + g, p[g])}</div>`).join("")}</details>`, '<span class="help">Saves as you type</span>')}\n      ${C(4, "shots", "Screenshots", `${ASSETS ? v.length ? `<div class="shots">${v.map(g => `<figure class="shot" style="margin:0"><img src="${esc(blobSrc(g.id))}" alt="${esc(g.name || "Screenshot")}" data-act="zoom" loading="lazy"><figcaption><span>${esc(g.name || "")}</span><button class="link" data-act="del-shot" data-id="${t.id}" data-v="${esc(g.id)}">Remove</button></figcaption></figure>`).join("")}</div>` : '<div class="muted">No screenshots yet.</div>' : '<div class="muted">Screenshots need the server version of the journal (see the README). In browser-only mode they are not stored.</div>'}`, ASSETS ? `<label class="btn sm" style="margin-left:auto">Upload<input type="file" accept="image/*" multiple data-upload="${t.id}" hidden></label>` : "")}\n    </div>\n    <aside class="tr-side">\n      <div class="sec-h"><h2>Setup &amp; costs</h2><button class="link ai-only ai-link" data-act="ai-suggest" data-id="${t.id}"><span class="ai-sp" aria-hidden="true">✦</span>Suggest setup</button></div>\n      <div class="surface pad"><div class="fgrid one">\n        <label class="f"><span>Setup</span><input list="trSetups" data-bind="trades|${t.id}|setup" value="${esc(t.setup || "")}" placeholder="e.g. Opening range"><datalist id="trSetups">${[ ...new Set([ ...S.settings.setups || [], ...S.trades.map(g => g.setup).filter(Boolean) ]) ].map(g => `<option value="${esc(g)}">`).join("")}</datalist></label>\n        <label class="f"><span>Fees &amp; commissions</span>${bindIn("trades", t.id, "fees_c", t.fees_c != null ? (t.fees_c / 100).toFixed(2) : "", {
    kind: "money",
    ph: "$"
  })}</label>\n        <label class="f"><span>Tags <span class="help">· comma separated</span></span>${bindIn("trades", t.id, "tags", (t.tags || []).join(", "), {
    kind: "tags",
    ph: "news, A+"
  })}</label>\n      </div></div>\n      <div class="sec-h"><h2>Economic context</h2></div><div class="surface pad news-ctx" id="newsCtx">${t.news !== void 0 ? newsBlock(t) : '<span class="muted">Save this trade from the ticket to attach nearby economic events automatically.</span>'}</div>\n      ${(t.executions || []).length > 2 ? `<div class="sec-h"><h2>Executions</h2></div><div class="surface" style="margin-bottom:24px"><table class="tbl"><thead><tr><th>Time (ET)</th><th>Side</th><th class="num">Qty</th><th class="num">Price</th></tr></thead><tbody>${t.executions.map(g => `<tr><td class="muted">${esc(g.t.slice(11, 19))}</td><td>${g.side === "buy" ? '<span class="tag-l">Buy</span>' : '<span class="tag-s">Sell</span>'}</td><td class="num">${g.qty}</td><td class="num">${(+g.price).toFixed(2)}</td></tr>`).join("")}</tbody></table></div>` : ""}\n    </aside>\n  </div>`;
}

const CP = {
  id: null,
  sel: new Set
};

function copyPanel(e, t) {
  if (CP.id !== e.id) return "";
  const a = new Set(t.map(s => s.account_id)), n = S.accounts.filter(s => s.status !== "archived" && !a.has(s.id));
  return `<div class="surface pad" style="margin-bottom:14px;border-color:var(--disc)"><h3 style="margin-bottom:8px">Copy this trade to other accounts</h3>\n   ${n.length ? `<div class="chips">${n.map(s => `<button type="button" class="chip ${CP.sel.has(s.id) ? "on" : ""}" data-act="copy-pick" data-v="${s.id}">${esc(acctLabel(s.id))}</button>`).join("")}</div>\n   <p class="help" style="margin:8px 0 0">Same prices, times and ${e.contracts} contract${e.contracts > 1 ? "s" : ""} on each account; adjust a copy afterwards if its size differed. Review, checklist and screenshots stay in sync.</p>\n   <div class="row" style="margin-top:12px"><button class="btn primary sm" data-act="copy-do" data-id="${e.id}" ${CP.sel.size ? "" : "disabled"}>Copy to ${CP.sel.size || ""} account${CP.sel.size === 1 ? "" : "s"}</button><button class="link" data-act="copy-close">Cancel</button></div>` : '<p class="muted" style="margin:0">This trade is already on every active account. <button class="link" data-act="copy-close">Close</button></p>'}</div>`;
}

function vJournal(e) {
  const t = `<div class="tabs"><a href="#journal/${todayStr()}" class="${e !== "weekly" && !(e || "").startsWith("w") ? "on" : ""}">Daily</a><a href="#journal/weekly" class="${e === "weekly" || (e || "").startsWith("w") ? "on" : ""}">Week</a></div>`;
  if (e === "weekly" || (e || "").startsWith("w")) return t + vWeekly(e === "weekly" ? weekStart(todayStr()) : e.slice(1));
  const a = /^\d{4}-\d{2}-\d{2}$/.test(e || "") ? e : todayStr(), n = dayMap(mergeCopies(sorted(S.trades.filter(acctOK)))), s = [ ...new Set([ todayStr(), ...n.keys(), ...S.journals.map(m => m.id) ]) ].sort().reverse().slice(0, 40);
  s.includes(a) || s.unshift(a);
  const i = s.map(m => {
    const v = n.get(m);
    return `<a href="#journal/${m}" class="${m === a ? "on" : ""}"><span>${fdate(m, {
      weekday: "short",
      month: "short",
      day: "numeric"
    })}</span><span class="${v ? cls(v.net) : "faint"}">${v ? moneyShort(v.net) : S.journals.find(b => b.id === m) ? "·" : ""}</span></a>`;
  }).join(""), o = getDoc("journals", a) || {}, r = o.pre || {}, c = o.post || {}, l = n.get(a), p = stats(l ? l.trades : []), u = (m, v, b) => bindTA("journals", a, m, v, b), h = (m, v) => `<div class="prompt"><label>${m}</label>${v}</div>`;
  return `${t}<div class="jlayout">\n    <div class="jside"><input type="date" data-act-change="goto-journal" value="${a}" aria-label="Go to date" style="width:100%;margin-bottom:10px"><div class="jlist">${i}</div></div>\n    <div class="jstrip" data-noi18n>${s.slice().reverse().map(m => {
    const v = n.get(m), b = pd(m);
    return `<a href="#journal/${m}" class="${m === a ? "on" : ""}"><small>${b.toLocaleDateString(LOC(), {
      weekday: "short"
    })}</small><b>${b.getDate()}</b><i class="${v ? cls(v.net) : "none"}"></i></a>`;
  }).join("")}<label class="jpick" aria-label="Go to date"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><rect x="3.5" y="5" width="17" height="15" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg><input type="date" data-act-change="goto-journal" value="${a}"></label></div>\n    <div>\n      <div class="row" style="margin-bottom:14px"><h2 style="font-size:15px">${fdateL(a)}</h2><span class="help" style="margin-left:auto">Saves as you type</span>${aiBtn("ai-day", "Debrief my day", `data-v="${a}"`)}${l ? shareBtn("day", a, "Share") : ""}</div>\n      <div class="statline"><div><span>Daily P&amp;L</span><span class="${cls(p.net)}">${p.n ? money(p.net) : "—"}</span></div><div><span>Trades</span><span>${p.n}</span></div><div><span>Win rate</span><span>${pct(p.wr)}</span></div><div><span>Discipline</span><span class="dc">${dpct(p.disc)}</span></div>${r.max_loss && p.net < 0 && -p.net > parseMoney(r.max_loss) ? '<div><span>Daily loss limit</span><span class="neg">Exceeded</span></div>' : ""}${r.max_trades && p.n > Number(r.max_trades) ? `<div><span>Max trades</span><span class="neg">Exceeded (${p.n}/${esc(r.max_trades)})</span></div>` : ""}</div>\n      <section style="margin-bottom:28px"><div class="sec-h"><h2>Trades</h2><button class="link" data-act="add-trade" data-date="${a}">Add trade for this day</button></div><div class="surface">${l ? tradeTable(l.trades, {
    compact: !0
  }) : '<div class="empty">No trades on this day.</div>'}</div></section>\n      <div class="cols even">\n        <section><div class="sec-h"><h2>Pre-market</h2></div><div class="surface pad">\n          ${h("Market bias", segFor("journals", a, "pre.bias", [ [ "bullish", "Bullish" ], [ "bearish", "Bearish" ], [ "neutral", "Neutral" ], [ "no_trade", {
    fr: "Pas de trade",
    es: "Sin operar"
  }[LANG] || "No trade" ] ], r.bias))}${typeof journalSetupsHtml == "function" ? h({
    fr: "Setups prévus",
    es: "Setups previstos"
  }[LANG] || "Planned setups", journalSetupsHtml(a, r.setups || [])) : ""}\n          ${h("Key levels", u("pre.levels", r.levels, {
    ph: "e.g. PDH 21,480 · ONL 21,310"
  }))}\n          ${h("Expected scenario", u("pre.scenario", r.scenario))}\n          ${h("Alternative scenario", u("pre.alt", r.alt))}\n          ${h("Economic events", u("pre.events", r.events, {
    rows: 1
  }))}\n          ${h("Trading plan", u("pre.plan", r.plan))}\n          <div class="fgrid two" style="margin-bottom:12px"><div class="f"><span>Max daily loss</span>${bindIn("journals", a, "pre.max_loss", r.max_loss, {
    ph: "$"
  })}</div><div class="f"><span>Max number of trades</span>${bindIn("journals", a, "pre.max_trades", r.max_trades, {
    type: "number"
  })}</div></div>\n          ${h("Personal focus for today", bindIn("journals", a, "pre.focus", r.focus, {
    ph: "Do not add to losing positions."
  }))}\n        </div></section>\n        <section><div class="sec-h"><h2>Post-market</h2></div><div class="surface pad">\n          ${h("Did I follow my plan?", segFor("journals", a, "post.followed", [ [ "yes", "Yes" ], [ "partly", "Partly" ], [ "no", "No" ] ], c.followed))}\n          ${h("What went well?", u("post.well", c.well))}\n          ${h("What went wrong?", u("post.wrong", c.wrong))}\n          ${h("What triggered my mistakes?", u("post.triggers", c.triggers))}\n          ${h("Main lesson from today", u("post.lesson", c.lesson))}\n          ${h("What will I do differently tomorrow?", u("post.tomorrow", c.tomorrow))}\n          ${h("Daily grade", segFor("journals", a, "post.grade", GRADES.map(m => [ m, m ]), c.grade))}\n        </div></section>\n      </div>\n\n    </div></div>`;
}

function vWeekly(e) {
  e = weekStart(e);
  const t = addDays(e, 6), a = mergeCopies(sorted(S.trades.filter(p => acctOK(p) && p.date >= e && p.date <= t))), n = stats(a), s = violations(a)[0], i = [ ...groupBy(a, p => p.session) ].map(([p, u]) => ({
    k: p,
    net: stats(u).net,
    n: u.length
  })).sort((p, u) => u.net - p.net), r = (getDoc("weekly", e) || {}).answers || {}, c = (p, u, h = "") => `<div><span>${p}</span><span class="${h}">${u}</span></div>`, l = [ [ "worked", "What worked this week?" ], [ "hurt", "What hurt my performance?" ], [ "repeated", "What behavior repeated itself?" ], [ "stop", "What should I stop doing?" ], [ "continue", "What should I continue doing?" ], [ "focus", "What is my primary focus next week?" ] ];
  return `<div class="row" style="margin-bottom:14px"><a class="btn sm" href="#journal/w${addDays(e, -7)}">Previous week</a><h2 style="font-size:15px;padding:0 8px">Week of ${fdate(e, {
    month: "long",
    day: "numeric",
    year: "numeric"
  })}</h2>${aiBtn("ai-review", "AI review", 'style="margin-left:auto"')}${a.length ? shareBtn("week", e, "Share") : ""}<a class="btn sm" href="#journal/w${addDays(e, 7)}">Next week</a></div>\n  ${F.account !== "all" || F.firm !== "all" ? `<p class="help">Filtered to ${esc(F.account !== "all" ? acctLabel(F.account) : firm(F.firm)?.name || "")}. <button class="link" data-act="clear-filters">Show all accounts</button></p>` : ""}\n  ${a.length ? `<div class="metrics surface" style="margin-bottom:24px">${c("Weekly P&amp;L", money(n.net), cls(n.net))}${c("Trades", n.n)}${c("Win rate", pct(n.wr))}${c("Profit factor", pf(n.pf))}\n   ${c("Average R", rfmt(n.avgR))}${c("Average discipline", dpct(n.disc), "dc")}${c("Best trade", n.best ? `<a href="#trade/${n.best.id}">${money(tNet(n.best))}</a>` : "—", n.best ? cls(tNet(n.best)) : "")}${c("Worst trade", n.worst ? `<a href="#trade/${n.worst.id}">${money(tNet(n.worst))}</a>` : "—", n.worst ? cls(tNet(n.worst)) : "")}\n   ${c("Best day", n.bestDay ? `${money(n.bestDay.net)} <span class="faint">${fdate(n.bestDay.date, {
    weekday: "short"
  })}</span>` : "—", n.bestDay ? cls(n.bestDay.net) : "")}${c("Worst day", n.worstDay ? `${money(n.worstDay.net)} <span class="faint">${fdate(n.worstDay.date, {
    weekday: "short"
  })}</span>` : "—", n.worstDay ? cls(n.worstDay.net) : "")}\n   ${c("Most broken rule", s ? `${esc(s.q.viol)} <span class="faint">×${s.n}</span>` : "None recorded")}${c("Most / least profitable session", i.length ? `${sessName(i[0].k)} / ${sessName(i.at(-1).k)}` : "—")}</div>` : '<div class="empty surface" style="margin-bottom:24px">No trades this week.</div>'}\n  <div class="surface pad" style="max-width:760px">${l.map(([p, u]) => `<div class="prompt"><label>${u}</label>${bindTA("weekly", e, "answers." + p, r[p])}</div>`).join("")}<span class="help">Saves as you type</span></div>`;
}

function compactPnl(e) {
  const t = Math.abs(e) / 100;
  return (e < 0 ? "−" : e > 0 ? "+" : "") + (t >= 1e3 ? decl((t / 1e3).toFixed(t >= 1e4 ? 0 : 1)) + "k" : Math.round(t));
}

function vCalendar(e) {
  const t = /^\d{4}-\d{2}$/.test(e || "") ? e : todayStr().slice(0, 7), a = t + "-01", n = pd(a), s = ymd(new Date(n.getFullYear(), n.getMonth() - 1, 1)).slice(0, 7), i = ymd(new Date(n.getFullYear(), n.getMonth() + 1, 1)).slice(0, 7), o = mergeCopies(sorted(S.trades.filter(g => acctOK(g) && g.date.startsWith(t)))), r = stats(o), c = r.days, l = [ ...c.values() ], p = l.filter(g => g.disc != null), u = Math.max(0, ...l.map(g => Math.abs(g.net))), h = weekStart(a), m = todayStr(), v = addDays(ymd(new Date(n.getFullYear(), n.getMonth() + 1, 1)), -1);
  ECON.days[a] && ECON.days[v] || loadEcon(a, v).then(() => {
    route().v === "calendar" && render();
  });
  const E = g => (ECON.days[g] || []).filter(P => P.impact === "high"), R = g => {
    const P = E(g);
    return P.length ? `<span class="cev">${P.slice(0, 2).map(O => `<span title="${esc(O.event)} · ${etStr(O.ts).slice(11, 16)} ET"><i></i>${etStr(O.ts).slice(11, 16)} ${esc(shortEv(O.event))}</span>`).join("")}${P.length > 2 ? `<span class="faint">+${P.length - 2}</span>` : ""}</span>` : "";
  }, L = calDays(c, t);
  let x = [ ...[ "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" ].slice(0, L), "Week" ].map(g => `<div class="hd${g === "Week" ? " wkh" : ""}">${g}</div>`).join("");
  for (let g = h; g.slice(0, 7) <= t || g < a; g = addDays(g, 7)) {
    let P = 0, O = 0;
    for (let H = 0; H < 7; H++) {
      const J = addDays(g, H), q = J.startsWith(t), z = c.get(J);
      if (H >= L) {
        z && (P += z.net, O += z.n);
        continue;
      }
      if (!q) {
        x += `<div class="out"><span class="dn">${pd(J).getDate()}</span></div>`;
        continue;
      }
      z && (P += z.net, O += z.n), x += `<a class="d ${J === m ? "is-today" : ""}" href="#journal/${J}" style="${z ? heatStyle(z.net, u) : ""}"><span class="dn">${pd(J).getDate()}</span>${R(J)}${z ? `<span class="p ${cls(z.net)}"><span class="full">${money(z.net)}</span><span class="short">${compactPnl(z.net)}</span></span><span class="m">${z.n} trade${z.n > 1 ? "s" : ""}</span><span class="m dc">${z.disc == null ? "" : Math.round(z.disc) + "% discipline"}</span>` : ""}</a>`;
    }
    if (x += `<div class="wk">${O ? `<span class="p ${cls(P)}"><span class="full">${money(P)}</span><span class="short">${compactPnl(P)}</span></span><span class="m">${O} trades</span>` : ""}</div>`, 
    addDays(g, 7).slice(0, 7) > t) break;
  }
  const C = (g, P, O = "") => `<div><span>${g}</span><span class="${O}">${P}</span></div>`;
  return `${filterBar({
    period: !1,
    session: !1,
    dir: !1
  })}\n  <div class="row" style="margin-bottom:14px"><a class="btn sm" href="#calendar/${s}" aria-label="Previous month">‹</a><h2 style="font-size:15px;min-width:150px;text-align:center">${n.toLocaleDateString(LOC(), {
    month: "long",
    year: "numeric"
  })}</h2><a class="btn sm" href="#calendar/${i}" aria-label="Next month">›</a>${t !== m.slice(0, 7) ? '<a class="link" href="#calendar">This month</a>' : ""}</div>\n  <div class="statline">${C("Monthly P&amp;L", money(r.net), cls(r.net))}${C("Trading days", c.size)}${C("Winning days", r.winDays)}${C("Losing days", r.lossDays)}${C("Day win rate", c.size ? pct(r.winDays / c.size) : "—")}${C("Avg daily P&amp;L", c.size ? money(r.net / c.size) : "—", c.size ? cls(r.net) : "")}${C("Avg discipline", p.length ? Math.round(p.reduce((g, P) => g + P.disc, 0) / p.length) + "%" : "—", "dc")}</div>\n  <div class="surface cal-wrap ${U.calSw ? "sw-" + U.calSw : ""}" data-prev="${s}" data-next="${i}" style="overflow:hidden" ${billOld(a, addDays(ymd(new Date(n.getFullYear(), n.getMonth() + 1, 1)), -1)) ? 'data-lock="analytics_history" data-force="1"' : ""}><div class="cal d${L}">${x}</div></div>`;
}

function accountForm() {
  const e = S.firms.slice().sort((t, a) => t.name.localeCompare(a.name));
  return `<form data-form="account" class="fgrid four" autocomplete="off">\n    <label class="f"><span>Prop firm</span><select name="firm">${opts([ ...e.map(t => [ t.id, t.name ]), [ "__new", "New prop firm…" ] ], e[0]?.id || "__new")}</select></label>\n    <label class="f" data-newfirm ${e.length ? "hidden" : ""}><span>New prop firm name</span><input name="firmName" placeholder="Topstep"></label>\n    <label class="f"><span>Account name</span><input name="name" required placeholder="Account 1"></label>\n    <label class="f"><span>Starting balance</span><input name="start" inputmode="decimal" placeholder="50,000" required></label>\n    <label class="f"><span>Created</span><input type="date" name="created" value="${todayStr()}"></label>\n    <div class="f full"><div class="row"><button class="btn primary" type="submit">Add account</button>${U.addAcct ? '<button class="btn" type="button" data-act="acct-add" data-v="0">Cancel</button>' : ""}<span class="err" data-err></span></div></div>\n  </form>`;
}

function vAccounts() {
  const e = S.accounts.filter(n => n.status !== "archived"), t = S.accounts.filter(n => n.status === "archived"), a = [ ...groupBy(e, n => n.firm_id) ];
  return `<section><div class="sec-h"><h2>Active accounts</h2></div><div class="surface">${acctTable(e)}\n    ${U.addAcct ? `<div class="acct-add">${accountForm()}</div>` : '<button class="add-row" data-act="acct-add" data-v="1"><span class="add-ic">+</span>Add account</button>'}</div></section>\n  ${a.length > 1 ? `<section class="sec"><div class="sec-h"><h2>By prop firm</h2></div><div class="surface">${groupTable("Prop firm", new Map(a.map(([n, s]) => [ firm(n)?.name || "—", S.trades.filter(i => s.some(o => o.id === i.account_id)) ])), {
    showR: !1
  })}</div></section>` : ""}\n  ${t.length ? `<section class="sec"><div class="sec-h"><h2>Closed accounts</h2><span class="help">Trades, payouts and expenses stay in your history and filters.</span></div><div class="surface">${acctTable(t, {
    totals: !1
  })}</div></section>` : ""}`;
}

function vAccount(e) {
  const t = getDoc("accounts", e);
  if (!t) return '<div class="empty">Account not found. <a href="#accounts">Back to accounts</a></div>';
  const a = sorted(S.trades.filter(o => o.account_id === e)), n = stats(a), s = firm(t.firm_id), i = S.payouts.filter(o => o.account_id === e);
  return `<div class="row" style="margin-bottom:14px"><a class="link" href="#accounts">Accounts</a><span class="faint">/</span><span class="muted">${esc(s?.name || "")} — ${esc(t.name)}</span><span style="flex:1"></span>\n    ${t.status === "archived" ? `<span class="help" style="margin-left:6px">Outcome</span>${segFor("accounts", e, "outcome", [ [ "failed", "Failed" ], [ "passed", "Passed" ], [ "other", "Closed" ] ], t.outcome || "other")}` : ""}\n    <button class="btn sm" data-act="filter-account" data-id="${e}">${{
    fr: "Voir ses stats",
    es: "Ver sus estadísticas"
  }[LANG] || "See its stats"}</button>\n    <details class="menu acc-menu"><summary class="btn sm" aria-label="${{
    fr: "Plus d’actions",
    es: "Más acciones"
  }[LANG] || "More actions"}">⋯</summary><div class="menu-pop" data-noi18n>\n      <button data-act="set" data-col="accounts" data-id="${e}" data-path="status" data-v="${t.status === "archived" ? "active" : "archived"}">${t.status === "archived" ? {
    fr: "Rouvrir le compte",
    es: "Reabrir la cuenta"
  }[LANG] || "Reopen" : {
    fr: "Fermer le compte",
    es: "Cerrar la cuenta"
  }[LANG] || "Close account"}</button>\n      ${t.status === "archived" ? "" : `<button data-fail="${e}" class="nav-fail-m">${{
    fr: "Marquer comme échoué",
    es: "Marcar como fallida"
  }[LANG] || "Mark as failed"}</button>`}\n      ${a.length ? `<button disabled title="${{
    fr: "Supprime d’abord ses trades",
    es: "Elimina primero sus operaciones"
  }[LANG] || "Delete its trades first"}">${{
    fr: "Supprimer",
    es: "Eliminar"
  }[LANG] || "Delete"}</button>` : `<button class="danger" data-act="del-account" data-id="${e}">${{
    fr: "Supprimer",
    es: "Eliminar"
  }[LANG] || "Delete"}</button>`}\n    </div></details></div>\n  <div class="statline"><div><span>Balance</span><span>${moneyU(acctBalance(t))}</span></div><div><span>Net P&amp;L</span><span class="${cls(n.net)}">${money(n.net)}</span></div><div><span>Trades</span><span>${n.n}</span></div><div><span>Win rate</span><span>${pct(n.wr)}</span></div><div><span>Profit factor</span><span>${pf(n.pf)}</span></div><div><span>Discipline</span><span class="dc">${dpct(n.disc)}</span></div><div><span>Worst drawdown</span><span class="${n.maxDD ? "neg" : ""}">${money(n.maxDD)}</span></div></div>\n  <section class="cols" style="margin-bottom:28px"><div><div class="sec-h"><h2>Status</h2></div><div class="acards" style="grid-template-columns:1fr">${accountCard(t, {
    full: !0
  }).replace('<a class="acard"', '<div class="acard"').replace(/<\/a>$/, "</div>")}</div></div>\n  <div><div class="sec-h"><h2>Firm rules</h2><span class="help">Saved as you type</span></div><div class="surface pad">${rulesForm(t)}</div></div></section>\n  <section class="cols"><div><div class="sec-h"><h2>Equity</h2></div><div class="surface pad">${lineChart(equitySeries(a, "daily"), {
    lab: eqLab("daily")
  })}</div></div>\n  <div><div class="sec-h"><h2>Details</h2></div><div class="surface pad"><div class="fgrid two">\n    <label class="f"><span>Account name</span>${bindIn("accounts", e, "name", t.name)}</label>\n    <label class="f"><span>Reference</span>${bindIn("accounts", e, "ref", t.ref)}</label>\n    <label class="f"><span>Starting balance</span>${bindIn("accounts", e, "starting_balance_c", money(t.starting_balance_c, {
    sign: !1
  }), {
    kind: "money"
  })}</label>\n    <label class="f"><span>Created</span>${bindIn("accounts", e, "created_on", t.created_on, {
    type: "date"
  })}</label>\n    <label class="f full"><span>Notes</span>${bindTA("accounts", e, "notes", t.notes)}</label></div></div></div></section>\n  <section class="sec"><div class="sec-h"><h2>Trades</h2></div><div class="surface">${a.length ? tradeTable(a.slice().reverse().slice(0, 50)) : '<div class="empty">No trades yet. <button class="link" data-act="add-trade">Add your first trade</button></div>'}</div></section>\n  ${i.length ? `<section class="sec"><div class="sec-h"><h2>Payouts</h2></div><div class="surface">${payoutTable(i)}</div></section>` : ""}`;
}

function payoutTable(e) {
  return `<div class="scroll-x"><table class="tbl pay-tbl"><thead><tr><th>Account</th><th class="num">Amount</th><th>Status</th><th>Requested</th><th>Approved</th><th>Paid</th><th>Notes</th><th></th></tr></thead><tbody>${e.slice().sort((t, a) => (a.request_date || "").localeCompare(t.request_date || "")).map(t => U.editP === t.id ? `<tr><td colspan="8">${payoutForm(t)}</td></tr>` : `<tr><td>${esc(acctLabel(t.account_id))}</td><td class="num">${moneyU(t.amount_c)}</td><td><select data-bind="payouts|${t.id}|status" aria-label="Status">${opts(PST, t.status)}</select></td><td class="muted">${fdate(t.request_date)}</td><td class="muted">${fdate(t.approval_date)}</td><td class="muted">${fdate(t.payment_date)}</td><td class="muted wrap">${esc(t.notes || "")}</td><td class="num">${t.status === "paid" ? shareBtn("payout", t.id, "Share", "link sh-link") : ""}<button class="link" data-act="edit-payout" data-id="${t.id}">Edit</button></td></tr>`).join("")}</tbody></table></div>`;
}

function payoutForm(e = {}) {
  return `<form class="fgrid four" data-form="payout" data-id="${e.id || ""}" autocomplete="off">\n   <label class="f"><span>Account</span><select name="account" required>${opts(S.accounts.map(t => [ t.id, acctLabel(t.id) ]), e.account_id || F.account)}</select></label>\n   <label class="f"><span>Amount</span><input name="amount" inputmode="decimal" required value="${e.amount_c != null ? e.amount_c / 100 : ""}" placeholder="$"></label>\n   <label class="f"><span>Status</span><select name="status">${opts(PST, e.status || "requested")}</select></label>\n   <label class="f"><span>Request date</span><input type="date" name="request_date" value="${e.request_date || todayStr()}"></label>\n   <label class="f"><span>Approval date</span><input type="date" name="approval_date" value="${e.approval_date || ""}"></label>\n   <label class="f"><span>Payment date</span><input type="date" name="payment_date" value="${e.payment_date || ""}"></label>\n   <label class="f" style="grid-column:span 2"><span>Notes</span><input name="notes" value="${esc(e.notes || "")}"></label>\n   <div class="f full"><div class="row"><button class="btn primary" type="submit">${e.id ? "Save payout" : "Add payout"}</button>${e.id ? `<button class="btn" type="button" data-act="cancel-edit">Cancel</button><button class="btn danger" type="button" data-act="del-payout" data-id="${e.id}">Delete</button>` : ""}</div></div></form>`;
}

function expenseForm(e = {}) {
  const t = S.firms;
  return `<form class="fgrid four" data-form="expense" data-id="${e.id || ""}" autocomplete="off">\n   <label class="f"><span>Date</span><input type="date" name="date" value="${e.date || todayStr()}" required></label>\n   <label class="f"><span>Prop firm</span><select name="firm">${opts([ [ "", "—" ], ...t.map(a => [ a.id, a.name ]) ], e.firm_id || "")}</select></label>\n   <label class="f"><span>Account (optional)</span><select name="account">${opts([ [ "", "—" ], ...S.accounts.map(a => [ a.id, acctLabel(a.id) ]) ], e.account_id || "")}</select></label>\n   <label class="f"><span>Category</span><select name="category">${opts(ECAT, e.category || "evaluation")}</select></label>\n   <label class="f"><span>Amount</span><input name="amount" inputmode="decimal" required value="${e.amount_c != null ? e.amount_c / 100 : ""}" placeholder="$"></label>\n   <label class="f" style="grid-column:span 3"><span>Notes</span><input name="notes" value="${esc(e.notes || "")}"></label>\n   <div class="f full"><div class="row"><button class="btn primary" type="submit">${e.id ? "Save expense" : "Add expense"}</button>${e.id ? `<button class="btn" type="button" data-act="cancel-edit">Cancel</button><button class="btn danger" type="button" data-act="del-expense" data-id="${e.id}">Delete</button>` : ""}</div></div></form>`;
}

function vPayouts() {
  if (!S.accounts.length) return onboarding();
  const e = h => !(F.account !== "all" && h.account_id !== F.account || F.firm !== "all" && (h.firm_id || acct(h.account_id)?.firm_id) !== F.firm), t = S.payouts.filter(e), a = S.expenses.filter(e), n = (h, m = () => !0) => h.filter(m).reduce((v, b) => v + (b.amount_c || 0), 0), s = S.trades.filter(acctOK).reduce((h, m) => h + tNet(m), 0), i = n(t, h => [ "requested", "approved", "paid" ].includes(h.status)), o = n(t, h => [ "approved", "paid" ].includes(h.status)), r = n(t, h => h.status === "paid"), c = n(t, h => [ "requested", "approved" ].includes(h.status)), l = n(a), p = (h, m, v = "") => `<div><span>${h}</span><span class="${v}">${m}</span></div>`, u = a.slice().sort((h, m) => (m.date || "").localeCompare(h.date || "")).map(h => U.editE === h.id ? `<tr><td colspan="6">${expenseForm(h)}</td></tr>` : `<tr><td class="muted">${fdate(h.date)}</td><td>${esc(firm(h.firm_id)?.name || "—")}</td><td class="muted">${h.account_id ? esc(acctName(h.account_id)) : "—"}</td><td>${esc((ECAT.find(m => m[0] === h.category) || [ 0, "Other" ])[1])}</td><td class="num">${moneyU(h.amount_c)}</td><td class="muted wrap">${esc(h.notes || "")} <button class="link" data-act="edit-expense" data-id="${h.id}" style="float:right">Edit</button></td></tr>`).join("");
  return `${filterBar({
    period: !1,
    session: !1,
    dir: !1
  })}<div data-lock="payouts" data-feature="payouts" class="bill-lock">\n  <div class="kpis k4"><div><div class="lbl">${tip("Trading P&amp;L", "Net P&L from all logged trades. Not money in your bank account.")}</div><div class="val ${cls(s)}">${money(s, {
    dec: 0
  })}</div></div><div><div class="lbl">Payouts received</div><div class="val">${moneyU(r)}</div></div><div><div class="lbl">Trading expenses</div><div class="val ${l ? "neg" : ""}">${l ? money(-l, {
    dec: 0
  }) : "$0"}</div></div><div><div class="lbl">${tip("Net realized income", "Payouts received − trading expenses. The money trading actually made you.")}</div><div class="val ${cls(r - l)}">${money(r - l, {
    dec: 0
  })}</div></div></div>\n  ${r || S.expenses.length ? `<div class="sh-row">${shareBtn("net", "all", "Share net after fees")}</div>` : ""}\n  <div class="metrics surface m4" style="margin-top:10px">${p("Requested", moneyU(i))}${p("Approved", moneyU(o))}${p("Pending", moneyU(c), c ? "dc" : "")}${p("Rejected", moneyU(n(t, h => h.status === "rejected")))}</div>\n  <section class="sec"><div class="sec-h"><h2>Payouts</h2></div><div class="surface">${t.length ? payoutTable(t) : '<div class="empty">No payouts yet.</div>'}</div>\n    <div class="surface pad" style="margin-top:10px">${U.editP ? "" : payoutForm()}${U.editP ? '<span class="muted">Finish editing the payout above to add a new one.</span>' : ""}</div></section>\n  <section class="sec"><div class="sec-h"><h2>Expenses</h2>${aiBtn("ai-scan", "Scan a receipt")}</div><div class="surface">${a.length ? `<div class="scroll-x"><table class="tbl exp-tbl"><thead><tr><th>Date</th><th>Prop firm</th><th>Account</th><th>Category</th><th class="num">Amount</th><th>Notes</th></tr></thead><tbody>${u}</tbody></table></div>` : '<div class="empty">No expenses yet.</div>'}</div>\n    <div class="surface pad" style="margin-top:10px">${U.editE ? '<span class="muted">Finish editing the expense above to add a new one.</span>' : expenseForm()}</div></section></div>`;
}

function shortEv(e) {
  const t = [ [ /core cpi|core inflation/i, "Core CPI" ], [ /\bcpi\b|inflation rate/i, "CPI" ], [ /core ppi/i, "Core PPI" ], [ /\bppi\b/i, "PPI" ], [ /core pce/i, "Core PCE" ], [ /\bpce\b/i, "PCE" ], [ /non.?farm payrolls/i, "NFP" ], [ /unemployment/i, "Unemployment" ], [ /average hourly/i, "Earnings" ], [ /press conference/i, "Fed presser" ], [ /minutes/i, "FOMC minutes" ], [ /fomc|interest rate decision/i, "FOMC" ], [ /\bgdp\b/i, "GDP" ], [ /retail sales/i, "Retail" ], [ /ism manufacturing/i, "ISM Mfg" ], [ /ism services/i, "ISM Svc" ], [ /jolts/i, "JOLTS" ], [ /\badp\b/i, "ADP" ], [ /jobless/i, "Claims" ], [ /consumer confidence/i, "Confidence" ] ];
  for (const [a, n] of t) if (a.test(e)) return n;
  return e.length > 14 ? e.slice(0, 13) + "…" : e;
}

function anDir(e) {
  const t = stats(e.filter(i => i.direction === "long")), a = stats(e.filter(i => i.direction === "short")), n = (i, o) => `<tr><td class="muted">${i}</td><td class="num">${o(t)}</td><td class="num">${o(a)}</td></tr>`, s = i => `<span class="${cls(i)}">${money(i)}</span>`;
  return `<div class="surface" style="max-width:640px"><table class="tbl"><thead><tr><th></th><th class="num tag-l">Long</th><th class="num tag-s">Short</th></tr></thead><tbody>\n   ${n("Trades", i => i.n)}${n("Win rate", i => pct(i.wr))}${n("Net P&amp;L", i => s(i.net))}${n("Average P&amp;L", i => s(i.avg))}${n("Profit factor", i => pf(i.pf))}${n("Expectancy", i => s(i.exp))}${n("Average R", i => rfmt(i.avgR))}${n("Discipline", i => dcell(i.disc))}</tbody></table></div>\n   ${t.n < MIN_N || a.n < MIN_N ? `<p class="help" style="margin-top:10px">Not enough data yet to compare directions reliably (at least ${MIN_N} trades each).</p>` : ""}`;
}

function anSess(e) {
  const t = groupBy(e, n => n.session), a = new Map(SESS.filter(([n]) => t.has(n)).map(([n]) => [ n, t.get(n) ]));
  return `<div class="surface">${groupTable("Session", a, {
    label: sessName
  })}</div><section class="sec"><div class="sec-h"><h2>Net P&amp;L by session</h2></div><div class="surface pad">${barChart([ ...a ].map(([n, s]) => ({
    label: sessName(n),
    v: stats(s).net
  })), {
    h: 170
  })}</div></section>`;
}

function anTime(e) {
  const t = groupBy(e, c => c.entry_time ? c.entry_time.slice(0, 2) : null), a = [ ...t.keys() ].sort(), n = new Map(a.map(c => [ c, t.get(c) ])), s = a.map(c => ({
    k: c,
    s: stats(t.get(c))
  })).filter(c => c.s.n >= 3), i = s.slice().sort((c, l) => l.s.avg - c.s.avg)[0], o = s.slice().sort((c, l) => c.s.avg - l.s.avg)[0], r = c => `${c}:00–${c}:59`;
  return `${i && o && i !== o ? `<div class="statline"><div><span>Strongest hour (avg trade)</span><span class="pos">${r(i.k)} · ${money(i.s.avg)}</span></div><div><span>Weakest hour (avg trade)</span><span class="neg">${r(o.k)} · ${money(o.s.avg)}</span></div><div><span>Based on</span><span class="muted" style="font-weight:400">hours with 3+ trades</span></div></div>` : ""}\n  <div class="surface pad">${barChart(a.map(c => ({
    label: c + "h",
    title: r(c),
    v: stats(t.get(c)).net
  })), {
    h: 170
  })}</div>\n  <section class="sec"><div class="surface">${groupTable("Entry hour (NY time)", n, {
    label: r
  })}</div></section>`;
}

function anWeekday(e) {
  const t = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" ], a = groupBy(e, s => (pd(s.date).getDay() + 6) % 7), n = new Map([ 0, 1, 2, 3, 4, 5, 6 ].filter(s => a.has(s)).map(s => [ s, a.get(s) ]));
  return `<div class="surface">${groupTable("Day", n, {
    label: s => t[s]
  })}</div><section class="sec"><div class="surface pad">${barChart([ ...n ].map(([s, i]) => ({
    label: t[s].slice(0, 3),
    v: stats(i).net
  })), {
    h: 160
  })}</div></section>`;
}

function anSetup(e) {
  const t = groupBy(e, n => n.setup || "No setup"), a = new Map([ ...t ].sort((n, s) => stats(s[1]).net - stats(n[1]).net));
  return `<div class="surface">${groupTable("Setup", a)}</div>`;
}

function anDisc(e) {
  const t = S.settings.threshold || 90, a = e.filter(L => tDisc(L) != null), n = e.length - a.length;
  if (a.length < MIN_N) return `<div class="empty surface">Not enough data yet. Complete the discipline checklist on at least ${MIN_N} trades (${a.length} so far).</div>`;
  const s = L => tDisc(L) >= t, i = [ [ 1, 1 ], [ 1, 0 ], [ 0, 1 ], [ 0, 0 ] ].map(([L, x]) => {
    const C = a.filter(g => s(g) === !!L && (x ? tNet(g) > 0 : tNet(g) <= 0));
    return {
      g: L,
      w: x,
      n: C.length,
      net: C.reduce((g, P) => g + tNet(P), 0)
    };
  }), o = L => `<div class="cell"><b class="${cls(L.net)}">${money(L.net)}</b><span>${L.n} trade${L.n === 1 ? "" : "s"} · ${pct(a.length ? L.n / a.length : null)}</span></div>`, r = stats(a.filter(s)), c = stats(a.filter(L => !s(L))), l = violations(a), p = a.filter(L => Object.values(L.discipline || {}).includes("n")), u = a.filter(L => !Object.values(L.discipline || {}).includes("n")), h = stats(p), m = stats(u), v = stats(a).net, b = (L, x, C, g = P => P) => `<tr><td class="muted">${L}</td><td class="num">${g(x)}</td><td class="num">${g(C)}</td></tr>`, E = L => `<span class="${cls(L)}">${money(L)}</span>`, R = l.slice().sort((L, x) => x.n - L.n)[0];
  return `<div class="statline"><div><span>If every rule had been followed</span><span>${p.length ? `You would have avoided ${p.length} trades that netted <span class="${cls(h.net)}">${money(h.net)}</span>` : "No rule violations recorded"}</span></div>${p.length ? `<div><span>Net P&amp;L without them</span><span class="${cls(m.net)}">${money(m.net)} <span class="faint" style="font-weight:400">vs ${money(v)} actual</span></span></div>` : ""}</div>\n  <section class="cols even"><div><div class="sec-h"><h2>Process vs outcome</h2><span class="help">Good process = discipline ≥ ${t}%</span></div>\n    <div class="quad"><div></div><div class="ax">Winning trade</div><div class="ax">Losing or breakeven</div>\n      <div class="ax">Good process</div>${o(i[0])}${o(i[1])}<div class="ax">Bad process</div>${o(i[2])}${o(i[3])}</div>\n    <p class="help" style="margin-top:8px">A loss with good process is a well-executed trade. A win with bad process is a habit you are being paid to repeat.</p></div>\n  <div><div class="sec-h"><h2>Rules followed vs broken</h2></div><div class="surface"><table class="tbl"><thead><tr><th></th><th class="num">Discipline ≥ ${t}%</th><th class="num">Below ${t}%</th></tr></thead><tbody>\n    ${b("Trades", r.n, c.n)}${b("Net P&amp;L", r.net, c.net, E)}${b("Win rate", r.wr, c.wr, pct)}${b("Average P&amp;L", r.avg, c.avg, E)}${b("Average loss", r.avgLoss, c.avgLoss, E)}${b("Profit factor", r.pf, c.pf, pf)}</tbody></table></div></div></section>\n  <section class="sec"><div class="sec-h"><h2>Rule violations by financial impact</h2>${R ? `<span class="help">Most frequent: ${esc(R.q.viol)} (${R.n}×)</span>` : ""}</div><div class="surface">${l.length ? `<div class="scroll-x"><table class="tbl"><thead><tr><th>Violation</th><th class="num">Occurrences</th><th class="num">% of trades</th><th class="num">Total P&amp;L</th><th class="num">Average P&amp;L</th><th class="num">Average loss</th><th class="num">Largest loss</th><th class="num">Win rate</th></tr></thead><tbody>${l.map(L => `<tr class="${L.n < 3 ? "thin" : ""}"><td>${esc(L.q.viol)}</td><td class="num">${L.n}</td><td class="num">${pct(L.pct)}</td><td class="num ${cls(L.net)}">${money(L.net)}</td><td class="num">${money(L.avg)}</td><td class="num">${money(L.avgLoss)}</td><td class="num">${money(L.largest)}</td><td class="num">${pct(L.wr)}</td></tr>`).join("")}</tbody></table></div>` : '<div class="empty">No rule violations recorded in this period.</div>'}</div></section>\n  ${n ? `<p class="help" style="margin-top:10px">${n} trade${n > 1 ? "s" : ""} without a completed checklist ${n > 1 ? "are" : "is"} excluded from this view. <a href="#trades" data-act="ui-disc-none">Review them</a></p>` : ""}`;
}

function anBehavior(e) {
  const t = seq(e), a = (u, h) => {
    const m = stats(h);
    return `<tr class="${m.n < MIN_N ? "thin" : ""}"><td>${u}</td><td class="num">${m.n}</td><td class="num ${m.n < MIN_N ? "" : cls(m.net)}">${money(m.net)}</td><td class="num">${pct(m.wr)}</td><td class="num">${money(m.avg)}</td><td class="num">${m.avgQty == null ? "—" : m.avgQty.toFixed(1)}</td><td class="num">${dcell(m.disc)}</td></tr>`;
  }, n = '<thead><tr><th>Situation</th><th class="num">Trades</th><th class="num">Net P&amp;L</th><th class="num">Win rate</th><th class="num">Avg trade</th><th class="num">Avg size</th><th class="num">Discipline</th></tr></thead>', s = u => groupBy(e, h => h.emo && h.emo[u] || []), i = u => {
    const h = s(u), m = new Map([ ...h ].sort((v, b) => stats(v[1]).avg - stats(b[1]).avg));
    return m.size ? groupTable("Emotion", m, {
      showR: !1
    }) : '<div class="empty">No emotions recorded yet.</div>';
  }, o = (u, h) => {
    const m = groupBy(e, b => b.emo && b.emo[u] ? String(b.emo[u]) : null), v = new Map([ ...m ].sort());
    return v.size ? `<h3 style="padding:10px 10px 0">${h}</h3>${groupTable("Rating", v, {
      showR: !1,
      label: b => b + " / 5"
    })}` : "";
  }, r = e.filter(u => (u.discipline || {}).addloser === "n"), c = e.filter(u => (u.emo?.before || []).includes("Revenge mindset")), l = e.filter(u => (u.emo?.before || []).includes("Need to be right")), p = o("confidence", "Confidence") + o("execution", "Execution quality") + o("quality", "Trade quality");
  return `<section><div class="sec-h"><h2>What happens next</h2><span class="help">Sequences are within the same trading day</span></div><div class="surface scroll-x"><table class="tbl">${n}<tbody>\n    ${a("Every trade", e)}${a("Next trade after a loss", t.afterLoss)}${a("After two consecutive losses", t.after2Loss)}${a("Next trade after a win", t.afterWin)}\n    ${a("Rest of day when first trade loses", t.restFirstLose)}${a("Rest of day when first trade wins", t.restFirstWin)}\n    ${a("Revenge mindset selected", c)}${a("“Need to be right” selected", l)}${a("Added to a losing position", r)}</tbody></table></div></section>\n  <section class="sec cols even"><div><div class="sec-h"><h2>Emotional state before entry</h2></div><div class="surface">${i("before")}</div></div>\n  <div><div class="sec-h"><h2>Self-ratings</h2></div><div class="surface">${p || '<div class="empty">No ratings recorded yet.</div>'}</div></div></section>\n  <section class="sec cols even"><div><div class="sec-h"><h2>During the trade</h2></div><div class="surface">${i("during")}</div></div><div><div class="sec-h"><h2>After the trade</h2></div><div class="surface">${i("after")}</div></div></section>`;
}

function anRecovery(e) {
  const t = seq(e), a = stats(t.first), n = stats(t.afterLoss), s = stats(t.after2Loss), i = stats(t.afterFirstLoss), o = avgQty(t.beforeFirstLoss), r = avgQty(t.afterFirstLoss), c = stats(e), l = (m, v, b = "", E = "") => `<div><span>${m}</span><span class="${b}">${v}${E ? ` <span class="faint" style="font-weight:400">${E}</span>` : ""}</span></div>`, p = o && r != null ? (r - o) / o : null, u = stats(t.afterLoss).disc, h = stats(e.filter(m => !t.afterLoss.includes(m))).disc;
  return `<p class="muted" style="margin:0 0 14px;max-width:70ch">Does your trading change after you see red? Each figure compares behavior before and after losses within the same day.</p>\n  <div class="metrics surface" style="grid-template-columns:repeat(2,minmax(0,1fr))">\n   ${l("First trade of the day", money(a.avg), cls(a.avg), `avg · ${pct(a.wr)} win rate · ${a.n} days`)}\n   ${l("Next trade after a loss", money(n.avg), cls(n.avg), `avg · ${pct(n.wr)} win rate · ${n.n} trades`)}\n   ${l("After two consecutive losses", money(s.avg), cls(s.avg), `avg · ${pct(s.wr)} win rate · ${s.n} trades`)}\n   ${l("Overall average trade", money(c.avg), cls(c.avg), `${c.n} trades`)}\n   ${l(tip("Position size before vs after first daily loss", "Average contracts on trades up to and including the first losing trade of the day, versus trades after it."), o == null ? "—" : `${o.toFixed(1)} → ${r == null ? "—" : r.toFixed(1)}`, p > .1 ? "neg" : "", p == null ? "" : `${p > 0 ? "+" : ""}${Math.round(p * 100)}%`)}\n   ${l("Avg size after two losses", avgQty(t.after2Loss) == null ? "—" : avgQty(t.after2Loss).toFixed(1) + " contracts", "", `vs ${c.avgQty == null ? "—" : c.avgQty.toFixed(1)} overall`)}\n   ${l("Trades taken after the first daily loss", t.daysWithLoss ? (t.afterFirstLoss.length / t.daysWithLoss).toFixed(1) + " per day" : "—", "", `${t.daysWithLoss} days with a loss`)}\n   ${l("P&amp;L generated after the first daily loss", money(i.net), cls(i.net), `${i.n} trades · ${pct(i.wr)} win rate`)}\n   ${l("Discipline after a loss", dpct(u), "dc", `vs ${dpct(h)} otherwise`)}\n   ${l("Days with a losing trade", t.daysWithLoss + " of " + t.days)}\n  </div>\n  ${n.n < MIN_N ? `<p class="help" style="margin-top:10px">Not enough data yet for firm conclusions (${n.n} trades after a loss).</p>` : ""}\n  <section class="sec"><div class="sec-h"><h2>Position size, trade by trade within the day</h2></div><div class="surface pad">${(() => {
    const m = new Map;
    for (const b of dayMap(e).values()) b.trades.forEach((E, R) => {
      const L = Math.min(R + 1, 6);
      m.has(L) || m.set(L, []), m.get(L).push(E);
    });
    const v = [ ...m.keys() ].sort((b, E) => b - E);
    return barChart(v.map(b => ({
      label: b === 6 ? "6th+" : [ "1st", "2nd", "3rd", "4th", "5th" ][b - 1],
      title: (b === 6 ? "6th+ trade" : [ "1st", "2nd", "3rd", "4th", "5th" ][b - 1] + " trade") + ` (${m.get(b).length} trades)`,
      v: avgQty(m.get(b)),
      tv: avgQty(m.get(b)).toFixed(2) + " contracts"
    })), {
      h: 150,
      fmtV: b => b.toFixed(1),
      color: "bd"
    });
  })()}</div></section>`;
}

const SITE = "https://makeitsweep.com", sitePath = e => SITE + (LANG === "fr" ? "/fr" : LANG === "es" ? "/es" : "") + "/" + e, DISCLAIMER = {
  en: "Sweep is a tracking and analytics tool. It does not give trade signals or financial advice. Trading futures involves substantial risk of loss and is not suitable for everyone. Past performance does not guarantee future results.",
  fr: "Sweep est un outil de suivi et d'analyse. Il ne donne ni signaux de trading ni conseils financiers. Le trading de contrats à terme comporte un risque important de perte et ne convient pas à tout le monde. Les performances passées ne garantissent pas les résultats futurs.",
  es: "Sweep es una herramienta de seguimiento y análisis. No ofrece señales de trading ni asesoramiento financiero. Operar futuros implica un riesgo sustancial de pérdida y no es adecuado para todos. Los resultados pasados no garantizan resultados futuros."
};

function aiSettings() {
  if (!AI.on) return "";
  const e = AI.usage || {}, t = {
    en: [ "Sweep AI", "AI features are optional. Data leaves Sweep only when you tap an AI action: the text you type, the image you choose, and short summaries of your own stats (counts, win rates, P&L by session or setup). It is sent to Google Gemini (paid API), which under Google's terms for paid use does not use it to train its models. Results are kept on Sweep's server for up to 30 days so a repeated request is free, and are deleted with your account. AI answers can be wrong: check every draft before saving. Sweep AI never gives trade signals or financial advice.", "AI actions left today" ],
    fr: [ "Sweep AI", "Les fonctions IA sont facultatives. Tes données ne quittent Sweep que lorsque tu touches une action IA : le texte que tu tapes, l'image que tu choisis et de courts résumés de tes propres stats (nombre de trades, taux de réussite, P&L par session ou setup). Elles sont envoyées à Google Gemini (API payante), qui, selon les conditions de Google pour l'usage payant, ne les utilise pas pour entraîner ses modèles. Les résultats restent sur le serveur de Sweep jusqu'à 30 jours pour qu'une même demande soit gratuite, et sont supprimés avec ton compte. Une réponse de l'IA peut être fausse : vérifie chaque brouillon avant d'enregistrer. Sweep AI ne donne jamais de signaux de trading ni de conseils financiers.", "Actions IA restantes aujourd'hui" ],
    es: [ "Sweep AI", "Las funciones de IA son opcionales. Tus datos solo salen de Sweep cuando tocas una acción de IA: el texto que escribes, la imagen que eliges y breves resúmenes de tus propias estadísticas (número de operaciones, tasa de acierto, P&L por sesión o setup). Se envían a Google Gemini (API de pago), que según los términos de Google para el uso de pago no los usa para entrenar sus modelos. Los resultados se guardan en el servidor de Sweep hasta 30 días para que una misma petición sea gratuita, y se eliminan con tu cuenta. Una respuesta de la IA puede ser incorrecta: revisa cada borrador antes de guardar. Sweep AI nunca da señales de trading ni asesoramiento financiero.", "Acciones de IA restantes hoy" ]
  }[LANG];
  return `<section class="sec" data-noi18n><div class="sec-h"><h2><span class="ai-sp">✦</span>${t[0]}</h2>${e.remaining != null ? `<span class="help">${t[2]}${LANG === "fr" ? " :" : ":"} ${e.remaining}</span>` : ""}</div><div class="surface pad"><p class="muted" style="margin:0;max-width:80ch;line-height:1.6">${t[1]}</p></div></section>`;
}

function aboutSweep() {
  return `<section class="sec about" data-noi18n><div class="sec-h"><h2>${{
    en: "About Sweep",
    fr: "À propos de Sweep",
    es: "Acerca de Sweep"
  }[LANG]}</h2></div><div class="surface pad">\n    <div class="legal">${[ [ "privacy.html", {
    en: "Privacy policy",
    fr: "Politique de confidentialité",
    es: "Política de privacidad"
  } ], [ "terms.html", {
    en: "Terms of use",
    fr: "Conditions d'utilisation",
    es: "Términos de uso"
  } ], [ "risk.html", {
    en: "Risk disclosure",
    fr: "Avertissement sur les risques",
    es: "Divulgación de riesgos"
  } ], [ "contact.html", {
    en: "Contact",
    fr: "Contact",
    es: "Contacto"
  } ] ].map(([e, t]) => `<a href="${sitePath(e)}" target="_blank" rel="noopener">${t[LANG]}</a>`).join("")}<a href="${SITE}${LANG === "en" ? "" : "/" + LANG + "/"}" target="_blank" rel="noopener">makeitsweep.com</a></div>\n    <div class="social"><span>${{
    en: "Follow Sweep",
    fr: "Suis Sweep",
    es: "Sigue a Sweep"
  }[LANG]}</span><div class="social-icons"><a href="https://www.instagram.com/makeitsweep" target="_blank" rel="noopener" aria-label="Sweep on Instagram" title="Instagram"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r="1" fill="currentColor" stroke="none"/></svg></a><a href="https://www.tiktok.com/@makeitsweep" target="_blank" rel="noopener" aria-label="Sweep on TikTok" title="TikTok"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.6 3c.3 2.2 1.6 3.6 3.9 3.8v3.1c-1.4.1-2.7-.3-3.9-1.1v6.1c0 3.9-3.3 6.4-6.9 5.6-2.3-.5-4-2.5-4.1-4.9-.2-3.5 2.9-6.3 6.4-5.7v3.2c-.5-.2-1.1-.2-1.6-.1-1.3.3-2.1 1.5-1.8 2.8.2 1 1.1 1.8 2.2 1.8 1.4 0 2.4-1.1 2.4-2.5V3h3.4z"/></svg></a><a href="https://www.facebook.com/share/1Q6uHzUfQf/" target="_blank" rel="noopener" aria-label="Sweep on Facebook" title="Facebook"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13.5 21v-7.6h2.6l.4-3h-3V8.5c0-.9.3-1.5 1.5-1.5h1.6V4.3c-.3 0-1.2-.1-2.3-.1-2.3 0-3.9 1.4-3.9 4v2.2H7.8v3h2.6V21h3.1z"/></svg></a></div></div>\n    <p class="disclaimer">${DISCLAIMER[LANG]}</p><p class="signoff">Sweep down. Jump up.</p></div></section>`;
}

function vSettings() {
  const e = S.settings, t = S.trades.some(a => a.demo);
  return `${accountSection()}<section class="${S.mode === "server" && S.me ? "sec" : ""}"><div class="sec-h"><h2>Discipline checklist</h2><span class="help">Each question is answered Yes / No / N/A per trade. The violation label is used in analytics.</span></div>\n   <div class="surface"><div class="scroll-x"><table class="tbl q-tbl"><thead><tr><th style="width:44%">Question</th><th>Violation label</th><th>Active</th><th></th></tr></thead><tbody>${e.questions.map((a, n) => `<tr><td><input style="width:100%" data-bind="settings|settings|questions.${n}.text" value="${esc(a.text)}"></td><td data-l="Violation label"><input style="width:100%" data-bind="settings|settings|questions.${n}.viol" value="${esc(a.viol)}"></td><td><label class="sw"><input type="checkbox" data-act-change="q-active" data-i="${n}" ${a.active ? "checked" : ""} aria-label="Active"><i></i></label></td><td class="num">${S.trades.some(s => (s.discipline || {})[a.id]) ? '<span class="faint" title="Answered on existing trades — deactivate instead">In use</span>' : `<button class="link" data-act="q-del" data-i="${n}">Remove</button>`}</td></tr>`).join("")}</tbody></table></div>\n   <div class="pad row"><input id="newQ" placeholder="Add a question, e.g. Did I trade only my A+ setup?" style="flex:1;min-width:220px"><button class="btn" data-act="q-add">Add question</button></div></div>\n   <div class="row" style="margin-top:12px"><span class="muted">Good-process threshold</span><input type="number" min="50" max="100" style="width:80px" data-bind="settings|settings|threshold" data-kind="int" value="${e.threshold}"><span class="muted">% — trades at or above count as disciplined.</span></div></section>\n  <section class="sec"><div class="sec-h"><h2>Setups</h2><span class="help">Suggested when logging trades. You can also type new ones directly.</span></div>\n   <div class="surface pad"><div class="chips" style="margin-bottom:10px">${(e.setups || []).map((a, n) => `<span class="chip on">${esc(a)} <button class="link" data-act="setup-del" data-i="${n}" aria-label="Remove ${esc(a)}">×</button></span>`).join("") || '<span class="muted">No saved setups yet.</span>'}</div>\n   <div class="row"><input id="newSetup" placeholder="Setup name"><button class="btn" data-act="setup-add">Add setup</button></div></div></section>\n  <section class="sec"><div class="sec-h"><h2>Prop firms</h2></div><div class="surface pad">${S.firms.length ? S.firms.map(a => `<div class="row" style="margin-bottom:6px"><input data-bind="firms|${a.id}|name" value="${esc(a.name)}"><span class="muted">${S.accounts.filter(n => n.firm_id === a.id).length} accounts</span></div>`).join("") : '<span class="muted">Prop firms are created when you add an account.</span>'}</div></section>\n  <section class="sec"><div class="sec-h"><h2>Risk rules</h2><span class="help">Used by the trade ticket to flag oversized positions and excessive risk.</span></div><div class="surface pad"><div class="fgrid">\n    <label class="f"><span>Maximum contracts per trade</span>${bindIn("settings", "settings", "max_contracts", e.max_contracts ?? "", {
    type: "number",
    kind: "int",
    ph: "e.g. 3"
  })}</label>\n    <label class="f"><span>Maximum risk per trade</span>${bindIn("settings", "settings", "max_trade_risk_c", e.max_trade_risk_c != null ? (e.max_trade_risk_c / 100).toFixed(0) : "", {
    kind: "money",
    ph: "$"
  })}</label>\n    <div class="f"><span>&nbsp;</span><span class="help">The daily limit comes from each account's firm rules.</span></div></div></div></section>\n  <section class="sec"><div class="sec-h"><h2>Appearance</h2></div><div class="surface pad row"><span class="muted">Theme</span><div class="seg">${[ [ "auto", "Match my device" ], [ "light", "Light" ], [ "dark", "Dark" ] ].map(([a, n]) => `<button data-act="theme" data-v="${a}" class="${lsGet("tj.theme", "auto") === a ? "on" : ""}">${n}</button>`).join("")}</div>\n    <span class="muted" style="margin-left:18px">Language</span><div class="seg" data-noi18n>${[ [ "auto", LANG === "fr" ? "Automatique" : LANG === "es" ? "Automático" : "Automatic" ], [ "en", "English" ], [ "fr", "Français" ], [ "es", "Español" ] ].map(([a, n]) => `<button data-act="lang" data-v="${a}" class="${langPref() === a ? "on" : ""}">${n}</button>`).join("")}</div></div></section>\n  <section class="sec"><div class="sec-h"><h2>Copied trades</h2></div><div class="surface pad">\n    <label class="row" style="cursor:pointer"><input type="checkbox" data-act-change="merge-copies" ${e.mergeCopies !== !1 ? "checked" : ""}> Count a trade copied on several accounts as one trade when all accounts are shown</label>\n    <p class="help" style="margin:6px 0 0;max-width:75ch">Its P&amp;L is added up across accounts, so win rate, discipline and behavior statistics reflect your decisions rather than how many accounts you copy to. Per-account views always show each copy.</p></div></section>\n  <section class="sec"><div class="sec-h"><h2>Data</h2></div><div class="surface pad">\n    <p class="muted" style="margin:0 0 10px">${S.mode === "server" ? "Your journal is stored on the server and is private to your account: other traders cannot see it." : S.mode === "cloud" ? "Your journal is stored privately in this artifact — only you can read it, even if you share the page." : "Browser-only mode: data is stored in this browser. Run the included server to keep it in a database and sync across devices."} Times are entered in New York time; sessions are suggested from the entry time.</p>\n    <div class="row"><button class="btn" data-act="export">Export all data (JSON)</button><label class="btn">Import data (JSON)<input type="file" accept="application/json,.json" data-import hidden></label>\n    ${t ? '<button class="btn danger" data-act="demo-del">Remove sample data</button>' : '<button class="btn" data-act="demo">Load sample data</button>'}<span class="help">Sample data is tagged and can be removed in one click without touching your own records.</span></div></div></section>\n  <section class="sec"><div class="sec-h"><h2>Keyboard shortcuts</h2></div><div class="surface pad muted">N — add trade · 1–7 — switch section · / — search trades · J / K — next / previous trade · Esc — close panel · ⌘/Ctrl + Enter — save trade</div></section>\n  ${planSettings()}${aiSettings()}${aboutSweep()}`;
}

const REC = {
  code: null
}, ADM = {
  users: null,
  loading: !1,
  err: "",
  reg: "closed",
  invite: "",
  reset: "recovery",
  max: 0,
  temp: null
};

function loadAdmin() {
  ADM.loading || (ADM.loading = !0, apiJSON("api/admin/users").then(e => {
    ADM.users = e.users, ADM.reg = e.registration, ADM.invite = e.invite_code || "", 
    ADM.max = e.max_users, ADM.reset = e.reset_method || "recovery", ADM.prov = e.providers || {}, 
    ADM.err = "";
  }).catch(e => {
    ADM.err = e.message;
  }).finally(() => {
    ADM.loading = !1, route().v === "admin" && render();
  }));
}

function accountSection() {
  return S.mode !== "server" || !S.me ? "" : `<section><div class="sec-h"><h2>Your account</h2><span class="help">Signed in as ${esc(S.me.username)}${S.me.is_admin ? " · administrator" : ""}</span><button class="btn sm" data-act="logout" style="margin-left:auto">Log out</button></div>\n   <div class="surface pad">\n    <form data-form="email" class="fgrid" autocomplete="on" style="margin-bottom:18px;padding-bottom:16px;border-bottom:1px solid var(--line)">\n      <label class="f"><span>Email</span><input type="email" name="email" value="${esc(S.me.email || "")}" autocomplete="email" required placeholder="you@example.com"></label>\n      <label class="f"><span>Current password</span><input type="password" name="password" autocomplete="current-password" required></label>\n      <div class="f"><span>&nbsp;</span><div><button class="btn" type="submit">${S.me.email ? "Change email" : "Add email"}</button></div></div>\n      ${S.me.email ? "" : '<p class="help f full" style="margin:0">Add an email so you can reset your password if you forget it.</p>'}\n    </form>\n    <form data-form="password" class="fgrid" autocomplete="on">\n      <input type="text" name="username" value="${esc(S.me.username)}" autocomplete="username" hidden>\n      <label class="f"><span>Current password</span><input type="password" name="current" autocomplete="current-password" required></label>\n      <label class="f"><span>New password</span><input type="password" name="new" autocomplete="new-password" required placeholder="10+ characters"></label>\n      <div class="f"><span>&nbsp;</span><div><button class="btn" type="submit">Change password</button></div></div>\n    </form>\n    <p class="help" style="margin:8px 0 0">Changing your password signs you out on your other devices.</p>\n    <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--line)">\n      <h3 style="margin-bottom:6px">Recovery code</h3>\n      <p class="muted" style="margin:0 0 10px;max-width:70ch">${S.me.has_recovery ? `Saved${S.me.recovery_created ? " on " + fdate(S.me.recovery_created.slice(0, 10), {
    month: "short",
    day: "numeric",
    year: "numeric"
  }) : ""}. With your username and this code, you can reset your password from the sign-in page if you forget it. Generating a new code replaces the old one.` : "You have no recovery code yet. Generate one so you can reset your password yourself if you forget it."}</p>\n      ${REC.code ? `<div class="surface pad" style="border-color:var(--disc);margin-bottom:10px"><div class="row"><code style="font-size:17px;letter-spacing:.06em">${esc(REC.code)}</code><button class="btn sm" data-act="copy" data-v="${esc(REC.code)}">Copy</button><button class="link" data-act="rec-hide">I saved it</button></div><p class="help" style="margin:8px 0 0">Shown only once. Keep it in a password manager or a private note.</p></div>` : ""}\n      <form data-form="recovery" class="row"><input type="password" name="password" placeholder="Current password" autocomplete="current-password"><button class="btn" type="submit">${S.me.has_recovery ? "Generate a new code" : "Generate my recovery code"}</button></form>\n    </div>\n    <details class="more"><summary>Delete my account</summary>\n      <p class="muted" style="margin:0 0 10px;max-width:70ch">Deletes your account and all your data: trades, journals, accounts, payouts, expenses and screenshots. This cannot be undone. Export your data first if you want a copy.</p>\n      <form data-form="delete-account" class="row"><input type="password" name="password" placeholder="Your password" autocomplete="current-password"><button class="btn danger" type="submit">Delete my account and data</button></form>\n    </details>\n   </div></section>`;
}

function vAdmin() {
  if (!S.me || !S.me.is_admin) return '<div class="empty">Administrators only.</div>';
  if (!ADM.users && !ADM.err) return loadAdmin(), '<div class="empty">Loading traders…</div>';
  if (ADM.err) return `<div class="empty">Could not load traders: ${esc(ADM.err)}. <button class="link" data-act="adm-refresh">Try again</button></div>`;
  const e = location.origin + location.pathname + "#register", t = {
    open: "Open to anyone with the link",
    invite: "Invite code required",
    closed: "Closed"
  }[ADM.reg], a = ADM.users, n = i => i ? (i / 1048576).toFixed(i < 10485760 ? 1 : 0) + " MB" : "—", s = a.map(i => {
    const o = i.id === S.me.id, r = o || i.is_admin;
    return `<tr class="${i.disabled ? "thin" : ""}"><td>${esc(i.username)}${o ? ' <span class="faint">(you)</span>' : ""}</td><td class="muted">${i.has_recovery ? "Saved" : '<span class="faint">Not set</span>'}</td><td>${i.is_admin ? '<span class="pill approved">Admin</span>' : "Trader"}</td><td>${admPlanCell(i)}</td><td>${i.disabled ? '<span class="pill rejected">Disabled</span>' : '<span class="pill paid">Active</span>'}</td>\n      <td class="muted">${i.created_at ? fdate(i.created_at.slice(0, 10), {
      month: "short",
      day: "numeric",
      year: "numeric"
    }) : "—"}</td><td class="muted">${i.last_login ? fdate(i.last_login.slice(0, 10), {
      month: "short",
      day: "numeric",
      year: "numeric"
    }) : "Never"}</td>\n      <td class="num">${i.trades}</td><td class="num">${n(i.upload_bytes)}</td>\n      <td class="num"><button class="link" data-act="adm-manage" data-id="${esc(i.id)}">Manage</button>${r ? "" : ` · <button class="link" data-act="adm-reset" data-id="${esc(i.id)}" data-v="${esc(i.username)}">Reset password</button> · <button class="link" data-act="${i.disabled ? "adm-enable" : "adm-disable"}" data-id="${esc(i.id)}" data-v="${esc(i.username)}">${i.disabled ? "Enable" : "Disable"}</button> · <button class="link" data-act="adm-del" data-id="${esc(i.id)}" data-v="${esc(i.username)}" style="color:var(--neg)">Delete</button>`}</td></tr>`;
  }).join("");
  return `<div class="statline"><div><span>Traders</span><span>${a.length}${ADM.max ? ` <span class="faint" style="font-weight:400">of ${ADM.max} max</span>` : ""}</span></div><div><span>Active this month</span><span>${a.filter(i => i.last_login && i.last_login.slice(0, 7) === todayStr().slice(0, 7)).length}</span></div><div><span>Registration</span><span>${t}</span></div></div>\n  <div class="sec-h"><h2>Access</h2></div>\n  <form class="surface pad" data-form="access" style="margin-bottom:18px" autocomplete="off">\n    <div class="fgrid">\n      <label class="f"><span>Who can sign up</span><select name="registration">${opts([ [ "invite", "Anyone with the invite code" ], [ "open", "Anyone with the link" ], [ "closed", "Nobody (closed)" ] ], ADM.reg)}</select></label>\n      <div class="f"><span>Invite code</span><div class="row" style="flex-wrap:nowrap"><input name="invite_code" value="${esc(ADM.invite)}" placeholder="e.g. NQ-DISCORD-2026" style="flex:1;min-width:0"><button class="btn sm" type="button" data-act="gen-invite">Generate</button></div></div>\n      <label class="f"><span>${tip("Forgot password", "Personal recovery code: each trader gets a private code at sign-up. Invite code: any trader can reset with the shared invite code (not administrators).")}</span><select name="reset_method">${opts([ [ "recovery", "Username + personal recovery code" ], [ "invite", "Username + invite code" ], [ "off", "Off — ask the administrator" ] ], ADM.reset)}</select></label>\n    </div>\n    ${ADM.reset === "invite" ? `<p class="help" style="margin:10px 0 0;color:var(--warn)">With “invite code”, any member who knows another member's username can reset their password and open their journal. Personal recovery codes still work too.</p>` : ""}\n    <div class="row" style="margin-top:12px"><button class="btn primary" type="submit">Save access settings</button>\n    ${ADM.reg !== "closed" ? `<span class="muted" style="margin-left:8px">Sign-up link:</span><code style="font-size:12.5px">${esc(e)}</code><button class="btn sm" type="button" data-act="copy" data-v="${esc(e)}">Copy link</button>${ADM.reg === "invite" && ADM.invite ? `<button class="btn sm" type="button" data-act="copy" data-v="${esc(ADM.invite)}">Copy invite code</button>` : ""}` : ""}</div>\n    <p class="help" style="margin:8px 0 0">Changing the invite code stops old invitations. Existing accounts are not affected.</p>\n  </form>\n  ${ADM.temp ? `<div class="surface pad" style="margin-bottom:18px;border-color:var(--disc)"><div class="row"><span>Temporary password for <b>${esc(ADM.temp.name)}</b>:</span><code style="font-size:14px">${esc(ADM.temp.pw)}</code><button class="btn sm" data-act="copy" data-v="${esc(ADM.temp.pw)}">Copy</button><button class="link" data-act="adm-temp-hide">Hide</button></div><p class="help" style="margin:8px 0 0">Send it privately (Discord DM). They sign in with it, then change it in Settings. It is not shown again.</p></div>` : ""}\n  <div class="sec-h"><h2>Traders</h2><button class="link" data-act="adm-refresh">Refresh</button></div>\n  <div class="surface"><div class="scroll-x"><table class="tbl trd-tbl"><thead><tr><th>Username</th><th>${tip("Recovery code", "Whether the trader has a personal recovery code to reset a forgotten password.")}</th><th>Role</th><th>Plan</th><th>Status</th><th>Joined</th><th>Last sign-in</th><th class="num">Trades</th><th class="num">Screenshots</th><th></th></tr></thead><tbody>${s}</tbody></table></div></div>\n  <div class="surface pad row" style="margin-top:18px"><span class="muted">Data providers</span><span>Economic calendar: <b>${esc({
    fmp: "Financial Modeling Prep",
    finnhub: "Finnhub",
    manual: "manual entry"
  }[(ADM.prov || {}).econ] || "manual entry")}</b></span><span class="faint">·</span><span>Market data: <b>${(ADM.prov || {}).market === "databento" ? "Databento" : "not configured"}</b></span><span class="help">Set in config.php</span></div>\n  <p class="help" style="margin-top:10px;max-width:75ch">Traders' journals are private: this page shows account information and usage only, never their trades or notes.</p>\n  ${aiUsageSection()}${attributionSection()}${growthAdmin()}`;
}

async function admAction(e, t, a) {
  try {
    if (e === "reset") {
      if (!confirm(`Reset the password of ${a}? They will be signed out and need the new temporary password.`)) return;
      const n = await apiJSON("api/admin/users/" + encodeURIComponent(t) + "/reset", {
        method: "POST"
      });
      ADM.temp = {
        name: a,
        pw: n.password
      };
    } else if (e === "disable") {
      if (!confirm(`Disable ${a}? They are signed out and cannot sign in. Their data is kept.`)) return;
      await apiJSON("api/admin/users/" + encodeURIComponent(t) + "/disable", {
        method: "POST"
      }), toast(a + " disabled");
    } else if (e === "enable") await apiJSON("api/admin/users/" + encodeURIComponent(t) + "/enable", {
      method: "POST"
    }), toast(a + " enabled"); else if (e === "delete") {
      const n = prompt(`This permanently deletes ${a} and all of their data, including screenshots.\nType the username to confirm:`);
      if (n === null) return;
      if (n.trim() !== a) {
        toast("The username did not match. Nothing was deleted.");
        return;
      }
      await apiJSON("api/admin/users/" + encodeURIComponent(t) + "?_method=DELETE", {
        method: "POST"
      }), toast(a + " deleted");
    }
  } catch (n) {
    toast(n.message);
    return;
  }
  ADM.users = null, render();
}

async function saveAccess(e) {
  const t = e.elements;
  try {
    await apiJSON("api/admin/settings", {
      method: "POST",
      body: {
        registration: t.registration.value,
        invite_code: t.invite_code.value.trim(),
        reset_method: t.reset_method.value
      }
    }), toast("Access settings saved"), ADM.users = null, render();
  } catch (a) {
    toast(a.message);
  }
}

function genInvite() {
  const e = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let t = "";
  crypto.getRandomValues(new Uint8Array(8)).forEach((s, i) => {
    i === 4 && (t += "-"), t += e[s % 32];
  });
  const n = $('form[data-form="access"] [name="invite_code"]');
  n && (n.value = t, n.focus());
}

async function changePassword(e) {
  const t = e.elements.current.value, a = e.elements.new.value;
  if (a.length < 10) {
    toast("New password: at least 10 characters.");
    return;
  }
  try {
    await apiJSON("api/account/password", {
      method: "POST",
      body: {
        current: t,
        new: a
      }
    }), e.reset(), toast("Password changed");
  } catch (n) {
    toast(n.message);
  }
}

async function newRecovery(e) {
  const t = e.elements.password.value;
  if (!t) {
    toast("Enter your current password.");
    return;
  }
  if (!(S.me.has_recovery && !confirm("Replace your current recovery code? The old one stops working."))) try {
    const a = await apiJSON("api/account/recovery", {
      method: "POST",
      body: {
        password: t
      }
    });
    REC.code = a.recovery_code, S.me = {
      ...S.me,
      has_recovery: !0,
      recovery_created: (new Date).toISOString()
    }, render();
  } catch (a) {
    toast(a.message);
  }
}

async function deleteAccount(e) {
  const t = e.elements.password.value;
  if (!t) {
    toast("Enter your password to confirm.");
    return;
  }
  if (confirm("Delete your account and all of your data permanently?")) try {
    await apiJSON("api/account?_method=DELETE", {
      method: "POST",
      body: {
        password: t
      }
    }), location.href = location.pathname;
  } catch (a) {
    toast(a.message);
  }
}

function logout() {
  apiFetch("api/auth/logout", {
    method: "POST"
  }).finally(() => {
    location.href = location.pathname;
  });
}

async function changeEmail(e) {
  const t = new FormData(e);
  try {
    const a = await apiJSON("api/me/email", {
      method: "POST",
      body: {
        email: String(t.get("email") || "").trim(),
        password: t.get("password")
      }
    });
    S.me.email = a.email, toast("Email saved"), render();
  } catch (a) {
    toast(a.message);
  }
}

const AIU = {
  days: null,
  loading: !1
};

function aiUsageSection() {
  if (!AI.on) return "";
  !AIU.days && !AIU.loading && (AIU.loading = !0, apiJSON("api/admin/ai-usage").then(a => {
    AIU.days = a.days || [], AIU.loading = !1, render();
  }).catch(() => {
    AIU.days = [], AIU.loading = !1;
  }));
  const e = AIU.days || [];
  return `<section class="sec"><div class="sec-h"><h2>Sweep AI usage</h2><span class="help">Last 14 days · $${e.reduce((a, n) => a + (+n.usd || 0), 0).toFixed(2)}</span></div><div class="surface">${e.length ? `<div class="scroll-x"><table class="tbl"><thead><tr><th>Day (UTC)</th><th class="num">Calls</th><th class="num">Traders</th><th class="num">Tokens</th><th class="num">Cost</th></tr></thead><tbody>${e.map(a => `<tr><td>${esc(a.day)}</td><td class="num">${+a.calls}</td><td class="num">${+a.users}</td><td class="num">${(+a.tokens || 0).toLocaleString("en-US")}</td><td class="num">$${(+a.usd || 0).toFixed(4)}</td></tr>`).join("")}</tbody></table></div>` : `<div class="empty">${AIU.days ? "No AI calls yet." : "Loading…"}</div>`}</div></section>`;
}

const PLN = {
  en: {
    free: "Free",
    pro: "Pro",
    elite: "Elite"
  },
  fr: {
    free: "Gratuit",
    pro: "Pro",
    elite: "Elite"
  },
  es: {
    free: "Gratis",
    pro: "Pro",
    elite: "Elite"
  }
}, AL2 = () => ({
  en: {
    trial: "Trial",
    permanent: "Permanent",
    paid: "Paid",
    early: "Early access",
    signup: "Sign-up trial",
    config: "Permanent (config)",
    pre: "Before launch",
    left: e => `${e} d left`,
    manage: "Manage",
    title: "Plan and role",
    current: "Current access",
    give: "Give access",
    type: "Type",
    plan: "Plan",
    days: "Length",
    apply: "Apply",
    remove: "Remove the access you gave",
    role: "Role",
    trader: "Trader",
    admin: "Administrator",
    roleHelp: "Administrators can manage traders, sign-ups and this page.",
    note: "A paid subscription always stays in place. What you give here adds to it and replaces what you gave before.",
    saved: "Access updated",
    removed: "Access removed",
    roleSaved: "Role updated",
    self: "You can’t change your own role.",
    off: "Plans are not set up yet (billing-config.php).",
    until: e => `until ${e}`
  },
  fr: {
    trial: "Essai",
    permanent: "Permanent",
    paid: "Payé",
    early: "Accès anticipé",
    signup: "Essai d'inscription",
    config: "Permanent (config)",
    pre: "Avant le lancement",
    left: e => `${e} j restants`,
    manage: "Gérer",
    title: "Abonnement et rôle",
    current: "Accès actuel",
    give: "Donner un accès",
    type: "Type",
    plan: "Abonnement",
    days: "Durée",
    apply: "Appliquer",
    remove: "Retirer l'accès que tu as donné",
    role: "Rôle",
    trader: "Trader",
    admin: "Administrateur",
    roleHelp: "Les administrateurs gèrent les traders, les inscriptions et cette page.",
    note: "Un abonnement payé reste toujours en place. Ce que tu donnes ici s'y ajoute et remplace ce que tu avais donné avant.",
    saved: "Accès mis à jour",
    removed: "Accès retiré",
    roleSaved: "Rôle mis à jour",
    self: "Tu ne peux pas changer ton propre rôle.",
    off: "Les abonnements ne sont pas configurés (billing-config.php).",
    until: e => `jusqu'au ${e}`
  },
  es: {
    trial: "Prueba",
    permanent: "Permanente",
    paid: "Pagado",
    early: "Acceso anticipado",
    signup: "Prueba de registro",
    config: "Permanente (config)",
    pre: "Antes del lanzamiento",
    left: e => `${e} d restantes`,
    manage: "Gestionar",
    title: "Plan y rol",
    current: "Acceso actual",
    give: "Dar acceso",
    type: "Tipo",
    plan: "Plan",
    days: "Duración",
    apply: "Aplicar",
    remove: "Quitar el acceso que diste",
    role: "Rol",
    trader: "Trader",
    admin: "Administrador",
    roleHelp: "Los administradores gestionan traders, registros y esta página.",
    note: "Una suscripción pagada siempre se mantiene. Lo que das aquí se suma y reemplaza lo que diste antes.",
    saved: "Acceso actualizado",
    removed: "Acceso retirado",
    roleSaved: "Rol actualizado",
    self: "No puedes cambiar tu propio rol.",
    off: "Las suscripciones no están configurados (billing-config.php).",
    until: e => `hasta el ${e}`
  }
}[LANG] || null);

function admSrc(e) {
  const t = AL2();
  if (!e) return "";
  const a = e.ends_at ? Math.max(0, Math.ceil((e.ends_at * 1e3 - Date.now()) / 864e5)) : null;
  return {
    admin_trial: t.trial + (a != null ? " · " + t.left(a) : ""),
    permanent: t.permanent,
    comp: t.config,
    comp_grant: t.permanent + (a != null ? " · " + t.left(a) : ""),
    subscription: t.paid + (e.sub && e.sub.status !== "active" ? " · " + e.sub.status : ""),
    early_access: t.early + (a != null ? " · " + t.left(a) : ""),
    trial: t.signup + (a != null ? " · " + t.left(a) : ""),
    prelaunch: t.pre,
    free: ""
  }[e.source] ?? e.source;
}

function admPlanCell(e) {
  const t = e.plan;
  if (!t) return '<span class="faint">—</span>';
  const a = AL2();
  return `<span class="admplan" data-noi18n><span class="plan-chip p-${esc(t.plan)}">${esc(PLN[LANG][t.plan] || t.plan)}</span>${admSrc(t) ? `<small>${esc(admSrc(t))}</small>` : ""}</span>`;
}

const ADMS = {
  id: null,
  type: "trial",
  plan: "pro",
  days: 14,
  busy: !1
};

function admManage(e) {
  ADMS.id = e, ADMS.type = "trial", ADMS.plan = "pro", ADMS.days = 14;
  let t = $("#admSheet");
  if (!t) {
    t = document.createElement("aside"), t.id = "admSheet", t.className = "evp admsh", 
    t.setAttribute("data-noi18n", ""), t.innerHTML = '<div class="evp-in adm-in"></div>', 
    document.body.append(t);
    const a = document.createElement("div");
    a.id = "admScrim", a.className = "evp-scrim", a.addEventListener("click", admClose), 
    document.body.append(a), t.addEventListener("click", admClick), t.addEventListener("input", n => {
      n.target.name === "days" && (ADMS.days = Math.max(1, Math.min(365, +n.target.value || 1)));
    }), swipeDismiss(t, {
      scroller: () => t.querySelector(".adm-in"),
      onClose: admClose
    });
  }
  admRender(), requestAnimationFrame(() => {
    t.classList.add("open"), $("#admScrim").classList.add("open"), document.body.classList.add("evp-lock");
  });
}

function admClose() {
  const e = $("#admSheet");
  e && (e.classList.remove("open"), $("#admScrim").classList.remove("open"), document.body.classList.remove("evp-lock"));
}

function admRender() {
  const e = $("#admSheet .adm-in"), t = (ADM.users || []).find(r => r.id === ADMS.id);
  if (!e || !t) return;
  const a = AL2(), n = t.id === S.me.id, s = t.plan, i = (r, c) => `<div class="seg adm-seg">${c.map(([l, p]) => `<button type="button" data-adm="${r}" data-v="${l}" class="${String(ADMS[r]) === String(l) ? "on" : ""}">${p}</button>`).join("")}</div>`, o = s && [ "admin_trial", "permanent", "comp_grant" ].includes(s.source);
  e.innerHTML = `<div class="tk-head"><div><span class="stepl">${esc(t.username)}</span><h2>${a.title}</h2></div><button class="link" data-adm-close>✕</button></div>\n   <section class="adm-sec"><h3>${a.current}</h3>${s ? `<div class="adm-cur"><span class="plan-chip p-${esc(s.plan)}">${esc(PLN[LANG][s.plan])}</span><span class="muted">${esc(admSrc(s) || "")}</span></div>` : `<p class="muted">${a.off}</p>`}</section>\n   ${s ? `<section class="adm-sec"><h3>${a.give}</h3>\n     <label class="adm-l">${a.type}</label>${i("type", [ [ "trial", a.trial ], [ "permanent", a.permanent ] ])}\n     <label class="adm-l">${a.plan}</label>${i("plan", [ [ "pro", "Pro" ], [ "elite", "Elite" ] ])}\n     ${ADMS.type === "trial" ? `<label class="adm-l">${a.days}</label><div class="adm-days">${[ 7, 14, 30, 90 ].map(r => `<button type="button" class="chip ${ADMS.days === r ? "on" : ""}" data-adm="days" data-v="${r}">${r} ${LANG === "en" ? "days" : LANG === "fr" ? "jours" : "días"}</button>`).join("")}<input name="days" type="number" min="1" max="365" value="${ADMS.days}" inputmode="numeric" aria-label="${a.days}"></div>` : ""}\n     <button class="btn primary adm-apply" data-adm-do="apply" ${ADMS.busy ? "disabled" : ""}>${a.apply}</button>\n     ${o ? `<button class="link adm-remove" data-adm-do="remove">${a.remove}</button>` : ""}\n     <p class="help">${a.note}</p></section>` : ""}\n   <section class="adm-sec"><h3>${{
    en: "How they found Sweep",
    fr: "Comment il a découvert Sweep",
    es: "Cómo descubrió Sweep"
  }[LANG]}</h3>\n     <dl class="adm-acq">${[ [ "Source", [ t.utm_source, t.utm_medium, t.utm_campaign ].filter(Boolean).join(" / ") ], [ "Post", t.utm_content ], [ {
    en: "Answer",
    fr: "Réponse",
    es: "Respuesta"
  }[LANG], [ t.found_via, t.found_video ].filter(Boolean).join(" · ") ], [ {
    en: "Accounts",
    fr: "Comptes",
    es: "Cuentas"
  }[LANG], t.accounts_info ] ].map(([r, c]) => `<dt>${r}</dt><dd>${c ? esc(c) : '<span class="faint">—</span>'}</dd>`).join("")}</dl>\n     <label class="adm-int"><span>${{
    en: "Internal / test account (not counted on the /100 page)",
    fr: "Compte interne / de test (non compté sur la page /100)",
    es: "Cuenta interna / de prueba (no cuenta en la página /100)"
  }[LANG]}</span><span class="sw"><input type="checkbox" data-adm-internal ${+t.is_internal ? "checked" : ""}><i></i></span></label></section>\n   <section class="adm-sec"><h3>${a.role}</h3>${n ? `<p class="muted">${a.self}</p>` : i("role", [ [ "trader", a.trader ], [ "admin", a.admin ] ]).replace(`data-v="${t.is_admin ? "admin" : "trader"}" class="`, `data-v="${t.is_admin ? "admin" : "trader"}" class="on `)}<p class="help">${a.roleHelp}</p></section>`;
}

document.addEventListener("change", async e => {
  if (!e.target.matches || !e.target.matches("[data-adm-internal]")) return;
  const t = (ADM.users || []).find(a => a.id === ADMS.id);
  if (t) try {
    await apiJSON(`api/admin/users/${encodeURIComponent(ADMS.id)}/internal`, {
      method: "POST",
      body: {
        internal: e.target.checked
      }
    }), t.is_internal = e.target.checked ? 1 : 0, toast(AL2().saved);
  } catch (a) {
    toast(a.message), e.target.checked = !e.target.checked;
  }
});

async function admClick(e) {
  const t = AL2();
  if (e.target.closest("[data-adm-close]")) return admClose();
  const a = e.target.closest("[data-adm]");
  if (a) {
    const s = a.dataset.adm, i = a.dataset.v;
    if (s === "role") {
      const o = ADM.users.find(c => c.id === ADMS.id), r = i === "admin";
      if (o.is_admin === r) return;
      try {
        await apiJSON(`api/admin/users/${encodeURIComponent(ADMS.id)}/role`, {
          method: "POST",
          body: {
            admin: r
          }
        }), o.is_admin = r, toast(t.roleSaved), admRender(), render();
      } catch (c) {
        toast(c.message);
      }
      return;
    }
    ADMS[s] = s === "days" ? +i : i, admRender();
    return;
  }
  const n = e.target.closest("[data-adm-do]");
  if (n) {
    ADMS.busy = !0, admRender();
    try {
      const s = n.dataset.admDo === "remove" ? {
        action: "remove"
      } : {
        action: ADMS.type,
        plan: ADMS.plan,
        days: ADMS.days
      }, i = await apiJSON(`api/admin/users/${encodeURIComponent(ADMS.id)}/plan`, {
        method: "POST",
        body: s
      }), o = ADM.users.find(r => r.id === ADMS.id);
      o && (o.plan = i.plan), toast(n.dataset.admDo === "remove" ? t.removed : t.saved), 
      haptic && haptic(8), ADMS.id === S.me.id && window.SweepBilling && SweepBilling.refresh && SweepBilling.refresh(), 
      render();
    } catch (s) {
      toast(s.message);
    }
    ADMS.busy = !1, admRender();
  }
}

const ATT = {
  since: "2026-10-05",
  rows: null,
  loading: !1
};

function attributionSection() {
  !ATT.rows && !ATT.loading && (ATT.loading = !0, apiJSON("api/admin/attribution?since=" + ATT.since).then(a => {
    ATT.rows = a.rows || [], ATT.loading = !1, render();
  }).catch(() => {
    ATT.rows = [], ATT.loading = !1;
  }));
  const e = ATT.rows || [], t = a => e.reduce((n, s) => n + s[a], 0);
  return `<section class="sec" data-noi18n><div class="sec-h"><h2>${{
    en: "Campaign attribution",
    fr: "Attribution des campagnes",
    es: "Atribución de campañas"
  }[LANG]}</h2>\n    <label class="att-since">${{
    en: "Since",
    fr: "Depuis",
    es: "Desde"
  }[LANG]} <input type="date" value="${ATT.since}" data-att-since></label><button class="btn sm" data-act="att-copy">${{
    en: "Copy for the sheet",
    fr: "Copier pour le tableur",
    es: "Copiar para la hoja"
  }[LANG]}</button></div>\n    <div class="surface"><div class="scroll-x"><table class="tbl att-tbl"><thead><tr><th>Post</th><th>Source</th><th class="num">Sign-ups</th><th class="num">Activated</th><th class="num">3+ days</th><th class="num">D7</th><th class="num">D14</th></tr></thead>\n    <tbody>${e.map(a => `<tr><td>${esc(a.post_id)}</td><td class="muted">${esc(a.source)}</td><td class="num">${a.signups}</td><td class="num">${a.activated}</td><td class="num">${a.three_days}</td><td class="num">${a.d7}</td><td class="num">${a.d14}</td></tr>`).join("") || `<tr><td colspan="7" class="muted">${ATT.rows ? "—" : "…"}</td></tr>`}\n    ${e.length ? `<tr class="total"><td>Total</td><td></td><td class="num">${t("signups")}</td><td class="num">${t("activated")}</td><td class="num">${t("three_days")}</td><td class="num">${t("d7")}</td><td class="num">${t("d14")}</td></tr>` : ""}</tbody></table></div></div>\n    <p class="help">${{
    en: "Activated = 1 account and 1 trade. D7 / D14 = logged a trade 7–13 / 14–20 days after sign-up. Internal accounts and administrators are excluded.",
    fr: "Activé = 1 compte et 1 trade. J7 / J14 = un trade enregistré 7 à 13 / 14 à 20 jours après l’inscription. Comptes internes et administrateurs exclus.",
    es: "Activado = 1 cuenta y 1 operación. D7 / D14 = una operación registrada 7–13 / 14–20 días después del registro. Cuentas internas y administradores excluidos."
  }[LANG]}</p></section>`;
}

document.addEventListener("change", e => {
  e.target.matches && e.target.matches("[data-att-since]") && e.target.value && (ATT.since = e.target.value, 
  ATT.rows = null, render());
});

function attCopy() {
  const t = [ "post_id\tsource\tsignups\tactivated\tthree_days\td7\td14", ...(ATT.rows || []).map(a => [ a.post_id, a.source, a.signups, a.activated, a.three_days, a.d7, a.d14 ].join("\t")) ].join(`\n`);
  navigator.clipboard.writeText(t).then(() => toast({
    en: "Copied",
    fr: "Copié",
    es: "Copiado"
  }[LANG])).catch(() => prompt("", t));
}

const DD_TYPES = [ [ "eod", "Trailing — end of day" ], [ "trade", "Trailing — trade by trade" ], [ "static", "Static" ] ];

function hasRules(e) {
  const t = e.rules || {};
  return !!(t.target_c || t.dd_c || t.dll_c || t.consistency_pct || t.min_days);
}

function evalMissLabel(e) {
  const t = typeof LANG == "string" ? LANG : "en", a = e.map(([n, s, i, m]) => n === "cons" ? t === "fr" ? `consistance ${i} % (max ${s} %)` : t === "es" ? `consistencia ${i} % (máx. ${s} %)` : `consistency ${i}% (max ${s}%)` : m == null ? t === "fr" ? `${s} jour${s > 1 ? "s" : ""} de plus` : t === "es" ? `${s} día${s > 1 ? "s" : ""} más` : `${s} more day${s > 1 ? "s" : ""}` : t === "fr" ? `${i} jour${i > 1 ? "s" : ""} sur ${m}` : t === "es" ? `${i} día${i > 1 ? "s" : ""} de ${m}` : `${i} of ${m} days`).join(" / ");
  return t === "fr" ? `Objectif atteint · il manque : ${a}` : t === "es" ? `Objetivo alcanzado · falta: ${a}` : `Target reached · still missing: ${a}`;
}

function acctFlag(e) {
  let t;
  try {
    t = acctState(e);
  } catch (n) {
    return null;
  }
  const a = typeof LANG == "string" ? LANG : "en";
  return t.breached ? {
    k: "br",
    t: {
      fr: "Drawdown dépassé",
      es: "Drawdown superado"
    }[a] || "Drawdown exceeded",
    st: t
  } : t.dll && -t.today >= t.dll ? {
    k: "dl",
    t: {
      fr: "Limite du jour atteinte",
      es: "Límite diario alcanzado"
    }[a] || "Daily limit reached",
    st: t
  } : {
    k: "",
    t: "",
    st: t
  };
}

function acctSortBreachLast(e) {
  const t = new Map(e.map(a => [ a.id, (acctFlag(a) || {}).k === "br" ? 1 : 0 ]));
  return e.slice().sort((a, n) => t.get(a.id) - t.get(n.id));
}

function acctLine(e) {
  const t = acctFlag(e);
  if (!t) return "";
  const a = t.st, n = typeof LANG == "string" ? LANG : "en", s = [];
  t.k && s.push(`<span class="pill acc-flag">${esc(t.t)}</span>`);
  a.dd && s.push(`<span>${{
    fr: "Marge DD",
    es: "Margen DD"
  }[n] || "DD room"} ${moneyU(t.k === "br" ? 0 : Math.max(0, a.buffer))}</span>`);
  const i = window.SweepPayout && SweepPayout.status && SweepPayout.status(e);
  i && i.ready && s.push(`<span class="pos">${{
    fr: "Prêt pour le payout",
    es: "Listo para el payout"
  }[n] || "Ready for a payout"}</span>`);
  return s.length ? `<small class="acc-line" data-noi18n>${s.join(" · ")}</small>` : "";
}

function acctState(e) {
  const t = e.rules || {}, a = e.starting_balance_c || 0, n = sorted(S.trades.filter(H => H.account_id === e.id)), s = S.payouts.filter(H => H.account_id === e.id && H.status === "paid").reduce((H, J) => H + (J.amount_c || 0), 0), i = n.reduce((H, J) => H + tNet(J), 0), o = a + i - s;
  let r = a, c = a, l = null, p = !1;
  const PW = S.payouts.filter(H => H.account_id === e.id && H.status === "paid").map(H => ({
    d: String(H.payment_date || H.approval_date || H.request_date || H.date || ""),
    a: H.amount_c || 0
  })).sort((H, J) => H.d < J.d ? -1 : H.d > J.d ? 1 : 0);
  let PI = 0;
  const PAY = H => {
    for (;PI < PW.length && PW[PI].d && PW[PI].d < H; ) c -= PW[PI].a, PI++;
  };
  const u = t.dd_c || 0, h = t.dd_lock !== !1, m = H => h && t.dd_type !== "static" ? Math.min(H, a + (t.dd_lock_offset_c || 0)) : H;
  if (u) if (l = a - u, t.dd_type === "static") for (const H of n) PAY(H.date), c += tNet(H), 
  c <= l && (p = !0); else if (t.dd_type === "trade") for (const H of n) PAY(H.date), 
  c += tNet(H), c <= l && (p = !0), r = Math.max(r, c), l = m(r - u); else for (const H of dayMap(n).values()) {
    H.trades[0] && PAY(H.trades[0].date);
    for (const J of H.trades) c += tNet(J), c <= l && (p = !0);
    r = Math.max(r, c), l = m(r - u);
  }
  const v = n.filter(H => H.date === todayStr()).reduce((H, J) => H + tNet(J), 0), b = dayMap(n), E = [ ...b.values() ].map(H => H.net), R = E.length ? Math.max(...E) : 0, L = i, x = L > 0 && R > 0 ? R / L : null, C = l != null ? o - l : null, g = {
    bal: o,
    net: i,
    today: v,
    thr: l,
    buffer: C,
    breached: p,
    dd: u,
    target: t.target_c || 0,
    dll: t.dll_c || 0,
    consPct: t.consistency_pct || 0,
    cons: x,
    minDays: t.min_days || 0,
    days: b.size,
    payMin: t.payout_min_c || 0,
    missing: [],
    spark: (() => {
      let H = a;
      const J = [ a ];
      for (const q of b.values()) H += q.net, J.push(H);
      return J;
    })()
  };
  g.target && (g.consPct && x != null && x * 100 > g.consPct && g.missing.push([ "cons", g.consPct, Math.round(x * 100) ]), 
  g.minDays && g.days < g.minDays && g.missing.push([ "days", g.minDays - g.days, g.days, g.minDays ])), 
  g.reached = !!(g.target && L >= g.target), g.passed = g.reached && !g.missing.length && !p;
  let P = "none", O = "No rules";
  return hasRules(e) && (P = "ok", O = "In good standing", g.target && L >= g.target && (g.missing.length ? (P = "warn", 
  O = evalMissLabel(g.missing)) : (P = "target", O = "Target reached")), (u && C <= u * .25 || g.dll && -v >= g.dll * .75) && (P = "warn", 
  O = "Close to a limit"), (p || g.dll && -v >= g.dll) && (P = "breach", O = p ? "Drawdown breached" : "Daily limit hit"), 
  g.consPct && x != null && x * 100 > g.consPct && P === "ok" && (P = "warn", O = "Consistency rule")), 
  g.status = P, g.label = O, g;
}

function sparkline(e) {
  if (e.length < 2) return '<svg class="spark" viewBox="0 0 100 34"></svg>';
  const t = Math.min(...e), a = Math.max(...e), n = a - t || 1, s = e.map((i, o) => (o ? "L" : "M") + (o / (e.length - 1) * 100).toFixed(2) + " " + (31 - (i - t) / n * 28).toFixed(2)).join("");
  return `<svg class="spark" viewBox="0 0 100 34" preserveAspectRatio="none" aria-hidden="true"><path class="a" d="${s}L100 34L0 34Z"/><path class="l" d="${s}" vector-effect="non-scaling-stroke"/></svg>`;
}

const bar = (e, t) => `<div class="pbar"><i class="${t}" style="width:${Math.max(0, Math.min(100, e * 100)).toFixed(1)}%"></i></div>`;

function accountCard(e, {full: t = !1} = {}) {
  const a = acctState(e), n = firm(e.firm_id), s = [];
  let i = 0;
  if (a.dd) {
    const bf = a.breached ? 0 : Math.max(0, a.buffer), p = a.dd ? 1 - bf / a.dd : 0;
    s.push(`<div class="rule"><div class="lab"><span>${tip("Drawdown room", `Distance to the ${DD_TYPES.find(u => u[0] === ((e.rules || {}).dd_type || "eod"))[1].toLowerCase()} drawdown limit, currently at ${moneyU(a.thr)}.`)}</span><b>${moneyU(bf)}</b></div>${bar(Math.min(1, bf / a.dd), p > .75 ? "neg" : "pos")}</div>`);
  }
  a.target && s.push(`<div class="rule"><div class="lab"><span>Profit target</span><b>${moneyU(Math.max(0, a.net))} <span class="faint">/ ${moneyU(a.target)}</span></b></div>${bar(Math.max(0, a.net) / a.target, "pos")}</div>`);
  const o = a.dll && (t || a.today < 0);
  a.dll && !o && i++, o && s.push(`<div class="rule"><div class="lab"><span>Daily loss limit</span><b>${a.today < 0 ? moneyU(-a.today) : "$0"} <span class="faint">/ ${moneyU(a.dll)}</span></b></div>${bar(Math.max(0, -a.today) / a.dll, -a.today >= a.dll * .75 ? "neg" : "ink")}</div>`);
  const r = a.cons != null && a.cons * 100 > a.consPct, c = a.consPct && (t || r);
  a.consPct && !c && i++, c && s.push(`<div class="rule"><div class="lab"><span>${tip("Consistency", "Best day ÷ total profit. Must stay at or under the firm limit.")}</span><b>${a.cons == null ? "—" : Math.round(a.cons * 100) + "%"} <span class="faint">max ${a.consPct}%</span></b></div>${bar(a.cons == null ? 0 : a.cons * 100 / a.consPct, a.cons != null && a.cons * 100 > a.consPct ? "neg" : "ink")}</div>`);
  const l = a.minDays && (t || a.days < a.minDays);
  return a.minDays && !l && i++, l && s.push(`<div class="rule"><div class="lab"><span>Trading days</span><b>${a.days} <span class="faint">/ ${a.minDays}</span></b></div>${bar(a.days / a.minDays, "ink")}</div>`), 
  `<a class="acard${billFrozen(e.id) ? " is-frozen" : ""}" href="#account/${e.id}" ${billFrozen(e.id) ? "data-frozen" : ""}><div class="ac-top"><b>${esc(e.name)}${billBadge(e.id)}</b><span class="faint">${esc(n ? n.name : "")}</span></div>\n    <div class="ac-bal"><span>${cu(a.bal, "usd")}</span><div class="ac-sub"><span class="status ${a.status}">${a.label}</span><span class="${a.today ? cls(a.today) : "faint"}">${a.today ? money(a.today) + " today" : "Flat today"}</span></div></div>\n    ${sparkline(a.spark)}${s.join("") || (hasRules(e) ? "" : '<span class="help">Add your firm rules to track drawdown and target.</span>')}${i && !t ? `<span class="more-rules">${i} other rule${i > 1 ? "s" : ""} on track</span>` : ""}</a>`;
}

function rulesForm(e) {
  const t = e.rules || {}, a = S.accounts.filter(s => s.id !== e.id && hasRules(s)), n = (s, i) => bindIn("accounts", e.id, "rules." + s, i != null ? (i / 100).toFixed(0) : "", {
    kind: "money",
    ph: "$"
  });
  return `<div class="fgrid">\n    <label class="f"><span>Profit target</span>${n("target_c", t.target_c)}</label>\n    <label class="f"><span>Worst drawdown</span>${n("dd_c", t.dd_c)}</label>\n    <label class="f"><span>Drawdown type</span><select data-bind="accounts|${e.id}|rules.dd_type">${opts(DD_TYPES, t.dd_type || "eod")}</select></label>\n    <label class="f"><span>Daily loss limit</span>${n("dll_c", t.dll_c)}</label>\n    <label class="f"><span>Consistency max (%)</span>${bindIn("accounts", e.id, "rules.consistency_pct", t.consistency_pct ?? "", {
    type: "number",
    kind: "int",
    ph: "e.g. 50"
  })}</label>\n    <label class="f"><span>Minimum trading days</span>${bindIn("accounts", e.id, "rules.min_days", t.min_days ?? "", {
    type: "number",
    kind: "int"
  })}</label>\n    <label class="chk"><input type="checkbox" data-act-change="dd-lock" data-id="${e.id}" ${t.dd_lock !== !1 ? "checked" : ""}><span>Trailing drawdown stops at the starting balance</span></label>\n  </div>\n  <div class="row" style="margin-top:10px">${a.length ? `<select id="copyRulesFrom" aria-label="Copy rules from">${opts(a.map(s => [ s.id, acctLabel(s.id) ]), a[0].id)}</select><button class="btn sm" data-act="copy-rules" data-id="${e.id}">Copy rules</button>` : ""}\n  <span class="help">Enter the values of your firm's plan and check them against its current rules. Intraday trailing is approximated trade by trade.</span></div>`;
}

function perfScore(e) {
  const t = stats(e);
  if (t.n < 10) return null;
  const a = (i, o, r) => i == null || !isFinite(i) ? i === 1 / 0 ? 100 : 0 : Math.max(0, Math.min(100, (i - o) / (r - o) * 100)), n = t.days.size, s = [ [ "Win rate", a(t.wr, .3, .7) ], [ "Profit factor", a(t.pf === 1 / 0 ? 3 : t.pf, .5, 2.5) ], [ "Win / loss", a(t.rr, .5, 2.5) ], [ "Recovery", t.net > 0 ? a(t.maxDD ? t.net / -t.maxDD : 3, 0, 3) : 0 ], [ "Consistency", n ? a(t.winDays / n, .3, .7) : 0 ], [ "Discipline", t.disc == null ? 0 : t.disc ] ];
  return {
    axes: s,
    score: Math.round(s.reduce((i, o) => i + o[1], 0) / s.length),
    n: t.n
  };
}

function radar(e) {
  const o = e.length, r = (l, p) => {
    const u = -Math.PI / 2 + l * 2 * Math.PI / o;
    return [ 170 + Math.cos(u) * p, 116 + Math.sin(u) * p ];
  };
  let c = "";
  for (const l of [ .33, .66, 1 ]) c += `<polygon class="web" points="${e.map((p, u) => r(u, 80 * l).join(",")).join(" ")}"/>`;
  return e.forEach((l, p) => {
    const [u, h] = r(p, 80);
    c += `<line x1="170" y1="116" x2="${u}" y2="${h}"/>`;
  }), c += `<polygon class="val" points="${e.map((l, p) => r(p, 80 * Math.max(.04, l[1] / 100)).join(",")).join(" ")}"/>`, 
  e.forEach((l, p) => {
    const [u, h] = r(p, 96);
    c += `<text x="${u}" y="${h + 4}" text-anchor="${Math.abs(u - 170) < 5 ? "middle" : u > 170 ? "start" : "end"}">${esc(l[0])}<title>${esc(l[0])}: ${Math.round(l[1])}/100</title></text>`;
  }), `<svg class="radar" viewBox="0 0 340 230" role="img" aria-label="Performance score">${c}</svg>`;
}

function scoreBlock(e) {
  const t = perfScore(e);
  return t ? `<div class="score-wrap pad"><div><div class="muted" style="font-size:12px">${tip("Score out of 100", "Average of six measures scaled 0–100: win rate, profit factor, average win ÷ average loss, recovery (net P&L ÷ max drawdown), share of winning days, and discipline.")}</div><div class="score-num">${cu(t.score, "int")}</div><div class="help" style="margin-top:6px">${t.n} trades<br>${periodLabel()}</div></div>${radar(t.axes)}</div>` : '<div class="empty">Not enough data yet. The score needs at least 10 trades in the selected period.</div>';
}

function heatStyle(e, t) {
  if (!e || !t) return "";
  const a = (.05 + .17 * Math.min(1, Math.abs(e) / t)).toFixed(3);
  return `background:rgba(var(--${e > 0 ? "pos" : "neg"}-rgb),${a})`;
}

const IMP = {
  rows: null,
  err: "",
  file: "",
  account: null
};

function parseCSV(e) {
  const t = [];
  let a = [], n = "", s = !1;
  for (let i = 0; i < e.length; i++) {
    const o = e[i];
    s ? o === '"' ? e[i + 1] === '"' ? (n += '"', i++) : s = !1 : n += o : o === '"' ? s = !0 : o === "," ? (a.push(n), 
    n = "") : o === `\n` || o === "\r" ? (o === "\r" && e[i + 1] === `\n` && i++, a.push(n), 
    n = "", a.some(r => r !== "") && t.push(a), a = []) : n += o;
  }
  return a.push(n), a.some(i => i !== "") && t.push(a), t;
}

function tvTime(e) {
  e = String(e || "").trim();
  let t = e.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?/);
  return t ? {
    date: `${t[3]}-${pad(t[1])}-${pad(t[2])}`,
    time: `${pad(t[4])}:${t[5]}`,
    key: `${t[3]}${pad(t[1])}${pad(t[2])}${pad(t[4])}${t[5]}${t[6] || "00"}`
  } : (t = e.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?/), t ? {
    date: `${t[1]}-${t[2]}-${t[3]}`,
    time: `${t[4]}:${t[5]}`,
    key: t.slice(1, 7).join("")
  } : null);
}

function parseTradovate(e) {
  const t = parseCSV(e);
  if (t.length < 2) throw new Error("The file is empty.");
  const a = t[0].map(c => c.trim().toLowerCase()), n = c => a.indexOf(c.toLowerCase()), i = [ "symbol", "qty", "buyPrice", "sellPrice", "pnl", "boughtTimestamp", "soldTimestamp" ].filter(c => n(c) < 0);
  if (i.length) throw new Error("This does not look like a Tradovate Performance report (missing: " + i.join(", ") + ").");
  const o = new Map;
  for (const c of t.slice(1)) {
    const l = J => (c[n(J)] ?? "").trim(), p = tvTime(l("boughtTimestamp")), u = tvTime(l("soldTimestamp"));
    if (!p || !u) continue;
    const h = p.key <= u.key, m = Math.abs(parseInt(l("qty"), 10) || 0);
    if (!m) continue;
    const v = l("symbol").toUpperCase(), b = (v.match(/^(MNQ|NQ|MES|ES|MYM|YM|M2K|RTY|MCL|CL|MGC|GC)/) || [ , "NQ" ])[1];
    let E = l("pnl").replace(/[$,\s]/g, "");
    const R = /^\(.*\)$/.test(E) || E.startsWith("-");
    E = parseFloat(E.replace(/[()\-]/g, ""));
    const L = h ? l("buyFillId") || p.key : l("sellFillId") || u.key, x = `tv:${v}:${L}`, C = h ? p : u, g = h ? u : p, P = parseFloat(l(h ? "buyPrice" : "sellPrice")), O = parseFloat(l(h ? "sellPrice" : "buyPrice"));
    let H = o.get(x);
    H || (H = {
      key: x,
      inst: b,
      sym: v,
      dir: h ? "long" : "short",
      entryKey: C.key,
      date: C.date,
      entry_time: C.time,
      exit_time: g.time,
      exitKey: g.key,
      qty: 0,
      ew: 0,
      xw: 0,
      pnl_c: 0
    }, o.set(x, H)), H.qty += m, H.ew += P * m, H.xw += O * m, H.pnl_c += Math.round((R ? -1 : 1) * E * 100), 
    g.key > H.exitKey && (H.exitKey = g.key, H.exit_time = g.time);
  }
  const r = c => new Date(+c.slice(0, 4), +c.slice(4, 6) - 1, +c.slice(6, 8), +c.slice(8, 10), +c.slice(10, 12), +c.slice(12, 14)).getTime();
  return [ ...o.values() ].map(c => ({
    ...c,
    duration_s: Math.max(0, Math.round((r(c.exitKey) - r(c.entryKey)) / 1e3)),
    entry: Math.round(c.ew / c.qty * 4) / 4,
    exit: Math.round(c.xw / c.qty * 100) / 100
  })).sort((c, l) => (c.date + c.entry_time).localeCompare(l.date + l.entry_time));
}

function vImport() {
  if (!S.accounts.length) return onboarding();
  const e = IMP.account && acct(IMP.account) ? IMP.account : F.account !== "all" ? F.account : S.accounts.filter(i => i.status !== "archived")[0].id;
  IMP.account = e;
  const t = new Set(S.trades.filter(i => i.account_id === e && i.import_key).map(i => i.import_key)), a = IMP.rows || [], n = a.filter(i => !t.has(i.key)), s = n.reduce((i, o) => i + o.pnl_c, 0);
  return `<div class="row" style="margin-bottom:14px"><a class="link" href="#trades">Trades</a><span class="faint">/</span><span class="muted">Import</span></div>\n  <div class="cols"><div>\n    <div class="surface pad">\n      <div class="fgrid two" style="margin-bottom:14px"><label class="f"><span>Import into account</span><select data-imp="account">${opts(S.accounts.filter(i => i.status !== "archived").map(i => [ i.id, acctLabel(i.id) ]), e)}</select></label>\n      <div class="f"><span>Format</span><div style="padding:6px 0">Tradovate — Performance report (CSV)</div></div></div>\n      <label class="drop" id="drop"><input type="file" accept=".csv,text/csv" data-imp="file" hidden><b style="color:var(--text)">${IMP.file ? esc(IMP.file) : "Choose a CSV file"}</b><br>or drop it here</label>\n      ${IMP.err ? `<p class="err">${esc(IMP.err)}</p>` : ""}\n    </div>\n    ${a.length ? `<div class="sec-h" style="margin-top:22px"><h2>Preview</h2><span class="muted">${n.length} new · ${a.length - n.length} already imported · <span class="${cls(s)}">${money(s)}</span></span></div>\n    <div class="surface"><div class="scroll-x" style="max-height:420px;overflow:auto"><table class="tbl"><thead><tr><th>Date</th><th>Time</th><th>Symbol</th><th>Dir</th><th class="num">Qty</th><th class="num">Entry</th><th class="num">Exit</th><th class="num">P&amp;L</th><th></th></tr></thead><tbody>\n    ${a.map(i => `<tr class="${t.has(i.key) ? "thin" : ""}"><td>${fdate(i.date)}</td><td class="muted">${i.entry_time}–${i.exit_time}</td><td class="muted">${esc(i.sym)}</td><td>${dirTag(i.dir)}</td><td class="num">${i.qty}</td><td class="num">${i.entry.toFixed(2)}</td><td class="num">${i.exit.toFixed(2)}</td><td class="num ${cls(i.pnl_c)}">${money(i.pnl_c)}</td><td class="muted">${t.has(i.key) ? "Already imported" : ""}</td></tr>`).join("")}</tbody></table></div></div>\n    <div class="row" style="margin-top:12px"><button class="btn primary" data-act="imp-go" ${n.length ? "" : "disabled"}>Import ${n.length} trade${n.length === 1 ? "" : "s"}</button><button class="link" data-act="imp-reset">Clear</button></div>` : ""}\n  </div>\n  <div><div class="surface pad"><h3 style="margin-bottom:8px">How to export from Tradovate</h3>\n    <ol class="muted" style="margin:0;padding-left:18px;line-height:1.7"><li>Open <b style="color:var(--text2)">Account Reports</b> → <b style="color:var(--text2)">Performance</b>.</li><li>Pick the account and the dates.</li><li>Click <b style="color:var(--text2)">Download report</b> (CSV).</li></ol>\n    <p class="help" style="margin-top:12px">Fills of the same entry are grouped into one trade. Imported trades are never duplicated: re-importing the same file skips them. Times are used as exported — set Tradovate to New York time for accurate sessions. P&amp;L is imported as reported (gross); add fees afterwards if needed.</p></div></div></div>`;
}

async function impFile(e) {
  IMP.file = e.name, IMP.err = "", IMP.rows = null;
  try {
    IMP.rows = parseTradovate(await e.text()), IMP.rows.length || (IMP.err = "No closed trades found in this file.");
  } catch (t) {
    IMP.err = t.message;
  }
  render();
}

async function impGo() {
  const e = IMP.account, t = new Set(S.trades.filter(s => s.account_id === e && s.import_key).map(s => s.import_key)), a = (IMP.rows || []).filter(s => !t.has(s.key));
  if (!a.length) return;
  const n = a.map(s => ({
    id: uid(),
    account_id: e,
    instrument: s.inst,
    date: s.date,
    entry_time: s.entry_time,
    exit_time: s.exit_time,
    session: sessionFor(s.entry_time),
    direction: s.dir,
    contracts: s.qty,
    entry: s.entry,
    exit: s.exit,
    pnl_c: s.pnl_c,
    pnl_manual: !0,
    import_key: s.key,
    session_date: !0,
    duration_s: s.duration_s,
    discipline: {},
    emo: {},
    review: {},
    tags: [],
    shots: []
  }));
  toast(`Importing ${n.length} trades…`, {
    ms: 6e4
  });
  try {
    await bulkPut("trades", n), toast(`Imported ${n.length} trades`), IMP.rows = null, 
    IMP.file = "", location.hash = "#trades";
  } catch (s) {
    toast(saveErr(s));
  }
  render();
}

function applyTheme(e) {
  lsSet("tj.theme", e), e === "light" || e === "dark" ? document.documentElement.setAttribute("data-theme", e) : document.documentElement.removeAttribute("data-theme");
}

const RM = window.matchMedia ? matchMedia("(prefers-reduced-motion: reduce)") : {
  matches: !1
};

let ANIM = !0;

function runCountUps(e) {
  RM.matches || $$("[data-cu]", e).forEach(t => {
    const a = Number(t.dataset.cu);
    if (!isFinite(a)) return;
    const n = t.dataset.fmt || "money", s = c => n === "pct" ? Math.round(c) + "%" : n === "int" ? String(Math.round(c)) : n === "usd" ? money(Math.round(c / 100) * 100, {
      sign: !1,
      dec: 0
    }) : money(Math.round(c / 100) * 100, {
      dec: 0
    }), i = performance.now(), o = 900, r = c => {
      const l = Math.min(1, (c - i) / o), p = 1 - Math.pow(1 - l, 4);
      t.textContent = s(a * p), l < 1 ? requestAnimationFrame(r) : t.textContent = s(a);
    };
    requestAnimationFrame(r);
  });
}

const cu = (e, t = "money", a) => `<span data-cu="${Math.round(e || 0)}" data-fmt="${t}">${a ?? (t === "pct" ? Math.round(e) + "%" : t === "int" ? String(Math.round(e)) : t === "usd" ? money(Math.round((e || 0) / 100) * 100, {
  sign: !1,
  dec: 0
}) : money(Math.round((e || 0) / 100) * 100, {
  dec: 0
}))}</span>`;

function ring(e, {size: t = 64, stroke: a = 5} = {}) {
  const n = (t - a) / 2, s = 2 * Math.PI * n, i = e == null ? 0 : Math.max(0, Math.min(100, e));
  return `<svg class="ring" width="${t}" height="${t}" viewBox="0 0 ${t} ${t}" aria-hidden="true"><circle cx="${t / 2}" cy="${t / 2}" r="${n}" class="ring-bg" stroke-width="${a}"/><circle cx="${t / 2}" cy="${t / 2}" r="${n}" class="ring-fg" stroke-width="${a}" stroke-dasharray="${s.toFixed(2)}" stroke-dashoffset="${(s * (1 - i / 100)).toFixed(2)}" style="--c:${s.toFixed(2)}" transform="rotate(-90 ${t / 2} ${t / 2})"/></svg>`;
}

document.addEventListener("pointermove", e => {
  const t = e.target.closest && e.target.closest(".chartbox");
  if (!t) return;
  const a = t.querySelector("svg"), n = a.getBoundingClientRect(), s = +t.dataset.w;
  let i = t._pts;
  if (!i) try {
    i = t._pts = JSON.parse(t.dataset.pts);
  } catch {
    return;
  }
  const o = (e.clientX - n.left) / n.width * s;
  let r = i[0];
  for (const E of i) Math.abs(E[0] - o) < Math.abs(r[0] - o) && (r = E);
  const c = a.viewBox.baseVal, l = n.width / c.width, p = a.querySelector(".xh"), u = a.querySelector(".xdot"), h = t.querySelector(".ctip");
  p.setAttribute("x1", r[0]), p.setAttribute("x2", r[0]), u.setAttribute("cx", r[0]), 
  u.setAttribute("cy", r[1]), t.classList.add("hov"), h.innerHTML = `<span>${esc(r[2] || "Start")}</span><b class="${cls(r[3])}">${money(r[3])}</b>${r[4] != null ? `<i class="${cls(r[4])}">${money(r[4])}</i>` : ""}`;
  const m = t.getBoundingClientRect(), v = n.left - m.left + r[0] * l, b = n.top - m.top + r[1] * l;
  h.style.left = Math.max(60, Math.min(m.width - 60, v)) + "px", h.style.top = b + "px";
}), document.addEventListener("pointerout", e => {
  const t = e.target.closest && e.target.closest(".chartbox");
  t && !t.contains(e.relatedTarget) && t.classList.remove("hov");
});

let openSel = null;

function enhanceSelects(e = document) {
  $$("select:not([data-native]):not(.cs-done)", e).forEach(t => {
    if (t.closest(".sai")) return;
    t.classList.add("cs-done");
    const a = document.createElement("button");
    a.type = "button", a.className = "csel", a.setAttribute("aria-haspopup", "listbox"), 
    t.getAttribute("aria-label") && a.setAttribute("aria-label", t.getAttribute("aria-label")), 
    t.style.cssText && (a.style.cssText = t.style.cssText), a.innerHTML = '<span></span><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    const n = a.firstChild, s = () => {
      const i = t.options[t.selectedIndex], o = i ? i.text : "";
      n.textContent !== o && (n.textContent = o);
    };
    s(), t._sync = s, t.after(a), t._btn = a, a.addEventListener("click", () => openSelect(t)), 
    a.addEventListener("keydown", i => {
      [ "ArrowDown", "ArrowUp", "Enter", " " ].includes(i.key) && (i.preventDefault(), 
      openSelect(t));
    });
  });
}

function closeSelect() {
  openSel && (openSel.pop.remove(), openSel.btn.classList.remove("open"), openSel = null);
}

function openSelect(e) {
  if (openSel && openSel.sel === e) {
    closeSelect();
    return;
  }
  closeSelect();
  const t = e._btn, a = t.getBoundingClientRect(), n = document.createElement("div");
  n.className = "cpop", n.setAttribute("role", "listbox"), n.innerHTML = [ ...e.options ].map((l, p) => `<button type="button" role="option" data-i="${p}" class="${p === e.selectedIndex ? "on" : ""}">${esc(l.text)}</button>`).join(""), 
  document.body.append(n);
  const s = Math.min(n.scrollHeight, 320), i = innerHeight - a.bottom > s + 12;
  n.style.minWidth = a.width + "px", n.style.left = Math.min(a.left, innerWidth - n.offsetWidth - 8) + "px", 
  n.style.top = (i ? a.bottom + 6 : a.top - s - 6) + "px", t.classList.add("open"), 
  openSel = {
    sel: e,
    pop: n,
    btn: t
  };
  let o = Math.max(0, e.selectedIndex);
  const r = [ ...n.children ];
  r[o] && (r[o].focus({
    preventScroll: !0
  }), r[o].scrollIntoView({
    block: "nearest"
  })), n.addEventListener("click", l => {
    const p = l.target.closest("[data-i]");
    p && c(+p.dataset.i);
  }), n.addEventListener("keydown", l => {
    l.key === "ArrowDown" || l.key === "ArrowUp" ? (l.preventDefault(), o = Math.max(0, Math.min(r.length - 1, o + (l.key === "ArrowDown" ? 1 : -1))), 
    r[o].focus({
      preventScroll: !0
    }), r[o].scrollIntoView({
      block: "nearest"
    })) : l.key === "Escape" ? (l.stopPropagation(), closeSelect(), t.focus()) : l.key === "Tab" && closeSelect();
  });
  function c(l) {
    e.selectedIndex = l, e._sync(), closeSelect(), t.focus(), e.dispatchEvent(new Event("change", {
      bubbles: !0
    }));
  }
}

document.addEventListener("pointerdown", e => {
  openSel && !openSel.pop.contains(e.target) && !openSel.btn.contains(e.target) && closeSelect();
}), addEventListener("scroll", e => {
  openSel && (openSel.pop === e.target || openSel.pop.contains(e.target)) || closeSelect();
}, !0), addEventListener("resize", () => closeSelect()), new MutationObserver(e => {
  let t = !1;
  for (const a of e) {
    for (const n of a.addedNodes) if (n.nodeType === 1 && (n.tagName === "SELECT" || n.querySelector && n.querySelector("select:not(.cs-done)"))) {
      t = !0;
      break;
    }
    if (t) break;
  }
  !t || enhanceSelects.q || (enhanceSelects.q = !0, requestAnimationFrame(() => {
    enhanceSelects.q = !1, enhanceSelects();
  }));
}).observe(document.body, {
  childList: !0,
  subtree: !0
}), document.addEventListener("change", e => {
  e.target.tagName === "SELECT" && e.target._sync && e.target._sync();
}, !0);

const CMD = {
  open: !1,
  q: "",
  i: 0,
  items: []
};

function cmdItems(e) {
  e = e.trim().toLowerCase();
  const t = [], a = [ [ "Today", "#dashboard" ], [ "Trades", "#trades" ], [ "Calendar", "#calendar" ], [ "Journal — today", "#journal/" + todayStr() ], [ "Journal — week", "#journal/weekly" ], [ "Stats", "#analytics" ], [ "Accounts", "#accounts" ], [ "Payouts & expenses", "#payouts" ], [ "Import trades (CSV)", "#import" ], [ "Settings", "#settings" ] ];
  S.me && S.me.is_admin && a.push([ "Traders", "#admin" ]);
  const n = [ [ "New trade", () => openTicket(null) ], ...BILL.off ? [] : [ [ "Subscription", () => {
    location.hash = "#plan";
  } ] ], [ "Share this week", () => openShare("week", todayStr()) ], [ "Share net after fees", () => openShare("net", "all") ], ...AI.on ? [ [ "Sweep AI: log trades in plain words", () => aiOpen("log") ], [ "Sweep AI: ask your journal", () => aiOpen("ask") ], [ "Sweep AI: weekly review", () => aiOpen("review") ], [ "Sweep AI: scan a receipt", () => aiOpen("scan") ] ] : [], [ "Switch to dark theme", () => {
    applyTheme("dark"), render();
  } ], [ "Switch to light theme", () => {
    applyTheme("light"), render();
  } ], [ "Match device theme", () => {
    applyTheme("auto"), render();
  } ] ], s = i => !e || i.toLowerCase().includes(e);
  return n.filter(i => s(i[0])).forEach(i => t.push({
    g: "Actions",
    t: i[0],
    run: i[1]
  })), a.filter(i => s(i[0])).forEach(i => t.push({
    g: "Go to",
    t: i[0],
    run: () => {
      location.hash = i[1];
    }
  })), S.accounts.filter(i => s(acctLabel(i.id))).slice(0, 6).forEach(i => t.push({
    g: "Accounts",
    t: acctLabel(i.id),
    sub: moneyU(acctBalance(i)),
    run: () => {
      location.hash = "#account/" + i.id;
    }
  })), e && sorted(S.trades).reverse().filter(i => [ fdate(i.date), i.date, acctLabel(i.account_id), i.setup, sessName(i.session), i.direction, (i.tags || []).join(" "), i.notes ].join(" ").toLowerCase().includes(e)).slice(0, 8).forEach(i => t.push({
    g: "Trades",
    t: `${fdate(i.date)} · ${acctLabel(i.account_id)}${i.setup ? " · " + i.setup : ""}`,
    sub: money(tNet(i)),
    subc: cls(tNet(i)),
    run: () => {
      location.hash = "#trade/" + i.id;
    }
  })), t;
}

function openCmd() {
  CMD.open = !0, CMD.q = "", CMD.i = 0;
  let e = $("#cmd");
  e || (e = document.createElement("div"), e.id = "cmd", document.body.append(e)), 
  e.innerHTML = '<div class="cmd-bg" data-cmd="close"></div><div class="cmd-panel" role="dialog" aria-label="Command menu"><div class="cmd-in"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M16 16l4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><input id="cmdq" placeholder="Search or ask Sweep…" autocomplete="off" spellcheck="false"><kbd>esc</kbd></div><div class="cmd-list" id="cmdl"></div></div>', 
  e.hidden = !1, drawCmd(), setTimeout(() => $("#cmdq").focus(), 10);
}

function closeCmd() {
  CMD.open = !1;
  const e = $("#cmd");
  e && (e.hidden = !0);
}

function drawCmd() {
  CMD.items = cmdItems(CMD.q), CMD.i = Math.min(CMD.i, Math.max(0, CMD.items.length - 1));
  let e = "";
  $("#cmdl").innerHTML = CMD.items.length ? CMD.items.map((a, n) => {
    const s = a.g !== e ? `<div class="cmd-g">${esc(a.g)}</div>` : "";
    return e = a.g, s + `<button class="cmd-it ${n === CMD.i ? "on" : ""}" data-ci="${n}"><span>${esc(a.t)}</span>${a.sub ? `<em class="${a.subc || ""}">${esc(a.sub)}</em>` : ""}</button>`;
  }).join("") : '<div class="cmd-empty">No results</div>';
  const t = $("#cmdl .on");
  t && t.scrollIntoView({
    block: "nearest"
  });
}

document.addEventListener("input", e => {
  e.target.id === "cmdq" && (CMD.q = e.target.value, CMD.i = 0, drawCmd());
}), document.addEventListener("click", e => {
  if (!CMD.open) return;
  if (e.target.closest('[data-cmd="close"]')) {
    closeCmd();
    return;
  }
  const t = e.target.closest("[data-ci]");
  if (t) {
    const a = CMD.items[+t.dataset.ci];
    closeCmd(), a && a.run();
  }
}), document.addEventListener("keydown", e => {
  if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) {
    e.preventDefault(), CMD.open ? closeCmd() : openCmd();
    return;
  }
  if (CMD.open) {
    if (e.key === "Escape") e.preventDefault(), e.stopImmediatePropagation(), closeCmd(); else if (e.key === "ArrowDown" || e.key === "ArrowUp") e.preventDefault(), 
    CMD.i = Math.max(0, Math.min(CMD.items.length - 1, CMD.i + (e.key === "ArrowDown" ? 1 : -1))), 
    drawCmd(); else if (e.key === "Enter") {
      e.preventDefault();
      const t = CMD.items[CMD.i];
      closeCmd(), t && t.run();
    }
  }
}, !0);

const SKELETON = `<div class="skel" style="height:22px;width:260px;margin-bottom:26px"></div><div class="skel" style="height:170px;border-radius:18px"></div><div class="acards" style="margin-top:40px">${'<div class="skel" style="height:220px;border-radius:18px"></div>'.repeat(3)}</div>`, desk = () => innerWidth > 860;

function sideOpen(e) {
  const t = $(".side");
  t && t.classList.toggle("open", e && desk());
}

document.addEventListener("click", e => {
  const t = $(".side");
  if (!t || !desk()) return;
  if (!t.contains(e.target)) {
    t.classList.contains("open") && sideOpen(!1);
    return;
  }
  if (e.target.closest('[data-act="side-close"]')) {
    sideOpen(!1), e.stopPropagation();
    return;
  }
  if (e.target.closest('[data-act="side-toggle"]')) {
    sideOpen(!t.classList.contains("open"));
    return;
  }
  if (e.target.closest("a,button")) {
    t.classList.contains("open") && setTimeout(() => sideOpen(!1), 60);
    return;
  }
  sideOpen(!0);
}, !0);

function labelRail() {
  $$(".side a[data-v]").forEach(e => {
    e.dataset.label || (e.dataset.label = e.textContent.trim());
  });
}

const DUR_B = [ [ "under 15s", 0, 15 ], [ "15s to 45s", 15, 45 ], [ "45s to 1 min", 45, 60 ], [ "1 to 2 min", 60, 120 ], [ "2 to 5 min", 120, 300 ], [ "5 to 10 min", 300, 600 ], [ "10 to 30 min", 600, 1800 ], [ "30 min to 1 h", 1800, 3600 ], [ "1 to 4 h", 3600, 14400 ], [ "more than 4 h", 14400, 1 / 0 ] ];

function tDur(e) {
  if (e.duration_s != null && isFinite(e.duration_s)) return Number(e.duration_s);
  if (!e.entry_time || !e.exit_time) return null;
  const t = n => {
    const [s, i] = n.split(":").map(Number);
    return s * 60 + i;
  };
  let a = t(e.exit_time) - t(e.entry_time);
  return a < 0 && (a += 1440), a * 60;
}

const fdur = e => {
  if (e == null) return "—";
  e = Math.round(e);
  const t = Math.floor(e / 3600), a = Math.floor(e % 3600 / 60), n = e % 60;
  return t ? `${t}:${pad(a)}:${pad(n)}` : `${pad(a)}:${pad(n)}`;
}, WD = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" ];

function isoScore(e) {
  const o = (v, b, E) => [ 224 + (v - b) * 46 * .866, 258 + (v + b) * 46 * .5 - E * 46 ], r = v => v.map(b => b.toFixed(1)).join(",");
  let p = "";
  for (let v = 0; v <= 4; v++) p += `<line class="iso-g" x1="${o(v - 2, -2, 0)[0]}" y1="${o(v - 2, -2, 0)[1]}" x2="${o(v - 2, 2, 0)[0]}" y2="${o(v - 2, 2, 0)[1]}"/><line class="iso-g" x1="${o(-2, v - 2, 0)[0]}" y1="${o(-2, v - 2, 0)[1]}" x2="${o(2, v - 2, 0)[0]}" y2="${o(2, v - 2, 0)[1]}"/>`;
  for (const v of [ 1, 2, 3, 4 ]) {
    const b = v / 4 * 3.4;
    p += `<polyline class="iso-w" points="${r(o(-2, 2, b))} ${r(o(-2, -2, b))} ${r(o(2, -2, b))}"/><text class="iso-t" x="${o(-2, 2, b)[0] - 6}" y="${o(-2, 2, b)[1] + 3}" text-anchor="end">${v * 25}</text>`;
  }
  p += `<line class="iso-w" x1="${o(-2, -2, 0)[0]}" y1="${o(-2, -2, 0)[1]}" x2="${o(-2, -2, 3.4)[0]}" y2="${o(-2, -2, 3.4)[1]}"/><line class="iso-w" x1="${o(-2, 2, 0)[0]}" y1="${o(-2, 2, 0)[1]}" x2="${o(-2, 2, 3.4)[0]}" y2="${o(-2, 2, 3.4)[1]}"/><line class="iso-w" x1="${o(2, -2, 0)[0]}" y1="${o(2, -2, 0)[1]}" x2="${o(2, -2, 3.4)[0]}" y2="${o(2, -2, 3.4)[1]}"/>`;
  const u = [ [ -1.35, -1.1 ], [ .05, -1.1 ], [ 1.45, -1.1 ], [ -1.45, 1.1 ], [ -.05, 1.1 ], [ 1.35, 1.1 ] ], h = e.map((v, b) => ({
    a: v,
    x: u[b][0],
    y: u[b][1]
  })).sort((v, b) => v.x + v.y - (b.x + b.y)), m = .22;
  for (const {a: v, x: b, y: E} of h) {
    const R = Math.max(.06, v[1] / 100 * 3.4), L = [ o(b - m, E - m, R), o(b + m, E - m, R), o(b + m, E + m, R), o(b - m, E + m, R) ], x = [ o(b - m, E + m, 0), o(b + m, E + m, 0), o(b + m, E + m, R), o(b - m, E + m, R) ], C = [ o(b + m, E - m, 0), o(b + m, E + m, 0), o(b + m, E + m, R), o(b + m, E - m, R) ], g = o(b, E, R), P = o(b + m + .12, E + m + .12, 0);
    p += `<g class="iso-bar"><polygon class="iso-l" points="${x.map(r).join(" ")}"/><polygon class="iso-r" points="${C.map(r).join(" ")}"/><polygon class="iso-top" points="${L.map(r).join(" ")}"/>\n      <text class="iso-v" x="${g[0]}" y="${g[1] - 9}" text-anchor="middle">${Math.round(v[1])}</text>\n      <text class="iso-lab" x="${P[0] + 4}" y="${P[1] + 10}">${esc(v[0])}</text><title>${esc(v[0])}: ${Math.round(v[1])}/100</title></g>`;
  }
  return `<svg class="iso" viewBox="0 0 460 360" role="img" aria-label="Performance score breakdown"><defs>\n    <linearGradient id="isoTop" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="rgb(var(--pos-rgb))" stop-opacity=".95"/><stop offset="1" stop-color="rgb(var(--pos-rgb))" stop-opacity=".7"/></linearGradient>\n    <linearGradient id="isoSide" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgb(var(--pos-rgb))" stop-opacity=".75"/><stop offset="1" stop-color="rgb(var(--pos-rgb))" stop-opacity=".12"/></linearGradient></defs>${p}</svg>`;
}

function calDays(e, t) {
  for (const a of e.keys()) if (a.startsWith(t)) {
    const n = pd(a).getDay();
    if (n === 0 || n === 6) return 7;
  }
  return 5;
}

function calGrid(e, t) {
  const a = e + "-01", n = dayMap(t.filter(p => p.date.startsWith(e))), s = [ ...n.values() ], i = Math.max(0, ...s.map(p => Math.abs(p.net))), o = weekStart(a), r = todayStr(), c = calDays(n, e);
  let l = [ ...[ "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" ].slice(0, c), "Week" ].map(p => `<div class="hd${p === "Week" ? " wkh" : ""}">${p}</div>`).join("");
  for (let p = o; p.slice(0, 7) <= e || p < a; p = addDays(p, 7)) {
    let u = 0, h = 0, m = 0;
    for (let v = 0; v < 7; v++) {
      const b = addDays(p, v), E = n.get(b);
      if (v >= c) {
        E && b.startsWith(e) && (u += E.net, h += E.n, m++);
        continue;
      }
      if (!b.startsWith(e)) {
        l += `<div class="out"><span class="dn">${pd(b).getDate()}</span></div>`;
        continue;
      }
      E && (u += E.net, h += E.n, m++), l += `<a class="d ${b === r ? "is-today" : ""}" href="#journal/${b}" style="${E ? heatStyle(E.net, i) : ""}"><span class="dn">${pd(b).getDate()}</span>${E ? `<span class="p ${cls(E.net)}"><span class="full">${money(E.net)}</span><span class="short">${compactPnl(E.net)}</span></span><span class="m">${E.n} trade${E.n > 1 ? "s" : ""}</span>` : ""}</a>`;
    }
    if (l += `<div class="wk">${m ? `<span class="m">${m} day${m > 1 ? "s" : ""}</span><span class="p ${cls(u)}"><span class="full">${money(u)}</span><span class="short">${compactPnl(u)}</span></span>` : ""}</div>`, 
    addDays(p, 7).slice(0, 7) > e) break;
  }
  return `<div class="cal d${c}">${l}</div>`;
}

function card(e, t, a, {right: n = "", cls: s = ""} = {}) {
  return `<section class="surface ic ${s}"><div class="ic-h"><h2>${e}${t ? ` <span class="info" data-tip="${esc(t)}" tabindex="0">i</span>` : ""}</h2>${n}</div>${a}</section>`;
}

const segU = (e, t) => `<div class="seg">${t.map(([a, n]) => `<button data-act="useg" data-k="${e}" data-v="${a}" class="${U[e] === a ? "on" : ""}">${n}</button>`).join("")}</div>`;

function vAnalytics(e) {
  [ "discipline", "behavior", "recovery", "session", "time", "weekday", "setup", "direction", "news" ].includes(e) && (U.deep = e, 
  saveU());
  const t = ft(), a = stats(t);
  if (!t.length) return `${filterBar()}<div class="surface empty">No trades ${periodLabel()}. Change the period or add trades to see your stats.</div>`;
  U.cmp = U.cmp || "cum", U.dur = U.dur || "pct", U.brk = U.brk || "side", U.calv = U.calv || "cal", 
  U.deep = U.deep || "discipline";
  const n = todayStr(), s = t.filter(M => M.date === n).reduce((M, ne) => M + tNet(ne), 0), i = a.pf === 1 / 0 ? 3 : a.pf || 0, o = `<div class="ikpis">\n    <div class="surface ik"><span class="lbl">Net P&amp;L <span class="info" data-tip="Total profit and loss after fees for the selected trades." tabindex="0">i</span></span><b class="${cls(a.net)}">${cu(a.net)}</b><small>${s ? `<span class="${cls(s)}">${money(s)}</span> today` : `${a.n} trades · ${periodLabel()}`}</small></div>\n    <div class="surface ik"><span class="lbl">Win rate <span class="info" data-tip="Winning trades ÷ (winning + losing). Breakeven trades excluded." tabindex="0">i</span></span><b>${a.wr == null ? "—" : cu(a.wr * 100, "pct")}</b><div class="wl"><i style="flex:${a.wins || 0}"></i><i style="flex:${a.losses || 0}"></i></div><small>${a.wins} won · ${a.losses} lost${a.be ? ` · ${a.be} even` : ""}</small></div>\n    <div class="surface ik ik-ring"><div><span class="lbl">Profit factor <span class="info" data-tip="Gross profit ÷ gross loss. Above 1.0 is profitable." tabindex="0">i</span></span><b>${pf(a.pf)}</b><small>${moneyU(a.gp)} won · ${moneyU(-a.gl)} lost</small></div>${ring(Math.min(100, i / 3 * 100), {
    size: 62,
    stroke: 6
  })}</div>\n    <div class="surface ik"><span class="lbl">Avg win / loss <span class="info" data-tip="Average winning trade ÷ average losing trade." tabindex="0">i</span></span><b>${a.rr == null ? "—" : decl(a.rr.toFixed(2))}</b><div class="wl"><i style="flex:${Math.abs(a.avgWin || 0)}"></i><i style="flex:${Math.abs(a.avgLoss || 0)}"></i></div><small><span class="pos">${money(a.avgWin)}</span> · <span class="neg">${money(a.avgLoss)}</span></small></div>\n  </div>`, r = perfScore(t), c = card("Performance score", "Average of six measures scaled 0–100: win rate, profit factor, average win ÷ average loss, recovery (net P&L ÷ max drawdown), share of winning days, and discipline. Needs at least 10 trades.", r ? `<div class="cmp-num">${cu(r.score, "int")}</div>${isoScore(r.axes)}` : '<div class="empty">Not enough data yet. The score needs at least 10 trades.</div>', {
    cls: "ic-compass"
  }), l = equitySeries(t, "daily"), p = a.days, u = card("P&amp;L performance", "", U.cmp === "cum" ? lineChart(l, {
    lab: eqLab("daily"),
    h: 260
  }) : barChart([ ...p.values() ].map(M => ({
    label: fdate(M.date),
    title: fdateL(M.date),
    v: M.net
  })), {
    h: 260
  }), {
    right: segU("cmp", [ [ "cum", "Cumulative" ], [ "daily", "Daily" ] ])
  }), h = groupBy(t, M => (pd(M.date).getDay() + 6) % 7);
  let m = null, v = null, b = null;
  for (const [M, ne] of h) {
    const k = new Set(ne.map(N => N.date)).size, A = ne.length / k, j = ne.reduce((N, B) => N + tNet(B), 0);
    (!m || A > m.avg) && (m = {
      k: M,
      avg: A
    }), (!v || j > v.net) && (v = {
      k: M,
      net: j
    }), (!b || j < b.net) && (b = {
      k: M,
      net: j
    });
  }
  const E = stats(t.filter(M => M.direction === "long")), R = stats(t.filter(M => M.direction === "short")), L = E.n >= R.n ? [ "Long", E, R ] : [ "Short", R, E ], x = (M, ne, k, A, j, N = "") => `<div class="surface it"><span class="lbl">${M} <span class="info" data-tip="${esc(ne)}" tabindex="0">i</span></span><b>${k}</b>${A != null ? `<em class="${j || ""}">${A}</em>` : ""}${N ? `<small>${N}</small>` : ""}</div>`, C = `${x("Most active", "Weekday with the most trades per trading day.", WD[m.k], decl(m.avg.toFixed(1)), "", "avg trades per day")}\n    ${x("Most profitable", "Weekday with the highest net P&L.", WD[v.k], money(v.net), cls(v.net))}\n    ${x("Least profitable", "Weekday with the lowest net P&L.", WD[b.k], money(b.net), cls(b.net))}\n    ${x("Trade direction", "Direction you trade most, with its share of trades and net P&L.", L[0], Math.round(L[1].n / a.n * 100) + "%", "", `<span class="${cls(L[1].net)}">${money(L[1].net)}</span> vs <span class="${cls(L[2].net)}">${money(L[2].net)}</span>`)}`;
  let g = 0, P = 0;
  const O = [ {
    label: "",
    v: 0
  } ];
  for (const M of t) g += tNet(M), P = Math.max(P, g), O.push({
    label: M.date,
    v: g - P
  });
  const H = card("Drawdown curve", "Distance below the previous equity peak, trade by trade.", `<div class="statmini"><span>Worst drawdown <b class="neg">${money(a.maxDD)}</b></span></div>${lineChart(O, {
    lab: M => M ? fdate(M) : "Start",
    label: "Drawdown",
    h: 330,
    w: 420,
    tone: "neg"
  })}`), J = t.filter(M => tDur(M) != null), q = J.length ? J.reduce((M, ne) => M + tDur(ne), 0) / J.length : null, z = DUR_B.map(([M, ne, k]) => {
    const A = J.filter(N => {
      const B = tDur(N);
      return B >= ne && B < k;
    }), j = stats(A);
    return {
      l: M,
      n: A.length,
      wr: j.wr,
      avg: j.avg
    };
  }), Y = `<div class="durhead"><span>Avg win <b class="pos">${money(a.avgWin)}</b></span><span>Avg loss <b class="neg">${money(a.avgLoss)}</b></span><span>Avg trade duration <b>${fdur(q)}</b></span></div>\n    <div class="dur">${z.map(M => {
    const ne = U.dur === "pct" ? J.length ? M.n / J.length : 0 : M.wr || 0, k = M.n ? M.avg > 0 ? "pos" : M.avg < 0 ? "neg" : "ink" : "";
    return `<div class="dr" title="${M.n} trade${M.n === 1 ? "" : "s"}${M.n ? " · avg " + money(M.avg) : ""}"><span class="dl">${M.l}</span><div class="dt"><i class="${k}" style="width:${(ne * 100).toFixed(1)}%"></i></div><span class="dv">${M.n ? U.dur === "pct" ? Math.round(ne * 100) + "%" : pct(M.wr) : "—"}</span></div>`;
  }).join("")}</div>\n    <div class="dur-foot"><span class="lg"><i class="pos"></i>Positive avg. net P&amp;L</span><span class="lg"><i class="neg"></i>Negative avg. net P&amp;L</span>${segU("dur", [ [ "pct", "By % of trades" ], [ "wr", "By win rate" ] ])}</div>`, Q = card("Duration analysis", "Holding time of each trade, grouped. Bar color shows whether trades of that length make or lose money on average. Imported trades are precise to the second; manual trades to the minute.", Y), me = {
    side: M => M.direction === "long" ? "Long" : "Short",
    session: M => sessName(M.session),
    setup: M => M.setup || "No setup",
    tags: M => (M.tags || []).length ? M.tags : [ "No tag" ],
    instrument: M => M.instrument || "NQ",
    account: M => acctLabel(M.account_id),
    weekday: M => WD[(pd(M.date).getDay() + 6) % 7]
  }[U.brk], oe = [ ...groupBy(t, me) ].map(([M, ne]) => ({
    k: M,
    net: ne.reduce((k, A) => k + tNet(A), 0),
    n: ne.length
  })).sort((M, ne) => ne.net - M.net), ae = Math.max(1, ...oe.map(M => Math.abs(M.net))), we = card("P&amp;L breakdown", "", `<div class="brk">${oe.map(M => `<div class="br"><span class="bl" title="${esc(M.k)}">${esc(M.k)}<small>${M.n} trade${M.n > 1 ? "s" : ""}</small></span><div class="bt"><i class="${M.net >= 0 ? "pos" : "neg"}" style="${M.net >= 0 ? "left:50%" : "right:50%"};width:${(Math.abs(M.net) / ae * 50).toFixed(2)}%"></i></div><span class="bv ${cls(M.net)}">${money(M.net)}</span></div>`).join("")}</div>`, {
    right: segU("brk", [ [ "side", "Side" ], [ "session", "Session" ], [ "setup", "Setup" ], [ "weekday", "Day" ], [ "tags", "Tags" ], [ "account", "Account" ] ])
  }), te = (t.at(-1) || {
    date: todayStr()
  }).date.slice(0, 7), re = card(U.calv === "cal" ? pd(te + "-01").toLocaleDateString(LOC(), {
    month: "long",
    year: "numeric"
  }) : "Trades", "", U.calv === "cal" ? calGrid(te, t) : tradeTable(t.slice(-12).reverse()), {
    right: segU("calv", [ [ "cal", "Calendar" ], [ "trades", "Trades" ] ])
  }), X = [ [ "discipline", "Discipline", anDisc ], [ "behavior", "Behavior", anBehavior ], [ "recovery", "Loss recovery", anRecovery ], [ "session", "Sessions", anSess ], [ "time", "Time of day", anTime ], [ "weekday", "Day of week", anWeekday ], [ "setup", "Setups", anSetup ], [ "direction", "Long vs short", anDir ], [ "news", "News", anNews ] ], pe = X.find(M => M[0] === U.deep) || X[0], ue = billOld(t.length ? t[0].date : todayStr(), todayStr());
  return `${filterBar()}\n  <div ${ue ? 'data-lock="analytics_history" data-force="1" class="bill-lock"' : ""}>\n  ${o}\n  <div class="igrid g-top">${c}${u}</div>\n  <div class="igrid g-ins"><div class="vlabel"><span>Trading stats</span></div><div class="tiles">${C}</div>${H}${Q}</div>\n  <div class="igrid g-two">${we}${card("Patterns to watch", "Statistically supported observations from your trades. Each needs at least 5 trades per group.", insightList(t, 5))}</div>\n  ${re}\n  <section class="deep"><div class="sec-h"><h2>Deep dive</h2></div><div class="tabs">${X.map(([M, ne]) => `<button data-act="useg" data-k="deep" data-v="${M}" class="${U.deep === M ? "on" : ""}">${ne}</button>`).join("")}</div>${pe[2](t)}</section></div>`;
}

const TZ = "America/New_York", _etFmt = new Intl.DateTimeFormat("en-US", {
  timeZone: TZ,
  hour12: !1,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit"
});

function etStr(e) {
  const t = {};
  for (const a of _etFmt.formatToParts(new Date(e * 1e3))) t[a.type] = a.value;
  return `${t.year}-${t.month}-${t.day} ${t.hour === "24" ? "00" : t.hour}:${t.minute}:${t.second}`;
}

function etEpoch(e) {
  const t = String(e).match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?/);
  if (!t) return null;
  const a = Date.UTC(+t[1], t[2] - 1, +t[3], +t[4], +t[5], +(t[6] || 0)) / 1e3, n = i => {
    const o = etStr(i).match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/);
    return Date.UTC(+o[1], o[2] - 1, +o[3], +o[4], +o[5], +o[6]) / 1e3;
  };
  let s = a - (n(a) - a);
  return s = a - (n(s) - s), s;
}

const nowET = () => etStr(Math.floor(Date.now() / 1e3)), PV = e => instOf(e).tickC / instOf(e).tick;

function positionOf(e, t = "NQ") {
  const a = instOf(t).tickC, n = e.slice().sort((P, O) => P.t < O.t ? -1 : P.t > O.t ? 1 : 0);
  let s = [], i = 0, o = 0, r = null, c = 0, l = 0, p = 0, u = 0, h = 0, m = 0, v = 0, b = !1;
  const E = new Set, R = [], L = () => s.length ? s.reduce((P, O) => P + O.p * O.q, 0) / s.reduce((P, O) => P + O.q, 0) : null;
  for (const P of n) {
    const O = P.side === "buy" ? 1 : -1;
    let H = Math.abs(+P.qty || 0);
    const J = +P.price;
    if (!(!H || !isFinite(J))) {
      if (i === 0 && !s.length && r === null && (r = O > 0 ? "long" : "short"), i === 0 || Math.sign(i) === O) {
        if (i !== 0) {
          m++;
          const q = L();
          (J - q) * Math.sign(i) < 0 && E.add("addloser");
        }
        s.push({
          p: J,
          q: H
        }), i += O * H, l += H, p += J * H;
      } else {
        let q = H;
        for (;q > 0 && s.length; ) {
          const z = s[0], Y = Math.min(z.q, q);
          o += (ticks(J, t) - ticks(z.p, t)) * Math.sign(i) * Y * a, u += Y, h += J * Y, z.q -= Y, 
          q -= Y, i += O * Y, z.q || s.shift();
        }
        i !== 0 && v++, q > 0 && (b = !0);
      }
      c = Math.max(c, Math.abs(i)), R.push({
        t: P.t,
        pos: i,
        avg: L()
      });
    }
  }
  const x = n[0], C = n.at(-1), g = n.filter(P => (P.side === "buy" ? "long" : "short") !== r);
  return {
    dir: r,
    open: i,
    closed: i === 0 && u > 0,
    avgEntry: l ? p / l : null,
    avgExit: u ? h / u : null,
    realized_c: o,
    maxQty: c,
    firstQty: x ? +x.qty : 0,
    adds: m,
    partials: v,
    flip: b,
    flags: [ ...E ],
    start: x && x.t,
    end: g.length ? g.at(-1).t : C && C.t,
    timeline: R,
    count: n.length
  };
}

function riskOf({entry: e, stop: t, target: a, qty: n, dir: s, inst: i = "NQ"}) {
  const o = {}, r = +e, c = +t, l = +a, p = +n || 0, u = PV(i);
  return isFinite(r) && t !== "" && t != null && isFinite(c) && (o.riskPts = Math.abs(r - c), 
  o.risk_c = Math.round(o.riskPts * u * p), o.stopWrong = s && (s === "long" && c >= r || s === "short" && c <= r)), 
  isFinite(r) && a !== "" && a != null && isFinite(l) && (o.rewPts = Math.abs(l - r), 
  o.rew_c = Math.round(o.rewPts * u * p), o.targetWrong = s && (s === "long" && l <= r || s === "short" && l >= r)), 
  o.riskPts && o.rewPts != null && (o.rr = o.rewPts / o.riskPts), o;
}

function riskBudget(e, t, a) {
  const n = acct(e);
  if (!n || !n.rules || !n.rules.dll_c) return null;
  const s = S.trades.filter(i => i.account_id === e && i.date === t && (!a || i.copy_group !== a)).reduce((i, o) => i + tNet(o), 0);
  return {
    limit: n.rules.dll_c,
    used: Math.max(0, -s),
    left: Math.max(0, n.rules.dll_c + Math.min(0, s))
  };
}

const AUTO_RULES = {
  addloser: {
    q: "addloser",
    label: "Added to loser"
  },
  risklimit: {
    q: "dll",
    label: "Risk limit exceeded"
  },
  stop: {
    q: "stop",
    label: "Stop not respected"
  },
  oversized: {
    q: "size",
    label: "Oversized position"
  }
};

function detectFlags(e, t, a) {
  const n = new Set(t.flags), s = e.instrument || "NQ", i = +(S.settings.max_contracts || 0);
  i && t.maxQty > i && n.add("oversized");
  const o = riskOf({
    entry: t.avgEntry,
    stop: e.stop,
    target: e.target,
    qty: t.maxQty,
    dir: t.dir,
    inst: s
  });
  a && o.risk_c > a.left && n.add("risklimit");
  const r = +(S.settings.max_trade_risk_c || 0);
  return r && o.risk_c > r && n.add("risklimit"), e.stop != null && e.stop !== "" && t.avgExit != null && (t.dir === "long" ? +e.stop - t.avgExit : t.avgExit - +e.stop) > 2 && n.add("stop"), 
  [ ...n ];
}

const ECON = {
  days: {},
  pending: {},
  at: {},
  sample: !1
};

function loadEcon(e, t) {
  if (typeof S == "undefined" || S.mode !== "server" || !e || !t) return loadEconRaw(e, t);
  const N = Date.now(), G = loadEcon._g || (loadEcon._g = []);
  for (const g of G) if (e >= g[0] && t <= g[1] && N - g[2] < (e === t ? 6e4 : 6e5)) return g[3];
  let a = e, n = t;
  if (!G.length) {
    const T = todayStr(), M = T.slice(0, 8) + "01", A = ymdAdd(T, -21), B = ymdAdd(T, 9), E = ymdAdd(ymdAdd(M, 32).slice(0, 8) + "01", -1), wa = A < M ? A : M, wb = B > E ? B : E;
    e >= wa && t <= wb && (a = wa, n = wb);
  }
  const P = loadEconRaw(a, n);
  return G.push([ a, n, N, P ]), P;
}

async function loadEconRaw(e, t) {
  const a = e + "_" + t;
  if (ECON.pending[a] && Date.now() - (ECON.at[a] || 0) < 10 * 60 * 1e3) return ECON.pending[a];
  ECON.at[a] = Date.now();
  let n;
  return S.mode === "server" ? n = apiJSON(`api/econ?from=${e}&to=${t}`).then(s => s.events || []).catch(() => []) : n = Promise.resolve(sampleEcon(e, t)), 
  ECON.pending[a] = n.then(s => {
    for (let i = e; i <= t; i = addDays(i, 1)) ECON.days[i] = [];
    for (const i of s) {
      const o = etStr(i.ts).slice(0, 10);
      ECON.days[o] = ECON.days[o] || [], ECON.days[o].some(r => r.id === i.id) || ECON.days[o].push(i);
    }
    for (const i in ECON.days) ECON.days[i].sort((o, r) => o.ts - r.ts);
    return S.mode === "server" && typeof aiEconRefresh == "function" && aiEconRefresh(s), 
    s;
  }), ECON.pending[a];
}

function eventsBetween(e, t) {
  const a = [];
  for (let n = etStr(e).slice(0, 10); n <= etStr(t).slice(0, 10); n = addDays(n, 1)) for (const s of ECON.days[n] || []) s.ts >= e && s.ts <= t && a.push(s);
  return a;
}

function sampleEcon(e, t) {
  if (S.mode === "server") return [];
  ECON.sample = !0;
  const a = {
    o: "official",
    t: "official-tentative",
    e: "estimated"
  };
  return ECON_SEED.filter(n => n[0] >= e && n[0] <= t).map(n => ({
    id: "seed-" + n[0] + n[1] + n[2],
    ts: etEpoch(n[0] + " " + n[1] + ":00"),
    event: n[2],
    impact: n[3] === "h" ? "high" : "medium",
    status: a[n[4]],
    country: "US",
    actual: null,
    forecast: null,
    previous: null
  }));
}

function newsContext(e, t) {
  const a = eventsBetween(e - 1800, t + 1800), n = eventsBetween(e - 6 * 3600, e + 6 * 3600).filter(s => s.impact === "high").map(s => ({
    e: s,
    d: (e - s.ts) / 60
  })).sort((s, i) => Math.abs(s.d) - Math.abs(i.d))[0];
  return {
    news: a.map(s => ({
      id: s.id,
      ts: s.ts,
      event: s.event,
      impact: s.impact,
      sec: e - s.ts
    })),
    news_min: n ? Math.round(n.d) : null,
    news_near: n ? n.e.event : null
  };
}

const impactLabel = e => e === "high" ? "High" : "Medium";

function relMin(e) {
  const t = Math.abs(e);
  return t < 60 ? `${Math.round(t)} min` : `${Math.floor(t / 60)} h ${pad(Math.round(t % 60))}`;
}

let TICK = .25;

const snapPx = e => Math.round(e / TICK) * TICK;

function aggCandles(e, t) {
  if (t <= 1) return e;
  const a = t * 60, n = [];
  let s = null;
  for (const i of e) {
    const o = i[0] - i[0] % a;
    !s || s[0] !== o ? (s = [ o, i[1], i[2], i[3], i[4], i[5] || 0 ], n.push(s)) : (s[2] = Math.max(s[2], i[2]), 
    s[3] = Math.min(s[3], i[3]), s[4] = i[4], s[5] += i[5] || 0);
  }
  return n;
}

function synthCandles(e, t, a) {
  e = e - e % 60, t = t - t % 60;
  let n = e / 60 >>> 0;
  const s = () => (n = n * 1664525 + 1013904223 >>> 0, n / 4294967296), i = a.filter(l => isFinite(l.price)).sort((l, p) => l.t - p.t);
  if (!i.length) return [];
  const o = Math.max(.02, i[0].price / 21e3), r = [];
  let c = i[0].price + (s() - .5) * 20 * o;
  for (let l = e; l <= t; l += 60) {
    const p = i.find(L => L.t >= l), u = p ? p.price : i.at(-1).price + (s() - .5) * 30 * o, h = p ? Math.max(1, (p.t - l) / 60) : 30, m = (u - c) / h, v = c;
    let b = c + m + (s() - .5) * 9 * o;
    p && p.t - l < 60 && (b = p.price);
    const E = Math.max(v, b) + s() * 4 * o, R = Math.min(v, b) - s() * 4 * o;
    r.push([ l, snapPx(v), snapPx(E), snapPx(R), snapPx(b), Math.round(200 + s() * 900) ]), 
    c = b;
  }
  return r;
}

function niceStep(e, t) {
  const a = e / t, n = Math.pow(10, Math.floor(Math.log10(a)));
  return [ 1, 2, 2.5, 5, 10 ].map(s => s * n).find(s => s >= a) || 10 * n;
}

const TSTEPS = [ 60, 300, 900, 1800, 3600, 7200, 14400, 43200 ];

function chartMount(e, t) {
  e._ch = {
    cfg: Object.assign({
      tf: 1,
      h: 460,
      levels: {},
      execs: [],
      events: [],
      candles: []
    }, t),
    view: null,
    drag: null
  }, e._bound || (e._bound = !0, bindChart(e)), chartFit(e), drawChart(e);
}

function chartSet(e, t, {refit: a = !1} = {}) {
  !e || !e._ch || (Object.assign(e._ch.cfg, t), a && chartFit(e), drawChart(e));
}

function chartFit(e) {
  const t = e._ch.cfg, a = [ ...t.execs.map(o => o.t), ...t.focus || [] ].filter(isFinite);
  let n, s;
  a.length ? (n = Math.min(...a), s = Math.max(...a)) : t.candles.length ? (s = t.candles.at(-1)[0], 
  n = s - 3600) : (s = Math.floor(Date.now() / 1e3), n = s - 3600);
  const i = Math.max(1800, s - n);
  e._ch.view = {
    t0: n - i * .6,
    t1: s + i * .6,
    p0: null,
    p1: null
  };
}

function chartGeom(e) {
  const t = Math.max(320, e.clientWidth), a = e._ch.cfg.h;
  return {
    W: t,
    H: a,
    pl: 8,
    pr: 74,
    pt: 14,
    pb: 30,
    pw: t - 8 - 74,
    ph: a - 14 - 30
  };
}

function priceRange(e) {
  const {cfg: t, view: a} = e._ch;
  if (a.p0 != null) return [ a.p0, a.p1 ];
  const n = aggCandles(t.candles, t.tf).filter(l => l[0] >= a.t0 - t.tf * 60 && l[0] <= a.t1), s = [];
  n.forEach(l => {
    s.push(l[2], l[3]);
  });
  for (const l of [ "entry", "stop", "target", "exit" ]) isFinite(+t.levels[l]) && t.levels[l] !== "" && t.levels[l] != null && s.push(+t.levels[l]);
  if (t.execs.forEach(l => s.push(+l.price)), !s.length) return [ 21e3, 21100 ];
  let i = Math.min(...s), o = Math.max(...s);
  const r = TICK * 32;
  if (o - i < r) {
    const l = (i + o) / 2;
    i = l - r / 2, o = l + r / 2;
  }
  const c = (o - i) * .12;
  return [ i - c, o + c ];
}

function drawChart(e) {
  const t = e._ch, a = t.cfg, n = t.view;
  TICK = instOf(a.inst).tick;
  const s = chartGeom(e), [i, o] = priceRange(e);
  t.pr = [ i, o ];
  const r = q => s.pl + (q - n.t0) / (n.t1 - n.t0) * s.pw, c = q => s.pt + (o - q) / (o - i) * s.ph;
  t.X = r, t.Y = c, t.g = s;
  let l = `<svg class="tc" width="${s.W}" height="${s.H}" viewBox="0 0 ${s.W} ${s.H}"><defs><clipPath id="tcclip"><rect x="${s.pl}" y="${s.pt}" width="${s.pw}" height="${s.ph}"/></clipPath></defs>`;
  const p = [ "entry", "stop", "target", "exit" ].map(q => a.levels[q]).filter(q => q !== "" && q != null && isFinite(+q)).map(q => c(+q)), u = niceStep(o - i, 7);
  for (let q = Math.ceil(i / u) * u; q <= o; q += u) {
    const z = c(q);
    l += `<line class="tg" x1="${s.pl}" x2="${s.pl + s.pw}" y1="${z}" y2="${z}"/>${p.some(Y => Math.abs(Y - z) < 14) ? "" : `<text class="ta" x="${s.W - s.pr + 8}" y="${z + 4}">${q.toFixed(TICK < .1 || TICK < 1 ? 2 : 0)}</text>`}`;
  }
  const h = TSTEPS.find(q => (n.t1 - n.t0) / q <= 9) || 86400;
  for (let q = Math.ceil(n.t0 / h) * h; q <= n.t1; q += h) {
    const z = r(q);
    l += `<line class="tg" x1="${z}" x2="${z}" y1="${s.pt}" y2="${s.pt + s.ph}"/><text class="ta" x="${z}" y="${s.H - 10}" text-anchor="middle">${etStr(q).slice(11, 16)}</text>`;
  }
  l += '<g clip-path="url(#tcclip)">';
  const m = a.levels, v = q => m[q] !== "" && m[q] != null && isFinite(+m[q]);
  if (v("entry")) {
    const q = a.execs.length ? r(Math.min(...a.execs.map(ae => ae.t))) : isFinite(a.entryT) ? r(a.entryT) : s.pl, z = a.execs.length > 1 ? r(Math.max(...a.execs.map(ae => ae.t))) : s.pl + s.pw, Y = Math.max(s.pl, q), Q = Math.max(Y + 40, Math.min(s.pl + s.pw, z + (a.execs.length > 1, 
    0))), me = c(+m.entry);
    if (v("target")) {
      const ae = c(+m.target);
      l += `<rect class="pz-rew" x="${Y}" y="${Math.min(me, ae)}" width="${Q - Y}" height="${Math.abs(ae - me)}"/>`;
    }
    if (v("stop")) {
      const ae = c(+m.stop);
      l += `<rect class="pz-risk" x="${Y}" y="${Math.min(me, ae)}" width="${Q - Y}" height="${Math.abs(ae - me)}"/>`;
    }
    const oe = riskOf({
      entry: m.entry,
      stop: m.stop,
      target: m.target,
      qty: a.qty || 1,
      dir: a.dir,
      inst: a.inst || "NQ"
    });
    v("target") && (l += `<text class="pz-t" x="${Y + 8}" y="${c(+m.target) + (+m.target > +m.entry ? 16 : -8)}">Target · ${oe.rewPts != null ? oe.rewPts.toFixed(2) + " pts" : ""}${oe.rew_c != null ? " · " + moneyU(oe.rew_c) : ""}${oe.rr ? " · " + oe.rr.toFixed(2) + "R" : ""}</text>`), 
    v("stop") && (l += `<text class="pz-t risk" x="${Y + 8}" y="${c(+m.stop) + (+m.stop < +m.entry ? -8 : 16)}">Stop · ${oe.riskPts != null ? oe.riskPts.toFixed(2) + " pts" : ""}${oe.risk_c != null ? " · " + moneyU(oe.risk_c) : ""}</text>`);
  }
  const b = aggCandles(a.candles, a.tf), E = Math.max(1, s.pw / Math.max(1, (n.t1 - n.t0) / (a.tf * 60)) * .66);
  for (const q of b) {
    if (q[0] < n.t0 - a.tf * 60 || q[0] > n.t1) continue;
    const z = r(q[0] + a.tf * 30), Y = q[4] >= q[1];
    l += `<line class="cw" x1="${z}" x2="${z}" y1="${c(q[2])}" y2="${c(q[3])}"/><rect class="${Y ? "cu" : "cd"}" x="${z - E / 2}" y="${c(Math.max(q[1], q[4]))}" width="${E}" height="${Math.max(1, Math.abs(c(q[1]) - c(q[4])))}"/>`;
  }
  for (const q of a.events) {
    if (q.ts < n.t0 || q.ts > n.t1) continue;
    const z = r(q.ts);
    l += `<line class="nv ${q.impact}" x1="${z}" x2="${z}" y1="${s.pt}" y2="${s.pt + s.ph}"/>`;
  }
  const R = (q, z, Y) => {
    if (!v(q)) return "";
    const Q = c(+m[q]);
    return `<line class="lv ${z}" x1="${s.pl}" x2="${s.pl + s.pw}" y1="${Q}" y2="${Q}"/>`;
  };
  l += R("target", "lt") + R("stop", "ls") + R("entry", "le") + R("exit", "lx");
  const L = a.execs.slice().sort((q, z) => q.t - z.t), x = L.filter(q => (q.side === "buy" ? "long" : "short") === a.dir), C = L.filter(q => (q.side === "buy" ? "long" : "short") !== a.dir);
  x.length && C.length && (l += `<line class="exl" x1="${r(x[0].t)}" y1="${c(+x[0].price)}" x2="${r(C.at(-1).t)}" y2="${c(+C.at(-1).price)}"/>`);
  for (const q of L) {
    const z = r(q.t), Y = c(+q.price), Q = q.side === "buy";
    l += `<g class="xm ${Q ? "buy" : "sell"}"><path d="${Q ? `M${z} ${Y + 3}l-6 10h12z` : `M${z} ${Y - 3}l-6 -10h12z`}"/><text x="${z}" y="${Q ? Y + 26 : Y - 17}" text-anchor="middle">${Q ? "B" : "S"}${q.qty}</text></g>`;
  }
  l += "</g>";
  const g = TICK < 1 ? 2 : 0, P = [], O = (q, z) => {
    if (!v(q)) return "";
    const Y = c(+m[q]);
    return Y < s.pt - 8 || Y > s.pt + s.ph + 8 || P.some(Q => Math.abs(Q - Y) < 14) ? "" : (P.push(Y), 
    `<g class="ptag ${z}"><rect x="${s.W - s.pr + 2}" y="${Y - 10}" width="${s.pr - 6}" height="20" rx="6"/><text x="${s.W - s.pr + 8}" y="${Y + 4}">${(+m[q]).toFixed(g)}</text></g>`);
  };
  l += O("entry", "pt-e") + O("stop", "pt-s") + O("target", "pt-t") + O("exit", "pt-x");
  const H = [], J = (q, z, Y) => {
    if (!v(q)) return "";
    const Q = c(+m[q]);
    if (Q < s.pt + 12 || Q > s.pt + s.ph - 4 || H.some(oe => Math.abs(oe - Q) < 16)) return "";
    H.push(Q);
    const me = z.length * 6.4 + 14;
    return `<g class="lname ${Y}"><rect x="${s.pl + 6}" y="${Q - 19}" width="${me}" height="16" rx="5"/><text x="${s.pl + 13}" y="${Q - 7.5}">${z}</text></g>`;
  };
  l += J("entry", "Entry " + (+m.entry).toFixed(g), "ln-e") + J("exit", (Math.abs(+m.exit - +m.target) < TICK / 2 ? "Exit at target " : Math.abs(+m.exit - +m.stop) < TICK / 2 ? "Exit at stop " : "Exit ") + (v("exit") ? (+m.exit).toFixed(g) : ""), "ln-x");
  for (const q of a.events) {
    if (q.ts < n.t0 || q.ts > n.t1) continue;
    const z = r(q.ts);
    l += `<g class="nd ${q.impact}" data-ev="${esc(q.id)}"><circle cx="${z}" cy="${s.pt + s.ph + 8}" r="4.5"/><rect class="nhit" x="${z - 8}" y="${s.pt + s.ph}" width="16" height="18"/></g>`;
  }
  l += `<g class="xh2" style="display:none"><line class="xv" y1="${s.pt}" y2="${s.pt + s.ph}"/><line class="xhz" x1="${s.pl}" x2="${s.pl + s.pw}"/><g class="xpt"><rect width="${s.pr - 6}" height="20" rx="6"/><text x="6" y="14"></text></g><g class="xtt"><rect width="64" height="20" rx="6"/><text x="32" y="14" text-anchor="middle"></text></g></g>`, 
  l += "</svg>", e.innerHTML = l + (a.note ? `<div class="tc-note">${esc(a.note)}</div>` : "") + '<div class="tc-tip" hidden></div>';
}

function bindChart(e) {
  const t = o => {
    const r = e.getBoundingClientRect();
    return {
      x: o.clientX - r.left,
      y: o.clientY - r.top
    };
  }, a = (o, r) => {
    const c = e._ch, l = c.g, p = c.view, [u, h] = c.pr;
    return {
      t: p.t0 + (o - l.pl) / l.pw * (p.t1 - p.t0),
      p: h - (r - l.pt) / l.ph * (h - u)
    };
  };
  let n = 0;
  const s = () => {
    n || (n = requestAnimationFrame(() => {
      n = 0, drawChart(e);
    }));
  };
  e.addEventListener("pointerdown", o => {
    const r = e._ch;
    if (!r || o.button !== 0 || o.target.closest("[data-ev]")) return;
    const {x: c, y: l} = t(o), p = r.g, u = c > p.pl + p.pw, h = l > p.pt + p.ph;
    if (u) {
      const [m, v] = r.pr;
      r.drag = {
        kind: "pz",
        y: l,
        p0: m,
        p1: v
      };
    } else h ? r.drag = {
      kind: "tz",
      x: c,
      t0: r.view.t0,
      t1: r.view.t1
    } : r.drag = {
      kind: "pan",
      x: c,
      t0: r.view.t0,
      t1: r.view.t1
    };
    e.setPointerCapture(o.pointerId), e.classList.add("panning");
  }), e.addEventListener("pointermove", o => {
    const r = e._ch;
    if (!r || !r.g) return;
    const {x: c, y: l} = t(o), p = r.g, u = r.drag;
    if (u && u.kind === "pan") {
      const E = (c - u.x) / p.pw * (u.t1 - u.t0);
      r.view.t0 = u.t0 - E, r.view.t1 = u.t1 - E, s();
      return;
    }
    if (u && u.kind === "tz") {
      const E = Math.exp(-(c - u.x) * .006), R = (u.t0 + u.t1) / 2;
      let L = (u.t1 - u.t0) / 2 * E;
      L = Math.max(150, Math.min(86400 * 1.5, L)), r.view.t0 = R - L, r.view.t1 = R + L, 
      s();
      return;
    }
    if (u && u.kind === "pz") {
      const E = Math.exp((l - u.y) * .006), R = (u.p0 + u.p1) / 2, L = Math.max(TICK * 4, (u.p1 - u.p0) / 2 * E);
      r.view.p0 = R - L, r.view.p1 = R + L, s();
      return;
    }
    e.style.cursor = c > p.pl + p.pw ? "ns-resize" : l > p.pt + p.ph ? "ew-resize" : "";
    const h = e.querySelector(".xh2");
    if (!h) return;
    const m = c >= p.pl && c <= p.pl + p.pw && l >= p.pt && l <= p.pt + p.ph;
    if (h.style.display = m ? "" : "none", !m) return;
    const {t: v, p: b} = a(c, l);
    h.querySelector(".xv").setAttribute("x1", c), h.querySelector(".xv").setAttribute("x2", c), 
    h.querySelector(".xhz").setAttribute("y1", l), h.querySelector(".xhz").setAttribute("y2", l), 
    h.querySelector(".xpt").setAttribute("transform", `translate(${p.W - p.pr + 2},${l - 10})`), 
    h.querySelector(".xpt text").textContent = snapPx(b).toFixed(2), h.querySelector(".xtt").setAttribute("transform", `translate(${Math.min(p.pl + p.pw - 64, Math.max(p.pl, c - 32))},${p.pt + p.ph + 4})`), 
    h.querySelector(".xtt text").textContent = etStr(Math.round(v)).slice(11, 19);
  });
  const i = () => {
    const o = e._ch;
    !o || !o.drag || (o.drag = null, e.classList.remove("panning"), drawChart(e));
  };
  e.addEventListener("pointerup", i), e.addEventListener("pointercancel", i), e.addEventListener("pointerleave", () => {
    const o = e.querySelector(".xh2");
    o && (o.style.display = "none");
  }), e.addEventListener("dblclick", () => {
    chartFit(e), e._ch.view.p0 = e._ch.view.p1 = null, drawChart(e);
  }), e.addEventListener("click", o => {
    const r = o.target.closest("[data-ev]");
    r && typeof openEvent == "function" && (o.stopPropagation(), openEvent(r.dataset.ev));
  }), e.addEventListener("pointerover", o => {
    const r = o.target.closest("[data-ev]"), c = e.querySelector(".tc-tip");
    if (!c) return;
    if (!r) {
      c.hidden = !0;
      return;
    }
    const l = e._ch.cfg.events.find(h => h.id === r.dataset.ev);
    if (!l) return;
    const p = e.getBoundingClientRect(), u = r.getBoundingClientRect();
    c.innerHTML = `<b>${esc(l.event)}</b><span class="imp ${l.impact}">${impactLabel(l.impact)} impact · ${etStr(l.ts).slice(11, 16)} ET</span>${[ "actual", "forecast", "previous" ].map(h => `<div><span>${h[0].toUpperCase() + h.slice(1)}</span><span>${esc(l[h] ?? "—")}</span></div>`).join("")}`, 
    c.hidden = !1, c.style.left = Math.min(u.left - p.left - 10, p.width - 230) + "px", 
    c.style.top = u.top - p.top - c.offsetHeight - 10 + "px";
  });
}

const CANDLE_CACHE = {};

async function getCandles(e, t, a, {preview: n, inst: s = "NQ"} = {}) {
  if (e = Math.floor(e / 60) * 60, t = Math.ceil(t / 60) * 60, S.mode === "server") {
    const i = s + e + "-" + t;
    return CANDLE_CACHE[i] || (CANDLE_CACHE[i] = apiJSON(`api/market/candles?symbol=${encodeURIComponent(s)}&from=${e}&to=${t}`).then(o => ({
      candles: o.candles || [],
      provider: o.provider
    })).catch(() => ({
      candles: [],
      provider: "error"
    }))), CANDLE_CACHE[i];
  }
  return {
    candles: n !== !1 ? synthCandles(e, t, a) : [],
    provider: "preview"
  };
}

let TK = null;

function autoExitTime() {
  const e = nowET(), t = e.slice(11, 19);
  return TK.date === todayStr() && (!TK.entryTime || t > hms(TK.entryTime)) ? t : hms(TK.entryTime) || t;
}

const hms = e => (e = String(e || "").trim(), /^\d{1,2}:\d{2}$/.test(e) && (e += ":00"), 
/^\d{1,2}:\d{2}:\d{2}$/.test(e) ? e.padStart(8, "0") : "");

function ticketFrom(e, t) {
  const a = lsGet("tj.last", {}), n = S.accounts.filter(o => o.status !== "archived");
  if (e) {
    const o = e.executions && e.executions.length ? e.executions.map(c => ({
      ...c
    })) : [ {
      id: uid(),
      side: e.direction === "long" ? "buy" : "sell",
      qty: e.contracts,
      price: e.entry,
      t: wallOfTrade(e, hms(e.entry_time) || "09:30:00")
    }, ...e.exit != null ? [ {
      id: uid(),
      side: e.direction === "long" ? "sell" : "buy",
      qty: e.contracts,
      price: e.exit,
      t: wallOfTrade(e, hms(e.exit_time) || hms(e.entry_time) || "09:31:00")
    } ] : [] ], r = o.length <= 2 && (o.length < 2 || +o[0].qty == +o[1].qty);
    return {
      id: e.id,
      inst: e.instrument || "NQ",
      account: e.account_id,
      copyTo: new Set,
      dir: e.direction,
      qty: e.contracts,
      date: e.date,
      entry: e.entry,
      entryTime: hms(e.entry_time),
      stop: e.stop ?? "",
      target: e.target ?? "",
      exit: e.exit ?? "",
      exitTime: hms(e.exit_time),
      multi: !r,
      execs: o,
      setup: e.setup || "",
      session: e.session || "",
      fees: e.fees_c != null ? (e.fees_c / 100).toFixed(2) : "",
      tags: (e.tags || []).join(", "),
      notes: e.notes || "",
      adv: !1,
      tf: 1
    };
  }
  const s = nowET(), i = /^d:\d{4}-\d{2}-\d{2}$/.test(t || "") ? t.slice(2) : todayStr();
  return {
    id: null,
    inst: INSTR[a.inst] ? a.inst : "NQ",
    account: (n.find(o => o.id === a.account) || F.account !== "all" && acct(F.account) || n[0] || {}).id,
    copyTo: new Set((a.copyTo || []).filter(o => n.some(r => r.id === o))),
    dir: null,
    qty: a.contracts || 1,
    date: i,
    entry: "",
    entryTime: i === todayStr() ? s.slice(11, 19) : "09:30:00",
    stop: "",
    target: "",
    exit: "",
    exitTime: "",
    multi: !1,
    execs: [],
    setup: "",
    session: "",
    fees: "",
    tags: "",
    notes: "",
    adv: !1,
    tf: 1
  };
}

function tkExecs() {
  if (TK.multi) return TK.execs.filter(n => n.qty > 0 && isFinite(parseFloat(n.price)) && n.t).map(n => ({
    ...n,
    price: +n.price,
    qty: +n.qty
  }));
  const e = [];
  if (!TK.dir || !(+TK.qty > 0)) return e;
  const t = TK.dir === "long" ? "buy" : "sell", a = TK.dir === "long" ? "sell" : "buy";
  return isFinite(parseFloat(TK.entry)) && e.push({
    id: "e",
    side: t,
    qty: +TK.qty,
    price: +TK.entry,
    t: wallTs(TK.date, hms(TK.entryTime) || "09:30:00")
  }), isFinite(parseFloat(TK.exit)) && e.length && e.push({
    id: "x",
    side: a,
    qty: +TK.qty,
    price: +TK.exit,
    t: wallTs(TK.date, hms(TK.exitTime) || hms(TK.entryTime) || "09:30:00")
  }), e;
}

function tkState() {
  const e = tkExecs(), t = positionOf(e, TK.inst), a = TK.multi ? t.dir : TK.dir, n = TK.multi ? t.avgEntry != null ? Math.round(t.avgEntry * 100) / 100 : "" : TK.entry, s = TK.multi ? t.maxQty || 0 : +TK.qty, i = riskOf({
    entry: n,
    stop: TK.stop,
    target: TK.target,
    qty: s,
    dir: a,
    inst: TK.inst
  }), o = TK.account ? riskBudget(TK.account, TK.date, TK.id ? getDoc("trades", TK.id)?.copy_group : null) : null, r = e.length ? etEpoch(e.slice().sort((c, l) => c.t < l.t ? -1 : 1)[0].t) : etEpoch(wallTs(TK.date, hms(TK.entryTime) || "09:30:00"));
  return {
    ex: e,
    pos: t,
    dir: a,
    entry: n,
    qty: s,
    r: i,
    budget: o,
    t0: r
  };
}

function tkNum(e, t, {val: a, ph: n = ""} = {}) {
  return `<label class="tk-f"><span>${t}</span><div class="tk-in"><input name="${e}" inputmode="decimal" value="${esc(a ?? TK[e] ?? "")}" placeholder="${n}" data-tk="${e}" autocomplete="off"></div></label>`;
}

function ticketPanel(e) {
  if (billFrozen(TK.account)) {
    const i = S.accounts.find(o => o.status !== "archived" && !billFrozen(o.id));
    i && (TK.account = i.id);
  }
  const t = S.accounts.filter(i => i.status !== "archived" && billFrozen(i.id)).length, a = S.accounts.filter(i => (i.status !== "archived" || i.id === TK.account) && !billFrozen(i.id)), n = tkState(), s = TK.execs.map((i, o) => `<div class="tk-ex" data-i="${o}">\n      <div class="seg sm2">${[ "buy", "sell" ].map(r => `<button type="button" class="${i.side === r ? "on " + r : ""}" data-act="tk-exside" data-i="${o}" data-v="${r}">${r === "buy" ? "Buy" : "Sell"}</button>`).join("")}</div>\n      <input data-tkx="qty" data-i="${o}" value="${esc(i.qty)}" inputmode="numeric" aria-label="Quantity" class="q">\n      <input data-tkx="price" data-i="${o}" value="${esc(i.price)}" inputmode="decimal" aria-label="Price" placeholder="Price">\n      <input data-tkx="time" data-wheel="time" data-i="${o}" value="${esc(i.t.slice(11, 19))}" aria-label="Time (ET)" placeholder="hh:mm:ss" class="tm">\n      <button type="button" class="link" data-act="tk-exdel" data-i="${o}" aria-label="Remove execution">×</button></div>`).join("");
  return `<div class="tk-head"><div><h2>${TK.multi && n.pos.dir ? "Trade details" : e}</h2><span class="muted" id="tkSummary">${tkSummary(n)}</span></div><a class="link" href="#trades" data-act="tk-cancel">Cancel</a></div>\n  ${TK.id ? "" : '<button type="button" class="ai-banner ai-only" data-act="ai-log"><span class="ai-sp" aria-hidden="true">✦</span><span><b>Log with AI</b><small>Describe your trades in plain words, or import a screenshot.</small></span><i aria-hidden="true">›</i></button>'}\n  <div class="tk-sec">\n    <label class="tk-f"><span>Account</span><select data-tk="account">${opts(a.map(i => [ i.id, acctLabel(i.id) ]), TK.account)}</select></label>\n    ${t ? `<button type="button" class="tk-frozen" data-frozen>${billBadge(S.accounts.find(i => billFrozen(i.id)).id)}<span>${t} paused account${t > 1 ? "s" : ""}</span><b>Unlock</b></button>` : ""}\n    ${!TK.id && a.length > 1 ? `<div class="tk-copies"><span class="help">Also on</span>${a.filter(i => i.id !== TK.account).map(i => `<button type="button" class="chip ${TK.copyTo.has(i.id) ? "on" : ""}" data-act="tk-copy" data-v="${i.id}">${esc(acctLabel(i.id))}</button>`).join("")}</div>` : ""}\n  </div>\n  <div id="tkAlerts">${tkAlerts(n)}</div>\n  <div class="tk-sec">\n    <label class="tk-f"><span>Symbol</span><select data-tk="inst">${opts(Object.entries(INSTR).map(([i, o]) => [ i, `${i} — ${o.name}` ]), TK.inst)}</select></label>\n    <div class="tk-dir">${[ [ "long", "Buy", "Long" ], [ "short", "Sell", "Short" ] ].map(([i, o, r]) => `<button type="button" class="${i} ${n.dir === i ? "on" : ""}" data-act="tk-dir" data-v="${i}" ${TK.multi ? "disabled" : ""}><b>${o}</b><span>${r}</span></button>`).join("")}</div>\n    <div class="tk-row2"><label class="tk-f"><span>Date</span><input type="date" data-tk="date" value="${TK.date}"></label>${TK.multi ? "" : `<label class="tk-f"><span>Entry time (ET)</span><input data-tk="entryTime" data-wheel="time" value="${esc(TK.entryTime)}" placeholder="hh:mm:ss" autocomplete="off"></label>`}</div>\n    ${TK.multi ? "" : `<div class="tk-f"><span>Contracts</span><div class="tk-qty"><button type="button" data-act="tk-qty" data-v="-1" aria-label="Fewer contracts">−</button><input data-tk="qty" value="${esc(TK.qty)}" inputmode="numeric" aria-label="Contracts"><button type="button" data-act="tk-qty" data-v="1" aria-label="More contracts">+</button></div></div>`}\n    ${TK.multi ? `<div class="tk-f"><span>Avg entry</span><div class="tk-ro" id="tkAvg">${n.entry !== "" ? (+n.entry).toFixed(2) : "—"}</div></div>` : tkNum("entry", "Entry price", {
    ph: "21845.25"
  })}\n    <div class="tk-row2">${tkNum("stop", "Stop")}${tkNum("target", "Target")}</div>\n  </div>\n  <div class="tk-risk" id="tkRisk">${tkRisk(n)}</div>\n  <div class="tk-sec">\n    ${TK.multi ? `<div class="tk-f"><span>Executions <span class="help">· times in ET</span></span><div class="tk-exs">${s}</div><button type="button" class="btn sm" data-act="tk-exadd">+ Add execution</button></div>` : `<div class="tk-row2">${tkNum("exit", "Exit price")}<label class="tk-f"><span>Exit time (ET)</span><input data-tk="exitTime" data-wheel="time" value="${esc(TK.exitTime)}" placeholder="hh:mm:ss" autocomplete="off"></label></div>\n      <div class="row"><button type="button" class="chip" data-act="tk-exitat" data-v="target">Exit at target</button><button type="button" class="chip" data-act="tk-exitat" data-v="stop">Exit at stop</button><span style="flex:1"></span><button type="button" class="link" data-act="tk-multi">+ Add execution</button></div>`}\n    <div class="tk-result" id="tkResult">${tkResult(n)}</div>\n  </div>\n  <label class="tk-f"><span>Notes</span><textarea data-tk="notes" rows="3" placeholder="What happened, what you saw…">${esc(TK.notes)}</textarea></label>\n  ${TK.id ? "" : '<p class="help" style="margin:-4px 0 0">Setup, fees, checklist and review are on the next page.</p>'}\n  <div class="err" id="tkErr"></div>\n  <button class="btn primary tk-save" data-act="tk-save">${TK.id ? "Save changes" : "Save trade"}</button>`;
}

function tkSummary(e) {
  if (!e.dir) return `${TK.inst} · choose Buy or Sell`;
  const t = e.pos;
  return `${TK.inst} ${e.dir === "long" ? "Long" : "Short"} · ${TK.multi ? t.maxQty : TK.qty} contract${(TK.multi ? t.maxQty : TK.qty) == 1 ? "" : "s"}${e.entry !== "" ? " · avg " + (+e.entry).toFixed(2) : ""}${TK.multi && t.open ? ` · ${Math.abs(t.open)} open` : ""}`;
}

function tkRisk(e) {
  const t = e.r, a = e.budget;
  return `<div><span>Risk</span><b class="neg">${t.risk_c != null ? money(-t.risk_c) : "—"}</b><small>${t.riskPts != null ? t.riskPts.toFixed(2) + " pts" : ""}</small></div>\n    <div><span>Reward</span><b class="pos">${t.rew_c != null ? money(t.rew_c) : "—"}</b><small>${t.rewPts != null ? t.rewPts.toFixed(2) + " pts" : ""}</small></div>\n    <div><span>R : R</span><b>${t.rr ? "1 : " + t.rr.toFixed(2) : "—"}</b><small>${t.stopWrong ? '<span class="neg">Stop is on the wrong side</span>' : t.targetWrong ? '<span class="neg">Target is on the wrong side</span>' : ""}</small></div>`;
}

function tkAlerts(e) {
  const t = [], a = e.budget;
  if (a) {
    const i = a.left - (e.r.risk_c || 0);
    t.push(`<div class="tk-budget ${i < 0 ? "over" : ""}"><div><span>Daily risk left</span><b>${moneyU(a.left)}</b></div><div><span>Trade risk</span><b>${e.r.risk_c != null ? moneyU(e.r.risk_c) : "—"}</b></div><div><span>After trade</span><b class="${i < 0 ? "neg" : ""}">${e.r.risk_c != null ? money(i, {
      sign: !1
    }).replace("−", "−") : "—"}</b></div>${i < 0 ? '<p class="neg">Risk limit exceeded — it will be recorded on the trade.</p>' : ""}</div>`);
  }
  const n = +(S.settings.max_contracts || 0), s = TK.multi ? e.pos.maxQty : +TK.qty;
  if (n && s > n && t.push(`<div class="tk-warn">Oversized: ${s} contracts, your maximum is ${n}.</div>`), 
  isFinite(e.t0)) {
    const i = eventsBetween(e.t0 - 900, e.t0 + 1800).filter(o => o.impact === "high" || o.impact === "medium");
    for (const o of i.slice(0, 2)) {
      const r = (o.ts - e.t0) / 60;
      t.push(`<div class="tk-news ${o.impact}"><i></i><b>${impactLabel(o.impact)} news ${r >= 0 ? "in " + relMin(r) : relMin(r) + " ago"}</b><span>${esc(o.event)} · ${etStr(o.ts).slice(11, 16)} ET</span></div>`);
    }
  }
  return t.join("");
}

function tkResult(e) {
  const t = e.pos;
  if (!t.count || !t.closed) return `<span class="muted">${t.count && !t.closed ? `Position open: ${Math.abs(t.open)} contract${Math.abs(t.open) > 1 ? "s" : ""} — add the exit to close it.` : "P&L appears once the exit is set."}</span>`;
  const a = parseMoney(TK.fees) || 0, n = t.realized_c - a, s = t.avgExit != null && t.avgEntry != null ? (t.avgExit - t.avgEntry) * (t.dir === "long" ? 1 : -1) : null, i = etEpoch(t.end) - etEpoch(t.start);
  return `<div><span>Result</span><b class="${cls(n)}">${money(n)}</b></div><div><span>Points</span><b>${s != null ? (s >= 0 ? "+" : "−") + Math.abs(s).toFixed(2) : "—"}</b></div><div><span>Duration</span><b>${fdur(i)}</b></div>${t.adds ? `<div><span>Adds</span><b>${t.adds}</b></div>` : ""}${t.partials ? `<div><span>Partial exits</span><b>${t.partials}</b></div>` : ""}`;
}

function tkRefresh({panel: e = !1} = {}) {
  if (e) {
    const s = $("#tkPanel");
    s && (s.innerHTML = ticketPanel(TK.id ? "Edit trade" : "New trade"));
  }
  const t = tkState(), a = (s, i) => {
    const o = $("#" + s);
    o && (o.innerHTML = i);
  };
  a("tkRisk", tkRisk(t)), a("tkAlerts", tkAlerts(t)), a("tkResult", tkResult(t)), 
  a("tkSummary", tkSummary(t));
  const n = $("#tkAvg");
  n && (n.textContent = t.entry !== "" ? (+t.entry).toFixed(2) : "—");
}

async function tkSave() {
  const e = $("#tkErr"), t = tkState(), a = t.pos, n = [];
  if (TK.account || n.push("an account"), t.dir || n.push("Buy or Sell"), t.ex.length || n.push("the entry price"), 
  n.length) {
    e.textContent = "Add " + n.join(", ") + ".";
    return;
  }
  if (a.flip) {
    e.textContent = "An execution reverses the position. Record the reversal as a separate trade.";
    return;
  }
  if (!a.closed) {
    e.textContent = `The position is still open (${Math.abs(a.open)} contract${Math.abs(a.open) > 1 ? "s" : ""}). Add the exit.`;
    return;
  }
  const s = t.ex.slice().sort((v, b) => v.t < b.t ? -1 : 1), i = etEpoch(a.start), o = etEpoch(a.end);
  await loadEcon(etStr(i - 86400).slice(0, 10), etStr(o + 86400).slice(0, 10));
  const r = TK.id ? structuredClone(getDoc("trades", TK.id)) : null, c = r || {
    id: uid(),
    discipline: {},
    emo: {},
    review: {},
    shots: [],
    setup: "",
    tags: [],
    fees_c: null
  }, l = riskOf({
    entry: a.avgEntry,
    stop: TK.stop,
    target: TK.target,
    qty: a.maxQty,
    dir: a.dir,
    inst: TK.inst
  });
  Object.assign(c, {
    instrument: TK.inst,
    account_id: TK.account,
    date: sessionOfTs(s[0].t),
    session_date: !0,
    entry_time: s[0].t.slice(11, 16),
    exit_time: a.end.slice(11, 16),
    direction: a.dir,
    contracts: a.maxQty,
    entry: Math.round(a.avgEntry * 100) / 100,
    exit: Math.round(a.avgExit * 100) / 100,
    pnl_c: a.realized_c,
    pnl_manual: !1,
    stop: numOrNull(TK.stop),
    target: numOrNull(TK.target),
    risk_c: l.risk_c || null,
    planned_rr: l.rr ? l.rr.toFixed(2) : "",
    executions: s.map(v => ({
      id: v.id && v.id.length > 2 ? v.id : uid(),
      side: v.side,
      qty: +v.qty,
      price: +v.price,
      t: v.t
    })),
    duration_s: o - i,
    session: sessionFor(s[0].t.slice(11, 16)),
    notes: TK.notes.trim(),
    adds: a.adds,
    partials: a.partials
  }, newsContext(i, o));
  const p = riskBudget(TK.account, c.date, c.copy_group);
  c.auto_flags = detectFlags(c, a, p), c.discipline = c.discipline || {};
  for (const v of c.auto_flags) {
    const b = AUTO_RULES[v].q;
    c.discipline[b] !== "n" && (c.discipline[b] = "n");
  }
  const u = TK.id ? [] : [ ...TK.copyTo ].filter(v => v !== TK.account && acct(v));
  u.length && (c.copy_group = uid()), put("trades", c), lsSet("tj.last", {
    account: TK.account,
    inst: TK.inst,
    contracts: a.firstQty || a.maxQty,
    copyTo: [ ...TK.copyTo ]
  });
  for (const v of u) put("trades", {
    ...structuredClone(c),
    id: uid(),
    account_id: v,
    created_at: void 0
  });
  if (r && r.copy_group) for (const v of siblings(c.id)) editDoc("trades", v.id, b => {
    [ ...SHARED_FIELDS, "executions", "duration_s", "news", "news_min", "news_near", "auto_flags", "exit_time", "entry_time" ].forEach(R => {
      b[R] = JSON.parse(JSON.stringify(c[R] ?? null));
    });
    const E = positionOf((b.executions || []).map(R => ({
      ...R,
      qty: R.qty * (b.contracts / (c.contracts || 1))
    })));
    E.closed && (b.pnl_c = E.realized_c);
  });
  toast(TK.id ? "Trade updated" : u.length ? `Trade saved on ${u.length + 1} accounts` : "Trade saved");
  const h = c.id, m = !TK.id;
  location.hash = "#trade/" + h, m ? (TK = null, showStep2(h)) : closeTicket();
}

document.addEventListener("input", e => {
  if (!TK) return;
  const t = e.target;
  if (t.dataset.tk) {
    const a = t.dataset.tk;
    if (TK[a] = t.value, a === "exit" && t.value.trim() && !TK.exitTime) {
      TK.exitTime = autoExitTime();
      const n = $('[data-tk="exitTime"]');
      n && (n.value = TK.exitTime);
    }
    if (a === "account") {
      tkRefresh({
        panel: !0
      });
      return;
    }
    if (a === "date") {
      const n = $("#tkDate");
      n && (n.textContent = "· " + fdate(TK.date, {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric"
      })), TK.multi && TK.execs.forEach(s => {
        s.t = TK.date + s.t.slice(10);
      }), TK.slide && /^\d{4}-\d{2}-\d{2}$/.test(TK.date) && loadEcon(TK.date, TK.date).then(() => {
        if (TK) {
          const s = $("#tkAlerts");
          s && (s.innerHTML = tkAlerts(tkState()));
        }
      });
    }
    tkRefresh();
    return;
  }
  if (t.dataset.tkx) {
    const a = +t.dataset.i, n = TK.execs[a];
    if (!n) return;
    const s = t.dataset.tkx;
    if (s === "time") {
      const i = hms(t.value);
      i && (n.t = wallTs(TK.date, i));
    } else n[s] = t.value;
    tkRefresh();
  }
}), document.addEventListener("change", e => {
  if (!TK) return;
  const t = e.target.dataset.tk;
  t === "account" && (TK.account = e.target.value, tkRefresh({
    panel: !0
  })), t === "inst" && (TK.inst = e.target.value, tkRefresh({
    panel: !0
  }));
}), document.addEventListener("click", e => {
  if (!TK) return;
  const t = e.target.closest('[data-act^="tk-"]');
  if (!t) return;
  const a = t.dataset.act, n = t.dataset.v;
  if (a === "tk-dir") TK.dir = n, tkRefresh({
    panel: !0
  }); else if (a === "tk-qty") {
    TK.qty = Math.max(1, (+TK.qty || 1) + +n);
    const s = $('[data-tk="qty"]');
    s && (s.value = TK.qty), tkRefresh();
  } else if (a === "tk-exitat") {
    if (TK[n] === "") {
      toast(`Set the ${n} first`);
      return;
    }
    TK.exit = TK[n], TK.exitTime || (TK.exitTime = autoExitTime()), tkRefresh({
      panel: !0
    });
  } else if (a === "tk-multi") {
    TK.execs = tkExecs(), TK.multi = !0;
    const s = TK.execs.at(-1), i = positionOf(TK.execs);
    TK.execs.push({
      id: uid(),
      side: i.dir === "short" ? "sell" : "buy",
      qty: 1,
      price: s ? s.price : "",
      t: s ? s.t : wallTs(TK.date, hms(TK.entryTime) || "09:30:00")
    }), tkRefresh({
      panel: !0
    });
  } else if (a === "tk-exadd") {
    const s = TK.execs.at(-1), i = positionOf(tkExecs());
    TK.execs.push({
      id: uid(),
      side: i.dir === "long" ? "sell" : "buy",
      qty: Math.abs(i.open) || 1,
      price: s ? s.price : "",
      t: s ? s.t : `${TK.date} 09:30:00`
    }), tkRefresh({
      panel: !0
    });
  } else if (a === "tk-exdel") TK.execs.splice(+t.dataset.i, 1), tkRefresh({
    panel: !0
  }); else if (a === "tk-exside") TK.execs[+t.dataset.i].side = n, tkRefresh({
    panel: !0
  }); else if (a === "tk-copy") TK.copyTo.has(n) ? TK.copyTo.delete(n) : TK.copyTo.add(n), 
  t.classList.toggle("on"); else if (a === "tk-save") tkSave(); else if (a === "tk-cancel") {
    e.preventDefault(), closeTicket();
    return;
  }
}), document.addEventListener("keydown", e => {
  TK && (e.metaKey || e.ctrlKey) && e.key === "Enter" && TK.slide && (e.preventDefault(), 
  tkSave()), TK && TK.slide && e.key === "Escape" && !document.querySelector(".cpop") && (e.preventDefault(), 
  closeTicket());
});

function openTicket(e, {date: t} = {}) {
  if (!S.accounts.length) {
    openDrawer(null, {
      date: t
    });
    return;
  }
  const a = e ? getDoc("trades", e) : null;
  TK = ticketFrom(a, t ? "d:" + t : ""), TK.slide = !0, TK._arg = "slide";
  let n = $("#tkSlide");
  if (!n) {
    n = document.createElement("aside"), n.id = "tkSlide", n.className = "evp tks", 
    n.setAttribute("aria-label", "Trade ticket"), document.body.append(n);
    const s = document.createElement("div");
    s.id = "tkScrim", s.className = "evp-scrim", s.addEventListener("click", () => closeTicket()), 
    document.body.append(s), swipeDismiss(n, {
      scroller: () => n.querySelector(".evp-in"),
      onClose: () => closeTicket(),
      ignore: ".cpop"
    });
  }
  n.innerHTML = `<div class="evp-in tk-panel tk-slide" id="tkPanel">${ticketPanel(TK.id ? "Edit trade" : "New trade")}</div>`, 
  requestAnimationFrame(() => {
    n.classList.add("open"), $("#tkScrim").classList.add("open"), document.body.classList.add("evp-lock");
  }), tkRefresh(), loadEcon(TK.date, TK.date).then(() => {
    if (TK && TK.slide) {
      const s = $("#tkAlerts");
      s && (s.innerHTML = tkAlerts(tkState()));
    }
  });
}

function closeTicket() {
  if (STEP2) {
    closeStep2();
    return;
  }
  const e = $("#tkSlide");
  e && e.classList.remove("open");
  const t = $("#tkScrim");
  t && t.classList.remove("open"), document.body.classList.remove("evp-lock"), TK = null;
}

let STEP2 = null;

function step2Html(e) {
  const t = getDoc("trades", e);
  if (!t) return "";
  const a = tNet(t), n = t.emo || {};
  return `<div class="okmark" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 12.5l4 4 8-9"/></svg></div><div class="tk-head"><div><span class="stepl">Step 2 of 2 · Review</span><h2>How did it go?</h2><span class="muted">${esc(t.instrument || "NQ")} ${t.direction === "long" ? "Long" : "Short"} · ${t.contracts} · <b class="${cls(a)}">${money(a)}</b></span></div><button class="link" data-act="s2-close">Skip</button></div>\n    <section class="s2sec"><h3>Discipline checklist</h3>${checklist("trades", t)}</section>\n    <section class="s2sec"><h3>Emotional state</h3>${chipsFor("trades", e, "emo.before", EMO, n.before)}</section>\n    <button class="btn primary tk-save" data-act="s2-close">Done</button>`;
}

function showStep2(e) {
  STEP2 = e;
  const t = $("#tkPanel");
  t && (t.innerHTML = step2Html(e), t.scrollTop = 0);
}

function closeStep2() {
  STEP2 = null;
  const e = $("#tkSlide");
  e && e.classList.remove("open");
  const t = $("#tkScrim");
  t && t.classList.remove("open"), document.body.classList.remove("evp-lock"), render();
}

document.addEventListener("click", e => {
  if (STEP2) {
    if (e.target.closest('[data-act="s2-close"]')) {
      closeStep2();
      return;
    }
    e.target.closest("#tkSlide [data-act]") && setTimeout(() => {
      if (STEP2) {
        const t = $("#tkPanel"), a = t.scrollTop;
        t.innerHTML = step2Html(STEP2), t.scrollTop = a;
      }
    }, 40);
  }
}), document.addEventListener("keydown", e => {
  STEP2 && e.key === "Escape" && closeStep2();
});

const NEWS = {
  range: "today",
  info: null
};

function newsRange(e) {
  const t = todayStr(), a = weekStart(t);
  return {
    today: [ t, t ],
    tomorrow: [ addDays(t, 1), addDays(t, 1) ],
    week: [ a, addDays(a, 6) ],
    next: [ addDays(a, 7), addDays(a, 13) ]
  }[e];
}

const estTag = e => e.status === "estimated" ? ' <span class="est" title="Projected from the usual release pattern — confirm closer to the date">est.</span>' : e.status === "official-tentative" ? ' <span class="est" title="Federal Reserve tentative calendar">tent.</span>' : "";

function eventRow(e) {
  const t = econState(e), a = econDiff(e.actual, e.forecast), n = e.revised && e.revised !== e.previous, s = e.actual != null && e.actual !== "" ? `<b>${esc(e.actual)}</b>${a && a.direction !== "in_line" ? `<small class="sur ${a.direction}">${a.text}</small>` : ""}` : t === "awaiting" ? '<em class="await">Awaiting</em>' : '<span class="faint">—</span>', i = !(e.actual || e.forecast || e.previous) && t !== "awaiting";
  return `<button class="ff-row ${e.ts < Date.now() / 1e3 ? "past" : ""} ${t === "awaiting" ? "due" : ""} ${i ? "novals" : ""}" data-act="ev-open" data-id="${esc(e.id)}">\n    <span class="ff-t">${etStr(e.ts).slice(11, 16)}</span><span class="ff-c">USD</span><span class="ff-i"><span class="imp ${e.impact}" title="${impactLabel(e.impact)} impact"><i></i></span></span>\n    <span class="ff-n">${esc(e.event)}${estTag(e)}</span><span class="ff-v" data-l="${{
    en: "Actual",
    fr: "Réel",
    es: "Real"
  }[LANG]}">${s}</span><span class="ff-v" data-l="${{
    en: "Fcst",
    fr: "Prév.",
    es: "Prev."
  }[LANG]}">${e.forecast != null && e.forecast !== "" ? esc(e.forecast) : '<span class="faint">—</span>'}</span>\n    <span class="ff-v" data-l="${{
    en: "Prev",
    fr: "Préc.",
    es: "Ant."
  }[LANG]}">${e.previous != null && e.previous !== "" ? esc(e.previous) : '<span class="faint">—</span>'}${n ? `<small class="faint" title="Previously reported">rev. ${esc(e.revised)}</small>` : ""}</span><span class="ff-go">›</span></button>`;
}

function vNews(e) {
  [ "today", "tomorrow", "week", "next" ].includes(e) && (NEWS.range = e);
  const [t, a] = newsRange(NEWS.range), n = [ ...Array(Math.round((pd(a) - pd(t)) / 864e5) + 1) ].every((o, r) => ECON.days[addDays(t, r)]);
  n || loadEcon(t, a).then(() => {
    route().v === "news" && render();
  });
  let s = "";
  if (!n) s = '<div class="skel" style="height:260px;border-radius:18px"></div>'; else {
    const o = [];
    for (let c = t; c <= a; c = addDays(c, 1)) o.push(c);
    const r = o.map(c => {
      const l = ECON.days[c] || [];
      return !l.length && o.length > 1 ? "" : `<div class="ff-day"><span>${c === todayStr() ? "Today · " : ""}${fdate(c, {
        weekday: "long",
        month: "short",
        day: "numeric"
      })}</span><span class="faint">${l.length ? l.length + " event" + (l.length > 1 ? "s" : "") : ""}</span></div>${l.length ? l.map(eventRow).join("") : '<div class="ff-empty">No major U.S. economic events.</div>'}`;
    }).join("");
    s = r ? `<div class="surface ff"><div class="ff-head"><span>Time</span><span>Cur</span><span>Imp</span><span>Event</span><span class="r">Actual</span><span class="r">Forecast</span><span class="r">Previous</span><span></span></div>${r}</div>` : '<div class="surface empty">No major U.S. economic events in this period.</div>';
  }
  const i = S.mode === "server" && S.me && S.me.is_admin;
  return `<div class="row" style="margin-bottom:18px"><div class="seg">${[ [ "today", "Today" ], [ "tomorrow", "Tomorrow" ], [ "week", "This week" ], [ "next", "Next week" ] ].map(([o, r]) => `<a class="btnlike ${NEWS.range === o ? "on" : ""}" href="#news/${o}">${r}</a>`).join("")}</div>\n    <span class="muted" style="margin-left:auto">USD · <span class="imp high"><i></i>High</span> <span class="imp medium"><i></i>Medium</span> · Eastern Time</span></div>\n  ${s}\n  <p class="help" style="margin-top:12px">Click an event for details. <span class="est">est.</span> = date projected from the usual release pattern. Numbers come from the economic data provider.</p>\n  ${i ? '<div class="row" style="margin-top:24px"><label class="btn sm">Import schedule file (JSON)<input type="file" accept=".json,application/json" data-econ-import hidden></label><span class="help">Same format as econ-us-2026-2027.json. Existing events are kept.</span></div>' : ""}\n  ${i ? `<details class="more" style="margin-top:12px"><summary>Add an event manually</summary><form data-form="econ" class="fgrid four surface pad" autocomplete="off">\n    <label class="f"><span>Date</span><input type="date" name="date" value="${todayStr()}" required></label><label class="f"><span>Time (ET)</span><input name="time" placeholder="08:30" required></label>\n    <label class="f" style="grid-column:span 2"><span>Event</span><input name="event" required placeholder="CPI m/m"></label>\n    <label class="f"><span>Impact</span><select name="impact">${opts([ [ "high", "High" ], [ "medium", "Medium" ] ], "high")}</select></label>\n    <label class="f"><span>Actual</span><input name="actual"></label><label class="f"><span>Forecast</span><input name="forecast"></label><label class="f"><span>Previous</span><input name="previous"></label>\n    <div class="f full"><div><button class="btn primary" type="submit">Add event</button></div></div></form></details>` : ""}`;
}

async function addEcon(e) {
  const t = new FormData(e), a = String(t.get("time") || "").trim();
  if (!/^\d{1,2}:\d{2}$/.test(a)) {
    toast("Time format: 08:30");
    return;
  }
  try {
    await apiJSON("api/admin/econ", {
      method: "POST",
      body: {
        date: t.get("date"),
        time: a,
        event: t.get("event"),
        impact: t.get("impact"),
        actual: t.get("actual"),
        forecast: t.get("forecast"),
        previous: t.get("previous")
      }
    });
    for (const n in ECON.pending) delete ECON.pending[n];
    ECON.days = {}, toast("Event added"), render();
  } catch (n) {
    toast(n.message);
  }
}

function newsWidget() {
  const e = todayStr(), t = ECON.days[e];
  return t ? `<section class="sec"><div class="sec-h"><h2>Economic calendar</h2><a class="link" href="#news">Full calendar</a></div><div class="surface ev-mini">${t.length ? t.map(a => `<div class="evm ${a.ts < Date.now() / 1e3 ? "past" : ""}" data-act="ev-open" data-id="${esc(a.id)}" role="button" tabindex="0"><span class="ev-t">${etStr(a.ts).slice(11, 16)}</span><span class="imp ${a.impact}"><i></i>${impactLabel(a.impact)}</span><span class="ev-n">${esc(a.event)}</span><span class="muted">${a.actual != null ? "Actual " + esc(a.actual) : a.forecast ? "Fcst " + esc(a.forecast) : ""}</span></div>`).join("") : '<div class="empty">No major U.S. economic events today.</div>'}</div></section>` : (loadEcon(e, e).then(() => {
    route().v === "dashboard" && scheduleRender();
  }), "");
}

async function tradeChartMount(e) {
  const t = $("#tradeChart");
  if (!t || !e) return;
  const n = (e.executions && e.executions.length ? e.executions : [ {
    side: e.direction === "long" ? "buy" : "sell",
    qty: e.contracts,
    price: e.entry,
    t: wallOfTrade(e, hms(e.entry_time) || "09:30:00")
  }, ...e.exit != null ? [ {
    side: e.direction === "long" ? "sell" : "buy",
    qty: e.contracts,
    price: e.exit,
    t: wallOfTrade(e, hms(e.exit_time) || hms(e.entry_time) || "09:31:00")
  } ] : [] ]).map(p => ({
    ...p,
    t: etEpoch(p.t)
  })).filter(p => isFinite(p.t));
  if (!n.length) return;
  const s = Math.min(...n.map(p => p.t)), i = Math.max(...n.map(p => p.t)), o = s - 5400, r = i + 5400;
  chartMount(t, {
    editable: !1,
    inst: e.instrument || "NQ",
    h: innerWidth >= 1920 ? 540 : 420,
    tf: t.dataset.tf ? +t.dataset.tf : 1,
    levels: {
      entry: e.entry,
      stop: e.stop,
      target: e.target,
      exit: e.exit
    },
    dir: e.direction,
    qty: e.contracts,
    execs: n,
    events: [],
    candles: [],
    focus: [ s, i ]
  }), loadEcon(etStr(o).slice(0, 10), etStr(r).slice(0, 10)).then(() => {
    t._ch && chartSet(t, {
      events: eventsBetween(o - 3600, r + 3600)
    });
  });
  const {candles: c, provider: l} = await getCandles(o, r, n.map(p => ({
    t: p.t,
    price: +p.price
  })), {
    preview: S.mode !== "server",
    inst: e.instrument || "NQ"
  });
  t._ch && chartSet(t, {
    candles: c,
    note: l === "preview" ? "Preview: sample market data." : c.length ? "" : "No market data for this period."
  });
}

function tradeEntryEpoch(e) {
  const t = (e.executions || []).slice().sort((a, n) => a.t < n.t ? -1 : 1)[0];
  return etEpoch(t ? t.t : wallOfTrade(e, (e.entry_time || "09:30") + ":00"));
}

function newsBlock(e) {
  const t = e.news || [];
  if (!t.length) return '<div class="muted">No high or medium U.S. events from 30 minutes before entry to 30 minutes after exit.</div>';
  const a = tradeEntryEpoch(e), n = etStr(Math.min(...t.map(o => o.ts))).slice(0, 10), s = etStr(Math.max(...t.map(o => o.ts))).slice(0, 10);
  return ECON.days[n] && ECON.days[s] || loadEcon(n, s).then(() => {
    const o = $("#newsCtx");
    o && route().v === "trade" && (o.innerHTML = newsBlock(e));
  }), t.map(o => {
    const r = findEvent(o.id) || o, c = a - o.ts;
    return `<div class="nctx"><div class="nctx-h"><span class="imp ${o.impact}"><i></i></span><b>${esc(o.event)}</b><span class="muted">${etStr(o.ts).slice(11, 16)} ET</span></div>\n      <div class="nctx-v"><span>Actual <b>${esc(r.actual ?? "—")}</b></span><span>Forecast <b>${esc(r.forecast ?? "—")}</b></span><span>Previous <b>${esc(r.previous ?? "—")}</b></span></div>\n      <div class="nctx-f"><span>Your entry ${etStr(a).slice(11, 19)} · <b>${Math.abs(c) < 1 ? "at the release" : fmtSec(c) + (c > 0 ? " after" : " before") + " the release"}</b></span><button class="link" data-act="ev-open" data-id="${esc(o.id)}">View details</button></div></div>`;
  }).join("");
}

function anNews(e) {
  const t = {
    "Within 5 min of high-impact news": e.filter(n => n.news_min != null && Math.abs(n.news_min) <= 5),
    "Within 15 min of high-impact news": e.filter(n => n.news_min != null && Math.abs(n.news_min) <= 15),
    "Around any high or medium event (±30 min)": e.filter(n => (n.news || []).length),
    "No nearby news": e.filter(n => !(n.news || []).length && (n.news_min == null || Math.abs(n.news_min) > 60))
  }, a = e.filter(n => n.news !== void 0).length;
  return `${a < e.length ? `<p class="help" style="margin:0 0 12px">${e.length - a} older trades have no news data yet — it is attached automatically when a trade is saved from the ticket.</p>` : ""}<div class="surface">${groupTable("Context", new Map(Object.entries(t).filter(([, n]) => n.length)), {
    showR: !1
  })}</div>`;
}

async function importEconFile(e) {
  const t = e.files[0];
  if (e.value = "", !t) return;
  let a;
  try {
    a = JSON.parse(await t.text());
  } catch {
    toast("This file is not valid JSON.");
    return;
  }
  if (!a || !Array.isArray(a.events)) {
    toast('Expected {"events":[…]}');
    return;
  }
  try {
    const n = await apiJSON("api/admin/econ/import", {
      method: "POST",
      body: a
    });
    for (const s in ECON.pending) delete ECON.pending[s];
    ECON.days = {}, toast(`Imported ${n.imported} events`), render();
  } catch (n) {
    toast(n.message);
  }
}

document.addEventListener("change", e => {
  e.target.hasAttribute && e.target.hasAttribute("data-econ-import") && importEconFile(e.target);
});

function econNum(e) {
  if (e == null) return null;
  const t = String(e).replace(/[,\s]/g, "").match(/^([+-]?\d+(?:\.\d+)?)(%|K|M|B|T)?$/i);
  return t ? [ +t[1], (t[2] || "").toUpperCase(), (t[1].split(".")[1] || "").length ] : null;
}

function econDiff(e, t) {
  const a = econNum(e), n = econNum(t);
  if (!a || !n || a[1] !== n[1]) return null;
  const s = Math.round((a[0] - n[0]) * 1e4) / 1e4, i = a[1] === "%" ? " pp" : a[1], o = Math.min(3, Math.max(a[2], n[2]));
  return {
    value: s,
    direction: s > 0 ? "above" : s < 0 ? "below" : "in_line",
    text: s === 0 ? `In line (0${i})` : (s > 0 ? "+" : "−") + Math.abs(s).toFixed(o) + i
  };
}

function econProfile(e) {
  return ECON_PROFILES.find(t => new RegExp(t.match, "i").test(e)) || null;
}

function econState(e) {
  const t = Date.now() / 1e3;
  return e.ts > t ? "before" : e.actual == null || e.actual === "" ? (e.source === "schedule" || e.source === "manual" || e.sample || e.status) && t - e.ts > 86400 ? "past_no_data" : "awaiting" : t - e.ts >= 3600 ? "post" : "released";
}

const STATE_LABEL = {
  before: "Upcoming",
  awaiting: "Awaiting release",
  released: "Released",
  post: "Released",
  past_no_data: "No data recorded"
}, fmtSec = e => {
  e = Math.round(Math.abs(e));
  const t = Math.floor(e / 3600), a = Math.floor(e % 3600 / 60), n = e % 60;
  return t ? `${t}h ${a}m` : a ? `${a}m ${pad(n)}s` : `${n}s`;
}, EVP = {
  id: null,
  d: null,
  timer: 0
};

function evPanelEl() {
  let e = $("#evPanel");
  if (!e) {
    e = document.createElement("aside"), e.id = "evPanel", e.className = "evp", e.setAttribute("aria-label", "Economic event"), 
    e.innerHTML = '<div class="evp-in"></div>', document.body.append(e);
    const t = document.createElement("div");
    t.id = "evScrim", t.className = "evp-scrim", t.addEventListener("click", closeEvent), 
    document.body.append(t), swipeDismiss(e, {
      scroller: () => e.querySelector(".evp-in"),
      onClose: closeEvent,
      ignore: ".tbl"
    });
  }
  return e;
}

function findEvent(e) {
  for (const t in ECON.days) {
    const a = (ECON.days[t] || []).find(n => n.id === e);
    if (a) return a;
  }
  return null;
}

async function openEvent(e) {
  const t = evPanelEl();
  EVP.id = e, EVP.d = null, clearTimeout(EVP.timer), t.classList.add("open"), $("#evScrim").classList.add("open"), 
  document.body.classList.add("evp-lock");
  const a = findEvent(e);
  t.firstChild.innerHTML = a ? evpHeader(a, econState(a)) + '<div class="skel" style="height:140px;border-radius:14px;margin-top:18px"></div>' : '<div class="skel" style="height:220px;border-radius:14px"></div>', 
  await evLoad();
}

function closeEvent() {
  const e = $("#evPanel");
  e && (e.classList.remove("open"), $("#evScrim").classList.remove("open"), document.body.classList.remove("evp-lock"), 
  EVP.id = null, clearTimeout(EVP.timer));
}

document.addEventListener("keydown", e => {
  e.key === "Escape" && EVP.id && closeEvent();
});

async function evLoad() {
  const e = EVP.id;
  if (!e) return;
  let t;
  if (S.mode === "server") try {
    t = await apiJSON("api/econ/event/" + e);
  } catch {
    $("#evPanel .evp-in").innerHTML = '<div class="empty">Economic data temporarily unavailable.</div>';
    return;
  } else t = evLocalDetail(e);
  if (EVP.id !== e || !t) return;
  AIE && AIE.rep[e] && AIE.rep[e].state && AIE.rep[e].state !== "ready" && t.event.actual && AIE.rep[e].state === "awaiting_actual" && delete AIE.rep[e], 
  EVP.d = t, evRender();
  const a = t.state, n = a === "awaiting" ? 2e4 : a === "released" ? 6e4 : a === "before" && t.event.ts - Date.now() / 1e3 < 900 ? 3e4 : 0;
  clearTimeout(EVP.timer), n && (EVP.timer = setTimeout(() => {
    EVP.id === e && evLoad();
  }, n));
}

function evLocalDetail(e) {
  const t = findEvent(e);
  if (!t) return null;
  const a = econState(t), n = Object.values(ECON.days).flat().filter(s => s.event === t.event && s.ts < t.ts).sort((s, i) => i.ts - s.ts).slice(0, 6);
  return {
    event: t,
    state: a,
    computed: {
      vs_forecast: econDiff(t.actual, t.forecast),
      vs_previous: econDiff(t.actual, t.previous),
      revision: null
    },
    profile: econProfile(t.event),
    history: n.map(s => ({
      ...s,
      surprise: econDiff(s.actual, s.forecast)
    })),
    reaction: {
      available: !1,
      reason: "preview"
    },
    local: !0,
    provenance: {
      economic_data_provider: t.sample ? "bundled schedule (preview)" : "schedule",
      market_data_provider: null
    }
  };
}

function evpHeader(e, t) {
  return `<div class="evp-top"><div><div class="evp-meta"><span class="imp ${e.impact}"><i></i>USD · ${e.impact === "high" ? "High" : "Medium"} impact</span>${e.status === "estimated" ? '<span class="est">est. date</span>' : ""}</div>\n    <h2>${esc(e.event)}</h2><div class="muted">${fdate(etStr(e.ts).slice(0, 10), {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric"
  })} · ${etStr(e.ts).slice(11, 16)} ET <span class="stchip ${t}">${STATE_LABEL[t]}</span></div></div>\n    <button class="btn sm ghost" data-act="ev-close" aria-label="Close">✕</button></div>`;
}

function evValues(e) {
  const t = e.event, a = e.computed || {}, n = e.state, s = (c, l, p = "") => `<div class="evv ${p}"><span>${c}</span><b>${l}</b></div>`, i = t.actual != null && t.actual !== "" ? esc(t.actual) : n === "awaiting" ? "<em>Awaiting release</em>" : "—", o = t.forecast != null && t.forecast !== "" ? esc(t.forecast) : "<em>No consensus available</em>", r = a.vs_forecast;
  return `<div class="evvals">${s("Actual", i, "act")}${s("Forecast", o)}${s("Previous", t.previous != null && t.previous !== "" ? esc(t.previous) : "—")}${s("Surprise", r ? `<span class="sur ${r.direction}">${r.text}</span>` : "—")}</div>\n    ${a.vs_previous || a.revision ? `<div class="evsub">${a.vs_previous ? `<span>vs previous <b>${a.vs_previous.text}</b></span>` : ""}${a.revision ? `<span>Previous revised: reported <b>${esc(a.revision.reported)}</b> → now <b>${esc(a.revision.current)}</b></span>` : ""}</div>` : ""}`;
}

function evFacts(e) {
  const t = e.event, a = e.computed || {};
  if (t.actual == null || t.actual === "") return "";
  const n = (i, o, r) => LANG === "fr" ? o : LANG === "es" ? r : i, s = [ n(`Actual ${esc(t.actual)}.`, `Réel ${esc(t.actual)}.`, `Real ${esc(t.actual)}.`) ];
  if (t.forecast) {
    const i = a.vs_forecast, o = i ? i.direction === "in_line" ? n("in line", "conforme", "en línea") : `${i.text} ${i.direction === "above" ? n("above consensus", "au-dessus du consensus", "por encima del consenso") : n("below consensus", "sous le consensus", "por debajo del consenso")}` : "";
    s.push(`${n("Consensus", "Consensus", "Consenso")} ${esc(t.forecast)}${o ? ` — ${o}` : ""}.`);
  }
  return t.previous && s.push(`${n("Previous", "Précédent", "Anterior")} ${esc(t.previous)}${a.vs_previous ? ` (${a.vs_previous.text} ${n("vs previous", "vs précédent", "vs anterior")})` : ""}.`), 
  a.revision && s.push(n(`Previous was revised from ${esc(a.revision.reported)} to ${esc(a.revision.current)}.`, `Le précédent a été révisé de ${esc(a.revision.reported)} à ${esc(a.revision.current)}.`, `El anterior se revisó de ${esc(a.revision.reported)} a ${esc(a.revision.current)}.`)), 
  `<div class="facts-box"><span class="tagk">Result</span><p data-noi18n>${s.join(" ")}</p></div>`;
}

function evReaction(e) {
  const t = e.reaction, a = e.state;
  if (a === "before" || a === "awaiting" || a === "past_no_data") return "";
  if (!t || !t.available) return `<section class="evs"><h3>NQ reaction</h3><p class="muted">${{
    no_market_data: "Connect market data (Databento) in config.php to record the NQ reaction automatically.",
    too_early: "The first reading appears one minute after the release.",
    no_bars: "No NQ bars were found for this release.",
    preview: "NQ reaction is recorded on your server once market data is connected."
  }[t && t.reason] || "NQ reaction not available."}</p></section>`;
  const n = i => `<span class="${i > 0 ? "pos" : i < 0 ? "neg" : ""}">${i > 0 ? "+" : i < 0 ? "−" : ""}${Math.abs(i).toFixed(2)}</span>`, s = t.classification;
  return `<section class="evs"><h3>NQ reaction ${s ? `<span class="rxl ${s.key}" title="${esc(s.rule)}">${esc(s.label)}</span>` : ""}</h3>\n    <table class="tbl rx"><thead><tr><th>Window</th><th class="num">Price</th><th class="num">Change</th><th class="num">Max up</th><th class="num">Max down</th></tr></thead><tbody>\n    <tr><td>Release</td><td class="num">${(+t.release_price).toFixed(2)}</td><td class="num muted">—</td><td></td><td></td></tr>\n    ${t.offsets.map(i => `<tr><td>+${i.minutes} min</td><td class="num">${(+i.price).toFixed(2)}</td><td class="num">${n(i.change)} pts</td><td class="num">${n(i.max_up)}</td><td class="num">${n(i.max_down)}</td></tr>`).join("")}</tbody></table>\n    ${t.complete ? "" : '<p class="help">Recording… windows fill in as time passes.</p>'}</section>`;
}

const P_ = e => e ? `<p>${esc(e)}</p>` : "";

function evProfile(e) {
  const t = e.profile;
  if (!t) return "";
  const a = (n, s) => s ? `<div class="pr"><span>${n}</span><p>${esc(s)}</p></div>` : "";
  return `<section class="evs"><h3>Overview</h3><p class="lead">${esc(t.what_it_measures)}</p>${P_(t.why_it_matters)}\n    <details class="more"><summary>More about ${esc(t.name)}</summary><div class="prof">${a("Released by", t.releasing_agency)}${a("Frequency", t.release_frequency)}${a("Key components", (t.important_components || []).join(" · "))}\n    ${a("Inflation", t.relationship_to_inflation)}${a("Growth", t.relationship_to_growth)}${a("Labor market", t.relationship_to_labor_market)}${a("Fed policy", t.relationship_to_fed_policy)}${a("What markets focus on", t.typical_market_focus)}</div></details></section>`;
}

function evHistory(e) {
  const t = (e.history || []).filter(a => a.actual != null || a.forecast != null);
  return t.length ? `<section class="evs"><h3>Last ${t.length} releases</h3><table class="tbl"><thead><tr><th>Date</th><th class="num">Actual</th><th class="num">Forecast</th><th class="num">Surprise</th><th>NQ</th></tr></thead><tbody>\n    ${t.map(a => `<tr><td>${fdate(etStr(a.ts).slice(0, 10), {
    month: "short",
    day: "numeric",
    year: "2-digit"
  })}</td><td class="num">${esc(a.actual ?? "—")}</td><td class="num">${esc(a.forecast ?? "—")}</td><td class="num">${a.surprise ? `<span class="sur ${a.surprise.direction}">${a.surprise.text}</span>` : "—"}</td><td>${a.reaction && a.reaction.classification ? `<span class="rxl ${a.reaction.classification.key}">${esc(a.reaction.classification.label)}</span>` : '<span class="faint">—</span>'}</td></tr>`).join("")}</tbody></table>\n    ${t.length < 12 ? '<p class="help">Small sample: patterns across a few releases are not reliable on their own.</p>' : ""}</section>` : "";
}

function evProv(e) {
  const t = e.provenance || {}, a = n => n ? new Date(n).toLocaleString(LOC(), {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }) : "";
  return `<footer class="prov">Economic data: ${t.economic_data_provider === "ai" ? "Sweep AI · Google Search" : esc(t.economic_data_provider || "—")}${t.economic_data_last_updated ? " · updated " + a(t.economic_data_last_updated) : ""} · Market data: ${esc(t.market_data_provider || "not connected")}${t.market_data_timestamp ? " · " + a(t.market_data_timestamp) : ""}</footer>`;
}

function evRender() {
  const e = EVP.d, t = $("#evPanel .evp-in");
  !t || !e || (t.innerHTML = evpHeader(e.event, e.state) + evValues(e) + evFacts(e) + (typeof aiReportBlock == "function" ? aiReportBlock(e) : "") + evReaction(e) + evProfile(e) + evHistory(e) + evProv(e));
}

document.addEventListener("click", e => {
  const t = e.target.closest('[data-act^="ev-"]');
  if (!t) return;
  const a = t.dataset.act;
  a === "ev-open" ? (e.preventDefault(), openEvent(t.dataset.id)) : a === "ev-close" && closeEvent();
});

let ECON_POLL = 0;

function econPoll() {
  clearTimeout(ECON_POLL);
  const e = route().v;
  if (![ "news", "dashboard", "trade" ].includes(e) || S.mode !== "server") return;
  const t = Date.now() / 1e3, a = Object.values(ECON.days).flat().filter(o => Math.abs(o.ts - t) < 86400), n = a.some(o => o.ts <= t + 60 && o.ts > t - 1200 && (o.actual == null || o.actual === "")), s = a.some(o => o.impact === "high" && o.ts > t && o.ts - t < 1800);
  ECON_POLL = setTimeout(async () => {
    const o = todayStr();
    for (const l in ECON.pending) l.includes(o) && delete ECON.pending[l];
    const r = JSON.stringify((ECON.days[o] || []).map(l => [ l.id, l.actual ]));
    await loadEcon(o, o);
    const c = JSON.stringify((ECON.days[o] || []).map(l => [ l.id, l.actual ]));
    r !== c && [ "news", "dashboard" ].includes(route().v) && !isEditing() && render(), 
    econPoll();
  }, n ? 2e4 : s ? 6e4 : 3e5);
}

const WH = {
  el: null,
  input: null,
  vals: [ 0, 0, 0 ],
  t: 0
}, ROW = 36;

function wheelOpen(e) {
  wheelClose(), WH.input = e;
  const t = String(e.value || "").match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
  WH.vals = t ? [ +t[1], +t[2], +(t[3] || 0) ] : nowET().slice(11, 19).split(":").map(Number);
  const a = (i, o) => `<div class="whc" data-k="${i}"><div class="whl">${[ ...Array(o) ].map((r, c) => `<div class="whi" data-v="${c}">${pad(c)}</div>`).join("")}</div></div>`, n = document.createElement("div");
  if (n.className = "wheel", n.setAttribute("role", "dialog"), n.setAttribute("aria-label", "Choose a time"), 
  n.innerHTML = `<div class="wh-top"><span>${esc(e.closest("label")?.querySelector("span")?.textContent || "Time (ET)")}</span><button type="button" class="link" data-wh="now">Now</button></div>\n    <div class="wh-cols"><div class="wh-band"></div>${a(0, 24)}<span class="whsep">:</span>${a(1, 60)}<span class="whsep">:</span>${a(2, 60)}</div>\n    <div class="wh-foot"><button type="button" class="btn primary" data-wh="done">Done</button></div>`, 
  document.body.append(n), WH.el = n, matchMedia("(pointer:coarse)").matches || innerWidth <= 600) {
    n.classList.add("sheet-mode"), swipeDismiss(n, {
      onClose: wheelClose,
      ignore: ".whc"
    });
    const i = document.createElement("div");
    i.className = "wheel-scrim", i.addEventListener("click", wheelClose), document.body.append(i), 
    WH.scrim = i, requestAnimationFrame(() => {
      n.classList.add("open"), i.classList.add("open");
    });
  } else {
    const i = e.getBoundingClientRect(), o = 260;
    n.style.left = Math.min(innerWidth - o - 8, Math.max(8, i.left)) + "px";
    const r = i.bottom + 8 + 270 < innerHeight;
    n.style.top = (r ? i.bottom + 6 : Math.max(8, i.top - 276)) + "px", n.classList.add("open");
  }
  n.querySelectorAll(".whc").forEach(i => {
    const o = +i.dataset.k;
    i.scrollTop = WH.vals[o] * ROW, mark(i, WH.vals[o]), i.addEventListener("scroll", () => {
      clearTimeout(i._t), i._t = setTimeout(() => {
        const r = Math.max(0, Math.min(o ? 59 : 23, Math.round(i.scrollTop / ROW)));
        WH.vals[o] !== r && (WH.vals[o] = r, mark(i, r), wheelApply());
      }, 70);
    }, {
      passive: !0
    }), i.addEventListener("click", r => {
      const c = r.target.closest(".whi");
      c && i.scrollTo({
        top: +c.dataset.v * ROW,
        behavior: "smooth"
      });
    });
  }), n.addEventListener("click", i => {
    const o = i.target.closest("[data-wh]");
    o && (o.dataset.wh === "done" && wheelClose(), o.dataset.wh === "now" && (WH.vals = nowET().slice(11, 19).split(":").map(Number), 
    n.querySelectorAll(".whc").forEach(r => {
      r.scrollTo({
        top: WH.vals[+r.dataset.k] * ROW,
        behavior: "smooth"
      });
    }), wheelApply()));
  });
}

function mark(e, t) {
  e.querySelectorAll(".whi").forEach(a => a.classList.toggle("on", +a.dataset.v === t));
}

function wheelApply() {
  const e = WH.input;
  !e || !document.body.contains(e) || (e.value = WH.vals.map(pad).join(":"), e.dispatchEvent(new Event("input", {
    bubbles: !0
  })));
}

function wheelClose() {
  if (WH.el) {
    const e = WH.el;
    e.classList.remove("open"), setTimeout(() => e.remove(), 200);
  }
  if (WH.scrim) {
    const e = WH.scrim;
    e.classList.remove("open"), setTimeout(() => e.remove(), 200);
  }
  WH.el = WH.scrim = null, WH.input = null;
}

document.addEventListener("click", e => {
  const t = e.target.closest && e.target.closest('input[data-wheel="time"]');
  if (t) {
    WH.input !== t && wheelOpen(t);
    return;
  }
  WH.el && !WH.el.contains(e.target) && !(WH.scrim && WH.scrim.contains(e.target)) && wheelClose();
});

const touchUI = () => matchMedia("(pointer:coarse)").matches || innerWidth <= 600;

document.addEventListener("pointerdown", e => {
  const t = e.target.closest && e.target.closest('input[data-wheel="time"]');
  t && touchUI() && (e.preventDefault(), t.setAttribute("readonly", ""), t.setAttribute("inputmode", "none"));
}, !0), document.addEventListener("focusin", e => {
  const t = e.target.closest && e.target.closest('input[data-wheel="time"]');
  t && touchUI() && (t.setAttribute("readonly", ""), t.setAttribute("inputmode", "none"), 
  t.blur());
}), document.addEventListener("keydown", e => {
  WH.el && (e.key === "Escape" || e.key === "Enter") && (e.stopPropagation(), wheelClose());
}, !0);

function swipeDismiss(e, {scroller: t = () => null, onClose: a, ignore: n = ""} = {}) {
  if (!e || e._sw) return;
  e._sw = !0;
  let s = null, i = 0, o = 0, r = !1;
  const c = () => innerWidth <= 600;
  e.addEventListener("touchstart", p => {
    if (!c() || p.touches.length !== 1 || n && p.target.closest(n)) return;
    const u = p.touches[0], h = e.getBoundingClientRect(), m = t();
    !(u.clientY - h.top < 56) && m && m.scrollTop > 2 || (s = u.clientY, i = 0, o = performance.now(), 
    r = !1);
  }, {
    passive: !0
  }), e.addEventListener("touchmove", p => {
    if (s != null) {
      if (i = p.touches[0].clientY - s, !r) if (i > 8) r = !0, e.style.transition = "none", 
      document.activeElement && document.activeElement.blur && document.activeElement.blur(); else if (i < -6) {
        s = null;
        return;
      } else return;
      p.preventDefault(), e.style.transform = `translateY(${Math.max(0, i * (i > 0 ? 1 : .2))}px)`;
    }
  }, {
    passive: !1
  });
  const l = () => {
    if (s == null || (s = null, !r)) return;
    const p = i / Math.max(1, performance.now() - o);
    e.style.transition = "transform .28s cubic-bezier(.2,.8,.2,1)", i > 110 || p > .55 ? (haptic(), 
    e.style.transform = "translateY(110%)", setTimeout(() => {
      e.style.transition = "", e.style.transform = "", a && a();
    }, 260)) : (e.style.transform = "", setTimeout(() => {
      e.style.transition = "";
    }, 300)), r = !1;
  };
  e.addEventListener("touchend", l), e.addEventListener("touchcancel", l);
}

const haptic = (e = 8) => {
  try {
    navigator.vibrate && navigator.vibrate(e);
  } catch {}
};

let _tObs = null;

function watchTitle() {
  const e = document.getElementById("title"), t = document.getElementById("mtitle");
  !e || !t || (t.textContent = e.textContent, !_tObs && "IntersectionObserver" in window && (_tObs = new IntersectionObserver(([a]) => {
    document.body.classList.toggle("tcollapsed", !a.isIntersecting && a.boundingClientRect.top < 60);
  }, {
    rootMargin: "-56px 0px 0px 0px",
    threshold: 0
  }), _tObs.observe(e)));
}

function placeTabPill() {
  const e = document.getElementById("bottomnav");
  if (!e || getComputedStyle(e).display === "none") return;
  const t = e.querySelector(".bn-pill"), a = e.querySelector("a.on");
  if (!t) return;
  if (!a) {
    t.style.opacity = "0";
    return;
  }
  const n = e.getBoundingClientRect(), s = a.getBoundingClientRect();
  t.style.width = s.width + "px", t.style.transform = `translateX(${s.left - n.left - 7}px)`, 
  t.style.opacity = "1";
}

addEventListener("resize", () => placeTabPill()), new MutationObserver(() => {
  const e = document.getElementById("main");
  if (e && document.body.classList.contains("evp-lock")) {
    const t = e.getBoundingClientRect();
    e.style.transformOrigin = `50% ${Math.round(innerHeight / 2 - t.top)}px`;
  }
}).observe(document.body, {
  attributes: !0,
  attributeFilter: [ "class" ]
}), document.addEventListener("click", e => {
  e.target.closest('.bottomnav a,.bottomnav button,[data-act="tk-save"],[data-act="s2-close"]') && haptic(6);
}, !0);

const SYNC = {
  at: Date.now(),
  busy: !1
};

async function syncNow({manual: e = !1} = {}) {
  if (S.mode !== "server" || SYNC.busy || savingN > 0 || document.activeElement && document.activeElement.matches("input,textarea,select") && !e || TK || document.querySelector(".drawer.open")) return !1;
  SYNC.busy = !0;
  try {
    const t = await fetch("api/data", {
      headers: {
        Accept: "application/json"
      },
      cache: "no-store"
    });
    if (!t.ok) return !1;
    const a = await t.json();
    if (savingN > 0) return !1;
    const n = JSON.stringify(COLS.map(i => (S[i] || []).length)) + JSON.stringify((S.trades || []).map(i => i.updated_at || "").join());
    COLS.forEach(i => S[i] = a[i] || []), a.settings && (S.settings = a.settings);
    const s = JSON.stringify(COLS.map(i => (S[i] || []).length)) + JSON.stringify((S.trades || []).map(i => i.updated_at || "").join());
    return SYNC.at = Date.now(), (n !== s || e) && render(), !0;
  } catch {
    return !1;
  } finally {
    SYNC.busy = !1;
  }
}

document.addEventListener("visibilitychange", () => {
  document.visibilityState === "visible" && Date.now() - SYNC.at > 15e3 && syncNow();
}), setInterval(() => {
  document.visibilityState === "visible" && Date.now() - SYNC.at > 6e4 && syncNow();
}, 15e3), function() {
  let e = null, t = 0, a = null, n = !1;
  const s = () => (a || (a = document.createElement("div"), a.className = "ptr", a.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v5h-5"/></svg>', 
  document.body.append(a)), a);
  addEventListener("touchstart", i => {
    S.mode !== "server" || innerWidth > 860 || scrollY > 0 || document.body.classList.contains("evp-lock") || i.touches.length > 1 || i.target.closest(".evp,.sheet,.sai,.mseg,.jstrip,.mchips,.tchart,input,textarea,select") || (e = i.touches[0].clientY, 
    t = 0, n = !1);
  }, {
    passive: !0
  }), addEventListener("touchmove", i => {
    if (e == null) return;
    if (t = i.touches[0].clientY - e, t <= 0 || scrollY > 0) {
      s().style.opacity = "0";
      return;
    }
    const o = Math.min(1, t / 90), r = s();
    r.style.opacity = String(o), r.style.transform = `translate(-50%,${Math.min(70, t * .55)}px) rotate(${o * 270}deg)`, 
    o >= 1 && !n && (n = !0, haptic(8)), r.classList.toggle("armed", n);
  }, {
    passive: !0
  }), addEventListener("touchend", async () => {
    if (e == null) return;
    e = null;
    const i = s();
    n && (i.classList.add("spin"), await syncNow({
      manual: !0
    }), toast("Up to date")), i.classList.remove("spin", "armed"), i.style.opacity = "0", 
    i.style.transform = "translate(-50%,0)", n = !1;
  }, {
    passive: !0
  });
}(), function() {
  let e = null, t = null, a = null;
  addEventListener("touchstart", n => {
    if (a = n.target.closest && n.target.closest(".cal-wrap"), !a) {
      e = null;
      return;
    }
    e = n.touches[0].clientX, t = n.touches[0].clientY;
  }, {
    passive: !0
  }), addEventListener("touchend", n => {
    if (e == null || !a) return;
    const s = n.changedTouches[0], i = s.clientX - e, o = s.clientY - t;
    if (e = null, Math.abs(i) < 60 || Math.abs(o) > Math.abs(i) * .7) return;
    const r = i < 0 ? a.dataset.next : a.dataset.prev;
    r && (U.calSw = i < 0 ? "l" : "r", haptic(6), location.hash = "#calendar/" + r, 
    setTimeout(() => {
      U.calSw = null;
    }, 400));
  }, {
    passive: !0
  });
}();

(function() {
  "use strict";
  const e = {
    en: {
      title: "Sweep AI",
      close: "Close",
      tab_log: "Log",
      tab_ask: "Ask",
      tab_review: "Review",
      tab_scan: "Scan",
      log_hint: "Describe your trades like you would to a friend. Sweep fills the ticket for you.",
      log_ph: "e.g. 2 NQ longs at the London open, first stopped at -12 ticks, second +30 ticks at target. Sweep of Asia low.",
      read_note: "Fill my trades",
      or: "or",
      import_shot: "Import a screenshot",
      import_hint: "Fills, trade history or prop firm dashboard.",
      working: "Working…",
      reading_img: "Reading your screenshot…",
      drafts_title: d => `${d} trade${d > 1 ? "s" : ""} found — check and save`,
      no_trades_found: "No trades found. Add more details and try again.",
      account: "Account",
      date: "Date",
      side: "Side",
      long: "Long",
      short: "Short",
      instrument: "Instrument",
      contracts: "Contracts",
      entry: "Entry",
      exit: "Exit",
      entry_time: "Entry time",
      exit_time: "Exit time",
      pnl: "P&L ($)",
      setup: "Setup",
      notes: "Notes",
      fees: "Fees ($)",
      remove: "Remove",
      save_n: d => `Save ${d} trade${d > 1 ? "s" : ""}`,
      saved_n: d => `${d} saved`,
      missing: "Missing fields are highlighted.",
      ask_hint: "Ask anything about your own trading. Sweep computes the answer from your journal.",
      ask_ph: "e.g. What is my win rate on NQ after 10:30?",
      ask_btn: "Ask",
      ask_examples: [ "Which setup makes me the most money?", "How do I do on Fridays?", "Win rate in the London session this month?" ],
      trades_n: d => `${d} trade${d === 1 ? "" : "s"}`,
      week: "Week",
      day: "Day",
      generate_review: "Generate my review",
      regenerate: "Refresh",
      debrief_btn: "Debrief my day",
      no_trades_week: "No trades this week yet.",
      no_data_day: "No trades or journal for this day.",
      vs_prev: "vs last week",
      net: "Net",
      win_rate: "Win rate",
      trades: "Trades",
      pf: "Profit factor",
      went_well: "What went well",
      to_fix: "What to fix",
      plan_exec: "Plan vs execution",
      focus: "Focus next week",
      rule: "Rule for next week",
      score: "Process score",
      copy_recap: "Copy recap for Discord",
      copied: "Copied",
      verdict_followed: "Plan followed",
      verdict_partly: "Plan partly followed",
      verdict_broke: "Plan broken",
      verdict_no_plan: "No plan written",
      lesson: "Lesson",
      tomorrow: "Tomorrow",
      scan_hint: "Snap a receipt, invoice or payout email. Sweep files it as an expense or a payout.",
      scan_btn: "Choose an image",
      items_title: d => `${d} item${d > 1 ? "s" : ""} found — check and save`,
      no_items: "Nothing found in this image.",
      expense: "Expense",
      payout: "Payout",
      amount: "Amount ($)",
      category: "Category",
      status: "Status",
      firm: "Prop firm",
      none: "—",
      cat_evaluation: "Evaluation",
      cat_activation: "Activation",
      cat_reset: "Reset",
      cat_data: "Data fees",
      cat_platform: "Platform",
      cat_other: "Other",
      st_requested: "Requested",
      st_approved: "Approved",
      st_paid: "Paid",
      st_rejected: "Rejected",
      save_items: d => `Save ${d} item${d > 1 ? "s" : ""}`,
      fb_title: "Trade feedback",
      fb_good_process: "Good process",
      fb_mixed: "Mixed process",
      fb_poor_process: "Process to fix",
      fb_well: "Went well",
      fb_improve: "To improve",
      fb_next: "Next time",
      fb_setup: "This setup for you",
      tags_title: "Suggested labels",
      apply: "Apply",
      applied: "Applied",
      new_setup: "New setup",
      left: d => `${d} AI action${d === 1 ? "" : "s"} left today`,
      cached: "From cache · free",
      err_disabled: "AI is not set up yet.",
      err_upgrade_required: "This needs a higher plan. See the options that just opened.",
      err_quota: "You've used this period's AI allowance. It resets soon.",
      err_daily_limit: "You reached today's AI limit. It resets at midnight (New York).",
      err_budget: "AI is paused for today. Try again tomorrow.",
      err_throttle: "One moment… try again in a few seconds.",
      err_network: "AI is unreachable right now. Try again.",
      err_provider: "The AI service had a problem. Try again.",
      err_provider_busy: "The AI service is busy. Try again in a minute.",
      err_bad_output: "The AI answer was unreadable. Try again.",
      err_bad_input: "Write a bit more (or a bit less) and try again.",
      err_image: "Use a PNG, JPEG or WebP image.",
      err_image_too_big: "This image is too large.",
      err_not_found: "Not found.",
      err_server: "Something went wrong.",
      err_save: "Could not save. Try again.",
      wd: [ "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun" ],
      recap: d => `📊 Sweep weekly recap · ${d.range}\nNet ${d.net} · ${d.trades} · ${d.wr} win rate${d.pf ? " · PF " + d.pf : ""}\n${d.best ? "Best day: " + d.best + `\n` : ""}${d.focus ? "Focus next week: " + d.focus + `\n` : ""}Sweep down. Jump up.`
    },
    fr: {
      title: "Sweep IA",
      close: "Fermer",
      tab_log: "Saisir",
      tab_ask: "Demander",
      tab_review: "Bilan",
      tab_scan: "Scanner",
      log_hint: "Décris tes trades comme tu le ferais à un ami. Sweep remplit le ticket pour toi.",
      log_ph: "ex. 2 longs NQ à l'ouverture de Londres, le premier stoppé à -12 ticks, le deuxième +30 ticks au target. Sweep du low d'Asie.",
      read_note: "Remplir mes trades",
      or: "ou",
      import_shot: "Importer une capture",
      import_hint: "Exécutions, historique ou tableau de bord de ta prop firm.",
      working: "Un instant…",
      reading_img: "Lecture de ta capture…",
      drafts_title: d => `${d} trade${d > 1 ? "s" : ""} trouvé${d > 1 ? "s" : ""} — vérifie et enregistre`,
      no_trades_found: "Aucun trade trouvé. Ajoute des détails et réessaie.",
      account: "Compte",
      date: "Date",
      side: "Sens",
      long: "Long",
      short: "Short",
      instrument: "Instrument",
      contracts: "Contrats",
      entry: "Entrée",
      exit: "Sortie",
      entry_time: "Heure d'entrée",
      exit_time: "Heure de sortie",
      pnl: "P&L ($)",
      setup: "Setup",
      notes: "Notes",
      fees: "Frais ($)",
      remove: "Retirer",
      save_n: d => `Enregistrer ${d} trade${d > 1 ? "s" : ""}`,
      saved_n: d => `${d} enregistré${d > 1 ? "s" : ""}`,
      missing: "Les champs manquants sont surlignés.",
      ask_hint: "Pose n'importe quelle question sur ton trading. Sweep calcule la réponse à partir de ton journal.",
      ask_ph: "ex. Quel est mon taux de réussite sur NQ après 10 h 30?",
      ask_btn: "Demander",
      ask_examples: [ "Quel setup me rapporte le plus?", "Comment je performe le vendredi?", "Mon taux de réussite en session de Londres ce mois-ci?" ],
      trades_n: d => `${d} trade${d > 1 ? "s" : ""}`,
      week: "Semaine",
      day: "Jour",
      generate_review: "Générer mon bilan",
      regenerate: "Actualiser",
      debrief_btn: "Débriefer ma journée",
      no_trades_week: "Aucun trade cette semaine pour l'instant.",
      no_data_day: "Aucun trade ni journal pour ce jour.",
      vs_prev: "vs semaine passée",
      net: "Net",
      win_rate: "Réussite",
      trades: "Trades",
      pf: "Profit factor",
      went_well: "Ce qui a bien été",
      to_fix: "À corriger",
      plan_exec: "Plan vs exécution",
      focus: "Focus de la semaine prochaine",
      rule: "Règle pour la semaine prochaine",
      score: "Score de process",
      copy_recap: "Copier le résumé pour Discord",
      copied: "Copié",
      verdict_followed: "Plan respecté",
      verdict_partly: "Plan en partie respecté",
      verdict_broke: "Plan non respecté",
      verdict_no_plan: "Aucun plan écrit",
      lesson: "Leçon",
      tomorrow: "Demain",
      scan_hint: "Prends en photo un reçu, une facture ou un courriel de payout. Sweep le classe en dépense ou en payout.",
      scan_btn: "Choisir une image",
      items_title: d => `${d} élément${d > 1 ? "s" : ""} trouvé${d > 1 ? "s" : ""} — vérifie et enregistre`,
      no_items: "Rien trouvé dans cette image.",
      expense: "Dépense",
      payout: "Payout",
      amount: "Montant ($)",
      category: "Catégorie",
      status: "Statut",
      firm: "Prop firm",
      none: "—",
      cat_evaluation: "Évaluation",
      cat_activation: "Activation",
      cat_reset: "Reset",
      cat_data: "Frais de données",
      cat_platform: "Plateforme",
      cat_other: "Autre",
      st_requested: "Demandé",
      st_approved: "Approuvé",
      st_paid: "Payé",
      st_rejected: "Refusé",
      save_items: d => `Enregistrer ${d} élément${d > 1 ? "s" : ""}`,
      fb_title: "Retour sur le trade",
      fb_good_process: "Bon process",
      fb_mixed: "Process mitigé",
      fb_poor_process: "Process à corriger",
      fb_well: "Ce qui a bien été",
      fb_improve: "À améliorer",
      fb_next: "La prochaine fois",
      fb_setup: "Ce setup pour toi",
      tags_title: "Étiquettes suggérées",
      apply: "Appliquer",
      applied: "Appliqué",
      new_setup: "Nouveau setup",
      left: d => `${d} action${d > 1 ? "s" : ""} IA restante${d > 1 ? "s" : ""} aujourd'hui`,
      cached: "Depuis le cache · gratuit",
      err_disabled: "L'IA n'est pas encore configurée.",
      err_upgrade_required: "Cette fonction demande un abonnement supérieur. Regarde les options qui viennent de s'ouvrir.",
      err_quota: "Tu as utilisé ta limite IA pour cette période. Elle revient bientôt.",
      err_daily_limit: "Tu as atteint la limite IA du jour. Elle se réinitialise à minuit (New York).",
      err_budget: "L'IA est en pause pour aujourd'hui. Réessaie demain.",
      err_throttle: "Un instant… réessaie dans quelques secondes.",
      err_network: "L'IA est injoignable pour le moment. Réessaie.",
      err_provider: "Le service IA a eu un problème. Réessaie.",
      err_provider_busy: "Le service IA est occupé. Réessaie dans une minute.",
      err_bad_output: "La réponse de l'IA était illisible. Réessaie.",
      err_bad_input: "Écris un peu plus (ou un peu moins) et réessaie.",
      err_image: "Utilise une image PNG, JPEG ou WebP.",
      err_image_too_big: "Cette image est trop lourde.",
      err_not_found: "Introuvable.",
      err_server: "Une erreur est survenue.",
      err_save: "Impossible d'enregistrer. Réessaie.",
      wd: [ "lun", "mar", "mer", "jeu", "ven", "sam", "dim" ],
      recap: d => `📊 Bilan Sweep de la semaine · ${d.range}\nNet ${d.net} · ${d.trades} · ${d.wr} de réussite${d.pf ? " · PF " + d.pf : ""}\n${d.best ? "Meilleure journée : " + d.best + `\n` : ""}${d.focus ? "Focus la semaine prochaine : " + d.focus + `\n` : ""}Sweep down. Jump up.`
    },
    es: {
      title: "Sweep IA",
      close: "Cerrar",
      tab_log: "Registrar",
      tab_ask: "Preguntar",
      tab_review: "Resumen",
      tab_scan: "Escanear",
      log_hint: "Describe tus trades como se lo contarías a un amigo. Sweep llena el ticket por ti.",
      log_ph: "p. ej. 2 largos en NQ en la apertura de Londres, el primero con stop a -12 ticks, el segundo +30 ticks en el objetivo.",
      read_note: "Llenar mis trades",
      or: "o",
      import_shot: "Importar una captura",
      import_hint: "Ejecuciones, historial o panel de tu prop firm.",
      working: "Un momento…",
      reading_img: "Leyendo tu captura…",
      drafts_title: d => `${d} trade${d > 1 ? "s" : ""} encontrado${d > 1 ? "s" : ""} — revisa y guarda`,
      no_trades_found: "No se encontraron trades. Agrega detalles e inténtalo de nuevo.",
      account: "Cuenta",
      date: "Fecha",
      side: "Lado",
      long: "Largo",
      short: "Corto",
      instrument: "Instrumento",
      contracts: "Contratos",
      entry: "Entrada",
      exit: "Salida",
      entry_time: "Hora de entrada",
      exit_time: "Hora de salida",
      pnl: "P&L ($)",
      setup: "Setup",
      notes: "Notas",
      fees: "Comisiones ($)",
      remove: "Quitar",
      save_n: d => `Guardar ${d} trade${d > 1 ? "s" : ""}`,
      saved_n: d => `${d} guardado${d > 1 ? "s" : ""}`,
      missing: "Los campos faltantes están resaltados.",
      ask_hint: "Pregunta lo que quieras sobre tu trading. Sweep calcula la respuesta con tu diario.",
      ask_ph: "p. ej. ¿Cuál es mi tasa de acierto en NQ después de las 10:30?",
      ask_btn: "Preguntar",
      ask_examples: [ "¿Qué setup me da más dinero?", "¿Cómo me va los viernes?", "¿Tasa de acierto en la sesión de Londres este mes?" ],
      trades_n: d => `${d} trade${d === 1 ? "" : "s"}`,
      week: "Semana",
      day: "Día",
      generate_review: "Generar mi resumen",
      regenerate: "Actualizar",
      debrief_btn: "Analizar mi día",
      no_trades_week: "Aún no hay trades esta semana.",
      no_data_day: "No hay trades ni diario para este día.",
      vs_prev: "vs semana pasada",
      net: "Neto",
      win_rate: "Acierto",
      trades: "Trades",
      pf: "Profit factor",
      went_well: "Lo que salió bien",
      to_fix: "Lo que corregir",
      plan_exec: "Plan vs ejecución",
      focus: "Enfoque de la próxima semana",
      rule: "Regla para la próxima semana",
      score: "Puntaje de proceso",
      copy_recap: "Copiar resumen para Discord",
      copied: "Copiado",
      verdict_followed: "Plan respetado",
      verdict_partly: "Plan respetado en parte",
      verdict_broke: "Plan no respetado",
      verdict_no_plan: "Sin plan escrito",
      lesson: "Lección",
      tomorrow: "Mañana",
      scan_hint: "Toma una foto de un recibo, factura o correo de payout. Sweep lo registra como gasto o payout.",
      scan_btn: "Elegir una imagen",
      items_title: d => `${d} elemento${d > 1 ? "s" : ""} encontrado${d > 1 ? "s" : ""} — revisa y guarda`,
      no_items: "No se encontró nada en esta imagen.",
      expense: "Gasto",
      payout: "Payout",
      amount: "Monto ($)",
      category: "Categoría",
      status: "Estado",
      firm: "Prop firm",
      none: "—",
      cat_evaluation: "Evaluación",
      cat_activation: "Activación",
      cat_reset: "Reset",
      cat_data: "Datos",
      cat_platform: "Plataforma",
      cat_other: "Otro",
      st_requested: "Solicitado",
      st_approved: "Aprobado",
      st_paid: "Pagado",
      st_rejected: "Rechazado",
      save_items: d => `Guardar ${d} elemento${d > 1 ? "s" : ""}`,
      fb_title: "Comentarios del trade",
      fb_good_process: "Buen proceso",
      fb_mixed: "Proceso mixto",
      fb_poor_process: "Proceso a corregir",
      fb_well: "Salió bien",
      fb_improve: "A mejorar",
      fb_next: "La próxima vez",
      fb_setup: "Este setup para ti",
      tags_title: "Etiquetas sugeridas",
      apply: "Aplicar",
      applied: "Aplicado",
      new_setup: "Nuevo setup",
      left: d => `${d} acci${d === 1 ? "ón" : "ones"} de IA restante${d === 1 ? "" : "s"} hoy`,
      cached: "Desde caché · gratis",
      err_disabled: "La IA aún no está configurada.",
      err_upgrade_required: "Esto requiere un plan superior. Mira las opciones que se acaban de abrir.",
      err_quota: "Usaste tu límite de IA de este periodo. Vuelve pronto.",
      err_daily_limit: "Llegaste al límite de IA de hoy. Se reinicia a medianoche (Nueva York).",
      err_budget: "La IA está en pausa por hoy. Inténtalo mañana.",
      err_throttle: "Un momento… inténtalo en unos segundos.",
      err_network: "La IA no está disponible ahora. Inténtalo de nuevo.",
      err_provider: "El servicio de IA tuvo un problema. Inténtalo de nuevo.",
      err_provider_busy: "El servicio de IA está ocupado. Inténtalo en un minuto.",
      err_bad_output: "La respuesta de la IA no se pudo leer. Inténtalo de nuevo.",
      err_bad_input: "Escribe un poco más (o un poco menos) e inténtalo de nuevo.",
      err_image: "Usa una imagen PNG, JPEG o WebP.",
      err_image_too_big: "La imagen es demasiado grande.",
      err_not_found: "No encontrado.",
      err_server: "Algo salió mal.",
      err_save: "No se pudo guardar. Inténtalo de nuevo.",
      wd: [ "lun", "mar", "mié", "jue", "vie", "sáb", "dom" ],
      recap: d => `📊 Resumen semanal de Sweep · ${d.range}\nNeto ${d.net} · ${d.trades} · ${d.wr} de acierto${d.pf ? " · PF " + d.pf : ""}\n${d.best ? "Mejor día: " + d.best + `\n` : ""}${d.focus ? "Enfoque la próxima semana: " + d.focus + `\n` : ""}Sweep down. Jump up.`
    }
  }, t = {
    NQ: [ .25, 20 ],
    MNQ: [ .25, 2 ],
    ES: [ .25, 50 ],
    MES: [ .25, 5 ],
    YM: [ 1, 5 ],
    MYM: [ 1, .5 ],
    RTY: [ .1, 50 ],
    M2K: [ .1, 5 ],
    CL: [ .01, 1e3 ],
    MCL: [ .01, 100 ],
    GC: [ .1, 100 ],
    MGC: [ .1, 10 ]
  }, a = [ "evaluation", "activation", "reset", "data", "platform", "other" ], n = [ "requested", "approved", "paid", "rejected" ], s = {
    o: null,
    lang: "en",
    usage: null,
    root: null,
    tab: "log",
    busy: !1,
    log: {
      text: "",
      res: null,
      saved: 0
    },
    ask: {
      q: "",
      res: null
    },
    scan: {
      res: null
    },
    rev: {
      mode: "week",
      weekStart: null,
      date: null,
      week: null,
      day: null
    },
    trade: null
  }, i = (d, f) => {
    const _ = (e[s.lang] || e.en)[d] ?? e.en[d] ?? d;
    return typeof _ == "function" ? _(f) : _;
  }, o = d => String(d ?? "").replace(/[&<>"']/g, f => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[f])), r = () => ({
    en: "en-US",
    fr: "fr-CA",
    es: "es"
  }[s.lang] || "en-US"), c = (d, f = !0, y = !1) => {
    if (d == null || isNaN(d)) return "—";
    const _ = d / 100, I = Math.abs(_), V = y || I >= 1e3 ? 0 : 2;
    let K;
    try {
      K = new Intl.NumberFormat(r(), {
        style: "currency",
        currency: "USD",
        currencyDisplay: "narrowSymbol",
        minimumFractionDigits: V,
        maximumFractionDigits: V
      }).format(I);
    } catch {
      K = "$" + I.toFixed(V);
    }
    return (_ < 0 ? "−" : f && _ > 0 ? "+" : "") + K;
  }, l = d => d == null ? "—" : new Intl.NumberFormat(r(), {
    style: "percent",
    maximumFractionDigits: 0
  }).format(d), p = d => d > 0 ? "sai-pos" : d < 0 ? "sai-neg" : "", u = (d, f) => d == null ? "—" : f === "money" ? c(d) : f === "pct" ? l(d) : f === "min" ? Math.round(d) + " min" : f === "r" ? (d > 0 ? "+" : "") + d.toFixed(2) + "R" : f === "ratio" ? Number(d).toFixed(2) : new Intl.NumberFormat(r()).format(d), h = () => new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date), m = (d, f) => {
    const y = new Date(d + "T12:00:00Z");
    return y.setUTCDate(y.getUTCDate() + f), y.toISOString().slice(0, 10);
  }, v = d => {
    const y = (new Date(d + "T12:00:00Z").getUTCDay() + 6) % 7;
    return m(d, -y);
  }, b = d => new Intl.DateTimeFormat(r(), {
    month: "short",
    day: "numeric",
    timeZone: "UTC"
  }).format(new Date(d + "T12:00:00Z")), E = d => d + "-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8), R = (d, f) => d === "weekday" && i("wd")[Number(f) - 1] || f;
  function L() {
    const d = [ s.o.lang, document.documentElement.getAttribute("lang"), navigator.language ];
    for (const f of d) {
      const y = String(f || "").slice(0, 2).toLowerCase();
      if (e[y]) return y;
    }
    return "en";
  }
  function x(d, f) {
    if (s.o.url) return s.o.url(d, f);
    const y = s.o.base ?? "index.php", _ = new URLSearchParams({
      r: d,
      ...f || {}
    });
    return y + "?" + _.toString();
  }
  async function C(d, f, y) {
    let _;
    try {
      _ = await fetch(x(d), {
        method: y || (f ? "POST" : "GET"),
        credentials: "same-origin",
        headers: f ? {
          "Content-Type": "application/json",
          "X-Requested-With": "fetch"
        } : {
          "X-Requested-With": "fetch"
        },
        body: f ? JSON.stringify({
          lang: s.lang,
          ...f
        }) : void 0
      });
    } catch {
      throw {
        code: "network"
      };
    }
    let I = null;
    try {
      I = await _.json();
    } catch {}
    if (_.status === 402 && window.SweepBilling) throw SweepBilling.handleApiError(I || {}), 
    {
      code: I && I.code === "quota" ? "quota" : "upgrade_required",
      status: 402
    };
    if (!_.ok) throw {
      code: I && I.code || (_.status === 401, "server"),
      status: _.status
    };
    return I && I.usage && (s.usage = I.usage, oe()), I || {};
  }
  const g = {
    status: () => C("api/ai/status"),
    health: () => C("api/ai/health", {}),
    parseTrades: d => C("api/ai/parse-trades", {
      text: d
    }),
    importImage: (d, f) => C("api/ai/import", {
      image: d.data,
      mime: d.mime,
      mode: f || "trades"
    }),
    ask: d => C("api/ai/ask", {
      question: d
    }),
    weeklyReview: d => C("api/ai/weekly-review", {
      week_start: d
    }),
    dayDebrief: d => C("api/ai/day-debrief", {
      date: d
    }),
    tradeFeedback: (d, f) => C("api/ai/trade-feedback", {
      trade_id: d,
      ...f ? {
        image: f.data,
        mime: f.mime
      } : {}
    }),
    suggestTags: (d, f) => C("api/ai/suggest-tags", {
      trade_id: d,
      ...f ? {
        image: f.data,
        mime: f.mime
      } : {}
    })
  };
  async function P(d, f) {
    if (s.o.saveDoc) return s.o.saveDoc(d, f);
    if (!(await fetch(x("api/docs/" + d + "/" + encodeURIComponent(f.id)), {
      method: "PUT",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(f)
    })).ok) throw {
      code: "save"
    };
  }
  function O(d, f) {
    if (s.o.onDataChanged) return s.o.onDataChanged(d, f);
    document.dispatchEvent(new CustomEvent("sweep:ai-saved", {
      detail: {
        collection: d,
        docs: f
      }
    }));
  }
  async function H(d, f = 1600) {
    try {
      const y = await createImageBitmap(d), _ = Math.min(1, f / Math.max(y.width, y.height)), I = document.createElement("canvas");
      I.width = Math.round(y.width * _), I.height = Math.round(y.height * _);
      const V = I.getContext("2d");
      V.fillStyle = "#fff", V.fillRect(0, 0, I.width, I.height), V.drawImage(y, 0, 0, I.width, I.height);
      const K = await new Promise(le => I.toBlob(le, "image/jpeg", .86));
      return {
        data: await J(K),
        mime: "image/jpeg"
      };
    } catch {
      if (/^image\/(png|jpeg|webp)$/.test(d.type || "")) return {
        data: await J(d),
        mime: d.type
      };
      throw {
        code: "image"
      };
    }
  }
  const J = d => new Promise((f, y) => {
    const _ = new FileReader;
    _.onload = () => f(String(_.result).split(",")[1]), _.onerror = () => y({
      code: "image"
    }), _.readAsDataURL(d);
  });
  async function q(d) {
    const f = await fetch(d, {
      credentials: "same-origin"
    });
    if (!f.ok) throw {
      code: "image"
    };
    return H(await f.blob());
  }
  function z() {
    if (s.root) return;
    const d = document.createElement("div");
    if (d.className = "sai", d.hidden = !0, d.innerHTML = `<div class="sai-backdrop" data-act="close"></div>\n      <section class="sai-sheet" role="dialog" aria-modal="true" aria-labelledby="sai-title">\n        <header class="sai-head" data-drag><div class="sai-grabber"></div>\n          <div class="sai-head-row"><h2 id="sai-title"><span class="sai-spark" aria-hidden="true">✦</span> <span data-t="title"></span></h2>\n          <button class="sai-x" data-act="close" aria-label="Close">✕</button></div>\n          <nav class="sai-tabs" role="tablist"></nav></header>\n        <div class="sai-body"></div>\n        <footer class="sai-foot"></footer>\n      </section>`, 
    document.body.appendChild(d), s.root = d, d.addEventListener("click", $e), d.addEventListener("input", ve), 
    d.addEventListener("change", Ae), d.addEventListener("keydown", f => {
      if (f.key === "Escape" && me(), (f.metaKey || f.ctrlKey) && f.key === "Enter") {
        const y = d.querySelector("[data-primary]");
        y && !y.disabled && y.click();
      }
    }), Y(d.querySelector(".sai-sheet"), d.querySelector("[data-drag]")), s.o.fab !== !1) {
      const f = document.createElement("button");
      f.className = "sai-fab", f.type = "button", f.setAttribute("aria-label", i("title")), 
      f.textContent = "✦", f.addEventListener("click", () => Q()), document.body.appendChild(f);
    }
  }
  function Y(d, f) {
    let y = null, _ = 0;
    f.addEventListener("pointerdown", V => {
      V.target.closest("button,nav") || (y = V.clientY, _ = 0, d.style.transition = "none", 
      f.setPointerCapture(V.pointerId));
    }), f.addEventListener("pointermove", V => {
      y != null && (_ = Math.max(0, V.clientY - y), d.style.transform = `translateY(${_}px)`);
    });
    const I = () => {
      y != null && (y = null, d.style.transition = "", d.style.transform = "", _ > 110 && me());
    };
    f.addEventListener("pointerup", I), f.addEventListener("pointercancel", I);
  }
  function Q(d) {
    z(), d && (s.tab = d), s.trade = d === "trade" ? s.trade : null, s.root.hidden = !1, 
    requestAnimationFrame(() => s.root.classList.add("sai-open")), document.documentElement.classList.add("sai-locked"), 
    ae(), s.usage || g.status().then(f => {
      s.usage = f.usage, s.enabled = f.enabled, oe();
    }).catch(() => {}), setTimeout(() => {
      const f = s.root.querySelector("textarea,input[type=text]");
      f && matchMedia("(pointer:fine)").matches && f.focus();
    }, 250);
  }
  function me() {
    s.root && (s.root.classList.remove("sai-open"), document.documentElement.classList.remove("sai-locked"), 
    setTimeout(() => {
      s.root.classList.contains("sai-open") || (s.root.hidden = !0);
    }, 260));
  }
  function oe() {
    if (!s.root) return;
    const d = s.root.querySelector(".sai-foot");
    d && (d.textContent = s.usage ? i("left", s.usage.remaining) : "");
  }
  function ae() {
    s.root.querySelector('[data-t="title"]').textContent = i("title");
    const d = [ "log", "ask", "review", "scan" ], f = s.root.querySelector(".sai-tabs");
    f.hidden = s.tab === "trade", f.innerHTML = d.map(_ => `<button role="tab" aria-selected="${s.tab === _}" data-act="tab" data-tab="${_}">${o(i("tab_" + _))}</button>`).join("");
    const y = s.root.querySelector(".sai-body");
    y.innerHTML = ({
      log: pe,
      ask: B,
      review: Z,
      scan: de,
      trade: ke
    }[s.tab] || pe)(), oe();
  }
  const we = d => `<div class="sai-loading"><span class="sai-dots"><i></i><i></i><i></i></span>${o(d || i("working"))}</div>`, te = d => `<div class="sai-err" role="alert">${o(i("err_" + (d || "server")))}</div>`, re = d => d && d.cached ? `<div class="sai-cached">${o(i("cached"))}</div>` : "";
  async function X(d, f) {
    if (!s.busy) {
      s.busy = !0, s.err = null, ae();
      try {
        await d();
      } catch (y) {
        s.err = y && y.code || "server";
      }
      s.busy = !1, ae(), f && f();
    }
  }
  function pe() {
    const d = s.log;
    let f = `<p class="sai-hint">${o(i("log_hint"))}</p>\n      <textarea class="sai-input" rows="4" data-bind="log.text" placeholder="${o(i("log_ph"))}" maxlength="2000">${o(d.text)}</textarea>\n      <div class="sai-row"><button class="sai-btn sai-primary" data-act="parse" data-primary ${s.busy || !d.text.trim() ? "disabled" : ""}>${o(i("read_note"))}</button>\n      <span class="sai-or">${o(i("or"))}</span>\n      <label class="sai-btn sai-file ${s.busy ? "is-disabled" : ""}">${o(i("import_shot"))}<input type="file" accept="image/*" data-file="trades" ${s.busy ? "disabled" : ""}></label></div>\n      <p class="sai-sub">${o(i("import_hint"))}</p>`;
    return s.busy && (f += we(d.reading ? i("reading_img") : i("working"))), s.err && (f += te(s.err)), 
    d.res && !s.busy && (f += ue(d.res)), d.saved && (f += `<div class="sai-ok">✓ ${o(i("saved_n", d.saved))}</div>`), 
    f;
  }
  function ue(d) {
    const f = d.drafts.filter(V => !V.removed);
    if (!f.length) return `<div class="sai-empty">${o(i("no_trades_found"))}</div>` + ne(d.warnings);
    const y = V => `<option value="">${o(i("none"))}</option>` + d.accounts.map(K => `<option value="${o(K.id)}" ${K.id === V ? "selected" : ""}>${o(K.name)}${K.firm ? " · " + o(K.firm) : ""}</option>`).join(""), _ = `<datalist id="sai-setups">${(d.setups || []).map(V => `<option value="${o(V)}">`).join("")}</datalist>`, I = d.drafts.map((V, K) => {
      if (V.removed) return "";
      const le = V.trade, xe = ce => V.missing.includes(ce) && k(le, ce) ? " sai-miss" : "";
      return `<article class="sai-card" data-i="${K}">\n        <div class="sai-card-head"><div class="sai-seg">${[ "long", "short" ].map(ce => `<button class="${le.direction === ce ? "on" : ""}${xe("direction")}" data-act="dir" data-i="${K}" data-v="${ce}">${o(i(ce))}</button>`).join("")}</div>\n          <strong class="${p(le.pnl_c)}">${le.pnl_c == null ? "—" : c(le.pnl_c)}</strong>\n          <button class="sai-link" data-act="rm" data-i="${K}">${o(i("remove"))}</button></div>\n        <div class="sai-grid">\n          ${M(i("account"), `<select data-f="account_id" data-i="${K}" class="${xe("account")}">${y(le.account_id)}</select>`, 2)}\n          ${M(i("date"), `<input type="date" data-f="date" data-i="${K}" value="${o(le.date)}">`)}\n          ${M(i("instrument"), `<select data-f="instrument" data-i="${K}">${Object.keys(t).map(ce => `<option ${ce === le.instrument ? "selected" : ""}>${ce}</option>`).join("")}</select>`)}\n          ${M(i("contracts"), `<input inputmode="numeric" data-f="contracts" data-i="${K}" value="${o(le.contracts)}">`)}\n          ${M(i("entry"), `<input inputmode="decimal" data-f="entry" data-i="${K}" value="${o(le.entry ?? "")}">`)}\n          ${M(i("exit"), `<input inputmode="decimal" data-f="exit" data-i="${K}" value="${o(le.exit ?? "")}">`)}\n          ${M(i("entry_time"), `<input type="time" data-f="entry_time" data-i="${K}" value="${o(le.entry_time)}" class="${xe("entry_time")}">`)}\n          ${M(i("exit_time"), `<input type="time" data-f="exit_time" data-i="${K}" value="${o(le.exit_time)}" class="${xe("exit_time")}">`)}\n          ${M(i("pnl"), `<input inputmode="decimal" data-f="pnl" data-i="${K}" value="${le.pnl_c == null ? "" : (le.pnl_c / 100).toFixed(2)}" class="${xe("pnl")}">`)}\n          ${M(i("fees"), `<input inputmode="decimal" data-f="fees" data-i="${K}" value="${le.fees_c ? (le.fees_c / 100).toFixed(2) : ""}">`)}\n          ${M(i("setup"), `<input list="sai-setups" data-f="setup" data-i="${K}" value="${o(le.setup)}">`, 2)}\n          ${M(i("notes"), `<input data-f="notes" data-i="${K}" value="${o(le.notes)}">`, 2)}\n        </div></article>`;
    }).join("");
    return `<h3 class="sai-h3">${o(i("drafts_title", f.length))}</h3>${ne(d.warnings)}${_}${I}\n      <p class="sai-sub">${o(i("missing"))}</p>\n      <button class="sai-btn sai-primary sai-block" data-act="save-trades" data-primary>${o(i("save_n", f.length))}</button>`;
  }
  const M = (d, f, y) => `<label class="sai-f${y ? " sai-span" + y : ""}"><span>${o(d)}</span>${f}</label>`, ne = d => d && d.length ? `<ul class="sai-warn">${d.map(f => `<li>${o(f)}</li>`).join("")}</ul>` : "", k = (d, f) => ({
    direction: !d.direction,
    pnl: d.pnl_c == null,
    entry_time: !d.entry_time,
    exit_time: !d.exit_time,
    account: !d.account_id
  }[f]);
  function A(d) {
    if (d.entry != null && d.exit != null && d.direction && !d._pnlTyped) {
      const [, f] = t[d.instrument] || t.NQ;
      d.pnl_c = Math.round((d.exit - d.entry) * (d.direction === "long" ? 1 : -1) * f * Math.max(1, d.contracts) * 100), 
      d.pnl_manual = !1;
    }
  }
  const j = d => {
    if (d = String(d ?? "").replace(/[,\s$]/g, ""), d === "" || d === "-") return null;
    const f = Number(d);
    return isFinite(f) ? f : null;
  };
  async function N() {
    const f = s.log.res.drafts.filter(y => !y.removed);
    for (const y of f) {
      const _ = y.trade;
      if (!_.direction || _.pnl_c == null || !_.account_id || !_.entry_time || !_.exit_time) {
        y.missing = [ "direction", "pnl", "account", "entry_time", "exit_time" ], s.err = null, 
        ae(), _e(i("missing"));
        return;
      }
    }
    await X(async () => {
      const y = [];
      for (const _ of f) {
        const I = {
          ..._.trade
        };
        delete I._pnlTyped, s.o.sessionFor && I.entry_time && (I.session = s.o.sessionFor(I.entry_time) || ""), 
        await P("trades", I).catch(() => {
          throw {
            code: "save"
          };
        }), y.push(I);
      }
      s.log = {
        text: "",
        res: null,
        saved: y.length
      }, O("trades", y);
    });
  }
  function B() {
    const d = s.ask;
    let f = `<p class="sai-hint">${o(i("ask_hint"))}</p>\n      <div class="sai-askrow"><input type="text" class="sai-input" data-bind="ask.q" placeholder="${o(i("ask_ph"))}" value="${o(d.q)}" maxlength="400" enterkeyhint="send">\n      <button class="sai-btn sai-primary" data-act="ask" data-primary ${s.busy || !d.q.trim() ? "disabled" : ""}>${o(i("ask_btn"))}</button></div>\n      <div class="sai-chips">${i("ask_examples").map(_ => `<button class="sai-chip" data-act="ask-ex" data-q="${o(_)}">${o(_)}</button>`).join("")}</div>`;
    s.busy && (f += we()), s.err && (f += te(s.err));
    const y = d.res;
    if (y && !s.busy) if (!y.supported) f += `<div class="sai-card"><p>${o(y.reply)}</p></div>`; else {
      const _ = u(y.value, y.kind), I = (y.template || "{value}").replace("{value}", _).replace("{count}", y.count).replace("{best}", y.best != null ? R(y.group_by, y.best) : "—").replace("{worst}", y.worst != null ? R(y.group_by, y.worst) : "—");
      f += `<div class="sai-card sai-answer"><div class="sai-kicker">${o(y.title)}</div>\n          <div class="sai-big ${y.kind === "money" ? p(y.value) : ""}">${o(_)}</div><p>${o(I)}</p>\n          <div class="sai-sub">${o(i("trades_n", y.count))}</div>${G(y.rows, y.group_by)}</div>${re(y)}`;
    }
    return f;
  }
  function G(d, f) {
    if (!d || !d.length) return "";
    const y = Math.max(...d.map(_ => Math.abs(Number(_.value) || 0)), 1);
    return `<div class="sai-bars">${d.map(_ => {
      const I = Number(_.value) || 0, V = Math.round(Math.abs(I) / y * 100);
      return `<div class="sai-bar"><span class="sai-bar-l">${o(R(f, _.label))}</span>\n        <span class="sai-bar-t"><i class="${(_.kind === "money" || _.kind === "r") && I < 0 ? "neg" : "pos"}" style="width:${V}%"></i></span>\n        <span class="sai-bar-v ${_.kind === "money" ? p(I) : ""}">${o(u(_.value, _.kind))}</span><span class="sai-bar-n">${_.trades}</span></div>`;
    }).join("")}</div>`;
  }
  function Z() {
    const d = s.rev;
    d.weekStart = d.weekStart || v(h()), d.date = d.date || h();
    let f = `<div class="sai-seg sai-seg-wide">${[ "week", "day" ].map(y => `<button class="${d.mode === y ? "on" : ""}" data-act="rmode" data-v="${y}">${o(i(y))}</button>`).join("")}</div>`;
    if (d.mode === "week") {
      const y = m(d.weekStart, 6);
      f += `<div class="sai-nav"><button class="sai-x" data-act="wk" data-v="-7" aria-label="Previous">‹</button>\n        <strong>${o(b(d.weekStart))} → ${o(b(y))}</strong>\n        <button class="sai-x" data-act="wk" data-v="7" aria-label="Next" ${d.weekStart >= v(h()) ? "disabled" : ""}>›</button></div>`;
      const _ = d.week && d.week.week_start === d.weekStart ? d.week : null;
      f += `<button class="sai-btn sai-primary sai-block" data-act="gen-week" data-primary ${s.busy ? "disabled" : ""}>${o(i(_ ? "regenerate" : "generate_review"))}</button>`, 
      s.busy && (f += we()), s.err && (f += te(s.err)), _ && !s.busy && (f += Te(_));
    } else {
      f += `<div class="sai-nav"><input type="date" class="sai-input" data-bind="rev.date" value="${o(d.date)}" max="${o(h())}"></div>\n        <button class="sai-btn sai-primary sai-block" data-act="gen-day" data-primary ${s.busy ? "disabled" : ""}>${o(i("debrief_btn"))}</button>`, 
      s.busy && (f += we()), s.err && (f += te(s.err));
      const y = d.day && d.day.date === d.date ? d.day : null;
      y && !s.busy && (f += ie(y));
    }
    return f;
  }
  function ge(d, f) {
    const y = f && f.trades ? d.net_c - f.net_c : null;
    return `<div class="sai-kpis">\n      <div><span>${o(i("net"))}</span><b class="${p(d.net_c)}">${c(d.net_c, !0, !0)}</b>${y != null ? `<em class="${p(y)}">${c(y, !0, !0)} ${o(i("vs_prev"))}</em>` : ""}</div>\n      <div><span>${o(i("win_rate"))}</span><b>${l(d.win_rate)}</b></div>\n      <div><span>${o(i("trades"))}</span><b>${d.trades}</b></div>\n      <div><span>${o(i("pf"))}</span><b>${d.profit_factor == null ? "∞" : Number(d.profit_factor).toFixed(2)}</b></div></div>`;
  }
  function Te(d) {
    if (!d.review) return ge(d.stats, d.prev_stats) + `<div class="sai-empty">${o(i("no_trades_week"))}</div>`;
    const f = d.review, y = Object.entries(d.days || {}), _ = Math.max(1, ...y.map(([, K]) => Math.abs(K.net_c))), I = `<div class="sai-days">${y.map(([K, le]) => {
      const xe = (new Date(K + "T12:00:00Z").getUTCDay() + 6) % 7;
      return `<div class="sai-day"><div class="sai-day-bar"><i class="${le.net_c < 0 ? "neg" : "pos"}" style="height:${Math.max(4, Math.round(Math.abs(le.net_c) / _ * 100))}%"></i></div>\n        <b class="${p(le.net_c)}">${c(le.net_c, !0, !0)}</b><span>${o(i("wd")[xe])}</span></div>`;
    }).join("")}</div>`, V = (K, le, xe) => le && le.length ? `<h4>${o(K)}</h4><ul class="sai-list">${le.map(ce => `<li><span>${xe}</span>${o(ce)}</li>`).join("")}</ul>` : "";
    return `${ge(d.stats, d.prev_stats)}${I}\n      <div class="sai-card"><div class="sai-score"><span class="sai-ring" style="--p:${f.score * 10}">${f.score}</span><div><div class="sai-kicker">${o(i("score"))}</div><strong>${o(f.headline)}</strong></div></div>\n      <p>${o(f.summary)}</p>${V(i("went_well"), f.went_well, "↑")}${V(i("to_fix"), f.to_fix, "→")}\n      ${f.plan_vs_execution ? `<h4>${o(i("plan_exec"))}</h4><p>${o(f.plan_vs_execution)}</p>` : ""}</div>\n      <div class="sai-focus"><div><div class="sai-kicker">${o(i("focus"))}</div><p>${o(f.focus_next_week)}</p></div>\n      <div><div class="sai-kicker">${o(i("rule"))}</div><p>${o(f.rule_for_next_week)}</p></div></div>\n      <button class="sai-btn sai-block" data-act="recap">${o(i("copy_recap"))}</button>${re(d)}`;
  }
  function ye(d) {
    const f = Object.entries(d.days || {}).sort((_, I) => I[1].net_c - _[1].net_c), y = f[0] && f[0][1].net_c > 0 ? `${i("wd")[(new Date(f[0][0] + "T12:00:00Z").getUTCDay() + 6) % 7]} ${c(f[0][1].net_c)}` : "";
    return i("recap", {
      range: `${b(d.week_start)} → ${b(d.week_end)}`,
      net: c(d.stats.net_c),
      trades: i("trades_n", d.stats.trades),
      wr: l(d.stats.win_rate),
      pf: d.stats.profit_factor ? Number(d.stats.profit_factor).toFixed(2) : "",
      best: y,
      focus: d.review ? d.review.focus_next_week : ""
    });
  }
  function ie(d) {
    if (!d.debrief) return `<div class="sai-empty">${o(i("no_data_day"))}</div>`;
    const f = d.debrief, y = {
      followed: "pos",
      partly: "mid",
      broke: "neg",
      no_plan: "mid"
    }[f.verdict];
    return `${d.stats.trades ? ge(d.stats, null) : ""}\n      <div class="sai-card"><span class="sai-badge sai-${y}">${o(i("verdict_" + f.verdict))}</span><p>${o(f.summary)}</p>\n      ${f.checks.length ? `<ul class="sai-checks">${f.checks.map(_ => `<li><span class="${_.ok === !0 ? "sai-pos" : _.ok === !1 ? "sai-neg" : ""}">${_.ok === !0 ? "✓" : _.ok === !1 ? "✕" : "–"}</span><div><b>${o(_.label)}</b>${_.detail ? `<small>${o(_.detail)}</small>` : ""}</div></li>`).join("")}</ul>` : ""}\n      </div><div class="sai-focus"><div><div class="sai-kicker">${o(i("lesson"))}</div><p>${o(f.lesson)}</p></div>\n      <div><div class="sai-kicker">${o(i("tomorrow"))}</div><p>${o(f.tomorrow)}</p></div></div>${re(d)}`;
  }
  function de() {
    let d = `<p class="sai-hint">${o(i("scan_hint"))}</p>\n      <label class="sai-btn sai-primary sai-file sai-block ${s.busy ? "is-disabled" : ""}">${o(i("scan_btn"))}<input type="file" accept="image/*" data-file="receipt" ${s.busy ? "disabled" : ""}></label>`;
    s.busy && (d += we(i("reading_img"))), s.err && (d += te(s.err));
    const f = s.scan.res;
    return f && !s.busy && (d += se(f)), s.scan.saved && (d += `<div class="sai-ok">✓ ${o(i("saved_n", s.scan.saved))}</div>`), 
    d;
  }
  function se(d) {
    const f = d.items.filter(I => !I.removed);
    if (!f.length) return `<div class="sai-empty">${o(i("no_items"))}</div>` + ne(d.warnings);
    const y = s.o.expenseCategories || a, _ = d.items.map((I, V) => {
      if (I.removed) return "";
      const K = I.doc, le = I.kind === "payout", xe = ce => I.missing.includes(ce) && (ce === "amount" && K.amount_c == null || ce === "account" && !K.account_id) ? " sai-miss" : "";
      return `<article class="sai-card"><div class="sai-card-head"><div class="sai-seg">${[ "expense", "payout" ].map(ce => `<button class="${I.kind === ce ? "on" : ""}" data-act="kind" data-i="${V}" data-v="${ce}">${o(i(ce))}</button>`).join("")}</div>\n        <strong>${K.amount_c == null ? "—" : c(K.amount_c, !1)}</strong><button class="sai-link" data-act="rm-item" data-i="${V}">${o(i("remove"))}</button></div>\n        <div class="sai-grid">\n        ${M(i("amount"), `<input inputmode="decimal" data-g="amount" data-i="${V}" value="${K.amount_c == null ? "" : (K.amount_c / 100).toFixed(2)}" class="${xe("amount")}">`)}\n        ${M(i("date"), `<input type="date" data-g="${le ? "request_date" : "date"}" data-i="${V}" value="${o(le ? K.request_date : K.date)}">`)}\n        ${le ? M(i("status"), `<select data-g="status" data-i="${V}">${n.map(ce => `<option value="${ce}" ${ce === K.status ? "selected" : ""}>${o(i("st_" + ce))}</option>`).join("")}</select>`) : M(i("category"), `<select data-g="category" data-i="${V}">${y.map(ce => `<option value="${o(ce)}" ${ce === K.category ? "selected" : ""}>${o(e[s.lang]["cat_" + ce] || ce)}</option>`).join("")}</select>`)}\n        ${M(i("firm"), `<select data-g="firm_id" data-i="${V}"><option value="">${o(i("none"))}</option>${d.firms.map(ce => `<option value="${o(ce.id)}" ${ce.id === K.firm_id ? "selected" : ""}>${o(ce.name)}</option>`).join("")}</select>`)}\n        ${M(i("account"), `<select data-g="account_id" data-i="${V}" class="${xe("account")}"><option value="">${o(i("none"))}</option>${d.accounts.map(ce => `<option value="${o(ce.id)}" ${ce.id === K.account_id ? "selected" : ""}>${o(ce.name)}</option>`).join("")}</select>`, 2)}\n        ${M(i("notes"), `<input data-g="notes" data-i="${V}" value="${o(K.notes)}">`, 2)}</div></article>`;
    }).join("");
    return `<h3 class="sai-h3">${o(i("items_title", f.length))}</h3>${ne(d.warnings)}${_}\n      <button class="sai-btn sai-primary sai-block" data-act="save-items" data-primary>${o(i("save_items", f.length))}</button>`;
  }
  function ee(d, f, y) {
    if (d.kind === f) return;
    const _ = d.doc, I = _.date || _.request_date || h();
    d.kind = f, d.doc = f === "payout" ? {
      id: E("p"),
      account_id: _.account_id || "",
      firm_id: _.firm_id || "",
      amount_c: _.amount_c,
      status: "requested",
      request_date: I,
      approval_date: "",
      payment_date: "",
      notes: _.notes || "",
      ai_source: "image"
    } : {
      id: E("e"),
      date: I,
      firm_id: _.firm_id || "",
      account_id: _.account_id || "",
      category: "other",
      amount_c: _.amount_c,
      notes: _.notes || "",
      ai_source: "image"
    }, d.missing = [ "amount", "account" ];
  }
  async function fe() {
    const d = s.scan.res.items.filter(f => !f.removed);
    for (const f of d) if (f.doc.amount_c == null || f.doc.amount_c <= 0 || f.kind === "payout" && !f.doc.account_id) {
      ae(), _e(i("missing"));
      return;
    }
    await X(async () => {
      const f = {
        expenses: [],
        payouts: []
      };
      for (const y of d) {
        const _ = {
          ...y.doc
        };
        if (y.kind === "payout") {
          const V = s.scan.res.accounts.find(K => K.id === _.account_id);
          V && !_.firm_id && (_.firm_id = V.firm_id), _.status === "paid" && (_.approval_date = _.approval_date || _.request_date, 
          _.payment_date = _.payment_date || _.request_date), _.status === "approved" && (_.approval_date = _.approval_date || _.request_date);
        }
        const I = y.kind === "payout" ? "payouts" : "expenses";
        await P(I, _).catch(() => {
          throw {
            code: "save"
          };
        }), f[I].push(_);
      }
      s.scan = {
        res: null,
        saved: d.length
      }, f.expenses.length && O("expenses", f.expenses), f.payouts.length && O("payouts", f.payouts);
    });
  }
  function ke() {
    const d = s.trade || {};
    let f = `<h3 class="sai-h3">${o(d.kind === "tags" ? i("tags_title") : i("fb_title"))}</h3>`;
    if (s.busy) return f + we(d.hasImage ? i("reading_img") : i("working"));
    if (s.err) return f + te(s.err);
    const y = d.res;
    if (!y) return f;
    if (d.kind === "feedback") {
      const _ = y.feedback, I = {
        good_process: "pos",
        mixed: "mid",
        poor_process: "neg"
      }[_.verdict];
      f += `<div class="sai-card"><span class="sai-badge sai-${I}">${o(i("fb_" + _.verdict))}</span>\n        <h4>${o(i("fb_well"))}</h4><p>${o(_.went_well)}</p><h4>${o(i("fb_improve"))}</h4><p>${o(_.improve)}</p></div>\n        <div class="sai-focus"><div><div class="sai-kicker">${o(i("fb_next"))}</div><p>${o(_.next_time)}</p></div>\n        ${_.setup_context ? `<div><div class="sai-kicker">${o(i("fb_setup"))}</div><p>${o(_.setup_context)}</p></div>` : ""}</div>${re(y)}`;
    } else {
      const _ = [];
      y.setup && _.push(`<span class="sai-chip on">${o(i("setup"))}: ${o(y.setup)}</span>`), 
      y.new_setup && _.push(`<span class="sai-chip">${o(i("new_setup"))}: ${o(y.new_setup)}</span>`), 
      y.tags.forEach(I => _.push(`<span class="sai-chip">#${o(I)}</span>`)), f += `<div class="sai-card"><div class="sai-chips">${_.join("")}</div><p class="sai-sub">${o(y.reason)}</p></div>\n        <button class="sai-btn sai-primary sai-block" data-act="apply-tags" ${d.applied ? "disabled" : ""}>${o(d.applied ? "✓ " + i("applied") : i("apply"))}</button>${re(y)}`;
    }
    return f;
  }
  async function he(d, f, y = {}) {
    return s.trade = {
      kind: d,
      tradeId: f,
      opts: y,
      res: null,
      hasImage: !!y.imageUrl
    }, Q("trade"), await X(async () => {
      const _ = y.imageUrl ? await q(y.imageUrl).catch(() => null) : null;
      s.trade.res = d === "feedback" ? await g.tradeFeedback(f, _) : await g.suggestTags(f, _);
    }), s.trade.res;
  }
  async function be() {
    const d = s.trade, f = d.res, y = f.setup || f.new_setup || null;
    if (d.opts.onApply) {
      await d.opts.onApply({
        setup: y,
        tags: f.tags,
        tradeId: d.tradeId
      }), d.applied = !0, ae();
      return;
    }
    await X(async () => {
      const I = ((await C("api/data")).trades || []).find(V => V.id === d.tradeId);
      if (!I) throw {
        code: "not_found"
      };
      y && !I.setup && (I.setup = y), I.tags = [ ...new Set([ ...I.tags || [], ...f.tags ]) ], 
      await P("trades", I).catch(() => {
        throw {
          code: "save"
        };
      }), d.applied = !0, O("trades", [ I ]);
    });
  }
  function _e(d) {
    const f = s.root.querySelector(".sai-foot");
    f && (f.textContent = d, f.classList.add("sai-flash"), setTimeout(() => {
      f.classList.remove("sai-flash"), oe();
    }, 2600));
  }
  function $e(d) {
    const f = d.target.closest("[data-act]");
    if (!f) return;
    const y = f.dataset.act, _ = Number(f.dataset.i);
    if (y === "close") return me();
    if (y === "tab") return s.tab = f.dataset.tab, s.err = null, ae();
    if (y === "parse") return X(async () => {
      s.log.saved = 0, s.log.reading = !1, s.log.res = await g.parseTrades(s.log.text);
    });
    if (y === "dir") {
      const I = s.log.res.drafts[_].trade;
      return I.direction = f.dataset.v, A(I), ae();
    }
    if (y === "rm") return s.log.res.drafts[_].removed = !0, ae();
    if (y === "save-trades") return N();
    if (y === "ask-ex") return s.ask.q = f.dataset.q, X(async () => {
      s.ask.res = await g.ask(s.ask.q);
    });
    if (y === "ask") return X(async () => {
      s.ask.res = await g.ask(s.ask.q);
    });
    if (y === "rmode") return s.rev.mode = f.dataset.v, s.err = null, ae();
    if (y === "wk") return s.rev.weekStart = m(s.rev.weekStart, Number(f.dataset.v)), 
    s.err = null, ae();
    if (y === "gen-week") return X(async () => {
      s.rev.week = await g.weeklyReview(s.rev.weekStart);
    });
    if (y === "gen-day") return X(async () => {
      s.rev.day = await g.dayDebrief(s.rev.date);
    });
    if (y === "recap") {
      const I = ye(s.rev.week);
      (navigator.clipboard ? navigator.clipboard.writeText(I) : Promise.reject()).then(() => {
        f.textContent = "✓ " + i("copied");
      }).catch(() => {
        window.prompt("", I);
      });
      return;
    }
    if (y === "kind") return ee(s.scan.res.items[_], f.dataset.v, s.scan.res), ae();
    if (y === "rm-item") return s.scan.res.items[_].removed = !0, ae();
    if (y === "save-items") return fe();
    if (y === "apply-tags") return be();
  }
  function ve(d) {
    const f = d.target;
    if (f.dataset.bind) {
      const [y, _] = f.dataset.bind.split(".");
      s[y][_] = f.value;
      const I = s.root.querySelector("[data-primary]");
      I && (y === "log" || y === "ask") && (I.disabled = s.busy || !f.value.trim());
      return;
    }
    if (f.dataset.f) {
      const y = s.log.res.drafts[Number(f.dataset.i)].trade, _ = f.dataset.f, I = f.value;
      if (_ === "entry" || _ === "exit") y[_] = j(I), A(y), Se(f, y); else if (_ === "contracts") y.contracts = Math.max(1, parseInt(I, 10) || 1), 
      A(y), Se(f, y); else if (_ === "pnl") {
        const V = j(I);
        y.pnl_c = V == null ? null : Math.round(V * 100), y._pnlTyped = V != null, y.pnl_manual = !0, 
        Se(f, y, !0);
      } else if (_ === "fees") {
        const V = j(I);
        y.fees_c = V == null ? 0 : Math.round(Math.abs(V) * 100);
      } else y[_] = I;
      return;
    }
    if (f.dataset.g) {
      const y = s.scan.res.items[Number(f.dataset.i)].doc, _ = f.dataset.g;
      if (_ === "amount") {
        const I = j(f.value);
        y.amount_c = I == null ? null : Math.round(Math.abs(I) * 100);
      } else y[_] = f.value;
    }
  }
  function Se(d, f, y) {
    const _ = d.closest(".sai-card");
    if (!_) return;
    const I = _.querySelector(".sai-card-head strong");
    if (I.textContent = f.pnl_c == null ? "—" : c(f.pnl_c), I.className = p(f.pnl_c), 
    !y) {
      const V = _.querySelector('[data-f="pnl"]');
      V && (V.value = f.pnl_c == null ? "" : (f.pnl_c / 100).toFixed(2));
    }
  }
  function Ae(d) {
    const f = d.target;
    if (f.dataset.f === "instrument" || f.dataset.f === "account_id") {
      const y = s.log.res.drafts[Number(f.dataset.i)].trade;
      y[f.dataset.f] = f.value, A(y), Se(f, y);
      return;
    }
    if (f.dataset.g || f.dataset.f || f.dataset.bind) return ve(d);
    if (f.dataset.file) {
      const y = f.files && f.files[0];
      return f.value = "", y ? f.dataset.file === "trades" ? (s.log.reading = !0, s.log.saved = 0, 
      X(async () => {
        const I = await H(y);
        s.log.res = await g.importImage(I, "trades");
      }, () => {
        s.log.reading = !1;
      })) : (s.scan.saved = 0, X(async () => {
        const I = await H(y);
        s.scan.res = await g.importImage(I, "receipt");
      })) : void 0;
    }
  }
  function Le(d) {
    return s.o = Object.assign({}, d || {}), s.lang = L(), document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", z, {
      once: !0
    }) : z(), window.SweepAI;
  }
  window.SweepAI = {
    init: Le,
    open: Q,
    close: me,
    api: g,
    prepImage: H,
    setLang(d) {
      e[d] && (s.lang = d, s.root && !s.root.hidden && ae());
    },
    tradeFeedback: (d, f) => he("feedback", d, f),
    suggestTags: (d, f) => he("tags", d, f),
    recapText: d => ye(d)
  };
  const Me = document.currentScript;
  Me && Me.hasAttribute("data-autoinit") && Le({
    base: Me.getAttribute("data-base") || void 0
  });
})();

const AI = {
  on: !1,
  usage: null,
  ready: !1
};

function aiInit() {
  if (AI.ready || !window.SweepAI || S.mode !== "server") return;
  AI.ready = !0, SweepAI.init({
    fab: !1,
    lang: LANG,
    url: (t, a) => t + (a ? "?" + new URLSearchParams(a) : ""),
    sessionFor: sessionFor,
    expenseCategories: ECAT.map(t => t[0]),
    saveDoc: async (t, a) => {
      const n = {
        ...a
      };
      if (n.id || (n.id = uid()), t === "trades") {
        if (n.instrument = n.instrument || "NQ", n.contracts = Math.max(1, +n.contracts || 1), 
        n.entry_time && !n.session && (n.session = sessionFor(n.entry_time)), n.pnl_c == null && n.entry != null && n.exit != null && (n.pnl_c = calcPnl(n.direction, n.entry, n.exit, n.contracts, n.instrument)), 
        n.entry_time && n.exit_time) {
          const s = o => {
            const [r, c, l] = String(o).split(":").map(Number);
            return r * 3600 + c * 60 + (l || 0);
          }, i = s(n.exit_time) - s(n.entry_time);
          i >= 0 && (n.duration_s = i);
        }
        n.discipline = n.discipline || {}, n.emo = n.emo || {}, n.review = n.review || {}, 
        n.shots = n.shots || [], n.tags = n.tags || [];
      }
      put(t, n);
    },
    onDataChanged: () => {
      render(), toast("Saved");
    }
  });
  const e = document.querySelector(".sai");
  e && e.setAttribute("data-noi18n", ""), SweepAI.setLang(LANG), SweepAI.api.status().then(t => {
    AI.on = !!t.enabled, AI.usage = t.usage || null, document.body.classList.toggle("ai-on", AI.on), 
    AI.on && (render(), aiEconRefresh(Object.values(ECON.days).flat()), askShow(!0));
  }).catch(() => {});
}

function aiOpen(e) {
  AI.on && (closeTicket && TK && closeTicket(), SweepAI.open(e));
}

function aiDayDebrief(e) {
  aiOpen("review"), setTimeout(() => {
    const t = document.querySelector(".sai");
    if (!t) return;
    const a = t.querySelector('[data-act="rmode"][data-v="day"]');
    a && a.click(), setTimeout(() => {
      const n = t.querySelector('input[data-bind="rev.date"]');
      n && e && (n.value = e, n.dispatchEvent(new Event("input", {
        bubbles: !0
      })));
    }, 40);
  }, 60);
}

function aiTradeFeedback(e) {
  const t = getDoc("trades", e), a = (t && t.shots || [])[0];
  SweepAI.tradeFeedback(e, a ? {
    imageUrl: blobSrc(a.id)
  } : {});
}

function aiSuggest(e) {
  const t = getDoc("trades", e), a = (t && t.shots || [])[0];
  SweepAI.suggestTags(e, {
    ...a ? {
      imageUrl: blobSrc(a.id)
    } : {},
    onApply: ({setup: n, tags: s}) => {
      editDoc("trades", e, i => {
        n && (i.setup = n), s && s.length && (i.tags = [ ...new Set([ ...i.tags || [], ...s ]) ]);
      }), syncTrade(e, [ "setup", "tags" ]), render();
    }
  });
}

const aiBtn = (e, t, a = "") => `<button class="btn sm ai-btn ai-only" data-act="${e}" ${a}><span class="ai-sp" aria-hidden="true">✦</span>${t}</button>`;

document.addEventListener("keydown", e => {
  e.key === "Escape" && document.querySelector(".sai.sai-open") && window.SweepAI && (e.stopPropagation(), 
  SweepAI.close());
}, !0);

const AIE = {
  last: 0,
  busy: !1,
  rep: {}
};

function aiEconRefresh(e) {
  if (!AI.on || AIE.busy) return;
  const t = Date.now() / 1e3, a = (e || []).some(s => s.ts < t - 50 && s.ts > t - 900 && !s.actual);
  Date.now() - AIE.last < (a ? 4e4 : 12e4) || !(e || []).some(s => s.ts < t - 90 && s.ts > t - 3 * 86400 && !s.actual || s.ts > t && s.ts < t + 7 * 86400 && !s.forecast) || (AIE.busy = !0, 
  AIE.last = Date.now(), apiJSON("api/econ/ai-refresh", {
    method: "POST",
    body: {}
  }).then(s => {
    if (s && s.updated > 0) {
      ECON.pending = {}, ECON.at = {};
      for (const i in ECON.days) delete ECON.days[i];
      render(), EVP.id && typeof evLoad == "function" && evLoad();
    }
  }).catch(() => {}).finally(() => {
    AIE.busy = !1, a && (clearTimeout(AIE.t), AIE.t = setTimeout(() => aiEconRefresh(Object.values(ECON.days).flat()), 42e3));
  }));
}

function aiReportLoad(e) {
  if (!AI.on || S.mode !== "server") return;
  const t = AIE.rep[e], a = Date.now();
  t && (t.loading || t.state === "ready" && !(t.next_at && a >= t.next_at * 1e3) || t.state !== "ready" && t.at && a - t.at < 3e4) || (AIE.rep[e] = {
    loading: !0
  }, apiJSON("api/econ/event/" + e + "/report", {
    method: "POST",
    body: {
      lang: LANG
    }
  }).then(n => {
    AIE.rep[e] = {
      ...n,
      at: Date.now()
    };
  }).catch(n => {
    AIE.rep[e] = {
      state: "error",
      code: n && n.code,
      at: Date.now()
    };
  }).finally(() => {
    EVP.id === e && typeof evRender == "function" && evRender();
    const n = AIE.rep[e], s = n && (n.next_at || n.ready_at);
    s && (clearTimeout(AIE.rt), AIE.rt = setTimeout(() => {
      EVP.id === e && aiReportLoad(e);
    }, Math.max(5e3, s * 1e3 - Date.now() + 4e3)));
  }));
}

function aiReportBlock(e) {
  if (!AI.on || S.mode !== "server") return "";
  const t = e.event.id, a = AIE.rep[t];
  if ((!a || a.state === "ready" && a.next_at && Date.now() >= a.next_at * 1e3 || (a.state === "awaiting_actual" || a.state === "waiting") && e.event.actual && Date.now() / 1e3 >= e.event.ts + 60) && (setTimeout(() => aiReportLoad(t), 0), 
  !a)) return "";
  const n = {
    en: {
      t: "Market impact",
      by: "Sweep AI report",
      wait: "Flash recap in about a minute.",
      flash: "Flash · first minute",
      full: "Full report",
      fin: "Final report",
      more: "Full report with the market reaction about 30 minutes after the release.",
      awaiting: "Waiting for the official number. Sweep AI checks again every few minutes.",
      up: "Flash recap about one minute after the release, full report after 30 minutes.",
      load: "Writing the report…",
      err: "The report could not be generated right now. Try again later.",
      nq: "Nasdaq-100 (NQ)",
      es: "S&P 500 (ES)",
      yields: "10-year yield",
      dollar: "U.S. dollar",
      drivers: "Why it moved",
      fed: "Fed read",
      watch: "What to watch next",
      vs: "Versus expectations",
      src: "Sources",
      note: "AI-generated from public news. It can be wrong. Not financial advice.",
      conf: {
        high: "High confidence",
        medium: "Medium confidence",
        low: "Low confidence"
      },
      v: {
        hotter: "Hotter than expected",
        cooler: "Cooler than expected",
        stronger: "Stronger than expected",
        weaker: "Weaker than expected",
        in_line: "In line",
        mixed: "Mixed"
      }
    },
    fr: {
      t: "Impact sur le marché",
      by: "Rapport Sweep AI",
      wait: "Récap éclair dans environ une minute.",
      flash: "Éclair · première minute",
      full: "Rapport complet",
      fin: "Rapport final",
      more: "Rapport complet avec la réaction du marché environ 30 minutes après la publication.",
      awaiting: "En attente du chiffre officiel. Sweep AI revérifie toutes les quelques minutes.",
      up: "Récap éclair environ une minute après la publication, rapport complet après 30 minutes.",
      load: "Rédaction du rapport…",
      err: "Le rapport n'a pas pu être généré pour le moment. Réessaie plus tard.",
      nq: "Nasdaq-100 (NQ)",
      es: "S&P 500 (ES)",
      yields: "Taux 10 ans",
      dollar: "Dollar US",
      drivers: "Pourquoi ça a bougé",
      fed: "Lecture Fed",
      watch: "À surveiller ensuite",
      vs: "Par rapport aux attentes",
      src: "Sources",
      note: "Généré par l'IA à partir de nouvelles publiques. Peut contenir des erreurs. Pas un conseil financier.",
      conf: {
        high: "Confiance élevée",
        medium: "Confiance moyenne",
        low: "Confiance faible"
      },
      v: {
        hotter: "Plus chaud que prévu",
        cooler: "Plus froid que prévu",
        stronger: "Plus fort que prévu",
        weaker: "Plus faible que prévu",
        in_line: "Conforme",
        mixed: "Mitigé"
      }
    },
    es: {
      t: "Impacto en el mercado",
      by: "Informe de Sweep AI",
      wait: "Resumen rápido en un minuto aproximadamente.",
      flash: "Flash · primer minuto",
      full: "Informe completo",
      fin: "Informe final",
      more: "Informe completo con la reacción del mercado unos 30 minutos después de la publicación.",
      awaiting: "Esperando la cifra oficial. Sweep AI vuelve a comprobar cada pocos minutos.",
      up: "Resumen rápido un minuto después de la publicación, informe completo a los 30 minutos.",
      load: "Redactando el informe…",
      err: "No se pudo generar el informe ahora. Inténtalo más tarde.",
      nq: "Nasdaq-100 (NQ)",
      es: "S&P 500 (ES)",
      yields: "Rendimiento a 10 años",
      dollar: "Dólar EE. UU.",
      drivers: "Por qué se movió",
      fed: "Lectura de la Fed",
      watch: "Qué vigilar después",
      vs: "Frente a lo esperado",
      src: "Fuentes",
      note: "Generado por IA a partir de noticias públicas. Puede contener errores. No es asesoramiento financiero.",
      conf: {
        high: "Confianza alta",
        medium: "Confianza media",
        low: "Confianza baja"
      },
      v: {
        hotter: "Más caliente de lo esperado",
        cooler: "Más frío de lo esperado",
        stronger: "Más fuerte de lo esperado",
        weaker: "Más débil de lo esperado",
        in_line: "En línea",
        mixed: "Mixto"
      }
    }
  }[LANG], s = `<div class="sec-h"><h2><span class="ai-sp">✦</span>${n.t}</h2><span class="help">${n.by}</span></div>`, i = u => `<section class="evs air" data-noi18n>${s}<div class="air-box">${u}</div></section>`;
  if (a.loading) return i(`<div class="air-load"><span class="air-dot"></span>${n.load}</div>`);
  if (a.state === "upcoming") return i(`<p class="muted">${n.up}</p>`);
  if (a.state === "awaiting_actual") return i(`<p class="muted">${n.awaiting}</p>`);
  if (a.state === "waiting") return i(`<p class="muted">${n.wait}</p>`);
  if (a.state === "error" || a.state === "off") return i(`<p class="muted">${n.err}</p>`);
  const o = a.report || {}, r = o.reaction || {}, c = (u, h) => h ? `<div class="air-rx"><span>${n[u]}</span><b>${esc(h)}</b></div>` : "", l = (a.sources || []).map(u => `<a href="${esc(u.uri)}" target="_blank" rel="noopener nofollow">${esc(u.title || "source")}</a>`).join("");
  setTimeout(() => {
    const u = document.querySelector("#evPanel .air-suggest");
    if (u && a.suggest && !u.shadowRoot) {
      const h = u.attachShadow({
        mode: "open"
      });
      h.innerHTML = a.suggest;
    }
  }, 0);
  const p = a.stage || o.stage || "full";
  if (a.locked) {
    const u = `<div class="air-rxs"><div class="air-rx"><span>${n.nq}</span><b>−0.8% → −0.4%</b></div><div class="air-rx"><span>${n.yields}</span><b>+9 bp</b></div><div class="air-rx"><span>${n.es}</span><b>−0.5%</b></div><div class="air-rx"><span>${n.dollar}</span><b>+0.6%</b></div></div><div class="air-sub"><span>${n.drivers}</span>…</div>`;
    return i(`<div class="air-top"><span class="air-verdict v-${o.verdict}">${n.v[o.verdict] || ""}</span><span class="air-stage s-${p}">${p === "flash" ? n.flash : p === "final" ? n.fin : n.full}</span></div>\n      ${o.headline ? `<h3 class="air-h">${esc(o.headline)}</h3>` : ""}${o.summary ? `<p>${esc(o.summary)}</p>` : ""}\n      <div class="air-locked" data-lock="calendar_notes" data-feature="calendar_notes" aria-hidden="true">${u}</div><div class="air-suggest"></div>`);
  }
  return i(`<div class="air-top"><span class="air-verdict v-${o.verdict}">${n.v[o.verdict] || ""}</span><span class="air-stage s-${p}">${p === "flash" ? n.flash : p === "final" ? n.fin : n.full}</span></div>\n    ${o.headline ? `<h3 class="air-h">${esc(o.headline)}</h3>` : ""}${o.summary ? `<p>${esc(o.summary)}</p>` : ""}\n    ${o.vs_expectations ? `<div class="air-sub"><span>${n.vs}</span>${esc(o.vs_expectations)}</div>` : ""}\n    <div class="air-rxs">${c("nq", r.nq)}${c("es", r.es)}${c("yields", r.yields)}${c("dollar", r.dollar)}</div>\n    ${(o.drivers || []).length ? `<div class="air-sub"><span>${n.drivers}</span><ul>${o.drivers.map(u => `<li>${esc(u)}</li>`).join("")}</ul></div>` : ""}\n    ${o.fed_read ? `<div class="air-sub"><span>${n.fed}</span>${esc(o.fed_read)}</div>` : ""}\n    ${o.what_to_watch ? `<div class="air-sub"><span>${n.watch}</span>${esc(o.what_to_watch)}</div>` : ""}\n    ${l ? `<div class="air-src"><span>${n.src}</span>${l}</div>` : ""}<div class="air-suggest"></div>\n    ${p === "flash" ? `<p class="air-more">${n.more}</p>` : ""}\n    <p class="air-note">${n.conf[o.confidence] || ""} · ${n.note}</p>`);
}

const ASK = {
  open: !1,
  busy: !1,
  msgs: [],
  built: !1
}, ASKL = {
  en: {
    name: "Ask Sweep",
    sub: "Your trading assistant",
    hi: "Hi, I'm Sweep's assistant. Ask me about your trades, today's news, or how to use the app.",
    ph: "Ask anything…",
    send: "Send",
    starters: [ "How did I do this week?", "Which setup makes me the most money?", "What's on the economic calendar today?", "How do I add a trade?" ],
    left: e => `${e} AI actions left today`,
    think: "Thinking",
    clear: "New chat",
    close: "Close",
    err: {
      daily_limit: "You've used today's AI actions. They reset at midnight (New York).",
      budget: "Sweep AI is paused for today.",
      throttle: "One second…",
      disabled: "Sweep AI is turned off.",
      _: "Something went wrong. Try again."
    },
    act: {
      new_trade: "Open the trade ticket",
      ai_log: "Log with AI",
      ai_review: "Open the AI review",
      ai_scan: "Scan a receipt",
      insights: "Open Stats",
      calendar: "Open the calendar",
      news: "Open the economic calendar",
      journal: "Open the journal",
      accounts: "Open accounts",
      payouts: "Open payouts",
      settings: "Open settings",
      import: "Import a CSV"
    },
    note: "AI can be wrong. Not financial advice."
  },
  fr: {
    name: "Ask Sweep",
    sub: "Ton assistant de trading",
    hi: "Salut ! Je suis l'assistant de Sweep. Pose-moi une question sur tes trades, les nouvelles du jour ou l'utilisation de l'app.",
    ph: "Pose ta question…",
    send: "Envoyer",
    starters: [ "Comment s'est passée ma semaine ?", "Quel setup me rapporte le plus ?", "Qu'y a-t-il au calendrier économique aujourd'hui ?", "Comment ajouter un trade ?" ],
    left: e => `${e} actions IA restantes aujourd'hui`,
    think: "Réflexion",
    clear: "Nouvelle conversation",
    close: "Fermer",
    err: {
      daily_limit: "Tu as utilisé tes actions IA du jour. Elles reviennent à minuit (New York).",
      budget: "Sweep AI est en pause pour aujourd'hui.",
      throttle: "Une seconde…",
      disabled: "Sweep AI est désactivé.",
      _: "Une erreur est survenue. Réessaie."
    },
    act: {
      new_trade: "Ouvrir le ticket",
      ai_log: "Saisir avec l'IA",
      ai_review: "Ouvrir le bilan IA",
      ai_scan: "Scanner un reçu",
      insights: "Ouvrir les Stats",
      calendar: "Ouvrir le calendrier",
      news: "Ouvrir le calendrier économique",
      journal: "Ouvrir le journal",
      accounts: "Ouvrir les comptes",
      payouts: "Ouvrir les payouts",
      settings: "Ouvrir les réglages",
      import: "Importer un CSV"
    },
    note: "L'IA peut se tromper. Pas un conseil financier."
  },
  es: {
    name: "Ask Sweep",
    sub: "Tu asistente de trading",
    hi: "¡Hola! Soy el asistente de Sweep. Pregúntame por tus operaciones, las noticias de hoy o cómo usar la app.",
    ph: "Pregunta lo que quieras…",
    send: "Enviar",
    starters: [ "¿Cómo me fue esta semana?", "¿Qué setup me da más dinero?", "¿Qué hay hoy en el calendario económico?", "¿Cómo añado una operación?" ],
    left: e => `${e} acciones de IA restantes hoy`,
    think: "Pensando",
    clear: "Nueva conversación",
    close: "Cerrar",
    err: {
      daily_limit: "Usaste las acciones de IA de hoy. Vuelven a medianoche (Nueva York).",
      budget: "Sweep AI está en pausa hoy.",
      throttle: "Un segundo…",
      disabled: "Sweep AI está desactivado.",
      _: "Algo salió mal. Inténtalo de nuevo."
    },
    act: {
      new_trade: "Abrir el ticket",
      ai_log: "Registrar con IA",
      ai_review: "Abrir la revisión IA",
      ai_scan: "Escanear un recibo",
      insights: "Abrir Stats",
      calendar: "Abrir el calendario",
      news: "Abrir el calendario económico",
      journal: "Abrir el diario",
      accounts: "Abrir cuentas",
      payouts: "Abrir payouts",
      settings: "Abrir ajustes",
      import: "Importar un CSV"
    },
    note: "La IA puede equivocarse. No es asesoramiento financiero."
  }
}, AL = () => ASKL[LANG] || ASKL.en, ASK_MARK = '<svg viewBox="40 8 40 102" fill="none" aria-hidden="true"><line x1="60" y1="14" x2="60" y2="30" stroke="currentColor" stroke-width="7" stroke-linecap="round"/><rect x="46" y="28" width="28" height="44" rx="6" fill="currentColor"/><line x1="60" y1="70" x2="60" y2="84" stroke="currentColor" stroke-width="7"/><line x1="60" y1="84" x2="60" y2="104" stroke="var(--pos)" stroke-width="7" stroke-linecap="round"/></svg>';

function askBuild() {
  if (ASK.built) return;
  ASK.built = !0;
  try {
    ASK.msgs = JSON.parse(sessionStorage.getItem("tj.ask") || "[]");
  } catch {
    ASK.msgs = [];
  }
  const e = document.createElement("button");
  e.id = "askFab", e.className = "ask-fab", e.type = "button", e.setAttribute("data-noi18n", ""), 
  e.innerHTML = `<span class="ask-fab-ic">${ASK_MARK}<i>✦</i></span><span class="ask-fab-l">${AL().name}</span>`, 
  e.setAttribute("aria-label", AL().name), e.addEventListener("click", () => askToggle(!0));
  const t = document.createElement("aside");
  t.id = "askPanel", t.className = "evp askp", t.setAttribute("aria-label", AL().name), 
  t.setAttribute("data-noi18n", ""), t.innerHTML = '<div class="evp-in ask-in"></div>';
  const a = document.createElement("div");
  a.id = "askScrim", a.className = "evp-scrim ask-scrim", a.addEventListener("click", () => askToggle(!1)), 
  document.body.append(e, a, t), swipeDismiss(t, {
    scroller: () => t.querySelector(".ask-log"),
    onClose: () => askToggle(!1),
    ignore: "textarea,.ask-chips"
  }), t.addEventListener("click", askClick), t.addEventListener("keydown", n => {
    n.key === "Enter" && !n.shiftKey && n.target.matches("textarea") && (n.preventDefault(), 
    askSend());
  }), t.addEventListener("input", n => {
    n.target.matches("textarea") && (n.target.style.height = "auto", n.target.style.height = Math.min(120, n.target.scrollHeight) + "px");
  });
}

function askShow(e) {
  askBuild(), document.body.classList.toggle("ask-on", !!e);
}

function askToggle(e) {
  askBuild(), ASK.open = e;
  const t = $("#askPanel"), a = $("#askScrim");
  e ? (askRender(), requestAnimationFrame(() => {
    t.classList.add("open"), a.classList.add("open"), document.body.classList.add("ask-open");
  }), innerWidth <= 600 && document.body.classList.add("evp-lock"), setTimeout(() => {
    if (innerWidth > 600) {
      const n = t.querySelector("textarea");
      n && n.focus();
    }
  }, 350)) : (t.classList.remove("open"), a.classList.remove("open"), document.body.classList.remove("ask-open"), 
  document.body.classList.remove("evp-lock"));
}

function askBubble(e) {
  const t = AL();
  return e.role === "user" ? `<div class="ask-msg u"><div>${esc(e.text)}</div></div>` : `<div class="ask-msg b${e.err ? " err" : ""}"><span class="ask-av">${ASK_MARK}</span><div>${esc(e.text).replace(/\n/g, "<br>")}\n    ${e.action && t.act[e.action] ? `<button class="ask-act" data-ask-act="${e.action}">${t.act[e.action]} ›</button>` : ""}</div></div>`;
}

function askRender() {
  const e = $("#askPanel .ask-in");
  if (!e) return;
  const t = AL(), a = ASK.msgs.at(-1), n = a && a.role === "bot" && a.followups && a.followups.length ? a.followups : ASK.msgs.length ? [] : t.starters;
  e.innerHTML = `<header class="ask-head"><span class="ask-hav">${ASK_MARK}</span><div><b>${t.name}</b><small>${t.sub}</small></div>\n      <span class="ask-sp"></span>${ASK.msgs.length ? `<button class="ask-x ask-new" data-ask-act="clear" aria-label="${t.clear}" title="${t.clear}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg></button>` : ""}<button class="ask-x" data-ask-act="close" aria-label="${t.close}">✕</button></header>\n    <div class="ask-log" role="log" aria-live="polite">${askBubble({
    role: "bot",
    text: t.hi
  })}${ASK.msgs.map(askBubble).join("")}\n      ${ASK.busy ? `<div class="ask-msg b"><span class="ask-av">${ASK_MARK}</span><div class="ask-typing" aria-label="${t.think}"><i></i><i></i><i></i></div></div>` : ""}</div>\n    ${n.length && !ASK.busy ? `<div class="ask-chips">${n.map(i => `<button data-ask-q="${esc(i)}">${esc(i)}</button>`).join("")}</div>` : ""}\n    <div class="ask-bar"><textarea rows="1" placeholder="${t.ph}" maxlength="600" ${ASK.busy ? "disabled" : ""}></textarea><button class="ask-send" data-ask-act="send" aria-label="${t.send}" ${ASK.busy ? "disabled" : ""}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button></div>\n    <p class="ask-foot">${AI.usage && AI.usage.remaining != null ? t.left(AI.usage.remaining) + " · " : ""}${t.note}</p>`;
  const s = e.querySelector(".ask-log");
  s.scrollTop = s.scrollHeight;
}

function askClick(e) {
  const t = e.target.closest("[data-ask-q]");
  if (t) {
    askSend(t.dataset.askQ);
    return;
  }
  const a = e.target.closest("[data-ask-act]");
  if (!a) return;
  const n = a.dataset.askAct;
  if (n === "close") return askToggle(!1);
  if (n === "send") return askSend();
  if (n === "clear") return ASK.msgs = [], sessionStorage.removeItem("tj.ask"), askRender();
  const s = {
    new_trade: () => openTicket(null),
    ai_log: () => aiOpen("log"),
    ai_review: () => aiOpen("review"),
    ai_scan: () => aiOpen("scan"),
    insights: () => location.hash = "#analytics",
    calendar: () => location.hash = "#calendar",
    news: () => location.hash = "#news",
    journal: () => location.hash = "#journal",
    accounts: () => location.hash = "#accounts",
    payouts: () => location.hash = "#payouts",
    settings: () => location.hash = "#settings",
    import: () => location.hash = "#import"
  }[n];
  s && (askToggle(!1), setTimeout(s, innerWidth <= 600 ? 250 : 0));
}

async function askSend(e) {
  const t = $("#askPanel textarea");
  if (e = (e ?? (t ? t.value : "")).trim(), !e || ASK.busy) return;
  const a = ASK.msgs.slice(-8).map(s => ({
    role: s.role === "user" ? "user" : "bot",
    text: s.text
  }));
  ASK.msgs.push({
    role: "user",
    text: e
  }), ASK.busy = !0, askRender(), haptic && haptic(6);
  try {
    const s = await apiJSON("api/ai/chat", {
      method: "POST",
      body: {
        message: e,
        history: a,
        lang: LANG
      }
    });
    ASK.msgs.push({
      role: "bot",
      text: s.reply || "—",
      action: s.action,
      followups: s.followups
    }), s.usage && (AI.usage = s.usage);
  } catch (s) {
    const i = AL();
    ASK.msgs.push({
      role: "bot",
      err: !0,
      text: i.err[s && s.code] || i.err._
    });
  }
  ASK.busy = !1, ASK.msgs = ASK.msgs.slice(-30);
  try {
    sessionStorage.setItem("tj.ask", JSON.stringify(ASK.msgs));
  } catch {}
  askRender();
  const n = $("#askPanel textarea");
  n && innerWidth > 600 && n.focus();
}

document.addEventListener("keydown", e => {
  e.key === "Escape" && ASK.open && (e.stopPropagation(), askToggle(!1));
}, !0);

const SH = {
  kind: null,
  id: null,
  fmt: "post",
  amounts: !0,
  firm: !0,
  blob: null,
  url: null,
  busy: !1
}, SH_FORMATS = {
  post: [ 1080, 1350 ],
  story: [ 1080, 1920 ],
  wide: [ 1200, 675 ]
}, SHL = {
  en: {
    title: "Share card",
    post: "Post",
    story: "Story",
    wide: "Wide",
    amounts: "Show amounts",
    firm: "Show prop firm",
    share: "Share",
    download: "Save image",
    copy: "Copy caption",
    copied: "Caption copied",
    saved: "Image saved",
    payout: "Payout received",
    payoutN: e => `Payout #${e}`,
    first: "First payout",
    lifetime: "Lifetime payouts",
    week: "Weekly recap",
    weekOf: e => `Week of ${e}`,
    net: "Net after fees",
    netSub: "Payouts − evaluations, resets and fees",
    day: "Daily recap",
    trade: "Trade",
    pnl: "Net P&L",
    wr: "Win rate",
    trades: "Trades",
    disc: "Discipline",
    bestDay: "Best day",
    payouts: "Payouts",
    fees: "Fees paid",
    ret: "Return on fees",
    r: "R multiple",
    entry: "Entry",
    exit: "Exit",
    dur: "Duration",
    setup: "Setup",
    received: "Received",
    track: "Tracked with Sweep",
    account: "Account",
    hidden: "Amounts hidden",
    greenDays: "Green days",
    cap: {
      payout: e => `Payout received${e ? ` ${e}` : ""} 💸 Tracked with Sweep`,
      week: e => `My trading week${e ? `: ${e}` : ""}. Process first. Tracked with Sweep`,
      net: e => `Net after fees${e ? `: ${e}` : ""}. Every payout, every fee, one record. Tracked with Sweep`,
      trade: e => `Trade recap${e ? ` ${e}` : ""}. Tracked with Sweep`,
      day: e => `Today${e ? `: ${e}` : ""}. Tracked with Sweep`
    }
  },
  fr: {
    title: "Carte à partager",
    post: "Publication",
    story: "Story",
    wide: "Large",
    amounts: "Afficher les montants",
    firm: "Afficher la prop firm",
    share: "Partager",
    download: "Enregistrer l'image",
    copy: "Copier la légende",
    copied: "Légende copiée",
    saved: "Image enregistrée",
    payout: "Payout reçu",
    payoutN: e => `Payout no ${e}`,
    first: "Premier payout",
    lifetime: "Total des payouts",
    week: "Bilan de la semaine",
    weekOf: e => `Semaine du ${e}`,
    net: "Net après frais",
    netSub: "Payouts − évaluations, resets et frais",
    day: "Bilan du jour",
    trade: "Trade",
    pnl: "P&L net",
    wr: "Réussite",
    trades: "Trades",
    disc: "Discipline",
    bestDay: "Meilleur jour",
    payouts: "Payouts",
    fees: "Frais payés",
    ret: "Retour sur frais",
    r: "Multiple R",
    entry: "Entrée",
    exit: "Sortie",
    dur: "Durée",
    setup: "Setup",
    received: "Reçu",
    track: "Suivi avec Sweep",
    account: "Compte",
    hidden: "Montants masqués",
    greenDays: "Jours verts",
    cap: {
      payout: e => `Payout reçu${e ? ` ${e}` : ""} 💸 Suivi avec Sweep`,
      week: e => `Ma semaine de trading${e ? ` : ${e}` : ""}. Le processus d'abord. Suivi avec Sweep`,
      net: e => `Net après frais${e ? ` : ${e}` : ""}. Chaque payout, chaque frais, un seul historique. Suivi avec Sweep`,
      trade: e => `Récap de trade${e ? ` ${e}` : ""}. Suivi avec Sweep`,
      day: e => `Aujourd'hui${e ? ` : ${e}` : ""}. Suivi avec Sweep`
    }
  },
  es: {
    title: "Tarjeta para compartir",
    post: "Post",
    story: "Historia",
    wide: "Ancha",
    amounts: "Mostrar importes",
    firm: "Mostrar prop firm",
    share: "Compartir",
    download: "Guardar imagen",
    copy: "Copiar texto",
    copied: "Texto copiado",
    saved: "Imagen guardada",
    payout: "Payout recibido",
    payoutN: e => `Payout n.º ${e}`,
    first: "Primer payout",
    lifetime: "Payouts totales",
    week: "Resumen semanal",
    weekOf: e => `Semana del ${e}`,
    net: "Neto tras comisiones",
    netSub: "Payouts − evaluaciones, resets y comisiones",
    day: "Resumen del día",
    trade: "Operación",
    pnl: "P&L neto",
    wr: "Acierto",
    trades: "Operaciones",
    disc: "Disciplina",
    bestDay: "Mejor día",
    payouts: "Payouts",
    fees: "Comisiones",
    ret: "Retorno sobre comisiones",
    r: "Múltiplo R",
    entry: "Entrada",
    exit: "Salida",
    dur: "Duración",
    setup: "Setup",
    received: "Recibido",
    track: "Registrado con Sweep",
    account: "Cuenta",
    hidden: "Importes ocultos",
    greenDays: "Días verdes",
    cap: {
      payout: e => `Payout recibido${e ? ` ${e}` : ""} 💸 Registrado con Sweep`,
      week: e => `Mi semana de trading${e ? `: ${e}` : ""}. Primero el proceso. Registrado con Sweep`,
      net: e => `Neto tras comisiones${e ? `: ${e}` : ""}. Cada payout, cada comisión, un solo historial. Registrado con Sweep`,
      trade: e => `Resumen de operación${e ? ` ${e}` : ""}. Registrado con Sweep`,
      day: e => `Hoy${e ? `: ${e}` : ""}. Registrado con Sweep`
    }
  }
}, SL = () => SHL[LANG] || SHL.en, SH_SITE = "makeitsweep.com";

function shLink(e) {
  const t = new URL("https://makeitsweep.com/" + (LANG === "en" ? "" : LANG + "/"));
  return t.searchParams.set("utm_source", "share"), t.searchParams.set("utm_medium", "card"), 
  t.searchParams.set("utm_campaign", e), S.me && S.me.username && t.searchParams.set("ref", S.me.username), 
  t.toString();
}

function shData(e, t) {
  const a = SL(), n = SH.amounts, s = SH.firm;
  if (e === "payout") {
    const i = getDoc("payouts", t);
    if (!i) return null;
    const o = S.payouts.filter(p => p.status === "paid").sort((p, u) => (p.payment_date || p.request_date || "").localeCompare(u.payment_date || u.request_date || "")), r = Math.max(1, o.findIndex(p => p.id === t) + 1 || o.length), c = o.reduce((p, u) => p + (u.net_c ?? u.amount_c ?? 0), 0), l = firm(i.firm_id || acct(i.account_id)?.firm_id);
    return {
      label: a.payout,
      eyebrow: [ o.length <= 1 ? a.first : a.payoutN(r), s && l ? l.name : null ].filter(Boolean).join(" · "),
      big: n ? moneyU(i.net_c ?? i.amount_c) : "✓ " + a.received,
      tone: "pos",
      sub: fdate(i.payment_date || i.request_date, {
        month: "long",
        day: "numeric",
        year: "numeric"
      }),
      stats: [ [ a.payouts, String(o.length) ], ...n ? [ [ a.lifetime, moneyU(c) ] ] : [], ...s && acct(i.account_id) ? [ [ a.account, acctName(i.account_id) ] ] : [] ].slice(0, 3),
      demo: !!(i.demo || acct(i.account_id)?.demo),
      chart: null,
      bars: o.length > 1 ? o.slice(-12).map(p => [ p.net_c ?? p.amount_c ?? 0, p.id === t ]) : null,
      mark: o.length <= 1,
      cap: a.cap.payout(n ? moneyU(i.net_c ?? i.amount_c) : "")
    };
  }
  if (e === "net") {
    const i = S.payouts.filter(m => m.status === "paid"), o = S.expenses, r = i.reduce((m, v) => m + (v.net_c ?? v.amount_c ?? 0), 0), c = o.reduce((m, v) => m + (v.amount_c || 0), 0), l = window.SweepMoney ? SweepMoney.moneyOf({}).real.net : r - c, p = [ ...i.map(m => [ m.paid_on || m.payment_date || m.request_date || "", m.net_c ?? m.amount_c ?? 0 ]), ...o.map(m => [ m.date || "", -(m.amount_c || 0) ]) ].filter(m => m[0]).sort((m, v) => m[0].localeCompare(v[0]));
    let u = 0;
    const h = p.map(m => u += m[1]);
    return {
      label: a.net,
      eyebrow: a.netSub,
      big: n ? money(l) : c ? (r / c).toFixed(1) + "×" : "—",
      tone: l >= 0 ? "pos" : "neg",
      sub: n ? null : a.ret,
      stats: n ? [ [ a.payouts, moneyU(r) ], [ a.fees, moneyU(c) ], [ a.ret, c ? (r / c).toFixed(1) + "×" : "—" ] ] : [ [ a.payouts, String(i.length) ], [ a.ret, c ? (r / c).toFixed(1) + "×" : "—" ] ],
      demo: i.some(m => m.demo) || o.some(m => m.demo),
      chart: h.length > 1 ? h : null,
      cap: a.cap.net(n ? money(l) : "")
    };
  }
  if (e === "week" || e === "day") {
    const i = e === "week" ? weekStart(t) : t, o = e === "week" ? addDays(i, 6) : t, r = mergeCopies(sorted(S.trades.filter(m => acctOK(m) && m.date >= i && m.date <= o)));
    if (!r.length) return null;
    const c = stats(r);
    let l = 0;
    const p = [ 0, ...r.map(m => l += tNet(m)) ], h = [ ...c.days.values() ].sort((m, v) => v.net - m.net)[0];
    return {
      label: e === "week" ? a.week : a.day,
      eyebrow: e === "week" ? a.weekOf(fdate(i, {
        month: "long",
        day: "numeric"
      })) : fdate(t, {
        weekday: "long",
        month: "long",
        day: "numeric"
      }),
      big: n ? money(c.net) : pct(c.wr),
      tone: c.net >= 0 ? "pos" : "neg",
      sub: n ? null : a.wr,
      stats: [ [ n ? a.wr : a.trades, n ? pct(c.wr) : String(c.n) ], [ n ? a.trades : a.greenDays, String(n ? c.n : c.winDays) ], [ a.disc, c.disc == null ? "—" : dpct(c.disc) ] ],
      demo: r.some(m => m.demo),
      chart: p.length > 2 ? p : null,
      cap: (e === "week" ? a.cap.week : a.cap.day)(n ? money(c.net) : "")
    };
  }
  if (e === "trade") {
    const i = getDoc("trades", t);
    if (!i) return null;
    const o = tNet(i), r = tR(i), c = tDur(i);
    return {
      label: a.trade,
      eyebrow: `${i.instrument || "NQ"} · ${i.direction === "long" ? "Long" : "Short"} · ${i.contracts}` + (s && acct(i.account_id) ? ` · ${firm(acct(i.account_id).firm_id)?.name || ""}` : ""),
      big: n ? money(o) : rfmt(r),
      tone: o >= 0 ? "pos" : "neg",
      sub: fdate(i.date, {
        weekday: "short",
        month: "long",
        day: "numeric"
      }) + (i.setup ? " · " + i.setup : ""),
      stats: [ [ n ? a.r : a.entry, n ? rfmt(r) : fpx(i.entry) ], [ n ? a.entry : a.exit, fpx(n ? i.entry : i.exit) ], [ a.dur, c == null ? "—" : fdur(c) ], [ a.disc, tDisc(i) == null ? "—" : dpct(tDisc(i)) ] ].slice(0, 4),
      demo: !!i.demo,
      chart: null,
      cap: a.cap.trade(n ? money(o) : rfmt(r))
    };
  }
  return null;
}

function shRound(e, t, a, n, s, i) {
  e.beginPath(), e.moveTo(t + i, a), e.arcTo(t + n, a, t + n, a + s, i), e.arcTo(t + n, a + s, t, a + s, i), 
  e.arcTo(t, a + s, t, a, i), e.arcTo(t, a, t + n, a, i), e.closePath();
}

function shFit(e, t, a, n, s, i) {
  let o = n;
  do {
    if (e.font = `${s} ${o}px ${i}`, e.measureText(t).width <= a) break;
    o -= 4;
  } while (o > 24);
  return o;
}

async function shDraw(e) {
  const [t, a] = SH_FORMATS[SH.fmt], n = document.createElement("canvas");
  n.width = t, n.height = a;
  const s = n.getContext("2d");
  try {
    await Promise.all([ document.fonts.load("500 120px Geist"), document.fonts.load("600 40px Geist"), document.fonts.load('500 120px "Geist Mono"') ]);
  } catch {}
  const i = 'Geist, -apple-system, "SF Pro Display", system-ui, sans-serif', o = '"Geist Mono", ui-monospace, "SF Mono", monospace', r = "#4C8DFF", c = "#D4A24C", l = "#0B0B0C", p = "#F2F2F3", u = "#9A9AA2", h = "#26262A", m = SH.fmt === "wide", v = SH.fmt === "story", b = m ? 64 : 84, E = e.tone === "neg" ? c : r;
  s.fillStyle = l, s.fillRect(0, 0, t, a);
  let R = s.createRadialGradient(t * .15, a * .05, 0, t * .15, a * .05, t * 1.1);
  R.addColorStop(0, "rgba(76,141,255,.20)"), R.addColorStop(.55, "rgba(76,141,255,.04)"), 
  R.addColorStop(1, "rgba(76,141,255,0)"), s.fillStyle = R, s.fillRect(0, 0, t, a), 
  R = s.createRadialGradient(t * .95, a * .95, 0, t * .95, a * .95, t * .8), R.addColorStop(0, e.tone === "neg" ? "rgba(212,162,76,.10)" : "rgba(76,141,255,.10)"), 
  R.addColorStop(1, "rgba(0,0,0,0)"), s.fillStyle = R, s.fillRect(0, 0, t, a), s.strokeStyle = "rgba(255,255,255,.035)", 
  s.lineWidth = 1;
  const L = m ? 56 : 60;
  for (let te = L; te < t; te += L) s.beginPath(), s.moveTo(te + .5, 0), s.lineTo(te + .5, a), 
  s.stroke();
  for (let te = L; te < a; te += L) s.beginPath(), s.moveTo(0, te + .5), s.lineTo(t, te + .5), 
  s.stroke();
  const x = m ? 54 : 64, C = b, g = b, P = x / 96;
  s.save(), s.translate(g - 40 * P, C - 8 * P), s.scale(P, P), s.lineCap = "round", 
  s.strokeStyle = p, s.fillStyle = p, s.lineWidth = 6, s.beginPath(), s.moveTo(60, 14), 
  s.lineTo(60, 30), s.stroke(), shRound(s, 46, 28, 28, 44, 5), s.fill(), s.lineCap = "butt", 
  s.beginPath(), s.moveTo(60, 70), s.lineTo(60, 84), s.stroke(), s.lineCap = "round", 
  s.strokeStyle = r, s.beginPath(), s.moveTo(60, 84), s.lineTo(60, 104), s.stroke(), 
  s.restore(), s.fillStyle = p, s.font = `500 ${m ? 40 : 46}px ${i}`, s.textBaseline = "middle", 
  s.letterSpacing = "-1.5px", s.fillText("sweep", g + 40 * P + 12, C + x / 2 + 2), 
  s.letterSpacing = "0px", s.font = `500 ${m ? 24 : 28}px ${i}`;
  const O = s.measureText(e.label).width + 44, H = m ? 48 : 56;
  if (shRound(s, t - b - O, C + (x - H) / 2, O, H, H / 2), s.fillStyle = e.tone === "neg" ? "rgba(212,162,76,.14)" : "rgba(76,141,255,.16)", 
  s.fill(), s.fillStyle = E, s.fillText(e.label, t - b - O + 22, C + x / 2 + 1), e.demo) {
    const te = {
      en: "Sample data",
      fr: "Données d'exemple",
      es: "Datos de ejemplo"
    }[LANG] || "Sample data";
    s.font = `600 ${m ? 20 : 24}px ${i}`;
    const re = s.measureText(te).width + 36, X = m ? 40 : 46, pe = C + x + (m ? 20 : 28);
    shRound(s, t - b - re, pe, re, X, X / 2), s.fillStyle = c, s.fill(), s.fillStyle = l, 
    s.textBaseline = "middle", s.fillText(te, t - b - re + 18, pe + X / 2 + 1);
  }
  const J = m ? 190 : v ? 520 : 330;
  s.textBaseline = "alphabetic", s.fillStyle = u, s.font = `500 ${m ? 30 : 36}px ${i}`, 
  s.fillText(e.eyebrow || "", b, J);
  const q = /^[+−\-$€\d]/.test(e.big), z = q ? o : i, Y = shFit(s, e.big, t - b * 2, m ? 150 : v ? 190 : 170, 500, z);
  s.fillStyle = E, s.font = `500 ${Y}px ${z}`, s.letterSpacing = q ? "-4px" : "-3px", 
  s.fillText(e.big, b - 6, J + Y * 1.02), s.letterSpacing = "0px";
  let Q = J + Y * 1.02;
  e.sub && (s.fillStyle = p, s.globalAlpha = .75, s.font = `400 ${m ? 30 : 36}px ${i}`, 
  s.fillText(e.sub, b, Q + (m ? 54 : 66)), s.globalAlpha = 1, Q += m ? 54 : 66);
  const me = m ? 96 : 120;
  if (e.chart && !m) {
    const te = b, re = t - b * 2, X = Q + 60, pe = (e.stats || []).length ? v ? a - me - 150 - 120 : a - me - 150 - 60 : a - me - 40, ue = Math.max(200, Math.min(v ? 760 : 420, pe - X - 70)), M = Math.min(0, ...e.chart), ne = Math.max(0, ...e.chart), k = ne - M || 1, A = B => te + B / (e.chart.length - 1) * re, j = B => X + ue - (B - M) / k * ue;
    s.strokeStyle = "rgba(255,255,255,.08)", s.setLineDash([ 6, 8 ]), s.beginPath(), 
    s.moveTo(te, j(0)), s.lineTo(te + re, j(0)), s.stroke(), s.setLineDash([]);
    const N = s.createLinearGradient(0, X, 0, X + ue);
    N.addColorStop(0, e.tone === "neg" ? "rgba(212,162,76,.28)" : "rgba(76,141,255,.30)"), 
    N.addColorStop(1, "rgba(0,0,0,0)"), s.beginPath(), e.chart.forEach((B, G) => G ? s.lineTo(A(G), j(B)) : s.moveTo(A(G), j(B))), 
    s.lineTo(A(e.chart.length - 1), X + ue), s.lineTo(te, X + ue), s.closePath(), s.fillStyle = N, 
    s.fill(), s.beginPath(), e.chart.forEach((B, G) => G ? s.lineTo(A(G), j(B)) : s.moveTo(A(G), j(B))), 
    s.strokeStyle = E, s.lineWidth = 5, s.lineJoin = "round", s.lineCap = "round", s.stroke(), 
    s.beginPath(), s.arc(A(e.chart.length - 1), j(e.chart.at(-1)), 10, 0, 7), s.fillStyle = E, 
    s.fill(), s.beginPath(), s.arc(A(e.chart.length - 1), j(e.chart.at(-1)), 20, 0, 7), 
    s.fillStyle = e.tone === "neg" ? "rgba(212,162,76,.22)" : "rgba(76,141,255,.25)", 
    s.fill(), Q = X + ue;
  }
  if (e.bars && e.bars.length && !m) {
    const te = b, re = t - b * 2, X = Q + (v ? 140 : 90), pe = v ? 380 : 200, ue = e.bars.length, M = ue > 8 ? 14 : 22, ne = Math.min(110, (re - M * (ue - 1)) / ue), k = Math.max(...e.bars.map(N => N[0])) || 1, A = ue * ne + (ue - 1) * M;
    let j = te + (re - A) / 2;
    for (const [N, B] of e.bars) {
      const G = Math.max(14, N / k * pe);
      if (shRound(s, j, X + pe - G, ne, G, Math.min(16, ne / 3)), B) {
        const Z = s.createLinearGradient(0, X + pe - G, 0, X + pe);
        Z.addColorStop(0, r), Z.addColorStop(1, "rgba(76,141,255,.35)"), s.fillStyle = Z;
      } else s.fillStyle = "rgba(255,255,255,.10)";
      s.fill(), j += ne + M;
    }
    Q = X + pe;
  }
  if (e.mark && !m) {
    const te = Q + (v ? 160 : 70), re = v ? 520 : 280, X = re / 96, pe = t / 2;
    s.save(), s.translate(pe - 60 * X, te - 8 * X), s.scale(X, X), s.lineCap = "round", 
    s.lineWidth = 6;
    const ue = s.createLinearGradient(0, 14, 0, 104);
    ue.addColorStop(0, "rgba(242,242,243,.16)"), ue.addColorStop(1, "rgba(242,242,243,.04)"), 
    s.strokeStyle = ue, s.fillStyle = ue, s.beginPath(), s.moveTo(60, 14), s.lineTo(60, 30), 
    s.stroke(), shRound(s, 46, 28, 28, 44, 5), s.fill(), s.lineCap = "butt", s.beginPath(), 
    s.moveTo(60, 70), s.lineTo(60, 84), s.stroke(), s.lineCap = "round", s.strokeStyle = r, 
    s.globalAlpha = .85, s.beginPath(), s.moveTo(60, 84), s.lineTo(60, 104), s.stroke(), 
    s.restore(), s.globalAlpha = 1, Q = te + re;
  }
  const oe = e.stats || [];
  if (oe.length) {
    const te = m ? 16 : 20, re = oe.length, X = (t - b * 2 - te * (re - 1)) / re, pe = m ? 120 : 150, ue = m ? a - me - pe - 36 : v ? a - me - pe - 120 : a - me - pe - 60;
    oe.forEach(([M, ne], k) => {
      const A = b + k * (X + te);
      shRound(s, A, ue, X, pe, 28), s.fillStyle = "rgba(255,255,255,.045)", s.fill(), 
      s.strokeStyle = "rgba(255,255,255,.07)", s.lineWidth = 2, s.stroke(), s.fillStyle = u, 
      s.font = `400 ${m ? 22 : 26}px ${i}`, s.fillText(M, A + 28, ue + (m ? 44 : 52));
      const j = /^[+−\-$\d—]/.test(ne) ? o : i, N = shFit(s, ne, X - 56, m ? 40 : 50, 500, j);
      s.fillStyle = p, s.font = `500 ${N}px ${j}`, s.fillText(ne, A + 28, ue + (m ? 92 : 114));
    });
  }
  const ae = a - b + (m ? 14 : 4);
  s.fillStyle = h, s.fillRect(b, ae - me + 24, t - b * 2, 2), s.fillStyle = p, s.font = `500 ${m ? 28 : 32}px ${i}`, 
  s.fillText(SL().track, b, ae - 6), s.fillStyle = r, s.font = `500 ${m ? 28 : 32}px ${i}`;
  const we = s.measureText(SH_SITE).width;
  return s.fillText(SH_SITE, t - b - we, ae - 6), s.fillStyle = u, s.font = `400 ${m ? 20 : 24}px ${i}`, 
  s.fillText("Sweep down. Jump up.", b, ae + (m ? 26 : 30)), n;
}

async function openShare(e, t) {
  SH.kind = e, SH.id = t, SH.blob = null;
  let a = $("#shPanel");
  if (!a) {
    a = document.createElement("aside"), a.id = "shPanel", a.className = "evp shp", 
    a.setAttribute("aria-label", SL().title), a.setAttribute("data-noi18n", ""), a.innerHTML = '<div class="evp-in sh-in"></div>', 
    document.body.append(a);
    const n = document.createElement("div");
    n.id = "shScrim", n.className = "evp-scrim", n.addEventListener("click", closeShare), 
    document.body.append(n), swipeDismiss(a, {
      scroller: () => a.querySelector(".evp-in"),
      onClose: closeShare,
      ignore: ".sh-fmt,.sh-tg"
    }), a.addEventListener("click", shClick), a.addEventListener("change", s => {
      const i = s.target;
      i.dataset.sh && (SH[i.dataset.sh] = i.checked, shRender());
    });
  }
  requestAnimationFrame(() => {
    a.classList.add("open"), $("#shScrim").classList.add("open"), document.body.classList.add("evp-lock");
  }), await shRender(), e === "payout" && confetti();
}

function closeShare() {
  const e = $("#shPanel");
  e && (e.classList.remove("open"), $("#shScrim").classList.remove("open"), document.body.classList.remove("evp-lock"), 
  SH.url && (URL.revokeObjectURL(SH.url), SH.url = null));
}

async function shRender() {
  const e = SL(), t = $("#shPanel .sh-in");
  if (!t) return;
  const a = shData(SH.kind, SH.id);
  if (!a) {
    t.innerHTML = '<div class="empty">—</div>';
    return;
  }
  t.innerHTML = `<div class="sh-head"><h2>${e.title}</h2><button class="ask-x" data-sh-act="close" aria-label="Close">✕</button></div>\n    <div class="sh-prev ${SH.fmt}"><div class="sh-skel"></div></div>\n    <div class="sh-fmt" role="tablist">${[ "post", "story", "wide" ].map(o => `<button data-sh-fmt="${o}" class="${SH.fmt === o ? "on" : ""}"><i class="r-${o}"></i>${e[o]}</button>`).join("")}</div>\n    <div class="sh-tg"><label><span>${e.amounts}</span><span class="sw"><input type="checkbox" data-sh="amounts" ${SH.amounts ? "checked" : ""}><i></i></span></label>\n      ${SH.kind !== "net" ? `<label><span>${e.firm}</span><span class="sw"><input type="checkbox" data-sh="firm" ${SH.firm ? "checked" : ""}><i></i></span></label>` : ""}</div>\n    <div class="sh-acts"><button class="btn primary sh-go" data-sh-act="share"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>${e.share}</button>\n      <button class="btn" data-sh-act="download">${e.download}</button><button class="btn" data-sh-act="copy">${e.copy}</button></div>`;
  const n = await shDraw(a), s = await new Promise(o => n.toBlob(o, "image/png"));
  SH.blob = s, SH.cap = a.cap + " → " + shLink(SH.kind), SH.url && URL.revokeObjectURL(SH.url), 
  SH.url = URL.createObjectURL(s);
  const i = t.querySelector(".sh-prev");
  i && (i.innerHTML = `<img src="${SH.url}" alt="${esc(a.label)}">`);
}

async function shClick(e) {
  const t = e.target.closest("[data-sh-fmt]");
  if (t) return SH.fmt = t.dataset.shFmt, shRender();
  const a = e.target.closest("[data-sh-act]");
  if (!a) return;
  const n = a.dataset.shAct, s = SL();
  if (n === "close") return closeShare();
  if (!SH.blob) return;
  const i = `sweep-${SH.kind}-${todayStr()}.png`;
  if (n === "share") {
    const o = new File([ SH.blob ], i, {
      type: "image/png"
    });
    if (navigator.canShare && navigator.canShare({
      files: [ o ]
    })) try {
      await navigator.share({
        files: [ o ],
        text: SH.cap,
        title: "Sweep"
      }), haptic(8);
      return;
    } catch (r) {
      if (r && r.name === "AbortError") return;
    }
    shSave(i);
    try {
      await navigator.clipboard.writeText(SH.cap), toast(s.saved + " · " + s.copied);
    } catch {
      toast(s.saved);
    }
    return;
  }
  if (n === "download") {
    shSave(i), toast(s.saved);
    return;
  }
  if (n === "copy") try {
    await navigator.clipboard.writeText(SH.cap), toast(s.copied);
  } catch {
    prompt(s.copy, SH.cap);
  }
}

function shSave(e) {
  const t = document.createElement("a");
  t.href = SH.url, t.download = e, document.body.append(t), t.click(), t.remove();
}

function confetti() {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const e = document.createElement("canvas");
  e.className = "confetti", e.width = innerWidth * devicePixelRatio, e.height = innerHeight * devicePixelRatio, 
  document.body.append(e);
  const t = e.getContext("2d");
  t.scale(devicePixelRatio, devicePixelRatio);
  const a = [ "#4C8DFF", "#F2F2F3", "#8FB6FF", "#2F6FE4" ], n = Array.from({
    length: 90
  }, () => ({
    x: innerWidth / 2 + (Math.random() - .5) * 80,
    y: innerHeight * .42,
    vx: (Math.random() - .5) * 11,
    vy: -Math.random() * 13 - 5,
    r: Math.random() * 6 + 4,
    c: a[Math.random() * a.length | 0],
    a: Math.random() * 6,
    va: (Math.random() - .5) * .3
  })), s = performance.now();
  (function i(o) {
    const r = o - s;
    t.clearRect(0, 0, innerWidth, innerHeight);
    for (const c of n) c.vy += .35, c.vx *= .99, c.x += c.vx, c.y += c.vy, c.a += c.va, 
    t.save(), t.translate(c.x, c.y), t.rotate(c.a), t.globalAlpha = Math.max(0, 1 - r / 1600), 
    t.fillStyle = c.c, t.fillRect(-c.r / 2, -c.r / 4, c.r, c.r / 2), t.restore();
    r < 1600 ? requestAnimationFrame(i) : e.remove();
  })(s), haptic(12);
}

document.addEventListener("keydown", e => {
  e.key === "Escape" && document.querySelector("#shPanel.open") && (e.stopPropagation(), 
  closeShare());
}, !0);

const shareBtn = (e, t, a, n = "btn sm") => `<button class="${n} sh-btn" data-act="share" data-k="${e}" data-id="${esc(t)}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 15V3M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>${a}</button>`;

(function() {
  "use strict";
  const e = {
    en: {
      plan_free: "Free",
      plan_pro: "Pro",
      plan_elite: "Elite",
      monthly: "Monthly",
      yearly: "Yearly",
      save: "Save {p}%",
      per_month: "/mo",
      per_year: "/yr",
      billed_yearly: "{a} billed yearly",
      most_popular: "Most popular",
      current: "Current plan",
      upgrade_to: "Upgrade to {plan}",
      claim: "Claim {plan} at 50% off",
      not_now: "Not now",
      compare: "Compare all plans",
      trust: "Cancel anytime. Your data is never deleted.",
      founding_strip: "Founding price: {p}% off for life. Ends in {t}.",
      founding_locked: "Founding price locked in for life",
      wait_reset: "Wait for the reset ({t})",
      redirecting: "Opening secure checkout…",
      error: "Checkout didn’t open. Check your connection and try again.",
      h_add_account: "Track every prop account in one place",
      s_add_account: "Free covers 1 account. Pro has no limit.",
      h_frozen_account: "This account is paused",
      s_frozen_account: "Its trades are safe and visible. Upgrade to log on all your accounts again.",
      h_payouts: "Know what your trading really pays",
      s_payouts: "Track payouts, evaluations, resets and fees, so you see your true profit.",
      h_payouts_n: "You’ve logged {amount} in payouts",
      s_payouts_n: "Keep tracking every dollar in and out with Pro.",
      h_analytics_history: "See your whole track record",
      s_analytics_history: "Free shows your last {d} days. Everything older is saved and unlocks with Pro.",
      h_ai_quota: "You’ve used today’s AI messages",
      s_ai_quota: "Free includes {n} a day. Pro gives you {m}.",
      h_ai_quota_pro: "You’ve used today’s AI messages",
      s_ai_quota_pro: "Elite gives you {m} a day.",
      h_ai_import: "Stop typing your trades",
      s_ai_import: "Drop a screenshot or statement and Sweep AI fills in the trades.",
      h_ai_review: "Get a coach’s eye on every trade",
      s_ai_review: "You’ve used this month’s AI reviews. Elite reviews every trade.",
      h_calendar_notes: "Know how news moves NQ",
      s_calendar_notes: "Elite shows full AI notes before and after every release.",
      h_weekly_report: "Your week, analyzed",
      s_weekly_report: "Elite writes a weekly report on your edge, leaks and habits.",
      h_green_week: "Strong week. Keep the momentum.",
      s_green_week: "Pro shows you exactly what’s working, across your full history.",
      h_trial_ending: "Your Pro access ends in {d}",
      s_trial_ending: "Keep unlimited accounts, payouts and full analytics.",
      h_trial_ended: "Your Pro trial ended",
      s_trial_ended: "Your data is safe. Upgrade to unlock it again.",
      h_founding: "Founding member price",
      s_founding: "You were here early. Get {p}% off Pro or Elite, for as long as you stay subscribed.",
      h_generic: "Unlock more of Sweep",
      s_generic: "Pick the plan that fits how you trade.",
      b_accounts: "Unlimited trading accounts",
      b_payouts: "Payouts and expenses tracking",
      b_analytics: "Full analytics on your whole history",
      b_ai_import: "AI import from screenshots and statements",
      b_ai_more: "{n} AI messages a day",
      b_reviews_3: "3 AI trade reviews a month",
      b_reviews_all: "AI review on every trade",
      b_calendar: "AI notes on every economic release",
      b_weekly: "Weekly AI performance report",
      b_support: "Priority support",
      bn_past_due: "Your last payment didn’t go through. Update your card to keep {plan}.",
      bn_update_card: "Update card",
      bn_trial: "{plan} access: {d} left",
      bn_see_plans: "See plans",
      bn_founding: "Founding price ends in {t}",
      bn_claim: "Claim 50% off",
      bn_trial_ended: "Your {plan} trial ended. Your data is safe.",
      bn_get_back: "Get {plan} back",
      bn_cancel: "{plan} ends on {date}",
      bn_keep: "Keep {plan}",
      unlock_with: "Unlock with {plan}",
      locked: "Locked",
      your_plan: "Your plan",
      manage: "Manage billing",
      renews: "Renews on {date}",
      ends_on: "Ends on {date}",
      trial_left: "{plan} trial: {d} left",
      early_left: "Early access {plan}: {d} left",
      free_desc: "Journal and core dashboard",
      f_accounts: "Trading accounts",
      f_trades: "Manual trades",
      f_history: "Analytics history",
      f_payouts: "Payouts and expenses",
      f_ai_daily: "Sweep AI messages",
      f_ai_import: "AI import",
      f_ai_reviews: "AI trade reviews",
      f_calendar: "Economic calendar notes",
      f_weekly: "Weekly AI report",
      f_support: "Priority support",
      unlimited: "Unlimited",
      days: "{n} days",
      per_day: "{n} a day",
      per_month_n: "{n} a month",
      preview: "Headlines",
      full: "Full notes",
      included: "Included",
      not_included: "Not included",
      all_trades: "Unlimited",
      welcome_title: "You’re on {plan}",
      welcome_text: "Everything is unlocked. Thanks for backing Sweep.",
      welcome_cta: "Let’s go",
      pending_title: "Payment received",
      pending_text: "Your plan will update in a moment. Refresh if it doesn’t.",
      choose_title: "Choose your active account",
      choose_text: "Free includes 1 active account. The others stay saved and visible, and unlock again with Pro.",
      choose_cta: "Keep this one active",
      choose_upsell: "Keep all accounts active with Pro",
      d1: "1 day",
      dn: "{n} days",
      h1: "1 hour",
      hn: "{n} hours",
      in_t: "in {t}"
    },
    fr: {
      plan_free: "Gratuit",
      plan_pro: "Pro",
      plan_elite: "Elite",
      monthly: "Mensuel",
      yearly: "Annuel",
      save: "−{p} %",
      per_month: "/mois",
      per_year: "/an",
      billed_yearly: "{a} facturé annuellement",
      most_popular: "Le plus populaire",
      current: "Abonnement actuel",
      upgrade_to: "Passer à {plan}",
      claim: "Obtenir {plan} à 50 % de rabais",
      not_now: "Plus tard",
      compare: "Comparer les abonnements",
      trust: "Annule quand tu veux. Tes données ne sont jamais supprimées.",
      founding_strip: "Prix fondateur : {p} % de rabais à vie. Se termine dans {t}.",
      founding_locked: "Prix fondateur garanti à vie",
      wait_reset: "Attendre la remise à zéro ({t})",
      redirecting: "Ouverture du paiement sécurisé…",
      error: "Le paiement ne s’est pas ouvert. Vérifie ta connexion et réessaie.",
      h_add_account: "Tous tes comptes prop au même endroit",
      s_add_account: "Gratuit inclut 1 compte. Pro n’a aucune limite.",
      h_frozen_account: "Ce compte est en pause",
      s_frozen_account: "Ses trades sont conservés et visibles. Passe à Pro pour enregistrer sur tous tes comptes.",
      h_payouts: "Sache ce que ton trading rapporte vraiment",
      s_payouts: "Suis tes payouts, évaluations, resets et frais pour voir ton vrai profit.",
      h_payouts_n: "Tu as enregistré {amount} en payouts",
      s_payouts_n: "Continue de suivre chaque dollar avec Pro.",
      h_analytics_history: "Vois tout ton historique",
      s_analytics_history: "Gratuit montre tes {d} derniers jours. Le reste est conservé et se débloque avec Pro.",
      h_ai_quota: "Tu as utilisé tes messages IA du jour",
      s_ai_quota: "Gratuit en inclut {n} par jour. Pro t’en donne {m}.",
      h_ai_quota_pro: "Tu as utilisé tes messages IA du jour",
      s_ai_quota_pro: "Elite t’en donne {m} par jour.",
      h_ai_import: "Arrête de taper tes trades",
      s_ai_import: "Dépose une capture ou un relevé et Sweep AI remplit les trades.",
      h_ai_review: "Un œil de coach sur chaque trade",
      s_ai_review: "Tu as utilisé tes revues IA du mois. Elite analyse chaque trade.",
      h_calendar_notes: "Comprends comment les nouvelles font bouger le NQ",
      s_calendar_notes: "Elite affiche les notes IA complètes avant et après chaque annonce.",
      h_weekly_report: "Ta semaine, analysée",
      s_weekly_report: "Elite rédige un rapport hebdo sur ton edge, tes fuites et tes habitudes.",
      h_green_week: "Belle semaine. Garde l’élan.",
      s_green_week: "Pro te montre exactement ce qui fonctionne, sur tout ton historique.",
      h_trial_ending: "Ton accès Pro se termine dans {d}",
      s_trial_ending: "Garde les comptes illimités, les payouts et les analyses complètes.",
      h_trial_ended: "Ton essai Pro est terminé",
      s_trial_ended: "Tes données sont en sécurité. Passe à Pro pour les débloquer.",
      h_founding: "Prix membre fondateur",
      s_founding: "Tu étais là tôt. Obtiens {p} % de rabais sur Pro ou Elite, tant que tu restes abonné.",
      h_generic: "Débloque plus de Sweep",
      s_generic: "Choisis le abonnement qui correspond à ta façon de trader.",
      b_accounts: "Comptes de trading illimités",
      b_payouts: "Suivi des payouts et des dépenses",
      b_analytics: "Analyses complètes sur tout ton historique",
      b_ai_import: "Import IA depuis captures et relevés",
      b_ai_more: "{n} messages IA par jour",
      b_reviews_3: "3 revues IA de trades par mois",
      b_reviews_all: "Revue IA de chaque trade",
      b_calendar: "Notes IA sur chaque annonce économique",
      b_weekly: "Rapport de performance IA hebdomadaire",
      b_support: "Soutien prioritaire",
      bn_past_due: "Ton dernier paiement n’a pas passé. Mets ta carte à jour pour garder {plan}.",
      bn_update_card: "Mettre à jour",
      bn_trial: "Accès {plan} : {d} restants",
      bn_see_plans: "Voir les abonnements",
      bn_founding: "Le prix fondateur se termine dans {t}",
      bn_claim: "Obtenir 50 % de rabais",
      bn_trial_ended: "Ton essai {plan} est terminé. Tes données sont en sécurité.",
      bn_get_back: "Retrouver {plan}",
      bn_cancel: "{plan} se termine le {date}",
      bn_keep: "Garder {plan}",
      unlock_with: "Débloquer avec {plan}",
      locked: "Verrouillé",
      your_plan: "Ton abonnement",
      manage: "Gérer la facturation",
      renews: "Renouvellement le {date}",
      ends_on: "Se termine le {date}",
      trial_left: "Essai {plan} : {d} restants",
      early_left: "Accès anticipé {plan} : {d} restants",
      free_desc: "Journal et tableau de bord de base",
      f_accounts: "Comptes de trading",
      f_trades: "Trades manuels",
      f_history: "Historique des analyses",
      f_payouts: "Payouts et dépenses",
      f_ai_daily: "Messages Sweep AI",
      f_ai_import: "Import IA",
      f_ai_reviews: "Revues IA de trades",
      f_calendar: "Notes du calendrier économique",
      f_weekly: "Rapport IA hebdomadaire",
      f_support: "Soutien prioritaire",
      unlimited: "Illimité",
      days: "{n} jours",
      per_day: "{n} par jour",
      per_month_n: "{n} par mois",
      preview: "Titres",
      full: "Notes complètes",
      included: "Inclus",
      not_included: "Non inclus",
      all_trades: "Illimités",
      welcome_title: "Tu es sur {plan}",
      welcome_text: "Tout est débloqué. Merci de soutenir Sweep.",
      welcome_cta: "C’est parti",
      pending_title: "Paiement reçu",
      pending_text: "Ton abonnement sera mis à jour dans un instant. Rafraîchis si ce n’est pas le cas.",
      choose_title: "Choisis ton compte actif",
      choose_text: "Gratuit inclut 1 compte actif. Les autres restent sauvegardés et visibles, et se débloquent avec Pro.",
      choose_cta: "Garder ce compte actif",
      choose_upsell: "Garder tous mes comptes actifs avec Pro",
      d1: "1 jour",
      dn: "{n} jours",
      h1: "1 heure",
      hn: "{n} heures",
      in_t: "dans {t}"
    },
    es: {
      plan_free: "Gratis",
      plan_pro: "Pro",
      plan_elite: "Elite",
      monthly: "Mensual",
      yearly: "Anual",
      save: "−{p} %",
      per_month: "/mes",
      per_year: "/año",
      billed_yearly: "{a} facturado al año",
      most_popular: "El más popular",
      current: "Suscripción actual",
      upgrade_to: "Pasar a {plan}",
      claim: "Obtener {plan} con 50 % de descuento",
      not_now: "Ahora no",
      compare: "Comparar suscripciones",
      trust: "Cancela cuando quieras. Tus datos nunca se borran.",
      founding_strip: "Precio fundador: {p} % de descuento de por vida. Termina en {t}.",
      founding_locked: "Precio fundador asegurado de por vida",
      wait_reset: "Esperar al reinicio ({t})",
      redirecting: "Abriendo el pago seguro…",
      error: "El pago no se abrió. Revisa tu conexión e inténtalo de nuevo.",
      h_add_account: "Todas tus cuentas de fondeo en un solo lugar",
      s_add_account: "Gratis incluye 1 cuenta. Pro no tiene límite.",
      h_frozen_account: "Esta cuenta está en pausa",
      s_frozen_account: "Sus trades están guardados y visibles. Pasa a Pro para registrar en todas tus cuentas.",
      h_payouts: "Descubre lo que tu trading paga de verdad",
      s_payouts: "Registra payouts, evaluaciones, resets y comisiones para ver tu ganancia real.",
      h_payouts_n: "Has registrado {amount} en payouts",
      s_payouts_n: "Sigue cada dólar que entra y sale con Pro.",
      h_analytics_history: "Ve todo tu historial",
      s_analytics_history: "Gratis muestra tus últimos {d} días. Lo anterior está guardado y se desbloquea con Pro.",
      h_ai_quota: "Usaste tus mensajes de IA de hoy",
      s_ai_quota: "Gratis incluye {n} al día. Pro te da {m}.",
      h_ai_quota_pro: "Usaste tus mensajes de IA de hoy",
      s_ai_quota_pro: "Elite te da {m} al día.",
      h_ai_import: "Deja de escribir tus trades",
      s_ai_import: "Sube una captura o un estado de cuenta y Sweep AI rellena los trades.",
      h_ai_review: "Un ojo de coach en cada trade",
      s_ai_review: "Usaste las revisiones de IA del mes. Elite revisa cada trade.",
      h_calendar_notes: "Entiende cómo las noticias mueven el NQ",
      s_calendar_notes: "Elite muestra notas de IA completas antes y después de cada dato.",
      h_weekly_report: "Tu semana, analizada",
      s_weekly_report: "Elite escribe un informe semanal sobre tu ventaja, tus fugas y tus hábitos.",
      h_green_week: "Gran semana. Mantén el ritmo.",
      s_green_week: "Pro te muestra exactamente qué funciona, en todo tu historial.",
      h_trial_ending: "Tu acceso Pro termina en {d}",
      s_trial_ending: "Conserva cuentas ilimitadas, payouts y análisis completos.",
      h_trial_ended: "Tu prueba Pro terminó",
      s_trial_ended: "Tus datos están a salvo. Pasa a Pro para desbloquearlos.",
      h_founding: "Precio de miembro fundador",
      s_founding: "Llegaste temprano. Obtén {p} % de descuento en Pro o Elite mientras sigas suscrito.",
      h_generic: "Desbloquea más de Sweep",
      s_generic: "Elige el plan que encaja con tu forma de operar.",
      b_accounts: "Cuentas de trading ilimitadas",
      b_payouts: "Seguimiento de payouts y gastos",
      b_analytics: "Análisis completos de todo tu historial",
      b_ai_import: "Importación con IA desde capturas y estados",
      b_ai_more: "{n} mensajes de IA al día",
      b_reviews_3: "3 revisiones de IA al mes",
      b_reviews_all: "Revisión de IA en cada trade",
      b_calendar: "Notas de IA en cada dato económico",
      b_weekly: "Informe semanal de rendimiento con IA",
      b_support: "Soporte prioritario",
      bn_past_due: "Tu último pago no se procesó. Actualiza tu tarjeta para mantener {plan}.",
      bn_update_card: "Actualizar tarjeta",
      bn_trial: "Acceso {plan}: quedan {d}",
      bn_see_plans: "Ver suscripciones",
      bn_founding: "El precio fundador termina en {t}",
      bn_claim: "Obtener 50 % de descuento",
      bn_trial_ended: "Tu prueba {plan} terminó. Tus datos están a salvo.",
      bn_get_back: "Recuperar {plan}",
      bn_cancel: "{plan} termina el {date}",
      bn_keep: "Mantener {plan}",
      unlock_with: "Desbloquear con {plan}",
      locked: "Bloqueado",
      your_plan: "Tu plan",
      manage: "Gestionar facturación",
      renews: "Se renueva el {date}",
      ends_on: "Termina el {date}",
      trial_left: "Prueba {plan}: quedan {d}",
      early_left: "Acceso anticipado {plan}: quedan {d}",
      free_desc: "Diario y panel básico",
      f_accounts: "Cuentas de trading",
      f_trades: "Trades manuales",
      f_history: "Historial de análisis",
      f_payouts: "Payouts y gastos",
      f_ai_daily: "Mensajes de Sweep AI",
      f_ai_import: "Importación con IA",
      f_ai_reviews: "Revisiones de IA",
      f_calendar: "Notas del calendario económico",
      f_weekly: "Informe semanal con IA",
      f_support: "Soporte prioritario",
      unlimited: "Ilimitado",
      days: "{n} días",
      per_day: "{n} al día",
      per_month_n: "{n} al mes",
      preview: "Titulares",
      full: "Notas completas",
      included: "Incluido",
      not_included: "No incluido",
      all_trades: "Ilimitados",
      welcome_title: "Ya tienes {plan}",
      welcome_text: "Todo está desbloqueado. Gracias por apoyar Sweep.",
      welcome_cta: "Vamos",
      pending_title: "Pago recibido",
      pending_text: "Tu plan se actualizará en un momento. Recarga si no cambia.",
      choose_title: "Elige tu cuenta activa",
      choose_text: "Gratis incluye 1 cuenta activa. Las demás quedan guardadas y visibles, y se desbloquean con Pro.",
      choose_cta: "Mantener esta cuenta activa",
      choose_upsell: "Mantener todas mis cuentas activas con Pro",
      d1: "1 día",
      dn: "{n} días",
      h1: "1 hora",
      hn: "{n} horas",
      in_t: "en {t}"
    }
  }, t = {
    add_account: {
      plan: "pro",
      b: [ "b_accounts", "b_payouts", "b_analytics" ]
    },
    frozen_account: {
      plan: "pro",
      b: [ "b_accounts", "b_payouts", "b_analytics" ]
    },
    payouts: {
      plan: "pro",
      b: [ "b_payouts", "b_accounts", "b_analytics" ]
    },
    analytics_history: {
      plan: "pro",
      b: [ "b_analytics", "b_accounts", "b_payouts" ]
    },
    ai_quota: {
      plan: "pro",
      b: [ "b_ai_more", "b_ai_import", "b_analytics" ]
    },
    ai_import: {
      plan: "pro",
      b: [ "b_ai_import", "b_ai_more", "b_accounts" ]
    },
    ai_review: {
      plan: "elite",
      b: [ "b_reviews_all", "b_weekly", "b_calendar" ]
    },
    calendar_notes: {
      plan: "elite",
      b: [ "b_calendar", "b_reviews_all", "b_weekly" ]
    },
    weekly_report: {
      plan: "elite",
      b: [ "b_weekly", "b_reviews_all", "b_calendar" ]
    },
    green_week: {
      plan: "pro",
      b: [ "b_analytics", "b_accounts", "b_payouts" ]
    },
    trial_ending: {
      plan: "pro",
      b: [ "b_accounts", "b_payouts", "b_analytics" ]
    },
    trial_ended: {
      plan: "pro",
      b: [ "b_accounts", "b_payouts", "b_analytics" ]
    },
    founding: {
      plan: "pro",
      b: [ "b_accounts", "b_payouts", "b_analytics" ]
    },
    generic: {
      plan: "pro",
      b: [ "b_accounts", "b_payouts", "b_analytics" ]
    }
  }, a = {
    pro: [ "b_accounts", "b_payouts", "b_analytics", "b_ai_import", "b_ai_more", "b_reviews_3" ],
    elite: [ "b_reviews_all", "b_calendar", "b_weekly", "b_ai_more", "b_support", "b_accounts" ]
  }, n = {
    accounts: "add_account",
    payouts: "payouts",
    ai_import: "ai_import",
    ai_daily: "ai_quota",
    ai_reviews: "ai_review",
    calendar_notes: "calendar_notes",
    weekly_report: "weekly_report",
    analytics_days: "analytics_history"
  }, s = {
    url: k => "?r=" + encodeURIComponent(k),
    lang: "en",
    navigate: null,
    accounts: null,
    onChange: null,
    request: null
  };
  let i = null, o = !1, r = null;
  const c = () => e[s.lang] ? s.lang : "en";
  function l(k, A) {
    let j = e[c()][k] ?? e.en[k] ?? k;
    if (A) for (const [N, B] of Object.entries(A)) j = j.split("{" + N + "}").join(String(B));
    return j;
  }
  const p = k => l("plan_" + k), u = k => String(k).replace(/[&<>"']/g, A => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[A])), h = {
    get(k) {
      try {
        return sessionStorage.getItem(k);
      } catch {
        return null;
      }
    },
    set(k, A) {
      try {
        sessionStorage.setItem(k, A);
      } catch {}
    }
  }, m = {
    get(k) {
      try {
        return localStorage.getItem(k);
      } catch {
        return null;
      }
    },
    set(k, A) {
      try {
        localStorage.setItem(k, A);
      } catch {}
    }
  };
  function v(k, A) {
    const j = Math.abs(k % 1) < .005;
    try {
      return new Intl.NumberFormat(c() === "en" ? "en-US" : c() === "fr" ? "fr-CA" : "es", {
        style: "currency",
        currency: A || i && i.currency || "USD",
        currencyDisplay: "narrowSymbol",
        minimumFractionDigits: j ? 0 : 2,
        maximumFractionDigits: j ? 0 : 2
      }).format(k);
    } catch {
      return "$" + (j ? Math.round(k) : k.toFixed(2));
    }
  }
  function b(k) {
    try {
      return new Date(k).toLocaleDateString(c() === "fr" ? "fr-CA" : c(), {
        month: "long",
        day: "numeric"
      });
    } catch {
      return k;
    }
  }
  function E(k) {
    const A = new Date(k).getTime() - Date.now();
    if (!(A > 0)) return l("hn", {
      n: 0
    });
    const j = Math.floor(A / 864e5), N = Math.floor(A % 864e5 / 36e5), B = Math.floor(A % 36e5 / 6e4);
    return j >= 2 ? l("dn", {
      n: j
    }) : j === 1 ? l("d1") + (N ? " " + (N === 1 ? l("h1") : l("hn", {
      n: N
    })) : "") : N >= 1 ? N === 1 ? l("h1") : l("hn", {
      n: N
    }) : B + " min";
  }
  const R = k => k <= 1 ? l("d1") : l("dn", {
    n: k
  });
  async function L(k, A) {
    if (s.request) return s.request(k, A ? {
      method: "POST",
      body: A
    } : {
      method: "GET"
    });
    const j = await fetch(s.url(k), {
      method: A ? "POST" : "GET",
      credentials: "same-origin",
      headers: A ? {
        "Content-Type": "application/json",
        Accept: "application/json"
      } : {
        Accept: "application/json"
      },
      body: A ? JSON.stringify(A) : void 0
    }), N = await j.json().catch(() => ({}));
    if (!j.ok) {
      const B = new Error(N.error || "HTTP " + j.status);
      throw B.data = N, B;
    }
    return N;
  }
  function x(k, A, j) {
    L("api/billing/upsell", {
      trigger: k,
      action: A,
      blocking: !!j
    }).then(N => {
      i && N && typeof N.blocking_left == "number" && (i.paywall.blocking_left = N.blocking_left);
    }).catch(() => {});
  }
  async function C() {
    try {
      i = await L("api/billing/me"), document.documentElement.dataset.plan = i.plan, s.onChange && s.onChange(i), 
      window.dispatchEvent(new CustomEvent("sweep:billing", {
        detail: i
      })), M();
    } catch {}
    return i;
  }
  const g = () => i && i.limits || {};
  function P(k) {
    if (!i || !i.live) return !0;
    const A = g()[k];
    return typeof A == "boolean" ? A : A == null ? !0 : typeof A == "number" ? A > 0 : A === "full";
  }
  const O = k => i ? g()[k] : null;
  function H() {
    const k = i && i.live ? g().analytics_days : null;
    return k ? new Date(Date.now() - k * 864e5) : null;
  }
  function J(k) {
    return !!(i && i.accounts && i.accounts.frozen.includes(String(k)));
  }
  function q(k, A, j) {
    if (k === "accounts") {
      const N = O("accounts"), B = j && typeof j.count == "number" ? j.count : i && i.accounts ? i.accounts.active.length + i.accounts.frozen.length : 0;
      if (!i || !i.live || N === null || N === void 0 || B < N) return !0;
    } else if (P(k)) return !0;
    return oe(A || n[k] || "generic", j), !1;
  }
  function z(k, A) {
    const j = k && (k.data || k);
    if (!j || j.code !== "upgrade_required") return !1;
    let N = j.trigger || n[j.feature] || "generic";
    return j.feature === "ai_daily" && (N = "ai_quota"), oe(N, Object.assign({
      resetAt: j.reset_at,
      recommend: j.upgrade_to
    }, A || {})), !0;
  }
  function Y(k, {onClose: A, label: j} = {}) {
    r && r.close(!0);
    const N = document.activeElement, B = document.createElement("div");
    B.className = "sb-layer", B.setAttribute("data-noi18n", ""), B.innerHTML = '<div class="sb-backdrop"></div><div class="sb-sheet" role="dialog" aria-modal="true" tabindex="-1"><div class="sb-grab" aria-hidden="true"></div><div class="sb-body"></div></div>';
    const G = B.querySelector(".sb-sheet");
    j && G.setAttribute("aria-label", j), B.querySelector(".sb-body").appendChild(k), 
    document.body.appendChild(B), document.documentElement.classList.add("sb-lock"), 
    requestAnimationFrame(() => B.classList.add("sb-in"));
    let Z = !1;
    function ge(ee) {
      if (Z) return;
      Z = !0, B.classList.remove("sb-in"), B.classList.add("sb-out"), document.removeEventListener("keydown", Te), 
      window.removeEventListener("pointermove", de), window.removeEventListener("pointerup", se), 
      window.removeEventListener("pointercancel", se);
      const fe = () => {
        B.remove(), document.querySelector(".sb-layer") || document.documentElement.classList.remove("sb-lock");
      };
      if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches ? fe() : setTimeout(fe, 260), 
      r && r.root === B && (r = null), !ee && A && A(), N && N.focus) try {
        N.focus();
      } catch {}
    }
    function Te(ee) {
      if (ee.key === "Escape" && ge(), ee.key === "Tab") {
        const fe = G.querySelectorAll('button,[href],input,[tabindex]:not([tabindex="-1"])');
        if (!fe.length) return;
        ee.shiftKey && document.activeElement === fe[0] ? (ee.preventDefault(), fe[fe.length - 1].focus()) : !ee.shiftKey && document.activeElement === fe[fe.length - 1] && (ee.preventDefault(), 
        fe[0].focus());
      }
    }
    document.addEventListener("keydown", Te), B.querySelector(".sb-backdrop").addEventListener("click", () => ge());
    let ye = null, ie = 0;
    G.addEventListener("pointerdown", ee => {
      const fe = B.querySelector(".sb-body");
      ee.target.closest("button,a,input,label") || fe.scrollTop > 0 || (ye = ee.clientY, 
      ie = 0, G.style.transition = "none");
    });
    function de(ee) {
      ye !== null && (ie = Math.max(0, ee.clientY - ye), G.style.transform = "translateY(" + ie + "px)");
    }
    window.addEventListener("pointermove", de);
    function se() {
      ye !== null && (ye = null, G.style.transition = "", G.style.transform = "", ie > 110 && ge());
    }
    return window.addEventListener("pointerup", se), window.addEventListener("pointercancel", se), 
    setTimeout(() => G.focus({
      preventScroll: !0
    }), 60), r = {
      root: B,
      close: ge
    }, r;
  }
  function Q(k, A) {
    const j = i && i.plans || {}, N = j.free || {}, B = j.pro || {}, G = j.elite || {}, Z = t[k] ? k : "generic";
    if (Z === "payouts" && A && A.payoutTotal > 0) return [ l("h_payouts_n", {
      amount: v(A.payoutTotal)
    }), l("s_payouts_n") ];
    if (Z === "ai_quota" && i && i.plan === "pro") return [ l("h_ai_quota_pro"), l("s_ai_quota_pro", {
      m: G.ai_daily
    }) ];
    const ge = i && i.trial ? R(i.trial.days_left) : "";
    return [ l("h_" + Z, {
      d: ge
    }), l("s_" + Z, {
      n: N.ai_daily,
      m: B.ai_daily,
      d: N.analytics_days,
      p: i ? i.founding.percent : 50
    }) ];
  }
  function me(k, A) {
    const j = i && i.plans && i.plans[A] || {};
    return l(k, {
      n: j.ai_daily
    });
  }
  function oe(k, A) {
    if (A = A || {}, !i || !i.live || i.plan === "elite" && !i.trial) return null;
    const j = !!A.unprompted;
    if (j) {
      if (o || h.get("sb_shown") || i.paywall && i.paywall.blocking_left <= 0) return null;
      o = !0, h.set("sb_shown", "1");
    }
    const N = t[k] ? k : "generic";
    let B = A.recommend || t[N].plan;
    i.plan === "pro" && (B = "elite");
    let G = "year";
    const Z = i.plan === "pro" ? [ "elite" ] : [ "pro", "elite" ], [ge, Te] = Q(N, A), ye = i.founding, ie = document.createElement("div");
    ie.className = "sb-pw";
    function de(he, be) {
      const _e = (i.prices[he] || {})[be] || {
        amount: 0
      };
      return {
        full: _e.amount,
        now: _e.founding ?? _e.amount
      };
    }
    function se() {
      const he = de(B, "month").full, be = de(B, "year").full;
      return he ? Math.round((1 - be / (he * 12)) * 100) : 0;
    }
    function ee() {
      const he = Z.map($e => {
        const ve = de($e, G), Se = G === "year" ? ve.now / 12 : ve.now, Ae = $e === B;
        return '<button type="button" class="sb-opt' + (Ae ? " sb-sel" : "") + '" data-plan="' + $e + '" role="radio" aria-checked="' + Ae + '"><span class="sb-opt-l"><span class="sb-radio" aria-hidden="true"></span><span class="sb-opt-name">' + u(p($e)) + ($e === "pro" && Z.length > 1 ? '<span class="sb-tag">' + u(l("most_popular")) + "</span>" : "") + '</span></span><span class="sb-opt-r"><span class="sb-price">' + (ve.now !== ve.full ? "<s>" + u(v(G === "year" ? ve.full / 12 : ve.full)) + "</s> " : "") + "<b>" + u(v(Math.round(Se * 100) / 100)) + "</b><small>" + u(l("per_month")) + "</small></span>" + (G === "year" ? '<span class="sb-sub">' + u(l("billed_yearly", {
          a: v(ve.now)
        })) + "</span>" : "") + "</span></button>";
      }).join(""), be = B === t[N].plan ? t[N].b : a[B].slice(0, 3), _e = N === "ai_quota" && A.resetAt ? l("wait_reset", {
        t: E(A.resetAt)
      }) : l("not_now");
      ie.innerHTML = '<h2 class="sb-h">' + u(ge) + '</h2><p class="sb-p">' + u(Te) + "</p>" + (ye.eligible ? '<p class="sb-founding">' + u(l("founding_strip", {
        p: ye.percent,
        t: E(ye.deadline)
      })) + "</p>" : "") + '<div class="sb-seg" role="tablist"><button type="button" role="tab" data-iv="month" aria-selected="' + (G === "month") + '">' + u(l("monthly")) + '</button><button type="button" role="tab" data-iv="year" aria-selected="' + (G === "year") + '">' + u(l("yearly")) + " <em>" + u(l("save", {
        p: se()
      })) + '</em></button></div><div class="sb-opts" role="radiogroup">' + he + '</div><ul class="sb-bens">' + be.map($e => "<li>" + u(me($e, B)) + "</li>").join("") + '</ul><button type="button" class="sb-cta">' + u(ye.eligible ? l("claim", {
        plan: p(B)
      }) : l("upgrade_to", {
        plan: p(B)
      })) + '</button><p class="sb-trust">' + u(l("trust")) + '</p><p class="sb-err" role="alert" hidden></p><div class="sb-foot"><button type="button" class="sb-link sb-later">' + u(_e) + "</button>" + (s.navigate ? '<button type="button" class="sb-link sb-compare">' + u(l("compare")) + "</button>" : "") + "</div>";
    }
    ee();
    let fe = !1;
    const ke = Y(ie, {
      label: ge,
      onClose: () => {
        fe || x(N, "dismissed", j);
      }
    });
    return ie.addEventListener("click", async he => {
      const be = he.target.closest(".sb-seg [data-iv]"), _e = he.target.closest(".sb-opt[data-plan]");
      if (be) {
        G = be.dataset.iv, ee();
        return;
      }
      if (_e) {
        B = _e.dataset.plan, ee();
        return;
      }
      if (he.target.closest(".sb-later")) {
        ke.close();
        return;
      }
      if (he.target.closest(".sb-compare")) {
        ke.close(), s.navigate("plans");
        return;
      }
      const $e = he.target.closest(".sb-cta");
      if ($e) {
        fe = !0, x(N, "clicked", j), $e.disabled = !0, $e.textContent = l("redirecting");
        try {
          const ve = await L("api/billing/checkout", {
            plan: B,
            interval: G,
            trigger: N
          });
          if (ve.url) {
            window.location.href = ve.url;
            return;
          }
          throw new Error("no url");
        } catch (ve) {
          fe = !1, $e.disabled = !1, $e.textContent = ye.eligible ? l("claim", {
            plan: p(B)
          }) : l("upgrade_to", {
            plan: p(B)
          });
          const Se = ie.querySelector(".sb-err");
          Se.hidden = !1, Se.textContent = l("error") + (ve && ve.data && ve.data.detail ? " — " + ve.data.detail : "");
        }
      }
    }), x(N, "shown", j), ke;
  }
  function ae(k, A) {
    if (!i || !i.live || i.plan !== "free" && !i.trial || i.plan === "elite") return null;
    const j = (new Date).toISOString().slice(0, 10);
    if (m.get("sb_nudge") === j) return null;
    m.set("sb_nudge", j);
    const [N, B] = Q(k, A), G = document.createElement("div");
    G.className = "sb-nudge", G.setAttribute("role", "status"), G.setAttribute("data-noi18n", ""), 
    G.innerHTML = "<div><b>" + u(N) + "</b><span>" + u(B) + '</span></div><button type="button" class="sb-nudge-go">' + u(l("upgrade_to", {
      plan: p(t[k] ? t[k].plan : "pro")
    })) + '</button><button type="button" class="sb-x" aria-label="' + u(l("not_now")) + '">×</button>', 
    document.body.appendChild(G), requestAnimationFrame(() => G.classList.add("sb-in"));
    const Z = () => {
      G.classList.remove("sb-in"), setTimeout(() => G.remove(), 300);
    };
    return G.querySelector(".sb-x").onclick = () => {
      x(k, "dismissed", !1), Z();
    }, G.querySelector(".sb-nudge-go").onclick = () => {
      Z(), oe(k, A);
    }, setTimeout(Z, 12e3), x(k, "shown", !1), G;
  }
  function we(k) {
    if (!k || (k.innerHTML = "", !i || !i.live)) return null;
    let A = "", j = "", N = null, B = "";
    const G = i.subscription;
    if (G && G.status === "past_due" ? (A = l("bn_past_due", {
      plan: p(G.plan)
    }), j = l("bn_update_card"), N = pe, B = "warn") : i.trial && i.trial.days_left <= 5 && !G ? (A = l("bn_trial", {
      plan: p(i.trial.plan),
      d: R(i.trial.days_left)
    }), j = l("bn_see_plans"), N = () => oe("trial_ending")) : i.founding.eligible ? (A = l("bn_founding", {
      t: E(i.founding.deadline)
    }), j = l("bn_claim"), N = () => oe("founding")) : i.trial_ended && Date.now() - new Date(i.trial_ended.ended_at).getTime() < 14 * 864e5 ? (A = l("bn_trial_ended", {
      plan: p(i.trial_ended.plan)
    }), j = l("bn_get_back", {
      plan: p(i.trial_ended.plan)
    }), N = () => oe("trial_ended")) : G && G.cancel_at_period_end && G.period_end && (A = l("bn_cancel", {
      plan: p(G.plan),
      date: b(G.period_end)
    }), j = l("bn_keep", {
      plan: p(G.plan)
    }), N = pe), !A) return null;
    const Z = document.createElement("div");
    return Z.className = "sb-banner" + (B ? " sb-" + B : ""), Z.setAttribute("data-noi18n", ""), 
    Z.innerHTML = "<span>" + u(A) + '</span><button type="button">' + u(j) + "</button>", 
    Z.querySelector("button").onclick = N, k.appendChild(Z), Z;
  }
  function te(k, A, j) {
    if (!k || (re(k), !i || !i.live)) return;
    const N = t[A] ? A : "generic";
    let B = j && j.recommend || t[N].plan;
    i.plan === "pro" && (B = "elite"), k.classList.add("sb-locked");
    const G = document.createElement("div");
    G.className = "sb-lockover", G.setAttribute("data-noi18n", ""), G.innerHTML = '<button type="button"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 7V5a3 3 0 0 1 6 0v2h.5A1.5 1.5 0 0 1 13 8.5v5a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 3 13.5v-5A1.5 1.5 0 0 1 4.5 7H5Zm1.5 0h3V5a1.5 1.5 0 0 0-3 0v2Z"/></svg>' + u(l("unlock_with", {
      plan: p(B)
    })) + "</button>", G.querySelector("button").onclick = () => oe(N, Object.assign({
      recommend: B
    }, j || {})), k.appendChild(G);
  }
  function re(k) {
    k && (k.classList.remove("sb-locked"), k.querySelectorAll(":scope > .sb-lockover").forEach(A => A.remove()));
  }
  function X(k) {
    return P(k) ? "" : '<span class="sb-badge" data-noi18n aria-label=""' + u(l("locked")) + '"><svg viewBox="0 0 16 16"><path d="M5 7V5a3 3 0 0 1 6 0v2h.5A1.5 1.5 0 0 1 13 8.5v5a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 3 13.5v-5A1.5 1.5 0 0 1 4.5 7H5Zm1.5 0h3V5a1.5 1.5 0 0 0-3 0v2Z"/></svg></span>';
  }
  async function pe() {
    try {
      const k = await L("api/billing/portal", {});
      k.url && (window.location.href = k.url);
    } catch {
      alert(l("error"));
    }
  }
  function ue(k) {
    if (!k || !i) return;
    k.setAttribute("data-noi18n", "");
    let A = "year";
    const j = i.plans, N = i.founding, B = (ie, de) => de === "bool" ? ie ? '<span class="sb-yes" aria-label="' + u(l("included")) + '">✓</span>' : '<span class="sb-no" aria-label="' + u(l("not_included")) + '">–</span>' : ie == null ? u(l("unlimited")) : u(de === "days" ? l("days", {
      n: ie
    }) : de === "day" ? l("per_day", {
      n: ie
    }) : de === "month" ? l("per_month_n", {
      n: ie
    }) : de === "notes" ? l(ie) : String(ie)), G = [ [ "f_accounts", "accounts", "" ], [ "f_trades", null, "trades" ], [ "f_history", "analytics_days", "days" ], [ "f_payouts", "payouts", "bool" ], [ "f_ai_daily", "ai_daily", "day" ], [ "f_ai_import", "ai_import", "bool" ], [ "f_ai_reviews", "ai_reviews", "month" ], [ "f_calendar", "calendar_notes", "notes" ], [ "f_weekly", "weekly_report", "bool" ], [ "f_support", "priority_support", "bool" ] ];
    function Z() {
      const ie = i.subscription;
      return ie ? (ie.cancel_at_period_end ? l("ends_on", {
        date: b(ie.period_end)
      }) : ie.period_end ? l("renews", {
        date: b(ie.period_end)
      }) : "") + (ie.founding ? ' <span class="sb-chip">' + u(l("founding_locked")) + "</span>" : "") : i.trial ? u(l(i.trial.kind === "early_access" ? "early_left" : "trial_left", {
        plan: p(i.trial.plan),
        d: R(i.trial.days_left)
      })) : u(l("free_desc"));
    }
    const ge = () => window.matchMedia && window.matchMedia("(max-width: 640px)").matches;
    function Te() {
      return '<div class="sb-pcards">' + (i.plan === "elite" ? [ "elite", "pro", "free" ] : i.plan === "pro" ? [ "elite", "pro", "free" ] : [ "pro", "elite", "free" ]).map(de => {
        const se = (i.prices[de] || {})[A], ee = se ? se.founding ?? se.amount : 0, fe = se ? se.amount : 0, ke = A === "year" ? ee / 12 : ee, he = i.plan === de, be = de === "pro" && i.plan === "free";
        let _e = "";
        de !== "free" && !he && (i.plan === "free" || de === "elite") && (_e = '<button type="button" class="sb-cta" data-buy="' + de + '">' + u(N.eligible ? l("claim", {
          plan: p(de)
        }) : l("upgrade_to", {
          plan: p(de)
        })) + "</button>");
        const $e = de === "free" ? "<b>" + u(v(0)) + "</b>" : (se && se.founding !== null && se.founding !== void 0 ? "<s>" + u(v(A === "year" ? fe / 12 : fe)) + "</s>" : "") + "<b>" + u(v(Math.round(ke * 100) / 100)) + "</b>", ve = G.map(([Se, Ae, Le]) => {
          const Me = Le === "trades" ? null : j[de][Ae], d = Le === "bool" ? !Me : !1, f = Le === "trades" ? u(l("all_trades")) : Le === "bool" ? "" : B(Me, Le);
          return '<li class="' + (d ? "sb-off" : "") + '"><i aria-hidden="true">' + (d ? "–" : "✓") + "</i><span>" + u(l(Se)) + "</span>" + (f ? "<b>" + f + "</b>" : "") + "</li>";
        }).join("");
        return '<article class="sb-pcard' + (be ? " sb-hl" : "") + (he ? " sb-curcard" : "") + '"><header><span class="sb-pc-name">' + u(p(de)) + "</span>" + (be ? '<span class="sb-tag">' + u(l("most_popular")) + "</span>" : "") + (he ? '<span class="sb-cur">' + u(l("current")) + "</span>" : "") + '</header><div class="sb-pc-price">' + $e + "<small>" + u(l("per_month")) + "</small></div>" + (de !== "free" && A === "year" ? '<div class="sb-pc-sub">' + u(l("billed_yearly", {
          a: v(ee)
        })) + "</div>" : '<div class="sb-pc-sub">&nbsp;</div>') + _e + '<ul class="sb-pc-feats">' + ve + "</ul></article>";
      }).join("") + "</div>";
    }
    function ye() {
      const ie = [ "free", "pro", "elite" ].map(se => {
        const ee = (i.prices[se] || {})[A], fe = ee ? ee.founding ?? ee.amount : 0, ke = A === "year" ? fe / 12 : fe, he = i.plan === se;
        let be = "";
        return se !== "free" && !he && (i.plan === "free" || se === "elite") && (be = '<button type="button" class="sb-cta sb-sm" data-buy="' + se + '">' + u(l("upgrade_to", {
          plan: p(se)
        })) + "</button>"), he && (be = '<span class="sb-cur">' + u(l("current")) + "</span>"), 
        '<th scope="col"' + (se === "pro" ? ' class="sb-hl"' : "") + '><span class="sb-th-name">' + u(p(se)) + '</span><span class="sb-th-price">' + (se === "free" ? u(v(0)) : (ee && ee.founding !== null && ee.founding !== void 0 ? "<s>" + u(v(A === "year" ? ee.amount / 12 : ee.amount)) + "</s> " : "") + u(v(Math.round(ke * 100) / 100))) + "<small>" + u(l("per_month")) + "</small></span>" + be + "</th>";
      }).join(""), de = G.map(([se, ee, fe]) => '<tr><th scope="row">' + u(l(se)) + "</th>" + [ "free", "pro", "elite" ].map(ke => "<td" + (ke === "pro" ? ' class="sb-hl"' : "") + ">" + (fe === "trades" ? u(l("all_trades")) : B(j[ke][ee], fe)) + "</td>").join("") + "</tr>").join("");
      k.innerHTML = '<section class="sb-plans"><div class="sb-card"><div><span class="sb-label">' + u(l("your_plan")) + '</span><b class="sb-big">' + u(p(i.plan)) + '</b><span class="sb-status">' + Z() + "</span></div>" + (i.can_manage && i.subscription ? '<button type="button" class="sb-btn2 sb-manage">' + u(l("manage")) + "</button>" : "") + "</div>" + (N.eligible ? '<p class="sb-founding">' + u(l("founding_strip", {
        p: N.percent,
        t: E(N.deadline)
      })) + "</p>" : "") + '<div class="sb-seg" role="tablist"><button type="button" role="tab" data-iv="month" aria-selected="' + (A === "month") + '">' + u(l("monthly")) + '</button><button type="button" role="tab" data-iv="year" aria-selected="' + (A === "year") + '">' + u(l("yearly")) + " <em>" + u(l("save", {
        p: (() => {
          const se = ((i.prices.pro || {}).month || {}).amount, ee = ((i.prices.pro || {}).year || {}).amount;
          return se && ee ? Math.round((1 - ee / (se * 12)) * 100) : 0;
        })()
      })) + "</em></button></div>" + (ge() ? Te() : '<div class="sb-tablewrap"><table class="sb-table"><thead><tr><td></td>' + ie + "</tr></thead><tbody>" + de + "</tbody></table></div>") + '<p class="sb-trust">' + u(l("trust")) + "</p></section>";
    }
    ye();
    try {
      const ie = window.matchMedia("(max-width: 640px)");
      ie.onchange = () => {
        k.isConnected && ye();
      };
    } catch {}
    k.onclick = async ie => {
      const de = ie.target.closest("[data-iv]");
      if (de) {
        A = de.dataset.iv, ye();
        return;
      }
      if (ie.target.closest(".sb-manage")) {
        pe();
        return;
      }
      const se = ie.target.closest("[data-buy]");
      if (se) {
        x("plans_page", "clicked", !1), se.disabled = !0, se.textContent = l("redirecting");
        try {
          const ee = await L("api/billing/checkout", {
            plan: se.dataset.buy,
            interval: A,
            trigger: "plans_page"
          });
          ee.url && (window.location.href = ee.url);
        } catch (ee) {
          se.disabled = !1, se.textContent = l("upgrade_to", {
            plan: p(se.dataset.buy)
          }), alert(l("error") + (ee && ee.data && ee.data.detail ? `\n\n` + ee.data.detail : ""));
        }
      }
    };
  }
  async function M(k) {
    if (!i || !i.live || !i.accounts || !i.accounts.frozen.length || !k && (!i.accounts.needs_choice || h.get("sb_choose"))) return;
    h.set("sb_choose", "1");
    const A = s.accounts ? await s.accounts() : [ ...i.accounts.active, ...i.accounts.frozen ].map(Z => ({
      id: Z,
      name: Z
    }));
    let j = i.accounts.active[0];
    const N = document.createElement("div");
    N.className = "sb-pw";
    function B() {
      N.innerHTML = '<h2 class="sb-h">' + u(l("choose_title")) + '</h2><p class="sb-p">' + u(l("choose_text")) + '</p><div class="sb-opts" role="radiogroup">' + A.map(Z => '<button type="button" class="sb-opt' + (String(Z.id) === String(j) ? " sb-sel" : "") + '" role="radio" aria-checked="' + (String(Z.id) === String(j)) + '" data-acc="' + u(Z.id) + '"><span class="sb-opt-l"><span class="sb-radio"></span><span class="sb-opt-name">' + u(Z.name || Z.id) + "</span></span></button>").join("") + '</div><button type="button" class="sb-cta">' + u(l("choose_cta")) + '</button><div class="sb-foot"><button type="button" class="sb-link sb-up">' + u(l("choose_upsell")) + "</button></div>";
    }
    B();
    const G = Y(N, {
      label: l("choose_title")
    });
    N.addEventListener("click", async Z => {
      const ge = Z.target.closest("[data-acc]");
      if (ge) {
        j = ge.dataset.acc, B();
        return;
      }
      if (Z.target.closest(".sb-up")) {
        G.close(), oe("frozen_account");
        return;
      }
      if (Z.target.closest(".sb-cta")) {
        try {
          i.accounts = await L("api/billing/active-accounts", {
            ids: [ j ]
          });
        } catch {}
        G.close(), s.onChange && s.onChange(i);
      }
    });
  }
  async function ne() {
    let k;
    try {
      k = new URLSearchParams(location.search);
    } catch {
      return;
    }
    const A = k.get("billing");
    if (!A) return;
    k.delete("billing"), k.delete("plan");
    const j = location.pathname + (k.toString() ? "?" + k : "") + location.hash;
    try {
      history.replaceState(null, "", j);
    } catch {}
    if (A !== "success") {
      A === "portal" && C();
      return;
    }
    for (let Z = 0; Z < 8 && (await C(), !(i && i.subscription)); Z++) await new Promise(ge => setTimeout(ge, 1500));
    const N = i && i.subscription, B = document.createElement("div");
    B.className = "sb-pw sb-done", B.innerHTML = '<div class="sb-check" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></div><h2 class="sb-h">' + u(N ? l("welcome_title", {
      plan: p(i.subscription.plan)
    }) : l("pending_title")) + '</h2><p class="sb-p">' + u(l(N ? "welcome_text" : "pending_text")) + '</p><button type="button" class="sb-cta">' + u(l("welcome_cta")) + "</button>";
    const G = Y(B);
    B.querySelector(".sb-cta").onclick = () => G.close();
  }
  window.SweepBilling = {
    init(k) {
      return Object.assign(s, k || {}), C().then(() => ne());
    },
    refresh: C,
    setLang(k) {
      s.lang = k;
    },
    state: () => i,
    plan: () => i ? i.plan : null,
    can: P,
    limit: O,
    gate: q,
    handleApiError: z,
    usage: k => i && i.usage ? i.usage[k] : null,
    isFrozen: J,
    historyCutoff: H,
    paywall: oe,
    nudge: ae,
    renderBanner: we,
    lock: te,
    unlock: re,
    badge: X,
    renderPlans: ue,
    portal: pe,
    chooseAccounts: () => M(!0),
    _t: l
  };
})();

const BILL = {
  ready: !1,
  on: !1,
  st: null,
  off: !0
};

async function billRequest(e, {method: t, body: a} = {}) {
  const n = await fetch(e, {
    method: t || "GET",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "fetch",
      ...a ? {
        "Content-Type": "application/json"
      } : {}
    },
    body: a ? JSON.stringify(a) : void 0
  }), s = await n.json().catch(() => ({}));
  if (!n.ok) {
    const i = new Error(s.error || "HTTP " + n.status);
    throw i.data = s, i.status = n.status, i;
  }
  return s;
}

function billInit() {
  BILL.ready || S.mode !== "server" || !window.SweepBilling || (BILL.ready = !0, SweepBilling.init({
    url: e => e,
    lang: LANG,
    request: billRequest,
    navigate: e => {
      e === "plans" && (location.hash = "#plan");
    },
    accounts: async () => S.accounts.filter(e => !e.demo).map(e => ({
      id: e.id,
      name: acctLabel(e.id)
    })),
    onChange: e => {
      BILL.st = e, BILL.off = !e || !!e.off, BILL.on = !!(e && e.live && !e.off), document.body.classList.toggle("bill-live", BILL.on), 
      scheduleRender();
    }
  }).then(() => {
    const e = SweepBilling.state();
    e && e.live && e.trial && e.trial.days_left <= 3 && !e.subscription && setTimeout(() => SweepBilling.paywall("trial_ending", {
      unprompted: !0
    }), 1200);
  }).catch(() => {}));
}

const billLive = () => BILL.on, billCan = e => !BILL.on || !window.SweepBilling || SweepBilling.can(e), billFrozen = e => BILL.on && window.SweepBilling && SweepBilling.isFrozen(e);

function billGate(e, t, a) {
  return !BILL.on || !window.SweepBilling || SweepBilling.gate(e, t, a);
}

function billPayoutTotal() {
  return S.payouts.filter(e => e.status === "paid" && !e.demo).reduce((e, t) => e + (t.amount_c || 0), 0) / 100;
}

function billRealAccounts() {
  return S.accounts.filter(e => !e.demo);
}

function billDecorate() {
  if (!window.SweepBilling || S.mode !== "server") return;
  billChrome();
  const e = document.getElementById("billBanner");
  e && SweepBilling.renderBanner(e);
  const t = document.getElementById("planRoot");
  t && !t.dataset.done && (t.dataset.done = "1", SweepBilling.renderPlans(t)), BILL.on && document.querySelectorAll("[data-lock]").forEach(a => {
    const n = a.dataset.feature || a.dataset.lock;
    a.dataset.force === "1" || !SweepBilling.can(n) ? a.classList.contains("sb-locked") || SweepBilling.lock(a, a.dataset.lock, {
      payoutTotal: billPayoutTotal()
    }) : SweepBilling.unlock(a);
  });
}

function billNudge(e) {
  BILL.on && e > 0 && window.SweepBilling && setTimeout(() => SweepBilling.nudge("green_week"), 1500);
}

function billBadge(e) {
  return billFrozen(e) ? '<span class="frz" aria-label="Paused"><svg viewBox="0 0 16 16"><path d="M5 7V5a3 3 0 0 1 6 0v2h.5A1.5 1.5 0 0 1 13 8.5v5a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 3 13.5v-5A1.5 1.5 0 0 1 4.5 7H5Zm1.5 0h3V5a1.5 1.5 0 0 0-3 0v2Z"/></svg></span>' : "";
}

document.addEventListener("click", e => {
  if (e.target.closest("[data-frozen]") && BILL.on) {
    e.preventDefault(), e.stopPropagation(), SweepBilling.paywall("frozen_account");
    return;
  }
}, !0);

function billOld(e) {
  if (!BILL.on || !window.SweepBilling) return !1;
  const t = SweepBilling.historyCutoff();
  if (!t) return !1;
  const a = t.toISOString().slice(0, 10);
  return e < a && S.trades.some(n => !n.demo && n.date < a && acctOK(n));
}

function vPlan() {
  return S.mode !== "server" ? '<div class="empty">Plans are available in your Sweep account.</div>' : BILL.off && BILL.ready && BILL.st ? `<div class="empty">Subscriptions aren't available yet. Everything is included during early access.</div>` : `<div id="planRoot" class="plan-root"><div class="boot"><div class="skel"></div><div class="skel t"></div></div></div>${S.me && S.me.is_admin ? billDiagBlock() : ""}`;
}

function planSettings() {
  if (S.mode !== "server" || BILL.off || !BILL.st) return "";
  const e = BILL.st, t = {
    free: "Free",
    pro: "Pro",
    elite: "Elite"
  }[e.plan] || e.plan, a = {
    en: [ "Plan", e.live ? `You're on ${t}.` : "Early access: every feature is included until launch.", "Plans & billing" ],
    fr: [ "Abonnement", e.live ? `Tu es sur ${t}.` : "Accès anticipé : toutes les fonctions sont incluses jusqu'au lancement.", "Abonnements et facturation" ],
    es: [ "Plan", e.live ? `Estás en ${t}.` : "Acceso anticipado: todas las funciones están incluidas hasta el lanzamiento.", "Planes y facturación" ]
  }[LANG];
  return `<section class="sec" data-noi18n><div class="sec-h"><h2>${a[0]}</h2></div><div class="surface pad row plan-row"><span class="plan-chip p-${esc(e.plan)}">${esc(t)}</span><span class="muted">${a[1]}</span><a class="btn sm" href="#plan" style="margin-left:auto">${a[2]}</a></div></section>`;
}

const BDG = {
  res: null,
  busy: !1
};

function billDiagBlock() {
  const e = {
    en: [ "Stripe setup check", "Only you see this. It checks billing-config.php and your Stripe account, item by item.", "Run the check", "Checking…" ],
    fr: [ "Vérification de Stripe", "Toi seul vois ceci. Ça vérifie billing-config.php et ton compte Stripe, élément par élément.", "Lancer la vérification", "Vérification…" ],
    es: [ "Comprobación de Stripe", "Solo tú ves esto. Revisa billing-config.php y tu cuenta de Stripe, punto por punto.", "Comprobar", "Comprobando…" ]
  }[LANG], t = (BDG.res || []).map(a => `<li class="${a.ok ? "ok" : "ko"}"><i>${a.ok ? "✓" : "✕"}</i><div><b>${esc(a.label)}</b><span>${esc(a.detail || "")}</span></div></li>`).join("");
  return `<section class="sec bdiag" data-noi18n><div class="sec-h"><h2>${e[0]}</h2></div><div class="surface pad"><p class="muted" style="margin:0 0 12px">${e[1]}</p>\n    <button class="btn" data-act="bill-diag" ${BDG.busy ? "disabled" : ""}>${BDG.busy ? e[3] : e[2]}</button>${t ? `<ul class="bdiag-list">${t}</ul>` : ""}</div></section>`;
}

async function billDiag() {
  BDG.busy = !0, render();
  try {
    const e = await billRequest("api/billing/diag");
    BDG.res = e.checks || [];
  } catch (e) {
    BDG.res = [ {
      label: "Billing",
      ok: !1,
      detail: e.data && (e.data.detail || e.data.error) || e.message
    } ];
  }
  BDG.busy = !1, render();
}

new MutationObserver(e => {
  for (const t of e) for (const a of t.addedNodes) if (a.nodeType === 1 && a.querySelector && a.querySelector(".sb-done") && BILL.st && BILL.st.subscription) {
    setTimeout(() => typeof confetti == "function" && confetti(), 350);
    return;
  }
}).observe(document.body, {
  childList: !0
});

function billChrome() {
  const e = BILL.st, t = BILL.on && e;
  document.querySelectorAll(".who").forEach(n => {
    let s = n.querySelector(".plan-tag");
    t && e.plan !== "free" ? (s || (s = document.createElement("a"), s.className = "plan-tag", 
    s.href = "#plan", n.insertBefore(s, n.children[1] || null)), s.textContent = {
      pro: "Pro",
      elite: "Elite"
    }[e.plan] || e.plan, s.className = "plan-tag p-" + e.plan) : s && s.remove();
  });
  const a = document.getElementById("moreUpgrade");
  if (a) {
    const n = t && e.plan !== "elite";
    a.hidden = !n, n && (a.querySelector("span:last-child").textContent = {
      en: `Upgrade to ${e.plan === "pro" ? "Elite" : "Pro"}`,
      fr: `Passer à ${e.plan === "pro" ? "Elite" : "Pro"}`,
      es: `Pasar a ${e.plan === "pro" ? "Elite" : "Pro"}`
    }[LANG]);
  }
}

const REF_T = {
  fr: {
    title: "Parrainage",
    headline: "Invite un ami. Vous gagnez tous les deux.",
    lead: "Ton ami reçoit {d} jours d’Elite à son inscription. Toi, tu gagnes un mois gratuit dès qu’il utilise Sweep pour vrai.",
    candles: [ "{n} mois gagné sur {max} possibles cette année", "{n} mois gagnés sur {max} possibles cette année" ],
    bonus: "Pro gratuit jusqu’au {date}",
    copy: "Copier",
    copied: "Lien copié",
    share: "Partager mon lien",
    yourCode: "Ton code",
    shareText: "Je t’invite sur Sweep pour suivre ton trading et ton vrai P&L. Inscris-toi avec mon lien et reçois {d} jours d’Elite gratuits.",
    how: "Comment ça marche",
    steps: [ "Partage ton lien avec un ami trader.", "Il s’inscrit et reçoit {d} jours d’Elite.", "Quand il a ajouté {t} trades sur {k} jours différents, ou qu’il prend un abonnement payant, tu gagnes un mois." ],
    invites: "Tes invitations",
    summary: function(e) {
      return e.invited + (e.invited > 1 ? " invités, " : " invité, ") + e.pending + " en cours, " + e.validated + (e.validated > 1 ? " validés" : " validé");
    },
    empty: "Aucune invitation pour l’instant. Partage ton lien pour commencer.",
    joined: "Inscrit le {date}",
    progress: "{t}/{T} trades, {k}/{K} jours, {r} j restants",
    status: {
      pending: "En cours",
      qualified: "Validé",
      rewarded: "+1 mois",
      expired: "Expiré"
    },
    terms: "Conditions du programme",
    close: "Fermer",
    termsList: [ "Tu gagnes un mois gratuit pour chaque ami qui s’inscrit avec ton lien et qui, dans les {w} jours suivant son inscription, ajoute au moins {t} trades sur {k} jours différents ou prend un abonnement payant.", "Si tu as un abonnement payant, le mois est appliqué en crédit sur ta prochaine facture. Sinon, tu reçois un mois de Pro gratuit.", "Ton ami reçoit {d} jours d’Elite gratuits à son inscription.", "Maximum {max} mois gagnés par période de 12 mois.", "Tu ne peux pas te parrainer toi-même. Les comptes créés uniquement pour profiter du programme sont refusés.", "Les mois gagnés n’ont aucune valeur monétaire et ne peuvent pas être échangés contre de l’argent.", "Sweep peut modifier ou arrêter le programme en tout temps. Les mois déjà gagnés restent acquis." ],
    error: "Impossible de charger tes invitations. Réessaie dans un instant."
  },
  en: {
    title: "Referrals",
    headline: "Invite a friend. You both win.",
    lead: "Your friend gets {d} days of Elite when they sign up. You get a free month once they start using Sweep for real.",
    candles: [ "{n} month earned of {max} possible this year", "{n} months earned of {max} possible this year" ],
    bonus: "Free Pro until {date}",
    copy: "Copy",
    copied: "Link copied",
    share: "Share my link",
    yourCode: "Your code",
    shareText: "Join me on Sweep to track your trading and your real P&L. Sign up with my link and get {d} days of Elite free.",
    how: "How it works",
    steps: [ "Share your link with a trader friend.", "They sign up and get {d} days of Elite.", "Once they log {t} trades on {k} different days, or start a paid plan, you get a month." ],
    invites: "Your invites",
    summary: function(e) {
      return e.invited + " invited, " + e.pending + " in progress, " + e.validated + " confirmed";
    },
    empty: "No invites yet. Share your link to get started.",
    joined: "Joined {date}",
    progress: "{t}/{T} trades, {k}/{K} days, {r} days left",
    status: {
      pending: "In progress",
      qualified: "Confirmed",
      rewarded: "+1 month",
      expired: "Expired"
    },
    terms: "Program terms",
    close: "Close",
    termsList: [ "You earn a free month for each friend who signs up with your link and, within {w} days of signing up, logs at least {t} trades on {k} different days or starts a paid plan.", "If you’re on a paid plan, the month is applied as a credit on your next invoice. Otherwise, you get a free month of Pro.", "Your friend gets {d} days of Elite free when they sign up.", "Up to {max} months earned per 12-month period.", "You can’t refer yourself. Accounts created only to use the program are rejected.", "Earned months have no cash value and can’t be exchanged for money.", "Sweep may change or end the program at any time. Months already earned are kept." ],
    error: "Couldn’t load your invites. Try again in a moment."
  },
  es: {
    title: "Referidos",
    headline: "Invita a un amigo. Ganan los dos.",
    lead: "Tu amigo recibe {d} días de Elite al registrarse. Tú ganas un mes gratis cuando empiece a usar Sweep de verdad.",
    candles: [ "{n} mes ganado de {max} posibles este año", "{n} meses ganados de {max} posibles este año" ],
    bonus: "Pro gratis hasta el {date}",
    copy: "Copiar",
    copied: "Enlace copiado",
    share: "Compartir mi enlace",
    yourCode: "Tu código",
    shareText: "Te invito a Sweep para seguir tu trading y tu P&L real. Regístrate con mi enlace y recibe {d} días de Elite gratis.",
    how: "Cómo funciona",
    steps: [ "Comparte tu enlace con un amigo trader.", "Se registra y recibe {d} días de Elite.", "Cuando registre {t} trades en {k} días distintos, o tome un plan de pago, ganas un mes." ],
    invites: "Tus invitaciones",
    summary: function(e) {
      return e.invited + (e.invited === 1 ? " invitado, " : " invitados, ") + e.pending + " en curso, " + e.validated + (e.validated === 1 ? " validado" : " validados");
    },
    empty: "Aún no tienes invitaciones. Comparte tu enlace para empezar.",
    joined: "Se registró el {date}",
    progress: "{t}/{T} trades, {k}/{K} días, quedan {r} días",
    status: {
      pending: "En curso",
      qualified: "Validado",
      rewarded: "+1 mes",
      expired: "Vencido"
    },
    terms: "Condiciones del programa",
    close: "Cerrar",
    termsList: [ "Ganas un mes gratis por cada amigo que se registre con tu enlace y que, en los {w} días siguientes a su registro, registre al menos {t} trades en {k} días distintos o tome un plan de pago.", "Si tienes un plan de pago, el mes se aplica como crédito en tu próxima factura. Si no, recibes un mes de Pro gratis.", "Tu amigo recibe {d} días de Elite gratis al registrarse.", "Máximo {max} meses ganados por periodo de 12 meses.", "No puedes referirte a ti mismo. Las cuentas creadas solo para aprovechar el programa se rechazan.", "Los meses ganados no tienen valor monetario y no se pueden cambiar por dinero.", "Sweep puede modificar o terminar el programa en cualquier momento. Los meses ya ganados se conservan." ],
    error: "No se pudieron cargar tus invitaciones. Inténtalo de nuevo en un momento."
  }
}, FB_T = {
  fr: {
    title: "Feedback",
    lead: "Ton avis façonne Sweep. On lit chaque message.",
    t_experience: "Expérience",
    t_idea: "Idée",
    t_bug: "Bug",
    rateQ: "Comment se passe ton expérience avec Sweep ?",
    rates: [ "Mauvaise", "Bof", "Correcte", "Bonne", "Excellente" ],
    label: {
      experience: "Raconte-nous",
      idea: "Ton idée",
      bug: "Ce qui ne marche pas"
    },
    ph: {
      experience: "Ce que tu aimes, ce qui te frustre, ce qui t’aide dans ton trading…",
      idea: "Une fonction, un écran, une stat qui te manque…",
      bug: "Ce que tu faisais, ce qui s’est passé, ce que tu attendais…"
    },
    attach: "Ajouter une capture",
    send: "Envoyer",
    sent: "Merci, c’est envoyé",
    mine: "Tes envois",
    empty: "Tu n’as encore rien envoyé.",
    status: {
      new: "Reçu",
      planned: "Prévu",
      in_progress: "En cours",
      shipped: "Livré",
      declined: "Pas pour l’instant"
    },
    reply: "Réponse de l’équipe Sweep",
    errors: {
      limit: "Tu as atteint la limite d’envois pour aujourd’hui. Réessaie demain.",
      file: "La capture doit être une image PNG, JPG ou WebP de 5 Mo maximum.",
      invalid: "Écris un message avant d’envoyer.",
      server: "L’envoi n’a pas fonctionné. Réessaie dans un instant."
    }
  },
  en: {
    title: "Feedback",
    lead: "Your input shapes Sweep. We read every message.",
    t_experience: "Experience",
    t_idea: "Idea",
    t_bug: "Bug",
    rateQ: "How is your experience with Sweep?",
    rates: [ "Bad", "Meh", "Okay", "Good", "Great" ],
    label: {
      experience: "Tell us more",
      idea: "Your idea",
      bug: "What isn’t working"
    },
    ph: {
      experience: "What you like, what frustrates you, what helps your trading…",
      idea: "A feature, a screen, a stat you’re missing…",
      bug: "What you were doing, what happened, what you expected…"
    },
    attach: "Add a screenshot",
    send: "Send",
    sent: "Thanks, it’s sent",
    mine: "Your submissions",
    empty: "You haven’t sent anything yet.",
    status: {
      new: "Received",
      planned: "Planned",
      in_progress: "In progress",
      shipped: "Shipped",
      declined: "Not for now"
    },
    reply: "Reply from the Sweep team",
    errors: {
      limit: "You’ve reached today’s limit. Try again tomorrow.",
      file: "The screenshot must be a PNG, JPG or WebP image up to 5 MB.",
      invalid: "Write a message before sending.",
      server: "Sending didn’t work. Try again in a moment."
    }
  },
  es: {
    title: "Comentarios",
    lead: "Tu opinión da forma a Sweep. Leemos cada mensaje.",
    t_experience: "Experiencia",
    t_idea: "Idea",
    t_bug: "Error",
    rateQ: "¿Cómo va tu experiencia con Sweep?",
    rates: [ "Mala", "Regular", "Correcta", "Buena", "Excelente" ],
    label: {
      experience: "Cuéntanos",
      idea: "Tu idea",
      bug: "Qué no funciona"
    },
    ph: {
      experience: "Lo que te gusta, lo que te frustra, lo que te ayuda en tu trading…",
      idea: "Una función, una pantalla, una estadística que te falta…",
      bug: "Qué estabas haciendo, qué pasó, qué esperabas…"
    },
    attach: "Añadir una captura",
    send: "Enviar",
    sent: "Gracias, enviado",
    mine: "Tus envíos",
    empty: "Aún no has enviado nada.",
    status: {
      new: "Recibido",
      planned: "Previsto",
      in_progress: "En curso",
      shipped: "Publicado",
      declined: "Por ahora no"
    },
    reply: "Respuesta del equipo Sweep",
    errors: {
      limit: "Llegaste al límite de envíos de hoy. Inténtalo mañana.",
      file: "La captura debe ser una imagen PNG, JPG o WebP de 5 MB máximo.",
      invalid: "Escribe un mensaje antes de enviar.",
      server: "El envío no funcionó. Inténtalo de nuevo en un momento."
    }
  }
}, RT = () => REF_T[LANG] || REF_T.en, FT = () => FB_T[LANG] || FB_T.en, fmtT = (e, t) => String(e).replace(/\{(\w+)\}/g, (a, n) => t[n] ?? ""), GR = {
  ref: null,
  refErr: null,
  refAt: 0,
  fb: null,
  fbAt: 0,
  type: "experience",
  rating: 0,
  shot: null,
  busy: !1,
  from: null,
  adm: {
    fb: null,
    ref: null,
    st: "",
    ty: ""
  }
};

function loadRef(e) {
  S.mode !== "server" || !e && GR.ref && Date.now() - GR.refAt < 3e4 || (GR.refAt = Date.now(), 
  apiJSON("api/referral").then(t => {
    GR.ref = t, GR.refErr = null, render();
  }).catch(t => {
    GR.refErr = t.message, render();
  }));
}

function candles(e, t) {
  let a = "";
  for (let n = 0; n < t; n++) {
    const s = n < e;
    a += `<svg viewBox="40 8 40 102" class="${s ? "on" : ""}" aria-hidden="true"><line x1="60" y1="14" x2="60" y2="30" stroke="currentColor" stroke-width="6" stroke-linecap="round"/><rect x="46" y="28" width="28" height="44" rx="5" fill="currentColor"/><line x1="60" y1="70" x2="60" y2="96" stroke="currentColor" stroke-width="6" stroke-linecap="round"/></svg>`;
  }
  return a;
}

function vReferral() {
  if (S.mode !== "server") return `<div class="empty">${RT().error}</div>`;
  loadRef();
  const e = RT(), t = GR.ref;
  if (!t) return GR.refErr ? `<div class="empty">${esc(e.error)}</div>` : '<div class="boot"><div class="skel"></div><div class="skel t"></div></div>';
  const a = t.rules, n = t.stats, s = {
    pending: "p",
    review: "p",
    qualified: "q",
    rewarded: "r",
    expired: "x"
  }, i = t.referrals.length ? t.referrals.map(r => `<li class="rf-item"><span class="rf-av">${esc(r.initials)}</span><div class="rf-mid"><b>${esc(r.name)}</b><small>${esc(fmtT(e.joined, {
    date: fdate(r.joined.slice(0, 10), {
      month: "short",
      day: "numeric"
    })
  }))}</small>\n      ${r.status === "pending" && r.trades != null ? `<div class="rf-prog"><i style="width:${Math.min(100, Math.round(Math.min(r.trades / a.trades, 1) * 50 + Math.min(r.days / a.days, 1) * 50))}%"></i></div><small>${esc(fmtT(e.progress, {
    t: r.trades,
    T: a.trades,
    k: r.days,
    K: a.days,
    r: r.days_left
  }))}</small>` : ""}</div>\n      <span class="rf-st s-${s[r.status] || "p"}">${esc(e.status[r.status] || r.status)}</span></li>`).join("") : `<li class="rf-empty">${esc(e.empty)}</li>`, o = e.candles[n.earned_year === 1 ? 0 : 1];
  return `<div class="rf" data-noi18n>\n   <section class="rf-hero"><div class="rf-gift" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="13" rx="2"/><path d="M12 8v13M3 12h18M12 8c-2-4-6-4-6-1.5S9 8 12 8zm0 0c2-4 6-4 6-1.5S15 8 12 8z"/></svg></div>\n     <h2>${esc(e.headline)}</h2><p>${esc(fmtT(e.lead, {
    d: a.referee_days
  }))}</p>\n     <div class="rf-link"><div><small>${esc(e.yourCode)}</small><b>${esc(t.code)}</b><span>${esc(t.link.replace(/^https?:\/\//, ""))}</span></div><button class="btn sm" data-act="ref-copy">${esc(e.copy)}</button></div>\n     <button class="btn primary rf-share" data-act="ref-share"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 8l5-5 5 5"/><path d="M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/></svg>${esc(e.share)}</button>\n     <div class="rf-cand"><div class="rf-candles">${candles(n.earned_year, a.max_year)}</div><small>${esc(fmtT(o, {
    n: n.earned_year,
    max: a.max_year
  }))}</small>${t.bonus_until ? `<span class="rf-bonus">✦ ${esc(fmtT(e.bonus, {
    date: fdate(t.bonus_until.slice(0, 10), {
      month: "long",
      day: "numeric"
    })
  }))}</span>` : ""}</div>\n   </section>\n   <section class="sec"><div class="sec-h"><h2>${esc(e.how)}</h2></div><ol class="rf-steps">${e.steps.map((r, c) => `<li><span>${c + 1}</span>${esc(fmtT(r, {
    d: a.referee_days,
    t: a.trades,
    k: a.days
  }))}</li>`).join("")}</ol></section>\n   <section class="sec"><div class="sec-h"><h2>${esc(e.invites)}</h2><span class="help">${esc(e.summary(n))}</span></div><ul class="rf-list surface">${i}</ul>\n     <button class="link rf-terms" data-act="ref-terms">${esc(e.terms)}</button></section>\n  </div>`;
}

async function refShare() {
  const e = RT(), t = GR.ref;
  if (!t) return;
  const a = fmtT(e.shareText, {
    d: t.rules.referee_days
  });
  if (navigator.share) try {
    await navigator.share({
      title: "Sweep",
      text: a,
      url: t.link
    });
    return;
  } catch (n) {
    if (n && n.name === "AbortError") return;
  }
  refCopy();
}

async function refCopy() {
  const e = RT(), t = GR.ref;
  if (t) try {
    await navigator.clipboard.writeText(t.link), toast(e.copied), haptic && haptic(6);
  } catch {
    prompt(e.copy, t.link);
  }
}

function refTerms() {
  const e = RT(), t = GR.ref.rules;
  let a = $("#refTerms");
  if (!a) {
    a = document.createElement("aside"), a.id = "refTerms", a.className = "evp grsh", 
    a.setAttribute("data-noi18n", ""), a.innerHTML = '<div class="evp-in gr-in"></div>', 
    document.body.append(a);
    const n = document.createElement("div");
    n.id = "refTermsScrim", n.className = "evp-scrim", n.addEventListener("click", closeRefTerms), 
    document.body.append(n), a.addEventListener("click", s => {
      s.target.closest("[data-close]") && closeRefTerms();
    }), swipeDismiss(a, {
      scroller: () => a.querySelector(".gr-in"),
      onClose: closeRefTerms
    });
  }
  a.querySelector(".gr-in").innerHTML = `<div class="tk-head"><div><h2>${esc(e.terms)}</h2></div><button class="link" data-close>${esc(e.close)}</button></div><ol class="rf-terms-list">${e.termsList.map(n => `<li>${esc(fmtT(n, {
    w: t.window,
    t: t.trades,
    k: t.days,
    d: t.referee_days,
    max: t.max_year
  }))}</li>`).join("")}</ol>`, requestAnimationFrame(() => {
    a.classList.add("open"), $("#refTermsScrim").classList.add("open"), document.body.classList.add("evp-lock");
  });
}

function closeRefTerms() {
  const e = $("#refTerms");
  e && (e.classList.remove("open"), $("#refTermsScrim").classList.remove("open"), 
  document.body.classList.remove("evp-lock"));
}

function loadFb(e) {
  S.mode !== "server" || !e && GR.fb && Date.now() - GR.fbAt < 3e4 || (GR.fbAt = Date.now(), 
  apiJSON("api/feedback").then(t => {
    GR.fb = t.items || [], render();
  }).catch(() => {
    GR.fb = [], render();
  }));
}

const FACES = [ "😞", "😕", "😐", "🙂", "😄" ], FB_ICON = {
  bug: '<path d="M8 8a4 4 0 0 1 8 0v6a4 4 0 0 1-8 0z"/><path d="M4 12h4M16 12h4M5 7l3 2M19 7l-3 2M5 18l3-2M19 18l-3-2"/>',
  idea: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5.9 1.2.9 2V16h5.2v-.1c0-.8.3-1.5.9-2A6 6 0 0 0 12 3z"/>',
  experience: '<path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z"/><path d="M8.5 14.5s1.2 1.5 3.5 1.5 3.5-1.5 3.5-1.5M9 9.5h.01M15 9.5h.01"/>'
};

function vFeedback() {
  if (S.mode !== "server") return `<div class="empty">${FT().errors.server}</div>`;
  loadFb();
  const e = FT(), t = GR.type, a = GR.fb == null ? '<li class="rf-empty">…</li>' : GR.fb.length ? GR.fb.map(n => `<li class="fb-item"><div class="fb-top"><span class="fb-ic t-${n.type}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${FB_ICON[n.type]}</svg></span>\n      <b>${esc(e["t_" + n.type])}${n.rating ? ` ${FACES[n.rating - 1]}` : ""}</b><small>${esc(fdate(n.created.slice(0, 10), {
    month: "short",
    day: "numeric"
  }))}</small><span class="fb-st s-${n.status}">${esc(e.status[n.status] || n.status)}</span></div>\n      <p>${esc(n.message)}</p>${n.shot ? `<img class="fb-shot" src="${esc(n.shot)}" alt="" loading="lazy" data-act="zoom">` : ""}\n      ${n.reply ? `<div class="fb-reply"><small>${esc(e.reply)}</small><p>${esc(n.reply)}</p></div>` : ""}</li>`).join("") : `<li class="rf-empty">${esc(e.empty)}</li>`;
  return `<div class="fb" data-noi18n>\n   <p class="fb-lead">${esc(e.lead)}</p>\n   <section class="surface pad fb-form">\n     <div class="seg fb-seg" role="tablist">${[ "experience", "idea", "bug" ].map(n => `<button role="tab" data-act="fb-type" data-v="${n}" class="${t === n ? "on" : ""}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${FB_ICON[n]}</svg>${esc(e["t_" + n])}</button>`).join("")}</div>\n     ${t === "experience" ? `<p class="fb-q">${esc(e.rateQ)}</p><div class="fb-faces" role="radiogroup">${FACES.map((n, s) => `<button type="button" role="radio" aria-checked="${GR.rating === s + 1}" aria-label="${esc(e.rates[s])}" data-act="fb-rate" data-v="${s + 1}" class="${GR.rating === s + 1 ? "on" : ""}"><span>${n}</span><small>${esc(e.rates[s])}</small></button>`).join("")}</div>` : ""}\n     <label class="fb-l" for="fbMsg">${esc(e.label[t])}</label>\n     <textarea id="fbMsg" rows="5" maxlength="2000" placeholder="${esc(e.ph[t])}">${esc(GR.draft || "")}</textarea>\n     <div class="fb-row">${GR.shot ? `<span class="fb-thumb"><img src="${GR.shot}" alt=""><button type="button" data-act="fb-unshot" aria-label="Remove">✕</button></span>` : `<label class="btn sm fb-attach"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M21 16l-5-5-8 8"/></svg>${esc(e.attach)}<input type="file" accept="image/png,image/jpeg,image/webp" data-fb-shot hidden></label>`}\n       <span class="fb-count" id="fbCount">${(GR.draft || "").length}/2000</span></div>\n     <button class="btn primary fb-send" data-act="fb-send" ${GR.busy ? "disabled" : ""}>${esc(e.send)}</button>\n   </section>\n   <section class="sec"><div class="sec-h"><h2>${esc(e.mine)}</h2></div><ul class="fb-list">${a}</ul></section>\n  </div>`;
}

function fbReadShot(e) {
  return new Promise((t, a) => {
    if (!/^image\/(png|jpeg|webp)$/.test(e.type) || e.size > 20 * 1048576) return a("file");
    const n = new Image;
    n.onload = () => {
      const s = Math.min(1, 1600 / Math.max(n.width, n.height)), i = document.createElement("canvas");
      i.width = Math.round(n.width * s), i.height = Math.round(n.height * s), i.getContext("2d").drawImage(n, 0, 0, i.width, i.height);
      let o = i.toDataURL("image/webp", .85);
      if (o.startsWith("data:image/webp") || (o = i.toDataURL("image/jpeg", .85)), URL.revokeObjectURL(n.src), 
      o.length > 6.9 * 1048576) return a("file");
      t(o);
    }, n.onerror = () => a("file"), n.src = URL.createObjectURL(e);
  });
}

async function fbSend() {
  const e = FT(), t = ($("#fbMsg") || {}).value || "";
  if (!t.trim()) {
    toast(e.errors.invalid);
    return;
  }
  GR.busy = !0, GR.draft = t, render();
  try {
    await apiJSON("api/feedback", {
      method: "POST",
      body: {
        type: GR.type,
        rating: GR.type === "experience" && GR.rating || null,
        message: t,
        page: GR.from || "",
        screen: innerWidth + "x" + innerHeight,
        lang: LANG,
        version: (document.querySelector('script[src*="assets/app."]') || {}).src?.split("app.")[1]?.split(".js")[0] || "",
        shot: GR.shot
      }
    }), GR.draft = "", GR.shot = null, GR.rating = 0, toast(e.sent), haptic && haptic(8), 
    typeof confetti == "function" && GR.type === "experience" && confetti(), loadFb(!0);
  } catch (a) {
    toast(e.errors[a.data && a.data.error] || e.errors.server);
  }
  GR.busy = !1, render();
}

document.addEventListener("input", e => {
  if (e.target.id === "fbMsg") {
    GR.draft = e.target.value;
    const t = $("#fbCount");
    t && (t.textContent = e.target.value.length + "/2000");
  }
}), document.addEventListener("change", async e => {
  if (e.target.matches && e.target.matches("[data-fb-shot]") && e.target.files[0]) try {
    GR.shot = await fbReadShot(e.target.files[0]), render();
  } catch {
    toast(FT().errors.file);
  }
});

function growthAdmin() {
  const e = GR.adm;
  e.fb == null && (e.fb = [], apiJSON("api/admin/feedback" + (e.st || e.ty ? `?status=${e.st}&type=${e.ty}` : "")).then(o => {
    e.fb = o, render();
  }).catch(() => {}), apiJSON("api/admin/referrals").then(o => {
    e.ref = o.items || [], render();
  }).catch(() => {}));
  const t = FT(), a = e.fb && e.fb.items ? e.fb : {
    items: [],
    new: 0,
    avg_rating_30d: null
  }, n = (o, r, c) => `<button class="chip ${e[o] === r ? "on" : ""}" data-act="gadm-f" data-k="${o}" data-v="${r}">${esc(c)}</button>`, s = a.items.map(o => `<li class="fb-item adm" id="fb${o.id}"><div class="fb-top"><span class="fb-ic t-${o.type}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${FB_ICON[o.type]}</svg></span>\n      <b>${esc(o.user || "?")}${o.rating ? ` · ${FACES[o.rating - 1]} ${o.rating}/5` : ""}</b><small>${esc(fdate(o.created.slice(0, 10), {
    month: "short",
    day: "numeric"
  }))}${o.page ? " · " + esc(o.page) : ""}${o.context && o.context.plan ? " · " + esc(o.context.plan) : ""}</small></div>\n      <p>${esc(o.message)}</p>${o.shot ? `<img class="fb-shot" src="${esc(o.shot)}" alt="" loading="lazy" data-act="zoom">` : ""}\n      <small class="faint">${esc([ o.email, o.context && o.context.screen, o.context && o.context.lang, o.context && o.context.version ].filter(Boolean).join(" · "))}</small>\n      <div class="gadm-row"><select data-gadm-status="${o.id}" data-native>${[ "new", "planned", "in_progress", "shipped", "declined" ].map(r => `<option value="${r}" ${o.status === r ? "selected" : ""}>${esc(t.status[r])}</option>`).join("")}</select>\n      <textarea data-gadm-reply="${o.id}" rows="2" placeholder="${esc(t.reply)}">${esc(o.reply || "")}</textarea><button class="btn sm primary" data-act="gadm-save" data-id="${o.id}">OK</button></div></li>`).join("") || '<li class="rf-empty">—</li>', i = (e.ref || []).map(o => `<tr><td>${esc(o.referrer || "?")}</td><td>${esc(o.referee || "?")}</td><td><span class="rf-st s-${{
    pending: "p",
    review: "v",
    qualified: "q",
    rewarded: "r",
    expired: "x",
    rejected: "x"
  }[o.status]}">${esc(o.status)}</span></td><td class="muted">${esc(o.reward_type || "")}${o.reward_type === "stripe_credit" ? " $" + (o.reward_value / 100).toFixed(2) : o.reward_value ? " " + o.reward_value + " d" : ""}</td><td class="muted">${fdate(new Date(o.created_at * 1e3).toISOString().slice(0, 10), {
    month: "short",
    day: "numeric"
  })}</td>\n      <td class="num">${o.status === "review" ? `<button class="link" data-act="gadm-ref" data-id="${o.id}" data-v="approve">Approve</button> · ` : ""}${[ "review", "pending" ].includes(o.status) ? `<button class="link" data-act="gadm-ref" data-id="${o.id}" data-v="reject" style="color:var(--neg)">Reject</button>` : ""}</td></tr>`).join("");
  return `<section class="sec" data-noi18n><div class="sec-h"><h2>Feedback</h2><span class="help">${a.new} new${a.avg_rating_30d != null ? ` · ${a.avg_rating_30d}/5 (30 d)` : ""}</span></div>\n     <div class="chips gadm-chips">${n("st", "", "All")}${[ "new", "planned", "in_progress", "shipped", "declined" ].map(o => n("st", o, t.status[o])).join("")}<span class="gadm-sep"></span>${n("ty", "", "All types")}${[ "bug", "idea", "experience" ].map(o => n("ty", o, t["t_" + o])).join("")}</div>\n     <ul class="fb-list">${s}</ul></section>\n   <section class="sec" data-noi18n><div class="sec-h"><h2>Referrals</h2><span class="help">${(e.ref || []).length} total · ${(e.ref || []).filter(o => o.status === "review").length} to review</span></div>\n     <div class="surface"><div class="scroll-x"><table class="tbl"><thead><tr><th>Referrer</th><th>Friend</th><th>Status</th><th>Reward</th><th>Joined</th><th></th></tr></thead><tbody>${i || '<tr><td colspan="6" class="muted">—</td></tr>'}</tbody></table></div></div></section>`;
}

async function gadmSave(e) {
  const t = $(`[data-gadm-status="${e}"]`).value, a = $(`[data-gadm-reply="${e}"]`).value;
  try {
    await apiJSON("api/admin/feedback/" + e, {
      method: "POST",
      body: {
        status: t,
        reply: a
      }
    }), toast("Saved"), GR.adm.fb = null, render();
  } catch (n) {
    toast(n.message);
  }
}

async function gadmRef(e, t) {
  try {
    await apiJSON("api/admin/referrals/" + e, {
      method: "POST",
      body: {
        action: t
      }
    }), toast("Saved"), GR.adm.fb = null, render();
  } catch (a) {
    toast(a.message);
  }
}

var _lastPhone = null;

const D = {
  open: !1,
  mode: "form",
  id: null,
  pnlManual: !1,
  sessManual: !1,
  copyTo: new Set
};

function openDrawer() {
  D.open = !0, D.mode = "account", renderDrawer(), $("#drawer").classList.add("on"), 
  $("#scrim").classList.add("on"), $("#drawer").setAttribute("aria-hidden", "false"), 
  setTimeout(() => {
    const e = $("#drawer input");
    e && e.focus();
  }, 60);
}

function closeDrawer() {
  flushDrafts(), D.open = !1, $("#drawer").classList.remove("on"), $("#scrim").classList.remove("on"), 
  $("#drawer").setAttribute("aria-hidden", "true"), scheduleRender();
}

function renderDrawer() {
  const e = $("#drawer");
  {
    e.innerHTML = `<header><h2>Add an account first</h2><button class="btn sm" data-act="close-drawer">Close</button></header><div class="body"><p class="muted" style="margin-top:0">Trades belong to an account.</p>${accountForm()}</div>`;
    return;
  }
}

function numOrNull(e) {
  if (e = String(e ?? "").replace(/,/g, "").trim(), e === "") return null;
  const t = Number(e);
  return isFinite(t) ? t : null;
}

function toast(e, {ms: t = 2600} = {}) {
  const a = $("#toast");
  a.textContent = e, a.classList.add("on"), clearTimeout(toast.t), toast.t = setTimeout(() => a.classList.remove("on"), t);
}

function refresh() {
  render();
}

function submitAccount(e) {
  if (!e.dataset.onb && !billGate("accounts", "add_account", {
    count: billRealAccounts().length
  })) return;
  const t = new FormData(e), a = e.querySelector("[data-err]");
  let n = t.get("firm");
  if (!n || n === "__new") {
    const o = String(t.get("firmName") || "").trim();
    if (!o) {
      a.textContent = "Enter the prop firm name.";
      return;
    }
    const r = S.firms.find(c => c.name.toLowerCase() === o.toLowerCase());
    r ? n = r.id : (n = uid(), put("firms", {
      id: n,
      name: o
    }));
  }
  const s = String(t.get("name") || "").trim();
  if (!s) {
    a.textContent = "Enter an account name.";
    return;
  }
  const i = parseMoney(t.get("start"));
  if (i == null) {
    a.textContent = "Enter the starting balance.";
    return;
  }
  if (put("accounts", {
    id: uid(),
    firm_id: n,
    name: s,
    starting_balance_c: i,
    status: "active",
    created_on: t.get("created") || todayStr()
  }), toast("Account added"), U.addAcct = !1, e.dataset.onb) {
    render(), setTimeout(() => openTicket(null), 300);
    return;
  }
  D.open && D.mode === "account" && (closeDrawer(), setTimeout(() => openTicket(null), 250)), 
  render();
}

function submitPayout(e) {
  if (!billGate("payouts", "payouts", {
    payoutTotal: billPayoutTotal()
  })) return;
  const t = new FormData(e), a = e.dataset.id || uid(), n = acct(t.get("account")), s = parseMoney(t.get("amount"));
  if (!n) {
    toast("Choose an account.");
    return;
  }
  if (s == null || s <= 0) {
    toast("Enter a payout amount.");
    return;
  }
  const i = getDoc("payouts", a) || {}, o = t.get("status") === "paid" && i.status !== "paid";
  put("payouts", {
    ...i,
    id: a,
    account_id: n.id,
    firm_id: n.firm_id,
    amount_c: s,
    status: t.get("status"),
    request_date: t.get("request_date") || "",
    approval_date: t.get("approval_date") || "",
    payment_date: t.get("payment_date") || "",
    notes: String(t.get("notes") || "").trim()
  });
  const r = (i && i.status) === "paid";
  toast(e.dataset.id ? "Payout saved" : "Payout added"), U.editP = null, render(), 
  t.get("status") === "paid" && !r && setTimeout(() => openShare("payout", a), 450), 
  o && setTimeout(() => openShare("payout", a), 350);
}

function submitExpense(e) {
  if (!billGate("payouts", "payouts", {
    payoutTotal: billPayoutTotal()
  })) return;
  const t = new FormData(e), a = e.dataset.id || uid(), n = parseMoney(t.get("amount"));
  if (n == null || n <= 0) {
    toast("Enter an expense amount.");
    return;
  }
  const s = t.get("account") || "", i = t.get("firm") || (s ? acct(s)?.firm_id : "") || "", o = getDoc("expenses", a) || {};
  put("expenses", {
    ...o,
    id: a,
    date: t.get("date"),
    firm_id: i,
    account_id: s,
    category: t.get("category"),
    amount_c: n,
    notes: String(t.get("notes") || "").trim()
  }), toast(e.dataset.id ? "Expense saved" : "Expense added"), U.editE = null, render();
}

async function uploadShots(e) {
  const t = e.dataset.upload, a = e.closest("[data-shotwrap]")?.querySelector("select") || $("#shotPhase"), n = a ? a.value : "before", s = [ ...e.files ];
  if (e.value = "", !(!ASSETS || !s.length)) {
    for (const i of s) try {
      toast("Uploading " + i.name + "…", {
        ms: 2e4
      });
      const o = await ASSETS.upload(i);
      editDoc("trades", t, r => {
        r.shots = r.shots || [], r.shots.push({
          id: o.id,
          phase: n,
          name: i.name
        });
      }), syncTrade(t, [ "shots" ]);
    } catch (o) {
      toast("Upload failed: " + (o.message || o.code || "unknown error"));
      return;
    }
    toast(s.length > 1 ? s.length + " screenshots added" : "Screenshot added"), refresh();
  }
}

async function exportData() {
  const e = {
    exported_at: (new Date).toISOString(),
    settings: S.settings
  };
  COLS.forEach(s => e[s] = S[s]);
  const t = JSON.stringify(e, null, 2), a = `sweep-export-${todayStr()}.json`;
  if (DL) {
    try {
      await DL.save({
        filename: a,
        data: t
      });
    } catch (s) {
      s && s.code !== "cancelled" && s.code !== "declined" && toast("Export failed: " + (s.message || s.code));
    }
    return;
  }
  const n = document.createElement("a");
  n.href = URL.createObjectURL(new Blob([ t ], {
    type: "application/json"
  })), n.download = a, n.click();
}

async function importData(e) {
  const t = e.files[0];
  if (e.value = "", !t) return;
  let a;
  try {
    a = JSON.parse(await t.text());
  } catch {
    toast("This file is not valid JSON.");
    return;
  }
  if (!a || typeof a != "object" || !COLS.some(i => Array.isArray(a[i]))) {
    toast("This file is not a journal export.");
    return;
  }
  const n = i => (Array.isArray(i) ? i : []).filter(o => o && typeof o == "object" && typeof o.id == "string" && /^[A-Za-z0-9_.:@+~-]{1,120}$/.test(o.id)), s = COLS.reduce((i, o) => i + n(a[o]).length, 0);
  if (confirm(`Import ${s} records? Records with the same id are replaced; nothing is deleted. Screenshots are not part of exports and are not imported.`)) {
    toast("Importing…", {
      ms: 12e4
    });
    try {
      for (const i of COLS) {
        const o = n(a[i]);
        i === "trades" && o.forEach(r => {
          r.shots = [];
        }), await bulkPut(i, o);
      }
      a.settings && Array.isArray(a.settings.questions) && await bulkPut("settings", [ {
        ...a.settings,
        id: "settings"
      } ]), toast(`Imported ${s} records`);
    } catch (i) {
      toast(saveErr(i));
    }
    render();
  }
}

async function loadDemo() {
  toast("Adding sample data…", {
    ms: 6e4
  });
  const e = (h, m) => h + Math.random() * (m - h), t = h => h[Math.floor(Math.random() * h.length)], a = h => Math.random() < h, n = h => Math.round(h * 4) / 4, s = [ [ "demo-f-topstep", "Topstep" ], [ "demo-f-lucid", "Lucid" ], [ "demo-f-apex", "Apex" ] ].map(([h, m]) => ({
    id: h,
    name: m,
    demo: !0
  })), i = [ [ "demo-a1", "demo-f-topstep", "Account 1" ], [ "demo-a2", "demo-f-topstep", "Account 2" ], [ "demo-a3", "demo-f-lucid", "Account 1" ], [ "demo-a4", "demo-f-lucid", "Account 2" ], [ "demo-a5", "demo-f-apex", "Account 1" ] ].map(([h, m, v]) => ({
    id: h,
    firm_id: m,
    name: v,
    starting_balance_c: 5e6,
    status: "active",
    created_on: addDays(todayStr(), -80),
    notes: "Sample account — sample rule values",
    demo: !0,
    rules: {
      target_c: 3e5,
      dd_c: 2e5,
      dd_type: "eod",
      dd_lock: !0,
      dll_c: 1e5,
      consistency_pct: 50,
      min_days: 5
    }
  })).map(h => {
    const m = {
      "demo-a1": "funded",
      "demo-a3": "funded",
      "demo-a5": "live"
    }[h.id] || "eval";
    return h.money_type = m, h.phase = m, m !== "eval" && (h.rules = {
      ...h.rules,
      target_c: null,
      min_days: null
    }), h;
  }), o = [ "Liquidity sweep", "FVG retest", "Break of structure", "Opening range" ], r = [], c = [];
  let l = 21400;
  for (let h = 72; h >= 0; h--) {
    const m = addDays(todayStr(), -h), v = pd(m).getDay();
    if (v === 0 || v === 6) continue;
    const b = Math.floor(e(1, 4.7)), E = t(i).id;
    let R = 0, L = 0;
    for (let x = 0; x < b; x++) {
      const C = R > 0 && a(.38), g = Math.random(), P = C ? t([ "nyam", "nypm" ]) : g < .58 ? "nyam" : g < .8 ? "nypm" : g < .93 ? "london" : "asia", O = {
        asia: 19 * 60,
        london: 3 * 60,
        nyam: 9 * 60 + 32,
        nypm: 12 * 60 + 10
      }[P], H = Math.round(O + x * 24 + e(0, 14)), J = H + Math.round(e(3, 22)), q = M => pad(Math.floor(M / 60) % 24) + ":" + pad(M % 60), z = a(.55) ? "long" : "short", Y = C ? Math.min(4, 1 + R + Math.floor(e(0, 2))) : t([ 1, 1, 2, 2, 2, 3 ]), Q = !C && a(.82), me = a(Q ? P === "nyam" ? .64 : .52 : .38), oe = me ? n(e(Q ? 18 : 10, Q ? 55 : 32)) : -n(e(Q ? 9 : 16, Q ? 21 : 48));
      l += e(-45, 45);
      const ae = n(l), we = ae + (z === "long" ? oe : -oe), te = n(e(11, 22)), re = {};
      if (DEFAULT_QS.forEach(([M]) => re[M] = "y"), re.dll = a(.7) ? "na" : "y", C) re.revenge = "n", 
      a(.5) && (re.chase = "n"), Y > 3 && (re.size = "n"), re.emotion = "n", a(.35) && (re.addloser = "n"), 
      a(.3) && (re.widen = "n"); else if (!Q) for (const M of [ t([ "confirm", "entry", "stop", "exit", "plan", "chase" ]), ...a(.3) ? [ t([ "widen", "addloser", "risk" ]) ] : [] ]) re[M] = "n";
      const X = a(.08), pe = C ? a(.5) ? [ "Frustrated", "Revenge mindset" ] : [ "Trying to recover a loss" ] : Q ? [ t([ "Calm", "Focused", "Patient", "Confident" ]) ] : [ t([ "FOMO", "Impulsive", "Hesitant", "Need to be right" ]) ], ue = {
        id: "demo-t-" + uid(),
        demo: !0,
        instrument: "NQ",
        account_id: E,
        date: m,
        entry_time: q(H),
        exit_time: q(J),
        session: sessionFor(q(H)),
        direction: z,
        contracts: Y,
        entry: ae,
        exit: we,
        stop: z === "long" ? ae - te : ae + te,
        target: z === "long" ? ae + te * 2 : ae - te * 2,
        pnl_c: calcPnl(z, ae, we, Y, "NQ"),
        pnl_manual: !1,
        fees_c: Y * 420,
        setup: t(o),
        grade: Q ? me ? "A" : "B" : me ? "C" : "D",
        tags: [],
        notes: "",
        review: {},
        shots: [],
        discipline: X ? {} : re,
        emo: X ? {} : {
          before: pe,
          after: [ t(me ? [ "Calm", "Confident" ] : [ "Frustrated", "Calm", "Angry" ]) ],
          confidence: t(Q ? [ 3, 4, 5 ] : [ 2, 3 ]),
          execution: t(Q ? [ 4, 5 ] : [ 1, 2, 3 ]),
          quality: t(Q ? [ 3, 4, 5 ] : [ 1, 2 ])
        }
      };
      r.push(ue), L += tNet(ue), R = tNet(ue) < 0 ? R + 1 : 0;
    }
    h < 16 && c.push({
      id: m,
      date: m,
      demo: !0,
      pre: {
        bias: t([ "bullish", "bearish", "neutral" ]),
        focus: t([ "Do not add to losing positions.", "Wait for confirmation.", "Two trades maximum." ]),
        max_loss: "1000",
        max_trades: "3"
      },
      post: {
        grade: L > 0 ? t([ "A", "B" ]) : t([ "B", "C", "D" ]),
        followed: L > 0 ? "yes" : t([ "partly", "no" ])
      }
    });
  }
  const p = [ {
    id: "demo-p1",
    account_id: "demo-a1",
    firm_id: "demo-f-topstep",
    amount_c: 2e5,
    status: "paid",
    request_date: addDays(todayStr(), -30),
    approval_date: addDays(todayStr(), -28),
    payment_date: addDays(todayStr(), -25),
    demo: !0
  }, {
    id: "demo-p2",
    account_id: "demo-a3",
    firm_id: "demo-f-lucid",
    amount_c: 15e4,
    status: "approved",
    request_date: addDays(todayStr(), -6),
    approval_date: addDays(todayStr(), -4),
    demo: !0
  }, {
    id: "demo-p3",
    account_id: "demo-a5",
    firm_id: "demo-f-apex",
    amount_c: 12e4,
    status: "requested",
    request_date: addDays(todayStr(), -2),
    demo: !0
  } ], u = [ [ "demo-e1", "demo-f-topstep", "demo-a1", "evaluation", 4900 ], [ "demo-e2", "demo-f-topstep", "demo-a2", "evaluation", 4900 ], [ "demo-e3", "demo-f-lucid", "", "evaluation", 8e3 ], [ "demo-e4", "demo-f-apex", "demo-a5", "activation", 8500 ], [ "demo-e5", "demo-f-topstep", "demo-a2", "reset", 4900 ] ].map(([h, m, v, b, E], R) => ({
    id: h,
    firm_id: m,
    account_id: v,
    category: b,
    amount_c: E,
    date: addDays(todayStr(), -78 + R * 9),
    notes: "",
    demo: !0
  }));
  try {
    await loadEcon(addDays(todayStr(), -75), todayStr());
    for (const h of r) Object.assign(h, newsContext(etEpoch(h.date + " " + h.entry_time + ":00"), etEpoch(h.date + " " + h.exit_time + ":00")));
  } catch {}
  if (window.SweepUndo && SweepUndo.demo && !await SweepUndo.demo(r.length, i.length)) return;
  r.forEach(h => {
    h.session_date = !0;
  });
  try {
    await bulkPut("firms", s), await bulkPut("accounts", i), await bulkPut("trades", r), 
    await bulkPut("journals", c), await bulkPut("payouts", p), await bulkPut("expenses", u), 
    toast(`Added ${r.length} sample trades`);
  } catch (h) {
    toast(saveErr(h));
  }
  F.period = "all", saveF(), render();
}

async function removeDemo() {
  if (confirm("Remove all sample data? Your own trades and accounts are not affected.")) {
    toast("Removing sample data…", {
      ms: 6e4
    });
    try {
      for (const e of COLS) await bulkDel(e, S[e].filter(t => t.demo).map(t => t.id));
      (F.account.startsWith("demo") || F.firm.startsWith("demo")) && (F.account = "all", 
      F.firm = "all", saveF()), toast("Sample data removed");
    } catch (e) {
      toast(saveErr(e));
    }
    render();
  }
}

document.addEventListener("click", e => {
  if (e.target.closest && e.target.closest(".sai")) return;
  const t = e.target.closest("tr[data-href]");
  if (t && !e.target.closest("a,button,select,input")) {
    location.hash = t.dataset.href;
    return;
  }
  const a = e.target.closest("th[data-sort]");
  if (a) {
    const i = a.dataset.sort;
    U.sort = U.sort.k === i ? {
      k: i,
      d: U.sort.d === "asc" ? "desc" : "asc"
    } : {
      k: i,
      d: [ "account", "session", "dir", "setup" ].includes(i) ? "asc" : "desc"
    }, saveU(), render();
    return;
  }
  const n = e.target.closest("[data-act]");
  if (!n) return;
  const s = n.dataset;
  switch (s.act) {
   case "add-trade":
    e.preventDefault(), openTicket(null, {
      date: s.date
    });
    break;

   case "edit-trade":
    openTicket(s.id);
    break;

   case "tr-tf":
    U.trtf = +s.v, saveU(), render();
    break;

   case "close-drawer":
    closeDrawer();
    break;

   case "open-review":
    closeDrawer(), location.hash = "#trade/" + s.id;
    break;

   case "period":
    F.period = s.v, s.v === "custom" && !F.from && (F.from = monthStart(todayStr()), 
    F.to = todayStr()), saveF(), render();
    break;

   case "clear-filters":
    Object.assign(F, {
      account: "all",
      firm: "all",
      session: "all",
      dir: "all",
      inst: "all"
    }), saveF(), render();
    break;

   case "toggle-more":
    U.more = !U.more, saveU(), render();
    break;

   case "eq":
    U.eq = s.v, saveU(), render();
    break;

   case "bars":
    U.bars = s.v, saveU(), render();
    break;

   case "set":
    {
      let i = s.v;
      /^[1-5]$/.test(i) && (i = Number(i));
      const o = s.col, r = s.id, c = s.path;
      editDoc(o, r, l => {
        const p = getPath(l, c);
        setPath(l, c, p === i && c !== "status" ? void 0 : i), o === "journals" && (l.date = r), 
        o === "weekly" && (l.week = r);
      }, {
        init: () => ({
          id: r
        })
      }), o === "trades" && SYNC_RE.test(c) && syncTrade(r, [ c ]), refresh();
      break;
    }

   case "toggle":
    {
      const i = s.col, o = s.id, r = s.path, c = s.v;
      editDoc(i, o, l => {
        const p = (getPath(l, r) || []).slice(), u = p.indexOf(c);
        u >= 0 ? p.splice(u, 1) : p.push(c), setPath(l, r, p);
      }), i === "trades" && SYNC_RE.test(r) && syncTrade(o, [ r ]), refresh();
      break;
    }

   case "all-yes":
    editDoc("trades", s.id, i => {
      i.discipline = i.discipline || {}, S.settings.questions.filter(o => o.active).forEach(o => {
        i.discipline[o.id] || (i.discipline[o.id] = "y");
      });
    }), syncTrade(s.id, [ "discipline" ]), refresh();
    break;

   case "del-trade":
    {
      const i = getDoc("trades", s.id), o = siblings(s.id);
      if (!confirm(o.length ? `Delete this copy (${acctLabel(i.account_id)})? The other ${o.length} cop${o.length > 1 ? "ies stay" : "y stays"}.` : "Delete this trade? This cannot be undone.")) break;
      o.length || (i.shots || []).forEach(r => ASSETS && ASSETS.delete(r.id).catch(() => {})), 
      remove("trades", s.id), toast("Trade deleted"), location.hash = o.length ? "#trade/" + o[0].id : "#trades";
      break;
    }

   case "del-trade-all":
    {
      const i = getDoc("trades", s.id), o = copiesOf(i);
      if (!confirm(`Delete this trade on all ${o.length} accounts? This cannot be undone.`)) break;
      (i.shots || []).forEach(r => ASSETS && ASSETS.delete(r.id).catch(() => {})), o.forEach(r => remove("trades", r.id)), 
      toast(`Deleted on ${o.length} accounts`), location.hash = "#trades";
      break;
    }

   case "copy-open":
    CP.id = CP.id === s.id ? null : s.id, CP.sel = new Set, render();
    break;

   case "copy-close":
    CP.id = null, render();
    break;

   case "copy-pick":
    CP.sel.has(s.v) ? CP.sel.delete(s.v) : CP.sel.add(s.v), render();
    break;

   case "copy-do":
    {
      const i = getDoc("trades", s.id);
      if (!i || !CP.sel.size) break;
      const o = i.copy_group || uid();
      i.copy_group || editDoc("trades", i.id, c => {
        c.copy_group = o;
      });
      const r = structuredClone(getDoc("trades", i.id));
      for (const c of CP.sel) put("trades", {
        ...r,
        id: uid(),
        account_id: c,
        copy_group: o,
        created_at: void 0
      });
      toast(`Copied to ${CP.sel.size} account${CP.sel.size > 1 ? "s" : ""}`), CP.id = null, 
      CP.sel = new Set, render();
      break;
    }

   case "del-shot":
    confirm("Remove this screenshot?") && (ASSETS && ASSETS.delete(s.v).catch(() => {}), 
    editDoc("trades", s.id, i => {
      i.shots = (i.shots || []).filter(o => o.id !== s.v);
    }), syncTrade(s.id, [ "shots" ]), refresh());
    break;

   case "zoom":
    {
      const i = document.createElement("div");
      i.className = "lightbox", i.innerHTML = `<img src="${n.getAttribute("src")}" alt="">`, 
      i.onclick = () => i.remove(), document.body.append(i);
      break;
    }

   case "edit-payout":
    U.editP = s.id, render();
    break;

   case "edit-expense":
    U.editE = s.id, render();
    break;

   case "cancel-edit":
    U.editP = U.editE = null, render();
    break;

   case "del-payout":
    confirm("Delete this payout?") && (remove("payouts", s.id), U.editP = null, render());
    break;

   case "del-expense":
    confirm("Delete this expense?") && (remove("expenses", s.id), U.editE = null, render());
    break;

   case "del-account":
    confirm("Delete this account? It has no trades.") && (remove("accounts", s.id), 
    location.hash = "#accounts");
    break;

   case "filter-account":
    F.account = s.id, F.firm = "all", saveF(), location.hash = "#analytics";
    break;

   case "ui-disc-none":
    U.disc = "none", saveU();
    break;

   case "q-add":
    {
      const o = $("#newQ").value.trim();
      if (!o) return;
      editDoc("settings", "settings", r => {
        r.questions.push({
          id: "q" + uid(),
          text: o,
          viol: "No: " + o.replace(/\?$/, ""),
          active: !0
        });
      }), render();
      break;
    }

   case "q-del":
    confirm("Remove this question?") && (editDoc("settings", "settings", i => {
      i.questions.splice(Number(s.i), 1);
    }), render());
    break;

   case "setup-add":
    {
      const o = $("#newSetup").value.trim();
      if (!o) return;
      editDoc("settings", "settings", r => {
        r.setups = r.setups || [], r.setups.includes(o) || r.setups.push(o);
      }), render();
      break;
    }

   case "setup-del":
    editDoc("settings", "settings", i => {
      i.setups.splice(Number(s.i), 1);
    }), render();
    break;

   case "export":
    exportData();
    break;

   case "demo":
    loadDemo();
    break;

   case "demo-del":
    removeDemo();
    break;

   case "logout":
    logout();
    break;

   case "cmd":
    openCmd();
    break;

   case "useg":
    U[s.k] = s.v, saveU(), render();
    break;

   case "more":
    {
      const i = $("#moreSheet");
      if (!i) break;
      i.hidden = !i.hidden, i.hidden || swipeDismiss(i.querySelector(".sheet-panel"), {
        onClose: () => {
          i.hidden = !0;
        }
      });
      break;
    }

   case "theme":
    applyTheme(s.v), render();
    break;

   case "lang":
    setLang(s.v);
    break;

   case "jump":
    e.preventDefault();
    {
      const i = document.getElementById(s.v);
      i && i.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    }
    break;

   case "onb-firm":
    {
      const i = $(".onb-form [name=firmName]");
      i.value = n.textContent.trim(), $$("[data-act=onb-firm]").forEach(r => r.classList.toggle("on", r === n));
      const o = $(".onb-form [name=name]");
      o && !o.value && o.focus();
      break;
    }

   case "onb-bal":
    {
      const i = $(".onb-form [name=start]");
      i.value = Number(s.v).toLocaleString("en-US"), $$("[data-act=onb-bal]").forEach(o => o.classList.toggle("on", o === n));
      break;
    }

   case "fsheet":
    openFSheet();
    break;

   case "fsheet-close":
    closeFSheet();
    break;

   case "freset":
    Object.assign(F, {
      firm: "all",
      account: "all",
      session: "all",
      dir: "all",
      inst: "all"
    }), saveF(), Object.assign(U, {
      result: "all",
      setup: "all",
      disc: "all",
      tag: ""
    }), saveU(), render(), refreshFSheet();
    break;

   case "fclear":
    {
      const [i, o] = s.k.split(":"), r = filterDefs(FSPEC).find(c => c.k === o);
      i === "F" ? (F[o] = r ? r.all : "all", saveF()) : (U[o] = r ? r.all : "all", saveU()), 
      render();
      break;
    }

   case "ai-log":
    aiOpen("log");
    break;

   case "ai-ask":
    aiOpen("ask");
    break;

   case "ai-review":
    if (!billGate("weekly_report", "weekly_report")) break;
    aiOpen("review");
    break;

   case "ai-scan":
    if (!billGate("ai_import", "ai_import")) break;
    aiOpen("scan");
    break;

   case "ai-day":
    aiDayDebrief(s.v);
    break;

   case "ai-feedback":
    aiTradeFeedback(s.id);
    break;

   case "ai-suggest":
    aiSuggest(s.id);
    break;

   case "share":
    openShare(s.k, s.id);
    break;

   case "att-copy":
    attCopy();
    break;

   case "ref-copy":
    refCopy();
    break;

   case "ref-share":
    refShare();
    break;

   case "ref-terms":
    refTerms();
    break;

   case "fb-type":
    GR.type = s.v, render();
    break;

   case "fb-rate":
    GR.rating = +s.v, haptic && haptic(5), render();
    break;

   case "fb-unshot":
    GR.shot = null, render();
    break;

   case "fb-send":
    fbSend();
    break;

   case "gadm-f":
    GR.adm[s.k] = s.v, GR.adm.fb = null, render();
    break;

   case "gadm-save":
    gadmSave(s.id);
    break;

   case "gadm-ref":
    gadmRef(s.id, s.v);
    break;

   case "adm-manage":
    admManage(s.id);
    break;

   case "bill-diag":
    billDiag();
    break;

   case "acct-add":
    if (s.v === "1" && !billGate("accounts", "add_account", {
      count: billRealAccounts().length
    })) break;
    U.addAcct = s.v === "1", render(), U.addAcct && setTimeout(() => {
      const i = $(".acct-add input[name=name]");
      i && i.focus();
    }, 50);
    break;

   case "more-trades":
    U.tlimit = (U.tlimit || 100) + 100, render();
    break;

   case "imp-go":
    impGo();
    break;

   case "imp-reset":
    IMP.rows = null, IMP.file = "", IMP.err = "", render();
    break;

   case "copy-rules":
    {
      const i = acct($("#copyRulesFrom").value);
      i && (editDoc("accounts", s.id, o => {
        o.rules = JSON.parse(JSON.stringify(i.rules || {}));
      }), toast("Rules copied"), render());
      break;
    }

   case "copy":
    (navigator.clipboard ? navigator.clipboard.writeText(s.v) : Promise.reject()).then(() => toast("Copied")).catch(() => prompt("Copy:", s.v));
    break;

   case "adm-refresh":
    ADM.users = null, ADM.err = "", render();
    break;

   case "adm-temp-hide":
    ADM.temp = null, render();
    break;

   case "rec-hide":
    REC.code = null, render();
    break;

   case "gen-invite":
    genInvite();
    break;

   case "adm-reset":
    admAction("reset", s.id, s.v);
    break;

   case "adm-disable":
    admAction("disable", s.id, s.v);
    break;

   case "adm-enable":
    admAction("enable", s.id, s.v);
    break;

   case "adm-del":
    admAction("delete", s.id, s.v);
    break;
  }
});

let searchT;

document.addEventListener("input", e => {
  if (e.target.closest && e.target.closest(".sai")) return;
  const t = e.target;
  t.dataset.bind && t.type !== "checkbox" && t.tagName !== "SELECT" && t.type !== "date" && onBind(t, !1), 
  t.dataset.ui === "q" && (U.q = t.value, saveU(), clearTimeout(searchT), searchT = setTimeout(() => {
    const a = t.selectionStart;
    render();
    const n = $("#search");
    if (n) {
      n.focus();
      try {
        n.setSelectionRange(a, a);
      } catch {}
    }
  }, 160));
}), document.addEventListener("change", e => {
  if (e.target.closest && e.target.closest(".sai")) return;
  const t = e.target;
  if (t.dataset.filter) {
    const n = t.dataset.filter;
    F[n] = t.value, n === "firm" && F.account !== "all" && acct(F.account)?.firm_id !== F.firm && F.firm !== "all" && (F.account = "all"), 
    (n === "from" || n === "to") && (F.period = "custom"), saveF(), render();
    return;
  }
  if (t.dataset.ui && t.dataset.ui !== "q") {
    U[t.dataset.ui] = t.value, saveU(), render();
    return;
  }
  if (t.dataset.bind && (t.tagName === "SELECT" || t.type === "date")) {
    onBind(t, !0), t.blur();
    return;
  }
  if (t.dataset.bind && t.type !== "checkbox") {
    const n = t.dataset.bind.split("|").slice(0, 2).join("/");
    dtimers[n] && (clearTimeout(dtimers[n].t), dtimers[n].flush());
  }
  if (t.dataset.actChange === "goto-journal" && t.value) {
    location.hash = "#journal/" + t.value;
    return;
  }
  if (t.dataset.imp === "account") {
    IMP.account = t.value, render();
    return;
  }
  if (t.dataset.imp === "file" && t.files[0]) {
    impFile(t.files[0]), t.value = "";
    return;
  }
  if (t.dataset.actChange === "dd-lock") {
    editDoc("accounts", t.dataset.id, n => {
      n.rules = n.rules || {}, n.rules.dd_lock = t.checked;
    }), scheduleRender();
    return;
  }
  if (t.dataset.actChange === "merge-copies") {
    editDoc("settings", "settings", n => {
      n.mergeCopies = t.checked;
    });
    return;
  }
  if (t.dataset.actChange === "q-active") {
    editDoc("settings", "settings", n => {
      n.questions[Number(t.dataset.i)].active = t.checked;
    });
    return;
  }
  if (t.dataset.upload) {
    uploadShots(t);
    return;
  }
  if (t.hasAttribute("data-import")) {
    importData(t);
    return;
  }
  const a = t.closest('form[data-form="account"]');
  if (a && t.name === "firm") {
    const n = a.querySelector("[data-newfirm]");
    n.hidden = t.value !== "__new", n.hidden || n.querySelector("input").focus();
  }
});

function onBind(e, t) {
  const [a, n, s] = e.dataset.bind.split("|");
  let i = e.value;
  const o = e.dataset.kind;
  o === "money" ? i = parseMoney(i) : o === "int" ? i = i === "" ? null : parseInt(i, 10) : o === "tags" && (i = i.split(",").map(r => r.trim()).filter(Boolean)), 
  editDoc(a, n, r => {
    setPath(r, s, i), a === "journals" && (r.date = n), a === "weekly" && (r.week = n);
  }, {
    delay: t ? 0 : 700,
    init: () => ({
      id: n
    })
  }), a === "trades" && SYNC_RE.test(s) && syncTrade(n, [ s ], {
    delay: t ? 0 : 700
  });
}

document.addEventListener("submit", e => {
  e.preventDefault();
  const t = e.target;
  t.dataset.form === "account" ? submitAccount(t) : t.dataset.form === "payout" ? submitPayout(t) : t.dataset.form === "expense" ? submitExpense(t) : t.dataset.form === "password" ? changePassword(t) : t.dataset.form === "email" ? changeEmail(t) : t.dataset.form === "econ" ? addEcon(t) : t.dataset.form === "recovery" ? newRecovery(t) : t.dataset.form === "access" ? saveAccess(t) : t.dataset.form === "delete-account" && deleteAccount(t);
}), document.addEventListener("keydown", e => {
  const t = e.target.closest && e.target.closest("input,textarea,select,[contenteditable]");
  if (e.key === "Escape") {
    const a = $(".lightbox");
    if (a) {
      a.remove();
      return;
    }
    if (D.open) {
      closeDrawer();
      return;
    }
    t && e.target.blur();
    return;
  }
  if (e.key === "Enter" && e.target.matches && e.target.matches("tr[data-href]")) {
    location.hash = e.target.dataset.href;
    return;
  }
  if (!(t || e.metaKey || e.ctrlKey || e.altKey || D.open)) {
    if (e.key === "n" || e.key === "N") {
      e.preventDefault(), openTicket(null);
      return;
    }
    if (/^[1-7]$/.test(e.key)) {
      location.hash = "#" + [ "dashboard", "trades", "calendar", "journal", "analytics", "accounts", "payouts" ][Number(e.key) - 1];
      return;
    }
    if (e.key === "/") {
      e.preventDefault(), route().v !== "trades" && (location.hash = "#trades"), setTimeout(() => $("#search") && $("#search").focus(), 40);
      return;
    }
    if ((e.key === "j" || e.key === "k") && route().v === "trade") {
      const a = sorted(S.trades), n = a.findIndex(i => i.id === route().arg), s = a[n + (e.key === "j" ? 1 : -1)];
      s && (location.hash = "#trade/" + s.id);
    }
  }
});

const TITLES = {
  referral: "Referrals",
  feedback: "Feedback",
  plan: "Subscription",
  dashboard: "Today",
  trades: "Trades",
  trade: "Trade review",
  journal: "Journal",
  calendar: "Calendar",
  accounts: "Accounts",
  account: "Account",
  payouts: "My money",
  analytics: "Stats",
  settings: "Settings",
  admin: "Traders",
  import: "Import trades",
  news: "Economic calendar"
};

function route() {
  const e = decodeURIComponent(location.hash.slice(1)) || "dashboard", [t, ...a] = e.split("/");
  return {
    v: TITLES[t] ? t : "dashboard",
    arg: a.join("/")
  };
}

let rq = !1, deferred = !1;

function isEditing() {
  const e = document.activeElement;
  return e && $("#main").contains(e) && e.matches("input:not([type=checkbox]):not([type=file]),textarea");
}

function scheduleRender() {
  rq || (rq = !0, requestAnimationFrame(() => {
    if (rq = !1, isEditing()) {
      deferred = !0;
      return;
    }
    render();
  }));
}

document.addEventListener("focusout", () => setTimeout(() => {
  deferred && !isEditing() && (deferred = !1, render());
}, 0));

function render() {
  if (location.hash.startsWith("#ticket")) {
    const o = location.hash.split("/")[1];
    history.replaceState(null, "", "#dashboard"), setTimeout(() => openTicket(o && !o.startsWith("d:") ? o : null, {
      date: o && o.startsWith("d:") ? o.slice(2) : void 0
    }), 0);
  }
  const e = route(), t = e.v === "trade" ? "trades" : e.v === "account" ? "accounts" : e.v;
  e.v !== "feedback" && (GR.from = location.hash || "#dashboard"), document.body.classList.toggle("srv", S.mode === "server"), 
  $("#title").textContent = (e.v === "dashboard" || e.v === "trades") && !S.accounts.length ? "Get started" : TITLES[e.v], 
  document.title = tr(TITLES[e.v]) + " · Sweep";
  {
    const o = $("#moreLogout");
    o && (o.hidden = !S.me);
  }
  $("#userBox").innerHTML = S.me ? `<button type="button" class="who" data-nav="menu" aria-label="Menu"><span class="av">${esc(S.me.username.slice(0, 1).toUpperCase())}</span><b>${esc(S.me.username)}</b></button>` : "";
  const a = {
    import: "trades",
    calendar: "trades",
    journal: "trades",
    payouts: "accounts"
  }[e.v] || t;
  $$("[data-v]", $(".side")).forEach(o => o.classList.toggle("on", o.dataset.v === a)), 
  $$("#bottomnav [data-v]").forEach(o => o.classList.toggle("on", o.dataset.v === a)), 
  labelRail(), $$("#moreSheet [data-v]").forEach(o => o.classList.toggle("on", o.dataset.v === e.v));
  const n = [ "journal", "analytics", "accounts", "payouts", "admin", "settings" ].includes(a);
  $("#moreBtn") && $("#moreBtn").classList.toggle("on", n), $("#moreAdmin") && ($("#moreAdmin").hidden = !(S.me && S.me.is_admin)), 
  $("#storeNote").textContent = S.mode === "cloud" ? "Synced · private to you" : S.mode === "server" ? S.me ? "Private to your account" : "Saved on your server" : S.mode === "local" ? "Saved in this browser" : "";
  const s = $("#main");
  if (S.mode === "loading") {
    s.innerHTML = SKELETON;
    return;
  }
  if (S.mode === "signedout") {
    s.innerHTML = '<div class="empty">You are signed out. <a href="./">Sign in</a></div>';
    return;
  }
  const i = {
    referral: vReferral,
    feedback: vFeedback,
    plan: vPlan,
    dashboard: vDashboard,
    trades: vTrades,
    trade: vTrade,
    journal: vJournal,
    calendar: vCalendar,
    accounts: vAccounts,
    account: vAccount,
    payouts: vPayouts,
    analytics: vAnalytics,
    settings: vSettings,
    admin: vAdmin,
    import: vImport,
    news: vNews
  }[e.v];
  try {
    s.innerHTML = i(e.arg);
  } catch (o) {
    console.error(o), s.innerHTML = `<div class="empty">This page could not be displayed: ${esc(o.message)}</div>`;
  }
  _lastPhone = isPhone(), _lastMob = isMobileUI(), typeof econPoll == "function" && econPoll(), 
  e.v === "trade" && requestAnimationFrame(() => tradeChartMount(getDoc("trades", e.arg))), 
  watchTitle(), requestAnimationFrame(placeTabPill);
  {
    const o = document.querySelector(".jstrip a.on");
    if (o) {
      const r = o.parentElement;
      r.scrollLeft = o.offsetLeft - r.clientWidth / 2 + o.clientWidth / 2;
    }
  }
  if (S.mode === "server" && !AI.ready && setTimeout(aiInit, 0), S.mode === "server" && !BILL.ready && setTimeout(billInit, 0), 
  S.mode !== "loading") {
    const o = document.getElementById("splash");
    o && !o.classList.contains("gone") && setTimeout(() => {
      o.classList.add("gone"), setTimeout(() => o.remove(), 500);
    }, Math.max(0, 900 - performance.now()));
  }
  billDecorate(), ANIM && (ANIM = !1, s.classList.remove("anim"), s.offsetWidth, s.classList.add("anim"), 
  runCountUps(s), clearTimeout(render.t), render.t = setTimeout(() => s.classList.remove("anim"), 1400));
}

addEventListener("hashchange", () => {
  ANIM = !0, closeSelect(), U.editP = U.editE = null, CP.id = null, ADM.temp = null, 
  REC.code = null, deferred = !1, render(), window.scrollTo(0, 0);
}), document.addEventListener("dragover", e => {
  const t = e.target.closest && e.target.closest("#drop");
  t && (e.preventDefault(), t.classList.add("over"));
}), document.addEventListener("dragleave", e => {
  const t = e.target.closest && e.target.closest("#drop");
  t && t.classList.remove("over");
}), document.addEventListener("drop", e => {
  const t = e.target.closest && e.target.closest("#drop");
  if (t) {
    e.preventDefault(), t.classList.remove("over");
    const a = e.dataTransfer.files[0];
    a && impFile(a);
  }
}), boot();

var _lastMob = null;

addEventListener("resize", () => {
  (_lastPhone !== null && isPhone() !== _lastPhone || _lastMob !== null && isMobileUI() !== _lastMob) && scheduleRender();
}), document.addEventListener("click", e => {
  document.querySelectorAll("details.menu[open]").forEach(t => {
    t.contains(e.target) || t.removeAttribute("open");
  });
}), document.addEventListener("change", e => {
  const t = e.target;
  if (t.matches && t.matches('select[data-bind^="payouts|"][data-bind$="|status"]') && t.value === "paid") {
    const a = t.dataset.bind.split("|")[1];
    setTimeout(() => openShare("payout", a), 450);
  }
}), setTimeout(() => {
  const e = document.getElementById("splash");
  e && e.remove();
}, 4e3);
