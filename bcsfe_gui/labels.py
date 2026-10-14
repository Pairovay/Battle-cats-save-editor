"""Names, descriptions and icons for BCSFE's menus and features.

Keys are the ones used by ``bcsfe.cli.feature_handler``. If BCSFE adds a
feature that is not listed here, the GUI still shows it with BCSFE's own name.
"""

from __future__ import annotations

from . import settings

# category -> (icon, English name, English description, Spanish name, Spanish description)
CATEGORIES: dict[str, tuple[str, str, str, str, str]] = {
    "save_management": ("save", "Save & sync", "Save, upload to the game servers, export or load another save.",
                        "Partida y guardado", "Guardar, subir a los servidores, exportar o cargar otro save."),
    "items": ("box", "Items", "Cat Food, tickets, XP, Catseyes, Catfruit, orbs and more.",
              "Objetos", "Comida de gato, tickets, XP, Catseyes, frutas, orbes y más."),
    "cats_special_skills": ("cat", "Cats & skills", "BCSFE options for cats, special skills and cat storage.",
                            "Gatos y habilidades", "Opciones de BCSFE para gatos, habilidades especiales y almacén."),
    "levels": ("map", "Levels & maps", "Story, events, treasures, Legend stages, towers, Dojo…",
               "Niveles y mapas", "Historia, eventos, tesoros, Legend, torres, Dojo…"),
    "gamototo": ("flask", "Gamatoto & Ototo", "Engineers, materials, cat cannon and Gamatoto.",
                 "Gamatoto y Ototo", "Ingenieros, materiales, cañón y Gamatoto."),
    "account": ("user", "Account", "Unban, inquiry code and managed items.",
                "Cuenta", "Desbaneo, código de consulta y objetos gestionados."),
    "gatya": ("dice", "Gacha", "Gacha seeds.", "Gacha", "Semillas de los gachas."),
    "fixes": ("wrench", "Fixes", "Fixes for game crashes and errors.",
              "Arreglos", "Soluciones a cierres y errores del juego."),
    "other": ("dots", "Other", "Slots, medals, missions, Gold Pass, play time…",
              "Otros", "Huecos, medallas, misiones, Gold Pass, tiempo de juego…"),
    "editor": ("gear", "Editor settings", "BCSFE settings and game data.",
               "Ajustes del editor", "Configuración de BCSFE y datos del juego."),
}

# feature -> (icon, flag, English name, English description, Spanish name, Spanish description)
# flag: "" | "ban" (may get the account banned) | "warn" (advanced, use with care)
FEATURES: dict[str, tuple[str, str, str, str, str, str]] = {
    # --- Save & sync
    "save_save": ("save", "", "Save changes", "Saves the save to the file you have open.",
                  "Guardar cambios", "Guarda el save en el archivo que tienes abierto."),
    "save_upload": ("upload", "", "Save & upload (get codes)",
                    "Uploads the save to the game servers and gives you a new transfer code and confirmation code to restore it on your phone.",
                    "Guardar y subir (obtener códigos)",
                    "Sube el save a los servidores del juego y te da un código de transferencia y de confirmación nuevos para recuperarlo en el móvil."),
    "save_save_file": ("save-as", "", "Save as…", "Choose where to save the SAVE_DATA file.",
                       "Guardar como…", "Elige dónde guardar el archivo SAVE_DATA."),
    "save_save_data_dir": ("folder", "", "Save to Documents", "Saves the save in BCSFE's folder inside Documents.",
                           "Guardar en Documentos", "Guarda el save en la carpeta de BCSFE de tus Documentos."),
    "adb_push": ("phone", "warn", "Send to phone (ADB)", "Saves and copies the save to the device connected via ADB.",
                 "Enviar al móvil (ADB)", "Guarda y copia el save al dispositivo conectado por ADB."),
    "adb_push_rerun": ("phone", "warn", "Send via ADB and restart", "Copies the save via ADB and reopens the game.",
                       "Enviar por ADB y reiniciar", "Copia el save por ADB y vuelve a abrir el juego."),
    "root_push": ("phone", "warn", "Send with root", "Copies the save into the game on a rooted Android device.",
                  "Enviar con root", "Copia el save al juego en un dispositivo Android con root."),
    "root_push_rerun": ("phone", "warn", "Send with root and restart", "Copies the save with root and reopens the game.",
                        "Enviar con root y reiniciar", "Copia el save con root y vuelve a abrir el juego."),
    "export_save": ("export", "", "Export to JSON", "Exports the whole save to a readable JSON file.",
                    "Exportar a JSON", "Exporta todo el save a un archivo JSON legible."),
    "load_save": ("open", "", "Load another save", "Switch to another save file.",
                  "Cargar otro save", "Cambia a otro archivo de guardado."),
    "convert_region": ("globe", "warn", "Change region", "Converts the save to another region (en, jp, kr, tw).",
                       "Cambiar región", "Convierte el save a otra región (en, jp, kr, tw)."),
    "convert_version": ("tag", "warn", "Change game version", "Changes the game version stored in the save.",
                        "Cambiar versión del juego", "Cambia la versión del juego guardada en el save."),
    # --- Items
    "catfood": ("item:CatFood", "ban", "Cat Food", "Edit Cat Food.", "Comida de gato", "Edita la comida de gato (Cat Food)."),
    "xp": ("xp", "", "XP", "Edit XP.", "XP", "Edita la experiencia (XP)."),
    "normal_tickets": ("ticket", "", "Cat Tickets", "Edit normal Cat Tickets.", "Tickets de gato", "Edita los tickets normales."),
    "rare_tickets": ("ticket", "ban", "Rare Tickets", "Edit Rare Tickets.", "Tickets raros", "Edita los tickets raros."),
    "rare_ticket_trade_feature_name": ("ticket", "", "Rare Ticket trade (safe)", "Get Rare Tickets more safely through the in-game trade.",
                                       "Canje de tickets raros (seguro)", "Consigue tickets raros de forma más segura mediante el canje del juego."),
    "platinum_tickets": ("ticket", "ban", "Platinum Tickets", "Edit Platinum Tickets.", "Tickets de platino", "Edita los tickets de platino."),
    "legend_tickets": ("ticket", "ban", "Legend Tickets", "Edit Legend Tickets.", "Tickets de leyenda", "Edita los tickets de leyenda."),
    "platinum_shards": ("gem", "", "Platinum Shards", "Edit Platinum Shards (safer than tickets).",
                        "Fragmentos de platino", "Edita los fragmentos de platino (más seguro que los tickets)."),
    "np": ("np", "", "NP", "Edit NP.", "NP", "Edita los NP."),
    "leadership": ("flag", "", "Leadership", "Edit Leadership.", "Liderazgo", "Edita el liderazgo (Leadership)."),
    "battle_items": ("item:Item0", "", "Battle items", "Speed Up, Treasure Radar, Rich Cat, Cat CPU, Cat Jobs and Sniper the Cat.",
                     "Objetos de batalla", "Speed Up, Treasure Radar, Rich Cat, Cat CPU, Cat Jobs y Sniper."),
    "battle_items_endless": ("item:Item3", "", "Endless battle items", "Make battle items unlimited for a while.",
                             "Objetos de batalla infinitos", "Activa objetos de batalla sin límite durante un tiempo."),
    "catseyes": ("item:Cateye3", "", "Catseyes", "Edit Catseyes to raise level caps.",
                 "Catseyes", "Edita los ojos de gato para subir el nivel máximo."),
    "catfruit": ("fruit", "", "Catfruit & seeds", "Edit Catfruit and seeds for true forms.",
                 "Frutas y semillas", "Edita las frutas y semillas para formas verdaderas."),
    "talent_orbs": ("orb", "", "Talent Orbs", "Edit Talent Orbs.", "Orbes de talento", "Edita los orbes de talento."),
    "catamins": ("flask", "", "Catamins", "Edit Catamins (A, B and C).", "Catamins", "Edita las Catamins (A, B y C)."),
    "scheme_items": ("scroll", "", "Scheme items", "Edit Scheme Items.", "Objetos de planos", "Edita los objetos de planos (Scheme Items)."),
    "labyrinth_medals": ("medal", "", "Labyrinth medals", "Edit Labyrinth medals.", "Medallas del laberinto", "Edita las medallas del laberinto."),
    "100_million_tickets": ("ticket", "warn", "100 Million ticket", "Edit the 100 Million Downloads tickets.",
                            "Ticket de 100 millones", "Edita los tickets de 100 millones de descargas."),
    "event_tickets": ("ticket", "", "Event tickets", "Edit event tickets and lucky tickets.",
                      "Tickets de evento", "Edita tickets de eventos y lucky tickets."),
    "treasure_chests": ("chest", "", "Treasure chests", "Edit treasure chests.", "Cofres del tesoro", "Edita los cofres del tesoro."),
    "reset_golden_cat_cpus": ("refresh", "", "Reset Golden Cat CPU", "Reset the Golden Cat CPU usage counter.",
                              "Reiniciar Golden Cat CPU", "Reinicia el contador de Golden Cat CPU."),
    # --- Cats & skills
    "cats": ("cat", "", "Cat editor (BCSFE)", "Select cats with BCSFE's options and edit them.",
             "Editor de gatos (BCSFE)", "Selecciona gatos con las opciones de BCSFE y edítalos."),
    "unlock_remove_cats": ("unlock", "", "Unlock / remove cats", "Unlock or remove cats.",
                           "Desbloquear / quitar gatos", "Desbloquea o elimina gatos."),
    "upgrade_cats": ("level", "", "Upgrade cats", "Change cats' level and plus level.",
                     "Subir nivel de gatos", "Cambia el nivel y el nivel + de los gatos."),
    "true_form_remove_form_cats": ("star", "", "True form", "Give or remove cats' true form.",
                                   "Forma verdadera", "Da o quita la forma verdadera a los gatos."),
    "force_true_form_cats": ("star", "warn", "Force true form", "Give the true form even if the cat doesn't officially have one.",
                             "Forzar forma verdadera", "Da la forma verdadera aunque el gato no la tenga oficialmente."),
    "fourth_form_remove_form_cats": ("star", "", "Fourth form", "Give or remove the fourth (ultra) form.",
                                     "Cuarta forma", "Da o quita la cuarta forma (ultra forma)."),
    "force_fourth_form_cats": ("star", "warn", "Force fourth form", "Give the fourth form even if the cat doesn't officially have one.",
                               "Forzar cuarta forma", "Da la cuarta forma aunque el gato no la tenga oficialmente."),
    "upgrade_talents_remove_talents_cats": ("orb", "", "Talents", "Max out, edit or remove cats' talents.",
                                            "Talentos", "Sube al máximo, edita o quita los talentos de los gatos."),
    "unlock_remove_cat_guide": ("book", "", "Cat Guide", "Claim or unclaim cats in the Cat Guide.",
                                "Guía de gatos", "Registra o quita gatos de la guía (Cat Guide)."),
    "special_skills": ("level", "", "Special skills", "Base upgrades: cannon, wallet, research, etc.",
                       "Habilidades especiales", "Mejoras de la base: cañón, cartera, investigación, etc."),
    "cat_storage": ("box", "", "Cat storage", "Edit the cat and item storage.", "Almacén de gatos", "Edita el almacén de gatos y objetos."),
    # --- Levels & maps
    "clear_tutorial": ("check", "", "Clear tutorial", "Mark the tutorial as completed.",
                       "Completar tutorial", "Marca el tutorial como completado."),
    "clear_story": ("map", "", "Main story", "Clear story chapters (EoC, ItF, CotC).",
                    "Historia principal", "Completa capítulos de la historia (EoC, ItF, CotC)."),
    "challenge_score": ("trophy", "", "Challenge Battle", "Edit the Challenge Battle score.",
                        "Challenge Battle", "Edita la puntuación de Challenge Battle."),
    "dojo_score": ("trophy", "", "Dojo score", "Edit the Dojo score.", "Puntuación del Dojo", "Edita la puntuación del Dojo."),
    "add_enigma_stages": ("puzzle", "", "Add Enigma stages", "Add available Enigma stages.",
                          "Añadir escenarios Enigma", "Añade escenarios Enigma disponibles."),
    "clear_enigma_stages": ("puzzle", "", "Clear Enigma stages", "Mark Enigma stages as cleared.",
                            "Completar escenarios Enigma", "Marca escenarios Enigma como completados."),
    "unlock_aku_realm": ("unlock", "", "Unlock Aku Realm", "Unlock the Aku Realm.", "Desbloquear Aku Realm", "Desbloquea el reino Aku."),
    "story_treasures": ("chest", "", "Story treasures", "Edit story treasures.", "Tesoros de la historia", "Edita los tesoros de la historia."),
    "outbreaks": ("map", "", "Zombie outbreaks", "Clear or edit zombie outbreaks.", "Brotes zombi", "Completa o edita los brotes zombi (Outbreaks)."),
    "aku_chapters": ("map", "", "Aku chapters", "Clear Aku Realm chapters.", "Capítulos Aku", "Completa capítulos del reino Aku."),
    "itf_timed_scores": ("clock", "", "Timed scores (ItF)", "Edit Into the Future timed scores.",
                         "Puntuaciones con tiempo (ItF)", "Edita las puntuaciones con tiempo de Into the Future."),
    "filibuster_reclearing": ("refresh", "", "Replay Filibuster Invasion", "Allow playing the Filibuster stage again.",
                              "Repetir Filibuster Invasion", "Permite volver a jugar el escenario Filibuster."),
    "sol": ("map", "", "Stories of Legend", "Clear Stories of Legend stages.", "Stories of Legend", "Completa escenarios de Stories of Legend."),
    "event": ("map", "", "Event stages", "Clear event stages.", "Escenarios de evento", "Completa escenarios de eventos."),
    "collab": ("map", "", "Collab stages", "Clear collaboration stages.", "Escenarios de colaboración", "Completa escenarios de colaboraciones."),
    "gauntlets": ("map", "", "Gauntlets", "Clear Gauntlets.", "Gauntlets", "Completa Gauntlets."),
    "collab_gauntlets": ("map", "", "Collab gauntlets", "Clear collaboration Gauntlets.",
                         "Gauntlets de colaboración", "Completa Gauntlets de colaboraciones."),
    "uncanny": ("map", "", "Uncanny Legends", "Clear Uncanny Legends stages.", "Uncanny Legends", "Completa escenarios de Uncanny Legends."),
    "catamin_stages": ("map", "", "Catamin stages", "Clear Catamin stages.", "Escenarios Catamin", "Completa escenarios de Catamin."),
    "behemoth_culling": ("map", "", "Behemoth Culling", "Clear Behemoth Culling stages.",
                         "Behemoth Culling", "Completa escenarios de Behemoth Culling."),
    "legend_quest": ("map", "", "Legend Quest", "Clear Legend Quest.", "Legend Quest", "Completa Legend Quest."),
    "towers": ("tower", "", "Towers", "Clear tower floors.", "Torres", "Completa pisos de las torres."),
    "zero_legends": ("map", "", "Zero Legends", "Clear Zero Legends stages.", "Zero Legends", "Completa escenarios de Zero Legends."),
    "dojo_catclaw_championships": ("trophy", "", "Catclaw Championships", "Edit the Dojo Catclaw Championships.",
                                   "Campeonato Catclaw", "Edita el Catclaw Championships del Dojo."),
    # --- Gamatoto & Ototo
    "engineers": ("wrench", "", "Engineers", "Edit Ototo engineers.", "Ingenieros", "Edita los ingenieros de Ototo."),
    "base_materials": ("box", "", "Base materials", "Edit materials for the cat cannon.",
                       "Materiales de base", "Edita los materiales para el cañón."),
    "gamatoto_xp_level": ("level", "", "Gamatoto XP / level", "Edit Gamatoto's XP and level.",
                          "XP / nivel de Gamatoto", "Edita la experiencia y el nivel de Gamatoto."),
    "gamatoto_helpers": ("user", "", "Gamatoto helpers", "Edit Gamatoto's helper team.",
                         "Ayudantes de Gamatoto", "Edita el equipo de ayudantes de Gamatoto."),
    "ototo_cat_cannon": ("cannon", "", "Cat cannon", "Upgrade the cat cannon parts.", "Cañón de gato", "Mejora las partes del cañón de gato."),
    "cat_shrine": ("shrine", "", "Cat shrine", "Edit the shrine level and XP.", "Santuario de gato", "Edita el nivel y la XP del santuario."),
    # --- Account
    "unban_account": ("shield", "warn", "Unban account", "Create a new account for the save if it's banned.",
                      "Quitar baneo", "Crea una cuenta nueva para el save si está baneado."),
    "upload_items": ("upload", "", "Upload managed items", "Send items (Cat Food, tickets…) to the server to avoid bans.",
                     "Subir objetos gestionados", "Envía al servidor los objetos (comida de gato, tickets…) para evitar baneos."),
    "inquiry_code": ("key", "warn", "Inquiry code", "Edit the inquiry code.", "Código de consulta", "Edita el código de consulta (inquiry code)."),
    "password_refresh_token": ("key", "warn", "Password token", "Edit the password refresh token.",
                               "Token de contraseña", "Edita el token de actualización de contraseña."),
    # --- Gacha
    "rare_gatya_seed": ("dice", "warn", "Rare gacha seed", "Edit the rare gacha seed.", "Semilla del gacha raro", "Edita la semilla del gacha raro."),
    "normal_gatya_seed": ("dice", "warn", "Normal gacha seed", "Edit the normal gacha seed.",
                          "Semilla del gacha normal", "Edita la semilla del gacha normal."),
    "event_gatya_seed": ("dice", "warn", "Event gacha seed", "Edit the event gacha seed.",
                         "Semilla del gacha de evento", "Edita la semilla del gacha de evento."),
    # --- Fixes
    "fix_gamatoto_crash": ("wrench", "", "Fix Gamatoto crash", "Fix the game crashing when opening Gamatoto.",
                           "Arreglar cierre de Gamatoto", "Soluciona que el juego se cierre al abrir Gamatoto."),
    "fix_ototo_crash": ("wrench", "", "Fix Ototo crash", "Fix the game crashing when opening Ototo.",
                        "Arreglar cierre de Ototo", "Soluciona que el juego se cierre al abrir Ototo."),
    "fix_time_errors": ("clock", "", "Fix time errors", "Fix the game's time and date errors.",
                        "Arreglar errores de hora", "Soluciona los errores de hora/fecha del juego."),
    "unlock_equip_menu": ("unlock", "", "Unlock equip menu", "Unlock the Equip menu.",
                          "Desbloquear menú de equipo", "Desbloquea el menú de equipo (Equip)."),
    "fix_officer_pass_crash": ("wrench", "", "Fix Officer Pass crash", "Fix the Officer Club crash.",
                               "Arreglar cierre del Officer Pass", "Soluciona el cierre relacionado con el Officer Club."),
    # --- Other
    "unlocked_slots": ("grid", "", "Lineup slots", "Edit how many lineup slots are unlocked.",
                       "Huecos de formación", "Edita cuántos huecos de formación hay desbloqueados."),
    "reset_gambling_events": ("refresh", "", "Reset gambling events", "Reset the gambling events.",
                              "Reiniciar eventos de apuestas", "Reinicia los eventos de apuestas (Gambling)."),
    "restart_pack": ("gift", "", "Enable Restart Pack", "Enable the Restart Pack.", "Activar Restart Pack", "Activa el paquete de reinicio (Restart Pack)."),
    "playtime": ("clock", "", "Play time", "Edit the play time.", "Tiempo de juego", "Edita el tiempo jugado."),
    "enemy_guide": ("book", "", "Enemy Guide", "Unlock or remove enemies in the guide.",
                    "Guía de enemigos", "Desbloquea o quita enemigos de la guía."),
    "user_rank_rewards": ("item:UserRank", "", "User rank rewards", "Claim or reset user rank rewards.",
                          "Recompensas de rango", "Reclama o reinicia las recompensas de rango de usuario."),
    "gold_pass": ("medal", "warn", "Gold Pass", "Edit the Gold Pass (Nyanko Club).", "Gold Pass", "Edita el Gold Pass (Nyanko Club)."),
    "medals": ("medal", "", "Medals", "Edit medals.", "Medallas", "Edita las medallas."),
    "missions": ("check", "", "Missions", "Complete or reset missions.", "Misiones", "Completa o reinicia misiones."),
    # --- Editor settings
    "config": ("gear", "", "BCSFE settings", "Editor options: backups, language, limits, etc.",
               "Configuración de BCSFE", "Opciones del editor: copias de seguridad, idioma, límites, etc."),
    "update_external": ("refresh", "", "Update external themes & languages", "Update external content installed in BCSFE.",
                        "Actualizar temas e idiomas externos", "Actualiza el contenido externo instalado en BCSFE."),
    "manage_game_data": ("database", "", "Manage game data", "Download or delete the game data BCSFE uses.",
                         "Gestionar datos del juego", "Descarga o borra los datos del juego que usa BCSFE."),
}

# Some BCSFE menu keys are already-translated text (the "save to Documents"
# option includes the path), so those are recognised by their function.
FEATURES_BY_FUNCTION: dict[str, str] = {
    "SaveManagement.save_save_data_dir": "save_save_data_dir",
}

HIDDEN_FEATURES = {"exit"}


def category(key: str) -> tuple[str, str, str] | None:
    """(icon, name, description) in the current language."""
    entry = CATEGORIES.get(key)
    if entry is None:
        return None
    icon, en_name, en_desc, es_name, es_desc = entry
    if settings.current["language"] == "es":
        return icon, es_name, es_desc
    return icon, en_name, en_desc


def feature(key: str) -> tuple[str, str, str, str] | None:
    """(icon, flag, name, description) in the current language."""
    entry = FEATURES.get(key)
    if entry is None:
        return None
    icon, flag, en_name, en_desc, es_name, es_desc = entry
    if settings.current["language"] == "es":
        return icon, flag, es_name, es_desc
    return icon, flag, en_name, en_desc
