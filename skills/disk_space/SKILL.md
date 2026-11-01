# Скилл: Анализ занятого места
Описание: найти, куда исчезло место — большие папки и файлы, топ по объёму

## Когда
«что занимает место», «диск забит», «куда делись гигабайты».

## Как
1. «что_перенести» {"диск":"C"} — готовый анализ больших папок, быстрый старт.
2. Топ-20 папок первого уровня по объёму (минута-две, предупреди «считаю»):
   run_ps: Get-ChildItem -Directory 'C:\' -EA SilentlyContinue | ForEach-Object { $s=(Get-ChildItem $_.FullName -Recurse -EA SilentlyContinue | Measure-Object Length -Sum).Sum/1GB; '{0,8:N2} ГБ  {1}' -f $s,$_.FullName } | Sort-Object -Descending | Select-Object -First 20
3. Файлы-гиганты (>2 ГБ):
   run_ps: Get-ChildItem 'D:\' -Recurse -File -EA SilentlyContinue | Where-Object Length -gt 2GB | Sort-Object Length -Descending | Select-Object -First 15 | ForEach-Object { '{0,8:N2} ГБ  {1}' -f ($_.Length/1GB),$_.FullName }
4. Итог: список + что можно безопасно перенести или удалить — и спроси Шефа.

## Грабли
- Рекурсивный подсчёт по всему диску — минуты. Не молчи, пиши «считаю».
- WinSxS и C:\Windows не трогай без явного приказа.
