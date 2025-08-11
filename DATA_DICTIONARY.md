# N-back Task — Data Dictionary

## Overview
This document defines every field produced by the N-back PsychoPy task. It ensures anyone can interpret the dataset without reading the source code.

## File naming and location
- Folder: `./data/`
- Filename template: `nback_{participantID}_{YYYYMMDD_HHMMSS}.csv`
- One file per session. If multiple sessions occur in the same second, the timestamp is identical; the participant or later start time will differ. Keeping sessions separate is recommended.

## Task parameters captured in each run (metadata sidecar .meta.json)
- `participant_id` (string)
- `session_timestamp` (string, `YYYYMMDD_HHMMSS`)
- `n_back` (int): N level (e.g., 1, 2, 3)
- `blocks` (int)
- `trials_per_block` (int)
- `practice_trials` (int)
- `practice_target_rate` (float, 0–1)
- `practice_has_lures` (bool)
- `target_rate` (float, 0–1)
- `lure_nminus1_rate` (float, 0–1)
- `lure_nplus1_rate` (float, 0–1)
- `max_consec_targets` (int)
- `iti_ms_range` ([int, int])
- `seed` (int or null)
- `letters` (list of strings)
- `psychopy_version` (string or null)
- `display_refresh_hz` (float or null): detected display refresh rate at startup
- `window_fullscreen` (bool): whether the task ran in fullscreen (recommended for timing)

## Trial-level columns
| Column name         | Description                                   | Type    | Values                               |
|---------------------|-----------------------------------------------|---------|--------------------------------------|
| `participant_id`    | Participant code                              | string  | alphanumeric                         |
| `session_timestamp` | Session start time (file timestamp)           | string  | `YYYYMMDD_HHMMSS`                    |
| `block_idx`         | Block index (1-based)                         | int     | `1..blocks`                          |
| `trial_idx`         | Trial index within block (1-based)            | int     | `1..trials_per_block`                |
| `n_back`            | N level for block                             | int     | `1`, `2`, or `3`                     |
| `stimulus`          | Letter shown                                  | string  | `A-Z` excluding I/O/Q by default     |
| `is_target`         | Target trial flag                             | int     | `1` = target, `0` = non-target       |
| `lure_type`         | Lure category                                 | string  | `"none"`, `"n-1"`, `"n+1"`             |
| `iti_ms`            | Planned inter-trial interval                  | int     | milliseconds                         |
| `stim_onset_time`   | Stimulus onset (returned by window.flip)      | float   | seconds (high-resolution timestamp)  |
| `response_key`      | Key pressed                                   | string  | key name (e.g., `"space"`) or empty   |
| `rt_ms`             | Reaction time from stimulus onset             | float   | milliseconds; empty if no response   |
| `correct`           | Response accuracy                             | int     | `1` = correct, `0` = incorrect       |
| `marker_code_stim`  | Marker code at stimulus onset                 | int     | see marker coding                    |
| `marker_code_resp`  | Marker code at response                       | int     | see marker coding or empty           |

## Marker coding
(Default: transport code is a no-op; call sites exist.)
| Event                      | Code |
|----------------------------|------|
| consent_shown              | 10   |
| block_start                | 20   |
| fixation_onset             | 30   |
| stimulus_target            | 41   |
| stimulus_nontarget         | 42   |
| stimulus_lure_n_minus_1    | 43   |
| stimulus_lure_n_plus_1     | 44   |
| response_registered        | 50   |
| block_end                  | 70   |
| thank_you                  | 90   |

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
- `response_key = ""` (empty string)
- `rt_ms = ""` (empty string)
- `correct = 0`
- `marker_code_resp = ""` (empty string)

## Example row
participant_id,session_timestamp,block_idx,trial_idx,n_back,stimulus,is_target,lure_type,iti_ms,stim_onset_time,response_key,rt_ms,correct,marker_code_stim,marker_code_resp
P001,20250811_113207,1,37,2,K,1,none,712,45.382,space,421.7,1,41,50

## Versioning
- Version: 1.0.2
- Last updated: 2025-08-11
- Maintainer: (add name/contact)

Changelog:
- 1.0.2 — Document `display_refresh_hz` and `window_fullscreen` in metadata; minor clarifications.
- 1.0.1 — Align docs with code: marker codes 41/42/43/44 and response 50; timestamp format `YYYYMMDD_HHMMSS`; empty string policy for missing.
- 1.0.0 — Initial dictionary covering trial CSV, marker scheme, and validation rules.
