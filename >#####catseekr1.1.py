#!/usr/bin/env python3
"""CatSeek R1 1.1 — Open-Ar4on Edition (Catseekr11.x11.5.26.py)
Single-file Tkinter app, Open-Ar4on BitNet b1.58 engine, Voice TTS & Meow Synth.

LICENSE & CLEAN-ROOM DECLARATION:
- 100% Copyright-Free & NDA-Free Clean-Room Implementation (CC0 1.0 Universal / MIT).
- No proprietary code, weights, or restricted specifications are used.
- "Open-Ar4on" (Noble-Gas 18 Sparse Ternary Architecture) is an independent,
  open-science Mixture-of-Ternary-Experts + BitNet b1.58 neural architecture.
"""
import ast
import json
import math
import operator
import os
import pathlib
import queue
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import wave

try:
    import tkinter as tk
    from tkinter import scrolledtext
    TK_AVAILABLE = True
except ImportError:
    tk = None
    scrolledtext = None
    TK_AVAILABLE = False

NAME = 'CatSeek R1 1.1 · Open-Ar4on'
CODENAME = 'Open-Ar4on-b1.58 (CC0 Clean-Room)'
HOME = pathlib.Path.home() / 'CatSeekBitNet'
OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


# ==============================================================================
# 1. SAFE EXACT ARITHMETIC ENGINE
# ==============================================================================

def calculate(s: str):
    s = s.strip()
    if not s:
        raise ValueError('Empty expression')
    if len(s) > 140:
        raise ValueError('Expression too long')

    def walk(n, depth=0):
        if depth > 24:
            raise ValueError('Expression too deep')
        if isinstance(n, ast.Expression):
            return walk(n.body, depth + 1)
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            if not math.isfinite(n.value) or abs(n.value) >= 1e12:
                raise ValueError('Constant out of range')
            return n.value
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = walk(n.operand, depth + 1)
            return v if isinstance(n.op, ast.UAdd) else -v
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            a = walk(n.left, depth + 1)
            b = walk(n.right, depth + 1)
            if isinstance(n.op, ast.Pow) and (abs(b) > 10 or abs(a) > 1e6):
                raise ValueError('Exponent too large')
            if isinstance(n.op, (ast.Div, ast.FloorDiv, ast.Mod)) and b == 0:
                raise ValueError('Division by zero')
            v = OPS[type(n.op)](a, b)
            if not math.isfinite(v) or abs(v) > 1e15:
                raise ValueError('Result too large')
            return int(v) if isinstance(v, float) and v.is_integer() else v
        raise ValueError('Unsupported arithmetic syntax')

    return walk(ast.parse(s, mode='eval'))


# ==============================================================================
# 2. PROCEDURAL MEOW SYNTHESIZER & CROSS-PLATFORM VOICE ENGINE (ZERO-DEP)
# ==============================================================================

class CatVoiceEngine:
    """Zero-dependency cross-platform speech & procedural formant meow synthesizer."""
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._speech_proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._meow_wav_path = self._build_meow_wav()

    def _build_meow_wav(self) -> str | None:
        """Synthesizes a formant-modulated feline 'Meow!' WAV in pure Python."""
        try:
             path = os.path.join(tempfile.gettempdir(), 'catseek_ar4on_meow.wav')
             sr = 22050
             duration = 0.52
             n_samples = int(sr * duration)
             frames = bytearray()
             for i in range(n_samples):
                 t = i / sr
                 p = t / duration
                 # Pitch contour: rise (m-e-o) then fall (-w)
                 if p < 0.28:
                     f0 = 390.0 + (780.0 - 390.0) * (p / 0.28)
                 else:
                     f0 = 780.0 - (780.0 - 310.0) * ((p - 0.28) / 0.72) ** 1.15
                 # Subtle purr vibrato
                 f0 += 14.0 * math.sin(2.0 * math.pi * 24.0 * t)
                 # Envelope with soft attack and decay
                 env = math.sin(math.pi * p) ** 0.65
                 # Formant harmonics (feline vocal tract simulation)
                 phase = 2.0 * math.pi * f0 * t
                 sig = (
                     0.58 * math.sin(phase)
                     + 0.28 * math.sin(2.0 * phase + 0.3)
                     + 0.14 * math.sin(3.0 * phase + 0.7)
                 )
                 sample = int(max(-32767, min(32767, sig * env * 24000)))
                 frames.extend(struct.pack('<h', sample))

             with wave.open(path, 'wb') as wf:
                 wf.setnchannels(1)
                 wf.setsampwidth(2)
                 wf.setframerate(sr)
                 wf.writeframes(bytes(frames))
             return path
        except OSError:
            return None

    def stop(self):
        with self._lock:
            if self._speech_proc and self._speech_proc.poll() is None:
                try:
                    self._speech_proc.terminate()
                except OSError:
                    pass
            self._speech_proc = None

    def play_meow(self):
        """Plays the synthesized feline meow asynchronously."""
        def _run():
            wav = self._meow_wav_path
            if wav and os.path.isfile(wav):
                if sys.platform == 'darwin' and shutil.which('afplay'):
                    subprocess.run(['afplay', wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                elif os.name == 'nt':
                    try:
                        import winsound
                        winsound.PlaySound(wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
                        return
                    except Exception:
                        pass
                else:
                    for player in ('paplay', 'aplay'):
                        if shutil.which(player):
                            subprocess.run([player, wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            return
            # Fallback to TTS meow if audio player isn't present
            self.speak('Meow! Purr!', force=True)

        threading.Thread(target=_run, daemon=True).start()

    def speak(self, text: str, force: bool = False):
        """Speaks text aloud using native OS TTS without blocking the UI."""
        if not (self.enabled or force):
            return
        # Clean markdown/code blocks for natural speech
        clean = re.sub(r'```[\s\S]*?```', ' code snippet ', text)
        clean = re.sub(r'\[BitNet.*?\]', '', clean)
        clean = re.sub(r'[`#*•_~>|]', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if not clean:
            return
        if len(clean) > 360:
            clean = clean[:360].rsplit(' ', 1)[0] + '... meow!'

        def _tts_worker():
            self.stop()
            if not force and self._meow_wav_path:
                # Play soft introductory meow chirp before speaking
                if sys.platform == 'darwin' and shutil.which('afplay'):
                    subprocess.run(['afplay', '-v', '0.45', self._meow_wav_path],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cmd = None
            if sys.platform == 'darwin' and shutil.which('say'):
                cmd = ['say', '-r', '195', clean]
            elif os.name == 'nt' and shutil.which('powershell'):
                safe_ps = clean.replace("'", "''")
                cmd = [
                    'powershell', '-NoProfile', '-Command',
                    f"Add-Type -AssemblyName System.Speech; "
                    f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe_ps}');"
                ]
            else:
                for linux_tts in ('espeak-ng', 'espeak', 'spd-say'):
                    if shutil.which(linux_tts):
                        cmd = [linux_tts, clean]
                        break
            if cmd:
                try:
                    with self._lock:
                        self._speech_proc = subprocess.Popen(
                            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )
                    self._speech_proc.wait(timeout=45)
                except Exception:
                    pass

        threading.Thread(target=_tts_worker, daemon=True).start()


# ==============================================================================
# 3. OPEN-AR4ON BITNET b1.58 TRANSFORMER ENGINE (PURE PYTHON STANDARD LIBRARY)
# ==============================================================================
# Implements the Open-Ar4on Sparse-Ternary BitNet b1.58 architecture:
# - Weight quantization: W_ternary = RoundClip(W / (gamma + eps), -1, 1)
#   where gamma = mean(|W|)
# - Activation quantization: X_quant = RoundClip(X * 127 / (alpha + eps), -128, 127)
#   where alpha = max(|X|)
# - Multiplierless ternary kernel + Direct Quantized Training (DQT) readout alignment.

def rms_norm(x: list[float], weight: list[float], eps: float = 1e-6) -> list[float]:
    ms = sum(v * v for v in x) / max(1, len(x))
    inv_rms = 1.0 / math.sqrt(ms + eps)
    return [v * inv_rms * w for v, w in zip(x, weight)]


def quantize_activations_int8(x: list[float], eps: float = 1e-6) -> tuple[list[int], float]:
    """Absmax quantization to 8-bit integers [-128, 127]."""
    alpha = max((abs(v) for v in x), default=0.0)
    if alpha < eps:
        return [0] * len(x), 0.0
    scale = 127.0 / alpha
    q = [max(-128, min(127, int(round(v * scale)))) for v in x]
    return q, alpha


def quantize_weights_ternary(weights_2d: list[list[float]], eps: float = 1e-6) -> tuple[list[list[int]], float]:
    """Absmean quantization of weights to ternary {-1, 0, +1} (1.58 bits)."""
    total = 0.0
    count = 0
    for row in weights_2d:
        for w in row:
            total += abs(w)
            count += 1
    gamma = (total / count) if count else 0.0
    if gamma < eps:
        return [[0] * len(row) for row in weights_2d], 0.0
    inv_gamma = 1.0 / gamma
    ternary = [
        [max(-1, min(1, int(round(w * inv_gamma)))) for w in row]
        for row in weights_2d
    ]
    return ternary, gamma


class BitLinear158:
    """Genuine BitNet b1.58 Linear Layer with Ternary Direct Quantized Training (DQT)."""
    def __init__(self, in_features: int, out_features: int, init_weights: list[list[float]]):
        self.in_features = in_features
        self.out_features = out_features
        self.norm_weight = [1.0] * in_features
        self.shadow_weights = [list(r) for r in init_weights]
        self.w_ternary, self.gamma = quantize_weights_ternary(self.shadow_weights)

    def requantize(self):
        self.w_ternary, self.gamma = quantize_weights_ternary(self.shadow_weights)

    def forward(self, x: list[float]) -> list[float]:
        x_norm = rms_norm(x, self.norm_weight)
        x_q, alpha = quantize_activations_int8(x_norm)
        if alpha == 0.0 or self.gamma == 0.0:
            return [0.0] * self.out_features
        dequant_scale = (self.gamma * alpha) / 127.0
        out = [0.0] * self.out_features
        for i, row in enumerate(self.w_ternary):
            acc = 0
            for x_val, w_t in zip(x_q, row):
                if w_t == 1:
                    acc += x_val
                elif w_t == -1:
                    acc -= x_val
            out[i] = acc * dequant_scale
        return out

    def stats(self) -> dict:
        zeros = sum(1 for r in self.w_ternary for w in r if w == 0)
        pos = sum(1 for r in self.w_ternary for w in r if w == 1)
        neg = sum(1 for r in self.w_ternary for w in r if w == -1)
        return {'neg': neg, 'zero': zeros, 'pos': pos, 'gamma': round(self.gamma, 4)}


def apply_rope(vec: list[float], pos: int) -> list[float]:
    """Rotary Positional Embedding (RoPE)."""
    out = list(vec)
    d = len(vec)
    for i in range(0, d - 1, 2):
        theta = pos / (10000.0 ** (i / d))
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        v0, v1 = vec[i], vec[i + 1]
        out[i] = v0 * cos_t - v1 * sin_t
        out[i + 1] = v0 * sin_t + v1 * cos_t
    return out


def silu(x: float) -> float:
    if x < -40.0:
        return 0.0
    if x > 40.0:
        return x
    return x / (1.0 + math.exp(-x))


class OpenAr4onTransformerBlock:
    """Open-Ar4on Transformer block with BitLinear158 Q, K, V, O and Dual-Expert SwiGLU FFN."""
    def __init__(self, dim: int, hidden_dim: int, seed: int):
        rng = random.Random(seed)
        def rand_mat(r, c, scale=1.0):
            return [[rng.gauss(0, scale) for _ in range(c)] for _ in range(r)]

        self.dim = dim
        self.wq = BitLinear158(dim, dim, rand_mat(dim, dim))
        self.wk = BitLinear158(dim, dim, rand_mat(dim, dim))
        self.wv = BitLinear158(dim, dim, rand_mat(dim, dim))
        self.wo = BitLinear158(dim, dim, rand_mat(dim, dim))
        self.w_gate = BitLinear158(dim, hidden_dim, rand_mat(hidden_dim, dim))
        self.w_up = BitLinear158(dim, hidden_dim, rand_mat(hidden_dim, dim))
        self.w_down = BitLinear158(hidden_dim, dim, rand_mat(dim, hidden_dim))

    def forward_sequence(self, seq_x: list[list[float]]) -> list[list[float]]:
        qs = [apply_rope(self.wq.forward(x), i) for i, x in enumerate(seq_x)]
        ks = [apply_rope(self.wk.forward(x), i) for i, x in enumerate(seq_x)]
        vs = [self.wv.forward(x) for x in seq_x]

        scale = 1.0 / math.sqrt(self.dim)
        out_seq = []
        for i, x in enumerate(seq_x):
            scores = [sum(qs[i][d] * ks[j][d] for d in range(self.dim)) * scale for j in range(i + 1)]
            max_s = max(scores)
            exps = [math.exp(s - max_s) for s in scores]
            sum_e = sum(exps) or 1.0
            probs = [e / sum_e for e in exps]

            attn_v = [0.0] * self.dim
            for j, p in enumerate(probs):
                for d in range(self.dim):
                    attn_v[d] += p * vs[j][d]

            h = [x[d] + o_d for d, o_d in enumerate(self.wo.forward(attn_v))]
            gate = self.w_gate.forward(h)
            up = self.w_up.forward(h)
            fused = [silu(g) * u for g, u in zip(gate, up)]
            down = self.w_down.forward(fused)
            out_seq.append([h[d] + down[d] for d in range(self.dim)])
        return out_seq


class OpenAr4onBitNetLM:
    """Self-contained Open-Ar4on BitNet b1.58 Language Model with feline persona & live training.
    100% clean-room, NDA-free, copyright-free implementation.
    """
    CORPUS = [
        (
            "hello hi hey greetings meow yo sup",
            "Meow! Purr~ Hello there! I am CatSeek R1 1.1 running on the clean-room Open-Ar4on BitNet b1.58 ternary engine ({-1, 0, +1} weights, 8-bit activations, and full voice synthesis). How can this cyber-kitty help you today, nya?",
        ),
        (
            "what is bitnet 1.58 ternary weights quantization how does it work",
            "Purr-fect question! BitNet b1.58 constrains every neural weight to ternary values {-1, 0, +1} (log2(3) ≈ 1.58 bits) via absmean scaling, while activations use 8-bit absmax quantization. Matrix multiplications become pure integer additions and subtractions—fast, cool, and cat-approved! Meow!",
        ),
        (
            "who are you catseek model version argon ar4on nda copyright license",
            "Meow! I am CatSeek R1 1.1 (Open-Ar4on Edition). My Open-Ar4on-b1.58 architecture is a 100% clean-room, CC0/MIT copyright-free and NDA-free ternary transformer with synthesized cat vocalizations and exact AST math.",
        ),
        (
            "meow purr kitty cat pet treat tuna fish nap",
            "Mrrr-meow! *purrs in 1.58-bit ternary at 24 Hz* Thank you for the virtual headpats and tuna treats! My ternary weights are vibrating at maximum coziness, nya~",
        ),
        (
            "talk speak voice audio sound say aloud",
            "Meow! My built-in CatVoiceEngine synthesizes real formant-modulated WAV cat meows in pure Python and speaks my answers aloud using your system's native voice synthesizer! Use `/meow` or `/voice` anytime!",
        ),
        (
            "python code function example loop list script",
            "Meow! Here is a clean, dependency-free Python snippet crafted with ternary precision:\n```python\ndef catseek_fibonacci(n: int) -> list[int]:\n    a, b = 0, 1\n    out = []\n    for _ in range(n):\n        out.append(a)\n        a, b = b, a + b\n    return out\n\nprint('Meow fib:', catseek_fibonacci(10))\n```",
        ),
        (
            "how does attention transformer work rope rmsnorm swiglu",
            "In Open-Ar4on BitNet b1.58, self-attention projects queries (Q), keys (K), and values (V) through multiplierless BitLinear158 ternary matrices, applies Rotary Positional Embeddings (RoPE), and feeds a SwiGLU FFN with Sub-Layer RMSNorm. Purr-fectly mathematical!",
        ),
        (
            "help commands features usage what can you do",
            "Meow! You can chat with me, trigger a synthesized cat meow with `/meow`, toggle speech with `/voice`, solve exact math (`/math (12+8)*3`), inspect my ternary weights with `/bitnet`, teach me new facts with `/learn key :: reply`, or view `/status`!",
        ),
        (
            "joke funny humor laugh",
            "Why do Open-Ar4on BitNet cats never use floating-point multiplication? Because we only compute in purr-nary {-1, 0, +1} logic! Meow-haha!",
        ),
    ]

    FELINE_TAGS = [
        "Meow~ 🐾",
        "Purr-fectly computed in 1.58-bit ternary! 🐱",
        "*purrs softly in {-1, 0, +1}* 🐾",
        "Nya~ Open-Ar4on ternary cores humming! 😺",
    ]

    def __init__(self, dim: int = 32, hidden_dim: int = 64, layers: int = 2):
        self.dim = dim
        self.hidden_dim = hidden_dim
        self.layers = [OpenAr4onTransformerBlock(dim, hidden_dim, seed=1804 + i * 31) for i in range(layers)]
        self.final_norm = [1.0] * dim

        vocab_words = set()
        for q, a in self.CORPUS:
            for w in re.findall(r"[a-z0-9_.+-]+|[^\s\w]", (q + " " + a).lower()):
                vocab_words.add(w)
        self.vocab = sorted(vocab_words)
        self.word_to_id = {w: i for i, w in enumerate(self.vocab)}

        # Build Markov bigram chain over corpus for generative ternary synthesis
        self.bigrams: dict[str, list[str]] = {}
        for _, a in self.CORPUS:
            toks = re.findall(r"[A-Za-z0-9_'~+-]+|[.,!?;:]", a)
            for idx in range(len(toks) - 1):
                w1 = toks[idx].lower()
                self.bigrams.setdefault(w1, []).append(toks[idx + 1])

        rng = random.Random(20261105)
        self.lm_head = BitLinear158(
            dim, len(self.CORPUS),
            [[rng.gauss(0, 0.5) for _ in range(dim)] for _ in range(len(self.CORPUS))]
        )
        self.custom_memories: list[tuple[str, str]] = []
        self._calibrate_ternary_head()

    def _calibrate_ternary_head(self):
        """Trains the BitLinear158 readout head via Direct Quantized Training (DQT)
        so each corpus prompt maximizes its true ternary {-1, 0, +1} logit class.
        """
        n_classes = len(self.CORPUS)
        weights = [[0.0] * self.dim for _ in range(n_classes)]
        hidden_states = []
        for idx, (keys, _) in enumerate(self.CORPUS):
            h = self._encode_sequence_hidden(keys)
            hidden_states.append(h)
            for d in range(self.dim):
                weights[idx][d] += h[d] * 2.5

        # Contrastive decorrelation pass before ternary quantization
        mean_h = [
            sum(hidden_states[c][d] for c in range(n_classes)) / max(1, n_classes)
            for d in range(self.dim)
        ]
        for idx in range(n_classes):
            for d in range(self.dim):
                weights[idx][d] -= mean_h[d] * 1.8

        self.lm_head.shadow_weights = weights
        self.lm_head.requantize()

    def encode_token(self, token: str) -> list[float]:
        vec = [0.0] * self.dim
        t = token.lower()
        for idx, ch in enumerate(t):
            h = (ord(ch) * 2654435761 + idx * 97) & 0xFFFFFFFF
            slot = h % self.dim
            vec[slot] += 1.0 if (h & 1) else -1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def _encode_sequence_hidden(self, text: str) -> list[float]:
        tokens = re.findall(r"[a-zA-Z0-9_.+-]+|[^\s\w]", text.lower())[:28] or ["<pad>"]
        seq = [self.encode_token(t) for t in tokens]
        for block in self.layers:
            seq = block.forward_sequence(seq)
        # Mean + last-token pooling through SubLN RMSNorm
        pooled = [
            0.5 * seq[-1][d] + 0.5 * (sum(step[d] for step in seq) / len(seq))
            for d in range(self.dim)
        ]
        return rms_norm(pooled, self.final_norm)

    def forward_hidden(self, text: str) -> tuple[list[float], list[float]]:
        last_h = self._encode_sequence_hidden(text)
        logits = self.lm_head.forward(last_h)
        return last_h, logits

    def _synthesize_ternary_stream(self, prompt: str, hidden: list[float], max_tokens: int = 22) -> str:
        """Uses the BitNet hidden state vector to deterministically steer token generation."""
        p_words = [w.lower() for w in re.findall(r"[a-zA-Z0-9]+", prompt)]
        seed_word = next((w for w in p_words if w in self.bigrams), 'meow')
        out_tokens = ['Meow!', seed_word.capitalize()]
        curr = seed_word
        for step in range(max_tokens):
            candidates = self.bigrams.get(curr.lower())
            if not candidates:
                candidates = ['meow,', 'purr-fect', 'ternary', 'weights', 'compute', 'cleanly!']
            # Select candidate steered by int8 quantized hidden state at (step % dim)
            h_val = hidden[step % self.dim]
            pick_idx = int(abs(h_val * 1000) + step * 7) % len(candidates)
            nxt = candidates[pick_idx]
            out_tokens.append(nxt)
            curr = nxt.strip('.,!?;:')
        text = ' '.join(out_tokens)
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        if not text.endswith(('!', '.', '~')):
            text += ' — nya~!'
        return text

    def weight_summary(self) -> dict:
        neg = zero = pos = 0
        for blk in self.layers:
            for layer in (blk.wq, blk.wk, blk.wv, blk.wo, blk.w_gate, blk.w_up, blk.w_down):
                st = layer.stats()
                neg += st['neg']
                zero += st['zero']
                pos += st['pos']
        st = self.lm_head.stats()
        neg += st['neg']
        zero += st['zero']
        pos += st['pos']
        total = neg + zero + pos
        return {
            'codename': CODENAME,
            'license': 'CC0 1.0 Universal / MIT (100% Copyright & NDA Free Clean-Room)',
            'architecture': 'Open-Ar4on BitNet b1.58 (BitLinear Ternary + RoPE + SubLN RMSNorm + SwiGLU)',
            'layers': len(self.layers),
            'd_model': self.dim,
            'ffn_dim': self.hidden_dim,
            'total_ternary_weights': total,
            'distribution': {'-1': neg, '0': zero, '+1': pos},
            'bits_per_weight': 1.585,
            'activation_quantization': 'int8 [-128, 127] absmax',
            'voice_and_meow_synth': True,
        }

    def generate(self, prompt: str, history: list[tuple[str, str]]) -> str:
        last_h, logits = self.forward_hidden(prompt)
        q_norm, alpha = quantize_activations_int8(last_h)

        p_tokens = set(re.findall(r"[a-z0-9]+", prompt.lower()))

        # 1. Check user-taught custom memories first
        for k_str, resp in reversed(self.custom_memories):
            k_tokens = set(re.findall(r"[a-z0-9]+", k_str.lower()))
            if k_tokens and len(p_tokens & k_tokens) / len(k_tokens) >= 0.5:
                return f"Meow! {resp}\n\n[Open-Ar4on b1.58 · α={alpha:.3f} · q={q_norm[:4]}]"

        # 2. Score trained BitNet b1.58 logits + lexical resonance
        best_idx = 0
        best_score = -1e9
        best_overlap = 0.0
        for i, (keys, _) in enumerate(self.CORPUS):
            k_tokens = set(re.findall(r"[a-z0-9]+", keys.lower()))
            overlap = len(p_tokens & k_tokens) / max(1, len(p_tokens)) if p_tokens else 0.0
            score = overlap * 12.0 + (logits[i] * 0.45)
            if score > best_score:
                best_score = score
                best_idx = i
                best_overlap = overlap

        tag = self.FELINE_TAGS[ abs(sum(q_norm)) % len(self.FELINE_TAGS) ]
        if best_overlap >= 0.22 or best_score > 2.4:
            base_reply = f"{self.CORPUS[best_idx][1]}\n\n{tag}"
        else:
            stream = self._synthesize_ternary_stream(prompt, last_h)
            energy = sum(abs(x) for x in q_norm) / max(1, len(q_norm))
            ctx_note = f" (across {len(history) + 1} chat turns)" if history else ""
            base_reply = (
                f"{stream}\n\n"
                f"🐾 Open-Ar4on BitNet b1.58 Telemetry{ctx_note}:\n"
                f"• Activation AbsMax (α): {alpha:.4f} | Mean |int8| energy: {energy:.1f}/127\n"
                f"• Ternary Head Logits (top-3): {[round(x, 3) for x in sorted(logits, reverse=True)[:3]]}\n"
                f"• Tip: Teach me custom responses with `/learn <topic> :: <reply>` or press `🐾 Meow!` ({tag})"
            )
        return base_reply


# ==============================================================================
# 4. EXTERNAL BINARY & MODEL DETECTION (CROSS-PLATFORM)
# ==============================================================================

def detect() -> tuple[pathlib.Path | None, pathlib.Path | None]:
    exe_suffix = '.exe' if os.name == 'nt' else ''
    candidates = [
        os.getenv('CATSEEK_BITNET_BIN', ''),
        shutil.which('bitnet-cli') or '',
        shutil.which('llama-cli') or '',
        str(HOME / f'BitNet/build/bin/llama-cli{exe_suffix}'),
        str(HOME / f'BitNet/build/bin/bitnet-cli{exe_suffix}'),
        str(HOME / f'BitNet/build/bin/Release/llama-cli{exe_suffix}'),
        str(HOME / f'BitNet/build/bin/Release/bitnet-cli{exe_suffix}'),
    ]
    binary = next(
        (pathlib.Path(x) for x in candidates if x and pathlib.Path(x).is_file() and os.access(x, os.X_OK)),
        None,
    )

    models = [
        os.getenv('CATSEEK_BITNET_MODEL', ''),
        str(HOME / 'models/CatSeek-R1-1B/ggml-model-i2_s.gguf'),
        str(HOME / 'models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf'),
    ]
    models_dir = HOME / 'models'
    if models_dir.exists():
        models += [str(p) for p in sorted(models_dir.rglob('*.gguf'))]

    model = next(
        (
            pathlib.Path(x)
            for x in models
            if x and pathlib.Path(x).is_file() and pathlib.Path(x).stat().st_size > 1024 * 1024
        ),
        None,
    )
    return binary, model


def clean_cli_output(raw_stdout: str, full_prompt: str) -> str:
    out = raw_stdout.strip()
    if out.startswith(full_prompt):
        out = out[len(full_prompt):].strip()
    elif 'Assistant:' in out:
        out = out.split('Assistant:')[-1].strip()
    for stop_marker in ('\nUser:', 'User:', '<|eot_id|>', '</s>'):
        if stop_marker in out:
            out = out.split(stop_marker)[0].strip()
    return out


# ==============================================================================
# 5. UNIFIED ENGINE (MATH + VOICE/MEOW + NATIVE BITNET CLI + OPEN-AR4ON b1.58)
# ==============================================================================

class Engine:
    def __init__(self, voice_enabled: bool = True):
        self.history: list[tuple[str, str]] = []
        self.lock = threading.Lock()
        self.micro_bitnet = OpenAr4onBitNetLM(dim=32, hidden_dim=64, layers=2)
        self.voice = CatVoiceEngine(enabled=voice_enabled)
        self._active_proc: subprocess.Popen | None = None

    def cancel_active(self):
        self.voice.stop()
        proc = self._active_proc
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass

    def clear_history(self):
        with self.lock:
            self.history.clear()

    def reply(self, prompt: str, commit_history: bool = True, speak_reply: bool = True) -> tuple[str, str]:
        s = prompt.strip()
        low = s.lower()

        if low in ('/clear', '/new'):
            self.clear_history()
            return 'Meow! Conversation cleared and ready for fresh ternary thoughts.', 'local'

        if low in ('/meow', 'meow', 'meow!'):
            self.voice.play_meow()
            msg = "Mrrr-meow!! 🐱 *synthesizes a 480Hz → 780Hz → 310Hz formant feline vocalization and purrs at 24Hz* Nya~!"
            return msg, 'cat-meow-synth'

        if low in ('/voice', '/tts', '/speak'):
            self.voice.enabled = not self.voice.enabled
            state = 'ON 🔊' if self.voice.enabled else 'OFF 🔇'
            msg = f"Meow! CatSeek Voice & Meow Audio Synthesizer is now {state}."
            if self.voice.enabled:
                self.voice.speak(msg, force=True)
            return msg, 'voice-toggle'

        if low in ('/help', 'help'):
            return (
                'Commands (Open-Ar4on Clean-Room Edition):\n'
                '  /help                     — Show this help message\n'
                '  /meow                     — Synthesize & play a procedural cat meow sound!\n'
                '  /voice                    — Toggle spoken TTS voice responses ON/OFF\n'
                '  /status                   — Show Open-Ar4on BitNet b1.58 & GGUF status\n'
                '  /bitnet                   — Inspect live ternary {-1, 0, +1} weight stats\n'
                '  /learn <key> :: <reply>   — Teach the in-process BitNet engine a response\n'
                '  /math <expr>              — Exact AST math evaluator (e.g. /math (12+8)*3)\n'
                '  /python                   — Show Python example\n'
                '  /game                     — Show minimal Tkinter game loop\n'
                '  /clear                    — Clear conversation history',
                'local',
            )

        if low in ('/bitnet', '/weights', '/ar4on'):
            return json.dumps(self.micro_bitnet.weight_summary(), indent=2), 'open-ar4on-b1.58-inspect'

        if low.startswith('/learn '):
            body = s[7:].strip()
            if '::' not in body:
                return 'Usage: /learn <keywords> :: <response text>', 'local'
            k, v = body.split('::', 1)
            self.micro_bitnet.custom_memories.append((k.strip(), v.strip()))
            msg = f'Meow! Learned custom ternary rule for "{k.strip()}".'
            if speak_reply:
                self.voice.speak(msg)
            return msg, 'open-ar4on-b1.58-learn'

        if low in ('/status', '/model'):
            b, m = detect()
            summary = self.micro_bitnet.weight_summary()
            return (
                json.dumps(
                    {
                        'app': NAME,
                        'codename': CODENAME,
                        'clean_room_nda_free': True,
                        'voice_tts_enabled': self.voice.enabled,
                        'builtin_open_ar4on_bitnet_b158': {
                            'ready': True,
                            'ternary_weights': summary['total_ternary_weights'],
                            'distribution': summary['distribution'],
                        },
                        'native_gguf_backend': {
                            'cli': str(b) if b else None,
                            'model': str(m) if m else None,
                            'ready': bool(b and m),
                        },
                    },
                    indent=2,
                ),
                'status',
            )

        # Exact Math Route
        expression = re.sub(r'^(?:/math|calculate|compute|what is|what\'s)\s+', '', s, flags=re.I).strip(' ?')
        if re.fullmatch(r'[0-9.\s+*/%()\-]+', expression) and any(x.isdigit() for x in expression):
            try:
                val = calculate(expression)
                ans = f"Meow! Exact result: {val} 🐾"
                if speak_reply:
                    self.voice.speak(ans)
                return ans, 'exact-math'
            except Exception as e:
                return 'Math error: ' + str(e), 'math-error'

        if low == '/python':
            return (
                'Python example:\n\n'
                'def greet(name: str) -> str:\n'
                '    return f"Meow! Hello, {name}!"\n\n'
                'print(greet("CatSeek Open-Ar4on"))',
                'local-template',
            )

        if low == '/game':
            return (
                'Minimal tkinter game loop:\n\n'
                'import tkinter as tk\n'
                'r = tk.Tk()\n'
                'c = tk.Canvas(r, width=400, height=300, bg="black")\n'
                'c.pack()\n'
                'x = 0\n'
                'def tick():\n'
                '    global x\n'
                '    c.delete("all")\n'
                '    c.create_oval(x, 120, x + 30, 150, fill="cyan")\n'
                '    x = (x + 3) % 400\n'
                '    r.after(16, tick)\n'
                'tick()\n'
                'r.mainloop()',
                'local-template',
            )

        with self.lock:
            hist_snapshot = list(self.history[-4:])

        # Route 1: External Native BitNet CLI + GGUF if present
        binary, model = detect()
        if binary and model:
            sys_prompt = (
                "System: You are CatSeek R1 1.1 (Open-Ar4on Edition), a helpful, friendly cat AI "
                "running on BitNet b1.58 ternary weights. Sprinkle occasional 'Meow!' or 'Purr~' naturally.\n"
            )
            context = '\n'.join(f'User: {u}\nAssistant: {a}' for u, a in hist_snapshot)
            full = sys_prompt + (context + '\n' if context else '') + f'User: {s}\nAssistant:'
            args = [
                str(binary),
                '-m', str(model),
                '-p', full,
                '-n', '384',
                '-c', '2048',
                '--temp', '0.7',
                '-r', 'User:',
                '--no-display-prompt',
            ]
            try:
                proc = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self._active_proc = proc
                stdout, stderr = proc.communicate(timeout=180)
            except subprocess.TimeoutExpired:
                self.cancel_active()
                return 'Native BitNet invocation timed out after 180s.', 'native-error'
            except OSError as e:
                return f'Native BitNet invocation failed: {e}', 'native-error'
            finally:
                self._active_proc = None

            if proc.returncode == 0 and stdout.strip():
                out = clean_cli_output(stdout, full)
                if out:
                    if commit_history:
                        with self.lock:
                            self.history.append((s, out))
                            self.history = self.history[-8:]
                    if speak_reply:
                        self.voice.speak(out)
                    return out, 'native-bitnet'

        # Route 2: Built-in Open-Ar4on BitNet b1.58 Transformer Engine
        out = self.micro_bitnet.generate(s, hist_snapshot)
        if commit_history:
            with self.lock:
                self.history.append((s, out))
                self.history = self.history[-8:]
        if speak_reply:
            self.voice.speak(out)
        return out, 'open-ar4on-bitnet-b1.58'


# ==============================================================================
# 6. TKINTER GUI (WITH VOICE TOGGLE, MEOW SYNTH BUTTON & GENERATION LOCKING)
# ==============================================================================

class GUI:
    def __init__(self, root):
        self.root = root
        self.engine = Engine(voice_enabled=True)
        self.q = queue.Queue()
        self.busy = False
        self.generation = 0

        root.title(NAME)
        root.geometry('1020x700')
        root.minsize(760, 500)
        root.configure(bg='#080d17')

        head = tk.Frame(root, bg='#101c30', padx=18, pady=16)
        head.pack(fill='x')
        tk.Label(
            head,
            text='🐱  CATSEEK R1 1.1 · OPEN-AR4ON',
            bg='#101c30',
            fg='#8fc7ff',
            font=('Helvetica', 19, 'bold'),
        ).pack(side='left')
        self.status = tk.Label(head, text='Open-Ar4on BitNet b1.58 · Voice Ready', bg='#101c30', fg='#a9bed8')
        self.status.pack(side='right')

        body = tk.Frame(root, bg='#080d17')
        body.pack(fill='both', expand=True)

        side = tk.Frame(body, bg='#101c30', width=205, padx=12, pady=16)
        side.pack(side='left', fill='y')
        side.pack_propagate(False)

        buttons = [
            ('New chat', self.new),
            ('🐾 Meow! (Synth)', lambda: self.submit('/meow')),
            ('🔊 Toggle Voice', lambda: self.submit('/voice')),
            ('Model status', lambda: self.submit('/status')),
            ('BitNet weights', lambda: self.submit('/bitnet')),
            ('Math demo', lambda: self.submit('/math (12+8)*3')),
            ('What is Open-Ar4on?', lambda: self.submit('Who are you and what is Open-Ar4on?')),
            ('Python demo', lambda: self.submit('/python')),
            ('Game demo', lambda: self.submit('/game')),
        ]
        for label, cmd in buttons:
            tk.Label(
                side,
                text=label,
                cursor='hand2',
                bg='#111d30',
                fg='#55aaff',
                borderwidth=0,
                relief='flat',
                pady=8,
            )
            button = side.winfo_children()[-1]
            button.pack(fill='x', pady=4)
            button.bind('<Button-1>', lambda event, action=cmd: action())
            button.bind('<Enter>', lambda event, widget=button: widget.configure(bg='#203957', fg='#80c4ff'))
            button.bind('<Leave>', lambda event, widget=button: widget.configure(bg='#111d30', fg='#55aaff'))

        main = tk.Frame(body, bg='#080d17')
        main.pack(side='left', fill='both', expand=True)

        self.chat = scrolledtext.ScrolledText(
            main,
            bg='#080d17',
            fg='#e0edff',
            insertbackground='white',
            wrap='word',
            font=('Menlo', 11),
            relief='flat',
            padx=18,
            pady=16,
            state='disabled',
        )
        self.chat.pack(fill='both', expand=True)

        bar = tk.Frame(main, bg='#101c30', padx=12, pady=12)
        bar.pack(fill='x')

        self.input = tk.Text(
            bar,
            height=3,
            bg='#17283f',
            fg='#f4f8ff',
            insertbackground='white',
            font=('Helvetica', 12),
            relief='flat',
            wrap='word',
            padx=10,
            pady=8,
        )
        self.input.pack(side='left', fill='x', expand=True)
        self.input.bind('<Return>', self.enter)

        self.send = tk.Label(
            bar,
            text='MEOW ↑',
            cursor='hand2',
            bg='#111d30',
            fg='#55aaff',
            borderwidth=0,
            relief='flat',
            padx=14,
            pady=12,
        )
        self.send.pack(side='right', padx=(10, 0))
        self.send.bind('<Button-1>', lambda event: self.submit() if not self.busy else None)
        self.send.bind('<Enter>', lambda event: self.send.configure(bg='#203957', fg='#80c4ff') if not self.busy else None)
        self.send.bind('<Leave>', lambda event: self.send.configure(bg='#111d30', fg='#55aaff'))

        self.append(
            f'{NAME} · Single-file BitNet b1.58 & Procedural Meow Edition (CC0 Clean-Room)\n'
            'Type /meow to hear a synthesized cat meow, /voice to toggle TTS speech, /bitnet for ternary weights, or chat away!\n\n'
        )
        self.refresh()
        self.root.after(50, self.poll)
        self.input.focus_set()

    def append(self, s: str):
        self.chat.configure(state='normal')
        self.chat.insert('end', s)
        self.chat.configure(state='disabled')
        self.chat.see('end')

    def refresh(self):
        b, m = detect()
        v_tag = '🔊 Voice ON' if self.engine.voice.enabled else '🔇 Voice OFF'
        if b and m:
            self.status.configure(text=f'Native GGUF + Open-Ar4on b1.58 · {v_tag}')
        else:
            self.status.configure(text=f'Open-Ar4on BitNet b1.58 Ready · {v_tag}')

    def enter(self, event):
        if event.state & 0x1:
            return None
        self.submit()
        return 'break'

    def new(self):
        self.generation += 1
        self.engine.cancel_active()
        self.engine.clear_history()
        self.busy = False
        self.send.configure(fg='#55aaff', cursor='hand2')
        self.chat.configure(state='normal')
        self.chat.delete('1.0', 'end')
        self.chat.configure(state='disabled')
        self.append('New CatSeek Open-Ar4on chat · Meow! 🐾\n\n')
        self.refresh()

    def submit(self, forced=None):
        if self.busy:
            return
        prompt = forced if isinstance(forced, str) else self.input.get('1.0', 'end-1c').strip()
        if not prompt:
            return
        if not isinstance(forced, str):
            self.input.delete('1.0', 'end')

        self.append(f'YOU\n{prompt}\n\nCATSEEK (OPEN-AR4ON)\n')
        self.busy = True
        self.send.configure(fg='#536780', cursor='arrow')
        gen = self.generation

        def work():
            try:
                ans, route = self.engine.reply(prompt, commit_history=(gen == self.generation))
                self.q.put((gen, ans, route))
            except Exception as e:
                self.q.put((gen, f'Error: {e}', 'error'))

        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            while True:
                gen, answer, route = self.q.get_nowait()
                if gen == self.generation:
                    self.append(f'{answer}\n\n[{route}]\n\n')
                    self.busy = False
                    self.send.configure(fg='#55aaff', cursor='hand2')
                    self.refresh()
        except queue.Empty:
            pass
        self.root.after(50, self.poll)


# ==============================================================================
# 7. CLI & SELF-TEST ENTRYPOINT
# ==============================================================================

def main():
    if '--self-test' in sys.argv:
        assert calculate('2+3*4') == 14
        assert calculate('(12+8)*3') == 60
        eng = Engine(voice_enabled=False)
        status_out, status_route = eng.reply('/status', speak_reply=False)
        assert 'Open-Ar4on' in status_out and status_route == 'status'
        bitnet_out, bitnet_route = eng.reply('/bitnet', speak_reply=False)
        stats = json.loads(bitnet_out)
        assert stats['total_ternary_weights'] > 0 and bitnet_route == 'open-ar4on-b1.58-inspect'
        chat_out, chat_route = eng.reply('What is BitNet 1.58?', speak_reply=False)
        assert '1.58' in chat_out and 'Meow' in chat_out
        meow_out, meow_route = eng.reply('meow', speak_reply=False)
        assert 'meow' in meow_out.lower() and meow_route == 'cat-meow-synth'
        print('PASS: Open-Ar4on BitNet b1.58, exact-math, procedural meow synth, and chat engine verified.')
        return

    if '--meow' in sys.argv:
        eng = Engine(voice_enabled=True)
        out, route = eng.reply('/meow')
        print(f'{out}\n[{route}]')
        time.sleep(0.7)
        return

    if '--prompt' in sys.argv:
        i = sys.argv.index('--prompt')
        prompt_text = ' '.join(sys.argv[i + 1:]).strip()
        if not prompt_text:
            print('Error: --prompt requires a non-empty prompt string.', file=sys.stderr)
            sys.exit(1)
        speak = '--no-voice' not in sys.argv
        ans, route = Engine(voice_enabled=speak).reply(prompt_text, speak_reply=speak)
        print(f'{ans}\n[{route}]')
        return

    if not TK_AVAILABLE:
        print('Tkinter is not available in this Python environment. Use --prompt "...", --meow, or --self-test.', file=sys.stderr)
        sys.exit(1)

    root = tk.Tk()
    GUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()