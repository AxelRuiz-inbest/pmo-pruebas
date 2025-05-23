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
        logging.error(f"Error obteniendo TimeLog: {response.text}")
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
    if response.status_code != 200:
        logging.error(f"Error actualizando {work_item_id}: {response.text}")
    return response.status_code, response.text

def obtener_todas_las_tasks():
    org = os.getenv("AZURE_ORG")
    project = os.getenv("AZ_PROYECTO")
    pat = os.getenv("DEVOPS_PAT")

    token = base64.b64encode(f":{pat}".encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

    wiql = {
        "query": f"SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Task' AND [System.TeamProject] = '{project}'"
    }

    url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version=7.0"
    response = requests.post(url, headers=headers, json=wiql)

    if response.status_code != 200:
        logging.error(f"Error ejecutando WIQL: {response.text}")
        return []

    work_items = response.json().get("workItems", [])
    return [item["id"] for item in work_items]

def main(mytimer: func.TimerRequest) -> None:
    logging.info('Iniciando sincronización de horas para tareas...')
    try:
        ids = obtener_todas_las_tasks()
        logging.info(f"Se encontraron {len(ids)} tareas para actualizar.")

        for work_item_id in ids:
            horas = obtener_horas_desde_timelog(work_item_id)
            update_work_item_with_hours(work_item_id, horas)

        logging.info("Sincronización completada.")
    except Exception as e:
        logging.error(f"Error en ejecución programada: {str(e)}")
