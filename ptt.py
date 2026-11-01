#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ДЖАРВИС — push-to-talk «РАЦИЯ» (v3.3.0, Task 100).
Держишь глобальный хоткей (по умолчанию CapsLock) — пишем с микрофона,
отпускаешь — распознавание (whisper через /api/asr) -> мозг (/api/chat) ->
плашка с ответом поверх любого окна + озвучка голосом Ирины (piper).
Работает из любой игры, чат открывать не нужно.

Запуск:  pythonw.exe ptt.py                      (жить и слушать хоткеи)
         python.exe ptt.py --selftest file.wav   (прогон конвейера без хоткея;
                                                  --speak — ещё и озвучить)
Конфиг — config.json: ptt_enabled, ptt_key (клавиатура), ptt_key2
                      (кнопка мыши: x / x2), ptt_speak, ptt_toast_sec,
                      piper_exe, piper_voice. Меняется голосом через
                      Джарвиса («рация на f9») — конфиг подхватывается на лету.
Зависимости: pip install keyboard mouse sounddevice (tkinter/winsound — штатные).
"""
import json, os, sys, time, io, wave, queue, subprocess, threading
import urllib.request
import ctypes

try:  # v3.3.0: свои пиксели для плашек (4K@200% без виртуализации)
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
CFGF = os.path.join(BASE, "config.json")
LOGF = os.path.join(BASE, "ptt.log")
DATA = os.path.join(BASE, "data")
CHAT_URL = "http://127.0.0.1:8123"
SR = 16000  # частота записи для whisper

with open(CFGF, encoding="utf-8-sig") as f:  # utf-8-sig: терпим BOM от PowerShell
    CFG = json.load(f)

PTT_KEY = CFG.get("ptt_key", "caps lock")
PTT_KEY2 = CFG.get("ptt_key2", "x2")  # v3.4.0: боковая кнопка мыши
PTT_SPEAK = bool(CFG.get("ptt_speak", True))
PTT_TOAST_SEC = int(CFG.get("ptt_toast_sec", 15))
PIPER_EXE = CFG.get("piper_exe", r"D:\Jarvis\piper\piper.exe")
PIPER_VOICE = CFG.get("piper_voice",
                      r"D:\Jarvis\piper\voices\ru_RU-irina-medium.onnx")

# v3.4.0: пакет mouse может отсутствовать — рация тогда только с клавиатуры
try:
    import mouse as _mouse
    MOUSE_OK = True
except Exception:
    _mouse = None
    MOUSE_OK = False


def log(msg):
    try:
        with open(LOGF, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (time.strftime("%d.%m %H:%M:%S"), msg))
    except Exception:
        pass


def _trim_log(max_bytes=200000):
    """ptt.log не растёт бесконечно (голос — потоковая история)."""
    try:
        if os.path.exists(LOGF) and os.path.getsize(LOGF) > max_bytes:
            with open(LOGF, encoding="utf-8") as f:
                txt = f.read()
            with open(LOGF, "w", encoding="utf-8") as f:
                f.write(txt[-max_bytes // 2:])
    except Exception:
        pass


# ---------------------------------------------------------------- микрофон

class Recorder:
    """Захват микрофона (sounddevice): старт на нажатие, стоп на отпускание."""

    def __init__(self):
        self._frames = []
        self._stream = None

    def start(self):
        import sounddevice as sd
        self._frames = []
        self._stream = sd.RawInputStream(
            samplerate=SR, channels=1, dtype="int16",
            callback=lambda ind, fr, t, st: self._frames.append(bytes(ind)))
        self._stream.start()

    def stop(self):
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
        self._stream = None
        pcm = b"".join(self._frames)
        self._frames = []
        return pcm

    @staticmethod
    def pcm_to_wav(pcm):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm)
        return buf.getvalue()


# ---------------------------------------------------------------- API чата

def asr_wav(wav_bytes, timeout=300):
    """wav (16k mono) -> текст: whisper через /api/asr локального чата."""
    req = urllib.request.Request(CHAT_URL + "/api/asr", data=wav_bytes,
                                 headers={"Content-Type": "audio/wav"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.loads(r.read().decode("utf-8"))
    if not j.get("ok"):
        raise RuntimeError("ASR: " + str(j.get("error", j))[:200])
    return (j.get("text") or "").strip()


def ask_brain(text, on_event=None, timeout=600):
    """Вопрос мозгу через /api/chat (стрим ndjson).
    on_event(kind, text) получает живые события: tok/say/tool.
    Возвращает финальный текст ответа."""
    body = json.dumps({"message": text, "sender": "ptt"}).encode("utf-8")
    req = urllib.request.Request(CHAT_URL + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    final = ""
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for raw in r:
            try:
                j = json.loads(raw.decode("utf-8"))
            except Exception:
                continue
            t = j.get("type", "")
            if t == "tok" and on_event:
                on_event("tok", j.get("text", ""))
            elif t in ("say", "tool") and on_event:
                on_event(t, j.get("text") or j.get("name") or "")
            elif t == "done":
                final = j.get("text", "")
            elif t == "error":
                raise RuntimeError("мозг: " + str(j.get("text"))[:200])
    if not final.strip():
        raise RuntimeError("мозг вернул пустой ответ")
    return final


def speak(text):
    """Озвучить ответ голосом Ирины (piper, локально, без сети)."""
    if not PTT_SPEAK:
        return False
    if not (os.path.isfile(PIPER_EXE) and os.path.isfile(PIPER_VOICE)):
        log("piper не найден: %s | %s" % (PIPER_EXE, PIPER_VOICE))
        return False
    os.makedirs(DATA, exist_ok=True)
    out = os.path.join(DATA, "ptt_tts.wav")
    try:
        p = subprocess.run(
            [PIPER_EXE, "--model", PIPER_VOICE, "--output_file", out],
            input=text[:600].encode("utf-8"),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=180)
        if p.returncode != 0 or not os.path.isfile(out) or \
                os.path.getsize(out) < 200:
            log("piper код=%s" % p.returncode)
            return False
        import winsound
        winsound.PlaySound(out, winsound.SND_FILENAME)
        return True
    except Exception as e:
        log("speak ERR: %s" % e)
        return False


# ---------------------------------------------------------------- плашки

class UI:
    """Мини-плашки поверх всех окон: «● СЛУШАЮ», «думаю…», ответ."""

    def __init__(self):
        import tkinter as tk
        self.tk = tk
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("ДЖАРВИС-РАЦИЯ")
        self.q = queue.Queue()
        self.root.after(80, self._pump)
        self._rec = None
        self._toast = None

    def _pump(self):
        try:
            while True:
                self.q.get_nowait()()
        except queue.Empty:
            pass
        self.root.after(80, self._pump)

    def post(self, fn):
        self.q.put(fn)

    # --- красная точка записи
    def rec_show(self):
        self.rec_hide()
        tk = self.tk
        w = tk.Toplevel(self.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        try:
            w.attributes("-alpha", 0.92)
        except Exception:
            pass
        tk.Label(w, text="  ●  СЛУШАЮ…  ", bg="#8b0000", fg="white",
                 font=("Segoe UI", 12, "bold"), padx=6, pady=2).pack()
        w.update_idletasks()
        sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
        w.geometry("+%d+%d" % (sw // 2 - w.winfo_width() // 2, sh - 160))
        self._rec = w

    def rec_hide(self):
        if self._rec is not None:
            try:
                self._rec.destroy()
            except Exception:
                pass
            self._rec = None

    # --- плашка ответа
    def toast(self, text, ms=None, small=False):
        if ms is None:
            ms = PTT_TOAST_SEC * 1000
        self.toast_close()
        tk = self.tk
        w = tk.Toplevel(self.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        try:
            w.attributes("-alpha", 0.95)
        except Exception:
            pass
        bg, fg = ("#10131c", "#e8eaf0") if not small else ("#2a2a35", "#c9c9d4")
        lbl = tk.Label(w, text=text, bg=bg, fg=fg, justify="left", anchor="w",
                       wraplength=560, font=("Segoe UI", 11), padx=12, pady=8)
        lbl.pack()
        w.bind("<Button-1>", lambda e: w.destroy())
        w.update_idletasks()
        sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
        x = max(8, sw - w.winfo_width() - 24)
        y = max(8, sh - w.winfo_height() - 56)
        w.geometry("+%d+%d" % (x, y))
        w.after(ms, lambda: w.destroy())
        self._toast = w

    def toast_update(self, text):
        """Живое обновление текста плашки (стрим ответа)."""
        if self._toast is None:
            self.toast(text)
            return
        try:
            for ch in self._toast.winfo_children():
                ch.configure(text=text)
            self._toast.update_idletasks()
            sw, sh = self._toast.winfo_screenwidth(), \
                self._toast.winfo_screenheight()
            self._toast.geometry("+%d+%d" % (
                max(8, sw - self._toast.winfo_width() - 24),
                max(8, sh - self._toast.winfo_height() - 56)))
        except Exception:
            pass

    def toast_close(self):
        if self._toast is not None:
            try:
                self._toast.destroy()
            except Exception:
                pass
            self._toast = None


# ---------------------------------------------------------------- конвейер

BUSY = threading.Lock()  # одна фраза за раз


def process_pcm(pcm, ui=None, do_speak=True):
    """pcm int16 -> wav -> whisper -> мозг -> плашка (+голос)."""
    dur = len(pcm) / float(SR * 2)
    if dur < 0.4:
        if ui:
            ui.post(lambda: ui.toast("🎤 Не расслышал — говори подольше", 3000,
                                     small=True))
        return None
    wav = Recorder.pcm_to_wav(pcm)
    t0 = time.time()
    try:
        text = asr_wav(wav)
    except Exception as e:
        log("asr ERR: %s" % e)
        if ui:
            ui.post(lambda: ui.toast("🎤 Распознавание не удалось: %s"
                                     % str(e)[:150], 6000, small=True))
        return None
    if not text:
        if ui:
            ui.post(lambda: ui.toast("🎤 Пустая фраза — не расслышал", 3000,
                                     small=True))
        return None
    log("голос [%.1f сек]: %s" % (dur, text))
    if ui:
        ui.post(lambda: ui.toast("🎙 «%s»\n\n⏳ думаю…" % text))
    acc = {"txt": ""}

    def on_event(kind, chunk):
        if kind == "tok":
            acc["txt"] += (chunk or "")
            if ui and acc["txt"].strip():
                cur = acc["txt"][-700:]
                ui.post(lambda: ui.toast_update("🎙 «%s»\n\n%s" % (text, cur)))

    try:
        final = ask_brain(text, on_event=on_event)
    except Exception as e:
        log("brain ERR: %s" % e)
        if ui:
            ui.post(lambda: ui.toast("⚠️ %s" % str(e)[:200], 8000, small=True))
        return None
    log("ответ [%.1f сек]: %s" % (time.time() - t0, final[:300]))
    if ui:
        ui.post(lambda: ui.toast("🎙 «%s»\n\n%s" % (text, final)))
    if do_speak:
        threading.Thread(target=speak, args=(final,), daemon=True).start()
    return final


# ---------------------------------------------------------------- main

def selftest(wav_path, do_speak=False):
    """Прогон всего конвейера на готовом wav (E2E без хоткея)."""
    with open(wav_path, "rb") as f:
        wav = f.read()
    print("wav: %d байт" % len(wav), flush=True)
    text = asr_wav(wav)
    print("ASR: «%s»" % text, flush=True)
    assert text.strip(), "пустая расшифровка"
    final = ask_brain(text)
    print("МОЗГ: «%s»" % final, flush=True)
    if do_speak:
        ok = speak(final)
        print("PIPER: %s" % ("проигран" if ok else "НЕ смог"), flush=True)
    print("SELFTEST OK", flush=True)


def main():
    _trim_log()
    if "--selftest" in sys.argv:
        i = sys.argv.index("--selftest")
        if len(sys.argv) <= i + 1:
            print("usage: ptt.py --selftest file.wav [--speak]")
            sys.exit(2)
        selftest(sys.argv[i + 1], "--speak" in sys.argv)
        return
    if not CFG.get("ptt_enabled", True):
        log("ptt выключен в конфиге (ptt_enabled=false) — выхожу")
        return

    import keyboard  # глобальный хоткей (устанавливается pip'ом)
    ui = UI()
    rec = Recorder()
    state = {"on": False}
    hooks = {"kb": [], "ms": []}

    def on_press(_e):
        if state["on"] or not BUSY.acquire(blocking=False):
            return
        state["on"] = True
        try:
            rec.start()
            ui.post(ui.rec_show)
        except Exception as ex:
            state["on"] = False
            BUSY.release()
            log("mic ERR: %s" % ex)
            ui.post(lambda: ui.toast("🎤 Микрофон недоступен: %s"
                                     % str(ex)[:120], 5000, small=True))

    def on_release(_e):
        if not state["on"]:
            return
        state["on"] = False
        ui.post(ui.rec_hide)
        pcm = rec.stop()

        def worker():
            try:
                process_pcm(pcm, ui)
            finally:
                BUSY.release()

        threading.Thread(target=worker, daemon=True).start()

    def unregister_all():
        # v3.4.0: перерегистрация хуков при смене клавиши на лету
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        if MOUSE_OK:
            try:
                _mouse.unhook_all()
            except Exception:
                pass
        hooks["kb"].clear()
        hooks["ms"].clear()

    def register_all():
        # v3.4.0: клавиша может быть и клавиатурной, и кнопкой мыши (x/x2)
        global PTT_KEY, PTT_KEY2
        keys = []
        if PTT_KEY in ("x", "x2"):
            if MOUSE_OK:
                keys.append(("ms", PTT_KEY))
            else:
                log("кнопка мыши «%s» недоступна: пакет mouse не установлен"
                    % PTT_KEY)
        else:
            keys.append(("kb", PTT_KEY))
        if PTT_KEY2 in ("x", "x2") and MOUSE_OK and PTT_KEY2 != PTT_KEY:
            keys.append(("ms", PTT_KEY2))
        for kind, k in keys:
            if kind == "kb":
                keyboard.on_press_key(k, on_press, suppress=True)
                keyboard.on_release_key(k, on_release, suppress=True)
                hooks["kb"].append(k)
            else:
                _mouse.on_button(on_press, buttons=[k], types=["down"])
                _mouse.on_button(on_release, buttons=[k], types=["up"])
                hooks["ms"].append(k)
        return keys

    def config_watcher():
        """v3.4.0: смена клавиши голосом («рация на f9») — без перезапуска:
        следим за config.json и перерегистрируем хуки на лету."""
        global PTT_KEY, PTT_KEY2, PTT_SPEAK, PTT_TOAST_SEC
        last_mtime = os.path.getmtime(CFGF)
        while True:
            time.sleep(3)
            try:
                m = os.path.getmtime(CFGF)
                if m == last_mtime:
                    continue
                last_mtime = m
                with open(CFGF, encoding="utf-8") as f:
                    cfg = json.load(f)
                if not cfg.get("ptt_enabled", True):
                    unregister_all()
                    log("ptt выключен в конфиге — хуки сняты")
                    continue
                nk = cfg.get("ptt_key", "caps lock")
                nk2 = cfg.get("ptt_key2", "")
                if nk != PTT_KEY or nk2 != PTT_KEY2:
                    PTT_KEY, PTT_KEY2 = nk, nk2
                    unregister_all()
                    keys = register_all()
                    log("конфиг перечитан: рация теперь на %s"
                        % " + ".join("%s(%s)" % (k, t) for t, k in keys))
                    ui.post(lambda: ui.toast(
                        "🎙 Рация теперь на: %s" %
                        " + ".join(k for _t, k in keys), 5000, small=True))
                PTT_SPEAK = bool(cfg.get("ptt_speak", True))
                PTT_TOAST_SEC = int(cfg.get("ptt_toast_sec", 15))
            except Exception as e:
                log("config-watcher ERR: %s" % e)

    keys = register_all()
    threading.Thread(target=config_watcher, daemon=True).start()
    log("=== РАЦИЯ на связи: держи %s и говори; отпускай — ответ "
        "плашкой%s ===" % (" + ".join(k for _t, k in keys),
                           " и голосом Ирины" if PTT_SPEAK else ""))
    log("конфиг: ключ=%s ключ2=%s speak=%s toast=%dc piper=%s mouse=%s"
        % (PTT_KEY, PTT_KEY2 or "-", PTT_SPEAK, PTT_TOAST_SEC,
           os.path.isfile(PIPER_EXE) and os.path.isfile(PIPER_VOICE),
           MOUSE_OK))
    ui.root.mainloop()


if __name__ == "__main__":
    main()
