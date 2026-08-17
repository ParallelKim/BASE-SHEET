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
  t0: 0,
  ctx: null,
  playhead: 0,
  timer: 0,
  voices: [],
  written: null,
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

function writtenAt(t) {
  const song = state.song;
  if (!song || !song.play || !song.play.length || !song.bpm) return null;
  const barS = 240 / song.bpm;
  let idx = Math.floor(Math.max(0, t - (song.t0 || 0)) / barS);
  if (idx < 0) idx = 0;
  if (idx >= song.play.length) idx = song.play.length - 1;
  return song.play[idx];
}

function showCrop(written) {
  if (written == null || written === state.written) return;
  state.written = written;
  const item = state.crops.find((c) => c.bar === written);
  const img = $("score");
  const meta = $("score-meta");
  if (!item) {
    img.removeAttribute("src");
    img.hidden = true;
    meta.textContent = state.song && state.song.crop_song ? `기보 ${written}마디 크롭 없음` : "이 곡은 출판 크롭이 없습니다";
    return;
  }
  img.hidden = false;
  img.src = item.url;
  const sec = sectionName(written);
  meta.textContent = `기보 ${written}마디` + (sec ? ` · ${sec}` : "");
}

function sectionName(written) {
  const song = state.song;
  if (!song || !song.play) return "";
  const played = song.play.indexOf(written);
  if (played < 0) return "";
  for (const [name, range] of Object.entries(song.sections || {})) {
    if (played >= range[0] && played < range[1]) return name;
  }
  return "";
}

function draw(playhead) {
  const notes = allNotes();
  const canvas = $("roll");
  const wrap = $("roll-wrap");
  if (!canvas || !wrap) return;
  const dur = Math.max(1, ...state.tracks.filter(Boolean).map((t) => t.duration), playhead || 0);
  let lo = 28, hi = 52;
  for (const n of notes) { lo = Math.min(lo, n.pitch); hi = Math.max(hi, n.pitch); }
  lo = Math.max(21, lo - 1); hi = Math.min(72, hi + 1);
  const rowH = 16, left = 44, px = Math.max(48, (wrap.clientWidth - left) / Math.max(dur, 8) * 6);
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
  if (bpm) {
    const bar = 240 / bpm;
    g.strokeStyle = "#2a3142";
    for (let t = 0; t < dur + bar; t += bar / 4) {
      const x = left + t * px;
      g.globalAlpha = Math.abs(t / bar - Math.round(t / bar)) < 1e-3 ? 0.55 : 0.22;
      g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke();
    }
    g.globalAlpha = 1;
  }
  for (const n of notes) {
    const x = left + n.start * px;
    const w = Math.max(3, (n.end - n.start) * px - 1);
    const y = (hi - n.pitch) * rowH + 2;
    g.fillStyle = n.track ? "#6aa6c9" : "#e2a15a";
    g.globalAlpha = 0.35 + (n.vel / 127) * 0.65;
    g.fillRect(x, y, w, rowH - 4);
    g.globalAlpha = 1;
  }
  if (playhead != null) {
    const x = left + playhead * px;
    g.strokeStyle = "#f3d39a"; g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke();
    g.lineWidth = 1;
    showCrop(writtenAt(playhead));
  }
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

function play() {
  const notes = allNotes();
  if (!notes.length) return;
  const ctx = ensureCtx();
  if (ctx.state === "suspended") ctx.resume();
  stopVoices();
  const now = ctx.currentTime + 0.05;
  state.t0 = now;
  state.playing = true;
  $("play").textContent = "일시정지";
  for (const n of notes) {
    state.voices.push(beep(ctx, n.pitch, Math.max(0.04, n.end - n.start), n.vel, now + n.start));
  }
  const tick = () => {
    if (!state.playing) return;
    state.playhead = ctx.currentTime - state.t0;
    draw(state.playhead);
    const dur = Math.max(0, ...state.tracks.filter(Boolean).map((t) => t.duration));
    if (state.playhead > dur + 0.2) { stop(); return; }
    state.timer = requestAnimationFrame(tick);
  };
  tick();
}

function pause() {
  state.playing = false;
  stopVoices();
  if (state.ctx) state.ctx.suspend();
  $("play").textContent = "재생";
  cancelAnimationFrame(state.timer);
}

function stop() {
  pause();
  state.playhead = 0;
  if (state.ctx) state.ctx.resume();
  draw(0);
  showCrop(writtenAt(0));
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
  draw(0);
  showCrop(writtenAt(0));
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
    showCrop(writtenAt(0));
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
  showCrop(writtenAt(0));
}

async function selectSong(id) {
  const song = state.catalog.songs.find((s) => s.id === id);
  state.song = song;
  state.tracks = [];
  state.written = null;
  $("missing").hidden = !!(song && song.midi);
  $("score-box").hidden = !(song && song.crop_song);
  if (!song) return;
  await loadCrops(song);
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
    draw(0);
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
  $("upload-status").textContent = "대기열에 넣었습니다. 전사는 수분 걸릴 수 있습니다.";
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

function bind() {
  document.querySelectorAll(".tabs button").forEach((b) => {
    b.onclick = () => showTab(b.dataset.tab);
  });
  $("song").onchange = () => selectSong($("song").value);
  $("midi-kind").onchange = () => state.song && selectSong(state.song.id);
  $("play").onclick = () => { if (state.playing) pause(); else play(); };
  $("stop").onclick = stop;
  $("prev-bar").onclick = () => nudgeBar(-1);
  $("next-bar").onclick = () => nudgeBar(1);
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
  window.addEventListener("resize", () => draw(state.playing ? state.playhead : 0));
}

function nudgeBar(delta) {
  const song = state.song;
  if (!song || !song.play.length) return;
  let w = state.written || song.play[0];
  const i = song.play.indexOf(w);
  const j = Math.max(0, Math.min(song.play.length - 1, (i < 0 ? 0 : i) + delta));
  const barS = 240 / song.bpm;
  state.playhead = (song.t0 || 0) + j * barS + 0.05;
  showCrop(song.play[j]);
  draw(state.playhead);
}

bind();
refreshCatalog();
renderJobs();
showTab("view");
