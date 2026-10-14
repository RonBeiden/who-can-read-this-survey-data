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
| explanation_best_english | English-only, language-standardized human explanation; original meaning/list form retained; check review status before training |
| explanation_best_status | investigator_approved, ai_context_checked_pending_human_review, or unresolved_excluded |
| reasoning_training_candidate | True only for nonempty, non-unresolved development explanations; not an assertion of gold approval |

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

`data/explanation_normalization.json`: correction ledger, text checksums and review provenance. Investigator review covers 239 development answers, including one approved exclusion; 238 texts are approved for training. Global `human_review_completed` remains false because 60 held-out texts were not investigator-reviewed. `development_review_completed` is true.

`data/reasoning_codebook.json`: investigator-approved definitions for 11 themes and a separate uncertainty flag. `data/reasoning_sample_coding.json`: 48 investigator-approved, AI-drafted development assignments with original evidence spans. The 20-example confirmatory verification is complete; neither file claims independent dual coding.

`data/reasoning_coding.json`: codes and literal original evidence for all 239 development answers. `review_source`, `personally_reviewed_by_investigator`, and `human_verification_status` distinguish personal review, delegated assistant review and records not individually reviewed. Coding does not change ratings or resolve ambiguous text.

`data/cited_expression_catalogue.json`: development-only cited expressions and their anonymous source answer IDs. `classification` explicitly does not assert objective jargon. `abstract_match_kind` distinguishes literal/format-equivalent matches from nonliteral respondent concepts. `context_requires_caution` flags unconfirmed terminology; `teacher_guidance_eligible` is false for those source mentions. `citation_type` identifies explicitly reviewed ordinary words/idioms where applicable, otherwise it remains unclassified. `commentary_separated` preserves excluded commentary and absent-context examples, with reasons. Counts deduplicate each answer within a group. Join source IDs to annotations and abstracts for full text.

`results/reasoning_review_summary.json`: review scope and actual provenance counts; no private paths or participant identifiers.

`baselines/readability_scores.csv`: six uncalibrated formula scores, sentence count and SMOG warning.
`baselines/calibration/*.json`: development-fitted tree parameters.
`baselines/test_predictions.csv`: one method–test abstract prediction per row.
`results/baseline_comparison.csv`: recomputable 12-abstract test metrics, including the majority baseline.
`results/readability_correlations.csv`: Spearman correlations by domain/split and target; descriptive, without inferential p-values.
`results/agreement.json`: frozen ordinal alpha, bootstrap intervals and squared-distance sensitivity.
`results/agreement_recomputed.json`: reproducible ordinal point estimates.
`results/dataset_summary.json`: participant counts and aggregate self-reported education; no individual profile table.
