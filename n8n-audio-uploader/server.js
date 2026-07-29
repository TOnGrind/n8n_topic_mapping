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

let latestPdf = null;

// Statische Frontend-Dateien
app.use(express.static(path.join(__dirname, "public")));

// Rohe PDF-Daten empfangen
app.use(
  express.raw({
    type: "application/pdf",
    limit: "20mb",
  })
);

// MP3 an n8n weiterleiten
app.post("/api/upload", upload.single("audio"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: 'Keine Datei im Feld "audio" erhalten.',
      });
    }

    console.log("Webhook-URL:", N8N_WEBHOOK_URL);
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

// PDF vom FastAPI-Server empfangen
app.post("/api/pdf-ready", (req, res) => {
  if (!Buffer.isBuffer(req.body) || req.body.length === 0) {
    return res.status(400).json({
      success: false,
      message: "Keine PDF erhalten.",
    });
  }

  latestPdf = {
    buffer: req.body,
    filename: "serviceprotokoll.pdf",
    createdAt: Date.now(),
  };

  console.log("PDF empfangen:", latestPdf.buffer.length, "Bytes");

  return res.json({
    success: true,
    filename: latestPdf.filename,
  });
});

// Status für das Frontend
app.get("/api/pdf-status", (_req, res) => {
  return res.json({
    ready: Boolean(latestPdf),
    filename: latestPdf?.filename ?? null,
  });
});

// PDF-Download
app.get("/api/pdf-download", (_req, res) => {
  if (!latestPdf) {
    return res.status(404).json({
      success: false,
      message: "Keine PDF verfügbar.",
    });
  }

  res.setHeader("Content-Type", "application/pdf");
  res.setHeader(
    "Content-Disposition",
    `attachment; filename="${latestPdf.filename}"`
  );
  res.setHeader("Content-Length", latestPdf.buffer.length);

  return res.send(latestPdf.buffer);
});

// Nur einmal starten
app.listen(PORT, () => {
  console.log(`Frontend läuft auf http://localhost:${PORT}`);
});
