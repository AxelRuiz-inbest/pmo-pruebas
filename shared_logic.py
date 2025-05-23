import os
import requests
import base64
import logging
from datetime import datetime

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
        logging.error(f"Error al consultar TimeLog: {response.status_code} - {response.text}")
        return 0

    data = response.json()
    logs = data if isinstance(data, list) else data.get("value", [])

    filtrados = [l for l in logs if str(l.get("workItemId")) == str(work_item_id)]

    if not filtrados:
        logging.info(f"No se encontraron logs de tiempo para el Work Item {work_item_id}")
        return 0

    for l in filtrados:
        logging.info(f"Entrada encontrada: ID {l.get('workItemId')}, tiempo: {l.get('time')}, fecha: {l.get('date')}")

    total_min = sum(l.get("time", 0) for l in filtrados if isinstance(l.get("time", 0), (int, float)))
    total_hr = round(total_min / 60, 2)

    logging.info(f"Total acumulado para Work Item {work_item_id}: {total_hr} horas")
    return total_hr

def actualizar_task_item_horas(work_item_id, horas):
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
    try:
        org = os.getenv("AZURE_ORG")
        project = os.getenv("AZ_PROYECTO")
        pat = os.getenv("DEVOPS_PAT")

        logging.info(f"Obteniendo tareas modificadas desde el inicio del mes actual - proyecto: {project}")

        if not all([org, project, pat]):
            logging.error("Faltan variables de entorno: AZURE_ORG, AZ_PROYECTO o DEVOPS_PAT")
            return []

        # Obtener la fecha del primer día del mes actual en formato ISO 8601
        ahora = datetime.utcnow()
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        inicio_mes_iso = inicio_mes.isoformat() + "Z"

        logging.info(f"Filtrando tareas desde: {inicio_mes_iso}")

        token = base64.b64encode(f":{pat}".encode()).decode()
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }

        wiql = {
            "query": f"""
                SELECT [System.Id] 
                FROM WorkItems 
                WHERE [System.WorkItemType] = 'Task' 
                  AND [System.TeamProject] = '{project}' 
                  AND [System.ChangedDate] >= '{inicio_mes_iso}'
            """
        }

        url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version=7.0"
        response = requests.post(url, headers=headers, json=wiql)

        if response.status_code != 200:
            logging.error(f"Error ejecutando WIQL: {response.status_code} - {response.text}")
            return []

        work_items = response.json().get("workItems", [])
        logging.info(f"WIQL ejecutado correctamente. {len(work_items)} tareas encontradas este mes.")
        return [item["id"] for item in work_items]

    except Exception as e:
        logging.error(f"Error dentro de obtener_todas_las_tasks: {str(e)}")
        return []
    org = os.getenv("AZURE_ORG")
    project = os.getenv("AZ_PROYECTO")
    pat = os.getenv("DEVOPS_PAT")

    logging.info(f"Obteniendo tareas modificadas desde mayo del proyecto: {project} en la organización: {org}")

    if not all([org, project, pat]):
        logging.error("Variables de entorno faltantes: AZURE_ORG, AZ_PROYECTO o DEVOPS_PAT")
        return []
    
    logging.info(f"Consultando tareas con ChangedDate >= {inicio_mes_iso}")

    ahora = datetime.utcnow()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_mes_iso = inicio_mes.isoformat() + "Z"

    token = base64.b64encode(f":{pat}".encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

    wiql = {
        "query": f"""
            SELECT [System.Id] 
            FROM WorkItems 
            WHERE [System.WorkItemType] = 'Task' 
              AND [System.TeamProject] = '{project}' 
              AND [System.ChangedDate] >= '{inicio_mes_iso}'
        """
    }

    url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version=7.0"
    response = requests.post(url, headers=headers, json=wiql)

    if response.status_code != 200:
        logging.error(f"Error ejecutando WIQL: {response.status_code} - {response.text}")
        return []

    work_items = response.json().get("workItems", [])
    logging.info(f"WIQL ejecutado correctamente. {len(work_items)} tareas encontradas desde mayo.")
    return [item["id"] for item in work_items]