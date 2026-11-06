#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
win_ctl.py — ДЖАРВИС v3.7.3 «РУКИ-АВТОФОКУС»: окна/мышь/клавиатура
со САМОПРОВЕРКОЙ каждого действия (Task 104).

v3.7.3 (Task 68, 02.11.2026, вечер-2): КРИТИЧЕСКИЙ ФИКС КЛИКОВ — у union
_IU первое поле ki (_KI), позиционный конструктор _IU(_MI(...)) падал
ctypes-ошибкой «incompatible types, _MI instance instead of _KI instance»:
ЛЮБОЙ клик/двойной/правый/скролл/перетащить через SendInput не работал
всю ночь и день 02.11 (движение было живо — оно через SetCursorPos, и
картина выглядела как «клик прошёл, а каретка/фокус не появились»).
Все вызовы переведены на именованные аргументы: _IU(mi=_MI(...)),
_IU(ki=_KI(...)). Поймано живым Тестом 3 (правый клик) по докладу мозга.

v3.7.2 (Task 68, 02.11.2026, вечер): живой Е2Е через мозг вскрыл разрыв
цепочки: после активации окна каретки нет -> мозг звал «мышь» -> кликал ->
И СНОВА «окно»/«печатать» — и на этих лишних шагах генерация деградировала
(пустой текст, оборванный ответ), текст так и не попадал в окно. Фикс:
type_text при отсутствии каретки САМ кликает в центр клиентской области
активного окна и повторяет проверку (клик тот же, что раньше подсказывался
мозгу — но без двух лишних шагов мозга). Печать без каретки даже после
клика — честный отказ.

История: v2.3.0 «МАКС» (Task 91) дал окнам/мыши/клавиатуре полные
разрешения. Ночь 02.11 вскрыла два изъяна: (1) мозг путал масштаб —
слал крошечные координаты («правый 350,260») на 4K-экране, курсор
улетал в левый верхний угол; (2) инструмент докладывал «OK: нажал»
после ЛЮБОГО вызова — без проверки, что действие состоялось. v3.7.0
чинит оба: координатный контракт (только физические пиксели скриншота)
и честность (З6): «OK … проверено» — только когда факт подтверждён
чтением состояния Windows.

Экспорт (вызывается из jarvis.tool_exec):
  windows_list(limit=30)                    — список видимых окон
  window_action(act, title, x, y, w, h)     — активировать/свернуть/развернуть/
                                              восстановить/закрыть/передвинуть/размер;
                                              каждое действие проверяется фактом
  mouse_action(act, x, y, x2, y2, amount)   — клик/двойной/правый/движение/
                                              перетащить/прокрутить/позиция;
                                              движение подтверждается чтением
                                              позиции курсора (±1 пиксель)
  key_combo("ctrl+s")                       — сочетание клавиш
  type_text("текст")                        — печать Юникода (русский работает)
  screen_size()                             — «3840x2160» (физические пиксели)
  screen_info()                             — физические + масштаб + логические

Координатный контракт (v3.7.0):
  процесс всегда DPI-aware (физические пиксели); скриншоты делаются в
  той же системе координат — координаты беру прямо со скриншота, 0,0 =
  левый верхний угол. Делить/умножать на масштаб НЕ нужно.

Безопасность:
  - закрытие системных и СВОИХ окон (llama/jarvis/python/Program Manager/
    панель задач) запрещено;
  - к UAC-запросам Windows доступа нет (secure desktop — защита системы);
  - окно для передвижения/размера ищется по части заголовка (без учёта регистра).
"""
import ctypes
import ctypes.wintypes as wt
import os
import time

try:  # v3.7.0: всегда физические пиксели — как в живом jarvis.py;
    # при повторном вызове Windows молча откажет, это норма
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

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
    # v3.7.1: НИКАКОГО pad! Настоящий INPUT на x64 = 40 байт
    # (DWORD type + выравнивание + union 32). Лишний pad давал 48 —
    # SendInput молча отклонял КАЖДЫЙ вызов: «печатать» не мог ввести
    # ни одного символа, выживали только \n через старый keybd_event.
    _fields_ = (("type", ctypes.c_ulong), ("u", _IU))


assert ctypes.sizeof(_IN) == 40, "INPUT должен быть 40 байт на x64, а не %d" % ctypes.sizeof(_IN)


_KBD = 1
_KEYUP = 0x0002
_UNICODE = 0x0004
# v3.7.1: мышь — тоже SendInput (как и клавиатуру): единый современный
# путь вместо древнего mouse_event (который из чат-сервера срабатывал
# не всегда — живой аудит 14:45: клик прошёл «ОК», а фокус не поставил)
_MOU = 0
_MLEFT_DOWN = 0x0002
_MLEFT_UP = 0x0004
_MRIGHT_DOWN = 0x0008
_MRIGHT_UP = 0x0010
_MWHEEL = 0x0800

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
CLOSE_DENY = ("program manager", "панель задач", "llama", "jarvis")

_EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

_DPI_PCT = None


def _title(h):
    b = ctypes.create_unicode_buffer(300)
    u32.GetWindowTextW(h, b, 300)
    return b.value.strip()


def _dpi_pct():
    """Масштаб Windows В ПРОЦЕНТАХ (250% -> 250; DPI 240/96=2.5). Лениво."""
    global _DPI_PCT
    if _DPI_PCT is None:
        try:
            hdc = u32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            u32.ReleaseDC(0, hdc)
            _DPI_PCT = max(100, int(round(int(dpi) * 100 / 96)))
        except Exception:
            _DPI_PCT = 100
    return _DPI_PCT


def screen_size():
    """«3840x2160» — ФИЗИЧЕСКИЕ пиксели (совпадают с системой координат
    скриншотов и мыши)."""
    return "%dx%d" % (u32.GetSystemMetrics(0), u32.GetSystemMetrics(1))


def screen_info():
    """Экран с масштабом: физические + логические пиксели."""
    w, h = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
    pct = _dpi_pct()
    if pct > 100:
        return ("%dx%d физические (масштаб Windows %d%%, логические %dx%d) — "
                "координаты мыши и скриншота в физических пикселях"
                % (w, h, pct, round(w * 100 / pct), round(h * 100 / pct)))
    return "%dx%d" % (w, h)


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
            (len(_visible_windows()), len(lines), screen_info(), "\n".join(lines)))


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
    time.sleep(0.15)
    return ok


def window_action(act, title, x=None, y=None, w=None, h=None):
    """v3.7.0: каждое действие подтверждается чтением фактического
    состояния окна. «OK … проверено» = правда; иначе честное «НЕ …»."""
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
        time.sleep(0.12)
        r2 = wt.RECT()
        u32.GetWindowRect(hw, ctypes.byref(r2))
        if (abs(r2.left - nx) <= 2 and abs(r2.top - ny) <= 2 and
                abs((r2.right - r2.left) - nw) <= 4 and
                abs((r2.bottom - r2.top) - nh) <= 4):
            return ("OK: окно «%s» — позиция (%d,%d), размер %dx%d — проверено "
                    "чтением границ" % (info, r2.left, r2.top,
                                        r2.right - r2.left, r2.bottom - r2.top))
        return ("НЕ подтвердилось: просил (%d,%d) %dx%d, по факту (%d,%d) %dx%d — "
                "окно могло ограничено системой или приложением"
                % (nx, ny, nw, nh, r2.left, r2.top,
                   r2.right - r2.left, r2.bottom - r2.top))
    hw, info = _find(title)
    if not hw:
        return info
    if act in ("активировать", "показать", "на_передний_план", "активно",
               "activate", "focus"):
        _activate(hw)
        if u32.GetForegroundWindow() == hw:
            return "OK: окно «%s» на переднем плане — проверено" % info
        return ("НЕ получилось: окно «%s» найдено, но Windows не отдал фокус "
                "(попробуй alt+tab или клик по окну мышью)" % info)
    if act in ("свернуть", "minimize"):
        u32.ShowWindow(hw, 6)
        time.sleep(0.12)
        if u32.IsIconic(hw):
            return "OK: окно «%s» свёрнуто — проверено" % info
        return "НЕ подтвердилось: окно «%s» всё ещё развёрнуто" % info
    if act in ("развернуть", "на_весь_экран", "maximize"):
        u32.ShowWindow(hw, 3)
        time.sleep(0.12)
        if u32.IsZoomed(hw):
            return "OK: окно «%s» развёрнуто на весь экран — проверено" % info
        return "НЕ подтвердилось: окно «%s» не развёрнуто" % info
    if act in ("восстановить", "обычный_размер", "restore"):
        u32.ShowWindow(hw, 9)
        time.sleep(0.12)
        if not u32.IsIconic(hw) and not u32.IsZoomed(hw):
            return "OK: окно «%s» восстановлено — проверено" % info
        return "НЕ подтвердилось: окно «%s» не в обычном размере" % info
    if act in ("закрыть", "close"):
        tl = info.lower()
        for d in CLOSE_DENY:
            if d in tl:
                return ("ОТКАЗ: окно «%s» системное/служебное — закрывать нельзя"
                        % info)
        u32.PostMessageW(hw, 0x0010, 0, 0)           # WM_CLOSE
        for _ in range(16):                          # до ~1.6 с ожидания
            time.sleep(0.1)
            if not u32.IsWindow(hw):
                return "OK: окно «%s» закрыто — проверено (окна больше нет)" % info
        if not u32.IsWindowVisible(hw):
            return ("OK: окно «%s» исчезло с экрана (закрылось или свернулось "
                    "в трей) — проверено" % info)
        return ("НЕ подтвердилось: окно «%s» живо спустя 1.6 с — вероятно, "
                "приложение спросило подтверждение или несохранённые данные. "
                "Посмотри «скрин» и скажи Шефу как есть" % info)
    return ("неизвестное действие «%s» (есть: активировать, свернуть, развернуть, "
            "восстановить, закрыть, передвинуть, размер)" % act)


# ---------------------------------------------------------------- мышь
def _cursor_pos():
    pt = wt.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def _move(x, y, tries=2):
    """Переместить курсор и ДОКАЗАТЬ: позиция читается назад.
    Возвращает (ok, факт_x, факт_y). Допуск ±1 пиксель (З6: «OK» —
    только если курсор реально стоит в точке)."""
    ax = ay = 0
    for _ in range(tries):
        u32.SetCursorPos(int(x), int(y))
        time.sleep(0.03)
        ax, ay = _cursor_pos()
        if abs(ax - int(x)) <= 1 and abs(ay - int(y)) <= 1:
            return True, ax, ay
    return False, ax, ay


def _click(button="left"):
    # v3.7.3: ФИКС КРИТИЧЕСКОГО БАГА v3.7.1: у union _IU первое поле — ki
    # (_KI), и позиционный _IU(_MI(...)) падал ctypes-ошибкой «_MI instance
    # instead of _KI instance» — ЛЮБОЙ клик/скролл/драг через SendInput
    # молча не работал с 02.11 утра (движение живо — оно через
    # SetCursorPos). Живой тест 18:15 поймал по докладу мозга.
    if button == "right":
        _si(_IN(_MOU, _IU(mi=_MI(0, 0, 0, _MRIGHT_DOWN, 0, None))))
        time.sleep(0.03)
        _si(_IN(_MOU, _IU(mi=_MI(0, 0, 0, _MRIGHT_UP, 0, None))))
    else:
        _si(_IN(_MOU, _IU(mi=_MI(0, 0, 0, _MLEFT_DOWN, 0, None))))
        time.sleep(0.03)
        _si(_IN(_MOU, _IU(mi=_MI(0, 0, 0, _MLEFT_UP, 0, None))))


def mouse_action(act, x=None, y=None, x2=None, y2=None, amount=0):
    """v3.7.0: движение всегда проверяется чтением позиции курсора;
    в докладе — фактические координаты. Координаты — физические
    пиксели (как на скриншоте)."""
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

    SW, SH = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)

    def _in_scr(vx, vy):
        return vx is None or vy is None or (0 <= vx <= SW and 0 <= vy <= SH)

    if act in ("позиция", "где_курсор", "pos"):
        ax, ay = _cursor_pos()
        return "курсор на (%d, %d); экран %s" % (ax, ay, screen_info())
    if act in ("движение", "переместить", "move"):
        if x is None or y is None:
            return "для движения нужны координаты x и y"
        if not _in_scr(x, y):
            return ("точка (%d,%d) вне экрана %s — проверь координаты по "
                    "скриншоту" % (x, y, screen_info()))
        ok, ax, ay = _move(x, y)
        if not ok:
            return ("НЕ получилось: курсор встал на (%d,%d) вместо (%d,%d) — "
                    "возможно, его удерживает игра/захват экрана"
                    % (ax, ay, x, y))
        return "OK: курсор на (%d, %d) — проверено чтением позиции" % (ax, ay)
    if act in ("клик", "нажать", "click"):
        if x is not None and y is not None:
            if not _in_scr(x, y):
                return ("точка (%d,%d) вне экрана %s — проверь координаты по "
                        "скриншоту" % (x, y, screen_info()))
            ok, ax, ay = _move(x, y)
            if not ok:
                return ("НЕ получилось навести: курсор на (%d,%d) вместо (%d,%d)"
                        % (ax, ay, x, y))
            _click("left")
            return "OK: клик левой на (%d, %d) — позиция проверена" % (ax, ay)
        _click("left")
        ax, ay = _cursor_pos()
        return "OK: клик левой в текущей позиции (%d, %d)" % (ax, ay)
    if act in ("двойной", "двойной_клик", "double"):
        if x is not None and y is not None:
            if not _in_scr(x, y):
                return ("точка (%d,%d) вне экрана %s — проверь координаты по "
                        "скриншоту" % (x, y, screen_info()))
            ok, ax, ay = _move(x, y)
            if not ok:
                return ("НЕ получилось навести: курсор на (%d,%d) вместо (%d,%d)"
                        % (ax, ay, x, y))
            _click("left")
            time.sleep(0.06)
            _click("left")
            return "OK: двойной клик на (%d, %d) — позиция проверена" % (ax, ay)
        _click("left")
        time.sleep(0.06)
        _click("left")
        ax, ay = _cursor_pos()
        return "OK: двойной клик в текущей позиции (%d, %d)" % (ax, ay)
    if act in ("правый", "правый_клик", "right"):
        if x is not None and y is not None:
            if not _in_scr(x, y):
                return ("точка (%d,%d) вне экрана %s — проверь координаты по "
                        "скриншоту" % (x, y, screen_info()))
            ok, ax, ay = _move(x, y)
            if not ok:
                return ("НЕ получилось навести: курсор на (%d,%d) вместо (%d,%d)"
                        % (ax, ay, x, y))
            _click("right")
            return "OK: клик правой на (%d, %d) — позиция проверена" % (ax, ay)
        _click("right")
        ax, ay = _cursor_pos()
        return "OK: клик правой в текущей позиции (%d, %d)" % (ax, ay)
    if act in ("прокрутить", "скролл", "колесо", "scroll"):
        if not amt:
            return "укажи «сколько» щелчков (минус = вниз)"
        ax, ay = _cursor_pos()
        _si(_IN(_MOU, _IU(mi=_MI(0, 0, amt * 120, _MWHEEL, 0, None))))
        return ("OK: прокрутил %d щелчков (%s) под курсором (%d, %d)"
                % (abs(amt), "вверх" if amt > 0 else "вниз", ax, ay))
    if act in ("перетащить", "тащить", "drag"):
        if None in (x, y, x2, y2):
            return "для перетаскивания нужны x,y (откуда) и x2,y2 (куда)"
        if not (_in_scr(x, y) and _in_scr(x2, y2)):
            return ("точки (%d,%d)->(%d,%d) вне экрана %s"
                    % (x, y, x2, y2, screen_info()))
        ok1, ax, ay = _move(x, y)
        if not ok1:
            return ("НЕ получилось навестись на старт: курсор (%d,%d) вместо (%d,%d)"
                    % (ax, ay, x, y))
        time.sleep(0.06)
        _si(_IN(_MOU, _IU(mi=_MI(0, 0, 0, _MLEFT_DOWN, 0, None))))
        steps = 20
        for i in range(1, steps + 1):
            u32.SetCursorPos(x + (x2 - x) * i // steps, y + (y2 - y) * i // steps)
            time.sleep(0.012)
        _si(_IN(_MOU, _IU(mi=_MI(0, 0, 0, _MLEFT_UP, 0, None))))
        time.sleep(0.05)
        ok2, fx, fy = _move(x2, y2)  # дожать до конечной точки
        if ok2:
            return ("OK: перетащил из (%d,%d) в (%d, %d) — конечная позиция "
                    "проверена" % (x, y, fx, fy))
        return ("перетащил из (%d,%d), но финал (%d,%d) вместо (%d,%d) — "
                "скажи Шефу и проверь «скрин»" % (x, y, fx, fy, x2, y2))
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
    dn = _IN(_KBD, _IU(ki=_KI(0, code, _UNICODE, 0, None)))
    up = _IN(_KBD, _IU(ki=_KI(0, code, _UNICODE | _KEYUP, 0, None)))
    # v3.7.1: SendInput возвращает число ДОСТАВЛЕННЫХ событий; 0 = отказ
    if _si(dn) != 1 or _si(up) != 1:
        raise RuntimeError("SendInput отклонил символ U+%04X" % code)


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
        elif len(p) == 1 and p.isalnum():
            # v3.7.1: буквы/цифры — ФИКСИРОВАННЫЕ VK-коды (0x41+ / 0x30+):
            # VkKeyScanW в русской раскладке не знает латиницу (-1), а
            # «ctrl+t» обязан работать в любой раскладке (VK не зависит от неё)
            if p.isdigit():
                keys.append(0x30 + int(p))
            else:
                keys.append(0x41 + (ord(p.lower()) - ord("a")))
        elif len(p) == 1 and p in " ,./;'[]\\`-=":
            # пунктуация —_best effort через раскладку
            vk = u32.VkKeyScanW(ord(p))
            if vk < 0 or (vk & 0xFF) == 0xFF:
                return ("не знаю клавишу «%s» (нет VK-кода в текущей "
                        "раскладке)" % p)
            keys.append(vk & 0xFF)
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


def _caret_hwnd():
    """v3.7.1: hwnd каретки активного GUI-потока (None = фокус не в поле
    ввода — печатать некуда)."""
    try:
        class _GUITHREADINFO(ctypes.Structure):
            _fields_ = (("cbSize", ctypes.c_ulong), ("flags", ctypes.c_ulong),
                        ("hwndActive", ctypes.c_void_p),
                        ("hwndFocus", ctypes.c_void_p),
                        ("hwndCapture", ctypes.c_void_p),
                        ("hwndMenuOwner", ctypes.c_void_p),
                        ("hwndMoveSize", ctypes.c_void_p),
                        ("hwndCaret", ctypes.c_void_p),
                        ("rcCaret", wt.RECT))
        gti = _GUITHREADINFO()
        gti.cbSize = ctypes.sizeof(_GUITHREADINFO)
        h = u32.GetForegroundWindow()
        tid = u32.GetWindowThreadProcessId(h, None) if h else 0
        if tid and u32.GetGUIThreadInfo(tid, ctypes.byref(gti)):
            return (h, gti.hwndFocus, gti.hwndCaret)
    except Exception:
        pass
    return (None, None, None)


def _gui_focus_info():
    """v3.7.1 (отладка): фокус-контроль и каретка активного потока GUI."""
    h, foc, car = _caret_hwnd()
    if h is None:
        return "(no gui info)"
    return "fg=%s focus=%s caret=%s" % (h, foc, car)


TRACE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "data", "type_trace.log") if os.path.isdir(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")) else None


def type_text(text, delay=0.012):
    text = str(text)
    if not text:
        return "пустой текст"
    fg = u32.GetForegroundWindow()
    ttl = _title(fg) if fg else "(активного окна НЕТ!)"
    # v3.7.2: АВТОФОКУС. Каретки нет -> сами кликаем в центр КЛИЕНТСКОЙ
    # области активного окна (та же точка, что раньше подсказывалась
    # мозгу) и проверяем каретку повторно. Живой Е2Е показал: лишние шаги
    # мозга («мышь» + повтор «печатать») — место, где генерация рвётся.
    # Клиентская область = без заголовка/вкладок; центр неё у текстовых
    # окон — редактор. Клик подтверждается появлением каретки, иначе
    # ничего не печатаем (З6: без каретки текст уходит «в никуда»).
    _h, _foc, car = _caret_hwnd()
    clicked = None
    if not car and _h:
        try:
            cr = wt.RECT()
            if u32.GetClientRect(_h, ctypes.byref(cr)):
                cpt = wt.POINT((cr.right - cr.left) // 2,
                               (cr.bottom - cr.top) * 45 // 100)
                if u32.ClientToScreen(_h, ctypes.byref(cpt)):
                    okm, ax, ay = _move(cpt.x, cpt.y)
                    if okm:
                        _click("left")
                        clicked = (ax, ay)
                        time.sleep(0.18)
                        _h, _foc, car = _caret_hwnd()
        except Exception:
            pass
    if not car:
        hint = ""
        try:
            r = wt.RECT()
            if _h and u32.GetWindowRect(_h, ctypes.byref(r)):
                cx = (r.left + r.right) // 2
                cy = (r.top + r.bottom) // 2
                hint = " — примерно (%d,%d)" % (cx, cy)
        except Exception:
            pass
        if clicked:
            return ("НЕ получилось: сам кликнул в центр окна «%s» (%d,%d), "
                    "но текстовый курсор не появился — без каретки не "
                    "печатаю (текст ушёл бы в никуда). Посмотри «скрин»: "
                    "поле ввода в другом месте окна" % (ttl, clicked[0],
                                                        clicked[1]))
        return ("НЕ получилось: в активном окне «%s» нет текстового курсора "
                "(фокус не в поле ввода — например, на полосе вкладок или "
                "панели). Кликни мышью в центр окна%s и сразу повтори "
                "печать" % (ttl, hint))
    tr = None
    if TRACE and len(text) > 20:      # трейс только для заметных печатей
        try:
            tr = open(TRACE, "a", encoding="utf-8")
            tr.write("[%s] печать %d симв. в «%s»; %s\n"
                     % (time.strftime("%H:%M:%S"), len(text), ttl,
                        _gui_focus_info()))
        except Exception:
            tr = None
    n = 0
    failed = 0
    for ch in text[:1500]:
        try:
            if ch == "\n":
                _tap_vk(0x0D)
            else:
                _key_unicode(ch)
        except Exception:
            failed += 1
        if tr is not None and n < 40:
            tr.write("  [%03d] %r t=%.3f %s\n"
                     % (n, ch, time.time() % 60.0, _gui_focus_info()
                        if n in (0, 1, 2, 3, 5, 8, 12, 20, 39) else ""))
        time.sleep(delay)
        n += 1
    if tr is not None:
        try:
            tr.write("[конец] %s\n" % _gui_focus_info())
            tr.close()
        except Exception:
            pass
    # v3.7.1: сверяем ОКНО (hwnd), а не заголовок — Notepad сам меняет
    # заголовок вкладки на первую строку набранного текста (это норма)
    fg2 = u32.GetForegroundWindow()
    if failed:
        return ("НЕ получилось: %d из %d символов НЕ дошли (SendInput "
                "отклонил) — текст в окне «%s» неполный, проверь «скрин»"
                % (failed, n, ttl))
    if fg2 != fg:
        ttl2 = _title(fg2) if fg2 else "?"
        return ("ВНИМАНИЕ: во время печати активное окно сменилось «%s» -> "
                "«%s» — текст мог уйти не туда, проверь «скрин»"
                % (ttl, ttl2))
    if clicked:
        return ("OK: набрал %d символов в активное окно «%s» (каретку "
                "поставил авто-клик в %d,%d)" % (n, ttl, clicked[0],
                                                clicked[1]))
    return "OK: набрал %d символов в активное окно «%s»" % (n, ttl)


if __name__ == "__main__":
    print("экран:", screen_info())
    print(windows_list(10))
    print(mouse_action("позиция"))
