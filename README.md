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

## Installation and Setup

### Option 1: Virtual Environment (Recommended)

This is the most reliable method for ensuring compatibility.

#### Linux/macOS
```bash
# Clone the repository
git clone https://github.com/TH3PL4Y3R1/n_back.git
cd n_back

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install dependencies
.venv/bin/python -m pip install -U pip setuptools wheel
.venv/bin/python -m pip install -r requirements.txt

# Verify installation
python check_psychopy.py
```

#### Windows (PowerShell)
```powershell
# Clone the repository
git clone https://github.com/TH3PL4Y3R1/n_back.git
cd n_back

# Create virtual environment (ensure Python 3.10.x is installed)
py -3.10 -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
.venv\Scripts\python -m pip install -U pip setuptools wheel
.venv\Scripts\python -m pip install -r requirements.txt

# Verify installation
python check_psychopy.py
```

### Option 2: Conda Environment

Conda can help avoid compilation issues with GUI dependencies.

```bash
# Create environment from file
conda env create -f environment.yml

# Activate environment
conda activate n_back

# Verify installation
python check_psychopy.py
```

#### Conda Configuration (First Time Setup)
```bash
# Add conda-forge with strict priority (recommended)
conda config --prepend channels conda-forge
conda config --set channel_priority strict

# Update environment after changes to requirements.txt
conda env update -f environment.yml --prune
```

### Verification

After installation, you should see output similar to:
```
PsychoPy version: 2025.1.1
```

**Note**: The `environment.yml` preinstalls `wxpython` from conda-forge to avoid slow/fragile source builds.

## Quick Start

### Basic Usage

Run a complete experiment with default settings (2-back, 2 blocks × 120 trials):
```bash
python nback_task.py --participant test
```

Run a quick test session (windowed, no practice, small block):
```bash
python nback_task.py --participant pilot --no-practice --blocks 1 --trials 10 --windowed
```

### Usage Examples

**Development/Testing**:
```bash
# Windowed mode for debugging (reduced timing precision)
python nback_task.py --participant dev --windowed

# Skip practice phase
python nback_task.py --participant test --no-practice

# Custom practice length
python nback_task.py --participant test --practice-trials 10
```

**Research Configurations**:
```bash
# 3-back task with custom parameters
python nback_task.py --participant P001 --n-back 3 --blocks 3 --trials 100

# Reproducible sequence with seed
python nback_task.py --participant P001 --seed 1234

# Custom timing and target rate
python nback_task.py --participant P001 --iti-min 400 --iti-max 1200 --target-rate 0.4
```

## Command-Line Interface

### Required Arguments
- `--participant, -p` (str): Participant ID for output filename

### Core Task Parameters
- `--n-back` (int): N-back level (1, 2, or 3). Default: `2`
- `--blocks` (int): Number of blocks in main task. Default: `2`
- `--trials` (int): Trials per block. Default: `120`

### Practice Phase
- `--no-practice` (flag): Skip practice phase
- `--practice-trials` (int): Number of practice trials. Default: `20`

### Display and Timing
- `--windowed` (flag): Run windowed (for debugging only; reduces timing precision)

### Advanced Configuration
- `--iti-min` (int): Minimum inter-trial interval (ms). Default: `500`
- `--iti-max` (int): Maximum inter-trial interval (ms). Default: `900`
- `--target-rate` (float): Target rate (0-1). Default: `0.30`
- `--lure-nminus1` (float): Rate of n-1 lures. Default: `0.05`
- `--lure-nplus1` (float): Rate of n+1 lures. Default: `0.05`
- `--max-consec-targets` (int): Max consecutive targets. Default: `1`
- `--seed` (int): Random seed for reproducibility

## Task Flow

1. **Informed Consent**: Displays consent form from `texts/informed_consent.txt`
2. **Instructions**: Task-specific instructions with N-back level
3. **Practice Phase** (optional): Training trials with feedback
4. **Main Task**: Multiple blocks with breaks between
5. **Data Export**: Automatic CSV and metadata JSON export

### Participant Instructions

- **Target Response**: Press SPACEBAR when current letter matches the one N trials ago
- **Non-target**: Do nothing for all other letters
- **Breaks**: Rest between blocks; press ENTER to continue
- **Exit**: Press ESC to quit (data saved only if task completes normally)

## Data Output

### File Structure
```
data/
├── nback_{participant}_{YYYYMMDD_HHMMSS}.csv     # Trial data
└── nback_{participant}_{YYYYMMDD_HHMMSS}.meta.json  # Metadata
```

### Trial Data Columns
| Column | Type | Description |
|--------|------|-------------|
| `participant_id` | string | Participant identifier |
| `session_timestamp` | string | Session start time (YYYYMMDD_HHMMSS) |
| `block_idx` | int | Block number (1-indexed) |
| `trial_idx` | int | Trial number within block (1-indexed) |
| `n_back` | int | N-back level for this trial |
| `stimulus` | string | Letter presented |
| `is_target` | int | 1=target, 0=non-target |
| `lure_type` | string | "none", "n-1", or "n+1" |
| `iti_ms` | int | Inter-trial interval (milliseconds) |
| `stim_onset_time` | float | Stimulus onset timestamp (seconds) |
| `response_key` | string | Key pressed ("space" or empty) |
| `rt_ms` | float | Reaction time (milliseconds, empty if no response) |
| `correct` | int | 1=correct, 0=incorrect |
| `marker_code_stim` | int | Stimulus onset marker code |
| `marker_code_resp` | int | Response marker code (empty if no response) |

See [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) for complete field specifications.

## Physiological Markers (Optional)

The task includes marker support for EEG/physiological recordings but is disabled by default.

### Enable Markers
1. Edit `nback/markers.py`
2. Set `ENABLE_MARKERS = True`
3. Uncomment and configure ONE marker method:

**Lab Streaming Layer (LSL)**:
```python
# Uncomment LSL section in markers.py
# Ensure pylsl receiver is running
```

**Serial Port**:
```python
# Uncomment Serial section in markers.py
# Update port name: '/dev/ttyUSB0' (Linux) or 'COM3' (Windows)
```

**Parallel Port**:
```python
# Uncomment Parallel section in markers.py  
# Update address: typically 0x0378
```

### Marker Codes
| Event | Code |
|-------|------|
| Consent shown | 10 |
| Block start | 20 |
| Fixation onset | 30 |
| Target stimulus | 41 |
| Non-target stimulus | 42 |
| N-1 lure | 43 |
| N+1 lure | 44 |
| Response registered | 50 |
| Block end | 70 |
| Task complete | 90 |

## Repository Structure

```
n_back/
├── README.md              # This file
├── DATA_DICTIONARY.md     # Complete data field descriptions
├── requirements.txt       # Python dependencies
├── environment.yml        # Conda environment specification
├── check_psychopy.py      # Installation verification script
├── nback_task.py         # Main task script
├── nback/                # Task modules
│   ├── __init__.py
│   ├── markers.py        # Marker/trigger integration
│   └── sequences.py      # Sequence generation logic
├── scripts/              # Utility scripts
│   ├── timing_diagnostics.py    # Display timing assessment
│   ├── preview_seq.py           # Sequence preview tool
│   └── local_sequence_check.py  # Sequence validation
└── texts/                # Instruction text files
    ├── informed_consent.txt
    ├── instructions_welcome.txt
    └── ... (other instruction files)
```

## Timing and Performance

### Timing Precision
- **Fullscreen mode** (default): Optimal timing precision using hardware vsync
- **Windowed mode** (`--windowed`): Reduced precision, for debugging only
- **Display refresh detection**: Automatic at startup, logged in metadata
- **Frame-synced presentation**: All stimuli locked to display refresh
- **Hardware keyboard**: Low-latency input when available

### Performance Monitoring
Run timing diagnostics to assess your system:
```bash
python scripts/timing_diagnostics.py --fullscr
```

### Sequence Preview
Preview generated sequences without running the full task:
```bash
# Preview 2-back sequence with 20 trials
PYTHONPATH=. python scripts/preview_seq.py 2 20

# With specific seed
PYTHONPATH=. python scripts/preview_seq.py 2 20 1234
```

## Troubleshooting

### Installation Issues

**wxPython build errors** (Linux):
- Use conda installation: `conda env create -f environment.yml`
- Ensure conda-forge channel is configured with strict priority

**Python version conflicts**:
- Ensure Python 3.10.x is installed and specified correctly
- On Windows: `py -3.10 -m venv .venv`
- Check version: `python --version`

**PsychoPy import failures**:
- Verify installation: `python check_psychopy.py`
- Check virtual environment activation
- Reinstall if needed: `pip install --force-reinstall psychopy==2025.1.1`

### Runtime Issues

**Display/timing problems**:
- Always use fullscreen mode for experiments (`--windowed` is debugging only)
- Run timing diagnostics: `python scripts/timing_diagnostics.py --fullscr`
- Close other applications that might affect display performance

**Task not starting**:
- Check file permissions on `texts/` directory
- Ensure `data/` directory exists (created automatically)
- Verify all instruction text files are present

**Data not saving**:
- Check write permissions in `data/` directory
- Avoid special characters in participant IDs
- Complete task normally (don't force-quit)

## Customization

### Instruction Text
Edit files in `texts/` directory to customize instructions:
- `informed_consent.txt` - Consent form
- `instructions_welcome.txt` - Welcome message
- `instructions_practice_headsup.txt` - Practice instructions
- `instructions_task_headsup.txt` - Main task instructions
- Other instruction files for breaks, feedback, etc.

### Task Parameters
Key parameters can be modified via command line or by editing defaults in `nback_task.py`:
- Stimulus letters (default: A-Z excluding I, O, Q)
- Timing parameters (ITI range, stimulus duration)
- Sequence constraints (target rate, lure rates)
- Display settings (colors, fonts, sizes)

## Contributing

We welcome contributions to improve the N-back task implementation. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style and standards
- Testing procedures
- Pull request process
- Bug reporting

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this implementation in your research, please cite:

```bibtex
@misc{nback_psychopy,
  title={N-back Task Implementation in PsychoPy},
  author={[Add author information]},
  year={2025},
  url={https://github.com/TH3PL4Y3R1/n_back}
}
```

## Support

- **Documentation**: See `DATA_DICTIONARY.md` for complete field descriptions
- **Issues**: Report bugs or request features via GitHub Issues
- **Questions**: For usage questions, please check existing issues first

---

**Version**: 1.0.0  
**Last Updated**: August 2025  
**Maintainer**: [Add maintainer contact information]