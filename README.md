# N-back (PsychoPy)

This folder contains a self-contained Python virtual environment and a complete N-back task built with PsychoPy.

## Setup

- Create/refresh the virtual environment (optional if `.venv` already exists):
  - Python 3.10+ recommended. On Linux, run:
    - python3 -m venv .venv
    - .venv/bin/python -m pip install -U pip setuptools wheel
    - .venv/bin/python -m pip install -r requirements.txt

## Activate

- Bash/Zsh:
  - source .venv/bin/activate

## Quick verify

- python check_psychopy.py

You should see a PsychoPy version printed.

## Run the task

Basic run (defaults to 2-back, 2 blocks x 120 trials, with practice):

```bash
python nback_task.py --participant test
```

Skip practice and run a small test block:

```bash
python nback_task.py --participant test --n-back 2 --blocks 1 --trials 40 --no-practice
```

Control number of practice trials (training trials):

```bash
python nback_task.py --participant test --practice-trials 10
```

## Command-line arguments

- `--participant, -p` (str): Participant ID used in the output filename. Default: `anon`.
- `--n-back` (int): N for N-back (1, 2, or 3). Default: `2`.
- `--blocks` (int): Number of blocks in the main task. Default: `2`.
- `--trials` (int): Trials per block in the main task. Default: `120`.
- `--no-practice` (flag): Skip the practice phase. Default: practice runs.
- `--practice-trials` (int): Number of practice trials when practice is enabled. Default: `20`.

## Data output

- Written to `./data/nback_{participant}_{YYYYMMDD_HHMMSS}.csv`.
- Columns: `participant_id, session_timestamp, block_idx, trial_idx, n_back, stimulus, is_target, lure_type, iti_ms, stim_onset_time, response_key, rt_ms, correct, marker_code_stim, marker_code_resp`.

## Markers / Triggers (optional)

- Call sites are active but `send_marker` is a no-op by default.
- To enable markers, open `nback_task.py`, set `ENABLE_MARKERS = True`, and follow one commented integration example (LSL / Serial / Parallel). Only enable one.

## Notes

- The `.gitignore` prevents committing the `.venv/` directory.
- Update versions in `requirements.txt` when needed.
