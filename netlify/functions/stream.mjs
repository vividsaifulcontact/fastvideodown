// Netlify Function v2: stream a large video through the server so the browser
// is FORCED to download it (Content-Disposition: attachment) instead of
// opening it in a player tab. Unlike the v1 download function, a streamed
// response has no 6MB limit — the file is piped straight from the CDN to the
// browser, chunk by chunk, without being held in memory. Limited by the 26s
// function timeout, so very large files on a slow connection may cut off.
//
// WHY THE PROXY: YouTube's googlevideo URLs are IP-locked to the IP yt-dlp
// used when it resolved the link (the URL carries ip=<proxy ip> and, for
// many videos, NO ipbypass=yes). The stream runs on a Lambda IP, so a direct
// fetch is rejected with 403. The frontend therefore passes proxyIp= (the
// ip= value from the direct URL); we find the Webshare proxy with that exact
// IP in YTDLP_PROXY and fetch through it, so the CDN sees the IP the URL
// was issued for. Usage:
//   GET /api/stream?url=<direct CDN url>&filename=<name.mp4>&proxyIp=<ip>
import { ProxyAgent } from 'undici';

export default async (request) => {
  const u = new URL(request.url);
  const target = u.searchParams.get('url') || '';
  const filename = (u.searchParams.get('filename') || 'video.mp4').replace(/[^\w.\-]/g, '_').slice(0, 100) || 'video.mp4';
  const proxyIp = u.searchParams.get('proxyIp') || '';
  const json = (obj, status) => new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } });
  if (!/^https?:\/\//.test(target)) return json({ ok: false, error: 'Missing url' }, 400);

  // Find the Webshare proxy whose host is exactly the IP the URL was
  // issued for. YTDLP_PROXY is a comma-separated list of individual
  // proxy URLs (http://user:pass@IP:PORT). If none matches, fall back
  // to a direct fetch (works when the URL has ipbypass=yes).
  let dispatcher;
  if (proxyIp) {
    const proxies = (process.env.YTDLP_PROXY || '').split(',').map(s => s.trim()).filter(Boolean);
    const match = proxies.find(p => {
      try { return new URL(p).hostname === proxyIp; } catch { return false; }
    });
    if (match) dispatcher = new ProxyAgent(match);
  }

  try {
    const res = await fetch(target, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' },
      redirect: 'follow',
      ...(dispatcher ? { dispatcher } : {}),
    });
    if (!res.ok || !res.body) return json({ ok: false, error: 'Could not fetch the file.' }, 502);
    const headers = new Headers();
    headers.set('Content-Type', res.headers.get('content-type') || 'video/mp4');
    headers.set('Content-Disposition', 'attachment; filename="' + filename + '"');
    const len = res.headers.get('content-length');
    if (len) headers.set('Content-Length', len);
    return new Response(res.body, { status: 200, headers });
  } catch (e) {
    return json({ ok: false, error: 'Stream failed.' }, 502);
  }
};

export const config = { path: '/api/stream' };
