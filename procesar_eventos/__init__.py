import azure.functions as func
import os
import requests
import base64
import json
from datetime import datetime, timedelta
from collections import defaultdict

def obtener_inicio_fin_semana():
    hoy = datetime.utcnow()
    inicio = hoy - timedelta(days=hoy.weekday())
    fin = inicio + timedelta(days=6)
    return inicio.date(), fin.date()

def obtener_horas_desde_timelog(work_item_id):
    org = os.getenv("AZURE_ORG")
    pat = os.getenv("DEVOPS_PAT")
    api_version = "7.2-preview.1"

    token = base64.b64encode(f":{pat}".encode()).decode()
    url = f"https://extmgmt.dev.azure.com/{org}/_apis/ExtensionManagement/InstalledExtensions/TechsBCN/DevOps-TimeLog/Data/Scopes/Default/Current/Collections/TimeLogData/Documents"
    headers = {
        "Authorization": f"Basic {token}",
        "Accept": f"application/json;api-version={api_version}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 0

    data = response.json()
    logs = data if isinstance(data, list) else data.get("value", [])
    logs_filtrados = [log for log in logs if str(log.get("workItemId")) == str(work_item_id)]

    total_minutos = sum(log.get("time", 0) for log in logs_filtrados)
    total_horas = round(total_minutos / 60, 2)
    return total_horas

def update_work_item_with_hours(work_item_id, horas_registradas):
    org = os.getenv("AZURE_ORG")
    project = os.getenv("AZ_PROYECTO")
    pat = os.getenv("DEVOPS_PAT")

    auth_header = base64.b64encode(f":{pat}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json-patch+json"
    }

    url = f"https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.0"
    payload = [
        {
            "op": "add",
            "path": "/fields/Custom.HorasRegistradas",
            "value": horas_registradas
        }
    ]

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code, response.text

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        work_item_id = body.get("resource", {}).get("workItemId")

        if not work_item_id:
            return func.HttpResponse("Falta el ID del Work Item", status_code=400)

        horas = obtener_horas_desde_timelog(work_item_id)
        status, result = update_work_item_with_hours(work_item_id, horas)

        if status == 200:
            return func.HttpResponse(f"Horas actualizadas correctamente: {horas}", status_code=200)
        else:
            return func.HttpResponse(f"Error al actualizar Work Item: {result}", status_code=500)

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
