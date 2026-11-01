#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hwinfo_sensors.py — v3.5.0: датчики HWiNFO через Shared Memory v2 (SM2).
Формат реверс-инжинирен (namazso/gist) + проверен на HWiNFO 8.42."""

import ctypes

SM2_NAMES = ("HWiNFO_SENS_SM2", "Global\\HWiNFO_SENS_SM2")
MUTEX_NAMES = ("HWiNFO_SM2_MUTEX", "Global\\HWiNFO_SM2_MUTEX")
MAGIC = 0x53695748  # 'SiWH' как MSVC multi-char constant (байты в LE: 48 57 69 53)
FILE_MAP_READ = 0x0004
TYPES = {0: "прочее", 1: "темп", 2: "напр", 3: "вент", 4: "ток",
         5: "мощн", 6: "част", 7: "нагр", 8: "др"}

_k32 = None
_h_map = 0
_view = 0


def _open():
    global _k32, _h_map, _view
    if _view:
        return True
    _k32 = ctypes.windll.kernel32
    _k32.OpenFileMappingW.restype = ctypes.c_void_p   # ВАЖНО: HANDLE 64-битный
    _k32.MapViewOfFile.restype = ctypes.c_void_p      # иначе указатель обрежется
    for n in SM2_NAMES:
        h = _k32.OpenFileMappingW(FILE_MAP_READ, False, n)
        if h:
            _h_map = h
            break
    else:
        return False
    _view = _k32.MapViewOfFile(_h_map, FILE_MAP_READ, 0, 0, 0) or 0
    return bool(_view)


def _u32(off):
    return ctypes.c_uint32.from_address(_view + off).value


def _i64(off):
    return ctypes.c_int64.from_address(_view + off).value


def _dbl(off):
    return ctypes.c_double.from_address(_view + off).value


def _cstr(off, n):
    raw = ctypes.string_at(_view + off, n)
    return raw.split(b"\x00", 1)[0].decode("utf-8", "replace").strip()


def close():
    """Освободить маппинг (вызывать не обязательно, но культурно)."""
    global _h_map, _view
    if _view and _k32:
        _k32.UnmapViewOfFile(ctypes.c_void_p(_view))
        _view = 0
    if _h_map and _k32:
        _k32.CloseHandle(ctypes.c_void_p(_h_map))
        _h_map = 0


def read_all():
    """[{"sensor": имя, "type": тип, "label": метка, "unit": ед,
    "value": v, "min":, "max":, "avg":}] — или [] если HWiNFO не найден."""
    if not _open():
        return []
    try:
        if _u32(0) != MAGIC:
            return []
        sens_off = _u32(0x14)
        sens_size = _u32(0x18)
        sens_cnt = _u32(0x1C)
        ent_off = _u32(0x20)
        ent_size = _u32(0x24)
        ent_cnt = _u32(0x28)
        if not (0 < sens_size <= 1024 and 0 < ent_size <= 1024
                and sens_cnt < 200 and ent_cnt < 4000):
            return []
        names = []
        for i in range(sens_cnt):
            base = sens_off + i * sens_size
            nm = _cstr(base + 8, 128) or _cstr(base + 0x88, 128)
            names.append(nm)
        out = []
        for i in range(ent_cnt):
            base = ent_off + i * ent_size
            typ = _u32(base)
            sidx = _u32(base + 4)
            if typ not in TYPES or sidx >= len(names):
                continue
            out.append({
                "sensor": names[sidx],
                "type": TYPES[typ],
                "label": _cstr(base + 0x0C, 128) or _cstr(base + 0x8C, 128),
                "unit": _cstr(base + 0x10C, 16),
                "value": _dbl(base + 0x11C),
                "min": _dbl(base + 0x124),
                "max": _dbl(base + 0x12C),
                "avg": _dbl(base + 0x134),
            })
        return out
    except Exception:
        return []


def gpu_summary():
    """Компактно: GPU температура/нагрузка/мощность/частота/вентилятор."""
    rows = read_all()
    g = [r for r in rows if "GPU" in r["sensor"].upper()
         or "RADEON" in r["sensor"].upper() or "AMD RADEON" in r["sensor"].upper()]
    keys = ("GPU Temperature", "Hotspot", "GPU Core", "GPU Power",
            "GPU Fan", "GPU Core Clock", "GPU Memory")
    pick = [r for r in g if any(k.lower() in r["label"].lower() for k in keys)]
    return pick or g[:14]


if __name__ == "__main__":
    rows = read_all()
    print("всего показаний:", len(rows))
    sens = {}
    for r in rows:
        sens.setdefault(r["sensor"], 0)
        sens[r["sensor"]] += 1
    print("мониторы:", sens)
    print("--- GPU-выжимка ---")
    for r in gpu_summary():
        print("  %-28s %-30s %8.1f %s" % (r["sensor"][:28], r["label"][:30],
                                          r["value"], r["unit"]))
