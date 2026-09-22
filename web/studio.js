const NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];
const midiHz = (m) => 440 * Math.pow(2, (m - 69) / 12);
const midiName = (m) => NOTE_NAMES[m % 12] + (Math.floor(m / 12) - 1);

function readVar(dv, i) {
  let v = 0, b;
  do { b = dv.getUint8(i++); v = (v << 7) | (b & 0x7f); } while (b & 0x80);
  return [v, i];
}

function parseMidi(buf) {
  const dv = new DataView(buf);
  const str = (o, n) => String.fromCharCode(...new Uint8Array(buf, o, n));
  if (str(0, 4) !== "MThd") throw new Error("MIDI 헤더가 아닙니다");
  const ntrks = dv.getUint16(10);
  const division = dv.getUint16(12);
  if (division & 0x8000) throw new Error("SMPTE MIDI는 지원하지 않습니다");
  let off = 14;
  const tracks = [];
  for (let t = 0; t < ntrks; t++) {
    if (str(off, 4) !== "MTrk") throw new Error("트랙 헤더가 깨졌습니다");
    const len = dv.getUint32(off + 4);
    tracks.push(new Uint8Array(buf, off + 8, len));
    off += 8 + len;
  }
  const events = [];
  let tempo = 500000;
  const tempos = [{ tick: 0, us: 500000 }];
  for (const bytes of tracks) {
    const td = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    let i = 0, tick = 0, run = 0;
    while (i < bytes.length) {
      let dt; [dt, i] = readVar(td, i);
      tick += dt;
      let st = td.getUint8(i);
      if (st < 0x80) { st = run; } else { i++; run = st; }
      if (st === 0xff) {
        const type = td.getUint8(i++);
        let ln; [ln, i] = readVar(td, i);
        if (type === 0x51 && ln === 3) {
          tempo = (td.getUint8(i) << 16) | (td.getUint8(i + 1) << 8) | td.getUint8(i + 2);
          tempos.push({ tick, us: tempo });
        }
        i += ln;
      } else if (st === 0xf0 || st === 0xf7) {
        let ln; [ln, i] = readVar(td, i); i += ln;
      } else {
        const cmd = st >> 4;
        const a = td.getUint8(i++);
        const b = (cmd === 0xc || cmd === 0xd) ? 0 : td.getUint8(i++);
        if (cmd === 0x9 || cmd === 0x8) events.push({ tick, on: cmd === 0x9 && b > 0, pitch: a, vel: b });
      }
    }
  }
  tempos.sort((x, y) => x.tick - y.tick);
  const tickSec = (tick) => {
    let t = 0, last = 0, us = tempos[0].us;
    for (const tp of tempos) {
      if (tp.tick >= tick) break;
      t += ((tp.tick - last) * us) / division / 1e6;
      last = tp.tick; us = tp.us;
    }
    return t + ((tick - last) * us) / division / 1e6;
  };
  const ons = new Map();
  const notes = [];
  for (const ev of events.sort((a, b) => a.tick - b.tick || a.on - b.on)) {
    if (ev.on) ons.set(ev.pitch, ev);
    else if (ons.has(ev.pitch)) {
      const s = ons.get(ev.pitch); ons.delete(ev.pitch);
      notes.push({ pitch: ev.pitch, start: tickSec(s.tick), end: Math.max(tickSec(ev.tick), tickSec(s.tick) + 0.03), vel: s.vel });
    }
  }
  for (const s of ons.values()) notes.push({ pitch: s.pitch, start: tickSec(s.tick), end: tickSec(s.tick) + 0.2, vel: s.vel });
  const bpm = 60e6 / tempos[tempos.length - 1].us;
  const duration = notes.reduce((m, n) => Math.max(m, n.end), 0);
  return { bpm, duration, notes };
}

const state = {
  catalog: { songs: [] },
  song: null,
  crops: [],
  tracks: [],
  playing: false,
  playMode: "beep",
  t0: 0,
  ctx: null,
  playhead: 0,
  timer: 0,
  voices: [],
  written: null,
  rollLayout: { left: 44, px: 1 },
  notationView: "roll",
};

function $(id) { return document.getElementById(id); }

function showTab(name) {
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("on", p.id === "panel-" + name));
}

function allNotes() {
  const out = [];
  state.tracks.forEach((t, i) => t && t.notes.forEach((n) => out.push({ ...n, track: i })));
  return out;
}

function barSeconds() {
  const song = state.song;
  const bpm = (song && song.bpm) || (state.tracks[0] && state.tracks[0].bpm);
  return bpm ? 240 / bpm : null;
}

function playedIndexAt(t) {
  const song = state.song;
  const barS = barSeconds();
  if (!song || !song.play || !song.play.length || !barS) return null;
  let idx = Math.floor(Math.max(0, t - (song.t0 || 0)) / barS);
  if (idx < 0) idx = 0;
  if (idx >= song.play.length) idx = song.play.length - 1;
  return idx;
}

function writtenAt(t) {
  const song = state.song;
  const idx = playedIndexAt(t);
  if (idx == null || !song) return null;
  return song.play[idx];
}

function barWindow(t) {
  const song = state.song;
  const barS = barSeconds();
  const idx = playedIndexAt(t);
  if (idx == null || !song || !barS) return null;
  const start = (song.t0 || 0) + idx * barS;
  return { idx, written: song.play[idx], start, end: start + barS, barS };
}

const STRIP_RADIUS = 5;

function updateSyncMeta(t) {
  const el = $("sync-meta");
  if (!el) return;
  const win = barWindow(t == null ? 0 : t);
  const dur = songDuration();
  if (!win) {
    el.textContent = dur ? `전곡 ${dur.toFixed(0)}초 · 재생 ${(t || 0).toFixed(1)}초` : "";
    return;
  }
  const label = sectionLabel(sectionNameAt(win.idx));
  el.textContent =
    `재생 ${(t || 0).toFixed(1)}초 / ${dur.toFixed(0)}초`
    + ` · 연주 ${win.idx + 1}/${state.song.play.length}마디`
    + ` · 출판 ${win.written}마디`
    + (label ? ` (${label})` : "")
    + ` · 재생 중 위 줄이 같이 이동`;
}

function midiDuration() {
  return Math.max(0, ...state.tracks.filter(Boolean).map((tr) => tr.duration));
}

function listenEl() {
  return $("listen");
}

function hasListenSrc() {
  const a = listenEl();
  return !!(a && a.getAttribute("src"));
}

function songDuration() {
  let d = midiDuration();
  const a = listenEl();
  if (a && Number.isFinite(a.duration) && a.duration > 0) d = Math.max(d, a.duration);
  return d;
}

function seekTo(t) {
  const dur = songDuration();
  let next = Number.isFinite(t) ? t : 0;
  if (next < 0) next = 0;
  if (dur > 0) next = Math.min(next, dur);
  state.playhead = next;
  state.written = null;
  const a = listenEl();
  if (a && a.getAttribute("src")) {
    try { a.currentTime = next; } catch (_) {}
  }
  if (state.playing && state.playMode === "beep") {
    playFromBeep(next);
    return;
  }
  draw(next);
}

function jumpToPlayedIndex(idx) {
  const song = state.song;
  const barS = barSeconds();
  if (!song || !song.play || !song.play.length || !barS) return;
  const j = Math.max(0, Math.min(song.play.length - 1, idx));
  seekTo((song.t0 || 0) + j * barS + 0.05);
}

function ensureScoreStrip(idx) {
  const strip = $("score-strip");
  const song = state.song;
  if (!strip || !song || !song.play || idx == null || idx < 0) return null;
  const from = Math.max(0, idx - STRIP_RADIUS);
  const to = Math.min(song.play.length - 1, idx + STRIP_RADIUS);
  if (strip.dataset.from === String(from) && strip.dataset.to === String(to) && strip.childElementCount) {
    return strip;
  }
  strip.dataset.from = String(from);
  strip.dataset.to = String(to);
  strip.hidden = false;
  strip.innerHTML = "";
  for (let i = from; i <= to; i++) {
    const written = song.play[i];
    const item = state.crops.find((c) => c.bar === written);
    const fig = document.createElement("button");
    fig.type = "button";
    fig.className = "score-cell" + (item ? "" : " missing");
    fig.dataset.played = String(i);
    const lab = sectionLabel(sectionNameAt(i));
    const cap = `출판 ${written}` + (lab ? ` · ${lab}` : "");
    if (item) {
      fig.innerHTML = `<img alt="${cap}" loading="lazy" /><span class="cap">${cap}</span>`;
      fig.querySelector("img").src = item.url;
    } else {
      fig.innerHTML = `<span class="cap">${cap}<br />크롭 없음</span>`;
    }
    fig.onclick = () => jumpToPlayedIndex(i);
    strip.appendChild(fig);
  }
  return strip;
}

function syncStripScroll(t) {
  const strip = $("score-strip");
  const win = barWindow(t);
  if (!strip || !win) return;
  ensureScoreStrip(win.idx);
  if (strip.hidden) return;
  const cells = [...strip.querySelectorAll(".score-cell")];
  if (!cells.length) return;
  const cur = cells.find((c) => Number(c.dataset.played) === win.idx);
  if (!cur) return;
  cells.forEach((c) => c.classList.toggle("on", Number(c.dataset.played) === win.idx));
  const next = cells.find((c) => Number(c.dataset.played) === win.idx + 1);
  const frac = Math.min(1, Math.max(0, (t - win.start) / win.barS));
  const x0 = cur.offsetLeft + cur.offsetWidth / 2;
  const x1 = next ? next.offsetLeft + next.offsetWidth / 2 : x0 + cur.offsetWidth;
  strip.scrollLeft = Math.max(0, x0 + (x1 - x0) * frac - strip.clientWidth / 2);
}

function showCrop(written) {
  const strip = $("score-strip");
  const meta = $("score-meta");
  if (!strip) return;
  if (written == null) {
    state.written = null;
    strip.hidden = true;
    strip.innerHTML = "";
    strip.dataset.from = "";
    strip.dataset.to = "";
    setScoreHint("");
    if (meta) meta.textContent = "";
    return;
  }
  const song = state.song;
  let idx = playedIndexAt(state.playhead || 0);
  if (idx == null || !song || song.play[idx] !== written) {
    idx = song && song.play ? song.play.indexOf(written) : -1;
  }
  state.written = written;
  const label = sectionLabel(sectionNameAt(idx));
  if (!song || !song.play || !song.play.length || idx < 0) {
    strip.hidden = true;
    if (meta) meta.textContent = "이 곡은 출판 크롭이 없습니다";
    setScoreHint("");
    return;
  }
  ensureScoreStrip(idx);
  syncStripScroll(state.playhead || 0);
  if (meta) {
    meta.textContent =
      `가운데 = 출판 ${written}마디`
      + (label ? ` · ${label}` : "")
      + ` · 연주 ${idx + 1}/${song.play.length}`
      + ` · 재생하면 줄이 따라 움직임`;
  }
  setScoreHint(sectionHintAt(idx));
}

function sectionName(written) {
  const song = state.song;
  if (!song || !song.play) return "";
  const played = song.play.indexOf(written);
  return sectionNameAt(played);
}

function sectionNameAt(played) {
  const song = state.song;
  if (!song || played == null || played < 0) return "";
  for (const [name, range] of Object.entries(song.sections || {})) {
    if (played >= range[0] && played < range[1]) return name;
  }
  return "";
}

function sectionLabel(name) {
  if (!name) return "";
  const labels = (state.song && state.song.section_labels) || {};
  return labels[name] || name;
}

function sectionHint(written) {
  return sectionHintAt(songPlayIndex(written));
}

function sectionHintAt(played) {
  const name = sectionNameAt(played);
  const hints = (state.song && state.song.section_hints) || {};
  return (name && hints[name]) || "";
}

function songPlayIndex(written) {
  const song = state.song;
  if (!song || !song.play) return -1;
  const fromHead = playedIndexAt(state.playhead || 0);
  if (fromHead != null && song.play[fromHead] === written) return fromHead;
  return song.play.indexOf(written);
}

function setScoreHint(text) {
  const el = $("score-hint");
  if (!el) return;
  el.hidden = !text;
  el.textContent = text || "";
}

function skipToReview() {
  const song = state.song;
  if (!song) return;
  jumpToPlayedIndex(song.review_from || 0);
}

function nudgeBar(delta) {
  const idx = playedIndexAt(state.playhead);
  jumpToPlayedIndex((idx == null ? 0 : idx) + delta);
}

function scrollPlayheadIntoView(x) {
  const wrap = $("roll-wrap");
  if (!wrap) return;
  if (state.playing) {
    wrap.scrollLeft = Math.max(0, x - wrap.clientWidth * 0.35);
    return;
  }
  const pad = wrap.clientWidth * 0.35;
  const left = wrap.scrollLeft;
  const right = left + wrap.clientWidth;
  if (x < left + 40 || x > right - 40) {
    wrap.scrollLeft = Math.max(0, x - pad);
  }
}

function draw(playhead) {
  const notes = allNotes();
  const canvas = $("roll");
  const wrap = $("roll-wrap");
  if (!canvas || !wrap) return;
  const t = playhead == null ? 0 : playhead;
  const dur = Math.max(1, ...state.tracks.filter(Boolean).map((tr) => tr.duration), t);
  let lo = 28, hi = 52;
  for (const n of notes) { lo = Math.min(lo, n.pitch); hi = Math.max(hi, n.pitch); }
  lo = Math.max(21, lo - 1); hi = Math.min(72, hi + 1);
  const rowH = 16, left = 44, px = Math.max(48, (wrap.clientWidth - left) / Math.max(dur, 8) * 6);
  state.rollLayout = { left, px };
  const W = Math.max(wrap.clientWidth, left + dur * px + 24);
  const H = Math.max(wrap.clientHeight, (hi - lo + 1) * rowH + 8);
  const dpr = window.devicePixelRatio || 1;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.width = W + "px"; canvas.style.height = H + "px";
  const g = canvas.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.fillStyle = "#0e1015"; g.fillRect(0, 0, W, H);
  for (let p = lo; p <= hi; p++) {
    const y = (hi - p) * rowH;
    const black = [1, 3, 6, 8, 10].includes(p % 12);
    g.fillStyle = black ? "#141821" : "#12151c";
    g.fillRect(left, y, W - left, rowH);
    g.fillStyle = "#2a2f3c"; g.fillRect(0, y, left, rowH);
    g.fillStyle = p % 12 === 4 ? "#c9c4b8" : "#7a808c";
    g.font = "11px ui-sans-serif";
    g.fillText(midiName(p), 6, y + 12);
  }
  const bpm = (state.song && state.song.bpm) || (state.tracks[0] && state.tracks[0].bpm);
  const barS = bpm ? 240 / bpm : null;
  if (barS) {
    g.strokeStyle = "#2a3142";
    for (let tt = 0; tt < dur + barS; tt += barS / 4) {
      const x = left + tt * px;
      g.globalAlpha = Math.abs(tt / barS - Math.round(tt / barS)) < 1e-3 ? 0.55 : 0.22;
      g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke();
    }
    g.globalAlpha = 1;
  }
  const win = barWindow(t);
  if (win) {
    const x0 = left + win.start * px;
    const bw = Math.max(2, win.barS * px);
    g.fillStyle = "rgba(243, 211, 154, 0.12)";
    g.fillRect(x0, 0, bw, H);
    g.fillStyle = "#f3d39a";
    g.font = "11px ui-sans-serif";
    g.fillText("출판 " + win.written, x0 + 4, 14);
  }
  for (const n of notes) {
    const x = left + n.start * px;
    const w = Math.max(3, (n.end - n.start) * px - 1);
    const y = (hi - n.pitch) * rowH + 2;
    const inBar = win && n.start >= win.start && n.start < win.end;
    g.fillStyle = n.track ? "#6aa6c9" : "#e2a15a";
    g.globalAlpha = inBar ? 0.55 + (n.vel / 127) * 0.45 : 0.22 + (n.vel / 127) * 0.35;
    g.fillRect(x, y, w, rowH - 4);
    g.globalAlpha = 1;
  }
  const x = left + t * px;
  g.strokeStyle = "#f3d39a"; g.lineWidth = 1.5;
  g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke();
  g.lineWidth = 1;
  showCrop(writtenAt(t));
  updateSyncMeta(t);
  scrollPlayheadIntoView(x);
  syncNotationScroll(t);
}

function ensureCtx() {
  if (!state.ctx) state.ctx = new AudioContext();
  return state.ctx;
}

function beep(ctx, pitch, dur, vel, when) {
  const o = ctx.createOscillator();
  const f = ctx.createBiquadFilter();
  const g = ctx.createGain();
  o.type = "sawtooth";
  o.frequency.value = midiHz(pitch);
  f.type = "lowpass"; f.frequency.value = 420 + pitch * 8;
  const peak = 0.08 * (vel / 127);
  g.gain.setValueAtTime(0.0001, when);
  g.gain.exponentialRampToValueAtTime(peak, when + 0.012);
  g.gain.exponentialRampToValueAtTime(0.0001, when + dur);
  o.connect(f); f.connect(g); g.connect(ctx.destination);
  o.start(when); o.stop(when + dur + 0.02);
  return o;
}

function stopVoices() {
  for (const o of state.voices) { try { o.stop(); } catch (_) {} }
  state.voices = [];
}

function playFromBeep(from) {
  const t = Math.max(0, from || 0);
  const notes = allNotes().filter((n) => n.end > t);
  if (!notes.length) {
    draw(t);
    return;
  }
  const ctx = ensureCtx();
  if (ctx.state === "suspended") ctx.resume();
  stopVoices();
  const now = ctx.currentTime + 0.05;
  state.playMode = "beep";
  state.t0 = now - t;
  state.playing = true;
  $("play").textContent = "일시정지";
  for (const n of notes) {
    const startAt = now + Math.max(0, n.start - t);
    const dur = n.end - Math.max(n.start, t);
    state.voices.push(beep(ctx, n.pitch, Math.max(0.04, dur), n.vel, startAt));
  }
  startPlayheadTick();
}

function playFromWav() {
  const a = listenEl();
  if (!a || !a.getAttribute("src")) {
    playFromBeep(state.playhead);
    return;
  }
  stopVoices();
  if (state.ctx) {
    try { state.ctx.suspend(); } catch (_) {}
  }
  state.playMode = "wav";
  try { a.currentTime = state.playhead; } catch (_) {}
  const start = () => {
    state.playing = true;
    $("play").textContent = "일시정지";
    startPlayheadTick();
  };
  const p = a.play();
  if (p && p.then) {
    p.then(start).catch(() => playFromBeep(state.playhead));
  } else {
    start();
  }
}

function play() {
  if (hasListenSrc()) {
    playFromWav();
    return;
  }
  if (!allNotes().length) return;
  playFromBeep(state.playhead);
}

function startPlayheadTick() {
  cancelAnimationFrame(state.timer);
  const tick = () => {
    if (!state.playing) return;
    if (state.playMode === "wav") {
      const a = listenEl();
      if (!a) { pause(); return; }
      state.playhead = a.currentTime;
      draw(state.playhead);
      if (a.ended) { pause(); return; }
    } else if (state.ctx) {
      state.playhead = state.ctx.currentTime - state.t0;
      draw(state.playhead);
      if (state.playhead > songDuration() + 0.2) { stop(); return; }
    }
    state.timer = requestAnimationFrame(tick);
  };
  tick();
}

function pause() {
  state.playing = false;
  stopVoices();
  if (state.ctx) {
    try { state.ctx.suspend(); } catch (_) {}
  }
  const a = listenEl();
  if (a && !a.paused) {
    try { a.pause(); } catch (_) {}
  }
  $("play").textContent = "재생";
  cancelAnimationFrame(state.timer);
}

function stop() {
  pause();
  seekTo(0);
}

function seekFromRollEvent(ev) {
  const layout = state.rollLayout;
  const wrap = $("roll-wrap");
  if (!layout || !layout.px || !wrap) return;
  const rect = wrap.getBoundingClientRect();
  const x = ev.clientX - rect.left + wrap.scrollLeft;
  seekTo((x - layout.left) / layout.px);
}

async function loadUrl(url, slot, name) {
  const buf = await (await fetch(url)).arrayBuffer();
  const parsed = parseMidi(buf);
  parsed.name = name;
  state.tracks[slot] = parsed;
  $("play").disabled = false;
  $("stop").disabled = false;
  const bits = state.tracks.filter(Boolean).map((t) => `${t.name} · ${t.notes.length}음 · ${t.duration.toFixed(0)}s`);
  $("meta").textContent = bits.join("  |  ");
  draw(state.playhead);
  refreshNotation();
}

async function fetchJson(urls) {
  const list = Array.isArray(urls) ? urls : [urls];
  let last = new Error("요청 실패");
  for (const url of list) {
    try {
      const res = await fetch(url);
      if (res.ok) return await res.json();
      last = new Error(url + " " + res.status);
    } catch (err) {
      last = err;
    }
  }
  throw last;
}

function isStaticHost() {
  return !!(state.catalog && (state.catalog.static || state.catalog.upload_available === false));
}

function applyHostMode() {
  const live = !isStaticHost();
  const liveBox = $("upload-live");
  const staticNote = $("upload-static");
  if (liveBox) liveBox.hidden = !live;
  if (staticNote) staticNote.hidden = live;
}

async function loadCrops(song) {
  state.crops = [];
  if (song.crops && song.crops.length) {
    state.crops = song.crops;
    showCrop(writtenAt(state.playhead));
    return;
  }
  if (!song.crop_song) {
    showCrop(null);
    return;
  }
  try {
    const data = await fetchJson("/api/crops/" + song.crop_song);
    state.crops = data.crops || [];
  } catch (_) {
    const n = song.n_crops || 0;
    for (let i = 1; i <= n; i++) {
      state.crops.push({
        bar: i,
        url: "/score_crops/" + song.crop_song + "/m" + String(i).padStart(3, "0") + ".png",
      });
    }
  }
  showCrop(writtenAt(state.playhead));
}

async function selectSong(id, keepTime) {
  pause();
  const song = state.catalog.songs.find((s) => s.id === id);
  const keep = keepTime ? state.playhead : null;
  state.song = song;
  state.tracks = [];
  state.written = null;
  $("missing").hidden = !!(song && song.midi);
  $("score-box").hidden = !(song && song.crop_song);
  const skip = $("skip-rest");
  if (skip) skip.hidden = !(song && song.review_from);
  if (!song) return;
  if (keep != null) seekTo(keep);
  else jumpToPlayedIndex(song.review_from || 0);
  await loadCrops(song);
  applyListenSource();
  const which = $("midi-kind").value;
  if (which === "both" && song.midi && song.quant) {
    await loadUrl(song.midi, 0, "성능");
    await loadUrl(song.quant, 1, "양자화");
  } else if (which === "quant" && song.quant) {
    await loadUrl(song.quant, 0, "양자화");
  } else if (song.midi) {
    await loadUrl(song.midi, 0, "성능");
  } else {
    $("meta").textContent = "이 곡 MIDI가 없습니다. 아래에서 전사하거나 음원을 올리세요.";
    draw(state.playhead);
    refreshNotation();
  }
}

function fillSongSelect() {
  const sel = $("song");
  sel.innerHTML = "";
  for (const s of state.catalog.songs) {
    const o = document.createElement("option");
    o.value = s.id;
    const tag = s.kind === "job" ? ` [${s.status || "작업"}]` : "";
    o.textContent = s.title + tag;
    sel.appendChild(o);
  }
}

async function refreshCatalog(keepId) {
  state.catalog = await fetchJson(["/api/catalog", "data/catalog.json"]);
  applyHostMode();
  fillSongSelect();
  const id = keepId || (state.song && state.song.id) || (state.catalog.songs[0] && state.catalog.songs[0].id);
  if (id) {
    $("song").value = id;
    await selectSong(id);
  }
}

async function submitUpload(file) {
  if (isStaticHost()) {
    $("upload-status").textContent = "정적 호스팅에서는 올릴 수 없습니다. 로컬 서버를 켜세요.";
    return;
  }
  const fd = new FormData();
  fd.append("audio", file, file.name);
  const bpm = $("bpm").value.trim();
  const key = $("key").value.trim();
  const grid = $("grid").value;
  if (bpm) fd.append("bpm", bpm);
  if (key) fd.append("key", key);
  fd.append("grid", grid);
  $("upload-status").textContent = "올리는 중…";
  const res = await fetch("/api/jobs", { method: "POST", body: fd });
  const data = await res.json();
  if (!res.ok) {
    $("upload-status").textContent = data.error || "실패";
    return;
  }
  $("upload-status").textContent = "대기열에 넣었습니다. CPU 전사라 꽤 걸릴 수 있습니다. 이 화면을 유지하세요.";
  pollJob(data.id || data.job_id);
}

async function pollJob(id) {
  const tick = async () => {
    const data = await (await fetch("/api/jobs/" + id)).json();
    renderJobs();
    $("upload-status").textContent = data.status === "done"
      ? "완료. 보기 탭에서 고르세요."
      : data.status === "error"
        ? ("실패: " + (data.error || ""))
        : (data.status === "running" ? "전사 중…" : "대기 중…");
    if (data.status === "done") {
      await refreshCatalog("job-" + id);
      showTab("view");
      return;
    }
    if (data.status === "error") return;
    setTimeout(tick, 2500);
  };
  tick();
}

async function renderJobs() {
  const box = $("jobs");
  if (!box) return;
  if (isStaticHost()) {
    box.innerHTML = "";
    return;
  }
  let data;
  try {
    data = await fetchJson("/api/jobs");
  } catch (_) {
    box.innerHTML = "";
    return;
  }
  box.innerHTML = "";
  for (const j of data.jobs || []) {
    const div = document.createElement("div");
    div.className = "job";
    const st = j.status === "done" ? "ok" : j.status === "error" ? "bad" : "";
    div.innerHTML = `<strong>${j.name || j.title}</strong> <span class="${st}">${j.status}</span>`
      + (j.error ? `<div class="bad">${j.error}</div>` : "");
    box.appendChild(div);
  }
}

const OSMD_URL = "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@2.1.3/build/opensheetmusicdisplay.min.js";
const AT_URL = "https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/alphaTab.min.js";
const AT_FONT = "https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/font/";
const scriptLoads = {};

function loadScript(src) {
  if (!scriptLoads[src]) {
    scriptLoads[src] = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.async = true;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error("스크립트를 불러오지 못했습니다"));
      document.head.appendChild(s);
    });
  }
  return scriptLoads[src];
}

function xmlEscape(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;",
  }[c]));
}

function keyInfo(text) {
  const raw = String(text || "").trim();
  const minor = /minor/i.test(raw);
  const name = raw.replace(/minor|major/ig, "").trim();
  const table = {
    "C": [0, "major"], "G": [1, "major"], "D": [2, "major"], "A": [3, "major"],
    "E": [4, "major"], "B": [5, "major"], "F#": [6, "major"], "C#": [7, "major"],
    "F": [-1, "major"], "Bb": [-2, "major"], "Eb": [-3, "major"], "Ab": [-4, "major"],
    "A minor": [0, "minor"], "E minor": [1, "minor"], "B minor": [2, "minor"],
    "F# minor": [3, "minor"], "C# minor": [4, "minor"], "G# minor": [5, "minor"],
    "D minor": [-1, "minor"], "G minor": [-2, "minor"], "C minor": [-3, "minor"],
  };
  const hit = table[minor ? name + " minor" : name] || table[raw];
  if (!hit) return { fifths: 0, mode: "major" };
  return { fifths: hit[0], mode: hit[1] };
}

const SHARP_SPELL = [["C", 0], ["C", 1], ["D", 0], ["D", 1], ["E", 0], ["F", 0], ["F", 1], ["G", 0], ["G", 1], ["A", 0], ["A", 1], ["B", 0]];
const FLAT_SPELL = [["C", 0], ["D", -1], ["D", 0], ["E", -1], ["E", 0], ["F", 0], ["G", -1], ["G", 0], ["A", -1], ["A", 0], ["B", -1], ["B", 0]];
const BASS_TUNING = [43, 38, 33, 28];

function spellPitch(midi, fifths) {
  const pc = ((midi % 12) + 12) % 12;
  const pair = (fifths < 0 ? FLAT_SPELL : SHARP_SPELL)[pc];
  return { step: pair[0], alter: pair[1], octave: Math.floor(midi / 12) - 1 };
}

function bassStringFret(midi) {
  let best = null;
  for (let s = 0; s < BASS_TUNING.length; s++) {
    const fret = midi - BASS_TUNING[s];
    if (fret < 0 || fret > 20) continue;
    if (!best || fret < best.fret) best = { string: s + 1, fret };
  }
  return best || { string: 4, fret: Math.max(0, midi - 28) };
}

function notationSourceNotes() {
  const kind = ($("midi-kind") && $("midi-kind").value) || "perf";
  if ((kind === "quant" || kind === "both") && state.tracks[1]) return state.tracks[1].notes;
  if (state.tracks[0]) return state.tracks[0].notes;
  return [];
}

function notesToMusicXml(mono, bpm, keyText, title) {
  const key = keyInfo(keyText);
  const last = mono.reduce((m, n) => Math.max(m, n.end), 0);
  const slots = Math.max(8, Math.ceil(last * 2));
  const grid = new Array(slots).fill(null);
  for (const n of mono) {
    const a = Math.max(0, Math.round(n.start * 2));
    const b = Math.max(a + 1, Math.round(n.end * 2));
    for (let i = a; i < b && i < grid.length; i++) grid[i] = n.pitch;
  }
  while (grid.length % 8) grid.push(null);
  let measures = "";
  for (let i = 0; i < grid.length; i++) {
    if (i % 8 === 0) {
      measures += `<measure number="${i / 8 + 1}">`;
      if (i === 0) {
        measures += `<attributes><divisions>2</divisions><key><fifths>${key.fifths}</fifths><mode>${key.mode}</mode></key><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>F</sign><line>4</line></clef><staff-details><staff-lines>4</staff-lines><staff-tuning line="1"><tuning-step>G</tuning-step><tuning-octave>2</tuning-octave></staff-tuning><staff-tuning line="2"><tuning-step>D</tuning-step><tuning-octave>2</tuning-octave></staff-tuning><staff-tuning line="3"><tuning-step>A</tuning-step><tuning-octave>1</tuning-octave></staff-tuning><staff-tuning line="4"><tuning-step>E</tuning-step><tuning-octave>1</tuning-octave></staff-tuning></staff-details></attributes>`;
        measures += `<direction><direction-type><metronome><beat-unit>quarter</beat-unit><per-minute>${Math.round(bpm)}</per-minute></metronome></direction-type><sound tempo="${Math.round(bpm)}"/></direction>`;
      }
    }
    const pitch = grid[i];
    const prev = i > 0 && grid[i - 1] === pitch && pitch != null;
    const next = i + 1 < grid.length && grid[i + 1] === pitch && pitch != null;
    if (pitch == null) {
      measures += `<note><rest/><duration>1</duration><type>eighth</type></note>`;
    } else {
      const sp = spellPitch(pitch, key.fifths);
      const sf = bassStringFret(pitch);
      const alter = sp.alter ? `<alter>${sp.alter}</alter>` : "";
      const ties = `${prev ? `<tie type="stop"/>` : ""}${next ? `<tie type="start"/>` : ""}`;
      const tied = `${prev ? `<tied type="stop"/>` : ""}${next ? `<tied type="start"/>` : ""}`;
      measures += `<note><pitch><step>${sp.step}</step>${alter}<octave>${sp.octave}</octave></pitch><duration>1</duration>${ties}<type>eighth</type><notations>${tied}<technical><string>${sf.string}</string><fret>${sf.fret}</fret></technical></notations></note>`;
    }
    if (i % 8 === 7) measures += `</measure>`;
  }
  return `<?xml version="1.0" encoding="UTF-8"?>` +
    `<score-partwise version="3.1"><work><work-title>${xmlEscape(title || "Bass")}</work-title></work>` +
    `<part-list><score-part id="P1"><part-name>Bass</part-name>` +
    `<score-instrument id="P1-I1"><instrument-name>Electric Bass</instrument-name></score-instrument>` +
    `<midi-instrument id="P1-I1"><midi-channel>1</midi-channel><midi-program>34</midi-program></midi-instrument>` +
    `</score-part></part-list><part id="P1">${measures}</part></score-partwise>`;
}

function buildNotationXml() {
  const song = state.song;
  const bpm = (song && song.bpm) || (state.tracks[0] && state.tracks[0].bpm) || 120;
  const origin = (song && song.t0) || 0;
  const beat = 60 / bpm;
  const mono = [];
  for (const n of notationSourceNotes()) {
    let start = (n.start - origin) / beat;
    let end = (n.end - origin) / beat;
    if (end <= 0) continue;
    if (start < 0) start = 0;
    start = Math.round(start * 2) / 2;
    end = Math.max(start + 0.5, Math.round(end * 2) / 2);
    if (mono.length && start < mono[mono.length - 1].end) {
      if (start <= mono[mono.length - 1].start) continue;
      mono[mono.length - 1].end = start;
    }
    mono.push({ start, end, pitch: n.pitch });
  }
  return notesToMusicXml(mono, bpm, song && song.key, song && song.title);
}

function setNotationNote(text) {
  const el = $("notation-note");
  if (el) el.textContent = text || "";
}

const NOTATION_NOTES = {
  roll: "피아노롤은 가로가 시간입니다. 누르면 그 시간으로 갑니다. 노란 선·띠가 위 가운데 마디와 같습니다.",
  osmd: "OSMD · BSD. 같은 MIDI를 8분 그리드 오선으로 그렸습니다. 마디 번호는 연주 순서입니다. 칸을 누르면 그 높이의 시간으로 갑니다.",
  alphatab: "alphaTab · MPL-2.0. 오선과 4현 탭입니다. 줄·프렛은 표준 튜닝에서 가장 낮은 프렛으로 추정한 것이고, 출판 탭이 아닙니다.",
  musescore: "MuseScore는 데스크톱 앱입니다. MIDI를 받아 거기서 열면 오선으로 양자화됩니다.",
};

function updateMuseScoreLink() {
  const a = $("midi-download");
  const song = state.song;
  if (!a) return;
  const kind = ($("midi-kind") && $("midi-kind").value) || "perf";
  const url = song && ((kind === "quant" && song.quant) || song.midi || song.quant);
  if (!url) {
    a.removeAttribute("href");
    a.textContent = "이 곡 MIDI가 없습니다.";
    return;
  }
  a.href = url;
  a.textContent = url.split("/").pop() + " 받기";
}

function syncNotationScroll(t) {
  const id = state.notationView === "osmd" ? "osmd-wrap" : state.notationView === "alphatab" ? "alphatab-wrap" : "";
  const el = id && $(id);
  if (!el || el.hidden) return;
  const dur = songDuration();
  const max = el.scrollHeight - el.clientHeight;
  if (!dur || max <= 0) return;
  const frac = Math.min(1, Math.max(0, (t || 0) / dur));
  el.scrollTop = frac * max;
}

function seekFromNotationEvent(ev) {
  if (state.notationView !== "osmd" && state.notationView !== "alphatab") return;
  const el = ev.currentTarget;
  const rect = el.getBoundingClientRect();
  const y = ev.clientY - rect.top + el.scrollTop;
  const frac = el.scrollHeight ? y / el.scrollHeight : 0;
  seekTo(frac * songDuration());
}

let notationToken = 0;

async function renderOsmd(xml) {
  await loadScript(OSMD_URL);
  const el = $("osmd-wrap");
  el.innerHTML = "";
  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {
    backend: "svg",
    drawTitle: true,
    drawPartNames: false,
    autoResize: true,
    drawingParameters: "compacttight",
  });
  state.osmd = osmd;
  await osmd.load(xml);
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  osmd.render();
}

async function ensureAlphaTab() {
  await loadScript(AT_URL);
  if (state.alphaTab) return state.alphaTab;
  const el = $("alphatab-wrap");
  state.alphaTab = new alphaTab.AlphaTabApi(el, {
    core: {
      engine: "svg",
      scriptFile: AT_URL,
      fontDirectory: AT_FONT,
    },
    display: {
      layoutMode: alphaTab.LayoutMode.Page,
      staveProfile: alphaTab.StaveProfile.ScoreTab,
      barsPerRow: 4,
    },
    player: {
      enablePlayer: false,
      enableCursor: false,
      scrollElement: el,
    },
  });
  return state.alphaTab;
}

async function renderAlphaTab(xml) {
  const api = await ensureAlphaTab();
  const bytes = new TextEncoder().encode(xml);
  const ok = api.load(bytes);
  if (ok === false) throw new Error("alphaTab이 이 악보를 열지 못했습니다");
  await new Promise((resolve) => {
    const timer = setTimeout(resolve, 20000);
    if (api.renderFinished && api.renderFinished.on) {
      const off = api.renderFinished.on(() => {
        clearTimeout(timer);
        if (typeof off === "function") off();
        resolve();
      });
    }
  });
}

function refreshNotation() {
  const view = state.notationView;
  if (view !== "osmd" && view !== "alphatab") return;
  const notes = notationSourceNotes();
  if (!notes.length) {
    setNotationNote("MIDI가 없습니다.");
    return;
  }
  const token = ++notationToken;
  setNotationNote("악보 그리는 중…");
  const xml = buildNotationXml();
  const job = view === "osmd" ? renderOsmd(xml) : renderAlphaTab(xml);
  job.then(() => {
    if (token !== notationToken) return;
    setNotationNote(NOTATION_NOTES[view]);
    requestAnimationFrame(() => syncNotationScroll(state.playhead));
  }).catch((err) => {
    if (token !== notationToken) return;
    setNotationNote("악보를 그리지 못했습니다. " + (err && err.message ? err.message : err));
  });
}

function setNotationView(name) {
  state.notationView = name;
  document.querySelectorAll("#notation-switch button").forEach((b) => {
    b.classList.toggle("active", b.dataset.notation === name);
  });
  const map = { roll: "roll-wrap", osmd: "osmd-wrap", alphatab: "alphatab-wrap", musescore: "musescore-wrap" };
  for (const [key, id] of Object.entries(map)) {
    const el = $(id);
    if (el) el.hidden = key !== name;
  }
  setNotationNote(NOTATION_NOTES[name] || "");
  if (name === "musescore") updateMuseScoreLink();
  if (name === "osmd" || name === "alphatab") refreshNotation();
  else draw(state.playhead);
}

function bind() {
  document.querySelectorAll(".tabs button").forEach((b) => {
    b.onclick = () => showTab(b.dataset.tab);
  });
  $("song").onchange = () => selectSong($("song").value);
  $("midi-kind").onchange = () => state.song && selectSong(state.song.id, true);
  $("play").onclick = () => { if (state.playing) pause(); else play(); };
  $("stop").onclick = stop;
  $("prev-bar").onclick = () => nudgeBar(-1);
  $("next-bar").onclick = () => nudgeBar(1);
  const skip = $("skip-rest");
  if (skip) skip.onclick = skipToReview;
  $("file").onchange = (e) => e.target.files[0] && submitUpload(e.target.files[0]);
  const drop = $("drop");
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("hot"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("hot"));
  drop.addEventListener("drop", (e) => {
    e.preventDefault(); drop.classList.remove("hot");
    const f = e.dataTransfer.files[0];
    if (f) submitUpload(f);
  });
  $("upload-btn").onclick = () => $("file").click();
  const wrap = $("roll-wrap");
  if (wrap) wrap.addEventListener("click", seekFromRollEvent);
  document.querySelectorAll("#notation-switch button").forEach((b) => {
    b.onclick = () => setNotationView(b.dataset.notation);
  });
  for (const id of ["osmd-wrap", "alphatab-wrap"]) {
    const pane = $(id);
    if (pane) pane.addEventListener("click", seekFromNotationEvent);
  }
  const listen = $("listen");
  if (listen) {
    listen.addEventListener("play", () => {
      stopVoices();
      state.playMode = "wav";
      state.playing = true;
      $("play").textContent = "일시정지";
      startPlayheadTick();
    });
    listen.addEventListener("pause", () => {
      if (!state.playing) return;
      if (state.playMode === "wav") {
        state.playing = false;
        $("play").textContent = "재생";
        cancelAnimationFrame(state.timer);
      }
    });
    listen.addEventListener("ended", () => {
      if (state.playMode === "wav") pause();
    });
    listen.addEventListener("loadedmetadata", () => {
      try { listen.currentTime = state.playhead; } catch (_) {}
    });
  }
  const listenKind = $("listen-kind");
  if (listenKind) {
    listenKind.onchange = () => {
      const was = state.playing;
      applyListenSource();
      if (was) play();
      else seekTo(state.playhead);
    };
  }
  window.addEventListener("resize", () => draw(state.playhead));
}

function applyListenSource() {
  const box = $("listen-box");
  const audio = $("listen");
  const kind = $("listen-kind");
  if (!box || !audio) return;
  const song = state.song;
  const preview = song && song.preview;
  const compare = song && song.compare;
  box.hidden = !(preview || compare);
  if (box.hidden) {
    audio.removeAttribute("src");
    return;
  }
  if (kind) {
    kind.querySelector('option[value="preview"]').disabled = !preview;
    kind.querySelector('option[value="compare"]').disabled = !compare;
    if (kind.value === "preview" && !preview) kind.value = "compare";
    if (kind.value === "compare" && !compare) kind.value = "preview";
  }
  const url = (kind && kind.value === "compare" && compare) || preview || compare;
  if (url && audio.getAttribute("src") !== url) audio.src = url;
}

bind();
refreshCatalog();
renderJobs();
showTab("view");
