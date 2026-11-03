#!/usr/bin/env python3
"""Phiên âm tiếng Việt có mốc thời gian từng từ bằng faster-whisper.

  pip install faster-whisper numpy
  ffmpeg -i in.mp4 -ac 1 -ar 16000 audio16k.wav
  python3 transcribe_vi.py small audio16k.wav > transcript.json

Tham số đầu là tên model (`small`, `medium`) hoặc đường dẫn tới thư mục model đã tải sẵn.
Kết quả thô thường nghe sai tên riêng và con số. Hãy sửa tay, và hỏi người dùng xác nhận
mọi con số (giá, diện tích) trước khi đưa lên thẻ chữ.
"""
import json, sys, wave
import numpy as np
from faster_whisper import WhisperModel

model, wav = sys.argv[1], sys.argv[2]
w = wave.open(wav)
audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
segments, _ = WhisperModel(model, device='cpu', compute_type='int8').transcribe(
    audio, language='vi', word_timestamps=True, beam_size=5,
    initial_prompt='Môi giới bất động sản giới thiệu nhà phố, hẻm xe hơi, diện tích, giá bán.')
out = []
for s in segments:
    out.append({'start': s.start, 'end': s.end, 'text': s.text,
                'words': [{'w': x.word, 's': x.start, 'e': x.end, 'p': x.probability} for x in s.words]})
    sys.stderr.write(f'[{s.start:6.2f}-{s.end:6.2f}] {s.text}\n')
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
