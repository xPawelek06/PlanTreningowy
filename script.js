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

// TODO po wdrożeniu na Render: podmień na prawdziwy URL backendu
// (Render Dashboard -> plan-treningowy-api -> adres na górze strony).
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

  tr.appendChild(
    makeEl("td", { text: exercise.sets_reps, attrs: { "data-label": "Serie x powtórzenia" } })
  );
  tr.appendChild(
    makeEl("td", { text: exercise.tm_info || "—", attrs: { "data-label": "TM" } })
  );

  const zapasCell = makeEl("td", { attrs: { "data-label": "Zapas" } });
  const zapasInput = makeEl("input", { attrs: { type: "text", placeholder: "np. spory – 3" } });
  zapasInput.value = exercise.latest_zapas || "";
  zapasCell.appendChild(zapasInput);
  tr.appendChild(zapasCell);

  const uwagiCell = makeEl("td", { attrs: { "data-label": "Uwagi" } });
  const uwagiInput = makeEl("input", { attrs: { type: "text", placeholder: "np. bolało ramię" } });
  uwagiInput.value = exercise.latest_uwagi || "";
  uwagiCell.appendChild(uwagiInput);
  tr.appendChild(uwagiCell);

  const actionCell = makeEl("td", { attrs: { "data-label": "" }, className: "action-cell" });
  const saveBtn = makeEl("button", { text: "Zapisz", className: "save-btn" });
  const status = makeEl("span", { className: "save-status" });
  saveBtn.addEventListener("click", () =>
    saveEntry(exercise.id, zapasInput.value, uwagiInput.value, saveBtn, status)
  );
  actionCell.appendChild(saveBtn);
  actionCell.appendChild(status);
  tr.appendChild(actionCell);

  return tr;
}

async function loadPlan() {
  setLoadStatus("Ładowanie planu…", false);
  try {
    const resp = await fetch(`${API_BASE}/api/plan`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
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

async function saveEntry(exerciseId, zapas, uwagi, button, statusEl) {
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
      body: JSON.stringify({ exercise_id: exerciseId, zapas, uwagi }),
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
