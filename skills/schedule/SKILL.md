# Скилл: Планировщик задач
Описание: регулярные дела — ежедневно, при старте ПК, раз в неделю

## Когда
«каждый день в ... делай ...», «при включении запускай ...», «раз в неделю ...».

## Как
Свои задачи называй ТОЛЬКО с префиксом JARVIS_ (чтобы не задеть чужие):
1. Создать:
   run_ps: schtasks /Create /TN JARVIS_имя /SC DAILY /ST 08:00 /TR "powershell -WindowStyle Hidden -File D:\Jarvis\data\скрипт.ps1" /F
   /SC: DAILY, WEEKLY (с /D MON), ONCE, ONSTART, ONLOGON.
2. Свои задачи:
   run_ps: Get-ScheduledTask | Where-Object TaskName -like 'JARVIS_*' | Select-Object TaskName,State
3. Выключить/удалить: /Change /DISABLE или /Delete /F.
4. Сообщение Шефу по расписанию — комбинируй со скиллом timers (тот же sendMessage).

## Грабли
- ЧУЖИЕ задачи (Microsoft\..., без префикса JARVIS_) — НЕ трогай.
- Путь с пробелами в /TR — кавычки в кавычках: /TR "\"D:\путь с пробелом\x.exe\" арг".
- Сложное действие: сначала создай .ps1 в D:\Jarvis\data\, потом задачу на него.
