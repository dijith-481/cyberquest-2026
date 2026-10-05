// aetheria's corner — interactions (no backend, all vibes)

// typing effect
const LINES = [
  "i break builds & hearts",
  "helix enjoyer, nixos btw",
  "good girls push to main",
  "professional yapper, amateur rustacean",
];
(function typeLoop() {
  const el = document.getElementById("typed");
  let li = 0, ci = 0, deleting = false;
  function tick() {
    const line = LINES[li];
    el.textContent = line.slice(0, ci);
    let wait = deleting ? 32 : 62;
    if (!deleting && ci === line.length) { wait = 1700; deleting = true; }
    else if (deleting && ci === 0) { deleting = false; li = (li + 1) % LINES.length; wait = 350; }
    else ci += deleting ? -1 : 1;
    setTimeout(tick, wait);
  }
  tick();
})();

// scroll reveal
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
}, { threshold: 0.12 });
document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

// sparkle cursor trail (throttled)
let last = 0;
const GLYPHS = ["✦", "♡", "★", "⋆"];
document.addEventListener("pointermove", (e) => {
  const now = Date.now();
  if (now - last < 70) return;
  last = now;
  const s = document.createElement("span");
  s.className = "spark";
  s.textContent = GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
  s.style.left = e.clientX + "px";
  s.style.top = e.clientY + "px";
  if (Math.random() < 0.4) s.style.color = "#9dcf1f";
  document.body.appendChild(s);
  setTimeout(() => s.remove(), 750);
});

// fake playlist
document.querySelectorAll(".track").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".track").forEach((b) => b.classList.remove("playing"));
    btn.classList.add("playing");
    document.getElementById("np-song").textContent = btn.dataset.song;
    document.getElementById("now-playing").hidden = false;
  });
});

// guestbook (local only — the internet forgets, aetheria doesn't)
const SEED = [
  ["zoya.exe", "ur site made me switch to helix. my pinky says thanks"],
  ["milo_444", "came for the lime green stayed for the vibes"],
  ["rina", "SIGNING BC U TOLD ME TO. also orbit looks so cute??"],
];
const entries = document.getElementById("entries");
function addEntry(name, msg) {
  const div = document.createElement("div");
  div.className = "entry";
  const b = document.createElement("b");
  b.textContent = name + " ⋆ ";
  div.appendChild(b);
  div.appendChild(document.createTextNode(msg));
  entries.prepend(div);
}
function loadGB() {
  let mine = [];
  try { mine = JSON.parse(localStorage.getItem("aetheria_gb") || "[]"); } catch { /* fresh */ }
  [...mine.reverse(), ...SEED].forEach(([n, m]) => addEntry(n, m));
}
document.getElementById("gb-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("gb-name").value.trim().slice(0, 24);
  const msg = document.getElementById("gb-msg").value.trim().slice(0, 120);
  if (!name || !msg) return;
  let mine = [];
  try { mine = JSON.parse(localStorage.getItem("aetheria_gb") || "[]"); } catch { /* fresh */ }
  mine.push([name, msg]);
  try { localStorage.setItem("aetheria_gb", JSON.stringify(mine.slice(-20))); } catch { /* private mode */ }
  addEntry(name, msg);
  e.target.reset();
  rain(14);
});
loadGB();

// serotonin rain
const RAIN = ["🎀", "♡", "✦", "★", "💚", "🦋", "🍋", "🌷"];
function rain(n) {
  const zone = document.getElementById("rain");
  for (let i = 0; i < n; i++) {
    const s = document.createElement("span");
    s.className = "fall";
    s.textContent = RAIN[Math.floor(Math.random() * RAIN.length)];
    s.style.left = Math.random() * 100 + "vw";
    s.style.fontSize = 18 + Math.random() * 22 + "px";
    s.style.animationDuration = 1.6 + Math.random() * 1.8 + "s";
    s.style.animationDelay = Math.random() * 0.4 + "s";
    zone.appendChild(s);
    setTimeout(() => s.remove(), 4200);
  }
}
document.getElementById("serotonin").addEventListener("click", () => rain(46));
