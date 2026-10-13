"use strict";
const $ = (id) => document.getElementById(id);
let state = null,
  busy = false,
  lang = localStorage.getItem("blockops-lang") || "fr";
const en = {
  "login-first": "Your world.",
  "login-second": "In safe hands.",
  "login-copy": "Monitor your server. Keep a copy.",
  "login-rest": "Start again with confidence.",
  "username-label": "Local username",
  "password-label": "Password",
  "login-submit": "Open console",
  "login-hint": "Access is reserved for users of this installation.",
  discover: "Explore BlockOps",
  title: "Overview",
  subtitle: "Less babysitting. More playing.",
  start: "Start",
  stop: "Stop",
  restart: "Restart",
  backup: "Create backup",
  "players-label": "PLAYERS • RECENT LOGS",
  "copies-label": "SAVED COPIES",
  "rule-label": "CAUTIOUS RESTART",
  "player-note": "Estimated from recent connection events.",
  "copy-note": "A local copy. A safer fresh start.",
  "rule-note": "3 observations · 2 attempts / hour",
  "backup-title": "Your recovery points",
  "backup-note":
    "Consistent copy: server stopped during backup. Restore leaves the server stopped.",
  "settings-title": "Set your own rhythm",
  "interval-label": "Interval (hours)",
  "retention-label": "Copies (2–30)",
  "auto-label": "Restart after a crash",
  "auto-note": "Never after an intentional stop. Off by default.",
  save: "Save rules",
  "logs-title": "Server journal",
  "refresh-note": "Refreshes every 10 s",
  "alerts-title": "Keep an eye on it",
  logout: "Sign out",
  cancel: "Cancel",
  "confirm-btn": "Confirm",
  "server-label": "DOCKER SERVER",
  "storage-note": "Copies on your host · no remote storage",
};
const fr = {};
Object.keys(en).forEach((k) => (fr[k] = $(k).textContent.trim()));
function translate() {
  document.documentElement.lang = lang;
  Object.keys(en).forEach((k) => label(k, (lang === "en" ? en : fr)[k]));
  label("language", lang === "en" ? "FR" : "EN");
  $("server-actions").setAttribute(
    "aria-label",
    lang === "en" ? "Server lifecycle" : "Cycle de vie du serveur",
  );
  $("logs").setAttribute(
    "aria-label",
    lang === "en" ? "Server journal" : "Journal du serveur",
  );
  updateThemeControl();
}
$("language").onclick = () => {
  lang = lang === "en" ? "fr" : "en";
  localStorage.setItem("blockops-lang", lang);
  translate();
  if (state) render();
};
translate();
let theme =
  localStorage.getItem("blockops-theme") ||
  (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
document.documentElement.dataset.theme = theme;
$("theme").onclick = () => {
  theme = theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("blockops-theme", theme);
  updateThemeControl();
};
updateThemeControl();
function label(id, text) {
  const target = $(id);
  (target.querySelector("[data-label]") || target).textContent = text;
}
function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"),
    use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  svg.setAttribute("class", "icon");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  use.setAttribute("href", "/assets/lucide/sprite.svg#" + name);
  svg.append(use);
  return svg;
}
function updateThemeControl() {
  const dark = document.documentElement.dataset.theme === "dark";
  $("theme").setAttribute(
    "aria-label",
    lang === "en"
      ? dark
        ? "Switch to light theme"
        : "Switch to dark theme"
      : dark
        ? "Passer au thème clair"
        : "Passer au thème sombre",
  );
  $("theme-icon").setAttribute(
    "href",
    "/assets/lucide/sprite.svg#" + (dark ? "sun" : "moon"),
  );
}
function error(text) {
  $("error").hidden = !text;
  label("error", text || "");
}
async function api(path, data) {
  const r = await fetch("/api/" + path, {
    method: data ? "POST" : "GET",
    headers: data
      ? {
          "Content-Type": "application/json",
          "X-CSRF-Token": state?.csrf || "",
        }
      : {},
    body: data ? JSON.stringify(data) : undefined,
  });
  const j = await r.json();
  if (!r.ok) {
    if (r.status === 401 && path !== "login") {
      state = null;
      $("console").hidden = true;
      $("login").hidden = false;
      $("logout").hidden = true;
    }
    const e = Error(j.error);
    e.status = r.status;
    throw e;
  }
  return j;
}
function feedback(text) {
  $("feedback").hidden = !text;
  label("feedback", text || "");
}
function backupDate(id) {
  const m = id.match(/backup-(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})/);
  return m
    ? new Date(
        Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]),
      ).toLocaleString(lang, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : id;
}
function el(tag, text, cls) {
  const e = document.createElement(tag);
  e.textContent = text;
  if (cls) e.className = cls;
  return e;
}
function render() {
  $("console").hidden = false;
  $("login").hidden = true;
  $("logout").hidden = false;
  $("server-name").textContent = state.server.name;
  label(
    "status",
    state.server.running
      ? lang === "en"
        ? "Running"
        : "En marche"
      : lang === "en"
        ? "Stopped"
        : "Arrêté",
  );
  $("status").classList.toggle("stopped", !state.server.running);
  $("status-icon").setAttribute(
    "href",
    "/assets/lucide/sprite.svg#" +
      (state.server.running ? "circle-check" : "circle-pause"),
  );
  $("role-label").textContent =
    state.role === "admin"
      ? lang === "en"
        ? "Administrator"
        : "Administrateur"
      : lang === "en"
        ? "View only"
        : "Lecture seule";
  $("mode").textContent = state.fixture
    ? state.fixture_transport === "local"
      ? "LOCAL QA FIXTURE"
      : "DOCKER FIXTURE"
    : "SELF-HOSTED";
  $("notice").hidden = !state.fixture;
  label(
    "notice",
    state.fixture_transport === "local"
      ? lang === "en"
        ? "Local QA fixture • Simulated Docker Engine, no Minecraft binary. Real world files and backup/restore."
        : "Fixture locale • Docker Engine simulé, aucun binaire Minecraft. Fichiers et backup/restauration réels."
      : lang === "en"
        ? "Disposable fixture • No Minecraft binary. World files and Docker operations are real."
        : "Fixture jetable • Aucun binaire Minecraft. Fichiers monde et opérations Docker réels.",
  );
  $("players").textContent =
    state.player_status.online ?? (state.fixture ? state.players.length : "—");
  $("players-label").textContent =
    state.player_status.source === "server_list_ping"
      ? lang === "en"
        ? "PLAYERS • SERVER STATUS"
        : "JOUEURS • STATUT SERVEUR"
      : lang === "en"
        ? "PLAYERS • RECENT LOGS"
        : "JOUEURS • LOGS RÉCENTS";
  $("player-note").textContent =
    state.player_status.source === "server_list_ping"
      ? lang === "en"
        ? "Reported by the Java server."
        : "Déclaré par le serveur Java."
      : lang === "en"
        ? "Live count unavailable. Log events may be incomplete."
        : "Nombre en direct indisponible. Logs potentiellement incomplets.";
  $("players").title = state.players.join(", ");
  $("copies").textContent = state.backups.length;
  $("rule").textContent = state.config.auto_restart
    ? lang === "en"
      ? "Enabled"
      : "Activé"
    : lang === "en"
      ? "Manual"
      : "Manuel";
  $("logs").textContent =
    state.logs || (lang === "en" ? "No recent logs." : "Aucun log récent.");
  if (document.activeElement.closest("form") !== $("settings")) {
    $("interval").value = state.config.backup_hours;
    $("retention").value = state.config.retention;
    $("auto").checked = state.config.auto_restart;
  }
  $("backups").replaceChildren();
  if (!state.backups.length) {
    const empty = el("div", "", "empty");
    empty.append(
      icon("archive"),
      el(
        "span",
        lang === "en"
          ? "No recovery point yet. Create your first copy."
          : "Aucun point de retour. Créez votre première copie.",
      ),
    );
    $("backups").append(empty);
  }
  state.backups.forEach((b) => {
    const row = el("div", "", "backup-row"),
      badge = el("div", "", "backup-symbol"),
      info = el("div", "", "backup-info");
    badge.append(icon("archive"));
    info.append(
      el("strong", backupDate(b.id)),
      el(
        "small",
        `${(b.bytes / 1024).toFixed(1)} KB · SHA256 ${b.sha256.slice(0, 12)}`,
      ),
    );
    const btn = el("button", "");
    btn.append(
      icon("archive-restore"),
      el("span", lang === "en" ? "Restore" : "Restaurer"),
    );
    btn.onclick = () => action("restore", b.id);
    btn.disabled = busy || state.role !== "admin";
    row.append(badge, info, btn);
    $("backups").append(row);
  });
  $("alerts").replaceChildren();
  if (!state.alerts.length) {
    const empty = el("div", "", "empty");
    empty.append(
      icon("bell"),
      el(
        "span",
        lang === "en"
          ? "No activity recorded yet."
          : "Aucune activité enregistrée.",
      ),
    );
    $("alerts").append(empty);
  }
  state.alerts.slice(0, 8).forEach((a) => {
    const row = el("div", "", "activity"),
      copy = el("div", a.message);
    const name = /failed|offline/i.test(a.message)
      ? "circle-alert"
      : /restored/i.test(a.message)
        ? "archive-restore"
        : /backup/i.test(a.message)
          ? "hard-drive-download"
          : /restart/i.test(a.message)
            ? "rotate-cw"
            : /requested stop/i.test(a.message)
              ? "square"
              : /requested start/i.test(a.message)
                ? "play"
                : "bell";
    copy.append(el("time", new Date(a.at).toLocaleString(lang)));
    row.append(icon(name), copy);
    $("alerts").append(row);
  });
  $("settings")
    .querySelectorAll("input,button")
    .forEach((e) => (e.disabled = busy || state.role !== "admin"));
  document
    .querySelectorAll("[data-action]")
    .forEach((e) => (e.disabled = busy || state.role !== "admin"));
}
async function refresh() {
  if (busy) return;
  try {
    state = await api("state");
    render();
    error("");
  } catch (e) {
    if (e.status !== 401) error(e.message);
  }
}
async function action(a, id) {
  const labels =
    lang === "en"
      ? {
          start: "start server",
          stop: "stop server",
          restart: "restart server",
          backup: "create backup",
          restore: "restore world",
        }
      : {
          start: "démarrer le serveur",
          stop: "arrêter le serveur",
          restart: "redémarrer le serveur",
          backup: "créer une copie",
          restore: "restaurer le monde",
        };
  $("confirm-title").textContent =
    (lang === "en" ? "Confirm: " : "Confirmer : ") + labels[a];
  $("confirm-text").textContent =
    a === "restore"
      ? lang === "en"
        ? "Replaces the world after a safety backup. Server stays stopped. Inspect it before starting."
        : "Remplace le monde après une copie de sécurité. Le serveur reste arrêté. Inspectez-le avant de démarrer."
      : a === "backup"
        ? lang === "en"
          ? "The server will stop during the copy and resume if it was running. Players will disconnect."
          : "Le serveur sera arrêté pendant la copie, puis relancé s’il était en marche. Les joueurs seront déconnectés."
        : lang === "en"
          ? "This changes the container lifecycle. Stopping or restarting disconnects players."
          : "Cette opération change le cycle de vie du conteneur. Un arrêt ou redémarrage déconnecte les joueurs.";
  $("confirm").returnValue = "";
  $("confirm").showModal();
  const yes = await new Promise((resolve) =>
    $("confirm").addEventListener(
      "close",
      () => resolve($("confirm").returnValue === "confirm"),
      { once: true },
    ),
  );
  if (!yes) return;
  busy = true;
  let failure = null;
  feedback(
    lang === "en"
      ? "Operation in progress. Wait before closing this console."
      : "Opération en cours. Patientez avant de fermer la console.",
  );
  render();
  try {
    await api("action", { action: a, id, confirmation: "CONFIRM" });
    error("");
  } catch (e) {
    failure = e.message;
  } finally {
    busy = false;
    await refresh();
    if (failure) {
      feedback("");
      error(failure);
    } else
      feedback(
        lang === "en"
          ? "Operation completed. Review server state and activity below."
          : "Opération terminée. Vérifiez l’état du serveur et l’activité ci-dessous.",
      );
  }
}
document
  .querySelectorAll("[data-action]")
  .forEach((e) => (e.onclick = () => action(e.dataset.action)));
$("login-form").onsubmit = async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button");
  btn.disabled = true;
  try {
    await api("login", {
      username: $("username").value,
      password: $("password").value,
    });
    $("password").value = "";
    await refresh();
  } catch (e) {
    error(e.message);
  } finally {
    btn.disabled = false;
  }
};
$("settings").onsubmit = async (e) => {
  e.preventDefault();
  try {
    await api("config", {
      backup_hours: Number($("interval").value),
      retention: Number($("retention").value),
      auto_restart: $("auto").checked,
    });
    await refresh();
    feedback(
      lang === "en"
        ? "Rules saved on this installation."
        : "Règles enregistrées sur cette installation.",
    );
  } catch (e) {
    error(e.message);
  }
};
$("logout").onclick = async () => {
  try {
    await api("logout", {});
    state = null;
    $("console").hidden = true;
    $("login").hidden = false;
    $("logout").hidden = true;
  } catch (e) {
    error(e.message);
  }
};
refresh();
setInterval(refresh, 10000);
