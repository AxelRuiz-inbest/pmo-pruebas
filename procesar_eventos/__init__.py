import azure.functions as func
import json
import logging
from shared_logic import obtener_horas_desde_timelog, actualizar_task_item_horas

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        logging.info(f"Payload recibido: {json.dumps(body)}")

        work_item_id = body.get("resource", {}).get("id")

        if not work_item_id:
            return func.HttpResponse("Falta el ID del Work Item en resource.id", status_code=400)

        horas = obtener_horas_desde_timelog(work_item_id)
        status, result = actualizar_task_item_horas(work_item_id, horas)

        if status == 200:
            return func.HttpResponse(f"Horas actualizadas correctamente: {horas}", status_code=200)
        else:
            return func.HttpResponse(f"Error al actualizar Work Item: {result}", status_code=500)

    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
