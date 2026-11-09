"""Build character pages for the Manga site from NFRP thread scrapes.

python3 tools/characters_gen.py <folder with nfrp_character_*.json> <site root>
Writes <site>/characters/index.html and one page per character.
"""
import glob, html, json, os, re, sys
from urllib.parse import unquote, urlparse, parse_qs
from bs4 import BeautifulSoup, NavigableString, Comment

SRC, SITE = sys.argv[1], sys.argv[2]
OUT = os.path.join(SITE, 'characters')
os.makedirs(OUT, exist_ok=True)

KEEP = {'b', 'strong', 'i', 'em', 'u', 's', 'sup', 'sub', 'br', 'hr', 'div', 'p', 'span', 'ul', 'ol', 'li',
        'table', 'tbody', 'thead', 'tr', 'td', 'th', 'a', 'img', 'blockquote', 'details', 'summary'}
FACT_KEYS = ['Name', 'Clan', 'Bloodlimit', 'Bloodline', 'Age', 'Height', 'Weight', 'Gender', 'Alignment',
             'Birth Country', 'Village', 'Language']
LABELS = ('Rank|Skill|Type|Effect|Special|Drawback|Description|Limit|Cost|Requirements?|Prerequisites?|'
          'Range|Duration|Mastery|Charges Available')
# Art made for a character (files in <site>/characters/art/). First entry is the portrait.
# Gallery runs in the order of her life; PORTRAIT picks the header picture.
ART = {'uchiha-duchess': [('chiaki-young.webp', 'Young'), ('chiaki-hokage.webp', 'Hokage'),
                          ('chiaki-retired-hokage.webp', 'Retired Hokage'), ('chiaki-duchess-1.webp', 'Duchess 1'),
                          ('chiaki-duchess-2.webp', 'Duchess 2')]}
PORTRAIT = {'uchiha-duchess': 3}


def real_href(h):
    if 'viglink.com' in h:
        q = parse_qs(urlparse(h).query).get('u')
        if q:
            h = unquote(q[0])
            if not h.startswith('http'):
                h = 'http:' + h if h.startswith('//') else 'http://' + h
    return h


def clean(raw):
    raw = re.sub(r'\[/?(?:b|i|u|ul|li|div|blockquote|center|font|size|color)[^\]]*\]', '', raw)
    soup = BeautifulSoup(raw, 'html.parser')
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    # forum spoilers -> <details>
    for hd in soup.select('div.spoiler_header'):
        body = hd.find_next_sibling('div', class_='spoiler')
        det = soup.new_tag('details', attrs={'class': 'spoil'})
        sm = soup.new_tag('summary'); sm.string = 'Show hidden text'
        det.append(sm)
        if body:
            body.extract(); body.attrs = {}; det.append(body)
        hd.replace_with(det)
    # "This image has been reduced" wrappers: keep only the picture
    for t in soup.find_all(string=re.compile('This image has been reduced')):
        t.replace_with('')
    for tag in soup.find_all(True):
        if tag.name not in KEEP:
            tag.unwrap(); continue
        a = tag.attrs
        if tag.name == 'a':
            h = real_href(a.get('href', ''))
            if not h or h.startswith('javascript') or h == '/':
                tag.unwrap(); continue
            if h.startswith('/'):  # links into the dead forum
                tag.unwrap(); continue
            tag.attrs = {'href': h, 'rel': 'nofollow noopener', 'target': '_blank'}
        elif tag.name == 'img':
            src = a.get('src', '')
            tag.attrs = {'src': src, 'alt': a.get('alt', ''), 'loading': 'lazy', 'class': 'pic',
                         'onerror': "this.replaceWith(Object.assign(document.createElement('span'),"
                                    "{className:'gone',textContent:'Picture no longer online'}))"}
        elif tag.name in ('td', 'th'):
            tag.attrs = {k: v for k, v in a.items() if k in ('colspan', 'rowspan')}
        elif tag.name == 'details':
            pass
        else:
            tag.attrs = {}
    # a picture link wrapping only an image -> just the image
    for a in soup.find_all('a'):
        if a.find('img') and not a.get_text(strip=True):
            a.unwrap()
    # empty wrappers
    for _ in range(3):
        for tag in soup.find_all(['b', 'i', 'u', 's', 'span', 'div', 'blockquote', 'ul', 'ol', 'p']):
            if not tag.get_text(strip=True) and not tag.find(['img', 'hr', 'table']):
                tag.replace_with(*([soup.new_tag('br')] if tag.name in ('div', 'p', 'blockquote') else []))
    for tag in soup.find_all(['ul', 'ol']):  # stray text directly inside lists
        if not tag.find('li'):
            tag.unwrap()
    s = str(soup)
    s = s.replace(' ', ' ')
    s = re.sub(r'(?:\s*<br/?>\s*){3,}', '<br/><br/>', s)
    s = re.sub(r'^(?:\s*<br/?>)+|(?:<br/?>\s*)+$', '', s)
    return s


def decorate(s):
    """Style technique entries: name line before 'Rank:', field labels, rank seals."""
    s = re.sub(r'((?:<br/>|^|</div>|<div>)\s*)((?:(?!<br/>|<div>|</div>).){2,140}?)'
               r'(\s*<br/>\s*(?:<[^>]+>\s*)*Rank\s*:)',
               lambda m: m.group(1) + '<span class="tn">' + m.group(2) + '</span>' + m.group(3), s)
    s = re.sub(r'(?<![\w"=/-])(' + LABELS + r')\s*:(?!//)', r'<span class="k">\1:</span>', s)

    def seals(m):
        letters = re.findall(r'\b([EDCBAS])\b', m.group(1))
        return m.group(0) + ''.join('<i class="seal">%s</i>' % l for l in letters) if False else \
            '<span class="k">Rank:</span>' + m.group(1)
    s = re.sub(r'<span class="k">Rank:</span>((?:\s|&quot;|"|,|\+|[EDCBAS](?![a-z]))+)',
               lambda m: '<span class="k">Rank:</span> ' + ''.join(
                   '<i class="seal">%s</i>' % l for l in re.findall(r'[EDCBAS]', m.group(1))) + ' ', s)
    s = str(BeautifulSoup(s, 'html.parser'))  # rebalance tags
    s = re.sub(r'(<span class="tn">(?:(?!</span>).)*</span>(?:\s*</[a-z]+>)*)(?:\s*<br/>)+', r'\1', s)
    s = re.sub(r'(?:<br/>\s*)+(<span class="tn">)', r'<br/>\1', s)
    return s


def first_line(h):
    t = BeautifulSoup(h, 'html.parser').get_text('\n')
    for line in t.split('\n'):
        line = re.sub(r'[♠»«]+', '', line).strip(' :-–')
        if len(line) > 1:
            return line[:70] + ('…' if len(line) > 70 else '')
    return ''


def facts(h):
    t = BeautifulSoup(h.replace('<br>', '\n').replace('<br/>', '\n'), 'html.parser').get_text('\n')
    t = t.replace('♠', '')
    out = []
    for k in FACT_KEYS:
        m = re.search(r'(?im)^\s*' + re.escape(k) + r'\s*:?\s*:\s*(.+)$', t) or \
            re.search(r'(?im)^\s*' + re.escape(k) + r'\s*:\s*\n\s*(.+)$', t) or \
            re.search(r'(?im)^\s*' + re.escape(k) + r'\s*:?\s*(\d.+)$', t)
        if m:
            v = m.group(1).strip(' :')
            if v and not v.startswith('(') and len(v) < 90 and k not in [o[0] for o in out]:
                out.append((k, v))
    return out


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def esc(s):
    return html.escape(s, quote=True)


HEAD = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title} · NFRP World</title>
  <meta name="description" content="{desc}">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@600;700&amp;display=swap">
  <link rel="stylesheet" href="../assets/style.css">
  <link rel="stylesheet" href="../assets/characters.css">
  <link rel="icon" href="../assets/icon.png">
  <script src="../assets/characters.js" defer></script>
</head>
<body>
<header><div class="hin">
  <a class="brand" href="https://cassiegiang.github.io/NFRP-World-Wiki/"><img src="../assets/icon.png" alt=""><span>NFRP World</span></a>
  <nav aria-label="Site"><a href="../">Manga</a><a href="./" class="on"{cur}>Characters</a></nav>
</div></header>
<main>
'''
FOOT = '''</main>
<footer>Character sheets from the Naruto Forum Role-play (NFRP), saved from the forum in February 2026. Each sheet is its player's work.</footer>
</body>
</html>
'''

chars = []
for f in sorted(glob.glob(os.path.join(SRC, 'nfrp_character_*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    posts = d['posts']
    owner = posts[0]['author']
    name = re.sub(r'\s*\[?revamp\]?\s*$', '', d['characterName'], flags=re.I).strip()
    revamp = 'revamp' in d['characterName'].lower()
    sheet, replies = [], []
    for p in posts:
        (sheet if p['author'] == owner else replies).append(p)
    fx = facts(posts[0]['htmlContent'])
    fxd = dict(fx)
    real = fxd.get('Name', '')
    sl = slug(name)
    secs = []
    for i, p in enumerate(sheet):
        body = clean(p['htmlContent'])
        if not BeautifulSoup(body, 'html.parser').get_text(strip=True).strip('-– '):
            continue
        title = 'Profile' if i == 0 else first_line(body)
        if title == 'Index' and len(BeautifulSoup(body, 'html.parser').get_text(strip=True)) < 120:
            continue  # the forum's in-thread link list; the contents bar replaces it
        if len(title) > 45:
            title = 'Update, ' + re.sub(r' at .*|,? \d+:\d+.*', '', p['timestamp'])
        plain = BeautifulSoup(body, 'html.parser').get_text(' ', strip=True)
        if len(plain) < 40 and i:  # empty placeholder posts ("Fire", "Reserved", "----")
            continue
        secs.append(dict(id='s%s' % p['postId'], title=title or 'Post', when=p['timestamp'],
                         body=decorate(body), words=len(plain.split())))
    reps = []
    for p in replies:
        txt = BeautifulSoup(clean(p['htmlContent']), 'html.parser').get_text(' ', strip=True)
        reps.append(dict(author=p['author'], when=p['timestamp'], text=txt, html=clean(p['htmlContent'])))
    pic = None
    for p in posts[:2]:
        if p['images']:
            pic = p['images'][0]['src']; break
    chars.append(dict(slug=sl, name=name, real=real, revamp=revamp, owner=owner, facts=fx, secs=secs,
                      reps=reps, url=d['threadUrl'], first=posts[0]['timestamp'],
                      pages=d['pageCount'], total=d['totalPosts'], pic=pic))

for c in chars:
    o = [HEAD.format(title=esc(c['name']), desc=esc('%s, an NFRP character sheet by %s.' % (c['name'], c['owner'])),
                     cur='')]
    o.append('<p class="crumb"><a href="./">Characters</a></p>')
    o.append('<div class="chero">')
    art = ART.get(c['slug'])
    if art:
        pf, pc = art[PORTRAIT.get(c['slug'], 0)]
        o.append('<img class="portrait art" src="art/%s" alt="%s, %s">' % (pf, esc(c['name']), esc(pc)))
    elif c['pic']:
        o.append('<img class="portrait" src="%s" alt="%s" onerror="this.remove()">' % (esc(c['pic']), esc(c['name'])))
    o.append('<div class="cmeta"><h1>%s</h1>' % esc(c['name']))
    sub = []
    if c['real'] and c['real'].lower() not in c['name'].lower():
        sub.append(esc(c['real']))
    o.append('<p class="lead">%s</p>' % ' · '.join(sub + ['Sheet by <b>%s</b>' % esc(c['owner'])] +
                                                    (['revamp'] if c['revamp'] else [])))
    if c['facts']:
        o.append('<dl class="facts">' + ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(v))
                                                for k, v in c['facts'] if k != 'Name') + '</dl>')
    o.append('<p class="meta">First posted %s · %d posts on %d forum page%s · original thread <code>%s</code></p>'
             % (esc(c['first']), c['total'], c['pages'], 's' if c['pages'] > 1 else '', esc(c['url'])))
    o.append('</div></div>')
    if art and len(art) > 1:
        o.append('<h2>Through the years</h2><div class="gallery">' + ''.join(
            '<figure><a href="art/%s"><img src="art/%s" alt="%s, %s" loading="lazy"></a><figcaption>%s</figcaption></figure>'
            % (f, f, esc(c['name']), esc(cap), esc(cap)) for f, cap in art) + '</div>')
        o.append('<h2>Character sheet</h2>')
    o.append('<nav class="toc" aria-label="Sections">' + ''.join(
        '<a href="#%s">%s</a>' % (s['id'], esc(s['title'])) for s in c['secs']) + '</nav>')
    o.append('<div class="toolbar"><input type="search" id="filter" placeholder="Find in this sheet…" '
             'aria-label="Find in this sheet"><button type="button" data-all="1">Open all</button>'
             '<button type="button" data-all="0">Close all</button><span class="count" id="count"></span></div>')
    for i, s in enumerate(c['secs']):
        o.append('<details class="sec" id="%s"%s><summary><span class="st">%s</span><small>%s</small></summary>'
                 '<div class="body post">%s</div></details>'
                 % (s['id'], ' open' if i == 0 else '', esc(s['title']), esc(s['when']), s['body']))
    if c['reps']:
        o.append('<section class="approval" aria-labelledby="appr"><h2 id="appr">Approval</h2>'
                 '<p class="meta">Staff checks and replies from the thread.</p><ul>')
        for r in c['reps']:
            o.append('<li><b>%s</b><small>%s</small><div>%s</div></li>' % (esc(r['author']), esc(r['when']), r['html']))
        o.append('</ul></section>')
    o.append(FOOT)
    open(os.path.join(OUT, c['slug'] + '.html'), 'w', encoding='utf-8').write('\n'.join(o))

# index
o = [HEAD.format(title='Characters', desc='Character sheets from the NFRP roleplay.', cur=' aria-current="page"')]
o.append('<h1>Characters</h1><p class="lead">Character sheets from the Naruto Forum Role-play, as their players '
         'posted them. Open one to read the full sheet: profile, techniques, items and history.</p>')
o.append('<div class="grid chars">')
for c in chars:
    if c['slug'] in ART:
        c['pic'] = 'art/' + ART[c['slug']][PORTRAIT.get(c['slug'], 0)][0]
    fx = dict(c['facts'])
    bits = [fx.get(k) for k in ('Bloodlimit', 'Bloodline', 'Clan', 'Village') if fx.get(k)]
    o.append('<a class="charcard" href="%s.html">%s<b>%s</b><span>%s</span><small>by %s · %d sections</small></a>' % (
        c['slug'], ('<img src="%s" alt="" onerror="this.replaceWith(Object.assign(document.createElement(\'span\'),'
                    '{className:\'mon\',textContent:\'%s\'}))">' % (esc(c['pic']), esc(c['name'][0])))
        if c['pic'] else '<span class="mon">%s</span>' % esc(c['name'][0]),
        esc(c['name']), esc(' · '.join(dict.fromkeys(bits[:2]))), esc(c['owner']), len(c['secs'])))
o.append('</div>')
o.append(FOOT)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write('\n'.join(o))
for c in chars:
    print(c['slug'], c['owner'], len(c['secs']), len(c['reps']), c['facts'], c['pic'])
    print('   ', [s['title'] for s in c['secs']])
