import azure.functions as func
import os
import requests
import base64
import json
import logging

def obtener_horas_desde_timelog(work_item_id):
    org = os.getenv("AZURE_ORG")
    pat = os.getenv("DEVOPS_PAT")

    token = base64.b64encode(f":{pat}".encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Accept": "application/json;api-version=7.2-preview.1"
    }

    url = f"https://extmgmt.dev.azure.com/{org}/_apis/ExtensionManagement/InstalledExtensions/TechsBCN/DevOps-TimeLog/Data/Scopes/Default/Current/Collections/TimeLogData/Documents"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return 0

    data = response.json()
    logs = data if isinstance(data, list) else data.get("value", [])
    filtrados = [l for l in logs if str(l.get("workItemId")) == str(work_item_id)]
    total = sum(l.get("time", 0) for l in filtrados)
    return round(total / 60, 2)

def update_work_item_with_hours(work_item_id, horas):
    org = os.getenv("AZURE_ORG")
    project = os.getenv("AZ_PROYECTO")
    pat = os.getenv("DEVOPS_PAT")

    token = base64.b64encode(f":{pat}".encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json-patch+json"
    }

    url = f"https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.0"
    payload = [{
        "op": "add",
        "path": "/fields/Horas Registrada",
        "value": horas
    }]

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code, response.text

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        logging.info(f"Payload recibido: {json.dumps(body)}")

        work_item_id = body.get("resource", {}).get("id")

        if not work_item_id:
            return func.HttpResponse("Falta el ID del Work Item en resource.id", status_code=400)

        horas = obtener_horas_desde_timelog(work_item_id)
        status, result = update_work_item_with_hours(work_item_id, horas)

        if status == 200:
            return func.HttpResponse(f"Horas actualizadas correctamente: {horas}", status_code=200)
        else:
            return func.HttpResponse(f"Error al actualizar Work Item: {result}", status_code=500)

    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
