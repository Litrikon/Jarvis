#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
router_api.py — доступ Джарвиса к роутеру Шефа (Keenetic Racer, 192.168.1.1).

v3.6.0 (Task 103, 02.11.2026). Приказ Шефа: «это пароль от роутера,
Джарвису дай его». Пароль лежит в config.json (router_ip / router_user /
router_pass) — НЕ в коде и НЕ в публичном гите. Закон З1 цел: Джарвис
никогда не вводит и не называет пароль — авторизация происходит целиком
внутри этого модуля.

Протокол: NDW4 Interactive (KeeneticOS 5.x) — SCRAM-рукопожатие:
  GET  /auth                      -> 401, endpoint x-ndw4-interactive
  POST /auth {login, nonce}       -> соль/nonce/iter/memcost
  argon2id(пароль, соль)          -> client_key/server_key (HMAC-SHA3-512)
  POST /auth {login, nonce, proof}-> сигнатура сервера (проверяем = пароль)
  POST /auth {...signature-proof} -> сессия (cookie)
  GET  /rci/...                   -> REST API роутера (JSON)
Классический NDW2 (md5(login:realm:pass) + sha256(challenge)) на этой
прошивке НЕ работает — не пытаться.

Только ЧТЕНИЕ: статус / устройства / интернет. Перезагрузку роутера
намеренно не умеем: она оборвёт интернет всему дому, включая меня самого.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.request

_SESS = {"cookie": None, "ts": 0}
SESS_TTL = 25 * 60  # минут держим сессию, потом переподключаемся сами

CKL = b"NDW4 Interactive Client Key"
SKL = b"NDW4 Interactive Server Key"


def _cfg():
    """(ip, user, password) из config.json рядом с модулем (BOM-толерантно)."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(p, encoding="utf-8-sig") as f:
        c = json.load(f)
    return (c.get("router_ip", "192.168.1.1"),
            c.get("router_user", "admin"),
            c.get("router_pass", ""))


def _http(method, url, payload=None, cookie=None, timeout=10):
    req = urllib.request.Request(
        url, method=method,
        data=json.dumps(payload).encode() if payload is not None else None)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


def _cookie_of(hd, old=None):
    for raw in (hd.get_all("Set-Cookie") if hasattr(hd, "get_all") else []) or []:
        pair = raw.split(";", 1)[0].strip()
        if "=" in pair:
            return pair
    return old


def auth(force=False):
    """NDW4 SCRAM-рукопожатие -> cookie сессии (кэшируется на SESS_TTL)."""
    if _SESS["cookie"] and not force and time.time() - _SESS["ts"] < SESS_TTL:
        return _SESS["cookie"]
    ip, user, password = _cfg()
    if not password:
        raise RuntimeError("в config.json нет router_pass — доступ не выдан")
    base = "http://%s" % ip

    st, hd, _ = _http("GET", base + "/auth")
    if st == 0:
        raise RuntimeError("роутер %s не отвечает (выключен?)" % ip)
    if st != 401:
        raise RuntimeError("роутер ответил неожиданно (HTTP %s)" % st)
    ndw4 = None
    for w in (hd.get_all("WWW-Authenticate") or []):
        if w.strip().lower().startswith("x-ndw4-interactive"):
            m = re.search(r'endpoint="([^"]*)"', w)
            ndw4 = m.group(1) if m else "/auth"
            break
    if not ndw4:
        raise RuntimeError("роутер не предлагает NDW4 (прошивка сменилась?)")
    auth_url = base + ndw4
    cookie = _cookie_of(hd)
    c_nonce = base64.b64encode(secrets.token_bytes(16)).decode()

    # --- фаза 1: сервер выдаёт соль и параметры argon2 ---
    st1, h1, _ = _http("POST", auth_url, {"login": user, "nonce": c_nonce}, cookie)
    cookie = _cookie_of(h1, cookie)
    d1 = h1.get("X-NDM-Data")
    if not d1:
        raise RuntimeError("рукопожатие сорвалось (нет X-NDM-Data)")
    rep = json.loads(base64.b64decode(d1).decode())
    if rep.get("error") or rep.get("e"):
        raise RuntimeError("роутер отказал: %s" % (rep.get("error") or rep.get("e")))
    combined = rep["nonce"]
    if not combined.startswith(c_nonce):
        raise RuntimeError("nonce сервера неверен — рукопожатие битое")

    from argon2.low_level import hash_secret_raw, Type
    salted = hash_secret_raw(secret=password.encode(),
                             salt=base64.b64decode(rep["salt"]),
                             time_cost=int(rep["iter"]),
                             memory_cost=int(rep["memcost"]),
                             parallelism=1, hash_len=64, type=Type.ID, version=19)

    def H(key, msg):
        return hmac.new(key, msg, hashlib.sha3_512).digest()

    client_key = H(salted, CKL)
    server_key = H(salted, SKL)
    stored_key = hashlib.sha3_512(client_key).digest()
    msg = ("login1=%s,nonce1=%s;iter2=%s,memcost2=%s,nonce2=%s,salt2=%s;"
           "login3=%s,nonce3=%s"
           % (user, c_nonce, rep["iter"], rep["memcost"], combined,
              rep["salt"], user, combined))

    def proof(m):
        sig = H(stored_key, m.encode())
        return base64.b64encode(bytes(a ^ b for a, b in zip(client_key, sig))).decode()

    # --- фаза 2: доказательство + проверка сигнатуры сервера (= пароль) ---
    st2, h2, _ = _http("POST", auth_url,
                       {"login": user, "nonce": combined, "proof": proof(msg)},
                       cookie)
    cookie = _cookie_of(h2, cookie)
    d2 = h2.get("X-NDM-Data")
    if not d2:
        raise RuntimeError("фаза 2 без ответа")
    rep2 = json.loads(base64.b64decode(d2).decode())
    if rep2.get("error") or rep2.get("e"):
        raise RuntimeError("роутер отказал: %s" % (rep2.get("error") or rep2.get("e")))
    sig = rep2.get("signature")
    if not sig or not hmac.compare_digest(base64.b64decode(sig),
                                          H(server_key, msg.encode())):
        raise RuntimeError("пароль роутера не подходит (Шеф его сменил?)")

    # --- фаза 3: финальное доказательство — сессия открыта ---
    st3, h3, _ = _http("POST", auth_url,
                       {"login": user, "nonce": combined,
                        "signature-proof": proof(msg + ";signature4=" + sig)},
                       cookie)
    cookie = _cookie_of(h3, cookie)
    if st3 != 200:
        raise RuntimeError("сессия не открылась (HTTP %s)" % st3)
    _SESS["cookie"] = cookie
    _SESS["ts"] = time.time()
    return cookie


def rci(path):
    """GET /rci/... с живой сессией (при 401 перелогиниваемся один раз)."""
    ip, _, _ = _cfg()
    st, hd, body = _http("GET", "http://%s%s" % (ip, path), None, auth(), 12)
    if st == 401:
        st, hd, body = _http("GET", "http://%s%s" % (ip, path), None,
                             auth(force=True), 12)
    if st != 200:
        raise RuntimeError("RCI %s -> HTTP %s" % (path, st))
    return json.loads(body.decode("utf-8", "replace"))


def _hum(sec):
    sec = int(sec)
    d, sec = divmod(sec, 86400)
    h, sec = divmod(sec, 3600)
    m, _ = divmod(sec, 60)
    return ("%d дн %d ч" % (d, h)) if d else ("%d ч %d мин" % (h, m))


def status():
    """Сводка: прошивка, аптайм, нагрузка, память, соединения, устройства."""
    s = rci("/rci/show/system")
    L = ["📡 *Роутер %s*" % s.get("hostname", "?")]
    try:
        v = rci("/rci/show/version")
        rel = v.get("release") or v.get("firmware") or ""
        if rel:
            L.append("прошивка: %s" % rel)
    except Exception:
        pass
    if s.get("uptime"):
        L.append("без перезагрузки: " + _hum(s["uptime"]))
    if "cpuload" in s:
        L.append("нагрузка CPU: %s%%" % s["cpuload"])
    mem = str(s.get("memory", "")).split("/")
    if len(mem) == 2 and mem[0].isdigit() and mem[1].isdigit():
        L.append("память: %d из %d МБ" % (int(mem[0]) // 1024, int(mem[1]) // 1024))
    if "conntotal" in s:
        L.append("сетевых соединений: %s" % s["conntotal"])
    try:
        n = len(rci("/rci/show/ip/hotspot").get("host", []))
        L.append("устройств в сети: %d" % n)
    except Exception:
        pass
    return "\n".join(L)


def devices():
    """Кто сейчас в сети: WiFi + провод, имена и IP."""
    hs = rci("/rci/show/ip/hotspot").get("host", [])
    online, offline = [], []
    for h in hs:
        (online if (h.get("active") and h.get("ip", "0.0.0.0") != "0.0.0.0")
         else offline).append(h)
    if not online:
        return "В сети роутера сейчас никого нет (знакомых устройств: %d)." % len(offline)
    L = ["👥 *В сети роутера (%d):*" % len(online)]
    for h in online:
        nm = h.get("name") or h.get("hostname") or "?"
        ipa = h.get("ip", "?")
        ifc = (h.get("interface") or {}).get("name") \
            or (h.get("interface") or {}).get("id", "")
        via = " (через ретранслятор)" \
            if h.get("via") and h.get("via") != h.get("mac") else ""
        L.append("• %s — %s%s%s" % (nm, ipa, (" · " + ifc) if ifc else "", via))
    if offline:
        L.append("")
        L.append("Ещё %d знакомых не в сети: %s" % (len(offline), ", ".join(
            (h.get("name") or h.get("hostname") or "?") for h in offline)))
    return "\n".join(L)


def internet():
    """WAN-адрес, шлюз, туннели: как дом выходит в интернет."""
    L = ["🌐 *Интернет (WAN):*"]
    try:
        ints = rci("/rci/show/interface")
        for k, v in (ints.items() if isinstance(ints, dict) else []):
            if not (isinstance(v, dict) and v.get("defaultgw")):
                continue
            addr = str(v.get("address", "?"))
            grey = " — серый IP провайдера (CGNAT)" if addr.startswith("100.") else ""
            L.append("• %s «%s»: %s%s" % (k, v.get("interface-name", ""), addr, grey))
            if v.get("link") == "up" and v.get("uptime"):
                L.append("  линк поднят без обрывов: " + _hum(v["uptime"]))
    except Exception:
        pass
    try:
        for r in rci("/rci/show/ip/route"):
            if isinstance(r, dict) and r.get("destination") == "0.0.0.0/0":
                L.append("• шлюз провайдера: %s (%s)" % (r.get("gateway"),
                                                          r.get("interface")))
                break
    except Exception:
        pass
    try:
        ints = rci("/rci/show/interface")
        for k, v in (ints.items() if isinstance(ints, dict) else []):
            if isinstance(v, dict) and "Wireguard" in k:
                up = "поднят" if v.get("connected") == "yes" else str(v.get("connected", "?"))
                L.append("• туннель %s до Москвы: %s" % (k, up))
    except Exception:
        pass
    return "\n".join(L)


def wifi():
    """Wi-Fi радио: каналы, ширина полосы, сигнал и клиенты по диапазонам."""
    ints = rci("/rci/show/interface")
    hs = rci("/rci/show/ip/hotspot").get("host", [])
    L = ["📶 *Wi-Fi роутера:*"]
    n = 0
    for k, v in sorted(ints.items() if isinstance(ints, dict) else []):
        if not (k.startswith("WifiMaster") and isinstance(v, dict) and v.get("hwstate") == "on"):
            continue
        n += 1
        ch = v.get("channel", "?")
        band = "5 ГГц" if isinstance(ch, int) and ch > 14 else "2.4 ГГц"
        bw = v.get("bandwidth", "?")
        clients = [h for h in hs
                   if str(h.get("ap") or "").startswith(k) and h.get("active")]
        rssi = [h.get("rssi") for h in clients if isinstance(h.get("rssi"), int)]
        sig = ", сигнал от %d до %d dBm" % (min(rssi), max(rssi)) if rssi else ""
        L.append("• %s: канал %s, ширина %s МГц, клиентов: %d%s"
                 % (band, ch, bw, len(clients), sig))
    if not n:
        return "Wi-Fi радио не отвечает (модуль выключен?)"
    return "\n".join(L)
