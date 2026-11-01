# Скилл: Архивы ZIP
Описание: упаковать, распаковать, посмотреть содержимое ZIP

## Когда
«заархивируй», «распакуй», «сожми папку», «что в архиве».

## Как
1. Упаковать:
   run_ps: Compress-Archive -Path 'D:\папка' -DestinationPath 'D:\папка.zip' -Force
   Только часть файлов: -Path 'D:\папка\*.log'
2. Распаковать:
   run_ps: Expand-Archive -Path 'D:\x.zip' -DestinationPath 'D:\x_out' -Force
3. Содержимое:
   run_ps: Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::OpenRead('D:\x.zip').Entries | Select-Object -First 30 FullName,@{n='МБ';e={[math]::Round($_.Length/1MB,2)}}
4. Дописать в архив: Compress-Archive с -Update.

## Грабли
- Существующий на месте назначения архив — нужен -Force (перезапишет: убедись, что это ок).
- Пустые папки Compress-Archive не сохраняет.
- Десятки ГБ — долго, предупреди Шефа.
