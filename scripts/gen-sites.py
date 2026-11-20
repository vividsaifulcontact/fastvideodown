#!/usr/bin/env python3
"""Generate one SEO downloader page per site in sites.txt, plus the
all-sites index and sitemap.xml. Run at build time (Netlify) and locally.
Usage: python3 scripts/gen-sites.py"""
import re, os, html

BASE = 'https://stately-pavlova-7c69c9.netlify.app'
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(OUT, 'sites.txt')) as f:
    sites = sorted({line.strip() for line in f if line.strip()})
print(len(sites), 'site pages to generate')

def slug(n):
    return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-') + '-video-downloader'

def display(n):
    return n[0].upper() + n[1:] if n else n

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%23e11d48'/%3E%3Cstop offset='1' stop-color='%237c3aed'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='64' height='64' rx='14' fill='url(%23g)'/%3E%3Cpath fill='%23fff' d='M32 14a2 2 0 0 1 2 2v14.6l5.3-5.3a2 2 0 1 1 2.8 2.8l-8.7 8.7a2 2 0 0 1-2.8 0l-8.7-8.7a2 2 0 1 1 2.8-2.8l5.3 5.3V16a2 2 0 0 1 2-2z'/%3E%3Crect x='14' y='46' width='36' height='4' rx='2' fill='%23fff'/%3E%3C/svg%3E">
<title>{name} Video Downloader &ndash; Download {name} Videos Free | FastVideoDown</title>
<meta name="description" content="Download {name} videos in HD &amp; MP3 for free with FastVideoDown. Paste any {name} link, pick your quality, and save the video in seconds. No sign-up, no watermark.">
<meta name="keywords" content="{name} video downloader, download {name} videos, {name} to mp4, {name} to mp3, free video downloader">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{base}/{slug}/">
<meta property="og:type" content="website">
<meta property="og:title" content="{name} Video Downloader &ndash; Download {name} Videos Free | FastVideoDown">
<meta property="og:description" content="Paste a {name} link and download the video in HD or MP3. Free, no sign-up, no watermark.">
<meta property="og:url" content="{base}/{slug}/">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1f2937;line-height:1.6}}
a{{color:#2563eb;text-decoration:none}}a:hover{{text-decoration:underline}}
header{{background:#111827;color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}}
.logo{{font-size:22px;font-weight:800;color:#fff;text-decoration:none;display:flex;align-items:center;gap:9px}}.logo-mark{{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#e11d48,#7c3aed);flex:none}}.logo-mark svg{{display:block}}.logo-accent{{background:linear-gradient(90deg,#fda4af,#c4b5fd);-webkit-background-clip:text;background-clip:text;color:transparent}}
nav a{{color:#d1d5db;margin-left:16px;font-size:14px}}
.hero{{background:#111827;color:#fff;text-align:center;padding:44px 20px 36px}}
.hero h1{{font-size:30px;margin-bottom:10px}}.hero p{{color:#d1d5db;max-width:640px;margin:0 auto 22px}}
.btn{{display:inline-block;background:#f59e0b;color:#111827;font-weight:700;padding:12px 26px;border-radius:8px}}
.btn:hover{{text-decoration:none;background:#d97706}}
main{{max-width:820px;margin:0 auto;padding:32px 20px}}
h2{{font-size:22px;margin:28px 0 10px}}h3{{font-size:17px;margin:18px 0 6px}}
ol,ul{{margin:8px 0 8px 22px}}li{{margin-bottom:6px}}
.faq details{{border:1px solid #e5e7eb;border-radius:8px;padding:12px 16px;margin-bottom:10px}}
.faq summary{{font-weight:600;cursor:pointer}}
.note{{background:#fef3c7;border:1px solid #fde68a;border-radius:8px;padding:14px 16px;margin:20px 0}}
footer{{background:#111827;color:#9ca3af;padding:28px 20px;text-align:center;font-size:14px}}
footer a{{color:#d1d5db;margin:0 8px}}
</style>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebApplication","name":"{name} Video Downloader","applicationCategory":"MultimediaApplication","operatingSystem":"Any","offers":{{"@type":"Offer","price":"0","priceCurrency":"USD"}},"url":"{base}/{slug}/"}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{{"@type":"Question","name":"Is the {name} downloader free?","acceptedAnswer":{{"@type":"Answer","text":"Yes. FastVideoDown is free forever. There is no sign-up, no daily limit, and no watermark on downloaded videos."}}}},{{"@type":"Question","name":"What quality can I download {name} videos in?","acceptedAnswer":{{"@type":"Answer","text":"FastVideoDown shows every quality the {name} video was published in, from the original upload quality down to smaller sizes, plus audio-only MP3 where available."}}}},{{"@type":"Question","name":"Do I need an account to download {name} videos?","acceptedAnswer":{{"@type":"Answer","text":"No. Paste the {name} link, pick a quality, and download. No account, no app, and no software to install."}}}}]}}
</script>
</head>
<body>
<header><a class="logo" href="/"><span class="logo-mark"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="#fff" d="M12 3a1 1 0 0 1 1 1v8.6l2.7-2.7a1 1 0 1 1 1.4 1.4l-4.4 4.4a1 1 0 0 1-1.4 0l-4.4-4.4a1 1 0 1 1 1.4-1.4l2.7 2.7V4a1 1 0 0 1 1-1z"/><path fill="#fff" d="M4 20a1 1 0 0 1 1-1h14a1 1 0 1 1 0 2H5a1 1 0 0 1-1-1z"/></svg></span> Fast<span class="logo-accent">VideoDown</span></a><nav><a href="/">Home</a><a href="/youtube-video-downloader/">YouTube</a><a href="/tiktok-video-downloader/">TikTok</a><a href="/sites/">All Downloaders</a><a href="/blog/how-to-download-youtube-videos/">Blog</a></nav></header>
<section class="hero"><h1>{name} Video Downloader</h1><p>Download {name} videos in HD &amp; MP3 for free. Paste any {name} link, pick your quality, and save it in seconds. No sign-up, no watermark.</p><a class="btn" href="/">Download a {name} Video &rarr;</a></section>
<main>
<h2>How to Download {name} Videos in 3 Steps</h2>
<ol><li><strong>Copy the link.</strong> Open the {name} video you want and copy its link from the address bar or the share menu.</li><li><strong>Paste it into FastVideoDown.</strong> Go to the <a href="/">FastVideoDown downloader</a>, paste the link, and click Get Video.</li><li><strong>Pick a quality and save.</strong> Choose the video quality or MP3 audio you want, then tap Download. The file comes straight from {name}'s servers.</li></ol>
<div class="note"><strong>Original quality:</strong> FastVideoDown lists every quality the video was published in on {name}, including the original upload quality, so you can save the best version available.</div>
<h2>Why Download {name} Videos with FastVideoDown?</h2>
<ul><li><strong>Free forever</strong> &mdash; no payment, no account, no daily limit.</li><li><strong>Real quality picker</strong> &mdash; HD, smaller sizes, and audio-only MP3 where the platform offers them.</li><li><strong>Fast direct downloads</strong> &mdash; files come straight from the platform's servers.</li><li><strong>No watermark</strong> &mdash; you get the video as published.</li><li><strong>Private</strong> &mdash; links are processed and never stored.</li><li><strong>Any device</strong> &mdash; works on phone, tablet, and desktop with no app to install.</li></ul>
<h2>Is It Legal to Download {name} Videos?</h2>
<p>Only download videos you own or have permission to save, or that are free for personal use. Respect the creator's rights and {name}'s terms of service. FastVideoDown is a tool for personal, lawful use.</p>
<div class="faq"><h2>Frequently Asked Questions</h2>
<details><summary>Is the {name} downloader free?</summary><p>Yes. FastVideoDown is free forever, with no sign-up and no daily limit.</p></details>
<details><summary>What quality can I download {name} videos in?</summary><p>FastVideoDown shows every quality the {name} video was published in, including the original upload quality, plus audio-only MP3 where available.</p></details>
<details><summary>Do I need an account to download {name} videos?</summary><p>No. Paste the link, pick a quality, and download. No account or app is needed.</p></details>
<details><summary>Can I download {name} videos on my phone?</summary><p>Yes. FastVideoDown works in any mobile browser. Paste the link, choose a quality, and save the file to your phone.</p></details>
</div>
<p style="margin-top:24px"><a href="/">Try the {name} downloader now &rarr;</a> &middot; <a href="/sites/">Browse all 1,000+ downloaders</a></p>
</main>
<footer><a href="/">FastVideoDown</a><a href="/sites/">All Downloaders</a><a href="/privacy.html">Privacy Policy</a><a href="/terms.html">Terms of Use</a><a href="/contact.html">Contact</a><a href="/sitemap.xml">Sitemap</a><br><br>FastVideoDown is not affiliated with {name}. Download only content you own or have permission to save.</footer>
</body>
</html>
"""

count = 0
for n in sites:
    s = slug(n)
    d = os.path.join(OUT, s)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w') as f:
        f.write(PAGE.format(name=html.escape(display(n)), slug=s, base=BASE))
    count += 1
print('pages written:', count)

# --- sites index ---
letters = {}
for n in sites:
    letters.setdefault(n[0].upper(), []).append(n)
idx = ['<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">',
'<title>All Video Downloaders &ndash; 1,000+ Sites | FastVideoDown</title>',
'<meta name="description" content="Browse every video downloader on FastVideoDown: YouTube, TikTok, Instagram, Facebook, X, and 1,000+ more sites. Pick a site and download videos in HD & MP3 free.">',
'<meta name="robots" content="index, follow">',
f'<link rel="canonical" href="{BASE}/sites/">',
'<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1f2937;line-height:1.6}a{color:#2563eb;text-decoration:none}a:hover{text-decoration:underline}header{background:#111827;color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}.logo{font-size:22px;font-weight:800;color:#fff}.logo span{color:#f59e0b}nav a{color:#d1d5db;margin-left:16px;font-size:14px}main{max-width:900px;margin:0 auto;padding:32px 20px}h1{font-size:28px;margin-bottom:8px}h2{font-size:20px;margin:26px 0 10px;border-bottom:1px solid #e5e7eb;padding-bottom:6px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:6px 18px;font-size:15px}.letters{margin:16px 0}.letters a{margin-right:10px;font-weight:600}footer{background:#111827;color:#9ca3af;padding:28px 20px;text-align:center;font-size:14px}footer a{color:#d1d5db;margin:0 8px}</style></head><body>',
'<header><a class="logo" href="/"><span class="logo-mark"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="#fff" d="M12 3a1 1 0 0 1 1 1v8.6l2.7-2.7a1 1 0 1 1 1.4 1.4l-4.4 4.4a1 1 0 0 1-1.4 0l-4.4-4.4a1 1 0 1 1 1.4-1.4l2.7 2.7V4a1 1 0 0 1 1-1z"/><path fill="#fff" d="M4 20a1 1 0 0 1 1-1h14a1 1 0 1 1 0 2H5a1 1 0 0 1-1-1z"/></svg></span> Fast<span class="logo-accent">VideoDown</span></a><nav><a href="/">Home</a><a href="/youtube-video-downloader/">YouTube</a><a href="/tiktok-video-downloader/">TikTok</a><a href="/blog/how-to-download-youtube-videos/">Blog</a></nav></header><main>',
f'<h1>All Video Downloaders &ndash; {len(sites)+8} Sites</h1>',
'<p>Every site FastVideoDown can download from. Pick a site, paste its video link on the <a href="/">homepage</a>, and save the video in HD or MP3 &mdash; free, no sign-up.</p>',
'<div class="letters">' + ' '.join(f'<a href="#{L}">{L}</a>' for L in sorted(letters)) + '</div>']
for L in sorted(letters):
    idx.append(f'<h2 id="{L}">{L}</h2><div class="grid">')
    for n in letters[L]:
        idx.append(f'<a href="/{slug(n)}/">{html.escape(display(n))} Downloader</a>')
    idx.append('</div>')
idx.append('</main><footer><a href="/">FastVideoDown</a><a href="/privacy.html">Privacy Policy</a><a href="/terms.html">Terms of Use</a><a href="/contact.html">Contact</a><a href="/sitemap.xml">Sitemap</a></footer></body></html>')
os.makedirs(os.path.join(OUT, 'sites'), exist_ok=True)
open(os.path.join(OUT, 'sites', 'index.html'), 'w').write('\n'.join(idx))
print('sites index written')

# --- sitemap ---
urls = ['', 'youtube-video-downloader/', 'tiktok-video-downloader/', 'facebook-video-downloader/',
        'instagram-video-downloader/', 'twitter-video-downloader/', 'reddit-video-downloader/',
        'vimeo-video-downloader/', 'dailymotion-video-downloader/', 'sites/',
        'thumbnail-downloader/',
        'privacy.html', 'terms.html', 'contact.html', 'blog/how-to-download-youtube-videos/']
for n in sites:
    urls.append(slug(n) + '/')
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    sm.append(f'  <url><loc>{BASE}/{u}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
sm.append('</urlset>')
open(os.path.join(OUT, 'sitemap.xml'), 'w').write('\n'.join(sm))
print('sitemap urls:', len(urls))
