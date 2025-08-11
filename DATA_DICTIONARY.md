# N-back Task — Data Dictionary

## Overview
This document defines every field produced by the N-back PsychoPy task. It ensures anyone can interpret the dataset without reading the source code.

## File naming and location
- Folder: `./data/`
- Filename template: `nback_{participantID}_{YYYYMMDD_HHMMSS}.csv`
- One file per session. Append a counter if multiple sessions occur in the same second.

## Task parameters captured in each run
- `n_back` (int): N level (e.g., 1, 2, 3)
- `n_blocks` (int)
- `trials_per_block` (int)
- `practice_trials` (int)
- `target_rate` (float, 0–1)
- `lure_n_minus_1_rate` (float, 0–1)
- `lure_n_plus_1_rate` (float, 0–1)
- `iti_min_ms`, `iti_max_ms` (int)
- `seed` (int or null)
- `enable_markers` (bool; default False)

## Trial-level columns
| Column name         | Description                                   | Type    | Values                               |
|---------------------|-----------------------------------------------|---------|--------------------------------------|
| `participant_id`    | Participant code                              | string  | alphanumeric                         |
| `session_timestamp` | Session start time                            | string  | `YYYY-MM-DD HH:MM:SS`                |
| `block_idx`         | Block index (1-based)                         | int     | `1..n_blocks`                        |
| `trial_idx`         | Trial index within block (1-based)            | int     | `1..trials_per_block`                |
| `n_back`            | N level for block                             | int     | `1`, `2`, or `3`                     |
| `stimulus`          | Letter shown                                  | string  | `A-Z`                                |
| `is_target`         | Target trial flag                             | int     | `1` = target, `0` = non-target       |
| `lure_type`         | Lure category                                 | string  | `"none"`, `"n-1"`, `"n+1"`             |
| `iti_ms`            | Planned inter-trial interval                  | int     | milliseconds                         |
| `stim_onset_time`   | Stimulus onset (relative to experiment start) | float   | seconds                              |
| `response_key`      | Key pressed                                   | string  | `"space"`, `"none"`, or key name       |
| `rt_ms`             | Reaction time from stimulus onset             | float   | milliseconds                         |
| `correct`           | Response accuracy                             | int     | `1` = correct, `0` = incorrect       |
| `marker_code_stim`  | Marker code at stimulus onset                 | int     | see marker coding                    |
| `marker_code_resp`  | Marker code at response                       | int     | see marker coding                    |

## Marker coding
(Default: transport code commented out; call sites exist.)
| Event               | Code |
|---------------------|------|
| consent_shown       | 10   |
| block_start         | 20   |
| fixation_onset      | 30   |
| stimulus_onset      | 40   |
| response_registered | 50   |
| block_end           | 70   |
| thank_you           | 90   |

Example scheme for encoding:
- Non-target: 40
- Target: 41
- Lure n-1: 42
- Lure n+1: 43

## Sequence constraints
1. No targets in first N trials
2. Target rate ≈ target_rate ±1 trial
3. Max consecutive targets = 1 (unless allowed)
4. Optional lures; never double-count as targets
5. Avoid unintended repeats for N>1
6. Max identical-letter run = 2 (unless required)
7. Soft balance letter frequency
8. Retry until constraints satisfied or max_attempts reached

## Missing values policy
If no response:
- `response_key = "none"`
- `rt_ms = NaN`
- `correct = 0`
- `marker_code_resp` may be 53 in the suggested scheme

## Example row
participant_id,session_timestamp,block_idx,trial_idx,n_back,stimulus,is_target,lure_type,iti_ms,stim_onset_time,response_key,rt_ms,correct,marker_code_stim,marker_code_resp
P001,2025-08-11 11:32:07,1,37,2,K,1,none,712,45.382,space,421.7,1,41,51

## Versioning
- Version: 1.0.0
- Last updated: 2025-08-11
- Maintainer: (add name/contact)

Changelog:
- 1.0.0 — Initial dictionary covering trial CSV, marker scheme, and validation rules.
