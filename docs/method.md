# Reproduction

Linux x86-64 needs Python 3, Java with compiler modules, GCC, `dpkg-deb`, Poppler and FFmpeg. Audiveris bundles its Java runtime; allow 8 GB RAM. Downloads are checked against [sources.json](../data/sources.json). Verification requires the original git history to inspect the freeze commit. Clone this repository with Git to preserve the history required by verification. 

```sh
python -m pip install -r requirements.txt
python scripts/fetch.py
python scripts/prepare.py
python scripts/notation_audio.py
python scripts/video.py
python scripts/verify.py
```

To repeat pixel recognition, run `python scripts/transcribe.py`. Outputs go to `results/final-omr/`; frozen predictions stay unchanged. For a new blind experiment, use a separate checkout without existing prediction/reference artifacts, transcribe, run `scripts/freeze.py`, commit the prediction, then fetch the reference with `scripts/fetch.py --reference`. The supplied repository already includes the revealed reference and cannot itself constitute a new blind test.

```sh
python scripts/engrave.py
python scripts/evaluate.py
python scripts/aligned_diagnostic.py
python -m unittest discover -s tests
```

Verification independently reconstructs the playback timeline and valid ties from frozen events using rational time, compares every MIDI note and program assignment, and re-synthesizes the complete waveform. The MP3 and the film’s delayed audio excerpt must correlate with that waveform. It also recomputes both evaluation results and decodes the full video.

The `.omr` project, MusicXML, MIDI, 72 engraved pages, MP3 and evaluation files are in `results/`.

## Interpretation

Playback uses only the frozen prediction. Common printed measure labels, including duplicate occurrences, share one timeline; missing staff measures become rests. Strings are assigned by staff order. The renderer sustains 150 valid adjacent tie continuations. Malformed ties remain separate attacks. It uses a chosen tempo of 168 quarter notes per minute, written durations and recognized dynamics. It does not expand repeats. No tremolos were recognized, so none are invented. Zero-duration grace notes are omitted. This is a complete traversal of the recovered notation, not a complete interpretation of every performance instruction.

Audiveris 5.11.0 failed to reload swapped sheets during export. A one-line CLI patch keeps sheets in memory; it does not change recognition. Verovio engraved the score but crashed exporting MIDI on malformed ties, so the independent event renderer produces both MIDI and audio. The score still needs human correction before rehearsal.

Original code is MIT. Scan, annotation, Audiveris, engraver and soundfont retain their own terms; see [provenance](../PROVENANCE.md) and `licenses/`.
