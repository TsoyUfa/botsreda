(function () {
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  const form = document.getElementById("lead-form");
  const statusEl = document.getElementById("form-status");
  const submitBtn = document.getElementById("submit-btn");
  const btnText = submitBtn?.querySelector(".btn-text");
  const btnLoader = submitBtn?.querySelector(".btn-loader");

  function setStatus(message, type) {
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.className = "form__status";
    if (type === "ok") statusEl.classList.add("form__status--ok");
    if (type === "err") statusEl.classList.add("form__status--err");
  }

  function setLoading(loading) {
    if (!submitBtn) return;
    submitBtn.disabled = loading;
    if (btnText) btnText.hidden = loading;
    if (btnLoader) btnLoader.hidden = !loading;
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      setStatus("", null);

      const fd = new FormData(form);
      const payload = {
        name: String(fd.get("name") || "").trim(),
        contact: String(fd.get("contact") || "").trim(),
        message: String(fd.get("message") || "").trim(),
      };

      if (!payload.name || !payload.contact || !payload.message) {
        setStatus("Заполни все поля.", "err");
        return;
      }

      setLoading(true);

      try {
        const res = await fetch("/api/lead", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          throw new Error(data.error || "Не удалось отправить заявку");
        }

        form.reset();
        setStatus("Заявка отправлена. Напишу в Telegram в ближайшее время.", "ok");
      } catch (err) {
        const isLocal =
          location.hostname === "localhost" ||
          location.hostname === "127.0.0.1" ||
          location.protocol === "file:";

        if (isLocal) {
          const tg = `https://t.me/antontsoy?text=${encodeURIComponent(
            `Заявка с сайта (локальный тест)\nИмя: ${payload.name}\nКонтакт: ${payload.contact}\nЗадача: ${payload.message}`
          )}`;
          setStatus(
            "Локально API недоступен. Открой ссылку в Telegram — сообщение уже собрано.",
            "ok"
          );
          window.open(tg, "_blank", "noopener,noreferrer");
        } else {
          setStatus(
            err.message ||
              "Ошибка отправки. Напиши напрямую в Telegram: @antontsoy",
            "err"
          );
        }
      } finally {
        setLoading(false);
      }
    });
  }

  // Interactive Tabs for Services
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      
      tabBtns.forEach((b) => b.classList.remove("is-active"));
      tabPanes.forEach((p) => p.classList.remove("is-active"));

      btn.classList.add("is-active");
      const activePane = document.getElementById(tabId);
      if (activePane) {
        activePane.classList.add("is-active");
      }
    });
  });

  // Pre-fill form when clicking "Order" on a specific service
  const orderBtns = document.querySelectorAll(".order-service-btn");
  const messageTextarea = document.querySelector('textarea[name="message"]');

  orderBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const serviceName = btn.getAttribute("data-service");
      if (messageTextarea && serviceName) {
        messageTextarea.value = `Здравствуйте! Меня интересует услуга: "${serviceName}". Расскажите, пожалуйста, подробнее о сроках и формате работы.`;
        messageTextarea.focus();
      }
    });
  });

  const revealEls = document.querySelectorAll(
    ".section, .hero__content, .case, .service, .card--hover"
  );
  revealEls.forEach((el) => el.classList.add("reveal"));

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
  );

  revealEls.forEach((el) => io.observe(el));
})();
