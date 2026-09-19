const STATIC_CACHE = "cropcircuit-static-v1";
const DATA_CACHE = "cropcircuit-data-v1";

const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./public_value/farm_labor_log.html",
  "./public_value/labor_opportunity_analyzer.html",
  "./public_value/equipment_cost_threshold.html",
  "./public_value/workflow_experiment_analyzer.html",
  "./public_value/farm_decision_calculator.html",
  "./public_value/chore_taxonomy_mapper.html",
  "./public_value/farm_chore_scheduler.html",
  "./public_value/benchmark_builder.html",
  "./public_value/benchmark_explorer.html",
  "./public_value/funding_explorer.html",
  "./public_value/schedule_estimate_calibrator.html",
  "./public_value/labor_csv_import_mapper.html",
  "./public_value/schedule_math.js",
  "./public_value/chore_load_planner.html",
  "./public_value/workspace.js",
  "./public_value/workspace_backup.html",
  "./public_value/weekly_ops_brief.html",
  "./public_value/farm_ops_console.html",
  "./public_value/csa_math.js",
  "./public_value/csa_break_even.html",
  "./public_value/market_math.js",
  "./public_value/market_day_break_even.html",
  "./public_value/farm_math.js",
  "./public_value/workflow_experiment.js",
  "./public_value/farm_chore_taxonomy.json",
  "./public_value/farm_labor_record.schema.json",
  "./public_value/farm_benchmark.schema.json"
];

const FRESH_DATA_PATTERNS = [
  /\/public_value\/funding_radar\.json$/,
  /\/public_value\/funding_radar\.csv$/,
  /\/public_value\/funding_feed\.json$/,
  /\/public_value\/funding_deadlines\.ics$/,
  /\/public_value\/manifest\.json$/
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => ![STATIC_CACHE, DATA_CACHE].includes(key))
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

function isFreshData(url) {
  return FRESH_DATA_PATTERNS.some(pattern => pattern.test(url.pathname));
}

async function networkFirst(request) {
  const cache = await caches.open(DATA_CACHE);
  try {
    const response = await fetch(request);
    if (response && response.ok) cache.put(request, response.clone());
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw error;
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response && response.ok && request.method === "GET") {
    const cache = await caches.open(STATIC_CACHE);
    cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (isFreshData(url)) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  event.respondWith(cacheFirst(event.request));
});
