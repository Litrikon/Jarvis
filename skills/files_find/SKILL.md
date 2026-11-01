# Скилл: Поиск файлов
Описание: найти файлы/папки по имени, маске или размеру; найти дубликаты

## Когда
«найди ...», «где лежит ...», «есть ли где-нибудь ...».

## Как
1. Простое: «найти» {"mask":"*.pdf","where":"D:\"} — быстрый топ-15.
2. С размером и датой:
   run_ps: Get-ChildItem 'D:\' -Recurse -File -Filter '*.pdf' -EA SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 15 | ForEach-Object { '{0,10:N1} МБ  {1}  {2}' -f ($_.Length/1MB),$_.LastWriteTime.ToString('dd.MM.yy'),$_.FullName }
3. Дубликаты по имени+размеру (быстро):
   run_ps: Get-ChildItem 'D:\' -Recurse -File -EA SilentlyContinue | Group-Object Name,Length | Where-Object Count -gt 1 | Select-Object -First 10 | ForEach-Object { $_.Group.FullName }
4. Точная проверка дубля — по хэшу (медленно, только для файлов до 1-2 ГБ):
   run_ps: Get-FileHash 'файл1','файл2' -Algorithm MD5 | Format-Table Hash,Path

## Грабли
- Поиск по всему диску — до пары минут, пиши «ищу».
- Мусор в выдаче: System Volume Information, $Recycle.Bin, AppData\Local\Temp — фильтруй.
