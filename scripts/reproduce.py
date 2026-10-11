"""Reproduce summaries, agreement and baseline evaluation using Python's stdlib."""
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHODS = ['flesch_reading_ease', 'flesch_kincaid_grade', 'smog_index',
           'dale_chall_grade', 'gunning_fog', 'automated_readability_index']


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def ranks(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        for i in order[start:end]:
            result[i] = (start + 1 + end) / 2
        start = end
    return result


def spearman(left, right):
    pairs = [(a, b) for a, b in zip(left, right) if a is not None and b is not None]
    if len(pairs) < 3:
        return None
    a, b = map(ranks, zip(*pairs))
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    denominator = math.sqrt(sum((v - ma) ** 2 for v in a) * sum((v - mb) ** 2 for v in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / denominator if denominator else None


def ordinal_alpha(groups):
    groups = [g for g in groups if len(g) >= 2]
    pooled = Counter(x for g in groups for x in g)
    total = sum(pooled.values())
    if total < 2:
        return None
    distance = {}
    for a in range(1, 5):
        for b in range(1, 5):
            lo, hi = sorted((a, b))
            distance[a, b] = (sum(pooled[k] for k in range(lo, hi + 1)) - (pooled[a] + pooled[b]) / 2) ** 2 if a != b else 0
    observed = 0.0
    for g in groups:
        counts = Counter(g)
        observed += sum(counts[a] * (counts[b] - (a == b)) * distance[a, b]
                        for a in range(1, 5) for b in range(1, 5)) / (len(g) - 1)
    expected = sum(pooled[a] * (pooled[b] - (a == b)) * distance[a, b]
                   for a in range(1, 5) for b in range(1, 5)) / (total - 1)
    return 1 - observed / expected if expected else None


def metrics(truth, predicted):
    n = len(truth)
    if not n or len(predicted) != n:
        raise ValueError('Empty or mismatched evaluation')
    confusion = [[sum(a == i and b == j for a, b in zip(truth, predicted)) for j in range(1, 5)] for i in range(1, 5)]
    f1s = []
    for k in range(4):
        tp = confusion[k][k]
        denominator = sum(confusion[k]) + sum(row[k] for row in confusion)
        f1s.append(2 * tp / denominator if denominator else 0)
    observed = sum(confusion[i][j] * (i - j) ** 2 for i in range(4) for j in range(4)) / n
    expected = sum(sum(confusion[i]) * sum(row[j] for row in confusion) * (i - j) ** 2
                   for i in range(4) for j in range(4)) / n ** 2
    return {'n': n, 'accuracy': sum(a == b for a, b in zip(truth, predicted)) / n,
            'macro_f1': sum(f1s) / 4, 'weighted_kappa': 1 - observed / expected if expected else None,
            'mean_absolute_level_error': sum(abs(a - b) for a, b in zip(truth, predicted)) / n}


def tree_predict(model, score):
    import struct
    # sklearn's tree inference converts input to float32.
    value = struct.unpack('f', struct.pack('f', score))[0]
    node = 0
    while model['children_left'][node] != -1:
        node = model['children_left'][node] if value <= model['thresholds'][node] else model['children_right'][node]
    probabilities = model['node_values'][node][0]
    return model['classes'][max(range(len(probabilities)), key=probabilities.__getitem__)]


def compute(root=ROOT):
    abstracts = {r['abstract_id']: r for r in rows(root / 'data/abstracts.csv')}
    annotations = json.loads((root / 'data/annotations.json').read_text(encoding='utf-8'))
    grouped = defaultdict(list)
    for r in annotations:
        grouped[r['abstract_id']].append(r)
    summaries = {}
    for aid, group in grouped.items():
        counts = Counter(r['jargon_level'] for r in group)
        mode = [k for k, v in counts.items() if v == max(counts.values())]
        scores = [r['jargon_score'] for r in group if r['jargon_score'] is not None]
        summaries[aid] = {'modal_level': mode[0] if len(mode) == 1 else None,
                          'mean_level': sum(r['jargon_level'] for r in group) / len(group),
                          'mean_score': sum(scores) / len(scores) if scores else None}
    readability = {r['abstract_id']: r for r in rows(root / 'baselines/readability_scores.csv')}
    test = sorted(aid for aid, r in abstracts.items() if r['split'] == 'test')
    train = [aid for aid, r in abstracts.items() if r['split'] == 'train']
    truth = [summaries[aid]['modal_level'] for aid in test]
    results = []
    correlations = []
    for method in METHODS:
        model = json.loads((root / f'baselines/calibration/{method}.json').read_text())
        predicted = [tree_predict(model, float(readability[aid][method])) for aid in test]
        results.append({'method': method, **metrics(truth, predicted)})
        for scope, ids in [('all', list(abstracts)), ('train', train), ('test', test)]:
            for domain in ['all', *sorted({r['domain'] for r in abstracts.values()})]:
                subset = [aid for aid in ids if domain == 'all' or abstracts[aid]['domain'] == domain]
                for target in ['modal_level', 'mean_level', 'mean_score']:
                    x = [float(readability[aid][method]) for aid in subset]
                    y = [summaries[aid][target] for aid in subset]
                    correlations.append({'scope': scope, 'domain': domain, 'method': method, 'target': target,
                                         'n': sum(v is not None for v in y), 'spearman_rho': spearman(x, y)})
    majority = Counter(summaries[aid]['modal_level'] for aid in train).most_common(1)[0][0]
    results.append({'method': 'training_majority_level', **metrics(truth, [majority] * len(test))})
    alpha = {'overall': ordinal_alpha([[r['jargon_level'] for r in g] for g in grouped.values()])}
    for domain in sorted({r['domain'] for r in abstracts.values()}):
        alpha[domain] = ordinal_alpha([[r['jargon_level'] for r in group] for aid, group in grouped.items() if abstracts[aid]['domain'] == domain])
    return results, correlations, alpha


if __name__ == '__main__':
    results, correlations, alpha = compute()
    output = ROOT / 'results'
    for name, records in [('baseline_comparison.csv', results), ('readability_correlations.csv', correlations)]:
        with (output / name).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows({k: 'null' if v is None else v for k, v in r.items()} for r in records)
    (output / 'agreement_recomputed.json').write_text(json.dumps(alpha, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ordinal_alpha': alpha['overall'], 'test_abstracts': results[0]['n'],
                      'baseline_accuracy': {r['method']: r['accuracy'] for r in results}}, indent=2))
