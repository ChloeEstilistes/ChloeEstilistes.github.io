#!/usr/bin/env python3
"""Genera la parte de productos de chloeestilistes.com a partir de la hoja de Google (pestaña "Web").

Qué hace (para que Google vea los productos sin depender de JavaScript):
  - productos/<producto>/index.html : una página por producto (con datos de producto para Google)
  - productos/index.html            : rellena las tarjetas y los datos para Google
  - salerm/index.html               : página "Productos Salerm en Barcelona"
  - index.html                      : rellena el carrusel de productos del inicio
  - sitemap.xml                     : añade las páginas de productos

Lo ejecuta GitHub Actions cada día (.github/workflows/productos.yml). También se puede lanzar a mano:
  python3 tools/productos.py
"""
import csv, html, io, json, os, re, sys, unicodedata, urllib.request
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_CSV = 'https://docs.google.com/spreadsheets/d/1jzho5U994GN3NV-uN9WKg4COmYo4BpK7N3jYnz0Mvq4/gviz/tq?tqx=out:csv&sheet=Web'
WEB = 'https://chloeestilistes.com'
WA = '34610273609'
HOY = date.today().isoformat()
DIR = 'Rambla de Prim, 45 bis'
SALON = {'@type': 'HairSalon', '@id': WEB + '/#salon', 'name': 'Chloe Estilistes'}

e = lambda s: html.escape(str(s or ''), quote=True)


def leer():
    with urllib.request.urlopen(URL_CSV, timeout=30) as r:
        t = r.read().decode('utf-8')
    ps = [p for p in csv.DictReader(io.StringIO(t)) if (p.get('id') or '').strip()]
    if not ps:
        sys.exit('La hoja no tiene productos: no toco nada.')
    for p in ps:
        p['regalo'] = p['id'].startswith('TARJETA')
        p['ok'] = (p.get('disponible') or '').strip().lower() == 'si'
        p['slug'] = slug(p)
        p['url'] = f"{WEB}/productos/{p['slug']}/"
        p['eur'] = f"{float(p['precio'] or 0):.2f}".replace('.', ',') + ' €'
        ds = re.sub(r'\s*(Recógel[oa]|Pídela por WhatsApp).*$', '', p.get('descripcion') or '', flags=re.S)
        ds = re.sub(r'^.*Producto profesional de peluquería\.$', '', ds).strip()
        if p['regalo']:
            ds = 'Tarjeta regalo para cualquier servicio de Chloe Estilistes: color, mechas, balayage, corte, alisados y tratamientos. Pídela por WhatsApp, te la preparamos y la recoges en el salón.'
        p['ds'] = ds
        msg = (f"¡Hola! Me gustaría una tarjeta regalo de {p['eur']}." if p['regalo']
               else f"¡Hola! Me gustaría reservar {p['nombre']} ({p['eur']}) para recogerlo en el salón.")
        p['wa'] = f'https://wa.me/{WA}?text=' + urllib.parse.quote(msg)
        p['boton'] = 'Pedir tarjeta' if p['regalo'] else ('Reservar' if p['ok'] else 'Avisadme')
    return ps


def slug(p):
    m, n = (p.get('marca') or '').strip(), (p.get('nombre') or '').strip()
    base = n if (not m or m == 'Chloe Estilistes' or n.lower().startswith(m.lower())) else f'{m} {n}'
    base = unicodedata.normalize('NFD', base).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', base).strip('-')


def ld_producto(p):
    d = {'@type': 'Product', 'name': p['nombre'], 'url': p['url'], 'sku': p['id'],
         'brand': {'@type': 'Brand', 'name': p.get('marca') or 'Chloe Estilistes'},
         'offers': {'@type': 'Offer', 'price': f"{float(p['precio'] or 0):.2f}", 'priceCurrency': 'EUR',
                    'itemCondition': 'https://schema.org/NewCondition',
                    'availability': 'https://schema.org/InStoreOnly' if p['ok'] else 'https://schema.org/OutOfStock',
                    'url': p['url'], 'seller': SALON,
                    'availableAtOrFrom': {'@type': 'Place', 'name': 'Chloe Estilistes', 'address': {
                        '@type': 'PostalAddress', 'streetAddress': 'Rambla de Prim, 45 Bis', 'addressLocality': 'Barcelona',
                        'postalCode': '08019', 'addressCountry': 'ES'}}}}
    if p.get('foto'): d['image'] = p['foto']
    if p['ds']: d['description'] = p['ds']
    if re.fullmatch(r'\d{8,14}', p.get('gtin') or ''): d['gtin'] = p['gtin']
    return d


def tarjeta(p, estatica=True):
    foto = (f'<div class="ph"><img src="{e(p["foto"])}" alt="{e(p["nombre"])}" loading="lazy" width="600" height="600"></div>' if p.get('foto')
            else '<div class="ph vacia"><img src="/img/logo-chloe-estilistes.webp" alt=""></div>')
    return (f'<article class="prod{" est" if estatica else ""}" id="{e(p["id"])}" data-id="{e(p["id"])}" tabindex="0">{foto}<div class="in">'
            + (f'<span class="mk">{e(p["marca"])}</span>' if p.get('marca') else '')
            + f'<h3><a href="/productos/{p["slug"]}/">{e(p["nombre"])}</a></h3>'
            + (f'<p class="ds">{e(p["ds"])}</p>' if p['ds'] and not p['regalo'] else '')
            + f'<span class="pr">{p["eur"]}</span>'
            + ('' if p['ok'] else '<span class="ag">Agotado ahora · pregúntanos</span>')
            + f'<a class="pill wa" href="{e(p["wa"])}" target="_blank" rel="noopener">{p["boton"]}</a></div></article>')


def entre(texto, marca, nuevo):
    a, b = f'<!--{marca}-->', f'<!--/{marca}-->'
    if a not in texto or b not in texto:
        sys.exit(f'Falta el marcador {marca}')
    i, j = texto.index(a) + len(a), texto.index(b)
    return texto[:i] + nuevo + texto[j:]


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>'


def estilos():
    h = open(os.path.join(RAIZ, 'productos/index.html'), encoding='utf-8').read()
    cab = h[:h.index('</head>')]
    return ''.join(re.findall(r'<style>.*?</style>', cab, re.S))


EXTRA_CSS = '''<style>
  .pp .foto{margin-top:18px; border-radius:16px; overflow:hidden; background:#f4f1ec; aspect-ratio:1; display:flex; align-items:center; justify-content:center}
  .pp .foto img{width:100%; height:100%; object-fit:contain}
  .pp .foto.vacia{background:radial-gradient(circle at 50% 50%, #0b0a09 0 2px, transparent 3px) 0 0/22px 22px, #161412}
  .pp .foto.vacia img{width:58%; height:auto}
  .pp .mk{display:block; margin-top:18px; font-size:12px; letter-spacing:.2em; text-transform:uppercase; color:var(--gold)}
  .pp h1{margin-top:4px}
  .pp .pr{font-size:26px; font-weight:600; margin-top:10px}
  .pp .ag{font-size:13px; color:#e3a08f; margin-top:2px}
  .pp .ds{margin-top:14px; font-size:16px; line-height:1.6; color:var(--silver); white-space:pre-line}
  .pp .rec{margin-top:12px; font-size:14px; color:var(--muted); line-height:1.5}
  .pp .acc{display:grid; gap:8px; margin-top:18px}
  .pp .acc a{display:flex; align-items:center; justify-content:center; gap:8px; padding:15px; border-radius:14px; font-size:16px; font-weight:600; text-decoration:none}
  .pp .acc .res{background:var(--wa); color:#08190f}
  .pp .acc .otr{border:1px solid var(--line); font-weight:400}
  .pp .intro a{color:var(--gold)}
  .prod h3 a{text-decoration:none}
  .prod.est{opacity:1; transform:none}
  @media (min-width:700px){.pp .dos{display:grid; grid-template-columns:1fr 1fr; gap:24px; align-items:start}}
</style>'''


def cabecera(titulo, desc, url, imagen, css, lds):
    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titulo)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#121110">
<link rel="canonical" href="{url}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="Chloe Estilistes">
<meta property="og:image" content="{e(imagen)}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<link rel="preload" href="/fonts/josefin-sans.woff2" as="font" type="font/woff2" crossorigin>
{css}{EXTRA_CSS}
{"".join(ld(x) for x in lds)}
</head>
<body>
<header class="top">
  <a class="home" href="/" aria-label="Chloe Estilistes"><img src="/img/logo-chloe-estilistes.webp" alt="Chloe Estilistes" width="900" height="526"></a>
</header>
'''


PIE = '''  <footer>© 2026 Chloe Estilistes · Rambla de Prim, 45 bis · 08019 Barcelona<br><a href="/#privacidad">Aviso legal y privacidad</a></footer>
</main>
<div class="sticky"><a href="https://wa.me/34610273609?text=%C2%A1Hola%21%20Quiero%20preguntar%20por%20un%20producto." target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .1-3.3-.8-2.8-1.1-4.5-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.6-.1l1.9.9c.3.1.4.2.5.3.1.2.1.7-.1 1.2z"/></svg>Pregúntanos por WhatsApp</a></div>
</body>
</html>
'''


def migas(*items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]}


def pagina_producto(p, ps, css):
    marca = p.get('marca') or ''
    if p['regalo']:
        titulo = f"{p['nombre']} para peluquería en Barcelona | Chloe Estilistes"
        desc = f"{p['nombre']} de Chloe Estilistes, peluquería en Rambla de Prim 45 bis (Sant Martí, junto a Diagonal Mar). Para cualquier servicio. Pídela por WhatsApp y recógela en el salón."
    else:
        nom = p['nombre'] if p['nombre'].lower().startswith(marca.lower()) else f"{marca} {p['nombre']}".strip()
        titulo = f"{nom} · {p['eur']} en Barcelona | Chloe Estilistes"
        desc = f"Compra {nom} por {p['eur']} en Chloe Estilistes, peluquería en Rambla de Prim 45 bis (Sant Martí, junto a Diagonal Mar, Barcelona). Resérvalo por WhatsApp y recógelo en el salón."
    if len(desc) > 165: desc = desc[:162].rsplit(' ', 1)[0] + '…'
    img = p.get('foto') or WEB + '/img/og-chloe-estilistes.jpg?v=2'
    prod = dict(ld_producto(p)); prod['@context'] = 'https://schema.org'
    lds = [prod, migas(('Chloe Estilistes', WEB + '/'), ('Productos', WEB + '/productos/'), (p['nombre'], p['url']))]
    foto = (f'<div class="foto"><img src="{e(p["foto"])}" alt="{e(p["nombre"])}" width="600" height="600"></div>' if p.get('foto')
            else '<div class="foto vacia"><img src="/img/logo-chloe-estilistes.webp" alt=""></div>')
    otros = [q for q in ps if q is not p and q['regalo'] == p['regalo'] and (q.get('marca') == marca)][:4]
    if len(otros) < 2: otros = [q for q in ps if q is not p][:4]
    enlace_marca = ' · <a href="/salerm/">Todos los productos Salerm</a>' if marca == 'Salerm' else ''
    cuerpo = f'''<main class="wrap page pp">
  <p class="crumbs"><a href="/">Inicio</a> › <a href="/productos/">Productos</a> › {e(p["nombre"])}</p>
  <div class="dos">
  {foto}
  <div>
  {f'<span class="mk">{e(marca)}</span>' if marca else ''}
  <h1>{e(p["nombre"])}</h1>
  <div class="pr">{p["eur"]}</div>
  {'' if p['ok'] else '<div class="ag">Agotado ahora · pregúntanos y te avisamos cuando llegue</div>'}
  {f'<p class="ds">{e(p["ds"])}</p>' if p['ds'] else ''}
  <p class="rec">Precio con IVA. Lo reservas por WhatsApp y lo recoges en Chloe Estilistes, {DIR} (Sant Martí, junto a Diagonal Mar, Barcelona), en horario de apertura.</p>
  <div class="acc">
    <a class="res" href="{e(p["wa"])}" target="_blank" rel="noopener">{'Pedir tarjeta por WhatsApp' if p['regalo'] else ('Reservar por WhatsApp' if p['ok'] else 'Avisadme cuando llegue')}</a>
    <a class="otr" href="/productos/">Ver todos los productos</a>
  </div>
  </div>
  </div>
  <section>
    <h2>También te puede interesar</h2>
    <div class="prods">{"".join(tarjeta(q) for q in otros)}</div>
    <p class="note"><a href="/productos/">Todos los productos</a>{enlace_marca} · <a href="/">El salón</a></p>
  </section>
'''
    return cabecera(titulo, desc, p['url'], img, css, lds) + cuerpo + PIE


def pagina_salerm(ps, css):
    sal = [p for p in ps if p.get('marca') == 'Salerm']
    url = WEB + '/salerm/'
    titulo = 'Productos Salerm en Barcelona · Sant Martí, junto a Diagonal Mar | Chloe Estilistes'
    desc = 'Compra Salerm 21, Biokera y más productos Salerm en Chloe Estilistes, peluquería en Rambla de Prim 45 bis (Sant Martí, junto a Diagonal Mar). Resérvalos por WhatsApp y recógelos en el salón.'
    faqs = [
        ('¿Dónde comprar Salerm 21 en Barcelona?', f'En Chloe Estilistes, {DIR}, en Sant Martí, a pocos minutos del centro comercial Diagonal Mar. Lo reservas por WhatsApp y lo recoges en el salón.'),
        ('¿Los productos Salerm son originales?', 'Sí. Son los mismos productos profesionales Salerm que usamos en el salón, comprados directamente a Salerm.'),
        ('¿Qué precio tienen?', 'Los vendemos al precio de la web oficial de Salerm, con IVA incluido. Tienes el precio de cada uno en esta página.'),
        ('¿Me aconsejáis cuál me va mejor?', 'Sí. Escríbenos por WhatsApp o pregúntanos en el salón y te recomendamos el producto según tu tipo de pelo, tu color o tus mechas.'),
        ('¿Hacéis envíos?', 'De momento no: los productos se recogen en el salón en horario de apertura.'),
    ]
    lista = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Productos Salerm · Chloe Estilistes', 'url': url,
             'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': p['url'], 'name': p['nombre']} for i, p in enumerate(sal)]}
    faq = {'@context': 'https://schema.org', '@type': 'FAQPage', 'inLanguage': 'es', 'url': url, 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}
    lds = [lista, faq, migas(('Chloe Estilistes', WEB + '/'), ('Productos', WEB + '/productos/'), ('Salerm', url))]
    faqhtml = ''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in faqs)
    cuerpo = f'''<main class="wrap page pp">
  <p class="crumbs"><a href="/">Inicio</a> › <a href="/productos/">Productos</a> › Salerm</p>
  <h1>Productos Salerm en Barcelona</h1>
  <p class="sub">{DIR} · Sant Martí, junto a Diagonal Mar</p>
  <div class="intro">
    <p>En Chloe Estilistes trabajamos con Salerm en el salón, y tienes sus productos para casa: el clásico Salerm 21, la línea Biokera, champús, mascarillas, ampollas, lacas y planchas.</p>
    <p>Los vendemos al precio de la web oficial de Salerm. Resérvalos por WhatsApp y los recoges en el salón; si no sabes cuál te va mejor, te aconsejamos según tu pelo.</p>
  </div>
  <div class="prods">{"".join(tarjeta(p) for p in sal)}</div>
  <section class="faq">
    <h2>Preguntas frecuentes</h2>
    <div class="card">{faqhtml}</div>
  </section>
  <section>
    <h2>Dónde estamos</h2>
    <div class="card"><p>Chloe Estilistes · {DIR}, 08019 Barcelona (Sant Martí, junto a Diagonal Mar).</p>
    <p class="note"><a href="https://maps.google.com/maps?cid=11681562341302808072" target="_blank" rel="noopener">Cómo llegar en Google Maps ›</a> · <a href="/productos/">Ver todos los productos</a> · <a href="/">El salón</a></p></div>
  </section>
'''
    return cabecera(titulo, desc, url, WEB + '/img/og-chloe-estilistes.jpg?v=2', css, lds) + cuerpo + PIE


def escribir(ruta, texto):
    ruta = os.path.join(RAIZ, ruta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    viejo = open(ruta, encoding='utf-8').read() if os.path.exists(ruta) else None
    if viejo != texto:
        open(ruta, 'w', encoding='utf-8').write(texto)
        return True
    return False


def sitemap(ps, cambiadas):
    ruta = os.path.join(RAIZ, 'sitemap.xml')
    sm = open(ruta, encoding='utf-8').read()
    # quita las entradas de productos y salerm generadas antes y las vuelve a poner
    sm = re.sub(r'\s*<url><loc>https://chloeestilistes\.com/(productos/[^<]+|salerm/)</loc>.*?</url>', '', sm)
    viejas = dict(re.findall(r'<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>', open(ruta, encoding='utf-8').read()))
    filas = []
    for u in [WEB + '/salerm/'] + [p['url'] for p in ps]:
        lm = HOY if (u in cambiadas or u not in viejas) else viejas[u]
        filas.append(f'  <url><loc>{u}</loc><lastmod>{lm}</lastmod></url>')
    if WEB + '/productos/' in cambiadas:
        sm = re.sub(r'(<loc>https://chloeestilistes\.com/productos/</loc><lastmod>)[^<]+', r'\g<1>' + HOY, sm)
    sm = sm.replace('</urlset>', '\n'.join(filas) + '\n</urlset>')
    return escribir('sitemap.xml', sm)


def main():
    ps = leer()
    css = estilos()
    cambiadas = set()
    # páginas de productos (y borra las de productos que ya no están)
    vivos = {p['slug'] for p in ps}
    base = os.path.join(RAIZ, 'productos')
    for d in os.listdir(base):
        if os.path.isdir(os.path.join(base, d)) and d not in vivos and os.path.exists(os.path.join(base, d, '.generada')):
            for f in os.listdir(os.path.join(base, d)): os.remove(os.path.join(base, d, f))
            os.rmdir(os.path.join(base, d))
    for p in ps:
        if escribir(f"productos/{p['slug']}/index.html", pagina_producto(p, ps, css)): cambiadas.add(p['url'])
        escribir(f"productos/{p['slug']}/.generada", 'Página generada por tools/productos.py\n')
    if escribir('salerm/index.html', pagina_salerm(ps, css)): cambiadas.add(WEB + '/salerm/')
    # listado de productos
    h = open(os.path.join(RAIZ, 'productos/index.html'), encoding='utf-8').read()
    lista = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Productos de peluquería · Chloe Estilistes',
             'url': WEB + '/productos/', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': p['url'], 'name': p['nombre']} for i, p in enumerate(ps)]}
    h = entre(h, 'PRODS', ''.join(tarjeta(p) for p in ps))
    h = entre(h, 'LD-PRODUCTOS', ld(lista) + ld(migas(('Chloe Estilistes', WEB + '/'), ('Productos', WEB + '/productos/'))))
    if escribir('productos/index.html', h): cambiadas.add(WEB + '/productos/')
    # carrusel del inicio
    h = open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()
    rail = [p for p in ps if p.get('foto') and not p['regalo']][:8]
    h = entre(h, 'RAIL', ''.join(
        f'<figure><a href="/productos/{p["slug"]}/"><div class="pi"><img src="{e(p["foto"])}" alt="{e(p["nombre"])}" loading="lazy"></div><figcaption>{e(p["nombre"])}<b>{p["eur"]}</b></figcaption></a></figure>'
        for p in rail))
    escribir('index.html', h)
    sitemap(ps, cambiadas)
    print(f'{len(ps)} productos · páginas cambiadas: {len(cambiadas)}')


if __name__ == '__main__':
    import urllib.parse
    main()
