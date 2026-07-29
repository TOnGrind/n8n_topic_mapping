const MAX_FILE_SIZE = 100 * 1024 * 1024;

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const webhookUrl = document.getElementById("webhookUrl");
const uploadButton = document.getElementById("uploadButton");
const removeButton = document.getElementById("removeButton");
const fileCard = document.getElementById("fileCard");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const audioPreview = document.getElementById("audioPreview");
const progressWrap = document.getElementById("progressWrap");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const message = document.getElementById("message");
const responseBox = document.getElementById("responseBox");
const responseText = document.getElementById("responseText");

let selectedFile = null;
let objectUrl = null;
let currentRequest = null;

function formatBytes(bytes) {
  if (!bytes) return "0 Byte";
  const units = ["Byte", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function showMessage(text, type) {
  message.textContent = text;
  message.className = `message ${type}`;
}

function clearMessage() {
  message.textContent = "";
  message.className = "message hidden";
  responseBox.classList.add("hidden");
  responseText.textContent = "";
}

function isMp3(file) {
  return (
    file.name.toLowerCase().endsWith(".mp3") ||
    ["audio/mpeg", "audio/mp3", "audio/x-mpeg"].includes(file.type)
  );
}

function chooseFile(file) {
  clearMessage();

  if (!file) return;

  if (!isMp3(file)) {
    showMessage("Bitte wähle eine MP3-Datei aus.", "error");
    return;
  }

  if (file.size > MAX_FILE_SIZE) {
    showMessage("Die Datei darf maximal 100 MB groß sein.", "error");
    return;
  }

  selectedFile = file;
  fileName.textContent = file.name;
  fileSize.textContent = formatBytes(file.size);
  fileCard.classList.remove("hidden");
  uploadButton.disabled = false;

  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = URL.createObjectURL(file);
  audioPreview.src = objectUrl;
  audioPreview.classList.remove("hidden");

  showMessage("Datei ist bereit zum Hochladen.", "info");
}

function resetFile() {
  if (currentRequest) {
    currentRequest.abort();
    currentRequest = null;
  }

  selectedFile = null;
  fileInput.value = "";
  fileCard.classList.add("hidden");
  audioPreview.classList.add("hidden");
  audioPreview.removeAttribute("src");
  audioPreview.load();
  uploadButton.disabled = true;
  progressWrap.classList.add("hidden");
  progressBar.style.width = "0%";
  progressText.textContent = "0%";
  clearMessage();

  if (objectUrl) {
    URL.revokeObjectURL(objectUrl);
    objectUrl = null;
  }
}

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    fileInput.click();
  }
});

fileInput.addEventListener("change", () => chooseFile(fileInput.files[0]));

["dragenter", "dragover"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragging");
  });
});

dropzone.addEventListener("drop", (event) => {
  chooseFile(event.dataTransfer.files[0]);
});

removeButton.addEventListener("click", resetFile);

uploadButton.addEventListener("click", () => {
  clearMessage();

  if (!selectedFile) {
    showMessage("Bitte wähle zuerst eine MP3-Datei aus.", "error");
    return;
  }

  let url;
  try {
    url = new URL(webhookUrl.value.trim());
  } catch {
    showMessage("Die Webhook-URL ist ungültig.", "error");
    return;
  }

 const formData = new FormData();

formData.append("audio", selectedFile, selectedFile.name);
formData.append("webhookUrl", url.toString());

const xhr = new XMLHttpRequest();
currentRequest = xhr;

xhr.open("POST", "/api/upload");


  uploadButton.disabled = true;
  uploadButton.textContent = "Wird gesendet …";
  progressWrap.classList.remove("hidden");
  showMessage("Upload läuft …", "info");

  xhr.upload.addEventListener("progress", (event) => {
    if (!event.lengthComputable) return;
    const percent = Math.round((event.loaded / event.total) * 100);
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
  });

  xhr.addEventListener("load", () => {
    currentRequest = null;
    uploadButton.disabled = false;
    uploadButton.textContent = "An n8n senden";
    progressBar.style.width = "100%";
    progressText.textContent = "100%";

    if (xhr.status >= 200 && xhr.status < 300) {
      showMessage("Die MP3-Datei wurde erfolgreich an n8n gesendet.", "success");
    } else {
      showMessage(`Der Webhook antwortete mit HTTP ${xhr.status}.`, "error");
    }

    if (xhr.responseText) {
      responseText.textContent = xhr.responseText;
      responseBox.classList.remove("hidden");
    }
  });

  xhr.addEventListener("error", () => {
    currentRequest = null;
    uploadButton.disabled = false;
    uploadButton.textContent = "An n8n senden";
    showMessage(
      "Netzwerkfehler. Prüfe, ob n8n läuft und ob CORS erlaubt ist.",
      "error"
    );
  });

  xhr.addEventListener("abort", () => {
    currentRequest = null;
    uploadButton.disabled = false;
    uploadButton.textContent = "An n8n senden";
    showMessage("Upload wurde abgebrochen.", "info");
  });

  xhr.send(formData);
});


const pdfDownload = document.getElementById("pdfDownload");

async function checkPdfStatus() {
  try {
    const response = await fetch("/api/pdf-status");
    const result = await response.json();

    if (result.ready) {
      pdfDownload.classList.remove("hidden");
      return;
    }
  } catch (error) {
    console.error("Statusprüfung fehlgeschlagen:", error);
  }

  setTimeout(checkPdfStatus, 2000);
}

checkPdfStatus();