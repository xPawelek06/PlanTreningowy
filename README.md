# Plan Treningowy

Statyczna strona z podglądem planu treningowego Pawła (trójbój siłowy + bieganie +
kalistenika). Zamiennik appki GymSage na czas jej przebudowy — czysty HTML/CSS/JS,
bez frameworków i backendu.

- Chroniona prostym hasłem po stronie klienta (JS, patrz `script.js`) — to tylko
  odstraszacz, nie prawdziwe zabezpieczenie.
- Dane (plan ćwiczeń, TM, obciążenia) pochodzą z repo "mózgu" Pawła:
  `silownia/plan-tygodniowy.md` i `silownia/progresja.md`. Ta strona jest
  regenerowana ręcznie przy każdej zmianie tamtych plików.
- Wyłącznie podgląd — brak zapisu/formularzy. Zapas i uwagi z treningu Paweł
  zgłasza trenerowi w rozmowie, nie tutaj.

Publikowana przez GitHub Pages z brancha `main`, katalog `/ (root)`.
