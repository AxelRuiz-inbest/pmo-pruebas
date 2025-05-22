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

def main(req: func.HttpRequest) -> func.HttpResponse:
    usuario = req.params.get('usuario')
    if not usuario:
        return func.HttpResponse("Falta el parámetro 'usuario'", status_code=400)

    org = os.getenv("AZURE_ORG")
    pat = os.getenv("DEVOPS_PAT")
    api_version = "7.2-preview.1"

    if not all([org, pat]):
        return func.HttpResponse("Faltan variables de entorno requeridas", status_code=500)

    url = f"https://extmgmt.dev.azure.com/{org}/_apis/ExtensionManagement/InstalledExtensions/TechsBCN/DevOps-TimeLog/Data/Scopes/Default/Current/Collections/TimeLogData/Documents"

    token = base64.b64encode(f":{pat}".encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Accept": f"application/json;api-version={api_version}"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return func.HttpResponse(
                json.dumps({"error": response.text, "status": response.status_code}, indent=2),
                mimetype="application/json",
                status_code=500
            )

        data = response.json()
        logs = data if isinstance(data, list) else data.get("value", [])
        inicio_semana, fin_semana = obtener_inicio_fin_semana()

        filtrados = [
            log for log in logs
            if log.get("user") == usuario and
            "date" in log and
            inicio_semana <= datetime.fromisoformat(log["date"]).date() <= fin_semana
        ]

        if not filtrados:
            return func.HttpResponse(
                json.dumps({
                    "mensaje": f"No se encontraron registros esta semana para '{usuario}'"
                }, indent=2),
                mimetype="application/json"
            )

        agrupado = defaultdict(list)
        total = 0

        for log in filtrados:
            wid = str(log.get("workItemId"))
            agrupado[wid].append({
                "fecha": log.get("date"),
                "tipo": log.get("type"),
                "minutos": log.get("time"),
                "nota": log.get("notes")
            })
            total += log.get("time", 0)

        respuesta = {
            "usuario": usuario,
            "semana": {
                "inicio": str(inicio_semana),
                "fin": str(fin_semana)
            },
            "total_minutos": total,
            "total_horas": round(total / 60, 2),
            "tareas": agrupado
        }

        return func.HttpResponse(json.dumps(respuesta, indent=2), mimetype="application/json")

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}), mimetype="application/json", status_code=500
        )
