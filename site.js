(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var root = document.documentElement;

  // Menu sur téléphone
  var btn = document.querySelector('.menu-btn');
  var nav = document.getElementById('nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.textContent = open ? 'Fermer' : 'Menu';
    });
  }

  // Ouverture en rideaux : une seule fois par visite
  var intro = document.querySelector('.intro');
  if (intro) {
    var seen = false;
    try { seen = sessionStorage.getItem('lm-intro') === '1'; sessionStorage.setItem('lm-intro', '1'); } catch (e) {}
    if (seen || reduce) { intro.remove(); root.classList.remove('has-intro'); }
    else {
      var name = intro.querySelector('.name');
      if (name) {
        name.innerHTML = name.textContent.split('').map(function (c, i) {
          return c === ' ' ? ' ' : '<span class="l" style="--i:' + i + '">' + c + '</span>';
        }).join('');
      }
      setTimeout(function () { if (intro.parentNode) intro.remove(); }, 3300);
    }
  }

  // Titres : les mots montent un par un
  document.querySelectorAll('[data-words]').forEach(function (el) {
    var i = 0;
    el.querySelectorAll('br').forEach(function (b) { b.replaceWith(' \n '); });
    var parts = el.textContent.split(/(\s+)/);
    el.innerHTML = parts.map(function (p) {
      if (p.indexOf('\n') > -1) return '<br>';
      if (!p.trim()) return ' ';
      return '<span class="w"><span style="--i:' + (i++) + '">' + p + '</span></span>';
    }).join('');
  });

  // Phrases qui s'allument : on découpe en mots
  var lights = [];
  document.querySelectorAll('[data-light]').forEach(function (el) {
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (n) {
      var frag = document.createDocumentFragment();
      n.textContent.split(/(\s+)/).forEach(function (p) {
        if (!p) return;
        if (!p.trim()) { frag.appendChild(document.createTextNode(p)); return; }
        var s = document.createElement('span'); s.className = 'lw'; s.textContent = p; frag.appendChild(s);
      });
      n.parentNode.replaceChild(frag, n);
    });
    lights.push({ el: el, words: el.querySelectorAll('.lw') });
  });

  // Vidéos : lecture muette, en léger ralenti quand demandé
  document.querySelectorAll('video').forEach(function (v) {
    v.muted = true;
    if (v.dataset.slow) v.playbackRate = parseFloat(v.dataset.slow);
    v.addEventListener('loadedmetadata', function () { if (v.dataset.slow) v.playbackRate = parseFloat(v.dataset.slow); });
    if (v.autoplay) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
  });

  // Vidéos hors de l'écran : en pause, pour garder un défilement fluide
  if ('IntersectionObserver' in window) {
    var vio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
        else v.pause();
      });
    }, { rootMargin: '200px 0px' });
    document.querySelectorAll('video[autoplay]').forEach(function (v) { vio.observe(v); });
  }

  // Animations liées au défilement
  var par = document.querySelectorAll('[data-parallax]');
  var grows = document.querySelectorAll('.grow');
  var bars = document.querySelectorAll('[data-progress]');
  var dock = document.querySelector('.dock');
  var ticking = false;
  function frame() {
    ticking = false;
    var vh = window.innerHeight;
    if (!reduce) {
      par.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.bottom < 0 || r.top > vh) return;
        var k = parseFloat(el.dataset.parallax) || 0.2;
        var y = Math.max(0, -r.top) * k;
        el.style.transform = 'translate3d(0,' + y + 'px,0) scale(' + (1 + Math.min(0.12, Math.max(0, -r.top) / vh * 0.12)) + ')';
      });
      grows.forEach(function (g) {
        var r = g.getBoundingClientRect();
        if (r.bottom < 0 || r.top > vh) return;
        var total = g.offsetHeight - vh;
        var p = Math.min(1, Math.max(0, -r.top / (total || 1)));
        g.style.setProperty('--p', p.toFixed(3));
        g.style.setProperty('--q', (1 - p).toFixed(3));
      });
    }
    bars.forEach(function (b) {
      var host = b.closest('section') || b;
      var r = host.getBoundingClientRect();
      var p = Math.min(1, Math.max(0, (vh - r.top) / (r.height + vh * 0.4)));
      b.style.setProperty('--p', p.toFixed(3));
    });
    lights.forEach(function (L) {
      var r = L.el.getBoundingClientRect();
      if (r.bottom < -vh || r.top > vh * 2) return;
      var p = (vh * 0.9 - r.top) / (r.height + vh * 0.35);
      if (reduce) p = 1;
      var n = Math.round(Math.min(1, Math.max(0, p)) * L.words.length);
      if (n === L.n) return;
      var from = Math.min(n, L.n || 0), to = Math.max(n, L.n || 0);
      for (var i = from; i < to; i++) L.words[i].classList.toggle('on', i < n);
      L.n = n;
    });
    if (dock) dock.classList.toggle('show', window.scrollY > vh * 0.5);
  }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  frame();

  // Chiffres qui comptent jusqu'à leur valeur
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        var el = e.target, to = parseFloat(el.dataset.count), suf = el.dataset.suffix || '', pre = el.dataset.prefix || '';
        var t0 = null, dur = 1400;
        function step(t) {
          if (!t0) t0 = t;
          var k = Math.min(1, (t - t0) / dur);
          var eased = 1 - Math.pow(1 - k, 3);
          el.innerHTML = pre + Math.round(to * eased) + suf;
          if (k < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.6 });
    document.querySelectorAll('[data-count]').forEach(function (el) { io.observe(el); });
  }

  // Cartes qui s'inclinent sous le doigt ou la souris
  if (!reduce) {
    document.querySelectorAll('[data-tilt]').forEach(function (el) {
      el.addEventListener('pointermove', function (ev) {
        var r = el.getBoundingClientRect();
        var x = (ev.clientX - r.left) / r.width - 0.5, y = (ev.clientY - r.top) / r.height - 0.5;
        el.style.setProperty('--ry', (x * 8).toFixed(2) + 'deg');
        el.style.setProperty('--rx', (-y * 8).toFixed(2) + 'deg');
        el.style.setProperty('--ty', '-6px');
      });
      el.addEventListener('pointerleave', function () {
        el.style.setProperty('--ry', '0deg'); el.style.setProperty('--rx', '0deg'); el.style.setProperty('--ty', '0px');
      });
    });
    // Boutons légèrement aimantés
    document.querySelectorAll('.btn').forEach(function (b) {
      b.addEventListener('pointermove', function (ev) {
        if (ev.pointerType !== 'mouse') return;
        var r = b.getBoundingClientRect();
        b.style.transform = 'translate(' + ((ev.clientX - r.left - r.width / 2) * 0.15).toFixed(1) + 'px,' + ((ev.clientY - r.top - r.height / 2) * 0.25).toFixed(1) + 'px)';
      });
      b.addEventListener('pointerleave', function () { b.style.transform = ''; });
    });
  }

  // Liens internes (#…) : on vise la vraie position de la section, sans le décalage de son animation d'entrée
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (ev) {
      var id = a.getAttribute('href').slice(1);
      var t = id && document.getElementById(id);
      if (!t) return;
      ev.preventDefault();
      t.style.animation = 'none';
      var y = t.getBoundingClientRect().top + window.scrollY;
      t.style.animation = '';
      var m = parseFloat(getComputedStyle(t).scrollMarginTop) || 0;
      window.scrollTo({ top: Math.max(0, y - m), behavior: reduce ? 'auto' : 'smooth' });
      try { history.replaceState(null, '', '#' + id); } catch (e) {}
    });
  });

  // Bulle « Contact » : se ferme quand on touche ailleurs
  document.addEventListener('click', function (ev) {
    document.querySelectorAll('details.reach[open]').forEach(function (d) { if (!d.contains(ev.target)) d.removeAttribute('open'); });
  });

  // Formulaire unique : les questions s'adaptent au type de demande
  var form = document.querySelector('form[data-demo], form[name="contact"]');
  if (form) {
    var radios = form.querySelectorAll('input[name="type"]');
    function show(type) {
      form.querySelectorAll('.fields[data-for]').forEach(function (fs) {
        var on = fs.dataset.for === type;
        fs.hidden = !on; fs.disabled = !on;
      });
    }
    radios.forEach(function (r) { r.addEventListener('change', function () { show(r.value); }); });
    var wanted = (location.hash || '').replace('#', '');
    var pick = form.querySelector('input[name="type"][value="' + wanted + '"]') || radios[0];
    if (pick) { pick.checked = true; show(pick.value); }
    // Envoi vers Formspree sans quitter le site, puis page « merci »
    if (form.hasAttribute('data-formspree') && window.fetch && window.FormData) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var btn = form.querySelector('button[type="submit"]');
        var err = form.querySelector('.form-error');
        if (err) err.hidden = true;
        if (btn) { btn.disabled = true; btn.dataset.label = btn.innerHTML; btn.textContent = 'Envoi…'; }
        fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' } })
          .then(function (r) { if (!r.ok) throw new Error(r.status); location.href = 'merci.html'; })
          .catch(function () {
            if (btn) { btn.disabled = false; btn.innerHTML = btn.dataset.label; }
            if (err) { err.hidden = false; err.focus(); }
          });
      });
    }
    form.addEventListener('submit', function (e) {
      if (!form.hasAttribute('data-demo')) return;
      e.preventDefault();
      var note = form.querySelector('.form-note');
      if (note) { note.hidden = false; note.focus(); }
    });
  }
})();
