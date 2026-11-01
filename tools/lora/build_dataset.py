#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_dataset.py — LoRA v4, шаг 1: датасет стиля Шефа из истории Джарвиса.

Источники:
  D:\\Jarvis\\data\\mirror.jsonl  — все реплики обоих каналов (TG + веб)
  D:\\Jarvis\\data\\history.json  — последние пары диалога

Что делает:
  - собирает пары «Шеф -> Джарвис» (финальные ответы, без инструментных
    JSON и служебных реплик GLM);
  - фильтрует мусор (⚠️-ошибки, дубли, слишком короткие/длинные);
  - пишет OpenAI-совместимый JSONL (system/user/assistant) для
    unsloth / axolotl / LLaMA-Factory;
  - печатает статистику.

Запуск:  D:\\Jarvis\\python\\python.exe D:\\Jarvis\\tools\\lora\\build_dataset.py
Выход:   E:\\Downloads\\Jarvis\\lora_dataset_<дата>.jsonl + сводка.
"""
import json, os, re, sys, time, collections

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # D:\Jarvis
MIRROR = os.path.join(BASE, "data", "mirror.jsonl")
HIST = os.path.join(BASE, "data", "history.json")
OUT_DIR = os.path.join("E:", os.sep, "Downloads", "Jarvis")

# Системный промпт берём из живого jarvis.py — датасет учит модель её роли
sys.path.insert(0, BASE)
try:
    import jarvis
    SYSTEM = jarvis.prompt_fill(jarvis.SYSTEM)
except Exception as e:
    print("не смог взять SYSTEM из jarvis.py (%s) — беру без подстановок" % e)
    SYSTEM = None

BAD_START = ("⚠️", "🏓", "🚨", "📡", "🎮", "☕", "🤖 *", "🖥 Локальный",
             "🎙 Рация", "🤝 GLM")
GLM_MARK = ("GLM (z.ai)", "glm", "служебная проверка", "служебная")


def load_mirror():
    rows = []
    if not os.path.isfile(MIRROR):
        return rows
    with open(MIRROR, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                continue
    return rows


def load_hist():
    try:
        with open(HIST, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def clean(t):
    t = re.sub(r"\s+", " ", str(t or "")).strip()
    return t


def good_user(t):
    if not (2 <= len(t) <= 600):
        return False
    if any(m in t for m in GLM_MARK):        # мои служебные реплики
        return False
    return True


def good_assistant(t):
    if not (2 <= len(t) <= 1200):
        return False
    if t.startswith(BAD_START):              # авто-уведомления и ошибки
        return False
    if t.lstrip().startswith('{"tool"'):     # сырой инструментный JSON
        return False
    return True


def pairs_from_rows(rows):
    """Идём по хронологии: boss-реплика + следующий jarvis-ответ."""
    pairs = []
    pending = None
    for r in rows:
        who = str(r.get("who", "")).lower()
        txt = clean(r.get("text", ""))
        if who == "boss":
            pending = txt
        elif who == "jarvis" and pending is not None:
            if good_user(pending) and good_assistant(txt):
                pairs.append((pending, txt))
            pending = None
        elif who == "glm":
            pending = None                    # служебный обмен — пропускаем
    return pairs


def main():
    rows = load_mirror()
    pairs = pairs_from_rows(rows)

    # история тоже даёт пары (могут пересекаться с зеркалом — дедуп)
    hist = load_hist()
    hq = []
    for i in range(0, len(hist) - 1, 2):
        u, a = hist[i], hist[i + 1]
        if u.get("role") == "user" and a.get("role") == "assistant":
            hq.append((clean(u.get("content")), clean(a.get("content"))))
    seen = set((u[:200], a[:200]) for u, a in pairs)
    for u, a in hq:
        k = (u[:200], a[:200])
        if k not in seen:
            seen.add(k)
            if good_user(u) and good_assistant(a):
                pairs.append((u, a))

    # дедуп финальный, сохраняем порядок
    uniq, useen = [], set()
    for u, a in pairs:
        k = (u[:300], a[:300])
        if k in useen:
            continue
        useen.add(k)
        uniq.append((u, a))
    pairs = uniq

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(
        OUT_DIR, "lora_dataset_%s.jsonl" % time.strftime("%Y%m%d"))
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for u, a in pairs:
            msg = [{"role": "user", "content": u},
                   {"role": "assistant", "content": a}]
            if SYSTEM:
                msg.insert(0, {"role": "system", "content": SYSTEM})
            f.write(json.dumps({"messages": msg}, ensure_ascii=False) + "\n")
            n += 1

    words = collections.Counter()
    for u, a in pairs:
        for w in re.findall(r"[а-яёa-z]{4,}", u.lower()):
            words[w] += 1
    print("=" * 60)
    print("ДАТАСЕТ: %s" % out)
    print("примеров (пар Шеф->Джарвис): %d" % n)
    print("зеркало: %d строк, история: %d записей" % (len(rows), len(hist)))
    print("system-промпт: %s" % ("живой из jarvis.py" if SYSTEM else "нет"))
    if words:
        print("любимые слова Шефа: %s" %
              ", ".join(w for w, _ in words.most_common(12)))
    print("=" * 60)
    print("Дальше — рецепт: tools/lora/README_LORA.md")
    print("Готово к обучению при появлении GPU (см. README).")


if __name__ == "__main__":
    main()
