#!/usr/bin/env python3
"""Build timestamped transcripts, comments and live-chat replay from yt-dlp raw files.
usage: build_extras.py RAWDIR INDEX OUTDIR   (RAWDIR/<id>/<id>.{ru-orig.vtt,info.json,live_chat.json})"""
import json, os, re, sys

def ts(sec):
    sec = int(sec); return "%02d:%02d:%02d" % (sec // 3600, sec % 3600 // 60, sec % 60)

def timed_transcript(vtt, vid, chunk=45):
    cues = []  # (start_sec, text)
    start = 0
    for raw in open(vtt, encoding="utf-8"):
        m = re.match(r"(\d\d):(\d\d):(\d\d)\.\d+ -->", raw)
        if m:
            start = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]); continue
        if "<c>" in raw or re.search(r"<\d\d:\d\d:\d\d\.\d+>", raw):
            s = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw)).strip()
            if s: cues.append((start, s))
    paras, cur, t0 = [], [], None
    for t, s in cues:
        if t0 is None: t0 = t
        elif t - t0 >= chunk:
            paras.append((t0, " ".join(cur))); cur, t0 = [], t
        cur.append(s)
    if cur: paras.append((t0, " ".join(cur)))
    return "\n\n".join("[%s](https://www.youtube.com/watch?v=%s&t=%ds) %s" % (ts(t), vid, t, p) for t, p in paras)

def comments_md(info):
    cs = info.get("comments") or []
    top = [c for c in cs if c.get("parent") == "root"]
    rep = {}
    for c in cs:
        if c.get("parent") != "root": rep.setdefault(c["parent"], []).append(c)
    out = []
    for c in sorted(top, key=lambda c: -(c.get("like_count") or 0)):
        out.append("- **%s** (👍 %s): %s" % (c["author"], c.get("like_count") or 0, c["text"].replace("\n", "\n  ")))
        for r in rep.get(c["id"], []):
            out.append("  - **%s**: %s" % (r["author"], r["text"].replace("\n", " ")))
    return len(cs), "\n".join(out)

def chat_md(path):
    rows = []
    for l in open(path, encoding="utf-8"):
        try: j = json.loads(l)
        except Exception: continue
        a = j.get("replayChatItemAction")
        if not a: continue
        off = int(a.get("videoOffsetTimeMsec", 0)) / 1000
        for x in a.get("actions", []):
            it = x.get("addChatItemAction", {}).get("item", {})
            r = it.get("liveChatTextMessageRenderer") or it.get("liveChatPaidMessageRenderer")
            if r:
                msg = "".join(y.get("text") or y.get("emoji", {}).get("shortcuts", [""])[0] for y in r.get("message", {}).get("runs", []))
                rows.append((off, r["authorName"]["simpleText"], msg))
    rows.sort()
    return len(rows), "\n".join("- `%s` **%s**: %s" % (ts(max(o, 0)), a, m) for o, a, m in rows)

if __name__ == "__main__":
    raw, index, out = sys.argv[1:4]
    for d in ("transcripts", "comments", "chat"): os.makedirs(os.path.join(out, d), exist_ok=True)
    for line in open(index, encoding="utf-8"):
        n, vid, dur, title = line.rstrip("\n").split("|", 3)
        base = os.path.join(raw, vid, vid)
        if not os.path.exists(os.path.join(raw, vid, "done")): continue
        name = "%s_%s.md" % (n, vid)
        hdr = "# Урок %d. %s\n\nhttps://www.youtube.com/watch?v=%s\n\n" % (int(n), title, vid)
        if os.path.exists(base + ".ru-orig.vtt"):
            open(os.path.join(out, "transcripts", name), "w", encoding="utf-8").write(
                hdr + "> Автосубтитры YouTube (ru-orig) с таймкодами (клик — переход к моменту видео). Возможны ошибки распознавания.\n\n" + timed_transcript(base + ".ru-orig.vtt", vid) + "\n")
        if os.path.exists(base + ".info.json"):
            k, body = comments_md(json.load(open(base + ".info.json", encoding="utf-8")))
            open(os.path.join(out, "comments", name), "w", encoding="utf-8").write(hdr + "Комментариев: %d\n\n" % k + (body or "_нет комментариев_") + "\n")
        if os.path.exists(base + ".live_chat.json"):
            k, body = chat_md(base + ".live_chat.json")
            open(os.path.join(out, "chat", name), "w", encoding="utf-8").write(hdr + "Повтор чата прямой трансляции, сообщений: %d (время — от начала видео)\n\n" % k + (body or "_нет сообщений_") + "\n")
