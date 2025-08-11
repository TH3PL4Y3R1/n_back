from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

LETTERS = [c for c in string.ascii_uppercase if c not in {"I", "O", "Q"}]

TARGET_RATE = 0.30
LURE_N_MINUS_1_RATE = 0.05
LURE_N_PLUS_1_RATE = 0.05
MAX_IDENTICAL_RUN = 2
MAX_ATTEMPTS = 300
MAX_CONSEC_TARGETS_DEFAULT = 1
ITI_JITTER_RANGE_MS = (500, 900)

@dataclass
class TrialPlan:
    stimulus: str
    is_target: int
    lure_type: str
    iti_ms: int


def _choose_letter(candidates: List[str], freq: Dict[str, int], soft_balance: bool = True) -> str:
    if not candidates:
        candidates = LETTERS[:]
    if soft_balance:
        max_count = max(freq.values()) if freq else 1
        weights = [(max_count - freq.get(c, 0) + 1) for c in candidates]
        weights = [max(w, 1) for w in weights]
        total = float(sum(weights))
        r = random.random() * total
        acc = 0.0
        for c, w in zip(candidates, weights):
            acc += w
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


def validate_sequence(seq: List[str], is_target_flags: List[int], lure_types: List[str], *,
                      n_back: int, target_rate: float, tolerance: int,
                      max_consec_targets: int) -> Tuple[bool, str]:
    n_trials = len(seq)
    if any(is_target_flags[i] == 1 for i in range(0, min(n_back, n_trials))):
        return False, "Target in first N trials"
    desired_targets = round(target_rate * n_trials)
    total_targets = sum(is_target_flags)
    if not (desired_targets - 1 <= total_targets <= desired_targets + 1):
        return False, f"Target count {total_targets} outside ±1 around {desired_targets}"
    if n_back > 1:
        for i in range(1, n_trials):
            if seq[i] == seq[i - 1] and is_target_flags[i] == 0 and lure_types[i] == "none":
                return False, "Immediate repeat without target/lure"
    for i in range(n_trials):
        lt = lure_types[i]
        if lt == "n-1":
            if not (i >= n_back - 1 and (n_back - 1) > 0):
                return False, "n-1 lure too early"
            if is_target_flags[i] == 1:
                return False, "lure double-counted as target"
            if seq[i] != seq[i - (n_back - 1)]:
                return False, "n-1 lure mismatch"
            if i >= n_back and seq[i] == seq[i - n_back]:
                return False, "n-1 lure equals target"
        elif lt == "n+1":
            if not (i >= n_back + 1):
                return False, "n+1 lure too early"
            if is_target_flags[i] == 1:
                return False, "lure double-counted as target"
            if seq[i] != seq[i - (n_back + 1)]:
                return False, "n+1 lure mismatch"
            if i >= n_back and seq[i] == seq[i - n_back]:
                return False, "n+1 lure equals target"
    consec = 0
    for f in is_target_flags:
        if f == 1:
            consec += 1
            if consec > max_consec_targets:
                return False, f">{max_consec_targets} consecutive targets"
        else:
            consec = 0
    return True, "ok"


def generate_sequence(n_back: int, n_trials: int, *,
                      target_rate: float = TARGET_RATE,
                      lure_n_minus_1_rate: float = LURE_N_MINUS_1_RATE,
                      lure_n_plus_1_rate: float = LURE_N_PLUS_1_RATE,
                      max_consec_targets: int = MAX_CONSEC_TARGETS_DEFAULT,
                      max_identical_run: int = MAX_IDENTICAL_RUN,
                      iti_range_ms: Tuple[int, int] = ITI_JITTER_RANGE_MS,
                      max_attempts: int = MAX_ATTEMPTS,
                      soft_balance_initial: bool = True,
                      include_lures: bool = True) -> List[TrialPlan]:
    tolerance = 1
    desired_targets = round(target_rate * n_trials)

    for _attempt in range(1, max_attempts + 1):
        seq: List[str] = []
        is_target_flags: List[int] = []
        lure_types: List[str] = []
        freqs: Dict[str, int] = {c: 0 for c in LETTERS}
        targets_placed = 0
        consec_target_run = 0

        for i in range(n_trials):
            iti_ms = random.randint(iti_range_ms[0], iti_range_ms[1])
            planned_type = "non-target"
            planned_lure_type = "none"

            can_be_target = (i >= n_back and consec_target_run < max_consec_targets) and (targets_placed < desired_targets + tolerance)
            if can_be_target and i >= n_back and targets_placed < desired_targets + tolerance:
                target_letter = seq[i - n_back]
                if _valid_run_limit(seq, target_letter, max_identical_run):
                    planned_type = "target"

            if planned_type != "target" and include_lures:
                can_n_minus_1 = (i >= n_back - 1) and (n_back - 1) > 0 and random.random() < lure_n_minus_1_rate
                if can_n_minus_1:
                    letter_nm1 = seq[i - (n_back - 1)] if (n_back - 1) > 0 else None
                    letter_n = seq[i - n_back] if i >= n_back else None
                    if letter_nm1 and (letter_n is None or letter_nm1 != letter_n) and _valid_run_limit(seq, letter_nm1, max_identical_run):
                        planned_type = "lure"
                        planned_lure_type = "n-1"

                if planned_type == "non-target":
                    can_n_plus_1 = (i >= n_back + 1) and random.random() < lure_n_plus_1_rate
                    if can_n_plus_1:
                        letter_np1 = seq[i - (n_back + 1)]
                        letter_n = seq[i - n_back] if i >= n_back else None
                        if (letter_np1 is not None) and (letter_n is None or letter_np1 != letter_n) and _valid_run_limit(seq, letter_np1, max_identical_run):
                            planned_type = "lure"
                            planned_lure_type = "n+1"

            if planned_type == "target":
                letter = seq[i - n_back]
            elif planned_type == "lure" and planned_lure_type == "n-1":
                letter = seq[i - (n_back - 1)]
                if i >= n_back and letter == seq[i - n_back]:
                    planned_type = "non-target"
                    planned_lure_type = "none"
            elif planned_type == "lure" and planned_lure_type == "n+1":
                letter = seq[i - (n_back + 1)]
                if i >= n_back and letter == seq[i - n_back]:
                    planned_type = "non-target"
                    planned_lure_type = "none"
            else:
                candidates = [c for c in LETTERS]
                if i >= n_back:
                    avoid = seq[i - n_back]
                    candidates = [c for c in candidates if c != avoid]
                if seq:
                    last = seq[-1]
                    if last in candidates and not _valid_run_limit(seq, last, max_identical_run - 1):
                        candidates = [c for c in candidates if c != last]
                letter = _choose_letter(candidates, freqs, soft_balance=soft_balance_initial)

            if not _valid_run_limit(seq, letter, max_identical_run):
                cands = [c for c in LETTERS if _valid_run_limit(seq, c, max_identical_run)]
                if i >= n_back:
                    cands = [c for c in cands if c != seq[i - n_back]]
                if seq:
                    last = seq[-1]
                    if last in cands and not _valid_run_limit(seq, last, max_identical_run - 1):
                        cands = [c for c in cands if c != last]
                letter = _choose_letter(cands, freqs, soft_balance=soft_balance_initial)

            seq.append(letter)
            freqs[letter] = freqs.get(letter, 0) + 1

            if planned_type == "target" and i >= n_back and letter == seq[i - n_back]:
                is_target_flags.append(1)
                consec_target_run += 1
                targets_placed += 1
                lure_types.append("none")
            else:
                is_target_flags.append(0)
                consec_target_run = 0
                if planned_lure_type.startswith("n-") or planned_lure_type.startswith("n+"):
                    lure_types.append(planned_lure_type)
                else:
                    lure_types.append("none")

        ok, _reason = validate_sequence(
            seq, is_target_flags, lure_types,
            n_back=n_back,
            target_rate=target_rate,
            tolerance=1,
            max_consec_targets=max_consec_targets,
        )
        if not ok:
            continue

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

    return generate_sequence(
        n_back,
        n_trials,
        target_rate=target_rate,
        lure_n_minus_1_rate=lure_n_minus_1_rate,
        lure_n_plus_1_rate=lure_n_plus_1_rate,
        max_consec_targets=max_consec_targets,
        max_identical_run=max_identical_run,
        iti_range_ms=iti_range_ms,
        max_attempts=1,
        soft_balance_initial=False,
        include_lures=include_lures,
    )
