# n_back PsychoPy environment

This folder contains a self-contained Python virtual environment for running PsychoPy-based tasks.

## Setup

- Create/refresh the virtual environment (optional if `.venv` already exists):
  - Python 3.10+ recommended. On Linux, run:
    - python3 -m venv .venv
    - .venv/bin/python -m pip install -U pip setuptools wheel
    - .venv/bin/python -m pip install -r requirements.txt

## Activate

- Bash/Zsh:
  - source .venv/bin/activate

## Verify

- python check_psychopy.py

You should see a PsychoPy version printed.

## Notes

- The `.gitignore` prevents committing the `.venv/` directory.
- Pin updates by editing `requirements.txt`.
