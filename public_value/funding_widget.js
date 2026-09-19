(function () {
  "use strict";

  const DEFAULT_DATA_URL =
    "https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_radar.json";

  const STATUS_ORDER = { open: 0, continuous: 1, watch: 2, paused: 3, closed: 4 };

  function esc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function normalizeList(value) {
    if (!value) return [];
    return String(value)
      .split(",")
      .map((x) => x.trim().toLowerCase())
      .filter(Boolean);
  }

  function isRelevantToCounty(item, county) {
    if (!county) return true;
    const scope = Array.isArray(item.county_scope) ? item.county_scope : [];
    if (scope.length === 0) return true;
    return scope.some((x) => String(x).toLowerCase() === county.toLowerCase());
  }

  function daysUntil(deadline) {
    if (!deadline) return null;
    const t = Date.parse(deadline);
    if (!Number.isFinite(t)) return null;
    return Math.ceil((t - Date.now()) / 86400000);
  }

  function timingLabel(item) {
    const days = daysUntil(item.deadline);
    if (item.status === "open" && days !== null) {
      if (days < 0) return "Deadline passed";
      if (days === 0) return "Due today";
      if (days === 1) return "1 day left";
      return `${days} days left`;
    }
    return item.deadline_label || item.status;
  }

  function renderCard(item, compact) {
    const tags = (item.tags || []).slice(0, compact ? 3 : 5);
    return `
      <article class="cc-fr-card cc-fr-status-${esc(item.status)}">
        <div class="cc-fr-topline">
          <span class="cc-fr-badge">${esc(item.status)}</span>
          <span class="cc-fr-timing">${esc(timingLabel(item))}</span>
        </div>
        <h3 class="cc-fr-title">${esc(item.title)}</h3>
        <div class="cc-fr-provider">${esc(item.provider)}</div>
        <div class="cc-fr-funding">${esc(item.funding)}</div>
        ${compact ? "" : `<p class="cc-fr-summary">${esc(item.summary)}</p>`}
        ${tags.length ? `<div class="cc-fr-tags">${tags.map((t) => `<span>${esc(t)}</span>`).join("")}</div>` : ""}
        <a class="cc-fr-link" href="${esc(item.source_url)}" target="_blank" rel="noopener noreferrer">Verify at primary source →</a>
      </article>
    `;
  }

  function styleText(theme) {
    const dark = theme === "dark";
    return `
      .cc-fr-root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:${dark ? "#f2f5f3" : "#19231d"};background:${dark ? "#142019" : "#f7faf7"};border:1px solid ${dark ? "#355044" : "#dbe4dc"};border-radius:14px;padding:16px;line-height:1.45}
      .cc-fr-header{display:flex;justify-content:space-between;gap:12px;align-items:end;margin-bottom:12px;flex-wrap:wrap}
      .cc-fr-header h2{font-size:1.2rem;margin:0}.cc-fr-meta{font-size:.82rem;color:${dark ? "#b8c7bf" : "#68766e"}}
      .cc-fr-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:12px}
      .cc-fr-card{background:${dark ? "#1d2a23" : "#fff"};border:1px solid ${dark ? "#3c5448" : "#dce5de"};border-radius:12px;padding:14px}
      .cc-fr-topline{display:flex;justify-content:space-between;gap:8px;align-items:center}.cc-fr-badge{text-transform:uppercase;font-size:.7rem;font-weight:800;letter-spacing:.04em;background:${dark ? "#294437" : "#eaf4ed"};padding:3px 7px;border-radius:999px}
      .cc-fr-timing{font-size:.78rem;color:${dark ? "#b8c7bf" : "#66736b"}}.cc-fr-title{font-size:1rem;margin:10px 0 4px}.cc-fr-provider{font-size:.83rem;color:${dark ? "#bacac1" : "#627168"}}
      .cc-fr-funding{font-weight:750;margin-top:8px}.cc-fr-summary{font-size:.9rem}.cc-fr-tags{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0}.cc-fr-tags span{font-size:.7rem;padding:2px 6px;border-radius:999px;background:${dark ? "#22382e" : "#eef3ef"}}
      .cc-fr-link{display:inline-block;margin-top:9px;color:${dark ? "#8dd2ad" : "#216044"};font-weight:700;text-decoration:none;font-size:.86rem}.cc-fr-link:hover{text-decoration:underline}
      .cc-fr-empty,.cc-fr-error{padding:12px;border-radius:9px;background:${dark ? "#2b302d" : "#fff7e8"}}.cc-fr-credit{font-size:.72rem;color:${dark ? "#9eb0a7" : "#7b887f"};margin-top:10px}.cc-fr-credit a{color:inherit}
    `;
  }

  async function render(el) {
    const dataUrl = el.dataset.source || DEFAULT_DATA_URL;
    const statuses = normalizeList(el.dataset.status || "open,continuous,watch");
    const county = (el.dataset.county || "").trim();
    const tags = normalizeList(el.dataset.tags);
    const maxItems = Math.max(1, Math.min(Number(el.dataset.count || 6) || 6, 25));
    const compact = el.dataset.compact === "true";
    const theme = (el.dataset.theme || "light").toLowerCase() === "dark" ? "dark" : "light";

    el.innerHTML = `
      <style>${styleText(theme)}</style>
      <div class="cc-fr-root"><div class="cc-fr-meta">Loading CropCircuit funding data…</div></div>
    `;

    try {
      const response = await fetch(dataUrl, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const radar = await response.json();
      let items = Array.isArray(radar.opportunities) ? radar.opportunities : [];

      items = items.filter((item) => statuses.length === 0 || statuses.includes(String(item.status).toLowerCase()));
      items = items.filter((item) => isRelevantToCounty(item, county));
      if (tags.length) {
        items = items.filter((item) => {
          const itemTags = (item.tags || []).map((x) => String(x).toLowerCase());
          return tags.some((tag) => itemTags.includes(tag));
        });
      }

      items.sort((a, b) => {
        const sa = STATUS_ORDER[a.status] ?? 99;
        const sb = STATUS_ORDER[b.status] ?? 99;
        if (sa !== sb) return sa - sb;
        const da = a.deadline ? Date.parse(a.deadline) : Number.POSITIVE_INFINITY;
        const db = b.deadline ? Date.parse(b.deadline) : Number.POSITIVE_INFINITY;
        return da - db;
      });

      items = items.slice(0, maxItems);

      const context = [
        county ? `County: ${county}` : "",
        tags.length ? `Tags: ${tags.join(", ")}` : "",
      ].filter(Boolean).join(" · ");

      el.innerHTML = `
        <style>${styleText(theme)}</style>
        <div class="cc-fr-root">
          <div class="cc-fr-header">
            <div><h2>Michigan Farm Funding Radar</h2><div class="cc-fr-meta">${esc(context || "Open, continuous, and watch-list programs")}</div></div>
            <div class="cc-fr-meta">Verified ${esc(radar.verified_at || "recently")}</div>
          </div>
          ${items.length
            ? `<div class="cc-fr-grid">${items.map((item) => renderCard(item, compact)).join("")}</div>`
            : '<div class="cc-fr-empty">No tracked opportunities match these filters.</div>'}
          <div class="cc-fr-credit">Data: <a href="https://github.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/tree/main/public_value" target="_blank" rel="noopener noreferrer">CropCircuit Open Farm Utilities</a>. Program status changes; verify at the primary source.</div>
        </div>
      `;
    } catch (error) {
      el.innerHTML = `
        <style>${styleText(theme)}</style>
        <div class="cc-fr-root">
          <div class="cc-fr-error"><strong>Funding radar unavailable.</strong> The source could not be loaded. Try again later or use the public dataset directly.</div>
        </div>
      `;
    }
  }

  function boot() {
    document.querySelectorAll("[data-cropcircuit-funding-radar]").forEach(render);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }

  window.CropCircuitFundingRadar = { render };
})();
