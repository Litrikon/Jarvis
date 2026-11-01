# Скилл: Таймеры и напоминания
Описание: разовое напоминание Шефу в Telegram через N минут или в заданное время

## Когда
«напомни через 20 минут ...», «разбуди в 8», «таймер на ...».

## Как
Одноразовая задача планировщика + Telegram API (токен в D:\Jarvis\config.json):
1. Создать (имя всегда с префиксом JARVIS_):
   run_ps:
   $cfg = Get-Content 'D:\Jarvis\config.json' -Raw | ConvertFrom-Json
   $msg = [uri]::EscapeDataString('НАПОМИНАНИЕ: текст')
   $at = (Get-Date).AddMinutes(20).ToString('HH:mm')
   $act = "powershell -WindowStyle Hidden -Command `"Invoke-RestMethod 'https://api.telegram.org/bot$($cfg.token)/sendMessage?chat_id=$($cfg.chat_id)&text=$msg'`""
   schtasks /Create /TN JARVIS_timer_1 /SC ONCE /ST $at /TR $act /F
2. Проверить: run_ps: schtasks /Query /TN JARVIS_timer_1
3. Отменить: run_ps: schtasks /Delete /TN JARVIS_timer_1 /F

## Грабли
- /ST — только HH:mm (локальное время), секунды нельзя.
- Момент сегодня уже прошёл — задача не сработает: ставь на завтра (/SD дата) или используй задержку shutdown-типа /ST на будущее.
- Текст пиши простым, без кавычек и переносов — меньше проблем с экранированием.
- Повторяющиеся напоминания — это скилл schedule, не этот.
