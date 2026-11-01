LoRA v4 — как обучить Джарвиса на стиле Шефа
=============================================
(cобрано 02.11.2026, Задача 101; датасет: build_dataset.py)

ЧТО МЫ УЧИМ
-----------
Файл стиля общения: пары «Шеф -> Джарвис» из реальных диалогов (TG +
веб-чат), финальные ответы без инструментного JSON и служебных реплик.
Цель — не новые знания, а тон, лексикон, типовые формулировки
(«дворецкий-технарь» на русском, коротко и по делу).

ШАГ 1. ДАТАСЕТ (уже сделано)
----------------------------
    D:\Jarvis\python\python.exe D:\Jarvis\tools\lora\build_dataset.py
Выход: E:\Downloads\Jarvis\lora_dataset_<дата>.jsonl
Формат — OpenAI messages (system + user + assistant): понимают
unsloth, axolotl, LLaMA-Factory. Датасет нужно пополнять:
запускай экстрактор раз в пару недель — зеркало растёт само.

ШАГ 2. ГДЕ УЧИТЬ (честно про железо)
------------------------------------
Материнская модель — Qwen3.8-27B (наш рабочий GGUF Q3_K_XL).
- 27B QLoRA (4-бит) требует ~20-24 ГБ VRAM. У нас Radeon 16 ГБ —
  НЕ ВЛЕЗАЕТ локально.
- Вариант А (рекомендую): аренда GPU на 1-2 часа (RTX 4090 24 ГБ /
  A100): runpod.io, vast.ai, lambda — ~0.4-1.5 $/час. 27B QLoRA на
  паре сотен примеров учится за один заход.
- Вариант Б: локально учить МЛАДШУЮ модель (Qwen3-4B/8B QLoRA на ROCm
  16 ГБ влезает) и держать её как «быстрый повседневный мозг», а 27B —
  для сложного. Тогда config.json: две секции, переключение голосом.
- Вариант В: подождать апгрейда видеокарты.

ШАГ 3. РЕЦЕПТ (unsloth, вариант А)
----------------------------------
    pip install unsloth
    from unsloth import FastLanguageModel
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="Qwen/Qwen3-14B" or наш базовый HF,  # см. примечание
        max_seq_length=2048, load_in_4bit=True)
    model = FastLanguageModel.get_peft_model(
        model, r=16, lora_alpha=32, lora_dropout=0.05,
        target_modules=["q_proj","k_proj","v_proj","o_proj",
                        "gate_proj","up_proj","down_proj"])
    # данные: jsonl с messages -> chat template tokenizer.apply_chat_template
    # обучение: SFTTrainer, epochs=2-3, lr=2e-4, batch=1, grad_accum=8
Примечание: GGUF Q3_K_XL — уже квантованная модель, учить надо
оригинал с HuggingFace (unsloth/Qwen3-...-Unsloth-bnb-4bit), а потом
квантировать результат заново.

ШАГ 4. СБОРКА В GGUF И ПОДКЛЮЧЕНИЕ
----------------------------------
    python llama.cpp/convert_hf_to_gguf.py ./lora-merged --outtype f16
    llama.cpp/llama-quantize model-f16.gguf model-Q4_K_M.gguf
Файл -> D:\Jarvis\models\...; в config.json поменять model_path (и
mmproj_path, если нужен тот же vision-проект), рестарт Джарвиса.
ОТКАТ: вернуть старый model_path (бэкап config не забудь).

ГРАБЛИ
------
- Не учи на инструментном JSON без нужды: если хочется сохранить
  вызовы инструментов — оставь в ассистентах и их (mixed data), но
  тогда фильтр good_assistant надо ослабить. Начинаем со стиля —
  чистые финальные ответы.
- 200-500 примеров хватает для стиля; 2000+ — для привычек. Меньше 100
  — не учи, выйдет шиза.
- Всегда merge + квантование заново; сырой LoRA-адаптер llama-server
  тоже умеет (--lora), но мердженный стабильнее.
- Датасет содержит личные диалоги — в публичный гит его НЕ класть
  (секрет-скан его и не пустит: приватные данные).
