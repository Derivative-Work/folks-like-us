// Folks Like Us O layers. window.renderFrame(t) draws one frame; every frame is a pure function of t, so frame
// ranges can render in any order (scripts/o_render.mjs). See folks.html for the scenes and query parameters.
const O = window.O;
const Q = new URLSearchParams(location.search);
const SCENE = Q.get('scene') || 'screen';
const FPS = O.fps;
const S = O.screen;
const stage = document.getElementById('stage');

// ---------------------------------------------------------------- helpers

function rng(seed) {  // mulberry32
  return () => {
    seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function el(tag, cls, parent, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  (parent || stage).appendChild(e);
  return e;
}
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const ease = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');

// The homography taking src[i] to dst[i] (four points each): [h0..h7], with x' = (h0 x + h1 y + h2) / (h6 x + h7 y + 1).
function homography(src, dst) {
  const A = [];
  for (let i = 0; i < 4; i++) {
    const [x, y] = src[i], [u, v] = dst[i];
    A.push([x, y, 1, 0, 0, 0, -x * u, -y * u, u]);
    A.push([0, 0, 0, x, y, 1, -x * v, -y * v, v]);
  }
  for (let c = 0; c < 8; c++) {  // Gaussian elimination with partial pivoting
    let p = c;
    for (let r = c + 1; r < 8; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    [A[c], A[p]] = [A[p], A[c]];
    for (let r = 0; r < 8; r++) {
      if (r === c) continue;
      const f = A[r][c] / A[c][c];
      for (let k = c; k < 9; k++) A[r][k] -= f * A[c][k];
    }
  }
  return A.map((row, i) => row[8] / row[i]);
}
function pin(node, bw, bh, quad) {
  const h = homography([[0, 0], [bw, 0], [bw, bh], [0, bh]], quad);
  node.style.transform = `matrix3d(${h[0]},${h[3]},0,${h[6]},${h[1]},${h[4]},0,${h[7]},0,0,1,0,${h[2]},${h[5]},0,1)`;
}
function setStage(w, h) {
  stage.style.width = `${w}px`;
  stage.style.height = `${h}px`;
  const rw = Number(Q.get('w') || w), rh = Number(Q.get('h') || h);
  stage.style.transform = `scale(${rw / w}, ${rh / h})`;
}

// ---------------------------------------------------------------- surfaces (scene=surface)

// Text overrides for a shot that reuses another shot's take and tracks (?as=).
const AS = { S25: { chair_tag: 'ALSO TBD' }, S24: {} };

function lines(text) { return text.split('|'); }
function fit(box, ls, k, max) {  // a font size that fits the lines in the box (k: average glyph width / em)
  const n = Math.max(...ls.map((l) => l.length));
  return Math.min(max || 999, box[1] / (ls.length * 1.12), box[0] / (n * k));
}
const STYLES = {
  mug: { box: [300, 300], html(t) {
    if (t === "World's Best Grandpa") return `<div style="font-size:54px">World's</div><div class="big" style="font-size:54px">BEST</div><div style="font-size:54px">Grandpa</div>`;
    if (t.startsWith('☐')) return `<div style="font-size:66px"><span class="box"></span>Not a</div><div style="font-size:66px">Robot</div>`;
    const ls = lines(t.replace(' ', '|'));
    return ls.map((l) => `<div style="font-size:${fit([280, 280], ls, 0.5, 96)}px">${esc(l)}</div>`).join('');
  } },
  mug_small: { box: [200, 260], html(t) {
    const ls = lines(t);
    return ls.map((l) => `<div style="font-size:${fit([190, 250], ls, 0.5)}px">${esc(l)}</div>`).join('');
  } },
  sign: { box: [600, 200], html: (t) => `<div style="font-size:${fit([580, 190], [t], 0.5)}px">${esc(t)}</div>` },
  marquee: { box: [400, 330], html(t) {
    const ls = lines(t);
    const fs = fit([380, 300], ls, 0.62, 60);
    return ls.map((l) => `<span style="font-size:${fs}px">${esc(l)}</span>`).join('');
  } },
  yard: { box: [300, 300], html(t) {
    const ls = lines(t);
    return `<div class="a" style="font-size:88px">${ls[0]}</div><div class="rule"></div><div class="b" style="font-size:64px">${ls[1]}</div>`
      + (ls[2] ? `<div class="c" style="font-size:64px">${ls[2]}</div>` : '');
  } },
  recipe: { box: [810, 620], html(t) {
    const ls = lines(t);
    return `<div class="t">${esc(ls[0])}</div>` + ls.slice(1).map((l) => `<div class="i">${esc(l)}</div>`).join('');
  } },
  tag: { box: [300, 210], html: (t) => `<div style="font-size:${fit([280, 190], [t], 0.42, 140)}px">${esc(t)}</div>` },
  sky: { box: [800, 260], html: () => `<div style="font-size:200px"><span class="A">A</span> <span class="I">I</span></div>` },
  gauge: { box: [200, 600], html: () => ['FULL', '3/4', '1/2', '1/4', 'EMPTY'].map((l, i) =>
    `<div class="tick">${l}${i === 4 ? '<span class="arrow">&#9664;</span>' : ''}</div>`).join('') },
  bill: { box: [560, 540], html: () => `<div class="hd">HOMETOWN POWER &amp; LIGHT</div>
    <div class="sub">Statement of account &middot; Residential service</div>
    <div class="row"><span>Previous balance</span><span>$0.00</span></div>
    <div class="row"><span>Energy charge</span><span class="e"></span></div>
    <div class="row"><span>Capacity adjustment</span><span class="c"></span></div>
    <div class="row"><span>Grid expansion rider</span><span class="g"></span></div>
    <div class="due">AMOUNT DUE</div><div class="amt"></div>` },
};
const money = (v) => '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

let SURF = null;
function buildSurfaces(shot) {
  const sh = O.surfaces[shot];
  setStage(sh.size[0], sh.size[1]);
  const over = AS[Q.get('as')] || {};
  SURF = sh.items.filter((it) => it.style !== 'tv').map((it) => {
    const st = STYLES[it.style];
    const node = el('div', `pin ${it.style}`);
    node.style.width = `${st.box[0]}px`;
    node.style.height = `${st.box[1]}px`;
    node.style.filter = `blur(${it.blur * 1.5}px)`;
    node.innerHTML = st.html(over[it.name] || it.text);
    return { it, st, node };
  });
}
function renderSurfaces(t) {
  const f = Math.round(t * FPS);
  for (const { it, st, node } of SURF) {
    const q = it.quads[clamp(f, 0, it.quads.length - 1)];
    pin(node, st.box[0], st.box[1], q);
    const u = clamp(f / (it.quads.length - 1), 0, 1);
    if (it.style === 'bill') {  // ticking up like a gas pump: it speeds up as the shot goes on
      const v = S.bill.from + (S.bill.to - S.bill.from) * Math.pow(u, 1.6);
      node.querySelector('.amt').textContent = money(v);
      node.querySelector('.e').textContent = money(v * 0.41);
      node.querySelector('.c').textContent = money(v * 0.27);
      node.querySelector('.g').textContent = money(v * 0.32);
    }
    if (it.style === 'sky' && Q.get('shot') === 'S16') {  // ST2: the I smears and drifts off; the A holds
      const I = node.querySelector('.I'), A = node.querySelector('.A');
      I.style.display = 'inline-block';
      I.style.filter = `blur(${2 + 22 * ease(u)}px)`;
      I.style.transform = `translate(${70 * u}px, ${-30 * u}px) scale(${1 + 1.6 * u}, ${1 - 0.3 * u})`;
      I.style.opacity = String(1 - 0.75 * u);
      A.style.filter = `blur(${4 * u}px)`;
    }
  }
}

// ---------------------------------------------------------------- screen (scene=screen, t = song time)

const L = O.lines;
const lineAt = (start) => L.findIndex((l) => Math.abs(l.start - start) < 0.05);
const lineOf = (text) => L.findIndex((l) => l.text.startsWith(text));
const ST = Object.fromEntries(S.swaps.map((s) => [s.id, s]));
const IDX = {
  ST1: lineOf("We're building something"), ST1next: lineOf('—day.'),
  ST2: lineOf("It's apple pie!"),
  ST3: lineOf("And we'll talk about"), ST3next: lineOf('—you!'),
  ST4: L.findIndex((l, i) => l.text.startsWith("It's apple pie!") && l.start > 100),
};

// Typing timelines: [start, [op, arg, rate]...]; ops: type (string), hold (s), del (n chars). Returns the text so far.
function typed(t, start, ops, base) {
  let s = base, at = start;
  for (const [op, arg, rate] of ops) {
    if (op === 'hold') { at += arg; continue; }
    if (op === 'at') { at = Math.max(at, arg); continue; }
    const n = op === 'type' ? arg.length : arg;
    const k = clamp(Math.floor((t - at) / rate) + 1, 0, n);
    if (t < at) return s;
    s = op === 'type' ? s + arg.slice(0, k) : s.slice(0, s.length - k);
    if (k < n) return s;
    at += n * rate;
  }
  return s;
}
function wordsHtml(words, t, opts = {}) {
  return words.map((w) => {
    let cls = 'w' + (t < w.start ? ' dim' : '');
    let style = '';
    if (opts.size && /^(artificial|intelligence)/.test(w.w)) style = `font-size:${opts.size}em;`;
    return `<span class="${cls}" style="${style}">${esc(w.w)}</span>`;
  }).join(' ');
}
const cursor = (t, on = true) => (on && Math.floor(t * 4) % 2 === 0 ? '<span class="cursor"></span>' : '<span class="cursor" style="opacity:0"></span>');

function caption(t) {
  // The line on screen: from just before its start until the next line (or 0.8 s after its end).
  let i = -1;
  for (let k = 0; k < L.length; k++) if (t >= L[k].start - 0.15) i = k;
  if (i < 0) return '';
  const l = L[i], next = L[i + 1];
  const until = next ? Math.min(next.start - 0.15, l.end + 0.8) : l.end + 0.8;

  // ST1: "data center" typed after "data—", held half a beat, deleted, "day." typed as he sings "—day."
  const st1 = (tt) => wordsHtml(L[IDX.ST1].words.slice(0, -1), tt) + ' ' + esc(typed(tt, ST.ST1.gap[0] + 0.06,
    [['type', ' center', 0.045], ['hold', S.half_beat], ['del', 11, 0.02], ['at', ST.ST1.swerve_at], ['type', 'day.', 0.03]],
    'data')) + cursor(tt);
  if (i === IDX.ST1 && t >= ST.ST1.gap[0]) return st1(t);
  if (i === IDX.ST1next) {  // "—day." is typed into the line before; this line shows from "A brand new day."
    return t < l.words[0].end + 0.25 ? st1(t) : wordsHtml(l.words.slice(1), t);
  }

  // ST2: in the gap a new line types "It's AI", holds, deletes "AI", types "apple pie!" as he sings it.
  if (i === IDX.ST2 - 1 && t >= ST.ST2.gap[0] + 0.2) return swapLine(t, ST.ST2, L[IDX.ST2]);
  if (i === IDX.ST2 && t < L[IDX.ST2].words[1].start + 0.5) return swapLine(t, ST.ST2, l);

  // ST4: the cursor blinks, types "It's A,", hesitates, deletes it, types "apple pie!" as he sings it.
  if (i === IDX.ST4 - 1 && t >= ST.ST4.gap[0] + 0.1) return swapLine(t, ST.ST4, L[IDX.ST4]);
  if (i === IDX.ST4 && t < L[IDX.ST4].words[1].start + 0.5) return swapLine(t, ST.ST4, l);

  // ST3: "data centers" typed across "everything, everything, every single thing", deleted on "but—", "you!" typed.
  if (i === IDX.ST3) {
    const w = l.words, a = w.findIndex((x) => x.w === 'everything,'), b = w.findIndex((x) => x.w === 'but—');
    const pre = wordsHtml(w.slice(0, a), t);
    const span0 = w[a].start, span1 = w[b - 1].end;
    if (t < w[b].start) {
      const n = clamp(Math.floor(12 * (t - span0) / (span1 - span0)) + 1, 0, 12);
      return pre + ' ' + esc('data centers'.slice(0, t < span0 ? 0 : n)) + cursor(t, t >= span0);
    }
    const s = typed(t, w[b].start, [['del', 12, (w[b].end - w[b].start) / 12], ['at', L[IDX.ST3next].start],
                                     ['type', 'you!', 0.04]], 'data centers');
    return pre + ' ' + esc(s) + cursor(t);
  }
  if (i === IDX.ST3next) {
    if (t < l.words[0].end + 0.25) return wordsHtml(L[IDX.ST3].words.slice(0, L[IDX.ST3].words.findIndex((x) => x.w === 'everything,')), t) + ' you!';
    return wordsHtml(l.words.slice(1), t);
  }

  if (t > until) return '';
  // S32: each sung "artificial intelligence" a size larger than the last.
  const ai = L.slice(0, i + 1).filter((x) => /artificial intelligence/.test(x.text)).length;
  return wordsHtml(l.words, t, /artificial intelligence/.test(l.text) ? { size: S.ai_sizes[ai - 1] } : {});
}
function swapLine(t, sw, line) {
  const apple = line.words[1].start;  // "apple"
  const ops = sw.id === 'ST2'
    ? [['type', "It's AI", 0.06], ['hold', S.half_beat], ['del', 2, 0.03], ['at', apple], ['type', 'apple pie!', 0.04]]
    : [['hold', 0.4], ['type', "It's A,", 0.07], ['hold', 0.3], ['del', 2, 0.04], ['at', apple], ['type', 'apple pie!', 0.04]];
  const s = typed(t, sw.gap[0] + (sw.id === 'ST2' ? 0.25 : 0.1), ops, '');
  return esc(s) + cursor(t);
}

let SCR = null;
const PORTRAIT = Q.get('portrait') === '1';
function buildScreen() {
  setStage(PORTRAIT ? 1080 : 1920, PORTRAIT ? 1920 : 1080);
  if (PORTRAIT) stage.classList.add('portrait');
  SCR = {
    lt: el('div', '', stage), counters: el('div', '', stage), fine: el('div', '', stage), cap: el('div', '', stage),
    label: el('div', '', stage, esc(S.label)),
  };
  SCR.lt.id = 'lt'; SCR.counters.id = 'counters'; SCR.fine.id = 'fine'; SCR.cap.id = 'cap'; SCR.label.id = 'label';
  SCR.fine.textContent = S.fine_print.repeat(6);
  SCR.counters.innerHTML = '<div class="c"><div class="k">Spent</div><div class="v m"></div></div>'
    + '<div class="c"><div class="k">Ads</div><div class="v a"></div></div>'
    + '<div class="c"><div class="k">Data centers mentioned</div><div class="v">0</div></div>';
}
function inF(t, k) { const f = O.failures[k]; return t >= f.start && t < f.end; }
function renderScreen(t) {
  const f = Math.round(t * FPS);
  const r = rng(f * 7919 + 17);
  // Caption, with the F1 jitter (S29) and the F2 jitter-and-smear (S32) inside their regions only.
  SCR.cap.innerHTML = `<span class="bg">${caption(t)}</span>`;
  SCR.cap.style.transform = '';
  SCR.cap.style.filter = '';
  if (!Q.get('nojitter') && inF(t, 'F1')) {
    const env = O.vocal[clamp(f, 0, O.vocal.length - 1)];
    for (const w of SCR.cap.querySelectorAll('.w')) {
      w.style.transform = `translate(${(r() - 0.5) * 30 * env}px, ${(r() - 0.5) * 22 * env}px) rotate(${(r() - 0.5) * 6 * env}deg)`;
    }
    SCR.cap.style.textShadow = `${4 * env}px 0 rgba(255,40,40,.7), ${-4 * env}px 0 rgba(40,200,255,.7), 0 2px 4px rgba(0,0,0,.65)`;
  } else if (inF(t, 'F2')) {
    for (const w of SCR.cap.querySelectorAll('.w')) {
      w.innerHTML = [...w.textContent].map((ch) => {
        const dx = (r() - 0.5) * 10, dy = (r() - 0.5) * 8, sm = r() < 0.35 ? 18 + r() * 40 : 0;
        return `<span style="display:inline-block;transform:translate(${dx}px,${dy}px);${sm ? `text-shadow:${sm}px 0 6px rgba(255,255,255,.55),${sm / 2}px 0 3px rgba(255,255,255,.7);` : ''}">${ch === ' ' ? '&nbsp;' : esc(ch)}</span>`;
      }).join('');
    }
    SCR.cap.style.textShadow = '';
  } else {
    SCR.cap.style.textShadow = '';
  }
  // Lower thirds: slide in and out.
  const lt = S.lower_thirds.find((x) => t >= x.start - 0.01 && t < x.end);
  if (lt) {
    const u = clamp(Math.min((t - lt.start) / 0.45, (lt.end - t) / 0.35), 0, 1);
    SCR.lt.innerHTML = `<div class="bar">${esc(lt.name)}</div><div class="rule"></div>` + (lt.sub ? `<div class="sub">${esc(lt.sub)}</div>` : '');
    SCR.lt.style.opacity = String(ease(u));
    SCR.lt.style.transform = `translateX(${-60 * (1 - ease(u))}px)`;
  } else SCR.lt.innerHTML = '';
  // S20 counters.
  const c = S.counters;
  if (t >= c.start && t < c.end) {
    const u = clamp(Math.min((t - c.start) / 0.4, (c.end - t) / 0.3), 0, 1);
    const m = clamp((t - c.start) / (c.money_until - c.start), 0, 1);
    SCR.counters.style.opacity = String(u);
    SCR.counters.querySelector('.m').textContent = '$' + Math.round(c.money * ease(m)).toLocaleString('en-US');
    SCR.counters.querySelector('.a').textContent = String(Math.round(c.ads * ease(clamp(m * 1.4, 0, 1))));
  } else SCR.counters.style.opacity = '0';
  // S32 fine print, scrolling fast across the bottom.
  const s32 = O.shots.S32;
  if (t >= s32.start && t < s32.end) {
    SCR.fine.style.display = 'block';
    SCR.fine.style.transform = `translateX(${1920 - (t - s32.start) * 760}px)`;
  } else SCR.fine.style.display = 'none';
}

// ---------------------------------------------------------------- cards

let CARD = null;
// The production log's address on its own line, in monospace so it reads letter by letter.
const logLine = () => `Production log: <span class="url">${esc(S.log_url)}</span>`;
function buildCard(kind) {
  setStage(1920, 1080);
  if (kind === 'title') {
    CARD = el('div', 'card', stage, `<div class="stars"></div><div class="stripes"></div>
      <div class="name">${esc(S.title.presents)}</div><div class="presents">${esc(S.title.line2)}</div>
      <div class="sub">${esc(S.title.sub)}</div>`);
    CARD.id = 'title';
    const r = rng(42), stars = CARD.querySelector('.stars');
    for (let i = 0; i < 70; i++) {
      const s = el('div', '', stars);
      Object.assign(s.style, { position: 'absolute', left: `${r() * 1920}px`, top: `${r() * 760}px`, width: `${3 + r() * 5}px`,
        height: `${3 + r() * 5}px`, background: '#fff', borderRadius: '50%', opacity: String(0.3 + r() * 0.6) });
    }
  } else if (kind === 'labelcard') {
    setStage(1080, 1920);
    CARD = el('div', 'card', stage, `<div class="big">AI-GENERATED<br>SATIRE</div>
      <div class="small">Folks Like Us PAC is fictional. ${esc(S.credits)}<br>${logLine()}</div>`);
    CARD.id = 'labelcard';
    return;
  } else if (kind === 's34') {  // &over=1: the text alone, for E to lay over the top of the spectrogram
    CARD = el('div', Q.get('over') ? 'card over' : 'card', stage, `<p>${esc(S.s34_card)}</p>`);
    CARD.id = 's34';
  } else if (kind === 'vote') {  // the human's closing note, after the label; it carries no label of its own
    if (PORTRAIT) { setStage(1080, 1920); stage.classList.add('portrait'); }
    CARD = el('div', 'card', stage, `<div class="from">${esc(S.vote.from)}</div><div class="when">${esc(S.vote.when)}</div>
      <div class="ask">${esc(S.vote.ask)}</div><div class="link"><span class="url">${esc(S.vote.url)}</span></div>`);
    CARD.id = 'vote';
    return;
  } else {
    CARD = el('div', 'card', stage, `<div class="badge">${esc(S.label)}</div><ul>${S.fact_card.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>
      <div class="credits">${esc(S.credits)}<br>${logLine()}</div>`);
    CARD.id = 'fact';
  }
  if (kind !== 'fact') { const lab = el('div', '', stage, esc(S.label)); lab.id = 'label'; }
}
function renderCard(t) {
  if (CARD.id === 'title') {
    CARD.style.transform = `scale(${1 + 0.012 * t})`;
    CARD.querySelector('.stripes').style.transform = `rotate(-4deg) translateX(${-20 * t}px)`;
  }
  CARD.style.opacity = String(clamp(t / 0.3, 0, 1));
}

// ---------------------------------------------------------------- chat (scene=chat, S35: t from the shot's start)

// Just enough Markdown for the planning chat: paragraphs, lists, bold, italics, links, and the tool-call placeholders.
function md(text, highlight) {
  const inline = (x) => esc(x).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\*(.+?)\*/g, '<i>$1</i>')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '<u>$1</u>')
    .replace(esc(highlight), `<mark>${esc(highlight)}</mark>`);
  return text.split(/\n\s*\n/).map((b) => {
    const lines = b.split('\n');
    if (/^> \*\[.*\]\*$/.test(b.trim())) return `<div class="tool">${esc(b.trim().slice(4, -2))}</div>`;
    if (lines.every((l) => /^- /.test(l))) return `<ul>${lines.map((l) => `<li>${inline(l.slice(2))}</li>`).join('')}</ul>`;
    if (lines.every((l) => /^\d+\. /.test(l))) return `<ol>${lines.map((l) => `<li>${inline(l.replace(/^\d+\. /, ''))}</li>`).join('')}</ol>`;
    return `<p>${inline(b)}</p>`;
  }).join('');
}
let CHAT = null;
function buildChat() {
  setStage(1920, 1080);
  const C = O.chat;
  const root = el('div', '', stage, `<div class="col"><div class="title">${esc(C.title)}</div>${C.messages.map((m) =>
    `<div class="msg ${m.role.toLowerCase()}"><div class="who">${m.role === 'User' ? 'The human' : 'Claude'}</div>
     <div class="body">${md(m.text, C.highlight)}</div></div>`).join('')}</div>`);
  root.id = 'chat';  // a real record, like the FEC pages before it: no satire label ([H])
  CHAT = root;
}
function renderChat(t) {
  const C = O.chat, col = CHAT.querySelector('.col'), mark = CHAT.querySelector('mark');
  const target = Math.max(0, mark.offsetTop + col.offsetTop - 1080 * 0.55);  // the highlight ends a little below centre
  const u = ease(clamp((t - C.start_s) / C.scroll_s, 0, 1));
  col.style.transform = `translateY(${-target * u}px)`;
  mark.style.setProperty('--hl', String(clamp((t - C.start_s - C.scroll_s) / 0.5, 0, 1)));
}

// ---------------------------------------------------------------- entry

if (SCENE === 'surface') buildSurfaces(Q.get('shot'));
else if (SCENE === 'screen') buildScreen();
else if (SCENE === 'chat') buildChat();
else buildCard(SCENE);
window.renderFrame = (t) => {
  if (SCENE === 'surface') renderSurfaces(t);
  else if (SCENE === 'screen') renderScreen(t);
  else if (SCENE === 'chat') renderChat(t);
  else renderCard(t);
};
window.ready = document.fonts.ready;
