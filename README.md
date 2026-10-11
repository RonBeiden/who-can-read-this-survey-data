# Who Can Read This? Survey dataset

Human judgments of the expertise needed to understand scientific abstracts.
Part of **Who Can Read This? Expert-Grounded Distillation of Jargon Levels in Scientific Abstract Using Large Language Models**, by Ron Beiden.

## Start here

1. Load `data/annotations.csv` (one person–abstract answer per row).
2. Join `abstract_id` to `data/abstracts.csv` for the exact text shown in the survey.
3. Use `data/abstract_summary.csv` for modal labels and the full four-level vote distribution.

```python
import json
from pathlib import Path

answers = json.loads(Path("data/annotations.json").read_text(encoding="utf-8"))
print(answers[0]["jargon_level"], answers[0]["jargon_score"])
```

JSON missing values are `null`. CSV missing values are the literal `null`.
With pandas, use `pd.read_csv(path, na_values=["null"])`.

## Survey and participants

The exported Qualtrics rating question asks: **“In your opinion, what is the minimum level of education required to fully understand this abstract?”** Participants selected a domain and received a set of five abstracts. Each abstract had a four-level classification, a continuous expertise score, and a question asking which vocabulary/concepts influenced the classification. All valid abstract-level answers are retained, including answers from unfinished surveys.

The 67 contributing survey records report MSc (38), PhD (22), or post-doc/faculty (7) backgrounds. These are self-reports, not independently verified credentials. Records are treated as distinct participants; person-level deduplication beyond the survey record was not independently verified. All survey responses are treated as human responses.

| Abstract domain | Participants | Abstracts | Answers |
| --- | ---: | ---: | ---: |
| Genetics / bioinformatics / biomedical | 22 | 20 | 102 |
| NLP / computational linguistics | 26 | 20 | 116 |
| HCI / IUI | 19 | 20 | 81 |
| Total | 67 | 60 | 299 |

## Labels and missing values

| Level | Minimum reader expertise |
| --- | --- |
| 1 | High school |
| 2 | BSc |
| 3 | MSc |
| 4 | PhD |

These labels describe the **reader required by the abstract**, not the annotator's degree. The continuous `jargon_score` is 0–100 in the survey, but **0 means unanswered in this release**, not low jargon. Five recorded zeros were converted to null, giving 13 missing scores in total. Means exclude missing scores. No categorical rating was changed.

`modal_level` is the most frequent rating, not unanimous or adjudicated truth. Keep the vote distribution when evaluating ambiguous abstracts. Overall ordinal Krippendorff’s alpha is **0.573**, with an abstract-bootstrap 95% interval **[0.440, 0.667]**. See `results/agreement.json` for domain estimates and the method.

## Traditional readability comparison

Six English readability formulas were scored on the exact survey text. A fixed decision tree (at most four leaves, minimum four development samples per leaf) maps each formula to the four labels. Calibration uses only 48 development abstracts; evaluation uses 12 test abstracts, four per domain. The split balances domain, label and ambiguity where feasible. Do not use test explanations or labels for training/prompt selection.

| Method | Test accuracy |
| --- | ---: |
| Flesch Reading Ease | 50.0% |
| Flesch–Kincaid Grade | 50.0% |
| SMOG | 50.0% |
| Dale–Chall | 50.0% |
| Gunning Fog | 41.7% |
| Automated Readability Index | 41.7% |
| Development-set majority label | 50.0% |

These are calibrated benchmarks, not native formula-to-education equivalences. The test set is small; one abstract changes accuracy by 8.3 percentage points. SMOG is exploratory because the abstracts are shorter than its usual 30-sentence basis. No model superiority is established. Public test labels can contaminate future evaluations if used during model development.

Run `python scripts/reproduce.py` to recompute agreement estimates, correlations, accuracy, macro-F1, quadratic weighted kappa and level error from the released data and stored calibration trees. No packages or API keys are needed. This reproduces evaluation, not extraction of the original readability scores. Score generation details are in `docs/METHODS.md`.

## Privacy, text review and limitations

Participant IDs are random release-specific codes. No participant emails, names, IP addresses, timestamps, original response IDs, row-level demographics, or private identifier mapping are included. Explanations were reviewed for identifying content. Linked response patterns can still carry residual re-identification risk; do not attempt to identify participants.

Original explanations retain their language and wording. A separate context-reviewed field is available for 17 investigator-reviewed answers; the other 282 remain unreviewed. These checks do not constitute independent dual coding or codebook approval. Abstract 55 retains one unresolved phrase. No unapproved AI-normalized explanation is presented as verified data.

Titles/source identifiers for **abs23, abs49 and abs52** do not match the displayed abstract body. Those metadata fields are null and flagged; the actual rated text is unchanged. Do not infer paper identity from these records until source metadata is resolved.

The dataset owner confirmed permission to share anonymized explanations and abstract texts. Annotations and derived data are **CC BY 4.0**; code is **MIT**. Third-party abstract texts retain their original rights and are not relicensed by this repository. See `LICENSE.md` and `docs/DATA_DICTIONARY.md`.

Snapshot: 8 October 2026. Version: 1.0.0. To cite, use `CITATION.cff`. Corrections can be reported through GitHub issues without posting participant information.
