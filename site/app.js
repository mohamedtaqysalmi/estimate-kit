(function () {
  "use strict";

  const ranges = window.EstimateRanges;
  const rowsEl = document.getElementById("rows");
  const errorEl = document.getElementById("calc-error");
  const fields = ["best", "likely", "worst"];

  const seed = [
    ["Stripe deposit checkout", 10, 18, 40],
    ["Confirmation email", 3, 7, 16],
    ["Owner login", 6, 10, 20],
    ["Admin screens", 8, 14, 30],
  ];

  function fmt(value) {
    return value.toFixed(1);
  }

  function cell(child) {
    const td = document.createElement("td");
    td.appendChild(child);
    return td;
  }

  function output(className) {
    const td = document.createElement("td");
    td.className = "num " + className;
    td.textContent = "-";
    return td;
  }

  function input(type, name, label, value) {
    const el = document.createElement("input");
    el.type = type;
    el.name = name;
    el.value = value;
    el.setAttribute("aria-label", label);
    if (type === "number") {
      el.min = "0";
      el.step = "0.5";
      el.inputMode = "decimal";
    } else {
      el.autocomplete = "off";
      el.spellcheck = false;
    }
    return el;
  }

  function addRow(label, best, likely, worst) {
    const tr = document.createElement("tr");
    tr.appendChild(cell(input("text", "label", "Task name", label)));
    tr.appendChild(cell(input("number", "best", "Best hours", best)));
    tr.appendChild(cell(input("number", "likely", "Likely hours", likely)));
    tr.appendChild(cell(input("number", "worst", "Worst hours", worst)));
    tr.appendChild(output("expected"));
    tr.appendChild(output("spread"));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "btn btn-small";
    remove.textContent = "Remove";
    remove.setAttribute("aria-label", "Remove this task");
    remove.addEventListener("click", function () {
      tr.remove();
      recalculate();
    });
    tr.appendChild(cell(remove));
    rowsEl.appendChild(tr);
  }

  function readRow(tr) {
    const raw = fields.map(function (name) {
      return tr.querySelector('[name="' + name + '"]').value.trim();
    });
    const name = tr.querySelector('[name="label"]').value.trim();
    if (!name && raw.every(function (v) { return v === ""; })) return null;
    const numbers = raw.map(function (v) { return v === "" ? NaN : Number(v); });
    return { name: name, numbers: numbers };
  }

  function setText(id, text) {
    document.getElementById(id).textContent = text;
  }

  function recalculate() {
    const valid = [];
    const problems = [];
    let index = 0;
    rowsEl.querySelectorAll("tr").forEach(function (tr) {
      index += 1;
      const row = readRow(tr);
      const expectedCell = tr.querySelector(".expected");
      const spreadCell = tr.querySelector(".spread");
      const inputs = tr.querySelectorAll("input");
      inputs.forEach(function (el) { el.removeAttribute("aria-invalid"); });
      expectedCell.textContent = "-";
      spreadCell.textContent = "-";
      if (!row) return;
      const error = ranges.validateTask(row.numbers[0], row.numbers[1], row.numbers[2]);
      if (error) {
        problems.push("Row " + index + (row.name ? " (" + row.name + ")" : "") + ": " + error);
        fields.forEach(function (name) {
          tr.querySelector('[name="' + name + '"]').setAttribute("aria-invalid", "true");
        });
        return;
      }
      const stats = ranges.taskStats(row.numbers[0], row.numbers[1], row.numbers[2]);
      expectedCell.textContent = fmt(stats.expected);
      spreadCell.textContent = fmt(stats.spread);
      valid.push(row.numbers);
    });

    errorEl.replaceChildren();
    if (problems.length) {
      problems.forEach(function (text) {
        const p = document.createElement("p");
        p.textContent = text;
        errorEl.appendChild(p);
      });
      const note = document.createElement("p");
      note.textContent = "Rows with a problem are left out of the totals below.";
      errorEl.appendChild(note);
    }
    errorEl.hidden = problems.length === 0;

    if (!valid.length) {
      ["sum-best", "sum-likely", "sum-expected", "sum-range", "sum-spread", "sum-worst"].forEach(
        function (id) { setText(id, "-"); },
      );
      return;
    }
    const total = ranges.combine(valid);
    setText("sum-best", fmt(total.best));
    setText("sum-likely", fmt(total.likely));
    setText("sum-expected", fmt(total.expected));
    setText("sum-spread", fmt(total.spread));
    setText("sum-range", fmt(total.low) + " to " + fmt(total.high));
    setText("sum-worst", fmt(total.worst));
  }

  seed.forEach(function (s) { addRow(s[0], s[1], s[2], s[3]); });
  document.getElementById("add-row").addEventListener("click", function () {
    addRow("", "", "", "");
    recalculate();
    const last = rowsEl.lastElementChild;
    if (last) last.querySelector("input").focus();
  });
  document.getElementById("calc-form").addEventListener("input", recalculate);
  document.getElementById("calc-form").addEventListener("submit", function (event) {
    event.preventDefault();
    recalculate();
  });
  recalculate();
})();
