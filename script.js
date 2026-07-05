// Prosta blokada hasłem po stronie klienta.
// To NIE jest prawdziwe zabezpieczenie (kod i hash są jawne w źródle strony) —
// to tylko odstraszacz przed przypadkowym trafieniem na stronę.
//
// Hasło nie jest trzymane jawnie w kodzie — porównujemy hash SHA-256 wpisanego
// hasła z hashem poprawnego hasła (obliczonym raz, wklejonym poniżej).
const CORRECT_HASH =
  "775704b885efc19d910e9f614108e6199876d1ad2070017948a5acd805229e5c";
const SESSION_KEY = "plan-treningowy-unlocked";

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
}

async function tryUnlock() {
  const input = document.getElementById("password-input");
  const error = document.getElementById("lock-error");
  const value = input.value;
  const hash = await sha256Hex(value);

  if (hash === CORRECT_HASH) {
    sessionStorage.setItem(SESSION_KEY, "1");
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
  showContent();
}
