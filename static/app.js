// Shared helpers used by every page.
const $ = (selector, root = document) => root.querySelector(selector);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: options.body ? { "Content-Type": "application/json" } : {},
    credentials: "same-origin",
    ...options,
  });
  if (response.status === 401 && !path.startsWith("/api/login")) {
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// The server stores UTC timestamps as "YYYY-MM-DD HH:MM:SS".
function parseUtc(value) {
  return value ? new Date(value.replace(" ", "T") + "Z") : null;
}

function formatTime(value) {
  const date = parseUtc(value);
  return date ? date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "—";
}

function formatDateTime(value) {
  const date = parseUtc(value);
  if (!date) return "—";
  const day = date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  return `${day} · ${formatTime(value)}`;
}

function formatDate(value) {
  const date = parseUtc(value);
  return date ? date.toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" }) : "—";
}

function initials(name) {
  return (name || "?").split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function formatUid(uid) {
  return (uid || "").replace(/(..)(?=.)/g, "$1:");
}

function toast(message) {
  const element = document.createElement("div");
  element.className = "toast";
  element.textContent = message;
  document.body.appendChild(element);
  setTimeout(() => element.remove(), 3000);
}

function debounce(fn, delay = 250) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function renderPager(container, { page, perPage, total }, onPage, label) {
  const pages = Math.max(1, Math.ceil(total / perPage));
  const from = total === 0 ? 0 : (page - 1) * perPage + 1;
  const to = Math.min(page * perPage, total);
  const buttons = [];
  const first = Math.max(1, Math.min(page - 1, pages - 2));
  for (let n = first; n <= Math.min(pages, first + 2); n++) {
    buttons.push(`<button data-page="${n}" class="${n === page ? "current" : ""}">${n}</button>`);
  }
  container.innerHTML = `
    <span>Showing ${from}–${to} of ${total.toLocaleString()} ${label}</span>
    <div class="pages">
      <button data-page="${page - 1}" ${page <= 1 ? "disabled" : ""} aria-label="Previous">‹</button>
      ${buttons.join("")}
      <button data-page="${page + 1}" ${page >= pages ? "disabled" : ""} aria-label="Next">›</button>
    </div>`;
  container.querySelectorAll("button[data-page]").forEach((button) =>
    button.addEventListener("click", () => onPage(Number(button.dataset.page)))
  );
}

const userButton = $("#user-btn");
if (userButton) {
  const dropdown = $("#user-dropdown");
  userButton.addEventListener("click", (event) => {
    event.stopPropagation();
    dropdown.hidden = !dropdown.hidden;
  });
  document.addEventListener("click", () => (dropdown.hidden = true));
  $("#logout-btn").addEventListener("click", async () => {
    await api("/api/logout", { method: "POST" });
    window.location.href = "/login";
  });
}

// "/" focuses the search box, like the shortcut hint in the design.
document.addEventListener("keydown", (event) => {
  const search = $("#search");
  if (search && (event.key === "/" || ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k")) && document.activeElement.tagName !== "INPUT") {
    event.preventDefault();
    search.focus();
  }
});
