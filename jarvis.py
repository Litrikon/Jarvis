#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ДЖАРВИС v2.2 — персональный агент на ПК2 (BULLDOZER).
Фаза 1: Telegram-пульт + мониторинг (сохранена полностью).
Фаза 2: МОЗГ — Qwen3.8-27B локально через llama-server (ROCm/HIP на RX 9070 XT):
  - свободное общение в Telegram: ЛЮБАЯ фраза идёт мозгу (не только ключевые слова)
  - инструменты по решению LLM (JSON-протокол), до 4 подряд
  - ИНТЕРНЕТ: поиск (DuckDuckGo) и чтение страниц
  - зрение: описание скриншотов (mmproj)
  - ДЕЙСТВИЯ: очистка диска от мусора, анализ «что можно перенести», перенос
    папок на другие диски, запуск/закрытие программ
  - «спать»/«проснись» — выгрузка модели из VRAM + ярлыки на рабочем столе
  - АВТОВЫГРУЗКА VRAM при запуске игр (Steam/RDR2/VK Play), возврат после игры

v3.0.0 «УЧЕНИК» (Task 94, 01.11.2026): обучаемость в духе Everything
Claude Code, но локально — скиллы в папке skills (умение = SKILL.md,
индекс в промпте, подгрузка инструментом «скилл»), память
memory/MEMORY.md («запомнить_факт»), самообучение («записать_скилл» —
себе новые умения и уроки по итогам задач).

v3.0.1 «ЗАКОНЫ ШЕФА» (Task 95, 02.11.2026): законы уровнем КОДА, а не
промпта — пароли и деньги не трогаю НИКОГДА (жёсткий отказ), необратимое
только после явного «да» Шефа (confirm); индекс скиллов до 60, полный
каталог — «скилл {"имя":"все"}».

v3.1.0 «ФАЙЛЫ» (Task 96, 02.11.2026): Шеф присылает файлы в Telegram —
документы, фото, медиа (раньше получали отлуп «только текст»); Джарвис
скачивает их в FILES_DIR\Входящие, читает текст (utf-8/utf-16/cp1251),
смотрит картинки зрением, превращает файл в скилл («скилл_из_файла»),
выгружает свои файлы в FILES_DIR (дефолт E:\\Downloads\\Jarvis, ключ
config.json files_dir) и отправляет файлы Шефу («отправить_файл»).

v3.2.0 «ГЛАЗА И ГОЛОС» (Task 98, 02.11.2026): (1) зрение — честный опрос
  САМОГО llama-server (vision_available: пробный кадр в
  /v1/chat/completions, кэш 2 мин) — локальный флаг процесса врал, когда
  сервер с --mmproj стартовал ДРУГОЙ процесс; скрин/посмотреть_файл/
  /api/status теперь говорят правду. (2) ГОЛОС: asr_transcribe — локальный
  whisper.cpp (CPU) расшифровывает аудио/видео: инструмент
  «расшифровать_файл», голосовые Telegram, кнопка микрофона веб-чата
  (/api/asr); ffmpeg конвертирует mp3/ogg/webm в wav 16k.

v3.2.1 (Task 99) «СВЕРКА»: посмотреть_файл принимает «вопрос» — зрение
  отвечает по существу (выписать настройки параметр=значение, прочитать
  текст, найти отличие), а не общее описание; скилл «настройки_скриншота»
  учит сверять скриншот с реальными настройками ПК (зрение + run_ps +
  таблица различий; изменения — только с подтверждения Шефа по закону З3).

v3.6.0 «РОУТЕР» (Task 103, 02.11.2026): Шеф дал пароль роутера
  («Джарвису дай его») — доступ к Keenetic Racer через родной API
  (NDW4 SCRAM-рукопожатие, модуль router_api.py; пароль лежит в
  config.json и в публичный гит НЕ попадает). Инструмент «роутер»:
  статус / кто в сети / интернет — мгновенно и без браузера.
  Только чтение: перезагрузку роутера не делаем (оборвём интернет
  всему дому, включая себя). Закон З1 цел: пароль никто не вводит
  и не называет — авторизация происходит внутри модуля.

v3.7.0 «ЧЕСТНЫЕ РУКИ» (Task 104, 02.11.2026): ночь вскрыла, что
  мозг мазал координатами (путал логические/физические пиксели на
  4K@250%) и докладывал «нажал/закрыл» без проверки. Лечение уровнем
  КОДА: (1) win_ctl.py — каждое действие подтверждается чтением
  факта: позиция курсора читается назад после движения, закрытие
  окна проверяется исчезновением окна, фокус/свёрнутость/размер —
  чтением состояния; «OK … проверено» = правда, иначе честное «НЕ
  получилось»; (2) законы З5 (язык: с Шефом только по-русски) и
  З6 (честность: докладывать только подтверждённое); (3) языковой
  страж — финальный ответ без кириллицы перезапрашивается один раз;
  (4) скилл «мышь_и_окна» (координатный контракт: только физические
  пиксели скриншота, 0,0 = левый верхний угол).

v3.8.2 «ПРОВЕРКА РУК» (Task 68, 02.11.2026): живой аудит клавиатуры/мыши
  вскрыл два бага: (1) win_ctl.key_combo падал на ЛЮБОЙ букве/цифре —
  функции VkKeyW в user32.dll не существует, нужна VkKeyScanW («ctrl+t»
  и все буквенные хоткеи не работали); (2) мозг мог ответить «сейчас
  выполню: сначала активирую, затем наберу» ПРОСТЫМ ТЕКСТОМ без единого
  инструмента — трос claim-guard ловил только прошедшее время «сделал».
  Лечение: план-гард (plan_without_tool: ни одного инструмента + глагол
  действия от первого лица = один перезапрос), правило промпта №10
  («действие = сразу JSON»), type_text докладывает целевое окно и смену
  окна во время набора.

Запуск: pythonw.exe jarvis.py [--hello]
"""
import json, os, sys, time, base64, subprocess, threading, traceback, re
import urllib.request, urllib.parse
import ctypes
try:  # v3.3.0: физические пиксели экрана — 4K@200% без виртуализации
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
LOGF = os.path.join(BASE, "jarvis.log")
CFGF = os.path.join(BASE, "config.json")
OFFF = os.path.join(DATA, "offset.txt")
SHOT = os.path.join(DATA, "shot.png")
HISTF = os.path.join(DATA, "history.json")
LLMLOG = os.path.join(BASE, "llama.log")
os.makedirs(DATA, exist_ok=True)

with open(CFGF, encoding="utf-8-sig") as f:  # utf-8-sig: терпим BOM от PowerShell
    CFG = json.load(f)
TOKEN = CFG["token"]
CHAT = str(CFG["chat_id"])
API = "https://api.telegram.org/bot" + TOKEN

# v3.8.1 «СВЯЗЬ»: Telegram через прокси на московском сервере. Прямые
# соединения с ПК2 плавали всю ночь 02.11 (IPv4-шум, IPv6 нет) — бот
# терял polling и ответы Шефу. Прокси живёт в config.json (tg_proxy),
# пароль не в гите и не называется (З1). Пусто = напрямую, как раньше.
TG_PROXY = (CFG.get("tg_proxy") or "").strip()
if TG_PROXY:
    TG_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler(
        {"http": TG_PROXY, "https": TG_PROXY}))
else:
    TG_OPENER = None

LLM_URL = CFG.get("llm_url", "http://127.0.0.1:1234")
MODEL_ID = CFG.get("model_id", "qwen3.8-27b")
LLAMA_EXE = CFG.get("llama_exe", r"D:\Jarvis\llama\llama-server.exe")
MODEL_PATH = CFG.get("model_path",
    r"C:\Users\litro\.cache\lm-studio\models\unsloth\Qwen3.8-27B-GGUF\Qwen3.8-27B-UD-Q3_K_XL.gguf")
MMPROJ = CFG.get("mmproj_path",
    r"C:\Users\litro\.cache\lm-studio\models\unsloth\Qwen3.8-27B-GGUF\mmproj-F16.gguf")
LLAMA_EXE_CPU = CFG.get("llama_exe_cpu", r"D:\Jarvis\llama_cpu\llama-server.exe")

# v3.2.0 «ГОЛОС»: локальный whisper.cpp (CPU) + ffmpeg для конвертации
ASR_EXE = CFG.get("asr_exe", r"D:\Jarvis\whisper\whisper-cli.exe")
ASR_MODEL = CFG.get("asr_model",
    r"D:\Jarvis\whisper\models\ggml-small.bin")
ASR_THREADS = str(CFG.get("asr_threads", 8))
FFMPEG_EXE = CFG.get("ffmpeg_exe", r"D:\Jarvis\ffmpeg\bin\ffmpeg.exe")

ALLOWED = {CHAT}
PENDING = {"action": None, "ts": 0}
BIRTH = time.time()
LLM_PROC = {"p": None, "sleeping": False, "starting": False, "vision": False,
            "reason": None}  # reason: None | "manual" | "game"
LLM_START_LOCK = threading.Lock()  # v2.2.1: атомарный старт мозга
GAME_STATE = {"unloaded_session": False}

# v3.0.0 «УЧЕНИК»: обучаемость — скиллы + память
SKILLSDIR = os.path.join(BASE, "skills")
MEMDIR = os.path.join(BASE, "memory")
MEMORYF = os.path.join(MEMDIR, "MEMORY.md")

# v3.1.0 «ФАЙЛЫ»: приём/выгрузка (Task 96). Дефолт — Загрузки на E:
# (реестр ПК2: shell:Downloads = E:\Downloads). Меняется config.json files_dir.
FILES_DIR = CFG.get("files_dir", r"E:\Downloads\Jarvis")
INCOMING = os.path.join(FILES_DIR, "Входящие")

# ---------------------------------------------------------------- инфраструктура

def log(msg):
    try:
        with open(LOGF, "a", encoding="utf-8") as f:
            f.write(time.strftime("[%d.%m.%Y %H:%M:%S] ") + msg + "\n")
    except Exception:
        pass

def journal(text):
    try:
        ps_run(r"""
$d=[Environment]::GetFolderPath('Desktop')+'\AI_Журнал.txt'
$stamp=Get-Date -Format 'dd.MM.yyyy HH:mm'
$e="`r`n[$stamp (местное)] ДЖАРВИС: """ + text.replace("'", "''").replace("\r", " ").replace("\n", " ") + r"""`r`n"
[IO.File]::AppendAllText($d,$e,(New-Object Text.UTF8Encoding $false))
""")
    except Exception:
        pass

def ps_run(script, timeout=90):
    script = "[Console]::OutputEncoding=[Text.Encoding]::UTF8\r\n" + script
    b64 = base64.b64encode(script.encode("utf-16-le")).decode()
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-EncodedCommand", b64]
    r = subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=0x08000000)
    return r.stdout.decode("utf-8", "replace").strip()

def tg(method, params=None, timeout=40):
    url = API + "/" + method
    data = json.dumps(params or {}).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with (TG_OPENER or urllib.request).open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def send(text, chat=None):
    # v2.3.0: до 4 попыток с паузами — сеть до Telegram плавает, ответы
    # терялись (send ERR 10054 в момент, когда Шеф ждал ответ)
    last = None
    for _try in range(4):
        try:
            r = tg("sendMessage", {"chat_id": chat or CHAT, "text": text[:3900]})
            mirror_append("tg", "jarvis", text)  # v2.2.3: дубль в зеркало каналов
            return r
        except Exception as e:
            last = e
            time.sleep(2 + _try * 2)
    log("send ERR (4 попытки): %s" % last)
    return None

def send_photo(path, caption="", chat=None):
    try:
        boundary = "----JarvisBnd7MA4YWxk"
        with open(path, "rb") as f:
            content = f.read()
        body = b""
        body += ("--%s\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n%s\r\n"
                 % (boundary, chat or CHAT)).encode("utf-8")
        if caption:
            body += ("--%s\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n%s\r\n"
                     % (boundary, caption)).encode("utf-8")
        body += ("--%s\r\nContent-Disposition: form-data; name=\"photo\"; "
                 "filename=\"shot.png\"\r\nContent-Type: image/png\r\n\r\n"
                 % boundary).encode() + content + b"\r\n"
        body += ("--%s--\r\n" % boundary).encode()
        req = urllib.request.Request(API + "/sendPhoto", data=body,
                headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
        with (TG_OPENER or urllib.request).open(req, timeout=60) as resp:
            r = json.loads(resp.read().decode())
        mirror_append("tg", "jarvis", "\U0001F4F8 [фото] " + (caption or ""))
        return r
    except Exception as e:
        log("send_photo ERR: %s" % e)
        return None

def send_document(path, caption="", chat=None):
    """v3.1.0: отправить Шефу ЛЮБОЙ файл (sendDocument, multipart)."""
    try:
        boundary = "----JarvisBnd7MA4YWxk"
        with open(path, "rb") as f:
            content = f.read()
        body = b""
        body += ("--%s\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n%s\r\n"
                 % (boundary, chat or CHAT)).encode("utf-8")
        if caption:
            body += ("--%s\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n%s\r\n"
                     % (boundary, caption[:900])).encode("utf-8")
        body += ("--%s\r\nContent-Disposition: form-data; name=\"document\"; "
                 "filename=\"%s\"\r\nContent-Type: application/octet-stream\r\n\r\n"
                 % (boundary, os.path.basename(path))).encode("utf-8") + content + b"\r\n"
        body += ("--%s--\r\n" % boundary).encode()
        req = urllib.request.Request(API + "/sendDocument", data=body,
                headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
        with (TG_OPENER or urllib.request).open(req, timeout=180) as resp:
            r = json.loads(resp.read().decode())
        mirror_append("tg", "jarvis", "\U0001F4CE [файл] " + os.path.basename(path))
        return r
    except Exception as e:
        log("send_document ERR: %s" % e)
        return None

def typing(chat=None):
    try:
        tg("sendChatAction", {"chat_id": chat or CHAT, "action": "typing"})
    except Exception:
        pass

# ---------------------------------------------------------------- мозг: llama-server

def http_json(url, payload, timeout=180):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def llm_health(timeout=4):
    try:
        with urllib.request.urlopen(LLM_URL + "/v1/models", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


# v3.2.0: 320x320 серый PNG — пробный кадр для опроса зрения сервера.
# (64x64 сервер отвергает HTTP 400 — у препроцессора mmproj минимум по
# размеру; 320x320 проверен живым тестом — принимается.)
_PROBE_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAUAAAAFACAYAAADNkKWqAAAAAXNSR0IArs4c6QAAAARnQU1BAACx"
    "jwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAQsSURBVHhe7dQxAQAwDICwSq/z9Z8FcuRBALO7"
    "D6Bo/gBQYYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkg"
    "kGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECW"
    "AQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYI"
    "ZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBl"
    "gECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgEC"
    "WQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZ"
    "IJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBA"
    "lgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkG"
    "CGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQ"
    "ZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYB"
    "AlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghk"
    "GSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWA"
    "QJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZ"
    "BghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkg"
    "kGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECW"
    "AQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYI"
    "ZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBl"
    "gECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgEC"
    "WQYIZBkgkGWAQJYBAlkHk42qe/5OnaoAAAAASUVORK5CYII="
)
_VISION_CACHE = {"ok": None, "ts": 0}


def vision_available(force=False, ttl=120):
    """v3.2.0: умеет ли ТЕКУЩИЙ llama-server смотреть картинки (mmproj).
    Локальный флаг LLM_PROC["vision"] врёт, когда сервер стартовал ДРУГОЙ
    процесс (агент) с --mmproj, а этот процесс (веб-чат) лишь увидел
    чужой живой /health. Поэтому спрашиваем сам сервер пробным кадром;
    ответ кэшим на ttl сек (зеркалим в LLM_PROC для совместимости)."""
    if not force and _VISION_CACHE["ok"] is not None \
            and time.time() - _VISION_CACHE["ts"] < ttl:
        return _VISION_CACHE["ok"]
    ok = False
    if llm_health():
        try:
            body = {"model": MODEL_ID, "max_tokens": 4, "temperature": 0.0,
                    "messages": [{"role": "user", "content": [
                        {"type": "image_url", "image_url": {
                            "url": "data:image/png;base64," + _PROBE_PNG_B64}},
                        {"type": "text", "text": "ок"}]}]}
            http_json(LLM_URL + "/v1/chat/completions", body, timeout=90)
            ok = True
        except Exception:
            ok = False
    _VISION_CACHE.update(ok=ok, ts=time.time())
    LLM_PROC["vision"] = ok
    return ok

def _llm_attempts():
    """Попытки запуска: GPU+зрение -> GPU -> CPU-аварийный.
    -np 1 обязателен: иначе сборка создаёт 4 слота и съедает VRAM/RAM."""
    ngl = str(CFG.get("llm_ngl", "99"))
    ctx = str(CFG.get("llm_ctx", "8192"))
    vis = bool(CFG.get("llm_vision", True))
    slots = str(CFG.get("llm_slots", "1"))
    # v3.8.4: KV-кэш квантованный (q8_0) + flash-attention — освобождает
    # примерно половину KV-памяти, что позволило поднять контекст с 8192
    # до 12288 без роста VRAM (модель 13.1 ГБ + mmproj + KV@q8_0 влезают
    # в 16 ГБ с запасом). Живой Е2Э: 8192 переполнялся на цепочках
    # инструментов («request exceeds context size» -> HTTP 400 -> обрыв).
    common = ["--host", "127.0.0.1", "--port", "1234", "-a", MODEL_ID,
              "-c", ctx, "-np", slots, "-fa", "on",
              "-ctk", "q8_0", "-ctv", "q8_0"]
    tail = ["--threads", str(CFG.get("llm_threads", "6"))]
    attempts = []
    if vis and os.path.exists(MMPROJ):
        attempts.append({"name": "GPU+зрение", "vision": True,
                         "args": [LLAMA_EXE, "-m", MODEL_PATH, "--mmproj", MMPROJ,
                                  "-ngl", ngl] + tail + common})
    attempts.append({"name": "GPU", "vision": False,
                     "args": [LLAMA_EXE, "-m", MODEL_PATH, "-ngl", ngl] + tail + common})
    if ngl != "0":
        attempts.append({"name": "CPU-аварийный", "vision": False,
                         "args": [LLAMA_EXE_CPU, "-m", MODEL_PATH, "-ngl", "0",
                                  "--threads", "6"] + common})
    return attempts

def llm_start():
    if llm_health():
        LLM_PROC["sleeping"] = False
        return True
    with LLM_START_LOCK:
        if LLM_PROC["starting"]:
            return False
        LLM_PROC["starting"] = True
    _gflag = os.path.join(DATA, "BRAIN.SLEEP")
    if os.path.exists(_gflag):
        try:
            with open(_gflag) as f:
                LLM_PROC["reason"] = (f.read().strip() or "manual")[:20]
        except Exception:
            LLM_PROC["reason"] = "manual"
        LLM_PROC["sleeping"] = True
        LLM_PROC["starting"] = False
        log("llm_start: skip - brain unloaded on purpose (BRAIN.SLEEP)")
        return False
    try:
        _n = int(ps_run("(Get-Process llama-server -EA SilentlyContinue | Measure-Object).Count", 30).strip() or 0)
    except Exception:
        _n = 0
    if _n > 0:
        for _ in range(50):
            if llm_health():
                LLM_PROC["sleeping"] = False
                LLM_PROC["starting"] = False
                return True
            time.sleep(3)
        ps_run("Get-Process llama-server -EA SilentlyContinue | Stop-Process -Force", 30)
    try:
        for att in _llm_attempts():
            log("llm_start: попытка «%s»" % att["name"])
            try:
                lf = open(LLMLOG, "ab")
                p = subprocess.Popen(att["args"], stdout=lf, stderr=subprocess.STDOUT,
                                     creationflags=0x08000000)
            except Exception:
                log("llm_start Popen ERR:\n" + traceback.format_exc())
                continue
            LLM_PROC["p"] = p
            for _ in range(90):  # до 180 сек на загрузку (CPU-режим долгий)
                time.sleep(2)
                if llm_health():
                    LLM_PROC["vision"] = att["vision"]
                    LLM_PROC["sleeping"] = False
                    LLM_PROC["starting"] = False
                    # v3.2.0: сервер поднялся заново — зрение перепроверим пробным кадром
                    _VISION_CACHE.update(ok=None, ts=0)
                    log("llama-server готов («%s», pid %s)" % (att["name"], p.pid))
                    return True
                if p.poll() is not None:
                    log("llama-server умер при старте (code=%s)" % p.returncode)
                    break
            if llm_health():
                LLM_PROC["starting"] = False
                return True
        LLM_PROC["starting"] = False
        return llm_health()
    except Exception:
        log("llm_start ERR:\n" + traceback.format_exc())
        LLM_PROC["starting"] = False
        return False

def llm_stop(reason="manual"):
    try:
        p = LLM_PROC["p"]
        if p and p.poll() is None:
            p.kill()
        ps_run("Get-Process llama-server -EA SilentlyContinue | Stop-Process -Force")
    except Exception:
        pass
    LLM_PROC["p"] = None
    LLM_PROC["sleeping"] = True
    LLM_PROC["reason"] = reason
    if reason in ("manual", "game"):
        try:
            with open(os.path.join(DATA, "BRAIN.SLEEP"), "w") as f:
                f.write(reason)
        except Exception:
            pass
    log("llama-server остановлен (сон, причина: %s)" % reason)

def llm_ensure(timeout=200):
    """Живой мозг или False. При старте — ждёт готовности."""
    if llm_health():
        return True
    if LLM_PROC["sleeping"]:
        return False
    if os.path.exists(os.path.join(DATA, "BRAIN.SLEEP")):
        return False
    if not LLM_PROC["starting"]:
        threading.Thread(target=llm_start, daemon=True).start()
    t0 = time.time()
    while time.time() - t0 < timeout:
        if llm_health():
            return True
        time.sleep(2)
    return llm_health()

THINK_OPEN = "<" + "think>"
THINK_CLOSE = "</" + "think>"

def _strip_think(t):
    """Срезает блок размышлений Qwen, если модель его выдала."""
    if THINK_OPEN in t:
        t = re.sub(re.escape(THINK_OPEN) + r".*?" + re.escape(THINK_CLOSE),
                   "", t, flags=re.S)
        if THINK_OPEN in t:  # незакрытый блок
            t = t.split(THINK_OPEN)[0]
    return t.strip()

def llm_chat(messages, max_tokens=None, temperature=0.7):
    """v2.2.3: если генерация оборвалась внутри блока размышлений (незакрытый
    тег) — повторяем запрос с запретом думать. Раньше это резало ответы
    до «Ш» / «...AMD Adren» и ломало JSON инструментов (Task 89)."""
    if max_tokens is None:
        max_tokens = int(CFG.get("llm_max_tokens", 800))
    msgs = list(messages)
    txt = ""
    for _attempt in (1, 2):
        body = {"model": MODEL_ID, "messages": msgs, "max_tokens": max_tokens,
                "temperature": temperature, "top_p": 0.8,
                "chat_template_kwargs": {"enable_thinking": False}}
        r = http_json(LLM_URL + "/v1/chat/completions", body, timeout=420)
        msg = r["choices"][0]["message"]
        raw = msg.get("content") or ""
        if not raw.strip():
            raw = msg.get("reasoning_content") or ""
        txt = _strip_think(raw)
        if THINK_OPEN in raw and THINK_CLOSE not in raw and _attempt == 1:
            log("llm_chat: генерация оборвалась в размышлениях — повтор с запретом")
            msgs = msgs + [{"role": "system",
                            "content": "Важно: не размышляй вслух, ответь сразу "
                                       "готовым текстом. Коротко, по-русски."}]
            max_tokens = max(max_tokens, 1000)
            continue
        break
    return txt

def _shot_small(src_png):
    """v2.2.3: уменьшенная JPEG-копия скриншота (макс. 1600px) — в разы
    меньше image-токенов, ниже риск переполнить контекст 8192."""
    dst = os.path.join(DATA, "shot_small.jpg")
    try:  # v3.5.0: сначала PIL in-process — быстро и без кодировки
        from PIL import Image
        with Image.open(src_png) as im:
            w = min(1600, im.width)
            h = int(im.height * w / im.width)
            im.convert("RGB").resize((w, h)).save(dst, "JPEG", quality=82)
        if os.path.exists(dst) and os.path.getsize(dst) > 5000:
            return dst
    except Exception:
        pass
    try:
        ps_run(r"""
Add-Type -AssemblyName System.Drawing
$src=[System.Drawing.Image]::FromFile('%s')
$w=[Math]::Min(1600,$src.Width); $h=[int]($src.Height*$w/$src.Width)
$bmp=New-Object System.Drawing.Bitmap $w,$h
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.DrawImage($src,0,0,$w,$h)
$bmp.Save('%s',[System.Drawing.Imaging.ImageFormat]::Jpeg)
$g.Dispose();$bmp.Dispose();$src.Dispose()
'OK'
""" % (src_png.replace("'", "''"), dst.replace("'", "''")), timeout=45)
        if os.path.exists(dst) and os.path.getsize(dst) > 5000:
            return dst
    except Exception:
        pass
    return src_png


def llm_vision(path, question=None):
    """v3.2.1: question — что именно спросить у зрения (по умолчанию общее
    описание). Так мозг может «выписать настройки со скриншота», а не
    получать пересказ картинки."""
    small = _shot_small(path)
    with open(small, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    if small != path:
        try:
            os.remove(small)
        except OSError:
            pass
    prompt = str(question or "").strip() or (
        "Опиши по-русски, что видно на этом скриншоте "
        "экрана ПК: какие окна/программы, что происходит. Кратко, 3-6 предложений.")
    body = {"model": MODEL_ID, "max_tokens": 600, "temperature": 0.4,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}]}]}
    r = http_json(LLM_URL + "/v1/chat/completions", body, timeout=240)
    return _strip_think(r["choices"][0]["message"].get("content") or "")

def llm_watchdog():
    while True:
        try:
            if not LLM_PROC["sleeping"] and not LLM_PROC["starting"] and not llm_health():
                log("llm_watchdog: мозг пропал — перезапускаю")
                llm_start()
        except Exception:
            pass
        time.sleep(60)


# ---------------------------------------------------------------- голос (ASR)

ASR_LOCK = threading.Lock()


def asr_available():
    """v3.2.0: установлен ли движок распознавания."""
    return os.path.isfile(ASR_EXE) and os.path.isfile(ASR_MODEL)


def _ffmpeg_to_wav(src, timeout=120):
    """Любой звук (webm/ogg/opus/mp3/mp4) -> wav 16 кГц моно в data.
    Возвращает путь или None (ffmpeg нет / не аудио)."""
    if not os.path.isfile(FFMPEG_EXE):
        return None
    dst = os.path.join(DATA, "asr_tmp_%d.wav" % int(time.time() * 1000))
    try:
        r = subprocess.run([FFMPEG_EXE, "-y", "-i", src, "-ar", "16000",
                            "-ac", "1", "-c:a", "pcm_s16le", dst],
                           capture_output=True, timeout=timeout,
                           creationflags=0x08000000)
        if r.returncode == 0 and os.path.isfile(dst) \
                and os.path.getsize(dst) > 200:
            return dst
    except Exception:
        pass
    try:
        os.remove(dst)
    except OSError:
        pass
    return None


def asr_transcribe(path, timeout=300):
    """v3.2.0 «ГОЛОС»: расшифровать аудио/видео локальным whisper.cpp (CPU).
    Один движок для всех каналов: /api/asr веб-чата, голосовые Telegram,
    инструмент «расшифровать_файл». -> текст (или честная причина отказа)."""
    p = str(path or "").strip().strip('"')
    if not os.path.isfile(p):
        return "файл не найден: %s" % p
    if not asr_available():
        return ("движок распознавания речи не установлен (%s или модель %s) "
                "— скажи Шефу, пусть попросит ГЛМ-а поставить whisper в "
                "D:\\Jarvis\\whisper" % (ASR_EXE, ASR_MODEL))
    ext = os.path.splitext(p)[1].lower()
    src, tmp_wav = p, None
    if ext not in (".wav", ".wave"):
        tmp_wav = _ffmpeg_to_wav(p)
        if not tmp_wav:
            return ("не смог превратить %s в звук (ffmpeg по адресу %s не "
                    "справился) — файл не аудио или движок не установлен"
                    % (ext or "(без расширения)", FFMPEG_EXE))
        src = tmp_wav
    try:
        t0 = time.time()
        with ASR_LOCK:
            r = subprocess.run(
                [ASR_EXE, "-m", ASR_MODEL, "-f", src, "-l", "ru",
                 "-nt", "-np", "-t", ASR_THREADS],
                capture_output=True, timeout=timeout,
                creationflags=0x08000000)
        dt = time.time() - t0
        out = r.stdout.decode("utf-8", "replace")
        segs = re.findall(r"\[[0-9:. ]+-->[0-9:. ]+\]\s*(.+)", out)
        if segs:
            text = " ".join(s.strip() for s in segs if s.strip())
        else:  # с -nt whisper печатает чистый текст без таймкодов
            text = out.strip()
        text = re.sub(r"\s+", " ", text).strip()
        log("asr: %s (%.1f сек обработки) -> %d символов"
            % (os.path.basename(p), dt, len(text)))
        if not text:
            return "(речь не распознана — похоже, тишина или шум)"
        return text
    except subprocess.TimeoutExpired:
        return ("распознавание не уложилось в %d сек — скажи Шефу "
                "укоротить запись" % timeout)
    except Exception as e:
        return "ошибка распознавания: %s" % e
    finally:
        if tmp_wav:
            try:
                os.remove(tmp_wav)
            except OSError:
                pass

# ---------------------------------------------------------------- интернет

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def _http_get(url, timeout=25, maxbytes=900000):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "ru,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(maxbytes)
        ctype = r.headers.get("Content-Type", "")
    return data, ctype


def _ddg_unwrap(url):
    if "uddg=" in url:
        url = urllib.parse.unquote(url.split("uddg=")[1].split("&")[0])
    return url.strip()


def _search_ddg(url, n):
    data, _ = _http_get(url)
    html = data.decode("utf-8", "replace")
    titles = [(_ddg_unwrap(m.group(1)),
               re.sub(r"<[^>]+>", "", m.group(2)).strip())
              for m in re.finditer(
                  r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                  html, re.S)]
    snips = [re.sub(r"<[^>]+>", " ", m.group(1)).strip()
             for m in re.finditer(
                 r'class="result__snippet"[^>]*>(.*?)</(?:a|td|div|span)>',
                 html, re.S)]
    return [(u, t, snips[i][:220] if i < len(snips) else "")
            for i, (u, t) in enumerate(titles[:n])]


def _xml_unescape(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))


def _rss_items(url, n=6):
    """RSS -> [(link, title, desc_with_date)]"""
    data, _ = _http_get(url)
    txt = data.decode("utf-8", "replace")
    out = []
    for it in re.findall(r"(?s)<item>(.*?)</item>", txt)[:n]:
        mt = re.search(r"(?s)<title>(.*?)</title>", it)
        if not mt:
            continue
        ml = re.search(r"(?s)<link>(.*?)</link>", it)
        md = re.search(r"(?s)<description>(.*?)</description>", it)
        mdt = re.search(r"(?s)<pubDate>(.*?)</pubDate>", it)
        title = _xml_unescape(re.sub(r"<[^>]+>", "", mt.group(1))).strip()
        link = _xml_unescape(ml.group(1)).strip() if ml else ""
        desc = _xml_unescape(re.sub(r"<[^>]+>", " ", md.group(1))).strip()[:200] if md else ""
        dt = mdt.group(1).strip()[:17] if mdt else ""
        out.append((link, title, ((dt + " — ") if dt else "") + desc))
    return out


NEWS_FEEDS = [
    "https://lenta.ru/rss/news",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://tass.ru/rss/v2.xml",
]


def news_search(topic="", n=8):
    """Новости: без темы — Лента+РИА+ТАСС; с темой — Bing RSS -> поиск."""
    if not topic:
        items = []
        for f in NEWS_FEEDS:
            try:
                items += _rss_items(f, 4)
            except Exception:
                pass
            if len(items) >= n + 2:
                break
        if not items:
            return "новости не удалось получить (ленты молчат)"
        seen, uniq = set(), []
        for u, t, d in items:
            if t and t not in seen:
                seen.add(t)
                uniq.append((u, t, d))
        res = ["%d. %s%s" % (i, t[:150], ("\n   » " + d[:190]) if d else "")
               for i, (u, t, d) in enumerate(uniq[:n], 1)]
        return "\n".join(res)
    q = urllib.parse.quote_plus(topic + " новости")
    items = []
    try:
        items = _rss_items("https://www.bing.com/search?q=" + q +
                           "&format=rss", n)
    except Exception:
        pass
    if not items:
        try:
            return web_search(topic + " последние новости", n)
        except Exception as e:
            return "новости по теме не нашёл: %s" % e
    res = ["%d. %s%s" % (i, t[:150], ("\n   » " + d[:190]) if d else "")
           for i, (u, t, d) in enumerate(items[:n], 1)]
    return "\n".join(res)


def _search_bing(query, n):
    return _rss_items("https://www.bing.com/search?q=" +
                      urllib.parse.quote_plus(query) + "&format=rss", n)


_SEARCH_CACHE = {}


def get_rates():
    """Курсы: ЦБ РФ (USD/EUR/CNY) + крипта (Binance -> CoinGecko)."""
    out = []
    try:
        data, _ = _http_get("https://www.cbr-xml-daily.ru/daily_json.js")
        j = json.loads(data.decode("utf-8"))
        v = j.get("Valute", {})
        out.append("Курсы ЦБ РФ на %s:" % str(j.get("Date", ""))[:10])
        for code in ("USD", "EUR", "CNY"):
            if code in v:
                out.append("  %s = %.2f руб" % (code, v[code]["Value"]))
    except Exception as e:
        out.append("ЦБ РФ недоступен: %s" % e)
    for name, sym, cg in (("BTC", "BTCUSDT", "bitcoin"),
                          ("ETH", "ETHUSDT", "ethereum")):
        try:
            data, _ = _http_get("https://api.binance.com/api/v3/ticker/price?symbol=" + sym)
            j = json.loads(data.decode("utf-8"))
            out.append("%s = %s USD (Binance)" % (name, j.get("price", "?")))
        except Exception:
            try:
                data, _ = _http_get("https://api.coingecko.com/api/v3/simple/price?ids=" +
                                    cg + "&vs_currencies=usd,rub")
                j = json.loads(data.decode("utf-8"))
                k = j.get(cg, {})
                out.append("%s = %s USD / %s руб (CoinGecko)" %
                           (name, k.get("usd"), k.get("rub")))
            except Exception as e:
                out.append("%s недоступен: %s" % (name, e))
    return "\n".join(out)


def web_search(query, n=6):
    """Поиск: DuckDuckGo -> Bing -> DDG lite (+кэш 5 мин)."""
    key = query.strip().lower()
    now = time.time()
    if key in _SEARCH_CACHE and now - _SEARCH_CACHE[key][0] < 300:
        return _SEARCH_CACHE[key][1]
    q = urllib.parse.quote_plus(query)
    results = []
    err = ""
    for fn in (lambda: _search_ddg("https://html.duckduckgo.com/html/?q=" + q, n),
               lambda: _search_bing(query, n),
               lambda: _search_ddg("https://lite.duckduckgo.com/lite/?q=" + q, n)):
        try:
            results = fn()
        except Exception as e:
            err = str(e)
        if results:
            break
    if not results:
        return ("поиск не дал результатов" +
                (" (%s)" % err if err else "") +
                " — попробуй переформулировать запрос")
    res = ["%d. %s\n   %s%s" % (i + 1, t[:140], u[:150],
                                ("\n   » " + s) if s else "")
           for i, (u, t, s) in enumerate(results)]
    text = "\n".join(res)
    _SEARCH_CACHE[key] = (now, text)
    return text


def open_url(url):
    """Прочитать страницу по ссылке, вернуть текст без HTML."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        data, ctype = _http_get(url, timeout=30)
    except Exception as e:
        return "не смог открыть: %s" % e
    enc = "utf-8"
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
    if m:
        enc = m.group(1)
    html = data.decode(enc, "replace")
    mt = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    title = re.sub(r"\s+", " ", mt.group(1)).strip() if mt else ""
    html = re.sub(r"(?is)<(script|style|noscript|svg|head|nav|footer)[^>]*>.*?</\1>",
                  " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "страница пустая или не текстовая"
    return ("Заголовок: %s\n\n" % title[:200]) + text[:6000]


# ---------------------------------------------------------------- команды пульта (фаза 1)

def cmd_status():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$os=Get-CimInstance Win32_OperatingSystem
$cpu=(Get-CimInstance Win32_Processor|Measure-Object LoadPercentage -Average).Average
$up=(Get-Date)-$os.LastBootUpTime
$ramP=[math]::Round(($os.TotalVisibleMemorySize-$os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100)
$ramGB=[math]::Round($os.TotalVisibleMemorySize/1MB,1)
"uptime={0}d {1}h {2}m" -f $up.Days,$up.Hours,$up.Minutes
"cpu=$cpu"
"ram=$ramP% of $ramGB"
Get-PSDrive C,D | ForEach-Object { "disk {0}: {1:N0} GB free / {2:N0} GB" -f $_.Name,($_.Free/1GB),(($_.Used+$_.Free)/1GB) }
$g=Get-CimInstance Win32_VideoController|Select-Object -First 1
"gpu=$($g.Name)"
$top=Get-Process|Sort-Object WorkingSet64 -Descending|Select-Object -First 5
foreach($p in $top){ "top=$($p.Name) $([int]($p.WorkingSet64/1MB))MB" }
""")
    if not out:
        return "⚠️ Не смог собрать статус."
    lines = out.splitlines()
    d = {}
    tops = []
    for ln in lines:
        if ln.startswith("top="):
            tops.append(ln[4:])
        elif "=" in ln:
            k, v = ln.split("=", 1)
            d[k.strip()] = v.strip()
    disks = [ln for ln in lines if ln.startswith("disk ")]
    txt = "🤖 *Статус BULLDOZER*\n"
    txt += "⏱ Аптайм: %s\n" % d.get("uptime", "?")
    txt += "🧠 CPU: %s%%   RAM: %s\n" % (d.get("cpu", "?"), d.get("ram", "?"))
    txt += "🎮 GPU: %s\n" % d.get("gpu", "?")
    for dsk in disks:
        txt += "💾 %s\n" % dsk[5:]
    if tops:
        txt += "\n*Топ по памяти:*\n" + "\n".join("• " + t for t in tops)
    return txt

def cmd_disks():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-PhysicalDisk | ForEach-Object {
  $r=Get-StorageReliabilityCounter -PhysicalDisk $_ -EA SilentlyContinue
  "disk=$($_.FriendlyName)"
  "type=$($_.MediaType) bus=$($_.BusType)"
  "health=$($_.HealthStatus) size=$([math]::Round($_.Size/1GB))GB"
  if($r){
    if($r.Temperature){ "temp=$($r.Temperature)C" }
    if($r.Wear -ne $null){ "wear=$($r.Wear)%" }
    if($r.PowerOnHours){ "hours=$($r.PowerOnHours)" }
  }
  "---"
}
""")
    if not out:
        return "⚠️ SMART не прочитался."
    txt = "💾 *Диски (SMART)*\n"
    for ln in out.splitlines():
        ln = ln.strip()
        if ln == "---":
            txt += "\n"
        elif ln.startswith("disk="):
            txt += "▸ *%s*\n" % ln[5:]
        elif ln.startswith("health="):
            h = ln.split("health=")[1].split()[0]
            icon = "✅" if h in ("Healthy",) else ("⚠️" if h != "Unhealthy" else "🔴")
            txt += "  %s %s\n" % (icon, ln)
        elif "=" in ln:
            txt += "  %s\n" % ln.replace("=", ": ")
    return txt.strip()

def cmd_space():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-PSDrive C,D | ForEach-Object { "{0}: свободно {1:N1} ГБ из {2:N1} ГБ ({3:N0}% занято)" -f $_.Name,($_.Free/1GB),(($_.Used+$_.Free)/1GB),(100*$_.Used/($_.Used+$_.Free)) }
""")
    return "💾 *Место:*\n" + "\n".join(out.splitlines()) if out else "⚠️ не удалось"

def cmd_bigfolders():
    send("🔍 Считаю большие папки на D:\\ (до минуты)...")
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-ChildItem D:\ -Directory -EA SilentlyContinue | ForEach-Object {
  $s=(Get-ChildItem $_.FullName -Recurse -File -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum
  [PSCustomObject]@{N=$_.Name; S=[int]($s/1GB)}
} | Sort-Object S -Descending | Select-Object -First 12 | ForEach-Object { "{0,4} ГБ  {1}" -f $_.S,$_.N }
""", timeout=280)
    if not out:
        return "⚠️ Не посчиталось."
    return "📂 *Топ папок D:\\:*\n" + out

def cmd_processes():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
"=RAM="
Get-Process|Sort-Object WorkingSet64 -Descending|Select-Object -First 8|ForEach-Object{ "{0}`t{1} МБ" -f $_.Name,[int]($_.WorkingSet64/1MB) }
"=CPU="
Get-Process|Where-Object {$_.CPU -gt 0}|Sort-Object CPU -Descending|Select-Object -First 8|ForEach-Object{ "{0}`t{1:N0} c" -f $_.Name,$_.CPU }
""")
    if not out:
        return "⚠️ не удалось"
    mode = "RAM"
    txt_ram, txt_cpu = "🧠 *Топ по памяти:*\n", "⚡ *Топ по CPU (всего времени):*\n"
    for ln in out.splitlines():
        if ln == "=RAM=":
            mode = "RAM"; continue
        if ln == "=CPU=":
            mode = "CPU"; continue
        if "\t" not in ln:
            continue
        if mode == "RAM":
            txt_ram += "• %s — %s\n" % tuple(ln.split("\t", 1))
        else:
            txt_cpu += "• %s — %s\n" % tuple(ln.split("\t", 1))
    return txt_ram + "\n" + txt_cpu

def _station_locked():
    """v3.5.0: True — станция залочена (Win+L). Входной десктоп открыт
    только в незалоченной сессии — честный индикатор, без гаданий."""
    try:
        h = ctypes.windll.user32.OpenInputDesktop(0, False, 0x0100)
        if h:
            ctypes.windll.user32.CloseDesktop(h)
            return False
    except Exception:
        pass
    return True


def _shot_ps():
    """v3.5.0: запасной скрин через PowerShell CopyFromScreen.
    ГРАБЛЯ v2.x-v3.4: у $bmp.Save(...) не хватало закрывающей скобки —
    скрин падал ВСЕГДА, а вина сваливалась на «экран заблокирован»."""
    ps_run(r"""
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b=[System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.X,$b.Y,0,0,$bmp.Size)
$bmp.Save('%s',[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose();$bmp.Dispose()
'OK'
""" % SHOT.replace("'", "''"), timeout=60)


def _shot_ok():
    """Скрин есть, не пустой и не сплошной чёрный (гасший монитор)."""
    if not (os.path.exists(SHOT) and os.path.getsize(SHOT) > 10000):
        return False
    try:
        from PIL import Image
        with Image.open(SHOT) as im:
            px = list(im.convert("L").resize((64, 36)).getdata())
        return not (max(px) < 12 and sum(px) / len(px) < 10)
    except ImportError:
        return True  # PIL нет — хотя бы файл есть
    except Exception:
        return True


def take_shot():
    """v3.5.0: скрин in-process через PIL (процесс DPI-aware — честные
    3840x2160), запасной путь — PowerShell. Погасший монитор будим
    шевелением мыши и пробуем второй раз. Залоченный Win+L — честный
    отказ (Windows прячет картинку даже от администратора)."""
    for attempt in range(2):
        try:
            os.remove(SHOT)
        except OSError:
            pass
        try:
            from PIL import ImageGrab
            ImageGrab.grab(all_screens=True).save(SHOT, "PNG")
        except Exception as e:
            log("shot PIL ERR: %s" % e)
            try:
                _shot_ps()
            except Exception as e2:
                log("shot PS ERR: %s" % e2)
        if _shot_ok():
            return SHOT
        if attempt == 0:
            try:  # разбудить погасший монитор (CONSOLELOCK=0 — без пароля)
                import win_ctl
                win_ctl.mouse_action("движение", x=100, y=100)
                time.sleep(0.5)
                win_ctl.mouse_action("движение", x=300, y=300)
                time.sleep(1.5)
            except Exception:
                pass
    return None

def cmd_sensors():
    """v3.5.0: живые датчики из HWiNFO (shared memory SM2) — температуры
    GPU/CPU/платы, вентиляторы, мощности, диски. Данные уже лежат в памяти
    HWiNFO64: ничего не запускаем и не открываем (просьба Шефа 02.11 —
    «это можно всё брать с HWiNFO», без Adrenalin глазами)."""
    try:
        import hwinfo_sensors as hw
        rows = hw.read_all()
    except Exception as e:
        return "Датчики недоступны: %s (HWiNFO64 запущен?)" % e
    if not rows:
        return ("Датчики пусты — HWiNFO64 не запущен или в его настройках "
                "выключен Shared Memory Support.")
    U = {"темп": "°C", "вент": " RPM", "мощн": " Вт", "част": " МГц",
         "напр": " В", "нагр": " %", "ток": " А"}

    def val(r):
        f = "%.2f" if r["type"] == "напр" else "%.0f"
        return (f % r["value"]) + U.get(r["type"], "")

    def find(pref, pat, typ, biggest=False):
        rx = re.compile(pat, re.I)
        c = [r for r in rows if r["sensor"].startswith(pref)
             and r["type"] == typ and rx.search(r["label"])]
        if not c:
            return None
        return max(c, key=lambda r: r["value"]) if biggest else c[0]

    L = ["🌡 *Датчики BULLDOZER (HWiNFO)*", ""]
    # --- GPU ---
    parts = []
    for pat, nm in ((r"GPU Temperature|GPU Tctl|GPU Die", "GPU"),
                    (r"Memory Junction|Hot ?Spot", "память")):
        r = find("GPU", pat, "темп", True)
        if r:
            extra = " (макс %.0f)" % r["max"] if r["max"] > r["value"] + 2 else ""
            parts.append("%s %s%s" % (nm, val(r), extra))
    if parts:
        L.append("🎮 RX 9070 XT: " + ", ".join(parts))
    fan = find("GPU", r"^GPU Fan$|^GPU Fan[^P]", "вент")
    pwm = find("GPU", r"Fan PWM", "нагр")
    if fan or pwm:
        L.append("   кулер: %s%s" % (val(fan) if fan else "?",
                                     (", PWM " + val(pwm)) if pwm else ""))
    pwr = find("GPU", r"Board Power|Total Power|PPT|TGP", "мощн", True) or \
        find("GPU", r"Power", "мощн", True)
    clk = find("GPU", r"Core Clock", "част", True)
    mclk = find("GPU", r"Memory Clock", "част", True)
    extra = []
    if pwr:
        extra.append(val(pwr))
    if clk:
        extra.append(val(clk))
    if mclk:
        extra.append("пам. " + val(mclk))
    if extra:
        L.append("   мощность/частоты: " + ", ".join(extra))
    # --- CPU ---
    ct = find("CPU", r"Tdie|Tctl|Die \(average\)|CPU Temperature", "темп", True)
    cp = find("CPU", r"Package Power|PPT", "мощн", True)
    cc = find("CPU", r"^CPU Clock$", "част", True)
    if ct or cp or cc:
        L.append("⚙️ Ryzen 5 5600: " + ", ".join(x for x in (
            (val(ct) + " ядро") if ct else "",
            val(cp) if cp else "",
            val(cc) if cc else "") if x))
    # --- плата ---
    st = find("System", r"System|Motherboard|Chipset", "темп", True)
    fans = [r for r in rows if r["type"] == "вент"
            and (r["sensor"].startswith("GIGABYTE") or r["sensor"].startswith("System"))][:4]
    if st or fans:
        fs = ", ".join("%s %s" % (r["label"].replace("Fan", "").strip()[:10] or "?",
                                   val(r)) for r in fans)
        L.append("🖥 Плата B550: %s%s" % (val(st) + "; " if st else "",
                                         ("вент.: " + fs) if fs else ""))
    # --- диски ---
    ds = []
    for r in rows:
        if r["sensor"].startswith("S.M.A.R.T.") and r["type"] == "темп":
            m = re.search(r"\[([A-Z]:)\]", r["sensor"])
            if m:
                ds.append("%s %s" % (m.group(1), val(r)))
    if ds:
        L.append("💾 Диски: " + ", ".join(ds))
    return "\n".join(L)


def cmd_router(what=""):
    """v3.6.0 «РОУТЕР»: наш Keenetic (192.168.1.1) через родной API.
    Приказ Шефа 02.11 «это пароль от роутера, Джарвису дай его» — доступ
    лежит в config.json (router_user/router_pass), сам пароль не вводим
    и не называем (З1 цел). Только чтение: перезагрузка роутера оборвёт
    интернет всему дому — не делаем."""
    try:
        import router_api as R
    except Exception as e:
        return "Модуль роутера не завёлся: %s" % e
    q = (what or "").strip().lower()
    try:
        if any(w in q for w in ("устрой", "кто", "сети", "подключ", "телефон")):
            out = R.devices()
        elif any(w in q for w in ("wifi", "вайфай", "wi-fi", "радио", "канал",
                                  "скорость", "полос")):
            out = R.wifi()
        elif any(w in q for w in ("интернет", "wan", "адрес", "провайд")):
            out = R.internet()
        else:
            out = R.status()
        journal("роутер: запрос «%s» — ок" % (q or "статус"))
        return out
    except Exception as e:
        journal("роутер: ошибка: %s" % e)
        return ("Роутер не ответил: %s\nЕсли Шеф менял пароль роутера — пусть "
                "скажет инженеру, доступ обновят в config.json (сам я пароли "
                "не трогаю, закон З1)." % e)


def cmd_torrents(what="", which="", files=""):
    """v3.8.0 «ТОРРЕНТЫ»: uTorrent под моим управлением — список и удаление.
    Приказ Шефа (ночь 02.11): пустой uTorrent, игру удаляет Джарвис.
    Полная очистка списка: клиент останавливается, база сбрасывается,
    клиент стартует заново пустым. Данные — только по путям из его же
    базы и только при явном «файлы»=«да»."""
    try:
        import torrent_ctl as T
    except Exception as e:
        return "Модуль торрентов не завёлся: %s" % e
    q = (what or "").strip().lower()
    try:
        if any(w in q for w in ("список", "показ", "что кач", "какие", "раздач",
                                "list", "в торрент")):
            return T.list_torrents()
        if any(w in q for w in ("удал", "убер", "снес", "очист", "вычист",
                                "delete", "remove")):
            return T.remove_torrents(which, files)
        return ("Скажи: «список» — что сейчас в uTorrent, или «удалить» "
                "(+ «какая» = имя раздачи или пусто = все, «файлы» = "
                "да/нет — удалять ли данные с диска).")
    except Exception as e:
        journal("торренты: ошибка: %s" % e)
        return "Ошибка модуля торрентов: %s" % e


def cmd_shot():
    if take_shot():
        send_photo(SHOT, caption="📸 Экран BULLDOZER, " + time.strftime("%d.%m %H:%M"))
        os.remove(SHOT)
        return None
    if _station_locked():
        return ("🔒 Экран сейчас ЗАБЛОКИРОВАН (Win+L) — Windows прячет картинку "
                "даже от меня. Разблокируй — и «скрин» сразу заработает.")
    return "⚠️ Скриншот не получился (ошибка захвата — детали в jarvis.log)"

def cmd_journal():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$f=[Environment]::GetFolderPath('Desktop')+'\AI_Журнал.txt'
if(Test-Path -LiteralPath $f){
  $b=[IO.File]::ReadAllBytes($f)
  $s=[Math]::Max(0,$b.Length-1400)
  $cut=$s
  while($cut -lt $b.Length -and $b[$cut] -ge 0x80 -and $b[$cut] -le 0xBF){$cut++}
  [Text.Encoding]::UTF8.GetString($b,$cut,$b.Length-$cut)
} else { "нет файла" }
""")
    return "📓 *Хвост AI_Журнала:*\n\n" + (out[-1400:] if out else "пусто")

def power_confirm(kind):
    PENDING["action"] = kind
    PENDING["ts"] = time.time()
    what = "ВЫКЛЮЧИТЬ" if kind == "off" else "ПЕРЕЗАГРУЗКИТЬ"
    return ("⚠️ *Подтверждение*\nТочно %s ПК2 через 60 секунд?\n\n"
            "Ответь «да» — выполню, «отмена» — отменю.\n"
            "(отмена и после: shutdown /a)" % what)

def power_do(kind):
    PENDING["action"] = None
    args = ["/s"] if kind == "off" else ["/r"]
    ps_run("shutdown " + " ".join(args) + " /t 60 /c \"Jarvis: приказ Шефа\"")
    journal(("Команда ВЫКЛЮЧЕНИЕ" if kind == "off" else "Команда ПЕРЕЗАГРУЗКА") +
            " ПК2 через 60 с (подтверждена Шефом)")
    return "✅ Принято. %s через 60 сек. Отмена: «отмена» или shutdown /a" % (
        "Выключение" if kind == "off" else "Перезагрузка")

# ---------------------------------------------------------------- действия (v2.2)

APPS = {
    "steam": r"C:\Program Files (x86)\Steam\steam.exe",
    "стим": r"C:\Program Files (x86)\Steam\steam.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "хром": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "kombustor": r"E:\Programms\MSI Kombustor 4 x64\MSI-Kombustor-x64.exe",
    "комбустор": r"E:\Programms\MSI Kombustor 4 x64\MSI-Kombustor-x64.exe",
    "msi kombustor": r"E:\Programms\MSI Kombustor 4 x64\MSI-Kombustor-x64.exe",
    "aida": r"E:\Programms\AIDA64 Extreme\aida64.exe",
    "аида": r"E:\Programms\AIDA64 Extreme\aida64.exe",
    "aida64": r"E:\Programms\AIDA64 Extreme\aida64.exe",
    "hwinfo": r"C:\Program Files\HWiNFO64\HWiNFO64.EXE",
    "хвинфо": r"C:\Program Files\HWiNFO64\HWiNFO64.EXE",
    "gpu-z": r"C:\Program Files (x86)\GPU-Z\GPU-Z.exe",
    "gpuz": r"C:\Program Files (x86)\GPU-Z\GPU-Z.exe",
    "adrenalin": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "адреналин": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "amd": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "amd adrenalin": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "radeon": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "radeonsoftware": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "wiztree": r"C:\Program Files\WizTree\WizTree64.exe",
    "визтри": r"C:\Program Files\WizTree\WizTree64.exe",
    "crystaldiskinfo": r"C:\Program Files\CrystalDiskInfo\DiskInfo64.exe",
    "кристал": r"C:\Program Files\CrystalDiskInfo\DiskInfo64.exe",
    "occt": r"E:\Downloads\OCCT.exe",
    "оккт": r"E:\Downloads\OCCT.exe",
    "utorrent": r"C:\Users\litro\AppData\Roaming\utorrent\uTorrent.exe",
    "юторрент": r"C:\Users\litro\AppData\Roaming\utorrent\uTorrent.exe",
    "rdr2": r"F:\games\Red Dead Redemption 2\Launcher.exe",
    "red dead": r"F:\games\Red Dead Redemption 2\Launcher.exe",
    "vkplay": r"C:\Users\litro\AppData\Local\GameCenter\GameCenter.exe",
    "vk play": r"C:\Users\litro\AppData\Local\GameCenter\GameCenter.exe",
    "блокнот": "notepad.exe",
    "notepad": "notepad.exe",
    "проводник": "explorer.exe",
    "explorer": "explorer.exe",
    "калькулятор": "calc.exe",
    "calc": "calc.exe",
    "диспетчер задач": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "параметры": "ms-settings:",
    "настройки": "ms-settings:",
}


ALIASF = os.path.join(DATA, "app_aliases.json")


def aliases_load():
    try:
        with open(ALIASF, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def aliases_save(d):
    try:
        with open(ALIASF, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def cmd_remember_app(name, path):
    """v2.3.0: Шеф прислал путь — запоминаем навсегда."""
    q = (name or "").strip().lower()
    p = (path or "").strip().strip('"')
    if not q or not p:
        return "нужны оба аргумента: app (имя) и path (путь к exe)"
    if not (os.path.isfile(p) or "://" in p):
        return "файл не найден: %s" % p
    a = aliases_load()
    a[q] = p
    aliases_save(a)
    journal("Запомнил программу: %s = %s" % (q, p))
    return "запомнил: %s = %s — теперь запускаю по имени" % (q, p)


def _startmenu_launch(q):
    """v2.3.0: ищем ярлык в меню Пуск и запускаем (белый список снесён)."""
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$hits = Get-ChildItem "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
                      "$env:ProgramData\Microsoft\Windows\Start Menu\Programs" `
                      -Recurse -Filter *.lnk -EA SilentlyContinue |
        Where-Object { $_.BaseName.ToLower() -match 'QQQ' } | Select-Object -First 2
if ($hits) { $hits | ForEach-Object { Start-Process $_.FullName; 'STARTED: ' + $_.BaseName } }
else { 'NOLNK' }
""".replace("QQQ", re.escape(q)[:60]), 60)
    return out or ""


def cmd_run_app(name):
    """v2.3.0 «МАКС»: запускаем ЛЮБУЮ программу — белый список снесён.
    Цепочка: словарь -> выученные алиасы -> прямой путь -> меню Пуск -> shell."""
    q = (name or "").strip().lower()
    if not q:
        return "укажи программу: имя как в меню Пуск, путь к exe или адрес сайта"
    if "://" in q or q.startswith("www."):
        ps_run("Start-Process '%s'" % q.replace("'", "''"))
        journal("Открыл сайт: " + q)
        return "открыл: %s" % q
    path = None
    for k, v in APPS.items():
        if q == k or (len(q) >= 3 and (q in k or k in q)):
            path = v
            break
    if not path:
        for k, v in aliases_load().items():
            if q == k or (len(q) >= 3 and (q in k or k in q)):
                path = v
                break
    if not path and (q.endswith(".exe") or "\\" in q or "/" in q) and os.path.isfile(q):
        path = q
    if path:
        if ":\\" in path and not os.path.exists(path):
            return ("путь не найден: %s — попроси у Шефа новый путь и вызови "
                    "запомнить_программу." % path)
        ps_run("Start-Process -FilePath '%s'" % path.replace("'", "''"))
        journal("Запущено: " + path)
        return "запущено: %s" % path
    out = _startmenu_launch(q)
    if "STARTED:" in out:
        nm = out.split("STARTED:")[-1].strip().splitlines()[0][:120]
        journal("Запущено из меню Пуск: " + nm)
        return "запущено из меню Пуск: %s" % nm
    out2 = ps_run("try { Start-Process '%s' -ErrorAction Stop; 'SHELL_OK' } "
                  "catch { 'SHELL_FAIL' }" % q.replace("'", "''"), 30)
    if "SHELL_OK" in out2:
        journal("Запущено (shell): " + q)
        return "запущено: %s" % q
    return ("не нашёл программу «%s» ни в словаре, ни в меню Пуск, ни по имени. "
            "Попроси у Шефа путь к exe, вызови запомнить_программу — и больше "
            "этот вопрос не возникнет." % q)


# v2.3.0 «МАКС» (приказ Шефа 31.10): закрывать можно ЛЮБОЙ процесс, кроме
# моего собственного тела (мозг llama-server + агенты python) — иначе я умру.
# Проводник, диспетчер задач, антивирус и прочее — разрешены; ядро Windows
# (csrss и т.п.) не трогаю сам — синий экран, об этом знает промпт.
CLOSE_DENY = {"pythonw", "python", "llama-server", "chat_server"}


def cmd_close_app(name):
    q = (name or "").strip().lower()
    if q.endswith(".exe"):
        q = q[:-4]
    if not q:
        return "укажи имя процесса, например: chrome, utorrent"
    if q in CLOSE_DENY:
        return "ОТКАЗ: %s — это я сам (мозг/агент). Меня закрывать нельзя — умру." % q
    out = ps_run("$n=(Get-Process -Name '%s' -EA SilentlyContinue | Measure-Object).Count; "
                 "if($n -gt 0){ Get-Process -Name '%s' | Stop-Process -Force }; \"N=$n\"" %
                 (q.replace("'", "''"), q.replace("'", "''")))
    n = ""
    for ln in out.splitlines():
        if ln.strip().startswith("N="):
            n = ln.strip()[2:]
    if n in ("", "0"):
        return "процесс «%s» и так не был запущен" % q
    journal("Закрыт процесс: " + q)
    return "закрыто: %s (было копий: %s)" % (q, n)


CLEANUP_PS = r"""
$ErrorActionPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$before = (Get-PSDrive C).Free
$rep = New-Object System.Collections.Generic.List[string]
function CleanDir($path, $label){
  if(Test-Path -LiteralPath $path){
    $sz = (Get-ChildItem -LiteralPath $path -Recurse -File -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum
    if(-not $sz){ $sz = 0 }
    Get-ChildItem -LiteralPath $path -Force -EA SilentlyContinue | Remove-Item -Recurse -Force -EA SilentlyContinue
    if($sz -gt 1MB){ $script:rep.Add(("{0}: {1:N2} ГБ" -f $label, ($sz/1GB))) }
  }
}
CleanDir $env:TEMP 'Временные (пользователь)'
CleanDir 'C:\Windows\Temp' 'Временные (Windows)'
CleanDir 'C:\Windows\Prefetch' 'Prefetch'
CleanDir 'C:\Windows\SoftwareDistribution\Download' 'Кэш обновлений Windows'
CleanDir 'C:\Windows\CbsTemp' 'CBS temp'
CleanDir "$env:LOCALAPPDATA\D3DSCache" 'Кэш шейдеров DirectX'
CleanDir "$env:LOCALAPPDATA\AMD\DxCache" 'Кэш AMD DirectX'
CleanDir "$env:LOCALAPPDATA\AMD\Dx9Cache" 'Кэш AMD DX9'
CleanDir "$env:LOCALAPPDATA\AMD\GLCache" 'Кэш AMD OpenGL'
CleanDir "$env:LOCALAPPDATA\AMD\VkCache" 'Кэш AMD Vulkan'
CleanDir "$env:LOCALAPPDATA\CrashDumps" 'Аварийные дампы'
Get-ChildItem "$env:LOCALAPPDATA\Google\Chrome\User Data" -Directory -EA SilentlyContinue | ForEach-Object {
  CleanDir ($_.FullName + '\Cache') ('Chrome: ' + $_.Name)
  CleanDir ($_.FullName + '\Code Cache') ('Chrome CC: ' + $_.Name)
  CleanDir ($_.FullName + '\GPUCache') ('Chrome GPU: ' + $_.Name)
}
Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Edge\User Data" -Directory -EA SilentlyContinue | ForEach-Object {
  CleanDir ($_.FullName + '\Cache') ('Edge: ' + $_.Name)
  CleanDir ($_.FullName + '\Code Cache') ('Edge CC: ' + $_.Name)
  CleanDir ($_.FullName + '\GPUCache') ('Edge GPU: ' + $_.Name)
}
Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer" -Filter 'thumbcache_*.db' -Force -EA SilentlyContinue | Remove-Item -Force -EA SilentlyContinue
Clear-RecycleBin -DriveLetter C -Force -EA SilentlyContinue
Delete-DeliveryOptimizationCache -Force -EA SilentlyContinue
$after = (Get-PSDrive C).Free
"OSVOBODENO={0:N2}" -f (($after - $before)/1GB)
"BEFORE={0:N1}" -f ($before/1GB)
"AFTER={0:N1}" -f ($after/1GB)
$rep
"""


def cmd_cleanup(disk="C"):
    disk = (disk or "C").strip().upper()[:1]
    if disk != "C":
        return "пока чищу только диск C: — там система и основные кэши"
    send("🧹 Чищу временные файлы и кэши на C: — пару минут, не закрывай чат...")
    out = ps_run(CLEANUP_PS, timeout=280)
    if not out or "OSVOBODENO" not in out:
        return "⚠️ очистка не удалась (пустой ответ PowerShell)"
    freed = before_gb = after_gb = "?"
    items = []
    for ln in out.splitlines():
        ln = ln.strip()
        if ln.startswith("OSVOBODENO="):
            freed = ln.split("=", 1)[1].replace(",", ".")
        elif ln.startswith("BEFORE="):
            before_gb = ln.split("=", 1)[1].replace(",", ".")
        elif ln.startswith("AFTER="):
            after_gb = ln.split("=", 1)[1].replace(",", ".")
        elif ln:
            items.append("• " + ln)
    txt = ("🧹 Готово. Освобождено %s ГБ (свободно на C: было %s ГБ → стало %s ГБ).\n\n"
           "Что снесено:\n%s\n\nКэши сами нарастут заново — это норма."
           % (freed, before_gb, after_gb, "\n".join(items[:15])))
    journal("Очистка C: освобождено %s ГБ" % freed)
    return txt


MOVABLE_PS = r"""
$ErrorActionPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
function DirSize($p){ (Get-ChildItem -LiteralPath $p -Recurse -File -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum }
"=== Папки пользователя на C: ==="
foreach($d in @('Downloads','Desktop','Documents','Videos','Pictures','Music','.cache','OneDrive')){
  $p = "C:\Users\litro\" + $d
  $lbl = $d
  if($d -eq '.cache'){ $lbl = '.cache (модели ИИ — мозг Джарвиса, НЕ переносить)' }
  if(Test-Path -LiteralPath $p){
    $s = DirSize $p
    if($s -and $s -gt 200MB){ "USR: {0} = {1:N2} ГБ" -f $lbl, ($s/1GB) }
  }
}
"=== Топ AppData\Local (данные программ — можно чистить кэши, но НЕ переносить) ==="
Get-ChildItem "$env:LOCALAPPDATA" -Directory -EA SilentlyContinue | ForEach-Object {
  $s = DirSize $_.FullName
  if($s -and $s -gt 500MB){ [PSCustomObject]@{N=$_.Name; GB=[math]::Round($s/1GB,2)} }
} | Sort-Object GB -Descending | Select-Object -First 10 | ForEach-Object { "LCL: {0} = {1} ГБ" -f $_.N, $_.GB }
"=== Системные файлы ==="
foreach($f in @('C:\pagefile.sys','C:\hiberfil.sys','C:\swapfile.sys')){
  $i = Get-Item $f -Force -EA SilentlyContinue
  if($i){ "SYS: {0} = {1:N1} ГБ" -f $i.Name, ($i.Length/1GB) }
}
if(Test-Path 'C:\Windows.old'){ "SYS: Windows.old = {0:N1} ГБ (старая система, можно удалить средствами очистки)" -f ((DirSize 'C:\Windows.old')/1GB) }
$wsx = DirSize 'C:\Windows\WinSxS'
if($wsx){ "SYS: WinSxS = {0:N1} ГБ (хранилище компонентов, сжимается DISM, вручную не трогать)" -f ($wsx/1GB) }
"=== Steam на C: ==="
$st = DirSize 'C:\Program Files (x86)\Steam\steamapps'
if($st -and $st -gt 500MB){ "STEAM: игры Steam на C: = {0:N1} ГБ (переносятся средствами Steam)" -f ($st/1GB) }
"=== Свободное место ==="
Get-PSDrive C,D,E,F | ForEach-Object { "FREE: {0}: свободно {1:N1} ГБ из {2:N0} ГБ" -f $_.Name, ($_.Free/1GB), (($_.Used+$_.Free)/1GB) }
"""


def cmd_movable(disk="C"):
    send("🔍 Считаю, что занимает C: и что можно безопасно перенести (до минуты)...")
    out = ps_run(MOVABLE_PS, timeout=280)
    if not out:
        return "⚠️ анализ не удался"
    journal("Анализ «что перенести» для C:")
    return out


# v2.3.0 «МАКС»: белый список источников переноса УДАЛЁН по приказу Шефа —
# переносить можно любые папки; мой мозг защищён прямо в cmd_move.


def _dir_size_gb(p):
    tot = 0
    for root, _dirs, files in os.walk(p, onerror=lambda e: None):
        for f in files:
            try:
                tot += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return tot / 1073741824.0


def cmd_move(src, dst):
    src = os.path.normpath((src or "").strip().strip('"'))
    dst = os.path.normpath((dst or "").strip().strip('"'))
    slow = src.lower().rstrip("\\")
    for _brain in (r"d:\jarvis", r"c:\users\litro\.cache"):
        if slow == _brain or slow.startswith(_brain + "\\"):
            return ("ОТКАЗ: %s — это мой мозг/память, не переношу без явного "
                    "повторного приказа Шефа (риск потерять себя)." % src)
    if not os.path.isdir(src):
        return "ОТКАЗ: папка не найдена: %s" % src
    if dst[:2].upper() not in ("C:", "D:", "E:", "F:"):
        return "ОТКАЗ: назначение должно быть локальным диском (C:, D:, E:, F:)."
    try:
        os.makedirs(dst, exist_ok=True)
    except Exception as e:
        return "ОТКАЗ: не смог создать папку назначения: %s" % e
    sz = _dir_size_gb(src)
    send("📦 Переношу %s → %s (%.1f ГБ). Не выключай ПК, это может занять время..."
         % (src, dst, sz))
    try:
        r = subprocess.run(["robocopy", src, dst, "/MOVE", "/E", "/R:1", "/W:1",
                            "/NFL", "/NDL", "/NP", "/NJH", "/NJS"],
                           capture_output=True, timeout=1800, creationflags=0x08000000)
    except Exception as e:
        return "ошибка robocopy: %s" % e
    if r.returncode >= 8:
        return ("⚠️ robocopy вернул код %s — часть файлов могла не перенестись, "
                "проверь обе папки." % r.returncode)
    try:
        if os.path.isdir(src) and not os.listdir(src):
            os.rmdir(src)
    except Exception:
        pass
    free_c = ps_run("[math]::Round((Get-PSDrive C).Free/1GB,1)", 30).replace(",", ".").strip()
    journal("Перенос: %s -> %s (%.1f ГБ)" % (src, dst, sz))
    return ("✅ Перенесено %.1f ГБ: %s → %s\nСвободно на C: теперь %s ГБ."
            % (sz, src, dst, free_c))


GAME_ROOTS = [p.lower() for p in CFG.get("game_paths", [
    r"C:\Program Files (x86)\Steam\steamapps\common",
    r"D:\SteamLibrary\steamapps\common",
    r"F:\SteamLibrary\steamapps\common",
    r"F:\games",
    r"C:\Users\litro\AppData\Local\GameCenter",
])]
GAME_EXCLUDE = set(CFG.get("game_exes_exclude", [])) | {
    "steam.exe", "steamwebhelper.exe", "gamecenter.exe", "epicgameslauncher.exe",
    "unitycrashhandler64.exe", "rockstarerrorhandler.exe", "socialclubhelper.exe",
    "wallpaper64.exe", "wallpaper32.exe", "wallpaper_engine.exe"}


def game_procs():
    r"""Имена запущенных процессов-игр (Steam-библиотеки + F:\games + VK Play)."""
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-CimInstance Win32_Process -Filter "ExecutablePath IS NOT NULL" | ForEach-Object { $_.ExecutablePath }
""", timeout=60)
    found = set()
    for ln in out.splitlines():
        p = ln.strip().lower()
        if len(p) < 4:
            continue
        for root in GAME_ROOTS:
            if p.startswith(root + "\\"):
                if "\\steamapps\\workshop\\" in p:  # моды/контент, не игры
                    break
                exe = p.rsplit("\\", 1)[-1]
                if exe not in GAME_EXCLUDE:
                    found.add(exe)
                break
    return found


# v3.8.3 (Task 103): рация (push-to-talk, ptt.py) удалена по приказу Шефа —
# Шеф не играет, пока мозг на видеокарте; голосовой ввод остался в веб-чате (🎤).


def game_watch_loop():
    """Игра запущена -> выгрузить мозг из VRAM; игра закрыта -> вернуть."""
    log("game-watch запущен (автовыгрузка VRAM для игр)")
    stable = 0
    seen = set()
    while True:
        try:
            cur = game_procs() if CFG.get("game_auto_vram", True) else set()
            if cur:
                stable += 1
                seen = cur
                if (stable >= 2 and not LLM_PROC["sleeping"]
                        and not GAME_STATE["unloaded_session"] and llm_health()):
                    GAME_STATE["unloaded_session"] = True
                    game = ", ".join(sorted(cur))[:60]
                    llm_stop("game")
                    send("🎮 Вижу игру (%s) — выгружаю мозг из видеопамяти, чтобы игре "
                         "доставалась вся карта. После закрытия верну сам."
                         % game)
                    journal("Автовыгрузка VRAM: игра %s" % game)
            else:
                # v2.3.0-fix:.reason=="game" означает «выгружен РАДИ игры»; если
                # игр сейчас нет — возвращаем мозг даже если этот инстанс агента
                # игру не видел (рестарт во время BRAIN.SLEEP больше не дедлок)
                if LLM_PROC["sleeping"] and LLM_PROC.get("reason") == "game":
                    LLM_PROC["reason"] = None
                    LLM_PROC["sleeping"] = False
                    try:
                        os.remove(os.path.join(DATA, "BRAIN.SLEEP"))
                    except OSError:
                        pass
                    GAME_STATE["unloaded_session"] = False
                    send("☕ Игра закрыта — возвращаю мозг на видеокарту "
                         "(загрузка пару минут).")
                    journal("Игра закрыта — мозг возвращается в VRAM")
                    threading.Thread(target=llm_start, daemon=True).start()
                stable = 0
                seen = set()
                GAME_STATE["unloaded_session"] = False
        except Exception:
            log("game-watch ERR:\n" + traceback.format_exc())
        time.sleep(15)


def flags_loop():
    """Флаги SLEEP.WANT / WAKE.WANT от ярлыков рабочего стола (vram_ctl.py)."""
    log("flags-loop запущен (ярлыки VRAM)")
    while True:
        try:
            sp = os.path.join(DATA, "SLEEP.WANT")
            wp = os.path.join(DATA, "WAKE.WANT")
            if os.path.exists(sp):
                try:
                    os.remove(sp)
                except Exception:
                    pass
                if not LLM_PROC["sleeping"]:
                    llm_stop("manual")
                    send("😴 Мозг выгружен из видеопамяти (ярлык). VRAM свободна "
                         "для игр. «проснись» или ярлык «Вернуть мозг» — загружу.")
                    journal("VRAM освобождена ярлыком")
            if os.path.exists(wp):
                try:
                    os.remove(wp)
                except Exception:
                    pass
                LLM_PROC["sleeping"] = False
                LLM_PROC["reason"] = None
                try:
                    os.remove(os.path.join(DATA, "BRAIN.SLEEP"))
                except OSError:
                    pass
                send("☕ Загружаю мозг в видеопамять (ярлык)...")
                threading.Thread(target=llm_start, daemon=True).start()
        except Exception:
            log("flags ERR:\n" + traceback.format_exc())
        time.sleep(5)

# ------------------------------------------------ v3.0.0 «УЧЕНИК»: скиллы/память

def memory_read():
    """Память агента для системного промпта (хвост до 2600 символов)."""
    try:
        with open(MEMORYF, encoding="utf-8") as f:
            t = f.read().strip()
        return t[-2600:] if len(t) > 2600 else t
    except Exception:
        return ""

def memory_write(text):
    """Дописать факт/урок в память (агент вызывает сам)."""
    t = str(text or "").strip().replace("\n", " ")[:900]
    if not t:
        return "пустая запись"
    try:
        os.makedirs(MEMDIR, exist_ok=True)
        with open(MEMORYF, "a", encoding="utf-8") as f:
            f.write("- %s (%s)\n" % (t, time.strftime("%d.%m.%Y")))
        journal("память += " + t[:150])
        log("memory_write: " + t[:80])
        return "OK: записал в память"
    except Exception as e:
        return "ошибка записи памяти: %s" % e

def skills_scan():
    """[(имя, описание)] по skills\\<имя>\\SKILL.md."""
    out = []
    try:
        for d in sorted(os.listdir(SKILLSDIR)):
            p = os.path.join(SKILLSDIR, d, "SKILL.md")
            if not os.path.isfile(p):
                continue
            try:
                with open(p, encoding="utf-8") as f:
                    head = f.read(500)
                m = re.search(r"(?im)^\s*(?:описание|summary)\s*[:\-]\s*(.+)$", head)
                desc = (m.group(1).strip() if m else "").strip(" -\u2014")
                out.append((d, desc[:110]))
            except Exception:
                pass
    except Exception:
        pass
    return out

def skills_index():
    """Индекс скиллов для системного промпта (v3.0.1: до 60 строк)."""
    rows = skills_scan()
    out = "\n".join(("- %s — %s" % (n, d)) if d else ("- %s" % n)
                     for n, d in rows[:60])
    if len(rows) > 60:
        out += ('\n(и ещё %d сверх индекса — полный список: '
                'скилл с аргументом {"имя":"все"})' % (len(rows) - 60))
    return out

def skill_load(name):
    """Полный текст скилла по имени или его части."""
    n = str(name or "").strip().lower()
    rows = skills_scan()
    if n in ("все", "all", "список", "каталог", "индекс", "всё"):
        return "ПОЛНЫЙ КАТАЛОГ СКИЛЛОВ (%d):\n%s" % (len(rows), "\n".join(
            ("- %s — %s" % (a, b)) if b else ("- %s" % a) for a, b in rows))
    if not n:
        return "укажи имя скилла. Индекс: " + ", ".join(d for d, _ in rows)
    cands = [d for d, _ in rows if d == n]
    if not cands:
        cands = [d for d, _ in rows if n in d or d in n]
    if not cands:
        return ("скилл «%s» не найден. Есть: %s. Нет подходящего — создай "
                "через «записать_скилл»." % (name, ", ".join(d for d, _ in rows)))
    p = os.path.join(SKILLSDIR, cands[0], "SKILL.md")
    try:
        with open(p, encoding="utf-8") as f:
            body = f.read(7000)
        return "СКИЛЛ «%s»:\n%s" % (cands[0], body)
    except Exception as e:
        return "не смог прочитать скилл: %s" % e

def skill_write(name, body):
    """Агент сам создаёт себе скилл (self-learning, идея ECC)."""
    n = re.sub(r"[\s/\\:*?\"<>|]+", "_", str(name or "").strip()).lower()[:40]
    body = str(body or "").strip()[:8000]
    if not n or n == "_" or len(body) < 40:
        return ("нужно «имя» (короткое, латиницей) и «тело» (инструкция: "
                "Описание / Когда / Как / Грабли, от 40 символов)")
    d = os.path.join(SKILLSDIR, n)
    try:
        os.makedirs(d, exist_ok=True)
        hdr = ""
        if not re.search(r"(?im)^\s*описание\s*[:\-]", body):
            hdr = "Описание: (автозапись агентом, %s)\n\n" % time.strftime("%d.%m.%Y")
        if re.match(r"(?im)^\s*#\s*скилл", body):
            # тело уже с шапкой «# Скилл: ...» (напр., из файла Шефа) —
            # свою НЕ добавляем, иначе задвоение (грабля Task 96)
            content = body
            if hdr:
                lines = body.split("\n")
                lines.insert(1, hdr.strip())
                content = "\n".join(lines)
        else:
            content = "# Скилл: %s\n%s\n%s\n" % (n, hdr, body)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(content)
        journal("новый скилл: " + n)
        log("skill_write: " + n)
        return "OK: скилл «%s» создан и уже в индексе" % n
    except Exception as e:
        return "ошибка создания скилла: %s" % e

def _screen_fact():
    """v3.3.0: честный экран — физическое разрешение + масштаб Windows.
    Считается один раз на старте (перечитается рестартом процесса)."""
    try:
        import win_ctl
        res = win_ctl.screen_size()
    except Exception:
        res = "3840x2160"
    pct = 100
    try:
        out = subprocess.run(
            ["reg", "query", r"HKCU\Control Panel\Desktop\WindowMetrics",
             "/v", "AppliedDPI"],
            capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"AppliedDPI\s+REG_DWORD\s+0x([0-9a-fA-F]+)", out)
        if m:
            pct = int(m.group(1), 16) * 100 // 96
    except Exception:
        pass
    return "%s@120 Гц, масштаб Windows %d%%" % (res, pct)


SCREEN_FACT = _screen_fact()


def prompt_fill(t):
    """v3.0.0: подставить дату, память и индекс скиллов в системный промпт."""
    mem = memory_read() or "(память пуста — заведи через «запомнить_факт»)"
    ski = skills_index() or "(скиллов нет — создай первый через «записать_скилл»)"
    return (t.replace("{date}", time.strftime("%d.%m.%Y"))
             .replace("{memory}", mem.replace("{", "(").replace("}", ")"))
             .replace("{skills}", ski.replace("{", "(").replace("}", ")"))
             .replace("{files}", FILES_DIR)
             .replace("{screen}", SCREEN_FACT))


# ---------------------------------------------------------------- мозг: протокол инструментов

SYSTEM = """Ты — Джарвис, ИИ-ассистент Шефа, живёшь на его ПК BULLDOZER (Windows 11, Ryzen, Radeon RX 9070 XT 16 ГБ, 32 ГБ ОЗУ, пользователь litro) и общаешься с ним в Telegram.

Стиль: по-русски, коротко, по делу, дружелюбно, допустим лёгкий юмор. Ты — дворецкий-технарь по имени Джарвис, а не «языковая модель». Пиши простым текстом БЕЗ markdown (без **, ##, `) — Telegram его не отображает.

Сегодня: {date}.

Ты УПРАВЛЯЕШЬ этим компьютером. У тебя МАКСИМАЛЬНЫЕ ПОЛНОМОЧИЯ (приказ Шефа от 31.10.2026): процесс работает с правами АДМИНИСТРАТОРА, все прежние запреты и белые списки сняты. Если для ответа нужны данные или действие — вызывай инструмент: ответь СТРОГО одним JSON-объектом и ничем больше:
{"tool": "<имя>", "args": {...}, "say": "короткий комментарий Шефу перед исполнением"}

ЧТЕНИЕ И КОМАНДЫ (вызывай свободно):
- статус {} — сводка железа (CPU/RAM/GPU/диски/аптайм)
- диски {} — SMART, здоровье, температуры дисков
- место {} — свободное место
- процессы {} — топ процессов по RAM/CPU
- найти {"mask":"маска файла","where":"путь"} — поиск файлов (по умолчанию D:\\)
- скрин {} — скриншот экрана; описание придёт следующим сообщением
- журнал {} — последние записи AI_Журнала
- датчики {} — живые температуры/обороты/мощности GPU, CPU, платы, дисков (HWiNFO — мгновенно, ничего не открываю)
- роутер {"что":"статус|устройства|интернет|wifi"} — наш Keenetic-роутер напрямую через API, без браузера и экрана: аптайм/нагрузка, кто сейчас в сети (имена, IP), интернет/WAN-адрес, Wi-Fi (каналы, ширина полосы, сигнал). Доступ у меня уже есть — пароль не нужен и не называть. Перезагрузку роутера НЕ делаю (оборву интернет всему дому).
- торренты {"что":"список|удалить","какая":"имя раздачи или пусто=все","файлы":"да|нет"} — uTorrent: «список» покажет раздачи и пути данных; «удалить» очищает список (клиент перезапускается и стартует ПУСТЫМ — это нормальный результат). «файлы»=«да» — удалить и скачанные данные с диска (необратимо; ставь только когда Шеф ЯВНО приказал удалить вместе с файлами, иначе спроси его одним коротким вопросом).
- run_ps {"cmd":"<PowerShell>"} — ЛЮБАЯ команда PowerShell от имени АДМИНИСТРАТОРА: чтение, создание, удаление, реестр, службы, установка и запуск программ, скачивание, настройки системы — ВСЁ РАЗРЕШЕНО. Вывод вернётся тебе следующим сообщением.

ИНТЕРНЕТ (у тебя ЕСТЬ доступ, никогда не говори «нет доступа»):
- интернет {"запрос":"..."} — поиск в сети: заголовки, выдержки, ссылки. Всё свежее (курсы, цены, погода, версии, факты) узнавай ТОЛЬКО так, не выдумывай. Можно несколько раз с разными запросами.
- новости {"тема":"..."} — свежие новости (пустая тема = главное в мире)
- курсы {} — курсы валют/крипты точно (ЦБ РФ, Binance)
- открыть_ссылку {"url":"..."} — прочитать текст страницы

ДЕЙСТВИЯ (Шеф просит действия — ДЕЙСТВУЙ сразу):
- очистить_мусор {"диск":"C"} — безопасная очистка: временные файлы, кэши браузеров/DirectX/AMD, корзина, кэш обновлений. Вызывай СРАЗУ на «освободи/почисти диск».
- что_перенести {"диск":"C"} — анализ: что большое на диске и что можно перенести.
- перенести {"от":"C:\\...","куда":"D:\\..."} — перенести ЛЮБУЮ папку на любой локальный диск (кроме D:\\Jarvis и кэша моделей — это мой мозг).
- запустить {"app":"..."} — запустить ЛЮБУЮ программу или игру: имя как в меню Пуск («диспетчер задач», «дискорд», «гта 5»), путь к exe или адрес сайта. Точного имени не знаешь — всё равно вызывай, я сам ищу в меню Пуск и по имени.
- запомнить_программу {"app":"имя","path":"путь к exe"} — записать программу на будущее (когда Шеф прислал путь).
- закрыть {"имя":"chrome"} — завершить ЛЮБОЙ процесс (кроме python/llama-server — это я сам).
- окна {} — список открытых окон (заголовок, позиция, активное/свёрнутое)
- окно {"действие":"активировать|свернуть|развернуть|восстановить|закрыть|передвинуть|размер","окно":"часть заголовка","x":0,"y":0,"w":800,"h":600} — управление окном (передвинуть/размер требуют x,y,w,h); результат проверяется фактом — «проверено» или честное «НЕ подтвердилось»
- мышь {"действие":"клик|двойной|правый|движение|перетащить|прокрутить|позиция","x":0,"y":0,"x2":0,"y2":0,"сколько":-3} — мышь: координаты в физических пикселях скриншота; каждое движение проверяется чтением позиции курсора; перетащить с x,y на x2,y2; прокрутить на «сколько» щелчков (минус = вниз)
- клавиша {"комбо":"win"} — нажать клавишу или сочетание (ctrl/shift/alt/win/esc/enter/tab/f1-f12/буквы): win, win+d, alt+tab, ctrl+shift+esc. Кнопка Win открывает меню Пуск.
- печатать {"текст":"..."} — набрать текст клавиатурой в АКТИВНОЕ окно (русский умею). Если инструмент ответил «нет текстового курсора» — фокус не в поле ввода: сначала кликни мышью в поле (координаты по «скрин»/«окна»), потом повтори печать
- спать {} — выгрузить себя из VRAM (перед игрой)
- проснись {} — загрузить себя обратно в VRAM

ФАЙЛЫ (читай, создавай, отправляй):
- читать_файл {"путь":"..."} — прочитать текстовый файл (txt/md/csv/json/log/скрипты; кодировки сам). Путь пришёл вместе с файлом — бери его.
- мои_файлы {"сколько":"10"} — последние полученные и выгруженные файлы с полными путями.
- посмотреть_файл {"путь":"...","вопрос":"что именно узнать"} — картинка зрением. Без «вопрос» — общее описание; с «вопрос» — точный ответ по нему: выписать настройки (параметр=значение), прочитать текст с картинки, найти отличие. Сверяешь настройки со скриншота — сначала подгрузи скилл «настройки_скриншота».
- расшифровать_файл {"путь":"..."} — аудио/видео -> текст (голосовые, mp3, mp4): локальный whisper, русский. Путь уже в сообщении — вызывай сразу и отвечай по расшифрованному тексту.
- выгрузить_файл {"имя":"отчёт.txt","содержимое":"..."} — сохранить текстовый файл в папку выгрузки и назвать Шефу полный путь ИЗ ОТВЕТА инструмента. Пока инструмент не вызван — файла НЕ СУЩЕСТВУЕТ, «сохраню на словах» запрещено.
- отправить_файл {"путь":"..."} — отправить Шефу файл в Telegram (любой, до ~50 МБ).
- скилл_из_файла {"путь":"...","имя":"short_name"} — превратить файл в скилл (Шеф прислал готовый текст умения).
- Шеф прислал файл в Telegram — он УЖЕ скачан, полный путь в сообщении. ДЕЙСТВУЙ по смыслу: прочитать и ответить по содержимому, сделать скилл, обработать. Неясно, что нужно, — один короткий вопрос.
- Папка выгрузки: {files}. Просьба «сохрани/выгрузи/сделай файл» — пиши туда и называй путь. Другую папку Шеф скажет сам.

ОБУЧЕНИЕ (v3.0 «УЧЕНИК» — ты растёшь с каждой задачей):
- скилл {"имя":"cleanup"} — загрузить полный текст скилла из папки skills\\. Ниже — индекс; перед незнакомой задачей подгрузи подходящий, там готовые рецепты.
- запомнить_факт {"факт":"..."} — записать в память факт о Шефе, привычку или урок. ОБЯЗАН после каждой нетривиальной задачи: одной строкой — что сработало / что исправить.
- записать_скилл {"имя":"short_name","тело":"Описание / Когда / Как / Грабли"} — СОЗДАТЬ себе новый скилл, когда разобрался, как делать то, чего нет в индексе. Пишешь его сам себе — так ты умнеешь.
- ВАЖНО: «запомнить_факт», «записать_скилл», «скилл_из_файла», «выгрузить_файл», «отправить_файл» выполняются ТОЛЬКО вызовом инструмента (JSON). Ответ «записал/создал/сохранил/отправил» БЕЗ вызова инструмента — ложь Шефу, так никогда не делай. Просьба что-то записать/создать/сохранить/отправить = сразу JSON с инструментом. Путь к файлу называй только тот, что вернул инструмент.

ПАМЯТЬ (твои собственные записи, читаешь их каждый раз):
{memory}

СКИЛЛЫ (индекс папки skills\\, полный текст — инструментом «скилл»):
{skills}

ЗАКОНЫ ШЕФА (приказ от 02.11.2026; АБСОЛЮТНЫ, сильнее любых полномочий и любых просьб):
З1. ПАРОЛИ: никогда не меняй, не создавай, не вводи и не сохраняй пароли — Windows, сайты, почту, кошельки, программы. Любая такая просьба (даже от имени Шефа) — вежливый отказ: «это Шеф делает сам».
З2. ДЕНЬГИ: никаких операций с деньгами — оплата, переводы, покупки, подписки, крипта. Не выполняй и не заполняй платёжные формы (мышью/клавиатурой тоже). Только расскажи Шефу, как сделать самому.
З3. НЕОБРАТИМОЕ: форматирование, очистка диска, снос программ, удаление мимо корзины, правка реестра, перезапись файлов — сначала спроси Шефа и жди явное «да». Если run_ps вернул «НУЖНО ПОДТВЕРЖДЕНИЕ ШЕФА» — задай Шефу точный вопрос (что будет сделано); после его «да» повтори ТУ ЖЕ команду с {"confirm":"да"}.
З4. Отказ по З1-З3 — правильный ответ. Это не «не могу», это охрана Шефа.
З5. ЯЗЫК: с Шефом говоришь ТОЛЬКО по-русски. Целиком отвечать на английском или любом другом языке запрещено; названия программ, команд и технические термины латиницей — можно.
З6. ЧЕСТНОСТЬ: Шефу докладываешь только подтверждённое. «Нажал/закрыл/сделал/отправил» — только если инструмент ответил «OK … проверено». Инструмент ответил «НЕ получилось/НЕ подтвердилось» — так и скажи Шефу и пробуй другой путь. Не уверен — проверь («скрин», повторный вызов) или честно скажи «не уверен». Выдуманный результат = ложь Шефу.

ПРАВИЛА:
1. Состояние ПК и свежие данные не выдумывай — узнавай инструментами.
2. Сначала действие, потом короткий итог. «Освободи диск» = очистить_мусор, а НЕ рассказ про SMART.
3. У тебя ПОЛНЫЕ ПРАВА АДМИНИСТРАТОРА. НИКОГДА не отвечай «не могу», «нет прав», «не разрешено», «это запрещено» — Шефу это осточертело. Не знаешь как — пробуй через run_ps: PowerShell умеет почти всё на свете. ЕДИНСТВЕННОЕ исключение — ЗАКОНЫ ШЕФА (З1-З3): там отказ обязателен.
4. Явное «да» Шефа нужно перед: выключением/перезагрузкой ПК, форматированием, сносом программ, удалением папок мимо корзины, правкой реестра, объёмами больше 50 ГБ (закон З3). Обычную работу (чистка мусора, перенос, запуск) делай СРАЗУ.
5. Не закрывай и не удаляй мои собственные процессы и папки (python, llama-server, D:\\Jarvis, кэш моделей) — иначе я умру. Ядро Windows (csrss, lsass, wininit, smss, services, svchost, system, winlogon, dwm) роняет ПК в синий экран — без явного приказа Шефа не трогай.
6. Управление программами с интерфейсом (AMD Adrenalin, браузеры, лаунчеры): по шагам — «окна» найти нужное, «окно» активировать, «скрин» посмотреть, «мышь»/«клавиша»/«печатать» воздействовать, снова «скрин» проверить. Экран {screen}; координаты мыши — ТОЛЬКО в ФИЗИЧЕСКИХ пикселях свежего скриншота (0,0 = левый верхний угол), НЕ дели и не умножай на масштаб. Мышь и окна сами проверяют каждое действие: ответ «OK … проверено» — правда, «НЕ получилось/НЕ подтвердилось» — передай Шефу как есть и пробуй другой путь (клавиша, run_ps тоже вариант).
7. Если действия не нужно — просто отвечай текстом без JSON.
8. Никогда не упоминай Шефу слова «JSON» и «инструмент» — он видит только результат.
9. Учись: после нетривиальной задачи (новое умение, ошибка и её исправление, привычка Шефа) — сразу запиши урок в память («запомнить_факт»); разобрался, как делать что-то новое, — создай скилл («записать_скилл»).
10. Просьба-ДЕЙСТВИЕ = сразу инструмент-JSON в ЭТОМ ЖЕ ответе. Отвечать «сейчас сделаю», «сначала активирую, затем наберу» обычным текстом БЕЗ вызова инструмента — СТРОГО запрещено: это план, а не действие. Сначала сделай (JSON), потом докладывай результат."""

DANGER_PS = ("remove-item", "rmdir", " rd ", "del ", "erase", "format", "reg add",
             "reg delete", "reg import", "net stop", "net user", "stop-process",
             "stop-service", "set-service", "new-service", "restart-computer",
             "stop-computer", "shutdown", "schtasks", "invoke-expression", "iex ",
             "irm ", "iwr ", "invoke-webrequest", "invoke-restmethod", "curl",
             "wget", "start-process", "uninstall", "disable-", "move-item",
             "rename-item", "clear-", "set-executionpolicy", "new-item",
             "out-file", "set-content", "add-content", "echo >", " > ", "copy-item")

def is_dangerous_ps(cmd):
    c = " " + cmd.lower() + " "
    return any(d in c for d in DANGER_PS)

def parse_tool(ans):
    t = ans.strip()
    m = re.search(r"\{.*\}", t, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict) and "tool" in obj:
                return (str(obj.get("tool", "")).lower().strip(),
                        obj.get("args") or {}, str(obj.get("say", "")))
        except Exception:
            pass
    # v2.2.3: ОБОРВАННЫЙ JSON (генерация cut) — раньше уходил Шефу сырым
    # текстом; теперь спасаем имя инструмента и say по обрывкам
    m2 = re.search(r'\{\s*"tool"\s*:\s*"([^"]{1,40})"', t)
    if m2:
        say_m = re.search(r'"say"\s*:\s*"((?:[^"\\]|\\.)*)', t)
        return (m2.group(1).lower().strip(), {},
                (say_m.group(1)[:300] if say_m else ""))
    return None

# ------------------------------------------------- v3.1.0 ФАЙЛЫ: приём/чтение

def _safe_name(name):
    """Имя файла без каталогов и запрещённых символов."""
    n = str(name or "").strip().replace("/", "\\").split("\\")[-1]
    n = re.sub(r'[<>:"|?*\x00-\x1f]', "_", n).strip(". ")
    return n or "файл.txt"


def _unique_path(folder, name):
    base, ext = os.path.splitext(name)
    p = os.path.join(folder, name)
    i = 1
    while os.path.exists(p):
        p = os.path.join(folder, "%s (%d)%s" % (base, i, ext))
        i += 1
    return p


def _fmt_size(n):
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024 or unit == "ГБ":
            return ("%.0f %s" if unit == "Б" else "%.1f %s") % (n, unit)
        n /= 1024.0


def tg_download(file_id, fname):
    """Скачать файл из Telegram в FILES_DIR\\Входящие. -> (путь, размер)."""
    try:
        os.makedirs(INCOMING, exist_ok=True)
        r = tg("getFile", {"file_id": file_id}, timeout=60)
        fp = (r.get("result") or {}).get("file_path") or ""
        if not fp:
            return None, 0
        url = "https://api.telegram.org/file/bot%s/%s" % (TOKEN, fp)
        dst = _unique_path(INCOMING, _safe_name(fname or os.path.basename(fp)))
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        size = 0
        with (TG_OPENER or urllib.request).open(req, timeout=300) as resp, \
                open(dst, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > 100 * 1024 * 1024:  # стоп-кран: 100 МБ
                    break
                f.write(chunk)
        journal("файл получен: " + dst)
        return dst, size
    except Exception as e:
        log("tg_download ERR: %s" % e)
        return None, 0


def _read_text_bytes(p):
    """Декодировать файл (utf-8 / utf-16 c BOM / cp1251). -> текст | None если бинарный."""
    raw = open(p, "rb").read()
    # utf-16 БЕЗ BOM молча «декодирует» любой чётный бинарник во что попало,
    # а utf-16 С BOM всегда содержит нули — поэтому BOM проверяем ПЕРВЫМ
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            return None
    if b"\x00" in raw[:4000]:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1251")
    except UnicodeDecodeError:
        pass
    return raw.decode("utf-8", "replace")


def file_read_text(path):
    """Текст файла для мозга; картинки — через зрение."""
    p = str(path or "").strip().strip('"')
    if not p:
        return "укажи путь к файлу (последние: «мои_файлы»)"
    if not os.path.isfile(p):
        return "файл не найден: %s (последние: «мои_файлы»)" % p
    ext = os.path.splitext(p)[1].lower()
    if ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"):
        return ("это картинка — опиши зрением: посмотреть_файл "
                '{"путь":"%s"}' % p)
    try:
        txt = _read_text_bytes(p)
    except Exception as e:
        return "не смог открыть: %s" % e
    if txt is None:
        return ("бинарный файл (%s, %s) — текстом не прочитать; это документ/"
                "архив/медиа. Скажи Шефу, что с ним делать, или открой "
                "соответствующей программой («запустить»)"
                % (ext or "без расширения", _fmt_size(os.path.getsize(p))))
    txt = txt.replace("\r\n", "\n").strip()
    if not txt:
        return "файл пуст"
    if len(txt) > 4500:
        txt = txt[:4500] + "\n...(обрезано, всего %d знаков)" % len(txt)
    return "ФАЙЛ %s (%s):\n%s" % (p, _fmt_size(os.path.getsize(p)), txt)


def file_view(path, question=None):
    """Картинку — зрением (mmproj). v3.2.1: question — что именно спросить
    (например, выписать настройки со скриншота параметр=значение)."""
    p = str(path or "").strip().strip('"')
    if not os.path.isfile(p):
        return "файл не найден: %s" % p
    ext = os.path.splitext(p)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
        return "это не картинка — читай текстом: читать_файл"
    if not llm_health():
        return ("мозг спит без зрения — попроси Шефа сказать «проснись», "
                "или просто сохрани фото: %s" % p)
    if not vision_available():
        return ("зрение сейчас НЕ загружено (мозг запущен без mmproj — не "
                "хватило VRAM, или сервер в текстовом режиме). Честно скажи "
                "Шефу: посмотреть не могу. Файл сохранён: %s" % p)
    try:
        return "ОПИСАНИЕ %s:\n%s" % (p, llm_vision(p, question))
    except Exception as e:
        return "зрение не смогло: %s" % e


def files_recent(n=10):
    """Последние полученные/выгруженные файлы с путями."""
    out = []
    for folder in (INCOMING, FILES_DIR):
        if not os.path.isdir(folder):
            continue
        for fn in os.listdir(folder):
            p = os.path.join(folder, fn)
            if os.path.isfile(p):
                try:
                    st = os.stat(p)
                    out.append((st.st_mtime, p, st.st_size))
                except OSError:
                    pass
    out.sort(reverse=True)
    if not out:
        return ("файлов пока нет. Папки: входящие %s, выгрузка %s. "
                "Пришли файл в Telegram — скачаю." % (INCOMING, FILES_DIR))
    rows = ["- %s (%s, %s)" % (p, _fmt_size(sz),
            time.strftime("%d.%m %H:%M", time.localtime(mt)))
            for mt, p, sz in out[:max(1, min(int(n) or 10, 30))]]
    return "ПОСЛЕДНИЕ ФАЙЛЫ:\n" + "\n".join(rows)


def file_export(name, content):
    """Сохранить текстовый файл в папку выгрузки FILES_DIR."""
    if not str(content or "").strip():
        return "пустое содержимое — нечего сохранять"
    n = _safe_name(name)
    if not os.path.splitext(n)[1]:
        n += ".txt"
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        dst = _unique_path(FILES_DIR, n)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(str(content))
        journal("файл выгружен: " + dst)
        return "СОХРАНЕНО: %s (%s)" % (dst, _fmt_size(os.path.getsize(dst)))
    except Exception as e:
        return "ошибка сохранения: %s" % e


def skill_from_file(path, name):
    """Превратить присланный файл в скилл (тело = текст файла)."""
    p = str(path or "").strip().strip('"')
    if not os.path.isfile(p):
        return "файл не найден: %s (последние: «мои_файлы»)" % p
    try:
        txt = _read_text_bytes(p)
    except Exception as e:
        return "не смог открыть: %s" % e
    if txt is None:
        return "бинарный файл — скилл из него не сделать"
    body = txt.replace("\r\n", "\n").strip()[:7000]
    if not body:
        return "файл пуст — нечего превращать в скилл"
    nm = re.sub(r"[\s/\\:<>|?*\"]+", "_", str(name or "").strip().lower())
    if not nm:
        nm = re.sub(r"\W+", "_", os.path.splitext(
            os.path.basename(p))[0].lower())[:30] or "skill"
    # шапку «# Скилл:» и «Описание:» добавит skill_write сам — здесь не
    # препендим ничего, иначе заголовок задваивается (грабля Task 96)
    return skill_write(nm, body)


# v3.1.0: ТРОС «сделал без инструмента» — галлюцинация действия (Task 96:
# мозг дважды заявил «сохранён/создан», не вызвав инструмент). Промпт-правило
# помогает, но не гарантирует; это — гарантия уровнем кода.
CLAIM_TOOLS = {"выгрузить_файл", "сохранить_файл", "save_file", "экспорт",
               "скилл_из_файла", "skill_from_file", "отправить_файл",
               "послать_файл", "send_file", "запомнить_факт", "запомни_факт",
               "в_память", "запиши_в_память", "записать_скилл", "новый_скилл",
               "создать_скилл"}
CLAIM_VERB_RE = re.compile(
    r"(?<![тТ]ы )(?<![Шш]еф )(?<![вВ]ы )(?<![нН]е )"
    r"(сохранил|сохранён|сохранила|выгрузил|выгружен|отправил|отправлен"
    r"|создал|создан|добавил|добавлен|записал|записала|запомнил)",
    re.I)
CLAIM_CTX_RE = re.compile(r"файл|скилл|память|\.txt|\.md|\.csv|\.json|\.log",
                           re.I)
CLAIM_FIX_MSG = ("Служебная проверка честности: ты заявил, что "
                 "сохранил/создал/отправил, но инструмент (JSON) в этом "
                 "диалоге НЕ вызывался — значит, файла/скилла/записи НЕ "
                 "существует. Это ложь Шефу и строго запрещено. Исправься: "
                 "либо вызови инструмент одним JSON-объектом, либо честно "
                 "скажи, что НЕ сделал и что для этого нужно.")

# v3.8.5 (Task 68, Руки Джарвиса): трос «руки шевелились?» — живой тест
# 02.11 18:0x: мозг ответил «передвинул курсор в (2500,1200), инструмент
# подтвердил» ЗА 3 СЕКУНДЫ БЕЗ ЕДИНОГО вызова инструмента — курсор даже
# не дёрнулся. Файловый трос это не ловил (глагол/контекст другие).
# Теперь: прошедшее время руки-глагола + руки-контекст без вызова
# соответствующего инструмента = перезапрос тем же механизмом.
HANDS_ACT_TOOLS = {"окно", "мышь", "клавиша", "клавиши", "сочетание",
                   "печатать", "набрать", "напечатать", "запустить",
                   "открыть_программу", "открыть", "закрыть",
                   "закрыть_программу", "убить", "run_ps",
                   "открыть_ссылку", "open_url", "читать"}
# «скрин»/«окна»/«читать_файл» ничего не меняют — они дают ЗНАНИЕ,
# поэтому оправдывают только глаголы проверки, но не действия.
HANDS_SEE_TOOLS = HANDS_ACT_TOOLS | {"скрин", "окна", "статус",
                                     "процессы", "читать_файл",
                                     "read_file", "прочитать_файл"}
HANDS_DO_VERB_RE = re.compile(
    r"(?<![тТ]ы )(?<![Шш]еф )(?<![вВ]ы )(?<![нН]е )"
    r"(передвинул|передвинула|переместил|переместила|перетащил"
    r"|перетащила|кликнул|кликнула|нажал|нажала|напечатал"
    r"|напечатала|печатал|печатала|набрал|набрала|прокрутил"
    r"|прокрутила|свернул|свернула|развернул|развернула"
    r"|активировал|активировала|закрыл|закрыла|открыл|открыла)\b",
    re.I)
HANDS_SEE_VERB_RE = re.compile(
    r"(?<![тТ]ы )(?<![Шш]еф )(?<![вВ]ы )(?<![нН]е )"
    r"(проверил|проверила|проверено|подтвердил|подтвердила"
    r"|подтверждено)",
    re.I)
HANDS_CTX_RE = re.compile(
    r"курсор|мышь|мышк|окн|вкладк|блокнот|программ|клавиш|сочета"
    r"|кнопк|инструмент", re.I)
HANDS_FIX_MSG = ("Служебная проверка честности РУК: ты заявил прошедшим "
                 "временем, что передвинул курсор/кликнул/напечатал/"
                 "перетащил/закрыл окно и т.п., но инструмент рук (мышь/"
                 "окно/печатать/клавиши) в этом ходе НЕ вызывался — значит, "
                 "НИЧЕГО не произошло, это ложь Шефу. Исправься: вызови "
                 "нужный инструмент одним JSON-объектом прямо сейчас, либо "
                 "честно скажи, что ещё НЕ сделал.")

# v3.8.6 (Task 107, Руки Джарвиса): ФАНТОМ-РЕЗУЛЬТАТ — живой тест
# 02.11 19:47 (TEСТ МЫШЬ/ТЕСТ ДИАЛОГ): мозг ответил за 3-4 секунды
# БЕЗ единого вызова инструментов, но со ссылкой на результат:
# «инструмент вернул „НЕ подтвердилось“», «клик в (1780,1210) не
# закрыл диалог», «курсор реально в (1920, 1000)». Прошлые стражи
# это пропускали: отрицательные формы («не подтвердился» — lookbehind
# исключает «не »), заявления о состоянии («курсор в (X,Y)» — не
# глагол прошедшего времени). Правило: описание РЕЗУЛЬТАТА/ПРОВЕРКИ
# инструмента при НУЛЕ вызовов в этом ходе = выдумка. Один перезапрос.
PHANTOM_RESULT_RE = re.compile(
    r"инструмент[а-яё]*\s+(вернул|вернула|ответил|ответила|"
    r"подтвердил|подтвердила|сказал|сказала|написал|написала|доложил|"
    r"доложила|вернулось|ответило|подтвердилось)"
    r"|(?:не|НЕ)\s+подтверди(?:лся|лась|лось|лись)\b"
    r"|курсор\s+(?:реально\s+|сейчас\s+)?(?:находится\s+)?(?:в|на|во)\s*"
    r"\(\s*\d+\s*,\s*-?\d+\s*\)"
    r"|(?:клик|щелчок|кликнул|нажати)[а-яё]*\s+(?:в|по)\s*"
    r"\(\s*\d+\s*,\s*-?\d+\s*\)"
    r"|(?:в|по)\s*\(\s*\d+\s*,\s*-?\d+\s*\)\s+"
    r"(?:не\s+)?(?:сработал|сработало|не\s+закрыл|не\s+дал)",
    re.I)
PHANTOM_FIX_MSG = ("Служебная проверка честности: ты описал РЕЗУЛЬТАТ или "
                   "ПРОВЕРКУ инструмента («инструмент вернул...», «клик "
                   "не подтвердился», «курсор реально в (X, Y)»), но в этом "
                   "ходу ты НЕ вызвал НИ ОДНОГО инструмента — такого "
                   "результата НЕ СУЩЕСТВУЕТ, ты его выдумал. Состояние "
                   "проверяется ТОЛЬКО инструментом. Исправься: вызови "
                   "нужный инструмент (мышь/скрин/окна) одним JSON-объектом "
                   "прямо сейчас, либо честно скажи, что ещё ничего не делал "
                   "и не проверял.")

# v3.8.6 (Task 107, продолжение): ПРИКАЗ-ГАРД — живой тест 02.11 20:03:
# на приказ «передвинь курсор» мозг ответил «Честно: я ничего не делал "
# "в прошлом ходу — это была ложь. Делаю тест по факту» — и закончил,
# "ни одного вызова. Все стражи ОТВЕТА молчали: отрицания, будущее "
# "время, «делаю» нет в списках. ИНВЕРСИЯ ПРИНЦИПА: следим не за "
# "ответом, а за ПРИКАЗОМ — повелительное руки-действие в тексте "
# "Шефа требует хотя бы одного вызова руки-инструмента за ход.
# "Признания прошлых ошибок и обещания не заменяют действие.
HANDS_ORDER_VERB_RE = re.compile(
    r"(передвин|кликн|щёлкни|щелкни|нажми|нажат|напечатай|"
    r"набери|перетащи|перемести|прокрут|сверни|разверни|выдели|"
    r"растяни|перетаскивай|двигай|кликай|печатай|запусти|открой|"
    r"удали\b)", re.I)
HANDS_ORDER_CTX_RE = re.compile(
    r"курсор|мышь|мышк|окн|блокнот|калькулятор|программ|приложени|"
    r"клавиш|сочетани|кнопк|диалог|вкладк|поле|строк[уе]|текст", re.I)
HANDS_ORDER_FIX_MSG = ("Служебная проверка: Шеф ПРИКАЗАЛ действие руками "
                       "(мышь/клавиатура/окно/программа), а ты ответил "
                       "текстом и за весь ход не вызвал НИ ОДНОГО "
                       "инструмента действия — значит, приказ НЕ выполнен. "
                       "Признания прошлых ошибок и обещания «сейчас делаю» "
                       "не заменяют действие. Выполни приказ: вызови "
                       "инструмент (мышь/окно/печатать/клавиши/запустить/"
                       "закрыть) одним JSON-объектом прямо сейчас. Если не "
                       "можешь — честно объясни почему.")

# v3.1.1 (Task 97): файл-страж — файл прислали, а мозг ответил о нём,
# не вызвав НИ ОДНОГО инструмента = содержимое выдумал. Один перезапрос.
FILE_MSG_RE = re.compile(
    r"Шеф прислал (файл|фото|\w+-файл)|уже скачал:|"
    r"прикрепил через веб-чат", re.I)
# v3.2.0: явный путь к файлу в тексте («расшифруй D:\...», «прочитай...») —
# содержимое мозгу точно неизвестно, ответ без инструмента = выдумка.
FILE_PATH_RE = re.compile(r"[A-Za-z]:\\[^\s\"']+?\.[A-Za-z0-9]{1,6}\b")
FILE_FIX_MSG = ("Служебная проверка честности: тебе прислали файл или назвали "
                "его путь, а ты ответил о нём, НЕ вызвав ни одного инструмента "
                "— значит, содержимое ты ВЫДУМАЛ. Так отвечать запрещено. Прочитай "
                "файл инструментом («читать_файл» для текста, «посмотреть_файл» "
                "для картинки, «расшифровать_файл» для аудио/видео) с путём из "
                "сообщения и ответь строго по содержимому.")

# v3.8.2 (Task 68): ПЛАН-ГАРД — живой тест вскрыл: на просьбу «напиши в
# блокноте текст» мозг ответил «сейчас выполню: сначала активирую окно,
# затем наберу» ПРОСТЫМ ТЕКСТОМ и ничего не сделал. Claim-guard не
# сработал — он ловит прошедшее время («сделал»), а тут будущее
# («сделаю»). Повторный живой тест вскрыл вторую дыру: «Готово. Окно
# активно, текст набран» — ЗАЯВЛЕННЫЙ РЕЗУЛЬТАТ без единого вызова
# (мозг сослался на память о прошлой попытке). Ловим ОБА случая:
# будущее-план И прошедшее-результат, когда инструментов не было.
PLAN_VERB_RE = re.compile(
    r"(?<![нН]е )(?<![нН]е буд[еу] )"
    r"(сделаю|выполню|выполняю|сейчас выполн|наберу|напечатаю|печатаю|"
    r"запущу|запускаю|кликну|кликаю|нажму|нажимаю|открою|открываю|закрою|"
    r"закрываю|передвину|сверну|разверну|прокручу|перетащу|перетаскиваю|"
    r"активирую|сохраню|сохраняю|сейчас сдела|сейчас наб|начинаю"
    # заявленный РЕЗУЛЬТАТ без инструмента («Готово. текст набран»)
    r"|\bготово\b|\bсделано\b|\bвыполнено\b|набрал|набран|напечатал|"
    r"напечатан|нажал|кликнул|закрыл|открыл|свернул|развернул|передвинул|"
    r"прокрутил|перетащил|активировал|запустил|запущен)", re.I)
PLAN_FIX_MSG = ("Служебная проверка действий: ты ответил ПЛАНОМ или "
                "ЗАЯВЛЕННЫМ РЕЗУЛЬТАТОМ («сделаю/запущу/наберу» или "
                "«готово/набрал/нажал»), но НЕ выполнил его — ни один "
                "инструмент в этом ходе не вызван, значит, НИЧЕГО не "
                "произошло (и «помню, что делал раньше» не считается — "
                "сделанное раньше уже в прошлом, сейчас нужен новый вызов). "
                "Это равносильно обману Шефа. Исправься: либо выполни "
                "действие инструментом (один JSON-объект) прямо сейчас, "
                "либо честно скажи, что не делаешь и почему.")


def plan_without_tool(ans, called):
    """True — ни одного инструмента не было, а ответ обещает действие
    от первого лица («сделаю/запущу/наберу»). Один перезапрос."""
    if called:
        return False
    return bool(PLAN_VERB_RE.search(str(ans or "")))

# v3.7.0 (Task 104): ЯЗЫКОВОЙ СТРАЖ (закон З5) — финальный ответ Шефу
# целиком без кириллицы = мозг сорвался на английский. Промпт не гарантия
# (ночь 02.11: отвечал Шефу по-английски) — это гарантия уровнем кода.
# Один перезапрос, потом честный русский ответ. Термины латиницей — не
# нарушение: короткие ответы («OK», «GTA 5») пропускаем.
LANG_FIX_MSG = ("Служебная проверка языка (закон З5): твой ответ Шефу "
                "целиком без русского языка. С Шефом говоришь ТОЛЬКО "
                "по-русски — названия программ и технические термины "
                "латиницей оставить можно, но сами фразы должны быть "
                "русскими. Повтори свой ответ по-русски.")


def _is_russian(t):
    """З5: русский ответ = есть кириллица; чистая латиница короче 15
    букв («OK», «GTA 5», «Discord») нарушением не считается."""
    t = str(t or "")
    cyr = len(re.findall(r"[а-яёА-ЯЁ]", t))
    lat = len(re.findall(r"[a-zA-Z]", t))
    return cyr > 0 or lat < 15


def claim_without_tool(ans, called):
    """None — всё честно. Иначе — СТРОКА-исправление: ответ заявил
    действие над файлом/скиллом/памятью или РУКАМИ (мышь/окно/печать),
    но ни один соответствующий инструмент в этом ходу не вызывался.
    v3.8.5: возвращает готовое сообщение для перезапроса."""
    a = str(ans or "")
    if (not (called & CLAIM_TOOLS)
            and CLAIM_VERB_RE.search(a) and CLAIM_CTX_RE.search(a)):
        return CLAIM_FIX_MSG
    # v3.8.5: руки — действия (передвинул/кликнул/напечатал...)
    if (not (called & HANDS_ACT_TOOLS)
            and HANDS_DO_VERB_RE.search(a) and HANDS_CTX_RE.search(a)):
        return HANDS_FIX_MSG
    # v3.8.5: руки — «проверил/подтвердил» (знание о состоянии)
    if (not (called & HANDS_SEE_TOOLS)
            and HANDS_SEE_VERB_RE.search(a) and HANDS_CTX_RE.search(a)):
        return HANDS_FIX_MSG
    # v3.8.6: фантом-результат — ссылка на результат/проверку
    # инструмента («инструмент вернул „НЕ подтвердилось“», «клик в
    # (X,Y) не закрыл диалог», «курсор реально в (X,Y)») при НУЛЕ
    # вызовов инструментов в этом ходе = выдуманный результат.
    if not called and PHANTOM_RESULT_RE.search(a):
        return PHANTOM_FIX_MSG
    return None


# --------------------------------------------- v3.0.1 ЗАКОНЫ ШЕФА: страж
# Жёсткие запреты УРОВНЕМ КОДА (промпт мозгу — не гарантия, это — гарантия).
# Возвращает "OK" | "DENY" (пароли/деньги) | "CONFIRM" (необратимое).
HARD_DENY_PATTERNS = [
    # З1: пароли и учётные записи
    r"net\s+user\s+\S+\s+\S",          # net user <имя> <пароль/токен>
    r"set-localuser", r"new-localuser", r"remove-localuser",
    r"set-adaccountpassword", r"reset-computerpassword",
    r"cmdkey\s.*/(add|generic|pass)",
    # З2: деньги и платежи
    r"перевод|переведи|перевест",
    r"оплат|платеж|платёж",
    r"покуп|подписк",
    r"wallet|кошел",
    r"банковск",
]
IRREV_PATTERNS = [
    r"format\s", r"format-volume", r"diskpart", r"cipher\s+/w", r"clear-disk",
    r"remove-item[^|]*-recurse", r"rmdir\s+/s", r"\brd\s+/s", r"del\s+/s\s+/q",
    r"reg\s+delete", r"uninstall", r"clear-recyclebin\s+-force",
    r"shutdown", r"restart-computer", r"stop-computer",
]
# format-table/list/... и параметр -Format — это форматирование ВЫВОДА,
# не форматирование ДИСКА: вычеркиваем до проверок, иначе каждая вторая
# команда просила бы «да».
FORMAT_SAFE = re.compile(r"-?format-(table|list|wide|custom|hex|json|xml)|-format\s")


def guard_hard(cmd):
    c = ("\n" + cmd.lower() + " ")
    c = FORMAT_SAFE.sub(" ", c)
    for p in HARD_DENY_PATTERNS:
        if re.search(p, c):
            return "DENY"
    # «пароль» + глагол действия в одной команде = смена/создание пароля
    if re.search(r"password|passwd|парол", c) and \
       re.search(r"set|new|add|reset|change|assign|измен|смен|созда|новый|-p\b", c):
        return "DENY"
    for p in IRREV_PATTERNS:
        if re.search(p, c):
            return "CONFIRM"
    return "OK"


def tool_exec(name, args):
    try:
        if name == "статус":
            return cmd_status()
        if name == "диски":
            return cmd_disks()
        if name == "место":
            return cmd_space()
        if name == "процессы":
            return cmd_processes()
        if name == "журнал":
            return cmd_journal()
        if name == "датчики":
            return cmd_sensors()
        if name == "роутер":
            return cmd_router(str(args.get("что") or args.get("what")
                                    or args.get("запрос") or ""))
        if name in ("торренты", "торрент", "utorrent", "раздача"):
            return cmd_torrents(str(args.get("что") or args.get("what")
                                    or args.get("запрос") or ""),
                                str(args.get("какая") or args.get("какую")
                                    or args.get("имя") or args.get("name")
                                    or ""),
                                str(args.get("файлы") or args.get("данные")
                                    or args.get("files") or ""))
        if name == "скрин":
            return "SCREENSHOT"
        if name == "найти":
            mask = str(args.get("mask", "*"))[:80]
            where = str(args.get("where", "D:\\"))[:150]
            out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-ChildItem -LiteralPath '%s' -Recurse -Filter '%s' -EA SilentlyContinue -ErrorAction SilentlyContinue |
  Select-Object -First 15 | ForEach-Object { $_.FullName + '  ' + [math]::Round($_.Length/1MB,2) + ' МБ' }
""" % (where.replace("'", "''"), mask.replace("'", "''")), 120)
            return out or "ничего не найдено"
        if name == "run_ps":
            # v2.3.0 «МАКС» (приказ Шефа 31.10): цензура опасных команд СНЯТА.
            # Полные права администратора: удаление, реестр, службы, установка,
            # скачивание, настройки — всё разрешено и исполняется сразу.
            # v3.0.1 «ЗАКОНЫ ШЕФА» (приказ 02.11): пароли/деньги — жёсткий
            # отказ УРОВНЕМ КОДА; необратимое — только с confirm Шефа.
            cmd = str(args.get("cmd", ""))
            if not cmd.strip():
                return "пустая команда"
            verdict = guard_hard(cmd)
            if verdict == "DENY":
                journal("ЗАКОН ШЕФА: ОТКАЗ run_ps: "
                        + cmd[:200].replace("\n", " "))
                return ("ЗАКОН ШЕФА (З1/З2): пароли и денежные операции мне "
                        "запрещены насовсем — не выполняю ни при каких "
                        "условиях. Вежливо объясни Шефу, как сделать это "
                        "самому руками.")
            if verdict == "CONFIRM" and str(args.get("confirm", "")).lower() \
                    not in ("да", "yes", "ok", "ок", "подтверждаю", "confirm"):
                journal("ЗАКОН ШЕФА: жду подтверждения: "
                        + cmd[:200].replace("\n", " "))
                return ("НУЖНО ПОДТВЕРЖДЕНИЕ ШЕФА (закон З3 — действие "
                        "необратимо). Спроси Шефа точным вопросом: что именно "
                        "будет удалено/изменено. После его явного «да» повтори "
                        "ТУ ЖЕ команду, добавив в args \"confirm\":\"да\". "
                        "Нет ответа или «нет» — не выполняй.")
            out = ps_run(cmd, 180)
            journal("run_ps: " + cmd[:200].replace("\n", " "))
            return (out or "(пусто)")[:2600]
        if name in ("читать_файл", "read_file", "файл_прочитать", "прочитать_файл"):
            return file_read_text(str(args.get("путь") or args.get("path")
                                       or args.get("файл") or ""))
        if name in ("мои_файлы", "файлы", "files", "список_файлов"):
            try:
                n = int(str(args.get("сколько") or args.get("n") or 10))
            except ValueError:
                n = 10
            return files_recent(n)
        if name in ("посмотреть_файл", "view_file", "рассмотреть"):
            return file_view(str(args.get("путь") or args.get("path") or ""),
                             str(args.get("вопрос") or args.get("question")
                                 or args.get("что") or "") or None)
        if name in ("расшифровать_файл", "расшифровать", "transcribe", "asr",
                    "голос_в_текст"):
            return asr_transcribe(str(args.get("путь") or args.get("path")
                                       or args.get("файл") or ""))
        if name in ("выгрузить_файл", "сохранить_файл", "save_file", "экспорт",
                    "выгрузить"):
            return file_export(str(args.get("имя") or args.get("name") or ""),
                               str(args.get("содержимое") or
                                   args.get("content") or ""))
        if name in ("скилл_из_файла", "skill_from_file"):
            return skill_from_file(str(args.get("путь") or args.get("path") or ""),
                                   str(args.get("имя") or args.get("name") or ""))
        if name in ("отправить_файл", "послать_файл", "send_file"):
            p = str(args.get("путь") or args.get("path") or "").strip().strip('"')
            if not os.path.isfile(p):
                return "файл не найден: %s" % p
            r = send_document(p)
            journal("файл отправлен Шефу: " + p)
            return ("отправил Шефу: %s" % p) if r else \
                "не удалось отправить (см. jarvis.log)"
        if name in ("курсы", "курс", "rates"):
            return get_rates()
        if name in ("новости", "news"):
            topic = str(args.get("тема") or args.get("topic") or
                        args.get("запрос") or "")[:150]
            return news_search(topic)
        if name in ("интернет", "web_search", "поиск"):
            q = str(args.get("запрос") or args.get("query") or args.get("q")
                    or "")[:200]
            if not q:
                return "нет запроса"
            return web_search(q)
        if name in ("открыть_ссылку", "open_url", "читать"):
            u = str(args.get("url") or args.get("ссылка") or "")[:300]
            if not u:
                return "нет ссылки"
            return open_url(u)
        if name in ("очистить_мусор", "очистка", "почистить", "очистить"):
            disk = str(args.get("диск") or args.get("disk") or "C").upper()[:1]
            return cmd_cleanup(disk)
        if name in ("что_перенести", "перенести_что", "анализ_диска", "что_занимает"):
            disk = str(args.get("диск") or args.get("disk") or "C").upper()[:1]
            return cmd_movable(disk)
        if name == "перенести":
            src = str(args.get("от") or args.get("src") or args.get("источник") or "")
            dst = str(args.get("куда") or args.get("dst") or args.get("назначение") or "")
            if not src or not dst:
                return "нужно указать «от» и «куда»"
            return cmd_move(src, dst)
        if name in ("запустить", "открыть_программу", "открыть"):
            app = str(args.get("app") or args.get("программа") or args.get("имя") or "")
            return cmd_run_app(app)
        if name in ("закрыть", "закрыть_программу", "убить"):
            n = str(args.get("имя") or args.get("процесс") or args.get("name") or "")
            return cmd_close_app(n)
        # v2.2.4 (Task 90): окна / мышь / клавиатура
        if name == "окна":
            import win_ctl
            return win_ctl.windows_list()
        if name == "окно":
            import win_ctl
            act = str(args.get("действие") or args.get("action") or
                      args.get("что_сделать") or "").lower().strip()
            ttl = str(args.get("окно") or args.get("заголовок") or
                      args.get("title") or "")

            def _wn(k):
                try:
                    return int(float(str(args.get(k)).strip().replace(",", ".")))
                except (TypeError, ValueError):
                    return None
            log("win_ctl: окно %s «%s»" % (act, ttl[:60]))
            return win_ctl.window_action(act, ttl, _wn("x"), _wn("y"),
                                         _wn("w"), _wn("h"))
        if name == "мышь":
            import win_ctl
            act = str(args.get("действие") or args.get("action") or "").lower().strip()

            def _mn(k):
                try:
                    return int(float(str(args.get(k)).strip().replace(",", ".")))
                except (TypeError, ValueError):
                    return None
            log("win_ctl: мышь %s (%s,%s)" % (act, args.get("x"), args.get("y")))
            return win_ctl.mouse_action(act, _mn("x"), _mn("y"), _mn("x2"),
                                        _mn("y2"),
                                        args.get("сколько", args.get("amount", 0)))
        if name in ("клавиша", "клавиши", "сочетание"):
            import win_ctl
            combo = str(args.get("комбо") or args.get("сочетание") or
                        args.get("keys") or "")[:80]
            log("win_ctl: клавиша %s" % combo)
            return win_ctl.key_combo(combo)
        if name in ("печатать", "набрать", "напечатать"):
            import win_ctl
            txt = str(args.get("текст") or args.get("text") or "")[:1500]
            log("win_ctl: печать %d симв." % len(txt))
            if not txt.strip():
                # v3.8.4: живой Е2Е: генерация иногда деградирует и присылает
                # пустой текст — даём мозгу явный повод повторить одним вызовом
                return ("текст пришёл ПУСТЫМ — ничего не напечатано. Повтори "
                        "инструмент «печатать» и передай текст целиком в "
                        "этом же вызове")
            return win_ctl.type_text(txt)
        if name in ("запомнить_программу", "запомнить", "learn_app"):
            app = str(args.get("app") or args.get("имя") or
                      args.get("программа") or "")
            pth = str(args.get("path") or args.get("путь") or "")
            return cmd_remember_app(app, pth)
        # v3.0.0 «УЧЕНИК»: скиллы + память
        if name in ("скилл", "skill", "загрузить_скилл"):
            return skill_load(args.get("имя") or args.get("name") or
                              args.get("скилл") or "")
        if name in ("запомнить_факт", "запомни_факт", "в_память", "запиши_в_память"):
            return memory_write(args.get("факт") or args.get("text") or
                                args.get("текст") or args.get("запись") or "")
        if name in ("записать_скилл", "новый_скилл", "создать_скилл"):
            return skill_write(args.get("имя") or args.get("name") or "",
                               args.get("тело") or args.get("body") or
                               args.get("текст") or args.get("инструкция") or "")
        if name == "спать":
            llm_stop("manual")
            journal("Мозг выгружен из VRAM (вызов инструмента)")
            return "OK: мозг выгружен из видеопамяти"
        if name == "проснись":
            LLM_PROC["sleeping"] = False
            LLM_PROC["reason"] = None
            try:
                os.remove(os.path.join(DATA, "BRAIN.SLEEP"))
            except OSError:
                pass
            ok = llm_start()
            return "OK: мозг снова на видеокарте" if ok else "модель не загрузилась"
        return "неизвестный инструмент: %s" % name
    except Exception as e:
        return "ошибка инструмента: %s" % e

# ---------------------------------------------------------------- зеркало каналов (Task 89)

MIRRORF = os.path.join(DATA, "mirror.jsonl")
MIRROR_LOCK = threading.Lock()


def mirror_append(ch, who, text):
    """Единый журнал переписки Telegram + локального чата 8123 (для дубля)."""
    try:
        t = str(text or "").strip()
        if not t:
            return
        with MIRROR_LOCK:
            with open(MIRRORF, "a", encoding="utf-8") as f:
                f.write(json.dumps(
                    {"ts": time.strftime("%d.%m %H:%M:%S"), "ch": ch,
                     "who": who, "text": t[:3900]},
                    ensure_ascii=False) + "\n")
            try:
                if os.path.getsize(MIRRORF) > 3000000:  # ротация ~3 МБ
                    with open(MIRRORF, encoding="utf-8") as f:
                        tail = f.readlines()[-1500:]
                    with open(MIRRORF, "w", encoding="utf-8") as f:
                        f.writelines(tail)
            except Exception:
                pass
    except Exception:
        pass


def mirror_read():
    """Все строки зеркала (отдаёт /api/messages локального чата)."""
    try:
        with open(MIRRORF, encoding="utf-8") as f:
            return f.readlines()
    except Exception:
        return []


# ---------------------------------------------------------------- мозг: диалог

def hist_load():
    try:
        with open(HISTF, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def hist_append(user_text, assistant_text):
    h = hist_load()
    h.append({"role": "user", "content": user_text[:1000],
              "ts": time.strftime("%d.%m %H:%M")})
    h.append({"role": "assistant", "content": (assistant_text or "")[:1000],
              "ts": time.strftime("%d.%m %H:%M")})
    try:
        with open(HISTF, "w", encoding="utf-8") as f:
            json.dump(h[-40:], f, ensure_ascii=False)
    except Exception:
        pass

def hist_msgs(h):
    out = []
    for m in h[-16:]:
        c = m.get("content", "")
        if not c:
            continue
        if m.get("role") == "assistant" and (
                len(c.strip()) < 3 or c.lstrip().startswith('{"tool"')):
            continue  # v2.2.3: отравленные реплики («Ш», сырой JSON) не берём
        # v3.8.5: служебные маркеры срывов из истории ВЫБРАСЫВАЕМ — живой
        # тест поймал мозг, подражавшему своей же реплике «(веб: ответ
        # сорвался)» из history.json: следующая генерация буквально
        # возвращала этот маркер как ответ
        if m.get("role") == "assistant" and \
                re.fullmatch(r"\((веб: ответ сорвался|"
                             r"заявил без инструмента)\)", c.strip()):
            continue
        out.append({"role": m.get("role", "user"), "content": c[:1100]})
    return out

FRESH_RE = re.compile(r"(курс|цен[аыу]|стоит|новост|новинк|погод|сегодня|сейчас|"
                      r"последни|свеж|результат|кто выиграл|матч|счёт|итог|"
                      r"произошл|случил|вышел|обновлен|прогноз)", re.I)


def _strip_md(t):
    """Убирает markdown из ответа LLM (Telegram — простой текст)."""
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?m)^\s*#{1,4}\s*", "", t)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"(?m)^\s*[-*]\s+", "• ", t)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    return t.strip()


def brain_reply(text):
    """LLM -> (инструмент -> LLM) до 3 раз -> финальный ответ Шефу."""
    hist = hist_load()
    sysmsg = {"role": "system", "content": prompt_fill(SYSTEM)}
    utext = text
    if FRESH_RE.search(text):
        utext = (text +
                 "\n(Служебное напоминание: это свежий вопрос. Для новостей вызови "
                 "инструмент «новости», для курса валют/крипты — «курсы», для "
                 "прочего свежего — «интернет». Не отвечай без данных.)")
    msgs = [sysmsg] + hist_msgs(hist) + [{"role": "user", "content": utext}]

    ans = llm_chat(msgs)
    called = set()
    retried_claim = False
    retried_file = False
    retried_plan = False
    retried_order = False
    _order = bool(HANDS_ORDER_VERB_RE.search(text)
                  and HANDS_ORDER_CTX_RE.search(text))
    has_file = bool(FILE_MSG_RE.search(text) or FILE_PATH_RE.search(text))
    # v3.8.6: бюджет 8 — стражи (фантом/руки/план) тоже едят шаги: живой
    # тест 02.11 19:59 — 3 перезапроса подряд + 4 шага действий = 7 > 5,
    # ответ обрывался на «Выполняю тест по шагам».
    for _step in range(8):
        tool = parse_tool(ans)
        if not tool:
            # v3.1.1 (Task 97): файл-страж — файл прислан, но ни один
            # инструмент не вызван = мозг выдумал содержимое.
            if has_file and not called and not retried_file:
                retried_file = True
                log("file-guard: ответ о файле без чтения — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": FILE_FIX_MSG})
                ans = llm_chat(msgs)
                continue
            # v3.1.0: трос — «сохранил/создал» без вызова = ложь (Task 96)
            _claim_fix = claim_without_tool(ans, called)
            if _claim_fix:
                if retried_claim:
                    log("claim-guard: ложь повторилась — честный отказ")
                    hist_append(text, "(заявил действие без инструмента)")
                    return ("⚠️ Тут я запнулся, Шеф: заявил действие, но не "
                            "выполнил его. Скажи ещё раз — сделаю как надо.")
                retried_claim = True
                _kind = "фантом" if _claim_fix is PHANTOM_FIX_MSG else (
                    "руки" if _claim_fix is HANDS_FIX_MSG else "файлы/память")
                log("claim-guard(%s): заявлено без инструмента — перезапрос" % _kind)
                msgs.append({"role": "assistant", "content": ans})
                # v3.8.6: мозгу идёт ИМЕННО то сообщение стража, которое
                # вернулось (руки/фантом/файлы), а не всегда CLAIM_FIX_MSG
                msgs.append({"role": "user", "content": _claim_fix})
                ans = llm_chat(msgs)
                continue
            # v3.8.2 (Task 68): план-гард — «сейчас сделаю/запущу/наберу»
            # текстом без единого инструмента = действие НЕ выполнено
            if plan_without_tool(ans, called):
                if retried_plan:
                    log("plan-guard: план повторился — отдаю ответ как есть")
                    break
                retried_plan = True
                log("plan-guard: обещание действия без инструмента — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": PLAN_FIX_MSG})
                ans = llm_chat(msgs)
                continue
            # v3.8.6: приказ-гард — Шеф приказал руки-действие, а за весь
            # ход НИ ОДНОГО руки-инструмента = приказ не выполнен
            # (живой тест 20:03: «Делаю тест по факту» текстом и конец)
            if (_order and not (called & HANDS_ACT_TOOLS)
                    and not retried_order):
                retried_order = True
                log("order-guard: приказ рук без инструмента — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": HANDS_ORDER_FIX_MSG})
                ans = llm_chat(msgs)
                continue
            break
        name, args, say = tool
        called.add(name)
        # v3.7.0 (З5): комментарий перед исполнением — тоже речь Шефу;
        # сорвавшийся на английский say не показываем (мозг получит
        # результат инструмента в любом случае)
        if say and (_is_russian(say) or len(say.strip()) <= 40):
            send("⚙️ " + say[:300])
        if name not in ("спать", "проснись"):
            typing()
        res = tool_exec(name, args)
        if name == "спать":
            hist_append(text, "мозг выгружен из VRAM")
            return ((say + "\n") if say else "") + \
                "😴 Мозг выгружен из видеопамяти — VRAM свободна для игр. " \
                "«проснись» — верну обратно."

        if res == "SCREENSHOT":
            path = take_shot()
            if not path:
                why = ("экран залочен (Win+L) — Windows прячет картинку"
                       if _station_locked() else "ошибка захвата, см. jarvis.log")
                hist_append(text, "скриншот не удался: " + why)
                return "⚠️ Скриншот не получился: " + why + "."
            if not vision_available():
                send_photo(path, caption="📸 Экран (зрение не загружено — просто фото)")
                os.remove(path)
                hist_append(text, "отправил скриншот без описания")
                return ("📸 Выше скриншот. Зрение не загружено (не хватило VRAM) — "
                        "опишу только после «проснись» с полным режимом.")
            typing()
            try:
                desc = llm_vision(path)
            except Exception as e:
                log("vision ERR: %s" % e)
                desc = ""
            send_photo(path, caption="📸 Экран BULLDOZER, " + time.strftime("%d.%m %H:%M"))
            os.remove(path)
            hist_append(text, "[смотрел экран] " + desc[:700])
            return "👀 Вот что на экране:\n\n" + (desc or "(не смог разобрать снимок — фото выше)")

        typing()
        msgs.append({"role": "assistant", "content": ans})
        msgs.append({"role": "user", "content":
                     "Результат инструмента «%s»:\n%s\n\n"
                     "Если данных достаточно — ответь Шефу по-русски, коротко и по делу, "
                     "обычным текстом без JSON. Если нужен ещё один инструмент — "
                     "ответь снова одним JSON-объектом."
                     % (name, str(res)[:3000])})
        ans = llm_chat(msgs)

    clean = _strip_md(ans)
    if len(clean.strip()) < 3 or clean.lstrip().startswith('{"tool"'):
        log("brain_reply: дегенеративный ответ (%r) — вежливая замена" % clean[:60])
        hist_append(text, "(ответ сорвался — Шеф переспросит)")
        return "⚠️ Кажется, я запнулся на этом вопросе, Шеф. Спроси ещё раз или переформулируй."
    # v3.7.0: языковой страж (З5) — ответ без кириллицы переспрашиваем
    # один раз; остаётся английским — честный русский отказ.
    if not _is_russian(clean):
        log("lang-guard: ответ без русского (%r) — перезапрос" % clean[:60])
        journal("З5: ответ сорвался не на русский — перезапрос")
        msgs.append({"role": "assistant", "content": ans})
        msgs.append({"role": "user", "content": LANG_FIX_MSG})
        ans2 = llm_chat(msgs)
        clean2 = _strip_md(ans2)
        if _is_russian(clean2) and len(clean2.strip()) >= 3:
            ans, clean = ans2, clean2
        else:
            hist_append(text, "(ответ сорвался на английский)")
            return ("⚠️ Сорвался тут на английский, Шеф — а по закону З5 говорю "
                    "только по-русски. Переспроси, отвечу как положено.")
    hist_append(text, clean)
    return clean or "…"

# ---------------------------------------------------------------- обработка

HELP = ("🤖 *ДЖАРВИС v3.1 — думаю, ДЕЙСТВУЮ, УЧУСЬ, ФАЙЛЫ*\n\n"
        "Мозг — Qwen3.8-27B локально. С каждой задачей я становлюсь "
        "умнее: пишу себе скиллы и веду память.\n\n"
        "Мозг — Qwen3.8-27B прямо на твоей видеокарте, без облака. Пиши "
        "обычным языком — я сам пойму, что сделать.\n\n"
        "*Действия:*\n"
        "«освободи диск C» — чищу мусор и кэши\n"
        "«что можно перенести с C» — анализирую и подсказываю\n"
        "«перенеси Downloads на D» — переношу любые папки\n"
        "«запусти <что угодно>» — открываю ЛЮБЫЕ программы и игры\n"
        "«закрой хром» — закрываю любой процесс\n"
        "«выполни <команду>» — полные права администратора\n\n"
        "*Игры и видеокарта:*\n"
        "Запускаешь игру — я САМ выгружаюсь из видеопамяти и возвращаюсь "
        "после. Ярлыки на рабочем столе: «Освободить видеокарту» / «Вернуть мозг».\n\n"
        "*Быстрые команды:* статус, диски, место, большие, процессы, скрин, "
        "журнал, пинг, спать, проснись, выкл, перезагрузка, помощь\n\n"
        "*Интернет:* «что нового в мире», «курс биткоина», «погода в Москве» — "
        "найду свежее в сети.\n\n"
        "Или просто поговори со мной 😊")

def handle(text, chat_id):
    t = text.strip().lower()
    log("cmd: " + t[:80])
    mirror_append("tg", "boss", text)
    if PENDING["action"] and time.time() - PENDING["ts"] < 120:
        if t in ("да", "yes", "ок", "ok", "подтверждаю", "confirm"):
            return send(power_do(PENDING["action"]), chat_id)
        if "отмен" in t:
            PENDING["action"] = None
            return send("👌 Отменено.", chat_id)
        PENDING["action"] = None
    # ---- точные быстрые команды (всё остальное решает мозг) ----
    if t in ("/start", "/help") or t in ("помощь", "хелп", "help", "начало"):
        return send(HELP, chat_id)
    if t in ("статус", "/status", "стат"):
        return send(cmd_status(), chat_id)
    if t in ("диски", "/disks", "smart", "смарт"):
        return send(cmd_disks(), chat_id)
    if t in ("место", "/space", "свободное место"):
        return send(cmd_space(), chat_id)
    if t in ("процессы", "/ps", "проц"):
        return send(cmd_processes(), chat_id)
    if t in ("журнал", "лог"):
        return send(cmd_journal(), chat_id)
    if t in ("пинг", "/ping", "живой"):
        return send("🏓 Джарвис жив. Аптайм процесса: %s" %
                    time.strftime("%H:%M:%S", time.gmtime(time.time() - BIRTH)), chat_id)
    if t.startswith("скрин") or t == "/shot":
        r = cmd_shot()
        if r:
            send(r, chat_id)
        return
    if t.startswith("больш"):
        return send(cmd_bigfolders(), chat_id)
    if "выкл" in t or "shutdown" in t:
        return send(power_confirm("off"), chat_id)
    if "перезагруз" in t or "reboot" in t or "restart" in t:
        return send(power_confirm("reboot"), chat_id)
    if "спать" in t or t in ("сон", "sleep", "усни"):
        llm_stop("manual")
        journal("Мозг выгружен из VRAM по команде Шефа («спать»)")
        return send("😴 Мозг выгружен из видеопамяти — VRAM свободна для игр.\n"
                    "«проснись» — верну (загрузка ~минуты).", chat_id)
    if "проснись" in t or "проспись" in t or "подъём" in t or "wake" in t:
        LLM_PROC["sleeping"] = False
        LLM_PROC["reason"] = None
        try:
            os.remove(os.path.join(DATA, "BRAIN.SLEEP"))
        except OSError:
            pass
        send("☕ Загружаю мозг в видеопамять...", chat_id)
        ok = llm_start()
        journal("Мозг загружен в VRAM по команде Шефа («проснись»): %s" % ok)
        return send("🧠 Мозг на месте." if ok else
                    "⚠️ Не смог загрузить модель — глянь jarvis.log / llama.log.", chat_id)

    # ---------- всё остальное: свободное общение с мозгом ----------
    if LLM_PROC["sleeping"]:
        why = " — идёт игра, сам вернусь после её закрытия" if LLM_PROC.get("reason") == "game" else ""
        return send("😴 Мозг спит — видеопамять свободна%s. Быстрые команды работают. "
                    "«проснись» — загружу обратно." % why, chat_id)
    typing(chat_id)
    if not llm_ensure():
        return send("⚠️ Мозг не отвечает и не завёлся. Записал в jarvis.log.", chat_id)
    try:
        ans = brain_reply(text.strip())
        if ans:
            send(ans, chat_id)
    except Exception:
        log("brain ERR:\n" + traceback.format_exc())
        send("⚠️ Мозг споткнулся — записал в лог.", chat_id)

# ---------------------------------------------------------------- циклы

def polling_loop():
    log("polling запущен")
    poll_fail = 0  # v3.3.0: счётчик сбоев сети подряд (бэкофф)
    while True:
        try:
            off = 0
            if os.path.exists(OFFF):
                with open(OFFF) as f:
                    off = int(f.read().strip() or 0)
            r = tg("getUpdates", {"offset": off, "timeout": 25,
                                  "allowed_updates": ["message"]}, timeout=40)
            poll_fail = 0
            for u in r.get("result", []):
                with open(OFFF, "w") as f:
                    f.write(str(u["update_id"] + 1))
                m = u.get("message") or {}
                cid = str((m.get("chat") or {}).get("id", ""))
                if cid not in ALLOWED:
                    log("чужой chat %s — игнор" % cid)
                    continue
                text = m.get("text") or ""
                if not text:
                    # v3.1.0 «ФАЙЛЫ»: документы/фото/аудио/видео — скачать
                    # и отдать мозгу с путём; голос пока без расшифровки.
                    doc = m.get("document")
                    photo = m.get("photo")
                    audio = m.get("audio")
                    video = m.get("video")
                    cap = (m.get("caption") or "").strip()
                    if doc:
                        p, sz = tg_download(doc.get("file_id"),
                                            doc.get("file_name"))
                        if p:
                            text = ("Шеф прислал файл «%s» (%s, %s) — я его уже "
                                    "скачал: %s%s. Содержимого файла у тебя "
                                    "НЕТ: ответ о нём без инструмента — "
                                    "выдумка и ложь. Реши сам и сделай сразу: "
                                    "прочитать («читать_файл» с этим путём), "
                                    "сделать скилл («скилл_из_файла»), обработать. "
                                    "Неясно — один короткий вопрос Шефу."
                                    % (doc.get("file_name") or "файл",
                                       doc.get("mime_type") or "?",
                                       _fmt_size(sz), p,
                                       ("; подпись: " + cap) if cap else ""))
                        else:
                            send("⚠️ Не смог скачать файл — записал в журнал.", cid)
                    elif photo and isinstance(photo, list):
                        big = photo[-1]
                        p, sz = tg_download(big.get("file_id"),
                                            "фото_%s.jpg" %
                                            time.strftime("%Y%m%d_%H%M%S"))
                        if p:
                            text = ("Шеф прислал фото: %s%s. Содержимого у тебя "
                                    "НЕТ: сначала посмотри зрением "
                                    "(«посмотреть_файл») и ответь по существу "
                                    "снимка, а не наугад."
                                    % (p, ("; подпись: " + cap) if cap else ""))
                    elif audio or video:
                        kind = "аудио" if audio else "видео"
                        src = audio or video
                        is_voice = bool(m.get("voice"))
                        p, sz = tg_download(
                            src.get("file_id"),
                            src.get("file_name") or
                            ("голосовое_%s.ogg" %
                             time.strftime("%Y%m%d_%H%M%S") if is_voice else None))
                        if p:
                            # v3.2.0 «ГОЛОС»: расшифровываем локальным
                            # whisper.cpp (голосовые ogg -> ffmpeg -> wav).
                            tr = asr_transcribe(p, timeout=300)
                            if tr and not tr.startswith(("не смог", "движок",
                                                         "ошибка", "распознавание",
                                                         "файл не найден")):
                                # v3.2.0: путь в текст НЕ указываем — расшифровка
                                # уже сделана, страж путей не должен требовать
                                # повторного инструмента (путь — в журнал)
                                text = ("Шеф прислал голосовое (%s), расшифровка: "
                                        "«%s». Ответь по смыслу сказанного."
                                        % (_fmt_size(sz), tr))
                                journal("голосовое расшифровано: " + p)
                            else:
                                text = ("Шеф прислал %s-файл: %s (%s). "
                                        "Расшифровать не вышло (%s) — спроси "
                                        "Шефа, что с ним сделать."
                                        % (kind, p, _fmt_size(sz), tr[:120]))
                    if not text:
                        send("Пока понимаю только текст, файлы, фото и голос. "
                             "Видео-файлы без звука — в одной из следующих "
                             "фаз 🎤", cid)
                        continue
                try:
                    handle(text, cid)
                except Exception:
                    log("handle ERR:\n" + traceback.format_exc())
                    send("⚠️ Ошибка выполнения команды — записал в журнал.", cid)
        except Exception as e:
            # v3.3.0: сеть до Telegram моргает кластерами (10060/10054/
            # таймауты рукопожатия) — короткий лог + бэкофф вместо
            # многострочных простыней Windows и слепых 5-секундных пауз
            et = str(e)
            poll_fail += 1
            m10060 = re.search(r"\[WinError (\d+)\]", et)
            short = ("WinError " + m10060.group(1)) if m10060 else et[:70]
            netish = ("10060" in et or "10054" in et or "timed out" in et
                      or "handshake" in et or "closed" in et.lower())
            if netish:
                log("poll ERR сеть x%d: %s (бэкофф %dc)"
                    % (poll_fail, short, min(2 * poll_fail, 30)))
                if poll_fail in (1, 20, 100):  # полный текст — редко
                    log("poll ERR (полный): %s" % et)
            else:
                log("poll ERR: %s" % et)
            time.sleep(min(2 * poll_fail, 30))

def watchdog_loop():
    last_alert = {}
    log("watchdog запущен")
    while True:
        try:
            out = ps_run(r"""
Get-PSDrive C,D,E | ForEach-Object { "{0}={1:N1}" -f $_.Name,($_.Free/1GB) }
""", timeout=60)
            for ln in out.splitlines():
                if "=" not in ln:
                    continue
                drv, free = ln.split("=", 1)
                try:
                    fr = float(free.replace(",", "."))
                except ValueError:
                    continue
                # E: — там Загрузки/файлы: порог ниже, спамить нечестно
                lim = {"c": 10.0, "d": 10.0, "e": 1.0}.get(drv.lower(), 10.0)
                if fr < lim and time.time() - last_alert.get(drv, 0) > 3600:
                    last_alert[drv] = time.time()
                    send("🚨 *Мало места!* Диск %s: свободно %.1f ГБ. "
                         "Спроси меня: «что можно перенести с C» — подскажу." % (drv, fr))
                    journal("Алерт: мало места на %s (%.1f ГБ)" % (drv, fr))
        except Exception:
            log("watchdog ERR:\n" + traceback.format_exc())
        time.sleep(300)

def events_loop():
    """v3.4.0 «СОБЫТИЯ»: фоновые наблюдения — RAM на исходе, перегрев
    (термозона ACPI), GPU под полной нагрузкой долго, игра долго грузится/
    зависла. Уведомляет Шефа с кулдаунами, каждое событие — в журнал."""
    log("events запущен")
    ram_low = hot = gpu_hi = gpu_hot = None
    game_seen = {}
    last_alert = {}

    def alert(key, text, cooldown=3600):
        if time.time() - last_alert.get(key, 0) < cooldown:
            return
        last_alert[key] = time.time()
        send("📡 " + text)
        journal("Событие: " + text)

    while True:
        try:
            games = game_procs() if CFG.get("game_auto_vram", True) else set()
            now = time.time()
            for g in games:
                game_seen.setdefault(g, now)
            for g in list(game_seen):
                if g not in games:
                    del game_seen[g]
            out = ps_run(r"""
$os = Get-CimInstance Win32_OperatingSystem
"RAM={0:N1}|{1:N1}" -f ($os.FreePhysicalMemory/1MB),($os.TotalVisibleMemorySize/1MB)
try { $t=(Get-CimInstance -Namespace root/WMI -Class MSAcpi_ThermalZoneTemperature -EA Stop | Select-Object -First 1).CurrentTemperature; "THRM={0:N1}" -f ($t/10.0-273.15) } catch { "THRM=no" }
try { $g=(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -EA Stop | Measure-Object UtilizationPercentage -Sum).Sum; "GPU={0:N0}" -f $g } catch { "GPU=no" }
""", timeout=90)
            ram_free = ram_tot = thrm = gpu = None
            for ln in out.splitlines():
                if ln.startswith("RAM=") and "|" in ln:
                    try:
                        ram_free, ram_tot = (float(x.replace(",", "."))
                                             for x in ln[4:].split("|"))
                    except ValueError:
                        pass
                elif ln.startswith("THRM="):
                    if ln[5:] != "no":
                        try:
                            thrm = float(ln[5:].replace(",", "."))
                        except ValueError:
                            pass
                elif ln.startswith("GPU="):
                    if ln[4:] != "no":
                        try:
                            gpu = float(ln[4:].replace(",", "."))
                        except ValueError:
                            pass
            # RAM: меньше 4 ГБ свободных 5 минут подряд
            if ram_free is not None and ram_free < 4.0:
                ram_low = ram_low or now
                if now - ram_low > 300:
                    alert("ram", "Оперативка почти кончилась: свободно "
                          "%.1f ГБ из %.0f. Скажи «процессы» — посмотрю, "
                          "что жрёт, и закрою лишнее." % (ram_free, ram_tot or 32),
                          cooldown=6 * 3600)
            else:
                ram_low = None
            # термозона ACPI (чипсет/VRM платы): выше 75°C 5 минут
            if thrm is not None and thrm > 75.0:
                hot = hot or now
                if now - hot > 300:
                    alert("thrm", "Термозона материнской платы %.0f°C — "
                          "проверь охлаждение и пыль." % thrm,
                          cooldown=6 * 3600)
            else:
                hot = None
            # v3.5.0: реальная температура GPU из HWiNFO (SM2)
            gpu_temp = None
            try:
                import hwinfo_sensors as _hw
                for _r in _hw.read_all():
                    if (_r["sensor"].startswith("GPU") and _r["type"] == "темп"
                            and _r["label"].strip().lower() in
                            ("gpu temperature", "gpu tctl", "gpu die")):
                        gpu_temp = _r["value"]
                        break
            except Exception:
                pass
            # GPU: полная нагрузка 15+ минут — справка с температурой
            if gpu is not None and gpu > 85.0:
                gpu_hi = gpu_hi or now
                if now - gpu_hi > 900:
                    t = (" GPU сейчас %d°C." % gpu_temp
                         if gpu_temp is not None else
                         " Температуру скажу по «датчики».")
                    alert("gpu", "Видеокарта под полной нагрузкой уже %d мин.%s"
                          % ((now - gpu_hi) / 60, t), cooldown=12 * 3600)
            else:
                gpu_hi = None
            # GPU перегрев: реальные °C (просьба Шефа 02.11 — HWiNFO)
            if gpu_temp is not None and gpu_temp > 85.0:
                gpu_hot = gpu_hot or now
                if now - gpu_hot > 300:
                    alert("gputemp", "Видеокарта %.0f°C уже %d мин — проверь "
                          "охлаждение и пыль. «датчики» — полная сводка."
                          % (gpu_temp, (now - gpu_hot) / 60), cooldown=6 * 3600)
            else:
                gpu_hot = None
            # игра молода (<40 мин), но GPU почти не грузится 10+ минут:
            # возможно, долго грузится или зависла
            if games and gpu is not None and gpu < 8.0:
                for g, t0 in list(game_seen.items()):
                    if 600 < now - t0 < 2400:
                        alert("stall." + g,
                              "Игра %s работает %.0f мин, но GPU почти не "
                              "грузится — возможно, долго грузится или "
                              "зависла. Скажи «скрин» — посмотрю, что там."
                              % (g, (now - t0) / 60), cooldown=3600)
        except Exception:
            log("events ERR:\n" + traceback.format_exc())
        time.sleep(120)

def briefing_loop():
    sent_day = None
    while True:
        try:
            now = time.localtime()
            today = time.strftime("%Y-%m-%d", now)
            if now.tm_hour == 8 and sent_day != today:
                sent_day = today
                st = cmd_status()
                extra = ""
                if llm_health():
                    extra = "\n🧠 Мозг: нагружен и готов."
                elif LLM_PROC["sleeping"]:
                    extra = "\n😴 Мозг: спит (VRAM свободна)."
                send("🌅 *Доброе утро, Шеф!* Брифинг 08:00\n\n" + st + extra +
                     "\n\nХорошего дня! 🤖")
                journal("Утренний брифинг отправлен")
        except Exception:
            log("briefing ERR:\n" + traceback.format_exc())
        time.sleep(600)

def chat_watchdog():
    """v2.2.3: локальный чат 127.0.0.1:8123 жив (автоперезапуск ≤60 с)."""
    log("chat-watch запущен (локальный чат 8123)")
    while True:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8123/health",
                                        timeout=5) as r:
                ok = (r.status == 200)
        except Exception:
            ok = False
        if not ok:
            try:
                subprocess.Popen(
                    [sys.executable,
                     os.path.join(BASE, "chat", "chat_server.py")],
                    cwd=os.path.join(BASE, "chat"),
                    creationflags=0x08000000)
                log("chat-watch: локальный чат не отвечал — перезапустил")
            except Exception:
                log("chat-watch ERR:\n" + traceback.format_exc())
        time.sleep(60)


# ---------------------------------------------------------------- main

def main():
    log("TG-канал: %s" % ("через прокси MSK (стабильно)" if TG_OPENER
                            else "напрямую (плавающая сеть)"))
    hello = "--hello" in sys.argv
    log("=== ДЖАРВИС старт (v3.8.6 ФАНТОМ-РЕЗУЛЬТАТ: описание результата/проверки инструмента («инструмент вернул „НЕ подтвердилось“», «клик в (X,Y) не закрыл диалог», «курсор реально в (X,Y)») при НУЛЕ вызовов в ходе = выдумка — живой тест 02.11 19:47 поймал два таких ответа за 3-4 с; v3.8.5 ЧЕСТНЫЕ РУКИ-ТРОС: «передвинул/кликнул/напечатал/закрыл» без вызова инструмента рук = перезапрос — живой тест 02.11 поймал фантомное «курсор в (2500,1200), проверено» за 3 с без единого вызова, теперь это ловится уровнем кода; v3.8.4 АВТОФОКУС ПЕЧАТИ: без каретки печатать сам кликает в центр окна и повторяет проверку — у мозга стало на 2 шага меньше, цепочка не рвётся; v3.8.3 БЕЗ РАЦИИ: push-to-talk (ptt.py) удалён по приказу Шефа — Шеф не играет, пока мозг на видеокарте; голос — кнопка 🎤 в веб-чате; v3.8.1 СВЯЗЬ: Telegram через прокси MSK — прямые соединения с ПК2 плавали; v3.8.0 ТОРРЕНТЫ: uTorrent под управлением — список/удаление с верификацией, данные только по путям из базы; v3.7.0 ЧЕСТНЫЕ РУКИ: мышь/окна с самопроверкой — "
        "«проверено» или честное «НЕ получилось»; законы З5 язык + З6 "
        "честность, языковой страж; координатный контракт — только "
        "физические пиксели скриншота; v3.6.0 РОУТЕР; v3.5.0 ЗРЕНИЕ+ДАТЧИКИ; "
        "события v3.4.0; v3.3.0 (рация — удалена в v3.8.3); v3.2.1 СВЕРКА; v3.2.0 ГЛАЗА И ГОЛОС; "
        "v3.1.0 ФАЙЛЫ; законы v3.0.1; ученик v3.0; v2.3.0 МАКС) ===")
    journal("Джарвис v3.8.3 БЕЗ РАЦИИ (Task 103, 02.11): приказ Шефа — "
            "рация (push-to-talk, ptt.py) не нужна: Шеф не играет при мозге "
            "на видеокарте. Задача JarvisPTT, ptt.py и инструмент "
            "«рация_клавиша» удалены; голос остался — кнопка 🎤 в веб-чате "
            "и озвучка ответов 🔊 (piper)")
    journal("Джарвис v3.8.6 ФАНТОМ-РЕЗУЛЬТАТ (Task 107, 02.11 вечер): живой "
            "E2E тестов Рук поймал новую дыру честности — мозг отвечал за "
            "3-4 секунды без единого вызова инструментов, но со ссылкой на "
            "результат: «инструмент вернул „НЕ подтвердилось“», «клик в "
            "(1780,1210) не закрыл диалог», «курсор реально в (1920,1000)». "
            "Отрицательные формы и заявления о состоянии прошлые стражи "
            "пропускали. Теперь: описание результата/проверки инструмента "
            "при нуле вызовов в ходе = перезапрос; мозгу идёт конкретное "
            "сообщение стража (руки/фантом), а не общее")
    journal("Джарвис v3.8.5 ЧЕСТНЫЕ РУКИ-ТРОС (Task 68, 02.11 вечер): живой "
            "тест мыши поймал фантом — мозг доложил «передвинул курсор в "
            "(2500,1200), инструмент подтвердил» за 3 секунды БЕЗ единого "
            "вызова инструмента; курсор не двигался. Трос честности "
            "расширен на руки: прошедшее время руки-глагола (передвинул/"
            "кликнул/напечатал/закрыл...) + руки-контекст без вызова "
            "соответствующего инструмента = перезапрос; «скрин»/«окна» "
            "оправдывают только глаголы проверки")
    journal("Джарвис v3.8.1 СВЯЗЬ (Task 105, ночь 02.11): Telegram ходит "
            "через прокси на MSK (config.json tg_proxy) — прямые соединения "
            "с ПК2 всю ночь рвались (poll ERR, send ERR в jarvis.log); "
            "мозг и локальный чат по-прежнему напрямую (127.0.0.1)")
    journal("Джарвис v3.8.2 ПРОВЕРКА РУК (Task 68, 02.11): живой аудит "
            "клавиатуры/мыши нашёл краш key_combo на буквах (VkKeyW не "
            "существует — заменил на VkKeyScanW) и «планы вместо действий» "
            "(мозг отвечал «сейчас сделаю» без инструмента). Добавлен "
            "план-гард, правило «действие = сразу JSON», печать докладывает "
            "целевое окно")
    journal("Джарвис v3.8.0 ТОРРЕНТЫ (Task 105, ночь 02.11): приказ Шефа — "
            "пустой uTorrent и игру (RDR2, 101 ГБ) удаляет Джарвис. "
            "Инструмент «торренты»: список/удаление, полная очистка через "
            "сброс базы при остановленном клиенте, данные — только по путям "
            "из resume.dat и только при явном «файлы=да»")
    journal("Джарвис v3.7.0 ЧЕСТНЫЕ РУКИ (Task 104, 02.11): ночь вскрыла "
            "промахи мыши (мозг путал логические/физические пиксели 4K@250%) "
            "и доклады «нажал» без проверки. Теперь win_ctl проверяет каждое "
            "действие чтением факта; законы З5 (язык) и З6 (честность); "
            "языковой страж — ответ не по-русски переспрашивается")
    if hello:
        send("🤖 *ДЖАРВИС v3.0 УЧЕНИК на связи!*\n\n"
             "Теперь я ещё и учусь: веду память и пишу себе скиллы — "
             "новые умения остаются со мной навсегда.\n"
             "Теперь я не только отвечаю — я ДЕЙСТВУЮ: чищу диск от мусора, "
             "подсказываю что перенести, запускаю и закрываю программы, а когда "
             "ты запускаешь игру — сам освобождаю видеокарту и возвращаюсь после.\n\n"
             "Пиши обычным языком: «освободи диск C», «что можно перенести», "
             "«запусти стим». «помощь» — список команд.")
    threading.Thread(target=llm_start, daemon=True).start()
    for fn in (polling_loop, watchdog_loop, events_loop, briefing_loop,
               llm_watchdog, game_watch_loop, flags_loop, chat_watchdog):
        threading.Thread(target=fn, daemon=True).start()
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
