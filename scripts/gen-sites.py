#!/usr/bin/env python3
"""Generate one SEO downloader page per site in sites.txt, one blog guide
per site, the all-sites index and sitemap.xml.
Every page and blog is VARIED: each site gets a deterministic variant
(by MD5 hash of its name) so no two pages share the same wording,
structure, title pattern, or FAQ order. Categories (news, music, sports,
education, video, social) tailor the copy further.
Run at build time (Cloudflare Pages) and locally.
Usage: python3 scripts/gen-sites.py"""
import re, os, html, hashlib

BASE = 'https://fastvideodown.pages.dev'
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(OUT, 'sites.txt')) as f:
    sites = sorted({line.strip() for line in f if line.strip()})
print(len(sites), 'site pages to generate')

def slug(n):
    return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-') + '-video-downloader'

def display(n):
    return n[0].upper() + n[1:] if n else n

def pick(name, options):
    """Deterministic variant pick by MD5 hash of the site name."""
    h = hashlib.md5(name.encode()).hexdigest()
    return options[int(h[:8], 16) % len(options)]

def category(n):
    nl = n.lower()
    if any(k in nl for k in ['news', 'broadcast', 'channel', 'journal', 'press', 'daily', 'times', 'post']):
        return 'news'
    if any(k in nl for k in ['music', 'audio', 'sound', 'bandcamp', 'spotify', 'song', 'radio']):
        return 'music'
    if any(k in nl for k in ['sport', 'football', 'nfl', 'nba', 'cricket', 'fifa', 'golf', 'tennis', 'boxing', 'wwe', 'ufc']):
        return 'sports'
    if any(k in nl for k in ['edu', 'course', 'learn', 'academy', 'school', 'university', 'lecture']):
        return 'education'
    if any(k in nl for k in ['tube', 'video', 'stream', 'watch', 'play', 'tv', 'film', 'movie', 'cinema']):
        return 'video'
    if any(k in nl for k in ['social', 'tiktok', 'instagram', 'facebook', 'twitter', 'snap', 'reel', 'share', 'chat']):
        return 'social'
    return 'general'

CAT_LINE = {
    'news': 'From breaking-news clips and interviews to full reports, {name} publishes videos people want to keep and rewatch.',
    'music': 'From songs and live sessions to music videos and mixes, {name} is where listeners find audio worth saving.',
    'sports': 'From match highlights and goals to interviews and analysis, {name} is where fans catch the moments that matter.',
    'education': 'From lectures and tutorials to full courses, {name} publishes lessons worth saving for later study.',
    'video': 'From short clips to full-length shows, {name} hosts videos viewers want to watch again and again.',
    'social': 'From viral clips and stories to posts from creators you follow, {name} is full of videos worth saving.',
    'general': 'From short clips to full-length uploads, {name} hosts videos viewers want to keep and watch offline.',
}

# Popular platform pages (hand-written) used for internal "related" links.
POPULAR = [
    ('YouTube', 'youtube-video-downloader'),
    ('TikTok', 'tiktok-video-downloader'),
    ('Facebook', 'facebook-video-downloader'),
    ('Instagram', 'instagram-video-downloader'),
    ('X (Twitter)', 'twitter-video-downloader'),
    ('Reddit', 'reddit-video-downloader'),
    ('Vimeo', 'vimeo-video-downloader'),
    ('Dailymotion', 'dailymotion-video-downloader'),
]

def related_links(name, s):
    links = [(t, u) for t, u in POPULAR if u != s][:5]
    idx = sites.index(name) if name in sites else -1
    if idx >= 0:
        for j in (idx + 1, idx + 2):
            if j < len(sites):
                n2 = sites[j]
                links.append((display(n2), slug(n2)))
    out = []
    for t, u in links[:6]:
        out.append(f'<li><a href="/{u}/">{html.escape(t)} Video Downloader</a></li>')
    return '\n'.join(out)

CSS = """*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1f2937;line-height:1.7}
a{color:#2563eb;text-decoration:none}a:hover{text-decoration:underline}
header{background:#111827;color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
.logo{font-size:22px;font-weight:800;color:#fff;text-decoration:none;display:flex;align-items:center;gap:9px}.logo-mark{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#e11d48,#7c3aed);flex:none}.logo-mark svg{display:block}.logo-accent{background:linear-gradient(90deg,#fda4af,#c4b5fd);-webkit-background-clip:text;background-clip:text;color:transparent}
nav a{color:#d1d5db;margin-left:16px;font-size:14px}
.hero{background:#111827;color:#fff;text-align:center;padding:44px 20px 36px}
.hero h1{font-size:30px;margin-bottom:10px}.hero p{color:#d1d5db;max-width:680px;margin:0 auto 22px}
.btn{display:inline-block;background:#f59e0b;color:#111827;font-weight:700;padding:12px 26px;border-radius:8px}
.btn:hover{text-decoration:none;background:#d97706}
main{max-width:820px;margin:0 auto;padding:32px 20px}
h2{font-size:22px;margin:28px 0 10px}h3{font-size:17px;margin:18px 0 6px}
ol,ul{margin:8px 0 8px 22px}li{margin-bottom:6px}
table{width:100%;border-collapse:collapse;margin:14px 0}th,td{border:1px solid #e5e7eb;padding:9px 12px;text-align:left;font-size:15px}th{background:#f9fafb}
.faq details{border:1px solid #e5e7eb;border-radius:8px;padding:12px 16px;margin-bottom:10px}
.faq summary{font-weight:600;cursor:pointer}
.note{background:#fef3c7;border:1px solid #fde68a;border-radius:8px;padding:14px 16px;margin:20px 0}
.related{background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:16px 20px;margin:24px 0}
.adblock-wall{position:fixed;inset:0;z-index:99999;background:#0f172a;color:#fff;display:none;align-items:center;justify-content:center;padding:24px;text-align:center}
.adblock-wall.show{display:flex}
.adblock-wall .box{max-width:520px}
.adblock-wall h2{font-size:26px;margin-bottom:14px;color:#fff}
.adblock-wall p{color:#cbd5e1;margin-bottom:12px;font-size:16px}
.adblock-wall .steps{text-align:left;background:#1e293b;border-radius:12px;padding:16px 20px;margin:18px 0;font-size:15px;color:#e2e8f0;list-style-position:inside}
.adblock-wall .steps li{margin-bottom:6px}
.adblock-wall .reload-btn{display:inline-block;background:linear-gradient(135deg,#e11d48,#7c3aed);color:#fff;font-weight:700;padding:14px 30px;border-radius:12px;border:0;cursor:pointer;font-size:17px}
footer{background:#111827;color:#9ca3af;padding:28px 20px;text-align:center;font-size:14px}
footer a{color:#d1d5db;margin:0 8px}.ad-label{font-size:11px;color:#94a3b8;text-align:center;letter-spacing:.12em;text-transform:uppercase;margin:10px 0 4px}.ad-banner728,.ad-banner468,.ad-banner300,.ad-banner160,.ad-banner160x600,.ad-native{max-width:100%;overflow:hidden}.ad-native .__bn{display:flex!important;flex-wrap:nowrap!important}.ad-native .__bn .__bn-container{flex:1 1 25%!important;max-width:25%!important;min-width:0!important}.ad-banner728 iframe,.ad-banner468 iframe,.ad-banner300 iframe,.ad-banner160 iframe,.ad-banner160x600 iframe{max-width:100%!important}@media(max-width:768px){.ad-banner468{display:block!important;overflow:hidden;height:45px;max-width:351px;margin-left:auto;margin-right:auto}.ad-banner468 iframe{transform:scale(.75);transform-origin:top left;width:468px!important;max-width:none!important}.ad-banner728{display:none!important}.ad-banner728 iframe{transform:scale(.5);transform-origin:top left;width:728px!important;max-width:none!important}}@media (max-width:600px){.menu-toggle{display:block!important}header .wrap{flex-wrap:wrap}nav{display:none}nav.open{display:flex;flex-wrap:wrap;gap:10px;order:3;width:100%;padding:8px 0 2px}.hero h1{font-size:20px!important;line-height:1.25}.hero p{font-size:14px!important}}html,body{overflow-x:hidden}html.dark{--ink:#e2e8f0;--muted:#94a3b8;--line:#334155;--card:#1e293b;--bg:#0f172a}html.dark body{background:#0f172a!important;color:#e2e8f0!important}html.dark header{background:#1e293b!important;border-color:#334155!important}html.dark nav a{color:#cbd5e1!important}html.dark a{color:#93c5fd}html.dark h1,html.dark h2,html.dark h3{color:#f1f5f9!important}html.dark p,html.dark li,html.dark td{color:#cbd5e1}html.dark input,html.dark textarea,html.dark select{background:#1e293b!important;color:#e2e8f0!important;border-color:#475569!important}html.dark input::placeholder{color:#64748b}html.dark footer{background:#0f172a!important;color:#94a3b8!important}html.dark .card,html.dark .tool,html.dark .step{background:#1e293b!important;border-color:#334155!important}html.dark .meta .sub,html.dark .fmt .d{color:#94a3b8!important}html.dark .meta h3,html.dark .fmt .q,html.dark .fmt .d b,html.dark .group h4{color:#f1f5f9!important}.night-toggle{background:none;border:1px solid #cbd5e1;border-radius:999px;padding:5px 12px;font-size:13px;cursor:pointer;color:inherit;white-space:nowrap}.menu-toggle{display:none;background:none;border:0;font-size:22px;line-height:1;cursor:pointer;color:inherit;padding:6px 8px}html.dark .night-toggle{border-color:#475569}"""

ADBLOCK_WALL = """<div class="adblock-wall" id="adblockWall" role="alertdialog" aria-label="Ad blocker detected">
  <div class="box">
    <h2>🚫 Ad Blocker Detected</h2>
    <p>FastVideoDown is <b>100% free</b> because of ads. To keep it free for everyone, please disable your ad blocker for this site.</p>
    <p id="adblockBrave" style="display:none">You are using <b>Brave browser</b>. Please turn off Brave Shields for this site: click the <b>lion icon</b> in the address bar and switch Shields <b>off</b>.</p>
    <ul class="steps">
      <li><b>Chrome / Edge:</b> click the ad-blocker icon in the toolbar → "Pause on this site" or "Don't run on this site".</li>
      <li><b>Firefox:</b> click the shield icon in the address bar → turn off Enhanced Tracking Protection for this site.</li>
      <li><b>Phone:</b> open your browser settings or your ad-blocker app and allow fastvideodown.pages.dev.</li>
    </ul>
    <button class="reload-btn" type="button" onclick="location.reload()">I've disabled it — Reload the page</button>
    <p style="margin-top:16px;font-size:14px;color:#94a3b8">FastVideoDown collects nothing and shows no pop-ups — the ads are the only thing that keeps the servers running.</p>
  </div>
</div>
<script>
(function(){
  function baitElementBlocked(){
    var bait = document.createElement('div');
    bait.className = 'adsbox ad-banner ads adslot pub_300x250';
    bait.style.cssText = 'width:300px;height:250px;position:absolute;left:-9999px;top:0;';
    bait.innerHTML = '&nbsp;';
    document.body.appendChild(bait);
    var cs = window.getComputedStyle(bait);
    var blocked = bait.offsetHeight === 0 || cs.display === 'none' || cs.visibility === 'hidden';
    bait.remove();
    return blocked;
  }
  function baitScriptBlocked(){
    return new Promise(function(resolve){
      var done = false;
      var s = document.createElement('script');
      s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js';
      s.async = true;
      s.onload = function(){ if(!done){ done = true; resolve(false); } };
      s.onerror = function(){ if(!done){ done = true; resolve(true); } };
      document.head.appendChild(s);
      setTimeout(function(){ if(!done){ done = true; resolve(true); } }, 5000);
    });
  }
  async function isBrave(){
    try {
      if (navigator.brave && navigator.brave.isBrave) return await navigator.brave.isBrave();
    } catch(e){}
    return false;
  }
  async function check(){
    await new Promise(function(r){ setTimeout(r, 200); });
    var elBlocked = baitElementBlocked();
    var brave = await isBrave();
    var blocked = elBlocked || brave;
    if (!blocked) {
      blocked = await baitScriptBlocked();
    }
    if (blocked) {
      var wall = document.getElementById('adblockWall');
      if (wall) wall.classList.add('show');
      if (brave) {
        var b = document.getElementById('adblockBrave');
        if (b) b.style.display = 'block';
      }
      document.body.style.overflow = 'hidden';
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', check);
  } else {
    check();
  }
})();
</script>"""

FAVICON = """<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">"""

SOCIAL_BAR = """<script data-cfasync="false" src="https://bellnewyork.org/14/f35df6e06fc69f99b8b2ce47d7d3bd4c"></script>"""
NATIVE_BANNER = """<div class="ad-label">Ads</div><div class="ad-native"><script async="async" data-cfasync="false" src="https://bellnewyork.org/21/7fe12e0cd0157c1a5aa6a92146507cd8"></script><div id="container-7fe12e0cd0157c1a5aa6a92146507cd8"></div></div>"""
BANNER_300 = """<div class="ad-label">Ads</div><div class="ad-banner300"><script>
  atOptions = {
    'key' : 'e44833ba896b1c664de7c10791813111',
    'format' : 'iframe',
    'height' : 250,
    'width' : 300,
    'params' : {}
  };
</script><script src="https://bellnewyork.org/22/e44833ba896b1c664de7c10791813111"></script></div>"""
BANNER_160 = """<div class="ad-label">Ads</div><div class="ad-banner160"><script>
  atOptions = {
    'key' : '4ccb6c7e07ad296505f3956a0fa5f9b5',
    'format' : 'iframe',
    'height' : 300,
    'width' : 160,
    'params' : {}
  };
</script><script src="https://bellnewyork.org/22/4ccb6c7e07ad296505f3956a0fa5f9b5"></script></div>"""
BANNER_160x600 = """<div class="ad-label">Ads</div><div class="ad-banner160x600"><script>
  atOptions = {
    'key' : 'b59ae1a26b0176eed2cb5f7a13ab12ba',
    'format' : 'iframe',
    'height' : 600,
    'width' : 160,
    'params' : {}
  };
</script><script src="https://bellnewyork.org/22/b59ae1a26b0176eed2cb5f7a13ab12ba"></script></div>"""
BANNER_320 = """<style>.ad-sticky320{position:fixed;left:0;right:0;bottom:0;z-index:9998;text-align:center;background:#fff;padding:4px 0 2px;box-shadow:0 -2px 10px rgba(0,0,0,.12);display:none}@media(max-width:768px){.ad-sticky320{display:block}body{padding-bottom:58px}}</style><div class="ad-sticky320"><div class="ad-label" style="margin:0 0 2px">Ads</div><script>
  atOptions = {
    'key' : 'c68d728f8fb3b0e170aed6f600c92dbc',
    'format' : 'iframe',
    'height' : 50,
    'width' : 320,
    'params' : {}
  };
</script><script src="https://bellnewyork.org/22/c68d728f8fb3b0e170aed6f600c92dbc"></script></div>"""
BANNER_728 = """<div class="ad-label">Ads</div><div class="ad-banner728"><script>
  atOptions = {
    'key' : 'b151b4d08c14193b5a8bbfd698df3094',
    'format' : 'iframe',
    'height' : 90,
    'width' : 728,
    'params' : {}
  };
</script><script src="https://bellnewyork.org/22/b151b4d08c14193b5a8bbfd698df3094"></script></div>"""
HEADER = """<header><a class="logo" href="/"><span class="logo-mark"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="#fff" d="M12 3a1 1 0 0 1 1 1v8.6l2.7-2.7a1 1 0 1 1 1.4 1.4l-4.4 4.4a1 1 0 0 1-1.4 0l-4.4-4.4a1 1 0 1 1 1.4-1.4l2.7 2.7V4a1 1 0 0 1 1-1z"/><path fill="#fff" d="M4 20a1 1 0 0 1 1-1h14a1 1 0 1 1 0 2H5a1 1 0 0 1-1-1z"/></svg></span> Fast<span class="logo-accent">VideoDown</span></a><nav><a href="/">Home</a><a href="/youtube-video-downloader/">YouTube</a><a href="/tiktok-video-downloader/">TikTok</a><a href="/sites/">All Downloaders</a><a href="/blog/">Blog</a></nav><button class="menu-toggle" id="menuToggle" onclick="document.querySelector(&quot;header nav&quot;).classList.toggle(&quot;open&quot;)" aria-label="Menu">☰</button><button class="night-toggle" id="nightToggle" onclick="toggleNight()">🌙 Night</button></header>"""

FOOTER = """<footer><a href="/">FastVideoDown</a><a href="/sites/">All Downloaders</a><a href="/blog/">Blog</a><a href="/privacy.html">Privacy Policy</a><a href="/terms.html">Terms of Use</a><a href="/contact.html">Contact</a><a href="/sitemap.xml">Sitemap</a><br><br>{disclaimer}</footer>"""

# ---------- PAGE (tool page) variants ----------
PAGE_INTROS = [
    "Looking for a fast, free way to save videos from {name}? FastVideoDown is a free online {name} video downloader that lets you download any public {name} video in its original quality &mdash; HD, smaller sizes, or audio-only MP3. There is nothing to install and no account to create: paste the link, choose a quality, and the file is yours. It works on Android, iPhone, Windows, and Mac, right in your browser.",
    "Save any {name} video in seconds with FastVideoDown &mdash; the free {name} downloader that needs no app, no account, and no payment. Paste a {name} link, pick HD video or MP3 audio, and download the file straight to your phone or computer. It works in any browser, on any device.",
    "FastVideoDown turns any public {name} link into a downloadable file. No software, no sign-up, no cost: paste the link and get the video in HD, a smaller size, or audio-only MP3. Your links are processed on the fly and never stored, so every download stays private.",
]
PAGE_INTRO2 = [
    "{cat} Whether you want to watch offline, keep a favourite clip, or save the audio as MP3, FastVideoDown handles the whole job in a few seconds.",
    "People save {name} videos to watch on the go, keep favourites, or listen to the audio later. FastVideoDown makes it a one-minute job: paste, pick, download.",
    "Offline viewing, favourite clips, audio-only saves &mdash; whatever you need, FastVideoDown does it from a single link, in the quality the video was published in.",
]
PAGE_WHATIS = [
    "{name} is a popular video platform where creators publish videos for viewers around the world. People watch {name} for entertainment, learning, news, music, and more. Because {name} does not offer a built-in download button for most videos, a downloader like FastVideoDown is the easiest way to save a video you like for offline viewing.",
    "On {name}, creators share videos with a global audience &mdash; clips, shows, music, talks, and more. Most videos have no download button, which is why people use FastVideoDown: paste the link and save the video you want, in the quality it was published in.",
    "{name} brings together creators and viewers from everywhere. If you have ever wanted to keep a {name} video for offline watching, FastVideoDown is the tool for it: free, fast, and working in any browser.",
]
PAGE_HERO_SUBS = [
    "Download {name} videos in HD &amp; MP3 for free. Paste any {name} link, pick your quality, and save it in seconds. No sign-up, no watermark.",
    "Save {name} videos free in HD or MP3. No app, no account &mdash; just paste the link and download.",
    "Free {name} video downloader: HD, MP3, and thumbnail in seconds. Works on phone and PC.",
]
PAGE_TIPS = [
    "<li>Copy the link from the video's own page or share button, not from a search result, so the downloader finds the right video.</li><li>Pick the highest quality when you have Wi-Fi, and a smaller size when you are on mobile data.</li><li>Use the MP3 option when you only need the audio &mdash; the file is much smaller.</li><li>Download the thumbnail too if you want a cover image for the video.</li><li>Only save videos you have the right to keep, and respect the creator's work.</li>",
    "<li>Always copy the full link from the video page &mdash; a shortened or partial link may fail.</li><li>On a slow connection, choose a smaller size first; you can re-download in HD later on Wi-Fi.</li><li>MP3 audio is the fastest option for music, talks, and podcasts.</li><li>Keep your downloads organised by saving them to a folder you can find again.</li><li>Check that the video is public before downloading; private videos cannot be saved.</li>",
    "<li>Use the share button on the video to copy a clean link.</li><li>HD is best for big screens; standard size is best for phones with little storage.</li><li>Save the thumbnail as well &mdash; it makes a great cover or preview image.</li><li>If a link fails, reload the video page and copy the link again.</li><li>Respect copyright: only keep videos you own or have permission to save.</li>",
]
PAGE_FAQS = [
    ("Is the {name} downloader free?", "Yes. FastVideoDown is free forever, with no sign-up and no daily limit."),
    ("What quality can I download {name} videos in?", "FastVideoDown shows every quality the {name} video was published in, including the original upload quality, plus audio-only MP3 where available."),
    ("Do I need an account to download {name} videos?", "No. Paste the link, pick a quality, and download. No account or app is needed."),
    ("Can I download {name} videos on my phone?", "Yes. FastVideoDown works in any mobile browser. Paste the link, choose a quality, and save the file to your phone."),
    ("Can I download {name} videos as MP3 audio?", "Yes. Where the video has audio, FastVideoDown offers an audio-only MP3 option alongside the video qualities."),
    ("Can I download the thumbnail of a {name} video?", "Yes. FastVideoDown also shows the video's thumbnail, which you can save as a JPG image."),
    ("Why did my {name} link fail?", "Private, deleted, or age-restricted videos cannot be downloaded. Check that the video is public and the link is complete, then try again."),
    ("Is it legal to download {name} videos?", "Only download videos you own or have permission to save. Respect the creator's rights and {name}'s terms of service."),
]
PAGE_TITLES = [
    "{name} Video Downloader &ndash; Download {name} Videos Free in HD &amp; MP3 | FastVideoDown",
    "Download {name} Videos Free &ndash; {name} Video Downloader (HD &amp; MP3) | FastVideoDown",
    "{name} Downloader &ndash; Save {name} Videos in HD, MP3 &amp; Thumbnail Free | FastVideoDown",
]
PAGE_DESCS = [
    "Download {name} videos in HD &amp; MP3 for free with FastVideoDown. Paste any {name} link, pick your quality, and save the video in seconds. No sign-up, no watermark, works on phone and PC.",
    "Free {name} video downloader: save any public {name} video in HD or MP3, no account needed. Paste the link and download in seconds on Android, iPhone, or PC.",
    "Save {name} videos free with FastVideoDown. HD video, audio-only MP3, and thumbnail downloads from any {name} link &mdash; no app, no sign-up, no watermark.",
]

def page_html(n, s):
    name = html.escape(display(n))
    cat = CAT_LINE[category(n)].format(name=name)
    intro = pick(n, PAGE_INTROS).format(name=name)
    intro2 = pick(n + 'b', PAGE_INTRO2).format(name=name, cat=cat)
    whatis = pick(n + 'c', PAGE_WHATIS).format(name=name)
    hero = pick(n + 'd', PAGE_HERO_SUBS).format(name=name)
    tips = pick(n + 'e', PAGE_TIPS)
    title = pick(n + 'f', PAGE_TITLES).format(name=name)
    desc = pick(n + 'g', PAGE_DESCS).format(name=name)
    # FAQ order rotated by variant
    faqs = list(PAGE_FAQS)
    rot = int(hashlib.md5((n + 'h').encode()).hexdigest()[:8], 16) % len(faqs)
    faqs = faqs[rot:] + faqs[:rot]
    faq_html = '\n'.join(
        f'<details><summary>{q.format(name=name)}</summary><p>{a.format(name=name)}</p></details>'
        for q, a in faqs)
    faq_json = ','.join(
        '{{"@type":"Question","name":"' + q.format(name=name).replace('"', '') +
        '","acceptedAnswer":{"@type":"Answer","text":"' + a.format(name=name).replace('"', '') + '"}}'
        for q, a in faqs)
    related = related_links(n, s)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<script id="aclib" type="text/javascript" src="//acscdn.com/script/aclib.js"></script><script type="text/javascript">
    aclib.runAutoTag({{
        zoneId: 'jz7nrikboa',
    }});
</script>
<script>
(function(){{try{{if(localStorage.getItem('fvd-theme')==='dark')document.documentElement.classList.add('dark')}}catch(e){{}}}})();
function toggleNight(){{var h=document.documentElement;var d=h.classList.toggle('dark');try{{localStorage.setItem('fvd-theme',d?'dark':'light')}}catch(e){{}}var b=document.getElementById('nightToggle');if(b)b.textContent=d?'☀️ Day':'🌙 Night';}}
document.addEventListener('DOMContentLoaded',function(){{try{{if(document.documentElement.classList.contains('dark')){{var b=document.getElementById('nightToggle');if(b)b.textContent='☀️ Day';}}}}catch(e){{}}}});
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
{FAVICON}
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{name} video downloader, download {name} videos, {name} to mp4, {name} to mp3, {name} video download free, save {name} video, {name} downloader online">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{BASE}/{s}/">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE}/{s}/">
<style>{CSS}</style>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebApplication","name":"{name} Video Downloader","applicationCategory":"MultimediaApplication","operatingSystem":"Any","offers":{{"@type":"Offer","price":"0","priceCurrency":"USD"}},"url":"{BASE}/{s}/"}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"{BASE}/"}},{{"@type":"ListItem","position":2,"name":"All Downloaders","item":"{BASE}/sites/"}},{{"@type":"ListItem","position":3,"name":"{name} Video Downloader","item":"{BASE}/{s}/"}}]}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{faq_json}]}}
</script>
</head>
<body>
{ADBLOCK_WALL}
{HEADER}
<section class="hero"><h1>{name} Video Downloader</h1><p>{hero}</p><a class="btn" href="/">Download a {name} Video &rarr;</a></section>
{BANNER_728}
<main>
<p>{intro}</p>
<p>{intro2}</p>
<h2>What Is {name}?</h2>
<p>{whatis}</p>
<h2>How to Download {name} Videos in 3 Steps</h2>
<ol><li><strong>Copy the link.</strong> Open the {name} video you want and copy its link from the address bar or the share menu.</li><li><strong>Paste it into FastVideoDown.</strong> Go to the <a href="/">FastVideoDown downloader</a>, paste the link into the box, and click Get Video.</li><li><strong>Pick a quality and save.</strong> Choose the video quality or MP3 audio you want, then tap Download. The file comes straight from {name}'s servers, in the quality it was published in.</li></ol>
<div class="note"><strong>Original quality:</strong> FastVideoDown lists every quality the video was published in on {name}, including the original upload quality, so you can save the best version available.</div>
<h2>Download {name} Videos on Your Phone</h2>
<p>FastVideoDown works in any mobile browser, so there is no app to install. On Android, paste the {name} link in Chrome, pick a quality, and the video saves to your Downloads folder. On iPhone, use Safari the same way &mdash; the file saves to Files, ready to watch offline. The same steps work on tablets and desktop computers.</p>
<h2>{name} Video Quality &amp; Formats</h2>
<table><tr><th>Format</th><th>Best for</th></tr>
<tr><td><strong>HD video (MP4)</strong> &ndash; the highest quality the video was published in</td><td>Watching on a big screen or keeping the best copy</td></tr>
<tr><td><strong>Standard video (MP4)</strong> &ndash; smaller file sizes</td><td>Saving space on your phone or slow connections</td></tr>
<tr><td><strong>Audio only (MP3)</strong> &ndash; just the sound track</td><td>Music, podcasts, and talks you only want to listen to</td></tr>
<tr><td><strong>Thumbnail (JPG)</strong> &ndash; the video's cover image</td><td>Using the cover as a picture or preview</td></tr></table>
<p>The exact qualities depend on how the video was uploaded to {name}. FastVideoDown always shows every option the platform makes available.</p>
{NATIVE_BANNER}
<h2>Why Download {name} Videos with FastVideoDown?</h2>
<ul><li><strong>Free forever</strong> &mdash; no payment, no account, no daily limit.</li><li><strong>Real quality picker</strong> &mdash; HD, smaller sizes, and audio-only MP3 where the platform offers them.</li><li><strong>Fast direct downloads</strong> &mdash; files come straight from the platform's servers.</li><li><strong>No watermark</strong> &mdash; you get the video as published.</li><li><strong>Private</strong> &mdash; links are processed and never stored.</li><li><strong>Any device</strong> &mdash; works on phone, tablet, and desktop with no app to install.</li></ul>
<h2>Tips for the Best {name} Downloads</h2>
<ul>{tips}</ul>
<h2>Is It Legal to Download {name} Videos?</h2>
<p>Only download videos you own or have permission to save, or that are free for personal use. Respect the creator's rights and {name}'s terms of service. FastVideoDown is a tool for personal, lawful use.</p>
<div class="faq"><h2>Frequently Asked Questions</h2>
{faq_html}
</div>
<div class="related"><h2>More Video Downloaders</h2><ul>
{related}
</ul></div>
<p style="margin-top:24px"><a href="/">Try the {name} downloader now &rarr;</a> &middot; <a href="/sites/">Browse all 1,000+ downloaders</a></p>
</main>
{BANNER_300}
{FOOTER.format(disclaimer=f"FastVideoDown is not affiliated with {name}. Download only content you own or have permission to save.")}
{SOCIAL_BAR}
{BANNER_320}
</body>
</html>
"""

# ---------- BLOG (guide) variants: 4 different angles ----------
BLOG_TITLES = [
    "How to Download {name} Videos in HD (2026 Guide) &ndash; Free {name} Downloader | FastVideoDown",
    "Download {name} Videos Free &ndash; Save {name} Videos in HD &amp; MP3 (2026) | FastVideoDown",
    "{name} Video Downloader: The Complete 2026 Guide to Saving {name} Videos | FastVideoDown",
    "How to Download {name} Videos on Android &amp; iPhone (2026) &ndash; Free Guide | FastVideoDown",
]
BLOG_DESCS = [
    "Learn how to download {name} videos in HD and MP3 for free in 2026. Step-by-step guide for phone and PC, quality options, and answers to common questions.",
    "Save any {name} video free in HD or MP3. This 2026 guide shows the fastest way to download {name} videos on Android, iPhone, and PC &mdash; no app, no account.",
    "The complete guide to the {name} video downloader: how it works, which quality to pick, mobile downloads, and free HD &amp; MP3 options for 2026.",
    "Download {name} videos on your phone in 2026: a free, step-by-step guide for Android and iPhone, with HD video and MP3 audio options.",
]
BLOG_INTROS = [
    "Want to save a video from {name} to watch offline? This guide shows you how to download {name} videos in HD and MP3 for free, on your phone or computer, in under a minute. No app, no account, and no payment &mdash; just the link and the free <a href=\"/{slug}/\">{name} downloader</a> on FastVideoDown.",
    "If you have ever wished you could keep a {name} video &mdash; to watch on a flight, share with a friend, or listen to as audio &mdash; this guide is for you. FastVideoDown downloads any public {name} video free, in HD or MP3, with no app and no account. Here is how it works in 2026.",
    "{name} videos are easy to watch but hard to keep: most have no download button. The fix takes less than a minute. In this guide you will learn how to save any {name} video in HD or MP3 with the free <a href=\"/{slug}/\">{name} downloader</a> &mdash; on phone and PC.",
    "Downloading a {name} video should be simple, and with FastVideoDown it is. This 2026 guide walks you through saving {name} videos in HD and MP3 on Android, iPhone, and desktop &mdash; free, with no app to install and no account to create.",
]
BLOG_BODIES = [
    # Variant 0 — step-by-step how-to
    """<h2>What Is {name}?</h2>
<p>{name} is a video platform where creators publish videos for viewers all over the world. People use {name} for entertainment, learning, music, news, and more. Because most videos on {name} have no built-in download button, the easiest way to keep a video is with an online downloader.</p>
<h2>How to Download {name} Videos &ndash; Step by Step</h2>
<ol><li><strong>Find the video.</strong> Open {name} and go to the video you want to save.</li><li><strong>Copy its link.</strong> Tap Share, then Copy Link &mdash; or copy the address from your browser's address bar.</li><li><strong>Open FastVideoDown.</strong> Go to the <a href="/">FastVideoDown homepage</a> and paste the link into the box.</li><li><strong>Click Get Video.</strong> The tool reads the link and lists every available quality.</li><li><strong>Pick a quality and download.</strong> Choose HD video, a smaller size, or MP3 audio, then tap Download. The file saves to your device.</li></ol>
<h2>Which Quality Should You Pick?</h2>
<p>FastVideoDown lists every quality the video was published in on {name}. Pick the highest quality when you want the best picture, for example to watch on a TV or keep a favourite clip. Pick a smaller size when you are short on storage or on mobile data. If you only want the sound &mdash; a song, a talk, or a podcast &mdash; choose the MP3 audio option; the file is much smaller and plays anywhere.</p>
<h2>Download {name} Videos on Mobile</h2>
<p>On Android, open the {name} link in Chrome, paste it into FastVideoDown, and save the file to Downloads. On iPhone, use Safari the same way; the file lands in the Files app. Nothing to install, and the same steps work on tablets and desktop computers.</p>
<h2>Is Downloading {name} Videos Free?</h2>
<p>Yes. FastVideoDown is free forever. There is no account, no daily limit, and no watermark on the videos you save. Your links are processed on the fly and never stored.</p>""",
    # Variant 1 — offline / keep-it angle
    """<h2>Why Save {name} Videos?</h2>
<p>Streaming is fine until the Wi-Fi drops, the video is removed, or you want to watch it again later. Saving a {name} video means you own a copy: watch it on a plane, show it to a friend without internet, or keep a favourite before it disappears. FastVideoDown makes that copy in seconds, free.</p>
<h2>The Fastest Way to Download a {name} Video</h2>
<p>You do not need an app, an account, or any software. Copy the {name} link, paste it into <a href="/">FastVideoDown</a>, and choose a quality. That is the whole process. The file comes straight from {name}'s servers, in the quality it was published in &mdash; HD when it is available, plus smaller sizes and MP3 audio.</p>
<h2>HD Video or MP3 Audio?</h2>
<p>It depends what the video is for. HD video is the right pick for watching &mdash; the picture is sharp on any screen. MP3 audio is the right pick for listening &mdash; a song, a talk, or a podcast takes a fraction of the space and plays in any music app. FastVideoDown shows both options side by side, so you pick per video.</p>
<h2>Watch {name} Videos Offline</h2>
<p>Once a video is on your device, it plays anywhere: on a flight, on the metro, or anywhere with no signal. On Android the file saves to Downloads; on iPhone it saves to Files. No app is needed to play it &mdash; your phone's built-in player is enough.</p>
<h2>What Does It Cost?</h2>
<p>Nothing. FastVideoDown is free forever, with no daily limit and no watermark. Paste a link, download, done.</p>""",
    # Variant 2 — complete guide / features angle
    """<h2>How the {name} Downloader Works</h2>
<p>FastVideoDown reads a public {name} link and asks the platform for the video's available files. It then shows you every quality the video was published in &mdash; HD, standard sizes, and audio-only MP3 &mdash; plus the thumbnail. You pick one, and the file downloads straight from {name}'s servers. Nothing is uploaded, nothing is stored, and nothing is installed on your device.</p>
<h2>Features of the Free {name} Downloader</h2>
<ul><li><strong>Original quality</strong> &mdash; HD when the video was published in HD.</li><li><strong>MP3 audio</strong> &mdash; save just the sound for music, talks, and podcasts.</li><li><strong>Thumbnail download</strong> &mdash; grab the video's cover image as a JPG.</li><li><strong>No watermark</strong> &mdash; the video you save is the video as published.</li><li><strong>No account</strong> &mdash; no sign-up, no email, no app.</li><li><strong>Any device</strong> &mdash; Android, iPhone, Windows, Mac, and tablets.</li></ul>
<h2>Step-by-Step: Save a {name} Video</h2>
<ol><li>Copy the video link from {name} (Share &rarr; Copy Link, or the address bar).</li><li>Paste it into the <a href="/">FastVideoDown downloader</a>.</li><li>Click Get Video and wait a few seconds.</li><li>Choose HD, a smaller size, or MP3, then tap Download.</li></ol>
<h2>Common Problems and Fixes</h2>
<p>If a link fails, the video is usually private, deleted, or age-restricted &mdash; those cannot be downloaded. Check that the video plays in your browser while logged out, copy the link again from the video page, and retry. Public videos work on the first try in almost every case.</p>
<h2>Is It Free?</h2>
<p>Yes. FastVideoDown costs nothing and has no daily limit. Use it as often as you like.</p>""",
    # Variant 3 — mobile-first angle
    """<h2>Save {name} Videos on Your Phone</h2>
<p>Most people watch {name} on their phone &mdash; so the downloader is built for phones first. There is no app to install and no account to create. Open your browser, paste the link, and the video saves to your device in under a minute.</p>
<h2>Download {name} Videos on Android</h2>
<ol><li>Open the {name} video and tap Share &rarr; Copy Link.</li><li>Open Chrome and go to <a href="/">FastVideoDown</a>.</li><li>Paste the link and tap Get Video.</li><li>Pick HD or MP3 and tap Download. The file lands in your Downloads folder.</li></ol>
<h2>Download {name} Videos on iPhone</h2>
<ol><li>Copy the link from the {name} app or Safari.</li><li>Open Safari and go to <a href="/">FastVideoDown</a>.</li><li>Paste the link and tap Get Video.</li><li>Choose a quality and tap Download. The file saves to the Files app, ready to watch offline.</li></ol>
<h2>Download {name} Videos on PC</h2>
<p>On Windows or Mac, copy the link from your browser's address bar, paste it into FastVideoDown, and pick a quality. The file downloads to your usual Downloads folder. The same free tool works on every device &mdash; no software to install anywhere.</p>
<h2>HD or MP3: What Should You Choose?</h2>
<p>Choose HD video when you want to watch the video again. Choose MP3 when you only want the sound &mdash; music, a talk, or a podcast &mdash; because the file is far smaller. FastVideoDown lists both, so the choice is yours for every video.</p>""",
]
BLOG_FAQS = [
    ("Is downloading {name} videos free?", "Yes. FastVideoDown is free forever, with no sign-up and no daily limit."),
    ("What quality can I download {name} videos in?", "FastVideoDown shows every quality the video was published in, from the original upload quality down to smaller sizes, plus audio-only MP3 where available."),
    ("Can I download {name} videos on my phone?", "Yes. It works in any mobile browser on Android and iPhone, with no app to install."),
    ("Why did my {name} link fail?", "Private, deleted, or age-restricted videos cannot be downloaded. Make sure the video is public and the link is complete, then try again."),
    ("Can I save a {name} video as MP3?", "Yes. Where the video has audio, FastVideoDown offers an audio-only MP3 option."),
    ("Do I need to install an app?", "No. FastVideoDown works in your browser on any device &mdash; no app, no software, no account."),
]
BLOG_CONCLUSIONS = [
    "Downloading {name} videos is simple: copy the link, paste it into FastVideoDown, and pick your quality. In a few seconds you have the video &mdash; in HD, a smaller size, or MP3 &mdash; saved on your own device, ready to watch offline whenever you like.",
    "That is all there is to it. One link, one click, and the {name} video is yours &mdash; in HD or MP3, free, on any device. Keep the ones you love and watch them whenever you want, online or off.",
    "With FastVideoDown, saving a {name} video takes less time than watching it. Paste the link, choose HD or MP3, and the file is on your device &mdash; free, private, and ready offline.",
]

def blog_html(n, s, bslug):
    name = html.escape(display(n))
    v = int(hashlib.md5((n + 'blog').encode()).hexdigest()[:8], 16) % len(BLOG_TITLES)
    title = BLOG_TITLES[v].format(name=name)
    desc = BLOG_DESCS[v].format(name=name)
    intro = BLOG_INTROS[v].format(name=name, slug=s)
    body = BLOG_BODIES[v].format(name=name, slug=s)
    concl = pick(n + 'blogc', BLOG_CONCLUSIONS).format(name=name)
    # FAQ: 4 questions, rotated by variant
    faqs = list(BLOG_FAQS)
    rot = int(hashlib.md5((n + 'blogf').encode()).hexdigest()[:8], 16) % len(faqs)
    faqs = (faqs[rot:] + faqs[:rot])[:4]
    faq_html = '\n'.join(
        f'<details><summary>{q.format(name=name)}</summary><p>{a.format(name=name)}</p></details>'
        for q, a in faqs)
    faq_json = ','.join(
        '{{"@type":"Question","name":"' + q.format(name=name).replace('"', '') +
        '","acceptedAnswer":{"@type":"Answer","text":"' + a.format(name=name).replace('"', '') + '"}}'
        for q, a in faqs)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<script id="aclib" type="text/javascript" src="//acscdn.com/script/aclib.js"></script><script type="text/javascript">
    aclib.runAutoTag({{
        zoneId: 'jz7nrikboa',
    }});
</script>
<script>
(function(){{try{{if(localStorage.getItem('fvd-theme')==='dark')document.documentElement.classList.add('dark')}}catch(e){{}}}})();
function toggleNight(){{var h=document.documentElement;var d=h.classList.toggle('dark');try{{localStorage.setItem('fvd-theme',d?'dark':'light')}}catch(e){{}}var b=document.getElementById('nightToggle');if(b)b.textContent=d?'☀️ Day':'🌙 Night';}}
document.addEventListener('DOMContentLoaded',function(){{try{{if(document.documentElement.classList.contains('dark')){{var b=document.getElementById('nightToggle');if(b)b.textContent='☀️ Day';}}}}catch(e){{}}}});
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
{FAVICON}
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="how to download {name} videos, {name} video downloader, download {name} video free, {name} to mp4, {name} to mp3">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{BASE}/blog/{bslug}/">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE}/blog/{bslug}/">
<style>{CSS}</style>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{title}","author":{{"@type":"Organization","name":"FastVideoDown","url":"{BASE}/"}},"publisher":{{"@type":"Organization","name":"FastVideoDown","url":"{BASE}/"}},"mainEntityOfPage":{{"@type":"WebPage","@id":"{BASE}/blog/{bslug}/"}}}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{faq_json}]}}
</script>
</head>
<body>
{ADBLOCK_WALL}
{HEADER}
<main>
{BANNER_728}
<h1>{title.split(' &ndash; ')[0].split(' | ')[0]}</h1>
<p>{intro}</p>
{body}
{NATIVE_BANNER}
<h2>Frequently Asked Questions</h2>
<div class="faq">
{faq_html}
</div>
<h2>Conclusion</h2>
<p>{concl} <a href="/{s}/">Try the {name} downloader now &rarr;</a></p>
<p><a href="/blog/">More guides</a> &middot; <a href="/sites/">Browse all 1,000+ downloaders</a></p>
</main>
{BANNER_300}
{FOOTER.format(disclaimer=f"FastVideoDown is not affiliated with {name}. Download only content you own or have permission to save.")}
{SOCIAL_BAR}
{BANNER_320}
</body>
</html>
"""

count = 0
for n in sites:
    s = slug(n)
    d = os.path.join(OUT, s)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w') as f:
        f.write(page_html(n, s))
    bslug = s + '-guide'
    bd = os.path.join(OUT, 'blog', bslug)
    os.makedirs(bd, exist_ok=True)
    with open(os.path.join(bd, 'index.html'), 'w') as f:
        f.write(blog_html(n, s, bslug))
    count += 1
print('pages written:', count)
print('blog guides written:', count)

# --- sites index ---
letters = {}
for n in sites:
    letters.setdefault(n[0].upper(), []).append(n)
idx = ['<!DOCTYPE html><html lang="en"><head><script id="aclib" type="text/javascript" src="//acscdn.com/script/aclib.js"></script><script type="text/javascript">aclib.runAutoTag({zoneId: \"jz7nrikboa\",});</script><script>(function(){try{if(localStorage.getItem(\"fvd-theme\")==="dark")document.documentElement.classList.add(\"dark\")}catch(e){}})();function toggleNight(){var h=document.documentElement;var d=h.classList.toggle(\"dark\");try{localStorage.setItem(\"fvd-theme\",d?\"dark\":\"light\")}catch(e){}var b=document.getElementById(\"nightToggle\");if(b)b.textContent=d?\"\\u2600\\uFE0F Day\":\"\\uD83C\\uDF19 Night\";}document.addEventListener(\"DOMContentLoaded\",function(){try{if(document.documentElement.classList.contains(\"dark\")){var b=document.getElementById(\"nightToggle\");if(b)b.textContent=\"\\u2600\\uFE0F Day\";}}catch(e){}});</script><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><link rel="icon" type="image/x-icon" href="/favicon.ico"><link rel="icon" type="image/svg+xml" href="/favicon.svg">',
'<title>All Video Downloaders &ndash; 1,000+ Sites | FastVideoDown</title>',
'<meta name="description" content="Browse every video downloader on FastVideoDown: YouTube, TikTok, Instagram, Facebook, X, and 1,000+ more sites. Pick a site and download videos in HD & MP3 free.">',
'<meta name="robots" content="index, follow">',
f'<link rel="canonical" href="{BASE}/sites/">',
'<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1f2937;line-height:1.6}a{color:#2563eb;text-decoration:none}a:hover{text-decoration:underline}header{background:#111827;color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}.logo{font-size:22px;font-weight:800;color:#fff}.logo span{color:#f59e0b}nav a{color:#d1d5db;margin-left:16px;font-size:14px}main{max-width:900px;margin:0 auto;padding:32px 20px}h1{font-size:28px;margin-bottom:8px}h2{font-size:20px;margin:26px 0 10px;border-bottom:1px solid #e5e7eb;padding-bottom:6px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:6px 18px;font-size:15px}.letters{margin:16px 0}.letters a{margin-right:10px;font-weight:600}footer{background:#111827;color:#9ca3af;padding:28px 20px;text-align:center;font-size:14px}footer a{color:#d1d5db;margin:0 8px}.ad-label{font-size:11px;color:#94a3b8;text-align:center;letter-spacing:.12em;text-transform:uppercase;margin:10px 0 4px}.ad-banner728,.ad-banner468,.ad-banner300,.ad-banner160,.ad-banner160x600,.ad-native{max-width:100%;overflow:hidden}.ad-native .__bn{display:flex!important;flex-wrap:nowrap!important}.ad-native .__bn .__bn-container{flex:1 1 25%!important;max-width:25%!important;min-width:0!important}.ad-banner728 iframe,.ad-banner468 iframe,.ad-banner300 iframe,.ad-banner160 iframe,.ad-banner160x600 iframe{max-width:100%!important}@media(max-width:768px){.ad-banner468{display:block!important;overflow:hidden;height:45px;max-width:351px;margin-left:auto;margin-right:auto}.ad-banner468 iframe{transform:scale(.75);transform-origin:top left;width:468px!important;max-width:none!important}.ad-banner728{display:none!important}.ad-banner728 iframe{transform:scale(.5);transform-origin:top left;width:728px!important;max-width:none!important}}@media (max-width:600px){.menu-toggle{display:block!important}header .wrap{flex-wrap:wrap}nav{display:none}nav.open{display:flex;flex-wrap:wrap;gap:10px;order:3;width:100%;padding:8px 0 2px}.hero h1{font-size:20px!important;line-height:1.25}.hero p{font-size:14px!important}}html,body{overflow-x:hidden}html.dark{--ink:#e2e8f0;--muted:#94a3b8;--line:#334155;--card:#1e293b;--bg:#0f172a}html.dark body{background:#0f172a!important;color:#e2e8f0!important}html.dark header{background:#1e293b!important;border-color:#334155!important}html.dark nav a{color:#cbd5e1!important}html.dark a{color:#93c5fd}html.dark h1,html.dark h2,html.dark h3{color:#f1f5f9!important}html.dark p,html.dark li,html.dark td{color:#cbd5e1}html.dark input,html.dark textarea,html.dark select{background:#1e293b!important;color:#e2e8f0!important;border-color:#475569!important}html.dark input::placeholder{color:#64748b}html.dark footer{background:#0f172a!important;color:#94a3b8!important}html.dark .card,html.dark .tool,html.dark .step{background:#1e293b!important;border-color:#334155!important}html.dark .meta .sub,html.dark .fmt .d{color:#94a3b8!important}html.dark .meta h3,html.dark .fmt .q,html.dark .fmt .d b,html.dark .group h4{color:#f1f5f9!important}.night-toggle{background:none;border:1px solid #cbd5e1;border-radius:999px;padding:5px 12px;font-size:13px;cursor:pointer;color:inherit;white-space:nowrap}.menu-toggle{display:none;background:none;border:0;font-size:22px;line-height:1;cursor:pointer;color:inherit;padding:6px 8px}html.dark .night-toggle{border-color:#475569}.adblock-wall{position:fixed;inset:0;z-index:99999;background:#0f172a;color:#fff;display:none;align-items:center;justify-content:center;padding:24px;text-align:center}.adblock-wall.show{display:flex}.adblock-wall .box{max-width:520px}.adblock-wall h2{font-size:26px;margin-bottom:14px;color:#fff;border:0;padding:0}.adblock-wall p{color:#cbd5e1;margin-bottom:12px;font-size:16px}.adblock-wall .steps{text-align:left;background:#1e293b;border-radius:12px;padding:16px 20px;margin:18px 0;font-size:15px;color:#e2e8f0;list-style-position:inside}.adblock-wall .steps li{margin-bottom:6px}.adblock-wall .reload-btn{display:inline-block;background:linear-gradient(135deg,#e11d48,#7c3aed);color:#fff;font-weight:700;padding:14px 30px;border-radius:12px;border:0;cursor:pointer;font-size:17px}</style></head><body>',
'<header><a class="logo" href="/">Fast<span>VideoDown</span></a><nav><a href="/">Home</a><a href="/youtube-video-downloader/">YouTube</a><a href="/tiktok-video-downloader/">TikTok</a><a href="/blog/">Blog</a></nav><button class="menu-toggle" id="menuToggle" onclick="document.querySelector(&quot;header nav&quot;).classList.toggle(&quot;open&quot;)" aria-label="Menu">☰</button><button class="night-toggle" id="nightToggle" onclick="toggleNight()">🌙 Night</button></header><main>',
f'<h1>All Video Downloaders &ndash; {len(sites)+8} Sites</h1>',
'<p>Every site FastVideoDown can download from. Pick a site, paste its video link on the <a href="/">homepage</a>, and save the video in HD or MP3 &mdash; free, no sign-up.</p>',
'<div class="letters">' + ' '.join(f'<a href="#{L}">{L}</a>' for L in sorted(letters)) + '</div>']
for L in sorted(letters):
    idx.append(f'<h2 id="{L}">{L}</h2><div class="grid">')
    for n in letters[L]:
        idx.append(f'<a href="/{slug(n)}/">{html.escape(display(n))} Downloader</a>')
    idx.append('</div>')
idx.append('</main><footer><a href="/">FastVideoDown</a><a href="/privacy.html">Privacy Policy</a><a href="/terms.html">Terms of Use</a><a href="/contact.html">Contact</a><a href="/sitemap.xml">Sitemap</a></footer>' + SOCIAL_BAR + BANNER_320 + '</body></html>')
os.makedirs(os.path.join(OUT, 'sites'), exist_ok=True)
open(os.path.join(OUT, 'sites', 'index.html'), 'w').write('\n'.join(idx).replace('<body>', '<body>' + ADBLOCK_WALL, 1))
print('sites index written')

# --- blog index ---
bidx = ['<!DOCTYPE html><html lang="en"><head><script id="aclib" type="text/javascript" src="//acscdn.com/script/aclib.js"></script><script type="text/javascript">aclib.runAutoTag({zoneId: \"jz7nrikboa\",});</script><script>(function(){try{if(localStorage.getItem(\"fvd-theme\")==="dark")document.documentElement.classList.add(\"dark\")}catch(e){}})();function toggleNight(){var h=document.documentElement;var d=h.classList.toggle(\"dark\");try{localStorage.setItem(\"fvd-theme\",d?\"dark\":\"light\")}catch(e){}var b=document.getElementById(\"nightToggle\");if(b)b.textContent=d?\"\\u2600\\uFE0F Day\":\"\\uD83C\\uDF19 Night\";}document.addEventListener(\"DOMContentLoaded\",function(){try{if(document.documentElement.classList.contains(\"dark\")){var b=document.getElementById(\"nightToggle\");if(b)b.textContent=\"\\u2600\\uFE0F Day\";}}catch(e){}});</script><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><link rel="icon" type="image/x-icon" href="/favicon.ico"><link rel="icon" type="image/svg+xml" href="/favicon.svg">',
'<title>Video Downloader Guides &ndash; How to Download Videos from 1,000+ Sites | FastVideoDown</title>',
'<meta name="description" content="Step-by-step guides to downloading videos from YouTube, TikTok, Instagram, Facebook, X, and 1,000+ more sites in HD and MP3, free.">',
'<meta name="robots" content="index, follow">',
f'<link rel="canonical" href="{BASE}/blog/">',
'<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1f2937;line-height:1.6}a{color:#2563eb;text-decoration:none}a:hover{text-decoration:underline}header{background:#111827;color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}.logo{font-size:22px;font-weight:800;color:#fff}.logo span{color:#f59e0b}nav a{color:#d1d5db;margin-left:16px;font-size:14px}main{max-width:900px;margin:0 auto;padding:32px 20px}h1{font-size:28px;margin-bottom:8px}h2{font-size:20px;margin:26px 0 10px;border-bottom:1px solid #e5e7eb;padding-bottom:6px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:6px 18px;font-size:15px}footer{background:#111827;color:#9ca3af;padding:28px 20px;text-align:center;font-size:14px}footer a{color:#d1d5db;margin:0 8px}.ad-label{font-size:11px;color:#94a3b8;text-align:center;letter-spacing:.12em;text-transform:uppercase;margin:10px 0 4px}.ad-banner728,.ad-banner468,.ad-banner300,.ad-banner160,.ad-banner160x600,.ad-native{max-width:100%;overflow:hidden}.ad-native .__bn{display:flex!important;flex-wrap:nowrap!important}.ad-native .__bn .__bn-container{flex:1 1 25%!important;max-width:25%!important;min-width:0!important}.ad-banner728 iframe,.ad-banner468 iframe,.ad-banner300 iframe,.ad-banner160 iframe,.ad-banner160x600 iframe{max-width:100%!important}@media(max-width:768px){.ad-banner468{display:block!important;overflow:hidden;height:45px;max-width:351px;margin-left:auto;margin-right:auto}.ad-banner468 iframe{transform:scale(.75);transform-origin:top left;width:468px!important;max-width:none!important}.ad-banner728{display:none!important}.ad-banner728 iframe{transform:scale(.5);transform-origin:top left;width:728px!important;max-width:none!important}}@media (max-width:600px){.menu-toggle{display:block!important}header .wrap{flex-wrap:wrap}nav{display:none}nav.open{display:flex;flex-wrap:wrap;gap:10px;order:3;width:100%;padding:8px 0 2px}.hero h1{font-size:20px!important;line-height:1.25}.hero p{font-size:14px!important}}html,body{overflow-x:hidden}html.dark{--ink:#e2e8f0;--muted:#94a3b8;--line:#334155;--card:#1e293b;--bg:#0f172a}html.dark body{background:#0f172a!important;color:#e2e8f0!important}html.dark header{background:#1e293b!important;border-color:#334155!important}html.dark nav a{color:#cbd5e1!important}html.dark a{color:#93c5fd}html.dark h1,html.dark h2,html.dark h3{color:#f1f5f9!important}html.dark p,html.dark li,html.dark td{color:#cbd5e1}html.dark input,html.dark textarea,html.dark select{background:#1e293b!important;color:#e2e8f0!important;border-color:#475569!important}html.dark input::placeholder{color:#64748b}html.dark footer{background:#0f172a!important;color:#94a3b8!important}html.dark .card,html.dark .tool,html.dark .step{background:#1e293b!important;border-color:#334155!important}html.dark .meta .sub,html.dark .fmt .d{color:#94a3b8!important}html.dark .meta h3,html.dark .fmt .q,html.dark .fmt .d b,html.dark .group h4{color:#f1f5f9!important}.night-toggle{background:none;border:1px solid #cbd5e1;border-radius:999px;padding:5px 12px;font-size:13px;cursor:pointer;color:inherit;white-space:nowrap}.menu-toggle{display:none;background:none;border:0;font-size:22px;line-height:1;cursor:pointer;color:inherit;padding:6px 8px}html.dark .night-toggle{border-color:#475569}.adblock-wall{position:fixed;inset:0;z-index:99999;background:#0f172a;color:#fff;display:none;align-items:center;justify-content:center;padding:24px;text-align:center}.adblock-wall.show{display:flex}.adblock-wall .box{max-width:520px}.adblock-wall h2{font-size:26px;margin-bottom:14px;color:#fff;border:0;padding:0}.adblock-wall p{color:#cbd5e1;margin-bottom:12px;font-size:16px}.adblock-wall .steps{text-align:left;background:#1e293b;border-radius:12px;padding:16px 20px;margin:18px 0;font-size:15px;color:#e2e8f0;list-style-position:inside}.adblock-wall .steps li{margin-bottom:6px}.adblock-wall .reload-btn{display:inline-block;background:linear-gradient(135deg,#e11d48,#7c3aed);color:#fff;font-weight:700;padding:14px 30px;border-radius:12px;border:0;cursor:pointer;font-size:17px}</style></head><body>',
'<header><a class="logo" href="/">Fast<span>VideoDown</span></a><nav><a href="/">Home</a><a href="/youtube-video-downloader/">YouTube</a><a href="/tiktok-video-downloader/">TikTok</a><a href="/sites/">All Downloaders</a></nav><button class="menu-toggle" id="menuToggle" onclick="document.querySelector(&quot;header nav&quot;).classList.toggle(&quot;open&quot;)" aria-label="Menu">☰</button><button class="night-toggle" id="nightToggle" onclick="toggleNight()">🌙 Night</button></header><main>',
f'<h1>Video Downloader Guides &ndash; {len(sites)+1} Articles</h1>',
'<p>Step-by-step guides for downloading videos from every site FastVideoDown supports. Each guide covers how to copy the link, pick a quality, and save the video in HD or MP3 &mdash; free, on phone and PC.</p>',
'<h2>Featured Guides</h2><div class="grid">',
'<a href="/blog/how-to-download-youtube-videos/">How to Download YouTube Videos</a>',
'</div><h2>All Guides</h2><div class="grid">']
for n in sites:
    bidx.append(f'<a href="/blog/{slug(n)}-guide/">How to Download {html.escape(display(n))} Videos</a>')
bidx.append('</div></main><footer><a href="/">FastVideoDown</a><a href="/sites/">All Downloaders</a><a href="/privacy.html">Privacy Policy</a><a href="/terms.html">Terms of Use</a><a href="/contact.html">Contact</a><a href="/sitemap.xml">Sitemap</a></footer>' + SOCIAL_BAR + BANNER_320 + '</body></html>')
os.makedirs(os.path.join(OUT, 'blog'), exist_ok=True)
open(os.path.join(OUT, 'blog', 'index.html'), 'w').write('\n'.join(bidx).replace('<body>', '<body>' + ADBLOCK_WALL, 1))
print('blog index written')

# --- sitemap ---
urls = ['', 'youtube-video-downloader/', 'tiktok-video-downloader/', 'facebook-video-downloader/',
        'instagram-video-downloader/', 'twitter-video-downloader/', 'reddit-video-downloader/',
        'vimeo-video-downloader/', 'dailymotion-video-downloader/', 'sites/', 'blog/',
        'thumbnail-downloader/',
        'privacy.html', 'terms.html', 'contact.html', 'blog/how-to-download-youtube-videos/']
for n in sites:
    urls.append(slug(n) + '/')
    urls.append('blog/' + slug(n) + '-guide/')
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    sm.append(f'  <url><loc>{BASE}/{u}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
sm.append('</urlset>')
open(os.path.join(OUT, 'sitemap.xml'), 'w').write('\n'.join(sm))
print('sitemap urls:', len(urls))
