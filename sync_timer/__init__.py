import azure.functions as func
import logging
from shared_logic import obtener_todas_las_tasks, obtener_horas_desde_timelog, actualizar_task_item_horas

def main(mytimer: func.TimerRequest) -> None:
    logging.info("Inicio del Timer Trigger - Sincronización de tareas")

    try:
        ids = obtener_todas_las_tasks()
        logging.info(f"Se encontraron {len(ids)} tareas tipo 'Task' para procesar")

        for wid in ids:
            horas = obtener_horas_desde_timelog(wid)
            logging.info(f"Task {wid}: {horas} horas obtenidas desde TimeLog")

            status, response = actualizar_task_item_horas(wid, horas)

            if status == 200:
                logging.info(f"Task {wid} actualizada con éxito ({horas} horas registradas)")
            else:
                logging.error(f"Error actualizando Task {wid}: {response}")

        logging.info("Finalizó la sincronización de tareas correctamente")

    except Exception as e:
        logging.error(f"Error durante la sincronización: {str(e)}")
