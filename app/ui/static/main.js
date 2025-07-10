document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("export-form");
  const logStream = document.getElementById("log-stream");
  const timerDisplay = document.getElementById("timer");
  const processedChatsDisplay = document.getElementById("processed_chats");
  const startButton = document.getElementById("start-button");
  // const stopButton = document.getElementById("stop-button");
  const progressBar = document.getElementById("progress-bar-inner");

  const INFO = '<span class="text-info">[INFO]</span> '
  const INFO_SUCCESS = '<span class="text-success">[INFO]</span> '
  const WARNING = '<span class="text-warning">[WARNING]</span> '
  const ERROR = '<span class="text-danger">[ERROR]</span> '
  const DEBUG = '<span class="text-primary">[DEBUG]</span> '
  const STATUS = '<span class="text-secondary">[STATUS]</span> '
  const NOTE = '<span class="text-muted">[NOTE]</span> '

  let timerInterval;
  let seconds = 0;
  let totalChats = 1;
  let chatsProcessed = 0;

  const progress = {
    contactsSaved: false,
    chatsProcessed: 0,
    summarySaved: false,
  };

  function updateProgress() {
    let percent = 0;

    if (progress.contactsSaved) {
      percent += 5;
    }

    percent += (progress.chatsProcessed / totalChats) * 90;

    if (progress.summarySaved) {
      percent += 5;
    }

    updateProgressBar(Math.round(percent));
  }

  let eventSource = new EventSource("/api/log-stream");
  eventSource.onmessage = (event) => {
      console.log(event)
      logStream.innerHTML += INFO + event.data + "\n";
      logStream.scrollTop = logStream.scrollHeight;
      
      if (event.data.includes("chat(s) per last")) {
        totalChats = parseInt(event.data.split(" ")[2]);
        processedChatsDisplay.textContent = `0/${totalChats}`
      }

      if (event.data.includes("☎️ Exported")) {
        updateProgressBar(5);
      }

      if (event.data.includes("💬 Processing chat:")) {
        chatsProcessed++;
        processedChatsDisplay.textContent = `${chatsProcessed}/${totalChats}`
        const percent = 5 + (chatsProcessed * (90 / totalChats));
        updateProgressBar(Math.min(Number(percent.toFixed(1)), 95));
      }
      
      if (event.data.includes("Total time")) {
        // ⏹ Зупинити таймер
        stopTimer();
        timerInterval = null;
        eventSource.close();

        // ✅ 100% прогрес
        updateProgressBar(100);
        eventSource = new EventSource("/api/log-stream");
        
      }

      // const progressMatch = event.data.match(/PROGRESS: (\d+)%/);
      // if (progressMatch) {
      //   const percent = Number(progressMatch[1]);
      //   progressBar.style.width = percent + "%";
      //   progressBar.textContent = percent + "%";
      // }

      // if (event.data.includes("Експорт завершено")) {
      //   clearInterval(timerInterval);
      //   eventSource.close();
      //   eventSource = null;
      // }
    };

  let startTime;
  let currentProgress = 0;

  function startTimer() {
    startTime = Date.now();
    timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const minutes = String(Math.floor(elapsed / 60)).padStart(2, '0');
      const seconds = String(elapsed % 60).padStart(2, '0');
      document.getElementById('timer').textContent = `${minutes}:${seconds}`;
      currentProgress += 1;
      updateProgressBar(currentProgress);
      }, 1000);
  }

  function stopTimer() {
    clearInterval(timerInterval);
  }

  function updateProgressBar(percentage) {
    const progressBar = document.getElementById('progress-bar-inner');
    const safePercentage = Math.min(Math.max(percentage, 0), 100);

    // Анімаційно оновлюємо ширину
    progressBar.style.transition = 'width 0.3s ease-in-out';
    progressBar.style.width = `${safePercentage}%`;

    // Оновлюємо текст
    progressBar.textContent = `${safePercentage}%`;

    // Зберігаємо значення у localStorage
    // localStorage.setItem('progress', safePercentage.toString());
  }

  function resetProgressBar() {
    updateProgressBar(0);
    // localStorage.removeItem('progress');
  }


  // Завантажити saved config
  // const savedConfig = localStorage.getItem("exportConfig");
  // if (savedConfig) {
  //   const parsed = JSON.parse(savedConfig);
  //   Object.entries(parsed).forEach(([key, value]) => {
  //     const input = form.elements[key];
  //     if (!input) return;
  //     if (input.type === "checkbox") input.checked = value;
  //     else input.value = Array.isArray(value) ? JSON.stringify(value) : value;
  //   });
  // }

  // stopButton.addEventListener("click", () => {
  //   if (eventSource) {
  //     eventSource.close();
  //     eventSource = null;
  //   }
  //   clearInterval(timerInterval);
  //   logStream.textContent += "\n⏹️ Зупинено вручну\n";
  // });

  startButton.addEventListener("click", async (e) => {
    logStream.innerHTML = ""
    e.preventDefault();
    // if (eventSource) {
    //   logStream.textContent += "\n❗️ Експорт вже запущено\n";
    //   return;
    // }
    // logStream.textContent = "🔄 Запуск експорту...\n";
    timerDisplay.textContent = "00:00";
    progressBar.style.width = "0%";
    progressBar.textContent = "0%";
    currentProgress = 0;
    resetProgressBar();
    stopTimer();
    startTimer();



    // const formData = new FormData(form);
    const config = getFormConfig();

    // for (const [key, value] of formData.entries()) {
    //   if (value === "on") config[key] = true;
    //   else if (value === "") config[key] = null;
    //   else if (key === "chat_ids") config[key] = JSON.parse(`[${value}]`);
    //   else if (!isNaN(value) && key !== "api_hash" && key !== "session_string") config[key] = Number(value);
    //   else config[key] = value;
    // }

    // localStorage.setItem("exportConfig", JSON.stringify(config));

    // Запуск таймера
    seconds = 0;
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      seconds++;
      const min = String(Math.floor(seconds / 60)).padStart(2, '0');
      const sec = String(seconds % 60).padStart(2, '0');
      timerDisplay.textContent = `${min}:${sec}`;
    }, 1000);

    // logStream.textContent = "";
    progressBar.style.width = "0%";
    progressBar.textContent = "0%";

    const method = document.getElementById("export-method").value;
    const url = method === "async" ? "/api/execute-async" : "/api/execute-sync";

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config)
    });
    
    const data = await response.json();

    console.log(data);
    if (!response.ok) {
      logStream.innerHTML = "❌ Помилка запиту";
      clearInterval(timerInterval);
      return;
    } else {
      logStream.innerHTML += INFO + "Запит успішно надіслано. Очікуємо на відповідь сервера...\n";
      if (data.status === "error") {
        logStream.innerHTML += ERROR + "Помилка: " + data.error + "\n";
        clearInterval(timerInterval);
        return;
      } else{
        logStream.innerHTML += STATUS + data.status + "\n";
      }
      // logStream.textContent += JSON.stringify(response.status, null, 2) + "\n";
      logStream.scrollTop = logStream.scrollHeight; // Прокрутка вниз
    }

    // eventSource = new EventSource("/events");
    
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const config = {};

    for (const [key, value] of formData.entries()) {
      if (value === "on") config[key] = true;
      else if (value === "") config[key] = null;
      else if (key === "chat_ids") config[key] = JSON.parse(`${value}`);
      // else if (key === "session_string" && value === "") config[key] = null;
      else if (!isNaN(value) && key !== "api_hash" && key !== "session_string") config[key] = Number(value);
      else config[key] = value;
    }

    // localStorage.setItem("exportConfig", JSON.stringify(config));

    // Запуск таймера
    seconds = 0;
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      seconds++;
      const min = String(Math.floor(seconds / 60)).padStart(2, '0');
      const sec = String(seconds % 60).padStart(2, '0');
      timerDisplay.textContent = `${min}:${sec}`;
    }, 1000);

    logStream.textContent = "";
    progressBar.style.width = "0%";
    progressBar.textContent = "0%";

    const method = document.getElementById("export-method").value;
    const url = method === "async" ? "/api/execute-async" : "/api/execute-sync";

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config)
    });

    if (!response.ok) {
      logStream.textContent = "❌ Помилка запиту";
      clearInterval(timerInterval);
      return;
    }

    eventSource = new EventSource("/events");
    eventSource.onmessage = (event) => {
      logStream.textContent += event.data + "\n";

      const progressMatch = event.data.match(/PROGRESS: (\d+)%/);
      if (progressMatch) {
        const percent = Number(progressMatch[1]);
        progressBar.style.width = percent + "%";
        progressBar.textContent = percent + "%";
      }

      if (event.data.includes("Експорт завершено")) {
        clearInterval(timerInterval);
        eventSource.close();
        eventSource = null;
      }
    };
  });
});

function getFormConfig() {
  const form = document.getElementById("export-form");
  const formData = new FormData(form);
  const config = {};

  for (const [key, value] of formData.entries()) {
    // Checkbox
    if (form.querySelector(`[name="${key}"]`)?.type === "checkbox") {
      config[key] = true;
    }

    // Порожнє значення → null
    else if (value === "") {
      config[key] = null;
    }

    // Chat IDs → масив (розділені комами, трим пробіли)
    else if (key === "chat_ids") {
      config[key] = value
        .split(",")
        .map((v) => v.trim())
        .filter((v) => v.length > 0);
    }

    // JSON file page size або messages_limit → число
    else if (!isNaN(value) && ["messages_limit", "json_file_page_size"].includes(key)) {
      config[key] = Number(value);
    }

    // Все інше — як рядок
    else {
      config[key] = value;
    }
  }

  // Обробка чекбоксів, які не вибрані (бо вони не потрапляють у formData.entries())
  const allCheckboxes = form.querySelectorAll('input[type="checkbox"]');
  allCheckboxes.forEach((checkbox) => {
    if (!formData.has(checkbox.name)) {
      config[checkbox.name] = false;
    }
  });
  console.log("Form config:", config);
  return config;
}

// document.getElementById("config-form").onsubmit = async (e) => {
//   e.preventDefault();
//   const session_string = e.target.session_string.value;
//   await fetch("/api/config", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ session_string: session_string })
//   });

//   const evtSource = new EventSource("/stream");
//   const log = document.getElementById("progress-log");
//   evtSource.onmessage = function(event) {
//     const data = JSON.parse(event.data);
//     log.textContent += JSON.stringify(data) + "\n";
//     if (data.status === "complete") {
//       evtSource.close();
//     }
//   };
// };