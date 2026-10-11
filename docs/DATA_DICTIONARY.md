# Data dictionary

All CSVs use UTF-8, one header row, and `null` for missing values. JSON uses true nulls. Join files with `abstract_id`.

## `data/annotations.csv` and `.json`

| Field | Meaning |
| --- | --- |
| annotation_id | Release-specific answer ID; no source identifiers |
| participant_id | Random participant code, stable within this release |
| abstract_id | Survey abstract number, e.g. abs27 |
| jargon_level | Selected minimum reader expertise, integer 1–4 |
| jargon_score | Continuous expertise score; null if blank or recorded as 0 |
| explanation_original | Privacy-reviewed original answer, unchanged wording |
| explanation_context_reviewed | Context-checked wording for 17 reviewed answers; otherwise null |
| context_review_status | investigator_reviewed, reviewed_unresolved_wording, or not_reviewed |

## `data/abstracts.csv`

`domain`: genetics_bioinformatics_biomedical, nlp, or hci_iui.
`abstract_text`: exact body shown to respondents, not a newly retrieved version.
`abstract_sha256`: UTF-8 text checksum for identifying the exact version.
`title`, `openalex_id`: paper metadata. Three originally mismatched identities were corrected in version 1.0.1.
`metadata_status`: no_mismatch_detected or source_verified_corrected. “No mismatch detected” does not certify publisher-level provenance.
`data/source_corrections.json`: corrected metadata for abs23, abs49 and abs52, with DOI, primary source link, verification date and exact survey-text checksum. Only metadata was changed.
`split`: train (development) or test. Splits are at abstract level, not participant level; a participant may occur in both.

## `data/abstract_summary.csv`

`n_annotations`: number of distinct participant codes rating the abstract.
`modal_level`, `modal_share`: most frequent level and its proportion.
`strict_majority`: modal share greater than 0.5.
`mean_level`: arithmetic mean of levels, descriptive only.
`mean_score`, `n_nonmissing_scores`: mean and denominator after excluding blank/zero scores.
`level_range`: highest minus lowest rating.
`level_1_count` … `level_4_count`: all votes.
`level_1_probability` … `level_4_probability`: empirical vote proportions, not model confidence.

## Baselines and results

`baselines/readability_scores.csv`: six uncalibrated formula scores, sentence count and SMOG warning.
`baselines/calibration/*.json`: development-fitted tree parameters.
`baselines/test_predictions.csv`: one method–test abstract prediction per row.
`results/baseline_comparison.csv`: recomputable 12-abstract test metrics, including the majority baseline.
`results/readability_correlations.csv`: Spearman correlations by domain/split and target; descriptive, without inferential p-values.
`results/agreement.json`: frozen ordinal alpha, bootstrap intervals and squared-distance sensitivity.
`results/agreement_recomputed.json`: reproducible ordinal point estimates.
`results/dataset_summary.json`: participant counts and aggregate self-reported education; no individual profile table.
