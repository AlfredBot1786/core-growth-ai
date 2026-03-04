# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Voice Transcription

When John sends voice notes via Telegram:
1. Audio files are saved to `~/.openclaw/media/inbound/`
2. Use faster-whisper to transcribe:

```python
from faster_whisper import WhisperModel
model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe("/path/to/audio.ogg", language="en")
for segment in segments:
    print(segment.text)
```

Model: tiny (fast, lower accuracy) 
Larger models: base, small, medium, large

---

Add whatever helps you do your job. This is your cheat sheet.

---

### GitHub

- Account: AlfredBot1786 (alfred@coregrowthai.com)
- Auth: Using `gh` CLI with token stored in macOS keychain
- Can create repos, commits, PRs, issues, manage workflows
