# -*- coding: utf-8 -*-
"""remind_ctl.py — ядро напоминаний Джарвиса (Task 177, v3.28.0).
Хранится на ПК2 рядом с jarvis.py (D:\\Jarvis\\remind_ctl.py).

Формат хранения: D:\\Jarvis\\data\\reminders.json — список
{"id": int, "text": str, "due": epoch, "repeat": ""|"daily"|"weekly"|"monthly",
 "state": "active"|"done", "created": epoch}

Повторения считаем местным временем ПК2 (time.localtime), как весь Джарвис.
Часовые пояса не храним: ПК2 — единственные часы, Шеф рядом с ними живёт.

API для jarvis.py:
  add(text, due, repeat="") -> dict записи (с id)
  due_now(now=None)         -> [записи, чьё время наступило] (и двигает повторы)
  list_items(only_active=True) -> форматированная строка для Шефа
  cancel(ref)               -> снять по id или по тексту
  help_str()                -> справка
Мозг сам парсит «через 2 часа» / «каждое 15-е в 12:00» — LLM лучше
справляется с естественным языком, чем регулярки; модуль только хранит
и считает время.
"""
import json
import os
import re
import time

STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "data", "reminders.json")

REPEATS = {"": "однократно", "daily": "ежедневно",
           "weekly": "еженедельно", "monthly": "ежемесячно"}


def _load():
    try:
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(items):
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STORE)


def _next_due(due, repeat, now):
    """Следующее время срабатывания повторяющегося напоминания."""
    lt = time.localtime(due)
    if repeat == "daily":
        while due <= now:
            due += 86400
    elif repeat == "weekly":
        while due <= now:
            due += 7 * 86400
    elif repeat == "monthly":
        # по дню месяца; 31-е в коротком месяце не существует — mktime
        # молча съезжает на 1-3-е следующего (живой тест t177 поймал),
        # поэтому проверяем, что день в результате совпал, и идём дальше
        y, m, d = lt.tm_year, lt.tm_mon, lt.tm_mday
        while True:
            m += 1
            if m > 12:
                m, y = 1, y + 1
            try:
                cand = time.mktime((y, m, d, lt.tm_hour, lt.tm_min,
                                    0, 0, 0, -1))
            except Exception:
                continue
            if cand > now and time.localtime(cand).tm_mday == d:
                return cand
    return due


def add(text, due, repeat=""):
    if not str(text).strip():
        return {"error": "пустой текст напоминания"}
    if not isinstance(due, (int, float)) or due <= time.time() - 60:
        return {"error": "время должно быть в будущем (epoch)"}
    if repeat not in REPEATS:
        return {"error": "повтор: '' | daily | weekly | monthly"}
    items = _load()
    rid = max([it.get("id", 0) for it in items], default=0) + 1
    rec = {"id": rid, "text": str(text).strip()[:500], "due": float(due),
           "repeat": repeat, "state": "active",
           "created": time.time()}
    items.append(rec)
    _save(items)
    return rec


def due_now(now=None):
    """Зрелые напоминания; повторяющиеся НЕ закрываем, а двигаем вперёд.
    Возврат: (зрелые записи, повторяющиеся записи, которые подвинули)."""
    now = now if now is not None else time.time()
    items = _load()
    fired, moved = [], []
    for it in items:
        if it.get("state") != "active" or it.get("due", 0) > now:
            continue
        if it.get("repeat"):
            it["due"] = _next_due(it["due"], it["repeat"], now)
            moved.append(it)
        else:
            it["state"] = "done"
            fired.append(it)
    if fired or moved:
        _save(items)
    return fired, moved


def _fmt(rec, now=None):
    now = now if now is not None else time.time()
    left = rec["due"] - now
    when = time.strftime("%d.%m %H:%M", time.localtime(rec["due"]))
    if left > 0:
        if left < 3600:
            in_h = "через %d мин" % max(1, round(left / 60))
        elif left < 86400:
            in_h = "через %.1f ч" % (left / 3600)
        else:
            in_h = "через %d дн" % round(left / 86400)
    else:
        in_h = "ПРОСРОЧЕНО"
    rep = REPEATS.get(rec.get("repeat", ""), "")
    return "#%d %s (%s, %s)" % (rec.get("id", 0), rec["text"], when,
                                in_h + (", " + rep if rep and rep != "однократно" else ""))


def list_items(only_active=True):
    items = [it for it in _load()
             if (it.get("state") == "active" or not only_active)]
    if not items:
        return ("Напоминаний нет. Скажи «напомни через 30 минут …» — "
                "и я заведу первое.")
    items.sort(key=lambda r: r.get("due", 0))
    return "\n".join(_fmt(it) for it in items[:20])


def cancel(ref):
    """ref: id (int/str-цифра) или часть текста."""
    items = _load()
    ref = str(ref).strip().lstrip("#")
    hit = None
    if ref.isdigit():
        for it in items:
            if it.get("id") == int(ref) and it.get("state") == "active":
                hit = it
                break
    if hit is None:
        # ищем по вхождению текста (без учёта регистра)
        low = ref.lower()
        cands = [it for it in items if it.get("state") == "active"
                 and low and low in it.get("text", "").lower()]
        if len(cands) == 1:
            hit = cands[0]
        elif len(cands) > 1:
            return ("Нашёл несколько: "
                    + "; ".join("#%d %s" % (c.get("id", 0), c["text"][:40])
                                for c in cands[:5])
                    + " — уточни по номеру.")
    if hit is None:
        return "Не нашёл активное напоминание «%s». Список: напомни список" % ref
    hit["state"] = "done"
    _save(items)
    return "Снял: #%d %s" % (hit.get("id", 0), hit["text"])


def help_str():
    return ("⏰ Напоминания: «напомни через 20 мин / в 19:30 / завтра в 9:00 "
            "— <что>»; повтор: «каждый день в 8:00», «каждое 15-е в 12:00» "
            "(daily/weekly/monthly); «напомни список»; «сними напоминание "
            "<№ или часть текста>».")
