#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phone_ctl.py — телефон Шефа (POCO X7 Pro) под управлением Джарвиса.
Task 178 (v3.29.0). Пути:
  1) WiFi/сеть (работает УЖЕ, без настроек на телефоне):
     - онлайн-статус и IP через роутер (router_api)
     - связка «Связь с телефоном» (Phone Link): связан с POCO с 09.11
  2) ADB (полное управление — включается на телефоне ОДИН раз):
     - беспроводной ADB: пара по USB ИЛИ «Беспроводная отладка» в меню
       разработчика (прямое соединение, без пары — adb connect ip:port)
     - экран телефона на ПК + управление (scrcpy, без экрана: --record)
     - фото/файлы с телефона (adb pull), заливка (adb push)
     - батаре/память/статус (dumpsys battery, df)
     - приложения: список/установка/удаление (pm list/install/uninstall)
     - автоматизация: тапы/свайпы/текст (input tap/swipe/text)
Состояние (переживает рестарт): data/phone_state.json — ip, порт adb.
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

# Телефон Шефа (роутер так его зовёт)
PHONE_NAME = "POCO"
DEFAULT_IP = "192.168.1.20"


def _state():
    try:
        with open(STATE_F, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"ip": DEFAULT_IP, "adb_port": 5555}


def _save_state(st):
    os.makedirs(os.path.dirname(STATE_F), exist_ok=True)
    with open(STATE_F, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


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


def _phone_online_router():
    """POCO онлайн в WiFi? IP через роутер (если модуль доступен)."""
    try:
        import router_api as R
        out = R.devices()
        for ln in out.splitlines():
            if PHONE_NAME.lower() in ln.lower():
                return True, ln.strip("• ").strip()
        return False, out
    except Exception as e:
        return None, "роутер не ответил: %s" % e


def _try_connect(ip=None, port=None):
    """adb connect по WiFi. Возвращает (ok, текст)."""
    st = _state()
    ip = ip or st.get("ip") or DEFAULT_IP
    port = port or st.get("adb_port") or 5555
    code, out = _adb("connect", "%s:%s" % (ip, port), timeout=12)
    ok = "connected" in out.lower() and "cannot" not in out.lower()
    if ok:
        st["ip"], st["adb_port"] = ip, port
        _save_state(st)
    return ok, out


def _mdns_services():
    """mDNS-сервисы «Беспроводной отладки» (Android 11+): телефон слушает
    СЛУЧАЙНЫЙ порт, который меняется при каждом включении отладки/ребуте
    WiFi — обычный connect по старому порту не сработает. adb mdns находит
    актуальный порт сам. Возвращает (connect-порты, pairing-порты)."""
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


def _one_device():
    devs = _connected()
    if not devs:
        return None
    # предпочитаем wifi-подключение телефона (ip:port)
    for d in devs:
        if ":" in d:
            return d
    return devs[0]


# ---------------------------------------------------------------- команды

def status():
    """Полный статус: сеть + adb + телефон."""
    parts = []
    on, info = _phone_online_router()
    if on is True:
        parts.append("📶 В WiFi: ДА — %s" % info)
    elif on is False:
        parts.append("📶 В WiFi: нет (из роутера не виден)")
        parts.append("   %s" % info if info else "")
    else:
        parts.append("📶 Роутер: %s" % info)
    devs = _connected()
    if devs:
        parts.append("🔌 ADB: подключён (%s)" % ", ".join(devs))
        d = _one_device()
        code, out = _adb("-s", d, "shell", "dumpsys battery", timeout=15)
        m = re.search(r"level:\s*(\d+)", out)
        if m:
            parts.append("🔋 Батарея: %s%%" % m.group(1))
        code, model = _adb("-s", d, "shell", "getprop", "ro.product.model",
                           timeout=10)
        if model and "error" not in model.lower():
            parts.append("📱 Модель: %s" % model)
    else:
        ok, out = _try_connect()
        if ok:
            return status()  # подключились — перечитали
        parts.append("🔌 ADB: не подключён (отладка на телефоне выключена?)")
        parts.append(_howto_enable())
    return "\n".join(parts)


def _howto_enable():
    return ("ℹ️ Полное управление телефоном — включи на нём отладку ОДИН раз:\n"
            "Настройки → О телефоне → 7 раз тапни «Версия HyperOS» → в "
            "«Параметры разработчика» включи «Отладка по USB» (и/или "
            "«Беспроводная отладка»). После этого скажи мне «телефон "
            "подключи» — я сам найду его по WiFi.")


def connect(what=""):
    """Подключиться к телефону: adb connect ip:port (или auto)."""
    # если USB-отладка включена и телефон воткнут — он уже в devices
    devs = _connected()
    if devs:
        return ("Уже подключён: %s" % ", ".join(devs))
    m = re.search(r"(\d+\.\d+\.\d+\.\d+):?(\d+)?", what or "")
    ip = m.group(1) if m else None
    port = m.group(2) if m and m.group(2) else None
    if ip is None:
        # IP с роутера; недоступен — берём сохранённый/дефолтный и всё
        # равно пробуем mDNS (он работает и без роутера)
        on, info = _phone_online_router()
        if on:
            m2 = re.search(r"(\d+\.\d+\.\d+\.\d+)", info or "")
            if m2:
                ip = m2.group(1)
    if ip is None:
        conn, pr = _mdns_services()
        if conn or pr:
            ip = (conn or pr)[0][0]  # mDNS сам знает адрес телефона
    if ip is None:
        ip = _state().get("ip") or DEFAULT_IP
    # ЖИВАЯ ОСОБЕННОСТЬ (Task 178b): mDNS-обнаружение у adb «просыпается»
    # не сразу после kill/disconnect; если ничего не нашли — restart
    # adb-сервера и ещё раз (живой тест: после disconnect mdns пуст,
    # после kill/start-server сервис появился мгновенно)
    conn, pr = _mdns_services()
    if not conn and not pr:
        _adb("kill-server", timeout=10)
        _adb("start-server", timeout=15)
        time.sleep(4)
        conn, pr = _mdns_services()
    # пробуем сохранённый порт, затем mDNS-поиск СЛУЧАЙНОГО порта
    # беспроводной отладки, затем стандартные
    st = _state()
    ports = [port] if port else [st.get("adb_port"), 5555, 5554, 5037]
    for p in ports:
        if not p:
            continue
        ok, out = _try_connect(ip, p)
        if ok:
            return ("✅ Подключился к телефону: %s:%s (%s)" % (ip, p, out))
    # порт беспроводной отладки случайный — mDNS-порты
    for cip, cport in conn:
        ok, out = _try_connect(cip, cport)
        if ok:
            return ("✅ Подключился к телефону по беспроводной отладке "
                    "(mDNS нашёл порт): %s:%s" % (cip, cport))
    if pr and not conn:
        return ("Вижу телефон в сети отладки, но он ещё НЕ СПАРЕН с ПК "
                "(mDNS показывает только pairing-порт %s). Спари один раз: "
                "на телефоне «Беспроводная отладка» → «Подключение устройства "
                "с помощью кода» — скажи мне код из 6 цифр и цифры IP:порт "
                "с экрана, я запомню НАВСЕГДА (пара переживает ребуты, "
                "меняться будет только порт — его я сам найду)."
                % ("%s:%s" % pr[0]))
    return ("Не подключился (%s:%s — отладка выключена или порт другой). %s"
            % (ip, ports, _howto_enable()))


def battery():
    d = _one_device()
    if not d:
        return _no_adb()
    code, out = _adb("-s", d, "shell", "dumpsys battery", timeout=15)
    m = re.search(r"level:\s*(\d+)", out)
    s = re.search(r"status:\s*(\d+)", out)
    chg = {2: "заряжается", 3: "не заряжается", 4: "полный", 5: "разряд"}.get(
        int(s.group(1)) if s else 0, "?")
    if m:
        return "🔋 Батарея: %s%% (%s)" % (m.group(1), chg)
    return "Не прочитал: %s" % out[:200]


def photos(count=5, days=3):
    """Свежие фото с телефона: adb pull из DCIM/Camera."""
    d = _one_device()
    if not d:
        return _no_adb()
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
    return ("📸 Скачал %d фото с телефона (самые свежие):\n%s"
            % (len(got), "\n".join(got)))


def push(src, dst=""):
    d = _one_device()
    if not d:
        return _no_adb()
    if not os.path.exists(src):
        return "Файла нет: %s" % src
    dst = dst or "/sdcard/Download/" + os.path.basename(src)
    code, out = _adb("-s", d, "push", src, dst, timeout=120)
    if code == 0:
        return "✅ Залил на телефон: %s" % dst
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


def apps(query=""):
    d = _one_device()
    if not d:
        return _no_adb()
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
    return "📱 Приложений: %d%s\n%s" % (
        len(pkgs), (" по «%s»" % query if query else ""),
        "\n".join(pkgs[:40]))


def tap(x, y):
    d = _one_device()
    if not d:
        return _no_adb()
    _adb("-s", d, "shell", "input", "tap", str(int(x)), str(int(y)))
    return "Тапнул (%s, %s)" % (x, y)


def swipe(x1, y1, x2, y2, ms=300):
    d = _one_device()
    if not d:
        return _no_adb()
    _adb("-s", d, "shell", "input", "swipe", str(int(x1)), str(int(y1)),
         str(int(x2)), str(int(y2)), str(int(ms)))
    return "Свайпнул"


def type_text(text):
    d = _one_device()
    if not d:
        return _no_adb()
    _adb("-s", d, "shell", "input", "text", text.replace(" ", "%s")[:300])
    return "Напечатал на телефоне: %s" % text[:60]


def key(k):
    """Кнопка: home/back/recents/power/volume_up/volume_down."""
    d = _one_device()
    if not d:
        return _no_adb()
    keys = {"home": "3", "back": "4", "recents": "187", "power": "26",
            "volume_up": "24", "volume_down": "25", "camera": "27"}
    kc = keys.get((k or "").lower())
    if not kc:
        return "Кнопка не понята: %s (есть %s)" % (k, ", ".join(keys))
    _adb("-s", d, "shell", "input", "keyevent", kc)
    return "Нажал %s" % k


def screenshot():
    """Скрин телефона -> файл; Джарвис смотрит его зрением и шлёт Шефу."""
    d = _one_device()
    if not d:
        return _no_adb()
    _adb("-s", d, "shell", "screencap -p /sdcard/_jarvis_shot.png", timeout=20)
    dst = os.path.join(BASE, "data", "phone_shot.png")
    code, out = _adb("-s", d, "pull", "/sdcard/_jarvis_shot.png", dst,
                     timeout=30)
    if code == 0 and os.path.exists(dst):
        return "SCREENSHOT_OK:%s" % dst
    return "Скрин не вышел: %s" % out[:150]


def mirror(record_seconds=0, window=True):
    """Зеркало экрана телефона на мониторе ПК2 (scrcpy)."""
    d = _one_device()
    if not d:
        return _no_adb()
    args = [SCRCPY, "-s", d]
    if record_seconds:
        args += ["--record", os.path.join(BASE, "data",
                                          "phone_rec.mp4"), "--no-playback"]
        try:
            subprocess.Popen(args, creationflags=0x08000000)
        except Exception as e:
            return "Запись не стартовала: %s" % e
        return ("🔴 Записываю экран телефона %d сек в D:\\Jarvis\\data\\"
                "phone_rec.mp4" % record_seconds)
    try:
        subprocess.Popen(args)  # окно на экране ПК2
        return ("🖥 Открыл зеркало телефона на экране ПК2 (scrcpy). Закрыть "
                "окно = прекратить.")
    except Exception as e:
        return "scrcpy не стартовал: %s" % e


def _no_adb():
    devs_before = _connected()
    if not devs_before:
        ok, out = _try_connect()
        if ok:
            return None  # подключились; вызывающий повторит
    return ("Телефон не подключён по ADB. %s" % _howto_enable())


def pair(code, host=""):
    """Спарить ПК с телефоном ОДИН РАЗ (adb pair ip:port code).
    Код из 6 цифр и ip:порт Шеф видит на телефоне: «Беспроводная
    отладка» → «Подключение устройства с помощью кода». Пара сохраняется
    НАВСЕГДА (переживает ребуты и смену порта) — пароль больше не нужен."""
    m = re.search(r"(\d+\.\d+\.\d+\.\d+):(\d+)", host or "")
    if not m or not re.fullmatch(r"\d{6}", (code or "").strip()):
        # может, в host лежит всё вместе: «спарить 123456 192.168.1.20:37851»
        m2 = re.search(r"(\d+\.\d+\.\d+\.\d+):(\d+)", (code or "") + " " + (host or ""))
        if m2 and re.search(r"\b\d{6}\b", (code or "") + " " + (host or "")):
            code = re.search(r"\b(\d{6})\b", code + " " + host).group(1)
            m = m2
        else:
            return ("Спарка: нужны код из 6 цифр и адрес с экрана телефона. "
                    "На телефоне: Настройки → Дополнительно → Параметры "
                    "разработчика → Беспроводная отладка → «Подключение "
                    "устройства с помощью кода». Продиктуй мне, например: "
                    "«телефон спарить 482913 192.168.1.20:37851»")
    ip, port = m.group(1), m.group(2)
    code, out = _adb("pair", "%s:%s" % (ip, port), code.strip(), timeout=20)
    if code == 0 and ("success" in out.lower() or "paired" in out.lower()):
        # спарились — сразу пробуем подключиться (порт подключения другой,
        # обычно соседний; найдём mDNS или перебором рядом с pairing-портом)
        st = _state()
        st["ip"] = ip
        st["paired"] = True
        _save_state(st)
        ok_msg = ("✅ Спарил ПК с телефоном НАВСЕГДА (adb pair %s:%s). "
                  "Пара сохранена — пароль/код больше не понадобятся. "
                  % (ip, port))
        # пробуем mDNS и соседние порты для connect
        for cip, cport in _mdns_services()[0]:
            ok, out = _try_connect(cip, cport)
            if ok:
                return ok_msg + "Подключился сразу: %s:%s" % (cip, cport)
        base = int(port)
        for p in (base - 1, base + 1, base, 5555, base + 2, base - 2):
            ok, out = _try_connect(ip, p)
            if ok:
                return ok_msg + "Подключился сразу: %s:%s" % (ip, p)
        return ok_msg + ("Подключиться сразу не вышло — скажи «телефон "
                         "подключи», я найду актуальный порт (он меняется, "
                         "это нормально — я ищу его сам).")
    return ("Не спарился (%s). Проверь: код из 6 цифр и ip:порт должны "
            "быть с ЭКРАНА телефона прямо сейчас (код живёт ~минуту, "
            "меняется при каждом открытии). Повтори: «телефон спарить "
            "<код> <ip:порт>». Ответ adb: %s" % (ip, out[:150]))


def handle(what):
    """Единый вход для cmd_phone(what): строка -> строка."""
    q = (what or "").strip().lower()
    if not q or q.startswith("статус") or q.startswith("справка"):
        if q.startswith("справка"):
            return help_str()
        return status()
    if q.startswith("подключ"):
        return connect(q)
    if q.startswith("спар") or q.startswith("pair"):
        # «спарить 482913 192.168.1.20:37851» или «спарить 482913»
        rest = re.sub(r"^(спарить|спарка|pair)\s*", "", q).strip()
        nums = re.search(r"\b(\d{6})\b", rest)
        addr = re.search(r"(\d+\.\d+\.\d+\.\d+:\d+)", rest)
        if nums and addr:
            return pair(nums.group(1), addr.group(1))
        if nums:
            # адрес не дали — попробуем с роутера/mDNS pairing-порт
            _, pr = _mdns_services()
            if pr:
                return pair(nums.group(1), "%s:%s" % pr[0])
            on, info = _phone_online_router()
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", info or "")
            return ("Код понял (%s), но нужен ещё ip:порт с экрана телефона "
                    "(строка «IP-адрес и порт» над кодом). Скажи: «телефон "
                    "спарить %s <ip:порт>»" % (nums.group(1), nums.group(1)))
        return pair("", "")
    if "батаре" in q or "заряд" in q:
        # может быть без adb — тогда через роутер только онлайн
        d = _one_device()
        if not d:
            st = status()
            return st
        return battery()
    if q.startswith("фото") or "снимк" in q or "камер" in q and "скрин" not in q:
        m = re.search(r"(\d+)", q)
        return photos(int(m.group(1)) if m else 5)
    if q.startswith("скрин"):
        r = screenshot()
        return r
    if q.startswith("зеркал") or "экран на пк" in q:
        return mirror()
    if q.startswith("приложени"):
        m = re.search(r"приложени[а-яё]*\s+(.+)$", q)
        return apps(m.group(1).strip() if m else "")
    if q.startswith("тап") or q.startswith("клик"):
        m = re.search(r"(\d+)[^\d]+(\d+)", q)
        if m:
            return tap(m.group(1), m.group(2))
        return "Тап куда? Пример: «телефон тап 540 1200»"
    if q.startswith("свайп"):
        nums = re.findall(r"(\d+)", q)
        if len(nums) >= 4:
            return swipe(nums[0], nums[1], nums[2], nums[3])
        return "Свайп: «телефон свайп 540 1500 540 500»"
    if q.startswith("печа") or q.startswith("напиши") or q.startswith("текст"):
        m = re.search(r"(?:печать|написать|текст)\s+(.+)$", q)
        return type_text(m.group(1)) if m else "Что напечатать?"
    if q.startswith("кнопк") or q.startswith("нажми"):
        m = re.search(r"(?:кнопка|нажать)\s+([a-zа-я_]+)", q)
        return key(m.group(1)) if m else "Какую кнопку? home/back/recents/power/volume_up/volume_down"
    if q.startswith("зали") or q.startswith("закин") or q.startswith("push"):
        m = re.search(r"(?:залить|закинуть|push)\s+(.+)$", q)
        return push(m.group(1).strip()) if m else "Что залить? Дай путь."
    return ("Не понял: «%s». %s" % (what, help_str()))


def help_str():
    return ("📱 Телефон: «телефон статус» (сеть/adb/батарея), «телефон "
            "подключи» (сам найдёт порт по mDNS), «телефон спарить <6 цифр> "
            "<ip:порт>» (один раз, пара навсегда), «телефон фото 5» (скачать "
            "свежие), «телефон скрин», «телефон зеркало» (экран на ПК), "
            "«телефон приложения <поиск>», «телефон тап X Y» / «свайп X1 Y1 "
            "X2 Y2» / «печать текст» / «кнопка home|back|power», «телефон "
            "залить <путь>». Порт отладки на телефоне меняется — это "
            "нормально, я ищу актуальный сам.")
