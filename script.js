// Prosta blokada hasłem po stronie klienta.
// To NIE jest prawdziwe zabezpieczenie (kod i hash są jawne w źródle strony) —
// to tylko odstraszacz przed przypadkowym trafieniem na stronę.
//
// UWAGA v2: to samo hasło ("PlanTreningowy") jest teraz też sekretem wysyłanym
// do backendu przy zapisie (nagłówek X-Auth-Secret) — patrz saveEntry() niżej.
const CORRECT_HASH =
  "775704b885efc19d910e9f614108e6199876d1ad2070017948a5acd805229e5c";
const SESSION_KEY = "plan-treningowy-unlocked";
const SECRET_SESSION_KEY = "plan-treningowy-secret";

// Backend wdrożony i zweryfikowany na Renderze (2026-07-05) - to prawdziwy,
// żywy URL, połączony z bazą Neon.
const API_BASE = "https://plan-treningowy-api.onrender.com";

let authSecret = "";

async function sha256Hex(text) {
  const data = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function showContent() {
  document.getElementById("lock-screen").classList.add("hidden");
  document.getElementById("content").classList.remove("hidden");
  loadPlan();
  loadTrend();
}

async function tryUnlock() {
  const input = document.getElementById("password-input");
  const error = document.getElementById("lock-error");
  const value = input.value;
  const hash = await sha256Hex(value);

  if (hash === CORRECT_HASH) {
    authSecret = value;
    sessionStorage.setItem(SESSION_KEY, "1");
    sessionStorage.setItem(SECRET_SESSION_KEY, value);
    showContent();
  } else {
    error.textContent = "Złe hasło, spróbuj ponownie.";
    input.value = "";
    input.focus();
  }
}

document.getElementById("unlock-btn").addEventListener("click", tryUnlock);
document.getElementById("password-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") tryUnlock();
});

// Jeśli już odblokowano w tej karcie/sesji przeglądarki, nie pytaj ponownie.
if (sessionStorage.getItem(SESSION_KEY) === "1") {
  authSecret = sessionStorage.getItem(SECRET_SESSION_KEY) || "";
  showContent();
}

// --- Zakładki ---

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.add("hidden"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.remove("hidden");
  });
});

// --- Plan: pobranie z API i render tabel ---

function setLoadStatus(text, isError) {
  const statusEl = document.getElementById("load-status");
  if (!text) {
    statusEl.classList.add("hidden");
    return;
  }
  statusEl.textContent = text;
  statusEl.classList.remove("hidden");
  statusEl.classList.toggle("load-error", Boolean(isError));
}

function makeEl(tag, opts) {
  const node = document.createElement(tag);
  opts = opts || {};
  if (opts.text !== undefined) node.textContent = opts.text;
  if (opts.className) node.className = opts.className;
  if (opts.attrs) {
    for (const [k, v] of Object.entries(opts.attrs)) node.setAttribute(k, v);
  }
  return node;
}

// Komorka, ktora rozbija tekst na osobne linie po znaku nowej linii (\n).
// Dla wartosci bez \n (wiekszosc dni) zachowuje sie jak zwykla, jednoliniowa
// komorka - wiec zmiana dotyczy tylko wierszy z wieloliniowym breakdownem.
function multilineCell(text, label) {
  const td = makeEl("td", { attrs: { "data-label": label } });
  const lines = String(text).split("\n");
  if (lines.length === 1) {
    td.textContent = lines[0];
    return td;
  }
  const wrap = makeEl("div", { className: "lines" });
  for (const line of lines) {
    wrap.appendChild(makeEl("div", { text: line, className: "line" }));
  }
  td.appendChild(wrap);
  return td;
}

function buildRow(exercise) {
  const tr = document.createElement("tr");

  const nameCell = makeEl("td", { attrs: { "data-label": "Ćwiczenie" } });
  if (exercise.is_main_lift) {
    const strong = document.createElement("strong");
    strong.textContent = exercise.name;
    nameCell.appendChild(strong);
  } else {
    nameCell.textContent = exercise.name;
  }
  tr.appendChild(nameCell);

  tr.appendChild(multilineCell(exercise.sets_reps, "Serie x powtórzenia"));
  tr.appendChild(multilineCell(exercise.tm_info || "—", "TM"));

  const zapasCell = makeEl("td", { attrs: { "data-label": "Zapas" } });
  const zapasInput = makeEl("input", { attrs: { type: "text"} });
  zapasInput.value = exercise.latest_zapas || "";
  zapasCell.appendChild(zapasInput);
  tr.appendChild(zapasCell);

  const seriaPlusCell = makeEl("td", { attrs: { "data-label": "Seria +" } });
  const seriaPlusInput = makeEl("input", { attrs: { type: "text"} });
  seriaPlusInput.value = exercise.latest_seria_plus || "";
  seriaPlusCell.appendChild(seriaPlusInput);
  tr.appendChild(seriaPlusCell);

  const uwagiCell = makeEl("td", { attrs: { "data-label": "Uwagi" } });
  const uwagiInput = makeEl("input", { attrs: { type: "text"} });
  uwagiInput.value = exercise.latest_uwagi || "";
  uwagiCell.appendChild(uwagiInput);
  tr.appendChild(uwagiCell);

  const actionCell = makeEl("td", { attrs: { "data-label": "" }, className: "action-cell" });
  const saveBtn = makeEl("button", { text: "Zapisz", className: "save-btn" });
  const status = makeEl("span", { className: "save-status" });
  saveBtn.addEventListener("click", () =>
    saveEntry(exercise.id, zapasInput.value, seriaPlusInput.value, uwagiInput.value, saveBtn, status)
  );
  actionCell.appendChild(saveBtn);
  actionCell.appendChild(status);
  tr.appendChild(actionCell);

  return tr;
}

// Fetch z ponawianiem: darmowy plan Render usypia backend/baze po ~15 min
// bezczynnosci - pierwszy request po uspieniu regularnie konczy sie 500/timeoutem
// (baza jeszcze sie "budzi"), kolejny juz przechodzi. Telefon jest zwykle
// otwierany po dluzszej przerwie (backend zimny) - stad appka bywa pusta zaraz
// po otwarciu, choc odswiezenie po chwili juz dziala. Ponawiamy kilka razy
// zanim pokazemy blad (ten sam wzorzec co appka Waga, naprawiona 2026-07-13).
async function fetchWithRetry(url, options, attempts, delayMs) {
  attempts = attempts || 3;
  delayMs = delayMs || 1500;
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      const resp = await fetch(url, options);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return resp;
    } catch (err) {
      lastErr = err;
      if (i < attempts - 1) {
        await new Promise((r) => setTimeout(r, delayMs * (i + 1)));
      }
    }
  }
  throw lastErr;
}

async function loadPlan() {
  setLoadStatus("Ładowanie planu… (jeśli backend spał, może to potrwać do 30 sek)", false);
  try {
    const resp = await fetchWithRetry(`${API_BASE}/api/plan`);
    const exercises = await resp.json();

    document.querySelectorAll("tbody[data-day]").forEach((tbody) => {
      tbody.innerHTML = "";
    });

    for (const exercise of exercises) {
      const tbody = document.querySelector(`tbody[data-day="${exercise.day}"]`);
      if (!tbody) continue; // dzień spoza znanej listy - pomijamy
      tbody.appendChild(buildRow(exercise));
    }

    setLoadStatus(null);
  } catch (err) {
    setLoadStatus(
      "Nie udało się połączyć z serwerem planu. Sprawdź internet i spróbuj odświeżyć stronę.",
      true
    );
    console.error("Błąd ładowania planu:", err);
  }
}

// --- Trend: historia poprzednich tygodni (zrzuty planu) ---

function groupTrendByWeek(rows) {
  // rows juz posortowane przez backend: week_start desc, day_order, position.
  const weeks = [];
  const byWeekStart = new Map();
  for (const row of rows) {
    let week = byWeekStart.get(row.week_start);
    if (!week) {
      week = { week_start: row.week_start, week_end: row.week_end, days: new Map() };
      byWeekStart.set(row.week_start, week);
      weeks.push(week);
    }
    let dayRows = week.days.get(row.day);
    if (!dayRows) {
      dayRows = [];
      week.days.set(row.day, dayRows);
    }
    dayRows.push(row);
  }
  return weeks;
}

function buildTrendRow(exercise) {
  const tr = document.createElement("tr");

  const nameCell = makeEl("td", { attrs: { "data-label": "Ćwiczenie" } });
  if (exercise.is_main_lift) {
    const strong = document.createElement("strong");
    strong.textContent = exercise.name;
    nameCell.appendChild(strong);
  } else {
    nameCell.textContent = exercise.name;
  }
  tr.appendChild(nameCell);

  tr.appendChild(multilineCell(exercise.tm_info || "—", "Obciążenie"));
  tr.appendChild(multilineCell(exercise.sets_reps, "Serie x powtórzenia"));

  return tr;
}

function renderTrendWeeks(weeks) {
  const container = document.getElementById("trend-weeks");
  container.innerHTML = "";

  if (!weeks.length) {
    container.appendChild(
      makeEl("p", {
        className: "load-status",
        text: "Brak zapisanych tygodni jeszcze — pojawi się po pierwszej cotygodniowej archiwizacji.",
      })
    );
    return;
  }

  for (const week of weeks) {
    const section = makeEl("div", { className: "trend-week" });
    section.appendChild(
      makeEl("h2", { className: "trend-week-title", text: `Tydzień ${week.week_start} – ${week.week_end}` })
    );

    for (const [day, rows] of week.days) {
      const dayBlock = makeEl("div", { className: "trend-day" });
      dayBlock.appendChild(makeEl("h3", { className: "trend-day-title", text: day }));

      const tableWrap = makeEl("div", { className: "table-wrap" });
      const table = document.createElement("table");
      const thead = document.createElement("thead");
      thead.innerHTML =
        "<tr><th>Ćwiczenie</th><th>Obciążenie</th><th>Serie x powtórzenia</th></tr>";
      const tbody = document.createElement("tbody");
      for (const row of rows) {
        tbody.appendChild(buildTrendRow(row));
      }
      table.appendChild(thead);
      table.appendChild(tbody);
      tableWrap.appendChild(table);
      dayBlock.appendChild(tableWrap);
      section.appendChild(dayBlock);
    }

    container.appendChild(section);
  }
}

async function loadTrend() {
  const statusEl = document.getElementById("trend-status");
  statusEl.textContent = "Ładowanie… (jeśli backend spał, może to potrwać do 30 sek)";
  statusEl.classList.remove("hidden", "load-error");
  try {
    const resp = await fetchWithRetry(`${API_BASE}/api/weekly-trend`);
    const rows = await resp.json();
    const weeks = groupTrendByWeek(rows);
    renderTrendWeeks(weeks);
    statusEl.classList.add("hidden");
  } catch (err) {
    statusEl.textContent = "Nie udało się pobrać historii tygodni. Sprawdź internet i spróbuj odświeżyć stronę.";
    statusEl.classList.add("load-error");
    console.error("Błąd ładowania trendu:", err);
  }
}

async function saveEntry(exerciseId, zapas, seriaPlus, uwagi, button, statusEl) {
  button.disabled = true;
  statusEl.textContent = "Zapisywanie…";
  statusEl.classList.remove("save-error");
  try {
    const resp = await fetch(`${API_BASE}/api/entries`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Secret": authSecret,
      },
      body: JSON.stringify({ exercise_id: exerciseId, zapas, seria_plus: seriaPlus, uwagi }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    statusEl.textContent = "Zapisano ✓";
    setTimeout(() => {
      statusEl.textContent = "";
    }, 2500);
  } catch (err) {
    statusEl.textContent = "Błąd zapisu";
    statusEl.classList.add("save-error");
    console.error("Błąd zapisu wpisu:", err);
  } finally {
    button.disabled = false;
  }
}
