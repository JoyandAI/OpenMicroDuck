(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  const stage = $("stage");
  const stream = $("stream");
  const toastEl = $("toast");

  let state = null;
  let toastTimer = 0;
  const positionChart = $("position-canvas");
  const positionCtx = positionChart ? positionChart.getContext("2d") : null;
  const positionTrace = { points: [], lastSim: null, range: 20, targetRange: 20 };
  let camTimer = 0;
  let pendingCamera = null;
  let drag = null;
  let recognition = null;
  let booted = false;

  const fmt = (value, digits = 1) => {
    const number = Number(value);
    if (!Number.isFinite(number)) return "—";
    return number.toFixed(digits);
  };

  const fmtTime = (seconds) => {
    const s = Math.max(0, Number(seconds) || 0);
    const m = Math.floor(s / 60);
    const rest = s - m * 60;
    return `${String(m).padStart(2, "0")}:${rest.toFixed(1).padStart(4, "0")}`;
  };

  const toast = (text) => {
    toastEl.textContent = text;
    toastEl.classList.add("show");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toastEl.classList.remove("show"), 2600);
  };

  async function api(path, payload) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  function addMessage(role, text) {
    const box = document.createElement("div");
    box.className = `message ${role}`;
    const label = document.createElement("span");
    label.className = "msg-label";
    label.textContent = role === "user" ? "你" : "小鸭";
    const p = document.createElement("p");
    p.textContent = text;
    box.append(label, p);
    $("messages").append(box);
    $("messages").scrollTop = $("messages").scrollHeight;
  }

  // A small strip-chart in the telemetry card.  The reference is a live
  // position scope rather than a one-shot progress bar, so keep a 4.2 s tail
  // of the simulator's X/Y position and draw a two-trace scope.
  function recordPosition(s) {
    const t = Number(s.time);
    const x = Number(s.x_mm);
    const y = Number(s.y_mm);
    if (![t, x, y].every(Number.isFinite)) return;

    if (positionTrace.lastSim !== null && t < positionTrace.lastSim - 0.05) {
      positionTrace.points.length = 0;
      positionTrace.range = 20;
      positionTrace.targetRange = 20;
    }
    positionTrace.lastSim = t;
    const last = positionTrace.points[positionTrace.points.length - 1];
    if (last && t <= last.t + 0.005) {
      last.x = x;
      last.y = y;
    } else {
      positionTrace.points.push({ t, x, y });
    }
    const cutoff = t - 4.2 - 0.25;
    while (positionTrace.points.length > 2 && positionTrace.points[0].t < cutoff) {
      positionTrace.points.shift();
    }
    let peak = 20;
    for (const point of positionTrace.points) peak = Math.max(peak, Math.abs(point.x), Math.abs(point.y));
    positionTrace.targetRange = Math.ceil(peak / 10) * 10;
    positionTrace.range += (positionTrace.targetRange - positionTrace.range) * 0.2;
    $("position-x").textContent = fmt(x, 1);
    $("position-y").textContent = fmt(y, 1);
    $("position-range").textContent = `±${Math.round(positionTrace.range)} mm`;
    drawPositionChart();
  }

  function drawPositionChart() {
    if (!positionCtx || !positionChart) return;
    const rect = positionChart.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const width = Math.round(rect.width);
    const height = Math.round(rect.height);
    if (positionChart.width !== Math.round(width * dpr) || positionChart.height !== Math.round(height * dpr)) {
      positionChart.width = Math.round(width * dpr);
      positionChart.height = Math.round(height * dpr);
    }
    const ctx = positionCtx;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const pad = 8;
    const top = 7;
    const bottom = height - 7;
    const plotW = width - pad * 2;
    const plotH = bottom - top;
    const lastT = positionTrace.lastSim ?? 0;
    const startT = lastT - 4.2;
    const xOf = (t) => pad + ((t - startT) / 4.2) * plotW;
    const yOf = (v) => top + plotH / 2 - (v / positionTrace.range) * (plotH / 2 - 2);

    // A quiet instrument grid: six columns, two rails and a brighter zero line.
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(230, 240, 235, 0.075)";
    for (let i = 1; i < 6; i += 1) {
      const x = pad + (plotW * i) / 6;
      ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, bottom); ctx.stroke();
    }
    ctx.beginPath(); ctx.moveTo(pad, top); ctx.lineTo(width - pad, top); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(pad, bottom); ctx.lineTo(width - pad, bottom); ctx.stroke();
    ctx.strokeStyle = "rgba(230, 240, 235, 0.16)";
    ctx.setLineDash([2, 4]);
    ctx.beginPath(); ctx.moveTo(pad, yOf(0)); ctx.lineTo(width - pad, yOf(0)); ctx.stroke();
    ctx.setLineDash([]);

    if (!positionTrace.points.length) return;
    const visible = positionTrace.points.filter((p) => p.t >= startT - 0.05);
    if (!visible.length) return;

    // Soft fill below X gives the scope depth without making the panel busy.
    const fill = ctx.createLinearGradient(0, top, 0, bottom);
    fill.addColorStop(0, "rgba(231, 143, 113, 0.22)");
    fill.addColorStop(1, "rgba(231, 143, 113, 0.00)");
    ctx.beginPath();
    visible.forEach((p, i) => {
      const x = xOf(p.t), y = yOf(p.x);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.lineTo(xOf(visible[visible.length - 1].t), bottom - 1);
    ctx.lineTo(xOf(visible[0].t), bottom - 1);
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();

    const strokeTrace = (key, color) => {
      ctx.beginPath();
      visible.forEach((p, i) => {
        const x = xOf(p.t), y = yOf(p[key]);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.35;
      ctx.shadowColor = color;
      ctx.shadowBlur = 6;
      ctx.stroke();
      ctx.shadowBlur = 0;
    };
    strokeTrace("y", "rgba(134, 200, 177, 0.86)");
    strokeTrace("x", "rgba(245, 164, 134, 0.96)");

    const end = visible[visible.length - 1];
    const ex = xOf(end.t), eyX = yOf(end.x), eyY = yOf(end.y);
    ctx.strokeStyle = "rgba(230, 240, 235, 0.18)";
    ctx.beginPath(); ctx.moveTo(ex, top); ctx.lineTo(ex, bottom); ctx.stroke();
    const dot = (x, y, color) => {
      ctx.fillStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 10;
      ctx.beginPath(); ctx.arc(x, y, 2.2, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = "rgba(255,255,255,.38)";
      ctx.lineWidth = 0.8;
      ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.stroke();
    };
    dot(ex, eyY, "#86c8b1");
    dot(ex, eyX, "#f5a486");
  }

  function updateSliderFill() {
    const slider = $("speed-slider");
    const min = Number(slider.min);
    const max = Number(slider.max);
    const value = Number(slider.value);
    const pct = max > min ? ((value - min) / (max - min)) * 100 : 0;
    slider.style.setProperty("--fill", `${pct}%`);
  }

  function updateUI(s) {
    state = s;
    const label = s.mode_label || s.mode;
    $("server-url").textContent = location.host || "127.0.0.1:18765";

    $("connection").textContent = "本地已连接";
    $("connection").classList.remove("offline");
    $("pulse").style.background = "";
    $("height").textContent = fmt(s.height_mm, 1);
    $("tilt").textContent = `${fmt(s.roll_deg, 1)} / ${fmt(s.pitch_deg, 1)}`;
    $("lateral").textContent = fmt(s.y_mm, 1);
    $("speed").textContent = fmt(s.cmd?.vx, 2);
    recordPosition(s);
    $("auto-reset").textContent = `AUTO RESET ${s.auto_reset_count || 0}`;
    $("run-status").textContent = s.paused ? "已暂停" : label;
    $("caption-mode").textContent = s.paused ? "已暂停" : label;
    $("caption-event").textContent = s.event || "拖动画面旋转，滚轮缩放";
    $("mode-pill").textContent = label;
    $("sim-time").textContent = fmtTime(s.time);
    $("timeline-fill").style.width = `${Math.min(100, ((s.mode_time || 0) % 5) * 20)}%`;

    const paused = Boolean(s.paused);
    $("pause-icon").textContent = paused ? "▶" : "Ⅱ";
    $("pause-button").setAttribute("aria-label", paused ? "继续播放" : "暂停");

    const standup = Boolean(s.standup);
    // The right-panel sitstand preset shows the sit/stand toggle label; the
    // duplicate console sit/stand buttons were removed.
    $("sitstand-label").textContent = standup ? "站起中…" : (s.sit ? "站起" : "坐下");
    $("head-value").textContent = `${fmt(s.head_yaw, 2)} rad`;
    $("speed-value").textContent = `${fmt(s.cmd?.vx, 2)} m/s`;
    if (document.activeElement !== $("speed-slider")) {
      $("speed-slider").value = String(s.cmd?.vx ?? 0.12);
      updateSliderFill();
    }

    $("fps").textContent = `${fmt(s.render_fps, 0)} FPS`;
    $("render-fps").textContent = `${fmt(s.render_fps, 1)} fps`;
    $("policy-count").textContent = `${(s.policies || []).length} / 6`;
    $("footer-time").textContent = new Date().toLocaleTimeString("zh-CN", { hour12: false });

    // Highlight + knob deck follow the user's selected action, not the policy
    // physically running.  A one-shot (kick/roulade/pick) ends back in stand,
    // but selection and its knobs stay put so params can keep being tuned.
    const selected = s.selected || s.mode;
    $$(".preset").forEach((button) => {
      const active = button.dataset.mode === selected;
      button.classList.toggle("active", active);
    });
    renderKnobDeck(selected);
    syncTune(s.tune);
  }

  function setOffline() {
    $("connection").textContent = "本地未连接";
    $("connection").classList.add("offline");
    $("pulse").style.background = "var(--accent)";
    $("run-status").textContent = "离线";
  }

  async function refreshState() {
    try {
      const response = await fetch("/api/state", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      updateUI(await response.json());
      if (!booted && state) {
        booted = true;
        applyActionLoad(state.selected || state.mode, false);  // restore the last-chosen source
      }
    } catch (error) {
      setOffline();
    }
  }

  async function setMode(mode) {
    try {
      const payload = { mode };
      if (mode === "sitstand") payload.sit = !(state && state.sit);
      const result = await api("/api/mode", payload);
      if (result.state) updateUI(result.state);
      // Restore the source the user last loaded for this action (recommended /
      // custom saved / deploy), instead of always forcing recommended.
      applyActionLoad(mode, true);
      if (mode === "walk") {
        const vx = Number($("tune-vx").value) || 0.16;
        $("speed-slider").value = String(vx);
        updateSliderFill();
        await api("/api/twist", { vx, vy: 0, wz: 0 });
      }
      if (result.event) addMessage("assistant", result.event);
    } catch (error) {
      toast("策略切换失败，请检查后端");
    }
  }

  async function togglePause() {
    try {
      const paused = !(state && state.paused);
      const result = await api("/api/pause", { paused });
      if (result.state) updateUI(result.state);
    } catch (error) {
      toast("暂停失败");
    }
  }

  async function resetSim(announce = true) {
    try {
      // keep_mode defaults true on the server: clear the pose but stay in the
      // current action instead of snapping back to a stand.
      const result = await api("/api/reset", {});
      if (result.state) updateUI(result.state);
      if (announce) {
        const label = (result.state && (result.state.mode_label || result.state.mode)) || "当前动作";
        addMessage("assistant", `已重置姿态，保持在「${label}」。`);
      }
    } catch (error) {
      toast("重置失败");
    }
  }

  async function sendCamera(camera) {
    pendingCamera = camera;
    if (camTimer) return;
    camTimer = window.setTimeout(async () => {
      const value = pendingCamera;
      pendingCamera = null;
      camTimer = 0;
      if (!value) return;
      try {
        const result = await api("/api/camera", value);
        if (result.state && state) {
          state.camera = result.state.camera;
        }
      } catch (error) {
        // Camera is non-critical; don't nag the user.
      }
    }, 55);
  }

  // Mode presets and buttons -------------------------------------------------
  $$("[data-mode]").forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
  });
  $("pause-button").addEventListener("click", togglePause);
  $("reset-button").addEventListener("click", () => resetSim(true));
  $("reset-camera").addEventListener("click", async () => {
    try {
      await api("/api/camera/reset", {});
      toast("视角已复位");
    } catch (error) {
      toast("视角复位失败");
    }
  });

  // 坐下 / 站起 live on the right-panel sitstand preset now; the duplicate
  // console buttons were removed.
  $("walk-button").addEventListener("click", () => setMode("walk"));
  $("stop-button").addEventListener("click", async () => {
    try {
      await api("/api/twist", { vx: 0, vy: 0, wz: 0 });
      await setMode("stand");
    } catch (error) {
      toast("停止失败");
    }
  });

  $$("[data-head]").forEach((button) => {
    button.addEventListener("click", async () => {
      const yaw = Number(button.dataset.head);
      try {
        const result = await api("/api/head", { yaw });
        if (result.state) updateUI(result.state);
      } catch (error) {
        toast("头部控制失败");
      }
    });
  });

  $("speed-slider").addEventListener("input", () => {
    updateSliderFill();
    const vx = Number($("speed-slider").value);
    $("speed-value").textContent = `${vx.toFixed(2)} m/s`;
    api("/api/twist", { vx }).then((result) => {
      if (result.state) updateUI(result.state);
    }).catch(() => {});
  });

  // Lab tuning (no-retrain motion knobs) ------------------------------------
  const fillSlider = (el) => {
    if (!el) return;
    const min = Number(el.min), max = Number(el.max), value = Number(el.value);
    el.style.setProperty("--fill", `${max > min ? ((value - min) / (max - min)) * 100 : 0}%`);
  };
  // id -> {key: server field, fmt: value-label formatter}
  const TUNE_SPEC = [
    { id: "tune-legs", key: "legs_lowpass", fmt: (v) => v.toFixed(2) },
    { id: "tune-head", key: "head_lowpass", fmt: (v) => v.toFixed(2) },
    { id: "tune-walk-scale", key: "walk_scale", fmt: (v) => v.toFixed(2) },
    { id: "tune-kick-scale", key: "kick_scale", fmt: (v) => v.toFixed(2) },
    { id: "tune-roulade-scale", key: "roulade_scale", fmt: (v) => v.toFixed(2) },
    { id: "tune-vx", key: "walk_default_vx", fmt: (v) => `${v.toFixed(2)} m/s` },
    { id: "tune-kick", key: "kick_duration", fmt: (v) => `${v.toFixed(2)} s` },
    { id: "tune-roulade", key: "roulade_duration", fmt: (v) => `${v.toFixed(2)} s` },
    { id: "tune-roulade-prep", key: "roulade_prep", fmt: (v) => `${v.toFixed(2)} s` },
    { id: "tune-standup", key: "standup_handoff", fmt: (v) => `${v.toFixed(2)} s` },
    { id: "tune-sitnudge", key: "sit_nudge", fmt: (v) => `${v.toFixed(2)} s` },
    { id: "tune-groundpick", key: "ground_pick_duration", fmt: (v) => v.toFixed(2) },
    { id: "tune-falltilt", key: "fall_tilt", fmt: (v) => `${v.toFixed(2)} rad` },
    { id: "tune-fallheight", key: "fall_height", fmt: (v) => `${v.toFixed(3)} m` },
    { id: "tune-fallgrace", key: "fall_grace", fmt: (v) => `${v.toFixed(1)} s` },
    { id: "tune-renderfps", key: "render_fps", fmt: (v) => `${v.toFixed(0)} fps` },
    { id: "tune-quality", key: "jpeg_quality", fmt: (v) => v.toFixed(0) },
  ];
  const TUNE_IDS = TUNE_SPEC.map((s) => s.id);
  const labelTune = () => {
    TUNE_SPEC.forEach((s) => {
      const el = $(s.id), out = $(`${s.id}-value`);
      if (!el || !out) return;
      out.textContent = s.fmt(Number(el.value));
      fillSlider(el);
    });
  };
  const postTune = (patch) => {
    api("/api/tune", patch).then((result) => {
      if (result.state) updateUI(result.state);
    }).catch(() => toast("调参未生效，请检查后端"));
  };
  const tuneFromControls = () => {
    const patch = { smooth_skills: $("tune-smooth-skills").checked };
    TUNE_SPEC.forEach((s) => { patch[s.key] = Number($(s.id).value); });
    postTune(patch);
  };
  TUNE_SPEC.forEach((s) => {
    $(s.id).addEventListener("input", () => { labelTune(); tuneFromControls(); });
  });
  $("tune-smooth-skills").addEventListener("change", tuneFromControls);

  // Per-action recommended presets --------------------------------------
  // Each action carries its own sensible starting values plus the subset of
  // knobs worth exposing for it, so selecting an action loads good defaults
  // instead of making the user hunt for numbers.  Values are heuristic
  // starting points tuned toward the known complaints (walk too mechanical,
  // kick/roulade not crisp), not a verified optimum.
  const ACTION_TUNE = {
    walk: {
      label: "行走",
      knobs: ["tune-walk-scale", "tune-legs", "tune-head"],
      preset: { walk_scale: 0.80, walk_default_vx: 0.16, legs_lowpass: 0.45, head_lowpass: 0.40, smooth_skills: false },
    },
    stand: {
      label: "站立",
      knobs: ["tune-legs", "tune-head"],
      preset: { legs_lowpass: 0.50, head_lowpass: 0.40 },
    },
    sitstand: {
      label: "坐 / 站",
      knobs: ["tune-standup", "tune-sitnudge", "tune-legs"],
      preset: { standup_handoff: 0.40, sit_nudge: 0.12, legs_lowpass: 0.50 },
    },
    ground_pick: {
      label: "捡东西",
      knobs: ["tune-groundpick", "tune-legs"],
      preset: { ground_pick_duration: 0.70, legs_lowpass: 0.50 },
    },
    kick_right: {
      label: "右踢",
      knobs: ["tune-kick-scale", "tune-kick"],
      preset: { kick_scale: 0.70, kick_duration: 0.42, smooth_skills: false },
    },
    roulade: {
      label: "前滚翻",
      knobs: ["tune-roulade-scale", "tune-roulade", "tune-roulade-prep"],
      preset: { roulade_scale: 1.00, roulade_duration: 3.00, roulade_prep: 1.02, smooth_skills: false },
    },
  };
  // server tune-field -> slider id, so a preset patch also moves the sliders.
  const KEY_TO_ID = {};
  TUNE_SPEC.forEach((s) => { KEY_TO_ID[s.key] = s.id; });

  let currentMode = "stand";

  // Reflect which action is active: label + show only its knobs (compact view).
  function renderKnobDeck(mode) {
    const cfg = ACTION_TUNE[mode];
    currentMode = mode;
    $("console-action").textContent = cfg ? cfg.label : (mode || "—");
    const active = new Set(cfg ? cfg.knobs : []);
    $$("#knob-deck .knob").forEach((el) => {
      el.classList.toggle("knob-active", active.has(el.dataset.knob));
    });
    $("console").classList.toggle("no-knobs", active.size === 0);
    const text = $("knobs-caption-text");
    if (text) text.textContent = cfg ? `${cfg.label} · 该动作调参` : "该动作调参";
    // Preset slot is per-action: refresh the bar for the new current mode.
    if (typeof renderPresetBar === "function") renderPresetBar();
  }

  // Load an action's recommended values (moves sliders + pushes to backend).
  function applyActionPreset(mode, announce) {
    const cfg = ACTION_TUNE[mode];
    if (!cfg) return;
    Object.entries(cfg.preset).forEach(([key, value]) => {
      if (key === "smooth_skills") { $("tune-smooth-skills").checked = Boolean(value); return; }
      const id = KEY_TO_ID[key];
      if (id && $(id)) $(id).value = String(value);
    });
    labelTune();
    tuneFromControls();
    if (announce) {
      const note = $("console-note");
      note.classList.remove("flash");
      void note.offsetWidth;
      note.classList.add("flash");
    }
  }

  // Per-action load intent --------------------------------------------------
  // Remember, per action, which source the user last loaded: the recommended
  // preset, their custom saved slot, or the board deploy defaults.  Switching
  // actions then restores that choice instead of always forcing recommended.
  const loadModeKey = (mode) => `omd.motionlab.loadmode.v1.${mode || currentMode}`;
  const readLoadMode = (mode) => {
    try {
      const v = localStorage.getItem(loadModeKey(mode));
      if (v === "custom" || v === "deploy" || v === "recommended") return v;
    } catch (error) { /* fall through */ }
    return "recommended";
  };
  const writeLoadMode = (mode, value) => {
    try { localStorage.setItem(loadModeKey(mode || currentMode), value); } catch (error) { /* ignore */ }
    if (typeof renderPresetBar === "function") renderPresetBar();
  };

  // Load the source the user last chose for this action. Falls back to the
  // recommended preset when custom/deploy are unavailable.
  function applyActionLoad(mode, announce) {
    const intent = readLoadMode(mode);
    if (intent === "custom") {
      const p = readPreset(mode);
      if (p) { applyPreset(p); return; }
    } else if (intent === "deploy") {
      if (state && state.tune && state.tune.deploy) { applyDeploy(); return; }
    }
    applyActionPreset(mode, announce);
  }

  // Expand / collapse the full parameter grid.
  $("console-expand").addEventListener("click", () => {
    const expanded = $("console").classList.toggle("expanded");
    $("console-expand").setAttribute("aria-expanded", String(expanded));
    $("console-expand").textContent = expanded ? "收起 ◂" : "展开全部参数 ▸";
  });

  // "恢复本动作推荐值" — reload the current action's recommended preset.
  $("tune-reset").addEventListener("click", () => {
    applyActionPreset(currentMode, true);
    writeLoadMode(currentMode, "recommended");
    toast(`已恢复「${(ACTION_TUNE[currentMode] || {}).label || currentMode}」推荐值`);
  });

  // Advanced: restore every knob to the board deploy value.
  $("tune-reset-deploy").addEventListener("click", () => {
    const t = state && state.tune && state.tune.deploy;
    TUNE_SPEC.forEach((s) => {
      if (t && t[s.key] != null) $(s.id).value = String(t[s.key]);
    });
    $("tune-smooth-skills").checked = t ? Boolean(t.smooth_skills) : false;
    labelTune();
    tuneFromControls();
    writeLoadMode(currentMode, "deploy");
    toast("已恢复全部部署值");
  });

  // Single-slot preset (localStorage) --------------------------------------
  // Three buttons: save the current params into one slot, load them back, or
  // load the board deploy defaults. No names, no list, no delete.
  // One saved slot per action, so each动作的 save/load 互相独立.
  const presetKey = (mode) => `omd.motionlab.preset.v4.${mode || currentMode}`;
  const capturePreset = () => {
    const p = { smooth_skills: $("tune-smooth-skills").checked, saved_at: Date.now() };
    TUNE_SPEC.forEach((s) => { p[s.key] = Number($(s.id).value); });
    return p;
  };
  const applyPreset = (p) => {
    if (!p) return;
    TUNE_SPEC.forEach((s) => {
      if (p[s.key] != null && $(s.id)) $(s.id).value = String(p[s.key]);
    });
    $("tune-smooth-skills").checked = Boolean(p.smooth_skills);
    labelTune();
    tuneFromControls();
  };
  const readPreset = (mode) => {
    try {
      const p = JSON.parse(localStorage.getItem(presetKey(mode)) || "null");
      if (p && typeof p === "object") return p;
    } catch (error) { /* fall through */ }
    return null;
  };
  // Load the board deploy values (the "默认载入" button).
  const applyDeploy = () => {
    const t = state && state.tune && state.tune.deploy;
    TUNE_SPEC.forEach((s) => {
      if (t && t[s.key] != null) $(s.id).value = String(t[s.key]);
    });
    $("tune-smooth-skills").checked = t ? Boolean(t.smooth_skills) : false;
    labelTune();
    tuneFromControls();
  };
  const renderPresetBar = () => {
    const p = readPreset();
    $("preset-load").disabled = !p;
    const label = (ACTION_TUNE[currentMode] || {}).label || currentMode;
    const eyebrow = $("preset-eyebrow");
    if (eyebrow) eyebrow.textContent = `我的预设 · ${label}`;
    const hint = $("preset-hint");
    if (hint) {
      const when = p && p.saved_at ? new Date(p.saved_at).toLocaleString("zh-CN", { hour12: false }) : "";
      const intent = readLoadMode();
      const source = intent === "custom" ? "自定义" : intent === "deploy" ? "默认" : "推荐";
      const saved = p ? `已存：${when}` : "尚未保存";
      hint.textContent = `当前：${source}｜${saved}`;
    }
  };

  $("preset-save").addEventListener("click", () => {
    try {
      localStorage.setItem(presetKey(), JSON.stringify(capturePreset()));
    } catch (error) { toast("保存失败（浏览器存储不可用）"); return; }
    writeLoadMode(currentMode, "custom");
    renderPresetBar();
    toast(`已保存「${(ACTION_TUNE[currentMode] || {}).label || currentMode}」参数`);
  });

  $("preset-load").addEventListener("click", () => {
    const p = readPreset();
    if (!p) { toast("该动作还没有保存过参数"); return; }
    applyPreset(p);
    writeLoadMode(currentMode, "custom");
    const when = p.saved_at ? new Date(p.saved_at).toLocaleString("zh-CN", { hour12: false }) : "";
    toast(when ? `已载入「${(ACTION_TUNE[currentMode] || {}).label || currentMode}」保存值（${when}）` : "已载入保存值");
  });

  $("preset-default").addEventListener("click", () => {
    applyDeploy();
    writeLoadMode(currentMode, "deploy");
    toast("已载入默认参数");
  });

  renderPresetBar();

  // Info "!" tooltips: tap to toggle (hover/focus handled by CSS).
  document.querySelectorAll(".info").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const open = btn.classList.contains("info-open");
      document.querySelectorAll(".info-open").forEach((o) => o.classList.remove("info-open"));
      if (!open) btn.classList.add("info-open");
    });
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest || !e.target.closest(".info")) {
      document.querySelectorAll(".info-open").forEach((o) => o.classList.remove("info-open"));
    }
  });

  // Keep the tuning controls in sync unless the user is dragging one.
  function syncTune(t) {
    if (!t) return;
    const active = document.activeElement;
    const touching = active && (TUNE_IDS.includes(active.id) || active.id === "tune-smooth-skills");
    if (touching) return;
    TUNE_SPEC.forEach((s) => {
      if (t[s.key] != null) $(s.id).value = String(t[s.key]);
    });
    $("tune-smooth-skills").checked = Boolean(t.smooth_skills);
    labelTune();
  }

  // Chat -------------------------------------------------------------------
  async function sendChat(text) {
    const value = (text || "").trim();
    if (!value) return;
    addMessage("user", value);
    $("chat-input").value = "";
    try {
      const result = await api("/api/chat", { text: value });
      addMessage("assistant", result.reply || "已收到。");
      if (result.state) updateUI(result.state);
    } catch (error) {
      addMessage("assistant", "本地服务没有响应。检查 motion-lab/server.py 是否在运行。");
      setOffline();
    }
  }

  $("chat-form").addEventListener("submit", (event) => {
    event.preventDefault();
    sendChat($("chat-input").value);
  });
  $$("[data-chat]").forEach((button) => {
    button.addEventListener("click", () => sendChat(button.dataset.chat));
  });

  // Optional browser speech recognition.  No audio is uploaded by this app.
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = "zh-CN";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onstart = () => {
      $("mic-button").classList.add("recording");
      $("mic-label").textContent = "正在听…";
    };
    recognition.onend = () => {
      $("mic-button").classList.remove("recording");
      $("mic-label").textContent = "开始录音";
    };
    recognition.onerror = () => {
      $("mic-button").classList.remove("recording");
      $("mic-label").textContent = "开始录音";
      toast("没有识别到语音，可以直接输入文字");
    };
    recognition.onresult = (event) => {
      const text = event.results?.[0]?.[0]?.transcript || "";
      if (text) sendChat(text);
    };
    $("mic-button").addEventListener("click", () => {
      if ($("mic-button").classList.contains("recording")) {
        recognition.stop();
      } else {
        try {
          recognition.start();
        } catch (error) {
          toast("语音识别启动失败");
        }
      }
    });
  } else {
    $("mic-button").addEventListener("click", () => toast("这个浏览器不支持语音输入，请直接输入文字"));
  }

  // Camera orbit / zoom -----------------------------------------------------
  stage.addEventListener("pointerdown", (event) => {
    if (event.target.closest("button")) return;
    if (!state?.camera) return;
    drag = {
      x: event.clientX,
      y: event.clientY,
      azimuth: state.camera.azimuth,
      elevation: state.camera.elevation,
    };
    stage.setPointerCapture?.(event.pointerId);
  });

  stage.addEventListener("pointermove", (event) => {
    if (!drag) return;
    const azimuth = drag.azimuth - (event.clientX - drag.x) * 0.34;
    const elevation = drag.elevation + (event.clientY - drag.y) * 0.26;
    if (state?.camera) {
      state.camera.azimuth = Math.max(-180, Math.min(180, azimuth));
      state.camera.elevation = Math.max(-89, Math.min(89, elevation));
    }
    sendCamera({
      azimuth: Math.max(-180, Math.min(180, azimuth)),
      elevation: Math.max(-89, Math.min(89, elevation)),
    });
  });

  const endDrag = () => { drag = null; };
  stage.addEventListener("pointerup", endDrag);
  stage.addEventListener("pointercancel", endDrag);
  stage.addEventListener("pointerleave", (event) => {
    if (event.buttons === 0) endDrag();
  });

  stage.addEventListener("wheel", (event) => {
    if (!state?.camera) return;
    event.preventDefault();
    const distance = Math.max(0.28, Math.min(1.4, state.camera.distance * Math.exp(event.deltaY * 0.0012)));
    state.camera.distance = distance;
    sendCamera({ distance });
  }, { passive: false });

  stream.addEventListener("load", () => {
    stream.dataset.loaded = `${stream.naturalWidth}x${stream.naturalHeight}`;
  });
  stream.addEventListener("error", () => setOffline());

  // Keyboard ----------------------------------------------------------------
  document.addEventListener("keydown", (event) => {
    const tag = (event.target.tagName || "").toLowerCase();
    if (["input", "textarea", "button", "a", "select"].includes(tag)) return;
    if (event.code === "Space") {
      event.preventDefault();
      togglePause();
    } else if (event.key === "r" || event.key === "R") {
      resetSim(true);
    } else if (["1", "2", "3", "4", "5", "6"].includes(event.key)) {
      const order = ["walk", "stand", "sitstand", "ground_pick", "kick_right", "roulade"];
      setMode(order[Number(event.key) - 1]);
    }
  });

  // Boot --------------------------------------------------------------------
  $("server-url").textContent = location.host || "127.0.0.1:18765";
  if (stream.dataset.stream) {
    window.setTimeout(() => { stream.src = stream.dataset.stream; }, 350);
  }
  updateSliderFill();
  labelTune();
  refreshState();
  window.setInterval(refreshState, 150);
  window.addEventListener("resize", drawPositionChart);
})();
