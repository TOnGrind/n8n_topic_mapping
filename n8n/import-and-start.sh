#!/bin/sh

set -u

WORKFLOW_FILE="/home/node/workflows/automation_workflow.json"
IMPORT_MARKER="/home/node/.n8n/.automation_workflow_imported"

echo "=== n8n Initialisierung ==="
echo "Workflow: ${WORKFLOW_FILE}"

mkdir -p /home/node/.n8n

if [ ! -f "${WORKFLOW_FILE}" ]; then
    echo "FEHLER: Workflow-Datei nicht gefunden."
    ls -la /home/node/workflows || true
    exit 1
fi

if [ ! -f "${IMPORT_MARKER}" ]; then
    echo "Importiere Workflow ..."

    if n8n import:workflow --input="${WORKFLOW_FILE}"; then
        touch "${IMPORT_MARKER}"
        echo "Workflow erfolgreich importiert."
    else
        echo "FEHLER: Workflow-Import fehlgeschlagen."
        exit 1
    fi
else
    echo "Workflow wurde bereits importiert."
fi

echo "Starte n8n auf Port 5678 ..."

exec n8n start