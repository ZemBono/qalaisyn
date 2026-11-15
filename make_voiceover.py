"""Builds the final demo video from 12 voice clips (01.mp3 ... 12.mp3, e.g. generated with ElevenLabs).
Each clip starts at its segment in VIDEO_SCRIPT_FULL.md; a clip longer than its segment is sped up slightly
(at most 1.25x) so it never runs into the next line. Run: .venv/Scripts/python make_voiceover.py"""
import json, pathlib, re, subprocess, sys
import imageio_ffmpeg
from make_prompter import lines

ROOT = pathlib.Path(__file__).parent
VOICE = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "demo_video" / "voice"
VID = ROOT / "demo_video" / "Qalaisyn_demo_full.mp4"
OUT = ROOT / "demo_video" / "Qalaisyn_demo_final.mp4"
FF = imageio_ffmpeg.get_ffmpeg_exe()
START_PAD = 0.3      # start speaking a moment after the segment begins


def duration(p):
    r = subprocess.run([FF, "-hide_banner", "-i", str(p)], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def find_clip(i):
    for ext in ("mp3", "wav", "m4a", "ogg", "aac", "flac"):
        for name in (f"{i:02d}.{ext}", f"{i}.{ext}"):
            if (VOICE / name).exists():
                return VOICE / name
    return None


def main():
    L = lines()
    inputs, filters, report = ["-i", str(VID)], [], []
    for i, (a, b, text) in enumerate(L, 1):
        clip = find_clip(i)
        if clip is None:
            report.append(f"{i:02d}: file missing"); continue
        d = duration(clip)
        room = (L[i][0] if i < len(L) else b) - a - START_PAD - 0.15
        tempo = min(1.25, d / room) if d > room else 1.0
        n = len(inputs) // 2
        inputs += ["-i", str(clip)]
        delay = int((a + START_PAD) * 1000)
        chain = f"[{n}:a]aresample=48000,aformat=channel_layouts=mono"
        if tempo > 1.0:
            chain += f",atempo={tempo:.3f}"
        chain += f",adelay={delay}|{delay}[v{n}]"
        filters.append(chain)
        report.append(f"{i:02d}: {d:4.1f}s in a {room:4.1f}s slot" + (f" -> sped up {tempo:.2f}x" if tempo > 1 else "")
                      + (" (STILL TOO LONG: shorten this line)" if d / tempo > room + 0.05 else ""))
    print("\n".join(report))
    k = len(filters)
    if not k:
        sys.exit("no clips found in " + str(VOICE))
    mix = "".join(f"[v{j}]" for j in range(1, k + 1))
    filters.append(f"{mix}amix=inputs={k}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,apad[a]")
    subprocess.run([FF, "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                    "-shortest", str(OUT)], check=True)
    print(OUT)


if __name__ == "__main__":
    main()
