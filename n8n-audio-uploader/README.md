# n8n Audio Uploader für Node.js 20.2.0

Diese Version verwendet kein Vite und kein Rolldown. Sie läuft mit Node.js 20.2.0.

## Start

```powershell
npm install
npm start
```

Danach im Browser öffnen:

```text
http://localhost:3000
```

## n8n testen

1. Webhook-Node auf `POST` stellen.
2. Auf `Listen for test event` klicken.
3. Im Frontend die Test-URL eintragen:
   `http://localhost:5678/webhook-test/DEINE_ID`
4. MP3 auswählen und hochladen.

Die Datei wird im Formularfeld `audio` gesendet und sollte in n8n unter
`$binary.audio` erscheinen.

## Produktiv

Workflow aktivieren und in der URL `/webhook-test/` durch `/webhook/` ersetzen.

## CORS

Sollte der Browser einen CORS-Fehler melden, muss n8n Requests von
`http://localhost:3000` erlauben.
