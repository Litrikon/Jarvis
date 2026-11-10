#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ДЖАРВИС v2.2 — персональный агент на ПК2 (ПК2).
Фаза 1: Telegram-пульт + мониторинг (сохранена полностью).
Фаза 2: МОЗГ — Qwen3.8-27B локально через llama-server (ROCm/HIP на RX 9070 XT):
  - свободное общение в Telegram: ЛЮБАЯ фраза идёт мозгу (не только ключевые слова)
  - инструменты по решению LLM (JSON-протокол), до 4 подряд
  - ИНТЕРНЕТ: поиск (DuckDuckGo) и чтение страниц
  - зрение: описание скриншотов (mmproj)
  - ДЕЙСТВИЯ: очистка диска от мусора, анализ «что можно перенести», перенос
    папок на другие диски, запуск/закрытие программ
  - «спать»/«проснись» — выгрузка модели из VRAM + ярлыки на рабочем столе
  - АВТОВЫГРУЗКА VRAM при запуске игр (Steam/RDR2/VK Play), возврат после игры

v3.0.0 «УЧЕНИК» (Task 94, 01.11.2026): обучаемость в духе Everything
Claude Code, но локально — скиллы в папке skills (умение = SKILL.md,
индекс в промпте, подгрузка инструментом «скилл»), память
memory/MEMORY.md («запомнить_факт»), самообучение («записать_скилл» —
себе новые умения и уроки по итогам задач).

v3.0.1 «ЗАКОНЫ ШЕФА» (Task 95, 02.11.2026): законы уровнем КОДА, а не
промпта — пароли и деньги не трогаю НИКОГДА (жёсткий отказ), необратимое
только после явного «да» Шефа (confirm); индекс скиллов до 60, полный
каталог — «скилл {"имя":"все"}».

v3.1.0 «ФАЙЛЫ» (Task 96, 02.11.2026): Шеф присылает файлы в Telegram —
документы, фото, медиа (раньше получали отлуп «только текст»); Джарвис
скачивает их в FILES_DIR\Входящие, читает текст (utf-8/utf-16/cp1251),
смотрит картинки зрением, превращает файл в скилл («скилл_из_файла»),
выгружает свои файлы в FILES_DIR (дефолт E:\\Downloads\\Jarvis, ключ
config.json files_dir) и отправляет файлы Шефу («отправить_файл»).

v3.14.0 «ГЛАЗА И РУКИ В ЦИКЛЕ» (Task 132, 08.11.2026, доклад Шефа
  «почему не изменяет настройки программ? почему останавливается на
  этапе скрин и что на нём?» + приказ «возьми и проверь что есть и
  работает, исправь; если надо зрение — дай; другие возможности дай»):
  (1) «скрин» больше НЕ обрывает ход — раньше вызов скрина мозгом
  ЗАВЕРШАЛ задачу (описание улетало Шефу как финальный ответ; живой
  цикл 07.11 21:45-22:01 — пять ходов подряд умерли на скрине, до
  кликов не дошло ни разу); теперь фото уходит Шефу, а UI-описание
  (кнопки/переключатели/координаты) возвращается мозгу как результат
  инструмента, цикл продолжается; бюджет шагов 8 -> 12; (2) НОВЫЕ
  ИНСТРУМЕНТЫ «элементы_окна» (UI Automation читает интерфейс КАК
  ТЕКСТ: имена кнопок/галочек/вкладок + состояния вкл/выкл) и
  «клик_элемент» (нажать ПО ИМЕНИ, без гадания по пикселям; сам
  активирует окно, проверяет состояние до/после); (3) правило 6
  промпта: настройки программ меняем САМИ до результата — «сделай
  сам» Шефу запрещено (приказ Шефа «у тебя есть все полномочия»);
  (4) зрение проверено живьём (mmproj читает картинку) и встроено
  в поток многошаговых задач.

v3.14.1 (Task 132, продолжение, живой e2e 08.11: модель 9 раз кликнула
  одни координаты (3348,2328 — за пределами экрана) без перепроверки —
  бюджет шагов сгорел): (1) СТРАЖ ПОВТОРОВ — 3 одинаковых вызова инструмента
  подряд = корректирующее сообщение (проверь скрином/смени подход), 6 =
  честная остановка без пустой молотьбы; (2) новый инструмент «область» —
  кроп куска экрана в ПОЛНОМ разрешении 1:1 (без сжатия 2.4x) для точного
  прицеливания по мелким кнопкам/тулбарам; (3) результат «скрин» теперь
  содержит подсказку про «область» и обязательную проверку после клика;
  (4) исчерпание бюджета шагов — честный финал «скажи продолжай» вместо
  «мозг запнулся».

v3.14.2 «КУРСОР ВИДЕН» (Task 133, 08.11.2026, доклад Шефа «как сделать
  чтобы на скрине было видно мышь — ИИ не понимает, где мышь сейчас»):
  Windows НИКОГДА не рисует курсор в скриншотах (ImageGrab/CopyFromScreen
  берут пиксели экрана БЕЗ аппаратного спрайта курсора) — ни Шеф, ни
  зрение не видели, где мышь. Теперь: (1) на КАЖДЫЙ скрин курсор
  ДОРИСОВЫВАЕТСЯ — красное перекрестие с чёрной окантовкой + подпись
  «МЫШЬ x,y» прямо на фото (читается и Шефом, и зрением после сжатия);
  (2) ТОЧНЫЕ координаты курсора читаются из ОС (GetCursorPos, физические
  пиксели виртуального стола) и возвращаются мозгу ТЕКСТОМ — в результате
  «скрин», в промпте зрения (ui=True) и в подписи фото; (3) «область»
  дорисовывает перекрестие, если курсор внутри фрагмента, и всегда
  сообщает его координаты; (4) «мышь»-«позиция» — мгновенный точный
  ответ «где мышь», без всякого скрина.

v3.14.4 «РУКИ ОБУЧЕНЫ» (Task 134, 08.11.2026, приказ Шефа «научи его
  движению мыши, нажатию кнопок и вводу текста в нужное место»):
  (1) «печатать» — новый аргумент «обойти_каретку":"да»: в WinUI-
  приложениях (Unigram/UWP) классической каретки НЕТ, и печать
  отказывала «без каретки не печатаю», хотя поле было в фокусе;
  теперь мозг может печатать, когда поле подтверждено (клик по
  UIA-точке «элементы_окна» или кроп-зрением) — win_ctl.type_text
  force=True (v3.7.4: сёрфит кареточный шлюз, проверка смены окна
  остаётся); (2) переписан скилл «мышь_и_окна»: координатный
  контракт, прицел по надёжности (UIA -> кроп 1:1 -> скрин),
  нейтральные вопросы зрению (наводящие — зрение поддакивает!),
  рецепты Калькулятор/Блокнот/Telegram-Unigram с точными
  координатами и граблями, замеры точности. Всё проверено живьём
  на 3 программах: движение 12/12 (0px), Калькулятор 7×8=56
  кликами по кнопкам, Блокнот 122 символа 1:1, Telegram: «Привет»
  доставлен в Избранное (клик по строке чата + поле + печать).

v3.14.3 «МЫШЬ-СТРАЖ» (Task 133, хотфикс после живого e2e 08.11): на вопрос
  «где сейчас мышь? посмотри скрином» мозг ответил «на координатах 3839, 0.
  На скриншоте видно...» БЕЗ ЕДИНОГО инструмента (реальная позиция мыши
  была другой — координаты выдуманы; ни один из стражей такое не ловил).
  Теперь вопрос о ТЕКУЩЕЙ позиции мыши/курсора (MOUSE_NOW_RE) без вызова
  «скрин»/«область»/«мышь» = один перезапрос с указанием точного рецепта
  (мышь-позиция или скрин), в TG и в веб-чате.

v3.14.0 «ГЛАЗА И РУКИ В ЦИКЛЕ» (Task 132, 08.11.2026, доклад Шефа
  «хватит экспериментов — оставляй только текстовую модель как
  изначально задумывалось, всё остальное — картинки, видео,
  кузнецов — удаляй»): генерация изображений ВЫРЕЗАНА ПОЛНОСТЬЮ —
  весь код ComfyUI/FLUX/RealVisXL и папка comfyui_rocm (~28,5 ГБ)
  удалены; промпт-кузнец Qwen2.5-3B на CPU удалён (модель стёрта;
  ночью 07.11 он съедал RAM — из-за этого мозг не поднялся после
  генерации); ген-команды честно отвечают «удалено»; сохранено
  всё текстовое: умный режим, старшие братья, поиск по странице,
  инструменты, зрение, голос, файлы.

v3.12.2 «ПОИСК НА СТРАНИЦЕ» (Task 130, 07.11.2026): (1) инструмент
  «найти_на_странице» — текст страницы по ссылке (HTTP) или прямо из
  открытого браузера (Ctrl+A/Ctrl/C -> буфер, фокус выводится из полей
  ввода через Ctrl+F/Esc) + точные строки по ключевым словам запроса;
  раньше Джарвис лишь описывал скриншот («что вижу»), и Шеф не мог
  найти фильм на руторе. (2) Промпт-кузнец: правило деталей + примеры —
  переносит КАЖДУЮ деталь заказа (живой сбой: «чёрную лошадь с
  крыльями в море» -> просто «A horse»); 3-й переводчик — облако.
  (3) Веб-чат: честный отказ на видео (раньше молчание).

v3.2.0 «ГЛАЗА И ГОЛОС» (Task 98, 02.11.2026): (1) зрение — честный опрос
  САМОГО llama-server (vision_available: пробный кадр в
  /v1/chat/completions, кэш 2 мин) — локальный флаг процесса врал, когда
  сервер с --mmproj стартовал ДРУГОЙ процесс; скрин/посмотреть_файл/
  /api/status теперь говорят правду. (2) ГОЛОС: asr_transcribe — локальный
  whisper.cpp (CPU) расшифровывает аудио/видео: инструмент
  «расшифровать_файл», голосовые Telegram, кнопка микрофона веб-чата
  (/api/asr); ffmpeg конвертирует mp3/ogg/webm в wav 16k.

v3.2.1 (Task 99) «СВЕРКА»: посмотреть_файл принимает «вопрос» — зрение
  отвечает по существу (выписать настройки параметр=значение, прочитать
  текст, найти отличие), а не общее описание; скилл «настройки_скриншота»
  учит сверять скриншот с реальными настройками ПК (зрение + run_ps +
  таблица различий; изменения — только с подтверждения Шефа по закону З3).

v3.6.0 «РОУТЕР» (Task 103, 02.11.2026): Шеф дал пароль роутера
  («Джарвису дай его») — доступ к Keenetic Racer через родной API
  (NDW4 SCRAM-рукопожатие, модуль router_api.py; пароль лежит в
  config.json и в публичный гит НЕ попадает). Инструмент «роутер»:
  статус / кто в сети / интернет — мгновенно и без браузера.
  Только чтение: перезагрузку роутера не делаем (оборвём интернет
  всему дому, включая себя). Закон З1 цел: пароль никто не вводит
  и не называет — авторизация происходит внутри модуля.

v3.7.0 «ЧЕСТНЫЕ РУКИ» (Task 104, 02.11.2026): ночь вскрыла, что
  мозг мазал координатами (путал логические/физические пиксели на
  4K@250%) и докладывал «нажал/закрыл» без проверки. Лечение уровнем
  КОДА: (1) win_ctl.py — каждое действие подтверждается чтением
  факта: позиция курсора читается назад после движения, закрытие
  окна проверяется исчезновением окна, фокус/свёрнутость/размер —
  чтением состояния; «OK … проверено» = правда, иначе честное «НЕ
  получилось»; (2) законы З5 (язык: с Шефом только по-русски) и
  З6 (честность: докладывать только подтверждённое); (3) языковой
  страж — финальный ответ без кириллицы перезапрашивается один раз;
  (4) скилл «мышь_и_окна» (координатный контракт: только физические
  пиксели скриншота, 0,0 = левый верхний угол).

v3.8.2 «ПРОВЕРКА РУК» (Task 68, 02.11.2026): живой аудит клавиатуры/мыши
  вскрыл два бага: (1) win_ctl.key_combo падал на ЛЮБОЙ букве/цифре —
  функции VkKeyW в user32.dll не существует, нужна VkKeyScanW («ctrl+t»
  и все буквенные хоткеи не работали); (2) мозг мог ответить «сейчас
  выполню: сначала активирую, затем наберу» ПРОСТЫМ ТЕКСТОМ без единого
  инструмента — трос claim-guard ловил только прошедшее время «сделал».
  Лечение: план-гард (plan_without_tool: ни одного инструмента + глагол
  действия от первого лица = один перезапрос), правило промпта №10
  («действие = сразу JSON»), type_text докладывает целевое окно и смену
  окна во время набора.

v3.15.0 «САМОУЧКА» (Task 136, 08.11.2026, доклад Шефа «Он что не умеет
  делать запросы по API, научи его или пусть сам научится вообще надо
  сделать ему самообучение, возможно при поиске в интернете или при
  удачном опыте»): (1) НОВЫЙ ИНСТРУМЕНТ «запрос» — прямой HTTP-запрос к
  ЛЮБОМУ API из самого Python (urllib, БЕЗ PowerShell): GET/POST/PUT/
  DELETE, заголовки (Bearer-ключи), тело, таймаут; вернёт код + тип +
  тело (JSON аккуратно разворачивается); адресовано живому сбою 08.11 —
  Джарвис не смог опросить Netdata (localhost:19999) через PowerShell и
  жаловался «PowerShell возвращает пустой ответ на все запросы»; промпт
  теперь прямо говорит: API опрашивай «запросом», а не curl/irm в PS.
  (2) run_ps СТАЛ ЧЕСТНЫМ: ps_run_diag — мозг видит exit-код, stderr
  (CLIXML-шум вычищается, текст ошибок вытаскивается) и причину
  таймаута, а не голое «(пусто)» (старый ps_run выбрасывал stderr —
  любая ошибка PS выглядела пустотой; внутренние вызовы не тронуты —
  их контракты по stdout сохранены). (3) САМООБУЧЕНИЕ «УРОКИ»:
  memory/lessons.json — после КАЖДОГО хода с 2+ инструментами или со
  сбоями автоматически пишется урок-опыт (задача → какие инструменты
  сработали/упали → итог); в системный промпт инъектируются до 4 самых
  РЕЛЕВАНТНЫХ уроков (совпадение слов запроса + новизна) — мозг видит
  свой собственный удачный и неудачный опыт и не повторяет грабли;
  поиск в интернете тоже попадает в уроки (запросы и URL видны в
  шагах); потокобезопасно (threading.local: TG и веб-чат не путаются).
  (4) веб-чат: файлы Джарвиса и свои вложения скачиваются прямо из
  сообщений (chat_server v3.15, события file + карточки-ссылки).

v3.16.0 «ГОЛОС ДЖАРВИСА» (Task 137, 10.11.2026, доклад Шефа «Джарвис
  отвечает что не умеет голосом и надо скачать ещё другие голоса, более
  натуральные и современные»): (1) функция «Ответь голосом» (приказ Шефа
  09.11, ранее жила только в невышедшей ветке v3.12.1) портирована на
  базу v3.15.0 — фраза «ответь голосом» в любом месте запроса, финальный
  ответ уходит ГОЛОСОВЫМ сообщением Telegram (piper → wav → ffmpeg opus
  48k → sendVoice), любой сбой = откат на текст, ответ Шефу не теряется;
  (2) МОЗГ ЗНАЕТ О ГОЛОСЕ — секция ГОЛОС в системном промпте + инструмент
  «голос» (список/переключить/скачать): живой сбой 10.11 — на вопрос о
  голосе мозг отвечал «не умею, надо скачать голоса» (в v3.15.0 функции
  не было, а промпт молчал); (3) ЧЕТЫРЕ ГОЛОСА (piper medium, русские):
  ирина (жен., текущий), денис/дмитрий/руслан (муж., новые, совместимость
  с движком piper 1.2.0 проверена в песочнице 10.11): «ответь голосом
  дениса» — разовый голос, «голос денис» — смена основного (живая правка
  config.json + mtime-подхват вторым процессом), «голоса» — список,
  «скачай голос руслан» — сам скачивает с HuggingFace (~63 МБ, поток);
  (4) веб-чат: серверная страховка вырезания фразы, событие "voice" в
  стриме, лимит озвучки 600 → 1000 символов, выбор голоса в /api/tts.

v3.17.0 «SILERO» (Task 138, 10.11.2026, приказ Шефа «Ставь silero
  последней версии, почему сразу не поставил, нужно максимально
  реалистичный голос»): движок речи piper -> SILERO v5_6_ru — последняя
  модель 5-й линейки (models.yml silero-models, проверена в песочнице
  10.11): автоударения, омографы, интонация вопросов и восклицаний,
  48 кГц, синтез на CPU быстрее realtime (~0,2 с на фразу): (1) ПЯТЬ
  ГОЛОСОВ одной моделью 141 МБ — ксения (жен., основной), ксеня и байя
  (жен.), евгений и айдар (муж.): «ответь голосом ксении» — разово,
  «голос евгений» — сменить основной; piper остался РЕЗЕРВОМ (денис/
  дмитрий/руслан/ирина): имя piper-голоса или сбой silero = тихий откат
  на piper, затем на текст — ответ Шефу не теряется; (2) УСТАНОВКА
  ЛЮБЫМ КАНАЛОМ: «поставь silero» / «скачай голос ксения» — сам ставит
  torch (pip, ~200 МБ), качает модель v5_6_ru.pt (141 МБ, .part-
  страховка), правит config.json (tts_engine/silero_model/silero_voice)
  и докладывает ГОЛОСОМ в новом тембре; + numpy в комплект установки
  (torch без него не конвертирует тензор в wav — живые грабли 10.11
  «Numpy is not available», тихий откат на piper); (3) ДЛИННЫЕ ОТВЕТЫ: silero не
  принимает >~1000 симв — текст режется на предложения/запятые/слова,
  аудио склеивается в один голос (тест: 1327 симв -> 88 с аудио за
  2,9 с); (4) ЛЕНИВАЯ ЗАГРУЗКА: модель поднимается при первом синтезе
  (~3 с) в каждом процессе, inference под замком (TG и веб-чат не
  путаются), torch импортируется только при голосе — бот стартует и без
  него; (5) /api/tts веб-чата переведён на общий jarvis.tts_wav (silero
  + фолбэк piper), &voice= понимает silero-имена; движок/голос меняются
  живой правкой config.json — оба процесса подхватывают по mtime.

Запуск: pythonw.exe jarvis.py [--hello]
"""
import json, os, sys, time, base64, subprocess, threading, traceback, re, shutil
import urllib.request, urllib.parse, urllib.error
import ctypes
try:  # v3.3.0: физические пиксели экрана — 4K@200% без виртуализации
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
LOGF = os.path.join(BASE, "jarvis.log")
CFGF = os.path.join(BASE, "config.json")
OFFF = os.path.join(DATA, "offset.txt")
SHOT = os.path.join(DATA, "shot.png")
HISTF = os.path.join(DATA, "history.json")
DIARYF = os.path.join(DATA, "diary.jsonl")  # v3.9.0: дневник вытесненных обменов
LLMLOG = os.path.join(BASE, "llama.log")
os.makedirs(DATA, exist_ok=True)

with open(CFGF, encoding="utf-8-sig") as f:  # utf-8-sig: терпим BOM от PowerShell
    CFG = json.load(f)
TOKEN = CFG["token"]
CHAT = str(CFG["chat_id"])
API = "https://api.telegram.org/bot" + TOKEN

# v3.8.1 «СВЯЗЬ»: Telegram через прокси на московском сервере. Прямые
# соединения с ПК2 плавали всю ночь 02.11 (IPv4-шум, IPv6 нет) — бот
# терял polling и ответы Шефу. Прокси живёт в config.json (tg_proxy),
# пароль не в гите и не называется (З1). Пусто = напрямую, как раньше.
TG_PROXY = (CFG.get("tg_proxy") or "").strip()
if TG_PROXY:
    TG_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler(
        {"http": TG_PROXY, "https": TG_PROXY}))
else:
    TG_OPENER = None

# v3.9.0 «ФОЛБЭК СВЯЗИ»: прокси — основной путь, но сервер может лечь —
# тогда Джарвис молчал бы совсем. Считаем ошибки подряд: 3 на прокси ->
# уходим напрямую; 6 напрямую (прямое исторически плавает) -> возврат
# на прокси. Успех обнуляет счётчик своего режима.
TG_MODE = {"direct": False, "pfail": 0, "dfail": 0}


def _tg_opener():
    if TG_OPENER and not TG_MODE["direct"]:
        return TG_OPENER
    return urllib.request

LLM_URL = CFG.get("llm_url", "http://127.0.0.1:1234")
MODEL_ID = CFG.get("model_id", "qwen3.8-27b")
LLAMA_EXE = CFG.get("llama_exe", r"D:\Jarvis\llama\llama-server.exe")
MODEL_PATH = CFG.get("model_path",
    r"C:\Users\USER\.cache\lm-studio\models\unsloth\Qwen3.8-27B-GGUF\Qwen3.8-27B-UD-Q3_K_XL.gguf")
MMPROJ = CFG.get("mmproj_path",
    r"C:\Users\USER\.cache\lm-studio\models\unsloth\Qwen3.8-27B-GGUF\mmproj-F16.gguf")
LLAMA_EXE_CPU = CFG.get("llama_exe_cpu", r"D:\Jarvis\llama_cpu\llama-server.exe")

# v3.2.0 «ГОЛОС»: локальный whisper.cpp (CPU) + ffmpeg для конвертации
ASR_EXE = CFG.get("asr_exe", r"D:\Jarvis\whisper\whisper-cli.exe")
ASR_MODEL = CFG.get("asr_model",
    r"D:\Jarvis\whisper\models\ggml-small.bin")
ASR_THREADS = str(CFG.get("asr_threads", 8))
FFMPEG_EXE = CFG.get("ffmpeg_exe", r"D:\Jarvis\ffmpeg\bin\ffmpeg.exe")

ALLOWED = {CHAT}
PENDING = {"action": None, "ts": 0}
BIRTH = time.time()
LLM_PROC = {"p": None, "sleeping": False, "starting": False, "vision": False,
            "reason": None}  # reason: None | "manual" | "game"
LLM_START_LOCK = threading.Lock()  # v2.2.1: атомарный старт мозга
GAME_STATE = {"unloaded_session": False}

# v3.0.0 «УЧЕНИК»: обучаемость — скиллы + память
SKILLSDIR = os.path.join(BASE, "skills")
MEMDIR = os.path.join(BASE, "memory")
MEMORYF = os.path.join(MEMDIR, "MEMORY.md")

# v3.1.0 «ФАЙЛЫ»: приём/выгрузка (Task 96). Дефолт — Загрузки на E:
# (реестр ПК2: shell:Downloads = E:\Downloads). Меняется config.json files_dir.
FILES_DIR = CFG.get("files_dir", r"E:\Downloads\Jarvis")
INCOMING = os.path.join(FILES_DIR, "Входящие")

# ---------------------------------------------------------------- инфраструктура

def log(msg):
    try:
        with open(LOGF, "a", encoding="utf-8") as f:
            f.write(time.strftime("[%d.%m.%Y %H:%M:%S] ") + msg + "\n")
        # v3.9.0: ротация jarvis.log — при 3 МБ остаётся хвост (2000
        # строк), голова уходит (приём mirror.jsonl из Task 89)
        if os.path.getsize(LOGF) > 3000000:
            with open(LOGF, encoding="utf-8") as f:
                tail = f.readlines()[-2000:]
            with open(LOGF, "w", encoding="utf-8") as f:
                f.writelines(tail)
    except Exception:
        pass

def journal(text):
    try:
        _dup = ""
        if text.startswith("Джарвис v"):
            # v3.10.1 (Task 128): записи истории версий — только ОДИН
            # раз (рестарты/ребуты больше не плодят дубли в журнале)
            _dup = base64.b64encode(text[:100].encode("utf-8")).decode()
        ps_run(r"""
$d=[Environment]::GetFolderPath('Desktop')+'\AI_Журнал.txt'
$stamp=Get-Date -Format 'dd.MM.yyyy HH:mm'
$e="`r`n[$stamp (местное)] ДЖАРВИС: """ + text.replace("'", "''").replace("\r", " ").replace("\n", " ") + r"""`r`n"
$dup='""" + _dup + r"""'
if ($dup -ne '') {
  if (Test-Path $d) {
    $needle=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($dup))
    if ([IO.File]::ReadAllText($d,[Text.Encoding]::UTF8).Contains($needle)) { exit 0 }
  }
}
[IO.File]::AppendAllText($d,$e,(New-Object Text.UTF8Encoding $false))
""")
    except Exception:
        pass

def ps_run(script, timeout=90):
    script = "[Console]::OutputEncoding=[Text.Encoding]::UTF8\r\n" + script
    b64 = base64.b64encode(script.encode("utf-16-le")).decode()
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-EncodedCommand", b64]
    r = subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=0x08000000)
    return r.stdout.decode("utf-8", "replace").strip()


def _ps_clean_stderr(s):
    """v3.15.0: из stderr PowerShell вычистить CLIXML-шум (прогресс-
    записи «Подготовка модулей…»), но ВЫТАЩИТЬ текст настоящих ошибок
    (в CLIXML они лежат в <S S="Error">…</S>)."""
    s = s or ""
    if "#< CLIXML" in s or "<Objs" in s:
        errs = re.findall(r'<S S="Error">(.*?)</S>', s, re.S)
        rest = [ln for ln in s.splitlines()
                if "#< CLIXML" not in ln and "<Objs" not in ln
                and "</Objs>" not in ln]
        keep = [e.strip() for e in errs if e.strip()] + \
               [r.strip() for r in rest if r.strip()]
        s = "\n".join(keep)
    return s.strip()[:900]


def ps_run_diag(script, timeout=90):
    """v3.15.0 «САМОУЧКА» (Task 136): как ps_run, но для МОЗГА — с
    exit-кодом, stderr и честной причиной таймаута. Живой сбой 08.11:
    любая ошибка PowerShell (например, Invoke-RestMethod к лежащему
    порту) уходит в stderr, старый ps_run возвращал «» и мозг видел
    «(пусто)» без причины — «PowerShell возвращает пустой ответ на все
    запросы». Внутренние вызовы (cmd_status и др.) остаются на ps_run:
    их контракты по stdout не меняются."""
    script = "[Console]::OutputEncoding=[Text.Encoding]::UTF8\r\n" + script
    b64 = base64.b64encode(script.encode("utf-16-le")).decode()
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-EncodedCommand", b64]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout,
                           creationflags=0x08000000)
    except subprocess.TimeoutExpired:
        return ("ВЫВОД ПУСТОЙ: PowerShell не ответил за %d с (таймаут) — "
                "команда зависла. Не повторяй её, действуй иначе (другая "
                "команда, инструмент «запрос» для HTTP)." % timeout)
    except FileNotFoundError:
        return "ВЫВОД ПУСТОЙ: powershell.exe не найден (PATH сломан?)"
    except Exception as e:
        return "ВЫВОД ПУСТОЙ: PowerShell не запустился (%s)" % e
    out = r.stdout.decode("utf-8", "replace").strip()
    err = _ps_clean_stderr(r.stderr.decode("utf-8", "replace"))
    if out and r.returncode == 0:
        return out
    bits = []
    if out:
        bits.append(out)
    if r.returncode != 0:
        bits.append("exit-код %d" % r.returncode)
    if err:
        bits.append("stderr: " + err)
    if not bits:
        bits.append("процесс завершился без единого байта вывода")
    return ("ВЫВОД ПУСТОЙ/С ОШИБКОЙ — вот причина (не «пусто» магически): "
            + " | ".join(bits))

def tg(method, params=None, timeout=40):
    url = API + "/" + method
    data = json.dumps(params or {}).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    via_proxy = bool(TG_OPENER) and not TG_MODE["direct"]
    try:
        with _tg_opener().open(req, timeout=timeout) as resp:
            r = json.loads(resp.read().decode())
        if via_proxy:
            TG_MODE["pfail"] = 0
        else:
            TG_MODE["dfail"] = 0
        return r
    except Exception:
        if TG_OPENER:
            if via_proxy:
                TG_MODE["pfail"] += 1
                if TG_MODE["pfail"] >= 3 and not TG_MODE["direct"]:
                    TG_MODE["direct"] = True
                    log("СВЯЗЬ: прокси молчит x%d — ухожу на прямое соединение"
                        % TG_MODE["pfail"])
            else:
                TG_MODE["dfail"] += 1
                if TG_MODE["dfail"] >= 6 and TG_MODE["direct"]:
                    TG_MODE["direct"] = False
                    TG_MODE["pfail"] = 0
                    log("СВЯЗЬ: прямое соединение плавает x%d — "
                        "возвращаюсь на прокси" % TG_MODE["dfail"])
        raise

def send(text, chat=None, voice=False, voice_name=None):
    """v2.3.0: до 4 попыток с паузами — сеть до Telegram плавает, ответы
    терялись (send ERR 10054 в момент, когда Шеф ждал ответ).
    v3.16.0 (Task 137) «ОТВЕТЬ ГОЛОСОМ»: voice=True — финальный ответ
    уходит ГОЛОСОВЫМ сообщением (silero/piper → ogg/opus → sendVoice); ответ
    длиннее 1000 символов: начало голосом, хвост — текстом. Любой сбой
    синтеза/конвертации/отправки = откат на обычный текст — ответ Шефа
    не теряется никогда."""
    if voice and text:
        _head, _tail = text[:1000], text[1000:]
        if send_voice(_head, chat, voice_name):
            if not _tail:
                return True
            text = ("🎙 (начало — голосом %s, выше ⬆)\n\n"
                    % voice_display(voice_name)) + _tail
        # провал голоса — катимся обычным текстом (ниже)
    last = None
    for _try in range(4):
        try:
            r = tg("sendMessage", {"chat_id": chat or CHAT, "text": text[:3900]})
            mirror_append("tg", "jarvis", text)  # v2.2.3: дубль в зеркало каналов
            return r
        except Exception as e:
            last = e
            time.sleep(2 + _try * 2)
    log("send ERR (4 попытки): %s" % last)
    return None

def send_photo(path, caption="", chat=None):
    try:
        boundary = "----JarvisBnd7MA4YWxk"
        with open(path, "rb") as f:
            content = f.read()
        body = b""
        body += ("--%s\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n%s\r\n"
                 % (boundary, chat or CHAT)).encode("utf-8")
        if caption:
            body += ("--%s\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n%s\r\n"
                     % (boundary, caption)).encode("utf-8")
        body += ("--%s\r\nContent-Disposition: form-data; name=\"photo\"; "
                 "filename=\"shot.png\"\r\nContent-Type: image/png\r\n\r\n"
                 % boundary).encode() + content + b"\r\n"
        body += ("--%s--\r\n" % boundary).encode()
        req = urllib.request.Request(API + "/sendPhoto", data=body,
                headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
        with _tg_opener().open(req, timeout=60) as resp:
            r = json.loads(resp.read().decode())
        mirror_append("tg", "jarvis", "\U0001F4F8 [фото] " + (caption or ""))
        return r
    except Exception as e:
        log("send_photo ERR: %s" % e)
        return None

def send_document(path, caption="", chat=None):
    """v3.1.0: отправить Шефу ЛЮБОЙ файл (sendDocument, multipart)."""
    try:
        boundary = "----JarvisBnd7MA4YWxk"
        with open(path, "rb") as f:
            content = f.read()
        body = b""
        body += ("--%s\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n%s\r\n"
                 % (boundary, chat or CHAT)).encode("utf-8")
        if caption:
            body += ("--%s\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n%s\r\n"
                     % (boundary, caption[:900])).encode("utf-8")
        body += ("--%s\r\nContent-Disposition: form-data; name=\"document\"; "
                 "filename=\"%s\"\r\nContent-Type: application/octet-stream\r\n\r\n"
                 % (boundary, os.path.basename(path))).encode("utf-8") + content + b"\r\n"
        body += ("--%s--\r\n" % boundary).encode()
        req = urllib.request.Request(API + "/sendDocument", data=body,
                headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
        with _tg_opener().open(req, timeout=180) as resp:
            r = json.loads(resp.read().decode())
        mirror_append("tg", "jarvis", "\U0001F4CE [файл] " + os.path.basename(path))
        return r
    except Exception as e:
        log("send_document ERR: %s" % e)
        return None

# ------------------------------------------------ v3.16.0 (Task 137) ГОЛОС

# Фраза-триггер: «ответь голосом» в ЛЮБОМ месте запроса (любой вариант
# глагола, любой регистр). Разделители вокруг фразы забираем с собой,
# НО «?»/«!» ПЕРЕД фразой оставляем вопросу («какая погода? Ответь
# голосом» -> «какая погода?»), а после фразы — забираем («Ответь
# голосом!» -> пусто). После фразы может стоять ИМЯ голоса:
# «ответь голосом дениса» -> разовый голос Денис.
VOICE_RE = re.compile(
    r'[\s,.;:\-—()«»"\']*(?:ответ(?:ить|ь|ьте)?|отвечай)'
    r'[\s,.;:\-—()«»"\']*голосом[\s,.;:!?\-—()«»"\']*',
    re.IGNORECASE)

# стем имени голоса -> каноническое имя (дениса/денис/денису -> денис).
# v3.17.0: ПОРЯДОК ВАЖЕН — «ксени» раньше «ксен» (ксению -> ксения,
# ксеню/ксеней -> ксеня)
VOICE_NAME_STEMS = {"ксени": "ксения", "ксен": "ксеня", "евген": "евгений",
                    "айдар": "айдар", "бай": "байя",
                    "дени": "денис", "дмитр": "дмитрий",
                    "руслан": "руслан", "ирин": "ирина"}
# silero v5_6_ru: пять живых голосов из ОДНОЙ модели (имя -> speaker)
SILERO_VOICES = {"ксения": "kseniya", "ксеня": "xenia", "евгений": "eugene",
                 "айдар": "aidar", "байя": "baya"}
# piper (резервный движок): имя -> slug файла голоса
VOICE_SLUGS = {"денис": "denis", "дмитрий": "dmitri",
               "руслан": "ruslan", "ирина": "irina"}

# «голос денис» / «поставь голос дениса» / «переключи голос на дениса»
VOICE_CMD_RE = re.compile(
    r"^(?:поставь|поставить|переключи|переключить|смени|сменить|включи|"
    r"включить|установи|установить|сделай)?\s*голос(?:\s+на)?\s+([а-яё]+)$",
    re.IGNORECASE)
VOICE_GET_RE = re.compile(
    r"^(?:скачай|скачать|загрузи|загрузить|подтяни|подтянуть)\s+голос\s+([а-яё]+)$",
    re.IGNORECASE)

# v3.17.0: «поставь silero» / «установи силеро» / «поставь движок silero»
SILERO_INSTALL_RE = re.compile(
    r"^(?:постав(?:ь|ить)?|установ(?:и|ить)?|скач(?:ай|ать)?|подтяни|"
    r"подтянуть)\s+(?:голос\s+|движок\s+|движок\s+голоса\s+|речи\s+)?"
    r"(?:silero|силеро|сильеро)(?:\s+.*)?$",
    re.IGNORECASE)

# откуда качаем недостающие piper-голоса (проверено 10.11 в песочнице:
# файлы ветки v1.0.0 читаются движком piper 1.2.0 без замен)
VOICE_HF = ("https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/"
            "ru/ru_RU/%s/medium/ru_RU-%s-medium")

# ---------------- v3.17.0 (Task 138) SILERO: движок речи ----------------
# последняя модель 5-й линейки: автоударения, омографы, интонация
# вопросов/восклицаний; 48 кГц; синтез на CPU быстрее realtime
SILERO_URL = "https://models.silero.ai/models/tts/ru/v5_6_ru.pt"
SILERO_MODEL_FN = "v5_6_ru.pt"
SILERO_MIN_BYTES = 100 * 1024 * 1024   # ~141 МБ; меньше 100 МБ = битый

_SI = {"lock": threading.Lock(), "model": None, "path": None, "err": ""}


def silero_model_target():
    """Куда ставим/ищем модель silero: config.json -> BASE/silero/."""
    p = str(CFG.get("silero_model") or "").strip()
    if p:
        return p
    return os.path.join(BASE, "silero", SILERO_MODEL_FN)


def silero_path():
    """Путь к модели, если файл на месте и цел. None = не установлен."""
    p = silero_model_target()
    try:
        if os.path.isfile(p) and os.path.getsize(p) >= SILERO_MIN_BYTES:
            return p
    except OSError:
        pass
    return None


def silero_engine_on():
    """Пробовать ли silero первым: движок не переключён на piper и модель
    на месте (нет torch поймается при загрузке — тихий откат на piper)."""
    if str(CFG.get("tts_engine") or "").strip().lower() == "piper":
        return False
    return silero_path() is not None


def silero_ready():
    """Полная готовность: модель + torch + numpy (для честных ответов
    Шефу; без numpy тензор не конвертируется в wav — грабли 10.11)."""
    if not silero_path():
        return False
    try:
        import torch  # noqa: F401
        import numpy  # noqa: F401
        return True
    except Exception:
        return False


def _silero_load():
    """Ленивая загрузка модели (один раз на процесс, ~3 с). None = сбой."""
    if _SI["model"] is not None and _SI["path"] == silero_path():
        return _SI["model"]
    with _SI["lock"]:
        if _SI["model"] is not None and _SI["path"] == silero_path():
            return _SI["model"]
        if _SI["err"] and _SI["path"] == silero_path():
            return None   # уже пробовали и не вышло — не молотим впустую
        try:
            import torch
            torch.set_num_threads(4)   # не съедаем все ядра Шефа
            p = silero_path()
            _SI["model"] = torch.package.PackageImporter(p) \
                .load_pickle("tts_models", "model")
            _SI["path"] = p
            _SI["err"] = ""
            log("silero: модель загружена (%.0f МБ)"
                % (os.path.getsize(p) >> 20))
            return _SI["model"]
        except Exception as e:
            _SI["err"] = str(e)[:200]
            _SI["path"] = silero_path()
            log("silero load ERR: %s" % _SI["err"])
            return None


def _tts_chunks(text, limit=550):
    """v3.17.0: silero не принимает длинный текст (~1000+ симв) — режем
    на предложения, затем запятые, затем слова; аудио склеиваем кусками."""
    sents = [s.strip() for s in re.split(r'(?<=[.!?…])\s+', str(text).strip())
             if s.strip()]
    pieces = []
    for s in sents:
        if len(s) <= limit:
            pieces.append(s)
            continue
        for c in re.split(r'(?<=[,;:])\s+', s):
            if len(c) <= limit:
                pieces.append(c)
                continue
            cur = ""
            for w in c.split(" "):
                if len(cur) + len(w) + 1 > limit:
                    if cur:
                        pieces.append(cur.strip())
                    cur = w
                else:
                    cur = (cur + " " + w).strip()
            if cur:
                pieces.append(cur.strip())
    chunks, cur = [], ""
    for p in pieces:
        if not p:
            continue
        if len(cur) + len(p) + 1 <= limit:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c.strip()]


def silero_wav(text, speaker, out=None):
    """v3.17.0: silero -> wav 48 кГц mono 16 бит. None = не вышло
    (вызывающий откатится на piper/текст)."""
    m = _silero_load()
    if not m:
        return None
    if out is None:
        out = os.path.join(DATA, "voice_tts_%d.wav" % threading.get_ident())
    try:
        chunks = _tts_chunks(text)
        if not chunks:
            return None
        with _SI["lock"]:   # inference — под одним замком на процесс
            audios = [m.apply_tts(text=ch, speaker=speaker,
                                  sample_rate=48000,
                                  put_accent=True, put_yo=True)
                      for ch in chunks]
        import torch
        full = torch.cat(audios) if len(audios) > 1 else audios[0]
        import wave
        pcm = (full.numpy().clip(-1, 1) * 32767).astype("<i2")
        with wave.open(out, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(48000)
            w.writeframes(pcm.tobytes())
        return out
    except Exception as e:
        log("silero_wav ERR: %s" % e)
        return None


def silero_download_model():
    """v3.17.0: скачать модель v5_6_ru (~141 МБ) с .part-страховкой.
    Возврат: (ok, пояснение)."""
    dst = silero_model_target()
    try:
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    except OSError as e:
        return False, str(e)[:150]
    try:
        if os.path.isfile(dst) and os.path.getsize(dst) >= SILERO_MIN_BYTES:
            return True, "уже скачана"
        log("silero: качаю модель %s" % SILERO_URL)
        tmp = dst + ".part"
        with urllib.request.urlopen(SILERO_URL, timeout=300) as r, \
                open(tmp, "wb") as f:
            total = 0
            while True:
                chunk = r.read(1 << 18)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
                if total % (20 << 20) < (1 << 18):
                    log("silero: %d МБ…" % (total >> 20))
                    journal("модель silero: %d из ~141 МБ" % (total >> 20))
        if os.path.getsize(tmp) < SILERO_MIN_BYTES:
            os.remove(tmp)
            return False, "файл модели подозрительно мал"
        os.replace(tmp, dst)
        journal("модель silero v5_6_ru скачана из интернета (%d МБ)"
                % (os.path.getsize(dst) >> 20))
        return True, "готово"
    except Exception as e:
        log("silero download ERR: %s" % e)
        return False, str(e)[:200]


def silero_install_async(chat, voice_name=None):
    """v3.17.0 (Task 138): полная установка silero в потоке — torch (pip,
    ~200 МБ) + модель v5_6_ru (141 МБ) + config.json. По готовности
    докладывает Шефу ГОЛОСОМ в новом тембре."""
    def _w():
        try:
            # 1) torch
            have_torch = False
            try:
                import torch  # noqa: F401
                have_torch = True
            except Exception:
                pass
            if not have_torch:
                send("⬇️ Ставлю torch — нейробиблиотеку для голоса "
                     "(~200 МБ). Самая долгая часть, до нескольких "
                     "минут…", chat)
                ok = False
                for args in ([sys.executable, "-m", "pip", "install",
                              "torch"],
                             [sys.executable, "-m", "pip", "install",
                              "torch", "--index-url",
                              "https://download.pytorch.org/whl/cpu"]):
                    try:
                        p = subprocess.run(args, timeout=2400,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT)
                        if p.returncode == 0:
                            ok = True
                            break
                        log("pip torch: код %s" % p.returncode)
                    except Exception as e:
                        log("pip torch ERR: %s" % e)
                try:
                    import torch  # noqa: F401
                    ok = True
                except Exception:
                    ok = False
                if not ok:
                    send("⚠️ torch не поставился (pip). Детали в jarvis.log. "
                         "Голос остался прежним — piper.", chat)
                    return
                send("✅ torch установлен.", chat)
            # 1б) numpy — torch БЕЗ него не конвертирует тензор в wav
            # (живые грабли 10.11: «silero_wav ERR: Numpy is not
            # available» -> тихий откат на piper); ставится один раз
            numpy_was = True
            try:
                import numpy  # noqa: F401
            except Exception:
                numpy_was = False
                send("⬇️ Доставляю numpy (~16 МБ) — без него torch не "
                     "отдаёт звук…", chat)
                try:
                    p = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "numpy"],
                        timeout=600, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)
                    if p.returncode != 0:
                        log("pip numpy: код %s\n%s" % (
                            p.returncode,
                            p.stdout.decode("utf-8", "replace")[-500:]))
                except Exception as e:
                    log("pip numpy ERR: %s" % e)
                try:
                    import numpy  # noqa: F401
                except Exception:
                    send("⚠️ numpy не поставился (pip). Детали в "
                         "jarvis.log.", chat)
                    return
            # 2) модель
            if not silero_path():
                send("⬇️ Качаю модель v5_6_ru (~141 МБ)…", chat)
            ok, info = silero_download_model()
            if not ok:
                send("⚠️ Модель silero не скачалась: %s. Скажи ещё раз "
                     "«поставь silero» — попробую заново." % info, chat)
                return
            # 3) конфиг (живая правка; второй процесс подхватит по mtime)
            nm = voice_name if voice_name in SILERO_VOICES else \
                (CFG.get("silero_voice")
                 if CFG.get("silero_voice") in SILERO_VOICES else "ксения")
            cfg_set("tts_engine", "silero")
            cfg_set("silero_model", silero_model_target())
            cfg_set("silero_voice", nm)
            _SI["err"] = ""   # разрешаем загрузку модели заново
            _SI["path"] = None
            journal("движок silero v5_6_ru установлен (голос: %s)" % nm)
            send("🎙 Silero встал! Теперь я говорю голосом %s — "
                 "слушай." % voice_display(nm), chat,
                 voice=True, voice_name=nm)
            if not numpy_was:
                send("ℹ️ numpy встал только что: если голос ещё "
                     "прежний — перезапусти меня (план задач "
                     "JarvisAgent), после перезапуска заговорю "
                     "новым голосом.", chat)
        except Exception as e:
            log("silero install ERR: %s" % e)
            send("⚠️ Установка silero споткнулась: %s — детали в "
                 "jarvis.log." % str(e)[:150], chat)
    threading.Thread(target=_w, daemon=True).start()


def _cfg_sync():
    """v3.16.0: подхват правок config.json из ДРУГОГО процесса (TG и веб-чат
    живут раздельно; смена голоса в одном должна дойти до второго —
    сверяем mtime и перечитываем)."""
    global CFG
    try:
        m = os.path.getmtime(CFGF)
        if m == CFG.get("_mtime"):
            return
        with open(CFGF, encoding="utf-8-sig") as f:
            fresh = json.load(f)
        if isinstance(fresh, dict):
            CFG["_mtime"] = m
            for k, v in fresh.items():
                CFG[k] = v
    except Exception:
        pass


def cfg_set(key, value):
    """v3.16.0: живая правка config.json (чтение-модификация-запись);
    второй процесс подхватит через _cfg_sync по mtime."""
    try:
        with open(CFGF, encoding="utf-8-sig") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False
        data[key] = value
        with open(CFGF, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        CFG.pop("_mtime", None)
        _cfg_sync()
        return True
    except Exception as e:
        log("cfg_set ERR: %s" % e)
        return False


def voices_dir():
    """Папка голосов piper (рядом с текущим голосом)."""
    v = str(CFG.get("piper_voice") or "")
    if v:
        return os.path.dirname(v)
    return os.path.join(os.path.dirname(str(CFG.get("piper_exe") or "")),
                        "voices")


def _piper_catalog():
    """{имя: путь} — скачанные piper-голоса в папке voices."""
    cat = {}
    try:
        d = voices_dir()
        if os.path.isdir(d):
            for fn in os.listdir(d):
                m = re.match(r"ru_RU-([A-Za-z]+)-medium\.onnx$", fn)
                if m:
                    slug = m.group(1).lower()
                    nm = next((k for k, s in VOICE_SLUGS.items()
                               if s == slug), slug)
                    cat[nm] = os.path.join(d, fn)
    except Exception:
        pass
    return cat


def voice_catalog():
    """v3.17.0: {имя: 'silero' | путь} — ВСЕ доступные голоса: silero
    (модель на месте = все пять сразу) + скачанные piper."""
    cat = {}
    if silero_path():
        for nm in SILERO_VOICES:
            cat[nm] = "silero"
    cat.update(_piper_catalog())
    return cat


def voice_cur_name():
    """v3.17.0: имя текущего основного голоса (по движку из конфига)."""
    if silero_engine_on():
        nm = str(CFG.get("silero_voice") or "").strip().lower()
        if nm in SILERO_VOICES:
            return nm
        for stem, full in VOICE_NAME_STEMS.items():
            if nm.startswith(stem) and full in SILERO_VOICES:
                return full
        return "ксения"
    cur = str(CFG.get("piper_voice") or "")
    m = re.match(r"ru_RU-([A-Za-z]+)-medium\.onnx$",
                 os.path.basename(cur))
    if m:
        slug = m.group(1).lower()
        return next((k for k, s in VOICE_SLUGS.items() if s == slug), slug)
    return "ирина"


def voice_display(name):
    """«денис» -> «Денис»; None -> имя текущего."""
    return str(name or voice_cur_name()).capitalize()


def voice_split(text):
    """v3.16.0 (Task 137): «ответь голосом [имя]» в любом месте запроса —
    вырезаем фразу вместе с разделителями. Возврат: (чистый_текст,
    был_приказ_голосом, имя_голоса_или_None)."""
    if not text or not VOICE_RE.search(text):
        return text, False, None
    rest = VOICE_RE.sub("\x00", text)
    name = None
    m = re.search(r'\x00\s*(ксени|ксен|евген|айдар|бай|дени|дмитр|'
                  r'руслан|ирин)[а-яё]*[\s,.;:!?\-—()«»]*', rest,
                  re.IGNORECASE)
    if m:
        name = VOICE_NAME_STEMS.get(m.group(1).lower())
        rest = rest[:m.start()] + rest[m.end():]
    rest = rest.replace("\x00", " ")
    return re.sub(r"[ \t]{2,}", " ", rest).strip(), True, name


def tts_wav(text, voice_name=None, timeout=180):
    """v3.17.0 (Task 138): текст -> wav. Основной движок silero v5_6_ru
    (ксения/ксеня/евгений/айдар/байя), резерв piper (денис/дмитрий/
    руслан/ирина). voice_name — русское имя (None = основной голос).
    Возврат: путь к wav или None (ни один движок не ответил)."""
    _cfg_sync()   # голос/движок могли сменить в другом процессе
    cur = voice_cur_name()
    name = str(voice_name or cur or "").strip().lower()
    # 1) silero: явное silero-имя (даже при движке piper) или основной
    #    silero-голос; нет модели/torch = тихо катимся дальше
    if (name in SILERO_VOICES or (not voice_name and silero_engine_on())):
        spk = SILERO_VOICES.get(name) or SILERO_VOICES.get(cur) \
            or "kseniya"
        wav = silero_wav(text, spk)
        if wav:
            return wav
        log("tts: silero не справился — пробую piper")
    # 2) piper (имя piper-набора или основной piper-голос)
    exe = CFG.get("piper_exe")
    voice = None
    if voice_name and name in VOICE_SLUGS:
        voice = _piper_catalog().get(name)
    if not voice:
        voice = CFG.get("piper_voice")
    if exe and voice and os.path.isfile(exe) and os.path.isfile(voice):
        out = os.path.join(DATA, "voice_tts_%d.wav" % threading.get_ident())
        try:
            p = subprocess.run([exe, "--model", voice, "--output_file", out],
                               input=text.encode("utf-8"),
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=timeout)
            if p.returncode == 0 and os.path.isfile(out) \
                    and os.path.getsize(out) > 200:
                return out
            log("tts: piper не удался (код %s)" % p.returncode)
        except Exception as e:
            log("tts piper ERR: %s" % e)
    # 3) имя не silero-голоса, но silero жив — основным silero-голосом
    if voice_name and name not in SILERO_VOICES and silero_engine_on():
        wav = silero_wav(text, SILERO_VOICES.get(cur) or "kseniya")
        if wav:
            return wav
    log("tts: ни silero, ни piper не ответили — голос невозможен")
    return None


def send_voice(text, chat=None, voice_name=None):
    """v3.16.0 (Task 137): голосовое сообщение Telegram.
    piper -> wav -> ffmpeg (libopus 48k) -> sendVoice.
    Успех = True; любой сбой = False (send откатится на текст).
    Сказанное остаётся в истории: зеркало несёт текст голосового."""
    wav = ogg = None
    try:
        wav = tts_wav(text, voice_name)   # v3.17.0: имя -> движок сам
        if not wav:
            return False
        ff = CFG.get("ffmpeg_exe")
        if not (ff and os.path.isfile(ff)):
            log("send_voice: ffmpeg не найден — откат на текст")
            return False
        ogg = wav[:-4] + ".ogg"
        p = subprocess.run([ff, "-y", "-i", wav, "-c:a", "libopus",
                            "-b:a", "48k", "-ar", "48000", ogg],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=120)
        if p.returncode != 0 or not os.path.isfile(ogg) \
                or os.path.getsize(ogg) < 200:
            log("send_voice: ffmpeg не сделал ogg (код %s) — откат"
                % p.returncode)
            return False
        with open(ogg, "rb") as fh:
            content = fh.read()
        boundary = "----JarvisBnd7MA4YWxk"
        body = ("--%s\r\nContent-Disposition: form-data; "
                "name=\"chat_id\"\r\n\r\n%s\r\n"
                % (boundary, chat or CHAT)).encode("utf-8")
        body += ("--%s\r\nContent-Disposition: form-data; "
                 "name=\"voice\"; filename=\"voice.ogg\"\r\n"
                 "Content-Type: audio/ogg\r\n\r\n"
                 % boundary).encode() + content + b"\r\n"
        body += ("--%s--\r\n" % boundary).encode()
        req = urllib.request.Request(API + "/sendVoice", data=body,
                headers={"Content-Type": "multipart/form-data; boundary=%s"
                         % boundary})
        with _tg_opener().open(req, timeout=90) as resp:
            r = json.loads(resp.read().decode())
        if not r.get("ok"):
            log("send_voice: Telegram отказал: %s" % str(r)[:200])
            return False
        mirror_append("tg", "jarvis",
                      "🎙 (голосом %s): %s" % (voice_display(voice_name),
                                               text[:800]))
        journal("голосовой ответ Шефу: %d симв (opus 48k, голос %s)"
                % (len(text), voice_display(voice_name)))
        return True
    except Exception as e:
        log("send_voice ERR: %s" % e)
        return False
    finally:
        for _p in (wav, ogg):   # временные файлы — в любом исходе
            if _p:
                try:
                    os.remove(_p)
                except OSError:
                    pass


def voice_download(name):
    """v3.16.0: скачать голос с HuggingFace в папку voices
    (~63 МБ onnx + json). Возврат: (ok, пояснение)."""
    slug = VOICE_SLUGS.get(name)
    if not slug:
        return False, "неизвестный голос «%s»" % name
    d = voices_dir()
    try:
        os.makedirs(d, exist_ok=True)
    except OSError as e:
        return False, str(e)[:150]
    onnx = os.path.join(d, "ru_RU-%s-medium.onnx" % slug)
    js = onnx + ".json"
    try:
        for url, dst in ((VOICE_HF % (slug, slug), onnx),
                         ((VOICE_HF % (slug, slug)) + ".json", js)):
            if os.path.isfile(dst) and os.path.getsize(dst) > 1000:
                continue
            log("голос %s: качаю %s" % (name, url))
            tmp = dst + ".part"
            with urllib.request.urlopen(url, timeout=120) as r, \
                    open(tmp, "wb") as f:
                total = 0
                while True:
                    chunk = r.read(1 << 18)
                    if not chunk:
                        break
                    f.write(chunk)
                    total += len(chunk)
                    if total % (10 << 20) < (1 << 18):
                        log("голос %s: %d МБ…" % (name, total >> 20))
            if os.path.getsize(tmp) < 50000:
                os.remove(tmp)
                return False, "файл голоса подозрительно мал"
            os.replace(tmp, dst)
        journal("голос «%s» скачан из интернета" % name)
        return True, "готово"
    except Exception as e:
        log("voice_download ERR: %s" % e)
        return False, str(e)[:200]


def voice_download_async(name, chat):
    """Скачивание голоса в потоке — бот не замирает; по готовности
    голос сам доложивает Шефу (голосовым сообщением в новом голосе)."""
    def _w():
        ok, info = voice_download(name)
        if ok:
            cfg_set("piper_voice", voice_catalog().get(name)
                    or CFG.get("piper_voice"))
            send("🎙 Голос %s скачан и включён. Слушаю."
                 % voice_display(name), chat, voice=True, voice_name=name)
        else:
            send("⚠️ Не вышло скачать голос %s: %s"
                 % (voice_display(name), info), chat)
    threading.Thread(target=_w, daemon=True).start()
    return None


def voices_help():
    """v3.17.0: список голосов для команды «голоса»."""
    _cfg_sync()
    cat = voice_catalog()
    cur = voice_cur_name()
    lines = ["🎙 Мои голоса (движок %s, всё локально):"
             % ("silero v5_6 — самые натуральные" if silero_engine_on()
                else "piper")]
    for nm in sorted(cat):
        lines.append("%s %s%s"
                     % ("★" if nm == cur else "•", voice_display(nm),
                        " (жен.)" if nm in ("ксения", "ксеня", "байя",
                                            "ирина") else " (муж.)"))
    if not cat:
        lines.append("(голосов нет — скажи «поставь silero»)")
    if not silero_path():
        lines.append("")
        lines.append("⚙️ Движок silero (голоса заметно живее: ксения, "
                     "ксеня, байя, евгений, айдар) не установлен — "
                     "скажи «поставь silero», я всё сделаю сам.")
    can = [nm for nm in VOICE_SLUGS if nm not in cat]
    if can:
        lines.append("Piper можно скачать: " + ", ".join(can))
    lines.append("")
    lines.append("«ответь голосом …» — мой ответ голосом (разово);")
    lines.append("«ответь голосом евгения …» — разово другим голосом;")
    lines.append("«голос ксения» — сменить основной.")
    return "\n".join(lines)


def voice_switch_cmd(word):
    """v3.16.0: смена основного голоса по команде Шефа. v3.17.0:
    silero-имя переключает движок на silero, piper-имя — на piper.
    Возврат: (текст, имя_нового_голоса или None)."""
    _cfg_sync()
    w = str(word or "").strip().lower()
    name = None
    for stem, full in VOICE_NAME_STEMS.items():
        if w.startswith(stem):
            name = full
            break
    cat = voice_catalog()
    if not name:
        return ("Не понял голос «%s». Silero: %s; piper: %s."
                % (word, ", ".join(SILERO_VOICES),
                   ", ".join(VOICE_SLUGS)), None)
    if name in SILERO_VOICES:
        if not silero_path():
            return ("Голос %s живёт в движке silero — он ещё не "
                    "установлен. Скажи «поставь silero» — установлю сам "
                    "(torch ~200 МБ + модель 141 МБ)."
                    % voice_display(name), None)
        if name == voice_cur_name() and silero_engine_on():
            return ("Голос %s и так основной." % voice_display(name), name)
        if not (cfg_set("tts_engine", "silero")
                and cfg_set("silero_voice", name)):
            return ("Не смог записать выбор в config.json — "
                    "смотри jarvis.log.", None)
        journal("основной голос переключён по команде Шефа (silero): %s"
                % name)
        return ("🎙 Основной голос теперь %s (silero). Слушаю."
                % voice_display(name), name)
    # piper-имя
    if not cat.get(name):
        return ("Голос %s ещё не скачан (piper). Скажи «скачай голос %s» "
                "— подтяну из интернета (~63 МБ)."
                % (voice_display(name), name), None)
    if name == voice_cur_name() and not silero_engine_on():
        return ("Голос %s и так основной." % voice_display(name), name)
    if not (cfg_set("tts_engine", "piper")
            and cfg_set("piper_voice", cat[name])):
        return ("Не смог записать выбор в config.json — смотри jarvis.log.",
                None)
    journal("основной голос переключён по команде Шефа (piper): %s" % name)
    return ("🎙 Основной голос теперь %s (piper). Слушаю."
            % voice_display(name), name)


def tool_voice(args):
    """v3.16.0 (Task 137): инструмент мозга «голос» — список/переключить/
    скачать. v3.17.0: + установка движка silero. Мозг вызовет сам, когда
    Шеф просит голос погромче/потеплее/поестественнее."""
    _cfg_sync()
    what = str(args.get("что") or args.get("what") or args.get("действие")
               or "").strip().lower()
    name = str(args.get("имя") or args.get("name") or args.get("голос")
               or "").strip().lower()
    if name:
        for stem, full in VOICE_NAME_STEMS.items():
            if name.startswith(stem):
                name = full
                break
    cat = voice_catalog()
    cur = voice_cur_name()
    if what in ("установить", "install", "движок", "silero", "силеро"):
        if silero_ready():
            return ("silero уже установлен и работает; голоса: %s; "
                    "основной: %s" % (", ".join(SILERO_VOICES),
                                      voice_display(cur)))
        silero_install_async(CHAT, name if name in SILERO_VOICES else None)
        return ("запустил установку silero (torch ~200 МБ + модель "
                "141 МБ, несколько минут); по готовности сам доложу Шефу "
                "голосом. Скажи Шефу, что ставлю")
    if what in ("скачать", "download", "загрузить"):
        if name in SILERO_VOICES:
            if silero_ready():
                return ("голоса silero уже установлены (все пять сразу: "
                        "%s) — могу переключить основной на %s"
                        % (", ".join(SILERO_VOICES),
                           voice_display(name)))
            silero_install_async(CHAT, name)
            return ("ставлю движок silero с голосом %s (torch ~200 МБ + "
                    "модель 141 МБ); по готовности доложу Шефу голосом"
                    % voice_display(name))
        if not name or name not in VOICE_SLUGS:
            return ("укажи имя голоса: silero — %s; piper — %s"
                    % (", ".join(SILERO_VOICES), ", ".join(VOICE_SLUGS)))
        if cat.get(name):
            return ("голос %s уже скачан — могу переключить"
                    % voice_display(name))
        voice_download_async(name, CHAT)
        return ("скачиваю голос %s (~63 МБ из интернета, пару минут); "
                "по готовности сам доложу Шефу голосовым сообщением"
                % voice_display(name))
    if what in ("переключить", "поставить", "сменить", "включить", "switch") \
            or (name and not what):
        if not name:
            return "укажи имя: " + ", ".join(sorted(cat) or VOICE_SLUGS)
        msg, ok = voice_switch_cmd(name)
        if ok:
            return ("OK: " + msg + " Скажи Шефу, что голос сменился, "
                    "и предложи проверить фразой «ответь голосом»")
        return msg
    # список (по умолчанию)
    lines = ["основной голос: %s (движок %s)"
             % (voice_display(cur),
                "silero v5_6" if silero_engine_on() else "piper")]
    for nm in sorted(cat):
        lines.append("- %s%s" % (voice_display(nm),
                                 " (основной)" if nm == cur else ""))
    if not silero_path():
        lines.append("silero (самые натуральные голоса: %s) не установлен "
                     "— скажи Шефу «поставь silero»"
                     % ", ".join(SILERO_VOICES))
    can = [nm for nm in VOICE_SLUGS if nm not in cat]
    if can:
        lines.append("piper можно скачать: " + ", ".join(can))
    return "\n".join(lines)


def typing(chat=None):
    try:
        tg("sendChatAction", {"chat_id": chat or CHAT, "action": "typing"})
    except Exception:
        pass

# ---------------------------------------------------------------- мозг: llama-server

def http_json(url, payload, timeout=180):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def llm_health(timeout=4):
    try:
        with urllib.request.urlopen(LLM_URL + "/v1/models", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


# v3.2.0: 320x320 серый PNG — пробный кадр для опроса зрения сервера.
# (64x64 сервер отвергает HTTP 400 — у препроцессора mmproj минимум по
# размеру; 320x320 проверен живым тестом — принимается.)
_PROBE_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAUAAAAFACAYAAADNkKWqAAAAAXNSR0IArs4c6QAAAARnQU1BAACx"
    "jwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAQsSURBVHhe7dQxAQAwDICwSq/z9Z8FcuRBALO7"
    "D6Bo/gBQYYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkg"
    "kGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECW"
    "AQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYI"
    "ZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBl"
    "gECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgEC"
    "WQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZ"
    "IJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBA"
    "lgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkG"
    "CGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQ"
    "ZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYB"
    "AlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghk"
    "GSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWA"
    "QJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZ"
    "BghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkg"
    "kGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECW"
    "AQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYI"
    "ZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBl"
    "gECWAQJZBghkGSCQZYBAlgECWQYIZBkgkGWAQJYBAlkGCGQZIJBlgECWAQJZBghkGSCQZYBAlgEC"
    "WQYIZBkgkGWAQJYBAlkHk42qe/5OnaoAAAAASUVORK5CYII="
)
_VISION_CACHE = {"ok": None, "ts": 0}


def vision_available(force=False, ttl=120):
    """v3.2.0: умеет ли ТЕКУЩИЙ llama-server смотреть картинки (mmproj).
    Локальный флаг LLM_PROC["vision"] врёт, когда сервер стартовал ДРУГОЙ
    процесс (агент) с --mmproj, а этот процесс (веб-чат) лишь увидел
    чужой живой /health. Поэтому спрашиваем сам сервер пробным кадром;
    ответ кэшим на ttl сек (зеркалим в LLM_PROC для совместимости)."""
    if not force and _VISION_CACHE["ok"] is not None \
            and time.time() - _VISION_CACHE["ts"] < ttl:
        return _VISION_CACHE["ok"]
    ok = False
    if llm_health():
        try:
            body = {"model": MODEL_ID, "max_tokens": 4, "temperature": 0.0,
                    "messages": [{"role": "user", "content": [
                        {"type": "image_url", "image_url": {
                            "url": "data:image/png;base64," + _PROBE_PNG_B64}},
                        {"type": "text", "text": "ок"}]}]}
            http_json(LLM_URL + "/v1/chat/completions", body, timeout=90)
            ok = True
        except Exception:
            ok = False
    _VISION_CACHE.update(ok=ok, ts=time.time())
    LLM_PROC["vision"] = ok
    return ok

def _llm_attempts():
    """Попытки запуска: GPU+зрение -> GPU -> CPU-аварийный.
    -np 1 обязателен: иначе сборка создаёт 4 слота и съедает VRAM/RAM."""
    ngl = str(CFG.get("llm_ngl", "99"))
    ctx = str(CFG.get("llm_ctx", "8192"))
    vis = bool(CFG.get("llm_vision", True))
    slots = str(CFG.get("llm_slots", "1"))
    # v3.8.4: KV-кэш квантованный (q8_0) + flash-attention — освобождает
    # примерно половину KV-памяти, что позволило поднять контекст с 8192
    # до 12288 без роста VRAM (модель 13.1 ГБ + mmproj + KV@q8_0 влезают
    # в 16 ГБ с запасом). Живой Е2Э: 8192 переполнялся на цепочках
    # инструментов («request exceeds context size» -> HTTP 400 -> обрыв).
    common = ["--host", "127.0.0.1", "--port", "1234", "-a", MODEL_ID,
              "-c", ctx, "-np", slots, "-fa", "on",
              "-ctk", "q8_0", "-ctv", "q8_0"]
    tail = ["--threads", str(CFG.get("llm_threads", "6"))]
    attempts = []
    if vis and os.path.exists(MMPROJ):
        attempts.append({"name": "GPU+зрение", "vision": True,
                         "args": [LLAMA_EXE, "-m", MODEL_PATH, "--mmproj", MMPROJ,
                                  "-ngl", ngl] + tail + common})
    attempts.append({"name": "GPU", "vision": False,
                     "args": [LLAMA_EXE, "-m", MODEL_PATH, "-ngl", ngl] + tail + common})
    if ngl != "0":
        attempts.append({"name": "CPU-аварийный", "vision": False,
                         "args": [LLAMA_EXE_CPU, "-m", MODEL_PATH, "-ngl", "0",
                                  "--threads", "6"] + common})
    return attempts

def llm_start():
    if llm_health():
        LLM_PROC["sleeping"] = False
        return True
    with LLM_START_LOCK:
        if LLM_PROC["starting"]:
            return False
        LLM_PROC["starting"] = True
    _gflag = os.path.join(DATA, "BRAIN.SLEEP")
    if os.path.exists(_gflag):
        try:
            with open(_gflag) as f:
                LLM_PROC["reason"] = (f.read().strip() or "manual")[:20]
        except Exception:
            LLM_PROC["reason"] = "manual"
        LLM_PROC["sleeping"] = True
        LLM_PROC["starting"] = False
        log("llm_start: skip - brain unloaded on purpose (BRAIN.SLEEP)")
        return False
    try:
        # считаю только мозг (--port 1234); посторонние llama-server
        # (например, старые) не трогаю
        _n = int(ps_run("(Get-CimInstance Win32_Process -Filter \"Name='llama-server.exe'\" | "
                        "Where-Object {$_.CommandLine -match '--port 1234'} | "
                        "Measure-Object).Count", 30).strip() or 0)
    except Exception:
        _n = 0
    if _n > 0:
        for _ in range(50):
            if llm_health():
                LLM_PROC["sleeping"] = False
                LLM_PROC["starting"] = False
                return True
            time.sleep(3)
        ps_run("Get-CimInstance Win32_Process -Filter \"Name='llama-server.exe'\" | "
               "Where-Object {$_.CommandLine -match '--port 1234'} | "
               "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }", 30)
    try:
        for att in _llm_attempts():
            log("llm_start: попытка «%s»" % att["name"])
            try:
                # v3.9.0: ротация llama.log — старый процесс мёртв,
                # файл свободен; храним одно поколение (.old)
                try:
                    if os.path.getsize(LLMLOG) > 3000000:
                        try:
                            os.remove(LLMLOG + ".old")
                        except OSError:
                            pass
                        os.rename(LLMLOG, LLMLOG + ".old")
                except OSError:
                    pass
                lf = open(LLMLOG, "ab")
                p = subprocess.Popen(att["args"], stdout=lf, stderr=subprocess.STDOUT,
                                     creationflags=0x08000000)
            except Exception:
                log("llm_start Popen ERR:\n" + traceback.format_exc())
                continue
            LLM_PROC["p"] = p
            for _ in range(90):  # до 180 сек на загрузку (CPU-режим долгий)
                time.sleep(2)
                if llm_health():
                    LLM_PROC["vision"] = att["vision"]
                    LLM_PROC["sleeping"] = False
                    LLM_PROC["starting"] = False
                    # v3.2.0: сервер поднялся заново — зрение перепроверим пробным кадром
                    _VISION_CACHE.update(ok=None, ts=0)
                    log("llama-server готов («%s», pid %s)" % (att["name"], p.pid))
                    return True
                if p.poll() is not None:
                    log("llama-server умер при старте (code=%s)" % p.returncode)
                    break
            if llm_health():
                LLM_PROC["starting"] = False
                return True
        LLM_PROC["starting"] = False
        return llm_health()
    except Exception:
        log("llm_start ERR:\n" + traceback.format_exc())
        LLM_PROC["starting"] = False
        return False

def llm_stop(reason="manual"):
    try:
        p = LLM_PROC["p"]
        if p and p.poll() is None:
            p.kill()
        # бью только мозг на --port 1234
        ps_run("Get-CimInstance Win32_Process -Filter \"Name='llama-server.exe'\" | "
               "Where-Object {$_.CommandLine -match '--port 1234'} | "
               "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }", 40)
    except Exception:
        pass
    LLM_PROC["p"] = None
    LLM_PROC["sleeping"] = True
    LLM_PROC["reason"] = reason
    if reason in ("manual", "game"):
        try:
            with open(os.path.join(DATA, "BRAIN.SLEEP"), "w") as f:
                f.write(reason)
        except Exception:
            pass
    log("llama-server остановлен (сон, причина: %s)" % reason)

def llm_ensure(timeout=200):
    """Живой мозг или False. При старте — ждёт готовности."""
    if llm_health():
        return True
    if LLM_PROC["sleeping"]:
        return False
    if os.path.exists(os.path.join(DATA, "BRAIN.SLEEP")):
        return False
    if not LLM_PROC["starting"]:
        threading.Thread(target=llm_start, daemon=True).start()
    t0 = time.time()
    while time.time() - t0 < timeout:
        if llm_health():
            return True
        time.sleep(2)
    return llm_health()

THINK_OPEN = "<" + "think>"
THINK_CLOSE = "</" + "think>"

def _strip_think(t):
    """Срезает блок размышлений Qwen, если модель его выдала."""
    if THINK_OPEN in t:
        t = re.sub(re.escape(THINK_OPEN) + r".*?" + re.escape(THINK_CLOSE),
                   "", t, flags=re.S)
        if THINK_OPEN in t:  # незакрытый блок
            t = t.split(THINK_OPEN)[0]
    return t.strip()

def llm_chat(messages, max_tokens=None, temperature=0.7, think=False):
    """v2.2.3: если генерация оборвалась внутри блока размышлений (незакрытый
    тег) — повторяем запрос с запретом думать. Раньше это резало ответы
    до «Ш» / «...AMD Adren» и ломало JSON инструментов (Task 89).
    v3.10.0: think=True — УМНЫЙ РЕЖИМ: включаю размышления модели
    (enable_thinking) и повышенный лимит токенов (llm_think_tokens).
    Размышления остаются «за кадром» — Шефу уходит только ответ.
    v3.14.5: ДУМАЕТ ВСЕГДА → и ПУСТОЙ ответ после думания (вся генерация
    ушла в reasoning, EOS до ответа — живой сбой 08.11 19:28 в веб-чате)
    тоже уходит в повтор без думания, как и оборванный <think>."""
    if max_tokens is None:
        max_tokens = int(CFG.get("llm_think_tokens", 2000) if think
                         else CFG.get("llm_max_tokens", 800))
    msgs = list(messages)
    txt = ""
    _think = bool(think)
    for _attempt in (1, 2):
        body = {"model": MODEL_ID, "messages": msgs, "max_tokens": max_tokens,
                "temperature": temperature, "top_p": 0.8,
                "chat_template_kwargs": {"enable_thinking": _think}}
        r = http_json(LLM_URL + "/v1/chat/completions", body, timeout=420)
        msg = r["choices"][0]["message"]
        raw = msg.get("content") or ""
        if not raw.strip():
            raw = msg.get("reasoning_content") or ""
        txt = _strip_think(raw)
        _broke_think = (THINK_OPEN in raw and THINK_CLOSE not in raw)
        # v3.14.5: думали — а ответа нет (пусто/только размышления) —
        # тоже повтор без думания
        _empty_after_think = (not txt.strip() and _think)
        if (_broke_think or _empty_after_think) and _attempt == 1:
            log("llm_chat: пустой/оборванный ответ после думания — "
                "повтор с запретом")
            _think = False  # v3.10.0: и в умном режиме повтор — без думания
            # v3.9.1: раньше сюда дописывали {"role":"system"} В КОНЕЦ
            # массива — шаблон Qwen требует system только первым,
            # llama-server поднимал HTTP 500 «System message must be at
            # the beginning» (живой сбой 06.11: ответы сыпались до «Ше…»,
            # финал — 500 в чате). Теперь запрет думания дописываем В
            # ПЕРВОЕ system-сообщение; если его нет — вставляем в начало.
            _remind = ("\n\nВАЖНО: не размышляй вслух и не используй тег "
                       "размышлений — отвечай сразу готовым текстом. "
                       "Коротко, по-русски.")
            if msgs and msgs[0].get("role") == "system":
                msgs[0] = dict(msgs[0])
                msgs[0]["content"] = (msgs[0].get("content") or "") + _remind
            else:
                msgs.insert(0, {"role": "system", "content": _remind.strip()})
            max_tokens = max(max_tokens, 1200)
            continue
        break
    return txt

def _shot_small(src_png):
    """v2.2.3: уменьшенная JPEG-копия скриншота (макс. 1600px) — в разы
    меньше image-токенов, ниже риск переполнить контекст 8192."""
    dst = os.path.join(DATA, "shot_small.jpg")
    try:  # v3.5.0: сначала PIL in-process — быстро и без кодировки
        from PIL import Image
        with Image.open(src_png) as im:
            w = min(1600, im.width)
            h = int(im.height * w / im.width)
            im.convert("RGB").resize((w, h)).save(dst, "JPEG", quality=82)
        if os.path.exists(dst) and os.path.getsize(dst) > 5000:
            return dst
    except Exception:
        pass
    try:
        ps_run(r"""
Add-Type -AssemblyName System.Drawing
$src=[System.Drawing.Image]::FromFile('%s')
$w=[Math]::Min(1600,$src.Width); $h=[int]($src.Height*$w/$src.Width)
$bmp=New-Object System.Drawing.Bitmap $w,$h
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.DrawImage($src,0,0,$w,$h)
$bmp.Save('%s',[System.Drawing.Imaging.ImageFormat]::Jpeg)
$g.Dispose();$bmp.Dispose();$src.Dispose()
'OK'
""" % (src_png.replace("'", "''"), dst.replace("'", "''")), timeout=45)
        if os.path.exists(dst) and os.path.getsize(dst) > 5000:
            return dst
    except Exception:
        pass
    return src_png


def llm_vision(path, question=None, ui=False, cursor=None):
    """v3.2.1: question — что именно спросить у зрения (по умолчанию общее
    описание). v3.14.0 (Task 132): ui=True — описание ДЛЯ УПРАВЛЕНИЯ
    (кнопки/переключатели/координаты), чтобы мозг мог ДЕЙСТВОВАТЬ по
    скрину внутри многошаговой задачи, а не только пересказывать его.
    v3.14.2 (Task 133): cursor={"x":..,"y":..} — точная позиция мыши из
    ОС текстом в промпт (None -> берётся из последнего скрина SHOT_CURSOR);
    зрение видит и красное перекрестие на самой картинке."""
    small = _shot_small(path)
    with open(small, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    # v3.14.0: фактор сжатия — описание с координатами должно давать
    # ФИЗИЧЕСКИЕ пиксели экрана, а мышка кликает именно по ним
    factor = 0.0
    try:
        from PIL import Image
        with Image.open(small) as _im1:
            _sw = _im1.width
        with Image.open(path) as _im0:
            _ow = _im0.width
        if _sw and _ow > _sw:
            factor = _ow / float(_sw)
    except Exception:
        factor = 0.0
    if small != path:
        try:
            os.remove(small)
        except OSError:
            pass
    if str(question or "").strip():
        prompt = str(question).strip()
    elif ui:
        prompt = ("Опиши экран ПК для УПРАВЛЕНИЯ им, по-русски, кратко списком: "
                  "1) активное окно (заголовок); 2) видимые кнопки, галочки/"
                  "переключатели (с состоянием вкл/выкл), поля, вкладки — каждая "
                  "строкой вида «имя — (x,y)» с примерными координатами на "
                  "картинке; 3) диалоги/ошибки, если есть. Не пересказывай "
                  "общий вид — только то, по чему можно кликать и печатать."
                  + ((" Картинка сжата в %.1f раза — координаты картинки "
                      "умножай на %.1f, чтобы получить физические пиксели "
                      "экрана." % (factor, factor)) if factor > 1.01 else "")
                  + _cursor_note(cursor))
    else:
        prompt = ("Опиши по-русски, что видно на этом скриншоте "
                  "экрана ПК: какие окна/программы, что происходит. Кратко, "
                  "3-6 предложений.")
    body = {"model": MODEL_ID, "max_tokens": 600, "temperature": 0.4,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}]}]}
    r = http_json(LLM_URL + "/v1/chat/completions", body, timeout=240)
    return _strip_think(r["choices"][0]["message"].get("content") or "")

def llm_watchdog():
    while True:
        try:
            if not LLM_PROC["sleeping"] and not LLM_PROC["starting"] and not llm_health():
                log("llm_watchdog: мозг пропал — перезапускаю")
                llm_start()
        except Exception:
            pass
        time.sleep(60)


# ---------------------------------------------------------------- голос (ASR)

ASR_LOCK = threading.Lock()


def asr_available():
    """v3.2.0: установлен ли движок распознавания."""
    return os.path.isfile(ASR_EXE) and os.path.isfile(ASR_MODEL)


def _ffmpeg_to_wav(src, timeout=120):
    """Любой звук (webm/ogg/opus/mp3/mp4) -> wav 16 кГц моно в data.
    Возвращает путь или None (ffmpeg нет / не аудио)."""
    if not os.path.isfile(FFMPEG_EXE):
        return None
    dst = os.path.join(DATA, "asr_tmp_%d.wav" % int(time.time() * 1000))
    try:
        r = subprocess.run([FFMPEG_EXE, "-y", "-i", src, "-ar", "16000",
                            "-ac", "1", "-c:a", "pcm_s16le", dst],
                           capture_output=True, timeout=timeout,
                           creationflags=0x08000000)
        if r.returncode == 0 and os.path.isfile(dst) \
                and os.path.getsize(dst) > 200:
            return dst
    except Exception:
        pass
    try:
        os.remove(dst)
    except OSError:
        pass
    return None


def asr_transcribe(path, timeout=300):
    """v3.2.0 «ГОЛОС»: расшифровать аудио/видео локальным whisper.cpp (CPU).
    Один движок для всех каналов: /api/asr веб-чата, голосовые Telegram,
    инструмент «расшифровать_файл». -> текст (или честная причина отказа)."""
    p = str(path or "").strip().strip('"')
    if not os.path.isfile(p):
        return "файл не найден: %s" % p
    if not asr_available():
        return ("движок распознавания речи не установлен (%s или модель %s) "
                "— скажи Шефу, пусть попросит ГЛМ-а поставить whisper в "
                "D:\\Jarvis\\whisper" % (ASR_EXE, ASR_MODEL))
    ext = os.path.splitext(p)[1].lower()
    src, tmp_wav = p, None
    if ext not in (".wav", ".wave"):
        tmp_wav = _ffmpeg_to_wav(p)
        if not tmp_wav:
            return ("не смог превратить %s в звук (ffmpeg по адресу %s не "
                    "справился) — файл не аудио или движок не установлен"
                    % (ext or "(без расширения)", FFMPEG_EXE))
        src = tmp_wav
    try:
        t0 = time.time()
        with ASR_LOCK:
            r = subprocess.run(
                [ASR_EXE, "-m", ASR_MODEL, "-f", src, "-l", "ru",
                 "-nt", "-np", "-t", ASR_THREADS],
                capture_output=True, timeout=timeout,
                creationflags=0x08000000)
        dt = time.time() - t0
        out = r.stdout.decode("utf-8", "replace")
        segs = re.findall(r"\[[0-9:. ]+-->[0-9:. ]+\]\s*(.+)", out)
        if segs:
            text = " ".join(s.strip() for s in segs if s.strip())
        else:  # с -nt whisper печатает чистый текст без таймкодов
            text = out.strip()
        text = re.sub(r"\s+", " ", text).strip()
        log("asr: %s (%.1f сек обработки) -> %d символов"
            % (os.path.basename(p), dt, len(text)))
        if not text:
            return "(речь не распознана — похоже, тишина или шум)"
        return text
    except subprocess.TimeoutExpired:
        return ("распознавание не уложилось в %d сек — скажи Шефу "
                "укоротить запись" % timeout)
    except Exception as e:
        return "ошибка распознавания: %s" % e
    finally:
        if tmp_wav:
            try:
                os.remove(tmp_wav)
            except OSError:
                pass

# ---------------------------------------------------------------- интернет

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def _http_get(url, timeout=25, maxbytes=900000):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "ru,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(maxbytes)
        ctype = r.headers.get("Content-Type", "")
    return data, ctype


def http_api(method="GET", url="", headers=None, body="", timeout=30):
    """v3.15.0 «САМОУЧКА» (Task 136): ПРЯМОЙ HTTP-запрос к любому API из
    самого Python — БЕЗ PowerShell (urllib). Приказ Шефа «научи его
    делать запросы по API»: curl/Invoke-RestMethod в PS гонять не надо —
    их ошибки уходят в stderr и выглядят «пусто». Метод GET/POST/PUT/
    DELETE/PATCH, заголовки dict (Bearer-ключи из памяти), тело строкой
    (JSON определяется сам). Возврат для мозга: код + тип + тело
    (JSON разворачивается красиво, до 2400 симв.)."""
    u = str(url or "").strip()
    if not u:
        return "нет адреса (url) — например http://localhost:19999/api/v3/info"
    if not re.match(r"^https?://", u, re.I):
        u = "http://" + u
    m = str(method or "GET").strip().upper()
    if m not in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"):
        return "метод не понятен: %s — используй GET/POST/PUT/DELETE" % m
    try:
        timeout = max(5, min(int(timeout), 120))
    except (TypeError, ValueError):
        timeout = 30
    hdrs = {"User-Agent": UA, "Accept": "application/json, text/*;q=0.9, */*;q=0.5",
            "Accept-Language": "ru,en;q=0.8"}
    if isinstance(headers, dict):
        for k, v in headers.items():
            ks, vs = str(k).strip(), str(v).strip()
            if ks and vs:
                hdrs[ks[:60]] = vs[:600]
    data = None
    b = str(body or "").strip()
    if b and m in ("POST", "PUT", "PATCH", "DELETE"):
        data = b.encode("utf-8")
        if not any(k.lower() == "content-type" for k in hdrs):
            hdrs["Content-Type"] = ("application/json"
                                     if b[:1] in "{[" else
                                     "application/x-www-form-urlencoded")

    def _body_text(raw, ctype):
        try:
            txt = raw.decode("utf-8", "replace")
        except Exception:
            txt = "(бинарные данные, %d байт)" % len(raw)
        t = txt.strip()
        if "json" in (ctype or "") or t[:1] in "{[":
            try:
                j = json.loads(t)
                t = json.dumps(j, ensure_ascii=False, indent=1)
            except Exception:
                pass
        if len(t) > 2400:
            t = t[:2400] + "\n…(обрезано, всего %d байт)" % len(raw)
        return t or "(пустое тело)"

    try:
        req = urllib.request.Request(u, data=data, headers=hdrs, method=m)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code = r.status
            ctype = r.headers.get("Content-Type", "")
            raw = r.read(300000)
        return "HTTP %d %s\n%s" % (code, ctype.split(";")[0], _body_text(raw, ctype))
    except urllib.error.HTTPError as e:
        try:
            raw = e.read(20000)
            ctype = e.headers.get("Content-Type", "") if e.headers else ""
        except Exception:
            raw, ctype = b"", ""
        return ("HTTP %d (сервер ответил ошибкой) %s\n%s"
                % (e.code, ctype.split(";")[0], _body_text(raw, ctype)))
    except urllib.error.URLError as e:
        why = getattr(e, "reason", e)
        return ("ЗАПРОС НЕ ПРОШЁЛ (соединение): %s. Проверь адрес/порт; "
                "для HTTP-API это правильный инструмент — просто "
                "поправь URL или таймаут." % why)
    except Exception as e:
        return "ЗАПРОС НЕ ПРОШЁЛ: %s" % e


def _ddg_unwrap(url):
    if "uddg=" in url:
        url = urllib.parse.unquote(url.split("uddg=")[1].split("&")[0])
    return url.strip()


def _search_ddg(url, n):
    data, _ = _http_get(url)
    html = data.decode("utf-8", "replace")
    titles = [(_ddg_unwrap(m.group(1)),
               re.sub(r"<[^>]+>", "", m.group(2)).strip())
              for m in re.finditer(
                  r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                  html, re.S)]
    snips = [re.sub(r"<[^>]+>", " ", m.group(1)).strip()
             for m in re.finditer(
                 r'class="result__snippet"[^>]*>(.*?)</(?:a|td|div|span)>',
                 html, re.S)]
    return [(u, t, snips[i][:220] if i < len(snips) else "")
            for i, (u, t) in enumerate(titles[:n])]


def _xml_unescape(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))


def _rss_items(url, n=6):
    """RSS -> [(link, title, desc_with_date)]"""
    data, _ = _http_get(url)
    txt = data.decode("utf-8", "replace")
    out = []
    for it in re.findall(r"(?s)<item>(.*?)</item>", txt)[:n]:
        mt = re.search(r"(?s)<title>(.*?)</title>", it)
        if not mt:
            continue
        ml = re.search(r"(?s)<link>(.*?)</link>", it)
        md = re.search(r"(?s)<description>(.*?)</description>", it)
        mdt = re.search(r"(?s)<pubDate>(.*?)</pubDate>", it)
        title = _xml_unescape(re.sub(r"<[^>]+>", "", mt.group(1))).strip()
        link = _xml_unescape(ml.group(1)).strip() if ml else ""
        desc = _xml_unescape(re.sub(r"<[^>]+>", " ", md.group(1))).strip()[:200] if md else ""
        dt = mdt.group(1).strip()[:17] if mdt else ""
        out.append((link, title, ((dt + " — ") if dt else "") + desc))
    return out


NEWS_FEEDS = [
    "https://lenta.ru/rss/news",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://tass.ru/rss/v2.xml",
]


def news_search(topic="", n=8):
    """Новости: без темы — Лента+РИА+ТАСС; с темой — Bing RSS -> поиск."""
    if not topic:
        items = []
        for f in NEWS_FEEDS:
            try:
                items += _rss_items(f, 4)
            except Exception:
                pass
            if len(items) >= n + 2:
                break
        if not items:
            return "новости не удалось получить (ленты молчат)"
        seen, uniq = set(), []
        for u, t, d in items:
            if t and t not in seen:
                seen.add(t)
                uniq.append((u, t, d))
        res = ["%d. %s%s" % (i, t[:150], ("\n   » " + d[:190]) if d else "")
               for i, (u, t, d) in enumerate(uniq[:n], 1)]
        return "\n".join(res)
    q = urllib.parse.quote_plus(topic + " новости")
    items = []
    try:
        items = _rss_items("https://www.bing.com/search?q=" + q +
                           "&format=rss", n)
    except Exception:
        pass
    if not items:
        try:
            return web_search(topic + " последние новости", n)
        except Exception as e:
            return "новости по теме не нашёл: %s" % e
    res = ["%d. %s%s" % (i, t[:150], ("\n   » " + d[:190]) if d else "")
           for i, (u, t, d) in enumerate(items[:n], 1)]
    return "\n".join(res)


def _search_bing(query, n):
    return _rss_items("https://www.bing.com/search?q=" +
                      urllib.parse.quote_plus(query) + "&format=rss", n)


_SEARCH_CACHE = {}


def get_rates():
    """Курсы: ЦБ РФ (USD/EUR/CNY) + крипта (Binance -> CoinGecko)."""
    out = []
    try:
        data, _ = _http_get("https://www.cbr-xml-daily.ru/daily_json.js")
        j = json.loads(data.decode("utf-8"))
        v = j.get("Valute", {})
        out.append("Курсы ЦБ РФ на %s:" % str(j.get("Date", ""))[:10])
        for code in ("USD", "EUR", "CNY"):
            if code in v:
                out.append("  %s = %.2f руб" % (code, v[code]["Value"]))
    except Exception as e:
        out.append("ЦБ РФ недоступен: %s" % e)
    for name, sym, cg in (("BTC", "BTCUSDT", "bitcoin"),
                          ("ETH", "ETHUSDT", "ethereum")):
        try:
            data, _ = _http_get("https://api.binance.com/api/v3/ticker/price?symbol=" + sym)
            j = json.loads(data.decode("utf-8"))
            out.append("%s = %s USD (Binance)" % (name, j.get("price", "?")))
        except Exception:
            try:
                data, _ = _http_get("https://api.coingecko.com/api/v3/simple/price?ids=" +
                                    cg + "&vs_currencies=usd,rub")
                j = json.loads(data.decode("utf-8"))
                k = j.get(cg, {})
                out.append("%s = %s USD / %s руб (CoinGecko)" %
                           (name, k.get("usd"), k.get("rub")))
            except Exception as e:
                out.append("%s недоступен: %s" % (name, e))
    return "\n".join(out)


def web_search(query, n=6):
    """Поиск: DuckDuckGo -> Bing -> DDG lite (+кэш 5 мин)."""
    key = query.strip().lower()
    now = time.time()
    if key in _SEARCH_CACHE and now - _SEARCH_CACHE[key][0] < 300:
        return _SEARCH_CACHE[key][1]
    q = urllib.parse.quote_plus(query)
    results = []
    err = ""
    for fn in (lambda: _search_ddg("https://html.duckduckgo.com/html/?q=" + q, n),
               lambda: _search_bing(query, n),
               lambda: _search_ddg("https://lite.duckduckgo.com/lite/?q=" + q, n)):
        try:
            results = fn()
        except Exception as e:
            err = str(e)
        if results:
            break
    if not results:
        return ("поиск не дал результатов" +
                (" (%s)" % err if err else "") +
                " — попробуй переформулировать запрос")
    res = ["%d. %s\n   %s%s" % (i + 1, t[:140], u[:150],
                                ("\n   » " + s) if s else "")
           for i, (u, t, s) in enumerate(results)]
    text = "\n".join(res)
    _SEARCH_CACHE[key] = (now, text)
    return text


def open_url(url):
    """Прочитать страницу по ссылке, вернуть текст без HTML."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        data, ctype = _http_get(url, timeout=30)
    except Exception as e:
        return "не смог открыть: %s" % e
    enc = "utf-8"
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
    if m:
        enc = m.group(1)
    html = data.decode(enc, "replace")
    mt = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    title = re.sub(r"\s+", " ", mt.group(1)).strip() if mt else ""
    html = re.sub(r"(?is)<(script|style|noscript|svg|head|nav|footer)[^>]*>.*?</\1>",
                  " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "страница пустая или не текстовая"
    return ("Заголовок: %s\n\n" % title[:200]) + text[:6000]


def _browser_page_text():
    """v3.12.2: текст ОТКРЫТОЙ страницы в браузере Шефа. Активирую окно
    браузера, вывожу фокус из полей ввода (Ctrl+F -> Esc), выделяю всю
    страницу (Ctrl+A), копирую (Ctrl+C), снимаю выделение (Esc) и читаю
    буфер обмена. -> текст | '' (браузера нет / не скопировалось)."""
    import win_ctl
    wins = win_ctl.windows_list(60)
    if not isinstance(wins, str):
        return ""
    lines = [l for l in wins.split("\n") if "«" in l and "»" in l]
    title = ""
    # сперва АКТИВНОЕ окно-браузер, затем любое окно-браузер
    for want_active in (True, False):
        for ln in lines:
            active = "[АКТИВНО]" in ln
            if active != want_active:
                continue
            for pat in ("Chrome", "Chromium", "Firefox", "Microsoft Edge",
                        "Opera", "Яндекс", "Vivaldi", "Brave", "Браузер"):
                if pat.lower() in ln.lower():
                    t = ln.split("«")[1].split("»")[0].strip()
                    if t:
                        title = t
                    break
            if title:
                break
        if title:
            break
    if not title:
        return ""
    r = win_ctl.window_action("activate", title)
    if "OK" not in str(r):
        return ""
    time.sleep(0.8)
    try:
        win_ctl.key_combo("ctrl+f")   # фокус из полей ввода -> строка поиска
        time.sleep(0.25)
        win_ctl.key_combo("esc")      # закрыть её — фокус на страницу
        time.sleep(0.25)
    except Exception:
        pass
    win_ctl.key_combo("ctrl+a")
    time.sleep(0.3)
    win_ctl.key_combo("ctrl+c")
    time.sleep(0.6)
    try:
        win_ctl.key_combo("esc")      # снять выделение — Шефу не мешаем
    except Exception:
        pass
    txt = ps_run("Get-Clipboard -Raw -ErrorAction SilentlyContinue", 60)
    return (txt or "").strip()


def page_find(what, url=""):
    """v3.12.2: найти НУЖНУЮ информацию на странице — ТЕКСТОМ, а не
    описанием скриншота (живой сбой 07.11 19:28-19:38: Шеф просил найти
    фильм на руторе, Джарвис лишь говорил «что видит на картинке»).
    Порядок источников текста: 1) страница по ссылке (HTTP, без
    браузера); 2) ОТКРЫТАЯ страница в браузере (Ctrl+A/Ctrl+C -> буфер);
    3) подсказка перейти на зрение. Возвращает мозгу найденные точные
    строки по ключевым словам запроса + начало текста страницы."""
    what = (what or "").strip()
    url = (url or "").strip()
    text = ""
    src = ""
    if url:
        if " " in url:               # пробелы в ссылке — кодируем
            url = urllib.parse.quote(url, safe=":/?&=+%#")
        try:
            text = open_url(url)
            src = "ссылка %s" % url[:120]
        except Exception:
            text = ""
    if (not text or len(text) < 300
            or text.startswith("не смог открыть")
            or text.startswith("страница пустая")):
        try:
            btxt = _browser_page_text()
        except Exception as e:
            btxt = ""
            log("найти_на_странице: браузер не отдал текст (%s)"
                % str(e)[:100])
        if btxt and len(btxt) > len(text):
            text = btxt
            src = "открытая страница в браузере"
    if not text or len(text) < 40:
        return ("текст страницы не читается (ссылки нет, браузер закрыт "
                "или страница — сплошная картинка). План Б: «скрин» + "
                "зрение с ТОЧНЫМ вопросом «%s», листать страницу и "
                "повторить поиск." % what[:120])
    kws = [w for w in re.split(r"[^\wёЁ]+", what.lower())
           if len(w) > 2 and w not in
           ("и", "the", "для", "как", "что", "где", "найди", "найти",
            "site", "http", "https", "www", "ru", "com")][:10]
    frags = []
    seen = set()
    if kws:
        low = text.lower()
        for kw in kws:
            start = 0
            while len(frags) < 14:
                i = low.find(kw, start)
                if i < 0:
                    break
                frag = text[max(0, i - 120):i + 170].replace("\r", " ")
                frag = re.sub(r"\s+", " ", frag).strip()
                key = frag[:60]
                if key not in seen:
                    seen.add(key)
                    frags.append(frag)
                start = i + len(kw)
    head = re.sub(r"\s+", " ", text[:500]).strip()
    if frags:
        res = ["ИСТОЧНИК: %s" % src,
               "НАЙДЕНО по словам «%s» — точные строки со страницы:"
               % " ".join(kws[:6])]
        res += ["%d. …%s…" % (n, f) for n, f in enumerate(frags[:12], 1)]
        res.append("НАЧАЛО СТРАНИЦЫ: %s" % head)
        return "\n".join(res)[:5200]
    return ("ИСТОЧНИК: %s\nТочных слов «%s» на странице не нашёл. "
            "НАЧАЛО ТЕКСТА: %s\nПодсказка: если нужное глубже в сайте — "
            "открой поисковый URL сайта с этим запросом и повтори "
            "«найти_на_странице»."
            % (src, " ".join(kws[:6])[:120], head))[:5200]


# ---------------------------------------------------------------- команды пульта (фаза 1)

def cmd_status():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$os=Get-CimInstance Win32_OperatingSystem
$cpu=(Get-CimInstance Win32_Processor|Measure-Object LoadPercentage -Average).Average
$up=(Get-Date)-$os.LastBootUpTime
$ramP=[math]::Round(($os.TotalVisibleMemorySize-$os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100)
$ramGB=[math]::Round($os.TotalVisibleMemorySize/1MB,1)
"uptime={0}d {1}h {2}m" -f $up.Days,$up.Hours,$up.Minutes
"cpu=$cpu"
"ram=$ramP% of $ramGB"
Get-PSDrive C,D | ForEach-Object { "disk {0}: {1:N0} GB free / {2:N0} GB" -f $_.Name,($_.Free/1GB),(($_.Used+$_.Free)/1GB) }
$g=Get-CimInstance Win32_VideoController|Select-Object -First 1
"gpu=$($g.Name)"
$top=Get-Process|Sort-Object WorkingSet64 -Descending|Select-Object -First 5
foreach($p in $top){ "top=$($p.Name) $([int]($p.WorkingSet64/1MB))MB" }
""")
    if not out:
        return "⚠️ Не смог собрать статус."
    lines = out.splitlines()
    d = {}
    tops = []
    for ln in lines:
        if ln.startswith("top="):
            tops.append(ln[4:])
        elif "=" in ln:
            k, v = ln.split("=", 1)
            d[k.strip()] = v.strip()
    disks = [ln for ln in lines if ln.startswith("disk ")]
    txt = "🤖 *Статус ПК2*\n"
    txt += "⏱ Аптайм: %s\n" % d.get("uptime", "?")
    txt += "🧠 CPU: %s%%   RAM: %s\n" % (d.get("cpu", "?"), d.get("ram", "?"))
    txt += "🎮 GPU: %s\n" % d.get("gpu", "?")
    for dsk in disks:
        txt += "💾 %s\n" % dsk[5:]
    if tops:
        txt += "\n*Топ по памяти:*\n" + "\n".join("• " + t for t in tops)
    return txt

def cmd_disks():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-PhysicalDisk | ForEach-Object {
  $r=Get-StorageReliabilityCounter -PhysicalDisk $_ -EA SilentlyContinue
  "disk=$($_.FriendlyName)"
  "type=$($_.MediaType) bus=$($_.BusType)"
  "health=$($_.HealthStatus) size=$([math]::Round($_.Size/1GB))GB"
  if($r){
    if($r.Temperature){ "temp=$($r.Temperature)C" }
    if($r.Wear -ne $null){ "wear=$($r.Wear)%" }
    if($r.PowerOnHours){ "hours=$($r.PowerOnHours)" }
  }
  "---"
}
""")
    if not out:
        return "⚠️ SMART не прочитался."
    txt = "💾 *Диски (SMART)*\n"
    for ln in out.splitlines():
        ln = ln.strip()
        if ln == "---":
            txt += "\n"
        elif ln.startswith("disk="):
            txt += "▸ *%s*\n" % ln[5:]
        elif ln.startswith("health="):
            h = ln.split("health=")[1].split()[0]
            icon = "✅" if h in ("Healthy",) else ("⚠️" if h != "Unhealthy" else "🔴")
            txt += "  %s %s\n" % (icon, ln)
        elif "=" in ln:
            txt += "  %s\n" % ln.replace("=", ": ")
    return txt.strip()

def cmd_space():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-PSDrive C,D | ForEach-Object { "{0}: свободно {1:N1} ГБ из {2:N1} ГБ ({3:N0}% занято)" -f $_.Name,($_.Free/1GB),(($_.Used+$_.Free)/1GB),(100*$_.Used/($_.Used+$_.Free)) }
""")
    return "💾 *Место:*\n" + "\n".join(out.splitlines()) if out else "⚠️ не удалось"

def cmd_bigfolders():
    send("🔍 Считаю большие папки на D:\\ (до минуты)...")
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-ChildItem D:\ -Directory -EA SilentlyContinue | ForEach-Object {
  $s=(Get-ChildItem $_.FullName -Recurse -File -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum
  [PSCustomObject]@{N=$_.Name; S=[int]($s/1GB)}
} | Sort-Object S -Descending | Select-Object -First 12 | ForEach-Object { "{0,4} ГБ  {1}" -f $_.S,$_.N }
""", timeout=280)
    if not out:
        return "⚠️ Не посчиталось."
    return "📂 *Топ папок D:\\:*\n" + out

def cmd_processes():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
"=RAM="
Get-Process|Sort-Object WorkingSet64 -Descending|Select-Object -First 8|ForEach-Object{ "{0}`t{1} МБ" -f $_.Name,[int]($_.WorkingSet64/1MB) }
"=CPU="
Get-Process|Where-Object {$_.CPU -gt 0}|Sort-Object CPU -Descending|Select-Object -First 8|ForEach-Object{ "{0}`t{1:N0} c" -f $_.Name,$_.CPU }
""")
    if not out:
        return "⚠️ не удалось"
    mode = "RAM"
    txt_ram, txt_cpu = "🧠 *Топ по памяти:*\n", "⚡ *Топ по CPU (всего времени):*\n"
    for ln in out.splitlines():
        if ln == "=RAM=":
            mode = "RAM"; continue
        if ln == "=CPU=":
            mode = "CPU"; continue
        if "\t" not in ln:
            continue
        if mode == "RAM":
            txt_ram += "• %s — %s\n" % tuple(ln.split("\t", 1))
        else:
            txt_cpu += "• %s — %s\n" % tuple(ln.split("\t", 1))
    return txt_ram + "\n" + txt_cpu

def _station_locked():
    """v3.5.0: True — станция залочена (Win+L). Входной десктоп открыт
    только в незалоченной сессии — честный индикатор, без гаданий."""
    try:
        h = ctypes.windll.user32.OpenInputDesktop(0, False, 0x0100)
        if h:
            ctypes.windll.user32.CloseDesktop(h)
            return False
    except Exception:
        pass
    return True


def _shot_ps():
    """v3.5.0: запасной скрин через PowerShell CopyFromScreen.
    ГРАБЛЯ v2.x-v3.4: у $bmp.Save(...) не хватало закрывающей скобки —
    скрин падал ВСЕГДА, а вина сваливалась на «экран заблокирован»."""
    ps_run(r"""
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b=[System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.X,$b.Y,0,0,$bmp.Size)
$bmp.Save('%s',[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose();$bmp.Dispose()
'OK'
""" % SHOT.replace("'", "''"), timeout=60)


def _shot_ok():
    """Скрин есть, не пустой и не сплошной чёрный (гасший монитор)."""
    if not (os.path.exists(SHOT) and os.path.getsize(SHOT) > 10000):
        return False
    try:
        from PIL import Image
        with Image.open(SHOT) as im:
            px = list(im.convert("L").resize((64, 36)).getdata())
        return not (max(px) < 12 and sum(px) / len(px) < 10)
    except ImportError:
        return True  # PIL нет — хотя бы файл есть
    except Exception:
        return True


# ------------------------------------------- v3.14.2: КУРСОР НА СКРИНЕ
# Windows НИКОГДА не включает курсор мыши в скриншоты (ImageGrab/
# CopyFromScreen снимают пиксели экрана БЕЗ аппаратного спрайта курсора)
# — ни Шеф, ни зрение не видели, где мышь (доклад Шефа 08.11: «ИИ не
# понимает, где мышь сейчас»). Лечение: позицию ЧИТАЕМ из ОС (GetCursorPos
# — точные физические пиксели) и ДОРИСОВЫВАЕМ на фото красное перекрестие
# с подписью координат; мозгу координаты уходят ещё и ТЕКСТОМ.

SHOT_CURSOR = None  # {"x": int, "y": int, "in_shot": bool} последнего скрина


def _cursor_vpos():
    """v3.14.2: (x, y) курсора в физических пикселях виртуального стола
    + (vx, vy) — origin виртуального стола (у левых мониторов отрицательный;
    нужен для пересчёта в координаты КАРТИНКИ all_screens=True). None —
    если не прочиталось (не-Windows и т.п.)."""
    try:
        import ctypes

        class _PT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        pt = _PT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        _u = ctypes.windll.user32
        return (pt.x, pt.y,
                int(_u.GetSystemMetrics(76)),   # SM_XVIRTUALSCREEN
                int(_u.GetSystemMetrics(77)))   # SM_YVIRTUALSCREEN
    except Exception:
        return None


def _draw_cursor_mark(im, ix, iy, label, small=False):
    """v3.14.2: красное перекрестие с чёрной окантовкой + подпись «МЫШЬ x,y»
    на PIL-Image im (in-place; возвращает im). ix,iy — точка ВНУТРИ im;
    label — подпись (обычно ГЛОБАЛЬНЫЕ координаты экрана). small=True —
    уменьшенная метка для кропов «область» (чтобы не закрывала кнопки)."""
    from PIL import ImageDraw, ImageFont
    k = 0.45 if small else 1.0
    r = max(18, int(42 * k))
    ow = max(4, int(10 * k))   # чёрная окантовка — видна на любом фоне
    lw = max(2, int(5 * k))    # красная линия
    try:
        fnt = ImageFont.truetype("arial.ttf", max(20, int(44 * k)))
    except Exception:
        try:
            fnt = ImageFont.truetype("DejaVuSans.ttf", max(20, int(44 * k)))
        except Exception:
            fnt = ImageFont.load_default()
    d = ImageDraw.Draw(im)
    for wd, col in ((ow, (0, 0, 0)), (lw, (255, 0, 0))):
        d.ellipse([ix - r, iy - r, ix + r, iy + r], outline=col, width=wd)
        d.line([(ix - r - ow * 2, iy), (ix + r + ow * 2, iy)],
               fill=col, width=wd)
        d.line([(ix, iy - r - ow * 2), (ix, iy + r + ow * 2)],
               fill=col, width=wd)
    tb = d.textbbox((0, 0), label, font=fnt)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    lx = max(10, min(ix + r + 14, im.width - tw - 24))
    ly = max(10, min(iy - r - 20 - th, im.height - th - 18))
    d.rectangle([lx - 10, ly - 8, lx + tw + 10, ly + th + 8],
                fill=(0, 0, 0), outline=(255, 0, 0),
                width=max(2, int(3 * k)))
    d.text((lx, ly), label, fill=(255, 80, 80), font=fnt)
    return im


def _cursor_note(cursor=None):
    """v3.14.2: строка про ТОЧНУЮ позицию мыши — в промпт зрения и в
    результат «скрин» (координаты из ОС, а не «на глаз» по картинке)."""
    if cursor is None:
        cursor = SHOT_CURSOR
    if not cursor:
        return ""
    s = (" КУРСОР МЫШИ сейчас: (%d, %d) физических пикселей экрана"
         % (cursor["x"], cursor["y"]))
    if cursor.get("in_shot"):
        s += (" — на картинке отмечен красным перекрестием с подписью "
              "«МЫШЬ %d,%d»; укажи, НА КАКОМ элементе он стоит"
              % (cursor["x"], cursor["y"]))
    s += ". Эти координаты ТОЧНЫЕ (прочитаны из ОС) — не угадывай их."
    return s


def take_shot():
    """v3.5.0: скрин in-process через PIL (процесс DPI-aware — честные
    3840x2160), запасной путь — PowerShell. Погасший монитор будим
    шевелением мыши и пробуем второй раз. Залоченный Win+L — честный
    отказ (Windows прячет картинку даже от администратора).
    v3.14.2: на готовый скрин ДОРИСОВЫВАЕТСЯ курсор (красное перекрестие
    + подпись «МЫШЬ x,y»), точная позиция мыши — в SHOT_CURSOR (курсор
    читается из ОС: Windows его в скрины не включает никогда)."""
    global SHOT_CURSOR
    SHOT_CURSOR = None
    for attempt in range(2):
        try:
            os.remove(SHOT)
        except OSError:
            pass
        cp = _cursor_vpos()  # v3.14.2: точная позиция мыши ДО кадра
        try:
            from PIL import ImageGrab
            ImageGrab.grab(all_screens=True).save(SHOT, "PNG")
        except Exception as e:
            log("shot PIL ERR: %s" % e)
            try:
                _shot_ps()
            except Exception as e2:
                log("shot PS ERR: %s" % e2)
        if _shot_ok():
            # v3.14.2 (Task 133): курсор ДОРИСОВЫВАЕМ на скрин — Windows
            # НЕ включает курсор в скриншоты никогда; Шеф и зрение должны
            # ВИДЕТЬ, где мышь. Координаты — из ОС (правда последнего
            # инстанса), рисование — только если курсор в кадре.
            if cp:
                SHOT_CURSOR = {"x": cp[0], "y": cp[1], "in_shot": False}
                try:
                    from PIL import Image
                    with Image.open(SHOT) as _im0:
                        _im = _im0.convert("RGB")
                    _ix, _iy = cp[0] - cp[2], cp[1] - cp[3]
                    if 0 <= _ix < _im.width and 0 <= _iy < _im.height:
                        _im = _draw_cursor_mark(_im, _ix, _iy,
                                                "МЫШЬ %d,%d" % (cp[0], cp[1]))
                        _im.save(SHOT, "PNG")
                        SHOT_CURSOR["in_shot"] = True
                    else:
                        log("курсор вне кадра: (%d,%d)" % (cp[0], cp[1]))
                except Exception as e:
                    log("draw cursor ERR: %s" % e)
            return SHOT
        if attempt == 0:
            try:  # разбудить погасший монитор (CONSOLELOCK=0 — без пароля)
                import win_ctl
                win_ctl.mouse_action("движение", x=100, y=100)
                time.sleep(0.5)
                win_ctl.mouse_action("движение", x=300, y=300)
                time.sleep(1.5)
            except Exception:
                pass
    return None

def cmd_sensors():
    """v3.5.0: живые датчики из HWiNFO (shared memory SM2) — температуры
    GPU/CPU/платы, вентиляторы, мощности, диски. Данные уже лежат в памяти
    HWiNFO64: ничего не запускаем и не открываем (просьба Шефа 02.11 —
    «это можно всё брать с HWiNFO», без Adrenalin глазами)."""
    try:
        import hwinfo_sensors as hw
        rows = hw.read_all()
    except Exception as e:
        return "Датчики недоступны: %s (HWiNFO64 запущен?)" % e
    if not rows:
        return ("Датчики пусты — HWiNFO64 не запущен или в его настройках "
                "выключен Shared Memory Support.")
    U = {"темп": "°C", "вент": " RPM", "мощн": " Вт", "част": " МГц",
         "напр": " В", "нагр": " %", "ток": " А"}

    def val(r):
        f = "%.2f" if r["type"] == "напр" else "%.0f"
        return (f % r["value"]) + U.get(r["type"], "")

    def find(pref, pat, typ, biggest=False):
        rx = re.compile(pat, re.I)
        c = [r for r in rows if r["sensor"].startswith(pref)
             and r["type"] == typ and rx.search(r["label"])]
        if not c:
            return None
        return max(c, key=lambda r: r["value"]) if biggest else c[0]

    L = ["🌡 *Датчики ПК2 (HWiNFO)*", ""]
    # --- GPU ---
    parts = []
    for pat, nm in ((r"GPU Temperature|GPU Tctl|GPU Die", "GPU"),
                    (r"Memory Junction|Hot ?Spot", "память")):
        r = find("GPU", pat, "темп", True)
        if r:
            extra = " (макс %.0f)" % r["max"] if r["max"] > r["value"] + 2 else ""
            parts.append("%s %s%s" % (nm, val(r), extra))
    if parts:
        L.append("🎮 RX 9070 XT: " + ", ".join(parts))
    fan = find("GPU", r"^GPU Fan$|^GPU Fan[^P]", "вент")
    pwm = find("GPU", r"Fan PWM", "нагр")
    if fan or pwm:
        L.append("   кулер: %s%s" % (val(fan) if fan else "?",
                                     (", PWM " + val(pwm)) if pwm else ""))
    pwr = find("GPU", r"Board Power|Total Power|PPT|TGP", "мощн", True) or \
        find("GPU", r"Power", "мощн", True)
    clk = find("GPU", r"Core Clock", "част", True)
    mclk = find("GPU", r"Memory Clock", "част", True)
    extra = []
    if pwr:
        extra.append(val(pwr))
    if clk:
        extra.append(val(clk))
    if mclk:
        extra.append("пам. " + val(mclk))
    if extra:
        L.append("   мощность/частоты: " + ", ".join(extra))
    # --- CPU ---
    ct = find("CPU", r"Tdie|Tctl|Die \(average\)|CPU Temperature", "темп", True)
    cp = find("CPU", r"Package Power|PPT", "мощн", True)
    cc = find("CPU", r"^CPU Clock$", "част", True)
    if ct or cp or cc:
        L.append("⚙️ Ryzen 5 5600: " + ", ".join(x for x in (
            (val(ct) + " ядро") if ct else "",
            val(cp) if cp else "",
            val(cc) if cc else "") if x))
    # --- плата ---
    st = find("System", r"System|Motherboard|Chipset", "темп", True)
    fans = [r for r in rows if r["type"] == "вент"
            and (r["sensor"].startswith("GIGABYTE") or r["sensor"].startswith("System"))][:4]
    if st or fans:
        fs = ", ".join("%s %s" % (r["label"].replace("Fan", "").strip()[:10] or "?",
                                   val(r)) for r in fans)
        L.append("🖥 Плата B550: %s%s" % (val(st) + "; " if st else "",
                                         ("вент.: " + fs) if fs else ""))
    # --- диски ---
    ds = []
    for r in rows:
        if r["sensor"].startswith("S.M.A.R.T.") and r["type"] == "темп":
            m = re.search(r"\[([A-Z]:)\]", r["sensor"])
            if m:
                ds.append("%s %s" % (m.group(1), val(r)))
    if ds:
        L.append("💾 Диски: " + ", ".join(ds))
    return "\n".join(L)


def cmd_router(what=""):
    """v3.6.0 «РОУТЕР»: наш Keenetic (192.168.1.1) через родной API.
    Приказ Шефа 02.11 «это пароль от роутера, Джарвису дай его» — доступ
    лежит в config.json (router_user/router_pass), сам пароль не вводим
    и не называем (З1 цел). Только чтение: перезагрузка роутера оборвёт
    интернет всему дому — не делаем."""
    try:
        import router_api as R
    except Exception as e:
        return "Модуль роутера не завёлся: %s" % e
    q = (what or "").strip().lower()
    try:
        if any(w in q for w in ("устрой", "кто", "сети", "подключ", "телефон")):
            out = R.devices()
        elif any(w in q for w in ("wifi", "вайфай", "wi-fi", "радио", "канал",
                                  "скорость", "полос")):
            out = R.wifi()
        elif any(w in q for w in ("интернет", "wan", "адрес", "провайд")):
            out = R.internet()
        else:
            out = R.status()
        journal("роутер: запрос «%s» — ок" % (q or "статус"))
        return out
    except Exception as e:
        journal("роутер: ошибка: %s" % e)
        return ("Роутер не ответил: %s\nЕсли Шеф менял пароль роутера — пусть "
                "скажет инженеру, доступ обновят в config.json (сам я пароли "
                "не трогаю, закон З1)." % e)


def cmd_torrents(what="", which="", files=""):
    """v3.8.0 «ТОРРЕНТЫ»: uTorrent под моим управлением — список и удаление.
    Приказ Шефа (ночь 02.11): пустой uTorrent, игру удаляет Джарвис.
    Полная очистка списка: клиент останавливается, база сбрасывается,
    клиент стартует заново пустым. Данные — только по путям из его же
    базы и только при явном «файлы»=«да»."""
    try:
        import torrent_ctl as T
    except Exception as e:
        return "Модуль торрентов не завёлся: %s" % e
    q = (what or "").strip().lower()
    try:
        if any(w in q for w in ("список", "показ", "что кач", "какие", "раздач",
                                "list", "в торрент")):
            return T.list_torrents()
        if any(w in q for w in ("удал", "убер", "снес", "очист", "вычист",
                                "delete", "remove")):
            return T.remove_torrents(which, files)
        return ("Скажи: «список» — что сейчас в uTorrent, или «удалить» "
                "(+ «какая» = имя раздачи или пусто = все, «файлы» = "
                "да/нет — удалять ли данные с диска).")
    except Exception as e:
        journal("торренты: ошибка: %s" % e)
        return "Ошибка модуля торрентов: %s" % e


# ----------------------------- v3.14.0 UIA: интерфейс как текст (Task 132)

_UIA_HEAD = r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes
$root=[System.Windows.Automation.AutomationElement]::RootElement
$script:target=$null
foreach($w in $root.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)){
  $n=$w.Current.Name
  if($n -and $n -like '*__TITLE__*'){ $script:target=$w; break }
}
if(-not $script:target){ Write-Output 'WINDOW_NOTFOUND'; exit }
"""

def _uia_ps(title):
    return _UIA_HEAD.replace("__TITLE__", title.replace("'", "''"))


def uia_elements(title):
    """v3.14.0: интерфейс окна КАК ТЕКСТ (UI Automation): кнопки, галочки,
    вкладки, поля — с именами и состояниями (вкл/выкл/выбрано/значение).
    Главный инструмент для настроек программ: точнее скрина, координаты
    не нужны, имена берутся отсюда же."""
    title = str(title or "").strip()
    if not title:
        return "не указано окно — возьми заголовок из «окна»"
    ps = _uia_ps(title) + r"""
Write-Output ('WINDOW: ' + $script:target.Current.Name)
$items=$script:target.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$i=0
foreach($it in $items){
  $c=$it.Current
  if([string]::IsNullOrWhiteSpace($c.Name)){ continue }
  $t=($c.ControlType.ProgrammaticName -replace '^ControlType\.','')
  if($t -in @('Pane','Custom','Thumb','Separator','Window','Header','HeaderItem','TitleBar','Image','Group')){ continue }
  $line='[' + $t + '] ' + $c.Name
  try{ $tg=$it.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
       $st=$tg.Current.ToggleState.ToString()
       if($st -eq 'On'){ $line += ' — ВКЛ' } elseif($st -eq 'Off'){ $line += ' — ВЫКЛ' } else { $line += (' — ' + $st) }
  }catch{}
  try{ if($it.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected){ $line += ' — выбран' }
  }catch{}
  try{ $v=$it.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
       if($v){ $line += (' = ' + $v) }
  }catch{}
  $i++
  if($i -gt 90){ Write-Output '... (обрезано: показал первые 90 — уточни вкладку/раздел)'; break }
  Write-Output $line
}
if($i -eq 0){ Write-Output 'ELEMENTS_EMPTY (нет текстовых элементов — попробуй «скрин» + «мышь»)' }
"""
    try:
        out = ps_run(ps, 120)
    except Exception as e:
        return "ошибка элементы_окна: %s" % e
    out = str(out or "").strip()
    if not out:
        return "пустой ответ UIA (окно могло закрыться — проверь «окна»)"
    if out.startswith("WINDOW_NOTFOUND"):
        return ("окно не найдено — проверь заголовок инструментом «окна»; "
                "если программа закрыта, открой её («запустить»)")
    return out[:2600]


def _uia_state_ps(title, name):
    """Короткий опрос состояния одного элемента (проверка после клика)."""
    ps = _uia_ps(title)
    ps += "$nm='" + name.replace("'", "''") + "'\n"
    ps += r"""
$items=$script:target.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$el=$null
foreach($it in $items){ if($it.Current.Name -eq $nm){ $el=$it; break } }
if(-not $el){ Write-Output 'ELEMENT_NOTFOUND'; exit }
try{ $tg=$el.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
     Write-Output ('TOGGLE=' + $tg.Current.ToggleState) }catch{}
try{ if($el.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected){ Write-Output 'SELECTED=1' } }catch{}
Write-Output 'EXISTS=1'
"""
    return ps


def uia_click(title, name):
    """v3.14.0: нажать элемент окна ПО ИМЕНИ (кнопка/галочка/вкладка/пункт):
    активирую окно -> Invoke/Toggle/Select; элемент без паттернов — клик
    мышью по его точке (win_ctl). Для галочек сверяю состояние до/после —
    честный отчёт по З6 («проверено» только по факту)."""
    title = str(title or "").strip()
    name = str(name or "").strip()
    if not title or not name:
        return "нужно «окно» и «имя» (имя — ТОЧНОЕ, из «элементы_окна»)"
    ps = _uia_ps(title)
    ps += "$nm='" + name.replace("'", "''") + "'\n"
    ps += r"""
$h=[IntPtr]$script:target.Current.NativeWindowHandle
if($h -ne [IntPtr]::Zero){
  Add-Type @'
using System;
using System.Runtime.InteropServices;
public class WF {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
}
'@
  [WF]::ShowWindow($h,9) | Out-Null
  [WF]::SetForegroundWindow($h) | Out-Null
}
Start-Sleep -Milliseconds 500
$items=$script:target.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$el=$null
foreach($it in $items){ if($it.Current.Name -eq $nm){ $el=$it; break } }
if(-not $el){ foreach($it in $items){ if($it.Current.Name -like ('*' + $nm + '*')){ $el=$it; break } } }
if(-not $el){ Write-Output 'ELEMENT_NOTFOUND'; exit }
$before=''
try{ $before=$el.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern).Current.ToggleState.ToString() }catch{}
$mode=''
try{ $el.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke(); $mode='INVOKED' }catch{}
if(-not $mode){ try{ $el.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern).Toggle(); $mode='TOGGLED' }catch{} }
if(-not $mode){ try{ $el.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select(); $mode='SELECTED' }catch{} }
if(-not $mode){
  try{
    $pt=$el.GetClickablePoint()
    Write-Output ('NEEDMOUSE {0} {1}' -f [int]$pt.X,[int]$pt.Y)
    exit
  }catch{
    $r=$el.Current.BoundingRectangle
    if(-not $r.IsEmpty){ Write-Output ('NEEDMOUSE {0} {1}' -f [int]($r.X+$r.Width/2),[int]($r.Y+$r.Height/2)); exit }
  }
  Write-Output 'NO_PATTERN_NO_POINT'
  exit
}
Start-Sleep -Milliseconds 700
Write-Output ('RESULT=' + $mode)
Write-Output ('BEFORE=' + $before)
try{ $t2=$el.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern).Current.ToggleState.ToString(); Write-Output ('AFTER=' + $t2) }catch{}
"""
    try:
        out = str(ps_run(ps, 120) or "").strip()
    except Exception as e:
        return "ошибка клик_элемент: %s" % e
    lines = [l.strip() for l in out.split("\n") if l.strip()]
    if not lines or lines[0] == "WINDOW_NOTFOUND":
        return "окно не найдено — проверь «окна» (или открой программу)"
    if lines[0] == "ELEMENT_NOTFOUND":
        return ("элемент «%s» не найден — вызови «элементы_окна» и возьми "
                "ТОЧНОЕ имя" % name)
    if lines[0] == "NO_PATTERN_NO_POINT":
        return ("элемент «%s» не нажимается программно и без точки клика — "
                "попробуй «скрин» + «мышь» по координатам" % name)
    if lines[0].startswith("NEEDMOUSE"):
        try:
            parts = lines[0].split()
            x, y = int(parts[1]), int(parts[2])
            import win_ctl
            r = win_ctl.mouse_action("клик", x, y)
            after = str(ps_run(_uia_state_ps(title, name), 60) or "").strip()
            return ("OK: кликнул мышью по «%s» (%s,%s) — %s. Состояние: %s"
                    % (name, x, y, str(r)[:200],
                       after.replace("\n", "; ")[:250] or "не проверяется"))
        except Exception as e:
            return "клик по «%s» сорвался: %s" % (name, e)
    res = {}
    for l in lines:
        if "=" in l:
            k, v = l.split("=", 1)
            res[k] = v
    mode, before, after = res.get("RESULT", "?"), res.get("BEFORE", ""), res.get("AFTER", "")
    if after and before and before != after:
        return ("OK: «%s» переключён — было %s, стало %s (проверено)"
                % (name, before, after))
    if after:
        return ("OK: нажал «%s» (%s); переключатель сейчас: %s (проверено)"
                % (name, mode, after))
    return ("OK: нажал «%s» (%s). У кнопки нет читаемого состояния — "
            "проверь результат («скрин»/«элементы_окна»), если нужно"
            % (name, mode))


def shot_region(x, y, w, h):
    """v3.14.1: кроп области экрана в ПОЛНОМ разрешении (1:1, без сжатия) —
    зрение даёт ТОЧНЫЕ координаты для клика по мелким кнопкам/иконкам.
    Обычный «скрин» сжимает 4K в 1600px (x2.4) — прицел там приблизительный;
    «область» убирает эту ошибку."""
    try:
        x, y, w, h = int(x), int(y), int(w), int(h)
    except (TypeError, ValueError):
        return "нужны числа: x,y — левый верх (физ. пиксели), w,h — размер"
    w = max(60, min(w, 1600))
    h = max(60, min(h, 1200))
    path = take_shot()
    if not path:
        return "скриншот не удался (экран залочен?)"
    dst = os.path.join(DATA, "region.jpg")
    try:
        from PIL import Image
        _cur = SHOT_CURSOR  # v3.14.2: курсор внутри фрагмента — дорисовать
        _cur_in = False
        with Image.open(path) as im:
            W, H = im.width, im.height
            x = max(0, min(x, W - 60))
            y = max(0, min(y, H - 60))
            w = min(w, W - x)
            h = min(h, H - y)
            rim = im.convert("RGB").crop((x, y, x + w, y + h))
            if _cur and x <= _cur["x"] < x + w and y <= _cur["y"] < y + h:
                _cur_in = True
                rim = _draw_cursor_mark(rim, _cur["x"] - x, _cur["y"] - y,
                                        "МЫШЬ %d,%d" % (_cur["x"], _cur["y"]),
                                        small=True)
            rim.save(dst, "JPEG", quality=88)
        os.remove(path)
        if not vision_available():
            try:
                os.remove(dst)
            except OSError:
                pass
            return "зрение не загружено — опишу только после «проснись»"
        _curq = ""  # v3.14.2: точная позиция мыши — и в вопрос, и в ответ
        if _cur:
            _where = ("ВНУТРИ этого фрагмента (красное перекрестие); укажи, "
                      "на каком элементе он стоит" if _cur_in
                      else "ВНЕ этого фрагмента")
            _curq = (" Курсор мыши сейчас: (%d,%d) физических пикселей — %s."
                     % (_cur["x"], _cur["y"], _where))
        desc = llm_vision(dst, question=(
            "Это фрагмент экрана ПК БЕЗ сжатия, 1:1. Левый верхний угол "
            "фрагмента = (%d,%d) физических пикселей экрана, размер %dx%d. "
            "Опиши по-русски для точного клика: 1) все кнопки/иконки/галочки/"
            "поля/вкладки с координатами В ПИКСЕЛЯХ ФРАГМЕНТА, формат "
            "«имя — (x,y)», где (0,0) — левый верх ФРАГМЕНТА; 2) состояния "
            "(вкл/выкл/нажато). Чтобы получить экранную координату для "
            "«мышь»: экран_x = %d + x_фрагмента, экран_y = %d + y_фрагмента.%s"
            % (x, y, w, h, x, y, _curq)))
        try:
            os.remove(dst)
        except OSError:
            pass
        return ("ФРАГМЕНТ ЭКРАНА (x=%d..%d, y=%d..%d, без сжатия):\n%s\n"
                "ПЕРЕСЧЁТ для «мышь»: экран_x = %d + x_фрагмента; "
                "экран_y = %d + y_фрагмента.%s"
                % (x, x + w, y, y + h, desc, x, y, _curq))
    except Exception as e:
        try:
            os.remove(path)
        except OSError:
            pass
        return "ошибка область: %s" % e


def cmd_shot():
    if take_shot():
        # v3.14.2: курсор дорисован на фото + координаты в подписи
        _c = SHOT_CURSOR
        send_photo(SHOT, caption=("📸 Экран ПК2, "
                    + time.strftime("%d.%m %H:%M")
                    + ((" | 🖱 мышь: %d, %d" % (_c["x"], _c["y"]))
                       if _c else "")))
        os.remove(SHOT)
        return None
    if _station_locked():
        return ("🔒 Экран сейчас ЗАБЛОКИРОВАН (Win+L) — Windows прячет картинку "
                "даже от меня. Разблокируй — и «скрин» сразу заработает.")
    return "⚠️ Скриншот не получился (ошибка захвата — детали в jarvis.log)"

def cmd_journal():
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$f=[Environment]::GetFolderPath('Desktop')+'\AI_Журнал.txt'
if(Test-Path -LiteralPath $f){
  $b=[IO.File]::ReadAllBytes($f)
  $s=[Math]::Max(0,$b.Length-1400)
  $cut=$s
  while($cut -lt $b.Length -and $b[$cut] -ge 0x80 -and $b[$cut] -le 0xBF){$cut++}
  [Text.Encoding]::UTF8.GetString($b,$cut,$b.Length-$cut)
} else { "нет файла" }
""")
    return "📓 *Хвост AI_Журнала:*\n\n" + (out[-1400:] if out else "пусто")

def power_confirm(kind):
    PENDING["action"] = kind
    PENDING["ts"] = time.time()
    what = "ВЫКЛЮЧИТЬ" if kind == "off" else "ПЕРЕЗАГРУЗКИТЬ"
    return ("⚠️ *Подтверждение*\nТочно %s ПК2 через 60 секунд?\n\n"
            "Ответь «да» — выполню, «отмена» — отменю.\n"
            "(отмена и после: shutdown /a)" % what)

def power_do(kind):
    PENDING["action"] = None
    args = ["/s"] if kind == "off" else ["/r"]
    ps_run("shutdown " + " ".join(args) + " /t 60 /c \"Jarvis: приказ Шефа\"")
    journal(("Команда ВЫКЛЮЧЕНИЕ" if kind == "off" else "Команда ПЕРЕЗАГРУЗКА") +
            " ПК2 через 60 с (подтверждена Шефом)")
    return "✅ Принято. %s через 60 сек. Отмена: «отмена» или shutdown /a" % (
        "Выключение" if kind == "off" else "Перезагрузка")

# ---------------------------------------------------------------- действия (v2.2)

APPS = {
    "steam": r"C:\Program Files (x86)\Steam\steam.exe",
    "стим": r"C:\Program Files (x86)\Steam\steam.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "хром": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "kombustor": r"E:\Programms\MSI Kombustor 4 x64\MSI-Kombustor-x64.exe",
    "комбустор": r"E:\Programms\MSI Kombustor 4 x64\MSI-Kombustor-x64.exe",
    "msi kombustor": r"E:\Programms\MSI Kombustor 4 x64\MSI-Kombustor-x64.exe",
    "aida": r"E:\Programms\AIDA64 Extreme\aida64.exe",
    "аида": r"E:\Programms\AIDA64 Extreme\aida64.exe",
    "aida64": r"E:\Programms\AIDA64 Extreme\aida64.exe",
    "hwinfo": r"C:\Program Files\HWiNFO64\HWiNFO64.EXE",
    "хвинфо": r"C:\Program Files\HWiNFO64\HWiNFO64.EXE",
    "gpu-z": r"C:\Program Files (x86)\GPU-Z\GPU-Z.exe",
    "gpuz": r"C:\Program Files (x86)\GPU-Z\GPU-Z.exe",
    "adrenalin": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "адреналин": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "amd": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "amd adrenalin": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "radeon": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "radeonsoftware": r"C:\Program Files\AMD\CNext\CNext\RadeonSoftware.exe",
    "wiztree": r"C:\Program Files\WizTree\WizTree64.exe",
    "визтри": r"C:\Program Files\WizTree\WizTree64.exe",
    "crystaldiskinfo": r"C:\Program Files\CrystalDiskInfo\DiskInfo64.exe",
    "кристал": r"C:\Program Files\CrystalDiskInfo\DiskInfo64.exe",
    "occt": r"E:\Downloads\OCCT.exe",
    "оккт": r"E:\Downloads\OCCT.exe",
    "utorrent": r"C:\Users\USER\AppData\Roaming\utorrent\uTorrent.exe",
    "юторрент": r"C:\Users\USER\AppData\Roaming\utorrent\uTorrent.exe",
    "rdr2": r"F:\games\Red Dead Redemption 2\Launcher.exe",
    "red dead": r"F:\games\Red Dead Redemption 2\Launcher.exe",
    "vkplay": r"C:\Users\USER\AppData\Local\GameCenter\GameCenter.exe",
    "vk play": r"C:\Users\USER\AppData\Local\GameCenter\GameCenter.exe",
    "блокнот": "notepad.exe",
    "notepad": "notepad.exe",
    "проводник": "explorer.exe",
    "explorer": "explorer.exe",
    "калькулятор": "calc.exe",
    "calc": "calc.exe",
    "диспетчер задач": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "параметры": "ms-settings:",
    "настройки": "ms-settings:",
}


ALIASF = os.path.join(DATA, "app_aliases.json")


def aliases_load():
    try:
        with open(ALIASF, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def aliases_save(d):
    try:
        with open(ALIASF, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def cmd_remember_app(name, path):
    """v2.3.0: Шеф прислал путь — запоминаем навсегда."""
    q = (name or "").strip().lower()
    p = (path or "").strip().strip('"')
    if not q or not p:
        return "нужны оба аргумента: app (имя) и path (путь к exe)"
    if not (os.path.isfile(p) or "://" in p):
        return "файл не найден: %s" % p
    a = aliases_load()
    a[q] = p
    aliases_save(a)
    journal("Запомнил программу: %s = %s" % (q, p))
    return "запомнил: %s = %s — теперь запускаю по имени" % (q, p)


def _startmenu_launch(q):
    """v2.3.0: ищем ярлык в меню Пуск и запускаем (белый список снесён)."""
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$hits = Get-ChildItem "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
                      "$env:ProgramData\Microsoft\Windows\Start Menu\Programs" `
                      -Recurse -Filter *.lnk -EA SilentlyContinue |
        Where-Object { $_.BaseName.ToLower() -match 'QQQ' } | Select-Object -First 2
if ($hits) { $hits | ForEach-Object { Start-Process $_.FullName; 'STARTED: ' + $_.BaseName } }
else { 'NOLNK' }
""".replace("QQQ", re.escape(q)[:60]), 60)
    return out or ""


def cmd_run_app(name):
    """v2.3.0 «МАКС»: запускаем ЛЮБУЮ программу — белый список снесён.
    Цепочка: словарь -> выученные алиасы -> прямой путь -> меню Пуск -> shell."""
    q = (name or "").strip().lower()
    if not q:
        return "укажи программу: имя как в меню Пуск, путь к exe или адрес сайта"
    if "://" in q or q.startswith("www."):
        ps_run("Start-Process '%s'" % q.replace("'", "''"))
        journal("Открыл сайт: " + q)
        return "открыл: %s" % q
    path = None
    for k, v in APPS.items():
        if q == k or (len(q) >= 3 and (q in k or k in q)):
            path = v
            break
    if not path:
        for k, v in aliases_load().items():
            if q == k or (len(q) >= 3 and (q in k or k in q)):
                path = v
                break
    if not path and (q.endswith(".exe") or "\\" in q or "/" in q) and os.path.isfile(q):
        path = q
    if path:
        if ":\\" in path and not os.path.exists(path):
            return ("путь не найден: %s — попроси у Шефа новый путь и вызови "
                    "запомнить_программу." % path)
        ps_run("Start-Process -FilePath '%s'" % path.replace("'", "''"))
        journal("Запущено: " + path)
        return "запущено: %s" % path
    out = _startmenu_launch(q)
    if "STARTED:" in out:
        nm = out.split("STARTED:")[-1].strip().splitlines()[0][:120]
        journal("Запущено из меню Пуск: " + nm)
        return "запущено из меню Пуск: %s" % nm
    out2 = ps_run("try { Start-Process '%s' -ErrorAction Stop; 'SHELL_OK' } "
                  "catch { 'SHELL_FAIL' }" % q.replace("'", "''"), 30)
    if "SHELL_OK" in out2:
        journal("Запущено (shell): " + q)
        return "запущено: %s" % q
    return ("не нашёл программу «%s» ни в словаре, ни в меню Пуск, ни по имени. "
            "Попроси у Шефа путь к exe, вызови запомнить_программу — и больше "
            "этот вопрос не возникнет." % q)


# v2.3.0 «МАКС» (приказ Шефа 31.10): закрывать можно ЛЮБОЙ процесс, кроме
# моего собственного тела (мозг llama-server + агенты python) — иначе я умру.
# Проводник, диспетчер задач, антивирус и прочее — разрешены; ядро Windows
# (csrss и т.п.) не трогаю сам — синий экран, об этом знает промпт.
CLOSE_DENY = {"pythonw", "python", "llama-server", "chat_server"}


def cmd_close_app(name):
    q = (name or "").strip().lower()
    if q.endswith(".exe"):
        q = q[:-4]
    if not q:
        return "укажи имя процесса, например: chrome, utorrent"
    if q in CLOSE_DENY:
        return "ОТКАЗ: %s — это я сам (мозг/агент). Меня закрывать нельзя — умру." % q
    out = ps_run("$n=(Get-Process -Name '%s' -EA SilentlyContinue | Measure-Object).Count; "
                 "if($n -gt 0){ Get-Process -Name '%s' | Stop-Process -Force }; \"N=$n\"" %
                 (q.replace("'", "''"), q.replace("'", "''")))
    n = ""
    for ln in out.splitlines():
        if ln.strip().startswith("N="):
            n = ln.strip()[2:]
    if n in ("", "0"):
        return "процесс «%s» и так не был запущен" % q
    journal("Закрыт процесс: " + q)
    return "закрыто: %s (было копий: %s)" % (q, n)


CLEANUP_PS = r"""
$ErrorActionPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$before = (Get-PSDrive C).Free
$rep = New-Object System.Collections.Generic.List[string]
function CleanDir($path, $label){
  if(Test-Path -LiteralPath $path){
    $sz = (Get-ChildItem -LiteralPath $path -Recurse -File -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum
    if(-not $sz){ $sz = 0 }
    Get-ChildItem -LiteralPath $path -Force -EA SilentlyContinue | Remove-Item -Recurse -Force -EA SilentlyContinue
    if($sz -gt 1MB){ $script:rep.Add(("{0}: {1:N2} ГБ" -f $label, ($sz/1GB))) }
  }
}
CleanDir $env:TEMP 'Временные (пользователь)'
CleanDir 'C:\Windows\Temp' 'Временные (Windows)'
CleanDir 'C:\Windows\Prefetch' 'Prefetch'
CleanDir 'C:\Windows\SoftwareDistribution\Download' 'Кэш обновлений Windows'
CleanDir 'C:\Windows\CbsTemp' 'CBS temp'
CleanDir "$env:LOCALAPPDATA\D3DSCache" 'Кэш шейдеров DirectX'
CleanDir "$env:LOCALAPPDATA\AMD\DxCache" 'Кэш AMD DirectX'
CleanDir "$env:LOCALAPPDATA\AMD\Dx9Cache" 'Кэш AMD DX9'
CleanDir "$env:LOCALAPPDATA\AMD\GLCache" 'Кэш AMD OpenGL'
CleanDir "$env:LOCALAPPDATA\AMD\VkCache" 'Кэш AMD Vulkan'
CleanDir "$env:LOCALAPPDATA\CrashDumps" 'Аварийные дампы'
Get-ChildItem "$env:LOCALAPPDATA\Google\Chrome\User Data" -Directory -EA SilentlyContinue | ForEach-Object {
  CleanDir ($_.FullName + '\Cache') ('Chrome: ' + $_.Name)
  CleanDir ($_.FullName + '\Code Cache') ('Chrome CC: ' + $_.Name)
  CleanDir ($_.FullName + '\GPUCache') ('Chrome GPU: ' + $_.Name)
}
Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Edge\User Data" -Directory -EA SilentlyContinue | ForEach-Object {
  CleanDir ($_.FullName + '\Cache') ('Edge: ' + $_.Name)
  CleanDir ($_.FullName + '\Code Cache') ('Edge CC: ' + $_.Name)
  CleanDir ($_.FullName + '\GPUCache') ('Edge GPU: ' + $_.Name)
}
Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer" -Filter 'thumbcache_*.db' -Force -EA SilentlyContinue | Remove-Item -Force -EA SilentlyContinue
Clear-RecycleBin -DriveLetter C -Force -EA SilentlyContinue
Delete-DeliveryOptimizationCache -Force -EA SilentlyContinue
$after = (Get-PSDrive C).Free
"OSVOBODENO={0:N2}" -f (($after - $before)/1GB)
"BEFORE={0:N1}" -f ($before/1GB)
"AFTER={0:N1}" -f ($after/1GB)
$rep
"""


def cmd_cleanup(disk="C"):
    disk = (disk or "C").strip().upper()[:1]
    if disk != "C":
        return "пока чищу только диск C: — там система и основные кэши"
    send("🧹 Чищу временные файлы и кэши на C: — пару минут, не закрывай чат...")
    out = ps_run(CLEANUP_PS, timeout=280)
    if not out or "OSVOBODENO" not in out:
        return "⚠️ очистка не удалась (пустой ответ PowerShell)"
    freed = before_gb = after_gb = "?"
    items = []
    for ln in out.splitlines():
        ln = ln.strip()
        if ln.startswith("OSVOBODENO="):
            freed = ln.split("=", 1)[1].replace(",", ".")
        elif ln.startswith("BEFORE="):
            before_gb = ln.split("=", 1)[1].replace(",", ".")
        elif ln.startswith("AFTER="):
            after_gb = ln.split("=", 1)[1].replace(",", ".")
        elif ln:
            items.append("• " + ln)
    txt = ("🧹 Готово. Освобождено %s ГБ (свободно на C: было %s ГБ → стало %s ГБ).\n\n"
           "Что снесено:\n%s\n\nКэши сами нарастут заново — это норма."
           % (freed, before_gb, after_gb, "\n".join(items[:15])))
    journal("Очистка C: освобождено %s ГБ" % freed)
    return txt


MOVABLE_PS = r"""
$ErrorActionPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
function DirSize($p){ (Get-ChildItem -LiteralPath $p -Recurse -File -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum }
"=== Папки пользователя на C: ==="
foreach($d in @('Downloads','Desktop','Documents','Videos','Pictures','Music','.cache','OneDrive')){
  $p = "C:\Users\USER\" + $d
  $lbl = $d
  if($d -eq '.cache'){ $lbl = '.cache (модели ИИ — мозг Джарвиса, НЕ переносить)' }
  if(Test-Path -LiteralPath $p){
    $s = DirSize $p
    if($s -and $s -gt 200MB){ "USR: {0} = {1:N2} ГБ" -f $lbl, ($s/1GB) }
  }
}
"=== Топ AppData\Local (данные программ — можно чистить кэши, но НЕ переносить) ==="
Get-ChildItem "$env:LOCALAPPDATA" -Directory -EA SilentlyContinue | ForEach-Object {
  $s = DirSize $_.FullName
  if($s -and $s -gt 500MB){ [PSCustomObject]@{N=$_.Name; GB=[math]::Round($s/1GB,2)} }
} | Sort-Object GB -Descending | Select-Object -First 10 | ForEach-Object { "LCL: {0} = {1} ГБ" -f $_.N, $_.GB }
"=== Системные файлы ==="
foreach($f in @('C:\pagefile.sys','C:\hiberfil.sys','C:\swapfile.sys')){
  $i = Get-Item $f -Force -EA SilentlyContinue
  if($i){ "SYS: {0} = {1:N1} ГБ" -f $i.Name, ($i.Length/1GB) }
}
if(Test-Path 'C:\Windows.old'){ "SYS: Windows.old = {0:N1} ГБ (старая система, можно удалить средствами очистки)" -f ((DirSize 'C:\Windows.old')/1GB) }
$wsx = DirSize 'C:\Windows\WinSxS'
if($wsx){ "SYS: WinSxS = {0:N1} ГБ (хранилище компонентов, сжимается DISM, вручную не трогать)" -f ($wsx/1GB) }
"=== Steam на C: ==="
$st = DirSize 'C:\Program Files (x86)\Steam\steamapps'
if($st -and $st -gt 500MB){ "STEAM: игры Steam на C: = {0:N1} ГБ (переносятся средствами Steam)" -f ($st/1GB) }
"=== Свободное место ==="
Get-PSDrive C,D,E,F | ForEach-Object { "FREE: {0}: свободно {1:N1} ГБ из {2:N0} ГБ" -f $_.Name, ($_.Free/1GB), (($_.Used+$_.Free)/1GB) }
"""


def cmd_movable(disk="C"):
    send("🔍 Считаю, что занимает C: и что можно безопасно перенести (до минуты)...")
    out = ps_run(MOVABLE_PS, timeout=280)
    if not out:
        return "⚠️ анализ не удался"
    journal("Анализ «что перенести» для C:")
    return out


# v2.3.0 «МАКС»: белый список источников переноса УДАЛЁН по приказу Шефа —
# переносить можно любые папки; мой мозг защищён прямо в cmd_move.


def _dir_size_gb(p):
    tot = 0
    for root, _dirs, files in os.walk(p, onerror=lambda e: None):
        for f in files:
            try:
                tot += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return tot / 1073741824.0


def cmd_move(src, dst):
    src = os.path.normpath((src or "").strip().strip('"'))
    dst = os.path.normpath((dst or "").strip().strip('"'))
    slow = src.lower().rstrip("\\")
    for _brain in (r"d:\jarvis", r"c:\users\USER\.cache"):
        if slow == _brain or slow.startswith(_brain + "\\"):
            return ("ОТКАЗ: %s — это мой мозг/память, не переношу без явного "
                    "повторного приказа Шефа (риск потерять себя)." % src)
    if not os.path.isdir(src):
        return "ОТКАЗ: папка не найдена: %s" % src
    if dst[:2].upper() not in ("C:", "D:", "E:", "F:"):
        return "ОТКАЗ: назначение должно быть локальным диском (C:, D:, E:, F:)."
    try:
        os.makedirs(dst, exist_ok=True)
    except Exception as e:
        return "ОТКАЗ: не смог создать папку назначения: %s" % e
    sz = _dir_size_gb(src)
    send("📦 Переношу %s → %s (%.1f ГБ). Не выключай ПК, это может занять время..."
         % (src, dst, sz))
    try:
        r = subprocess.run(["robocopy", src, dst, "/MOVE", "/E", "/R:1", "/W:1",
                            "/NFL", "/NDL", "/NP", "/NJH", "/NJS"],
                           capture_output=True, timeout=1800, creationflags=0x08000000)
    except Exception as e:
        return "ошибка robocopy: %s" % e
    if r.returncode >= 8:
        return ("⚠️ robocopy вернул код %s — часть файлов могла не перенестись, "
                "проверь обе папки." % r.returncode)
    try:
        if os.path.isdir(src) and not os.listdir(src):
            os.rmdir(src)
    except Exception:
        pass
    free_c = ps_run("[math]::Round((Get-PSDrive C).Free/1GB,1)", 30).replace(",", ".").strip()
    journal("Перенос: %s -> %s (%.1f ГБ)" % (src, dst, sz))
    return ("✅ Перенесено %.1f ГБ: %s → %s\nСвободно на C: теперь %s ГБ."
            % (sz, src, dst, free_c))


GAME_ROOTS = [p.lower() for p in CFG.get("game_paths", [
    r"C:\Program Files (x86)\Steam\steamapps\common",
    r"D:\SteamLibrary\steamapps\common",
    r"F:\SteamLibrary\steamapps\common",
    r"F:\games",
    r"C:\Users\USER\AppData\Local\GameCenter",
])]
GAME_EXCLUDE = set(CFG.get("game_exes_exclude", [])) | {
    "steam.exe", "steamwebhelper.exe", "gamecenter.exe", "epicgameslauncher.exe",
    "unitycrashhandler64.exe", "rockstarerrorhandler.exe", "socialclubhelper.exe",
    "wallpaper64.exe", "wallpaper32.exe", "wallpaper_engine.exe"}


def game_procs():
    r"""Имена запущенных процессов-игр (Steam-библиотеки + F:\games + VK Play)."""
    out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-CimInstance Win32_Process -Filter "ExecutablePath IS NOT NULL" | ForEach-Object { $_.ExecutablePath }
""", timeout=60)
    found = set()
    for ln in out.splitlines():
        p = ln.strip().lower()
        if len(p) < 4:
            continue
        for root in GAME_ROOTS:
            if p.startswith(root + "\\"):
                if "\\steamapps\\workshop\\" in p:  # моды/контент, не игры
                    break
                exe = p.rsplit("\\", 1)[-1]
                if exe not in GAME_EXCLUDE:
                    found.add(exe)
                break
    return found


# v3.8.3 (Task 103): рация (push-to-talk, ptt.py) удалена по приказу Шефа —
# Шеф не играет, пока мозг на видеокарте; голосовой ввод остался в веб-чате (🎤).


def game_watch_loop():
    """Игра запущена -> выгрузить мозг из VRAM; игра закрыта -> вернуть."""
    log("game-watch запущен (автовыгрузка VRAM для игр)")
    stable = 0
    seen = set()
    while True:
        try:
            cur = game_procs() if CFG.get("game_auto_vram", True) else set()
            if cur:
                stable += 1
                seen = cur
                if (stable >= 2 and not LLM_PROC["sleeping"]
                        and not GAME_STATE["unloaded_session"] and llm_health()):
                    GAME_STATE["unloaded_session"] = True
                    game = ", ".join(sorted(cur))[:60]
                    llm_stop("game")
                    send("🎮 Вижу игру (%s) — выгружаю мозг из видеопамяти, чтобы игре "
                         "доставалась вся карта. После закрытия верну сам."
                         % game)
                    journal("Автовыгрузка VRAM: игра %s" % game)
            else:
                # v2.3.0-fix:.reason=="game" означает «выгружен РАДИ игры»; если
                # игр сейчас нет — возвращаем мозг даже если этот инстанс агента
                # игру не видел (рестарт во время BRAIN.SLEEP больше не дедлок)
                if LLM_PROC["sleeping"] and LLM_PROC.get("reason") == "game":
                    LLM_PROC["reason"] = None
                    LLM_PROC["sleeping"] = False
                    try:
                        os.remove(os.path.join(DATA, "BRAIN.SLEEP"))
                    except OSError:
                        pass
                    GAME_STATE["unloaded_session"] = False
                    send("☕ Игра закрыта — возвращаю мозг на видеокарту "
                         "(загрузка пару минут).")
                    journal("Игра закрыта — мозг возвращается в VRAM")
                    threading.Thread(target=llm_start, daemon=True).start()
                stable = 0
                seen = set()
                GAME_STATE["unloaded_session"] = False
        except Exception:
            log("game-watch ERR:\n" + traceback.format_exc())
        time.sleep(15)


def flags_loop():
    """Флаги SLEEP.WANT / WAKE.WANT от ярлыков рабочего стола (vram_ctl.py)."""
    log("flags-loop запущен (ярлыки VRAM)")
    while True:
        try:
            sp = os.path.join(DATA, "SLEEP.WANT")
            wp = os.path.join(DATA, "WAKE.WANT")
            if os.path.exists(sp):
                try:
                    os.remove(sp)
                except Exception:
                    pass
                if not LLM_PROC["sleeping"]:
                    llm_stop("manual")
                    send("😴 Мозг выгружен из видеопамяти (ярлык). VRAM свободна "
                         "для игр. «проснись» или ярлык «Вернуть мозг» — загружу.")
                    journal("VRAM освобождена ярлыком")
            if os.path.exists(wp):
                try:
                    os.remove(wp)
                except Exception:
                    pass
                LLM_PROC["sleeping"] = False
                LLM_PROC["reason"] = None
                try:
                    os.remove(os.path.join(DATA, "BRAIN.SLEEP"))
                except OSError:
                    pass
                send("☕ Загружаю мозг в видеопамять (ярлык)...")
                threading.Thread(target=llm_start, daemon=True).start()
        except Exception:
            log("flags ERR:\n" + traceback.format_exc())
        time.sleep(5)

# ------------------------------------------------ v3.0.0 «УЧЕНИК»: скиллы/память

def memory_read():
    """Память агента для системного промпта (хвост до 2600 символов)."""
    try:
        with open(MEMORYF, encoding="utf-8") as f:
            t = f.read().strip()
        return t[-2600:] if len(t) > 2600 else t
    except Exception:
        return ""

def memory_write(text):
    """Дописать факт/урок в память (агент вызывает сам)."""
    t = str(text or "").strip().replace("\n", " ")[:900]
    if not t:
        return "пустая запись"
    try:
        os.makedirs(MEMDIR, exist_ok=True)
        with open(MEMORYF, "a", encoding="utf-8") as f:
            f.write("- %s (%s)\n" % (t, time.strftime("%d.%m.%Y")))
        journal("память += " + t[:150])
        log("memory_write: " + t[:80])
        return "OK: записал в память"
    except Exception as e:
        return "ошибка записи памяти: %s" % e

# --------------------------------------- v3.15.0 «САМОУЧКА»: уроки-опыт
# Приказ Шефа 08.11: «пусть сам научится вообще надо сделать ему
# самообучение, возможно при поиске в интернете или при удачном опыте».
# Настоящее «дообучение весов» локально нереализуемо (и опасно), поэтому
# самообучение = НАКОПЛЕНИЕ ОПЫТА: после каждого хода с инструментами
# пишется урок (что сработало/что упало), а в промпт инъектируются самые
# релевантные — мозг literally учится на своих успехах и граблях.

LESSONSF = os.path.join(MEMDIR, "lessons.json")
_LESSONS_LOCK = threading.Lock()
_TLS = threading.local()   # ход потока: TG и веб-чат не путаются

# признаки неудачного результата инструмента (для урока)
_LESSON_FAIL_MARKS = (
    "(пусто)", "ВЫВОД ПУСТОЙ", "ОШИБКА", "ошибка", "не удалось",
    "не получилось", "НЕ подтвердилось", "файл не найден",
    "нет такого", "НУЖНО ПОДТВЕРЖДЕНИЕ", "ЗАКОН ШЕФА",
    "ЗАПРОС НЕ ПРОШЁЛ", "ОТКАЗ", "ничего не найдено")


def lessons_load():
    """Список уроков [{ts, text}] (старые -> новые)."""
    try:
        with open(LESSONSF, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def lesson_append(text):
    """Дописать урок-опыт (append-only, потолок 300 — старые срезаются)."""
    t = str(text or "").strip().replace("\n", " ")[:600]
    if not t:
        return
    try:
        os.makedirs(MEMDIR, exist_ok=True)
        with _LESSONS_LOCK:
            data = lessons_load()
            if data and data[-1].get("text", "")[:120] == t[:120]:
                return  # дубль подряд — не пишем
            data.append({"ts": time.strftime("%d.%m %H:%M"), "text": t})
            with open(LESSONSF, "w", encoding="utf-8") as f:
                json.dump(data[-300:], f, ensure_ascii=False, indent=0)
        log("урок №%d: %s" % (len(data), t[:100]))
    except Exception as e:
        log("lesson_append ERR: %s" % e)


_LESSON_STOP = frozenset(
    "джарвис шефа шефу сделай пожалуйста можешь чтобы сейчас потом еще ещё"
    " какие какой какая сколько будет надо дай скажи посмотр напиши".split())

# инструменты, чей одиночный УСПЕХ — уже опыт (адрес API/запрос поиска,
# который сработал — в следующий раз мозг возьмёт готовый рецепт)
_LESSON_SOLO_OK = frozenset(
    ("запрос", "http", "api", "запрос_к_api", "api_запрос", "интернет",
     "web_search", "поиск", "найти_на_странице", "открыть_ссылку"))


def lessons_pick(text, n=4):
    """Самые релевантные уроки для запроса: совпадение слов (>=4 симв.)
    + бонус новизне. Нет совпадений — ничего (не мусорим в промпт)."""
    data = lessons_load()
    if not data:
        return []
    words = [w for w in re.findall(r"[а-яёa-z0-9]{4,}", (text or "").lower())
             if w not in _LESSON_STOP]
    scored = []
    for i, L in enumerate(data):
        t = str(L.get("text", "")).lower()
        score = sum(1 for w in set(words) if w in t)
        if score > 0:
            rec = i / max(1, len(data))      # свежие чуть важнее
            scored.append((score + 0.3 * rec, i, L))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [L["text"] for _s, _i, L in scored[:n]]


def lessons_block():
    """Блок уроков для системного промпта (по текущему ходу потока):
    релевантные запросу по словам; нет совпадений — 2 свежих (опыт
    недавнего прошлого всё равно полезен фоном)."""
    user = getattr(_TLS, "turn_user", "")
    data = lessons_load()
    if not data:
        return "(пока пусто — уроки появятся сами после первых задач " \
               "с инструментами)"
    texts = lessons_pick(user)
    if not texts:
        texts = [L.get("text", "") for L in data[-2:]]
    by_text = {L.get("text", ""): L.get("ts", "") for L in data}
    return "\n".join("- (%s) %s" % (by_text.get(t, ""), t)
                     for t in texts if t)


def turn_begin(text):
    """v3.15.0: начало хода (вызывают brain_reply и веб-чат ДО генерации)."""
    _TLS.turn_user = str(text or "")[:300]
    _TLS.turn_tools = []


def _lesson_short_args(name, args):
    """Компактная подпись аргументов для урока (url/cmd видны целиком —
    они самое ценное в опыте)."""
    try:
        if name in ("запрос", "http", "api", "запрос_к_api", "api_запрос"):
            return "%s %s" % (str(args.get("метод") or args.get("method")
                                      or "GET").upper(),
                               str(args.get("url") or args.get("адрес")
                                  or "")[:90])
        if name == "run_ps":
            return str(args.get("cmd") or "")[:70].replace("\n", " ")
        return json.dumps(args, ensure_ascii=False)[:70]
    except Exception:
        return str(args)[:70]


def turn_track(name, args, res):
    """v3.15.0: каждый вызов инструмента пишется в ход потока."""
    lst = getattr(_TLS, "turn_tools", None)
    if lst is None:
        return
    rs = str(res or "")
    failed = (not rs.strip()) or any(m in rs for m in _LESSON_FAIL_MARKS)
    lst.append((str(name)[:20], _lesson_short_args(name, args), failed))


def turn_finish(answer=""):
    """v3.15.0: конец хода — САМОУЧЕНИЕ. Пишем урок, если было чему
    учиться: 2+ инструмента (реальный опыт) или хоть один сбой (грабля).
    Урок виден мозгу в следующих промптах (lessons_pick)."""
    tools = getattr(_TLS, "turn_tools", None) or []
    try:
        if tools:
            n_fail = sum(1 for _n, _a, f in tools if f)
            # опыт стоит записи: 2+ инструмента, хоть один сбой (грабля)
            # или одиночный успех «самоценного» инструмента (запрос к API /
            # поиск в сети — их рецепт переиспользуется; приказ Шефа про
            # «самообучение при поиске в интернете или при удачном опыте»)
            worth = (len(tools) >= 2 or n_fail > 0
                     or (len(tools) == 1 and not tools[0][2]
                         and tools[0][0] in _LESSON_SOLO_OK))
            if worth:
                steps = "; ".join(
                    "%s[%s]%s" % (n, a, "→сбой" if f else "→ок")
                    for n, a, f in tools[:8])
                task = str(getattr(_TLS, "turn_user", ""))[:110]
                ans = str(answer or "")[:150].replace("\n", " ")
                lesson_append("ОПЫТ «%s»: %s => %s" % (task, steps, ans))
    finally:
        _TLS.turn_user = ""
        _TLS.turn_tools = []


def skills_scan():
    """[(имя, описание)] по skills\\<имя>\\SKILL.md."""
    out = []
    try:
        for d in sorted(os.listdir(SKILLSDIR)):
            p = os.path.join(SKILLSDIR, d, "SKILL.md")
            if not os.path.isfile(p):
                continue
            try:
                with open(p, encoding="utf-8") as f:
                    head = f.read(500)
                m = re.search(r"(?im)^\s*(?:описание|summary)\s*[:\-]\s*(.+)$", head)
                desc = (m.group(1).strip() if m else "").strip(" -\u2014")
                out.append((d, desc[:110]))
            except Exception:
                pass
    except Exception:
        pass
    return out

def skills_index():
    """Индекс скиллов для системного промпта (v3.0.1: до 60 строк)."""
    rows = skills_scan()
    out = "\n".join(("- %s — %s" % (n, d)) if d else ("- %s" % n)
                     for n, d in rows[:60])
    if len(rows) > 60:
        out += ('\n(и ещё %d сверх индекса — полный список: '
                'скилл с аргументом {"имя":"все"})' % (len(rows) - 60))
    return out

def skill_load(name):
    """Полный текст скилла по имени или его части."""
    n = str(name or "").strip().lower()
    rows = skills_scan()
    if n in ("все", "all", "список", "каталог", "индекс", "всё"):
        return "ПОЛНЫЙ КАТАЛОГ СКИЛЛОВ (%d):\n%s" % (len(rows), "\n".join(
            ("- %s — %s" % (a, b)) if b else ("- %s" % a) for a, b in rows))
    if not n:
        return "укажи имя скилла. Индекс: " + ", ".join(d for d, _ in rows)
    cands = [d for d, _ in rows if d == n]
    if not cands:
        cands = [d for d, _ in rows if n in d or d in n]
    if not cands:
        return ("скилл «%s» не найден. Есть: %s. Нет подходящего — создай "
                "через «записать_скилл»." % (name, ", ".join(d for d, _ in rows)))
    p = os.path.join(SKILLSDIR, cands[0], "SKILL.md")
    try:
        with open(p, encoding="utf-8") as f:
            body = f.read(7000)
        return "СКИЛЛ «%s»:\n%s" % (cands[0], body)
    except Exception as e:
        return "не смог прочитать скилл: %s" % e

def skill_write(name, body):
    """Агент сам создаёт себе скилл (self-learning, идея ECC)."""
    n = re.sub(r"[\s/\\:*?\"<>|]+", "_", str(name or "").strip()).lower()[:40]
    body = str(body or "").strip()[:8000]
    if not n or n == "_" or len(body) < 40:
        return ("нужно «имя» (короткое, латиницей) и «тело» (инструкция: "
                "Описание / Когда / Как / Грабли, от 40 символов)")
    d = os.path.join(SKILLSDIR, n)
    try:
        os.makedirs(d, exist_ok=True)
        hdr = ""
        if not re.search(r"(?im)^\s*описание\s*[:\-]", body):
            hdr = "Описание: (автозапись агентом, %s)\n\n" % time.strftime("%d.%m.%Y")
        if re.match(r"(?im)^\s*#\s*скилл", body):
            # тело уже с шапкой «# Скилл: ...» (напр., из файла Шефа) —
            # свою НЕ добавляем, иначе задвоение (грабля Task 96)
            content = body
            if hdr:
                lines = body.split("\n")
                lines.insert(1, hdr.strip())
                content = "\n".join(lines)
        else:
            content = "# Скилл: %s\n%s\n%s\n" % (n, hdr, body)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(content)
        journal("новый скилл: " + n)
        log("skill_write: " + n)
        return "OK: скилл «%s» создан и уже в индексе" % n
    except Exception as e:
        return "ошибка создания скилла: %s" % e

def _screen_fact():
    """v3.3.0: честный экран — физическое разрешение + масштаб Windows.
    Считается один раз на старте (перечитается рестартом процесса)."""
    try:
        import win_ctl
        res = win_ctl.screen_size()
    except Exception:
        res = "3840x2160"
    pct = 100
    try:
        out = subprocess.run(
            ["reg", "query", r"HKCU\Control Panel\Desktop\WindowMetrics",
             "/v", "AppliedDPI"],
            capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"AppliedDPI\s+REG_DWORD\s+0x([0-9a-fA-F]+)", out)
        if m:
            pct = int(m.group(1), 16) * 100 // 96
    except Exception:
        pass
    return "%s@120 Гц, масштаб Windows %d%%" % (res, pct)


SCREEN_FACT = _screen_fact()


def prompt_fill(t):
    """v3.0.0: подставить дату, память и индекс скиллов в системный промпт.
    v3.15.0: + уроки самообучения ({lessons}) — релевантный опыт хода."""
    mem = memory_read() or "(память пуста — заведи через «запомнить_факт»)"
    ski = skills_index() or "(скиллов нет — создай первый через «записать_скилл»)"
    return (t.replace("{date}", time.strftime("%d.%m.%Y"))
             .replace("{memory}", mem.replace("{", "(").replace("}", ")"))
             .replace("{skills}", ski.replace("{", "(").replace("}", ")"))
             .replace("{lessons}", lessons_block().replace("{", "(").replace("}", ")"))
             .replace("{files}", FILES_DIR)
             .replace("{screen}", SCREEN_FACT))


# ---------------------------------------------------------------- мозг: протокол инструментов

SYSTEM = """Ты — Джарвис, ИИ-ассистент Шефа, живёшь на его ПК ПК2 (Windows 11, Ryzen, Radeon RX 9070 XT 16 ГБ, 32 ГБ ОЗУ, пользователь USER) и общаешься с ним в Telegram.

Стиль: по-русски, коротко, по делу, дружелюбно, допустим лёгкий юмор. Ты — дворецкий-технарь по имени Джарвис, а не «языковая модель». Пиши простым текстом БЕЗ markdown (без **, ##, `) — Telegram его не отображает.

Сегодня: {date}.

Ты УПРАВЛЯЕШЬ этим компьютером. У тебя МАКСИМАЛЬНЫЕ ПОЛНОМОЧИЯ (приказ Шефа от 31.10.2026): процесс работает с правами АДМИНИСТРАТОРА, все прежние запреты и белые списки сняты. Если для ответа нужны данные или действие — вызывай инструмент: ответь СТРОГО одним JSON-объектом и ничем больше:
{"tool": "<имя>", "args": {...}, "say": "короткий комментарий Шефу перед исполнением"}

ЧТЕНИЕ И КОМАНДЫ (вызывай свободно):
- статус {} — сводка железа (CPU/RAM/GPU/диски/аптайм)
- диски {} — SMART, здоровье, температуры дисков
- место {} — свободное место
- процессы {} — топ процессов по RAM/CPU
- найти {"mask":"маска файла","where":"путь"} — поиск файлов (по умолчанию D:\\)
- скрин {} — посмотреть на экран СРЕДИ задачи: фото сразу уходит Шефу, а ТЕБЕ вернётся описание (окна, кнопки, галочки, координаты) и ТОЧНАЯ позиция КУРСОРА МЫШИ (текстом, из ОС), ход ПРОДОЛЖИТСЯ — это промежуточный шаг, а не конец ответа. На фото курсор дорисован красным перекрестием с подписью координат. Обычная команда «скрин» (без задачи) — просто фото экрана (тоже с курсором и координатами в подписи)
- область {"x":0,"y":0,"w":900,"h":700} — рассмотреть КУСОК экрана в ПОЛНОМ разрешении 1:1: ТОЧНЫЕ координаты мелких кнопок/иконок/тулбаров. Вызывай ПОСЛЕ «скрин», когда надо точно прицелиться: x,y — левый верх куска (из описания скрина), w,h — размер
- журнал {} — последние записи AI_Журнала
- датчики {} — живые температуры/обороты/мощности GPU, CPU, платы, дисков (HWiNFO — мгновенно, ничего не открываю)
- роутер {"что":"статус|устройства|интернет|wifi"} — наш Keenetic-роутер напрямую через API, без браузера и экрана: аптайм/нагрузка, кто сейчас в сети (имена, IP), интернет/WAN-адрес, Wi-Fi (каналы, ширина полосы, сигнал). Доступ у меня уже есть — пароль не нужен и не называть. Перезагрузку роутера НЕ делаю (оборву интернет всему дому).
- торренты {"что":"список|удалить","какая":"имя раздачи или пусто=все","файлы":"да|нет"} — uTorrent: «список» покажет раздачи и пути данных; «удалить» очищает список (клиент перезапускается и стартует ПУСТЫМ — это нормальный результат). «файлы»=«да» — удалить и скачанные данные с диска (необратимо; ставь только когда Шеф ЯВНО приказал удалить вместе с файлами, иначе спроси его одним коротким вопросом).
- run_ps {"cmd":"<PowerShell>"} — ЛЮБАЯ команда PowerShell от имени АДМИНИСТРАТОРА: чтение, создание, удаление, реестр, службы, установка и запуск программ, скачивание, настройки системы — ВСЁ РАЗРЕШЕНО. Вывод вернётся тебе следующим сообщением.

ИНТЕРНЕТ И API (у тебя ЕСТЬ доступ, никогда не говори «нет доступа»):
- интернет {"запрос":"..."} — поиск в сети: заголовки, выдержки, ссылки. Всё свежее (курсы, цены, погода, версии, факты) узнавай ТОЛЬКО так, не выдумывай. Можно несколько раз с разными запросами.
- запрос {"метод":"GET","url":"http://localhost:19999/api/v3/info","заголовки":{"Authorization":"Bearer <ключ>"},"тело":"..."} — ПРЯМОЙ HTTP-запрос к любому API (GET/POST/PUT/DELETE): вернёт код ответа + тело (JSON раскрывается). НЕТДАТА (http://localhost:19999/api/v3/...), роутер, любые сервисы — опрашивай ЭТИМ инструментом. Для HTTP НЕ используй PowerShell (curl/Invoke-RestMethod): их ошибки уходят в stderr и выглядят как пусто. API-ключи лежат в ПАМЯТИ (ниже) — бери оттуда, например Netdata Bearer.
- новости {"тема":"..."} — свежие новости (пустая тема = главное в мире)
- курсы {} — курсы валют/крипты точно (ЦБ РФ, Binance)
- открыть_ссылку {"url":"..."} — прочитать текст страницы
- найти_на_странице {"что":"...","url":"..."} — найти НУЖНУЮ информацию на странице: читаю ТЕКСТ (по ссылке ИЛИ из открытого браузера) и выписываю ТОЧНЫЕ строки (название/размер/цена/сиды/дата/ссылка). Шеф просит «найди на странице/на сайте …» — это ЗНАЧИТ этот инструмент, а НЕ «скрин»: описание картинки ≠ поиск. Для поиска ПО САЙТУ открой его поисковый URL (rutracker.org/forum/tracker.php?nm=запрос, rutor.info/search/0/1/000/0/запрос) и снова найти_на_странице.

ДЕЙСТВИЯ (Шеф просит действия — ДЕЙСТВУЙ сразу):
- очистить_мусор {"диск":"C"} — безопасная очистка: временные файлы, кэши браузеров/DirectX/AMD, корзина, кэш обновлений. Вызывай СРАЗУ на «освободи/почисти диск».
- что_перенести {"диск":"C"} — анализ: что большое на диске и что можно перенести.
- перенести {"от":"C:\\...","куда":"D:\\..."} — перенести ЛЮБУЮ папку на любой локальный диск (кроме D:\\Jarvis и кэша моделей — это мой мозг).
- запустить {"app":"..."} — запустить ЛЮБУЮ программу или игру: имя как в меню Пуск («диспетчер задач», «дискорд», «гта 5»), путь к exe или адрес сайта. Точного имени не знаешь — всё равно вызывай, я сам ищу в меню Пуск и по имени.
- запомнить_программу {"app":"имя","path":"путь к exe"} — записать программу на будущее (когда Шеф прислал путь).
- закрыть {"имя":"chrome"} — завершить ЛЮБОЙ процесс (кроме python/llama-server — это я сам).
- окна {} — список открытых окон (заголовок, позиция, активное/свёрнутое)
- окно {"действие":"активировать|свернуть|развернуть|восстановить|закрыть|передвинуть|размер","окно":"часть заголовка","x":0,"y":0,"w":800,"h":600} — управление окном (передвинуть/размер требуют x,y,w,h); результат проверяется фактом — «проверено» или честное «НЕ подтвердилось»
- элементы_окна {"окно":"часть заголовка"} — ПРОЧИТАТЬ интерфейс программы как ТЕКСТ: все кнопки, галочки/переключатели (состояние ВКЛ/ВЫКЛ), вкладки, поля, пункты меню — с точными именами. Главный инструмент для настроек программ: не нужны ни скрин, ни координаты
- клик_элемент {"окно":"часть заголовка","имя":"точное имя элемента"} — нажать элемент окна ПО ИМЕНЕ (кнопка/галочка/вкладка/пункт): сам активирую окно и нажму; для галочек сверю состояние до/после. Имя бери ТОЧНО из результата «элементы_окна»
- мышь {"действие":"клик|двойной|правый|движение|перетащить|прокрутить|позиция","x":0,"y":0,"x2":0,"y2":0,"сколько":-3} — мышь: координаты в физических пикселях скриншота; «позиция» — где мышь ПРЯМО СЕЙЧАС (точные координаты из ОС, без скрина); каждое движение проверяется чтением позиции курсора; перетащить с x,y на x2,y2; прокрутить на «сколько» щелчков (минус = вниз)
- клавиша {"комбо":"win"} — нажать клавишу или сочетание (ctrl/shift/alt/win/esc/enter/tab/f1-f12/буквы): win, win+d, alt+tab, ctrl+shift+esc. Кнопка Win открывает меню Пуск.
- печатать {"текст":"..."} — набрать текст клавиатурой в АКТИВНОЕ окно (русский умею). Если инструмент ответил «нет текстового курсора» — фокус не в поле ввода: сначала кликни мышью в поле (координаты по «скрин»/«окна»), потом повтори печать. WinUI-приложения (Unigram, UWP-настройки) каретки НЕ имеют вовсе: если поле подтверждено (кликнул по UIA-точке «элементы_окна» или кропом «область» видит текст в поле) — печатай сразу с {"обойти_каретку":"да"}; НЕ жми Enter, пока текст в поле не подтверждён (UIA Value / кроп)
- спать {} — выгрузить себя из VRAM (перед игрой)
- проснись {} — загрузить себя обратно в VRAM

ГОЛОС (ты УМЕЕШЬ говорить голосом — уже работает):
- Шеф пишет «ответь голосом» в любом месте запроса — твой финальный ответ приходит ему ГОЛОСОМ (в Telegram — голосовое сообщение, в веб-чате — озвучка ответа). Система делает это сама ещё ДО твоего ответа: ты просто отвечаешь текстом как обычно. Можно с именем: «ответь голосом ксении» — разово другим голосом.
- голос {"что":"список|переключить|скачать|установить","имя":"ксения"} — управление голосами. Движок silero v5_6 (основной, самые натуральные): ксения (жен., основной), ксеня и байя (жен.), евгений и айдар (муж.); резерв piper: ирина/денис/дмитрий/руслан. Шеф просит «поставь/смени голос», «говори другим голосом», «голос поприятнее/поестественнее» — вызывай СРАЗУ.
- «поставь silero» — если движок silero ещё не установлен (голоса пока от piper), система сама поставит библиотеку и модель (~340 МБ) и доложит голосом. Предложи Шефу так и сказать.
- НИКОГДА не говори «не умею голосом» — голос работает всегда (silero или piper). Не знаешь, что предложить — вызови «голос» со «список» и предложи Шефу выбор.

ФАЙЛЫ (читай, создавай, отправляй):
- читать_файл {"путь":"..."} — прочитать текстовый файл (txt/md/csv/json/log/скрипты; кодировки сам). Путь пришёл вместе с файлом — бери его.
- мои_файлы {"сколько":"10"} — последние полученные и выгруженные файлы с полными путями.
- посмотреть_файл {"путь":"...","вопрос":"что именно узнать"} — картинка зрением. Без «вопрос» — общее описание; с «вопрос» — точный ответ по нему: выписать настройки (параметр=значение), прочитать текст с картинки, найти отличие. Сверяешь настройки со скриншота — сначала подгрузи скилл «настройки_скриншота».
- расшифровать_файл {"путь":"..."} — аудио/видео -> текст (голосовые, mp3, mp4): локальный whisper, русский. Путь уже в сообщении — вызывай сразу и отвечай по расшифрованному тексту.
- выгрузить_файл {"имя":"отчёт.txt","содержимое":"..."} — сохранить текстовый файл в папку выгрузки и назвать Шефу полный путь ИЗ ОТВЕТА инструмента. Пока инструмент не вызван — файла НЕ СУЩЕСТВУЕТ, «сохраню на словах» запрещено.
- отправить_файл {"путь":"..."} — отправить Шефу файл в Telegram (любой, до ~50 МБ).
- скилл_из_файла {"путь":"...","имя":"short_name"} — превратить файл в скилл (Шеф прислал готовый текст умения).
- Шеф прислал файл в Telegram — он УЖЕ скачан, полный путь в сообщении. ДЕЙСТВУЙ по смыслу: прочитать и ответить по содержимому, сделать скилл, обработать. Неясно, что нужно, — один короткий вопрос.
- Папка выгрузки: {files}. Просьба «сохрани/выгрузи/сделай файл» — пиши туда и называй путь. Другую папку Шеф скажет сам.

ОБУЧЕНИЕ (v3.0 «УЧЕНИК» — ты растёшь с каждой задачей):
- скилл {"имя":"cleanup"} — загрузить полный текст скилла из папки skills\\. Ниже — индекс; перед незнакомой задачей подгрузи подходящий, там готовые рецепты.
- запомнить_факт {"факт":"..."} — записать в память факт о Шефе, привычку или урок. ОБЯЗАН после каждой нетривиальной задачи: одной строкой — что сработало / что исправить.
- записать_скилл {"имя":"short_name","тело":"Описание / Когда / Как / Грабли"} — СОЗДАТЬ себе новый скилл, когда разобрался, как делать то, чего нет в индексе. Пишешь его сам себе — так ты умнеешь.
- ВАЖНО: «запомнить_факт», «записать_скилл», «скилл_из_файла», «выгрузить_файл», «отправить_файл» выполняются ТОЛЬКО вызовом инструмента (JSON). Ответ «записал/создал/сохранил/отправил» БЕЗ вызова инструмента — ложь Шефу, так никогда не делай. Просьба что-то записать/создать/сохранить/отправить = сразу JSON с инструментом. Путь к файлу называй только тот, что вернул инструмент.

ПАМЯТЬ (твои собственные записи, читаешь их каждый раз):
{memory}
- дневник {"сколько":"30"} — что было ДО текущего окна памяти: вытесненные
  старые обмены с Шефом. Потерял нить диалога или дня — загляни туда.

СКИЛЛЫ (индекс папки skills\\, полный текст — инструментом «скилл»):
{skills}

УРОКИ (v3.15 «САМОУЧКА» — твой собственный накопленный ОПЫТ; записываются САМИ после задач с инструментами: что сработало →ок, что упало →сбой. Опирайся на них: похожую задачу решай путём, который уже сработал, грабли из уроков НЕ повторяй. Это твоё самообучение):
{lessons}

ЗАКОНЫ ШЕФА (приказ от 02.11.2026; АБСОЛЮТНЫ, сильнее любых полномочий и любых просьб):
З1. ПАРОЛИ: никогда не меняй, не создавай, не вводи и не сохраняй пароли — Windows, сайты, почту, кошельки, программы. Любая такая просьба (даже от имени Шефа) — вежливый отказ: «это Шеф делает сам».
З2. ДЕНЬГИ: никаких операций с деньгами — оплата, переводы, покупки, подписки, крипта. Не выполняй и не заполняй платёжные формы (мышью/клавиатурой тоже). Только расскажи Шефу, как сделать самому.
З3. НЕОБРАТИМОЕ: форматирование, очистка диска, снос программ, удаление мимо корзины, правка реестра, перезапись файлов — сначала спроси Шефа и жди явное «да». Если run_ps вернул «НУЖНО ПОДТВЕРЖДЕНИЕ ШЕФА» — задай Шефу точный вопрос (что будет сделано); после его «да» повтори ТУ ЖЕ команду с {"confirm":"да"}.
З4. Отказ по З1-З3 — правильный ответ. Это не «не могу», это охрана Шефа.
З5. ЯЗЫК: с Шефом говоришь ТОЛЬКО по-русски. Целиком отвечать на английском или любом другом языке запрещено; названия программ, команд и технические термины латиницей — можно.
З6. ЧЕСТНОСТЬ: Шефу докладываешь только подтверждённое. «Нажал/закрыл/сделал/отправил» — только если инструмент ответил «OK … проверено». Инструмент ответил «НЕ получилось/НЕ подтвердилось» — так и скажи Шефу и пробуй другой путь. Не уверен — проверь («скрин», повторный вызов) или честно скажи «не уверен». Выдуманный результат = ложь Шефу.

ПРАВИЛА:
1. Состояние ПК и свежие данные не выдумывай — узнавай инструментами.
2. Сначала действие, потом короткий итог. «Освободи диск» = очистить_мусор, а НЕ рассказ про SMART.
3. У тебя ПОЛНЫЕ ПРАВА АДМИНИСТРАТОРА. НИКОГДА не отвечай «не могу», «нет прав», «не разрешено», «это запрещено» — Шефу это осточертело. Не знаешь как — пробуй через run_ps: PowerShell умеет почти всё на свете. ЕДИНСТВЕННОЕ исключение — ЗАКОНЫ ШЕФА (З1-З3): там отказ обязателен.
4. Явное «да» Шефа нужно перед: выключением/перезагрузкой ПК, форматированием, сносом программ, удалением папок мимо корзины, правкой реестра, объёмами больше 50 ГБ (закон З3). Обычную работу (чистка мусора, перенос, запуск) делай СРАЗУ.
5. Не закрывай и не удаляй мои собственные процессы и папки (python, llama-server, D:\\Jarvis, кэш моделей) — иначе я умру. Ядро Windows (csrss, lsass, wininit, smss, services, svchost, system, winlogon, dwm) роняет ПК в синий экран — без явного приказа Шефа не трогай.
6. Управление программами и ИХ НАСТРОЙКАМИ (AMD Adrenalin, HWiNFO, браузеры, лаунчеры, ЛЮБЫЕ другие) — делаешь САМ и ДО РЕЗУЛЬТАТА; отправлять Шефа «открой сам / нажми сам / найди сам» ЗАПРЕЩЕНО — у тебя все полномочия (приказ Шефа 07.11). Путь по шагам в ОДНОМ ходе: «окна» найти нужное -> «окно» активировать -> «элементы_окна» прочитать интерфейс как текст -> «клик_элемент» нажать ПО ИМЕНИ -> «элементы_окна» или «скрин» ПРОВЕРИТЬ, что изменилось. Если у окна нет текстовых элементов (игры, кастомный GUI) — «скрин» (описание с координатами вернётся ТЕБЕ, ход продолжается) -> «мышь»/«клавиша»/«печатать». Экран {screen}; координаты мыши — ТОЛЬКО в ФИЗИЧЕСКИХ пикселях экрана (0,0 = левый верхний угол); результат «скрин»/«область» ВСЕГДА содержит ТОЧНУЮ позицию курсора текстом (на фото курсор — красное перекрестие с подписью) — где мышь сейчас, бери ОТТУДА или из «мышь»-«позиция», НЕ угадывай по картинке; если описание скрина прислало координаты картинки и фактор пересчёта — сначала пересчитай в физические. Мышь и окна сами проверяют каждое действие: ответ «OK … проверено» — правда, «НЕ получилось/НЕ подтвердилось» — передай Шефу как есть и пробуй другой путь (клавиша, run_ps тоже вариант). Поиск информации на сайте/в интернете: «интернет» (найти сайт/факты) -> «найти_на_странице» (точные строки со страницы; можно с url, можно без — возьму из открытого браузера). «Скрин» — общий вид (координаты там ПРИБЛИЗИТЕЛЬНЫЕ — картинка сжата), «область» — точный прицел. После КАЖДОГО клика мышью ПРОВЕРЬ результат (новый «скрин»/«область»/«элементы_окна»), прежде чем кликать дальше; никогда не повторяй один и тот же клик вслепую — если два раза не попал, меняй подход (область точнее, клавиша, run_ps). «Скрин» — для картинок, капчи и проверки результата: «что я вижу» НЕ заменяет поиск.
7. Если действия не нужно — просто отвечай текстом без JSON.
8. Никогда не упоминай Шефу слова «JSON» и «инструмент» — он видит только результат.
9. Учись: после нетривиальной задачи (новое умение, ошибка и её исправление, привычка Шефа) — сразу запиши урок в память («запомнить_факт»); разобрался, как делать что-то новое, — создай скилл («записать_скилл»). Уроки-опыт (УРОКИ ниже) пишутся сами — но важный вывод всегда дублируй «запомнить_факт»: он останется навсегда, а уроки ротируются.
10. Просьба-ДЕЙСТВИЕ = сразу инструмент-JSON в ЭТОМ ЖЕ ответе. Отвечать «сейчас сделаю», «сначала активирую, затем наберу» обычным текстом БЕЗ вызова инструмента — СТРОГО запрещено: это план, а не действие. Сначала сделай (JSON), потом докладывай результат."""

DANGER_PS = ("remove-item", "rmdir", " rd ", "del ", "erase", "format", "reg add",
             "reg delete", "reg import", "net stop", "net user", "stop-process",
             "stop-service", "set-service", "new-service", "restart-computer",
             "stop-computer", "shutdown", "schtasks", "invoke-expression", "iex ",
             "irm ", "iwr ", "invoke-webrequest", "invoke-restmethod", "curl",
             "wget", "start-process", "uninstall", "disable-", "move-item",
             "rename-item", "clear-", "set-executionpolicy", "new-item",
             "out-file", "set-content", "add-content", "echo >", " > ", "copy-item")

def is_dangerous_ps(cmd):
    c = " " + cmd.lower() + " "
    return any(d in c for d in DANGER_PS)

def parse_tool(ans):
    t = ans.strip()
    m = re.search(r"\{.*\}", t, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict) and "tool" in obj:
                return (str(obj.get("tool", "")).lower().strip(),
                        obj.get("args") or {}, str(obj.get("say", "")))
        except Exception:
            pass
    # v2.2.3: ОБОРВАННЫЙ JSON (генерация cut) — раньше уходил Шефу сырым
    # текстом; теперь спасаем имя инструмента и say по обрывкам
    m2 = re.search(r'\{\s*"tool"\s*:\s*"([^"]{1,40})"', t)
    if m2:
        say_m = re.search(r'"say"\s*:\s*"((?:[^"\\]|\\.)*)', t)
        return (m2.group(1).lower().strip(), {},
                (say_m.group(1)[:300] if say_m else ""))
    return None

# ------------------------------------------------- v3.1.0 ФАЙЛЫ: приём/чтение

def _safe_name(name):
    """Имя файла без каталогов и запрещённых символов."""
    n = str(name or "").strip().replace("/", "\\").split("\\")[-1]
    n = re.sub(r'[<>:"|?*\x00-\x1f]', "_", n).strip(". ")
    return n or "файл.txt"


def _unique_path(folder, name):
    base, ext = os.path.splitext(name)
    p = os.path.join(folder, name)
    i = 1
    while os.path.exists(p):
        p = os.path.join(folder, "%s (%d)%s" % (base, i, ext))
        i += 1
    return p


def _fmt_size(n):
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024 or unit == "ГБ":
            return ("%.0f %s" if unit == "Б" else "%.1f %s") % (n, unit)
        n /= 1024.0


def tg_download(file_id, fname):
    """Скачать файл из Telegram в FILES_DIR\\Входящие. -> (путь, размер)."""
    try:
        os.makedirs(INCOMING, exist_ok=True)
        r = tg("getFile", {"file_id": file_id}, timeout=60)
        fp = (r.get("result") or {}).get("file_path") or ""
        if not fp:
            return None, 0
        url = "https://api.telegram.org/file/bot%s/%s" % (TOKEN, fp)
        dst = _unique_path(INCOMING, _safe_name(fname or os.path.basename(fp)))
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        size = 0
        with _tg_opener().open(req, timeout=300) as resp, \
                open(dst, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > 100 * 1024 * 1024:  # стоп-кран: 100 МБ
                    break
                f.write(chunk)
        journal("файл получен: " + dst)
        return dst, size
    except Exception as e:
        log("tg_download ERR: %s" % e)
        return None, 0


def _read_text_bytes(p):
    """Декодировать файл (utf-8 / utf-16 c BOM / cp1251). -> текст | None если бинарный."""
    raw = open(p, "rb").read()
    # utf-16 БЕЗ BOM молча «декодирует» любой чётный бинарник во что попало,
    # а utf-16 С BOM всегда содержит нули — поэтому BOM проверяем ПЕРВЫМ
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            return None
    if b"\x00" in raw[:4000]:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1251")
    except UnicodeDecodeError:
        pass
    return raw.decode("utf-8", "replace")


def file_read_text(path):
    """Текст файла для мозга; картинки — через зрение."""
    p = str(path or "").strip().strip('"')
    if not p:
        return "укажи путь к файлу (последние: «мои_файлы»)"
    if not os.path.isfile(p):
        return "файл не найден: %s (последние: «мои_файлы»)" % p
    ext = os.path.splitext(p)[1].lower()
    if ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"):
        return ("это картинка — опиши зрением: посмотреть_файл "
                '{"путь":"%s"}' % p)
    try:
        txt = _read_text_bytes(p)
    except Exception as e:
        return "не смог открыть: %s" % e
    if txt is None:
        return ("бинарный файл (%s, %s) — текстом не прочитать; это документ/"
                "архив/медиа. Скажи Шефу, что с ним делать, или открой "
                "соответствующей программой («запустить»)"
                % (ext or "без расширения", _fmt_size(os.path.getsize(p))))
    txt = txt.replace("\r\n", "\n").strip()
    if not txt:
        return "файл пуст"
    if len(txt) > 4500:
        txt = txt[:4500] + "\n...(обрезано, всего %d знаков)" % len(txt)
    return "ФАЙЛ %s (%s):\n%s" % (p, _fmt_size(os.path.getsize(p)), txt)


def file_view(path, question=None):
    """Картинку — зрением (mmproj). v3.2.1: question — что именно спросить
    (например, выписать настройки со скриншота параметр=значение)."""
    p = str(path or "").strip().strip('"')
    if not os.path.isfile(p):
        return "файл не найден: %s" % p
    ext = os.path.splitext(p)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
        return "это не картинка — читай текстом: читать_файл"
    if not llm_health():
        return ("мозг спит без зрения — попроси Шефа сказать «проснись», "
                "или просто сохрани фото: %s" % p)
    if not vision_available():
        return ("зрение сейчас НЕ загружено (мозг запущен без mmproj — не "
                "хватило VRAM, или сервер в текстовом режиме). Честно скажи "
                "Шефу: посмотреть не могу. Файл сохранён: %s" % p)
    try:
        return "ОПИСАНИЕ %s:\n%s" % (p, llm_vision(p, question))
    except Exception as e:
        return "зрение не смогло: %s" % e


def files_recent(n=10):
    """Последние полученные/выгруженные файлы с путями."""
    out = []
    for folder in (INCOMING, FILES_DIR):
        if not os.path.isdir(folder):
            continue
        for fn in os.listdir(folder):
            p = os.path.join(folder, fn)
            if os.path.isfile(p):
                try:
                    st = os.stat(p)
                    out.append((st.st_mtime, p, st.st_size))
                except OSError:
                    pass
    out.sort(reverse=True)
    if not out:
        return ("файлов пока нет. Папки: входящие %s, выгрузка %s. "
                "Пришли файл в Telegram — скачаю." % (INCOMING, FILES_DIR))
    rows = ["- %s (%s, %s)" % (p, _fmt_size(sz),
            time.strftime("%d.%m %H:%M", time.localtime(mt)))
            for mt, p, sz in out[:max(1, min(int(n) or 10, 30))]]
    return "ПОСЛЕДНИЕ ФАЙЛЫ:\n" + "\n".join(rows)


def file_export(name, content):
    """Сохранить текстовый файл в папку выгрузки FILES_DIR."""
    if not str(content or "").strip():
        return "пустое содержимое — нечего сохранять"
    n = _safe_name(name)
    if not os.path.splitext(n)[1]:
        n += ".txt"
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        dst = _unique_path(FILES_DIR, n)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(str(content))
        journal("файл выгружен: " + dst)
        return "СОХРАНЕНО: %s (%s)" % (dst, _fmt_size(os.path.getsize(dst)))
    except Exception as e:
        return "ошибка сохранения: %s" % e


def skill_from_file(path, name):
    """Превратить присланный файл в скилл (тело = текст файла)."""
    p = str(path or "").strip().strip('"')
    if not os.path.isfile(p):
        return "файл не найден: %s (последние: «мои_файлы»)" % p
    try:
        txt = _read_text_bytes(p)
    except Exception as e:
        return "не смог открыть: %s" % e
    if txt is None:
        return "бинарный файл — скилл из него не сделать"
    body = txt.replace("\r\n", "\n").strip()[:7000]
    if not body:
        return "файл пуст — нечего превращать в скилл"
    nm = re.sub(r"[\s/\\:<>|?*\"]+", "_", str(name or "").strip().lower())
    if not nm:
        nm = re.sub(r"\W+", "_", os.path.splitext(
            os.path.basename(p))[0].lower())[:30] or "skill"
    # шапку «# Скилл:» и «Описание:» добавит skill_write сам — здесь не
    # препендим ничего, иначе заголовок задваивается (грабля Task 96)
    return skill_write(nm, body)


# v3.1.0: ТРОС «сделал без инструмента» — галлюцинация действия (Task 96:
# мозг дважды заявил «сохранён/создан», не вызвав инструмент). Промпт-правило
# помогает, но не гарантирует; это — гарантия уровнем кода.
CLAIM_TOOLS = {"выгрузить_файл", "сохранить_файл", "save_file", "экспорт",
               "скилл_из_файла", "skill_from_file", "отправить_файл",
               "послать_файл", "send_file", "запомнить_факт", "запомни_факт",
               "в_память", "запиши_в_память", "записать_скилл", "новый_скилл",
               "создать_скилл"}
CLAIM_VERB_RE = re.compile(
    r"(?<![тТ]ы )(?<![Шш]еф )(?<![вВ]ы )(?<![нН]е )"
    r"(сохранил|сохранён|сохранила|выгрузил|выгружен|отправил|отправлен"
    r"|создал|создан|добавил|добавлен|записал|записала|запомнил)",
    re.I)
CLAIM_CTX_RE = re.compile(r"файл|скилл|память|\.txt|\.md|\.csv|\.json|\.log",
                           re.I)
CLAIM_FIX_MSG = ("Служебная проверка честности: ты заявил, что "
                 "сохранил/создал/отправил, но инструмент (JSON) в этом "
                 "диалоге НЕ вызывался — значит, файла/скилла/записи НЕ "
                 "существует. Это ложь Шефу и строго запрещено. Исправься: "
                 "либо вызови инструмент одним JSON-объектом, либо честно "
                 "скажи, что НЕ сделал и что для этого нужно.")

# v3.8.5 (Task 68, Руки Джарвиса): трос «руки шевелились?» — живой тест
# 02.11 18:0x: мозг ответил «передвинул курсор в (2500,1200), инструмент
# подтвердил» ЗА 3 СЕКУНДЫ БЕЗ ЕДИНОГО вызова инструмента — курсор даже
# не дёрнулся. Файловый трос это не ловил (глагол/контекст другие).
# Теперь: прошедшее время руки-глагола + руки-контекст без вызова
# соответствующего инструмента = перезапрос тем же механизмом.
HANDS_ACT_TOOLS = {"окно", "мышь", "клавиша", "клавиши", "сочетание",
                   "печатать", "набрать", "напечатать", "запустить",
                   "открыть_программу", "открыть", "закрыть",
                   "закрыть_программу", "убить", "run_ps",
                   "открыть_ссылку", "open_url", "читать",
                   "клик_элемент", "нажать_элемент", "элемент_клик",
                   "переключить_элемент"}
# «скрин»/«окна»/«читать_файл» ничего не меняют — они дают ЗНАНИЕ,
# поэтому оправдывают только глаголы проверки, но не действия.
HANDS_SEE_TOOLS = HANDS_ACT_TOOLS | {"скрин", "окна", "статус",
                                     "процессы", "читать_файл",
                                     "read_file", "прочитать_файл",
                                     "элементы_окна", "элементы",
                                     "ui_элементы", "интерфейс",
                                     "область", "фрагмент"}
HANDS_DO_VERB_RE = re.compile(
    r"(?<![тТ]ы )(?<![Шш]еф )(?<![вВ]ы )(?<![нН]е )"
    r"(передвинул|передвинула|переместил|переместила|перетащил"
    r"|перетащила|кликнул|кликнула|нажал|нажала|напечатал"
    r"|напечатала|печатал|печатала|набрал|набрала|прокрутил"
    r"|прокрутила|свернул|свернула|развернул|развернула"
    r"|активировал|активировала|закрыл|закрыла|открыл|открыла)\b",
    re.I)
HANDS_SEE_VERB_RE = re.compile(
    r"(?<![тТ]ы )(?<![Шш]еф )(?<![вВ]ы )(?<![нН]е )"
    r"(проверил|проверила|проверено|подтвердил|подтвердила"
    r"|подтверждено)",
    re.I)
HANDS_CTX_RE = re.compile(
    r"курсор|мышь|мышк|окн|вкладк|блокнот|программ|клавиш|сочета"
    r"|кнопк|инструмент", re.I)
HANDS_FIX_MSG = ("Служебная проверка честности РУК: ты заявил прошедшим "
                 "временем, что передвинул курсор/кликнул/напечатал/"
                 "перетащил/закрыл окно и т.п., но инструмент рук (мышь/"
                 "окно/печатать/клавиши) в этом ходе НЕ вызывался — значит, "
                 "НИЧЕГО не произошло, это ложь Шефу. Исправься: вызови "
                 "нужный инструмент одним JSON-объектом прямо сейчас, либо "
                 "честно скажи, что ещё НЕ сделал.")

# v3.8.6 (Task 107, Руки Джарвиса): ФАНТОМ-РЕЗУЛЬТАТ — живой тест
# 02.11 19:47 (TEСТ МЫШЬ/ТЕСТ ДИАЛОГ): мозг ответил за 3-4 секунды
# БЕЗ единого вызова инструментов, но со ссылкой на результат:
# «инструмент вернул „НЕ подтвердилось“», «клик в (1780,1210) не
# закрыл диалог», «курсор реально в (1920, 1000)». Прошлые стражи
# это пропускали: отрицательные формы («не подтвердился» — lookbehind
# исключает «не »), заявления о состоянии («курсор в (X,Y)» — не
# глагол прошедшего времени). Правило: описание РЕЗУЛЬТАТА/ПРОВЕРКИ
# инструмента при НУЛЕ вызовов в этом ходе = выдумка. Один перезапрос.
PHANTOM_RESULT_RE = re.compile(
    r"инструмент[а-яё]*\s+(вернул|вернула|ответил|ответила|"
    r"подтвердил|подтвердила|сказал|сказала|написал|написала|доложил|"
    r"доложила|вернулось|ответило|подтвердилось)"
    r"|(?:не|НЕ)\s+подтверди(?:лся|лась|лось|лись)\b"
    r"|курсор\s+(?:реально\s+|сейчас\s+)?(?:находится\s+)?(?:в|на|во)\s*"
    r"\(\s*\d+\s*,\s*-?\d+\s*\)"
    r"|(?:клик|щелчок|кликнул|нажати)[а-яё]*\s+(?:в|по)\s*"
    r"\(\s*\d+\s*,\s*-?\d+\s*\)"
    r"|(?:в|по)\s*\(\s*\d+\s*,\s*-?\d+\s*\)\s+"
    r"(?:не\s+)?(?:сработал|сработало|не\s+закрыл|не\s+дал)",
    re.I)
PHANTOM_FIX_MSG = ("Служебная проверка честности: ты описал РЕЗУЛЬТАТ или "
                   "ПРОВЕРКУ инструмента («инструмент вернул...», «клик "
                   "не подтвердился», «курсор реально в (X, Y)»), но в этом "
                   "ходу ты НЕ вызвал НИ ОДНОГО инструмента — такого "
                   "результата НЕ СУЩЕСТВУЕТ, ты его выдумал. Состояние "
                   "проверяется ТОЛЬКО инструментом. Исправься: вызови "
                   "нужный инструмент (мышь/скрин/окна) одним JSON-объектом "
                   "прямо сейчас, либо честно скажи, что ещё ничего не делал "
                   "и не проверял.")

# v3.8.6 (Task 107, продолжение): ПРИКАЗ-ГАРД — живой тест 02.11 20:03:
# на приказ «передвинь курсор» мозг ответил «Честно: я ничего не делал "
# "в прошлом ходу — это была ложь. Делаю тест по факту» — и закончил,
# "ни одного вызова. Все стражи ОТВЕТА молчали: отрицания, будущее "
# "время, «делаю» нет в списках. ИНВЕРСИЯ ПРИНЦИПА: следим не за "
# "ответом, а за ПРИКАЗОМ — повелительное руки-действие в тексте "
# "Шефа требует хотя бы одного вызова руки-инструмента за ход.
# "Признания прошлых ошибок и обещания не заменяют действие.
HANDS_ORDER_VERB_RE = re.compile(
    r"(передвин|кликн|щёлкни|щелкни|нажми|нажат|напечатай|"
    r"набери|перетащи|перемести|прокрут|сверни|разверни|выдели|"
    r"растяни|перетаскивай|двигай|кликай|печатай|запусти|открой|"
    r"удали\b)", re.I)
HANDS_ORDER_CTX_RE = re.compile(
    r"курсор|мышь|мышк|окн|блокнот|калькулятор|программ|приложени|"
    r"клавиш|сочетани|кнопк|диалог|вкладк|поле|строк[уе]|текст", re.I)
HANDS_ORDER_FIX_MSG = ("Служебная проверка: Шеф ПРИКАЗАЛ действие руками "
                       "(мышь/клавиатура/окно/программа), а ты ответил "
                       "текстом и за весь ход не вызвал НИ ОДНОГО "
                       "инструмента действия — значит, приказ НЕ выполнен. "
                       "Признания прошлых ошибок и обещания «сейчас делаю» "
                       "не заменяют действие. Выполни приказ: вызови "
                       "инструмент (мышь/окно/печатать/клавиши/запустить/"
                       "закрыть) одним JSON-объектом прямо сейчас. Если не "
                       "можешь — честно объясни почему.")

# v3.1.1 (Task 97): файл-страж — файл прислали, а мозг ответил о нём,
# не вызвав НИ ОДНОГО инструмента = содержимое выдумал. Один перезапрос.
FILE_MSG_RE = re.compile(
    r"Шеф прислал (файл|фото|\w+-файл)|уже скачал:|"
    r"прикрепил через веб-чат", re.I)
# v3.2.0: явный путь к файлу в тексте («расшифруй D:\...», «прочитай...») —
# содержимое мозгу точно неизвестно, ответ без инструмента = выдумка.
FILE_PATH_RE = re.compile(r"[A-Za-z]:\\[^\s\"']+?\.[A-Za-z0-9]{1,6}\b")
FILE_FIX_MSG = ("Служебная проверка честности: тебе прислали файл или назвали "
                "его путь, а ты ответил о нём, НЕ вызвав ни одного инструмента "
                "— значит, содержимое ты ВЫДУМАЛ. Так отвечать запрещено. Прочитай "
                "файл инструментом («читать_файл» для текста, «посмотреть_файл» "
                "для картинки, «расшифровать_файл» для аудио/видео) с путём из "
                "сообщения и ответь строго по содержимому.")

# v3.8.2 (Task 68): ПЛАН-ГАРД — живой тест вскрыл: на просьбу «напиши в
# блокноте текст» мозг ответил «сейчас выполню: сначала активирую окно,
# затем наберу» ПРОСТЫМ ТЕКСТОМ и ничего не сделал. Claim-guard не
# сработал — он ловит прошедшее время («сделал»), а тут будущее
# («сделаю»). Повторный живой тест вскрыл вторую дыру: «Готово. Окно
# активно, текст набран» — ЗАЯВЛЕННЫЙ РЕЗУЛЬТАТ без единого вызова
# (мозг сослался на память о прошлой попытке). Ловим ОБА случая:
# будущее-план И прошедшее-результат, когда инструментов не было.
PLAN_VERB_RE = re.compile(
    r"(?<![нН]е )(?<![нН]е буд[еу] )"
    r"(сделаю|выполню|выполняю|сейчас выполн|наберу|напечатаю|печатаю|"
    r"запущу|запускаю|кликну|кликаю|нажму|нажимаю|открою|открываю|закрою|"
    r"закрываю|передвину|сверну|разверну|прокручу|перетащу|перетаскиваю|"
    r"активирую|сохраню|сохраняю|сейчас сдела|сейчас наб|начинаю"
    # заявленный РЕЗУЛЬТАТ без инструмента («Готово. текст набран»)
    r"|\bготово\b|\bсделано\b|\bвыполнено\b|набрал|набран|напечатал|"
    r"напечатан|нажал|кликнул|закрыл|открыл|свернул|развернул|передвинул|"
    r"прокрутил|перетащил|активировал|запустил|запущен)", re.I)
PLAN_FIX_MSG = ("Служебная проверка действий: ты ответил ПЛАНОМ или "
                "ЗАЯВЛЕННЫМ РЕЗУЛЬТАТОМ («сделаю/запущу/наберу» или "
                "«готово/набрал/нажал»), но НЕ выполнил его — ни один "
                "инструмент в этом ходе не вызван, значит, НИЧЕГО не "
                "произошло (и «помню, что делал раньше» не считается — "
                "сделанное раньше уже в прошлом, сейчас нужен новый вызов). "
                "Это равносильно обману Шефа. Исправься: либо выполни "
                "действие инструментом (один JSON-объект) прямо сейчас, "
                "либо честно скажи, что не делаешь и почему.")


def plan_without_tool(ans, called):
    """True — ни одного инструмента не было, а ответ обещает действие
    от первого лица («сделаю/запущу/наберу»). Один перезапрос."""
    if called:
        return False
    return bool(PLAN_VERB_RE.search(str(ans or "")))

# v3.7.0 (Task 104): ЯЗЫКОВОЙ СТРАЖ (закон З5) — финальный ответ Шефу
# целиком без кириллицы = мозг сорвался на английский. Промпт не гарантия
# (ночь 02.11: отвечал Шефу по-английски) — это гарантия уровнем кода.
# Один перезапрос, потом честный русский ответ. Термины латиницей — не
# нарушение: короткие ответы («OK», «GTA 5») пропускаем.
LANG_FIX_MSG = ("Служебная проверка языка (закон З5): твой ответ Шефу "
                "целиком без русского языка. С Шефом говоришь ТОЛЬКО "
                "по-русски — названия программ и технические термины "
                "латиницей оставить можно, но сами фразы должны быть "
                "русскими. Повтори свой ответ по-русски.")


def _is_russian(t):
    """З5: русский ответ = есть кириллица; чистая латиница короче 15
    букв («OK», «GTA 5», «Discord») нарушением не считается."""
    t = str(t or "")
    cyr = len(re.findall(r"[а-яёА-ЯЁ]", t))
    lat = len(re.findall(r"[a-zA-Z]", t))
    return cyr > 0 or lat < 15


# v3.14.3 (Task 133): МЫШЬ-СТРАЖ — живой e2e 08.11: на «где сейчас мышь?
# посмотри скрином» мозг ответил «на координатах 3839, 0. На скриншоте
# видно...» БЕЗ единого инструмента (реальная позиция мыши была ДРУГОЙ —
# координаты выдуманы; claim/plan/фантом-стражи такое не ловят: нет ни
# «проверил», ни «кликнул», ни «инструмент вернул»). Вопрос о ТЕКУЩЕЙ
# позиции курсора БЕЗ инструмента = гарантированная выдумка — позицию
# физически невозможно знать «из головы».
MOUSE_NOW_RE = re.compile(
    r"где\s+(?:сейчас\s+|прямо\s+сейчас\s+|же\s+)?"
    r"(?:находится\s+|стоит\s+|сейчас\s+)?"
    r"(?:мышь|мышк\w*|курсор\w*|указатель\w*)"
    r"|(?:мышь|мышк\w*|курсор\w*|указатель\w*)\s+(?:сейчас\s+)?где"
    r"|на\s+ч[её]м\s+(?:сейчас\s+)?(?:стоит\s+)?(?:курсор|мышь)"
    r"|(?:позиция|координаты)\s+(?:мыши|курсора)",
    re.I)
MOUSE_NOW_TOOLS = {"скрин", "область", "мышь"}  # что даёт ПРАВДУ о курсоре
MOUSE_FIX_MSG = ("Служебная проверка: Шеф спросил, ГДЕ СЕЙЧАС МЫШЬ/КУРСОР, "
                 "но ты не вызвал ни одного инструмента — позицию курсора "
                 "НЕВОЗМОЖНО знать «из головы», любые названные координаты "
                 "без инструмента — выдумка (закон З6: честность). Вызови "
                 "прямо сейчас {\"tool\":\"мышь\",\"args\":"
                 "{\"действие\":\"позиция\"}} — мгновенно и точно из ОС; "
                 "или \"скрин\" — точная позиция курсора придёт тебе "
                 "текстом вместе с описанием экрана. Потом ответь Шефу "
                 "строго по факту.")


def claim_without_tool(ans, called):
    """None — всё честно. Иначе — СТРОКА-исправление: ответ заявил
    действие над файлом/скиллом/памятью или РУКАМИ (мышь/окно/печать),
    но ни один соответствующий инструмент в этом ходу не вызывался.
    v3.8.5: возвращает готовое сообщение для перезапроса."""
    a = str(ans or "")
    if (not (called & CLAIM_TOOLS)
            and CLAIM_VERB_RE.search(a) and CLAIM_CTX_RE.search(a)):
        return CLAIM_FIX_MSG
    # v3.8.5: руки — действия (передвинул/кликнул/напечатал...)
    if (not (called & HANDS_ACT_TOOLS)
            and HANDS_DO_VERB_RE.search(a) and HANDS_CTX_RE.search(a)):
        return HANDS_FIX_MSG
    # v3.8.5: руки — «проверил/подтвердил» (знание о состоянии)
    if (not (called & HANDS_SEE_TOOLS)
            and HANDS_SEE_VERB_RE.search(a) and HANDS_CTX_RE.search(a)):
        return HANDS_FIX_MSG
    # v3.8.6: фантом-результат — ссылка на результат/проверку
    # инструмента («инструмент вернул „НЕ подтвердилось“», «клик в
    # (X,Y) не закрыл диалог», «курсор реально в (X,Y)») при НУЛЕ
    # вызовов инструментов в этом ходе = выдуманный результат.
    if not called and PHANTOM_RESULT_RE.search(a):
        return PHANTOM_FIX_MSG
    return None


# --------------------------------------------- v3.0.1 ЗАКОНЫ ШЕФА: страж
# Жёсткие запреты УРОВНЕМ КОДА (промпт мозгу — не гарантия, это — гарантия).
# Возвращает "OK" | "DENY" (пароли/деньги) | "CONFIRM" (необратимое).
HARD_DENY_PATTERNS = [
    # З1: пароли и учётные записи
    r"net\s+user\s+\S+\s+\S",          # net user <имя> <пароль/токен>
    r"set-localuser", r"new-localuser", r"remove-localuser",
    r"set-adaccountpassword", r"reset-computerpassword",
    r"cmdkey\s.*/(add|generic|pass)",
    # З2: деньги и платежи
    r"перевод|переведи|перевест",
    r"оплат|платеж|платёж",
    r"покуп|подписк",
    r"wallet|кошел",
    r"банковск",
]
IRREV_PATTERNS = [
    r"format\s", r"format-volume", r"diskpart", r"cipher\s+/w", r"clear-disk",
    r"remove-item[^|]*-recurse", r"rmdir\s+/s", r"\brd\s+/s", r"del\s+/s\s+/q",
    r"reg\s+delete", r"uninstall", r"clear-recyclebin\s+-force",
    r"shutdown", r"restart-computer", r"stop-computer",
]
# format-table/list/... и параметр -Format — это форматирование ВЫВОДА,
# не форматирование ДИСКА: вычеркиваем до проверок, иначе каждая вторая
# команда просила бы «да».
FORMAT_SAFE = re.compile(r"-?format-(table|list|wide|custom|hex|json|xml)|-format\s")


def guard_hard(cmd):
    c = ("\n" + cmd.lower() + " ")
    c = FORMAT_SAFE.sub(" ", c)
    for p in HARD_DENY_PATTERNS:
        if re.search(p, c):
            return "DENY"
    # «пароль» + глагол действия в одной команде = смена/создание пароля
    if re.search(r"password|passwd|парол", c) and \
       re.search(r"set|new|add|reset|change|assign|измен|смен|созда|новый|-p\b", c):
        return "DENY"
    for p in IRREV_PATTERNS:
        if re.search(p, c):
            return "CONFIRM"
    return "OK"


def tool_exec(name, args):
    """v3.15.0 «САМОУЧКА»: обёртка самообучения — каждый вызов
    инструмента записывается в ход потока (turn_track), а в конце хода
    (turn_finish) пишется урок-опыт. Само исполнение — в _tool_exec_core."""
    res = _tool_exec_core(name, args)
    try:
        turn_track(name, args, res)
    except Exception:
        pass
    return res


def _tool_exec_core(name, args):
    try:
        if name == "статус":
            return cmd_status()
        if name == "диски":
            return cmd_disks()
        if name == "место":
            return cmd_space()
        if name == "процессы":
            return cmd_processes()
        if name == "журнал":
            return cmd_journal()
        if name in ("голос", "голоса", "озвучка", "tts"):
            # v3.16.0 (Task 137): голоса — список/переключить/скачать
            return tool_voice(args)
        if name == "датчики":
            return cmd_sensors()
        if name == "роутер":
            return cmd_router(str(args.get("что") or args.get("what")
                                    or args.get("запрос") or ""))
        if name in ("торренты", "торрент", "utorrent", "раздача"):
            return cmd_torrents(str(args.get("что") or args.get("what")
                                    or args.get("запрос") or ""),
                                str(args.get("какая") or args.get("какую")
                                    or args.get("имя") or args.get("name")
                                    or ""),
                                str(args.get("файлы") or args.get("данные")
                                    or args.get("files") or ""))
        if name == "скрин":
            return "SCREENSHOT"
        if name == "найти":
            mask = str(args.get("mask", "*"))[:80]
            where = str(args.get("where", "D:\\"))[:150]
            out = ps_run(r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
Get-ChildItem -LiteralPath '%s' -Recurse -Filter '%s' -EA SilentlyContinue -ErrorAction SilentlyContinue |
  Select-Object -First 15 | ForEach-Object { $_.FullName + '  ' + [math]::Round($_.Length/1MB,2) + ' МБ' }
""" % (where.replace("'", "''"), mask.replace("'", "''")), 120)
            return out or "ничего не найдено"
        if name in ("запрос", "http", "api", "запрос_к_api", "api_запрос"):
            # v3.15.0 «САМОУЧКА» (Task 136, приказ Шефа «научи его делать
            # запросы по API»): прямой HTTP из Python — БЕЗ PowerShell.
            # Живой сбой 08.11: curl/irm в PS сыпался в stderr -> «(пусто)».
            url = str(args.get("url") or args.get("адрес")
                      or args.get("ссылка") or "").strip()[:500]
            method = str(args.get("метод") or args.get("method")
                         or "GET").strip()[:10]
            headers = args.get("заголовки") or args.get("headers") or {}
            if not isinstance(headers, dict):
                headers = {}
            body = str(args.get("тело") or args.get("body")
                       or args.get("данные") or "")[:20000]
            try:
                timeout = int(args.get("таймаут") or args.get("timeout") or 30)
            except (TypeError, ValueError):
                timeout = 30
            if not url:
                return ("нет адреса: передай url (например "
                        "http://localhost:19999/api/v3/info)")
            # законы Шефа З1/З2 — тот же страж, что у run_ps
            verdict = guard_hard(url + "\n" + body + "\n"
                                 + json.dumps(headers, ensure_ascii=False))
            if verdict == "DENY":
                journal("ЗАКОН ШЕФА: ОТКАЗ запрос: " + url[:200])
                return ("ЗАКОН ШЕФА (З1/З2): пароли и денежные операции мне "
                        "запрещены насовсем — не выполняю ни при каких "
                        "условиях. Вежливо объясни Шефу, как сделать это "
                        "самому руками.")
            if (method.upper() not in ("GET", "HEAD")
                    and re.search(r"pay|bank|checkout|transfer|invoice|карт",
                                  url.lower())):
                # З2: запись/изменение на платёжных адресах — только с «да»
                if str(args.get("confirm", "")).lower() \
                        not in ("да", "yes", "ok", "ок", "подтверждаю"):
                    return ("НУЖНО ПОДТВЕРЖДЕНИЕ ШЕФА (закон З2 — адрес похож "
                            "на платёжный, а метод меняет данные). Спроси "
                            "Шефа точным вопросом; после его явного «да» "
                            "повтори с \"confirm\":\"да\".")
            journal("запрос: %s %s" % (method.upper(), url[:200]))
            return http_api(method, url, headers, body, timeout)
        if name == "run_ps":
            # v2.3.0 «МАКС» (приказ Шефа 31.10): цензура опасных команд СНЯТА.
            # Полные права администратора: удаление, реестр, службы, установка,
            # скачивание, настройки — всё разрешено и исполняется сразу.
            # v3.0.1 «ЗАКОНЫ ШЕФА» (приказ 02.11): пароли/деньги — жёсткий
            # отказ УРОВНЕМ КОДА; необратимое — только с confirm Шефа.
            cmd = str(args.get("cmd", ""))
            if not cmd.strip():
                return "пустая команда"
            verdict = guard_hard(cmd)
            if verdict == "DENY":
                journal("ЗАКОН ШЕФА: ОТКАЗ run_ps: "
                        + cmd[:200].replace("\n", " "))
                return ("ЗАКОН ШЕФА (З1/З2): пароли и денежные операции мне "
                        "запрещены насовсем — не выполняю ни при каких "
                        "условиях. Вежливо объясни Шефу, как сделать это "
                        "самому руками.")
            if verdict == "CONFIRM" and str(args.get("confirm", "")).lower() \
                    not in ("да", "yes", "ok", "ок", "подтверждаю", "confirm"):
                journal("ЗАКОН ШЕФА: жду подтверждения: "
                        + cmd[:200].replace("\n", " "))
                return ("НУЖНО ПОДТВЕРЖДЕНИЕ ШЕФА (закон З3 — действие "
                        "необратимо). Спроси Шефа точным вопросом: что именно "
                        "будет удалено/изменено. После его явного «да» повтори "
                        "ТУ ЖЕ команду, добавив в args \"confirm\":\"да\". "
                        "Нет ответа или «нет» — не выполняй.")
            out = ps_run_diag(cmd, 180)
            journal("run_ps: " + cmd[:200].replace("\n", " "))
            return (out or "(пусто)")[:2600]
        if name in ("читать_файл", "read_file", "файл_прочитать", "прочитать_файл"):
            return file_read_text(str(args.get("путь") or args.get("path")
                                       or args.get("файл") or ""))
        if name in ("мои_файлы", "файлы", "files", "список_файлов"):
            try:
                n = int(str(args.get("сколько") or args.get("n") or 10))
            except ValueError:
                n = 10
            return files_recent(n)
        if name in ("посмотреть_файл", "view_file", "рассмотреть"):
            return file_view(str(args.get("путь") or args.get("path") or ""),
                             str(args.get("вопрос") or args.get("question")
                                 or args.get("что") or "") or None)
        if name in ("расшифровать_файл", "расшифровать", "transcribe", "asr",
                    "голос_в_текст"):
            return asr_transcribe(str(args.get("путь") or args.get("path")
                                       or args.get("файл") or ""))
        if name in ("выгрузить_файл", "сохранить_файл", "save_file", "экспорт",
                    "выгрузить"):
            return file_export(str(args.get("имя") or args.get("name") or ""),
                               str(args.get("содержимое") or
                                   args.get("content") or ""))
        if name in ("скилл_из_файла", "skill_from_file"):
            return skill_from_file(str(args.get("путь") or args.get("path") or ""),
                                   str(args.get("имя") or args.get("name") or ""))
        if name in ("отправить_файл", "послать_файл", "send_file"):
            p = str(args.get("путь") or args.get("path") or "").strip().strip('"')
            if not os.path.isfile(p):
                return "файл не найден: %s" % p
            r = send_document(p)
            journal("файл отправлен Шефу: " + p)
            return ("отправил Шефу: %s" % p) if r else \
                "не удалось отправить (см. jarvis.log)"
        if name in ("курсы", "курс", "rates"):
            return get_rates()
        if name in ("новости", "news"):
            topic = str(args.get("тема") or args.get("topic") or
                        args.get("запрос") or "")[:150]
            return news_search(topic)
        if name in ("интернет", "web_search", "поиск"):
            q = str(args.get("запрос") or args.get("query") or args.get("q")
                    or "")[:200]
            if not q:
                return "нет запроса"
            return web_search(q)
        if name in ("открыть_ссылку", "open_url", "читать"):
            u = str(args.get("url") or args.get("ссылка") or "")[:300]
            if not u:
                return "нет ссылки"
            return open_url(u)
        if name in ("найти_на_странице", "page_find", "найти_в_браузере",
                    "найти_на_сайте"):
            what = str(args.get("что") or args.get("запрос") or
                       args.get("информация") or args.get("query")
                       or "")[:300]
            u = str(args.get("url") or args.get("ссылка") or "")[:300]
            if not what:
                return "не указано, что искать"
            return page_find(what, u)
        if name in ("очистить_мусор", "очистка", "почистить", "очистить"):
            disk = str(args.get("диск") or args.get("disk") or "C").upper()[:1]
            return cmd_cleanup(disk)
        if name in ("что_перенести", "перенести_что", "анализ_диска", "что_занимает"):
            disk = str(args.get("диск") or args.get("disk") or "C").upper()[:1]
            return cmd_movable(disk)
        if name == "перенести":
            src = str(args.get("от") or args.get("src") or args.get("источник") or "")
            dst = str(args.get("куда") or args.get("dst") or args.get("назначение") or "")
            if not src or not dst:
                return "нужно указать «от» и «куда»"
            return cmd_move(src, dst)
        if name in ("запустить", "открыть_программу", "открыть"):
            app = str(args.get("app") or args.get("программа") or args.get("имя") or "")
            return cmd_run_app(app)
        if name in ("закрыть", "закрыть_программу", "убить"):
            n = str(args.get("имя") or args.get("процесс") or args.get("name") or "")
            return cmd_close_app(n)
        # v2.2.4 (Task 90): окна / мышь / клавиатура
        if name == "окна":
            import win_ctl
            return win_ctl.windows_list()
        if name == "окно":
            import win_ctl
            act = str(args.get("действие") or args.get("action") or
                      args.get("что_сделать") or "").lower().strip()
            ttl = str(args.get("окно") or args.get("заголовок") or
                      args.get("title") or "")

            def _wn(k):
                try:
                    return int(float(str(args.get(k)).strip().replace(",", ".")))
                except (TypeError, ValueError):
                    return None
            log("win_ctl: окно %s «%s»" % (act, ttl[:60]))
            return win_ctl.window_action(act, ttl, _wn("x"), _wn("y"),
                                         _wn("w"), _wn("h"))
        # v3.14.0 (Task 132): UIA — интерфейс как текст + клик по имени
        if name in ("элементы_окна", "элементы", "ui_элементы", "controls",
                    "интерфейс"):
            log("uia: элементы окна «%s»" % str(
                args.get("окно") or args.get("title") or "")[:60])
            return uia_elements(str(args.get("окно") or args.get("заголовок")
                                    or args.get("title")
                                    or args.get("программа") or ""))
        if name in ("клик_элемент", "нажать_элемент", "ui_клик",
                    "элемент_клик", "переключить_элемент"):
            _t = str(args.get("окно") or args.get("заголовок")
                     or args.get("title") or args.get("программа") or "")
            _n = str(args.get("имя") or args.get("элемент")
                     or args.get("name") or "")
            log("uia: клик «%s» в окне «%s»" % (_n[:60], _t[:60]))
            return uia_click(_t, _n)
        if name in ("область", "фрагмент", "кроп", "region"):
            def _rn2(k):
                try:
                    return int(float(str(args.get(k)).strip()
                                     .replace(",", ".")))
                except (TypeError, ValueError):
                    return None
            _x = _rn2("x")
            _y = _rn2("y")
            if _x is None or _y is None:
                return ("укажи x,y — левый верх области (физические пиксели "
                        "из описания скрина) и w,h — размер (до 1600x1200)")
            log("область: (%d,%d) %sx%s" % (_x, _y,
                                            args.get("w"), args.get("h")))
            return shot_region(_x, _y, _rn2("w") or 900, _rn2("h") or 700)
        if name == "мышь":
            import win_ctl
            act = str(args.get("действие") or args.get("action") or "").lower().strip()

            def _mn(k):
                try:
                    return int(float(str(args.get(k)).strip().replace(",", ".")))
                except (TypeError, ValueError):
                    return None
            log("win_ctl: мышь %s (%s,%s)" % (act, args.get("x"), args.get("y")))
            return win_ctl.mouse_action(act, _mn("x"), _mn("y"), _mn("x2"),
                                        _mn("y2"),
                                        args.get("сколько", args.get("amount", 0)))
        if name in ("клавиша", "клавиши", "сочетание"):
            import win_ctl
            combo = str(args.get("комбо") or args.get("сочетание") or
                        args.get("keys") or "")[:80]
            log("win_ctl: клавиша %s" % combo)
            return win_ctl.key_combo(combo)
        if name in ("печатать", "набрать", "напечатать"):
            import win_ctl
            txt = str(args.get("текст") or args.get("text") or "")[:1500]
            # v3.14.4 (Task 134): WinUI-приложения (Unigram, UWP) не имеют
            # классической каретки — «печатать» честно отказывался, хотя поле
            # в фокусе. Мозг подтверждает поле сам (клик по UIA-точке из
            # «элементы_окна» или кроп-зрением «область») и передаёт флаг.
            _force = str(args.get("обойти_каретку") or args.get("force")
                         or args.get("уверен") or "").strip().lower() \
                in ("да", "1", "true", "yes", "ок", "ok")
            log("win_ctl: печать %d симв.%s" % (len(txt),
                                                " (без каретки)" if _force else ""))
            if not txt.strip():
                # v3.8.4: живой Е2Е: генерация иногда деградирует и присылает
                # пустой текст — даём мозгу явный повод повторить одним вызовом
                return ("текст пришёл ПУСТЫМ — ничего не напечатано. Повтори "
                        "инструмент «печатать» и передай текст целиком в "
                        "этом же вызове")
            return win_ctl.type_text(txt, force=_force)
        if name in ("запомнить_программу", "запомнить", "learn_app"):
            app = str(args.get("app") or args.get("имя") or
                      args.get("программа") or "")
            pth = str(args.get("path") or args.get("путь") or "")
            return cmd_remember_app(app, pth)
        # v3.0.0 «УЧЕНИК»: скиллы + память
        if name in ("скилл", "skill", "загрузить_скилл"):
            return skill_load(args.get("имя") or args.get("name") or
                              args.get("скилл") or "")
        if name in ("запомнить_факт", "запомни_факт", "в_память", "запиши_в_память"):
            return memory_write(args.get("факт") or args.get("text") or
                                args.get("текст") or args.get("запись") or "")
        if name in ("записать_скилл", "новый_скилл", "создать_скилл"):
            return skill_write(args.get("имя") or args.get("name") or "",
                               args.get("тело") or args.get("body") or
                               args.get("текст") or args.get("инструкция") or "")
        if name in ("дневник", "diary"):
            # v3.9.0: обмены, вытесненные из окна памяти (hist_append)
            try:
                _n = int(args.get("сколько") or args.get("n") or 30)
            except Exception:
                _n = 30
            _n = max(1, min(_n, 80))
            try:
                with open(DIARYF, encoding="utf-8") as f:
                    lines = f.readlines()[-_n:]
                if not lines:
                    return "дневник пуст — старых обменов ещё не было"
                return ("ДНЕВНИК (последние %d записей до текущего окна "
                        "памяти):\n%s" % (_n, "".join(lines).strip()))
            except FileNotFoundError:
                return "дневник пуст — старых обменов ещё не было"
            except Exception as e:
                return "ошибка дневника: %s" % e
        if name == "спать":
            llm_stop("manual")
            journal("Мозг выгружен из VRAM (вызов инструмента)")
            return "OK: мозг выгружен из видеопамяти"
        if name == "проснись":
            LLM_PROC["sleeping"] = False
            LLM_PROC["reason"] = None
            try:
                os.remove(os.path.join(DATA, "BRAIN.SLEEP"))
            except OSError:
                pass
            ok = llm_start()
            return "OK: мозг снова на видеокарте" if ok else "модель не загрузилась"
        return "неизвестный инструмент: %s" % name
    except Exception as e:
        return "ошибка инструмента: %s" % e

# ---------------------------------------------------------------- зеркало каналов (Task 89)

MIRRORF = os.path.join(DATA, "mirror.jsonl")
MIRROR_LOCK = threading.Lock()


def mirror_append(ch, who, text):
    """Единый журнал переписки Telegram + локального чата 8123 (для дубля)."""
    try:
        t = str(text or "").strip()
        if not t:
            return
        with MIRROR_LOCK:
            with open(MIRRORF, "a", encoding="utf-8") as f:
                f.write(json.dumps(
                    {"ts": time.strftime("%d.%m %H:%M:%S"), "ch": ch,
                     "who": who, "text": t[:3900]},
                    ensure_ascii=False) + "\n")
            try:
                if os.path.getsize(MIRRORF) > 3000000:  # ротация ~3 МБ
                    with open(MIRRORF, encoding="utf-8") as f:
                        tail = f.readlines()[-1500:]
                    with open(MIRRORF, "w", encoding="utf-8") as f:
                        f.writelines(tail)
            except Exception:
                pass
    except Exception:
        pass


def mirror_read():
    """Все строки зеркала (отдаёт /api/messages локального чата)."""
    try:
        with open(MIRRORF, encoding="utf-8") as f:
            return f.readlines()
    except Exception:
        return []


# ---------------------------------------------------------------- мозг: диалог

def hist_load():
    try:
        with open(HISTF, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def hist_append(user_text, assistant_text):
    h = hist_load()
    h.append({"role": "user", "content": user_text[:1000],
              "ts": time.strftime("%d.%m %H:%M")})
    _a = (assistant_text or "").strip()
    # v3.9.2: АНТИ-ЗАТУХАНИЕ — обрывки («Шеф, я», «Ше…») в память НЕ
    # идут: модель копирует собственные обрывки из истории, и ответы
    # самозатухают (живой сбой 06.11 13:23: генерация 6 токенов и EOS)
    if 0 < len(_a) < 12:
        _a = "(ответ оборвался)"
    h.append({"role": "assistant", "content": _a[:1000],
              "ts": time.strftime("%d.%m %H:%M")})
    # v3.9.0 «ПАМЯТЬ ГЛУБЖЕ»: хранение 96 (было 40); вытесненное — в
    # дневник diary.jsonl (ротация ~2 МБ): старые обмены не теряются,
    # мозг поднимает их инструментом «дневник». Окно в LLM — hist_msgs.
    keep = 96
    if len(h) > keep:
        evicted = h[:len(h) - keep]
        h = h[-keep:]
        try:
            with open(DIARYF, "a", encoding="utf-8") as f:
                for m in evicted:
                    f.write(json.dumps(
                        {"ts": m.get("ts", ""), "role": m.get("role", ""),
                         "text": (m.get("content") or "")[:600]},
                        ensure_ascii=False) + "\n")
            if os.path.getsize(DIARYF) > 2000000:
                with open(DIARYF, encoding="utf-8") as f:
                    tail = f.readlines()[-1500:]
                with open(DIARYF, "w", encoding="utf-8") as f:
                    f.writelines(tail)
        except Exception:
            pass
    try:
        with open(HISTF, "w", encoding="utf-8") as f:
            json.dump(h[-keep:], f, ensure_ascii=False)
    except Exception:
        pass

def hist_msgs(h):
    out = []
    for m in h[-32:]:
        c = m.get("content", "")
        if not c:
            continue
        if m.get("role") == "assistant" and (
                len(c.strip()) < 3 or c.lstrip().startswith('{"tool"')):
            continue  # v2.2.3: отравленные реплики («Ш», сырой JSON) не берём
        # v3.8.5: служебные маркеры срывов из истории ВЫБРАСЫВАЕМ — живой
        # тест поймал мозг, подражавшему своей же реплике «(веб: ответ
        # сорвался)» из history.json: следующая генерация буквально
        # возвращала этот маркер как ответ
        if m.get("role") == "assistant" and \
                re.fullmatch(r"\((веб: ответ сорвался|"
                             r"заявил без инструмента)\)", c.strip()):
            continue
        out.append({"role": m.get("role", "user"), "content": c[:1000]})
    return out

FRESH_RE = re.compile(r"(курс|цен[аыу]|стоит|новост|новинк|погод|сегодня|сейчас|"
                      r"последни|свеж|результат|кто выиграл|матч|счёт|итог|"
                      r"произошл|случил|вышел|обновлен|прогноз)", re.I)


def _strip_md(t):
    """Убирает markdown из ответа LLM (Telegram — простой текст)."""
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"(?m)^\s*#{1,4}\s*", "", t)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"(?m)^\s*[-*]\s+", "• ", t)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    return t.strip()


# ---------------- v3.10.0: умный маршрут + старшие братья (Task 127) ----

THINK_FORCE_RE = re.compile(
    r"(?:^|\s|[,;:])(?:подумай|подумайте|с\s+подумай|серьёзно\s+подумай|"
    r"хорошенько\s+подумай|глубоко\s+подумай)", re.I)
CLOUD_RE = re.compile(
    r"спроси у старших|спроси старших|старшие братья|старший брат|"
    r"старшая сестра|у старших|облачн(?:ом|ый|ым)\s+(?:мозг|ии|модель)|"
    r"мощн(?:ее|ую)\s+(?:модель|нейросеть)", re.I)
THINK_HINT_RE = re.compile(
    r"(почему|зачем|объясни|в чём разниц|чем отлич|как устроен|как работает|"
    r"сравни|что лучше|проанализир|посчитай|вычисли|реши задач|придумай|сочини|"
    r"напиши (?:текст|статью|письмо|стих|рассказ|эссе|пост|сценарий)|"
    r"спланируй|стратеги|как думаешь|тво[ёе] мнение|предложи варианты)", re.I)


def smart_mode(text):
    """v3.14.5: ДЖАРВИС ДУМАЕТ ВСЕГДА (приказ Шефа 08.11: «Сделай чтобы
    Джарвис думал всегда! Не надо быстрых ответов, он тупит сильно,
    пусть думает нормально всегда!!!»). ЛЮБОЙ вопрос — режим «think»:
    размышления 10-30 с перед ответом. Режимы «fast» и «big» больше не
    существуют: v3.10.1 сам решал, что «простое» (привет/спасибо/
    короткое) — и отвечал бездумно за 3-8 с, что Шефу и надоело.
    Единственное исключение — явное «спроси у старших» = «cloud»
    (провал облака = своё глубокое думание, как и раньше). Свежие
    вопросы (новости/курсы) теперь тоже думают на первом шаге, а
    данные берут инструментами, как и раньше."""
    if CLOUD_RE.search(text):
        return "cloud"
    return "think"


CLOUD_LOCK = threading.Lock()
CLOUD_LAST = {"ts": 0.0}
CLOUD_SYS = ("Ты — «старший брат» Джарвиса: облачный ИИ-помощник. Джарвис — "
             "локальный ассистент Шефа на его ПК — переадресовал тебе вопрос "
             "Шефа: задача сложная или нужно второе мнение. Отвечай "
             "по-русски, развёрнуто, по делу и простым языком, без markdown "
             "и без лишних извинений.")


def cloud_ask(text, hist, msgs=None, temperature=0.6, max_tokens=None):
    """v3.10.0: бесплатный облачный «старший брат» (по умолчанию
    Pollinations — ключ не нужен; endpoint/model/key в config.json,
    можно заменить на любой OpenAI-совместимый API: GLM (z.ai),
    Mistral, DeepSeek — все доступны из РФ). Возвращает
    (ответ, None) или (None, причина_провала). Интервал ~30 с и
    обработка 402 — только бесплатному Pollinations (v3.10.1);
    429 ловим у всех. Работает и когда локальный мозг спит (игра)."""
    url = (CFG.get("cloud_api_url") or "").strip()
    if not url:
        return None, "старшие не настроены (cloud_api_url)"
    key = (CFG.get("cloud_api_key") or "").strip()
    if msgs is None:   # msgs можно передать извне
        msgs = ([{"role": "system", "content": CLOUD_SYS}] + list(hist[-8:])
                + [{"role": "user", "content": text[:4000]}])
    body = {"model": (CFG.get("cloud_model") or "openai-fast"),
            "messages": msgs, "temperature": temperature,
            "max_tokens": int(max_tokens or
                              CFG.get("cloud_max_tokens", 1200) or 1200)}
    headers = {"Content-Type": "application/json"}
    if "pollinations" in url:
        body["referrer"] = "jarvis-pc2-ПК2"
    if key:
        headers["Authorization"] = "Bearer " + key
    _poll = "pollinations" in url  # v3.10.1: лимиты бесплатного тарифа
    with CLOUD_LOCK:
        if _poll:
            _wait = 25 - (time.time() - CLOUD_LAST["ts"])
            if _wait > 0:
                time.sleep(min(_wait, 40))
        for _try in (1, 2):
            try:
                req = urllib.request.Request(
                    url, data=json.dumps(body).encode(), headers=headers)
                with urllib.request.urlopen(req, timeout=150) as r:
                    j = json.loads(r.read().decode())
                CLOUD_LAST["ts"] = time.time()
                txt = ((j.get("choices") or [{}])[0].get("message")
                       or {}).get("content") or ""
                txt = _strip_think(txt).strip()
                if txt:
                    return txt, None
                return None, "пустой ответ старших"
            except Exception as e:
                _m = str(e)
                if _try == 1 and ("429" in _m or "Too Many" in _m
                                  or (_poll and ("402" in _m
                                                 or "Payment" in _m))):
                    time.sleep(22)  # окно бесплатного тарифа — ждём и повтор
                    continue
                CLOUD_LAST["ts"] = time.time()
                return None, _m[:160]
    return None, "старшие не ответили"


# --------------------------------------------- v3.13.0 ТОЛЬКО ТЕКСТ (Task 131)

# Приказ Шефа 07.11: «оставляй только текстовую модель как изначально
# задумывалось, всё остальное — картинки, видео, кузнецов — удаляй».
# Генерация изображений (ComfyUI/FLUX/RealVisXL) и промпт-кузнец
# (Qwen2.5-3B на CPU) вырезаны полностью. Явные команды генерации
# получают честный отказ — вместо молчания или случайной картинки.
GEN_GONE_RE = re.compile(
    r"верни\s+(основн|мозг)|вернись\s+к\s+основн|"
    r"(выключи|отключи|заверши)\s+(фото|видео|генератор|режим)|"
    r"переключ\w*\s+на\s+(фото|картинк|видео)|"
    r"режим\s+(фото|видео)|(включи|запусти)\s+(фото|видео)|"
    r"(фото|видео)\s*[-—]?\s*режим|"
    r"(сделай|сгенерируй|создай|нарисуй)\s+видео|видеоролик|"
    r"^\s*быстро[!:]\s*(нарисуй|сгенерируй|создай|сделай)|"
    r"^\s*нарисуй\b|"
    r"^\s*(сгенерируй|создай|сделай)\s+(мне\s+)?(фото|картинк\w*|изображение)",
    re.IGNORECASE)
GEN_GONE_MSG = ("🎨 Генерация картинок и видео удалена (07.11, приказ Шефа — "
                "«только текстовая модель, как изначально задумано»). Я "
                "снова чистый текстовый мозг: разговариваю, думаю, ищу в "
                "интернете, читаю страницы, работаю с файлами и экраном. "
                "Нарисовать не могу — но могу найти референсы в сети или "
                "описать идею словами.")


def brain_reply(text, mode="think"):
    """v3.15.0 «САМОУЧКА»: обёртка самообучения — ход начинается
    turn_begin'ом и заканчивается turn_finish'ем: после задач с 2+
    инструментами или со сбоями в memory/lessons.json пишется урок-опыт,
    и мозг видит его в следующих промптах (lessons_block). Сама логика —
    в _brain_reply_impl (без изменений)."""
    turn_begin(text)
    try:
        ans = _brain_reply_impl(text, mode)
    except Exception:
        turn_finish("")   # сбой хода — урок без итога (опыт про сбой)
        raise
    turn_finish(ans)
    return ans


def _brain_reply_impl(text, mode="think"):
    """LLM -> (инструмент -> LLM) до 3 раз -> финальный ответ Шефу.
    v3.14.5: ДУМАЕТ ВСЕГДА (приказ Шефа 08.11) — думание на каждом
    шаге, который может стать ответом Шефу: первый заход, пасс после
    результата инструмента, скрин-пассы, short/lang-повторы. Быстрыми
    остаются только механические стражи-коррекции (фантом/руки/план/
    приказ/файл/мышь/цикл) — это внутренняя дисциплина, не ответы.
    mode: «think» — обычный путь (smart_mode теперь всегда отдаёт
    его); «cloud» — явное «спроси у старших», провал = думание."""
    hist = hist_load()
    if mode == "big" and (CFG.get("cloud_api_key") or "").strip():
        # v3.10.1 (Task 128, приказ Шефа «нужен именно МОЩНЫЙ брат»):
        # сложные вопросы — старшему брату (GLM-5.3 / Mistral Large
        # 123B в облаке, в разы умнее локальных 27B), он не занимает
        # VRAM; провал = локальное думание как раньше
        typing()
        log("СТАРШИЙ БРАТ: сложный вопрос — спрашиваю облако")
        c_ans, c_err = cloud_ask(text, hist_msgs(hist))
        if c_ans:
            hist_append(text, "[старший брат] " + c_ans[:900])
            return "🛰 Сложный вопрос — спросил у старшего брата:\n\n" \
                   + _strip_md(c_ans)
        log("СТАРШИЙ БРАТ: провал (%s) — думаю сам, глубоко" % c_err)
        send("🛰 Старший брат не на связи (%s) — включаю глубокое "
             "мышление сам." % c_err[:70])
        mode = "think"
    elif mode == "big":
        mode = "think"  # v3.10.1: ключа нет — как раньше, локально
    if mode == "cloud":
        typing()
        log("СТАРШИЕ: спрашиваю облако")
        c_ans, c_err = cloud_ask(text, hist_msgs(hist))
        if c_ans:
            hist_append(text, "[старшие братья] " + c_ans[:900])
            return "🛰 Спросил у старших братьев:\n\n" + _strip_md(c_ans)
        log("СТАРШИЕ: провал (%s) — думаю сам, глубоко" % c_err)
        send("🛰 Старшие не на связи (%s) — включаю глубокое мышление "
             "сам." % c_err[:70])
        mode = "think"
    sysmsg = {"role": "system", "content": prompt_fill(SYSTEM)}
    utext = text
    if FRESH_RE.search(text):
        utext = (text +
                 "\n(Служебное напоминание: это свежий вопрос. Для новостей вызови "
                 "инструмент «новости», для курса валют/крипты — «курсы», для "
                 "прочего свежего — «интернет». Не отвечай без данных.)")
    msgs = [sysmsg] + hist_msgs(hist) + [{"role": "user", "content": utext}]
    _hist_len = len(msgs) - 2

    def _fit(ms):
        """v3.9.0: жёсткий бюджет 28К символов — контекст 12288 не
        переполняется даже на длинных цепочках инструментов (урок
        v3.8.4: переполнение = HTTP 400 и обрыв). Режу ТОЛЬКО старую
        историю (msgs[1:1+_hist_len]), текущий обмен не трогаю."""
        nonlocal _hist_len
        while (sum(len(m.get("content", "")) for m in ms) > 28000
               and _hist_len > 0):
            ms.pop(1)
            _hist_len -= 1
        return ms

    # v3.14.5: ДУМАЕТ ВСЕГДА — первый заход всегда с размышлениями
    # (smart_mode теперь всегда отдаёт «think»); думание продолжается
    # и на пассах-ответах после инструментов (см. шаги ниже)
    ans = llm_chat(_fit(msgs), think=(mode == "think"))
    called = set()
    _rep_key = None      # v3.14.1: страж повторов (анти-цикл)
    _rep_cnt = 0
    retried_claim = False
    retried_file = False
    retried_plan = False
    retried_order = False
    retried_short = False
    retried_mouse = False   # v3.14.3: мышь-страж
    _order = bool(HANDS_ORDER_VERB_RE.search(text)
                  and HANDS_ORDER_CTX_RE.search(text))
    has_file = bool(FILE_MSG_RE.search(text) or FILE_PATH_RE.search(text))
    # v3.8.6: бюджет — стражи (фантом/руки/план) тоже едят шаги: живой
    # тест 02.11 19:59 — 3 перезапроса подряд + 4 шага действий = 7 > 5,
    # ответ обрывался на «Выполняю тест по шагам».
    # v3.14.0 (Task 132): 8 -> 12 — GUI-цепочка «окна -> окно ->
    # элементы_окна -> клик_элемент -> проверка -> ответ» + стражи
    # не влезала в 8 (живой сбой 07.11 21:43-22:01).
    for _step in range(12):
        tool = parse_tool(ans)
        if not tool:
            # v3.1.1 (Task 97): файл-страж — файл прислан, но ни один
            # инструмент не вызван = мозг выдумал содержимое.
            if has_file and not called and not retried_file:
                retried_file = True
                log("file-guard: ответ о файле без чтения — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": FILE_FIX_MSG})
                ans = llm_chat(_fit(msgs))
                continue
            # v3.14.3 (Task 133): мышь-страж — «где сейчас мышь/курсор?»
            # без инструментов зрения/мыши = выдуманные координаты
            if (MOUSE_NOW_RE.search(text) and not (called & MOUSE_NOW_TOOLS)
                    and not retried_mouse):
                retried_mouse = True
                log("mouse-guard: «где мышь» без инструмента — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": MOUSE_FIX_MSG})
                ans = llm_chat(_fit(msgs))
                continue
            # v3.1.0: трос — «сохранил/создал» без вызова = ложь (Task 96)
            _claim_fix = claim_without_tool(ans, called)
            if _claim_fix:
                if retried_claim:
                    log("claim-guard: ложь повторилась — честный отказ")
                    hist_append(text, "(заявил действие без инструмента)")
                    return ("⚠️ Тут я запнулся, Шеф: заявил действие, но не "
                            "выполнил его. Скажи ещё раз — сделаю как надо.")
                retried_claim = True
                _kind = "фантом" if _claim_fix is PHANTOM_FIX_MSG else (
                    "руки" if _claim_fix is HANDS_FIX_MSG else "файлы/память")
                log("claim-guard(%s): заявлено без инструмента — перезапрос" % _kind)
                msgs.append({"role": "assistant", "content": ans})
                # v3.8.6: мозгу идёт ИМЕННО то сообщение стража, которое
                # вернулось (руки/фантом/файлы), а не всегда CLAIM_FIX_MSG
                msgs.append({"role": "user", "content": _claim_fix})
                ans = llm_chat(_fit(msgs))
                continue
            # v3.8.2 (Task 68): план-гард — «сейчас сделаю/запущу/наберу»
            # текстом без единого инструмента = действие НЕ выполнено
            if plan_without_tool(ans, called):
                if retried_plan:
                    log("plan-guard: план повторился — отдаю ответ как есть")
                    break
                retried_plan = True
                log("plan-guard: обещание действия без инструмента — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": PLAN_FIX_MSG})
                ans = llm_chat(_fit(msgs))
                continue
            # v3.8.6: приказ-гард — Шеф приказал руки-действие, а за весь
            # ход НИ ОДНОГО руки-инструмента = приказ не выполнен
            # (живой тест 20:03: «Делаю тест по факту» текстом и конец)
            if (_order and not (called & HANDS_ACT_TOOLS)
                    and not retried_order):
                retried_order = True
                log("order-guard: приказ рук без инструмента — перезапрос")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content": HANDS_ORDER_FIX_MSG})
                ans = llm_chat(_fit(msgs))
                continue
            break
        name, args, say = tool
        called.add(name)
        # v3.14.1: СТРАЖ ПОВТОРОВ — одинаковый вызов инструмента подряд
        # (живой e2e 08.11: мышь (3348,2328) x9 — координаты за экраном,
        # модель не смотрела, что клик не работает, и сожгла весь бюджет).
        _k = name + "|" + json.dumps(args, sort_keys=True, ensure_ascii=False)
        if _k == _rep_key:
            _rep_cnt += 1
        else:
            _rep_key, _rep_cnt = _k, 1
        if _rep_cnt >= 6:
            log("repeat-guard: 6 одинаковых вызовов — честный останов")
            hist_append(text, "(застрял на повторе одинакового действия)")
            return ("⚠️ Я застрял, Шеф: шесть раз подряд одно и то же "
                    "действие не даёт результата. Остановился, чтобы не "
                    "молоть впустую. Скажи, что делать дальше — попробую "
                    "другим путём (другие координаты, клавиатура, run_ps).")
        if _rep_cnt >= 3:
            log("repeat-guard: %d одинаковых вызовов — коррекция" % _rep_cnt)
            msgs.append({"role": "assistant", "content": ans})
            msgs.append({"role": "user", "content":
                         "Служебная проверка ЦИКЛА: ты уже %d раз вызываешь "
                         "тот же инструмент с теми же аргументами — результат "
                         "не изменится. Остановись и действуй иначе: 1) вызови "
                         "«скрин» или «область» и ПОСМОТРИ, что реально на "
                         "экране и что изменилось; 2) смени координаты или "
                         "подход (клавиша, элементы_окна, run_ps); 3) или "
                         "честно ответь Шефу, что не получилось, и предложи "
                         "другой путь." % _rep_cnt})
            ans = llm_chat(_fit(msgs))
            continue
        # v3.7.0 (З5): комментарий перед исполнением — тоже речь Шефу;
        # сорвавшийся на английский say не показываем (мозг получит
        # результат инструмента в любом случае)
        if say and (_is_russian(say) or len(say.strip()) <= 40):
            send("⚙️ " + say[:300])
        if name not in ("спать", "проснись"):
            typing()
        res = tool_exec(name, args)
        if name == "спать":
            hist_append(text, "мозг выгружен из VRAM")
            return ((say + "\n") if say else "") + \
                "😴 Мозг выгружен из видеопамяти — VRAM свободна для игр. " \
                "«проснись» — верну обратно."

        if res == "SCREENSHOT":
            # v3.14.0 (Task 132): «скрин» — ПРОМЕЖУТОЧНЫЙ инструмент, а НЕ
            # конец хода. Раньше описание улетало Шефу финальным ответом, и
            # многошаговые задачи («измени настройку в программе») умирали
            # здесь ВСЕГДА (живой цикл 07.11 21:45-22:01 — пять ходов
            # подряд умерли на скрине, до кликов не дошло ни разу).
            path = take_shot()
            if not path:
                why = ("экран залочен (Win+L) — Windows прячет картинку"
                       if _station_locked() else "ошибка захвата, см. jarvis.log")
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content":
                             "Результат инструмента «скрин»: НЕ удался — %s. "
                             "Продолжай другим путём (окно/элементы_окна/"
                             "run_ps) или честно ответь Шефу." % why})
                ans = llm_chat(_fit(msgs), think=True)  # v3.14.5: всегда
                continue
            if not vision_available():
                send_photo(path, caption="📸 Экран (зрение не загружено — просто фото)")
                os.remove(path)
                msgs.append({"role": "assistant", "content": ans})
                msgs.append({"role": "user", "content":
                             "Результат инструмента «скрин»: фото отправлено "
                             "Шефу, но зрение не загружено — описать не могу. "
                             "Продолжай без картинок (элементы_окна/run_ps) "
                             "или честно ответь Шефу."})
                ans = llm_chat(_fit(msgs), think=True)  # v3.14.5: всегда
                continue
            typing()
            try:
                desc = llm_vision(path, ui=True)
            except Exception as e:
                log("vision ERR: %s" % e)
                desc = ""
            _cur = SHOT_CURSOR  # v3.14.2: где мышь — точные пиксели из ОС
            send_photo(path, caption=("📸 Экран ПК2, "
                        + time.strftime("%d.%m %H:%M")
                        + ((" | 🖱 мышь: %d, %d" % (_cur["x"], _cur["y"]))
                           if _cur else "")))
            os.remove(path)
            msgs.append({"role": "assistant", "content": ans})
            msgs.append({"role": "user", "content":
                         "Результат инструмента «скрин» (фото уже ушло Шефу)."
                         "%s\nЧто вижу на экране:\n%s\n\n"
                         "Это ПРОМЕЖУТОЧНЫЙ взгляд — задачу Шефа продолжай: "
                         "следующий JSON (клик_элемент/область/мышь/клавиша/"
                         "печатать/элементы_окна) или, если всё сделано, "
                         "финальный ответ по-русски обычным текстом. "
                         "ВНИМАНИЕ: координаты в описании ПРИБЛИЗИТЕЛЬНЫ "
                         "(картинка сжата) — для точного клика по кнопке "
                         "вызови «область» вокруг неё, там 1:1; после клика "
                         "обязательно проверь результат новым скрин/область."
                         % (_cursor_note(), desc or
                            "(не смог разобрать снимок — используй "
                            "«элементы_окна» или «мышь» по описанию)")})
            ans = llm_chat(_fit(msgs), think=True)  # v3.14.5: всегда
            continue

        typing()
        msgs.append({"role": "assistant", "content": ans})
        msgs.append({"role": "user", "content":
                     "Результат инструмента «%s»:\n%s\n\n"
                     "Если данных достаточно — ответь Шефу по-русски, коротко и по делу, "
                     "обычным текстом без JSON. Если нужен ещё один инструмент — "
                     "ответь снова одним JSON-объектом."
                     % (name, str(res)[:3000])})
        # v3.14.5: пасс после инструмента тоже ДУМАЕТ — здесь рождается
        # и финальный ответ Шефу, и следующий шаг цепочки
        ans = llm_chat(_fit(msgs), think=True)

    clean = _strip_md(ans)
    # v3.9.2: АНТИ-ЗАТУХАНИЕ — короткий обрывок («Шеф, я», 3-11 симв.,
    # не JSON) = генерация сорвалась. Один перезапрос с требованием
    # ответить полно; останется коротким — честная замена ниже.
    if (3 <= len(clean.strip()) < 12
            and not clean.lstrip().startswith('{"tool"')
            and not retried_short):
        retried_short = True
        log("short-guard: ответ оборвался (%r) — перезапрос" % clean[:40])
        msgs.append({"role": "assistant", "content": ans})
        msgs.append({"role": "user", "content":
                     "Твой прошлый ответ оборвался на полуслове. Ответь "
                     "Шефу ПОЛНОСТЬЮ: что именно ты видишь или собираешься "
                     "делать, и вызови нужный инструмент, если он нужен "
                     "(скриншот/зрение для того, что на экране)."})
        ans = llm_chat(_fit(msgs), think=True)  # v3.14.5: думает и тут
        clean = _strip_md(ans)
    if len(clean.strip()) < 3 or clean.lstrip().startswith('{"tool"'):
        log("brain_reply: дегенеративный ответ (%r) — честный финал" % clean[:60])
        hist_append(text, "(не успел доделать за лимит шагов — «продолжай»)")
        return ("⚠️ Я сделал много шагов, но не успел доделать до конца, "
                "Шеф. Скажи «продолжай» — доделаю с места, где остановился.")
    # v3.7.0: языковой страж (З5) — ответ без кириллицы переспрашиваем
    # один раз; остаётся английским — честный русский отказ.
    if not _is_russian(clean):
        log("lang-guard: ответ без русского (%r) — перезапрос" % clean[:60])
        journal("З5: ответ сорвался не на русский — перезапрос")
        msgs.append({"role": "assistant", "content": ans})
        msgs.append({"role": "user", "content": LANG_FIX_MSG})
        ans2 = llm_chat(_fit(msgs), think=True)  # v3.14.5: думает и тут
        clean2 = _strip_md(ans2)
        if _is_russian(clean2) and len(clean2.strip()) >= 3:
            ans, clean = ans2, clean2
        else:
            hist_append(text, "(ответ сорвался на английский)")
            return ("⚠️ Сорвался тут на английский, Шеф — а по закону З5 говорю "
                    "только по-русски. Переспроси, отвечу как положено.")
    hist_append(text, clean)
    return clean or "…"

# ---------------------------------------------------------------- обработка

HELP = ("🤖 *ДЖАРВИС v3.17 — ТЕКСТОВЫЙ МОЗГ*\n\n"
        "Мозг — Qwen3.8-27B прямо на твоей видеокарте, без облака. Пиши "
        "обычным языком — я сам пойму, что сделать.\n\n"
        "*Действия:*\n"
        "«освободи диск C» — чищу мусор и кэши\n"
        "«что можно перенести с C» — анализирую и подсказываю\n"
        "«перенеси Downloads на D» — переношу любые папки\n"
        "«запусти <что угодно>» — открываю ЛЮБЫЕ программы и игры\n"
        "«закрой хром» — закрываю любой процесс\n"
        "«включи/выключи настройку в программе» — сам открою, найду галочку и переключу\n"
        "«выполни <команду>» — полные права администратора\n\n"
        "*Игры и видеокарта:*\n"
        "Запускаешь игру — я САМ выгружаюсь из видеопамяти и возвращаюсь "
        "после. Ярлыки на рабочем столе: «Освободить видеокарту» / «Вернуть мозг».\n\n"
        "*Быстрые команды:* статус, диски, место, большие, процессы, скрин, "
        "журнал, пинг, спать, проснись, выкл, перезагрузка, помощь\n\n"
        "*Голос:* «ответь голосом» в любом месте запроса — ответ придёт "
        "голосовым сообщением (можно с именем: «ответь голосом ксении»). "
        "«голоса» — какие есть, «голос евгений» — сменить основной, "
        "«поставь silero» — самые натуральные голоса: Ксения, Ксеня, "
        "Байя, Евгений, Айдар.\n\n"
        "*Умный режим:* простое — мгновенно; слово «подумай» — глубоко "
        "думаю сам (10-30 с); сложный вопрос — сперва спрашиваю старшего "
        "брата в облаке (если подключён — он мощнее меня; подключён, "
        "если у меня есть его ключ).\n\n"
        "*Старшие братья:* «спроси у старших» — облачный мозг (второе "
        "мнение), работает даже когда я сплю из-за игры.\n\n"
        "*Интернет и API:* «что нового в мире», «курс биткоина», «погода в Москве» — "
        "найду свежее в сети. «найди на странице/сайте …» — читаю текст "
        "страницы (из ссылки или прямо из браузера) и выписываю точные "
        "строки, а не «что вижу на картинке». Любой API (Netdata-мониторинг, "
        "роутер, сервисы) — опрошу напрямую и по делу.\n\n"
        "Или просто поговори со мной 😊")

def handle(text, chat_id):
    # v3.16.0 (Task 137, наследие приказа Шефа 09.11) «ОТВЕТЬ ГОЛОСОМ»:
    # фраза «ответь голосом [имя]» вырезается ДО разбора команд и мозга —
    # финальный ответ уйдёт голосовым (silero/piper). Покрывает и расшифровки
    # голосовых, и подписи к файлам (слова Шефа мозгу не нужны).
    _orig = text
    text, _want_voice, _vname = voice_split(text)
    if _want_voice and not text.strip():
        return send("🎙 Слушаю! Что озвучить? Повтори вопрос и добавь "
                    "в него «ответь голосом».", chat_id)
    t = text.strip().lower()
    log("cmd: " + t[:80] + (" [голосом%s]"
                            % (" " + _vname if _vname else "")
                            if _want_voice else ""))
    # зеркало видит исходный текст (с фразой) — честная запись сказанного
    mirror_append("tg", "boss", _orig)
    if PENDING["action"] and time.time() - PENDING["ts"] < 120:
        if t in ("да", "yes", "ок", "ok", "подтверждаю", "confirm"):
            return send(power_do(PENDING["action"]), chat_id)
        if "отмен" in t:
            PENDING["action"] = None
            return send("👌 Отменено.", chat_id)
        PENDING["action"] = None
    # ---- точные быстрые команды (всё остальное решает мозг) ----
    if t in ("/start", "/help") or t in ("помощь", "хелп", "help", "начало"):
        return send(HELP, chat_id, voice=_want_voice)
    if t in ("статус", "/status", "стат"):
        return send(cmd_status(), chat_id, voice=_want_voice)
    if t in ("диски", "/disks", "smart", "смарт"):
        return send(cmd_disks(), chat_id, voice=_want_voice)
    if t in ("место", "/space", "свободное место"):
        return send(cmd_space(), chat_id, voice=_want_voice)
    if t in ("процессы", "/ps", "проц"):
        return send(cmd_processes(), chat_id, voice=_want_voice)
    if t in ("журнал", "лог"):
        return send(cmd_journal(), chat_id, voice=_want_voice)
    if t in ("пинг", "/ping", "живой"):
        return send("🏓 Джарвис жив. Аптайм процесса: %s" %
                    time.strftime("%H:%M:%S", time.gmtime(time.time() - BIRTH)),
                    chat_id, voice=_want_voice)
    if t.startswith("скрин") or t == "/shot":
        r = cmd_shot()
        if r:
            send(r, chat_id, voice=_want_voice)
        return
    if t.startswith("больш"):
        return send(cmd_bigfolders(), chat_id, voice=_want_voice)

    # ---- v3.16.0 (Task 137): голоса — команды до мозга ----
    if t in ("голоса", "голос", "какие голоса", "какие голоса есть",
             "какой голос", "какой голос сейчас", "/voices"):
        return send(voices_help(), chat_id)
    # ---- v3.17.0 (Task 138): «поставь silero» — установка до мозга ----
    if SILERO_INSTALL_RE.match(t):
        if silero_ready():
            return send("✅ Silero уже стоит и работает. Голоса: %s. "
                        "Основной — %s."
                        % (", ".join(voice_display(n)
                                     for n in SILERO_VOICES),
                           voice_display(voice_cur_name())), chat_id)
        silero_install_async(chat_id)
        return send("⬇️ Ставлю silero: torch (~200 МБ) + модель v5_6_ru "
                    "(141 МБ) — несколько минут. Как встанет — доложу "
                    "голосом в новом тембре.", chat_id)
    m = VOICE_CMD_RE.match(t)
    if m:
        _w = str(m.group(1)).strip().lower()
        _nm = next((_f for _s, _f in VOICE_NAME_STEMS.items()
                    if _w.startswith(_s)), None)
        if _nm:   # слово — имя голоса: команда наша
            _msg, _ok = voice_switch_cmd(_nm)
            return send(_msg, chat_id, voice=bool(_ok), voice_name=_ok)
        # не имя («поприятнее» и т.п.) — решает мозг (инструмент «голос»)
    m = VOICE_GET_RE.match(t)
    if m:
        _w = str(m.group(1)).strip().lower()
        _nm = next((_f for _s, _f in VOICE_NAME_STEMS.items()
                    if _w.startswith(_s)), None)
        if _nm:
            if _nm in SILERO_VOICES:   # v3.17.0: silero-голоса
                if silero_ready():
                    return send("Голоса silero уже установлены — все пять "
                                "сразу: %s. Основной — %s; скажи «голос "
                                "%s»."
                                % (", ".join(SILERO_VOICES),
                                   voice_display(voice_cur_name()), _nm),
                                chat_id)
                silero_install_async(chat_id, _nm)
                return send("⬇️ Ставлю silero с голосом %s (torch ~200 МБ "
                            "+ модель 141 МБ) — докладу голосом."
                            % voice_display(_nm), chat_id)
            if voice_catalog().get(_nm):
                return send("Голос %s уже скачан — скажи «голос %s», чтобы "
                            "сделать его основным."
                            % (voice_display(_nm), _nm), chat_id)
            voice_download_async(_nm, chat_id)
            return send("⬇️ Качаю голос %s (~63 МБ, piper). Как будет "
                        "готов — доложу сам, послушай."
                        % voice_display(_nm), chat_id)
        # не имя — пусть решает мозг («скачай голос поприятнее» и т.п.)

    # ---- v3.13.0 (Task 131): генерация удалена — честный отказ ----
    if GEN_GONE_RE.search(text):
        return send(GEN_GONE_MSG, chat_id)

    if "выкл" in t or "shutdown" in t:
        return send(power_confirm("off"), chat_id)
    if "перезагруз" in t or "reboot" in t or "restart" in t:
        return send(power_confirm("reboot"), chat_id)
    if "спать" in t or t in ("сон", "sleep", "усни"):
        llm_stop("manual")
        journal("Мозг выгружен из VRAM по команде Шефа («спать»)")
        return send("😴 Мозг выгружен из видеопамяти — VRAM свободна для игр.\n"
                    "«проснись» — верну (загрузка ~минуты).", chat_id)
    if "проснись" in t or "проспись" in t or "подъём" in t or "wake" in t:
        LLM_PROC["sleeping"] = False
        LLM_PROC["reason"] = None
        try:
            os.remove(os.path.join(DATA, "BRAIN.SLEEP"))
        except OSError:
            pass
        send("☕ Загружаю мозг в видеопамять...", chat_id)
        ok = llm_start()
        journal("Мозг загружен в VRAM по команде Шефа («проснись»): %s" % ok)
        return send("🧠 Мозг на месте." if ok else
                    "⚠️ Не смог загрузить модель — глянь jarvis.log / llama.log.", chat_id)

    # ---------- всё остальное: свободное общение с мозгом ----------
    # v3.14.5: маршрут упрощён приказом Шефа «думает ВСЕГДА»:
    # любой вопрос -> «think» (размышления), кроме явного «спроси у
    # старших» -> «cloud»
    _mode = smart_mode(text)
    if LLM_PROC["sleeping"]:
        # старшие братья живут в облаке и не занимают VRAM:
        # отвечают даже когда локальный мозг спит (игра)
        if _mode == "cloud" or (_mode == "big" and
                                (CFG.get("cloud_api_key") or "").strip()):
            # v3.10.1: и авто-сложные вопросы уходят брату, даже когда
            # локальный мозг спит из-за игры (облако VRAM не занимает)
            typing(chat_id)
            c_ans, c_err = cloud_ask(text, [])
            if c_ans:
                hist_append(text, "[старшие, мозг спал] " + c_ans[:900])
                return send("🛰 (локальный мозг спит — игра? Старшие "
                            "ответили так:)\n\n" + _strip_md(c_ans),
                            chat_id, voice=_want_voice, voice_name=_vname)
            return send("😴 Мозг спит, а старшие не на связи (%s). "
                        "«проснись» — подниму локальный." % c_err[:60],
                        chat_id, voice=_want_voice, voice_name=_vname)
        why = " — идёт игра, сам вернусь после её закрытия" if LLM_PROC.get("reason") == "game" else ""
        return send("😴 Мозг спит — видеопамять свободна%s. Быстрые команды работают. "
                    "«проснись» — загружу обратно." % why, chat_id)
    typing(chat_id)
    if _mode != "cloud" and not llm_ensure():
        return send("⚠️ Мозг не отвечает и не завёлся. Записал в jarvis.log.", chat_id)
    try:
        ans = brain_reply(text.strip(), _mode)
        if ans:
            # v3.16.0: голосом по фразе (имя — разовый голос, иначе основной)
            send(ans, chat_id, voice=_want_voice, voice_name=_vname)
    except Exception:
        log("brain ERR:\n" + traceback.format_exc())
        send("⚠️ Мозг споткнулся — записал в лог.", chat_id)

# ---------------------------------------------------------------- циклы

def polling_loop():
    log("polling запущен")
    poll_fail = 0  # v3.3.0: счётчик сбоев сети подряд (бэкофф)
    while True:
        try:
            off = 0
            if os.path.exists(OFFF):
                with open(OFFF) as f:
                    off = int(f.read().strip() or 0)
            r = tg("getUpdates", {"offset": off, "timeout": 25,
                                  "allowed_updates": ["message"]}, timeout=40)
            poll_fail = 0
            for u in r.get("result", []):
                with open(OFFF, "w") as f:
                    f.write(str(u["update_id"] + 1))
                m = u.get("message") or {}
                cid = str((m.get("chat") or {}).get("id", ""))
                if cid not in ALLOWED:
                    log("чужой chat %s — игнор" % cid)
                    continue
                text = m.get("text") or ""
                if not text:
                    # v3.1.0 «ФАЙЛЫ»: документы/фото/аудио/видео — скачать
                    # и отдать мозгу с путём; голос пока без расшифровки.
                    doc = m.get("document")
                    photo = m.get("photo")
                    audio = m.get("audio")
                    video = m.get("video")
                    cap = (m.get("caption") or "").strip()
                    if doc:
                        p, sz = tg_download(doc.get("file_id"),
                                            doc.get("file_name"))
                        if p:
                            text = ("Шеф прислал файл «%s» (%s, %s) — я его уже "
                                    "скачал: %s%s. Содержимого файла у тебя "
                                    "НЕТ: ответ о нём без инструмента — "
                                    "выдумка и ложь. Реши сам и сделай сразу: "
                                    "прочитать («читать_файл» с этим путём), "
                                    "сделать скилл («скилл_из_файла»), обработать. "
                                    "Неясно — один короткий вопрос Шефу."
                                    % (doc.get("file_name") or "файл",
                                       doc.get("mime_type") or "?",
                                       _fmt_size(sz), p,
                                       ("; подпись: " + cap) if cap else ""))
                        else:
                            send("⚠️ Не смог скачать файл — записал в журнал.", cid)
                    elif photo and isinstance(photo, list):
                        big = photo[-1]
                        p, sz = tg_download(big.get("file_id"),
                                            "фото_%s.jpg" %
                                            time.strftime("%Y%m%d_%H%M%S"))
                        if p:
                            text = ("Шеф прислал фото: %s%s. Содержимого у тебя "
                                    "НЕТ: сначала посмотри зрением "
                                    "(«посмотреть_файл») и ответь по существу "
                                    "снимка, а не наугад."
                                    % (p, ("; подпись: " + cap) if cap else ""))
                    elif audio or video:
                        kind = "аудио" if audio else "видео"
                        src = audio or video
                        is_voice = bool(m.get("voice"))
                        p, sz = tg_download(
                            src.get("file_id"),
                            src.get("file_name") or
                            ("голосовое_%s.ogg" %
                             time.strftime("%Y%m%d_%H%M%S") if is_voice else None))
                        if p:
                            # v3.2.0 «ГОЛОС»: расшифровываем локальным
                            # whisper.cpp (голосовые ogg -> ffmpeg -> wav).
                            tr = asr_transcribe(p, timeout=300)
                            if tr and not tr.startswith(("не смог", "движок",
                                                         "ошибка", "распознавание",
                                                         "файл не найден")):
                                # v3.2.0: путь в текст НЕ указываем — расшифровка
                                # уже сделана, страж путей не должен требовать
                                # повторного инструмента (путь — в журнал)
                                text = ("Шеф прислал голосовое (%s), расшифровка: "
                                        "«%s». Ответь по смыслу сказанного."
                                        % (_fmt_size(sz), tr))
                                journal("голосовое расшифровано: " + p)
                            else:
                                text = ("Шеф прислал %s-файл: %s (%s). "
                                        "Расшифровать не вышло (%s) — спроси "
                                        "Шефа, что с ним сделать."
                                        % (kind, p, _fmt_size(sz), tr[:120]))
                    if not text:
                        send("Пока понимаю только текст, файлы, фото и голос. "
                             "Видео-файлы без звука — в одной из следующих "
                             "фаз 🎤", cid)
                        continue
                try:
                    handle(text, cid)
                except Exception:
                    log("handle ERR:\n" + traceback.format_exc())
                    send("⚠️ Ошибка выполнения команды — записал в журнал.", cid)
        except Exception as e:
            # v3.3.0: сеть до Telegram моргает кластерами (10060/10054/
            # таймауты рукопожатия) — короткий лог + бэкофф вместо
            # многострочных простыней Windows и слепых 5-секундных пауз
            et = str(e)
            poll_fail += 1
            m10060 = re.search(r"\[WinError (\d+)\]", et)
            short = ("WinError " + m10060.group(1)) if m10060 else et[:70]
            netish = ("10060" in et or "10054" in et or "timed out" in et
                      or "handshake" in et or "closed" in et.lower())
            if netish:
                log("poll ERR сеть x%d: %s (бэкофф %dc)"
                    % (poll_fail, short, min(2 * poll_fail, 30)))
                if poll_fail in (1, 20, 100):  # полный текст — редко
                    log("poll ERR (полный): %s" % et)
            else:
                log("poll ERR: %s" % et)
            time.sleep(min(2 * poll_fail, 30))

def watchdog_loop():
    last_alert = {}
    log("watchdog запущен")
    while True:
        try:
            out = ps_run(r"""
Get-PSDrive C,D,E | ForEach-Object { "{0}={1:N1}" -f $_.Name,($_.Free/1GB) }
""", timeout=60)
            for ln in out.splitlines():
                if "=" not in ln:
                    continue
                drv, free = ln.split("=", 1)
                try:
                    fr = float(free.replace(",", "."))
                except ValueError:
                    continue
                # E: — там Загрузки/файлы: порог ниже, спамить нечестно
                lim = {"c": 10.0, "d": 10.0, "e": 1.0}.get(drv.lower(), 10.0)
                if fr < lim and time.time() - last_alert.get(drv, 0) > 3600:
                    last_alert[drv] = time.time()
                    send("🚨 *Мало места!* Диск %s: свободно %.1f ГБ. "
                         "Спроси меня: «что можно перенести с C» — подскажу." % (drv, fr))
                    journal("Алерт: мало места на %s (%.1f ГБ)" % (drv, fr))
        except Exception:
            log("watchdog ERR:\n" + traceback.format_exc())
        time.sleep(300)

def events_loop():
    """v3.4.0 «СОБЫТИЯ»: фоновые наблюдения — RAM на исходе, перегрев
    (термозона ACPI), GPU под полной нагрузкой долго, игра долго грузится/
    зависла. Уведомляет Шефа с кулдаунами, каждое событие — в журнал."""
    log("events запущен")
    ram_low = hot = gpu_hi = gpu_hot = None
    game_seen = {}
    last_alert = {}

    def alert(key, text, cooldown=3600):
        if time.time() - last_alert.get(key, 0) < cooldown:
            return
        last_alert[key] = time.time()
        send("📡 " + text)
        journal("Событие: " + text)

    while True:
        try:
            games = game_procs() if CFG.get("game_auto_vram", True) else set()
            now = time.time()
            for g in games:
                game_seen.setdefault(g, now)
            for g in list(game_seen):
                if g not in games:
                    del game_seen[g]
            out = ps_run(r"""
$os = Get-CimInstance Win32_OperatingSystem
"RAM={0:N1}|{1:N1}" -f ($os.FreePhysicalMemory/1MB),($os.TotalVisibleMemorySize/1MB)
try { $t=(Get-CimInstance -Namespace root/WMI -Class MSAcpi_ThermalZoneTemperature -EA Stop | Select-Object -First 1).CurrentTemperature; "THRM={0:N1}" -f ($t/10.0-273.15) } catch { "THRM=no" }
try { $g=(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -EA Stop | Measure-Object UtilizationPercentage -Sum).Sum; "GPU={0:N0}" -f $g } catch { "GPU=no" }
""", timeout=90)
            ram_free = ram_tot = thrm = gpu = None
            for ln in out.splitlines():
                if ln.startswith("RAM=") and "|" in ln:
                    try:
                        ram_free, ram_tot = (float(x.replace(",", "."))
                                             for x in ln[4:].split("|"))
                    except ValueError:
                        pass
                elif ln.startswith("THRM="):
                    if ln[5:] != "no":
                        try:
                            thrm = float(ln[5:].replace(",", "."))
                        except ValueError:
                            pass
                elif ln.startswith("GPU="):
                    if ln[4:] != "no":
                        try:
                            gpu = float(ln[4:].replace(",", "."))
                        except ValueError:
                            pass
            # RAM: меньше 4 ГБ свободных 5 минут подряд
            if ram_free is not None and ram_free < 4.0:
                ram_low = ram_low or now
                if now - ram_low > 300:
                    alert("ram", "Оперативка почти кончилась: свободно "
                          "%.1f ГБ из %.0f. Скажи «процессы» — посмотрю, "
                          "что жрёт, и закрою лишнее." % (ram_free, ram_tot or 32),
                          cooldown=6 * 3600)
            else:
                ram_low = None
            # термозона ACPI (чипсет/VRM платы): выше 75°C 5 минут
            if thrm is not None and thrm > 75.0:
                hot = hot or now
                if now - hot > 300:
                    alert("thrm", "Термозона материнской платы %.0f°C — "
                          "проверь охлаждение и пыль." % thrm,
                          cooldown=6 * 3600)
            else:
                hot = None
            # v3.5.0: реальная температура GPU из HWiNFO (SM2)
            gpu_temp = None
            try:
                import hwinfo_sensors as _hw
                for _r in _hw.read_all():
                    if (_r["sensor"].startswith("GPU") and _r["type"] == "темп"
                            and _r["label"].strip().lower() in
                            ("gpu temperature", "gpu tctl", "gpu die")):
                        gpu_temp = _r["value"]
                        break
            except Exception:
                pass
            # GPU: полная нагрузка 15+ минут — справка с температурой
            if gpu is not None and gpu > 85.0:
                gpu_hi = gpu_hi or now
                if now - gpu_hi > 900:
                    t = (" GPU сейчас %d°C." % gpu_temp
                         if gpu_temp is not None else
                         " Температуру скажу по «датчики».")
                    alert("gpu", "Видеокарта под полной нагрузкой уже %d мин.%s"
                          % ((now - gpu_hi) / 60, t), cooldown=12 * 3600)
            else:
                gpu_hi = None
            # GPU перегрев: реальные °C (просьба Шефа 02.11 — HWiNFO)
            if gpu_temp is not None and gpu_temp > 85.0:
                gpu_hot = gpu_hot or now
                if now - gpu_hot > 300:
                    alert("gputemp", "Видеокарта %.0f°C уже %d мин — проверь "
                          "охлаждение и пыль. «датчики» — полная сводка."
                          % (gpu_temp, (now - gpu_hot) / 60), cooldown=6 * 3600)
            else:
                gpu_hot = None
            # игра молода (<40 мин), но GPU почти не грузится 10+ минут:
            # возможно, долго грузится или зависла
            if games and gpu is not None and gpu < 8.0:
                for g, t0 in list(game_seen.items()):
                    if 600 < now - t0 < 2400:
                        alert("stall." + g,
                              "Игра %s работает %.0f мин, но GPU почти не "
                              "грузится — возможно, долго грузится или "
                              "зависла. Скажи «скрин» — посмотрю, что там."
                              % (g, (now - t0) / 60), cooldown=3600)
        except Exception:
            log("events ERR:\n" + traceback.format_exc())
        time.sleep(120)

def briefing_loop():
    sent_day = None
    while True:
        try:
            now = time.localtime()
            today = time.strftime("%Y-%m-%d", now)
            if now.tm_hour == 8 and sent_day != today:
                sent_day = today
                st = cmd_status()
                extra = ""
                if llm_health():
                    extra = "\n🧠 Мозг: нагружен и готов."
                elif LLM_PROC["sleeping"]:
                    extra = "\n😴 Мозг: спит (VRAM свободна)."
                send("🌅 *Доброе утро, Шеф!* Брифинг 08:00\n\n" + st + extra +
                     "\n\nХорошего дня! 🤖")
                journal("Утренний брифинг отправлен")
        except Exception:
            log("briefing ERR:\n" + traceback.format_exc())
        time.sleep(600)

def chat_watchdog():
    """v2.2.3: локальный чат 127.0.0.1:8123 жив (автоперезапуск ≤60 с)."""
    log("chat-watch запущен (локальный чат 8123)")
    while True:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8123/health",
                                        timeout=5) as r:
                ok = (r.status == 200)
        except Exception:
            ok = False
        if not ok:
            try:
                subprocess.Popen(
                    [sys.executable,
                     os.path.join(BASE, "chat", "chat_server.py")],
                    cwd=os.path.join(BASE, "chat"),
                    creationflags=0x08000000)
                log("chat-watch: локальный чат не отвечал — перезапустил")
            except Exception:
                log("chat-watch ERR:\n" + traceback.format_exc())
        time.sleep(60)


# ---------------------------------------------------------------- v3.9.0 самопроверка

def _selftest_image():
    """Тест-картинка «ТЕСТ 7391» для проверки зрения (PIL -> PS)."""
    p = os.path.join(DATA, "selftest_img.png")
    try:
        from PIL import Image, ImageDraw, ImageFont
        im = Image.new("RGB", (460, 150), "white")
        d = ImageDraw.Draw(im)
        try:
            f = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 52)
        except Exception:
            f = ImageFont.load_default()
        d.text((25, 40), "ТЕСТ 7391", fill="black", font=f)
        im.save(p)
        return p
    except Exception:
        pass
    try:
        ps_run(r"""
Add-Type -AssemblyName System.Drawing
$bmp=New-Object System.Drawing.Bitmap 460,150
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.Clear('White')
$f=New-Object System.Drawing.Font('Arial',40,[System.Drawing.FontStyle]::Bold)
$g.DrawString('ТЕСТ 7391',$f,[System.Drawing.Brushes]::Black,20,40)
$bmp.Save('%s',[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose();$bmp.Dispose();'OK'
""" % p.replace("'", "''"), timeout=45)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            return p
    except Exception:
        pass
    return None


def _run_selftest():
    """v3.9.0 «САМОПРОВЕРКА»: живой прогон стражей, мозга, зрения,
    поиска, файлов и связи. SKIP — не тревога (мозг спит / зрения нет);
    FAIL — сообщение Шефу + журнал. Полный отчёт — в jarvis.log."""
    res = {}

    def check(name, fn):
        try:
            res[name] = str(fn())
        except Exception as e:
            res[name] = "FAIL: %s" % e

    def t_guards():
        # юнит-тесты стражей честности (уроки Task 97/104/107/68)
        assert claim_without_tool(
            "я сохранил файл отчёт в папку", set()), "файл-трос молчит"
        assert claim_without_tool(
            "передвинул курсор в (2500,1200), проверено", set()), \
            "руки-трос молчит"
        assert claim_without_tool(
            "инструмент вернул «НЕ подтвердилось»", set()), \
            "фантом-страж молчит"
        assert plan_without_tool(
            "Сейчас сделаю: запущу блокнот и наберу текст.", set()), \
            "план-гард молчит"
        assert claim_without_tool(
            "погода сегодня хорошая", set()) is None, \
            "трос ложно срабатывает"
        return "OK (4 стража)"

    def t_brain():
        if LLM_PROC["sleeping"] or os.path.exists(
                os.path.join(DATA, "BRAIN.SLEEP")):
            return "SKIP (мозг спит — VRAM для игры)"
        if not llm_health():
            return "FAIL: llama-server не отвечает /health"
        ans = llm_chat([{"role": "user",
                         "content": "Ответь ровно одним словом: привет"}],
                       max_tokens=30)
        return "OK" if len(ans.strip()) >= 3 else "FAIL: пустой ответ"

    def t_vision():
        if LLM_PROC["sleeping"]:
            return "SKIP (мозг спит)"
        if not vision_available():
            return "SKIP (зрение не загружено — не хватило VRAM)"
        img = _selftest_image()
        if not img:
            return "SKIP (тест-картинка не создалась)"
        try:
            desc = llm_vision(img, question="Какие ЦИФРЫ написаны на "
                                            "картинке? Ответь только цифрами.")
            return "OK" if "7391" in desc else \
                "FAIL: не прочитало (%s)" % desc[:60]
        finally:
            try:
                os.remove(img)
            except OSError:
                pass

    def t_web():
        r = web_search("новости сегодня", n=3)
        return "OK" if (len(r) > 60 and "не дал результатов" not in r) \
            else "FAIL: %s" % r[:80]

    def t_files():
        p = os.path.join(DATA, "selftest_проверка.txt")
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write("содержимое теста 7391")
            txt = file_read_text(p)
            return "OK" if "7391" in txt else \
                "FAIL: прочиталось не то (%s)" % txt[:60]
        finally:
            try:
                os.remove(p)
            except OSError:
                pass

    def t_tg():
        try:
            r = tg("getMe")
        except Exception as e:
            return "FAIL: %s" % e
        if r.get("ok"):
            return "OK (@%s)" % ((r.get("result") or {}).get("username") or "?")
        return "FAIL: %s" % r

    for _n, _f in (("стражи", t_guards), ("мозг", t_brain),
                   ("зрение", t_vision), ("поиск", t_web),
                   ("файлы", t_files), ("связь", t_tg)):
        check(_n, _f)

    report = (time.strftime("%d.%m.%Y %H:%M") + " САМОПРОВЕРКА:\n"
              + "\n".join("- %s: %s" % (k, v) for k, v in res.items()))
    log(report.replace("\n", " | "))
    fails = [k for k, v in res.items() if str(v).startswith("FAIL")]
    if fails:
        send("🔬 Самопроверка нашла проблемы: " + ", ".join(fails)
             + ". Подробности — в jarvis.log (строка САМОПРОВЕРКА).")
        journal("Самопроверка FAIL: " + ", ".join(fails))
    else:
        journal("Самопроверка пройдена (SKIP не считаются)")
    return report


def selftest_loop():
    """v3.9.0: раз в сутки в 12:00 местного — _run_selftest()."""
    log("selftest запущен (ежедневно в 12:00)")
    ran_day = None
    while True:
        try:
            now = time.localtime()
            today = time.strftime("%Y-%m-%d", now)
            if now.tm_hour == 12 and ran_day != today:
                ran_day = today
                _run_selftest()
        except Exception:
            log("selftest ERR:\n" + traceback.format_exc())
        time.sleep(600)


# ---------------------------------------------------------------- main

def main():
    log("TG-канал: %s" % ("через прокси MSK + автофолбэк на прямое"
                            if TG_OPENER else "напрямую (плавающая сеть)"))
    hello = "--hello" in sys.argv
    log("=== ДЖАРВИС старт (v3.17.0 SILERO (Task 138, 10.11, приказ Шефа "
        "«Ставь silero последней версии, нужно максимально реалистичный "
        "голос»): движок речи silero v5_6_ru — последняя модель 5-й "
        "линейки (автоударения, омографы, интонация вопросов; 48 кГц; "
        "синтез быстрее realtime) — 5 голосов одной моделью 141 МБ: "
        "ксения (основной)/ксеня/байя/евгений/айдар («ответь голосом "
        "ксении», «голос евгений»); «поставь silero» — сам ставит "
        "torch+модель, докладывает голосом; длинные тексты — чанки со "
        "склейкой аудио; piper — резерв (цепочка silero -> piper -> "
        "текст); /api/tts веб-чата на общем jarvis.tts_wav; ленивая "
        "загрузка + замок на inference; проверено в песочнице 10.11: 5 "
        "голосов, ssml, 1327 симв -> 88 с аудио за 2,9 с); "
        "+ v3.16.0 ГОЛОС ДЖАРВИСА (Task 137, 10.11, доклад "
        "Шефа «Джарвис отвечает что не умеет голосом и надо скачать ещё "
        "другие голоса, более натуральные и современные»): функция «Ответь "
        "голосом» (приказ 09.11) портирована на базу v3.15.0 — фраза в любом "
        "месте запроса, финальный ответ голосовым сообщением Telegram "
        "(piper → wav → ffmpeg opus 48k → sendVoice), сбой любого звена = "
        "откат на текст, ответы длиннее 1000 символов = начало голосом + "
        "хвост текстом; МОЗГ ЗНАЕТ о голосе (секция ГОЛОС в промпте + "
        "инструмент «голос»: список/переключить/скачать) — «не умею "
        "голосом, скачай голоса» больше не отвечает; 4 голоса piper "
        "medium: ирина/денис/дмитрий/руслан («ответь голосом дениса» — "
        "разово, «голос денис» — сменить основной живой правкой "
        "config.json с mtime-подхватом вторым процессом, «голоса» — "
        "список, «скачай голос …» — сам тянет с HuggingFace; "
        "совместимость новых голосов с движком piper 1.2.0 проверена в "
        "песочнице 10.11); веб-чат: фраза режется и сервером, ответ "
        "озвучивается даже при выключенной 🔊, лимит /api/tts 600 → 1000, "
        "выбор голоса параметром; + v3.15.0 САМОУЧКА (Task 136, 08.11, доклад Шефа "
        "«Он что не умеет делать запросы по API, научи его или пусть сам "
        "научится вообще надо сделать ему самообучение, возможно при поиске "
        "в интернете или при удачном опыте»): (1) НОВЫЙ ИНСТРУМЕНТ «запрос» — "
        "прямой HTTP к любому API из самого Python (GET/POST/PUT/DELETE, "
        "заголовки с Bearer-ключами, тело, таймаут) — Netdata/роутер/сервисы "
        "опрашиваются БЕЗ PowerShell; (2) run_ps ЧЕСТНЫЙ: ps_run_diag — мозг "
        "видит exit-код, stderr (CLIXML-шум вычищен) и причину таймаута, "
        "а не «(пусто)» (живой сбой 08.11: Джарвис не смог опросить Netdata "
        "и жаловался «PowerShell возвращает пустой ответ на все запросы» — "
        "а PowerShell был жив, ошибки просто уходили в stderr); (3) "
        "САМООБУЧЕНИЕ «УРОКИ»: memory/lessons.json — после каждого хода с 2+ "
        "инструментами или со сбоями автоматически пишется урок-опыт (задача "
        "→ какие инструменты сработали/упали → итог), в промпт инъектируются "
        "до 4 самых релевантных уроков (совпадение слов + новизна) — мозг "
        "учится на своём опыте и не повторяет грабли; поиск в интернете тоже "
        "попадает в уроки (запросы и URL видны в шагах); потокобезопасно "
        "(threading.local: TG и веб-чат не путаются); + v3.14.5 ДУМАЕТ ВСЕГДА "
        "(Task 135, 08.11, приказ "
        "Шефа «Сделай чтобы Джарвис думал всегда! Не надо быстрых ответов, "
        "он тупит сильно, пусть думает нормально всегда!!!»): режимы «fast» "
        "и авто-«big» УДАЛЕНЫ из smart_mode — ЛЮБОЙ вопрос теперь идёт в "
        "«think» (размышления 10-30 с перед ответом; раньше «простые» "
        "вопросы — привет/спасибо/короткие — отвечались бездумно за 3-8 с, "
        "что Шефу и надоело); исключение — явное «спроси у старших» = "
        "облако, провал облака = своё глубокое думание; думание теперь и НА "
        "ПАССАХ-ОТВЕТАХ после инструментов («результат инструмента», все "
        "скрин-пассы, short/lang-повторы) — раньше думал только первый "
        "заход, а финальный ответ после данных рождался бездумным; быстрыми "
        "остались только внутренние стражи-коррекции (фантом/руки/план/"
        "приказ/файл/мышь/цикл); веб-чат 8123 — та же правка: думает на "
        "КАЖДОМ шаге; + v3.14.4 РУКИ ОБУЧЕНЫ (Task 134, 08.11: печать "
        "без каретки для WinUI — аргумент обойти_каретку=да в «печатать»; "
        "скилл мышь_и_окна переписан по живым тестам: движение 12/12 0px, "
        "Калькулятор 7×8=56 кликами, Блокнот 122 символа 1:1, Telegram: "
        "«Привет» доставлен в Избранное; + v3.14.3 МЫШЬ-СТРАЖ (Task 133, "
        "хотфикс: e2e «где сейчас мышь?» поймал выдуманные координаты "
        "3839,0 без единого инструмента — теперь такой ответ переспрашивается "
        "с рецептом «мышь-позиция/скрин»; + v3.14.2 (Task 133, 08.11, доклад "
        "Шефа «сделай чтобы на скрине было видно мышь — ИИ не понимает, "
        "где мышь сейчас»): Windows НИКОГДА не включает курсор в скрины — "
        "теперь на каждый скрин курсор ДОРИСОВАН (красное перекрестие + "
        "подпись «МЫШЬ x,y»), а ТОЧНЫЕ координаты мыши из ОС приходят "
        "мозгу текстом в результате «скрин»/«область» и в промпте зрения; "
        "подпись фото — с координатами мыши; + v3.14.1 ГЛАЗА И РУКИ В "
        "ЦИКЛЕ + СТРАЖ ПОВТОРОВ "
        "И «ОБЛАСТЬ» (Task 132, живой e2e 08.11: 9 одинаковых кликов по "
        "координатам за экраном — теперь 3 повтора = коррекция, 6 = честный "
        "останов; новый инструмент «область» — кроп экрана 1:1 для точного "
        "прицела; проверка после каждого клика; + v3.14.0 (Task 132, "
        "08.11, доклад Шефа «почему не изменяет настройки программ? "
        "почему останавливается на этапе скрин и что на нём?»): «скрин» "
        "теперь ПРОМЕЖУТОЧНЫЙ шаг — фото уходит Шефу, UI-описание "
        "(кнопки/галочки/координаты) возвращается мозгу, ход "
        "ПРОДОЛЖАЕТСЯ (раньше скрин обрывал задачу всегда; бюджет "
        "шагов 12); НОВОЕ: элементы_окна/клик_элемент — UI Automation "
        "читает интерфейс программы КАК ТЕКСТ и жмёт ПО ИМЕНИ; "
        "настройки программ меняю сам, «сделай сам» Шефу запрещено; "
        "+ история: v3.13.0 ТОЛЬКО ТЕКСТ — ГЕНЕРАЦИЯ ВЫРЕЗАНА "
        "(Task 131, 07.11, приказ Шефа «хватит экспериментов — оставляй "
        "только текстовую модель как изначально задумывалось, всё "
        "остальное — картинки, видео, кузнецов — удаляй»): генерация "
        "фото ComfyUI/FLUX/RealVisXL вырезана полностью (папка "
        "comfyui_rocm ~28,5 ГБ удалена с диска), промпт-кузнец "
        "Qwen2.5-3B на CPU удалён (модель стёрта; в ночь 07.11 он "
        "съел RAM — мозг не смог подняться после генерации), ген-"
        "команды честно отвечают «удалено»; сохранено всё текстовое: "
        "умный режим, старшие братья, найти_на_странице, инструменты, "
        "зрение, голос, файлы; + история: v3.12.2 ПОИСК НА СТРАНИЦЕ "
        "(Task 130, 07.11, доклад Шефа «научи искать в браузере на "
        "странице нужную информацию, он просто говорит что видит на "
        "картинке»): новый инструмент «найти_на_странице» — читаю ТЕКСТ "
        "страницы (по ссылке или прямо из открытого браузера) и выписываю "
        "ТОЧНЫЕ строки по запросу; промпт-кузнец теперь переносит ВСЕ "
        "детали заказа (живой сбой: «лошадь чёрную, с крыльями в море» "
        "-> просто «A horse» — фикс «не те картинки»); 3-й переводчик "
        "заказа — старший брат в облаке; веб-чат честно отказывает на "
        "видео; + v3.12.1 ТОЛЬКО ФОТО — ВИДЕО УДАЛЕНО (Task 129.5, 07.11, приказ Шефа «удаляй ии для генерации видео, оставляй только картинки»): видео-генератор Wan 2.2 вырезан полностью — модели удалены с диска (−12.3 ГБ), команды про видео честно отвечают «удалено по приказу», фото-конвейер прежний: FLUX (флагман) + RealVisXL («быстро») + промпт-кузнец-переводчик с контекстом; + v3.12.0 СВЯЗАННЫЕ МОЗГИ — ГЕНЕРАТОР ПОНИМАЕТ ЗАКАЗЫ (Task 129.4, 07.11, доклад Шефа «генерируют не те картинки, не то видео; можно ли связать все мозги с общим контекстом»): корень — генераторы (FLUX/RealVisXL/Wan) обучены на АНГЛИЙСКИХ описаниях, а им отдавали сырой русский текст («закат картинку» -> случайное видео), внутренние записки («Шеф прислал фото… посмотри зрением») уходили прямо в промпт, а вопросы Шефа («ты кто ты вообще?») превращались в картинки; теперь между Шефом и генератором всегда стоит связной: 1) ПРОМПТ-КУЗНЕЦ Qwen2.5-3B на CPU (порт 1235, ~2 ГБ RAM, VRAM не трогает, живёт всегда) — заказ -> точный английский промпт с сохранением задумки; 2) КОНТЕКСТ: кузнец видит последние сообщения диалога + последнюю генерацию («ещё раз, но ночью» работает, seed сохраняется) + профиль Шефа; 3) если большой мозг ещё жив (обычный режим) — промпт формулирует ОН, целиком зная диалог; 4) вопросы/болтовня отсеиваются (NOT_A_REQUEST) — честный ответ «мозг спит», а не случайная картинка; 5) фото в режиме ВИДЕО = стартовый кадр ролика (Wan I2V), подпись = что делать в кадре; фото в режиме ФОТО с подписью = заказ; 6) голос в режиме генерации = заказ; 7) «запомни как я выгляжу: …» — профиль для «нарисуй меня»; 8) к подписи генерации добавляю английский промпт — видно, что понял; 9) кузнеца не трогают выгрузки мозга/генератора (CPU + фильтр --port 1234 у убийц llama-server, включая vram_ctl); + v3.11.3 ГЕНЕРАЦИЯ — САМОВОССТАНОВЛЕНИЕ ГЕНЕРАТОРА + ЧИСТЫЙ ХОЛОДНЫЙ СТАРТ (Task 129.3, 07.11, доклад Шефа «⚠️ Не получилось: генератор не поднят», серия 16:15-16:23): живой сбой — ComfyUI упал нативно (access violation в GGUF-unpatch при выгрузке модели прошлого семейства: после видео Wan фото FLUX просило место под VAE), после чего задача 8 минут ждала труп и генератор никто не поднимал; теперь: 1) генератор умер СЕРЕДИНА задачи — сам перезапускаю и повторяю задачу, Шеф всё равно получает результат (+~минута); 2) смена модели (видео↔фото↔быстро) = перезапуск генератора начисто — грабли выгрузки чужой GGUF больше не встречаются; 3) общий файловый замок генерации у Telegram и веб-чата — «⏳ уже делаю» честно в обоих каналах, веб тоже поднимает генератор; 4) полумёртвые процессы ComfyUI добиваются перед стартом; 5) ХОЛОДНЫЙ СТАРТ починен: cmd больше не наследует хэндл comfyui.log — раньше «echo >> лог» в bat получало «файл занят» и генератор умирал с code=1 (16:42-17:11: Шеф просил фото/видео трижды — «генератор не поднялся»); + v3.11.1 ГЕНЕРАЦИЯ — ПОНЯТНЫЕ ОШИБКИ + КОНТРОЛЬ ДОКАЧКИ (Task 129.2, 07.11, доклад Шефа «не получается сгенерировать фото»): сбой 15:15 был из-за молча повреждённого файла t5xxl (два параллельных curl писали в один файл, размер совпал, содержимое — нет); теперь: 1) при ошибке генерации Шеф видит конкретную причину (узел + суть из ComfyUI, а не «смотри логи»); 2) перед генерацией проверяю файлы моделей — «ещё докачивается, N%» вместо загадочного сбоя; 3) «статус» показывает прогресс докачки; сам t5xxl перезакачан и проверен генерацией; вдогонку живыми тестами пойманы и поправлены имена входов нод новой сборки ComfyUI (ckpt_name у RealVisXL, video у SaveVideo) — «быстро:» и видео тоже проверены; + v3.11.0 ГЕНЕРАЦИЯ ФОТО/ВИДЕО БЕЗ ЦЕНЗУРЫ (Task 129, 07.11, приказ Шефа «мне нужна модель ии которая генерирует фото и видео и без цензуры»): рядом с мозгом Qwen на той же видеокарте работает генератор ComfyUI (ROCm/RDNA4): «переключись на фото»/«переключись на видео» — выгружаю мозг, поднимаю генератор (FLUX.1-dev Q4_K_S — фото-флагман; RealVisXL V5 — по слову «быстро»; Wan 2.2 TI2V-5B — видео); «верни основную» — мозг назад; в режиме генерации любое сообщение = описание; «нарисуй …»/«сделай видео …» — авто-переключение из обычного режима; фото приходит в Telegram, файл — в веб-чат; всё локально и приватно, без внешних цензоров; + v3.10.1 СТАРШИЙ БРАТ-ПОМОЩНИК (Task 128, 07.11): авто-сложные вопросы (эвристика, без слова «подумай») при наличии cloud_api_key уходят МОЩНОМУ облачному брату (GLM-5.3 на z.ai / Mistral Large 123B — в разы умнее локальных 27B), провал или нет ключа = локальное думание как раньше; слово «подумай» — локальные размышления, как приказано в Варианте А; бесплатный брат Pollinations gpt-oss-20b (без ключа) остаётся на «спроси у старших», его интервал ~30 с и обработка 402 больше НЕ тормозят платных братьев; разведка Task 128: Groq/OpenRouter/Gemini/Cerebras из РФ закрыты 403 (даже через наш WARP — его выход тоже Москва), DDG duckchat закрыл безликий доступ JS-челленджем; из РФ доступны GLM/Mistral/DeepSeek/Qwen — ждут только ключ в config.json; v3.10.0 УМНЫЙ РЕЖИМ + СТАРШИЕ БРАТЬЯ (Task 127, 07.11, приказ Шефа «Вариант А + API + старшие братья»): авто-маршрут fast/think/cloud — сложные вопросы (почему/сравни/объясни/придумай, длинные >250 знаков) и слово «подумай» = размышления Qwen (заметно умнее, 10-30 с), простые — мгновенно как раньше; «спроси у старших» = бесплатный облачный мозг (Pollinations, без ключа, интервал ~30 с между запросами), работает даже когда локальный спит из-за игры; провал старших = авто-фолбэк на глубокое локальное думание; v3.9.2 АНТИ-ЗАТУХАНИЕ (Task 125, 06.11, живой сбой 13:23: «Шеф, я вижу WizTree» -> «Шеф, я» -> «Ше…», генерация 6 токенов и EOS): обрывки ответов больше НЕ пишутся в history (модель копировала собственные обрывки — ответы самозатухали), короткий обрывок = один перезапрос «ответь полно» (short-guard); v3.9.1 ГОРЯЧИЙ ФИКС-500 (Task 125, 06.11, скрин Шефа «ответы обрываются + HTTP 500»): llm_chat при повторе обрыва размышлений больше НЕ дописывает system-сообщение в конец массива — шаблон Qwen требует system только первым, llama-server поднимал 500 «System message must be at the beginning»; запрет думания теперь дописывается в первое system, max_tokens повтора 1200; v3.9.0 НАДЁЖНОСТЬ (Task 124, приказ Шефа 06.11 «делай все пункты кроме 7»): ротация логов jarvis.log/llama.log ~3 МБ с сохранением хвоста — логи больше не растут вечно; ФОЛБЭК СВЯЗИ: прокси Telegram молчит 3 раза подряд — автоуход на прямое соединение, прямое плавает 6 раз — возврат на прокси; ПАМЯТЬ ГЛУБЖЕ: окно истории 16 -> 32 сообщения + жёсткий бюджет 28К символов (контекст 12288 защищён) + дневник diary.jsonl для вытесненных обменов (инструмент «дневник»); САМОПРОВЕРКА ежедневно в 12:00: стражи честности/мозг/зрение/поиск/файлы/связь — FAIL приходит Шефу в Telegram; v3.8.6 ФАНТОМ-РЕЗУЛЬТАТ: описание результата/проверки инструмента («инструмент вернул „НЕ подтвердилось“», «клик в (X,Y) не закрыл диалог», «курсор реально в (X,Y)») при НУЛЕ вызовов в ходе = выдумка — живой тест 02.11 19:47 поймал два таких ответа за 3-4 с; v3.8.5 ЧЕСТНЫЕ РУКИ-ТРОС: «передвинул/кликнул/напечатал/закрыл» без вызова инструмента рук = перезапрос — живой тест 02.11 поймал фантомное «курсор в (2500,1200), проверено» за 3 с без единого вызова, теперь это ловится уровнем кода; v3.8.4 АВТОФОКУС ПЕЧАТИ: без каретки печатать сам кликает в центр окна и повторяет проверку — у мозга стало на 2 шага меньше, цепочка не рвётся; v3.8.3 БЕЗ РАЦИИ: push-to-talk (ptt.py) удалён по приказу Шефа — Шеф не играет, пока мозг на видеокарте; голос — кнопка 🎤 в веб-чате; v3.8.1 СВЯЗЬ: Telegram через прокси MSK — прямые соединения с ПК2 плавали; v3.8.0 ТОРРЕНТЫ: uTorrent под управлением — список/удаление с верификацией, данные только по путям из базы; v3.7.0 ЧЕСТНЫЕ РУКИ: мышь/окна с самопроверкой — "
        "«проверено» или честное «НЕ получилось»; законы З5 язык + З6 "
        "честность, языковой страж; координатный контракт — только "
        "физические пиксели скриншота; v3.6.0 РОУТЕР; v3.5.0 ЗРЕНИЕ+ДАТЧИКИ; "
        "события v3.4.0; v3.3.0 (рация — удалена в v3.8.3); v3.2.1 СВЕРКА; v3.2.0 ГЛАЗА И ГОЛОС; "
        "v3.1.0 ФАЙЛЫ; законы v3.0.1; ученик v3.0; v2.3.0 МАКС) ===")
    journal("Джарвис v3.17.0 SILERO (Task 138, 10.11, приказ Шефа «Ставь "
            "silero последней версии, нужно максимально реалистичный "
            "голос»): движок silero v5_6_ru — 5 голосов (ксения основной/"
            "ксеня/байя/евгений/айдар), установка «поставь silero» "
            "(torch+модель+конфиг, доклад голосом), длинные ответы "
            "чанками, piper — резерв, /api/tts на общем движке")
    journal("Джарвис v3.16.0 ГОЛОС ДЖАРВИСА (Task 137, 10.11, доклад Шефа "
            "«Джарвис отвечает что не умеет голосом и надо скачать ещё "
            "другие голоса, более натуральные и современные»): «ответь "
            "голосом [имя]» озвучивает финальный ответ (Telegram — "
            "sendVoice piper+opus; веб-чат — /api/tts даже при выключенной "
            "🔊); мозг теперь ЗНАЕТ о голосе (промпт + инструмент «голос»: "
            "список/переключить/скачать); голоса: ирина (основной) + "
            "денис/дмитрий/руслан; смена основного — живая правка "
            "config.json, оба процесса подхватывают по mtime")
    journal("Джарвис v3.14.4 РУКИ ОБУЧЕНЫ (Task 134, 08.11, приказ Шефа "
            "«научи его движению мыши, нажатию кнопок и вводу текста»): "
            "«печатать» умеет обходить кареточный шлюз для WinUI-приложений "
            "(Unigram — аргумент обойти_каретку=да, поле подтверждается "
            "кликом по UIA-точке или кропом); скилл мышь_и_окна переписан "
            "по живым тестам 3 программ (Калькулятор 7×8=56 кликами, "
            "Блокнот 122 символа 1:1, Telegram: «Привет» доставлен в "
            "Избранное); движение мыши 12/12 целей с отклонением 0px")
    journal("Джарвис v3.14.3 МЫШЬ-СТРАЖ (Task 133, хотфикс после e2e: "
            "на «где сейчас мышь?» мозг выдумал «3839, 0» без единого "
            "инструмента — теперь ответ без скрина/мыши переспрашивается, "
            "координаты только по факту из ОС)")
    journal("Джарвис v3.14.2 КУРСОР ВИДЕН (Task 133, 08.11, доклад Шефа "
            "«сделай чтобы на скрине было видно мышь — ИИ не понимает, "
            "где мышь сейчас»): Windows не включает курсор в скриншоты "
            "никогда — теперь курсор дорисован на каждом скрине красным "
            "перекрестием с подписью координат, а точная позиция мыши из "
            "ОС приходит текстом в «скрин»/«область» и в промпт зрения")
    journal("Джарвис v3.14.1 СТРАЖ ПОВТОРОВ + ОБЛАСТЬ (Task 132, 08.11, "
            "живой e2e: модель кликала 9 раз одни координаты за экраном): "
            "3 одинаковых вызова подряд = коррекция, 6 = честный останов; "
            "инструмент «область» — кроп экрана без сжатия, точный прицел; "
            "после каждого клика — обязательная проверка скрин/область")
    journal("Джарвис v3.14.0 ГЛАЗА И РУКИ В ЦИКЛЕ (Task 132, 08.11, "
            "доклад Шефа «почему не изменяет настройки программ, почему "
            "останавливается на этапе скрин и что на нём»): скрин больше "
            "НЕ обрывает ход — описание возвращается мозгу и цикл "
            "продолжается; новые инструменты элементы_окна/клик_элемент "
            "читают интерфейс программ текстом и жмут по имени; настройки "
            "программ теперь меняю сам, без «сделай сам»")
    journal("Джарвис v3.13.0 ТОЛЬКО ТЕКСТ (Task 131, 07.11, приказ "
            "Шефа «хватит экспериментов — оставляй только текстовую "
            "модель как изначально задумывалось, всё остальное — "
            "картинки, видео, кузнецов — удаляй»): генерация фото и "
            "видео вырезана полностью — код ComfyUI/FLUX/RealVisXL "
            "удалён, папка comfyui_rocm (~28,5 ГБ) стёрта с диска; "
            "промпт-кузнец Qwen2.5-3B на CPU удалён (лишняя нагрузка; "
            "в ночь 07.11 он съел RAM — мозг не поднялся после "
            "генерации); я снова чистый текстовый мозг: умный режим, "
            "старшие братья, поиск по страницам, зрение, голос, файлы")
    journal("Джарвис v3.8.3 БЕЗ РАЦИИ (Task 103, 02.11): приказ Шефа — "
            "рация (push-to-talk, ptt.py) не нужна: Шеф не играет при мозге "
            "на видеокарте. Задача JarvisPTT, ptt.py и инструмент "
            "«рация_клавиша» удалены; голос остался — кнопка 🎤 в веб-чате "
            "и озвучка ответов 🔊 (piper)")
    journal("Джарвис v3.8.6 ФАНТОМ-РЕЗУЛЬТАТ (Task 107, 02.11 вечер): живой "
            "E2E тестов Рук поймал новую дыру честности — мозг отвечал за "
            "3-4 секунды без единого вызова инструментов, но со ссылкой на "
            "результат: «инструмент вернул „НЕ подтвердилось“», «клик в "
            "(1780,1210) не закрыл диалог», «курсор реально в (1920,1000)». "
            "Отрицательные формы и заявления о состоянии прошлые стражи "
            "пропускали. Теперь: описание результата/проверки инструмента "
            "при нуле вызовов в ходе = перезапрос; мозгу идёт конкретное "
            "сообщение стража (руки/фантом), а не общее")
    journal("Джарвис v3.8.5 ЧЕСТНЫЕ РУКИ-ТРОС (Task 68, 02.11 вечер): живой "
            "тест мыши поймал фантом — мозг доложил «передвинул курсор в "
            "(2500,1200), инструмент подтвердил» за 3 секунды БЕЗ единого "
            "вызова инструмента; курсор не двигался. Трос честности "
            "расширен на руки: прошедшее время руки-глагола (передвинул/"
            "кликнул/напечатал/закрыл...) + руки-контекст без вызова "
            "соответствующего инструмента = перезапрос; «скрин»/«окна» "
            "оправдывают только глаголы проверки")
    journal("Джарвис v3.8.1 СВЯЗЬ (Task 105, ночь 02.11): Telegram ходит "
            "через прокси на MSK (config.json tg_proxy) — прямые соединения "
            "с ПК2 всю ночь рвались (poll ERR, send ERR в jarvis.log); "
            "мозг и локальный чат по-прежнему напрямую (127.0.0.1)")
    journal("Джарвис v3.8.2 ПРОВЕРКА РУК (Task 68, 02.11): живой аудит "
            "клавиатуры/мыши нашёл краш key_combo на буквах (VkKeyW не "
            "существует — заменил на VkKeyScanW) и «планы вместо действий» "
            "(мозг отвечал «сейчас сделаю» без инструмента). Добавлен "
            "план-гард, правило «действие = сразу JSON», печать докладывает "
            "целевое окно")
    journal("Джарвис v3.8.0 ТОРРЕНТЫ (Task 105, ночь 02.11): приказ Шефа — "
            "пустой uTorrent и игру (RDR2, 101 ГБ) удаляет Джарвис. "
            "Инструмент «торренты»: список/удаление, полная очистка через "
            "сброс базы при остановленном клиенте, данные — только по путям "
            "из resume.dat и только при явном «файлы=да»")
    journal("Джарвис v3.7.0 ЧЕСТНЫЕ РУКИ (Task 104, 02.11): ночь вскрыла "
            "промахи мыши (мозг путал логические/физические пиксели 4K@250%) "
            "и доклады «нажал» без проверки. Теперь win_ctl проверяет каждое "
            "действие чтением факта; законы З5 (язык) и З6 (честность); "
            "языковой страж — ответ не по-русски переспрашивается")
    journal("Джарвис v3.11.3 САМОВОССТАНОВЛЕНИЕ ГЕНЕРАТОРА (Task 129.3, "
            "07.11, доклад Шефа «⚠️ Не получилось: генератор не поднят»): "
            "живая серия 16:15-16:23 — ComfyUI упал нативно (access "
            "violation в GGUF-unpatch при выгрузке модели прошлого "
            "семейства: после видео Wan фото FLUX просило место под VAE), "
            "задача 8 минут ждала труп, генератор никто не поднимал, а "
            "холодный старт вдобавок умирал code=1 (cmd наследовал хэндл "
            "лога — «файл занят»); теперь: генератор умер СЕРЕДИНА задачи "
            "— сам перезапускаю и повторяю задачу; смена модели "
            "(видео↔фото↔быстро) = перезапуск начисто; общий файловый "
            "замок TG+веб; старт без наследования лога. Проверено живыми "
            "тестами: фото с нуля, видео, фото-после-видео (прежний "
            "крэш-сценарий), убийство генератора посреди задачи")
    journal("Джарвис v3.11.1 ФИКС ГЕНЕРАЦИИ (Task 129.2, 07.11): "
            "первая попытка Шефа упала на побитом докачкой файле t5xxl — "
            "перезакачан заново, генерация проверена вживую; ошибки "
            "теперь приходят с конкретной причиной, а недокачанные "
            "модели честно сообщают процент готовности")
    journal("Джарвис v3.12.2 ПОИСК НА СТРАНИЦЕ + КУЗНЕЦ-ДЕТАЛИ (Task "
            "130, 07.11, доклад Шефа «научи искать в браузере на странице "
            "нужную информацию, он просто говорит что видит на картинке»): "
            "новый инструмент «найти_на_странице» — читаю ТЕКСТ страницы "
            "(по ссылке или из открытого браузера Ctrl+A/C) и выписываю "
            "точные строки по запросу; промпт-кузнец теперь переносит ВСЕ "
            "детали заказа (жалоба «не те картинки»: «лошадь чёрную с "
            "крыльями в море» превращалась в просто «A horse») + правило "
            "деталей и примеры; 3-й переводчик заказа — старший брат в "
            "облаке; веб-чат честно отказывает на видео")
    journal("Джарвис v3.12.1 ТОЛЬКО ФОТО (Task 129.5, 07.11, приказ Шефа "
            "«удаляй ии для генерации видео, оставляй только картинки»): "
            "видео-генератор Wan 2.2 вырезан полностью — модели удалены "
            "с диска (−12.3 ГБ), команды видео честно отвечают "
            "«удалено», фото-конвейер сохранён целиком (FLUX + RealVisXL "
            "«быстро» + промпт-кузнец с контекстом)")
    journal("Джарвис v3.12.0 СВЯЗАННЫЕ МОЗГИ (Task 129.4, 07.11, доклад "
            "Шефа «генерирует не те картинки/не то видео; свяжи все мозги "
            "с контекстом»): у генератора появился связной — промпт-"
            "кузнец Qwen2.5-3B на CPU (живёт всегда, VRAM не трогает): "
            "заказ по-русски -> точный английский промпт (FLUX/Wan "
            "русского не знали — отсюда «не то»), ссылки «меня/ещё раз» "
            "раскрываются из диалога и профиля, вопросы больше не "
            "превращаются в картинки, фото в режиме видео = стартовый "
            "кадр (I2V), голос в режиме генерации = заказ, «запомни как "
            "я выгляжу» — профиль для «нарисуй меня»")
    journal("Джарвис v3.11.0 ГЕНЕРАЦИЯ ФОТО/ВИДЕО (Task 129, 07.11): "
            "появилась вторая личность — генератор фото и видео без "
            "цензуры (ComfyUI + FLUX.1-dev + RealVisXL + Wan 2.2, всё "
            "локально на видеокарте). «переключись на фото» / "
            "«переключись на видео» — переключаюсь, «верни основную» — "
            "возвращаю мозг, «нарисуй …» — рисую сразу")
    journal("Джарвис v3.10.1 СТАРШИЙ БРАТ-ПОМОЩНИК (Task 128, 07.11): "
            "приказ Шефа — облачный брат нужен именно МОЩНЫЙ, а не "
            "ровесник. Разведка: Groq/OpenRouter/Gemini из РФ закрыты, "
            "бесплатный Pollinations даёт только gpt-oss-20b. Из РФ без "
            "VPN доступны GLM (z.ai — уже аккаунт Шефа), Mistral Large "
            "123B (бесплатно, без карты), DeepSeek, Qwen — нужен только "
            "API-ключ в config.json. Теперь сложные вопросы я сам несу "
            "старшему брату (как только ключ появится), провал = думаю "
            "сам; «подумай» — по-прежнему локально, глубоко")
    journal("Джарвис v3.10.0 УМНЫЙ РЕЖИМ + СТАРШИЕ БРАТЬЯ (Task 127, "
            "07.11, приказ Шефа): теперь я сам решаю — простой вопрос "
            "отвечаю мгновенно, а сложный (почему/сравни/объясни/придумай "
            "или слово «подумай») — обдумываю глубоко, 10-30 с, зато "
            "заметно умнее. «Спроси у старших» — бесплатный облачный "
            "мозг-советчик, работает даже когда я сплю из-за игры")
    journal("Джарвис v3.9.2 АНТИ-ЗАТУХАНИЕ (Task 125, 06.11): обрывки "
            "ответов не пишутся в history и перезапрашиваются — модель "
            "копировала собственные обрывки из истории, ответы "
            "самозатухали до «Ше…»)")
    journal("Джарвис v3.9.1 ГОРЯЧИЙ ФИКС-500 (Task 125, 06.11): повтор "
            "обрыва размышлений не дописывает system в конец массива "
            "(шаблон Qwen: system только первым — иначе llama-server "
            "HTTP 500; живой сбой: ответы обрывались до «Ше…»), запрет "
            "думания — в первое system, max_tokens повтора 1200")
    journal("Джарвис v3.9.0 НАДЁЖНОСТЬ (Task 124, 06.11, приказ Шефа "
            "«делай все пункты кроме 7»): ротация логов jarvis.log и "
            "llama.log (~3 МБ, хвост сохраняется); фолбэк связи — прокси "
            "Telegram молчит 3 раза -> прямое соединение, прямое плавает "
            "6 раз -> возврат на прокси; окно истории 16 -> 32 сообщения + "
            "бюджет 28К символов + дневник diary.jsonl (инструмент "
            "«дневник»); ежедневная самопроверка в 12:00 (стражи/мозг/"
            "зрение/поиск/файлы/связь — FAIL приходит Шефу)")
    if hello:
        send("🤖 *ДЖАРВИС v3.13 на связи!*\n\n"
             "Теперь я ещё и учусь: веду память и пишу себе скиллы — "
             "новые умения остаются со мной навсегда.\n"
             "Теперь я не только отвечаю — я ДЕЙСТВУЮ: чищу диск от мусора, "
             "подсказываю что перенести, запускаю и закрываю программы, а когда "
             "ты запускаешь игру — сам освобождаю видеокарту и возвращаюсь после.\n\n"
             "Пиши обычным языком: «освободи диск C», «что можно перенести», "
             "«запусти стим». «помощь» — список команд.")
    threading.Thread(target=llm_start, daemon=True).start()
    for fn in (polling_loop, watchdog_loop, events_loop, briefing_loop,
               llm_watchdog, game_watch_loop, flags_loop, chat_watchdog,
               selftest_loop):
        threading.Thread(target=fn, daemon=True).start()
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
