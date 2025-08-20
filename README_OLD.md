# N-back Task (PsychoPy)

A comprehensive implementation of the N-back cognitive task built with PsychoPy for research in working memory and cognitive neuroscience.

## What is the N-back Task?

The N-back task is a well-established cognitive paradigm used to assess and train working memory. Participants are presented with a sequence of stimuli (letters in this implementation) and must identify when the current stimulus matches the one presented N trials ago. For example, in a 2-back task, participants press a key when the current letter matches the letter shown 2 trials earlier.

This implementation provides:
- **Configurable N-back levels** (1-back, 2-back, 3-back)
- **Precise timing** with display refresh rate detection
- **Comprehensive data output** with trial-by-trial logging
- **Optional EEG/physiological markers** (LSL, Serial, Parallel port)
- **Practice and main task phases** with customizable parameters
- **Cross-platform support** (Linux, macOS, Windows)

## Requirements

| Component | Version | Notes |
|-----------|---------|--------|
| **Operating System** | Linux, macOS, Windows | Tested on Ubuntu 20.04+, macOS 10.15+, Windows 10+ |
| **Python** | 3.10.x | Required by PsychoPy (3.11+ not yet supported) |
| **PsychoPy** | 2025.1.1 | Pinned for reproducibility |
| **Display** | Any | Fullscreen recommended for precise timing |

**Optional Dependencies** (pre-installed):
- `pylsl` ≥1.16.2 - For Lab Streaming Layer markers
- `pyserial` ≥3.5 - For serial port trigger devices

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

### Conda (Anaconda/Miniconda/Mambaforge)

- One-time channel setup (recommended):
  - `conda config --prepend channels conda-forge`
  - `conda config --set channel_priority strict`

- Create and activate the environment from `environment.yml`:
  - conda:
    - `conda env create -f environment.yml`
    - `conda activate n_back`
  - mamba (faster, if available):
    - `mamba env create -f environment.yml`
    - `conda activate n_back`

Notes:
- The `environment.yml` preinstalls `wxpython` from conda-forge to avoid slow/fragile source builds. Python and core tooling come from conda; PsychoPy and some extras are installed via pip from `requirements.txt`.

- Update the environment after changes to `requirements.txt`:
  - `conda env update -f environment.yml --prune`

Quick pilot run (windowed, no practice, small block):

```bash
conda activate n_back
python nback_task.py --participant pilot --no-practice --blocks 1 --trials 10 --windowed
```

Troubleshooting:
- If you see a pip build error for wxPython (GTK/headers missing), ensure you’re using this repo’s `environment.yml` (which installs `wxpython` via conda) and that conda-forge is enabled with strict priority.

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

Basic run (defaults to 2-back, 2 blocks x 120 trials, with practice). The task now defaults to fullscreen for stable timing, detects display refresh at startup, and reports it in the console and metadata:

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

Run in windowed mode for debugging (lower timing stability):

```bash
python nback_task.py --participant test --windowed
```

## Consent text

The consent screen reads from `texts/informed_consent.txt`. Edit that file to update the consent language without changing the code.

## Command-line arguments

- `--participant, -p` (str): Participant ID used in the output filename. Default: `anon`.
- `--n-back` (int): N for N-back (1, 2, or 3). Default: `2`.
- `--blocks` (int): Number of blocks in the main task. Default: `2`.
- `--trials` (int): Trials per block in the main task. Default: `120`.
- `--no-practice` (flag): Skip the practice phase. Default: practice runs.
- `--practice-trials` (int): Number of practice trials when practice is enabled. Default: `20`.
- `--windowed` (flag): Run windowed for debugging. Default is fullscreen (recommended for timing).

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
- Sidecar metadata JSON is also written next to the CSV (same stem with `.meta.json`) and documents generator settings, ITI range, the seed, detected display refresh (`display_refresh_hz`), and whether the window was fullscreen (`window_fullscreen`).

## Markers / Triggers (optional)

- Call sites are active but `send_marker` is a no-op by default.
- To enable markers, open `nback/markers.py`, set `ENABLE_MARKERS = True`, and follow one commented integration example (LSL / Serial / Parallel). Only enable one.
  - LSL: pylsl is pre-listed in requirements; ensure your receiver is running.
  - Serial: adjust serial port name (e.g., `COM3` on Windows or `/dev/ttyUSB0` on Linux).
  - Parallel: ensure your system supports a parallel port and set the correct address.

## Notes

- The `.gitignore` prevents committing the `.venv/` directory.
- Update versions in `requirements.txt` when needed.
- See `DATA_DICTIONARY.md` for detailed field descriptions.

## Timing

- Defaults to fullscreen for stable flip timing. Use `--windowed` for debugging only.
- Detects display refresh at startup and logs it to console and metadata (`display_refresh_hz`).
- Stimulus RT clock is aligned to the exact flip that presents the stimulus.
- Fixation and ITI are frame-synced using per-frame flips rather than coarse sleeps.
- Uses the hardware keyboard path when available for low-latency key events; falls back safely when not.

Diagnostics:
- Run `python scripts/timing_diagnostics.py --fullscr` to measure frame intervals on a given machine and flag long frames.
 - Optional: `python scripts/local_sequence_check.py` to quickly validate sequence constraints without opening a window.

## Sequence preview/debugging

To quickly preview the generated N-back sequence, targets, and lures for a given configuration (without running the full experiment), use:

```bash
PYTHONPATH=. python scripts/preview_seq.py [n_back] [n_trials] [seed]
```

Examples:

Preview a 2-back sequence of 10 trials:
```bash
PYTHONPATH=. python scripts/preview_seq.py 2 10
```

Preview a 3-back sequence of 20 trials with a fixed seed:
```bash
PYTHONPATH=. python scripts/preview_seq.py 3 20 1234
```

### Examples

- Custom ITI and reproducible sequence with 2-back, 1 block of 40 trials:
  - `python nback_task.py -p demo --n-back 2 --blocks 1 --trials 40 --iti-min 400 --iti-max 1200 --seed 1234`
- Increase target rate and allow up to 2 consecutive targets:
  - `python nback_task.py -p demo --target-rate 0.4 --max-consec-targets 2`
