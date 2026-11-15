"""Teleprompter video: the demo video with each voice-over line shown at the moment to say it, after a 3-2-1 countdown.
Also: merge_voice(audio) puts the recorded voice onto the clean demo video.
Run: .venv/Scripts/python make_prompter.py            -> demo_video/Qalaisyn_prompter.mp4
     .venv/Scripts/python make_prompter.py voice.m4a  -> demo_video/Qalaisyn_demo_with_voice.mp4"""
import pathlib, re, subprocess, sys
import imageio_ffmpeg

ROOT = pathlib.Path(__file__).parent
VID = ROOT / "demo_video" / "Qalaisyn_demo_full.mp4"
FF = imageio_ffmpeg.get_ffmpeg_exe()
LEAD = 3.0          # seconds of countdown before the demo starts
EARLY = 0.6         # show each line a little before its segment starts, so there is time to read the first words


def lines():
    s = (ROOT / "VIDEO_SCRIPT_FULL.md").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r'\*\*(\d+):(\d+)–(\d+):(\d+) · .*?\*\*\n> "(.*?)"', s, re.S):
        out.append((int(m[1]) * 60 + int(m[2]), int(m[3]) * 60 + int(m[4]), m[5].replace("\n", " ")))
    return out


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def make_prompter():
    L = lines()
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 0", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
           "MarginR, MarginV, Encoding",
           "Style: Say,Segoe UI,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&HC0201810,1,0,0,0,100,100,0,0,3,22,0,2,140,140,70,1",
           "Style: Next,Segoe UI,34,&H00B8C4CC,&H00B8C4CC,&H00000000,&HC0201810,0,0,0,0,100,100,0,0,3,14,0,8,160,160,40,1",
           "Style: Count,Segoe UI,220,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0201810,1,0,0,0,100,100,0,0,3,40,0,5,0,0,0,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for i, n in enumerate(("3", "2", "1")):
        ass.append(f"Dialogue: 0,{ts(i)},{ts(i + 1)},Count,,0,0,0,,{n}")
    ass.append(f"Dialogue: 0,{ts(0)},{ts(LEAD)},Next,,0,0,0,,Start your voice recording now. First line: {L[0][2]}")
    for k, (a, b, text) in enumerate(L):
        start, end = LEAD + a - (EARLY if k else 0), LEAD + b
        ass.append(f"Dialogue: 0,{ts(start)},{ts(end)},Say,,0,0,0,,{text}")
        if k + 1 < len(L):
            ass.append(f"Dialogue: 0,{ts(end - 3)},{ts(end)},Next,,0,0,0,,next: {L[k + 1][2][:90]}…")
    p = ROOT / "demo_video" / "prompter.ass"
    p.write_text("\n".join(ass), encoding="utf-8")
    out = ROOT / "demo_video" / "Qalaisyn_prompter.mp4"
    # 3 s of the first frame frozen for the countdown, then the demo with the lines burned in
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(VID), "-vf",
                    f"tpad=start_duration={LEAD}:start_mode=clone,subtitles=prompter.ass",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-r", "30", str(out)],
                   check=True, cwd=str(ROOT / "demo_video"))
    print(out)


def merge_voice(audio):
    """Put the voice onto the clean demo video. The voice was recorded while the prompter played, so speech starts
    about LEAD seconds after the countdown began; we find the first speech and line it up with the first line."""
    audio = pathlib.Path(audio)
    # where speech starts in the recording (first moment louder than -35 dB)
    r = subprocess.run([FF, "-hide_banner", "-i", str(audio), "-af", "silencedetect=noise=-35dB:d=0.4", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    m = re.search(r"silence_end: ([\d.]+)", r.stderr)
    first_speech = float(m.group(1)) if m and float(m.group(1)) < 15 else 0.0
    shift = first_speech - 0.4          # the first words come ~0.4 s into the demo
    out = ROOT / "demo_video" / "Qalaisyn_demo_with_voice.mp4"
    af = f"atrim=start={max(shift, 0):.2f},asetpts=PTS-STARTPTS" if shift > 0 else f"adelay={int(-shift * 1000)}|{int(-shift * 1000)}"
    af += ",loudnorm=I=-16:TP=-1.5:LRA=11,apad"
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(VID), "-i", str(audio), "-filter_complex",
                    f"[1:a]{af}[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                    "-shortest", str(out)], check=True)
    print(out, f"(speech started at {first_speech:.2f}s in the recording, shifted by {shift:.2f}s)")


if __name__ == "__main__":
    merge_voice(sys.argv[1]) if len(sys.argv) > 1 else make_prompter()
