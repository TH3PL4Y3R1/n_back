#!/usr/bin/env python3
from __future__ import annotations

import sys
import random
from nback.sequences import generate_sequence

n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
trials = int(sys.argv[2]) if len(sys.argv) > 2 else 10
seed = int(sys.argv[3]) if len(sys.argv) > 3 else None
if seed is not None:
    random.seed(seed)
plans = generate_sequence(n, trials)
print('n_back:', n, 'trials:', trials)
print('seq:       ', ''.join(p.stimulus for p in plans))
print('is_target: ', [p.is_target for p in plans])
print('lure_type: ', [p.lure_type for p in plans])
