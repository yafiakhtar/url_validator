(function themeToggle() {
  var root = document.documentElement;
  var btn = document.getElementById("themeToggle");
  var icon = document.getElementById("themeIcon");
  var moonSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  var sunSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
  function apply(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem("url-validator-theme", theme);
    icon.innerHTML = theme === "dark" ? sunSvg : moonSvg;
  }
  btn.addEventListener("click", function() {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    apply(next);
  });
  apply(root.getAttribute("data-theme"));
})();

const frequencyLabels = {
  300: "5 min",
  900: "15 min",
  3600: "1 h",
  21600: "6 h",
  86400: "24 h"
};

function showError(msg) {
  const el = document.getElementById("error");
  el.textContent = msg;
  el.style.display = msg ? "block" : "none";
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
    ...(options.body && { body: JSON.stringify(options.body) })
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const contentType = res.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) return res.json();
  return res.text();
}

async function loadRuns(jobId) {
  const runs = await api(`/jobs/${jobId}/runs`);
  return runs[0] || null;
}

function renderResult(run) {
  if (!run) return { html: '<span class="empty">No runs yet</span>', risk: null };
  if (run.status === "running") {
    return { html: '<span class="result">Loading</span>', risk: "loading" };
  }
  const risk = run.risk_level || "none";
  if (risk === "none") {
    return { html: '<span class="result safe">Safe</span>', risk };
  }
  const flags = (run.flags && run.flags.length) ? ` (${run.flags.join(", ")})` : "";
  return { html: `<span class="result risk">Rescue${flags}</span>`, risk };
}

function renderJob(job, latestRun) {
  const { html: resultHtml } = renderResult(latestRun);
  const intervalLabel = frequencyLabels[job.interval_seconds] || `${job.interval_seconds}s`;
  const lastChecked = latestRun && latestRun.finished_at ? formatTimestamp(latestRun.finished_at) : "—";
  const detectedAt = latestRun && latestRun.risk_at ? formatTimestamp(latestRun.risk_at) : "";
  return `
    <li class="job" data-job-id="${job.id}">
      <div class="url">${escapeHtml(job.url)}</div>
      <div class="meta">Frequency: ${escapeHtml(intervalLabel)}</div>
      <div class="meta">Status: ${escapeHtml(job.status)}</div>
      <div class="meta">Last checked: ${escapeHtml(lastChecked)}</div>
      ${detectedAt ? `<div class="meta">Detected: ${escapeHtml(detectedAt)}</div>` : ""}
      <div class="result">${resultHtml}</div>
      <div class="actions">
        <button type="button" data-action="run">Run now</button>
        <button type="button" data-action="delete">Delete</button>
      </div>
    </li>
  `;
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function formatTimestamp(value) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

async function loadJobs() {
  showError("");
  const listEl = document.getElementById("jobList");
  const alertsEl = document.getElementById("alerts");
  const alertListEl = document.getElementById("alertList");
  try {
    const jobs = await api("/jobs");
    if (jobs.length === 0) {
      listEl.innerHTML = '<li class="empty">No jobs yet. Add one above.</li>';
      alertsEl.style.display = "none";
      return;
    }
    const alerts = [];
    const html = await Promise.all(
      jobs.map(async (job) => {
        const run = await loadRuns(job.id);
        if (run && run.risk_level && run.risk_level !== "none") {
          const flags = (run.flags && run.flags.length) ? run.flags.join(", ") : "risk detected";
          alerts.push({
            url: job.url,
            flags,
            finished_at: run.finished_at || "",
            risk_at: run.risk_at || ""
          });
        }
        return renderJob(job, run);
      })
    );
    listEl.innerHTML = html.join("");
    if (alerts.length) {
      alertListEl.innerHTML = alerts
        .map(
          (item) =>
            `<li>
              <strong>${escapeHtml(item.url)}</strong>
              <div>Flagged content: ${escapeHtml(item.flags)}</div>
              ${item.risk_at ? `<div>Detected: ${escapeHtml(formatTimestamp(item.risk_at))}</div>` : ""}
              ${item.finished_at ? `<div>Last checked: ${escapeHtml(formatTimestamp(item.finished_at))}</div>` : ""}
            </li>`
        )
        .join("");
      alertsEl.style.display = "block";
    } else {
      alertsEl.style.display = "none";
      alertListEl.innerHTML = "";
    }
    listEl.querySelectorAll(".job").forEach((node) => {
      const jobId = node.dataset.jobId;
      node.querySelector('[data-action="run"]').addEventListener("click", () => runNow(jobId));
      node.querySelector('[data-action="delete"]').addEventListener("click", () => deleteJob(jobId));
    });
  } catch (e) {
    showError("Failed to load jobs: " + e.message);
    listEl.innerHTML = "";
  }
}

async function runNow(jobId) {
  showError("");
  try {
    await api(`/jobs/${jobId}/run`, { method: "POST" });
    await loadJobs();
  } catch (e) {
    showError("Run now failed: " + e.message);
  }
}

async function deleteJob(jobId) {
  showError("");
  try {
    await api(`/jobs/${jobId}`, { method: "DELETE" });
    await loadJobs();
  } catch (e) {
    showError("Delete failed: " + e.message);
  }
}

document.getElementById("createForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("");
  const url = document.getElementById("url").value.trim();
  const interval_seconds = parseInt(document.getElementById("frequency").value, 10);
  try {
    await api("/jobs", {
      method: "POST",
      body: {
        url: url.startsWith("http") ? url : "https://" + url,
        interval_seconds,
        mode: "auto",
      }
    });
    document.getElementById("url").value = "";
    await loadJobs();
  } catch (e) {
    showError("Failed to create job: " + e.message);
  }
});

loadJobs();
setInterval(loadJobs, 15000);
