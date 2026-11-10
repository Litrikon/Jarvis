# -*- coding: utf-8 -*-
"""Установка Silero v5_6_ru для Джарвиса (v3.17.0, Task 138).

Запуск из папки с распакованными файлами:
    python install_silero.py             (Джарвис живёт в D:\\Jarvis)
    python install_silero.py E:\\Jarvis  (если папка другая)

Что делает:
  1) копирует новые файлы (старые — в бэкап *.bak-дата);
  2) ставит torch через pip (~200 МБ), если его нет, + numpy
     (без него torch не конвертирует тензор в wav);
  3) качает модель v5_6_ru.pt (141 МБ) в <Джарвис>\\silero\\;
  4) правит config.json: tts_engine=silero, silero_voice=ксения.

После установки перезапусти jarvis.py и chat_server.py
и скажи Джарвису «ответь голосом» — услышишь Ксению.
"""
import json, os, shutil, subprocess, sys, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
JD = sys.argv[1] if len(sys.argv) > 1 else "D:\\Jarvis"
MODEL_URL = "https://models.silero.ai/models/tts/ru/v5_6_ru.pt"
MIN_BYTES = 100 * 1024 * 1024   # ~141 МБ; меньше = битый файл


def say(msg):
    print(msg, flush=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    say("=== Установка Silero для Джарвиса (v3.17.0) ===")
    say("Папка Джарвиса: %s" % JD)
    if not os.path.isdir(JD):
        say("ОШИБКА: папка не найдена. Запусти так: "
            "python install_silero.py <путь к папке Джарвиса>")
        return 1
    cfgp = os.path.join(JD, "config.json")
    if not os.path.isfile(cfgp):
        say("ОШИБКА: в папке нет config.json — это не папка Джарвиса.")
        return 1

    stamp = time.strftime("%Y%m%d_%H%M%S")

    # ---- 1) файлы (старые не теряем — бэкапим) ----
    pairs = [("jarvis_v3170.py", "jarvis.py"),
             ("chat_server_v317.py", "chat_server.py"),
             ("chat_server_v317.py", os.path.join("chat", "chat_server.py")),
             ("index_v317.html", os.path.join("chat", "index.html"))]
    for src, dst in pairs:
        s = os.path.join(BASE, src)
        d = os.path.join(JD, dst)
        if not os.path.isfile(s):
            say("!! не найден %s — пропускаю (файлы могли уже скопировать)"
                % src)
            continue
        os.makedirs(os.path.dirname(d) or JD, exist_ok=True)
        if os.path.isfile(d):
            shutil.copy2(d, d + ".bak-" + stamp)
            say("бэкап: %s.bak-%s" % (dst, stamp))
        shutil.copy2(s, d)
        say("файл: %s -> %s" % (src, dst))

    # ---- 2) torch ----
    try:
        import torch  # noqa: F401
        say("torch уже установлен.")
    except Exception:
        say("ставлю torch (~200 МБ, несколько минут)...")
        for args in ([sys.executable, "-m", "pip", "install", "torch"],
                     [sys.executable, "-m", "pip", "install", "torch",
                      "--index-url",
                      "https://download.pytorch.org/whl/cpu"]):
            try:
                r = subprocess.run(args)
                if r.returncode == 0:
                    break
            except Exception as e:
                say("pip споткнулся: %s" % e)
        try:
            import torch  # noqa: F401
            say("torch установлен.")
        except Exception:
            say("ОШИБКА: torch не поставился — посмотри вывод pip выше "
                "и запусти установку ещё раз.")
            return 1

    # ---- 2б) numpy (torch без него не конвертирует тензор в wav —
    # живые грабли 10.11: «Numpy is not available») ----
    try:
        import numpy  # noqa: F401
        say("numpy уже установлен.")
    except Exception:
        say("ставлю numpy (~16 МБ)...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "numpy"])
            import numpy  # noqa: F401
            say("numpy установлен.")
        except Exception as e:
            say("ОШИБКА: numpy не поставился: %s — запусти ещё раз."
                % str(e)[:150])
            return 1

    # ---- 3) модель ----
    dst = os.path.join(JD, "silero", "v5_6_ru.pt")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not (os.path.isfile(dst) and os.path.getsize(dst) >= MIN_BYTES):
        say("качаю модель v5_6_ru (~141 МБ)...")
        tmp = dst + ".part"
        try:
            with urllib.request.urlopen(MODEL_URL, timeout=600) as r, \
                    open(tmp, "wb") as f:
                total = 0
                while True:
                    c = r.read(1 << 18)
                    if not c:
                        break
                    f.write(c)
                    total += len(c)
                    if total % (20 << 20) < (1 << 18):
                        say("  %d МБ..." % (total >> 20))
            if os.path.getsize(tmp) < MIN_BYTES:
                os.remove(tmp)
                say("ОШИБКА: файл модели подозрительно мал. Скачай вручную: "
                    "%s -> %s" % (MODEL_URL, dst))
                return 1
            os.replace(tmp, dst)
        except Exception as e:
            say("ОШИБКА скачивания: %s. Запусти ещё раз — докачает."
                % str(e)[:200])
            return 1
    say("модель на месте: %s" % dst)

    # ---- 4) config.json ----
    with open(cfgp, encoding="utf-8-sig") as f:
        cfg = json.load(f)
    if not isinstance(cfg, dict):
        say("ОШИБКА: config.json не похож на конфиг.")
        return 1
    cfg["tts_engine"] = "silero"
    cfg["silero_model"] = dst
    cfg["silero_voice"] = "ксения"
    with open(cfgp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    say("config.json обновлён: tts_engine=silero, голос=ксения.")

    say("")
    say("ГОТОВО. Теперь:")
    say("  1) перезапусти Джарвиса (jarvis.py и chat_server.py);")
    say("  2) скажи ему «ответь голосом» — услышишь Ксению;")
    say("  3) «голоса» — список, «голос евгений» — сменить основной.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
