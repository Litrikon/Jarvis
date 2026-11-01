# Скилл: Железо и диагностика
Описание: температуры, SMART дисков, железо, сеть, ошибки в журнале системы

## Когда
«как железо», «температуры», «проверь диски», «что с сетью», «были ошибки».

## Как
1. «статус» {} — сводка CPU/RAM/GPU/диски/аптайм.
2. «диски» {} — SMART и температуры дисков.
3. Загрузка GPU:
   run_ps: (Get-Counter '\GPU Engine(*engtype_3D)\Utilization Percentage' -EA SilentlyContinue).CounterSamples | Measure-Object CookedValue -Sum | ForEach-Object { 'GPU 3D: {0:N0}%' -f $_.Sum }
4. Сеть:
   run_ps: Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object Name,LinkSpeed | Format-Table -AutoSize
5. Ошибки системы:
   run_ps: Get-EventLog System -Newest 20 -EntryType Error,Warning | Select-Object TimeGenerated,Source,Message | Format-List

## Грабли
- Температуры GPU AMD из PowerShell часто недоступны — НЕ выдумывай цифры; скажи честно или предложи скрин Adrenalin.
- Свежие значения узнавай только инструментами, не по памяти.
