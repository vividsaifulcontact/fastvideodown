// Netlify Function: get available formats for a social media link (yt-dlp).
// POST /.netlify/functions/formats  { url }
// Returns { ok, title, thumbnail, duration, uploader, extractor, webpage_url,
//            formats: { video: [...], audio: [...] } } or { ok:false, error, code, detail }
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
      maxBuffer: 10 * 1024 * 1024,
      env: { ...process.env, HOME: '/tmp', XDG_CACHE_HOME: '/tmp/.cache', YTDLP_NO_UPDATE: '1', TMPDIR: tmpDir },
    }, (err, stdout, stderr) => {
      try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (e) { /* ignore */ }
      if (err) console.error('[yt-dlp] exec error: ' + err.message + ' | stderr: ' + (stderr || '').slice(0, 500));
      resolve({ err, stdout, stderr });
    });
  });
}

// ---------- helpers ----------

function classifyError(stderr) {
  const s = (stderr || '').toLowerCase();
  if (s.includes('binary_not_found') || s.includes('binary_prepare_failed'))
    return { code: 'engine_error', error: 'Download engine is not available on the server right now.' };
  if (s.includes('ip address is blocked') || s.includes('blocked from accessing'))
    return { code: 'ip_blocked', error: 'This platform blocked the server (IP blocked). Try another link or try again later.' };
  // YouTube's anti-bot screen ("Sign in to confirm you're not a bot") is NOT
  // a private video — the video is public, YouTube is just refusing the
  // server's IP. Say so plainly instead of claiming it needs a login.
  if (s.includes('not a bot') || s.includes('sign in to confirm') || s.includes('confirm you'))
    return { code: 'bot_check', error: 'YouTube blocked this request from our server (it asked to sign in to prove it is not a bot). The video itself is public — please try again later, or try a different video.' };
  if (s.includes('login required') || s.includes('log in') || s.includes('cookies') || s.includes('sign in to confirm'))
    return { code: 'login_required', error: 'This link needs a logged-in account (private / login-only content).' };
  if (s.includes('unsupported url') || s.includes('no video') || s.includes('not a valid url'))
    return { code: 'unsupported', error: 'This link is not supported or has no downloadable video.' };
  if (s.includes('timed out') || s.includes('timeout'))
    return { code: 'timeout', error: 'The platform took too long to respond. Please try again.' };
  if (s.includes('private video') || s.includes('this video is private'))
    return { code: 'private', error: 'This video is private.' };
  if (s.includes('video unavailable') || s.includes('removed') || s.includes('deleted'))
    return { code: 'unavailable', error: 'This video is unavailable or was removed.' };
  return { code: 'failed', error: 'Could not fetch this link. The platform may be blocking downloads right now.' };
}

function pickThumbnail(thumbnails) {
  if (!Array.isArray(thumbnails) || !thumbnails.length) return null;
  const sorted = [...thumbnails].sort((a, b) => (b.width || 0) - (a.width || 0));
  return sorted[0] && sorted[0].url ? sorted[0].url : null;
}

function buildFormats(list) {
  const videoByHeight = new Map();
  const audioByKey = new Map();
  for (const f of list || []) {
    if (!f || !f.url || f.ext === 'mhtml') continue;
    const proto = (f.protocol || '').toLowerCase();
    if (proto && !proto.startsWith('http')) continue;
    // Some extractors (e.g. X/Twitter syndication) omit codec fields: a format
    // with a height but no codec info is a combined video+audio file.
    const hasVideo = (f.vcodec && f.vcodec !== 'none') || !!f.height;
    const hasAudio = (f.acodec && f.acodec !== 'none') || (!f.vcodec && !f.acodec && !!f.height);
    if (hasVideo) {
      const h = f.height || 0;
      if (!h) continue;
      const key = String(h);
      const item = {
        format_id: String(f.format_id),
        label: h + 'p',
        height: h,
        ext: f.ext || 'mp4',
        hasAudio: !!hasAudio,
        fps: f.fps || null,
        filesize: f.filesize || f.filesize_approx || null,
        vcodec: f.vcodec,
        // Direct link, already fetched: the Download button opens it instantly
        // instead of running a second yt-dlp lookup.
        url: f.url || null,
      };
      const prev = videoByHeight.get(key);
      if (!prev || (!prev.hasAudio && item.hasAudio) ||
          (prev.hasAudio === item.hasAudio && (item.filesize || 0) > (prev.filesize || 0))) {
        videoByHeight.set(key, item);
      }
    } else if (hasAudio) {
      const key = (f.ext || 'audio') + '|' + (f.abr || 0);
      const item = {
        format_id: String(f.format_id),
        label: (f.abr ? Math.round(f.abr) + ' kbps' : (f.ext || 'audio')).toUpperCase(),
        ext: f.ext || 'm4a',
        abr: f.abr || null,
        filesize: f.filesize || f.filesize_approx || null,
        // Direct link, already fetched: the Download button opens it instantly.
        url: f.url || null,
      };
      const prev = audioByKey.get(key);
      if (!prev || (item.filesize || 0) > (prev.filesize || 0)) audioByKey.set(key, item);
    }
  }
  const video = [...videoByHeight.values()].sort((a, b) => b.height - a.height);
  const audio = [...audioByKey.values()].sort((a, b) => (b.abr || 0) - (a.abr || 0));
  return { video, audio };
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
  let url = '';
  try { url = (JSON.parse(event.body || '{}').url || '').trim(); } catch (e) { /* ignore */ }
  if (!/^https?:\/\/.+/i.test(url)) {
    return { statusCode: 400, headers, body: JSON.stringify({ ok: false, code: 'bad_url', error: 'Please paste a valid link starting with http:// or https://' }) };
  }

  // Proxy pool (IP rotation): set YTDLP_PROXY to one proxy URL, or a
  // comma-separated list to rotate the egress IP per request. Without it,
  // every request leaves from the same server IP and platforms can block it.
  const proxies = (process.env.YTDLP_PROXY || '').split(',').map(s => s.trim()).filter(Boolean);
  const proxyArgs = proxies.length ? ['--proxy', proxies[Math.floor(Math.random() * proxies.length)]] : [];
  const isX = /https?:\/\/(www\.)?(x\.com|twitter\.com)\//i.test(url);

  const baseArgs = ['-J', '--no-playlist', '--skip-download', '--no-warnings',
    '--socket-timeout', '8', '--retries', '1',
    '--js-runtimes', 'node', '--remote-components', 'ejs:github'];
  const androidArgs = ['-J', '--no-playlist', '--skip-download', '--no-warnings',
    '--socket-timeout', '8', '--retries', '1',
    '--extractor-args', 'youtube:player_client=android', ...proxyArgs, url];
  const androidNoCertArgs = ['-J', '--no-playlist', '--skip-download', '--no-warnings',
    '--socket-timeout', '8', '--retries', '1', '--no-check-certificates',
    '--extractor-args', 'youtube:player_client=android', ...proxyArgs, url];
  const webArgs = [...baseArgs, '--extractor-args', 'youtube:player_client=web,android', ...proxyArgs, url];
  // X/Twitter: the default GraphQL API is blocked from server IPs, but the
  // public syndication (embed) endpoint still answers — use it as fallback.
  const syndicationArgs = ['-J', '--no-playlist', '--skip-download', '--no-warnings',
    '--socket-timeout', '8', '--retries', '1',
    '--extractor-args', 'twitter:api=syndication', ...proxyArgs, url];
  // Fast path first (android client answers in ~3s); web scan is slower.
  // deep=true forces the web scan first (more qualities, slower).
  // Per-attempt timeouts sum to <=25s (Netlify function limit is 26s).
  let deep = false;
  try { deep = !!JSON.parse(event.body || '{}').deep; } catch (e) { /* ignore */ }
  // No cache: every lookup runs yt-dlp fresh, so nothing is stored.
  const isYT = /https?:\/\/(www\.)?(youtube\.com|youtu\.be)\//i.test(url);
  // YouTube deep scan: web first (full formats with the EJS solver), then the
  // TV client — from server IPs it sometimes returns the high qualities the
  // web client withholds — then the reliable android fallback, then no-cert.
  const tvArgs = [...baseArgs, '--extractor-args', 'youtube:player_client=tv', ...proxyArgs, url];
  const mid = isX ? { a: syndicationArgs, t: 9000 } : { a: webArgs, t: 12000 };
  const attempts = deep
    ? (isYT
      ? [{ a: webArgs, t: 9000 }, { a: tvArgs, t: 6000 }, { a: androidArgs, t: 5000 }, { a: androidNoCertArgs, t: 5000 }]
      : [mid, { a: androidArgs, t: 8000 }, { a: androidNoCertArgs, t: 5000 }])
    : [{ a: androidArgs, t: 8000 }, mid, { a: androidNoCertArgs, t: 5000 }];

  let data = null;
  let bestData = null;
  let bestCount = 0;
  let lastErr = '';
  for (const { a, t } of attempts) {
    const { err, stdout, stderr } = await runYtDlp(a, t);
    lastErr = stderr || '';
    if (stdout) {
      try { data = JSON.parse(stdout); } catch (e) { data = null; }
    }
    if (data) {
      // Fast path: usable formats found — return now, don't wait for slower scans.
      const f = buildFormats(data.formats);
      if (f.video.length || f.audio.length) {
        // Deep YouTube scan: don't stop at the low 360p-only fallback — a
        // later client (tv/ios) may return the high qualities.
        const onlyLow = deep && isYT && !f.video.some(v => (v.height || 0) > 360) && !f.audio.length;
        if (onlyLow) {
          const n = f.video.length + f.audio.length;
          if (n > bestCount) { bestCount = n; bestData = data; }
          data = null;
          continue;
        }
        break;
      }
      data = null;
    }
  }
  if (!data) data = bestData;

  if (!data) {
    const c = classifyError(lastErr);
    return { statusCode: 200, headers, body: JSON.stringify({ ok: false, ...c, detail: (lastErr || '').slice(0, 300) }) };
  }

  const formats = buildFormats(data.formats);
  if (!formats.video.length && !formats.audio.length) {
    return { statusCode: 200, headers, body: JSON.stringify({ ok: false, code: 'no_formats', error: 'No downloadable formats were found for this link.' }) };
  }

  const body = JSON.stringify({
    ok: true,
    title: data.title || 'Video',
    thumbnail: pickThumbnail(data.thumbnails),
    duration: data.duration || null,
    uploader: data.uploader || data.channel || null,
    extractor: data.extractor || null,
    webpage_url: data.webpage_url || url,
    formats,
  });
  return { statusCode: 200, headers, body };
};
