# Докачка комментариев, чата и таймкодов (Windows)

1. В Chrome залогиньтесь на youtube.com, расширением «Get cookies.txt LOCALLY» экспортируйте куки для youtube.com в файл `cookies.txt` (формат Netscape) и положите его в папку `fetch` рядом с этим файлом. **Не коммитьте cookies.txt** (он в .gitignore).
2. Установите Python и yt-dlp: `pip install yt-dlp`.
3. В PowerShell из папки репозитория:
```
yt-dlp --cookies fetch/cookies.txt --skip-download --write-comments --write-subs --sub-langs "ru-orig,live_chat" --write-info-json --sleep-requests 2 --sleep-interval 8 --max-sleep-interval 15 -o "fetch/raw/%(id)s/%(id)s" -a fetch/ids_missing.txt
```
4. Загрузите папку `fetch/raw` в репозиторий (git add fetch/raw; commit; push, или перетащите на GitHub) и напишите мне — я соберу таймкоды, комментарии и чат.
