# N-back (PsychoPy)

This folder contains a self-contained Python virtual environment and a complete N-back task built with PsychoPy.

## Requirements

- Operating systems: Linux, macOS, or Windows.
- Python: 3.10.x (required by PsychoPy).
- PsychoPy: 2025.1.1 (pinned in requirements.txt).
- Optional for markers (installed by default here):
  - pylsl (for LSL markers)
  - pyserial (for serial trigger devices)

## Setup

- Create/refresh the virtual environment (optional if `.venv` already exists):
  - Python 3.10.x is required for PsychoPy (tested on 3.10). On Linux, run:
    - python3 -m venv .venv
    - .venv/bin/python -m pip install -U pip setuptools wheel
    - .venv/bin/python -m pip install -r requirements.txt
  - Windows (PowerShell):
    - py -3.10 -m venv .venv
    - .venv\Scripts\python -m pip install -U pip setuptools wheel
    - .venv\Scripts\python -m pip install -r requirements.txt

## Activate

- Bash/Zsh:
  - source .venv/bin/activate
  
- Windows (PowerShell):
  - .venv\Scripts\Activate.ps1

## Quick verify

- Ensure you’re on Python 3.10.x:
  - Linux/macOS: `.venv/bin/python -V`
  - Windows: `.venv\Scripts\python -V`
- Verify PsychoPy import:
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

## Consent text

The consent screen reads from `informed_consent.txt` placed next to `nback_task.py`. Edit that file to update the consent language without changing the code.

## Command-line arguments

- `--participant, -p` (str): Participant ID used in the output filename. Default: `anon`.
- `--n-back` (int): N for N-back (1, 2, or 3). Default: `2`.
- `--blocks` (int): Number of blocks in the main task. Default: `2`.
- `--trials` (int): Trials per block in the main task. Default: `120`.
- `--no-practice` (flag): Skip the practice phase. Default: practice runs.
- `--practice-trials` (int): Number of practice trials when practice is enabled. Default: `20`.

Advanced controls:
- `--iti-min` (int): Minimum ITI jitter in ms. Default: 500.
- `--iti-max` (int): Maximum ITI jitter in ms. Default: 900.
- `--lure-nminus1` (float): Probability of n-1 lures per non-target trial. Default: 0.05.
- `--lure-nplus1` (float): Probability of n+1 lures per non-target trial. Default: 0.05.
- `--target-rate` (float): Target rate per block (0–1). Default: 0.30.
- `--max-consec-targets` (int): Maximum allowed consecutive targets. Default: 1.
- `--seed` (int): Random seed for reproducibility. If provided, a sidecar `.meta.json` is produced capturing parameters.

## Data output

- Written to `./data/nback_{participant}_{YYYYMMDD_HHMMSS}.csv`.
- Columns: `participant_id, session_timestamp, block_idx, trial_idx, n_back, stimulus, is_target, lure_type, iti_ms, stim_onset_time, response_key, rt_ms, correct, marker_code_stim, marker_code_resp`.
- Sidecar metadata JSON is also written next to the CSV (same stem with `.meta.json`) and documents generator settings, ITI range, and the seed.

## Markers / Triggers (optional)

- Call sites are active but `send_marker` is a no-op by default.
- To enable markers, open `nback_task.py`, set `ENABLE_MARKERS = True`, and follow one commented integration example (LSL / Serial / Parallel). Only enable one.
  - LSL: pylsl is pre-listed in requirements; ensure your receiver is running.
  - Serial: adjust serial port name (e.g., `COM3` on Windows or `/dev/ttyUSB0` on Linux).
  - Parallel: ensure your system supports a parallel port and set the correct address.

## Notes

- The `.gitignore` prevents committing the `.venv/` directory.
- Update versions in `requirements.txt` when needed.
- See `DATA_DICTIONARY.md` for detailed field descriptions.

### Examples

- Custom ITI and reproducible sequence with 2-back, 1 block of 40 trials:
  - `python nback_task.py -p demo --n-back 2 --blocks 1 --trials 40 --iti-min 400 --iti-max 1200 --seed 1234`
- Increase target rate and allow up to 2 consecutive targets:
  - `python nback_task.py -p demo --target-rate 0.4 --max-consec-targets 2`
