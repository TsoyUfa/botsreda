// ═══════════════════════════════════════
// INITIAL STATE & TEMPLATE DATA
// ═══════════════════════════════════════

const DEFAULT_TEMPLATES = {
  leads: [
    {
      id: "start",
      text: "👋 Приветствую! Я ваш автоматический помощник по подбору недвижимости.\n\nДавайте помогу найти идеальную квартиру в Уфе. Это займет всего 1 минуту!\n\nНажмите кнопку ниже, чтобы начать расчет.",
      image: "",
      expectInput: false,
      storeVariable: "",
      inputNextScreen: "",
      inlineButtons: [
        { text: "🚀 Начать расчет", targetScreenId: "ask_goal" }
      ],
      replyButtons: [],
      replyOneTime: true
    },
    {
      id: "ask_goal",
      text: "🏠 Какая цель покупки квартиры для вас главная?\n\nВыберите один из вариантов ниже 👇",
      image: "",
      expectInput: false,
      storeVariable: "",
      inputNextScreen: "",
      inlineButtons: [
        { text: "Своё первое жильё", targetScreenId: "store_goal_first" },
        { text: "Расширение для детей", targetScreenId: "store_goal_expansion" },
        { text: "Инвестиции / Сбережение", targetScreenId: "store_goal_invest" }
      ],
      replyButtons: [],
      replyOneTime: true
    },
    {
      id: "store_goal_first",
      text: "Отлично, подберем уютное первое жилье! Как к вам обращаться? Напишите ваше имя:",
      image: "",
      expectInput: true,
      storeVariable: "user_name",
      inputNextScreen: "ask_dp",
      inlineButtons: [],
      replyButtons: [],
      replyOneTime: true
    },
    {
      id: "store_goal_expansion",
      text: "Большой семье — просторное жилье! Подберем отличные планировки. Как к вам обращаться? Напишите ваше имя:",
      image: "",
      expectInput: true,
      storeVariable: "user_name",
      inputNextScreen: "ask_dp",
      inlineButtons: [],
      replyButtons: [],
      replyOneTime: true
    },
    {
      id: "store_goal_invest",
      text: "Недвижимость — надежный щит от инфляции! Подберем самые ликвидные новостройки. Как к вам обращаться? Напишите ваше имя:",
      image: "",
      expectInput: true,
      storeVariable: "user_name",
      inputNextScreen: "ask_dp",
      inlineButtons: [],
      replyButtons: [],
      replyOneTime: true
    },
    {
      id: "ask_dp",
      text: "Приятно познакомиться, {user_name}! 🤝\n\nКакой первоначальный взнос вы рассматриваете?\n\n(Можно без взноса!)",
      image: "",
      expectInput: false,
      storeVariable: "",
      inputNextScreen: "",
      inlineButtons: [
        { text: "❌ Без взноса (0 ₽)", targetScreenId: "store_dp_zero" },
        { text: "🔹 До 1.5 млн ₽", targetScreenId: "store_dp_mid" },
        { text: "🔥 Более 1.5 млн ₽", targetScreenId: "store_dp_high" }
      ],
      replyButtons: [],
      replyOneTime: true
    },
    {
      id: "store_dp_zero",
      text: "Понял вас. Есть отличные программы без первого взноса! Напишите, пожалуйста, ваш номер телефона для отправки расчетов и каталога квартир в WhatsApp:",
      image: "",
      expectInput: true,
      storeVariable: "user_phone",
      inputNextScreen: "finish",
      inlineButtons: [],
      replyButtons: [],
      replyOneTime: true
    },
    {
      id: "store_dp_mid",
      text: "Отлично, 1.5 млн ₽ открывают доступ ко всем льготным ипотекам! Напишите ваш номер телефона для отправки расчетов и каталога в WhatsApp:",
      image: "",
      expectInput: true,
      storeVariable: "user_phone",
      inputNextScreen: "finish",
      inlineButtons: [],
      replyButtons: [],
      replyOneTime: true
    },
    {
      id: "store_dp_high" ,
      text: "Отличный стартовый бюджет! Есть супер-варианты. Напишите ваш номер телефона для отправки расчетов и каталога в WhatsApp:",
      image: "",
      expectInput: true,
      storeVariable: "user_phone",
      inputNextScreen: "finish",
      inlineButtons: [],
      replyButtons: [],
      replyOneTime: true
    },
    {
      id: "finish",
      text: "🎉 Спасибо, {user_name}! Данные приняты.\n\nМы отправим персональный расчет на номер {user_phone} в течение 10 минут.\n\nНаши специалисты уже работают над подборкой! 🚀",
      image: "",
      expectInput: false,
      storeVariable: "",
      inputNextScreen: "",
      inlineButtons: [],
      replyButtons: [
        { text: "🔄 Пройти тест заново", targetScreenId: "start" }
      ],
      replyOneTime: true
    }
  ]
};

// ═══════════════════════════════════════
// STATE MANAGEMENT
// ═══════════════════════════════════════

let screens = [];
let activeScreenId = null;

// Simulator State
let simulatorActiveState = null;
let simulatorHistory = [];
let simulatorVariables = {};

// ═══════════════════════════════════════
// DOM ELEMENTS
// ═══════════════════════════════════════

const dom = {
  screenList: document.getElementById("screen-list"),
  btnTemplateLeads: document.getElementById("btn-template-leads"),
  btnImport: document.getElementById("btn-import"),
  importFileInput: document.getElementById("import-file-input"),
  btnExportJson: document.getElementById("btn-export-json"),
  btnExportPython: document.getElementById("btn-export-python"),
  btnAddScreen: document.getElementById("btn-add-screen"),
  screenSearch: document.getElementById("screen-search"),
  
  // Editor
  noScreenSelected: document.getElementById("no-screen-selected"),
  screenEditor: document.getElementById("screen-editor"),
  editScreenId: document.getElementById("edit-screen-id"),
  btnDeleteScreen: document.getElementById("btn-delete-screen"),
  editScreenText: document.getElementById("edit-screen-text"),
  editScreenImage: document.getElementById("edit-screen-image"),
  editExpectInput: document.getElementById("edit-expect-input"),
  inputCaptureDetails: document.getElementById("input-capture-details"),
  editStoreVariable: document.getElementById("edit-store-variable"),
  editInputNextScreen: document.getElementById("edit-input-next-screen"),
  inlineButtonsList: document.getElementById("inline-buttons-list"),
  btnAddInline: document.getElementById("btn-add-inline"),
  replyButtonsList: document.getElementById("reply-buttons-list"),
  btnAddReply: document.getElementById("btn-add-reply"),
  replyOptions: document.querySelector(".reply-options"),
  editReplyOnetime: document.getElementById("edit-reply-onetime"),
  
  // Simulator
  tgChatHistory: document.getElementById("tg-chat-history"),
  tgReplyKeyboardContainer: document.getElementById("tg-reply-keyboard-container"),
  tgReplyKeyboard: document.getElementById("tg-reply-keyboard"),
  tgUserInput: document.getElementById("tg-user-input"),
  tgSendBtn: document.getElementById("tg-send-btn"),
  btnRestartSimulator: document.getElementById("btn-restart-simulator"),
  variableList: document.getElementById("variable-list"),
  
  // Modal
  modalExport: document.getElementById("modal-export"),
  modalClose: document.getElementById("modal-close"),
  exportedCode: document.getElementById("exported-code"),
  btnCopyCode: document.getElementById("btn-copy-code")
};

// ═══════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  loadFromLocalStorage();
  if (screens.length === 0) {
    loadTemplate("leads");
  } else {
    renderScreenList();
    selectScreen(screens[0].id);
  }
  
  initSimulator();
  setupEventListeners();
});

// ═══════════════════════════════════════
// LOCAL STORAGE & SYNC
// ═══════════════════════════════════════

function saveToLocalStorage() {
  localStorage.setItem("botsreda_screens", JSON.stringify(screens));
}

function loadFromLocalStorage() {
  try {
    const raw = localStorage.getItem("botsreda_screens");
    if (raw) {
      screens = JSON.parse(raw);
    }
  } catch (e) {
    console.error("Ошибка загрузки из локального хранилища:", e);
  }
}

// ═══════════════════════════════════════
// TEMPLATE & IMPORT / EXPORT
// ═══════════════════════════════════════

function loadTemplate(name) {
  if (DEFAULT_TEMPLATES[name]) {
    screens = JSON.parse(JSON.stringify(DEFAULT_TEMPLATES[name]));
    saveToLocalStorage();
    renderScreenList();
    if (screens.length > 0) {
      selectScreen(screens[0].id);
    }
    initSimulator();
  }
}

function exportToJson() {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(screens, null, 2));
  const downloadAnchor = document.createElement('a');
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", "telegram_bot_schema.json");
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}

function importFromJson(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(evt) {
    try {
      const parsed = JSON.parse(evt.target.result);
      if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].id) {
        screens = parsed;
        saveToLocalStorage();
        renderScreenList();
        selectScreen(screens[0].id);
        initSimulator();
        alert("Проект успешно импортирован!");
      } else {
        alert("Неверный формат JSON файла.");
      }
    } catch (err) {
      alert("Ошибка при чтении файла: " + err.message);
    }
  };
  reader.readAsText(file);
}

// ═══════════════════════════════════════
// RENDER SCREEN LIST (SIDEBAR)
// ═══════════════════════════════════════

function renderScreenList() {
  const searchVal = dom.screenSearch.value.toLowerCase();
  dom.screenList.innerHTML = "";
  
  screens.forEach(screen => {
    if (searchVal && !screen.id.toLowerCase().includes(searchVal) && !screen.text.toLowerCase().includes(searchVal)) {
      return;
    }
    
    const li = document.createElement("li");
    li.dataset.id = screen.id;
    if (screen.id === activeScreenId) {
      li.classList.add("active");
    }
    
    let badge = "Кнопки";
    if (screen.expectInput) badge = "Запрос ввода";
    else if (screen.replyButtons && screen.replyButtons.length > 0) badge = "Reply-меню";
    else if (screen.inlineButtons.length === 0) badge = "Финал";
    
    li.innerHTML = `
      <span class="screen-list-id">${screen.id}</span>
      <span class="screen-list-badge">${badge}</span>
    `;
    
    li.addEventListener("click", () => selectScreen(screen.id));
    dom.screenList.appendChild(li);
  });
}

// ═══════════════════════════════════════
// SCREEN SELECTION & FORM POPULATION
// ═══════════════════════════════════════

function selectScreen(id) {
  activeScreenId = id;
  
  // Highlight active
  document.querySelectorAll("#screen-list li").forEach(li => {
    li.classList.toggle("active", li.dataset.id === id);
  });
  
  const screen = screens.find(s => s.id === id);
  if (!screen) {
    dom.noScreenSelected.style.display = "flex";
    dom.screenEditor.style.display = "none";
    return;
  }
  
  dom.noScreenSelected.style.display = "none";
  dom.screenEditor.style.display = "flex";
  
  // Populate general info
  dom.editScreenId.value = screen.id;
  dom.editScreenText.value = screen.text;
  dom.editScreenImage.value = screen.image || "";
  
  // Expect input
  dom.editExpectInput.checked = !!screen.expectInput;
  dom.inputCaptureDetails.style.display = screen.expectInput ? "block" : "none";
  dom.editStoreVariable.value = screen.storeVariable || "";
  
  // Load Screen Select Lists
  populateScreenDropdown(dom.editInputNextScreen, screen.inputNextScreen);
  
  // Render buttons
  renderInlineButtonsEditor(screen);
  renderReplyButtonsEditor(screen);
}

function populateScreenDropdown(selectEl, selectedValue) {
  selectEl.innerHTML = '<option value="">-- Выберите экран --</option>';
  screens.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = s.id;
    if (s.id === selectedValue) {
      opt.selected = true;
    }
    selectEl.appendChild(opt);
  });
}

// ═══════════════════════════════════════
// INLINE BUTTONS EDITOR
// ═══════════════════════════════════════

function renderInlineButtonsEditor(screen) {
  dom.inlineButtonsList.innerHTML = "";
  if (!screen.inlineButtons) screen.inlineButtons = [];
  
  screen.inlineButtons.forEach((btn, idx) => {
    const div = document.createElement("div");
    div.className = "button-item";
    
    const input = document.createElement("input");
    input.type = "text";
    input.value = btn.text;
    input.placeholder = "Текст кнопки";
    input.addEventListener("input", (e) => {
      btn.text = e.target.value;
      saveToLocalStorage();
    });
    
    const select = document.createElement("select");
    populateScreenDropdown(select, btn.targetScreenId);
    select.addEventListener("change", (e) => {
      btn.targetScreenId = e.target.value;
      saveToLocalStorage();
      renderScreenList();
    });
    
    const delBtn = document.createElement("button");
    delBtn.className = "button-item-delete";
    delBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
    `;
    delBtn.addEventListener("click", () => {
      screen.inlineButtons.splice(idx, 1);
      saveToLocalStorage();
      renderInlineButtonsEditor(screen);
    });
    
    div.appendChild(input);
    div.appendChild(select);
    div.appendChild(delBtn);
    dom.inlineButtonsList.appendChild(div);
  });
}

// ═══════════════════════════════════════
// REPLY KEYBOARD EDITOR
// ═══════════════════════════════════════

function renderReplyButtonsEditor(screen) {
  dom.replyButtonsList.innerHTML = "";
  if (!screen.replyButtons) screen.replyButtons = [];
  
  if (screen.replyButtons.length > 0) {
    dom.replyOptions.style.display = "block";
  } else {
    dom.replyOptions.style.display = "none";
  }
  dom.editReplyOnetime.checked = screen.replyOneTime !== false;
  
  screen.replyButtons.forEach((btn, idx) => {
    const div = document.createElement("div");
    div.className = "button-item";
    
    const input = document.createElement("input");
    input.type = "text";
    input.value = btn.text;
    input.placeholder = "Текст кнопки";
    input.addEventListener("input", (e) => {
      btn.text = e.target.value;
      saveToLocalStorage();
    });
    
    const select = document.createElement("select");
    populateScreenDropdown(select, btn.targetScreenId);
    select.addEventListener("change", (e) => {
      btn.targetScreenId = e.target.value;
      saveToLocalStorage();
      renderScreenList();
    });
    
    const delBtn = document.createElement("button");
    delBtn.className = "button-item-delete";
    delBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
    `;
    delBtn.addEventListener("click", () => {
      screen.replyButtons.splice(idx, 1);
      saveToLocalStorage();
      renderReplyButtonsEditor(screen);
    });
    
    div.appendChild(input);
    div.appendChild(select);
    div.appendChild(delBtn);
    dom.replyButtonsList.appendChild(div);
  });
}

// ═══════════════════════════════════════
// ACTIONS & EVENTS
// ═══════════════════════════════════════

function setupEventListeners() {
  // Search
  dom.screenSearch.addEventListener("input", renderScreenList);
  
  // Template & Imports
  dom.btnTemplateLeads.addEventListener("click", () => {
    if (confirm("Вы уверены? Это сбросит текущую схему и загрузит шаблон квалификации.")) {
      loadTemplate("leads");
    }
  });
  dom.btnExportJson.addEventListener("click", exportToJson);
  dom.btnImport.addEventListener("click", () => dom.importFileInput.click());
  dom.importFileInput.addEventListener("change", importFromJson);
  
  // Screen Management
  dom.btnAddScreen.addEventListener("click", () => {
    const newId = prompt("Введите ID нового экрана (английскими буквами, например, ask_city):");
    if (!newId) return;
    
    const cleanId = newId.trim().toLowerCase().replace(/[^a-z0-9_]/g, "");
    if (!cleanId) {
      alert("Недопустимый ID.");
      return;
    }
    
    if (screens.some(s => s.id === cleanId)) {
      alert("Экран с таким ID уже существует.");
      return;
    }
    
    screens.push({
      id: cleanId,
      text: "Новый экран. Отредактируйте этот текст в панели управления.",
      image: "",
      expectInput: false,
      storeVariable: "",
      inputNextScreen: "",
      inlineButtons: [],
      replyButtons: [],
      replyOneTime: true
    });
    
    saveToLocalStorage();
    renderScreenList();
    selectScreen(cleanId);
  });
  
  dom.btnDeleteScreen.addEventListener("click", () => {
    if (!activeScreenId) return;
    if (confirm(`Вы уверены, что хотите удалить экран "${activeScreenId}"?`)) {
      const idx = screens.findIndex(s => s.id === activeScreenId);
      if (idx !== -1) {
        screens.splice(idx, 1);
        activeScreenId = screens.length > 0 ? screens[0].id : null;
        saveToLocalStorage();
        renderScreenList();
        selectScreen(activeScreenId);
      }
    }
  });
  
  // Form updates
  dom.editScreenId.addEventListener("change", (e) => {
    const oldId = activeScreenId;
    const newId = e.target.value.trim().toLowerCase().replace(/[^a-z0-9_]/g, "");
    if (!newId || newId === oldId) {
      dom.editScreenId.value = oldId;
      return;
    }
    
    if (screens.some(s => s.id === newId)) {
      alert("Экран с таким ID уже существует.");
      dom.editScreenId.value = oldId;
      return;
    }
    
    // Update IDs in transitions across other screens
    screens.forEach(s => {
      if (s.inputNextScreen === oldId) s.inputNextScreen = newId;
      s.inlineButtons.forEach(b => {
        if (b.targetScreenId === oldId) b.targetScreenId = newId;
      });
      s.replyButtons.forEach(b => {
        if (b.targetScreenId === oldId) b.targetScreenId = newId;
      });
    });
    
    const screen = screens.find(s => s.id === oldId);
    screen.id = newId;
    activeScreenId = newId;
    
    saveToLocalStorage();
    renderScreenList();
    selectScreen(newId);
  });
  
  dom.editScreenText.addEventListener("input", (e) => {
    const screen = screens.find(s => s.id === activeScreenId);
    if (screen) {
      screen.text = e.target.value;
      saveToLocalStorage();
    }
  });
  
  dom.editScreenImage.addEventListener("input", (e) => {
    const screen = screens.find(s => s.id === activeScreenId);
    if (screen) {
      screen.image = e.target.value.trim();
      saveToLocalStorage();
    }
  });
  
  dom.editExpectInput.addEventListener("change", (e) => {
    const screen = screens.find(s => s.id === activeScreenId);
    if (screen) {
      screen.expectInput = e.target.checked;
      dom.inputCaptureDetails.style.display = screen.expectInput ? "block" : "none";
      saveToLocalStorage();
      renderScreenList();
    }
  });
  
  dom.editStoreVariable.addEventListener("input", (e) => {
    const screen = screens.find(s => s.id === activeScreenId);
    if (screen) {
      screen.storeVariable = e.target.value.trim().toLowerCase().replace(/[^a-z0-9_]/g, "");
      saveToLocalStorage();
    }
  });
  
  dom.editInputNextScreen.addEventListener("change", (e) => {
    const screen = screens.find(s => s.id === activeScreenId);
    if (screen) {
      screen.inputNextScreen = e.target.value;
      saveToLocalStorage();
    }
  });
  
  dom.editReplyOnetime.addEventListener("change", (e) => {
    const screen = screens.find(s => s.id === activeScreenId);
    if (screen) {
      screen.replyOneTime = e.target.checked;
      saveToLocalStorage();
    }
  });
  
  // Add buttons
  dom.btnAddInline.addEventListener("click", () => {
    const screen = screens.find(s => s.id === activeScreenId);
    if (screen) {
      if (!screen.inlineButtons) screen.inlineButtons = [];
      screen.inlineButtons.push({ text: "Новая кнопка", targetScreenId: "" });
      saveToLocalStorage();
      renderInlineButtonsEditor(screen);
    }
  });
  
  dom.btnAddReply.addEventListener("click", () => {
    const screen = screens.find(s => s.id === activeScreenId);
    if (screen) {
      if (!screen.replyButtons) screen.replyButtons = [];
      screen.replyButtons.push({ text: "Новая кнопка", targetScreenId: "" });
      saveToLocalStorage();
      renderReplyButtonsEditor(screen);
    }
  });
  
  // Simulator triggers
  dom.btnRestartSimulator.addEventListener("click", initSimulator);
  dom.tgUserInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      handleUserTextSubmit();
    }
  });
  dom.tgSendBtn.addEventListener("click", handleUserTextSubmit);
  
  // Python Modal
  dom.btnExportPython.addEventListener("click", openPythonModal);
  dom.modalClose.addEventListener("click", () => dom.modalExport.style.display = "none");
  dom.btnCopyCode.addEventListener("click", copyExportedCode);
}

// ═══════════════════════════════════════
// INTERACTIVE TELEGRAM SIMULATOR LOGIC
// ═══════════════════════════════════════

function initSimulator() {
  simulatorHistory = [];
  simulatorVariables = {};
  
  // Start with 'start' state if exists, otherwise first screen
  const firstScreen = screens.find(s => s.id === "start") || screens[0];
  if (!firstScreen) {
    dom.tgChatHistory.innerHTML = '<div class="var-empty" style="padding: 20px; text-align: center;">Создайте хотя бы один экран для запуска симулятора.</div>';
    return;
  }
  
  simulatorActiveState = firstScreen.id;
  renderVariables();
  
  // Send first bot message
  triggerBotResponse(firstScreen);
}

function triggerBotResponse(screen) {
  // Format message string
  let text = screen.text;
  
  // Variable replacement
  Object.keys(simulatorVariables).forEach(key => {
    const regex = new RegExp(`{${key}}`, "g");
    text = text.replace(regex, simulatorVariables[key]);
  });
  
  const msgObj = {
    sender: "bot",
    text: text,
    image: screen.image || "",
    inlineButtons: screen.inlineButtons ? JSON.parse(JSON.stringify(screen.inlineButtons)) : []
  };
  
  simulatorHistory.push(msgObj);
  renderChatHistory();
  
  // Setup Reply keyboard if any
  if (screen.replyButtons && screen.replyButtons.length > 0) {
    dom.tgReplyKeyboardContainer.style.display = "block";
    dom.tgReplyKeyboard.innerHTML = "";
    screen.replyButtons.forEach(btn => {
      const button = document.createElement("button");
      button.className = "tg-reply-btn";
      button.textContent = btn.text;
      button.addEventListener("click", () => handleKeyboardClick(btn.text, btn.targetScreenId, screen.replyOneTime));
      dom.tgReplyKeyboard.appendChild(button);
    });
  } else {
    dom.tgReplyKeyboardContainer.style.display = "none";
  }
  
  // Focus User Input if waiting for input
  if (screen.expectInput) {
    dom.tgUserInput.placeholder = "Введите ответ...";
  } else {
    dom.tgUserInput.placeholder = "Нажмите кнопку на экране...";
  }
}

function renderChatHistory() {
  dom.tgChatHistory.innerHTML = "";
  
  simulatorHistory.forEach(msg => {
    const msgDiv = document.createElement("div");
    msgDiv.className = `tg-msg tg-msg-${msg.sender}`;
    
    // Add image if any
    if (msg.image) {
      const img = document.createElement("img");
      img.className = "tg-msg-image";
      img.src = msg.image;
      img.onerror = () => img.style.display = "none"; // Hide broken image
      msgDiv.appendChild(img);
    }
    
    // Add text body
    const textNode = document.createElement("span");
    // Replace newlines with breaks
    textNode.innerHTML = msg.text.replace(/\n/g, "<br>");
    msgDiv.appendChild(textNode);
    
    // Inline keyboard below message
    if (msg.sender === "bot" && msg.inlineButtons && msg.inlineButtons.length > 0) {
      const keyboardDiv = document.createElement("div");
      keyboardDiv.className = "tg-inline-keyboard";
      
      // Group inline buttons (single button per row for simplicity, or dual if text fits)
      let currentRow = null;
      msg.inlineButtons.forEach((btn, idx) => {
        if (idx % 2 === 0) {
          currentRow = document.createElement("div");
          currentRow.className = "tg-inline-row";
          keyboardDiv.appendChild(currentRow);
        }
        
        const btnDiv = document.createElement("div");
        btnDiv.className = "tg-inline-btn";
        btnDiv.textContent = btn.text;
        btnDiv.addEventListener("click", () => handleInlineClick(btn.text, btn.targetScreenId));
        currentRow.appendChild(btnDiv);
      });
      
      msgDiv.appendChild(keyboardDiv);
    }
    
    dom.tgChatHistory.appendChild(msgDiv);
  });
  
  // Scroll to bottom
  dom.tgChatHistory.scrollTop = dom.tgChatHistory.scrollHeight;
}

function handleInlineClick(text, targetScreenId) {
  // Push user event message
  simulatorHistory.push({
    sender: "user",
    text: text
  });
  renderChatHistory();
  
  transitionSimulatorState(targetScreenId);
}

function handleKeyboardClick(text, targetScreenId, oneTime) {
  // Push user event message
  simulatorHistory.push({
    sender: "user",
    text: text
  });
  
  if (oneTime) {
    dom.tgReplyKeyboardContainer.style.display = "none";
  }
  
  renderChatHistory();
  
  transitionSimulatorState(targetScreenId);
}

function handleUserTextSubmit() {
  const inputVal = dom.tgUserInput.value.trim();
  if (!inputVal) return;
  
  dom.tgUserInput.value = "";
  
  // Add message
  simulatorHistory.push({
    sender: "user",
    text: inputVal
  });
  renderChatHistory();
  
  const screen = screens.find(s => s.id === simulatorActiveState);
  if (screen && screen.expectInput && screen.storeVariable) {
    // Save variable
    simulatorVariables[screen.storeVariable] = inputVal;
    renderVariables();
    
    // Transition
    transitionSimulatorState(screen.inputNextScreen);
  } else {
    // No expected input, check if text matches any button target
    let matchedTarget = null;
    if (screen.inlineButtons) {
      const match = screen.inlineButtons.find(b => b.text.toLowerCase() === inputVal.toLowerCase());
      if (match) matchedTarget = match.targetScreenId;
    }
    if (!matchedTarget && screen.replyButtons) {
      const match = screen.replyButtons.find(b => b.text.toLowerCase() === inputVal.toLowerCase());
      if (match) matchedTarget = match.targetScreenId;
    }
    
    if (matchedTarget) {
      transitionSimulatorState(matchedTarget);
    } else {
      // Send error text
      simulatorHistory.push({
        sender: "bot",
        text: "Пожалуйста, используйте кнопки на экране для ответа.",
        inlineButtons: []
      });
      renderChatHistory();
    }
  }
}

function transitionSimulatorState(targetScreenId) {
  if (!targetScreenId) {
    // End of bot flow placeholder
    setTimeout(() => {
      simulatorHistory.push({
        sender: "bot",
        text: "🏁 Конец диалога. Вы можете нажать кнопку перезапуска вверху, чтобы начать сначала.",
        inlineButtons: []
      });
      renderChatHistory();
    }, 400);
    return;
  }
  
  const nextScreen = screens.find(s => s.id === targetScreenId);
  if (!nextScreen) {
    console.error(`Целевой экран "${targetScreenId}" не найден.`);
    return;
  }
  
  simulatorActiveState = targetScreenId;
  
  // Simulate network latency
  setTimeout(() => {
    triggerBotResponse(nextScreen);
  }, 350);
}

function renderVariables() {
  dom.variableList.innerHTML = "";
  const keys = Object.keys(simulatorVariables);
  
  if (keys.length === 0) {
    dom.variableList.innerHTML = '<span class="var-empty">Данные пока не введены</span>';
    return;
  }
  
  keys.forEach(key => {
    const div = document.createElement("div");
    div.className = "var-item";
    div.innerHTML = `
      <span class="var-name">${key}</span>
      <span class="var-val">"${simulatorVariables[key]}"</span>
    `;
    dom.variableList.appendChild(div);
  });
}

// ═══════════════════════════════════════
// AIOGRAM V3 CODE GENERATOR EXPORTER
// ═══════════════════════════════════════

function openPythonModal() {
  dom.modalExport.style.display = "flex";
  dom.exportedCode.textContent = generatePythonCode();
}

function copyExportedCode() {
  const code = dom.exportedCode.textContent;
  navigator.clipboard.writeText(code).then(() => {
    const origText = dom.btnCopyCode.textContent;
    dom.btnCopyCode.textContent = "Скопировано! ✓";
    setTimeout(() => {
      dom.btnCopyCode.textContent = origText;
    }, 2000);
  }).catch(err => {
    alert("Не удалось скопировать: " + err);
  });
}

function generatePythonCode() {
  let code = `import os
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# Загрузка токена из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация роутера
router = Router()

# Определение состояний бота (FSM)
class BotStates(StatesGroup):
`;

  // Define FSM states dynamically
  screens.forEach(s => {
    code += `    screen_${s.id} = State()\n`;
  });

  code += `\n# ═══════════════════════════════════════\n`;
  code += `# КЛАВИАТУРЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ\n`;
  code += `# ═══════════════════════════════════════\n\n`;

  // Keyboard generator helpers
  screens.forEach(s => {
    // Inline keyboard builder
    if (s.inlineButtons && s.inlineButtons.length > 0) {
      code += `def get_keyboard_${s.id}():\n`;
      code += `    buttons = [\n`;
      s.inlineButtons.forEach(b => {
        const targetStateStr = b.targetScreenId ? `goto:${b.targetScreenId}` : "end_flow";
        code += `        [InlineKeyboardButton(text="${b.text}", callback_data="${targetStateStr}")],\n`;
      });
      code += `    ]\n`;
      code += `    return InlineKeyboardMarkup(inline_keyboard=buttons)\n\n`;
    }

    // Reply keyboard builder
    if (s.replyButtons && s.replyButtons.length > 0) {
      code += `def get_reply_${s.id}():\n`;
      code += `    keyboard_buttons = [\n`;
      s.replyButtons.forEach(b => {
        code += `        [KeyboardButton(text="${b.text}")],\n`;
      });
      code += `    ]\n`;
      code += `    return ReplyKeyboardMarkup(\n`;
      code += `        keyboard=keyboard_buttons,\n`;
      code += `        resize_keyboard=True,\n`;
      code += `        one_time_keyboard=${s.replyOneTime !== false ? 'True' : 'False'}\n`;
      code += `    )\n\n`;
    }
  });

  // Safe Text Formatter Helper
  code += `async def format_text(text: str, state: FSMContext) -> str:\n`;
  code += `    """Заменяет плейсхолдеры типа {user_name} значениями из FSM Context"""\n`;
  code += `    data = await state.get_data()\n`;
  code += `    formatted_text = text\n`;
  
  // Extract all placeholders from code screens
  const variables = new Set();
  screens.forEach(s => {
    const matches = s.text.match(/{[a-zA-Z0-9_]+}/g);
    if (matches) {
      matches.forEach(m => variables.add(m.replace(/[{}]/g, "")));
    }
  });

  variables.forEach(v => {
    code += `    formatted_text = formatted_text.replace("{${v}}", str(data.get("${v}", ""))) \n`;
  });
  code += `    return formatted_text\n\n`;

  // Start Handler
  code += `# ═══════════════════════════════════════\n`;
  code += `# ОБРАБОТЧИКИ СОБЫТИЙ И СОСТОЯНИЙ\n`;
  code += `# ═══════════════════════════════════════\n\n`;

  const startScreen = screens.find(s => s.id === "start") || screens[0];
  code += `@router.message(CommandStart())\n`;
  code += `@router.message(Command("restart"))\n`;
  code += `async def cmd_start(message: Message, state: FSMContext):\n`;
  code += `    await state.clear()\n`; // Reset FSM
  code += `    await state.set_state(BotStates.screen_${startScreen.id})\n`;
  
  // Text & image formatting for start
  code += `    text = await format_text("""${startScreen.text}""", state)\n`;
  if (startScreen.image) {
    code += `    # Отправка фото\n`;
    code += `    try:\n`;
    code += `        await message.answer_photo(photo="${startScreen.image}", caption=text`;
    if (startScreen.inlineButtons && startScreen.inlineButtons.length > 0) {
      code += `, reply_markup=get_keyboard_${startScreen.id}()`;
    } else if (startScreen.replyButtons && startScreen.replyButtons.length > 0) {
      code += `, reply_markup=get_reply_${startScreen.id}()`;
    }
    code += `)\n`;
    code += `    except Exception as e:\n`;
    code += `        logger.error(f"Ошибка отправки фото: {e}")\n`;
    code += `        await message.answer(text=text`;
    if (startScreen.inlineButtons && startScreen.inlineButtons.length > 0) {
      code += `, reply_markup=get_keyboard_${startScreen.id}()`;
    } else if (startScreen.replyButtons && startScreen.replyButtons.length > 0) {
      code += `, reply_markup=get_reply_${startScreen.id}()`;
    }
    code += `)\n`;
  } else {
    code += `    await message.answer(text=text`;
    if (startScreen.inlineButtons && startScreen.inlineButtons.length > 0) {
      code += `, reply_markup=get_keyboard_${startScreen.id}()`;
    } else if (startScreen.replyButtons && startScreen.replyButtons.length > 0) {
      code += `, reply_markup=get_reply_${startScreen.id}()`;
    }
    code += `)\n`;
  }
  code += `\n`;

  // Individual handlers for each screen
  screens.forEach(screen => {
    // Handler if we wait for text input
    if (screen.expectInput && screen.storeVariable && screen.inputNextScreen) {
      const nextScreen = screens.find(s => s.id === screen.inputNextScreen);
      code += `@router.message(BotStates.screen_${screen.id})\n`;
      code += `async def process_input_${screen.id}(message: Message, state: FSMContext):\n`;
      code += `    user_text = message.text\n`;
      code += `    # Сохраняем введенную переменную\n`;
      code += `    await state.update_data(${screen.storeVariable}=user_text)\n\n`;
      
      // Move to next state
      code += `    # Переходим к следующему состоянию\n`;
      code += `    await state.set_state(BotStates.screen_${screen.inputNextScreen})\n`;
      
      // Text and layout for next screen
      code += `    next_text = await format_text("""${nextScreen.text}""", state)\n`;
      
      if (nextScreen.image) {
        code += `    try:\n`;
        code += `        await message.answer_photo(photo="${nextScreen.image}", caption=next_text`;
        if (nextScreen.inlineButtons && nextScreen.inlineButtons.length > 0) {
          code += `, reply_markup=get_keyboard_${nextScreen.id}()`;
        } else if (nextScreen.replyButtons && nextScreen.replyButtons.length > 0) {
          code += `, reply_markup=get_reply_${nextScreen.id}()`;
        } else {
          code += `, reply_markup=ReplyKeyboardRemove()`;
        }
        code += `)\n`;
        code += `    except Exception as e:\n`;
        code += `        await message.answer(text=next_text`;
        if (nextScreen.inlineButtons && nextScreen.inlineButtons.length > 0) {
          code += `, reply_markup=get_keyboard_${nextScreen.id}()`;
        } else if (nextScreen.replyButtons && nextScreen.replyButtons.length > 0) {
          code += `, reply_markup=get_reply_${nextScreen.id}()`;
        } else {
          code += `, reply_markup=ReplyKeyboardRemove()`;
        }
        code += `)\n`;
      } else {
        code += `    await message.answer(text=next_text`;
        if (nextScreen.inlineButtons && nextScreen.inlineButtons.length > 0) {
          code += `, reply_markup=get_keyboard_${nextScreen.id}()`;
        } else if (nextScreen.replyButtons && nextScreen.replyButtons.length > 0) {
          code += `, reply_markup=get_reply_${nextScreen.id}()`;
        } else {
          code += `, reply_markup=ReplyKeyboardRemove()`;
        }
        code += `)\n`;
      }
      code += `\n`;
    }

    // Handler if we have reply buttons
    if (screen.replyButtons && screen.replyButtons.length > 0) {
      screen.replyButtons.forEach(btn => {
        if (!btn.targetScreenId) return;
        const targetScreen = screens.find(s => s.id === btn.targetScreenId);
        
        code += `@router.message(BotStates.screen_${screen.id}, F.text == "${btn.text}")\n`;
        code += `async def reply_btn_${screen.id}_${btn.targetScreenId.replace(/[^a-z0-9_]/g, "")}(message: Message, state: FSMContext):\n`;
        code += `    await state.set_state(BotStates.screen_${btn.targetScreenId})\n`;
        code += `    text = await format_text("""${targetScreen.text}""", state)\n`;
        
        if (targetScreen.image) {
          code += `    try:\n`;
          code += `        await message.answer_photo(photo="${targetScreen.image}", caption=text`;
          if (targetScreen.inlineButtons && targetScreen.inlineButtons.length > 0) {
            code += `, reply_markup=get_keyboard_${targetScreen.id}()`;
          } else if (targetScreen.replyButtons && targetScreen.replyButtons.length > 0) {
            code += `, reply_markup=get_reply_${targetScreen.id}()`;
          } else {
            code += `, reply_markup=ReplyKeyboardRemove()`;
          }
          code += `)\n`;
          code += `    except Exception as e:\n`;
          code += `        await message.answer(text=text`;
          if (targetScreen.inlineButtons && targetScreen.inlineButtons.length > 0) {
            code += `, reply_markup=get_keyboard_${targetScreen.id}()`;
          } else if (targetScreen.replyButtons && targetScreen.replyButtons.length > 0) {
            code += `, reply_markup=get_reply_${targetScreen.id}()`;
          } else {
            code += `, reply_markup=ReplyKeyboardRemove()`;
          }
          code += `)\n`;
        } else {
          code += `    await message.answer(text=text`;
          if (targetScreen.inlineButtons && targetScreen.inlineButtons.length > 0) {
            code += `, reply_markup=get_keyboard_${targetScreen.id}()`;
          } else if (targetScreen.replyButtons && targetScreen.replyButtons.length > 0) {
            code += `, reply_markup=get_reply_${targetScreen.id}()`;
          } else {
            code += `, reply_markup=ReplyKeyboardRemove()`;
          }
          code += `)\n`;
        }
        code += `\n`;
      });
    }
  });

  // Global Callback Query Handler (for inline buttons)
  code += `# Обработка кликов по inline-кнопкам (Callback Queries)\n`;
  code += `@router.callback_query(F.data.startswith("goto:"))\n`;
  code += `async def process_callback_state_transition(callback: CallbackQuery, state: FSMContext):\n`;
  code += `    await callback.answer()\n`;
  code += `    target_state_name = callback.data.split(":")[1]\n\n`;
  
  // Transition logic mapping state name to state object
  code += `    # Переключение состояний\n`;
  screens.forEach((s, idx) => {
    const cond = idx === 0 ? "if" : "elif";
    code += `    ${cond} target_state_name == "${s.id}":\n`;
    code += `        await state.set_state(BotStates.screen_${s.id})\n`;
    code += `        text = await format_text("""${s.text}""", state)\n`;
    
    // Send next screen message
    code += `        # Удаляем предыдущую инлайн клавиатуру\n`;
    code += `        try:\n`;
    code += `            await callback.message.edit_reply_markup(reply_markup=None)\n`;
    code += `        except Exception:\n`;
    code += `            pass\n\n`;
    
    code += `        if "${s.image}":\n`;
    code += `            try:\n`;
    code += `                await callback.message.answer_photo(photo="${s.image}", caption=text`;
    if (s.inlineButtons && s.inlineButtons.length > 0) {
      code += `, reply_markup=get_keyboard_${s.id}()`;
    } else if (s.replyButtons && s.replyButtons.length > 0) {
      code += `, reply_markup=get_reply_${s.id}()`;
    } else {
      code += `, reply_markup=ReplyKeyboardRemove()`;
    }
    code += `)\n`;
    code += `            except Exception:\n`;
    code += `                await callback.message.answer(text=text`;
    if (s.inlineButtons && s.inlineButtons.length > 0) {
      code += `, reply_markup=get_keyboard_${s.id}()`;
    } else if (s.replyButtons && s.replyButtons.length > 0) {
      code += `, reply_markup=get_reply_${s.id}()`;
    } else {
      code += `, reply_markup=ReplyKeyboardRemove()`;
    }
    code += `)\n`;
    code += `        else:\n`;
    code += `            await callback.message.answer(text=text`;
    if (s.inlineButtons && s.inlineButtons.length > 0) {
      code += `, reply_markup=get_keyboard_${s.id}()`;
    } else if (s.replyButtons && s.replyButtons.length > 0) {
      code += `, reply_markup=get_reply_${s.id}()`;
    } else {
      code += `, reply_markup=ReplyKeyboardRemove()`;
    }
    code += `)\n`;
  });
  code += `\n`;

  // Catch-all end flow callback handler
  code += `@router.callback_query(F.data == "end_flow")\n`;
  code += `async def process_callback_end(callback: CallbackQuery):\n`;
  code += `    await callback.answer("Диалог завершен.")\n`;
  code += `    try:\n`;
  code += `        await callback.message.edit_reply_markup(reply_markup=None)\n`;
  code += `    except Exception:\n`;
  code += `        pass\n\n`;

  // Main Boilerplate
  code += `async def main():\n`;
  code += `    if not BOT_TOKEN or BOT_TOKEN == "ВАШ_ТОКЕН":\n`;
  code += `        print("ОШИБКА: Пожалуйста, настройте BOT_TOKEN в файле .env")\n`;
  code += `        return\n\n`;
  code += `    bot = Bot(token=BOT_TOKEN)\n`;
  code += `    dp = Dispatcher()\n`;
  code += `    dp.include_router(router)\n\n`;
  code += `    print("Бот успешно запущен!")\n`;
  code += `    await dp.start_polling(bot)\n\n`;
  code += `if __name__ == "__main__":\n`;
  code += `    asyncio.run(main())\n`;

  return code;
}
