import cv2, os, struct

processed = 'data/processed'
print('=== PROCESSED VIDEO CODEC & MP4 BOX ANALYSIS ===')
for fname in ['session_9_pose.mp4', 'session_9_analysis.mp4', 'session_10_pose.mp4', 'session_10_analysis.mp4']:
    fpath = os.path.join(processed, fname)
    if not os.path.exists(fpath):
        print(f"  MISSING: {fname}")
        continue
    size = os.path.getsize(fpath)
    cap = cv2.VideoCapture(fpath)
    fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc_str = ''.join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    with open(fpath, 'rb') as f:
        raw = f.read(8)
    box_type = raw[4:8].decode('ascii', errors='ignore')
    print(f"  {fname}: {size/1024/1024:.1f}MB, codec={fourcc_str!r}, {w}x{h}@{fps:.0f}fps, frames={frames}, first_box={box_type!r}")

print('\n=== KEY: mp42 brand + H264 codec = browser-decodable H.264 ===')
print('=== CHECK: moov atom position for streaming ===')

for fname in ['session_9_pose.mp4']:
    fpath = os.path.join(processed, fname)
    if not os.path.exists(fpath): continue
    # Scan first 512 bytes for 'moov' box
    with open(fpath, 'rb') as f:
        head = f.read(512)
    moov_pos = head.find(b'moov')
    mdat_pos = head.find(b'mdat')
    print(f"  {fname}: moov found at offset {moov_pos}, mdat found at offset {mdat_pos}")
    if moov_pos >= 0 and (mdat_pos < 0 or moov_pos < mdat_pos):
        print("  => FASTSTART OK (moov before mdat)")
    elif moov_pos >= 0:
        print("  => SLOW START (mdat before moov) - browser must download full file before playing")
    else:
        print("  => moov NOT IN FIRST 512 bytes - browser must download much of file first")
