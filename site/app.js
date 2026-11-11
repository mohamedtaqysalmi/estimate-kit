(function () {
  "use strict";

  const PLAUSIBLE_SIGMAS = 2;

  const seed = [
    { label: "Stripe deposit checkout", best: 10, likely: 18, worst: 40 },
    { label: "Confirmation email", best: 3, likely: 7, worst: 16 },
    { label: "Owner login", best: 6, likely: 10, worst: 20 },
    { label: "Admin screens", best: 8, likely: 14, worst: 30 },
  ];

  const rowsEl = document.getElementById("rows");
  const form = document.getElementById("calc-form");
  const addBtn = document.getElementById("add-row");

  function fmt(n) {
    return Number.isFinite(n) ? n.toFixed(1) : "—";
  }

  function expected(best, likely, worst) {
    return (best + 4 * likely + worst) / 6;
  }

  function spread(best, worst) {
    return (worst - best) / 6;
  }

  function addRow(data) {
    const row = document.createElement("div");
    row.className = "row";
    row.innerHTML = `
      <input type="text" name="label" aria-label="Task label" placeholder="Task" />
      <input type="number" name="best" aria-label="Best hours" min="0" step="0.5" />
      <input type="number" name="likely" aria-label="Likely hours" min="0" step="0.5" />
      <input type="number" name="worst" aria-label="Worst hours" min="0" step="0.5" />
      <button type="button" class="remove" aria-label="Remove task">Remove</button>
    `;
    row.querySelector('[name="label"]').value = data.label || "";
    row.querySelector('[name="best"]').value = data.best;
    row.querySelector('[name="likely"]').value = data.likely;
    row.querySelector('[name="worst"]').value = data.worst;
    row.querySelector(".remove").addEventListener("click", function () {
      row.remove();
      recalculate();
    });
    rowsEl.appendChild(row);
  }

  function readRows() {
    return Array.from(rowsEl.querySelectorAll(".row")).map(function (row) {
      const best = Number(row.querySelector('[name="best"]').value);
      const likely = Number(row.querySelector('[name="likely"]').value);
      const worst = Number(row.querySelector('[name="worst"]').value);
      return { best: best, likely: likely, worst: worst };
    });
  }

  function recalculate() {
    const tasks = readRows();
    let best = 0;
    let likely = 0;
    let worst = 0;
    let exp = 0;
    let variance = 0;
    let valid = 0;

    for (const t of tasks) {
      if (![t.best, t.likely, t.worst].every(Number.isFinite)) continue;
      if (!(t.best >= 0 && t.best <= t.likely && t.likely <= t.worst)) continue;
      best += t.best;
      likely += t.likely;
      worst += t.worst;
      exp += expected(t.best, t.likely, t.worst);
      const s = spread(t.best, t.worst);
      variance += s * s;
      valid += 1;
    }

    const sigma = Math.sqrt(variance);
    const low = valid ? Math.max(best, exp - PLAUSIBLE_SIGMAS * sigma) : NaN;
    const high = valid ? Math.min(worst, exp + PLAUSIBLE_SIGMAS * sigma) : NaN;

    document.getElementById("sum-best").textContent = valid ? fmt(best) : "—";
    document.getElementById("sum-likely").textContent = valid ? fmt(likely) : "—";
    document.getElementById("sum-expected").textContent = valid ? fmt(exp) : "—";
    document.getElementById("sum-worst").textContent = valid ? fmt(worst) : "—";
    document.getElementById("sum-range").textContent = valid
      ? fmt(low) + " to " + fmt(high)
      : "—";
  }

  seed.forEach(addRow);
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    recalculate();
  });
  form.addEventListener("input", recalculate);
  addBtn.addEventListener("click", function () {
    addRow({ label: "", best: 2, likely: 4, worst: 8 });
    recalculate();
  });
  recalculate();
})();
