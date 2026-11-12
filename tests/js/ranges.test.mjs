import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);
const ranges = require("../../site/ranges.js");
const vectors = JSON.parse(readFileSync(new URL("../../site/range-vectors.json", import.meta.url)));

for (const c of vectors.cases) {
  test(`combine: ${c.name}`, () => {
    const total = ranges.combine(c.tasks);
    for (const [key, want] of Object.entries(c.total)) {
      assert.ok(
        Math.abs(total[key] - want) <= vectors.tolerance,
        `${key}: got ${total[key]}, want ${want}`,
      );
    }
  });
}

for (const [best, likely, worst] of vectors.invalid) {
  test(`rejects ${best}/${likely}/${worst}`, () => {
    assert.ok(ranges.validateTask(best, likely, worst));
    assert.throws(() => ranges.combine([[best, likely, worst]]));
  });
}

test("accepts equal values and names the problem", () => {
  assert.equal(ranges.validateTask(4, 4, 4), null);
  assert.match(ranges.validateTask(3, 2, 5), /best.*above likely/i);
  assert.match(ranges.validateTask(NaN, 2, 5), /numbers/i);
});
