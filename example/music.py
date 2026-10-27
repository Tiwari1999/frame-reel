"""Score for the 6 s example: the kit's four-on-the-floor groove at 120 BPM, a bell on the scene cut. `music.py OUT.wav`"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from synth import Score, groove, bell

# (start, end, bass root, voicing) as MIDI notes: Am, F, G
CHORDS = [(0, 2, 45, [57, 60, 64]), (2, 4, 41, [53, 57, 60]), (4, 6.1, 43, [55, 59, 62])]
sc = Score(6.0)
groove(sc, CHORDS, 0, 6.0)
sc.pluck.add(3.0, bell(81), 0.5)
sc.mix(sys.argv[1], ref=(0, 6), fade_from=5.4)
