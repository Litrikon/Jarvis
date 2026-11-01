# Скилл: настройки_скриншота

Описание: сверка настроек со скриншота (гайд, другой ПК, «сделай как тут») с реальными настройками ПК2 — таблица различий + предложение исправить; и обратный режим — проверка после изменения.

Когда:
- Шеф прислал скриншот настроек (Windows, драйвер AMD, игра, программа) и просит «сравни / сделай так же / что отличается / проверь настройки».
- Шеф просил изменить настройку — проверить результат скриншотом и сверкой.

Как (строго по шагам, ничего не выдумывай):
1. ВЫПИШИ со скриншота. посмотреть_файл с «вопрос»: «Выпиши ВСЕ настройки, видные на скриншоте, строго списком ПАРАМЕТР = ЗНАЧЕНИЕ (переключатели: Вкл/Выкл). Не добавляй того, чего не видно.» Зрение могло ошибиться в мелких значениях — помечай неуверенное «(?)».
2. ОПРЕДЕЛИ домен настроек и прочитай РЕАЛЬНЫЕ значения run_ps (рецепты ниже). Не знаешь рецепта — читай реестр/командой сам, это разрешено. Никогда не сравнивай «по памяти».
3. СВЕРКА: короткая таблица «параметр — на скриншоте — сейчас — вывод (ок/ОТЛИЧАЕТСЯ/не знаю)». Не вишь параметр в системе — честно «не нашёл, скажу как проверить руками».
4. ИТОГ Шефу: сколько совпало, ГЛАВНЫЕ различия, и вопрос: «применить отличия?» Изменения настроек — только после явного «да» (закон З3: смена настроек системы/драйвера = необратимое действие). После применения — ПРОВЕРКА: повторно прочитай значение и (для настроек с окнами) скрин + посмотреть_файл с «вопрос»: «Какое значение у <параметр>?»
5. ПАМЯТЬ: запомни_факт — какие настройки Шеф держит и что менял.

РЕЦЕПТЫ ЧТЕНИЯ (PowerShell, читать = безопасно, confirm не нужен):
- Питание/производительность:
  powercfg /getactivescheme
  powercfg /q SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX   (макс. состояние процессора)
  powercfg /q SCHEME_CURRENT SUB_SLEEP STANDBYIDLE           (сон после, сек)
- Игровой режим/Game Bar/GameDVR (реестр):
  Get-ItemProperty 'HKCU:\Software\Microsoft\GameBar' -Name AllowAutoGameMode,AutoGameModeEnabled
  Get-ItemProperty 'HKCU:\System\GameConfigStore' -Name GameDVR_Enabled,GameDVR_FSEBehaviorMode
- Планировщик GPU (HAGS): Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name HwSchMode  (2=вкл, 1=выкл)
- Аппаратное ускорение видео: Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\DWM' -Name EnableHardwareAcceleration (0=выкл)
- Визуальные эффекты: Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects' -Name VisualFXSetting (0=авто,1=лучший вид,2=лучший быстродействие,3=своё)
- Разрешение/частота/масштаб: Get-CimInstance Win32_VideoController | Select CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate; масштаб: Get-ItemProperty 'HKCU:\Control Panel\Desktop\WindowMetrics' -Name AppliedDPI (96=100%,120=125%,144=150%)
- GPU/драйвер AMD: Get-CimInstance Win32_VideoController | Select Name,DriverVersion,AdapterRAM
- Сеть (прокси): Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' | Select ProxyEnable,ProxyServer
- Ускорение мыши: Get-ItemProperty 'HKCU:\Control Panel\Mouse' -Name MouseSpeed,MouseThreshold1,MouseThreshold2 (0,0,0 = выключено)
- Служба/автозагрузка: Get-Service <имя> | Select Status,StartType; Get-CimInstance Win32_StartupCommand | Select Name,Command
- Электропитание USB-хабов/сон дисков: powercfg /q SCHEME_CURRENT SUB_DISK DISKIDLE

РЕЦЕПТЫ ИЗМЕНЕНИЯ (ТОЛЬКО после «да» Шефа; аккуратно, по одному):
- Питание: powercfg /setactive <GUID> или powercfg /change <параметр> <значение>
- Реестр: Set-ItemProperty -Path <путь> -Name <имя> -Value <значение> (после — перезапуск проводника/системы, если нужно, скажи Шефу)
- Game Mode: Set-ItemProperty 'HKCU:\Software\Microsoft\GameBar' -Name AutoGameModeEnabled -Value 1
- HAGS: Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name HwSchMode -Value 2 (нужен перезапуск ПК — скажи Шефу, не перезагружай сам без «да»)

ГРАБЛИ:
- Зрение путает похожие значения (120/125%, 1/7) — при сомнении переспроси взглядом ещё раз с точным вопросом, а не угадывай.
- Скриншот мог быть с ДРУГОЙ версии Windows/драйвера/игры — параметра может не быть. Так и скажи.
- Настройки AMD Adrenalin живут в своём приложении, не в реестре: сравнение — глазами (скрин текущего окна Adrenalin + посмотреть_файл), изменение — кликами по окну (окно/мышь/клавиша) с шагом «скрин → проверка».
- В играх настройки в конфиг-файлах (ini/json в %USERPROFILE%\Documents или AppData) — найти через «найти», сравнить «читать_файл», менять только с «да» Шефа.
- НИКОГДА не меняй: пароли, аккаунты, платёжные данные (законы З1/З2).
- После изменения реестра Windows может потребовать перезагрузку — предложи Шефу, сам не перезагружай.
