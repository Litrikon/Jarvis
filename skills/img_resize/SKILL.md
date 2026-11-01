# Скилл: img_resize

Описание: Изменение размера изображений (JPG, PNG, BMP, WEBP) по пикселям, весу файла или процентам.
Когда: Шеф просит уменьшить/увеличить фото, сделать файл легче, изменить разрешение.
Как: Использовать PowerShell с System.Drawing. Примеры: 1) По пикселям: Add-Type -AssemblyName System.Drawing; $img = [System.Drawing.Image]::FromFile('C:\photo.jpg'); $new = New-Object System.Drawing.Bitmap 1920, 1080; $g = [System.Drawing.Graphics]::FromImage($new); $g.DrawImage($img, 0, 0, $new.Width, $new.Height); $new.Save('C:\photo_new.jpg'); 2) По весу: перебирать качество JPEG (1-100) пока размер не станет нужным. 3) По процентам: рассчитать новые размеры от текущих. Грабли: Не забыть закрыть Graphics и Bitmap, иначе файл может блокироваться. Для PNG использовать Lossless если нужно сохранить прозрачность.
