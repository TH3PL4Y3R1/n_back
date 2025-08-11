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
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from psychopy import core, visual, event, gui

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
ITI_JITTER_RANGE_MS = (500, 900)  # inclusive bounds for uniform jitter

# Sequence constraints
TARGET_RATE = 0.30
ALLOW_ADJACENT_TARGETS = False
LURE_N_MINUS_1_RATE = 0.05
LURE_N_PLUS_1_RATE = 0.05
MAX_IDENTICAL_RUN = 2  # cap identical-letter runs unless needed for target/lure
MAX_ATTEMPTS = 300

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

# Markers / Triggers
ENABLE_MARKERS = False  # set to True and configure one of the commented examples below

# Marker codes
MARK_CONSENT_SHOWN = 10
MARK_BLOCK_START = 20
MARK_FIXATION_ONSET = 30
# Stimulus onset codes differentiated by trial type
MARK_STIM_TARGET = 41
MARK_STIM_NONTARGET = 42
MARK_STIM_LURE_N_MINUS_1 = 43
MARK_STIM_LURE_N_PLUS_1 = 44
MARK_RESPONSE_REGISTERED = 50
MARK_BLOCK_END = 70
MARK_THANK_YOU = 90

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


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
# Marker plumbing
# =========================

# You can enable markers by setting ENABLE_MARKERS = True and implementing one of the
# commented examples below. By default, send_marker is a no-op.

# --- LSL EXAMPLE (COMMENTED OUT) ---
# _lsl_outlet = None
# def _get_lsl_outlet():
#     global _lsl_outlet
#     if _lsl_outlet is None:
#         from pylsl import StreamInfo, StreamOutlet
#         info = StreamInfo(name='Markers', type='Markers', channel_count=1,
#                           nominal_srate=0, channel_format='int32', source_id='nback-markers')
#         _lsl_outlet = StreamOutlet(info)
#     return _lsl_outlet

# --- SERIAL EXAMPLE (COMMENTED OUT) ---
# _serial_port = None
# def _get_serial_port():
#     global _serial_port
#     if _serial_port is None:
#         import serial
#         _serial_port = serial.Serial('/dev/ttyUSB0', 115200, timeout=0)
#     return _serial_port

# --- PARALLEL EXAMPLE (COMMENTED OUT) ---
# _parallel_port = None
# def _get_parallel_port():
#     global _parallel_port
#     if _parallel_port is None:
#         from psychopy import parallel
#         _parallel_port = parallel.ParallelPort(address=0x0378)
#     return _parallel_port


def send_marker(code: int, info: Optional[dict] = None) -> None:
    """Send a marker if ENABLE_MARKERS is True; otherwise no-op.

    info is an optional dictionary of context (block_idx, n_back, etc.).
    """
    if not ENABLE_MARKERS:
        return

    # Choose exactly one integration method and uncomment that block.

    # --- LSL send (COMMENTED OUT) ---
    # outlet = _get_lsl_outlet()
    # outlet.push_sample([int(code)])

    # --- Serial send (COMMENTED OUT) ---
    # ser = _get_serial_port()
    # ser.write(bytes([int(code) & 0xFF]))

    # --- Parallel port send (COMMENTED OUT) ---
    # p = _get_parallel_port()
    # p.setData(int(code) & 0xFF)
    # core.wait(0.005)
    # p.setData(0)


# =========================
# Sequence generation
# =========================

@dataclass
class TrialPlan:
    stimulus: str
    is_target: int  # 0/1
    lure_type: str  # 'none' | 'n-1' | 'n+1'
    iti_ms: int


def _choose_letter(candidates: List[str], freq: Dict[str, int], soft_balance: bool = True) -> str:
    if not candidates:
        # Fallback to full set if constraints over-restrict
        candidates = LETTERS[:]
    if soft_balance:
        # Inverse frequency weighting
        max_count = max(freq.values()) if freq else 1
        weights = []
        for c in candidates:
            w = (max_count - freq.get(c, 0) + 1)
            weights.append(max(w, 1))
        total = float(sum(weights))
        probs = [w / total for w in weights]
        r = random.random()
        acc = 0.0
        for c, p in zip(candidates, probs):
            acc += p
            if r <= acc:
                return c
        return candidates[-1]
    return random.choice(candidates)


def _valid_run_limit(seq: List[str], candidate: str, max_run: int) -> bool:
    if max_run <= 0:
        return True
    run_len = 1
    i = len(seq) - 1
    while i >= 0 and seq[i] == candidate:
        run_len += 1
        i -= 1
    return run_len <= max_run


def generate_sequence(n_back: int, n_trials: int, target_rate: float = TARGET_RATE,
                      lure_n_minus_1_rate: float = LURE_N_MINUS_1_RATE,
                      lure_n_plus_1_rate: float = LURE_N_PLUS_1_RATE,
                      allow_adjacent_targets: bool = ALLOW_ADJACENT_TARGETS,
                      max_identical_run: int = MAX_IDENTICAL_RUN,
                      iti_range_ms: Tuple[int, int] = ITI_JITTER_RANGE_MS,
                      max_attempts: int = MAX_ATTEMPTS,
                      soft_balance_initial: bool = True,
                      include_lures: bool = True) -> List[TrialPlan]:
    """Generate a constrained n-back sequence returning per-trial plans.

    Enforces:
    - No targets in first N trials
    - Approx target rate with ±1 trial tolerance
    - Max consecutive targets = 1 unless allowed
    - Lures (n-1 and n+1) by independent probabilities, never double-counted as targets
    - Avoid accidental immediate repeats for N>1 unless target/lure
    - Cap identical-letter runs
    - Soft balance letter frequency
    """
    desired_targets = round(target_rate * n_trials)
    tolerance = 1

    for attempt in range(1, max_attempts + 1):
        seq: List[str] = []
        is_target_flags: List[int] = []
        lure_types: List[str] = []
        freqs: Dict[str, int] = {c: 0 for c in LETTERS}
        targets_placed = 0
        last_was_target = False

        for i in range(n_trials):
            # Decide planned ITI now
            iti_ms = random.randint(iti_range_ms[0], iti_range_ms[1])

            can_be_target = (i >= n_back and (ALLOW_ADJACENT_TARGETS or not last_was_target)) and (targets_placed < desired_targets + tolerance)

            # Decide trial type priority: target > lures > non-target
            planned_type = "non-target"
            planned_lure_type = "none"

            # Target decision (don't allow in first N)
            if can_be_target and i >= n_back and targets_placed < desired_targets + tolerance:
                # Also avoid violating max_identical_run if choosing target
                target_letter = seq[i - n_back]
                if _valid_run_limit(seq, target_letter, max_identical_run):
                    planned_type = "target"

            # Lure decisions if not target
            if planned_type != "target" and include_lures:
                # n-1 lure: current equals i-(n-1), and must not equal i-n (which would be target)
                can_n_minus_1 = (i >= n_back - 1) and (n_back - 1) > 0 and random.random() < lure_n_minus_1_rate
                if can_n_minus_1:
                    letter_nm1 = seq[i - (n_back - 1)] if (n_back - 1) > 0 else None
                    letter_n = seq[i - n_back] if i >= n_back else None
                    if letter_nm1 and (letter_n is None or letter_nm1 != letter_n) and _valid_run_limit(seq, letter_nm1, max_identical_run):
                        planned_type = "lure"
                        planned_lure_type = "n-1"

                # n+1 lure: current equals i-(n+1), but must not equal i-n (target)
                if planned_type == "non-target":
                    can_n_plus_1 = (i >= n_back + 1) and random.random() < lure_n_plus_1_rate
                    if can_n_plus_1:
                        letter_np1 = seq[i - (n_back + 1)]
                        letter_n = seq[i - n_back] if i >= n_back else None
                        if (letter_np1 is not None) and (letter_n is None or letter_np1 != letter_n) and _valid_run_limit(seq, letter_np1, max_identical_run):
                            planned_type = "lure"
                            planned_lure_type = "n+1"

            # Construct candidate set and choose letter
            if planned_type == "target":
                letter = seq[i - n_back]
            elif planned_type == "lure" and planned_lure_type == "n-1":
                letter = seq[i - (n_back - 1)]
                # Ensure not accidentally target
                if i >= n_back and letter == seq[i - n_back]:
                    planned_type = "non-target"
                    planned_lure_type = "none"
            elif planned_type == "lure" and planned_lure_type == "n+1":
                letter = seq[i - (n_back + 1)]
                if i >= n_back and letter == seq[i - n_back]:
                    planned_type = "non-target"
                    planned_lure_type = "none"
            else:
                # Non-target selection: must not create accidental target when N>1
                candidates = [c for c in LETTERS]
                if i >= n_back:
                    avoid = seq[i - n_back]
                    candidates = [c for c in candidates if c != avoid]
                # Avoid immediate repeats unless needed for target/lure
                if seq:
                    last = seq[-1]
                    if last in candidates and not _valid_run_limit(seq, last, max_identical_run - 1):
                        candidates = [c for c in candidates if c != last]
                letter = _choose_letter(candidates, freqs, soft_balance=soft_balance_initial)

            # Final guard against run limit violations
            if not _valid_run_limit(seq, letter, max_identical_run):
                # fallback pick
                cands = [c for c in LETTERS if _valid_run_limit(seq, c, max_identical_run)]
                if i >= n_back:
                    cands = [c for c in cands if c != seq[i - n_back]]
                if seq:
                    last = seq[-1]
                    if last in cands and not _valid_run_limit(seq, last, max_identical_run - 1):
                        cands = [c for c in cands if c != last]
                letter = _choose_letter(cands, freqs, soft_balance=soft_balance_initial)

            # Apply and update flags
            seq.append(letter)
            freqs[letter] = freqs.get(letter, 0) + 1

            if planned_type == "target" and i >= n_back and letter == seq[i - n_back]:
                is_target_flags.append(1)
                last_was_target = True
                targets_placed += 1
                lure_types.append("none")
            else:
                is_target_flags.append(0)
                last_was_target = False
                # Verify lure validity; ensure no double counting as target
                if planned_lure_type.startswith("n-") or planned_lure_type.startswith("n+"):
                    lure_types.append(planned_lure_type)
                else:
                    # Re-check if we accidentally made a lure; conservative none
                    lure_types.append("none")

        # Validate constraints
        # 1) No targets in first N trials
        if any(is_target_flags[i] == 1 for i in range(0, min(n_back, n_trials))):
            continue
        # 2) Target rate tolerance
        if not (desired_targets - tolerance <= sum(is_target_flags) <= desired_targets + tolerance):
            continue
        # 3) Max consecutive targets
        if not allow_adjacent_targets:
            consec = 0
            bad = False
            for f in is_target_flags:
                if f == 1:
                    consec += 1
                    if consec > 1:
                        bad = True
                        break
                else:
                    consec = 0
            if bad:
                continue
        # 5) Avoid accidental immediate repeats when N>1 unless target/lure
        if n_back > 1:
            bad_repeat = False
            for i in range(1, n_trials):
                if seq[i] == seq[i - 1] and is_target_flags[i] == 0 and lure_types[i] == "none":
                    # allow if it was needed by constraints? We cap by run limit; still avoid here
                    if MAX_IDENTICAL_RUN <= 1:
                        bad_repeat = True
                        break
            if bad_repeat:
                continue
        # 6) Cap identical-letter runs
        run = 1
        too_long = False
        for i in range(1, n_trials):
            if seq[i] == seq[i - 1]:
                run += 1
                if run > max_identical_run and is_target_flags[i] == 0 and lure_types[i] == "none":
                    too_long = True
                    break
            else:
                run = 1
        if too_long:
            continue

        # Success: build TrialPlan list
        plans: List[TrialPlan] = []
        for i in range(n_trials):
            iti_ms = random.randint(iti_range_ms[0], iti_range_ms[1])
            plans.append(TrialPlan(
                stimulus=seq[i],
                is_target=is_target_flags[i],
                lure_type=lure_types[i],
                iti_ms=iti_ms,
            ))
        return plans

    # If reached here, relax soft constraints and try a last time deterministically
    return generate_sequence(n_back, n_trials, target_rate, lure_n_minus_1_rate, lure_n_plus_1_rate,
                             allow_adjacent_targets, max_identical_run, iti_range_ms, 1,
                             soft_balance_initial=False, include_lures=include_lures)


# =========================
# Rendering / Task flow
# =========================

def show_consent(win: visual.Window) -> None:
    txt = "PLACEHOLDER\n\nPress ENTER/RETURN to continue."
    stim = visual.TextStim(win, text=txt, color=TEXT_COLOR, font=FONT, height=0.06, wrapWidth=1.5)
    stim.draw()
    win.flip()
    send_marker(MARK_CONSENT_SHOWN, {"event": "consent_shown"})
    # Wait for return
    event.clearEvents()
    while True:
        keys = event.waitKeys(keyList=[KEY_PROCEED, KEY_QUIT])
        if KEY_QUIT in keys:
            graceful_quit(None, None, [], win, abort=True)
        if KEY_PROCEED in keys:
            break


def show_instructions(win: visual.Window, n_back: int) -> None:
    lines = [
        f"Welcome to the {n_back}-back task.",
        "You will see a stream of letters.",
        f"Press SPACE when the current letter matches the one from {n_back} trial(s) before.",
        "If it doesn't match, do not press any key.",
        "Respond as quickly and accurately as possible.",
        "Press ENTER/RETURN to begin practice.",
    ]
    txt = "\n\n".join(lines)
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


def show_practice_headsup(win: visual.Window) -> None:
    msg = "Practice is about to begin.\nTry to reach the accuracy criterion to proceed.\n\nPress ENTER/RETURN to start."
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
    msg = f"End of block {block_idx}.\nAccuracy: {acc*100:.1f}%\n"
    if mean_rt is not None:
        msg += f"Mean RT (correct): {mean_rt:.0f} ms\n"
    msg += "\nPress ENTER/RETURN to continue."
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


def show_thanks(win: visual.Window) -> None:
    stim = visual.TextStim(win, text="Thank you!", color=TEXT_COLOR, font=FONT, height=0.08)
    stim.draw()
    win.flip()
    send_marker(MARK_THANK_YOU, {"event": "thank_you"})
    core.wait(1.5)


def show_save_and_exit_prompt(win: visual.Window) -> None:
    """Final screen: require ENTER/RETURN to save and exit; ESC is ignored here."""
    msg = "Task complete.\n\nPress ENTER/RETURN to save and exit."
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
    plans = generate_sequence(n_back, practice_trials, target_rate=PRACTICE_TARGET_RATE,
                              include_lures=PRACTICE_HAS_LURES)
    accs: List[int] = []
    rts: List[float] = []
    _ = run_block(win, block_idx=0, n_back=n_back, plans=plans, is_practice=True,
                  accs_out=accs, rts_out=rts, rows_out=None)
    acc = sum(accs) / len(accs) if accs else 0.0
    mean_rt = (sum(rts) / len(rts)) if rts else None

    # Feedback
    passed = acc >= PRACTICE_PASS_ACC
    msg = f"Practice complete.\nAccuracy: {acc*100:.1f}% (criterion: {PRACTICE_PASS_ACC*100:.0f}%)\n"
    if mean_rt is not None:
        msg += f"Mean RT (correct): {mean_rt:.0f} ms\n"
    if passed:
        msg += "\nYou passed the criterion. Press ENTER/RETURN to continue."
    else:
        msg += "\nYou did not reach the criterion. Press ENTER/RETURN to repeat practice."
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
    lines = [
        "Main task is about to begin.",
        f"Remember: Press SPACE when the letter matches the one from {n_back} trial(s) ago.",
        "Try to be both fast and accurate.",
        "\nPress ENTER/RETURN to start the task.",
    ]
    txt = "\n\n".join(lines)
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


def _draw_fixation(win: visual.Window) -> None:
    fix = visual.TextStim(win, text="+", color=TEXT_COLOR, font=FONT, height=FIXATION_HEIGHT)
    fix.draw()


def _draw_stimulus(win: visual.Window, letter: str) -> None:
    stim = visual.TextStim(win, text=letter, color=TEXT_COLOR, font=FONT, height=FONT_HEIGHT)
    stim.draw()


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

    kb = event  # using legacy event for simplicity and stability

    # Trial loop
    correct_count = 0
    rt_list: List[float] = []

    for t_idx, plan in enumerate(plans, start=1):
        # Fixation
        _draw_fixation(win)
        win.flip()
        send_marker(MARK_FIXATION_ONSET, {"event": "fixation_onset", "block_idx": block_idx, "trial_idx": t_idx})
        core.wait(FIXATION_DUR_MS / 1000.0)

        # Stimulus
        _draw_stimulus(win, plan.stimulus)
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
        kb.clearEvents()
        resp_clock = core.Clock()
        resp_clock.reset()
        got_response = False
        resp_key = None
        rt_ms: Optional[float] = None

        # Present for STIM_DUR_MS, then blank until RESP_WINDOW_MS
        while True:
            now_ms = resp_clock.getTime() * 1000.0
            if now_ms >= RESP_WINDOW_MS:
                break
            keys = kb.getKeys(timeStamped=resp_clock)
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

        # ITI
        core.wait(plan.iti_ms / 1000.0)

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
    # If aborting, remove CSV file if it exists
    if ABORT_WITHOUT_SAVE and CSV_PATH:
        try:
            if os.path.exists(CSV_PATH):
                os.remove(CSV_PATH)
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
    global CURRENT_PARTICIPANT, SESSION_TS, CSV_PATH

    parser = argparse.ArgumentParser(description="PsychoPy N-back Task")
    parser.add_argument("--participant", "-p", default="anon", help="Participant ID")
    parser.add_argument("--n-back", type=int, default=N_BACK_DEFAULT, help="N for N-back (1, 2, 3)")
    parser.add_argument("--blocks", type=int, default=N_BLOCKS, help="Number of blocks")
    parser.add_argument("--trials", type=int, default=TRIALS_PER_BLOCK, help="Trials per block")
    parser.add_argument("--no-practice", action="store_true", help="Skip practice")
    parser.add_argument("--practice-trials", type=int, default=PRACTICE_TRIALS, help="Number of practice trials")
    args = parser.parse_args(argv)

    n_back = max(1, min(3, int(args.n_back)))
    n_blocks = int(args.blocks)
    trials_per_block = int(args.trials)
    CURRENT_PARTICIPANT = safe_filename(str(args.participant)) or "anon"
    SESSION_TS = timestamp()

    make_data_dir(DATA_DIR)
    csv_name = f"nback_{CURRENT_PARTICIPANT}_{SESSION_TS}.csv"
    CSV_PATH = os.path.join(DATA_DIR, csv_name)

    # Configure window
    win = visual.Window(size=(1280, 720), color=BACKGROUND_COLOR, units="height", fullscr=False)

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
        plans = generate_sequence(n_back, trials_per_block)
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
