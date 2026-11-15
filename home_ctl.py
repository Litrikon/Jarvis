# -*- coding: utf-8 -*-
"""home_ctl.py — умный дом (Task 176, v3.27.1).

Устройства Шефа (разведка 15.11.2026, изоляция Guest-сети СНЯТА):
  * Два ТВ, оба управляемы локально по Cast (протокол Chromecast,
    никакого Google Home API — приказ Шефа от 15.11: GH закрываем):
      - TCL Google TV   192.168.1.6  «TCL»
      - Grundig Android 192.168.1.4  «Grundig» (Chromecast built-in)
  * Умные устройства Tuya в Guest-сети 192.168.2.x — теперь ДОСТИЖИМЫ
    из Home (isolate-private снят на роутере, TCP 6668 открыт):
      - Свет в спальне 192.168.2.2, Тёплый пол 192.168.2.10,
        Пульт 192.168.2.9.
    Для управления не хватает local_key (выдаёт только облако Tuya/
    приложение): устройства на запросы с неверным ключом молчат.

Стиль — как router_api.py: функции без состояния, всё возвращает строку
для Шефа. Секретов не храним (tuya-ключи выдаёт Шеф через конфиг).
"""
import json
import os
import socket
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(_HERE, "home_config.json")

# --- ТВ (fallback-адреса, если конфига нет) --------------------------
TVS = {
    # ключ: (ip, имя для Шефа, friendly-имя Cast)
    "tcl": ("192.168.1.6", "TCL", "TCL Google TV"),
    "grundig": ("192.168.1.4", "Grundig", "Grundig Android UHD TV"),
}
TUYA_DEVICES = {
    # имя Шефа: [ip, id, key, версия] — заполнится после выдачи local_key
    # пример: "свет в спальне": ["192.168.2.2", "tuya-id", "local-key", "3.3"],
    "свет в спальне": ["192.168.2.2", "", "", "3.3"],
    "тёплый пол": ["192.168.2.10", "", "", "3.3"],
}


def _load_cfg():
    """домашний конфиг (если Шеф выдал tuya-ключи или сменил IP ТВ)"""
    try:
        with open(CFG, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


# ---------------------------------------------------------------- ТВ (Cast)
def _cast(which="tcl"):
    """подключение к ТВ по Cast (быстро, без mDNS-поиска — IP знаем)"""
    import uuid as _uuid
    import pychromecast
    from pychromecast.models import CastInfo, HostServiceInfo
    cfg = _load_cfg()
    host = cfg.get("tv_%s" % which, {}).get("ip", TVS[which][0])
    friendly, model = TVS[which][2], TVS[which][2]
    # честная проверка доступности без длинных таймаутов pychromecast
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.5)
    try:
        s.connect((host, 8009))
    except OSError:
        return None, host
    finally:
        s.close()
    info = CastInfo({HostServiceInfo(host, 8009)}, _uuid.uuid4(),
                    friendly, model, host, 8009, "cast", friendly)
    cast = pychromecast.Chromecast(info)
    cast.wait(5)
    return cast, host


def _pick_tv(q):
    """какой ТВ хочет Шеф: 'grundig'/'грундиг' → grundig, иначе tcl"""
    if "grundig" in q or "грундиг" in q:
        return "grundig"
    return "tcl"


def tv_status(which="tcl"):
    cast, host = _cast(which)
    nm = TVS[which][1]
    if cast is None:
        return ("📺 %s недоступен по сети (%s:8009). Выключен или спит — "
                "включи его пультом, потом повтори." % (nm, host))
    try:
        app = cast.status.app_id or "(нет приложения)"
        vol = int(round(cast.status.volume_level * 100))
        muted = cast.status.volume_muted
        named = {"CC1AD845": "YouTube", "233637DE": "Netflix (Tab)",
                 "0F5096E8": "Google TV", "E8C28D3C": "YouTube Music"}.get(app, app)
        # pychromecast 14: is_playing нет — берём медиа-статус, если он есть
        try:
            playing = cast.media_controller.status.player_state  # PLAYING/PAUSED/IDLE
            st = {"PLAYING": "▶️ играет", "PAUSED": "⏸ на паузе",
                  "BUFFERING": "⏳ буферизует"}.get(playing, "⏹ не играет")
        except Exception:
            st = "⏹ медиа-сессии нет"
        return ("📺 *%s TV* (%s)\n• приложение: %s\n• громкость: %d%%%s\n• состояние: %s"
                % (nm, host, named, vol, " (звук выкл)" if muted else "", st))
    finally:
        cast.disconnect()


def tv_volume(which="tcl", delta=0, absolute=None, mute=None):
    cast, host = _cast(which)
    nm = TVS[which][1]
    if cast is None:
        return "📺 %s недоступен (%s). Включи пультом и повтори." % (nm, host)
    try:
        cur = cast.status.volume_level
        if mute is not None:
            cast.set_volume_muted(bool(mute))
            return "🔇 Звук %s: %s." % (nm, "выключен" if mute else "включён")
        if absolute is not None:
            new = max(0, min(100, int(absolute))) / 100.0
        else:
            new = max(0.0, min(1.0, cur + int(delta) / 100.0))
        cast.set_volume(new)
        return "🔊 %s: громкость %d%% (было %d%%)." % (nm, round(new * 100), round(cur * 100))
    finally:
        cast.disconnect()


def tv_media(which="tcl", cmd=""):
    cast, host = _cast(which)
    nm = TVS[which][1]
    if cast is None:
        return "📺 %s недоступен (%s)." % (nm, host)
    try:
        # медиа-сессия есть? (pychromecast 14: смотрим player_state)
        try:
            pstate = cast.media_controller.status.player_state
        except Exception:
            pstate = None
        if not pstate or pstate == "IDLE":
            return "📺 На %s ничего не воспроизводится — управлять нечем." % nm
        m = {
            "пауза": lambda: cast.media_controller.pause(),
            "продолжить": lambda: cast.media_controller.play(),
            "play": lambda: cast.media_controller.play(),
            "стоп": lambda: cast.media_controller.stop(),
            "дальше": lambda: cast.media_controller.skip(),
            "назад": lambda: cast.media_controller.queue_prev(),
            "тише": lambda: cast.set_volume(max(0, cast.status.volume_level - 0.05)),
            "громче": lambda: cast.set_volume(min(1, cast.status.volume_level + 0.05)),
        }.get(cmd.strip().lower())
        if not m:
            return "Не понял команду ТВ: «%s». Есть: пауза/продолжить/стоп/дальше/назад/тише/громче." % cmd
        m()
        return "✅ %s: %s." % (nm, cmd)
    finally:
        cast.disconnect()


def tv_youtube(which="tcl", query=""):
    """поиск на YouTube через Cast-приложение (без Tube API-ключей)"""
    cast, host = _cast(which)
    nm = TVS[which][1]
    if cast is None:
        return "📺 %s недоступен (%s)." % (nm, host)
    try:
        cast.play_media(
            "https://www.youtube.com/results?search_query=%s"
            % query.replace(" ", "+"), "video/mp4")
        return "▶️ Открыл поиск YouTube на %s: «%s»." % (nm, query)
    except Exception as e:
        return "YouTube на %s не пошёл (%s). Скажи точнее или открой приложение на ТВ сам." % (nm, e)
    finally:
        cast.disconnect()


# ------------------------------------------------------------- Tuya-устройства
def tuya_scan():
    """скан обеих подсетей: кто живой (изоляция Guest снята 15.11)"""
    import concurrent.futures
    cfg = _load_cfg()
    nets = cfg.get("nets", ["192.168.2"])
    ports = (6668,)

    def probe(ip, port):
        s_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_.settimeout(0.5)
        try:
            s_.connect((ip, port)); return (ip, port)
        except OSError:
            return None
        finally:
            s_.close()

    names = {"192.168.2.2": "Свет в спальне", "192.168.2.9": "Пульт",
             "192.168.2.10": "Тёплый пол"}
    tasks = [("%s.%d" % (n, i), p) for n in nets for i in range(1, 255) for p in ports]
    hits = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=200) as ex:
        for r in ex.map(lambda t: probe(*t), tasks):
            if r:
                hits.append(r)
    if not hits:
        return ("🔍 В 192.168.2.x никто не отвечает на 6668. Устройства "
                "офлайн или роутер снова изолировал сети.")
    L = ["🔍 Tuya-устройства на связи (порт 6668):"]
    for ip, port in hits:
        L.append("• %s — %s" % (names.get(ip, "?"), ip))
    L.append("Для управления нужен local_key каждого (облако Tuya) — см. отчёт.")
    return "\n".join(L)


def tuya_control(name, action):
    """управление Tuya-устройством — только если есть local_key"""
    try:
        import tinytuya
    except ImportError:
        return ("🔧 Tuya-модуль не установлен на ПК2 (pip install tinytuya). "
                "Скажи инженеру — поставлю.")
    dev_cfg = _load_cfg().get("tuya", {}).get(name.lower()) or TUYA_DEVICES.get(name.lower())
    if not dev_cfg:
        return ("🔧 Устройство «%s» мне неизвестно." % name)
    ip, did, key, ver = dev_cfg
    if not (did and key):
        return ("🔧 %s: сеть открыта (я его вижу на %s), но для команды нужен "
                "local_key из облака Tuya — Шеф ещё не выдал. Пока могу "
                "только видеть его в сети." % (name, ip))
    try:
        d = tinytuya.OutletDevice(did, ip, key)
        d.set_version(float(ver))
        if action in ("вкл", "on", "включить"):
            d.turn_on()
            return "💡 %s: включил." % name
        if action in ("выкл", "off", "выключить"):
            d.turn_off()
            return "💡 %s: выключил." % name
        st = d.status()
        return "💡 %s: %s" % (name, json.dumps(st.get("dps", {}), ensure_ascii=False))
    except Exception as e:
        return "🔧 %s не ответил (%s)." % (name, str(e)[:80])


# ------------------------------------------------------------------ фасад
def handle(what):
    """единый вход для cmd_home(what) — строка → строка"""
    q = (what or "").strip().lower()
    if not q:
        return ("🏠 Умный дом: «дом статус» — что доступно; «дом тв громкость 20» / "
                "«дом грундиг пауза» / «дом свет спальня вкл» (Tuya — после local_key).")
    # --- ТВ ---
    if q.startswith("тв") or "телевизор" in q or "телевиз" in q:
        which = _pick_tv(q)
        rest = q.replace("тв", "", 1).replace("телевизор", "", 1).replace("телевиз", "", 1)
        rest = rest.replace("grundig", "").replace("грундиг", "").strip(" ,.")
        if not rest or rest.startswith("статус"):
            return tv_status(which)
        if "громкость" in rest or rest.startswith("звук"):
            num = None
            for tok in rest.replace("%", " ").split():
                if tok.lstrip("-").isdigit():
                    num = int(tok)
                    break
            if num is None:
                return "Скажи число: «дом тв громкость 20»."
            if "тише" in rest:
                return tv_volume(which, delta=-abs(num))
            if "громче" in rest:
                return tv_volume(which, delta=abs(num))
            return tv_volume(which, absolute=num)
        if "тише" in rest:
            return tv_volume(which, delta=-5)
        if "громче" in rest:
            return tv_volume(which, delta=5)
        if "без звука" in rest or "мут" in rest or "mute" in rest:
            return tv_volume(which, mute=True)
        if "со звуком" in rest or "размут" in rest:
            return tv_volume(which, mute=False)
        if "найди" in rest or "youtube" in rest or "ютуб" in rest:
            query = rest.replace("найди", "").replace("youtube", "").replace("ютуб", "").strip()
            return tv_youtube(which, query or "music")
        return tv_media(which, rest or "пауза")
    # --- Tuya-свет/пол ---
    if any(w in q for w in ("свет", "ламп", "пол", "розетк", "удлинител", "увлажнител")):
        if "пол" in q and "свет" not in q:
            name = "тёплый пол"
        elif "свет" in q or "ламп" in q:
            name = "свет в спальне"
        elif "удлинител" in q:
            name = "sonoff удлинитель"
        elif "увлажнител" in q:
            name = "увлажнитель"
        else:
            name = "свет в спальне"
        action = "вкл" if any(w in q for w in ("вкл", "включ", "зажг", "постав")) else (
            "выкл" if any(w in q for w in ("выкл", "выключ", "погас", "стоп")) else "статус")
        return tuya_control(name, action)
    if q.startswith("скан"):
        return tuya_scan()
    if q.startswith("статус") or q.startswith("что"):
        parts = [tv_status("tcl"), tv_status("grundig")]
        seen = []
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(_tcp_ok, ip): nm
                    for ip, nm in (("192.168.2.2", "Свет в спальне"),
                                   ("192.168.2.9", "Пульт"),
                                   ("192.168.2.10", "Тёплый пол"))}
            for f in concurrent.futures.as_completed(futs):
                if f.result():
                    seen.append(futs[f])
        if seen:
            parts.append("🔌 Умные устройства в сети (локальный доступ открыт): "
                         + ", ".join(seen) + ". Для команд нужен local_key.")
        else:
            parts.append("🔌 Умные устройства не отвечают (офлайн?).")
        return "\n\n".join(parts)
    return ("🏠 Не понял: «%s». Примеры: «дом статус», «дом тв громкость 20», "
            "«дом грундиг пауза», «дом свет спальня вкл»." % what)


def _tcp_ok(ip, port=6668, timeout=1.5):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        return True
    except OSError:
        return False
    finally:
        s.close()
