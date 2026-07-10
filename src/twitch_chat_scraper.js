/**
 * Twitch Chat Scraper
 * -------------------
 * Iterates a list of channels. For each one that is live, reads chat
 * for READ_DURATION_MS and saves all messages to a per-channel CSV file.
 *
 * Setup:
 *   1. npm install
 *   2. Fill in config.js (tokens from https://twitchtokengenerator.com/)
 *   3. node twitch_chat_scraper.js
 */

const tmi   = require("tmi.js");
const axios = require("axios");
const fs    = require("fs");
const path  = require("path");

let {
  CLIENT_ID,
  CLIENT_SECRET,
  ACCESS_TOKEN,
  REFRESH_TOKEN,
  TWITCH_USERNAME,
  CHANNELS,
  READ_DURATION_MS,
  OUTPUT_DIR,
} = require("./config");

// ─── Logging ─────────────────────────────────────────────────────────────────

function log(msg) {
  console.log(`[${new Date().toISOString()}] ${msg}`);
}

// ─── Token Auto-Refresh ───────────────────────────────────────────────────────

async function refreshAccessToken() {
  log("🔄 Access token expired — refreshing...");
  try {
    const resp = await axios.post("https://id.twitch.tv/oauth2/token", null, {
      params: {
        grant_type:    "refresh_token",
        refresh_token: REFRESH_TOKEN,
        client_id:     CLIENT_ID,
        client_secret: CLIENT_SECRET,
      },
    });
    ACCESS_TOKEN  = resp.data.access_token;
    REFRESH_TOKEN = resp.data.refresh_token ?? REFRESH_TOKEN;
    log("✅ Token refreshed successfully.");
    return true;
  } catch (err) {
    log(`❌ Token refresh failed: ${err.response?.data?.message ?? err.message}`);
    return false;
  }
}

// ─── Twitch Helix API — Live Check ───────────────────────────────────────────

async function isChannelLive(channelName, retried = false) {
  try {
    const resp = await axios.get("https://api.twitch.tv/helix/streams", {
      params:  { user_login: channelName },
      headers: {
        "Client-ID":    CLIENT_ID,
        Authorization:  `Bearer ${ACCESS_TOKEN}`,
      },
    });
    const streams = resp.data.data;
    return Array.isArray(streams) && streams.length > 0 && streams[0].type === "live";
  } catch (err) {
    const status = err.response?.status;
    if (status === 401 && !retried) {
      const ok = await refreshAccessToken();
      if (ok) return isChannelLive(channelName, true);
    }
    log(`  ⚠️  Could not check live status for "${channelName}": ${err.response?.data?.message ?? err.message}`);
    return false;
  }
}

// ─── CSV Helpers ─────────────────────────────────────────────────────────────

function ensureOutputDir() {
  if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

function escapeCsv(value) {
  const s = value == null ? "" : String(value);
  return s.includes(",") || s.includes('"') || s.includes("\n")
    ? `"${s.replace(/"/g, '""')}"`
    : s;
}

function csvRow(...fields) {
  return fields.map(escapeCsv).join(",") + "\n";
}

const CSV_HEADER = csvRow("timestamp","channel","username","display_name","color","badges","message");

function getCsvPath(channelName) {
  const date = new Date().toISOString().slice(0, 10);
  return path.join(OUTPUT_DIR, `${channelName}_${date}.csv`);
}

function initCsvFile(filePath) {
  // Write header only if the file is new
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, CSV_HEADER, "utf8");
  }
}

function appendMessage(filePath, row) {
  fs.appendFileSync(filePath, csvRow(
    row.timestamp,
    row.channel,
    row.username,
    row.displayName,
    row.color,
    row.badges,
    row.message,
  ), "utf8");
}

// ─── Chat Reader (tmi.js — anonymous, no token needed for read-only) ──────────

function readChatForDuration(channelName, durationMs) {
  return new Promise((resolve) => {
    const filePath = getCsvPath(channelName);
    initCsvFile(filePath);

    let count    = 0;
    let finished = false;

    // tmi.js supports anonymous connections for read-only chat.
    // We pass the access token so the connection is authenticated
    // (required for some channels that restrict anonymous chat).
    const client = new tmi.Client({
      options:  { debug: false, skipUpdatingEmotesets: true },
      identity: {
        username: TWITCH_USERNAME,
        password: `oauth:${ACCESS_TOKEN}`,   // tmi.js always needs the "oauth:" prefix
      },
      channels:   [channelName],
      connection: { reconnect: false, secure: true },
    });

    function finish(reason) {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      client.disconnect().catch(() => {});
      log(`  ✅ Finished "${channelName}" — ${count} messages → ${filePath} (${reason})`);
      resolve({ channel: channelName, messages: count, file: filePath });
    }

    const timer = setTimeout(() => finish("1 h time limit"), durationMs);

    client.on("message", (_channel, tags, message, self) => {
      if (self) return;
      appendMessage(filePath, {
        timestamp:   new Date().toISOString(),
        channel:     channelName,
        username:    tags.username ?? "",
        displayName: tags["display-name"] ?? tags.username ?? "",
        color:       tags.color ?? "",
        badges:      tags.badges ? Object.keys(tags.badges).join("|") : "",
        message,
      });
      count++;
    });

    client.on("disconnected", (reason) => {
      if (!finished) finish(`disconnected: ${reason}`);
    });

    client.connect()
      .then(() => log(`  🟢 Connected to "${channelName}" — capturing chat for ${durationMs / 60000} min...`))
      .catch((err) => finish(`connect error: ${err}`));
  });
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function run() {
  ensureOutputDir();

  log("═".repeat(60));
  log("  Twitch Chat Scraper — Starting");
  log(`  Channels to check : ${CHANNELS.length}`);
  log(`  Duration per live  : ${READ_DURATION_MS / 60000} min`);
  log(`  Output directory   : ${path.resolve(OUTPUT_DIR)}`);
  log("═".repeat(60));

  const summary = [];

  for (let i = 0; i < CHANNELS.length; i++) {
    const channel = CHANNELS[i].toLowerCase().trim();
    log(`\n[${i + 1}/${CHANNELS.length}] Checking "${channel}"...`);

    const live = await isChannelLive(channel);

    if (!live) {
      log(`  ⭕ "${channel}" is offline — skipping.`);
      summary.push({ channel, status: "offline" });
      continue;
    }

    log(`  🔴 "${channel}" is LIVE — starting capture.`);
    const result = await readChatForDuration(channel, READ_DURATION_MS);
    summary.push({ channel, status: "captured", messages: result.messages, file: result.file });
  }

  // Summary table
  log("\n" + "═".repeat(60));
  log("  SUMMARY");
  log("═".repeat(60));
  for (const s of summary) {
    if (s.status === "captured") {
      log(`  ✅ ${s.channel}: ${s.messages} messages → ${s.file}`);
    } else {
      log(`  ⭕ ${s.channel}: offline`);
    }
  }
  log("═".repeat(60));
  log("  Done!");
}

run().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
