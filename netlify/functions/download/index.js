// Netlify Function: resolve a direct download URL for a chosen format (yt-dlp -g).
// POST /.netlify/functions/download  { url, formatId }
// Returns { ok, url, filename } or { ok:false, error, code, detail }
// Note: the function returns the direct media URL; the browser downloads it
// straight from the platform CDN (Lambda cannot proxy large files).
const { execFile } = require('child_process');
const path = require('path');
const fs = require('fs');

// ---------- yt-dlp binary: find it and run it ----------
// The PyInstaller onefile binary extracts ~120MB into TMPDIR at startup.
// On Lambda one invocation runs per container, so the bundled binary can be
// run directly (no per-invocation 41MB copy); TMPDIR stays unique per run
// and is cleaned up, so /tmp (512MB on Lambda) never fills up.
const crypto = require('crypto');

function searchDir(dir, depth) {
  if (depth > 3) return null;
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return null; }
  for (const ent of entries) {
    if (ent.isFile() && ent.name === 'yt-dlp') return path.join(dir, ent.name);
  }
  for (const ent of entries) {
    if (ent.isDirectory() && ent.name !== 'node_modules' && !ent.name.startsWith('.')) {
      const found = searchDir(path.join(dir, ent.name), depth + 1);
      if (found) return found;
    }
  }
  return null;
}

function findBinarySrc() {
  const candidates = [
    path.join(__dirname, 'yt-dlp'),                       // folder-format: same dir
    path.join(__dirname, 'bin', 'yt-dlp'),
    path.join(__dirname, 'netlify', 'functions', 'bin', 'yt-dlp'),
    path.join(process.cwd(), 'netlify', 'functions', 'bin', 'yt-dlp'),
    path.join('/var/task', 'netlify', 'functions', 'bin', 'yt-dlp'),
    path.join('/var/task', 'bin', 'yt-dlp'),
  ];
  for (const c of candidates) {
    try { if (fs.existsSync(c)) return c; } catch (e) { /* next */ }
  }
  return searchDir(__dirname, 3) || searchDir(process.cwd(), 3) || searchDir('/var/task', 3);
}

function runYtDlp(args, timeoutMs) {
  return new Promise((resolve) => {
    const src = findBinarySrc();
    if (!src) {
      const msg = 'binary_not_found (__dirname=' + __dirname + ' cwd=' + process.cwd() + ')';
      console.error('[yt-dlp] ' + msg);
      return resolve({ err: new Error(msg), stdout: '', stderr: msg });
    }
    // Run the bundled binary directly (no per-invocation copy — that cost
    // ~0.5s per run). The PyInstaller binary still extracts into its own
    // temp dir per run, so TMPDIR stays unique per invocation and is cleaned up.
    const tag = process.pid + '-' + crypto.randomBytes(4).toString('hex');
    const tmpDir = '/tmp/yt-' + tag;
    try { fs.mkdirSync(tmpDir, { recursive: true }); } catch (e) { /* ignore */ }
    execFile(src, args, {
      timeout: timeoutMs,
      maxBuffer: 5 * 1024 * 1024,
      env: { ...process.env, HOME: '/tmp', XDG_CACHE_HOME: '/tmp/.cache', YTDLP_NO_UPDATE: '1', TMPDIR: tmpDir },
    }, (err, stdout, stderr) => {
      try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (e) { /* ignore */ }
      if (err) console.error('[yt-dlp] exec error: ' + err.message + ' | stderr: ' + (stderr || '').slice(0, 500));
      resolve({ err, stdout, stderr });
    });
  });
}

function safeName(title, ext) {
  const base = (title || 'video').replace(/[^\w\s\-\u0980-\u09FF.]/g, '').trim().slice(0, 80) || 'video';
  return base + '.' + (ext || 'mp4');
}

// Fetch a small file (audio / short clip) through the server so the browser
// is FORCED to download it instead of playing it. Direct .mp4/.mp3 links
// open in the browser's player; a same-origin Blob download is always saved.
// Capped at 5.5MB (Netlify's function response limit is 6MB) — bigger files
// fall back to the direct link. Follows redirects (googlevideo 302s).
const http = require('http');
const https = require('https');
const MAX_PROXY_BYTES = 5500000;
function fetchSmall(startUrl, timeoutMs) {
  return new Promise((resolve) => {
    let redirects = 0;
    let done = false;
    const finish = (r) => { if (!done) { done = true; resolve(r); } };
    const timer = setTimeout(() => finish({ ok: false, reason: 'timeout' }), timeoutMs);
    const go = (u) => {
      const lib = u.startsWith('https:') ? https : http;
      const req = lib.get(u, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' } }, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location && redirects < 5) {
          redirects++;
          res.resume();
          go(new URL(res.headers.location, u).toString());
          return;
        }
        if (res.statusCode !== 200 && res.statusCode !== 206) {
          clearTimeout(timer); res.resume();
          return finish({ ok: false, reason: 'http_' + res.statusCode });
        }
        const chunks = [];
        let total = 0;
        let tooBig = false;
        res.on('data', (c) => {
          total += c.length;
          if (total > MAX_PROXY_BYTES) { tooBig = true; req.destroy(); }
          else chunks.push(c);
        });
        res.on('end', () => {
          clearTimeout(timer);
          if (tooBig) return finish({ ok: false, reason: 'too_big' });
          finish({ ok: true, buffer: Buffer.concat(chunks), contentType: res.headers['content-type'] || 'application/octet-stream' });
        });
        res.on('error', () => { clearTimeout(timer); finish({ ok: false, reason: 'stream_error' }); });
      });
      req.on('error', () => { clearTimeout(timer); finish({ ok: false, reason: 'fetch_error' }); });
      req.setTimeout(timeoutMs, () => { try { req.destroy(); } catch (e) { /* ignore */ } clearTimeout(timer); finish({ ok: false, reason: 'timeout' }); });
    };
    go(startUrl);
  });
}

exports.handler = async (event) => {
  const headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
  if (event.httpMethod === 'OPTIONS') return { statusCode: 204, headers, body: '' };
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, headers, body: JSON.stringify({ ok: false, error: 'POST only' }) };
  }
  let body = {};
  try { body = JSON.parse(event.body || '{}'); } catch (e) { /* ignore */ }
  const url = (body.url || '').trim();
  let formatId = String(body.formatId || 'best').trim();
  if (!/^https?:\/\/.+/i.test(url)) {
    return { statusCode: 400, headers, body: JSON.stringify({ ok: false, error: 'Invalid link.' }) };
  }
  // 'bestaudio' must stay WITHOUT a /best fallback: with 'bestaudio/best',
  // a missing audio-only format silently returns the VIDEO file, so a user
  // clicking "Audio only" would get a video mislabeled as audio. Keep it
  // strict — the attempt loop tries several clients for bestaudio, and if
  // none has it, we return a clear error instead of the wrong file.
  if (formatId === 'bestaudio') formatId = 'bestaudio';
  if (!/^[a-zA-Z0-9_\-\+\/]+$/.test(formatId)) {
    return { statusCode: 400, headers, body: JSON.stringify({ ok: false, error: 'Invalid format.' }) };
  }
  const ext = String(body.ext || 'mp4').replace(/[^a-z0-9]/gi, '') || 'mp4';
  const title = String(body.title || 'video').slice(0, 120);

  // Proxy pool (IP rotation): YTDLP_PROXY = one proxy URL or comma-separated list.
  const proxies = (process.env.YTDLP_PROXY || '').split(',').map(s => s.trim()).filter(Boolean);
  const proxyArgs = proxies.length ? ['--proxy', proxies[Math.floor(Math.random() * proxies.length)]] : [];
  const isX = /https?:\/\/(www\.)?(x\.com|twitter\.com)\//i.test(url);

  // Fast path first: android client answers in ~3s; web scan is slower.
  // X/Twitter: fall back to the public syndication (embed) endpoint.
  // Per-attempt timeouts sum to <=25s (Netlify function limit is 26s).
  const mk = (extra) => ['-g', '-f', formatId, '--no-playlist', '--no-warnings',
    '--socket-timeout', '8', '--retries', '1', ...extra, ...proxyArgs, url];
  const attempts = [
    { a: mk(['--extractor-args', 'youtube:player_client=android']), t: 8000 },
    isX
      ? { a: mk(['--extractor-args', 'twitter:api=syndication']), t: 9000 }
      : { a: mk(['--js-runtimes', 'node', '--remote-components', 'ejs:github', '--extractor-args', 'youtube:player_client=web,android']), t: 12000 },
    { a: mk(['--no-check-certificates', '--extractor-args', 'youtube:player_client=android']), t: 5000 },
  ];
  let direct = '';
  let stderr = '';
  for (const { a, t } of attempts) {
    const r = await runYtDlp(a, t);
    stderr = r.stderr || stderr;
    direct = (r.stdout || '').trim().split('\n')[0] || '';
    if (/^https?:\/\//.test(direct)) break;
  }
  if (!/^https?:\/\//.test(direct)) {
    const s = (stderr || '').toLowerCase();
    const error = s.includes('binary_not_found') || s.includes('binary_prepare_failed')
      ? 'Download engine is not available on the server right now.'
      : s.includes('not a bot') || s.includes('sign in to confirm') ? 'YouTube blocked this request from our server (bot check). The video itself is public — please try again later, or try a different video.'
      : s.includes('blocked') ? 'This platform blocked the server. Try again later.'
      : s.includes('login') || s.includes('cookies') ? 'This link needs a logged-in account.'
      : 'Could not get a download link for this format. Please try again.';
    return { statusCode: 200, headers, body: JSON.stringify({ ok: false, error, detail: (stderr || '').slice(0, 300) }) };
  }
  // Force-download mode (proxy: true): stream small files through the server
  // with Content-Disposition: attachment so the browser SAVES the file
  // instead of playing it. Falls back to the direct link when the file is
  // too big or the fetch fails.
  if (body.proxy) {
    const got = await fetchSmall(direct, 20000);
    if (got.ok) {
      return {
        statusCode: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': got.contentType,
          'Content-Disposition': 'attachment; filename="' + safeName(title, ext).replace(/"/g, '') + '"',
        },
        body: got.buffer.toString('base64'),
        isBase64Encoded: true,
      };
    }
  }
  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({ ok: true, url: direct, filename: safeName(title, ext) }),
  };
};
