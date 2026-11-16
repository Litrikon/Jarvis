#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brain_core.py — ЕДИНЫЙ ЦИКЛ МОЗГА (Task 182, стратегический рефакторинг
по приказу Шефа «ДЕЛАЙ / СТРАТЕГИЧЕСКИЙ РЕФАКТОРИНГ», 16.11.2026).

КОРЕНЬ ПРОБЛЕМЫ (аудит Task 181): цикл «LLM -> инструмент -> LLM» был
физически продублирован в jarvis.py (TG) и chat_server.py (веб). Каждый
новый страж приходилось копировать в оба места — и один раз забыли
(BT-страж, Task 175: «стража НЕ БЫЛО ВОВСЕ, только в TG-ветке»), ссылка-
и short-стражи в веб так и не доехали, консилиум в вебе молча
превращался в think, «спать/проснись/статус» из веба уходили мозгу
вместо мгновенных команд.

РЕШЕНИЕ: один модуль, один цикл. Оба канала (TG и веб) вызывают
brain_loop(); стражи, консилиум, короткие ответы, честные финалы живут
ЗДЕСЬ. Канал отличается только «раковиной» (sink) — куда доставлять
текст/фото/индикатор «печатает».

API:
    brain_loop(j, ctx)  -> (final_text, events) — главный цикл
        j: модуль jarvis (импортируется КАК ЕДИНОЕ ЦЕЛОЕ, чтобы не
           плодить вторую копию состояния LLM_PROC/history)
        ctx: dict(
            text, mode, sysmsg, hist_len(None=авто), stream(bool),
            emit(evdict)->bool, on_step()->None, log(msg)->None)
    fast_command(j, t)  -> dict|None — быстрые команды ДО мозга
        возвращает {"kind":"photo","path",...} | {"kind":"text","text"}
        или None (= не быстрая команда, решает мозг)
    web_sysmsg(j)       — системный промпт для веб-чата
    llm_stream_chat(j, messages, ...) — потоковая генерация (веб)

СОБЫТИЯ (единый протокол, канал сам решает, как их показать):
    {"type":"say","text":...}        — комментарий перед инструментом
    {"type":"tool","name":...}       — инструмент исполнен
    {"type":"image","path":...}      — фото (скрин/камера) — канал сам
                                       кодирует/удаляет файл
    {"type":"waiting"}               — долгая работа (typing/спиннер)
    {"type":"file","path","name","size"} — карточка «скачать» (веб)
    {"type":"final","text":...}      — финальный ответ (возвращается
                                       также из brain_loop)
    {"type":"fail","text":...}       — честный отказ/срыв (тоже финал)
"""

import json
import os
import time
import traceback


# ---------------------------------------------------------------- быстрые команды

def fast_command(j, t):
    """v3.30.0 (Task 182): быстрые команды — единый справочник для TG и
    веб. В TG это тело handle() до мозга; в вебе раньше их НЕ БЫЛО и
    «статус»/«спать» жгли 12 шагов думания или вовсе не работали.
    Возвращает dict или None. ТЕЛО команд остаётся в jarvis.py
    (cmd_status/cmd_disks/.../power_confirm) — здесь только маршрутизация,
    чтобы у команд было одно определение и одна справка."""
    t = (t or "").strip().lower()
    if t in ("/start", "/help") or t in ("помощь", "хелп", "help",
                                         "начало"):
        return {"kind": "text", "text": j.HELP}
    if t in ("статус", "/status", "стат"):
        return {"kind": "text", "text": j.cmd_status()}
    if t in ("диски", "/disks", "smart", "смарт"):
        return {"kind": "text", "text": j.cmd_disks()}
    if t in ("место", "/space", "свободное место"):
        return {"kind": "text", "text": j.cmd_space()}
    if t in ("процессы", "/ps", "проц"):
        return {"kind": "text", "text": j.cmd_processes()}
    if t in ("журнал", "лог"):
        return {"kind": "text", "text": j.cmd_journal()}
    if t in ("пинг", "/ping", "живой"):
        return {"kind": "text", "text": "🏓 Джарвис жив. Аптайм: %s" %
                time.strftime("%H:%M:%S",
                              time.gmtime(time.time() - j.BIRTH))}
    if t.startswith("скрин") or t == "/shot":
        # photo-команды исполняет КАНАЛ (TG — send_photo, веб — b64):
        # возвращаем {"kind":"cmd","fn":...}, канал сам решает, как
        # показать фото. cmd_shot() шлёт фото Шефу сам (send_photo
        # внутри) и возвращает текст-ошибку или None.
        return {"kind": "cmd", "fn": "cmd_shot"}
    if t.startswith("камер") or t == "/cam":
        return {"kind": "cmd", "fn": "cmd_camera"}
    if t.startswith("больш"):
        return {"kind": "text", "text": j.cmd_bigfolders()}
    if j.PC_POWER_OFF_RE.match(t):
        return {"kind": "text", "text": j.power_confirm("off")}
    if j.PC_POWER_REBOOT_RE.match(t):
        return {"kind": "text", "text": j.power_confirm("reboot")}
    return None


def _shot_caption(j):
    c = j.SHOT_CURSOR
    return ("📸 Экран %s, " % j.HOSTNAME
            + time.strftime("%d.%m %H:%M")
            + ((" | 🖱 мышь: %d, %d" % (c["x"], c["y"])) if c else ""))


def run_fast(j, fast, emit_photo):
    """Исполнение результата fast_command каналом. emit_photo(path,
    caption) — доставка фото (TG: send_photo, веб: карточка b64).
    Возвращает текст для Шефа или None (фото уже ушло)."""
    if not fast:
        return None
    if fast["kind"] == "text":
        return fast["text"]
    if fast["kind"] == "photo":
        emit_photo(fast["path"], fast.get("caption", ""))
        try:
            os.remove(fast["path"])
        except OSError:
            pass
        return None
    if fast["kind"] == "cmd":
        # cmd_shot/cmd_camera сами фотографируют и отдают фото Шефу
        # (send_photo внутри) — либо текст ошибки; их и зовём.
        fn = getattr(j, fast["fn"])
        return fn() or None
    return None


def sleep_wake(j, t, emit=None):
    """«спать»/«проснись» — единственная быстрая команда, которая МЕНЯЕТ
    состояние машины (VRAM). Вынесена отдельно: TG и веб обязаны звать
    её ДО brain_loop (мозг спит — цикл не нужен). emit (если канал дал) —
    показать «загружаю...» СРАЗУ: загрузка модели идёт минуты, Шеф не
    должен смотреть в тишину. Возвращает текст или None."""
    t = (t or "").strip().lower()
    if "спать" in t or t in ("сон", "sleep", "усни"):
        j.llm_stop("manual")
        j.journal("Мозг выгружен из VRAM командой Шефа («спать»)")
        return ("😴 Мозг выгружен из видеопамяти — VRAM свободна для "
                "игр.\n«проснись» — верну (загрузка ~минуты).")
    if any(w in t for w in ("проснись", "проспись", "подъём")) \
            or "wake" in t:
        j.LLM_PROC["sleeping"] = False
        j.LLM_PROC["reason"] = None
        try:
            os.remove(os.path.join(j.DATA, "BRAIN.SLEEP"))
        except OSError:
            pass
        if emit:
            emit({"type": "say", "text": "☕ Загружаю мозг в "
                  "видеопамять..."})
        else:
            j.send("☕ Загружаю мозг в видеопамять...")
        ok = j.llm_start()
        j.journal("Мозг загружен в VRAM командой Шефа («проснись»): %s" % ok)
        return ("🧠 Мозг на месте." if ok else
                "⚠️ Не смог загрузить модель — глянь jarvis.log / "
                "llama.log.")
    return None


# ---------------------------------------------------------------- системный промпт веба

def web_sysmsg(j):
    """v3.30.0: системный промпт веб-чата — та же замена, что была в
    chat_server.SYSTEM_LOCAL, но теперь по соседству с циклом."""
    return j.SYSTEM.replace(
        "и общаешься с ним в Telegram",
        "и общаешься с ним в окне локального чата прямо на этом ПК"
    ).replace("Пиши простым текстом БЕЗ markdown",
              "Отвечай простым текстом БЕЗ markdown")


# ---------------------------------------------------------------- потоковая генерация

def llm_stream_chat(j, messages, max_tokens=800, temperature=0.7,
                    think=False):
    """Потоковая генерация для веб-чата (перенесена из chat_server
    без изменений логики: упаковка _pack_for_ctx, удержание <think>,
    досдача короткого хвоста)."""
    import urllib.request
    body = {"model": j.MODEL_ID,
            "messages": j._pack_for_ctx(list(messages), max_tokens),
            "max_tokens": max_tokens, "temperature": temperature,
            "top_p": 0.8,
            "chat_template_kwargs": {"enable_thinking": bool(think)},
            "stream": True}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        j.LLM_URL + "/v1/chat/completions", data=data,
        headers={"Content-Type": "application/json"})
    _hold, _in_think, _checked = [], False, False
    with urllib.request.urlopen(req, timeout=420) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            try:
                pj = json.loads(payload)
            except Exception:
                continue
            delta = (pj.get("choices") or [{}])[0].get("delta") or {}
            txt = delta.get("content") or ""
            if not txt:
                continue
            if not think:
                yield txt
                continue
            if not _checked:
                _hold.append(txt)
                st = "".join(_hold).lstrip()
                if st.startswith("<think"):
                    _in_think, _checked = True, True
                elif len(st) >= 12:
                    yield "".join(_hold)
                    _hold, _checked = [], True
                continue
            if _in_think:
                _hold.append(txt)
                joined = "".join(_hold)
                if "</think>" in joined:
                    tail = joined.split("</think>", 1)[1]
                    _in_think, _hold = False, []
                    if tail:
                        yield tail
                continue
            yield txt
    if _hold and not _in_think:
        yield "".join(_hold)


# ---------------------------------------------------------------- главный цикл

def brain_loop(j, ctx):
    """ЕДИНЫЙ ЦИКЛ МОЗГА (Task 182). Содержит все стражи обоих каналов:
    файл, мышь, BT, ссылка, claim, план, приказ, повторы, короткий ответ,
    язык, консилиум, авто-второе-мнение. Возвращает (final_text, fail) —
    fail=True означает «это честный отказ, история уже записана».

    ctx обязательные поля:
      text     — вопрос Шефа (как его видит мозг)
      mode     — think|cloud|big|consilium (smart_mode уже решён)
      sysmsg   — системное сообщение канала (dict role=system)
      emit(ev) — доставка события каналу; False = канал отвалился,
                 цикл останавливается (веб закрыл вкладку)
      log(msg) — журнал канала (jarvis.log / chat.log)
    опциональные:
      stream   — True: генерация потоковая (веб), начальный текст
                 уходит через emit({"type":"tok",...})  [нет — TG]
      hist_len — сколько сообщений истории после system (авто)
    """
    text = ctx["text"]
    mode = ctx["mode"]
    sysmsg = ctx["sysmsg"]
    emit = ctx.get("emit") or (lambda ev: True)
    clog = ctx.get("log") or j.log
    stream = bool(ctx.get("stream"))

    hist = j.hist_load()
    hist_msgs = j.hist_msgs(hist)
    if ctx.get("hist_len") is None:
        ctx["hist_len"] = len(hist_msgs)

    # v3.16.0: свежий вопрос — служебное напоминание мозгу
    utext = text
    if j.FRESH_RE.search(text):
        utext = (text +
                 "\n(Служебное напоминание: это свежий вопрос. Для новостей "
                 "вызови инструмент «новости», для курса валют/крипты — "
                 "«курсы», для прочего свежего — «интернет». Не отвечай без "
                 "данных.)")

    # v3.25.1: вопрос помечен "_q" — упаковщик не выбросит его НИКОГДА
    msgs = [sysmsg] + hist_msgs + [
        {"role": "user", "content": utext, "_q": 1}]
    _hist_len = len(msgs) - 2

    def _fit(ms):
        """v3.9.0/v3.20.0: жёсткий бюджет истории 8.5К симв. (без
        системного промпта); финальную упаковку под контекст делает
        _pack_for_ctx в llm_chat/llm_stream."""
        nonlocal _hist_len
        while (sum(len(m.get("content") or "")
                   if isinstance(m.get("content"), str) else 2500
                   for m in ms[1:]) > 8500
               and _hist_len > 0):
            ms.pop(1)
            _hist_len -= 1
        return ms

    def _gen(ms, think):
        """Генерация шага. Потоковая (веб) или целиком (TG)."""
        if not stream:
            return j.llm_chat(_fit(ms), think=think)
        # v3.14.5b: пустой ответ после думания — повтор без думания
        # с дописанным напоминанием в ПЕРВОЕ system (шаблон Qwen).
        for _attempt in (1, 2):
            buf, head, visible = [], "", None
            try:
                for tok in llm_stream_chat(
                        j, ms,
                        max_tokens=(int(j.CFG.get("llm_think_tokens", 2000))
                                    if think else 800),
                        think=think):
                    if visible is None:
                        head += tok
                        st = head.lstrip()
                        if st.startswith("{"):
                            visible = False
                        elif len(st) >= 8 or "\n" in st:
                            visible = True
                            emit({"type": "tok", "text": head})
                    elif visible:
                        emit({"type": "tok", "text": tok})
                    buf.append(tok)
            except Exception as e:
                # v3.8.4 ctx-guard: 400 «контекст переполнен» — сброс
                # старой истории (системный промпт и текущая цепочка
                # инструментов остаются) и повтор ШАГА, а не смерть хода
                if "HTTP 400" in str(e) and "context" in str(e).lower():
                    clog("ctx-guard: 400 (контекст переполнен) — сброс "
                         "истории, повтор шага")
                    ms[:] = [ms[0]] + ms[1 + ctx["hist_len"]:]
                    continue
                raise
            if visible is None and head:
                emit({"type": "tok", "text": head})
            ans = j._strip_think("".join(buf))
            if ans.strip() or not think:
                return ans
            # думали — а ответа нет: повтор без думания (v3.14.5b),
            # напоминание дописываем в первое system
            clog("пустой ответ после думания — повтор без думания")
            think = False
            if ms and ms[0].get("role") == "system":
                ms[0] = dict(ms[0])
                ms[0]["content"] = (
                    (ms[0].get("content") or "")
                    + "\n\nВАЖНО: не размышляй вслух и не используй тег "
                      "размышлений — отвечай сразу готовым текстом. Коротко, "
                      "по-русски.")
            else:
                ms.insert(0, {"role": "system", "content":
                              "Не размышляй вслух — отвечай сразу готовым "
                              "текстом. Коротко, по-русски."})
        return ans

    # v3.14.5: ДУМАЕТ ВСЕГДА — первый заход с размышлениями.
    # mode="glm" (ИИ-коллега через веб-API): БЕЗ думания на всех шагах —
    # так вёл себя старый веб-путь для GLM (Task 91), сохраняем.
    _think = mode in ("think", "consilium")
    ans = _gen(msgs, think=_think)
    called = set()
    _rep_key = None
    _rep_cnt = 0
    retried_claim = retried_file = retried_plan = False
    retried_order = retried_short = retried_mouse = False
    retried_link = retried_bt = False
    _order = bool(j.HANDS_ORDER_VERB_RE.search(text)
                  and j.HANDS_ORDER_CTX_RE.search(text))
    has_file = bool(j.FILE_MSG_RE.search(text) or j.FILE_PATH_RE.search(text))

    def _fail(txt, hist_note):
        j.hist_append(text, hist_note)
        return txt, True

    for _step in range(12):
        if not emit({"type": "waiting"}):
            return "", True
        tool = j.parse_tool(ans)
        if not tool:
            # файл-страж (v3.1.1): файл прислан, инструмент не вызван
            if has_file and not called and not retried_file:
                retried_file = True
                clog("file-guard: ответ о файле без чтения — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": j.FILE_FIX_MSG})
                ans = _gen(msgs, think=True)
                continue
            # мышь-страж (v3.14.3)
            if (j.MOUSE_NOW_RE.search(text)
                    and not (called & j.MOUSE_NOW_TOOLS)
                    and not retried_mouse):
                retried_mouse = True
                clog("mouse-guard: «где мышь» без инструмента — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": j.MOUSE_FIX_MSG})
                ans = _gen(msgs, think=True)
                continue
            # BT-страж (v3.25.3) — повтор без думания (Task 169)
            if (j.BT_Q_RE.search(text) and j.BT_A_RE.search(ans)
                    and not (called & j.BT_TOOLS) and not retried_bt):
                retried_bt = True
                clog("bt-guard: ответ про блютуз без инструмента — "
                     "перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": j.BT_FIX_MSG})
                ans = _gen(msgs, think=False)
                continue
            # ссылка-страж (v3.19.0) — раньше был ТОЛЬКО в TG
            _links = j.LINK_MSG_RE.findall(text)
            if _links and not (called & j.LINK_TOOLS) and not retried_link:
                retried_link = True
                _lnk = _links[0][:300]
                clog("link-guard: ссылка без открытия — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user",
                             "content": j.LINK_FIX_MSG % (_lnk, _lnk)})
                ans = _gen(msgs, think=True)
                continue
            # claim-страж (v3.1.0/v3.8.5)
            _claim_fix = j.claim_without_tool(ans, called)
            if _claim_fix:
                if retried_claim:
                    clog("claim-guard: ложь повторилась — честный отказ")
                    return _fail(
                        "⚠️ Тут я запнулся, Шеф: заявил действие, но не "
                        "выполнил его. Скажи ещё раз — сделаю как надо.",
                        "(заявил действие без инструмента)")
                retried_claim = True
                _kind = ("фантом" if _claim_fix is j.PHANTOM_FIX_MSG else
                         ("руки" if _claim_fix is j.HANDS_FIX_MSG
                          else "файлы/память"))
                clog("claim-guard(%s): заявлено без инструмента — "
                     "перезапрос" % _kind)
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": _claim_fix})
                ans = _gen(msgs, think=True)
                continue
            # план-страж (v3.8.2)
            if j.plan_without_tool(ans, called):
                if retried_plan:
                    clog("plan-guard: план повторился — отдаю ответ")
                    break
                retried_plan = True
                clog("plan-guard: обещание без инструмента — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": j.PLAN_FIX_MSG})
                ans = _gen(msgs, think=True)
                continue
            # приказ-страж (v3.8.6)
            if _order and not (called & j.HANDS_ACT_TOOLS) \
                    and not retried_order:
                retried_order = True
                clog("order-guard: приказ рук без инструмента — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content":
                             j.HANDS_ORDER_FIX_MSG})
                ans = _gen(msgs, think=True)
                continue
            break
        name, args, say = tool
        called.add(name)
        # страж повторов (v3.14.1)
        _k = name + "|" + json.dumps(args, sort_keys=True,
                                     ensure_ascii=False)
        if _k == _rep_key:
            _rep_cnt += 1
        else:
            _rep_key, _rep_cnt = _k, 1
        if _rep_cnt >= 6:
            clog("repeat-guard: 6 одинаковых вызовов — честный останов")
            return _fail(
                "⚠️ Я застрял, Шеф: шесть раз подряд одно и то же действие "
                "не даёт результата. Остановился, чтобы не молоть впустую. "
                "Скажи, что делать дальше — попробую другим путём (другие "
                "координаты, клавиатура, run_ps).",
                "(застрял на повторе одинакового действия)")
        if _rep_cnt >= 3:
            clog("repeat-guard: %d одинаковых вызовов — коррекция" % _rep_cnt)
            msgs.append({"role": "assistant", "content": ans})
            msgs.append({"role": "user", "content":
                         "Служебная проверка ЦИКЛА: ты уже %d раз вызываешь "
                         "тот же инструмент с теми же аргументами — "
                         "результат не изменится. Остановись и действуй "
                         "иначе: 1) вызови «скрин» или «область» и "
                         "ПОСМОТРИ, что реально на экране и что изменилось; "
                         "2) смени координаты или подход (клавиша, "
                         "элементы_окна, run_ps); 3) или честно ответь "
                         "Шефу, что не получилось, и предложи другой "
                         "путь." % _rep_cnt})
            ans = _gen(msgs, think=True)
            continue
        # v3.7.0: say — речь Шефу перед исполнением (русский/короткий)
        if say and (j._is_russian(say) or len(say.strip()) <= 40):
            if not emit({"type": "say", "text": "⚙️ " + say[:300]}):
                return "", True
        if name not in ("спать", "проснись"):
            emit({"type": "waiting"})
        res = j.tool_exec(name, args)
        if name == "спать":
            j.hist_append(text, "мозг выгружен из VRAM")
            return ((say + "\n") if say else "") + \
                "😴 Мозг выгружен из видеопамяти — VRAM свободна для игр. " \
                "«проснись» — верну обратно.", True

        if res == "SCREENSHOT":
            # v3.14.0: скрин — ПРОМЕЖУТОЧНЫЙ взгляд, не конец хода.
            # Каналу уходит фото; описание зрением — мозгу.
            path = j.take_shot()
            if not path:
                why = ("экран залочен (Win+L) — Windows прячет картинку"
                       if j._station_locked()
                       else "ошибка захвата, см. jarvis.log")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content":
                             "Результат инструмента «скрин»: НЕ удался — "
                             "%s. Продолжай другим путём (окно/элементы_"
                             "окна/run_ps) или честно ответь Шефу." % why})
                ans = _gen(msgs, think=True)
                continue
            emit({"type": "image", "path": path,
                  "caption": _shot_caption(j)})
            _del = not j.vision_available()
            desc = ""
            if not _del:
                try:
                    desc = j.llm_vision(path, ui=True)
                except Exception as e:
                    clog("vision ERR: %s" % e)
            try:
                os.remove(path)
            except OSError:
                pass
            if _del:
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content":
                             "Результат инструмента «скрин»: фото "
                             "отправлено Шефу, но зрение не загружено — "
                             "описать не могу. Продолжай без картинок "
                             "(элементы_окна/run_ps) или честно ответь "
                             "Шефу."})
            else:
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content":
                             "Результат инструмента «скрин» (фото уже ушло "
                             "Шефу).%s\nЧто вижу на экране:\n%s\n\n"
                             "Это ПРОМЕЖУТОЧНЫЙ взгляд — задачу Шефа "
                             "продолжай: следующий JSON (клик_элемент/"
                             "область/мышь/клавиша/печатать/элементы_окна) "
                             "или, если всё сделано, финальный ответ "
                             "по-русски обычным текстом. ВНИМАНИЕ: "
                             "координаты в описании ПРИБЛИЗИТЕЛЬНЫ (картинка "
                             "сжата) — для точного клика по кнопке вызови "
                             "«область» вокруг неё, там 1:1; после клика "
                             "обязательно проверь результат новым "
                             "скрин/область."
                             % (j._cursor_note(), desc or
                                "(не смог разобрать снимок — используй "
                                "«элементы_окна» или «мышь» по описанию)")})
            ans = _gen(msgs, think=True)
            continue

        emit({"type": "tool", "name": name, "result": str(res)[:2000]})
        msgs.append({"role": "assistant", "content": ans})
        # v3.25.1: результат инструмента — 2200 симв. (cap упаковщика)
        msgs.append({"role": "user", "content":
                     "Результат инструмента «%s»:\n%s\n\n"
                     "Если данных достаточно — ответь Шефу по-русски, "
                     "коротко и по делу, обычным текстом без JSON. Если "
                     "нужен ещё один инструмент — ответь снова одним "
                     "JSON-объектом."
                     % (name, str(res)[:2200])})
        ans = _gen(msgs, think=True)

    clean = j._strip_md(ans)
    # short-страж (v3.9.2) — раньше был ТОЛЬКО в TG
    if (3 <= len(clean.strip()) < 12
            and not clean.lstrip().startswith('{"tool"')
            and not retried_short):
        retried_short = True
        clog("short-guard: ответ оборвался (%r) — перезапрос" % clean[:40])
        msgs.append({"role": "assistant", "content": ans})
        msgs.append({"role": "user", "content":
                     "Твой прошлый ответ оборвался на полуслове. Ответь "
                     "Шефу ПОЛНОСТЬЮ: что именно ты видишь или собираешься "
                     "делать, и вызови нужный инструмент, если он нужен "
                     "(скриншот/зрение для того, что на экране)."})
        ans = _gen(msgs, think=True)
        clean = j._strip_md(ans)
    if len(clean.strip()) < 3 or clean.lstrip().startswith('{"tool"'):
        clog("brain_loop: дегенеративный ответ (%r) — честный финал"
             % clean[:60])
        return _fail(
            "⚠️ Я сделал много шагов, но не успел доделать до конца, Шеф. "
            "Скажи «продолжай» — доделаю с места, где остановился.",
            "(не успел доделать за лимит шагов — «продолжай»)")
    # языковой страж (v3.7.0, Task 168: повтор без думания)
    if not j._is_russian(clean):
        clog("lang-guard: ответ без русского (%r) — перезапрос" % clean[:60])
        j.journal("З5: ответ сорвался не на русский — перезапрос")
        msgs.append({"role": "assistant", "content": ans})
        msgs.append({"role": "user",
                     "content": j.LANG_FIX_MSG +
                     " Отвечай сразу готовым текстом, без размышлений."})
        ans2 = _gen(msgs, think=False)
        clean2 = j._strip_md(ans2)
        if j._is_russian(clean2) and len(clean2.strip()) >= 3:
            ans, clean = ans2, clean2
        else:
            return _fail(
                "⚠️ Сорвался тут на английский, Шеф — а по закону З5 говорю "
                "только по-русски. Переспроси, отвечу как положено.",
                "(ответ сорвался на английский)")
    # консилиум (v3.22.0) — теперь РАБОТАЕТ В ОБОИХ КАНАЛАХ
    if clean and j._cloud_ready():
        _verify = (mode == "consilium")
        if (not _verify and j._senior_auto() and mode == "think"
                and not j.PRIVATE_RE.search(text)
                and j.UNCERT_RE.search(clean)):
            _verify = True   # мозг сам сказал «не уверен»
        if _verify:
            emit({"type": "waiting"})
            v_ans, v_err = j.cloud_verify(text, clean)
            if v_ans:
                full = (clean + "\n\n🛰 " +
                        ("Старший брат проверил мой ответ"
                         if mode == "consilium" else
                         "Я был не уверен — переспросил у старших")
                        + j._bro_src() + ":\n\n" + j._strip_md(v_ans))
                j.hist_append(text, full[:1200])
                return full, False
            clog("КОНСИЛИУМ: старшие не ответили (%s) — остаюсь при своём"
                 % str(v_err)[:80])
    j.hist_append(text, clean)
    return clean or "…", False


# ---------------------------------------------------------------- старшие братья

def senior_answer(j, text, mode, hist=None):
    """Вопрос целиком старшему брату (cloud/big). Возвращает текст или
    None (провал — вызывающий решает, что дальше). Единая реализация
    для TG и веба (раньше — две копии с чуть разным текстом)."""
    hist = hist if hist is not None else j.hist_msgs(j.hist_load())
    return j.cloud_ask(j._cloud_question(text, hist), hist)


def senior_prefix(mode):
    """Заголовок ответа старшего для канала."""
    return ("🛰 Сложный вопрос — спросил у старшего брата"
            if mode == "big" else "🛰 Спросил у старших")


def asleep_seniors(j, text, mode):
    """Мозг спит (игра/«спать»), а вопрос cloud/consilium/big — старшие
    отвечают без VRAM. Возвращает текст ответа Шефу или None."""
    c_ans, c_err = j.cloud_ask(j._cloud_question(text, []), [])
    if c_ans:
        j.hist_append(text, "[старшие, мозг спал] " + c_ans[:900])
        return ("🛰 (локальный мозг спит — игра? Старшие"
                + j._bro_src() + " ответили так:)\n\n"
                + j._strip_md(c_ans))
    return None
