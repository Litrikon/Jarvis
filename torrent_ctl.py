# -*- coding: utf-8 -*-
"""torrent_ctl.py v1.0 (Task 105, 02.11.2026) — uTorrent под управлением Джарвиса.

Приказ Шефа (ночь 02.11): «утром — окно ПК2 с ПУСТЫМ uTorrent, игру из него
удаляет ДЖАРВИС». Мозг вызывает инструмент «торренты», этот модуль делает
работу и докладывает ТОЛЬКО подтверждённые факты (закон З6).

Как устроено (проверено на живом клиенте):
- профиль клиента: %APPDATA%\\uTorrent, exe там же;
- список раздач живёт в resume.dat (bencode, СТАРЫЙ формат: записи прямо
  на верхнем уровне, ключи «<имя>.torrent»); .fileguard внутри — подпись
  неизвестного алгоритма, безопасно переписывать файл руками НЕЛЬЗЯ;
- поэтому полная очистка списка = при ОСТАНОВЛЕННОМ клиенте удалить
  resume.dat (+ .old, иначе откатится к нему) — клиент стартует заново
  с пустым списком и сам создаст свежую базу;
- данные (папки/файлы игры) удаляются ТОЛЬКО по путям из resume.dat —
  мозг не может подсунуть свой путь (защита от случайного сноса);
- перед удалением база копируется в D:\\Jarvis\\data\\utorrent_backups\\.
"""
import os
import re
import shutil
import subprocess
import time

PROFILE = os.path.join(os.environ.get("APPDATA", ""), "uTorrent")
EXE = os.path.join(PROFILE, "uTorrent.exe")
RESUME = os.path.join(PROFILE, "resume.dat")
RESUME_OLD = os.path.join(PROFILE, "resume.dat.old")
BACKUP_ROOT = r"D:\Jarvis\data\utorrent_backups"

# Пути, которые данные НЕ удаляем никогда (страховка поверх «только из базы»)
_DENY_PREFIXES = (r"c:\windows", r"c:\program", r"c:\users",
                  r"d:\jarvis", PROFILE.lower())


# ---------------------------------------------------------------- bencode

def _bdecode(data):
    pos = [0]

    def read(n):
        r = data[pos[0]:pos[0] + n]
        pos[0] += n
        return r

    def parse():
        c = data[pos[0]:pos[0] + 1]
        if c == b"d":
            pos[0] += 1
            d = {}
            while data[pos[0]:pos[0] + 1] != b"e":
                k = parse()
                d[k] = parse()
            pos[0] += 1
            return d
        if c == b"l":
            pos[0] += 1
            l = []
            while data[pos[0]:pos[0] + 1] != b"e":
                l.append(parse())
            pos[0] += 1
            return l
        if c == b"i":
            pos[0] += 1
            e = data.index(b"e", pos[0])
            v = int(data[pos[0]:e])
            pos[0] = e + 1
            return v
        e = data.index(b":", pos[0])
        n = int(data[pos[0]:e])
        pos[0] = e + 1
        return read(n)

    return parse()


def _entries():
    """Раздачи из resume.dat (последняя сохранённая база клиента)."""
    if not os.path.isfile(RESUME):
        return None  # базы нет = клиент никогда не сохранял список
    raw = open(RESUME, "rb").read()
    d = _bdecode(raw)
    out = []
    for k, v in d.items():
        if not isinstance(v, dict):
            continue  # .fileguard, rec и прочие служебные
        name = k.decode("utf-8", "replace")
        if not name.lower().endswith(".torrent"):
            continue
        path = (v.get(b"path") or b"").decode("utf-8", "replace")
        if not path:
            root = (v.get(b"root_dir") or b"").decode("utf-8", "replace")
            cap = (v.get(b"caption") or b"").decode("utf-8", "replace")
            path = os.path.join(root, cap) if root and cap else ""
        try:
            size = int(v.get(b"total_wanted") or v.get(b"size") or 0)
        except (TypeError, ValueError):
            size = 0
        out.append({"key": name, "name": name[:-len(".torrent")], "path": path,
                    "size": size, "caption":
                    (v.get(b"caption") or b"").decode("utf-8", "replace")})
    return out


# ---------------------------------------------------------------- процесс

def _proc():
    """(pid, жив ли) процесс uTorrent.exe."""
    try:
        r = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                           capture_output=True, timeout=20,
                           creationflags=0x08000000)
        for ln in r.stdout.decode("utf-8", "replace").split("\n"):
            if ln.lower().startswith('"utorrent.exe"'):
                pid = int(ln.split('","')[1])
                return pid, True
    except Exception:
        pass
    return None, False


def _stop(timeout=15):
    """Остановить клиент: вежливо (WM_CLOSE), затем решительно (/F)."""
    pid, alive = _proc()
    if not alive:
        return True, "клиент не был запущен"
    subprocess.run(["taskkill", "/PID", str(pid)],
                   capture_output=True, timeout=20, creationflags=0x08000000)
    for _ in range(timeout * 2):
        time.sleep(0.5)
        if not _proc()[1]:
            return True, "клиент закрыт штатно (WM_CLOSE)"
    subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                   capture_output=True, timeout=20, creationflags=0x08000000)
    for _ in range(10):
        time.sleep(0.5)
        if not _proc()[1]:
            return True, "клиент снят принудительно (/F)"
    return False, "клиент НЕ удалось остановить"


def _start():
    if not os.path.isfile(EXE):
        return False
    subprocess.Popen([EXE], cwd=PROFILE, close_fds=True)
    for _ in range(20):
        time.sleep(0.5)
        if _proc()[1]:
            return True
    return False


# ---------------------------------------------------------------- утилиты

def _fmt(n):
    x = float(n)
    for u in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if x < 1024 or u == "ТБ":
            return ("%.1f %s" % (x, u)) if u != "Б" else ("%d Б" % n)
        x /= 1024.0


def _dir_size(p):
    tot = 0
    for dp, _, fn in os.walk(p):
        for f in fn:
            try:
                tot += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return tot


def _backup():
    ts = time.strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, ts)
    os.makedirs(dst, exist_ok=True)
    saved = []
    for f in (RESUME, RESUME_OLD):
        if os.path.isfile(f):
            shutil.copy2(f, os.path.join(dst, os.path.basename(f)))
            saved.append(os.path.basename(f))
    return dst, saved


def _kill_torrent_files(names):
    """Удалить .torrent-файлы в профиле, соответствующие удалённым записям
    (включая дубли вроде «... .1.torrent»)."""
    stems = set()
    for n in names:
        st = n.lower()
        st = re.sub(r"\.\d+$", "", st)  # «name.1» -> «name»
        stems.add(st)
    removed = []
    try:
        for f in os.listdir(PROFILE):
            fl = f.lower()
            if not fl.endswith(".torrent"):
                continue
            core = fl[:-len(".torrent")]
            core = re.sub(r"\.\d+$", "", core)
            if any(core == s or core.startswith(s) or s.startswith(core)
                   for s in stems if len(s) > 6):
                try:
                    os.remove(os.path.join(PROFILE, f))
                    removed.append(f)
                except OSError:
                    pass
    except OSError:
        pass
    return removed


# ---------------------------------------------------------------- команды

def list_torrents():
    pid, alive = _proc()
    ent = _entries()
    head = "📡 uTorrent: %s\n" % ("запущен (PID %s)" % pid if alive
                                  else "сейчас НЕ запущен")
    if ent is None:
        return head + "Список ПУСТ (базы resume.dat нет — клиент стартовал чистым)."
    if not ent:
        return head + "Список ПУСТ (в базе 0 раздач)."
    lines = ["Раздач в списке: %d" % len(ent)]
    for e in ent:
        sz = _fmt(e["size"]) if e["size"] else "?"
        lines.append("• %s — %s\n  данные: %s" % (e["name"], sz, e["path"] or "?"))
    lines.append("(база — последняя сохранённая клиентом; живой процесс мог "
                 "добавить новое после сохранения)")
    return head + "\n".join(lines)


def remove_torrents(which="", files=""):
    """Удалить раздачи из списка (полная очистка). Данные — только при
    files=да и только по путям из базы."""
    which = (which or "").strip().lower()
    want_files = (files or "").strip().lower() in ("да", "yes", "ok", "ок",
                                                   "true", "1", "вместе с файлами")
    pid, alive = _proc()
    ent = _entries()
    if ent is None:
        ent = []
    if not which or which in ("все", "всё", "all"):
        match = ent
    else:
        match = [e for e in ent if which in e["name"].lower()
                 or which in (e.get("caption") or "").lower()]
        if not match:
            return ("❌ Не нашёл раздачу по слову «%s». Вот что есть:\n%s"
                    % (which, list_torrents()))
    if not match and not ent:
        # и так пусто: просто убедимся, что клиент есть и чист
        if alive:
            return ("Список и так ПУСТ (0 раздач), клиент запущен. "
                    "Делать нечего.")
        ok = _start()
        return ("Список пуст, клиент был не запущен. %s"
                % ("Запустил его — окно откроется на экране." if ok
                   else "Запустить клиент НЕ получилось (нет exe?)."))
    if match and len(match) < len(ent):
        return ("❌ Частичное удаление пока не умею (когда в списке остаются "
                "другие раздачи). Сейчас в списке %d, удалять просят %d. "
                "Умею: полная очистка списка («какая» пусто или «все»). "
                "Это честное ограничение, а не ошибка." % (len(ent), len(match)))

    # ---- 1. стоп клиента
    ok_stop, how = _stop()
    if not ok_stop:
        return "❌ НЕ получилось остановить uTorrent — отменил всё, ничего не трогал."

    # ---- 2. бэкап базы
    try:
        bdir, bsaved = _backup()
    except Exception as e:
        return "❌ НЕ получилось снять бэкап базы (%s) — отменил удаление." % e

    # ---- 3. очистка списка: удалить базу (клиент стартует пустым)
    gone = []
    for f in (RESUME, RESUME_OLD):
        try:
            if os.path.isfile(f):
                os.remove(f)
            if not os.path.isfile(f):
                gone.append(os.path.basename(f))
        except OSError:
            pass
    if len(gone) < 1:
        return ("❌ НЕ получилось удалить базу списка (resume.dat). Клиент "
                "остановлен, данные не тронуты. Бэкап: %s" % bdir)

    # ---- 4. удаление данных (только пути из базы!)
    freed, data_report = 0, []
    if want_files and match:
        for e in match:
            p = e["path"]
            low = p.lower().rstrip("\\")
            if not p or len(low) < 7 or low[1] != ":" \
                    or any(low.startswith(x) for x in _DENY_PREFIXES):
                data_report.append("• %s — путь отклонён защитой (системный "
                                   "или профильный), НЕ трогал" % (p or "(пусто)"))
                continue
            if os.path.isdir(p):
                sz = _dir_size(p)
                try:
                    shutil.rmtree(p)
                    if os.path.isdir(p):
                        data_report.append("• %s — НЕ удалилась, папка на месте" % p)
                    else:
                        freed += sz
                        data_report.append("• %s — удалено (%s), папки больше "
                                           "НЕТ — проверено" % (p, _fmt(sz)))
                except OSError as ex:
                    data_report.append("• %s — ошибка удаления: %s" % (p, ex))
            elif os.path.isfile(p):
                sz = os.path.getsize(p)
                try:
                    os.remove(p)
                    freed += sz
                    data_report.append("• файл %s — удалён (%s) — проверено"
                                       % (p, _fmt(sz)))
                except OSError as ex:
                    data_report.append("• файл %s — ошибка: %s" % (p, ex))
            else:
                data_report.append("• %s — на диске уже не было (и ладно)" % p)

    # ---- 5. .torrent-файлы в профиле
    tf = _kill_torrent_files([e["key"] for e in match]) if match else []

    # ---- 6. старт клиента заново (пустым)
    ok_start = _start()

    # ---- 7. итог только из фактов
    ent2 = _entries()
    left = len(ent2) if ent2 else 0
    lines = ["🧹 uTorrent: список очищен"]
    lines.append("• удалено из списка: %d %s"
                 % (len(match),
                    ("(" + "; ".join(e["name"] for e in match) + ")")
                    if match else ""))
    if want_files and match:
        lines.append("• данные на диске:")
        lines.extend("  " + x for x in data_report)
        lines.append("• освобождено: %s" % _fmt(freed))
    elif match:
        lines.append("• данные на диске НЕ тронуты («файлы» не «да»): %s"
                     % "; ".join(e["path"] for e in match if e["path"]))
    if tf:
        lines.append("• .torrent-файлы профиля удалены: %d шт." % len(tf))
    lines.append("• клиент: %s" % ("перезапущен (PID %s), окно откроется на "
                                   "экране" % _proc()[0] if ok_start and _proc()[1]
                                   else "ЗАПУСТИТЬ НЕ УДАЛОСЬ — скажи Шефу"))
    lines.append("• проверка базы: %s" % ("раздач осталось %d" % left
                                          if ent2 is not None
                                          else "новой базы ещё нет — клиент "
                                               "создаст при сохранении (старт "
                                               "был чистым)"))
    lines.append("• бэкап прежнего состояния: %s (%s)"
                 % (bdir, ", ".join(bsaved) or "пусто"))
    return "\n".join(lines)
