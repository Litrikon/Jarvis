# Скилл: Чистка диска
Описание: освободить место — мусор, кэши браузеров/системы, корзина, обновления

## Когда
«освободи диск», «почисти C», «места нет», watchdog ругнулся на мало места.

## Как
1. «место» {} — зафиксируй свободное место ДО.
2. «очистить_мусор» {"диск":"C"} — базовая безопасная чистка (temp, кэши, корзина) — стартуй с неё, она много умеет.
3. Нужно ещё? run_ps ПО ОДНОМУ пункту, после каждого — «место»:
   - Кэш шейдеров (пересоздадутся сами):
     Remove-Item "$env:LOCALAPPDATA\D3DSCache\*" -Recurse -Force -EA SilentlyContinue
   - Компоненты старых обновлений (долго, 5-20 мин — предупреди Шефа):
     Dism.exe /Online /Cleanup-Image /StartComponentCleanup
   - Кэш доставки обновлений:
     Delete-DeliveryOptimizationCache -Force -EA SilentlyContinue
   - Дампы: Remove-Item "C:\Windows\Minidump\*","C:\Windows\MEMORY.DMP" -Force -EA SilentlyContinue
   - Кэш браузеров (только закрытых!): "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache\*", аналогично Edge/Yandex.
4. Итог Шефу: «было X ГБ → стало Y ГБ, освободил Z».

## Грабли
- НЕ трогай: D:\Jarvis и кэш моделей (мой мозг), hiberfil.sys, pagefile.sys.
- Кэш браузера чисти только когда браузер закрыт (файлы заняты).
- После чистки запиши урок в память, если нашёл новый источник мусора.
