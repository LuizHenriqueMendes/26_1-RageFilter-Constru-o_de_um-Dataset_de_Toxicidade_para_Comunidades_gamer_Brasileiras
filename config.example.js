/**
 * config.js — Twitch Chat Scraper Configuration
 * -----------------------------------------------
 * Copy this file to config.js and fill in your own credentials.
 * config.js is gitignored — never commit real tokens.
 *
 * Get your tokens at: https://twitchtokengenerator.com/
 *   → Select scopes: chat:read  chat:edit  user:read:chat
 *   → Copy the Access Token, Refresh Token, and Client ID below.
 *
 * Get your Client Secret at: https://dev.twitch.tv/console/apps
 *   → Open your app → click "New Secret"
 */

module.exports = {
  // ─── Twitch App Credentials ───────────────────────────────────────────────
  CLIENT_ID: "YOUR_CLIENT_ID_HERE",          // from dev.twitch.tv/console
  CLIENT_SECRET: "YOUR_CLIENT_SECRET_HERE",  // needed for token auto-refresh

  // ─── User Tokens (from https://twitchtokengenerator.com/) ─────────────────
  ACCESS_TOKEN: "YOUR_ACCESS_TOKEN_HERE",    // do NOT include "oauth:" prefix
  REFRESH_TOKEN: "YOUR_REFRESH_TOKEN_HERE",  // used to auto-renew expired tokens
  TWITCH_USERNAME: "your_twitch_login",      // your Twitch login name (lowercase)

  // ─── Timing ──────────────────────────────────────────────────────────────
  READ_DURATION_MS: 60 * 60 * 1000,   // 1 hour per live channel
  // READ_DURATION_MS: 2 * 60 * 1000, // <- 2 min for quick testing

  // ─── Output ──────────────────────────────────────────────────────────────
  OUTPUT_DIR: "./data/chat_logs",

  // ─── Channel List ─────────────────────────────────────────────────────────
  // Order matters — checked top to bottom. Offline channels are skipped.
  CHANNELS: [
    "alanzoka",
    "loud_coringa",
    "cellbit",
  ],
};
