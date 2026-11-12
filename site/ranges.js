// Range math for the page. Mirrors src/estimate_kit/ranges.py; both are tested
// against site/range-vectors.json.
(function (root) {
  "use strict";

  const PLAUSIBLE_SIGMAS = 2;

  // Returns an error message, or null when the three numbers are a valid task.
  function validateTask(best, likely, worst) {
    if (![best, likely, worst].every(Number.isFinite)) {
      return "Enter best, likely and worst as numbers.";
    }
    if (best < 0) {
      return "Best must not be negative.";
    }
    if (best > likely) {
      return "Best (" + best + ") is above likely (" + likely + "). Each task needs best <= likely <= worst.";
    }
    if (likely > worst) {
      return "Likely (" + likely + ") is above worst (" + worst + "). Each task needs best <= likely <= worst.";
    }
    return null;
  }

  function taskStats(best, likely, worst) {
    return { expected: (best + 4 * likely + worst) / 6, spread: (worst - best) / 6 };
  }

  // tasks: array of [best, likely, worst]. Throws on an invalid task.
  function combine(tasks) {
    let best = 0;
    let likely = 0;
    let worst = 0;
    let expected = 0;
    let variance = 0;
    tasks.forEach(function (t) {
      const error = validateTask(t[0], t[1], t[2]);
      if (error) throw new Error(error);
      const stats = taskStats(t[0], t[1], t[2]);
      best += t[0];
      likely += t[1];
      worst += t[2];
      expected += stats.expected;
      variance += stats.spread * stats.spread;
    });
    const spread = Math.sqrt(variance);
    return {
      best: best,
      likely: likely,
      worst: worst,
      expected: expected,
      spread: spread,
      low: Math.max(best, expected - PLAUSIBLE_SIGMAS * spread),
      high: Math.min(worst, expected + PLAUSIBLE_SIGMAS * spread),
    };
  }

  const api = { validateTask: validateTask, taskStats: taskStats, combine: combine };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.EstimateRanges = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
