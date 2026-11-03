#!/usr/bin/env python3
"""Dò khoảng lặng theo NĂNG LƯỢNG âm thanh (không theo mốc từ của Whisper) và in danh sách đoạn giữ.

  python3 silence_cut.py <audio16k.wav> [thr_db=-34] [min_gap=0.18] [pad=0.07] > gaps.json

Vì sao không dùng word timestamp: Whisper hay "nuốt" khoảng lặng vào độ dài từ đứng trước
(vd 'cái' kéo 4,52→5,62s), nên cắt theo từ sẽ sót hoặc cắt lẹm.
Ngưỡng: đặt quanh phân vị 20% của RMS (dB) đã làm mượt; clip ngoài trời có nền ồn ~-40 dB.
Giữ `pad` ở mỗi mép để không mất phụ âm cuối/đầu. Sau khi dựng PHẢI phiên âm lại bản dựng để kiểm.
"""
import sys, json, wave
import numpy as np

wav = sys.argv[1]
thr = float(sys.argv[2]) if len(sys.argv) > 2 else -34
min_gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.18
w = wave.open(wav)
sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
hop = sr // 100
n = len(a) // hop
db = 20 * np.log10(np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop] ** 2)) + 1e-9 for i in range(n)]))
sm = np.convolve(db, np.ones(5) / 5, mode='same')
sys.stderr.write(f"RMS dB percentiles 5/20/50: {np.percentile(sm,5):.1f} / {np.percentile(sm,20):.1f} / {np.percentile(sm,50):.1f}\n")
low = sm < thr
gaps, i = [], 0
while i < n:
    if low[i]:
        j = i
        while j < n and low[j]: j += 1
        if (j - i) * 0.01 >= min_gap: gaps.append([round(i * 0.01, 2), round(j * 0.01, 2)])
        i = j
    else:
        i += 1
json.dump(gaps, sys.stdout)
sys.stderr.write(f"{len(gaps)} khoảng lặng\n")
