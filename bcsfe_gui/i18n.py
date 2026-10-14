"""Messages shown by the Python side of the GUI, in every supported language."""

from __future__ import annotations

from typing import Any

from . import settings

MESSAGES: dict[str, dict[str, str]] = {
    # Loading a save
    "no_save_loaded": {"en": "No save was loaded.", "es": "No se cargó ningún save."},
    "no_file_selected": {"en": "No file was selected.", "es": "No se seleccionó ningún archivo."},
    "file_not_found": {"en": "File not found: {path}", "es": "No existe el archivo: {path}"},
    "no_documents_save": {
        "en": "There is no save in BCSFE's Documents folder",
        "es": "No hay ningún save en la carpeta de Documentos de BCSFE",
    },
    "no_json_loaded": {"en": "No JSON was loaded.", "es": "No se cargó ningún JSON."},
    "invalid_region": {"en": "Invalid region: {cc}", "es": "Región no válida: {cc}"},
    "download_failed": {
        "en": "Could not download the save. Check the codes, the region and your connection.",
        "es": "No se pudo descargar el save. Revisa los códigos, la región y tu conexión.",
    },
    # Features
    "no_save_open": {"en": "No save is open", "es": "No hay ningún save abierto"},
    "unknown_feature": {"en": "Unknown feature: {path}", "es": "Función desconocida: {path}"},
    "not_a_feature": {"en": "That is a menu, not a feature", "es": "Eso es un menú, no una función"},
    "unknown_option": {"en": "Unknown option", "es": "Opción desconocida"},
    "feature": {"en": "Feature", "es": "Función"},
    # Cats
    "loading_cats": {
        "en": "Loading cat names and data… (the game data is downloaded the first time)",
        "es": "Cargando nombres y datos de los gatos… (la primera vez se descargan los datos del juego)",
    },
    "cats_loaded": {"en": "Loaded data for {total} cats.", "es": "Datos de {total} gatos cargados."},
    "no_cats_selected": {"en": "No cats selected", "es": "No hay gatos seleccionados"},
    "unknown_action": {"en": "Unknown action: {action}", "es": "Acción desconocida: {action}"},
    "cats_selected": {"en": "{count} cat(s) selected.", "es": "{count} gato(s) seleccionado(s)."},
    "no_level_change": {"en": "No level was changed.", "es": "No se cambió ningún nivel."},
    # Tasks
    "task_stopped": {"en": "Task stopped.", "es": "Tarea detenida."},
    "busy": {"en": "A task is already running", "es": "Ya hay una tarea en curso"},
    "wait_task": {"en": "Wait for the current task to finish", "es": "Espera a que termine la tarea en curso"},
    "job_open_file": {"en": "Open save file", "es": "Abrir archivo de guardado"},
    "job_documents": {"en": "Load save from Documents", "es": "Cargar save de Documentos"},
    "job_json": {"en": "Import save from JSON", "es": "Importar save desde JSON"},
    "job_adb": {"en": "Pull save with ADB", "es": "Extraer save por ADB"},
    "job_codes": {"en": "Download save with codes", "es": "Descargar save con códigos"},
    "job_config": {"en": "BCSFE settings", "es": "Configuración de BCSFE"},
    "job_update_external": {"en": "Update external content", "es": "Actualizar contenido externo"},
    "job_game_data": {"en": "Manage game data", "es": "Gestionar datos del juego"},
    "job_cat_meta": {"en": "Loading cat data", "es": "Cargando datos de los gatos"},
    "job_cats": {"en": "Edit cats", "es": "Editar gatos"},
    # API errors
    "host_not_allowed": {"en": "Host not allowed", "es": "Host no permitido"},
    "invalid_token": {"en": "Invalid token", "es": "Token no válido"},
    "not_found": {"en": "Not found", "es": "No encontrado"},
    "unknown_route": {"en": "Unknown route", "es": "Ruta desconocida"},
    "unknown_load_method": {"en": "Unknown load method", "es": "Método de carga desconocido"},
    "codes_required": {
        "en": "Enter the transfer code and the confirmation code",
        "es": "Escribe el código de transferencia y el de confirmación",
    },
    "missing_feature": {"en": "Missing feature", "es": "Falta la función"},
    "invalid_language": {"en": "Invalid language", "es": "Idioma no válido"},
    # Overview resources
    "res_catfood": {"en": "Cat Food", "es": "Comida de gato"},
    "res_xp": {"en": "XP", "es": "XP"},
    "res_normal_tickets": {"en": "Cat Tickets", "es": "Tickets de gato"},
    "res_rare_tickets": {"en": "Rare Tickets", "es": "Tickets raros"},
    "res_platinum_tickets": {"en": "Platinum Tickets", "es": "Tickets de platino"},
    "res_legend_tickets": {"en": "Legend Tickets", "es": "Tickets de leyenda"},
    "res_platinum_shards": {"en": "Platinum Shards", "es": "Fragmentos de platino"},
    "res_np": {"en": "NP", "es": "NP"},
    "res_leadership": {"en": "Leadership", "es": "Liderazgo"},
    # Start-up and file dialogs
    "bcsfe_missing": {
        "en": "Could not load BCSFE.\n\n{error}\n\nInstall it by opening a terminal and running:\n    py -m pip install bcsfe",
        "es": "No se pudo cargar BCSFE.\n\n{error}\n\nInstálalo abriendo una terminal y ejecutando:\n    py -m pip install bcsfe",
    },
    "startup_error": {"en": "Error starting the editor:\n\n{trace}", "es": "Error al iniciar el editor:\n\n{trace}"},
    "json_files": {"en": "JSON files (*.json)", "es": "Archivos JSON (*.json)"},
    "all_files": {"en": "All files (*.*)", "es": "Todos los archivos (*.*)"},
}


def t(key: str, **kwargs: Any) -> str:
    entry = MESSAGES.get(key)
    if entry is None:
        return key
    text = entry.get(settings.current["language"]) or entry["en"]
    return text.format(**kwargs) if kwargs else text
