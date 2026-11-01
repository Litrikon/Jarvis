# Скилл: Процессы и загрузка
Описание: кто ест CPU/RAM/GPU/диск, зависшие процессы, автозагрузка

## Когда
«тормозит», «висит», «кто жрёт память», «закрой ...».

## Как
1. «процессы» {} — топ по RAM/CPU.
2. Сводно по группе:
   run_ps: Get-Process chrome -EA SilentlyContinue | Measure-Object WS -Sum | ForEach-Object { '{0} шт, {1:N1} ГБ RAM' -f $_.Count,($_.Sum/1GB) }
3. Загрузка в моменте:
   run_ps: Get-CimInstance Win32_Processor | ForEach-Object { 'CPU: {0}%' -f $_.LoadPercentage }; Get-CimInstance Win32_OperatingSystem | ForEach-Object { 'RAM свободно: {0:N1} ГБ' -f ($_.FreePhysicalMemory/1MB) }
4. Завис: «закрыть» {"имя":"..."}; не помогло — run_ps: Stop-Process -Name 'имя' -Force
5. Автозагрузка:
   run_ps: Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location | Format-List

## Грабли
- НЕ убивай: python/pythonw, llama-server (это я), csrss, lsass, services, svchost, system, dwm, winlogon — синий экран.
- Много процессов chrome — норма (по процессу на вкладку).
- llama-server грузит GPU на 100%, когда я думаю — это норма.
