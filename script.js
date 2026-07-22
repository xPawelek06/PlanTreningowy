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
const API_BASE = "https://plan.136-113-151-64.sslip.io";

let authSecret = "";
// Referencja do ostatnio dodanego listenera "resize" dla suwakow poziomego
// przewijania w zakladce Trend - patrz attachDayScrollbarSync() nizej.
let trendResizeHandler = null;

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

// --- Trend: historia poprzednich tygodni, tabela przestawna (pivot) ---
//
// Uklad (ustalony z Pawlem 2026-07-13): wiersze = cwiczenia pogrupowane per
// dzien (jak dawniej), kolumny = tygodnie rosnace w prawo (najstarszy po
// lewej, najnowszy po prawej), kazdy tydzien to para kolumn "Obciazenie" /
// "Serie x powtorzenia" pod wspolnym naglowkiem z zakresem dat. Pierwsza
// kolumna (nazwa cwiczenia) jest przypieta (position: sticky) podczas
// przewijania w poziomie - patrz .sticky-col w style.css.
//
// Cwiczenia dopasowywane sa po kluczu "day|exercise_key" (dodane 2026-07-14) -
// exercise_key to staly identyfikator cwiczenia nadawany recznie w
// seed_data.py, niezalezny od wyswietlanej nazwy, wiec rename w planie juz
// NIE tworzy nowego wiersza w pivotcie, tylko kontynuuje historie starego.
// Wiersze sprzed migracji danych (patrz backend/migrate_exercise_keys.py) nie
// maja jeszcze exercise_key wypelnionego - dla nich trendKey() spada z
// powrotem na "day|name" (stare zachowanie), zeby nic sie nie wywalilo, zanim
// migracja zostanie zatwierdzona i wykonana.
function trendKey(row) {
  return `${row.day}|${row.exercise_key || row.name}`;
}

function buildTrendPivot(rows) {
  // rows: plaska lista z backendu, posortowana week_start desc, day_order, position.
  const weekMap = new Map();
  for (const row of rows) {
    let week = weekMap.get(row.week_start);
    if (!week) {
      week = { week_start: row.week_start, week_end: row.week_end, byKey: new Map() };
      weekMap.set(row.week_start, week);
    }
    week.byKey.set(trendKey(row), row);
  }

  // Najstarszy tydzien pierwszy (lewa kolumna) -> najnowszy ostatni (prawa kolumna).
  const weeks = Array.from(weekMap.values()).sort((a, b) =>
    a.week_start < b.week_start ? -1 : a.week_start > b.week_start ? 1 : 0
  );
  const newestIdx = weeks.length - 1;

  // Unia (day, name) ze WSZYSTKICH tygodni - zeby wiersz nie znikal tylko
  // dlatego, ze w najnowszym tygodniu danego cwiczenia nie bylo. Dla kazdego
  // klucza zapamietujemy metadane (day_order/position/is_main_lift) z
  // najnowszego tygodnia, w ktorym cwiczenie wystapilo.
  const exerciseMeta = new Map();
  weeks.forEach((week, wIdx) => {
    for (const [key, row] of week.byKey) {
      const existing = exerciseMeta.get(key);
      if (!existing || wIdx > existing.weekIdx) {
        exerciseMeta.set(key, {
          key,
          day: row.day,
          day_order: row.day_order,
          name: row.name,
          exercise_key: row.exercise_key,
          is_main_lift: row.is_main_lift,
          position: row.position,
          weekIdx: wIdx,
        });
      }
    }
  });

  const days = new Map();
  for (const meta of exerciseMeta.values()) {
    let arr = days.get(meta.day);
    if (!arr) {
      arr = [];
      days.set(meta.day, arr);
    }
    arr.push(meta);
  }

  // W obrebie dnia: cwiczenia obecne w najnowszym tygodniu ida pierwsze (wg
  // ich position tam), cwiczenia widoczne juz tylko w starszych tygodniach
  // ida na koniec sekcji dnia (najpierw te z pozniejszego "ostatniego
  // wystapienia", potem wg position).
  for (const arr of days.values()) {
    arr.sort((a, b) => {
      const aOld = a.weekIdx === newestIdx ? 0 : 1;
      const bOld = b.weekIdx === newestIdx ? 0 : 1;
      if (aOld !== bOld) return aOld - bOld;
      if (aOld === 1 && a.weekIdx !== b.weekIdx) return b.weekIdx - a.weekIdx;
      return a.position - b.position;
    });
  }

  const dayList = Array.from(days.values()).sort((a, b) => a[0].day_order - b[0].day_order);

  return { weeks, dayList };
}

// Komorka pivota dla jednego pola (tm_info / sets_reps) jednego cwiczenia w
// jednym tygodniu. Brak wiersza (cwiczenie w tym tygodniu nie wystepowalo /
// tydzien jeszcze nie zarchiwizowany) -> "---", nieedytowalne (nie ma wiersza
// w bazie do edycji). Wiersz istnieje -> edytowalne pole tekstowe (dane
// REALNEGO wykonania treningu, wpisywane recznie przez Pawla - patrz
// saveTrendCell nizej), nawet jesli akurat puste.
function trendCell(row, field) {
  if (!row) {
    return makeEl("td", { text: "---", className: "trend-cell trend-empty" });
  }

  const td = makeEl("td", { className: "trend-cell trend-cell-editable" });
  const value = row[field] || "";
  const rows = Math.min(Math.max(String(value).split("\n").length, 1), 6);
  const textarea = makeEl("textarea", {
    className: "trend-input",
    attrs: { rows: String(rows), spellcheck: "false", placeholder: "—" },
  });
  textarea.value = value;

  const status = makeEl("span", { className: "trend-cell-status" });

  let lastSaved = value;
  textarea.addEventListener("blur", () => {
    const next = textarea.value;
    if (next === lastSaved) return; // bez zmian - nie wysylaj zbednego zapisu
    saveTrendCell(row.id, field, next, textarea, status).then((ok) => {
      if (ok) lastSaved = next;
    });
  });

  td.appendChild(textarea);
  td.appendChild(status);
  return td;
}

// Zapis pojedynczej komorki Trendu (Obciazenie=tm_info / Serie x powtorzenia=
// sets_reps) - on blur z trendCell() wyzej. Ten sam naglowek X-Auth-Secret co
// saveEntry() (zakladka Plan) i ten sam fetchWithRetry co loadPlan/loadTrend,
// zeby zniesc ewentualny "zimny start" backendu na Renderze bez utraty
// wpisanej wartosci.
async function saveTrendCell(snapshotId, field, value, textareaEl, statusEl) {
  textareaEl.disabled = true;
  statusEl.textContent = "Zapisywanie…";
  statusEl.classList.remove("save-error");
  try {
    await fetchWithRetry(`${API_BASE}/api/admin/weekly-trend-snapshot/${snapshotId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Secret": authSecret,
      },
      body: JSON.stringify({ [field]: value }),
    });
    statusEl.textContent = "Zapisano ✓";
    setTimeout(() => {
      statusEl.textContent = "";
    }, 2000);
    return true;
  } catch (err) {
    statusEl.textContent = "Błąd zapisu — spróbuj ponownie";
    statusEl.classList.add("save-error");
    console.error("Błąd zapisu komórki trendu:", err);
    return false;
  } finally {
    textareaEl.disabled = false;
  }
}

// Suwak poziomego przewijania dla jednej sekcji dnia w pivotcie Trendu
// (2026-07-14) - problem: caly pivot to JEDEN szeroki, poziomo scrollowany
// kontener (.trend-pivot-wrap), a jedyny scrollbar renderowany przez
// przegladarke siedzi na samym DOLE tej (bardzo wysokiej) tabeli. Zeby
// porownac tygodnie dla dnia na gorze (np. Poniedzialek), trzeba bylo
// scrollowac na sam dol strony. Rozwiazanie: przy KAZDYM dniu wstawiamy
// dodatkowy wiersz z mini-suwakiem - divem z overflow-x:auto i
// position:sticky;left:0, wiec ten div zawsze zajmuje dokladnie widoczna
// szerokosc viewportu kontenera (tak samo jak przypieta kolumna nazwy
// cwiczenia, .sticky-col, ktora dziala na tej samej zasadzie), niezaleznie od
// tego, jak szeroka jest cala tabela pod spodem. Wewnatrz jest "track" div o
// szerokosci calej tabeli - sam scrollowanie tego paska ustawia scrollLeft
// prawdziwego kontenera (i odwrotnie), patrz attachDayScrollbarSync() nizej.
function createDayScrollbarRow(totalCols) {
  const row = makeEl("tr", { className: "trend-day-scrollbar-row" });
  const td = makeEl("td");
  td.colSpan = totalCols;
  const bar = makeEl("div", { className: "trend-day-scrollbar" });
  const track = makeEl("div", { className: "trend-day-scrollbar-track" });
  bar.appendChild(track);
  td.appendChild(bar);
  row.appendChild(td);
  return { row, bar, track };
}

// Synchronizuje scrollLeft prawdziwego kontenera (wrap) z kazdym mini-suwakiem
// (bars: lista { bar, track }) w obie strony. Flaga "syncing" chroni przed
// nieskonczona petla zdarzen scroll (ustawienie .scrollLeft programowo tez
// odpala 'scroll').
function attachDayScrollbarSync(wrap, table, bars) {
  let syncing = false;

  function applyScrollLeft(value, source) {
    syncing = true;
    if (wrap !== source) wrap.scrollLeft = value;
    for (const { bar } of bars) {
      if (bar !== source) bar.scrollLeft = value;
    }
    syncing = false;
  }

  wrap.addEventListener("scroll", () => {
    if (syncing) return;
    applyScrollLeft(wrap.scrollLeft, wrap);
  });
  for (const { bar } of bars) {
    bar.addEventListener("scroll", () => {
      if (syncing) return;
      applyScrollLeft(bar.scrollLeft, bar);
    });
  }

  // Szerokosc mini-suwaka (viewport) i jego wewnetrznego "toru" (pelna
  // szerokosc tabeli) trzeba przeliczyc po zbudowaniu DOM (dopiero wtedy
  // znane sa prawdziwe wymiary) i przy kazdej zmianie rozmiaru okna/orientacji.
  function syncWidths() {
    const viewWidth = wrap.clientWidth;
    const fullWidth = table.scrollWidth;
    for (const { bar, track } of bars) {
      bar.style.width = `${viewWidth}px`;
      track.style.width = `${fullWidth}px`;
    }
  }

  syncWidths();
  // renderTrendPivot() moze w zasadzie zostac wywolane ponownie (np. w
  // przyszlosci przy odswiezaniu bez przeladowania strony) - zdejmujemy
  // poprzedni listener resize, zeby nie mnozyc ich przy kazdym renderze
  // (stare zamkniecia trzymalyby referencje do juz odlaczonych elementow DOM).
  if (trendResizeHandler) window.removeEventListener("resize", trendResizeHandler);
  trendResizeHandler = syncWidths;
  window.addEventListener("resize", trendResizeHandler);
}

function renderTrendPivot(rows) {
  const container = document.getElementById("trend-weeks");
  container.innerHTML = "";

  if (!rows.length) {
    container.appendChild(
      makeEl("p", {
        className: "load-status",
        text: "Brak zapisanych tygodni jeszcze — pojawi się po pierwszej cotygodniowej archiwizacji.",
      })
    );
    return;
  }

  const { weeks, dayList } = buildTrendPivot(rows);

  const wrap = makeEl("div", { className: "table-wrap trend-pivot-wrap" });
  const table = makeEl("table", { className: "trend-pivot" });

  const thead = document.createElement("thead");
  const headRow1 = document.createElement("tr");
  const cornerTh = makeEl("th", { className: "sticky-col", text: "Ćwiczenie" });
  cornerTh.rowSpan = 2;
  headRow1.appendChild(cornerTh);
  for (const week of weeks) {
    const th = makeEl("th", {
      className: "trend-week-head",
      text: `${week.week_start} – ${week.week_end}`,
    });
    th.colSpan = 2;
    headRow1.appendChild(th);
  }
  const headRow2 = document.createElement("tr");
  for (const week of weeks) {
    headRow2.appendChild(makeEl("th", { text: "Obciążenie" }));
    headRow2.appendChild(makeEl("th", { text: "Serie x powtórzenia" }));
  }
  thead.appendChild(headRow1);
  thead.appendChild(headRow2);
  table.appendChild(thead);

  const totalCols = 1 + weeks.length * 2;
  const dayScrollbars = [];

  const tbody = document.createElement("tbody");
  for (const arr of dayList) {
    const dayRow = makeEl("tr", { className: "trend-day-row" });
    dayRow.appendChild(makeEl("td", { className: "sticky-col trend-day-cell", text: arr[0].day }));
    const spacer = makeEl("td", { className: "trend-day-spacer" });
    spacer.colSpan = weeks.length * 2;
    dayRow.appendChild(spacer);
    tbody.appendChild(dayRow);

    const { row: scrollbarRow, bar, track } = createDayScrollbarRow(totalCols);
    tbody.appendChild(scrollbarRow);
    dayScrollbars.push({ bar, track });

    for (const meta of arr) {
      const tr = document.createElement("tr");
      const nameCell = makeEl("td", { className: "sticky-col" });
      if (meta.is_main_lift) {
        const strong = document.createElement("strong");
        strong.textContent = meta.name;
        nameCell.appendChild(strong);
      } else {
        nameCell.textContent = meta.name;
      }
      tr.appendChild(nameCell);

      for (const week of weeks) {
        const row = week.byKey.get(meta.key);
        tr.appendChild(trendCell(row, "tm_info"));
        tr.appendChild(trendCell(row, "sets_reps"));
      }
      tbody.appendChild(tr);
    }
  }
  table.appendChild(tbody);
  wrap.appendChild(table);
  container.appendChild(wrap);

  // Dopiero po wpieciu do DOM (container.appendChild wyzej) mierzalne sa
  // prawdziwe wymiary (clientWidth/scrollWidth) potrzebne do zsynchronizowania
  // mini-suwakow z kontenerem - patrz attachDayScrollbarSync().
  attachDayScrollbarSync(wrap, table, dayScrollbars);
}

async function loadTrend() {
  const statusEl = document.getElementById("trend-status");
  statusEl.textContent = "Ładowanie… (jeśli backend spał, może to potrwać do 30 sek)";
  statusEl.classList.remove("hidden", "load-error");
  try {
    const resp = await fetchWithRetry(`${API_BASE}/api/weekly-trend`);
    const rows = await resp.json();
    renderTrendPivot(rows);
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
