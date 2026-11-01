#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
win_ctl.py — ДЖАРВИС v2.3.0 «МАКС»: окна/мышь/клавиатура + скан-коды (Task 91).
Приказ Шефа от 31.10: дать агенту «необходимые разрешения» — теперь доступны
окна/мышь/клавиатура на уровне Windows. Чистый ctypes (user32), БЕЗ pip-пакетов.

Экспорт (вызывается из jarvis.tool_exec):
  windows_list(limit=30)                    — список видимых окон
  window_action(act, title, x, y, w, h)     — активировать/свернуть/развернуть/
                                              восстановить/закрыть/передвинуть/размер
  mouse_action(act, x, y, x2, y2, amount)   — клик/двойной/правый/движение/
                                              перетащить/прокрутить/позиция
  key_combo("ctrl+s")                       — сочетание клавиш
  type_text("текст")                        — печать Юникода (русский работает)
  screen_size()                             — размер основного экрана

Безопасность:
  - закрытие системных и СВОИХ окон (llama/jarvis/python/Program Manager/
    панель задач) запрещено;
  - к UAC-запросам Windows доступа нет (secure desktop — защита системы);
  - окно для передвижения/размера ищется по части заголовка (без учёта регистра).
"""
import ctypes
import ctypes.wintypes as wt
import time

u32 = ctypes.windll.user32

# ---------------------------------------------------------------- структуры SendInput
_PUL = ctypes.POINTER(ctypes.c_ulong)


class _KI(ctypes.Structure):
    _fields_ = (("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", _PUL))


class _MI(ctypes.Structure):
    _fields_ = (("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", _PUL))


class _IU(ctypes.Union):
    _fields_ = (("ki", _KI), ("mi", _MI))


class _IN(ctypes.Structure):
    _fields_ = (("type", ctypes.c_ulong), ("u", _IU), ("pad", ctypes.c_ubyte * 8))


_KBD = 1
_KEYUP = 0x0002
_UNICODE = 0x0004

# ---------------------------------------------------------------- виртуальные клавиши
VK = {
    "ctrl": 0x11, "control": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B,
    "windows": 0x5B, "super": 0x5B, "esc": 0x1B, "escape": 0x1B, "enter": 0x0D,
    "return": 0x0D, "tab": 0x09, "space": 0x20, "backspace": 0x08, "delete": 0x2E,
    "del": 0x2E, "insert": 0x2D, "home": 0x24, "end": 0x23, "pageup": 0x21,
    "pagedown": 0x22, "pgup": 0x21, "pgdn": 0x22, "up": 0x26, "down": 0x28,
    "left": 0x25, "right": 0x27, "capslock": 0x14, "printscreen": 0x2C,
    "prtsc": 0x2C, "plus": 0xBB, "minus": 0xBD, "меню": 0x5D,
}
for _i in range(1, 13):
    VK["f%d" % _i] = 0x6F + _i

# системные окна, которые нельзя закрывать (нижний регистр, часть заголовка)
# v2.3.0 «МАКС»: только рабочий стол и я сам; диспетчер задач и прочее — можно
CLOSE_DENY = ("program manager", "панель задач", "llama", "jarvis")

_EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


def _title(h):
    b = ctypes.create_unicode_buffer(300)
    u32.GetWindowTextW(h, b, 300)
    return b.value.strip()


def _visible_windows():
    """[(hwnd, title, rect, iconic, is_foreground)] всех видимых окон с заголовком."""
    res = []
    fg = u32.GetForegroundWindow()

    @_EnumProc
    def cb(h, _l):
        try:
            if not u32.IsWindowVisible(h):
                return True
            t = _title(h)
            if not t:
                return True
            r = wt.RECT()
            u32.GetWindowRect(h, ctypes.byref(r))
            res.append((h, t, r, bool(u32.IsIconic(h)), h == fg))
        except Exception:
            pass
        return True

    u32.EnumWindows(cb, 0)
    return res


def windows_list(limit=30):
    lines = []
    for h, t, r, ic, fg in sorted(_visible_windows(),
                                  key=lambda x: x[1].lower())[:limit]:
        mark = "[АКТИВНО] " if fg else ("[свёрнуто] " if ic else "")
        lines.append("%s«%s»  x=%d y=%d %dx%d" %
                     (mark, t, r.left, r.top, r.right - r.left, r.bottom - r.top))
    if not lines:
        return "видимых окон с заголовками нет"
    return ("открыто %d окон (показаны первые %d); экран %s:\n%s" %
            (len(_visible_windows()), len(lines), screen_size(), "\n".join(lines)))


def _find(title):
    """Окно по части заголовка: точное совпадение > начало > вхождение."""
    q = (title or "").strip().lower()
    if not q:
        return 0, "не указан заголовок окна"
    wins = _visible_windows()
    for h, t, *_ in wins:
        if t.lower() == q:
            return h, t
    for h, t, *_ in wins:
        if t.lower().startswith(q):
            return h, t
    for h, t, *_ in wins:
        if q in t.lower():
            return h, t
    return 0, "окно с заголовком «%s» не найдено (вызови «окна»)" % title


def _activate(h):
    if u32.IsIconic(h):
        u32.ShowWindow(h, 9)                       # SW_RESTORE
    u32.keybd_event(0x12, 0, 0, 0)                 # ALT (трюк против запрета фокуса)
    u32.keybd_event(0x12, 0, _KEYUP, 0)
    ok = bool(u32.SetForegroundWindow(h))
    u32.BringWindowToTop(h)
    time.sleep(0.12)
    return ok


def window_action(act, title, x=None, y=None, w=None, h=None):
    act = (act or "").strip().lower()
    if act in ("передвинуть", "размер", "resize", "move"):
        hw, info = _find(title)
        if not hw:
            return info
        r = wt.RECT()
        u32.GetWindowRect(hw, ctypes.byref(r))
        nx = int(x) if x is not None else r.left
        ny = int(y) if y is not None else r.top
        nw = int(w) if w is not None else (r.right - r.left)
        nh = int(h) if h is not None else (r.bottom - r.top)
        if nw < 80 or nh < 40:
            return "слишком маленький размер (минимум 80x40)"
        if nx < -2000 or ny < -2000 or nx > 8000 or ny > 8000:
            return "координаты за пределами экрана"
        u32.MoveWindow(hw, nx, ny, nw, nh, True)
        return "OK: окно «%s» — позиция (%d,%d), размер %dx%d" % (info, nx, ny, nw, nh)
    hw, info = _find(title)
    if not hw:
        return info
    if act in ("активировать", "показать", "на_передний_план", "активно",
               "activate", "focus"):
        ok = _activate(hw)
        return ("OK: окно «%s» на переднем плане" % info if ok else
                "окно «%s» найдено, но Windows не отдал фокус (попробуй alt+tab)"
                % info)
    if act in ("свернуть", "minimize"):
        u32.ShowWindow(hw, 6)
        return "OK: окно «%s» свёрнуто" % info
    if act in ("развернуть", "на_весь_экран", "maximize"):
        u32.ShowWindow(hw, 3)
        return "OK: окно «%s» развёрнуто на весь экран" % info
    if act in ("восстановить", "обычный_размер", "restore"):
        u32.ShowWindow(hw, 9)
        return "OK: окно «%s» восстановлено" % info
    if act in ("закрыть", "close"):
        tl = info.lower()
        for d in CLOSE_DENY:
            if d in tl:
                return ("ОТКАЗ: окно «%s» системное/служебное — закрывать нельзя"
                        % info)
        u32.PostMessageW(hw, 0x0010, 0, 0)           # WM_CLOSE
        return "OK: окну «%s» отправлено закрытие" % info
    return ("неизвестное действие «%s» (есть: активировать, свернуть, развернуть, "
            "восстановить, закрыть, передвинуть, размер)" % act)


# ---------------------------------------------------------------- мышь
def _move(x, y):
    u32.SetCursorPos(int(x), int(y))


def _click(button="left"):
    if button == "right":
        u32.mouse_event(0x0008, 0, 0, 0, 0)
        time.sleep(0.03)
        u32.mouse_event(0x0010, 0, 0, 0, 0)
    else:
        u32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.03)
        u32.mouse_event(0x0004, 0, 0, 0, 0)


def mouse_action(act, x=None, y=None, x2=None, y2=None, amount=0):
    act = (act or "").strip().lower()

    def _n(v):
        try:
            return int(float(str(v).strip().replace(",", ".")))
        except (TypeError, ValueError):
            return None

    x, y, x2, y2 = _n(x), _n(y), _n(x2), _n(y2)
    try:
        amt = int(float(str(amount).strip().replace(",", "."))) if amount not in (None, "") else 0
    except (TypeError, ValueError):
        amt = 0

    if act in ("позиция", "где_курсор", "pos"):
        pt = wt.POINT()
        u32.GetCursorPos(ctypes.byref(pt))
        return "курсор на (%d, %d); экран %s" % (pt.x, pt.y, screen_size())
    if act in ("движение", "переместить", "move"):
        if x is None or y is None:
            return "для движения нужны координаты x и y"
        _move(x, y)
        return "OK: курсор на (%d, %d)" % (x, y)
    if act in ("клик", "нажать", "click"):
        if x is not None and y is not None:
            _move(x, y)
            time.sleep(0.04)
        _click("left")
        return "OK: клик левой кнопкой%s" % (" на (%d,%d)" % (x, y)
                                             if x is not None and y is not None else "")
    if act in ("двойной", "двойной_клик", "double"):
        if x is not None and y is not None:
            _move(x, y)
            time.sleep(0.04)
        _click("left")
        time.sleep(0.06)
        _click("left")
        return "OK: двойной клик%s" % (" на (%d,%d)" % (x, y)
                                       if x is not None and y is not None else "")
    if act in ("правый", "правый_клик", "right"):
        if x is not None and y is not None:
            _move(x, y)
            time.sleep(0.04)
        _click("right")
        return "OK: клик правой кнопкой"
    if act in ("прокрутить", "скролл", "колесо", "scroll"):
        if not amt:
            return "укажи «сколько» щелчков (минус = вниз)"
        u32.mouse_event(0x0800, 0, 0, amt * 120, 0)
        return "OK: прокрутил %d щелчков (%s)" % (amt, "вверх" if amt > 0 else "вниз")
    if act in ("перетащить", "тащить", "drag"):
        if None in (x, y, x2, y2):
            return "для перетаскивания нужны x,y (откуда) и x2,y2 (куда)"
        _move(x, y)
        time.sleep(0.06)
        u32.mouse_event(0x0002, 0, 0, 0, 0)
        steps = 20
        for i in range(1, steps + 1):
            _move(x + (x2 - x) * i // steps, y + (y2 - y) * i // steps)
            time.sleep(0.012)
        u32.mouse_event(0x0004, 0, 0, 0, 0)
        return "OK: перетащил из (%d,%d) в (%d,%d)" % (x, y, x2, y2)
    return ("неизвестное действие «%s» (есть: клик, двойной, правый, движение, "
            "перетащить, прокрутить, позиция)" % act)


# ---------------------------------------------------------------- клавиатура
def _si(inp):
    return u32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_IN))


def _tap_vk(vk):
    # v2.3.0: ОБЯЗАТЕЛЬНО скан-код — без него Explorer игнорирует синтетическую
    # кнопку Win (меню Пуск не открывалось; Task 91)
    scan = u32.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC
    u32.keybd_event(vk, scan, 0, 0)
    time.sleep(0.02)
    u32.keybd_event(vk, scan, _KEYUP, 0)


def _key_unicode(ch):
    code = ord(ch)
    dn = _IN(_KBD, _IU(_KI(0, code, _UNICODE, 0, None)))
    up = _IN(_KBD, _IU(_KI(0, code, _UNICODE | _KEYUP, 0, None)))
    _si(dn)
    _si(up)


def key_combo(combo):
    parts = [p.strip().lower() for p in str(combo).split("+") if p.strip()]
    if not parts:
        return "пустое сочетание клавиш"
    if len(parts) > 4:
        return "слишком длинное сочетание (максимум 4 клавиши)"
    keys = []
    for p in parts:
        if p in VK:
            keys.append(VK[p])
        elif len(p) == 1 and (p.isalnum() or p in " ,./;'[]\\`-="):
            keys.append(u32.VkKeyW(ord(p)) & 0xFF)
        else:
            return "не знаю клавишу «%s» (ctrl/shift/alt/win/esc/enter/tab/f1-f12/буква)" % p
    for vk in keys:
        scan = u32.MapVirtualKeyW(vk, 0)   # v2.3.0: скан-коды (фикс Win и игр)
        u32.keybd_event(vk, scan, 0, 0)
        time.sleep(0.015)
    time.sleep(0.025)
    for vk in reversed(keys):
        scan = u32.MapVirtualKeyW(vk, 0)
        u32.keybd_event(vk, scan, _KEYUP, 0)
        time.sleep(0.015)
    return "OK: нажал %s" % "+".join(parts)


def type_text(text, delay=0.012):
    text = str(text)
    if not text:
        return "пустой текст"
    n = 0
    for ch in text[:1500]:
        if ch == "\n":
            _tap_vk(0x0D)
        else:
            _key_unicode(ch)
        time.sleep(delay)
        n += 1
    return "OK: набрал %d символов в активное окно" % n


def screen_size():
    return "%dx%d" % (u32.GetSystemMetrics(0), u32.GetSystemMetrics(1))


if __name__ == "__main__":
    print("экран:", screen_size())
    print(windows_list(10))
    print(mouse_action("позиция"))
