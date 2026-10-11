"""Export development-only reasoning targets, with an explicit AI-standardized opt-in."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def select_targets(answers, abstracts, allow_ai_standardized=False):
    selected = []
    for r in answers:
        abstract = abstracts[r['abstract_id']]
        if abstract['split'] != 'train' or not r['reasoning_training_candidate']:
            continue
        if r['explanation_best_status'] == 'unresolved_excluded' or not r['explanation_best_english']:
            raise ValueError('Invalid reasoning training candidate')
        if r['explanation_best_status'] != 'investigator_approved' and not allow_ai_standardized:
            raise ValueError('English targets still need human QA and gold approval. Use --allow-ai-standardized only for explicitly AI-assisted candidate supervision.')
        selected.append({'annotation_id':r['annotation_id'], 'abstract_id':r['abstract_id'],
                         'abstract_text':abstract['abstract_text'], 'jargon_level':r['jargon_level'],
                         'explanation_target':r['explanation_best_english'],
                         'target_review_status':r['explanation_best_status']})
    return selected


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--allow-ai-standardized', action='store_true')
    a = p.parse_args()
    answers = json.loads((ROOT / 'data/annotations.json').read_text(encoding='utf-8'))
    with (ROOT / 'data/abstracts.csv').open(encoding='utf-8', newline='') as stream:
        abstracts = {r['abstract_id']:r for r in csv.DictReader(stream)}
    targets = select_targets(answers, abstracts, a.allow_ai_standardized)
    with a.output.open('x', encoding='utf-8') as stream:
        for row in targets:
            stream.write(json.dumps(row, ensure_ascii=False)+'\n')
    print(f'Exported {len(targets)} development-only explanation candidates; no held-out answers.')
