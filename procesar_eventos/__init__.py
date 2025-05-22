import azure.functions as func
import os
import requests
import base64
import json
from collections import defaultdict

def main(req: func.HttpRequest) -> func.HttpResponse:
    workitem_id = req.params.get('id')
    if not workitem_id:
        return func.HttpResponse("Falta el parámetro 'id'", status_code=400)

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
        filtrados = [log for log in logs if str(log.get("workItemId")) == str(workitem_id)]

        if not filtrados:
            return func.HttpResponse(
                json.dumps({"mensaje": f"No se encontraron registros para el Work Item {workitem_id}"}),
                mimetype="application/json"
            )

        total_min = sum(log.get("time", 0) for log in filtrados)

        agrupados = defaultdict(list)
        for log in filtrados:
            agrupados[log.get("date")].append({
                "usuario": log.get("user"),
                "tipo": log.get("type"),
                "minutos": log.get("time")
            })

        resultado = {
            "workItemId": workitem_id,
            "total_minutos": total_min,
            "total_horas": round(total_min / 60, 2),
            "logs_por_fecha": agrupados
        }

        return func.HttpResponse(json.dumps(resultado, indent=2), mimetype="application/json")

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}), mimetype="application/json", status_code=500
        )
