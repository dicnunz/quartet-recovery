"""Secondary reference-assisted measure alignment; not the strict benchmark score."""
from collections import Counter
from pathlib import Path
import hashlib
import json
from events import extract

ROOT = Path(__file__).resolve().parents[1]
GAP_COST = 0.6


def align_measures(predicted, reference):
    """Global sequence alignment using only pitch multiplicities for each measure.

    Substitution cost is one minus multiset Dice similarity. Empty/empty measures
    have zero cost. Gaps cost 0.6 each. Ties prefer diagonal, then deletion, then
    insertion. Neither onset nor duration is used to choose the alignment.
    """
    n, m = len(predicted), len(reference)
    costs = [[0.0] * (m + 1) for _ in range(n + 1)]
    moves = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        costs[i][0], moves[i][0] = i * GAP_COST, 1
    for j in range(1, m + 1):
        costs[0][j], moves[0][j] = j * GAP_COST, 2
    for i, a in enumerate(predicted, 1):
        for j, b in enumerate(reference, 1):
            size = sum(a.values()) + sum(b.values())
            similarity = 2 * sum((a & b).values()) / size if size else 1.0
            options = (costs[i - 1][j - 1] + 1 - similarity,
                       costs[i - 1][j] + GAP_COST,
                       costs[i][j - 1] + GAP_COST)
            move = min(range(3), key=lambda k: (round(options[k], 12), k))
            costs[i][j], moves[i][j] = options[move], move
    path = []
    i, j = n, m
    while i or j:
        move = moves[i][j]
        if move == 0:
            path.append((i - 1, j - 1)); i -= 1; j -= 1
        elif move == 1:
            path.append((i - 1, None)); i -= 1
        else:
            path.append((None, j - 1)); j -= 1
    return list(reversed(path)), costs[n][m]


def score(matches, predicted, reference):
    precision = matches / predicted if predicted else 0
    recall = matches / reference if reference else 0
    return {'matches': matches, 'predicted': predicted, 'reference': reference,
            'precision': precision, 'recall': recall,
            'f1': 2 * matches / (predicted + reference) if predicted + reference else 0}


def diagnostic(prediction, reference):
    assert len(prediction['parts']) == len(reference['parts']) == 4
    paths, total_matches = [], {'pitch_onset': 0, 'pitch_onset_duration': 0}
    for part in range(4):
        grouped = []
        for data in [prediction, reference]:
            measures = [[] for _ in data['parts'][part]['measures']]
            for event in data['events']:
                if event['part'] == part:
                    measures[event['measure']].append(event)
            grouped.append(measures)
        left, right = grouped
        path, cost = align_measures([Counter(e['midi'] for e in notes) for notes in left],
                                    [Counter(e['midi'] for e in notes) for notes in right])
        for a, b in path:
            if a is None or b is None:
                continue
            for label, fields in [('pitch_onset', ['onset', 'midi']),
                                  ('pitch_onset_duration', ['onset', 'midi', 'duration'])]:
                pa = Counter(tuple(e[k] for k in fields) for e in left[a])
                pb = Counter(tuple(e[k] for k in fields) for e in right[b])
                total_matches[label] += sum((pa & pb).values())
        paths.append({'part': part, 'alignment_cost': cost,
                      'paired_measures': sum(a is not None and b is not None for a, b in path),
                      'unpaired_predicted_measures': sum(b is None for a, b in path),
                      'unpaired_reference_measures': sum(a is None for a, b in path),
                      'measure_index_pairs': path})
    out = {label: score(matches, len(prediction['events']), len(reference['events']))
           for label, matches in total_matches.items()}
    out.update({'primary_result': 'metrics.json remains the strict measure-index comparison',
                'method': 'Reference-assisted global measure alignment independently within each staff-order part. '
                          'Measure pitch multisets only determine pairing; substitution cost = 1 - multiset Dice similarity; '
                          'gap cost = 0.6. No transposition or within-measure time warping. Ties prefer diagonal, deletion, insertion. '
                          'All notes, including notes in unpaired measures, remain in precision/recall denominators. '
                          'Not benchmark-equivalent: repeated/similar measures may be paired incorrectly and reference content helps choose alignment.',
                'gap_cost': GAP_COST, 'parts': paths})
    return out


def main():
    frozen = json.loads((ROOT / 'results/freeze.json').read_text())
    assert hashlib.sha256((ROOT / 'scripts/events.py').read_bytes()).hexdigest() == frozen['event_extractor_sha256']
    for name, digest in frozen['files'].items():
        assert hashlib.sha256((ROOT / 'results' / name).read_bytes()).hexdigest() == digest
    prediction = json.loads((ROOT / 'results/prediction-events.json').read_text())
    reference_path = ROOT / 'data/reference.musicxml'
    reference = extract(reference_path)
    out = diagnostic(prediction, reference)
    out['reference_sha256'] = hashlib.sha256(reference_path.read_bytes()).hexdigest()
    (ROOT / 'results/aligned-diagnostic.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k != 'parts'}, indent=2))
    print('Gaps by part:', [(p['unpaired_predicted_measures'], p['unpaired_reference_measures']) for p in out['parts']])


if __name__ == '__main__':
    main()
