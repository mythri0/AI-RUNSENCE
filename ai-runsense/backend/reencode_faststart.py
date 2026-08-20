"""
Re-encode all existing processed videos to browser-compatible H.264+faststart.
Run once to fix all existing sessions stored as MSMF/mp4v OpenCV output.
"""
import os, sys
sys.path.insert(0, '.')

from app.cv.video_converter import convert_to_web_h264, is_web_compatible

PROCESSED = "data/processed"
files = sorted(f for f in os.listdir(PROCESSED) if f.endswith(".mp4"))
print(f"Found {len(files)} processed video files\n")

ok_count = 0
skip_count = 0
fail_count = 0

for fname in files:
    fpath = os.path.join(PROCESSED, fname)
    size_before = os.path.getsize(fpath) / 1024 / 1024

    if is_web_compatible(fpath):
        print(f"  SKIP (already web-compatible): {fname} ({size_before:.1f}MB)")
        skip_count += 1
        continue

    print(f"  Converting: {fname} ({size_before:.1f}MB) ...", end=' ', flush=True)
    tmp = fpath + ".new.mp4"
    ok = convert_to_web_h264(fpath, tmp)
    if ok and os.path.exists(tmp):
        size_after = os.path.getsize(tmp) / 1024 / 1024
        os.replace(tmp, fpath)
        print(f"OK -> {size_after:.1f}MB")
        ok_count += 1
    else:
        if os.path.exists(tmp):
            os.remove(tmp)
        print("FAILED")
        fail_count += 1

print(f"\n=== Done: {ok_count} converted, {skip_count} skipped, {fail_count} failed ===")

# Verify first file is now web-compatible
sample = os.path.join(PROCESSED, files[0]) if files else None
if sample:
    with open(sample, 'rb') as f:
        head = f.read(1024 * 1024)
    moov = head.find(b'moov')
    mdat = head.find(b'mdat')
    print(f"\nVerification on {files[0]}:")
    print(f"  moov at offset {moov}, mdat at offset {mdat}")
    if moov >= 0 and (mdat < 0 or moov < mdat):
        print("  => FASTSTART OK - browser can start playing immediately!")
    else:
        print("  => WARNING: moov still not before mdat")
