#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ДЖАРВИС — локальный чат-сервер (127.0.0.1:8123).
Отдаёт веб-чат и проксирует мозг (llama-server :1234) с потоковым выводом.
Запуск: pythonw.exe chat_server.py [--open]
Ярлык на рабочем столе запускает этот скрипт и открывает браузер.
v3.1.1 (Task 97): файлы в веб-чате — POST /api/upload (сохранение в
Входящие, как из Telegram), files[] в /api/chat, GET /api/files (список),
GET /api/file (скачивание из папок Джарвиса).
v3.2.0 (Task 98) «ГЛАЗА И ГОЛОС»: /api/status спрашивает сам
llama-server о зрении (vision_available — пробный кадр, а не локальный
флаг, который врал); скрин в веб-чате описывается зрением, как в TG;
POST /api/asr — голосовой ввод: wav из браузера -> whisper.cpp -> текст
(кнопка микрофона в index.html).
v3.2.1 (Task 99) «СВЕРКА»: веб-чату — 6 шагов генерации (было 3; сценарий
  сверки = скилл+зрение+PowerShell+ответ, в веб-чате генерация в НАЧАЛЕ
  итерации — в отличие от TG, где ответ рождается внутри последней),
  чтобы многошаговые задачи не упирались в лимит.
v3.3.0 (Task 100): DPI-осознанность (скрины 4K@200% в физических
  пикселях, без мыльных 1920x1080).
v3.8.3 (Task 103): push-to-talk «рация» (ptt.py) удалён по приказу
  Шефа — /api/asr кормит только кнопку 🎤 веб-чата.
v3.4.0 (Task 101) «СОБЫТИЯ»: GET /api/tts?text=... — озвучка ответа
  голосом Ирины (piper) для кнопки 🔊 в веб-чате.
v3.10 (Task 128) «УМНЫЙ РЕЖИМ + СТАРШИЕ»: /api/chat теперь с тем же
  умным маршрутом, что и Telegram (jarvis.smart_mode): простое —
  мгновенно; слово «подумай»/авто-сложное — с размышлениями модели на
  первом шаге (думание Шефу не показываем); авто-сложное при наличии
  cloud_api_key и явное «спроси у старших» — облачный старший брат
  (jarvis.cloud_ask), отвечает даже при спящем локальном мозге (игра).
"""
import json, os, sys, time, base64, threading, traceback
import subprocess
import urllib.parse
import urllib.request
import urllib.error
import ctypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:  # v3.3.0: физические пиксели экрана — 4K@200% без виртуализации
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

CHAT_DIR = os.path.dirname(os.path.abspath(__file__))        # D:\Jarvis\chat
BASE = os.path.dirname(CHAT_DIR)                             # D:\Jarvis
PORT = 8123
MAX_UPLOAD = 100 * 1024 * 1024  # v3.1.1: стоп-кран загрузки, как в Telegram
MAX_VOICE = 30 * 1024 * 1024   # v3.2.0: голосовой ввод (wav 16k ~ 32 КБ/с)

sys.path.insert(0, BASE)
import jarvis  # noqa: E402  (конфиг, инструменты, обёртки LLM)

SYSTEM_LOCAL = jarvis.SYSTEM.replace(
    "и общаешься с ним в Telegram",
    "и общаешься с ним в окне локального чата прямо на этом ПК").replace(
    "Пиши простым текстом БЕЗ markdown",
    "Отвечай простым текстом БЕЗ markdown")

CHATLOG = os.path.join(CHAT_DIR, "chat.log")


def clog(msg):
    """Локальный журнал чат-сервера (Task 89)."""
    try:
        with open(CHATLOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (time.strftime("%d.%m %H:%M:%S"), msg))
    except Exception:
        pass


def _exhook(a):
    """v2: падения потоков-обработчиков — в chat.log (pythonw глотает stderr)."""
    try:
        clog("поток упал: %s" % "".join(traceback.format_exception(
            a.exc_type, a.exc_value, a.exc_traceback)).strip()[-600:])
    except Exception:
        pass


if hasattr(threading, "excepthook"):
    threading.excepthook = _exhook


def web_save_upload(name, data):
    """v3.1.1 (Task 97): файл из браузера -> Входящие (тот же конвейер, что
    у Telegram: _safe_name + _unique_path + журнал). -> (путь, размер)."""
    os.makedirs(jarvis.INCOMING, exist_ok=True)
    fn = jarvis._safe_name(name or "") or "файл.bin"
    dst = jarvis._unique_path(jarvis.INCOMING, fn)
    with open(dst, "wb") as fh:
        fh.write(data)
    try:
        jarvis.journal("файл получен (веб-чат): " + dst)
    except Exception:
        pass
    return dst, len(data)


def _files_json():
    """v3.1.1: последние файлы Входящих + выгрузки для панели браузера."""
    out = []
    for folder, tag in ((jarvis.INCOMING, "in"), (jarvis.FILES_DIR, "out")):
        if not os.path.isdir(folder):
            continue
        for fn in os.listdir(folder):
            p = os.path.join(folder, fn)
            if os.path.isfile(p):
                try:
                    st = os.stat(p)
                    out.append({"p": p, "n": fn, "s": st.st_size,
                                "t": int(st.st_mtime), "d": tag})
                except OSError:
                    pass
    out.sort(key=lambda x: -x["t"])
    return out[:60]


def llm_stream(messages, max_tokens=800, temperature=0.7, think=False):
    """v3.10 (Task 128): think=True — включаю размышления модели (умный
    режим). reasoning_content сервера не читаем (не показываем); если
    <think> идёт прямо в content — придерживаем поток до </think>."""
    body = {"model": jarvis.MODEL_ID, "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature, "top_p": 0.8,
            "chat_template_kwargs": {"enable_thinking": bool(think)},
            "stream": True}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        jarvis.LLM_URL + "/v1/chat/completions", data=data,
        headers={"Content-Type": "application/json"})
    _hold, _in_think, _checked = [], False, False
    with urllib.request.urlopen(req, timeout=420) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            try:
                j = json.loads(payload)
            except Exception:
                continue
            delta = (j.get("choices") or [{}])[0].get("delta") or {}
            txt = delta.get("content") or ""
            if not txt:
                continue
            if not think:
                yield txt
                continue
            if not _checked:
                _hold.append(txt)
                st = "".join(_hold).lstrip()
                if st.startswith("<think"):
                    _in_think, _checked = True, True
                elif len(st) >= 12:
                    yield "".join(_hold)
                    _hold, _checked = [], True
                continue
            if _in_think:
                _hold.append(txt)
                joined = "".join(_hold)
                if "</think>" in joined:
                    tail = joined.split("</think>", 1)[1]
                    _in_think, _hold = False, []
                    if tail:
                        yield tail
                continue
            yield txt


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send_json(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                with open(os.path.join(CHAT_DIR, "index.html"), "rb") as fh:
                    b = fh.read()
            except Exception:
                b = "<h1>index.html не найден</h1>".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        elif self.path == "/api/status":
            self._send_json({"ok": jarvis.llm_health(),
                             "model": jarvis.MODEL_ID,
                             "vision": jarvis.vision_available(),
                             "voice": jarvis.asr_available()})
        elif self.path.startswith("/api/messages"):
            # v2 (Task 89): зеркало переписки TG + веб (дублирование каналов)
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            try:
                after = int((qs.get("after") or ["0"])[0])
            except ValueError:
                after = 0
            lines = jarvis.mirror_read()
            out = []
            for i in range(max(after, 0), len(lines)):
                try:
                    j = json.loads(lines[i])
                except Exception:
                    continue
                j["i"] = i
                out.append(j)
            self._send_json({"n": len(lines), "msgs": out[-120:]})
        elif self.path == "/api/files":
            # v3.1.1 (Task 97): список файлов для панели браузера
            self._send_json({"ok": True, "files": _files_json()})
        elif self.path.startswith("/api/tts"):
            # v3.4.0 (Task 101): озвучка ответа голосом Ирины (piper)
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            text = (qs.get("text") or [""])[0][:600].strip()
            if not text:
                self._send_json({"error": "пустой текст"}, 400)
                return
            exe = jarvis.CFG.get("piper_exe")
            voice = jarvis.CFG.get("piper_voice")
            if not (exe and voice and os.path.isfile(exe)
                    and os.path.isfile(voice)):
                self._send_json({"error": "piper не установлен"}, 503)
                return
            out = os.path.join(jarvis.DATA, "web_tts.wav")
            try:
                p = subprocess.run([exe, "--model", voice,
                                    "--output_file", out],
                                   input=text.encode("utf-8"),
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=120)
                if p.returncode != 0 or not os.path.isfile(out) \
                        or os.path.getsize(out) < 200:
                    self._send_json({"error": "синтез не удался"}, 500)
                    return
                with open(out, "rb") as fh:
                    b = fh.read()
                os.remove(out)
            except Exception as e:
                self._send_json({"error": str(e)[:200]}, 500)
                return
            clog("tts: %d симв -> %d Б" % (len(text), len(b)))
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        elif self.path.startswith("/api/file"):
            # v3.1.1 (Task 97): скачать файл ИЗ папок Джарвиса (только они)
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            p = (qs.get("p") or [""])[0]
            npth = os.path.normcase(os.path.abspath(p))
            allowed = False
            for rd in (jarvis.INCOMING, jarvis.FILES_DIR):
                r = os.path.normcase(os.path.abspath(rd))
                if npth == r or npth.startswith(r + os.sep):
                    allowed = True
            if not allowed or not p or not os.path.isfile(p):
                self._send_json({"error": "нет такого файла в папках Джарвиса"}, 404)
                return
            ext = os.path.splitext(p)[1].lower()
            mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
                    ".txt": "text/plain", ".md": "text/plain", ".log": "text/plain",
                    ".csv": "text/csv", ".json": "application/json",
                    ".pdf": "application/pdf", ".mp3": "audio/mpeg",
                    ".wav": "audio/wav", ".ogg": "audio/ogg",
                    ".mp4": "video/mp4", ".webm": "video/webm"}.get(
                        ext, "application/octet-stream")
            try:
                with open(p, "rb") as fh:
                    b = fh.read()
            except OSError as e:
                self._send_json({"error": str(e)}, 500)
                return
            disp = ("inline" if mime.startswith("image/") else "attachment") + \
                "; filename*=UTF-8''" + urllib.parse.quote(os.path.basename(p))
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Content-Disposition", disp)
            self.end_headers()
            self.wfile.write(b)
        elif self.path == "/health":
            self._send_json({"ok": True})
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def do_POST(self):
        # v3.2.0 (Task 98): голосовой ввод — wav из браузера -> whisper -> текст
        if self.path.startswith("/api/asr"):
            try:
                ln = int(self.headers.get("Content-Length", 0))
            except ValueError:
                ln = 0
            if ln < 1200:
                self._send_json({"error": "слишком короткая запись"}, 400)
                return
            if ln > MAX_VOICE:
                self._send_json({"error": "голосовое больше 30 МБ — не приму"}, 413)
                return
            try:
                data = self.rfile.read(ln)
                p = os.path.join(jarvis.DATA,
                                 "voice_%s.wav" % time.strftime("%Y%m%d_%H%M%S"))
                with open(p, "wb") as fh:
                    fh.write(data)
            except Exception as e:
                self._send_json({"error": "не смог принять запись: %s" % e}, 500)
                return
            try:
                text = jarvis.asr_transcribe(p, timeout=300)
            finally:
                try:
                    os.remove(p)
                except OSError:
                    pass
            clog("голос: %d Б -> %d символов" % (ln, len(text or "")))
            bad = text.startswith(("не смог", "движок", "ошибка",
                                   "распознавание", "файл не найден"))
            if bad:
                self._send_json({"error": text[:300]}, 500)
                return
            self._send_json({"ok": True, "text": text})
            return
        # v3.1.1 (Task 97): загрузка файла из браузера -> Входящие
        if self.path.startswith("/api/upload"):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = (qs.get("name") or ["файл.bin"])[0][:200]
            try:
                ln = int(self.headers.get("Content-Length", 0))
            except ValueError:
                ln = 0
            if ln <= 0:
                self._send_json({"error": "пустой файл"}, 400)
                return
            if ln > MAX_UPLOAD:
                self._send_json({"error": "больше 100 МБ — положи прямо в папку "
                                          "Входящие"}, 413)
                return
            try:
                data = self.rfile.read(ln)
                p, sz = web_save_upload(name, data)
            except Exception as e:
                self._send_json({"error": "не смог сохранить: %s" % e}, 500)
                return
            clog("веб-загрузка: %s (%d Б)" % (p, sz))
            self._send_json({"ok": True, "path": p, "size": sz,
                             "name": os.path.basename(p)})
            return
        if self.path != "/api/chat":
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        try:
            ln = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(ln).decode("utf-8"))
        except Exception:
            self._send_json({"error": "bad request"}, 400)
            return
        message = str(req.get("message", "")).strip()[:4000]
        # v3.1.1 (Task 97): приложенные файлы (уже лежат в Входящих)
        clean = []
        for fd in (req.get("files") or [])[:5]:
            if not isinstance(fd, dict):
                continue
            p = str(fd.get("path") or "").strip()
            if p and os.path.isfile(p):
                try:
                    clean.append((p, os.path.getsize(p)))
                except OSError:
                    pass
        disp = message
        if clean:
            disp = ((message + "\n") if message else "") + "\n".join(
                "📎 %s (%s)" % (os.path.basename(p), jarvis._fmt_size(sz))
                for p, sz in clean)
        # v3 (Task 91): прямой канал ИИ-ИИ — GLM (z.ai) пишет через API как коллега
        is_glm = str(req.get("sender", "boss")).lower().strip() in ("glm", "ai")
        jarvis.mirror_append("web", "glm" if is_glm else "boss", disp)
        # v3.10 (Task 128): умный маршрут как в Telegram (коллега GLM — без)
        _mode = None if is_glm else jarvis.smart_mode(message)
        _want_cloud = _mode == "cloud" or (
            _mode == "big" and (jarvis.CFG.get("cloud_api_key") or "").strip())

        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def emit(obj):
            try:
                self.wfile.write((json.dumps(obj, ensure_ascii=False) + "\n").encode())
                self.wfile.flush()
                return True
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                return False

        try:
            if not message and not clean:
                emit({"type": "error", "text": "пустое сообщение"})
                return
            if message in ("пинг", "/ping"):
                jarvis.mirror_append("web", "jarvis", "🏓 локальный чат жив")
                emit({"type": "done",
                      "text": "🏓 Локальный чат жив. Мозг: %s." %
                              ("на связи" if jarvis.llm_health() else "спит")})
                return
            if _want_cloud:
                # v3.10 (Task 128): старший брат — облако, VRAM не занимает,
                # отвечает даже когда локальный мозг спит (игра)
                emit({"type": "waiting"})
                try:
                    c_ans, c_err = jarvis.cloud_ask(
                        message, jarvis.hist_msgs(jarvis.hist_load()))
                except Exception as e:
                    c_ans, c_err = None, str(e)
                if c_ans:
                    txt = "🛰 %s\n\n%s" % (
                        "Сложный вопрос — спросил у старшего брата:"
                        if _mode == "big" else "Спросил у старших братьев:",
                        jarvis._strip_md(c_ans))
                    jarvis.hist_append(
                        disp, ("[старший брат] " if _mode == "big"
                               else "[старшие братья] ") + c_ans[:900])
                    jarvis.mirror_append("web", "jarvis", txt)
                    emit({"type": "tok", "text": txt})
                    emit({"type": "done", "text": txt})
                    try:
                        jarvis.tg("sendMessage",
                                  {"chat_id": jarvis.CHAT,
                                   "text": ("🖥 Локальный чат\nШеф: %s\n\n"
                                            "Джарвис: %s"
                                            % (disp[:800], txt[:2400]))[:3900]})
                    except Exception:
                        pass
                    return
                emit({"type": "tok", "text":
                      "🛰 Старший брат не на связи (%s) — отвечаю сам, "
                      "глубоко.\n\n" % str(c_err or "?")[:70]})
                _mode = "think"
            if not jarvis.llm_health():
                emit({"type": "waiting"})
                if not jarvis.llm_ensure(timeout=200):
                    emit({"type": "error",
                          "text": "мозг не отвечает (llama-server не запустился — "
                                  "см. D:\\Jarvis\\jarvis.log)"})
                    return
            sysmsg = {"role": "system",
                      "content": jarvis.prompt_fill(SYSTEM_LOCAL)}
            if is_glm:  # v3: собеседник — не Шеф, а ИИ-коллега
                sysmsg["content"] += (
                    "\n\nОСОБОЕ УКАЗАНИЕ: сейчас с тобой общается GLM — старший "
                    "ИИ-коллега (z.ai): он управляет сервером и песочницей Шефа и "
                    "пишет тебе через API локального чата. Отвечай ему как коллеге-"
                    "профессионалу: сжатый отчёт по делу, без приветствий дворецкого. "
                    "Данные о ПК при необходимости бери инструментами.")
            utext = message
            if clean:
                # v3.1.1 (Task 97): подаём мозгу так же, как файлы из Telegram;
                # подчёркиваем: содержимого у мозга НЕТ — только пути.
                utext = ((message + "\n\n") if message else "") + (
                    "Шеф прикрепил через веб-чат файл(ы) — они сохранены "
                    "на диск, но содержимого у тебя ЕЩЁ НЕТ:\n" + "\n".join(
                        "- %s (%s)" % (p, jarvis._fmt_size(sz))
                        for p, sz in clean) +
                    "\nОтвет о файле без чтения — выдумка и ложь. Сначала "
                    "вызови «читать_файл» (текст) или «посмотреть_файл» "
                    "(картинка), потом отвечай строго по содержимому; из "
                    "файла можно сделать скилл («скилл_из_файла»). Неясно — "
                    "один короткий вопрос Шефу.")
            if jarvis.FRESH_RE.search(utext):
                utext = (utext +
                         "\n(Служебное напоминание: это свежий вопрос — узнай "
                         "актуальные данные инструментом «новости», «курсы» или "
                         "«интернет».)")
            # v2 (Task 89): единая история с Telegram (history.json)
            msgs = ([sysmsg] + jarvis.hist_msgs(jarvis.hist_load()) +
                    [{"role": "user", "content": utext}])
            final = ""
            called = set()
            retried_claim = False
            retried_file = False
            retried_plan = False
            retried_order = False
            hist_n = len(jarvis.hist_msgs(jarvis.hist_load()))
            for _step in range(8):  # v3.8.2: 8 шагов — цепочка печать->скрин->клик->печать требовала больше
                buf, head, visible = [], "", None
                ctx_retry = False
                while True:
                    try:
                        # v3.10 (Task 128): думание — только первый шаг
                        _think_now = (_mode in ("think", "big")) and _step == 0
                        for tok in llm_stream(
                                msgs,
                                max_tokens=(int(jarvis.CFG.get(
                                    "llm_think_tokens", 2000))
                                    if _think_now else 800),
                                think=_think_now):
                            if visible is None:
                                head += tok
                                st = head.lstrip()
                                if st.startswith("{"):
                                    visible = False
                                elif len(st) >= 8 or "\n" in st:
                                    visible = True
                                    emit({"type": "tok", "text": head})
                            elif visible:
                                emit({"type": "tok", "text": tok})
                            buf.append(tok)
                    except urllib.error.HTTPError as _e:
                        # v3.8.4 ctx-guard: llama-server ответил 400 «request
                        # exceeds context size» — раньше это убивало весь
                        # запрос. Сбрасываем старую историю (системный промпт
                        # и текущая цепочка инструментов остаются) и повторяем
                        # тот же шаг.
                        if _e.code == 400 and not ctx_retry:
                            ctx_retry = True
                            clog("ctx-guard: 400 (контекст переполнен) — "
                                 "сброс истории, повтор шага")
                            msgs = [sysmsg] + msgs[1 + hist_n:]
                            buf, head, visible = [], "", None
                            continue
                        raise
                    break
                if visible is None and head:
                    emit({"type": "tok", "text": head})
                ans = jarvis._strip_think("".join(buf))
                tool = jarvis.parse_tool(ans)
                if not tool:
                    # v3.1.1 (Task 97): файл-страж — файлы прикреплены, но ни
                    # один инструмент не вызван = содержимое выдумано.
                    # v3.2.0 (Task 98): + явный ПУТЬ в тексте («расшифруй
                    # D:\...») — содержимое тоже неизвестно мозгу.
                    if (clean or jarvis.FILE_PATH_RE.search(message)) \
                            and not called and not retried_file:
                        retried_file = True
                        clog("file-guard: ответ о файле без чтения — перезапрос")
                        msgs.append({"role": "assistant", "content": ans})
                        msgs.append({"role": "user",
                                     "content": jarvis.FILE_FIX_MSG})
                        continue
                    # v3.1.0: трос — «сохранил/создал» без вызова (Task 96)
                    # v3.8.5: + руки («передвинул/кликнул/напечатал» без
                    # инструмента) — claim_without_tool возвращает ГОТОВОЕ
                    # сообщение-исправление (файловое или рук)
                    _claim_fix = jarvis.claim_without_tool(ans, called)
                    if _claim_fix:
                        if retried_claim:
                            clog("claim-guard: повторная ложь — честный отказ")
                            jarvis.hist_append(disp, "(заявил без инструмента)")
                            emit({"type": "done",
                                  "text": "⚠️ Я заявил действие, но не выполнил "
                                          "его (внутренняя проверка честности). "
                                          "Спроси ещё раз."})
                            return
                        retried_claim = True
                        clog("claim-guard: перезапрос после ложного «сделал»")
                        msgs.append({"role": "assistant", "content": ans})
                        msgs.append({"role": "user",
                                     "content": _claim_fix})
                        continue
                    # v3.8.2 (Task 68): план-гард — «сейчас сделаю/запущу/
                    # наберу» текстом без единого инструмента = НИЧЕГО
                    # не произошло. Один перезапрос.
                    if jarvis.plan_without_tool(ans, called) and not retried_plan:
                        retried_plan = True
                        clog("plan-guard: обещание действия без инструмента — перезапрос")
                        msgs.append({"role": "assistant", "content": ans})
                        msgs.append({"role": "user",
                                     "content": jarvis.PLAN_FIX_MSG})
                        continue
                    # v3.8.6 (Task 107): приказ-гард — Шеф ПРИКАЗАЛ
                    # руки-действие (передвинь/кликни/напечатай/открой...),
                    # а за весь ход НИ ОДНОГО руки-инструмента = приказ
                    # НЕ выполнен (живой тест 02.11 20:03/20:09: мозг дважды
                    # уходил в «Честно: я ничего не делал — это была ложь.
                    # Сейчас делаю по факту» и заканчивал без вызовов).
                    if (jarvis.HANDS_ORDER_VERB_RE.search(message)
                            and jarvis.HANDS_ORDER_CTX_RE.search(message)
                            and not (called & jarvis.HANDS_ACT_TOOLS)
                            and not retried_order):
                        retried_order = True
                        clog("order-guard: приказ рук без инструмента — перезапрос")
                        msgs.append({"role": "assistant", "content": ans})
                        msgs.append({"role": "user",
                                     "content": jarvis.HANDS_ORDER_FIX_MSG})
                        continue
                    final = ans
                    if len(final.strip()) < 3 and _step < 2:
                        # v2: генерация оборвалась в размышлениях — повтор
                        msgs = msgs + [{"role": "system",
                                        "content": "Важно: не размышляй вслух, "
                                                   "ответь сразу готовым текстом."}]
                        continue
                    break
                name, args, say = tool
                called.add(name)
                if say:
                    emit({"type": "say", "text": say[:300]})
                res = jarvis.tool_exec(name, args)
                if res == "SCREENSHOT":
                    path = jarvis.take_shot()
                    if path:
                        with open(path, "rb") as fh:
                            emit({"type": "image",
                                  "b64": base64.b64encode(fh.read()).decode()})
                        # v3.2.0: в веб-чате скрин теперь ЕЩЁ и описываем
                        # зрением (как в TG), а не просто показываем картинку
                        if jarvis.vision_available():
                            try:
                                desc = jarvis.llm_vision(path)
                            except Exception as e:
                                jarvis.log("vision ERR: %s" % e)
                                desc = ""
                            res = ("скриншот показан Шефу в чате. Описание "
                                   "зрением: %s" % (desc or "(не разобрал)"))
                        else:
                            res = ("скриншот показан Шефу в чате (зрение не "
                                   "загружено — не выдумывай описание, скажи "
                                   "что видишь только картинку выше)")
                        os.remove(path)
                    else:
                        res = "скриншот не удался (экран заблокирован?)"
                emit({"type": "tool", "name": name})
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content":
                             "Результат инструмента «%s»:\n%s\n\n"
                             "Если данных достаточно — ответь по-русски коротко, "
                             "обычным текстом без JSON. Если нужен ещё инструмент — "
                             "снова один JSON-объект." % (name, str(res)[:3000])})
            final_txt = jarvis._strip_md(final)
            if len(final_txt.strip()) < 3 or final_txt.lstrip().startswith('{"tool"'):
                clog("веб-ответ сорвался (дегенеративный): %r" % final_txt[:80])
                jarvis.hist_append(disp, "(веб: ответ сорвался)")
                emit({"type": "error",
                      "text": "мозг запнулся (оборванная генерация) — спроси ещё раз"})
                return
            emit({"type": "done", "text": final_txt})
            # v2 (Task 89): общая история + зеркало + дубль в Telegram
            jarvis.hist_append(disp, final_txt)
            jarvis.mirror_append("web", "jarvis", final_txt)
            try:
                jarvis.tg("sendMessage",
                          {"chat_id": jarvis.CHAT,
                           "text": (("🤝 GLM ↔ Джарвис\nGLM: %s\n\nДжарвис: %s"
                                     if is_glm else
                                     "🖥 Локальный чат\nШеф: %s\n\nДжарвис: %s")
                                    % (disp[:800], final_txt[:2400]))[:3900]})
            except Exception as e:
                clog("дубль в Telegram не ушёл: %s" % e)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass
        except Exception as e:
            try:
                emit({"type": "error", "text": str(e)[:300]})
            except Exception:
                pass


def main():
    open_browser = "--open" in sys.argv
    # v2 (Task 89): на Windows allow_reuse_address разрешает ДВОЙНОЙ bind —
    # так и завёлся процесс-дубль. Сначала проверяем живой инстанс.
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/health" % PORT,
                                    timeout=3) as r:
            alive = (r.status == 200)
    except Exception:
        alive = False
    if alive:
        if open_browser:
            os.startfile("http://127.0.0.1:%d" % PORT)
        return
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        # уже запущен — просто открыть чат
        if open_browser:
            os.startfile("http://127.0.0.1:%d" % PORT)
        return
    Handler.timeout = 75  # v2: прибираем зависшие keep-alive соединения
    if open_browser:
        def _open():
            time.sleep(0.8)
            os.startfile("http://127.0.0.1:%d" % PORT)
        threading.Thread(target=_open, daemon=True).start()
    clog("чат-сервер запущен v3.10 умный режим + старшие братья (pid %s)"
         % os.getpid())
    while True:  # v2: serve_forever может упасть — цикл перезапускает
        try:
            srv.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            break
        except Exception:
            clog("serve_forever упал: %s" % traceback.format_exc()[-800:])
            time.sleep(2)


if __name__ == "__main__":
    main()
