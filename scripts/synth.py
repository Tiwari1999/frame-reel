"""Synth kit for reel soundtracks: numpy instruments on one beat grid, five buses, a simple mix.
A reel script builds a Score(dur), adds parts with the instruments here, then calls mix(path)."""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR, BPM = 48000, 120
BEAT = 60 / BPM
rng = np.random.default_rng(7)


def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def tt(n): return np.arange(n) / SR
def lp(x, f, o=2): return sosfilt(butter(o, f, "lowpass", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "highpass", fs=SR, output="sos"), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def kick(level=1.0):
    n = int(0.42 * SR); t = tt(n)
    ph = 2 * np.pi * np.cumsum(46 + 104 * np.exp(-t / 0.035)) / SR
    return (np.sin(ph) * np.exp(-t / 0.16) + lp(rng.standard_normal(n), 3500) * np.exp(-t / 0.004) * 0.25) * level


def clap():
    n = int(0.35 * SR); t = tt(n); env = np.zeros(n)
    for d in (0.0, 0.011, 0.022):
        k = t - d
        env += np.where(k >= 0, np.exp(-np.clip(k, 0, None) / (0.008 if d < 0.02 else 0.09)), 0)
    return bp(rng.standard_normal(n), 900, 4200) * env * 0.55


def hat(open_=False):
    n = int((0.2 if open_ else 0.06) * SR); t = tt(n)
    return hp(rng.standard_normal(n), 7500) * np.exp(-t / (0.06 if open_ else 0.014)) * 0.35


def saw(f, n, harm=14, detune=0.0):
    t = tt(n); s = np.zeros(n)
    for k in range(1, harm + 1):
        if f * k > SR / 2.2: break
        s += np.sin(2 * np.pi * f * k * (1 + detune) * t) / k
    return s


def bass_note(m, dur, dec=0.22):
    n = int(dur * SR); t = tt(n)
    s = saw(hz(m), n, 10) * 0.6 + np.sin(2 * np.pi * hz(m) * t)
    return lp(s * np.minimum(1, t / 0.004) * np.exp(-t / dec) * np.clip((dur - t) / 0.02, 0, 1), 520) * 0.9


def pad_chord(notes, dur, bright=1.0):
    n = int((dur + 0.6) * SR); t = tt(n); s = np.zeros(n)
    for m in notes:
        for d in (-0.004, 0.0, 0.0045):
            s += saw(hz(m), n, 9, d) / 3
    env = np.minimum(1, t / 0.28) * np.clip((dur + 0.6 - t) / 0.6, 0, 1)
    return lp(s * env, 900 + 1500 * bright) * 0.16


def pluck_note(m, bright=1.0, dec=0.32):
    n = int(0.9 * SR); t = tt(n); f = hz(m); s = np.zeros(n)
    for k in range(1, 9):
        if f * k > SR / 2.2: break
        s += np.sin(2 * np.pi * f * k * t) * (bright ** (k - 1)) / k ** 1.2 * np.exp(-t * k / dec / 2.2)
    return s * np.minimum(1, t / 0.002) * np.exp(-t / dec)


def bell(m, dec=0.7):
    n = int((dec * 3) * SR); t = tt(n); f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / (dec / 3)) \
        + 0.15 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / (dec / 6))
    return s * np.minimum(1, t / 0.002) * np.exp(-t / dec)


def tick(m, level=1.0):
    n = int(0.12 * SR); t = tt(n)
    tone = (np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(4 * np.pi * hz(m) * t)) * np.exp(-t / 0.035)
    noise = bp(rng.standard_normal(n), 1500, 4000) * np.exp(-t / 0.004) * 0.18
    return (tone + noise) * np.minimum(1, t / 0.003) * level


def key_tick():
    n = int(0.05 * SR); t = tt(n)
    return bp(rng.standard_normal(n), 1200, 5000) * np.exp(-t / 0.006) * 0.8


def swish(dur=0.28, up=True):
    n = int(dur * SR); t = tt(n); x = rng.standard_normal(n); out = np.zeros(n); seg = n // 8
    for i in range(8):
        a = i * seg; b = min(n, a + seg + 256)
        lo = 600 * (2 ** ((i if up else 7 - i) * 0.55))
        out[a:b] += bp(x[a:b], lo, min(lo * 3, 16000)) * np.hanning(b - a)
    return out * np.sin(np.pi * t / dur) ** 2 * 0.5


def sub_hit(m=36, dur=0.8):
    t = tt(int(dur * SR)); return np.sin(2 * np.pi * hz(m) * t) * np.exp(-t / 0.25)


class Bus:
    def __init__(self, n): self.x = np.zeros((2, n + SR * 3))

    def add(self, t0, sig, gain=1.0, pan=0.0):
        i = int(round(t0 * SR)); sig = np.asarray(sig) * gain
        n = min(len(sig), self.x.shape[1] - i)
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.x[0, i:i + n] += sig[:n] * l * np.sqrt(2)
        self.x[1, i:i + n] += sig[:n] * r * np.sqrt(2)


class Score:
    def __init__(self, dur):
        self.dur, self.N = dur, int(SR * dur)
        self.drums, self.bass, self.pad, self.pluck, self.sfx = (Bus(self.N) for _ in range(5))
        self.kicks = []

    def kick_at(self, t, level=1.0, duck=True):
        self.drums.add(t, kick(level))
        if duck: self.kicks.append(t)

    def mix(self, path, ref=(8.0, 16.0), fade_from=None):
        N = self.N
        def room(x, secs=1.6):
            n = int(secs * SR); t = tt(n)
            ir = np.stack([lp(rng.standard_normal(n), 5000) * np.exp(-t / 0.42) for _ in range(2)])
            ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
            return np.stack([fftconvolve(x[c], ir[c])[: x.shape[1]] for c in range(2)])
        target = {"drums": -16.0, "bass": -20.0, "pad": -21.0, "pluck": -22.0, "sfx": -33.0}
        def level(b):
            seg = b.x[:, int(ref[0] * SR):int(ref[1] * SR)].mean(axis=0)
            return 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-12)
        for name in target:
            b = getattr(self, name); g = 10 ** ((target[name] - level(b)) / 20); b.x *= g
            print(f"  {name:6} gain {20 * np.log10(g):+5.1f} dB")
        duck = np.ones(N + SR * 3)
        for k in self.kicks:
            i = int(k * SR); n = int(0.3 * SR); t = tt(n)
            duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.55 * np.exp(-t / 0.09))
        self.bass.x *= duck; self.pad.x *= 0.55 + 0.45 * duck; self.pluck.x *= 0.7 + 0.3 * duck
        wet = room(self.pluck.x * 0.7 + self.pad.x * 0.3 + self.sfx.x * 0.6) * 0.5
        mix = self.drums.x + self.bass.x + self.pad.x + self.pluck.x + self.sfx.x + wet
        mix = hp(mix, 30)[:, :N]
        mix = mix + 1.6 * bp(mix, 2000, 7000)
        fs = int((fade_from or self.dur - 0.8) * SR); fade = np.ones(N)
        fade[fs:] = np.cos(np.linspace(0, np.pi / 2, N - fs)) ** 2
        mix *= fade
        mix = np.tanh(mix / np.abs(mix).max() * 1.1) / np.tanh(1.1) * 0.89
        wavfile.write(path, SR, (mix.T * 32767).astype(np.int16))
        print("wrote", path, f"{N / SR:.2f}s")


def groove(sc, chords, a, b, hats=True, claps=True, bass=True, pluck_gain=0.2, pat=(0, 1, 2, 3, 2, 1, 2, 1)):
    """Four on the floor from a to b, with ducked eighth bass and a pluck arpeggio over chord_at."""
    def chord_at(t):
        for c in chords:
            if c[0] <= t < c[1]: return c
        return chords[-1]
    for i in range(int(round((b - a) / BEAT))):
        sc.kick_at(a + i * BEAT)
    for x in np.arange(a, b, 2.0):
        if claps:
            for off in (0.5, 1.5):
                if x + off < b: sc.drums.add(x + off, clap(), 0.55, 0.05)
    if hats:
        for e in np.arange(a, b, 0.25):
            if abs((e / 0.5) - round(e / 0.5)) > 1e-6: sc.drums.add(e, hat(), 0.95, 0.25)
    if bass:
        for e in np.arange(a, b, 0.25):
            root = chord_at(e)[2]
            sc.bass.add(e, bass_note(root + (12 if int(round(e / 0.25)) % 4 == 3 else 0), 0.22), 0.85)
    for i, e in enumerate(np.arange(a, b, 0.25)):
        v = chord_at(e)[3]; tones = [v[0] + 12, v[1] + 12, v[2] + 12, v[0] + 24]
        sc.pluck.add(e, pluck_note(tones[pat[i % 8]], bright=0.82), pluck_gain, pan=(-0.35 if i % 2 else 0.35))
    return chord_at
