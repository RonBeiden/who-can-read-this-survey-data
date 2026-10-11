import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reproduce', ROOT / 'scripts/reproduce.py')
reproduce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reproduce)


class DatasetTests(unittest.TestCase):
    def test_coverage_and_nulls(self):
        annotations = json.loads((ROOT / 'data/annotations.json').read_text(encoding='utf-8'))
        self.assertEqual(len(annotations), 299)
        self.assertEqual(len({r['participant_id'] for r in annotations}), 67)
        self.assertEqual(len({(r['participant_id'], r['abstract_id']) for r in annotations}), 299)
        self.assertEqual(sum(r['jargon_score'] is None for r in annotations), 13)
        self.assertTrue(all(r['jargon_level'] in [1, 2, 3, 4] for r in annotations))
        self.assertTrue(all(r['jargon_score'] is None or 0 < r['jargon_score'] <= 100 for r in annotations))
        csv_data = reproduce.rows(ROOT / 'data/annotations.csv')
        self.assertEqual(sum(r['jargon_score'] == 'null' for r in csv_data), 13)
        self.assertEqual(sum(r['explanation_context_reviewed'] is not None for r in annotations), 17)
        self.assertEqual({r['context_review_status'] for r in annotations}, {'not_reviewed', 'investigator_reviewed', 'reviewed_unresolved_wording'})

    def test_abstracts(self):
        abstracts = reproduce.rows(ROOT / 'data/abstracts.csv')
        self.assertEqual(len(abstracts), 60)
        self.assertEqual(sum(r['split'] == 'test' for r in abstracts), 12)
        for r in abstracts:
            self.assertEqual(hashlib.sha256(r['abstract_text'].encode()).hexdigest(), r['abstract_sha256'])
            if r['abstract_id'] in ['abs23', 'abs49', 'abs52']:
                self.assertEqual(r['title'], 'null')
                self.assertEqual(r['openalex_id'], 'null')
        summaries = reproduce.rows(ROOT / 'data/abstract_summary.csv')
        self.assertEqual(sum(int(r['n_annotations']) for r in summaries), 299)
        self.assertEqual(sum(int(r['n_nonmissing_scores']) for r in summaries), 286)
        for r in summaries:
            self.assertEqual(sum(int(r[f'level_{k}_count']) for k in range(1, 5)), int(r['n_annotations']))
            self.assertAlmostEqual(sum(float(r[f'level_{k}_probability']) for k in range(1, 5)), 1)

    def test_baseline_and_agreement_reproduction(self):
        results, _, alpha = reproduce.compute()
        frozen = {r['method']: r for r in reproduce.rows(ROOT / 'baselines/heldout_comparison.csv')}
        for result in results[:-1]:
            for metric in ['n', 'accuracy', 'macro_f1', 'weighted_kappa', 'mean_absolute_level_error']:
                self.assertAlmostEqual(result[metric], float(frozen[result['method']][metric]))
        reference = json.loads((ROOT / 'results/agreement.json').read_text())
        self.assertAlmostEqual(alpha['overall'], reference['overall']['estimate'])
        self.assertEqual(results[-1]['accuracy'], 0.5)
        expected = {(r['method'], r['abstract_id']): int(r['predicted_level']) for r in reproduce.rows(ROOT / 'baselines/test_predictions.csv')}
        score_rows = reproduce.rows(ROOT / 'baselines/readability_scores.csv')
        for method in reproduce.METHODS:
            tree = json.loads((ROOT / f'baselines/calibration/{method}.json').read_text())
            for row in score_rows:
                key = method, row['abstract_id']
                if key in expected:
                    self.assertEqual(reproduce.tree_predict(tree, float(row[method])), expected[key])

    def test_public_files_no_contacts_or_private_ids(self):
        for folder in ['data', 'baselines', 'results', 'docs']:
            for path in (ROOT / folder).rglob('*'):
                if path.is_file():
                    text = path.read_text(encoding='utf-8')
                    self.assertIsNone(re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', text), path.name)
                    self.assertIsNone(re.search(r'\bR_[A-Za-z0-9]+\b', text), path.name)
                    self.assertIsNone(re.search(r'\b[0-9a-f]{16}_abs\d+\b', text), path.name)


if __name__ == '__main__':
    unittest.main()
