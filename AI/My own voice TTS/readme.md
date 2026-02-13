
## WAV-based TTS Prototype (Reconstructed)

🍯 [Code](https://github.com/ulsidae/dev_logs/blob/main/AI/My%20own%20voice%20TTS/main.py)

Originally created as a personal experiment on text-to-speech and pronunciation control.

## 💡 Summary  

This repository contains an early-stage prototype of a wav-based TTS system.


Instead of neural synthesis, this project maps text tokens directly to prerecorded `.wav` files and plays them sequentially, with light trimming and speed adjustment.


The goal was not audio quality, but understanding the structure of TTS systems from the lowest level.

---

## 🔊 Core idea

Input text is split by spaces.  
Each token corresponds to a wav file.

Playback flow:

text → wav lookup → trim → slight speed adjustment → sequential playback

No ML models.  
No external APIs.

Just waveform manipulation.
This is closer to audio sequencing than speech synthesis.

---

## ⏸ Pause control

Pauses were a problem.

So I introduced `@`.

Each `@` inserts a short silence.  
Multiple `@` tokens create hesitation-like timing.

Example:

> hello @ world  

→ hello (0.1s pause) world

This allows manual rhythm control during playback.
`@` acts as a timing token rather than a character.

---

## 🍯 Background

This project was built purely for educational exploration.

I was interested in:

- building TTS from scratch
- avoiding corporate black-box systems
- experimenting with explicit timing
- preparing for future phoneme-based synthesis
- eventually supporting my own voice

This implementation represents a very early architectural sketch.

---

## ✅ Current features

- word-based wav playback  
- automatic trimming  
- micro speed adjustment  
- `@`-based pause control  
- cross-platform audio playback (Windows / macOS / Linux)

---

## ⚠ Limitations

This is not a real TTS system.

- no phoneme processing  
- no synthesis  
- no prosody modeling  

Audio quality depends entirely on prerecorded wav files.

Performance and naturalness were not priorities.

---

## Why this repo exists

This repository exists as a record of learning.

Today, I can use existing TTS frameworks.  
Back then, I wanted to understand what happens underneath.

This code is not about sound quality.  
It is about curiosity.

---

## 🛠 Usage

Place wav files in `./wav_files`  
Name files after tokens (e.g. `hello.wav`)

Run:

```bash
python main.py
```









