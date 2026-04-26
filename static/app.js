// Helpers for talking to the FastAPI backend.

async function apiGet(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function apiPost(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

async function apiPut(url, body) {
  const r = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

async function apiDelete(url, body) {
  const r = await fetch(url, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

function showMessage(elId, text, kind = "ok") {
  const el = document.getElementById(elId);
  if (!el) return;
  el.className = "msg " + kind;
  el.textContent = text;
  setTimeout(() => {
    el.textContent = "";
    el.className = "";
  }, 4000);
}

// Format a time coming back from MySQL (could be "HH:MM:SS" string)
function fmtTime(t) {
  if (!t) return "";
  return String(t).slice(0, 5); // HH:MM
}
