# Who Can Read This? Survey dataset

Expert judgments of the minimum reader expertise needed to understand scientific abstracts.
By Ron Beiden, for *Who Can Read This? Expert-Grounded Distillation of Jargon Levels
in Scientific Abstract Using Large Language Models*.

## Start here

1. `data/annotations.csv`: one annotator-answer per abstract, including the original and English-normalized explanation.
2. `data/abstracts.csv`: exact survey texts and paper metadata; join on `abstract_id`.
3. `data/abstract_summary.csv`: modal ratings and all four vote counts/proportions.

```python
import pandas as pd

answers = pd.read_csv("data/annotations.csv", na_values=["null"])
abstracts = pd.read_csv("data/abstracts.csv")
data = answers.merge(abstracts, on="abstract_id", validate="many_to_one")
```

The equivalent `annotations.json` uses JSON nulls. CSV missing values are the
literal `null`. Column definitions are in [the data dictionary](docs/DATA_DICTIONARY.md).

## Survey

Participants selected a domain and received five abstracts. For each, they chose
the minimum education needed to understand it, supplied an expertise score, and
named vocabulary/concepts influencing their judgment. Valid answers from
unfinished surveys are included. All survey responses are treated as human.

| Domain | Contributing survey records | Abstracts | Answers |
|---|---:|---:|---:|
| Genetics / bioinformatics / biomedical | 22 | 20 | 102 |
| NLP / computational linguistics | 26 | 20 | 116 |
| HCI / IUI | 19 | 20 | 81 |
| Total | 67 | 60 | 299 |

Self-reported backgrounds: MSc 38, PhD 22, post-doc/faculty 7. Credentials and
person-level uniqueness beyond the survey record were not independently verified.

Levels describe the required reader, not the annotator: **1 High school,
2 BSc, 3 MSc, 4 PhD**. Score 0 means unanswered and becomes null; 13 scores are
missing, including five converted zeros. Categorical ratings are unchanged.
Modal labels are not unanimous or adjudicated truth. Ordinal alpha is **0.573**,
with a 95% abstract-bootstrap interval **[0.440, 0.667]**; retain disagreement.

## Explanations

All 299 answers have `explanation_original` and `explanation_best_english`.
The English versions are AI-assisted translations/language corrections using
`gpt-5-6-luna`, checked against original wording and survey abstract context.
Lists remain lists; no new justifications are added. Corrections and provenance
are in `data/explanation_normalization.json`.

**238 development explanations are investigator-approved**; one unresolved
development explanation and all 60 test explanations are excluded from training.
Test explanations were not investigator-reviewed. This is not independent
bilingual or dual-human verification. Check approval and split before use:

```sh
python scripts/prepare_reasoning_training.py --output train_reasoning.jsonl
```

The `train` split means 48 development abstracts, not a prescribed inner
training/validation split. Create validation within development before tuning.
Coding, codebook and cited-expression files are optional descriptive extras,
not required training inputs or an objectively validated jargon dictionary.

## Readability baselines and reproduction

Six formulas are scored on the exact survey texts. Fixed calibration trees
were fitted on 48 development abstracts and evaluated on 12 test abstracts,
four per domain. Formula accuracies range from 41.7% to 50%; the development
majority baseline also scores 50%. See [all metrics](results/baseline_comparison.csv)
and [methods](docs/METHODS.md). Grades are not directly equated with degrees.
SMOG is exploratory on these short texts. Small samples do not establish superiority.

```sh
python scripts/reproduce.py
python scripts/validate_release.py
python -m unittest discover -s tests -v
```

Reproduction uses Python's standard library, stored scores and calibration trees;
it does not re-extract readability scores or require API keys. Generated files go
into ignored `outputs/reproduction/`, leaving the release unchanged. Never use
test labels or explanations for training or model selection.

## Privacy and reuse

IDs are random release-specific codes. No participant contacts, names, IPs,
timestamps, source response IDs, private mappings or individual demographics are
included. Explanations were privacy-reviewed; linked answer patterns still carry
residual identification risk. Do not attempt to identify participants.

The owner confirmed permission to share both text types. Annotations/derived data
are **CC BY 4.0**, code is **MIT**. Abstract texts retain their original rights;
this repo does not relicense them. See [licensing](LICENSE.md).

Snapshot: 8 October 2026. Version: **1.3.1** (repository cleanup only; annotations,
abstracts, explanations, splits and numerical results unchanged).
Use [CITATION.cff](CITATION.cff) to cite. Report corrections through GitHub issues
without posting participant information.
