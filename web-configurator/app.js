/**
 * Pico MacroPad Web Configurator
 * Full Web Serial integration, 3-mode rotary sync, mechanical keycap rendering, and modal editor
 */

// Available Keys for Selection
const AVAILABLE_KEYS = [
  // Letters
  "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
  "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
  // Numbers
  "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
  // Function Keys
  "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
  // Common Controls
  "ENTER", "ESCAPE", "SPACE", "TAB", "BACKSPACE", "DELETE",
  // Navigation
  "UP_ARROW", "DOWN_ARROW", "LEFT_ARROW", "RIGHT_ARROW",
  "HOME", "END", "PAGE_UP", "PAGE_DOWN",
  // Special
  "PRINT_SCREEN", "INSERT", "PAUSE"
];

const BUTTON_PINS_MAP = ["GP2", "GP3", "GP4", "GP5"];

// Default 3-Mode Configuration
const DEFAULT_CONFIG = {
  mode1: {
    name: "Dev & Code",
    buttons: [
      { type: "combo", modifiers: ["CTRL"], key: "C", label: "Copy" },
      { type: "combo", modifiers: ["CTRL"], key: "V", label: "Paste" },
      { type: "combo", modifiers: ["CTRL"], key: "Z", label: "Undo" },
      { type: "combo", modifiers: ["CTRL", "SHIFT"], key: "P", label: "Cmd Pal" }
    ]
  },
  mode2: {
    name: "Media & Audio",
    buttons: [
      { type: "media", action: "MUTE", label: "Mute" },
      { type: "media", action: "VOLUME_DOWN", label: "Vol -" },
      { type: "media", action: "VOLUME_UP", label: "Vol +" },
      { type: "media", action: "PLAY_PAUSE", label: "Play/Pause" }
    ]
  },
  mode3: {
    name: "Quick Tools",
    buttons: [
      { type: "combo", modifiers: ["GUI", "SHIFT"], key: "S", label: "Snip" },
      { type: "combo", modifiers: ["ALT"], key: "TAB", label: "Switch App" },
      { type: "string", text: "git status\n", label: "Git Status" },
      { type: "combo", modifiers: ["GUI"], key: "L", label: "Lock PC" }
    ]
  }
};

// Preset configurations
const PRESETS = {
  coding: {
    name: "Coding Preset",
    buttons: [
      { type: "combo", modifiers: ["CTRL"], key: "C", label: "Copy" },
      { type: "combo", modifiers: ["CTRL"], key: "V", label: "Paste" },
      { type: "combo", modifiers: ["CTRL"], key: "Z", label: "Undo" },
      { type: "combo", modifiers: ["CTRL", "SHIFT"], key: "P", label: "VS Code Pal" }
    ]
  },
  media: {
    name: "Media Preset",
    buttons: [
      { type: "media", action: "MUTE", label: "Mute Mic/Audio" },
      { type: "media", action: "VOLUME_DOWN", label: "Volume Down" },
      { type: "media", action: "VOLUME_UP", label: "Volume Up" },
      { type: "media", action: "PLAY_PAUSE", label: "Play / Pause" }
    ]
  },
  streaming: {
    name: "Stream & Utility",
    buttons: [
      { type: "combo", modifiers: ["GUI", "SHIFT"], key: "S", label: "Screenshot" },
      { type: "combo", modifiers: ["ALT"], key: "TAB", label: "App Switch" },
      { type: "string", text: "clear\n", label: "Clear Term" },
      { type: "combo", modifiers: ["GUI"], key: "L", label: "Lock Screen" }
    ]
  }
};

// App State
let currentMode = 1;
let currentConfig = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
let serialPort = null;
let serialReader = null;
let serialWriter = null;
let keepReading = false;
let editingButtonIndex = null;
let selectedMediaType = "MUTE";

// DOM Elements
const btnConnect = document.getElementById("btnConnect");
const btnConnectText = document.getElementById("btnConnectText");
const connectionStatus = document.getElementById("connectionStatus");
const btnSaveToPico = document.getElementById("btnSaveToPico");
const btnLoadFromPico = document.getElementById("btnLoadFromPico");
const logStream = document.getElementById("logStream");
const btnClearLog = document.getElementById("btnClearLog");
const keysGrid = document.getElementById("keysGrid");
const currentModeDisplayTitle = document.getElementById("currentModeDisplayTitle");

// LED dots
const ledGreen = document.getElementById("ledGreen");
const ledBlue = document.getElementById("ledBlue");
const ledRed = document.getElementById("ledRed");

// Modal Elements
const editModal = document.getElementById("editModal");
const modalCloseBtn = document.getElementById("modalCloseBtn");
const modalCancelBtn = document.getElementById("modalCancelBtn");
const modalApplyBtn = document.getElementById("modalApplyBtn");
const modalKeyTitle = document.getElementById("modalKeyTitle");
const modalKeySubtitle = document.getElementById("modalKeySubtitle");
const keyLabelInput = document.getElementById("keyLabelInput");
const actionTypeBtns = document.querySelectorAll(".action-type-btn");

const paneCombo = document.getElementById("paneCombo");
const paneSingle = document.getElementById("paneSingle");
const paneMedia = document.getElementById("paneMedia");
const paneString = document.getElementById("paneString");

const modCtrl = document.getElementById("modCtrl");
const modShift = document.getElementById("modShift");
const modAlt = document.getElementById("modAlt");
const modGui = document.getElementById("modGui");
const comboKeySelect = document.getElementById("comboKeySelect");
const comboPreviewText = document.getElementById("comboPreviewText");
const singleKeySelect = document.getElementById("singleKeySelect");
const stringTextInput = document.getElementById("stringTextInput");

// Presets
const btnPresets = document.getElementById("btnPresets");
const presetMenu = document.getElementById("presetMenu");

// ==============================================================================
// 1. INITIALIZATION & DROPDOWN POPULATION
// ==============================================================================

function populateKeyDropdowns() {
  AVAILABLE_KEYS.forEach(k => {
    const opt1 = document.createElement("option");
    opt1.value = k;
    opt1.textContent = k;
    comboKeySelect.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = k;
    opt2.textContent = k;
    singleKeySelect.appendChild(opt2);
  });
  comboKeySelect.value = "C";
  singleKeySelect.value = "ENTER";
}

function updateComboPreview() {
  const mods = [];
  if (modCtrl.checked) mods.push("Ctrl");
  if (modShift.checked) mods.push("Shift");
  if (modAlt.checked) mods.push("Alt");
  if (modGui.checked) mods.push("Win/Cmd");
  const key = comboKeySelect.value;
  comboPreviewText.textContent = mods.length ? `${mods.join(" + ")} + ${key}` : key;
}

[modCtrl, modShift, modAlt, modGui, comboKeySelect].forEach(el => {
  el.addEventListener("change", updateComboPreview);
});

// ==============================================================================
// 2. LOGGING & TELEMETRY
// ==============================================================================

function log(text, type = "system") {
  const entry = document.createElement("div");
  entry.className = `log-entry ${type}`;
  const time = new Date().toLocaleTimeString();
  entry.textContent = `[${time}] ${text}`;
  logStream.appendChild(entry);
  logStream.scrollTop = logStream.scrollHeight;
}

btnClearLog.addEventListener("click", () => {
  logStream.innerHTML = "";
  log("Telemetry cleared.", "system");
});

function updateModeTabLabels() {
  [1, 2, 3].forEach(m => {
    const modeKey = `mode${m}`;
    const modeData = currentConfig[modeKey];
    if (modeData && modeData.name) {
      const tab = document.getElementById(`tabMode${m}`);
      if (tab) {
        const titleEl = tab.querySelector(".tab-title");
        if (titleEl) titleEl.textContent = modeData.name;
      }
    }
  });
}

function setMode(modeNum, triggeredByHardware = false) {
  currentMode = modeNum;

  // Update tab labels
  updateModeTabLabels();

  // Update tabs
  document.querySelectorAll(".mode-tab").forEach(tab => {
    tab.classList.toggle("active", parseInt(tab.dataset.mode) === modeNum);
  });

  // Update hardware LEDs indicator
  ledGreen.classList.toggle("active", modeNum === 1);
  ledBlue.classList.toggle("active", modeNum === 2);
  ledRed.classList.toggle("active", modeNum === 3);

  // Update body theme class
  document.body.className = `theme-mode-${modeNum}`;

  const modeData = currentConfig[`mode${modeNum}`] || { name: `Mode ${modeNum}` };
  currentModeDisplayTitle.textContent = `Mode ${modeNum}: ${modeData.name}`;

  renderKeypad();

  if (triggeredByHardware) {
    log(`[HARDWARE] Rotary selector turned to Mode ${modeNum} (${modeData.name})`, "incoming");
  }
}

function renderKeypad() {
  keysGrid.innerHTML = "";
  const modeData = currentConfig[`mode${currentMode}`] || { buttons: [] };
  const buttons = modeData.buttons || [];

  buttons.forEach((btn, index) => {
    const slot = document.createElement("div");
    slot.className = "keycap-slot";

    const keycap = document.createElement("div");
    keycap.className = "keycap";
    keycap.id = `keycap-${index}`;

    // Header with index and physical GPIO pin
    const header = document.createElement("div");
    header.className = "keycap-header";
    header.innerHTML = `
      <span class="key-index">KEY ${index + 1}</span>
      <span class="key-gpio">${BUTTON_PINS_MAP[index] || "GPIO"}</span>
    `;

    // Key label
    const label = document.createElement("div");
    label.className = "key-label";
    label.textContent = btn.label || `Button ${index + 1}`;

    // Action badge
    const badge = document.createElement("div");
    badge.className = "key-action-badge";
    badge.textContent = formatActionSummary(btn);

    keycap.appendChild(header);
    keycap.appendChild(label);
    keycap.appendChild(badge);

    keycap.addEventListener("click", () => openEditModal(index));
    slot.appendChild(keycap);
    keysGrid.appendChild(slot);
  });
}

function formatActionSummary(btn) {
  if (btn.type === "combo") {
    const mods = btn.modifiers || [];
    return `${mods.join("+")}+${btn.key}`;
  } else if (btn.type === "single") {
    return btn.key;
  } else if (btn.type === "media") {
    return `Media: ${btn.action}`;
  } else if (btn.type === "string") {
    return `Text: "${(btn.text || "").replace("\n", "⏎")}"`;
  }
  return "Disabled";
}

// Mode tab clicks
document.querySelectorAll(".mode-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    const mode = parseInt(tab.dataset.mode);
    setMode(mode, false);
  });
});

// Flash key on screen when physical button pressed
function flashKeypressOnScreen(buttonId) {
  const el = document.getElementById(`keycap-${buttonId}`);
  if (el) {
    el.classList.add("key-pressed");
    setTimeout(() => {
      el.classList.remove("key-pressed");
    }, 150);
  }
}

// ==============================================================================
// 4. MODAL ACTION EDITOR
// ==============================================================================

function openEditModal(index) {
  editingButtonIndex = index;
  const modeData = currentConfig[`mode${currentMode}`];
  const btn = modeData.buttons[index] || { type: "single", key: "A", label: "" };

  modalKeyTitle.textContent = `Edit Button ${index + 1} (${BUTTON_PINS_MAP[index]})`;
  modalKeySubtitle.textContent = `Layer: Mode ${currentMode} - ${modeData.name}`;
  keyLabelInput.value = btn.label || "";

  // Set action type tab
  selectActionType(btn.type || "combo");

  if (btn.type === "combo") {
    const mods = btn.modifiers || [];
    modCtrl.checked = mods.includes("CTRL");
    modShift.checked = mods.includes("SHIFT");
    modAlt.checked = mods.includes("ALT");
    modGui.checked = mods.includes("GUI") || mods.includes("CMD") || mods.includes("WIN");
    comboKeySelect.value = btn.key || "C";
    updateComboPreview();
  } else if (btn.type === "single") {
    singleKeySelect.value = btn.key || "ENTER";
  } else if (btn.type === "media") {
    selectedMediaType = btn.action || "MUTE";
    updateMediaSelection();
  } else if (btn.type === "string") {
    stringTextInput.value = btn.text || "";
  }

  editModal.classList.remove("hidden");
}

function closeEditModal() {
  editModal.classList.add("hidden");
  editingButtonIndex = null;
}

function selectActionType(type) {
  actionTypeBtns.forEach(btn => {
    btn.classList.toggle("active", btn.dataset.type === type);
  });

  paneCombo.classList.toggle("hidden", type !== "combo");
  paneSingle.classList.toggle("hidden", type !== "single");
  paneMedia.classList.toggle("hidden", type !== "media");
  paneString.classList.toggle("hidden", type !== "string");
}

actionTypeBtns.forEach(btn => {
  btn.addEventListener("click", () => selectActionType(btn.dataset.type));
});

// Media options
document.querySelectorAll(".media-option").forEach(btn => {
  btn.addEventListener("click", () => {
    selectedMediaType = btn.dataset.media;
    updateMediaSelection();
  });
});

function updateMediaSelection() {
  document.querySelectorAll(".media-option").forEach(btn => {
    btn.classList.toggle("selected", btn.dataset.media === selectedMediaType);
  });
}

modalCloseBtn.addEventListener("click", closeEditModal);
modalCancelBtn.addEventListener("click", closeEditModal);

modalApplyBtn.addEventListener("click", () => {
  if (editingButtonIndex === null) return;

  const activeTypeBtn = document.querySelector(".action-type-btn.active");
  const type = activeTypeBtn ? activeTypeBtn.dataset.type : "single";
  const label = keyLabelInput.value.trim() || `Button ${editingButtonIndex + 1}`;

  let actionDef = { label, type };

  if (type === "combo") {
    const modifiers = [];
    if (modCtrl.checked) modifiers.push("CTRL");
    if (modShift.checked) modifiers.push("SHIFT");
    if (modAlt.checked) modifiers.push("ALT");
    if (modGui.checked) modifiers.push("GUI");
    actionDef.modifiers = modifiers;
    actionDef.key = comboKeySelect.value;
  } else if (type === "single") {
    actionDef.key = singleKeySelect.value;
  } else if (type === "media") {
    actionDef.action = selectedMediaType;
  } else if (type === "string") {
    actionDef.text = stringTextInput.value;
  }

  currentConfig[`mode${currentMode}`].buttons[editingButtonIndex] = actionDef;
  renderKeypad();
  closeEditModal();
  log(`Updated Button ${editingButtonIndex + 1} (${label}) in Mode ${currentMode}`, "system");
});

// ==============================================================================
// 5. PRESETS
// ==============================================================================

btnPresets.addEventListener("click", (e) => {
  e.stopPropagation();
  presetMenu.classList.toggle("hidden");
});

document.addEventListener("click", () => {
  presetMenu.classList.add("hidden");
});

document.querySelectorAll(".preset-item").forEach(item => {
  item.addEventListener("click", () => {
    const presetKey = item.dataset.preset;
    if (PRESETS[presetKey]) {
      currentConfig[`mode${currentMode}`].buttons = JSON.parse(JSON.stringify(PRESETS[presetKey].buttons));
      currentConfig[`mode${currentMode}`].name = PRESETS[presetKey].name;
      updateModeTabLabels();
      currentModeDisplayTitle.textContent = `Mode ${currentMode}: ${PRESETS[presetKey].name}`;
      renderKeypad();
      log(`Applied preset "${PRESETS[presetKey].name}" to Mode ${currentMode}`, "system");
    }
  });
});

// ==============================================================================
// 6. WEB SERIAL API INTEGRATION
// ==============================================================================

async function connectSerial() {
  if (!("serial" in navigator)) {
    alert("Web Serial API is not supported in this browser. Please use Google Chrome, Microsoft Edge, Brave, or Opera.");
    return;
  }

  try {
    log("Requesting USB Serial device access...", "system");
    serialPort = await navigator.serial.requestPort();
    await serialPort.open({ baudRate: 115200 });

    keepReading = true;
    updateConnectionUI(true);
    log("Connected to Pico MacroPad over USB CDC Serial (115200 baud).", "incoming");

    // Setup writer
    const textEncoder = new TextEncoderStream();
    textEncoder.readable.pipeTo(serialPort.writable);
    serialWriter = textEncoder.writable.getWriter();

    // Send PING handshake
    await sendSerialCommand({ action: "PING" });

    // Read loop
    readSerialLoop();
  } catch (err) {
    console.error(err);
    log(`Connection failed: ${err.message}`, "error");
    updateConnectionUI(false);
  }
}

async function disconnectSerial() {
  keepReading = false;
  try {
    if (serialReader) {
      await serialReader.cancel();
      serialReader = null;
    }
    if (serialWriter) {
      await serialWriter.close();
      serialWriter = null;
    }
    if (serialPort) {
      await serialPort.close();
      serialPort = null;
    }
  } catch (e) {
    console.error(e);
  }
  updateConnectionUI(false);
  log("Disconnected from USB device.", "system");
}

function updateConnectionUI(connected) {
  if (connected) {
    connectionStatus.classList.add("connected");
    connectionStatus.querySelector(".status-text").textContent = "Pico Connected";
    btnConnectText.textContent = "Disconnect";
    btnConnect.classList.replace("btn-primary", "btn-secondary");
    btnSaveToPico.disabled = false;
    btnLoadFromPico.disabled = false;
  } else {
    connectionStatus.classList.remove("connected");
    connectionStatus.querySelector(".status-text").textContent = "Disconnected";
    btnConnectText.textContent = "Connect Device";
    btnConnect.classList.replace("btn-secondary", "btn-primary");
    btnSaveToPico.disabled = true;
    btnLoadFromPico.disabled = true;
  }
}

async function sendSerialCommand(cmdObj) {
  if (!serialWriter) return;
  try {
    const line = JSON.stringify(cmdObj) + "\n";
    await serialWriter.write(line);
    log(`Sent: ${cmdObj.action}`, "outgoing");
  } catch (err) {
    log(`Send error: ${err.message}`, "error");
  }
}

async function readSerialLoop() {
  while (serialPort && serialPort.readable && keepReading) {
    const textDecoder = new TextDecoderStream();
    const readableStreamClosed = serialPort.readable.pipeTo(textDecoder.writable);
    serialReader = textDecoder.readable.getReader();

    let buffer = "";
    try {
      while (true) {
        const { value, done } = await serialReader.read();
        if (done) break;
        if (value) {
          buffer += value;
          const lines = buffer.split("\n");
          buffer = lines.pop(); // Keep incomplete line in buffer

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed) handleIncomingMessage(trimmed);
          }
        }
      }
    } catch (err) {
      console.warn("Serial read loop closed:", err);
    } finally {
      serialReader.releaseLock();
    }
  }
}

function handleIncomingMessage(raw) {
  try {
    const data = JSON.parse(raw);

    // Physical key pressed on breadboard!
    if (data.event === "BUTTON_PRESSED") {
      log(`[EVENT] Button ${data.button_id + 1} pressed (Mode ${data.mode})`, "incoming");
      flashKeypressOnScreen(data.button_id);
    }
    // Physical 3-position rotary switch changed!
    else if (data.event === "MODE_CHANGED") {
      setMode(data.mode, true);
    }
    // PONG handshake
    else if (data.response === "PONG") {
      log(`Handshake OK: ${data.device || "Pico"} | Active Mode: ${data.current_mode}`, "incoming");
      if (data.current_mode) setMode(data.current_mode, true);
      // Auto-fetch configuration from Pico
      sendSerialCommand({ action: "GET_CONFIG" });
    }
    // Configuration received from Pico
    else if (data.response === "CONFIG") {
      log("Successfully fetched active configuration from Pico.", "incoming");
      if (data.config) {
        currentConfig = data.config;
        updateModeTabLabels();
        const modeData = currentConfig[`mode${currentMode}`] || { name: `Mode ${currentMode}` };
        currentModeDisplayTitle.textContent = `Mode ${currentMode}: ${modeData.name}`;
        renderKeypad();
      }
    }
    // Config saved confirmation
    else if (data.response === "CONFIG_SAVED") {
      log("✅ Configuration successfully flashed to Pico!", "incoming");
      alert("Configuration successfully saved to your Raspberry Pi Pico!");
    }
  } catch (e) {
    // Non-JSON debug output from CircuitPython/Arduino
    log(`[Pico]: ${raw}`, "incoming");
  }
}

// Connect / Disconnect button click
btnConnect.addEventListener("click", () => {
  if (serialPort) {
    disconnectSerial();
  } else {
    connectSerial();
  }
});

// Save to Pico
btnSaveToPico.addEventListener("click", () => {
  sendSerialCommand({
    action: "SET_CONFIG",
    config: currentConfig
  });
  log("Sending configuration to Pico...", "outgoing");
});

// Read from Pico
btnLoadFromPico.addEventListener("click", () => {
  sendSerialCommand({ action: "GET_CONFIG" });
  log("Requesting configuration from Pico...", "outgoing");
});

// ==============================================================================
// 7. INITIAL BOOTSTRAP
// ==============================================================================

populateKeyDropdowns();
setMode(1, false);
log("Ready. Plug your Raspberry Pi Pico into USB and click Connect.", "system");
