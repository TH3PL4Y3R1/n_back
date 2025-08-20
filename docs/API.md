# API Reference

This document provides detailed information about the modules, functions, and classes in the N-back task implementation.

## Core Modules

### `nback_task.py`

The main task script that orchestrates the entire N-back experiment.

#### Key Functions

##### `main(argv: Optional[List[str]] = None) -> int`
Main entry point for the N-back task.

**Parameters:**
- `argv`: Command-line arguments (optional, uses sys.argv if None)

**Returns:**
- `int`: Exit code (0 for success)

**Example:**
```python
# Run programmatically
from nback_task import main
exit_code = main(['--participant', 'test', '--windowed'])
```

##### `show_consent(win: visual.Window, text_stim: Optional[visual.TextStim] = None, consent_file: Optional[str] = None) -> None`
Display informed consent screen.

**Parameters:**
- `win`: PsychoPy window object
- `text_stim`: Optional pre-configured text stimulus
- `consent_file`: Optional path to consent file (default: texts/informed_consent.txt)

##### `run_practice_block(win: visual.Window, n_back: int, n_trials: int, kb: Optional[object] = None) -> Tuple[float, float]`
Execute practice block with feedback.

**Parameters:**
- `win`: PsychoPy window object
- `n_back`: N-back level
- `n_trials`: Number of practice trials
- `kb`: Optional hardware keyboard object

**Returns:**
- `Tuple[float, float]`: (accuracy, mean_reaction_time)

##### `run_main_block(win: visual.Window, n_back: int, trials: List[TrialPlan], block_idx: int, writer: csv.DictWriter, kb: Optional[object] = None) -> Tuple[float, float]`
Execute main task block.

**Parameters:**
- `win`: PsychoPy window object
- `n_back`: N-back level
- `trials`: List of trial specifications
- `block_idx`: Block number (1-indexed)
- `writer`: CSV writer for data output
- `kb`: Optional hardware keyboard object

**Returns:**
- `Tuple[float, float]`: (accuracy, mean_reaction_time)

#### Configuration Constants

```python
# Task parameters
CFG_TARGET_RATE = 0.30          # Target trial rate
CFG_LURE_NM1 = 0.05            # N-1 lure rate
CFG_LURE_NP1 = 0.05            # N+1 lure rate
CFG_MAX_CONSEC_TARGETS = 1      # Max consecutive targets
CFG_ITI_RANGE_MS = (500, 900)   # ITI range in milliseconds

# Display settings
TEXT_COLOR = (1, 1, 1)          # White text
BG_COLOR = (0, 0, 0)            # Black background
FONT = "Arial"                  # Font family
STIM_HEIGHT = 0.15              # Stimulus height (norm units)

# Timing
FIXATION_DURATION_S = 0.5       # Fixation cross duration
STIMULUS_DURATION_S = 0.5       # Stimulus duration
RESPONSE_WINDOW_S = 2.0         # Response collection window

# Keys
KEY_PROCEED = "return"          # Continue/proceed key
KEY_QUIT = "escape"             # Quit key  
KEY_TARGET = "space"            # Target response key
```

### `nback/sequences.py`

Module for N-back sequence generation and validation.

#### Classes

##### `TrialPlan`
Dataclass representing a single trial specification.

```python
@dataclass
class TrialPlan:
    stimulus: str           # Letter to display
    is_target: bool        # Whether this is a target trial
    lure_type: str         # "none", "n-1", or "n+1"
    iti_ms: int           # Inter-trial interval in milliseconds
```

#### Functions

##### `generate_sequence(n_back: int, n_trials: int, target_rate: float = 0.30, lure_nminus1_rate: float = 0.05, lure_nplus1_rate: float = 0.05, max_consec_targets: int = 1, iti_range: Tuple[int, int] = (500, 900), letters: Optional[List[str]] = None, max_attempts: int = 1000) -> List[TrialPlan]`
Generate a complete N-back sequence with constraints.

**Parameters:**
- `n_back`: N-back level (1, 2, or 3)
- `n_trials`: Number of trials to generate
- `target_rate`: Proportion of target trials (0.0-1.0)
- `lure_nminus1_rate`: Rate of n-1 lures among non-targets
- `lure_nplus1_rate`: Rate of n+1 lures among non-targets  
- `max_consec_targets`: Maximum consecutive targets allowed
- `iti_range`: (min_ms, max_ms) for inter-trial intervals
- `letters`: Optional custom letter set (default: A-Z minus I,O,Q)
- `max_attempts`: Maximum generation attempts before giving up

**Returns:**
- `List[TrialPlan]`: Generated sequence

**Raises:**
- `ValueError`: If constraints cannot be satisfied

**Example:**
```python
from nback.sequences import generate_sequence

# Generate 2-back sequence
sequence = generate_sequence(
    n_back=2, 
    n_trials=20, 
    target_rate=0.3,
    max_consec_targets=1
)

for trial in sequence:
    print(f"Trial: {trial.stimulus}, Target: {trial.is_target}")
```

##### `validate_sequence(sequence: List[TrialPlan], n_back: int, target_rate: float, max_consec_targets: int) -> bool`
Validate that a sequence meets N-back constraints.

**Parameters:**
- `sequence`: Sequence to validate
- `n_back`: Expected N-back level
- `target_rate`: Expected target rate (tolerance: ±1 trial)
- `max_consec_targets`: Maximum allowed consecutive targets

**Returns:**
- `bool`: True if sequence is valid

##### `get_default_letters() -> List[str]`
Get default letter set (A-Z excluding I, O, Q).

**Returns:**
- `List[str]`: List of letter strings

### `nback/markers.py`

Module for physiological marker/trigger integration.

#### Configuration

```python
# Enable/disable markers globally
ENABLE_MARKERS = False  # Set to True to enable markers
```

#### Marker Codes

```python
MARK_CONSENT_SHOWN = 10         # Consent screen displayed
MARK_BLOCK_START = 20           # Block started
MARK_FIXATION_ONSET = 30        # Fixation cross shown
MARK_STIM_TARGET = 41           # Target stimulus presented
MARK_STIM_NONTARGET = 42        # Non-target stimulus presented
MARK_STIM_LURE_N_MINUS_1 = 43   # N-1 lure presented
MARK_STIM_LURE_N_PLUS_1 = 44    # N+1 lure presented
MARK_RESPONSE_REGISTERED = 50    # Response detected
MARK_BLOCK_END = 70             # Block completed
MARK_THANK_YOU = 90             # Task finished
```

#### Functions

##### `send_marker(code: int, info: Optional[dict] = None) -> None`
Send marker code via configured method.

**Parameters:**
- `code`: Marker code to send
- `info`: Optional additional information (for future use)

**Note:** This is a no-op unless `ENABLE_MARKERS = True` and a transport method is configured.

#### Transport Methods

The module includes commented implementations for:

- **Lab Streaming Layer (LSL)**: Via pylsl
- **Serial Port**: Via pyserial  
- **Parallel Port**: Via PsychoPy parallel port

To enable, uncomment the appropriate section and set `ENABLE_MARKERS = True`.

## Utility Scripts

### `scripts/timing_diagnostics.py`

Assess display timing performance.

**Usage:**
```bash
python scripts/timing_diagnostics.py [--fullscr] [--frames N]
```

**Options:**
- `--fullscr`: Run fullscreen for maximum timing stability
- `--frames N`: Number of frames to sample (default: 600)

**Output:**
- Frame interval statistics
- Dropped frame count
- Refresh rate detection

### `scripts/preview_seq.py`

Preview N-back sequences without running the full task.

**Usage:**
```bash
PYTHONPATH=. python scripts/preview_seq.py [n_back] [n_trials] [seed]
```

**Parameters:**
- `n_back`: N-back level (default: 2)
- `n_trials`: Number of trials (default: 20)
- `seed`: Random seed (optional)

**Output:**
- Trial-by-trial sequence breakdown
- Target/lure statistics
- Constraint validation

### `scripts/local_sequence_check.py`

Validate sequence generation constraints.

**Usage:**
```bash
python scripts/local_sequence_check.py
```

**Output:**
- Constraint validation results
- Statistical analysis of generated sequences

## Data Structures

### Trial Data Format

Each trial generates a row with these fields:

```python
{
    "participant_id": str,          # Participant identifier
    "session_timestamp": str,       # Session start (YYYYMMDD_HHMMSS)
    "block_idx": int,              # Block number (1-indexed)
    "trial_idx": int,              # Trial in block (1-indexed)
    "n_back": int,                 # N-back level
    "stimulus": str,               # Displayed letter
    "is_target": int,              # 1=target, 0=non-target
    "lure_type": str,              # "none", "n-1", "n+1"
    "iti_ms": int,                 # Inter-trial interval (ms)
    "stim_onset_time": float,      # Stimulus onset timestamp (s)
    "response_key": str,           # Key pressed or ""
    "rt_ms": Union[float, str],    # Reaction time (ms) or ""
    "correct": int,                # 1=correct, 0=incorrect
    "marker_code_stim": int,       # Stimulus marker code
    "marker_code_resp": Union[int, str],  # Response marker or ""
}
```

### Metadata Format

Session metadata is saved as JSON:

```python
{
    "participant_id": str,
    "session_timestamp": str,
    "n_back": int,
    "blocks": int,
    "trials_per_block": int,
    "practice_trials": int,
    "practice_target_rate": float,
    "practice_has_lures": bool,
    "target_rate": float,
    "lure_nminus1_rate": float,
    "lure_nplus1_rate": float,
    "max_consec_targets": int,
    "iti_ms_range": [int, int],
    "seed": Union[int, None],
    "letters": List[str],
    "psychopy_version": Union[str, None],
    "display_refresh_hz": Union[float, None],
    "window_fullscreen": bool
}
```

## Extension Points

### Custom Marker Integrations

To add new marker transport methods:

1. **Edit `nback/markers.py`**
2. **Add transport initialization function**:
   ```python
   _custom_transport = None
   def _get_custom_transport():
       global _custom_transport
       if _custom_transport is None:
           # Initialize your transport here
           pass
       return _custom_transport
   ```

3. **Add code to `send_marker()` function**:
   ```python
   # Custom transport send
   # transport = _get_custom_transport()
   # transport.send(int(code))
   ```

### Custom Instruction Text

Replace or modify instruction files in `texts/` directory:

- `informed_consent.txt` - Consent form
- `instructions_welcome.txt` - Welcome/intro
- `instructions_practice_headsup.txt` - Practice instructions
- `instructions_task_headsup.txt` - Main task instructions
- `instructions_break.txt` - Break screen
- `instructions_thanks.txt` - Completion message
- `instructions_save_and_exit.txt` - Final save prompt
- `instructions_practice_feedback_pass.txt` - Practice success
- `instructions_practice_feedback_fail.txt` - Practice failure

### Custom Stimuli

To use non-letter stimuli:

1. **Modify `get_default_letters()` in `nback/sequences.py`**
2. **Update stimulus rendering in `nback_task.py`**
3. **Adjust instruction text accordingly**

### Performance Monitoring

Add custom timing measurements:

```python
from psychopy import core

# High-resolution timing
start_time = core.getTime()
# ... your code ...
elapsed = core.getTime() - start_time
```

## Error Handling

### Common Exceptions

- `ValueError`: Invalid parameters or constraints
- `FileNotFoundError`: Missing instruction text files
- `ImportError`: Missing optional dependencies (hardware keyboard, etc.)
- `RuntimeError`: PsychoPy window/display issues

### Graceful Degradation

The task includes fallbacks for:

- **Hardware keyboard**: Falls back to standard event handling
- **Display refresh detection**: Uses default if detection fails
- **Marker sending**: No-op if disabled or transport unavailable

### Debugging Tips

1. **Use windowed mode** for development: `--windowed`
2. **Enable logging** in PsychoPy for detailed output
3. **Test with minimal trials**: `--trials 5 --no-practice`
4. **Check timing diagnostics** if experiencing performance issues

---

This API reference covers the main interfaces and extension points. For implementation details, see the source code comments and docstrings.