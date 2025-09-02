#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PsychoPy N-back task with optional (commented) marker plumbing for EEG/ECG integrations.
- Runs out of the box with markers disabled (no-op).
- Toggle ENABLE_MARKERS to True and follow commented examples to integrate with LSL/Serial/Parallel.

Data: Writes trial-wise CSV to ./data/nback_{participantID}_{YYYYMMDD_HHMMSS}.csv
"""

from __future__ import annotations

import os
import sys
import csv
import random
import string
import argparse
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from psychopy import core, visual, event, gui
try:
    from psychopy.hardware import keyboard as hw_keyboard
    _HAVE_HW_KB = True
except Exception:
    _HAVE_HW_KB = False
from nback.markers import (
    ENABLE_MARKERS,
    MARK_CONSENT_SHOWN,
    MARK_BLOCK_START,
    MARK_FIXATION_ONSET,
    MARK_STIM_TARGET,
    MARK_STIM_NONTARGET,
    MARK_STIM_LURE_N_MINUS_1,
    MARK_STIM_LURE_N_PLUS_1,
    MARK_RESPONSE_REGISTERED,
    MARK_BLOCK_END,
    MARK_THANK_YOU,
    send_marker,
)
from nback.sequences import (
    TrialPlan,
    generate_sequence,
)

# =========================
# Parameters (defaults)
# =========================
# Task structure
N_BACK_DEFAULT = 2
N_BLOCKS = 2
TRIALS_PER_BLOCK = 120

# Practice
PRACTICE_TRIALS = 20  # default; can be overridden via --practice-trials
PRACTICE_TARGET_RATE = 0.25
PRACTICE_HAS_LURES = False
# Practice passing criterion (fraction correct)
PRACTICE_PASS_ACC = 0.75

# Stimulus set
EXCLUDE_CONFUSABLES = True  # Exclude I/O/Q if True
LETTERS = [c for c in string.ascii_uppercase]
if EXCLUDE_CONFUSABLES:
    LETTERS = [c for c in LETTERS if c not in {"I", "O", "Q"}]

# Timing (ms)
FIXATION_DUR_MS = 500
STIM_DUR_MS = 500
RESP_WINDOW_MS = 1500  # measured from stimulus onset
ITI_JITTER_RANGE_MS = (500, 900)  # inclusive bounds for uniform jitter; CLI can override

# Sequence constraints
TARGET_RATE = 0.30
LURE_N_MINUS_1_RATE = 0.05
LURE_N_PLUS_1_RATE = 0.05
MAX_IDENTICAL_RUN = 2  # cap identical-letter runs unless needed for target/lure
MAX_ATTEMPTS = 300

# Default limit on consecutive targets (can be overridden via CLI)
MAX_CONSEC_TARGETS_DEFAULT = 1

# Visuals
BACKGROUND_COLOR = [0.2, 0.2, 0.2]  # gray
TEXT_COLOR = [1.0, 1.0, 1.0]
FONT = "Arial"
FONT_HEIGHT = 0.12  # normalized units
FIXATION_HEIGHT = 0.18

# Keys
KEY_PROCEED = "return"
KEY_RESPONSE = "space"
KEY_QUIT = "escape"

"""Markers are imported from nback.markers."""

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEXTS_DIR = os.path.join(os.path.dirname(__file__), "texts")
CONSENT_FILE = os.path.join(TEXTS_DIR, "informed_consent.txt")

# Runtime configuration (set from CLI in main())
CFG_TARGET_RATE = TARGET_RATE
CFG_LURE_NM1 = LURE_N_MINUS_1_RATE
CFG_LURE_NP1 = LURE_N_PLUS_1_RATE
CFG_MAX_CONSEC_TARGETS = MAX_CONSEC_TARGETS_DEFAULT
CFG_ITI_RANGE_MS = ITI_JITTER_RANGE_MS

# Pre-created stimuli (initialized after window creation)
STIM_LETTER: Optional[visual.TextStim] = None
STIM_FIXATION: Optional[visual.TextStim] = None


# =========================
# Utilities
# =========================

def make_data_dir(path: str = DATA_DIR) -> None:
    os.makedirs(path, exist_ok=True)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".")).strip()


# =========================
"""Marker plumbing now lives in nback/markers.py; send_marker is imported."""


# =========================
# Sequence generation
# =========================

"""TrialPlan dataclass is imported from nback.sequences."""


# Sequence helpers are imported from nback.sequences


# ...existing code...


# Validation is imported from nback.sequences


"""Sequence generation moved to nback.sequences.generate_sequence."""


# =========================
# Rendering / Task flow
# =========================

def show_consent(win: visual.Window, text_stim: Optional[visual.TextStim] = None, consent_file: Optional[str] = None) -> None:
    """Show informed consent first.
    Loads text from informed_consent.txt and appends "(Press ENTER to continue)".
    ENTER proceeds; ESC quits (no save).
    The consent marker call is present but commented by default.
    """
    # Load consent text from file (UTF-8). Fallback to minimal notice if missing.
    path = consent_file or CONSENT_FILE
    consent_text = None
    try:
        with open(path, "r", encoding="utf-8") as cf:
            consent_text = cf.read().strip()
    except Exception:
        consent_text = None

    if not consent_text:
        consent_text = (
            "Consent text file not found. Please add informed_consent.txt next to nback_task.py."
        )
    # Auto-scale to fit window height (avoids text running off-screen on smaller displays)
    txt = f"{consent_text}\n\n(Press ENTER to continue)"

    if text_stim is None:
        stim = _make_autosized_text(win, txt)
    else:
        # If a custom stim supplied, still ensure appended prompt and wrapping
        text_stim.text = txt
        text_stim.wrapWidth = text_stim.wrapWidth or _default_wrap_width(win)
        stim = text_stim

    stim.draw()
    win.flip()
    # send_marker(MARK_CONSENT_SHOWN)  # 10: consent_shown (commented by default)
    event.clearEvents()
    while True:
        keys = event.waitKeys(keyList=[KEY_PROCEED, KEY_QUIT])
        if KEY_QUIT in keys:
            graceful_quit(None, None, [], win, abort=True)
        if KEY_PROCEED in keys:
            break


INSTR_WELCOME_FILE = os.path.join(TEXTS_DIR, "instructions_welcome.txt")
INSTR_PRACTICE_FILE = os.path.join(TEXTS_DIR, "instructions_practice_headsup.txt")
INSTR_TASK_FILE = os.path.join(TEXTS_DIR, "instructions_task_headsup.txt")
INSTR_BREAK_FILE = os.path.join(TEXTS_DIR, "instructions_break.txt")
INSTR_THANKS_FILE = os.path.join(TEXTS_DIR, "instructions_thanks.txt")
INSTR_SAVE_EXIT_FILE = os.path.join(TEXTS_DIR, "instructions_save_and_exit.txt")
INSTR_PRACTICE_PASS_FILE = os.path.join(TEXTS_DIR, "instructions_practice_feedback_pass.txt")
INSTR_PRACTICE_FAIL_FILE = os.path.join(TEXTS_DIR, "instructions_practice_feedback_fail.txt")


def _load_text(path: str, fallback: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read().strip()
            return txt if txt else fallback
    except Exception:
        return fallback


def show_instructions(win: visual.Window, n_back: int) -> None:
    base = _load_text(INSTR_WELCOME_FILE, f"Welcome to the {n_back}-back task.\nPress ENTER/RETURN to begin practice.")
    txt = base.replace("{{N}}", str(n_back)) + "\n\n(Press ENTER/RETURN to continue)"
    stim = visual.TextStim(win, text=txt, color=TEXT_COLOR, font=FONT, height=0.06, wrapWidth=1.5)
    stim.draw()
    win.flip()
    event.clearEvents()
    while True:
        keys = event.waitKeys(keyList=[KEY_PROCEED, KEY_QUIT])
        if KEY_QUIT in keys:
            graceful_quit(None, None, [], win, abort=True)
        if KEY_PROCEED in keys:
            break


# =========================
# Text auto-sizing utilities
# =========================

def _default_wrap_width(win: visual.Window, margin: float = 0.95) -> float:
    """Compute a sensible wrapWidth in 'height' units given current window size.
    When units='height', width in those units equals aspect_ratio.
    We multiply by a margin < 1 to keep some horizontal padding.
    """
    try:
        aspect = win.size[0] / float(win.size[1])
    except Exception:
        aspect = 16/9
    return aspect * margin


def _make_autosized_text(
    win: visual.Window,
    text: str,
    start_height: float = 0.07,
    min_height: float = 0.03,
    max_height_frac: float = 0.9,
    shrink_factor: float = 0.9,
) -> visual.TextStim:
    """Create a TextStim that automatically shrinks until it fits the vertical space.

    Parameters:
        win: PsychoPy Window (units='height').
        text: Text to display.
        start_height: Initial character height (in 'height' units).
        min_height: Lower bound for shrinking.
        max_height_frac: Fraction of window pixel height allowed for bounding box.
        shrink_factor: Multiplicative factor applied per iteration when too tall.
    """
    wrap_w = _default_wrap_width(win)
    h = start_height
    stim = visual.TextStim(
        win,
        text=text,
        color=TEXT_COLOR,
        font=FONT,
        height=h,
        wrapWidth=wrap_w,
        alignText='left',
        anchorHoriz='center',
        anchorVert='center',
    )

    # Iteratively shrink until bounding box fits within desired vertical fraction.
    # boundingBox returns (w, h) in pixels, or None if not yet drawable.
    try:
        while True:
            bb = getattr(stim, 'boundingBox', None)
            if not bb:
                # Draw once to establish metrics
                stim.draw(); win.flip(); core.wait(0.01)
                bb = getattr(stim, 'boundingBox', None)
            if not bb:
                break
            bb_h = bb[1] if isinstance(bb, (list, tuple)) and len(bb) > 1 else 0
            if bb_h <= win.size[1] * max_height_frac:
                break
            h *= shrink_factor
            if h < min_height:
                break
            stim.height = h
    except Exception:
        pass  # Fail gracefully; keep last size
    return stim


def show_practice_headsup(win: visual.Window) -> None:
    msg = _load_text(INSTR_PRACTICE_FILE, "Practice is about to begin. Try to reach the accuracy criterion to proceed.") + "\n\n(Press ENTER/RETURN to start)"
    stim = visual.TextStim(win, text=msg, color=TEXT_COLOR, font=FONT, height=0.06, wrapWidth=1.5)
    stim.draw()
    win.flip()
    event.clearEvents()
    while True:
        keys = event.waitKeys(keyList=[KEY_PROCEED, KEY_QUIT])
        if KEY_QUIT in keys:
            graceful_quit(None, None, [], win, abort=True)
        if KEY_PROCEED in keys:
            break


def show_break(win: visual.Window, block_idx: int, acc: float, mean_rt: Optional[float]) -> None:
    template = _load_text(INSTR_BREAK_FILE, "End of block {{BLOCK}}. Accuracy: {{ACC}}%\n")
    body = template.replace("{{BLOCK}}", str(block_idx)).replace("{{ACC}}", f"{acc*100:.1f}")
    if mean_rt is not None:
        body += f"Mean RT (correct): {mean_rt:.0f} ms\n"
    body += "\nPress ENTER/RETURN to continue."
    stim = visual.TextStim(win, text=body, color=TEXT_COLOR, font=FONT, height=0.06, wrapWidth=1.5)
    stim.draw()
    win.flip()
    event.clearEvents()
    while True:
        keys = event.waitKeys(keyList=[KEY_PROCEED, KEY_QUIT])
        if KEY_QUIT in keys:
            graceful_quit(None, None, [], win, abort=True)
        if KEY_PROCEED in keys:
            break


def show_thanks(win: visual.Window) -> None:
    text = _load_text(INSTR_THANKS_FILE, "Thank you!")
    stim = visual.TextStim(win, text=text, color=TEXT_COLOR, font=FONT, height=0.08)
    stim.draw()
    win.flip()
    send_marker(MARK_THANK_YOU, {"event": "thank_you"})
    core.wait(1.5)


def show_save_and_exit_prompt(win: visual.Window) -> None:
    """Final screen: require ENTER/RETURN to save and exit; ESC is ignored here."""
    msg = _load_text(INSTR_SAVE_EXIT_FILE, "Task complete. Press ENTER/RETURN to save and exit.")
    stim = visual.TextStim(win, text=msg, color=TEXT_COLOR, font=FONT, height=0.06, wrapWidth=1.5)
    stim.draw()
    win.flip()
    event.clearEvents()
    # Only accept ENTER here; ignore ESC
    while True:
        keys = event.waitKeys(keyList=[KEY_PROCEED])
        if KEY_PROCEED in keys:
            break


def run_practice(win: visual.Window, n_back: int, practice_trials: int) -> Tuple[float, Optional[float]]:
    plans = generate_sequence(
        n_back,
        practice_trials,
        target_rate=PRACTICE_TARGET_RATE,
        lure_n_minus_1_rate=CFG_LURE_NM1 if PRACTICE_HAS_LURES else 0.0,
        lure_n_plus_1_rate=CFG_LURE_NP1 if PRACTICE_HAS_LURES else 0.0,
        max_consec_targets=CFG_MAX_CONSEC_TARGETS,
        iti_range_ms=CFG_ITI_RANGE_MS,
        include_lures=PRACTICE_HAS_LURES,
    )
    accs: List[int] = []
    rts: List[float] = []
    _ = run_block(win, block_idx=0, n_back=n_back, plans=plans, is_practice=True,
                  accs_out=accs, rts_out=rts, rows_out=None)
    acc = sum(accs) / len(accs) if accs else 0.0
    mean_rt = (sum(rts) / len(rts)) if rts else None

    # Feedback
    passed = acc >= PRACTICE_PASS_ACC
    if passed:
        template = _load_text(INSTR_PRACTICE_PASS_FILE, "Practice complete. Accuracy: {{ACC}}% (criterion: {{CRIT}}%).\nYou passed the criterion. Press ENTER/RETURN to continue.")
    else:
        template = _load_text(INSTR_PRACTICE_FAIL_FILE, "Practice complete. Accuracy: {{ACC}}% (criterion: {{CRIT}}%).\nYou did not reach the criterion. Press ENTER/RETURN to repeat practice.")
    msg = template.replace("{{ACC}}", f"{acc*100:.1f}").replace("{{CRIT}}", f"{PRACTICE_PASS_ACC*100:.0f}")
    if mean_rt is not None:
        msg += f"\nMean RT (correct): {mean_rt:.0f} ms"
    stim = visual.TextStim(win, text=msg, color=TEXT_COLOR, font=FONT, height=0.06, wrapWidth=1.5)
    stim.draw()
    win.flip()
    event.clearEvents()
    while True:
        keys = event.waitKeys(keyList=[KEY_PROCEED, KEY_QUIT])
        if KEY_QUIT in keys:
            graceful_quit(None, None, [], win, abort=True)
        if KEY_PROCEED in keys:
            break
    return acc, mean_rt


def show_task_headsup(win: visual.Window, n_back: int) -> None:
    base = _load_text(INSTR_TASK_FILE, "Main task is about to begin. Press ENTER/RETURN to start the task.")
    txt = base.replace("{{N}}", str(n_back)) + "\n\n(Press ENTER/RETURN to start the task)"
    stim = visual.TextStim(win, text=txt, color=TEXT_COLOR, font=FONT, height=0.06, wrapWidth=1.5)
    stim.draw()
    win.flip()
    event.clearEvents()
    while True:
        keys = event.waitKeys(keyList=[KEY_PROCEED, KEY_QUIT])
        if KEY_QUIT in keys:
            graceful_quit(None, None, [], win, abort=True)
        if KEY_PROCEED in keys:
            break


def _ensure_stims(win: visual.Window) -> None:
    global STIM_LETTER, STIM_FIXATION
    if STIM_LETTER is None:
        STIM_LETTER = visual.TextStim(win, text="", color=TEXT_COLOR, font=FONT, height=FONT_HEIGHT)
    if STIM_FIXATION is None:
        STIM_FIXATION = visual.TextStim(win, text="+", color=TEXT_COLOR, font=FONT, height=FIXATION_HEIGHT)


def _draw_fixation(win: visual.Window) -> None:
    _ensure_stims(win)
    assert STIM_FIXATION is not None
    STIM_FIXATION.draw()


def _draw_stimulus(win: visual.Window, letter: str) -> None:
    _ensure_stims(win)
    assert STIM_LETTER is not None
    STIM_LETTER.text = letter
    STIM_LETTER.draw()


def _flip_for_ms(win: visual.Window, duration_ms: int, draw_fn=None) -> None:
    """Flip each frame for duration_ms, optionally drawing via draw_fn before each flip."""
    clk = core.Clock(); clk.reset()
    while True:
        if draw_fn is not None:
            draw_fn()
        win.flip()
        if clk.getTime() * 1000.0 >= duration_ms:
            break


def _marker_code_for_stim(is_target: int, lure_type: str) -> int:
    if is_target:
        return MARK_STIM_TARGET
    if lure_type == "n-1":
        return MARK_STIM_LURE_N_MINUS_1
    if lure_type == "n+1":
        return MARK_STIM_LURE_N_PLUS_1
    return MARK_STIM_NONTARGET


def run_block(win: visual.Window, block_idx: int, n_back: int, plans: List[TrialPlan],
              is_practice: bool, accs_out: List[int], rts_out: List[float],
              rows_out: Optional[List[Dict]]) -> Tuple[float, Optional[float]]:
    # Start marker
    send_marker(MARK_BLOCK_START, {"event": "block_start", "n_back": n_back, "block_idx": block_idx})

    # Use hardware keyboard when available for better timing
    kb = None
    if _HAVE_HW_KB:
        try:
            kb = hw_keyboard.Keyboard(clock=core.Clock())
        except Exception:
            kb = None

    # Trial loop
    correct_count = 0
    rt_list: List[float] = []

    for t_idx, plan in enumerate(plans, start=1):
        # Fixation (frame-synced)
        def _draw_fix():
            _draw_fixation(win)
        send_marker(MARK_FIXATION_ONSET, {"event": "fixation_onset", "block_idx": block_idx, "trial_idx": t_idx})
        _flip_for_ms(win, FIXATION_DUR_MS, draw_fn=_draw_fix)

        # Stimulus
        _draw_stimulus(win, plan.stimulus)
        # Prepare response clock aligned with the stimulus flip
        resp_clock = core.Clock()
        win.callOnFlip(resp_clock.reset)
        if _HAVE_HW_KB and kb is not None:
            kb.clock = resp_clock
            kb.clearEvents()
        stim_onset = win.flip()
        stim_marker = _marker_code_for_stim(plan.is_target, plan.lure_type)
        send_marker(stim_marker, {
            "event": "stimulus_onset",
            "block_idx": block_idx,
            "trial_idx": t_idx,
            "is_target": plan.is_target,
            "lure_type": plan.lure_type,
            "stimulus": plan.stimulus,
        })

        # Response collection
        got_response = False
        resp_key = None
        rt_ms: Optional[float] = None

        # Present for STIM_DUR_MS, then blank until RESP_WINDOW_MS
        while True:
            now_ms = resp_clock.getTime() * 1000.0
            if now_ms >= RESP_WINDOW_MS:
                break
            if _HAVE_HW_KB and kb is not None:
                keys = kb.getKeys(keyList=[KEY_RESPONSE, KEY_QUIT], waitRelease=False, clear=False)
                if keys and not got_response:
                    k = keys[0]
                    name = k.name
                    if name == KEY_QUIT:
                        graceful_quit(None, None, rows_out if rows_out is not None else [], win, abort=True)
                    got_response = True
                    resp_key = name
                    rt_ms = (k.rt or 0.0) * 1000.0
                    send_marker(MARK_RESPONSE_REGISTERED, {
                        "event": "response_registered",
                        "block_idx": block_idx,
                        "trial_idx": t_idx,
                        "key": name,
                        "rt_ms": rt_ms,
                    })
            else:
                keys = event.getKeys(keyList=[KEY_RESPONSE, KEY_QUIT], timeStamped=resp_clock)
                if keys and not got_response:
                    for k, t in keys:
                        if k == KEY_QUIT:
                            graceful_quit(None, None, rows_out if rows_out is not None else [], win, abort=True)
                        if k:
                            got_response = True
                            resp_key = k
                            rt_ms = t * 1000.0
                            send_marker(MARK_RESPONSE_REGISTERED, {
                                "event": "response_registered",
                                "block_idx": block_idx,
                                "trial_idx": t_idx,
                                "key": k,
                                "rt_ms": rt_ms,
                            })
                            break
            # After STIM_DUR_MS, clear screen but keep collecting
            if now_ms >= STIM_DUR_MS:
                win.flip()  # blank
            else:
                _draw_stimulus(win, plan.stimulus)
                win.flip()

        # Score
        is_space = (resp_key == KEY_RESPONSE)
        correct = int((plan.is_target == 1 and is_space) or (plan.is_target == 0 and not is_space))
        if correct:
            correct_count += 1
        accs_out.append(correct)
        if correct and rt_ms is not None:
            rts_out.append(rt_ms)

        # Row output
        if rows_out is not None:
            row = {
                "participant_id": CURRENT_PARTICIPANT,
                "session_timestamp": SESSION_TS,
                "block_idx": block_idx,
                "trial_idx": t_idx,
                "n_back": n_back,
                "stimulus": plan.stimulus,
                "is_target": plan.is_target,
                "lure_type": plan.lure_type,
                "iti_ms": plan.iti_ms,
                "stim_onset_time": f"{stim_onset:.6f}",
                "response_key": resp_key or "",
                "rt_ms": f"{rt_ms:.2f}" if rt_ms is not None else "",
                "correct": correct,
                "marker_code_stim": stim_marker,
                "marker_code_resp": MARK_RESPONSE_REGISTERED if got_response else "",
            }
            rows_out.append(row)

    # ITI (frame-synced blank)
    _flip_for_ms(win, plan.iti_ms)

    # End marker
    send_marker(MARK_BLOCK_END, {"event": "block_end", "block_idx": block_idx})

    acc = correct_count / len(plans) if plans else 0.0
    mean_rt = (sum(rt_list) / len(rt_list)) if rt_list else (sum(rts_out) / len(rts_out) if rts_out else None)
    return acc, mean_rt


# =========================
# Graceful quit and CSV
# =========================

CURRENT_PARTICIPANT = ""
SESSION_TS = ""
CSV_PATH = ""
ABORT_WITHOUT_SAVE = False
META_PATH = ""


def graceful_quit(writer: Optional[csv.DictWriter], f: Optional[object], rows: List[Dict], win: Optional[visual.Window], abort: bool = False) -> None:
    """Exit the task. If abort is True (e.g., ESC pressed), don't save and delete any CSV file."""
    global ABORT_WITHOUT_SAVE
    ABORT_WITHOUT_SAVE = ABORT_WITHOUT_SAVE or abort

    # Only save when not aborting
    if not ABORT_WITHOUT_SAVE:
        try:
            if writer is not None and f is not None and rows:
                writer.writerows(rows)
                f.flush()
        except Exception:
            pass
    # Close file handle if present
    try:
        if f is not None:
            f.close()
    except Exception:
        pass
    # If aborting, remove CSV/metadata files if they exist
    if ABORT_WITHOUT_SAVE:
        try:
            if CSV_PATH and os.path.exists(CSV_PATH):
                os.remove(CSV_PATH)
        except Exception:
            pass
        try:
            if META_PATH and os.path.exists(META_PATH):
                os.remove(META_PATH)
        except Exception:
            pass
    # Close window
    try:
        if win is not None:
            win.close()
    except Exception:
        pass
    core.quit()


# =========================
# Main
# =========================

def main(argv: Optional[List[str]] = None) -> int:
    global CURRENT_PARTICIPANT, SESSION_TS, CSV_PATH, META_PATH

    parser = argparse.ArgumentParser(description="PsychoPy N-back Task")
    parser.add_argument("--participant", "-p", default="anon", help="Participant ID")
    parser.add_argument("--n-back", type=int, default=N_BACK_DEFAULT, help="N for N-back (1, 2, 3)")
    parser.add_argument("--blocks", type=int, default=N_BLOCKS, help="Number of blocks")
    parser.add_argument("--trials", type=int, default=TRIALS_PER_BLOCK, help="Trials per block")
    parser.add_argument("--no-practice", action="store_true", help="Skip practice")
    parser.add_argument("--practice-trials", type=int, default=PRACTICE_TRIALS, help="Number of practice trials")
    # New controls
    parser.add_argument("--iti-min", type=int, default=ITI_JITTER_RANGE_MS[0], help="Minimum ITI jitter in ms")
    parser.add_argument("--iti-max", type=int, default=ITI_JITTER_RANGE_MS[1], help="Maximum ITI jitter in ms")
    parser.add_argument("--lure-nminus1", type=float, default=LURE_N_MINUS_1_RATE, help="Probability of n-1 lures per non-target trial")
    parser.add_argument("--lure-nplus1", type=float, default=LURE_N_PLUS_1_RATE, help="Probability of n+1 lures per non-target trial")
    parser.add_argument("--target-rate", type=float, default=TARGET_RATE, help="Target rate (0-1) per block")
    parser.add_argument("--max-consec-targets", type=int, default=MAX_CONSEC_TARGETS_DEFAULT, help="Maximum allowed consecutive targets")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    # Default to full-screen; allow windowed mode for debugging
    parser.add_argument("--windowed", action="store_true", help="Run windowed for debugging (default: fullscreen)")
    args = parser.parse_args(argv)

    n_back = max(1, min(3, int(args.n_back)))
    n_blocks = int(args.blocks)
    trials_per_block = int(args.trials)
    CURRENT_PARTICIPANT = safe_filename(str(args.participant)) or "anon"
    SESSION_TS = timestamp()

    # Configure RNG
    if args.seed is not None:
        random.seed(int(args.seed))

    # Apply CLI config
    global CFG_TARGET_RATE, CFG_LURE_NM1, CFG_LURE_NP1, CFG_MAX_CONSEC_TARGETS, CFG_ITI_RANGE_MS
    CFG_TARGET_RATE = float(max(0.0, min(1.0, args.target_rate)))
    CFG_LURE_NM1 = float(max(0.0, min(1.0, args.lure_nminus1)))
    CFG_LURE_NP1 = float(max(0.0, min(1.0, args.lure_nplus1)))
    CFG_MAX_CONSEC_TARGETS = max(1, int(args.max_consec_targets))
    iti_min = max(0, int(args.iti_min))
    iti_max = max(iti_min, int(args.iti_max))
    CFG_ITI_RANGE_MS = (iti_min, iti_max)

    make_data_dir(DATA_DIR)
    csv_name = f"nback_{CURRENT_PARTICIPANT}_{SESSION_TS}.csv"
    CSV_PATH = os.path.join(DATA_DIR, csv_name)
    META_PATH = os.path.join(DATA_DIR, f"nback_{CURRENT_PARTICIPANT}_{SESSION_TS}.meta.json")

    # Configure window
    fullscr = not bool(args.windowed)
    win = visual.Window(size=(1280, 720), color=BACKGROUND_COLOR, units="height", fullscr=fullscr, allowGUI=False)
    try:
        win.mouseVisible = False
    except Exception:
        pass
    # Ensure frame-syncing
    try:
        win.waitBlanking = True
    except Exception:
        pass

    # Detect and report display refresh rate
    refresh_hz = None
    try:
        refresh_hz = win.getActualFrameRate(nIdentical=20, nMaxFrames=240, nWarmUpFrames=20, threshold=1)
    except Exception:
        refresh_hz = None
    if refresh_hz:
        print(f"Detected display refresh: {refresh_hz:.3f} Hz (frame ≈ {1000.0/refresh_hz:.2f} ms)")
    else:
        print("Warning: Could not detect display refresh rate; proceeding without it.")

    # Consent -> Instructions -> Practice heads up
    show_consent(win)
    show_instructions(win, n_back)
    show_practice_headsup(win)

    # Prepare CSV
    fieldnames = [
        "participant_id", "session_timestamp", "block_idx", "trial_idx",
        "n_back", "stimulus", "is_target", "lure_type", "iti_ms",
        "stim_onset_time", "response_key", "rt_ms", "correct",
        "marker_code_stim", "marker_code_resp",
    ]

    f = open(CSV_PATH, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    # Write sidecar metadata JSON for reproducibility (includes display refresh and fullscreen)
    try:
        meta = {
            "participant_id": CURRENT_PARTICIPANT,
            "session_timestamp": SESSION_TS,
            "n_back": n_back,
            "blocks": n_blocks,
            "trials_per_block": trials_per_block,
            "practice_trials": int(args.practice_trials),
            "practice_target_rate": PRACTICE_TARGET_RATE,
            "practice_has_lures": PRACTICE_HAS_LURES,
            "target_rate": CFG_TARGET_RATE,
            "lure_nminus1_rate": CFG_LURE_NM1,
            "lure_nplus1_rate": CFG_LURE_NP1,
            "max_consec_targets": CFG_MAX_CONSEC_TARGETS,
            "iti_ms_range": list(CFG_ITI_RANGE_MS),
            "seed": args.seed,
            "letters": LETTERS,
            "psychopy_version": None,
            "display_refresh_hz": refresh_hz,
            "window_fullscreen": bool(fullscr),
        }
        try:
            import psychopy
            meta["psychopy_version"] = getattr(psychopy, "__version__", None)
        except Exception:
            pass
        with open(META_PATH, "w", encoding="utf-8") as mf:
            json.dump(meta, mf, indent=2)
    except Exception:
        pass

    all_rows: List[Dict] = []
    overall_accs: List[int] = []
    overall_rts: List[float] = []

    # Practice loop with pass/fail
    practice_trials = max(1, int(args.practice_trials))
    if not args.no_practice and practice_trials > 0:
        while True:
            acc, _ = run_practice(win, n_back, practice_trials)
            if acc >= PRACTICE_PASS_ACC:
                break
            # If failed, re-show very brief reminder before repeating
            show_practice_headsup(win)

    # Heads-up before main task
    show_task_headsup(win, n_back)

    # Blocks
    for b in range(1, n_blocks + 1):
        plans = generate_sequence(
            n_back,
            trials_per_block,
            target_rate=CFG_TARGET_RATE,
            lure_n_minus_1_rate=CFG_LURE_NM1,
            lure_n_plus_1_rate=CFG_LURE_NP1,
            max_consec_targets=CFG_MAX_CONSEC_TARGETS,
            iti_range_ms=CFG_ITI_RANGE_MS,
            include_lures=True,
        )
        block_accs: List[int] = []
        block_rts: List[float] = []

        acc, mean_rt = run_block(win, block_idx=b, n_back=n_back, plans=plans,
                                 is_practice=False, accs_out=block_accs, rts_out=block_rts,
                                 rows_out=all_rows)

        # Persist rows periodically (per block)
        if all_rows:
            writer.writerows(all_rows)
            f.flush()
            overall_accs.extend(block_accs)
            overall_rts.extend([rt for rt in block_rts if rt is not None])
            all_rows.clear()

        # Break screen
        if b < n_blocks:
            show_break(win, b, acc, mean_rt)

    # Finish
    show_thanks(win)
    # Require explicit save/exit confirmation (ENTER) and avoid ESC here
    show_save_and_exit_prompt(win)

    # Final flush and close
    try:
        if all_rows:
            writer.writerows(all_rows)
        f.flush()
    finally:
        f.close()

    try:
        win.close()
    except Exception:
        pass

    # Summary
    total_trials = n_blocks * trials_per_block
    overall_acc = sum(overall_accs) / total_trials if total_trials else 0.0
    # Accuracy by target/non-target requires re-reading CSV rows; quick pass
    target_correct = 0
    target_total = 0
    nontarget_correct = 0
    nontarget_total = 0

    try:
        with open(CSV_PATH, "r", encoding="utf-8") as rf:
            r = csv.DictReader(rf)
            for row in r:
                itarget = int(row["is_target"]) if row["is_target"] != "" else 0
                corr = int(row["correct"]) if row["correct"] != "" else 0
                if itarget == 1:
                    target_total += 1
                    if corr == 1:
                        target_correct += 1
                else:
                    nontarget_total += 1
                    if corr == 1:
                        nontarget_correct += 1
    except Exception:
        pass

    target_acc = (target_correct / target_total) if target_total else 0.0
    nontarget_acc = (nontarget_correct / nontarget_total) if nontarget_total else 0.0
    mean_rt = (sum(overall_rts) / len(overall_rts)) if overall_rts else None

    print("\n===== Session Summary =====")
    print(f"File: {CSV_PATH}")
    print(f"Trials: {total_trials}")
    print(f"Overall accuracy: {overall_acc*100:.1f}%")
    print(f"Target accuracy: {target_acc*100:.1f}% (n={target_total})")
    print(f"Non-target accuracy: {nontarget_acc*100:.1f}% (n={nontarget_total})")
    if mean_rt is not None:
        print(f"Mean RT (correct): {mean_rt:.0f} ms")
    print("===========================\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        raise e
    except Exception as e:
        # Ensure graceful close if window exists
        try:
            core.quit()
        except Exception:
            pass
        raise
