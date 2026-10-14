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
    def test_completed_reasoning_review_and_catalogue_scope(self):
        coding=json.loads((ROOT/'data/reasoning_coding.json').read_text(encoding='utf-8'))
        catalogue=json.loads((ROOT/'data/cited_expression_catalogue.json').read_text(encoding='utf-8'))
        summary=json.loads((ROOT/'results/reasoning_review_summary.json').read_text(encoding='utf-8'))
        answers={r['annotation_id']:r for r in json.loads((ROOT/'data/annotations.json').read_text(encoding='utf-8'))}
        abstracts={r['abstract_id']:r for r in reproduce.rows(ROOT/'data/abstracts.csv')}
        self.assertEqual(len(coding['records']),239)
        self.assertEqual(sum(r['personally_reviewed_by_investigator'] for r in coding['records']),71)
        self.assertEqual(summary['predefined_sample_personally_reviewed'],20)
        self.assertFalse(summary['independent_double_human_coding'])
        self.assertEqual(len(catalogue['entries']),826)
        self.assertFalse(catalogue['complete_or_objectively_validated_jargon'])
        caution=0
        for record in coding['records']:
            self.assertEqual(abstracts[record['abstract_id']]['split'],'train')
            for code in record['codes']+record['quality_flags']:
                self.assertIn(code['evidence'],answers[record['annotation_id']]['explanation_original'])
        for entry in catalogue['entries']:
            self.assertEqual(entry['annotation_count'],len({s['annotation_id'] for s in entry['sources']}))
            for source in entry['sources']:
                self.assertTrue(answers[source['annotation_id']]['reasoning_training_candidate'])
                self.assertIn(source['canonical_english_span'],answers[source['annotation_id']]['explanation_best_english'])
                if source['context_requires_caution']:
                    caution+=1
                    self.assertFalse(source['teacher_guidance_eligible'])
        self.assertEqual(caution,4)
        self.assertEqual(len(catalogue['commentary_separated']),88)

    def test_best_english_and_training_split(self):
        answers = json.loads((ROOT / 'data/annotations.json').read_text(encoding='utf-8'))
        abstracts = {r['abstract_id']:r for r in reproduce.rows(ROOT / 'data/abstracts.csv')}
        ledger = json.loads((ROOT / 'data/explanation_normalization.json').read_text(encoding='utf-8'))
        self.assertEqual(ledger['model'], 'gpt-5-6-luna')
        self.assertFalse(ledger['human_review_completed'])
        self.assertTrue(ledger['development_review_completed'])
        records = {r['annotation_id']:r for r in ledger['records']}
        self.assertEqual(len(records), 299)
        for r in answers:
            norm = records[r['annotation_id']]
            self.assertEqual(r['explanation_best_english'], norm['english'])
            self.assertIsNone(re.search(r'[\u0590-\u05ff\u0600-\u06ff\u0400-\u04ff]', norm['english']))
            self.assertEqual(hashlib.sha256(r['explanation_original'].encode()).hexdigest(), norm['original_explanation_sha256'])
            self.assertEqual(abstracts[r['abstract_id']]['abstract_sha256'], norm['abstract_sha256'])
            self.assertEqual(r['reasoning_training_candidate'], norm['split'] == 'train' and not norm['unresolved'])
        self.assertEqual(sum(r['reasoning_training_candidate'] for r in answers), 238)
        self.assertEqual(sum(r['explanation_best_status'] == 'unresolved_excluded' for r in answers), 2)
        self.assertEqual(records['A285']['english'].split(', ')[-3], 'nominal prediction')
        self.assertIn('not necessarily reason with a high schooler', records['A274']['english'])
        self.assertEqual(records['A274']['investigator_approval_scope'], 'retain_exclusion')
        self.assertIn('theory of mind reasoning', records['A276']['english'])
        self.assertEqual(sum(r['explanation_best_status']=='investigator_approved' for r in answers),238)
        self.assertEqual(sum(r['human_review_completed'] for r in records.values()),239)
        self.assertTrue(all(not r['human_review_completed'] for r in records.values() if r['split']=='test'))
        spec = importlib.util.spec_from_file_location('training_targets', ROOT / 'scripts/prepare_reasoning_training.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        targets = module.select_targets(answers, abstracts)
        self.assertEqual(len(targets), 238)
        self.assertTrue(all(abstracts[r['abstract_id']]['split'] == 'train' for r in targets))
        pending=[dict(r) for r in answers]
        next(r for r in pending if r['reasoning_training_candidate'])['explanation_best_status']='ai_context_checked_pending_human_review'
        with self.assertRaises(ValueError):
            module.select_targets(pending,abstracts)

    def test_investigator_codebook_and_sample(self):
        book=json.loads((ROOT/'data/reasoning_codebook.json').read_text(encoding='utf-8'))
        sample=json.loads((ROOT/'data/reasoning_sample_coding.json').read_text(encoding='utf-8'))
        answers={r['annotation_id']:r for r in json.loads((ROOT/'data/annotations.json').read_text(encoding='utf-8'))}
        abstracts={r['abstract_id']:r for r in reproduce.rows(ROOT/'data/abstracts.csv')}
        self.assertEqual(book['status'],'approved')
        self.assertEqual(len(book['themes']),11)
        self.assertEqual(book['quality_flags'][0]['id'],'UNINTERPRETABLE')
        self.assertEqual(len(sample['records']),48)
        self.assertTrue(sample['confirmatory_verification_completed'])
        for r in sample['records']:
            self.assertEqual(abstracts[r['abstract_id']]['split'],'train')
            self.assertTrue(all(s in answers[r['annotation_id']]['explanation_original'] for s in r['source_evidence'].values()))
        contrast=next(r for r in sample['records'] if r['sample_position']==21)['source_evidence']['CONTEXT_DEPENDENCE']
        self.assertIn('In 2016',contrast)
        self.assertIn('However, nowadays',contrast)

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
        corrections = json.loads((ROOT / 'data/source_corrections.json').read_text(encoding='utf-8'))
        self.assertEqual(set(corrections), {'abs23', 'abs49', 'abs52'})
        for r in abstracts:
            self.assertEqual(hashlib.sha256(r['abstract_text'].encode()).hexdigest(), r['abstract_sha256'])
            if r['abstract_id'] in corrections:
                correction = corrections[r['abstract_id']]
                for field in ['title', 'openalex_id', 'abstract_sha256']:
                    self.assertEqual(r[field], correction[field])
                self.assertEqual(r['metadata_status'], 'source_verified_corrected')
                self.assertTrue(correction['doi'].startswith('https://doi.org/'))
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
