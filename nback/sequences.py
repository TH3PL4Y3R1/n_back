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


def _sample_target_indices(n_back: int, n_trials: int, desired: int, max_consec_targets: int, *, attempts: int = 200) -> Optional[List[int]]:
    """Randomly choose target indices >= n_back satisfying:
    - No more than max_consec_targets consecutive targets
    - No N-back chaining: i and i-n_back cannot both be targets (breaks repeating N-back cycles)
    Returns sorted indices or None on failure.
    """
    if desired <= 0:
        return []
    positions = list(range(n_back, n_trials))
    for _ in range(attempts):
        random.shuffle(positions)
        chosen: List[int] = []
        for i in positions:
            if len(chosen) >= desired:
                break
            # Consecutive target constraint
            if max_consec_targets <= 0:
                allow = False
            else:
                if max_consec_targets == 1 and chosen and i - chosen[-1] == 1:
                    continue
                # General case: ensure last run length would not exceed max
                if chosen:
                    run = 1
                    j = len(chosen) - 1
                    while j >= 0 and chosen[j] == (i - (len(chosen) - j)):
                        run += 1
                        j -= 1
                    if run > max_consec_targets:
                        continue
            # Break chains: do not select i if (i - n_back) already a target
            if (i - n_back) in chosen:
                continue
            chosen.append(i)
        if len(chosen) == desired:
            return sorted(chosen)
    return None


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

        target_indices = _sample_target_indices(n_back, n_trials, desired_targets, max_consec_targets)
        if target_indices is None:
            continue
        target_set = set(target_indices)

        for i in range(n_trials):
            iti_ms = random.randint(iti_range_ms[0], iti_range_ms[1])
            planned_lure_type = "none"
            # Target placement by pre-sampled indices
            if i in target_set and i >= n_back:
                # Letter must match n-back
                if i >= n_back:
                    letter = seq[i - n_back]
                else:
                    # Should not happen as indices start at n_back
                    letter = _choose_letter(LETTERS, freqs, soft_balance=soft_balance_initial)
                is_target_flags.append(1)
                lure_types.append("none")
            else:
                # Optionally place a lure on non-target trials
                if include_lures:
                    # n-1 lure
                    if (n_back - 1) > 0 and i >= (n_back - 1) and random.random() < lure_n_minus_1_rate:
                        letter_nm1 = seq[i - (n_back - 1)]
                        letter_n = seq[i - n_back] if i >= n_back else None
                        if letter_nm1 and (letter_n is None or letter_nm1 != letter_n) and _valid_run_limit(seq, letter_nm1, max_identical_run):
                            planned_lure_type = "n-1"
                            letter = letter_nm1
                        else:
                            planned_lure_type = "none"
                    # n+1 lure
                    if planned_lure_type == "none" and i >= (n_back + 1) and random.random() < lure_n_plus_1_rate:
                        letter_np1 = seq[i - (n_back + 1)]
                        letter_n = seq[i - n_back] if i >= n_back else None
                        if letter_np1 and (letter_n is None or letter_np1 != letter_n) and _valid_run_limit(seq, letter_np1, max_identical_run):
                            planned_lure_type = "n+1"
                            letter = letter_np1
                        else:
                            planned_lure_type = "none"
                # If still none, choose a regular non-target letter
                if planned_lure_type == "none":
                    candidates = [c for c in LETTERS]
                    if i >= n_back:
                        avoid = seq[i - n_back]
                        candidates = [c for c in candidates if c != avoid]
                    if seq:
                        last = seq[-1]
                        if last in candidates and not _valid_run_limit(seq, last, max_identical_run - 1):
                            candidates = [c for c in candidates if c != last]
                    letter = _choose_letter(candidates, freqs, soft_balance=soft_balance_initial)
                is_target_flags.append(0)
                lure_types.append(planned_lure_type)

            # Final run-limit check adjustment
            if not _valid_run_limit(seq, letter, max_identical_run):
                # Pick a different non-conflicting letter
                cands = [c for c in LETTERS if _valid_run_limit(seq, c, max_identical_run)]
                if i >= n_back:
                    cands = [c for c in cands if c != (seq[i - n_back] if i >= n_back else None)]
                if seq:
                    last = seq[-1]
                    if last in cands and not _valid_run_limit(seq, last, max_identical_run - 1):
                        cands = [c for c in cands if c != last]
                letter = _choose_letter(cands, freqs, soft_balance=soft_balance_initial)

            seq.append(letter)
            freqs[letter] = freqs.get(letter, 0) + 1

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
