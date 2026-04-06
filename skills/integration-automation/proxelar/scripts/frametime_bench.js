// frametime_bench.js
// Inject into a running page to track frame times and report percentiles.
// Inject via: mcp__claude-in-chrome__javascript_tool or agent-browser eval
// Read output via: mcp__claude-in-chrome__read_console_messages with pattern "p50"
//
// Reports every ~5 seconds (300 frames at 60fps):
//   { p50, p95, p99, p999, frames, dropped, fps_avg }
// Target: p999 < 16.67ms for solid 60fps

(function() {
  if (window.__frametime_bench) return; // prevent double-injection
  window.__frametime_bench = true;

  const frameTimes = [];
  let last = performance.now();
  const SAMPLE_SIZE = 1000; // ~16s at 60fps — large enough for meaningful p99.9

  function percentile(sorted, pct) {
    const idx = Math.floor(sorted.length * pct / 100);
    return sorted[Math.min(idx, sorted.length - 1)];
  }

  function measure() {
    const now = performance.now();
    frameTimes.push(now - last);
    last = now;

    if (frameTimes.length >= SAMPLE_SIZE) {
      const sorted = [...frameTimes].sort((a, b) => a - b);
      const total = frameTimes.reduce((a, b) => a + b, 0);
      const report = {
        p50: +percentile(sorted, 50).toFixed(2),
        p95: +percentile(sorted, 95).toFixed(2),
        p99: +percentile(sorted, 99).toFixed(2),
        p999: +percentile(sorted, 99.9).toFixed(2),
        frames: frameTimes.length,
        dropped: frameTimes.filter(t => t > 20).length,
        fps_avg: +(1000 / (total / frameTimes.length)).toFixed(1)
      };
      console.log('[FRAMETIME]', JSON.stringify(report));
      frameTimes.length = 0;
    }

    requestAnimationFrame(measure);
  }

  requestAnimationFrame(measure);
  console.log('[FRAMETIME] bench started, reporting every ~5s');
})();
