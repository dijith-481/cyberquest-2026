// orbit — waitlist chrome + waitlist behavior.
//
// All hand-drawn chrome comes from the drawably vendor sheet. Every element
// passed here gets position:relative and an absolutely-positioned pencil SVG,
// so the sketch follows the box on resize. Seeds are fixed so the page looks
// the same on every load — a launch page does not redraw itself at you.

import {
  drawablyBadge,
  drawablyButton,
  drawablyCard,
  drawablyCheckbox,
  drawablyCircle,
  drawablyDivider,
  drawablyHighlight,
  drawablyInput,
  drawablyList,
  drawablySelect,
  drawablyUnderline,
} from "./drawably/index.js";

function ink(root = document) {
  const scope = root instanceof Element ? root : document;
  scope.querySelectorAll?.("button:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyButton(el, { variant: el.dataset.variant ?? "outline" }); } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.(".fld[data-kind]:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try {
      const kind = el.dataset.kind;
      if (kind === "select") drawablySelect(el);
      else if (kind === "checkbox") drawablyCheckbox(el);
      else drawablyInput(el);
    } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.(".dcard:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyCard(el); } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.(".dbadge:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyBadge(el, { variant: el.dataset.variant ?? "outline" }); } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.("hr.rule:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyDivider(el); } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.("[data-circle]:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyCircle(el); } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.("[data-highlight]:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyHighlight(el); } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.("[data-underline]:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyUnderline(el); } catch { /* vendor missing */ }
  });
  scope.querySelectorAll?.("ul[data-list]:not(.drawn)").forEach((el) => {
    el.classList.add("drawn");
    try { drawablyList(el, { marker: el.dataset.list === "check" ? "check" : "dash" }); } catch { /* vendor missing */ }
  });
}

// The waitlist is a rehearsal, not a backend. Queue numbers are assigned
// locally so Facilities can ignore them in order.
function wireWaitlist() {
  const form = document.querySelector("#waitlist-form");
  if (!form) return;
  const msg = document.querySelector("#waitlist-msg");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = new FormData(form).get("email") ?? "you";
    const n = 4096 + Math.floor(Math.random() * 512);
    if (msg) {
      msg.hidden = false;
      msg.className = "msg ok";
      msg.textContent = `Noted, ${email}. You are #${n} in line. Facilities have been notified.`;
    }
    form.reset();
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => { ink(); wireWaitlist(); });
} else {
  ink(); wireWaitlist();
}
