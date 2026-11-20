#!/usr/bin/env python3
"""Δημιουργεί στατικές σελίδες (/meets/, /merch/<slug>/ κ.λπ.) από το index.html,
με δικό τους τίτλο, περιγραφή, canonical, εικόνα κοινοποίησης και JSON-LD,
καθώς και sitemap.xml, robots.txt και 404.html. Τρέξε το μετά από κάθε αλλαγή."""
import json, os, re, html, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://abarthclub.gr'
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
src = re.sub(r'<script type="application/ld\+json">.*?</script>\n', '', src, flags=re.S)

# ---- products & guides από το ίδιο το index.html ----
def js_products():
    block = src[src.index('const PRODUCTS=['):src.index('];', src.index('const PRODUCTS=['))]
    out = []
    for m in re.finditer(r"\{id:'([^']+)',slug:'([^']+)',name:'([^']+)',cat:'([^']+)',tag:'([^']*)',price:([\d.]+)(?:,was:([\d.]+))?.*?img:\['([^']+)'.*?desc:'([^']+)'\}", block):
        out.append(dict(id=m[1], slug=m[2], name=m[3], cat=m[4], tag=m[5], price=float(m[6]), img=m[8], desc=m[9]))
    return out
PRODUCTS = js_products()
gs = re.search(r"const GSLUG=(\[[^\]]+\])", src)[1]
GSLUG = json.loads(gs.replace("'", '"'))
GTITLE = re.findall(r"^ \['([^']+)','([^']+)',\[", src[src.index('const guides=['):src.index('];', src.index('const guides=['))], re.M)

ORG = {"@type": "Organization", "@id": BASE + "/#org", "name": "ABARTH_CLUB_GR", "url": BASE + "/",
       "logo": BASE + "/img/logo.png", "sameAs": ["https://instagram.com/abarth_club_gr"], "email": "Abarthclubgr@gmail.com"}

def product_ld(p):
    return {"@type": "Product", "name": p['name'], "image": [f"{BASE}/img/{p['img']}.jpg"], "description": p['desc'],
            "brand": {"@type": "Brand", "name": "ABARTH_CLUB_GR"}, "sku": p['id'], "url": f"{BASE}/merch/{p['slug']}/",
            "offers": {"@type": "Offer", "price": f"{p['price']:.2f}", "priceCurrency": "EUR", "url": f"{BASE}/merch/{p['slug']}/",
                       "availability": "https://schema.org/OutOfStock" if p['tag'] == 'sold' else "https://schema.org/InStock",
                       "itemCondition": "https://schema.org/NewCondition", "seller": {"@id": BASE + "/#org"},
                       "shippingDetails": {"@type": "OfferShippingDetails", "shippingRate": {"@type": "MonetaryAmount", "value": "3.00", "currency": "EUR"},
                                           "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "GR"},
                                           "deliveryTime": {"@type": "ShippingDeliveryTime", "handlingTime": {"@type": "QuantitativeValue", "minValue": 1, "maxValue": 3, "unitCode": "DAY"},
                                                            "transitTime": {"@type": "QuantitativeValue", "minValue": 1, "maxValue": 3, "unitCode": "DAY"}}},
                       "hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy", "applicableCountry": "GR", "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                                                   "merchantReturnDays": 14, "returnMethod": "https://schema.org/ReturnByMail", "returnFees": "https://schema.org/FreeReturn"}}}

EVENT = {"@type": "Event", "name": "Car meet First Mission · ABARTH_CLUB_GR", "startDate": "2026-12-05T22:00:00+02:00", "endDate": "2026-12-06T01:00:00+02:00",
         "eventStatus": "https://schema.org/EventScheduled", "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
         "location": {"@type": "Place", "name": "Varkiza Resort", "address": {"@type": "PostalAddress", "addressLocality": "Βάρκιζα", "addressRegion": "Αττική", "addressCountry": "GR"}},
         "image": [BASE + "/img/poster-mission.jpg"], "description": "Βραδινό car meet στη Βάρκιζα και κομβόι για τα μεσάνυχτα στον Ναό του Ποσειδώνα στο Σούνιο. Ανοιχτό σε Abarth, Fiat, Alfa Romeo και Lancia.",
         "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR", "availability": "https://schema.org/InStock", "url": BASE + "/meets/first-mission/"},
         "organizer": {"@id": BASE + "/#org"}, "url": BASE + "/meets/first-mission/"}

def crumbs(items):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + u} for i, (n, u) in enumerate(items)]}

def page(path, title, desc, image, ld, noindex=False):
    s = src
    s = re.sub(r'<title>.*?</title>', '<title>' + html.escape(title) + '</title>', s, count=1)
    s = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="' + html.escape(desc) + '">', s, count=1)
    s = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{BASE}{path}">', s, count=1)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{BASE}{path}">', s, count=1)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="' + html.escape(title.split(' | ')[0]) + '">', s, count=1)
    s = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="' + html.escape(desc) + '">', s, count=1)
    if image:
        s = s.replace(f'{BASE}/img/og-shop.jpg', f'{BASE}/img/{image}')
        if not image.startswith('og-'):
            s = re.sub(r'<meta property="og:image:width" content="\d+"><meta property="og:image:height" content="\d+">', '', s)
            s = re.sub(r'<meta property="og:image:(width|height)" content="\d+">\n?', '', s)
    graph = {"@context": "https://schema.org", "@graph": [ORG] + ld}
    s = s.replace('</head>', '<script type="application/ld+json">' + json.dumps(graph, ensure_ascii=False) + '</script>\n</head>', 1)
    if noindex:
        s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">', 1)
    return s

def write(rel, content):
    fp = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, 'w', encoding='utf-8').write(content)

urls = []
def add(path, *a, **k):
    rel = (path.strip('/') + '/index.html') if path != '/' else 'index.html'
    write(rel, page(path, *a, **k)); urls.append(path)

shop_list = {"@type": "ItemList", "name": "Official Merch ABARTH_CLUB_GR", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/merch/{p['slug']}/"} for i, p in enumerate(PRODUCTS)]}
site = {"@type": "WebSite", "@id": BASE + "/#site", "name": "ABARTH_CLUB_GR", "url": BASE + "/", "inLanguage": "el-GR", "publisher": {"@id": BASE + "/#org"}}
add('/', 'ABARTH_CLUB_GR · Official Merch Shop | Abarth Club Ελλάδα',
    'Επίσημο merch του Abarth Club GR: φούτερ, T-shirt, καπέλα και αξεσουάρ. Αποστολή BOX NOW σε όλη την Ελλάδα. Car meets στην Αθήνα για Abarth, Fiat, Alfa Romeo και Lancia.',
    None, [site, shop_list] + [product_ld(p) for p in PRODUCTS])
for p in PRODUCTS:
    eur = (f"{p['price']:.0f}" if p['price'] == int(p['price']) else f"{p['price']:.2f}".replace('.', ',')) + '€'
    add(f"/merch/{p['slug']}/", f"{p['name']} · {eur} | ABARTH_CLUB_GR", p['desc'][:158], p['img'] + '.jpg',
        [product_ld(p), crumbs([('Merch', '/'), (p['name'], f"/merch/{p['slug']}/")])])
add('/meets/', 'Car Meets στην Αθήνα · First Mission 5/12 | ABARTH_CLUB_GR',
    'Οι συναντήσεις του Abarth Club GR στην Αθήνα: First Mission το Σάββατο 5 Δεκεμβρίου, Βάρκιζα → Σούνιο. Πρόγραμμα, κανόνες, φωτογραφίες και άλμπουμ.',
    'poster-mission.jpg', [EVENT, crumbs([('Meets', '/meets/')])])
add('/meets/first-mission/', 'First Mission · Car meet Σάββατο 5/12, Βάρκιζα → Σούνιο | ABARTH_CLUB_GR',
    'Car meet First Mission του Abarth Club GR: Σάββατο 5 Δεκεμβρίου 2026, 22:00 Varkiza Resort, 23:00 αναχώρηση, 00:00 Ναός Ποσειδώνα στο Σούνιο. Δωρεάν, ανοιχτό σε όλα τα ιταλικά.',
    'poster-mission.jpg', [EVENT, crumbs([('Meets', '/meets/'), ('First Mission', '/meets/first-mission/')])])
add('/garage/', 'Garage μελών · 77 Abarth, Fiat, Alfa Romeo & Lancia | ABARTH_CLUB_GR',
    'Τα αυτοκίνητα των μελών του Abarth Club GR: Abarth 595, Grande Punto, MiTo, Giulietta, Delta και άλλα ιταλικά από όλη την Ελλάδα.',
    None, [crumbs([('Garage', '/garage/')])])
add('/odigoi/', 'Οδηγοί αγοράς Abarth, Fiat, Alfa Romeo & Lancia | ABARTH_CLUB_GR',
    'Τι να προσέξεις πριν αγοράσεις Abarth 595, Grande Punto, MiTo, Giulietta και άλλα ιταλικά. Κινητήρες, συχνά προβλήματα, πρώτες μετατροπές και διαδρομές στην Αττική.',
    None, [crumbs([('Οδηγοί', '/odigoi/')])])
for slug, (t, sub) in zip(GSLUG, GTITLE):
    add(f'/odigoi/{slug}/', f'Οδηγός {t}: τι να προσέξεις πριν την αγορά | ABARTH_CLUB_GR',
        f'Οδηγός για {t} ({sub}) από την κοινότητα του Abarth Club GR: κινητήρες, τι να προσέξεις πριν την αγορά και πρώτες μετατροπές.',
        None, [{"@type": "Article", "headline": f"Οδηγός {t}", "inLanguage": "el-GR", "author": {"@id": BASE + "/#org"}, "publisher": {"@id": BASE + "/#org"},
                "mainEntityOfPage": f"{BASE}/odigoi/{slug}/"}, crumbs([('Οδηγοί', '/odigoi/'), (t, f'/odigoi/{slug}/')])])
write('merch/index.html', page('/', 'ABARTH_CLUB_GR · Official Merch Shop', 'Επίσημο merch του Abarth Club GR.', None, [], noindex=False).replace('<base href="/">', '<base href="/"><meta http-equiv="refresh" content="0;url=/">'))
write('404.html', page('/', 'Η σελίδα δεν βρέθηκε | ABARTH_CLUB_GR', 'Η σελίδα δεν βρέθηκε. Δες το official merch του Abarth Club GR.', None, [], noindex=True))

today = datetime.date.today().isoformat()
pri = lambda u: '1.0' if u == '/' else '0.9' if u.startswith('/merch/') or u == '/meets/first-mission/' else '0.7'
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      ''.join(f'  <url><loc>{BASE}{u}</loc><lastmod>{today}</lastmod><priority>{pri(u)}</priority></url>\n' for u in urls) + '</urlset>\n')
write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')
print(len(urls), 'pages', [p['slug'] for p in PRODUCTS])
