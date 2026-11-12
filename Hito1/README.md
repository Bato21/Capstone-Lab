# Hito 1 · NextLap · Team 1

IIT414W capstone. Members: Vicente Rodríguez, Baptiste Vial.

| File | Content |
| --- | --- |
| [HITO1.md](HITO1.md) | Problem framing, reproduced reference, hypothesis and experiment plan. |
| [DECISION_LOG.md](DECISION_LOG.md) | Decisions, revisions after feedback, trials, contributions, AI record, next steps. |
| `run_references.py` | Reproduces training-median, persistence and OLS on the common validation rows. |
| `outputs/reference_metrics.csv` | MAE (s) and row counts, overall and per validation race. |
| `outputs/validation_reference_predictions.csv` | Per-`pair_id` predictions of the three references. |
| `outputs/reference_run.json` | Counts, rounds, features, environment versions and SHA-256 of inputs. |
| `requirements.txt` | Python dependencies. |

## Data location

The released dataset is not duplicated here. Unzip `IIT414W_Capstone_NextLap_StudentData_v1.zip` so that `base_NextLap/` sits next to this folder (in this repository: `base_NextLap/` at the repository root, git-ignored). Expected SHA-256:

| File | SHA-256 |
| --- | --- |
| `train_clean_v1.csv` | `43544f38cc9ef32b44886e6751e03522601265160086fe3a4956f04b87bd5c13` |
| `validation_clean_v1.csv` | `b19efb6a908af12a5d2c6bdde29aa40984295e62ce0f187a201b579278db7ee8` |
| `nextlap_reference_v1.py` | `f6c58925cd4a477bf3e1a5a2b3968e67df3a1cffabecee9e89701c3ac2d5f994` |

## Run

```bash
pip install -r requirements.txt
cd Hito1
python run_references.py                        # uses ../base_NextLap
python run_references.py --base PATH/base_NextLap   # if the data are elsewhere
```

The run takes a few seconds and overwrites `outputs/`. Verified with Python 3.10.4, numpy 1.26.4, pandas 2.2.3 and scikit-learn 1.7.2. The instructor reference was verified with numpy 2.0.2, pandas 2.3.1 and scikit-learn 1.8.0, and gives the same results.

The script uses the supplied `nextlap_reference_v1.py` (`make_model`) and is adapted from the class helper `probar_referencia_v1.py`. No reserved final-evaluation data are used.

## Submission

Repository: https://github.com/Bato21/Capstone-Lab · The exact submitted commit is given in the Canvas submission text and in the GitHub release `Hito1`.
