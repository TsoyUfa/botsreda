/**
 * Vercel Serverless: отправка заявки в Telegram.
 * Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
 */
module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;

  if (!token || !chatId) {
    return res.status(503).json({
      error: "Сервер не настроен: добавь TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в Vercel",
    });
  }

  let body = req.body;
  if (typeof body === "string") {
    try {
      body = JSON.parse(body);
    } catch {
      return res.status(400).json({ error: "Invalid JSON" });
    }
  }

  const name = String(body?.name || "").trim().slice(0, 120);
  const contact = String(body?.contact || "").trim().slice(0, 120);
  const message = String(body?.message || "").trim().slice(0, 2000);

  if (!name || !contact || !message) {
    return res.status(400).json({ error: "Заполни все поля" });
  }

  const text = [
    "🟢 Новая заявка с сайта",
    "",
    `Имя: ${name}`,
    `Контакт: ${contact}`,
    "",
    `Задача:\n${message}`,
  ].join("\n");

  try {
    const tgRes = await fetch(
      `https://api.telegram.org/bot${token}/sendMessage`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text,
          disable_web_page_preview: true,
        }),
      }
    );

    const tgData = await tgRes.json();
    if (!tgRes.ok || !tgData.ok) {
      console.error("Telegram error:", tgData);
      return res.status(502).json({ error: "Не удалось отправить в Telegram" });
    }

    return res.status(200).json({ ok: true });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ error: "Ошибка сервера" });
  }
};
