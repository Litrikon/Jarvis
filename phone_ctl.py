#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phone_ctl.py — телефоны семьи под управлением Джарвиса (v4, Task 179c).
Телефоны:
  - POCO X7 Pro (телефон Шефа, Task 178): спарен, adbkey навсегда
  - Realme 15 5G (телефон жены, Task 179c): беспроводная отладка включена
Пути управления (для каждого телефона):
  1) WiFi/сеть: онлайн-статус и IP через роутер (router_api)
  2) ADB (полное управление): беспроводная отладка (порт СЛУЧАЙНЫЙ,
     меняется — находим через mDNS), спарка кодом из 6 цифр один раз
Идентификация ЧЕЙ телефон: после connect читаем ro.product.brand/model
и сверяем с реестром — mDNS видит ОБА телефона, перепутать нельзя.
Состояние: data/phone_state.json — вложено по id телефона (миграция
со старого плоского формата Task 178 автоматически).
"""
import json
import os
import re
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(BASE, "platform-tools", "adb.exe")
SCRCPY = os.path.join(BASE, "scrcpy", "scrcpy.exe")
STATE_F = os.path.join(BASE, "data", "phone_state.json")

# ---------------- реестр телефонов семьи (Task 179c)
PHONES = {
    "poco": {
        "id": "poco",
        "label": "телефон Шефа (POCO X7 Pro)",
        "who": "Шефа",
        "router_names": ["poco"],           # как его зовёт роутер
        "brands": ["poco", "redmi", "xiaomi"],
        "models": ["2412dpc0ag", "rodin"],  # model / product
        "default_ip": "192.168.1.20",
    },
    "realme": {
        "id": "realme",
        "label": "телефон жены (Realme 15 5G)",
        "who": "жены",
        "router_names": ["realme", "rmx"],
        "brands": ["realme", "oppo", "oneplus"],
        "models": ["rmx"],                  # Realme модели все RMXxxxx
        "default_ip": None,                 # узнаем из роутера/mDNS
    },
}
DEFAULT_WHO = "poco"

_BRAND_CACHE = {}  # serial -> (brand, model); чистим при connect/pair


def _state(who=DEFAULT_WHO):
    """Состояние конкретного телефона (ip, adb_port, paired)."""
    try:
        with open(STATE_F, encoding="utf-8") as f:
            all_st = json.load(f)
    except Exception:
        all_st = {}
    # миграция со старого плоского формата Task 178 (только POCO)
    if "ip" in all_st and "poco" not in all_st:
        all_st = {"poco": all_st}
    if not isinstance(all_st.get(who), dict):
        all_st[who] = {}
    return all_st, all_st[who]


def _save_state(who, st):
    all_st, _ = _state(who)
    all_st[who] = st
    os.makedirs(os.path.dirname(STATE_F), exist_ok=True)
    with open(STATE_F, "w", encoding="utf-8") as f:
        json.dump(all_st, f, ensure_ascii=False, indent=1)


def _adb(*args, timeout=25):
    """adb-команда -> (код, вывод)."""
    try:
        p = subprocess.run([ADB] + list(args), capture_output=True,
                           timeout=timeout)
        out = (p.stdout or b"") + (p.stderr or b"")
        return p.returncode, out.decode("utf-8", "replace").strip()
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT"
    except Exception as e:
        return 1, str(e)


def _devices():
    code, out = _adb("devices")
    devs = []
    for ln in out.splitlines()[1:]:
        ln = ln.strip()
        if not ln or ln.startswith("*"):
            continue
        parts = ln.split()
        if len(parts) >= 2 and parts[1] == "device":
            devs.append(parts[0])
    return devs


def _connected():
    """Активные подключения adb (usb или ip:port)."""
    return _devices()


def _phone_cfg(who):
    return PHONES.get(who) or PHONES[DEFAULT_WHO]


def _device_id(serial):
    """(brand, model) подключённого устройства — с кэшем на вызов."""
    if serial in _BRAND_CACHE:
        return _BRAND_CACHE[serial]
    code, out = _adb("-s", serial, "shell", "getprop ro.product.brand",
                     timeout=10)
    brand = (out or "").splitlines()[0].strip().lower() if out else ""
    code, out = _adb("-s", serial, "shell", "getprop ro.product.model",
                     timeout=10)
    model = (out or "").splitlines()[0].strip().lower() if out else ""
    _BRAND_CACHE[serial] = (brand, model)
    return brand, model


def _device_is(serial, who):
    """Это тот самый телефон? Сверяем brand/model с реестром."""
    cfg = _phone_cfg(who)
    brand, model = _device_id(serial)
    hay = "%s %s" % (brand, model)
    return any(b in hay for b in cfg["brands"]) or \
        any(m in hay for m in cfg["models"])


def _phone_online_router(who=DEFAULT_WHO):
    """Телефон онлайн в WiFi? IP через роутер (если модуль доступен)."""
    cfg = _phone_cfg(who)
    try:
        import router_api as R
        out = R.devices()
        for ln in out.splitlines():
            if any(n in ln.lower() for n in cfg["router_names"]):
                return True, ln.strip("• ").strip()
        return False, out
    except Exception as e:
        return None, "роутер не ответил: %s" % e


def _router_ip(who):
    """IP телефона из роутера (или None)."""
    on, info = _phone_online_router(who)
    if on:
        m = re.search(r"(\d+\.\d+\.\d+\.\d+)", info or "")
        if m:
            return m.group(1)
    return None


def _try_connect(ip, port, who=DEFAULT_WHO):
    """adb connect ip:port. Возвращает (ok, текст, serial|None)."""
    code, out = _adb("connect", "%s:%s" % (ip, port), timeout=12)
    ok = "connected" in out.lower() and "cannot" not in out.lower() \
        and "failed" not in out.lower()
    if ok:
        st_all, st = _state(who)
        st["ip"], st["adb_port"] = ip, port
        _save_state(who, st)
        return True, out, "%s:%s" % (ip, port)
    return False, out, None


def _mdns_services():
    """mDNS-сервисы «Беспроводной отладки» (Android 11+): телефоны слушают
    СЛУЧАЙНЫЕ порты, меняющиеся при каждом включении отладки/ребуте WiFi.
    Возвращает (connect-порты, pairing-порты) — списки (ip, порт)."""
    code, out = _adb("mdns", "services", timeout=15)
    conn, pr = [], []
    for ln in (out or "").splitlines():
        m = re.search(r"(\d+\.\d+\.\d+\.\d+):(\d+)", ln)
        if not m:
            continue
        if "_adb-tls-connect" in ln:
            conn.append((m.group(1), int(m.group(2))))
        elif "_adb-tls-pairing" in ln:
            pr.append((m.group(1), int(m.group(2))))
    return conn, pr


def _one_device(who=DEFAULT_WHO):
    """Подключённый serial НУЖНОГО телефона (или None).
    ВСЕГДА сверяем brand/model с реестром: mDNS/роутер видят оба
    телефона, и по IP угадывать нельзя — только по железу."""
    for d in _connected():
        if _device_is(d, who):
            return d
    return None


def _shot_path(who):
    return os.path.join(BASE, "data", "phone_shot_%s.png" % who)


# ---------------------------------------------------------------- команды

def status(who=None):
    """Статус: одного телефона (who) или обоих сразу (who=None)."""
    if who is None:
        return "\n\n".join(status(w) for w in PHONES)
    cfg = _phone_cfg(who)
    parts = ["📱 %s:" % cfg["label"]]
    on, info = _phone_online_router(who)
    if on is True:
        parts.append("📶 В WiFi: ДА — %s" % info)
    elif on is False:
        parts.append("📶 В WiFi: нет (из роутера не виден)")
    else:
        parts.append("📶 Роутер: %s" % info)
    devs = _connected()
    mine = [d for d in devs if _device_is(d, who)]
    if mine:
        parts.append("🔌 ADB: подключён (%s)" % ", ".join(mine))
        d = mine[0]
        code, out = _adb("-s", d, "shell", "dumpsys battery", timeout=15)
        m = re.search(r"level:\s*(\d+)", out)
        if m:
            parts.append("🔋 Батарея: %s%%" % m.group(1))
        brand, model = _device_id(d)
        if model:
            parts.append("📱 Модель: %s" % model)
    else:
        parts.append("🔌 ADB: не подключён (скажи «телефон %s подключи»)"
                     % cfg["who"])
    return "\n".join(parts)


def _howto_enable(who=DEFAULT_WHO):
    cfg = _phone_cfg(who)
    return ("ℹ️ Полное управление телефоном %s — включи на нём отладку ОДИН "
            "раз:\nНастройки → О телефоне → 7 раз тапни «Версия …» → в "
            "«Параметры разработчика» включи «Беспроводную отладку». После "
            "этого скажи мне «телефон %s подключи» — я сам найду его по "
            "WiFi." % (cfg["who"], cfg["who"]))


def connect(what="", who=DEFAULT_WHO):
    """Подключиться к НУЖНОМУ телефону: adb connect (или auto через mDNS).
    mDNS видит ОБА телефона — после connect сверяем brand/model и чужие
    отключаем."""
    cfg = _phone_cfg(who)
    _BRAND_CACHE.clear()
    mine = _one_device(who)
    if mine:
        devs = _connected()
        return ("✅ %s уже подключён: %s%s" % (
            cfg["label"], mine,
            (" (ещё в сети: %s — чужие)" % ", ".join(d for d in devs
             if d != mine)) if len(devs) > 1 else ""))
    m = re.search(r"(\d+\.\d+\.\d+\.\d+):?(\d+)?", what or "")
    ip = m.group(1) if m else None
    port = m.group(2) if m and m.group(2) else None
    # кандидатные IP: роутер -> сохранённый -> дефолт
    ip = ip or _router_ip(who) or _state(who)[1].get("ip") \
        or cfg["default_ip"]
    # mDNS: если пусто — рестарт adb-сервера (Task 178b: после kill/disconnect
    # список «просыпается» только после рестарта)
    conn, pr = _mdns_services()
    if not conn and not pr:
        _adb("kill-server", timeout=10)
        _adb("start-server", timeout=15)
        time.sleep(4)
        conn, pr = _mdns_services()
    st = _state(who)[1]
    # 1) mDNS-порты (случайные, актуальные) — с проверкой ЧЕЙ телефон
    tried = set()
    for cip, cport in conn:
        tried.add((cip, cport))
        ok, out, serial = _try_connect(cip, cport, who)
        if ok:
            if _device_is(serial, who):
                return ("✅ Подключился к %s (mDNS нашёл порт): %s:%s"
                        % (cfg["label"], cip, cport))
            _adb("disconnect", serial, timeout=10)  # чужой — отключили
    # 2) сохранённый/стандартный порт на известном IP
    if ip:
        for p in ([port] if port else
                  [st.get("adb_port"), 5555, 5554, 5037]):
            if not p or (ip, p) in tried:
                continue
            ok, out, serial = _try_connect(ip, p, who)
            if ok:
                if _device_is(serial, who):
                    return ("✅ Подключился к %s: %s:%s" % (cfg["label"], ip, p))
                _adb("disconnect", serial, timeout=10)
    # 3) не спарен? mDNS pairing-порт нужного телефона (по IP из роутера)
    rip = _router_ip(who)
    pr_mine = [(pip, pport) for pip, pport in pr if pip == rip] if rip else []
    if pr_mine:
        return ("Вижу телефон %s в сети отладки, но он ещё НЕ СПАРЕН с ПК "
                "(mDNS показывает его pairing-порт %s:%s). Спари один раз: "
                "на телефоне «Беспроводная отладка» → «Подключение устройства "
                "с помощью кода» — скажи мне код из 6 цифр и цифры IP:порт "
                "с экрана, например «телефон %s спарить 482913 %s:%s». Пара "
                "сохранится НАВСЕГДА (переживает ребуты, меняется только "
                "порт — его я найду сам)."
                % (cfg["who"], pr_mine[0][0], pr_mine[0][1],
                   cfg["who"], pr_mine[0][0], pr_mine[0][1]))
    if pr:
        return ("Вижу в сети отладки чужой телефон (pairing-порт %s:%s — это "
                "не %s). Убедись, что на телефоне %s включена «Беспроводная "
                "отладка», и скажи «телефон %s подключи»."
                % (pr[0][0], pr[0][1], cfg["label"], cfg["who"], cfg["who"]))
    return ("Не нашёл %s (ни в роутере, ни в mDNS). Телефон дома, в WiFi и "
            "на зарядке? На нём включена «Беспроводная отладка»? Тогда: %s"
            % (cfg["label"], _howto_enable(who)))


def battery(who=DEFAULT_WHO):
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    code, out = _adb("-s", d, "shell", "dumpsys battery", timeout=15)
    m = re.search(r"level:\s*(\d+)", out)
    s = re.search(r"status:\s*(\d+)", out)
    chg = {2: "заряжается", 3: "не заряжается", 4: "полный", 5: "разряд"}.get(
        int(s.group(1)) if s else 0, "?")
    if m:
        return "🔋 Батарея: %s%% (%s)" % (m.group(1), chg)
    return "Не прочитал: %s" % out[:200]


def photos(count=5, days=3, who=DEFAULT_WHO):
    """Свежие фото с телефона: adb pull из DCIM/Camera."""
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    code, out = _adb("-s", d, "shell",
                     "ls -t /sdcard/DCIM/Camera/ | head -%d" % int(count),
                     timeout=15)
    files = [f.strip() for f in out.splitlines() if f.strip().endswith(
        (".jpg", ".jpeg", ".png", ".mp4"))]
    if not files:
        return "В DCIM/Camera свежих фото не нашёл (пусто или нет доступа)."
    dst_dir = os.path.join(BASE, "data", "phone_pull")
    os.makedirs(dst_dir, exist_ok=True)
    got = []
    for f in files:
        code, out = _adb("-s", d, "pull",
                         "/sdcard/DCIM/Camera/%s" % f,
                         os.path.join(dst_dir, f), timeout=60)
        if code == 0:
            got.append(os.path.join(dst_dir, f))
    if not got:
        return "Скачивание не вышло: %s" % out[:200]
    return ("📸 Скачал %d фото с телефона (%s):\n%s"
            % (len(got), _phone_cfg(who)["who"], "\n".join(got)))


def push(src, dst="", who=DEFAULT_WHO):
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    if not os.path.exists(src):
        return "Файла нет: %s" % src
    dst = dst or "/sdcard/Download/" + os.path.basename(src)
    code, out = _adb("-s", d, "push", src, dst, timeout=120)
    if code == 0:
        return "✅ Залил на телефон %s: %s" % (_phone_cfg(who)["who"], dst)
    return "Не вышло: %s" % out[:200]


# известные имена: разговорное -> пакет (поиск по-русски)
APP_ALIASES = {
    "ютуб": "youtube", "вк": "vk", "ватсап": "whatsapp",
    "вацап": "whatsapp", "телега": "telegram", "телеграм": "telegram",
    "инстаграм": "instagram", "тикток": "tiktok", "тамблер": "tumblr",
    "одноклассники": "ok.", "яндекс": "yandex", "сбер": "sber",
    "хром": "chrome", "оперу": "opera", "mozilla": "firefox",
    "firefox": "firefox", "spotty": "spotify", "спотифай": "spotify",
    "музыка": "miui.player", "камера": "camera", "галерея": "gallery",
    "настройки": "settings", "калькулятор": "calcul", "календар": "calendar",
    "банк": "bank", "сбербанк": "sberbank", "тинькофф": "tinkoff",
    "алфабанк": "alfa", "дискорд": "discord", "твич": "twitch",
    "зум": "zoom", "такси": "taxi", "убер": "uber", "доставка": "delivery",
    "озон": "ozon", "вилдберриз": "wildberries", "маркет": "market",
}


def _translit(s):
    m = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
         'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k',
         'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
         'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c',
         'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
         'э': 'e', 'ю': 'yu', 'я': 'ya'}
    return ''.join(m.get(c, c) for c in s.lower())


def apps(query="", who=DEFAULT_WHO):
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    code, out = _adb("-s", d, "shell", "pm list packages", timeout=20)
    pkgs = sorted(l.replace("package:", "").strip()
                  for l in out.splitlines() if l.startswith("package:"))
    if query:
        q = query.lower().strip()
        # ищем по: точному вхождению, алиасу, транслиту
        needles = {q, _translit(q)}
        for k, v in APP_ALIASES.items():
            if k in q or q in k:
                needles.add(v)
        pkgs = [p for p in pkgs
                if any(n and n in p.lower() for n in needles)]
    if not pkgs:
        return "Приложений по запросу «%s» нет." % query
    return "📱 Приложений на телефоне %s: %d%s\n%s" % (
        _phone_cfg(who)["who"], len(pkgs),
        (" по «%s»" % query if query else ""), "\n".join(pkgs[:40]))


def tap(x, y, who=DEFAULT_WHO):
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    _adb("-s", d, "shell", "input", "tap", str(int(x)), str(int(y)))
    return "Тапнул (%s, %s)" % (x, y)


def swipe(x1, y1, x2, y2, ms=300, who=DEFAULT_WHO):
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    _adb("-s", d, "shell", "input", "swipe", str(int(x1)), str(int(y1)),
         str(int(x2)), str(int(y2)), str(int(ms)))
    return "Свайпнул"


def type_text(text, who=DEFAULT_WHO):
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    _adb("-s", d, "shell", "input", "text", text.replace(" ", "%s")[:300])
    return "Напечатал на телефоне %s: %s" % (_phone_cfg(who)["who"],
                                             text[:60])


def key(k, who=DEFAULT_WHO):
    """Кнопка: home/back/recents/power/volume_up/volume_down."""
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    keys = {"home": "3", "back": "4", "recents": "187", "power": "26",
            "volume_up": "24", "volume_down": "25", "camera": "27"}
    kc = keys.get((k or "").lower())
    if not kc:
        return "Кнопка не понята: %s (есть %s)" % (k, ", ".join(keys))
    _adb("-s", d, "shell", "input", "keyevent", kc)
    return "Нажал %s" % k


def screenshot(who=DEFAULT_WHO):
    """Скрин телефона -> файл; Джарвис смотрит его зрением и шлёт Шефу."""
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    _adb("-s", d, "shell", "screencap -p /sdcard/_jarvis_shot.png",
         timeout=20)
    dst = _shot_path(who)
    code, out = _adb("-s", d, "pull", "/sdcard/_jarvis_shot.png", dst,
                     timeout=30)
    if code == 0 and os.path.exists(dst):
        return "SCREENSHOT_OK:%s" % dst
    return "Скрин не вышел: %s" % out[:150]


def mirror(record_seconds=0, window=True, who=DEFAULT_WHO):
    """Зеркало экрана телефона на мониторе ПК2 (scrcpy)."""
    d = _one_device(who)
    if not d:
        return _no_adb(who)
    args = [SCRCPY, "-s", d]
    rec = os.path.join(BASE, "data", "phone_rec_%s.mp4" % who)
    if record_seconds:
        args += ["--record", rec, "--no-playback"]
        try:
            subprocess.Popen(args, creationflags=0x08000000)
        except Exception as e:
            return "Запись не стартовала: %s" % e
        return ("🔴 Записываю экран телефона %s в %s"
                % (_phone_cfg(who)["who"], rec))
    try:
        subprocess.Popen(args)  # окно на экране ПК2
        return ("🖥 Открыл зеркало телефона %s на экране ПК2 (scrcpy). "
                "Закрыть окно = прекратить." % _phone_cfg(who)["who"])
    except Exception as e:
        return "scrcpy не стартовал: %s" % e


def _no_adb(who=DEFAULT_WHO):
    mine = _one_device(who)
    if not mine:
        connect("", who)
        mine = _one_device(who)
        if mine:
            return None  # подключились; вызывающий повторит
    return ("Телефон %s не подключён по ADB. %s"
            % (_phone_cfg(who)["who"], _howto_enable(who)))


def pair(code, host="", who=DEFAULT_WHO):
    """Спарить ПК с телефоном ОДИН РАЗ (adb pair ip:port code).
    Код из 6 цифр и ip:порт Шеф видит на телефоне: «Беспроводная
    отладка» → «Подключение устройства с помощью кода». Пара сохраняется
    НАВСЕГДА (переживает ребуты и смену порта)."""
    cfg = _phone_cfg(who)
    m = re.search(r"(\d+\.\d+\.\d+\.\d+):(\d+)", host or "")
    if not m or not re.fullmatch(r"\d{6}", (code or "").strip()):
        m2 = re.search(r"(\d+\.\d+\.\d+\.\d+):(\d+)",
                       (code or "") + " " + (host or ""))
        if m2 and re.search(r"\b\d{6}\b", (code or "") + " " + (host or "")):
            code = re.search(r"\b(\d{6})\b",
                             code + " " + host).group(1)
            m = m2
        else:
            return ("Спарка телефона %s: нужны код из 6 цифр и адрес с "
                    "экрана телефона. На телефоне: Настройки → Дополнительно "
                    "→ Параметры разработчика → Беспроводная отладка → "
                    "«Подключение устройства с помощью кода». Продиктуй "
                    "мне, например: «телефон %s спарить 482913 "
                    "192.168.1.30:37851»" % (cfg["who"], cfg["who"]))
    ip, port = m.group(1), m.group(2)
    _BRAND_CACHE.clear()
    code, out = _adb("pair", "%s:%s" % (ip, port), code.strip(), timeout=20)
    low = out.lower()
    ok = ("success" in low or "paired" in low) and "already" not in low \
        and "failed" not in low and "error" not in low and code == 0
    if ok:
        st = _state(who)[1]
        st["ip"] = ip
        st["paired"] = True
        _save_state(who, st)
        ok_msg = ("✅ Спарил ПК с телефоном %s НАВСЕГДА (adb pair %s:%s). "
                  "Пара сохранена — пароль/код больше не понадобятся. "
                  % (cfg["who"], ip, port))
        # сразу пробуем подключиться: mDNS + соседние порты
        for cip, cport in _mdns_services()[0]:
            ok, out, serial = _try_connect(cip, cport, who)
            if ok and _device_is(serial, who):
                return ok_msg + "Подключился сразу: %s:%s" % (cip, cport)
            if ok:
                _adb("disconnect", serial, timeout=10)
        base = int(port)
        for p in (base - 1, base + 1, base, 5555, base + 2, base - 2):
            ok, out, serial = _try_connect(ip, p, who)
            if ok and _device_is(serial, who):
                return ok_msg + "Подключился сразу: %s:%s" % (ip, p)
            if ok:
                _adb("disconnect", serial, timeout=10)
        return ok_msg + ("Подключиться сразу не вышло — скажи «телефон %s "
                         "подключи», я найду актуальный порт (он меняется, "
                         "это нормально — я ищу его сам)." % cfg["who"])
    return ("Не спарился (%s). Проверь: код из 6 цифр и ip:порт должны "
            "быть с ЭКРАНА телефона %s прямо сейчас (код живёт ~минуту, "
            "меняется при каждом открытии). Повтори: «телефон %s спарить "
            "<код> <ip:порт>». Ответ adb: %s"
            % (ip, cfg["who"], cfg["who"], out[:150]))


# ---------------------------------------------------------------- разбор

def _pick_who(q):
    """Кто спрашивают: «жены/жена/жене» -> realme, «шефа/мой/poco» ->
    poco. Возвращает (who, строка без слов-маркеров и слова «телефон»)."""
    who = DEFAULT_WHO
    keep = []
    for w in q.split():
        lw = w.lower().strip(",.!?")
        if re.match(r"^жен[аыоиуе]в?\w*$", lw) or lw.startswith("супруг") \
                or "realme" in lw or "realmi" in lw:
            who = "realme"
        elif re.match(r"^шеф[аы]?м?$", lw) or lw == "мой" or lw == "моя" \
                or "poco" in lw:
            who = "poco"
        elif re.match(r"^телефон\w*$", lw):
            pass  # само слово «телефон» — не команда и не маркер
        else:
            keep.append(w)
    return who, " ".join(keep)


def handle(what):
    """Единый вход для cmd_phone(what): строка -> строка.
    «телефон статус» — оба телефона; «телефон жены скрин» — телефон жены."""
    raw = (what or "").strip()
    q = raw.lower()
    who, q = _pick_who(q)
    has_marker = any(w in raw.lower() for w in
                     ("жен", "супруг", "realme", "realmi", "шеф", "poco",
                      "мой", "моя"))
    if not q or q.startswith("статус"):
        # «телефон статус» — ОБА телефона; «телефон жены статус» — только жены
        return status(who if has_marker else None)
    if q.startswith("справка"):
        return help_str()
    if q.startswith("подключ"):
        return connect(q, who)
    if q.startswith("спар") or q.startswith("pair"):
        # «спарить 482913 192.168.1.30:37851» или «спарить 482913»
        rest = re.sub(r"^(спарить|спарка|pair)\s*", "", q).strip()
        nums = re.search(r"\b(\d{6})\b", rest)
        addr = re.search(r"(\d+\.\d+\.\d+\.\d+:\d+)", rest)
        if nums and addr:
            return pair(nums.group(1), addr.group(1), who)
        if nums:
            _, pr = _mdns_services()
            rip = _router_ip(who)
            pr_mine = [(pip, pport) for pip, pport in pr if pip == rip] \
                if rip else []
            if pr_mine:
                return pair(nums.group(1), "%s:%s" % pr_mine[0], who)
            return ("Код понял (%s), но нужен ещё ip:порт с экрана телефона "
                    "%s (строка «IP-адрес и порт» над кодом). Скажи: "
                    "«телефон %s спарить %s <ip:порт>»"
                    % (nums.group(1), _phone_cfg(who)["who"],
                       _phone_cfg(who)["who"], nums.group(1)))
        return pair("", "", who)
    if "батаре" in q or "заряд" in q:
        d = _one_device(who)
        if not d:
            _no_adb(who)  # попробовали подключиться
            d = _one_device(who)
            if not d:
                return status(who)
        return battery(who)
    if q.startswith("фото") or "снимк" in q or "камер" in q and "скрин" not in q:
        m = re.search(r"(\d+)", q)
        return photos(int(m.group(1)) if m else 5, who=who)
    if q.startswith("скрин"):
        d = _one_device(who)
        if not d:
            _no_adb(who)
            d = _one_device(who)
            if not d:
                return status(who)
        return screenshot(who)
    if q.startswith("зеркал") or "экран на пк" in q:
        return mirror(who=who)
    if q.startswith("приложени"):
        m = re.search(r"приложени[а-яё]*\s+(.+)$", q)
        return apps(m.group(1).strip() if m else "", who)
    if q.startswith("тап") or q.startswith("клик"):
        m = re.search(r"(\d+)[^\d]+(\d+)", q)
        if m:
            return tap(m.group(1), m.group(2), who)
        return "Тап куда? Пример: «телефон жены тап 540 1200»"
    if q.startswith("свайп"):
        nums = re.findall(r"(\d+)", q)
        if len(nums) >= 4:
            return swipe(nums[0], nums[1], nums[2], nums[3], who=who)
        return "Свайп: «телефон жены свайп 540 1500 540 500»"
    if q.startswith("печа") or q.startswith("напиши") or q.startswith("текст"):
        m = re.search(r"(?:печать|написать|текст)\s+(.+)$", q)
        return type_text(m.group(1), who=who) if m else "Что напечатать?"
    if q.startswith("кнопк") or q.startswith("нажми"):
        m = re.search(r"(?:кнопка|нажать)\s+([a-zа-я_]+)", q)
        return key(m.group(1), who=who) if m else \
            "Какую кнопку? home/back/recents/power/volume_up/volume_down"
    if q.startswith("зали") or q.startswith("закин") or q.startswith("push"):
        m = re.search(r"(?:залить|закинуть|push)\s+(.+)$", q)
        return push(m.group(1).strip(), who=who) if m else \
            "Что залить? Дай путь."
    return ("Не понял: «%s». %s" % (what, help_str()))


def help_str():
    return ("📱 Телефоны: Шефа (POCO) и жены (Realme). Слова «жены»/«Шефа» "
            "выбирают телефон: «телефон жены статус», «телефон статус» "
            "(оба). Дальше: «подключи» (сам найдёт порт по mDNS), «спарить "
            "<6 цифр> <ip:порт>» (один раз, пара навсегда), «фото 5» "
            "(скачать свежие), «скрин», «зеркало» (экран на ПК), "
            "«приложения <поиск>», «тап X Y» / «свайп X1 Y1 X2 Y2» / "
            "«печать текст» / «кнопка home|back|power», «залить <путь>». "
            "Порт отладки на телефонах меняется — это нормально, я ищу "
            "актуальный сам.")
