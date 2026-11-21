/* Cesta de Chloe Estilistes: pedir varios productos en un solo mensaje de WhatsApp.
   La cesta se guarda solo en el navegador del cliente (localStorage). No se envía nada
   a ningún sitio hasta que el cliente manda el WhatsApp.
   Botones que añaden: cualquier elemento con class="cesta-add" y data-id, data-nombre,
   data-precio (número con punto) y data-url. Funciona también con tarjetas creadas por JS.
   Sin este script la web sigue funcionando: los enlaces .cesta-add son enlaces normales de
   WhatsApp («Comprar») y los elementos .cesta-solo quedan ocultos. Al cargar, el script
   marca <html class="cesta-on">, convierte esos enlaces en «Añadir a la cesta» y los intercepta. */
(function () {
  var WA = '34610273609', KEY = 'chloe-cesta', MAX = 20;

  function leer() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || '[]');
      return Array.isArray(v) ? v.filter(function (x) {
        return x && typeof x.id === 'string' && typeof x.nombre === 'string' && isFinite(x.precio) && x.n > 0;
      }) : [];
    } catch (e) { return []; }
  }
  var items = leer();
  function guardar() { try { localStorage.setItem(KEY, JSON.stringify(items)); } catch (e) {} pintar(); }
  function buscar(id) { for (var i = 0; i < items.length; i++) if (items[i].id === id) return items[i]; return null; }
  function eur(n) { return (Math.round(n * 100) / 100).toFixed(2).replace('.', ',') + ' €'; }
  function total() { return items.reduce(function (s, x) { return s + x.precio * x.n; }, 0); }
  function unidades() { return items.reduce(function (s, x) { return s + x.n; }, 0); }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  // ---- estilos (usan los colores de la web) ----
  var css = document.createElement('style');
  css.textContent = [
    'button.pill{font:inherit; cursor:pointer; color:inherit}',
    '.cesta-barra{position:fixed; left:0; right:0; bottom:0; z-index:6; padding:12px 16px calc(12px + env(safe-area-inset-bottom)); background:linear-gradient(transparent, rgba(18,17,16,.94) 35%)}',
    '.cesta-barra[hidden]{display:none}',
    '.cesta-barra button{max-width:520px; width:100%; margin:0 auto; display:flex; align-items:center; gap:12px; padding:15px 18px; border-radius:14px; border:0; background:var(--wa,#25d366); color:#08190f; font:inherit; font-size:16px; font-weight:600; cursor:pointer; box-shadow:0 8px 30px rgba(37,211,102,.25); transition:transform .16s}',
    '.cesta-barra button:active{transform:scale(.97)}',
    '.cesta-barra .num{min-width:26px; height:26px; border-radius:13px; background:#08190f; color:var(--wa,#25d366); display:inline-flex; align-items:center; justify-content:center; font-size:14px; padding:0 7px}',
    '.cesta-barra .ver{margin-left:auto; font-weight:400}',
    '.cesta-barra.pulso button{animation:cestaPulso .5s}',
    '@keyframes cestaPulso{40%{transform:scale(1.04)}}',
    'body.con-cesta .sticky{display:none}',
    '.cesta{position:fixed; inset:0; z-index:30; display:flex; align-items:flex-end; justify-content:center}',
    '.cesta[hidden]{display:none}',
    '.cesta .velo{position:absolute; inset:0; background:rgba(8,7,6,.72)}',
    '.cesta .hoja{position:relative; width:100%; max-width:560px; max-height:92vh; overflow-y:auto; overscroll-behavior:contain; background:#171513; color:var(--silver,#ece9e4); border:1px solid var(--line,rgba(236,233,228,.13)); border-bottom:0; border-radius:22px 22px 0 0; padding:18px 18px calc(18px + env(safe-area-inset-bottom))}',
    '@media (min-width:700px){.cesta{align-items:center} .cesta .hoja{border-radius:22px; border-bottom:1px solid var(--line,rgba(236,233,228,.13))}}',
    '.cesta h2{font-size:13px; font-weight:600; letter-spacing:.26em; text-transform:uppercase; color:var(--gold,#c9a96a); margin:4px 40px 14px 0}',
    '.cesta .x{position:absolute; top:12px; right:12px; width:40px; height:40px; border-radius:50%; border:1px solid var(--line,rgba(236,233,228,.13)); background:transparent; color:inherit; font-size:22px; line-height:1; cursor:pointer}',
    '.cesta ul{list-style:none; margin:0; padding:0}',
    '.cesta li{display:grid; grid-template-columns:1fr auto; gap:6px 12px; padding:12px 0; border-bottom:1px solid var(--line,rgba(236,233,228,.13))}',
    '.cesta li a{text-decoration:none; font-size:15px; line-height:1.3}',
    '.cesta li .pu{font-size:13px; color:var(--muted,#b4ada3)}',
    '.cesta li .sub{font-weight:600; text-align:right}',
    '.cesta .cant{display:flex; align-items:center; gap:4px}',
    '.cesta .cant button{width:34px; height:34px; border-radius:10px; border:1px solid var(--line,rgba(236,233,228,.13)); background:transparent; color:inherit; font:inherit; font-size:18px; cursor:pointer}',
    '.cesta .cant span{min-width:26px; text-align:center}',
    '.cesta .quitar{justify-self:end; background:none; border:0; color:var(--muted,#b4ada3); font:inherit; font-size:13px; text-decoration:underline; cursor:pointer}',
    '.cesta .tot{display:flex; justify-content:space-between; font-size:20px; font-weight:600; margin-top:14px}',
    '.cesta .nota{margin-top:6px; font-size:13px; color:var(--muted,#b4ada3); line-height:1.5}',
    '.cesta .biz{margin-top:16px}',
    '.cesta .acc{display:grid; gap:8px; margin-top:16px}',
    '.cesta .acc a, .cesta .acc button{display:flex; align-items:center; justify-content:center; padding:15px; border-radius:14px; font:inherit; font-size:16px; font-weight:600; text-decoration:none; cursor:pointer}',
    '.cesta .acc .res{background:var(--wa,#25d366); color:#08190f; border:0}',
    '.cesta .acc .otr{background:transparent; color:inherit; border:1px solid var(--line,rgba(236,233,228,.13)); font-weight:400}',
    '.cesta .vaciar{display:block; margin:14px auto 0; background:none; border:0; color:var(--muted,#b4ada3); font:inherit; font-size:13px; text-decoration:underline; cursor:pointer}',
    '.cesta .vacia{color:var(--muted,#b4ada3); padding:20px 0; text-align:center}',
    '.cesta li .cambio{grid-column:1/-1; font-size:13px; color:var(--gold,#c9a96a)}',
    'body.con-panel{overflow:hidden}'
  ].join('\n');
  document.head.appendChild(css);

  // ---- barra inferior y panel ----
  var barra = document.createElement('div');
  barra.className = 'cesta-barra'; barra.hidden = true;
  barra.innerHTML = '<button type="button" aria-haspopup="dialog"><span class="num"></span><span class="txt"></span><span class="ver">Ver cesta ›</span></button>';
  var panel = document.createElement('div');
  panel.className = 'cesta'; panel.hidden = true;
  panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-modal', 'true'); panel.setAttribute('aria-labelledby', 'cestaTit');
  panel.innerHTML = '<div class="velo" data-cerrar-cesta></div><div class="hoja">'
    + '<button class="x" type="button" data-cerrar-cesta aria-label="Cerrar la cesta">×</button>'
    + '<h2 id="cestaTit">Tu cesta</h2><div id="cestaLista"></div>'
    + '<div id="cestaPie">'
    + '<div class="tot"><span>Total</span><span id="cestaTotal"></span></div>'
    + '<p class="nota">Precios con IVA. Antes de pagar te confirmamos precio y disponibilidad por WhatsApp. Pagas por Bizum (te enviamos la petición a tu móvil y la aceptas) o con tarjeta o en efectivo al recogerlo. Lo recoges en Rambla de Prim, 45 bis (junto a Diagonal Mar). De momento no hacemos envíos.</p>'
    + '<label class="biz" for="cestaBiz"><span>Tu móvil para Bizum <em>(opcional)</em></span>'
    + '<input id="cestaBiz" type="tel" inputmode="tel" autocomplete="tel" placeholder="600 123 456" maxlength="16">'
    + '<small id="cestaBizAyuda">Si lo dejas vacío, te enviamos la petición al número de tu WhatsApp.</small></label>'
    + '<div class="acc"><a class="res" id="cestaEnviar" target="_blank" rel="noopener">Pedir por WhatsApp</a>'
    + '<button class="otr" type="button" data-cerrar-cesta>Seguir comprando</button></div>'
    + '<button class="vaciar" type="button" id="cestaVaciar">Vaciar la cesta</button>'
    + '</div></div>';
  document.body.appendChild(barra);
  document.body.appendChild(panel);

  var lista = panel.querySelector('#cestaLista'), pie = panel.querySelector('#cestaPie'),
      enviar = panel.querySelector('#cestaEnviar'), biz = panel.querySelector('#cestaBiz'),
      bizAyuda = panel.querySelector('#cestaBizAyuda'), AYUDA = bizAyuda.textContent, origen = null;

  function movil() {
    var n = biz.value.replace(/[^0-9+]/g, '').replace(/^(\+|00)34/, '');
    return /^[67][0-9]{8}$/.test(n) ? n.replace(/(\d{3})(\d{3})(\d{3})/, '$1 $2 $3') : '';
  }
  function mensaje() {
    var l = ['¡Hola! Quiero comprar estos productos y recogerlos en el salón:'];
    items.forEach(function (x) {
      l.push('• ' + x.n + ' × ' + x.nombre + ' (' + eur(x.precio) + ')' + (x.n > 1 ? ' = ' + eur(x.precio * x.n) : ''));
    });
    l.push('Total: ' + eur(total()));
    var m = movil(); if (m) l.push('Mi móvil para Bizum: ' + m + '.');
    l.push('(Os escribo desde la web)');
    return l.join('\n');
  }
  function pintar() {
    var u = unidades();
    barra.hidden = !u;
    document.body.classList.toggle('con-cesta', !!u);
    barra.querySelector('.num').textContent = u;
    barra.querySelector('.txt').textContent = (u === 1 ? '1 producto' : u + ' productos') + ' · ' + eur(total());
    if (!items.length) {
      lista.innerHTML = '<p class="vacia">La cesta está vacía.</p>'; pie.hidden = true; return;
    }
    pie.hidden = false;
    lista.innerHTML = '<ul>' + items.map(function (x) {
      return '<li data-id="' + esc(x.id) + '">'
        + '<div>' + (x.url ? '<a href="' + esc(x.url) + '">' + esc(x.nombre) + '</a>' : esc(x.nombre)) + '<div class="pu">' + eur(x.precio) + ' / unidad</div></div>'
        + '<div class="sub">' + eur(x.precio * x.n) + '</div>'
        + (isFinite(x.antes) && x.antes !== x.precio ? '<p class="cambio" role="status">El precio ha cambiado desde que lo añadiste: antes ' + eur(x.antes) + ', ahora ' + eur(x.precio) + '.</p>' : '')
        + '<div class="cant"><button type="button" data-menos aria-label="Quitar una unidad de ' + esc(x.nombre) + '">−</button><span aria-live="polite">' + x.n + '</span>'
        + '<button type="button" data-mas aria-label="Añadir una unidad de ' + esc(x.nombre) + '"' + (x.n >= MAX ? ' disabled' : '') + '>+</button></div>'
        + '<button class="quitar" type="button" data-quitar>Quitar</button></li>';
    }).join('') + '</ul>';
    panel.querySelector('#cestaTotal').textContent = eur(total());
    enviar.href = 'https://wa.me/' + WA + '?text=' + encodeURIComponent(mensaje());
  }

  // Mientras la cesta está abierta, el resto de la página queda inerte (no se puede tabular ni pulsar)
  var inertes = [];
  function fondoInerte(si) {
    if (si) {
      inertes = [].filter.call(document.body.children, function (el) { return el !== panel && !el.inert && el.tagName !== 'SCRIPT'; });
      inertes.forEach(function (el) { el.inert = true; el.setAttribute('aria-hidden', 'true'); });
    } else {
      inertes.forEach(function (el) { el.inert = false; el.removeAttribute('aria-hidden'); });
      inertes = [];
    }
  }
  function enfocables() {
    return [].filter.call(panel.querySelectorAll('a[href], button:not([disabled]), input:not([disabled])'), function (el) {
      return !el.closest('[hidden]') && el.offsetParent !== null;
    });
  }
  function abrir() {
    sincronizar();
    origen = document.activeElement;
    panel.hidden = false; document.body.classList.add('con-panel');
    fondoInerte(true);
    panel.querySelector('.x').focus({ preventScroll: true });
  }
  function cerrar() {
    if (panel.hidden) return;
    panel.hidden = true; document.body.classList.remove('con-panel');
    fondoInerte(false);
    // los avisos de «el precio ha cambiado» ya se han visto
    var habia = items.some(function (x) { return 'antes' in x; });
    items.forEach(function (x) { delete x.antes; });
    if (habia) guardar();
    if (origen && origen.focus && document.contains(origen)) origen.focus({ preventScroll: true });
  }

  // Precios al día: los botones de la página que se ve llevan el precio actual de la hoja
  function actualizar(x, b) {
    var precio = parseFloat(b.getAttribute('data-precio')), nombre = b.getAttribute('data-nombre'), url = b.getAttribute('data-url');
    var cambio = false;
    if (isFinite(precio) && precio !== x.precio) { if (!('antes' in x)) x.antes = x.precio; x.precio = precio; cambio = true; }
    if (nombre && nombre !== x.nombre) { x.nombre = nombre; cambio = true; }
    if (url && url !== x.url) { x.url = url; cambio = true; }
    return cambio;
  }
  function sincronizar(raiz) {
    var cambio = false;
    [].forEach.call((raiz || document).querySelectorAll('.cesta-add[data-id]'), function (b) {
      var x = buscar(b.getAttribute('data-id'));
      if (x && actualizar(x, b)) cambio = true;
    });
    if (cambio) guardar();
  }

  function anadir(b) {
    var id = b.getAttribute('data-id'), precio = parseFloat(b.getAttribute('data-precio'));
    if (!id || !isFinite(precio)) return;
    var x = buscar(id);
    if (x) { actualizar(x, b); x.n = Math.min(x.n + 1, MAX); }
    else items.push({ id: id, nombre: b.getAttribute('data-nombre') || id, precio: precio, url: b.getAttribute('data-url') || '', n: 1 });
    guardar();
    var t = b.getAttribute('data-texto') || b.textContent;
    b.setAttribute('data-texto', t); b.textContent = 'Añadido ✓';
    clearTimeout(b._t); b._t = setTimeout(function () { b.textContent = t; }, 1600);
    barra.classList.remove('pulso'); void barra.offsetWidth; barra.classList.add('pulso');
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest && ev.target.closest('.cesta-add');
    if (b) { ev.preventDefault(); ev.stopPropagation(); anadir(b); }
  }, true);
  barra.querySelector('button').addEventListener('click', abrir);
  panel.addEventListener('click', function (ev) {
    if (ev.target.closest('[data-cerrar-cesta]')) { cerrar(); return; }
    var li = ev.target.closest('li[data-id]'); if (!li) return;
    var id = li.getAttribute('data-id'), x = buscar(id); if (!x) return;
    var accion = ev.target.closest('[data-mas]') ? 'data-mas' : ev.target.closest('[data-menos]') ? 'data-menos' : ev.target.closest('[data-quitar]') ? 'data-quitar' : '';
    if (!accion) return;
    var pos = items.indexOf(x);
    if (accion === 'data-mas') x.n = Math.min(x.n + 1, MAX);
    else if (accion === 'data-menos') x.n -= 1;
    else x.n = 0;
    items = items.filter(function (y) { return y.n > 0; });
    guardar();
    // El foco vuelve al mismo control de la fila; si la fila ya no está, a la siguiente; si no queda nada, a cerrar
    var fila = null;
    [].forEach.call(lista.querySelectorAll('li[data-id]'), function (l) { if (l.getAttribute('data-id') === id) fila = l; });
    var destino = fila && (fila.querySelector('[' + accion + ']:not([disabled])') || fila.querySelector('[data-menos]'));
    if (!destino) {
      var filas = lista.querySelectorAll('li[data-id]');
      var otra = filas[Math.min(pos, filas.length - 1)];
      destino = otra ? otra.querySelector('[data-quitar]') : panel.querySelector('.x');
    }
    if (destino) destino.focus({ preventScroll: false });
  });
  // El tabulador da la vuelta dentro de la cesta (para navegadores sin «inert»)
  panel.addEventListener('keydown', function (ev) {
    if (ev.key !== 'Tab') return;
    var f = enfocables(); if (!f.length) return;
    var primero = f[0], ultimo = f[f.length - 1];
    if (ev.shiftKey && document.activeElement === primero) { ev.preventDefault(); ultimo.focus(); }
    else if (!ev.shiftKey && document.activeElement === ultimo) { ev.preventDefault(); primero.focus(); }
  });
  panel.querySelector('#cestaVaciar').addEventListener('click', function () { items = []; guardar(); cerrar(); });
  biz.addEventListener('input', function () {
    bizAyuda.textContent = biz.value && !movil() ? 'Escribe un móvil español de 9 cifras (empieza por 6 o 7).' : AYUDA;
    if (items.length) enviar.href = 'https://wa.me/' + WA + '?text=' + encodeURIComponent(mensaje());
  });
  // Esc cierra la cesta antes que cualquier otra ventana de la página
  window.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && !panel.hidden) { ev.stopPropagation(); cerrar(); }
  }, true);
  // Si la cesta cambia en otra pestaña, se actualiza aquí
  window.addEventListener('storage', function (ev) { if (ev.key === KEY) { items = leer(); pintar(); } });

  // Los enlaces de compra por WhatsApp (.cesta-add) pasan a ser «Añadir a la cesta» solo ahora que la cesta funciona
  function etiquetar(raiz) {
    [].forEach.call((raiz || document).querySelectorAll('a.cesta-add:not([data-cesta-lista])'), function (a) {
      a.setAttribute('data-cesta-lista', '');
      a.setAttribute('role', 'button');
      a.textContent = 'Añadir a la cesta';
    });
  }
  document.documentElement.classList.add('cesta-on');
  etiquetar();
  sincronizar();
  // El catálogo crea sus tarjetas más tarde con JavaScript: se etiquetan y se comparan precios al aparecer
  if ('MutationObserver' in window) {
    new MutationObserver(function (cambios) {
      var hay = cambios.some(function (c) { return c.addedNodes.length; });
      if (hay) { etiquetar(); sincronizar(); }
    }).observe(document.body, { childList: true, subtree: true });
  }

  pintar();
})();
