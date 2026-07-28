const express = require("express");
const multer = require("multer");
const path = require("path");

const app = express();

const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 100 * 1024 * 1024,
  },
});

const PORT = process.env.PORT || 3000;

const N8N_WEBHOOK_URL =
  "http://localhost:5678/webhook/0e8824b2-8b66-4c84-b143-8ed3863eb4cf";

app.use(express.static(path.join(__dirname, "public")));

app.post("/api/upload", upload.single("audio"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: 'Keine Datei im Feld "audio" erhalten.',
      });
    }

    console.log("Exakte Webhook-URL:", JSON.stringify(N8N_WEBHOOK_URL));
    console.log("Datei:", {
      name: req.file.originalname,
      type: req.file.mimetype,
      size: req.file.size,
    });

    const formData = new FormData();

    const audioBlob = new Blob([req.file.buffer], {
      type: req.file.mimetype || "audio/mpeg",
    });

    formData.append("audio", audioBlob, req.file.originalname);

    const n8nResponse = await fetch(N8N_WEBHOOK_URL, {
      method: "POST",
      body: formData,
    });

    const responseText = await n8nResponse.text();

    console.log("n8n Status:", n8nResponse.status);
    console.log("n8n Antwort:", responseText);

    return res.status(n8nResponse.status).json({
      success: n8nResponse.ok,
      status: n8nResponse.status,
      webhookUrl: N8N_WEBHOOK_URL,
      n8nResponse: responseText,
    });
  } catch (error) {
    console.error("Upload-Fehler:", error);

    return res.status(500).json({
      success: false,
      message: error.message,
    });
  }
});

app.listen(PORT, () => {
  console.log(`Frontend läuft auf http://localhost:${PORT}`);
});