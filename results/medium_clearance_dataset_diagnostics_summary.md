# Medium Clearance Dataset Diagnostics Summary

## Purpose

The next curriculum target is `medium` clearance, not direct narrow/tight
geometry. This pass adds dataset-level auditability before collecting the next
large batch, so future training runs can confirm which geometry and control
conditions are actually represented in the BC data.

## Implementation

- `scripts/collect_image_expert_dataset.py` now writes schema
  `image_expert_v2_diagnostics`.
- New arrays include `hole_half_size`, `peg_radius`, `hole_clearance`,
  `hole_center_offset`, control scale/noise/delay/filter values,
  fixture/table height offsets, and contact/dynamics multipliers.
- Metadata now includes success, collision, timeout, and kept-episode rates,
  array shapes/dtypes, and aggregate diagnostic summaries.
- `scripts/inspect_image_expert_dataset.py` writes md/csv summaries for any
  image expert `.npz` dataset.

## Smoke Results

Both smoke datasets use the UR5e adapter, `100x100` wrist images,
`64x64` near-hole crops, `guarded_two_stage` oracle, success-only filtering,
`approach_xy_tolerance=0.02`, and medium clearance:
`hole_half_size=0.020-0.024`, `peg_radius=0.0115-0.0125`.

| Dataset | Samples | Episodes | Kept episodes | Success | Collision | Timeout | Mean clearance | Mean delay | Mean alpha |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| medium guarded success smoke | 500 | 58 | 35 | 0.603 | 0.345 | 0.052 | 9.93 mm | 1.11 | 0.777 |
| medium hard guarded success smoke | 500 | 87 | 26 | 0.299 | 0.701 | 0.000 | 10.36 mm | 2.00 | 0.627 |

## Full 50k Collection

The full medium datasets were collected with the same settings and
success-only filtering.

| Dataset | Samples | Episodes | Kept episodes | Success | Collision | Timeout | Mean clearance | Mean delay | Mean alpha |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| medium guarded success 50k | 50000 | 5142 | 2978 | 0.579 | 0.385 | 0.037 | 10.05 mm | 0.88 | 0.785 |
| medium hard guarded success 50k | 50000 | 8096 | 2791 | 0.345 | 0.647 | 0.009 | 10.11 mm | 2.00 | 0.628 |

Inspection files:

- `results/image_expert_medium_guarded_success_smoke_inspection.md`
- `results/image_expert_medium_guarded_success_smoke_inspection.csv`
- `results/image_expert_medium_hard_guarded_success_smoke_inspection.md`
- `results/image_expert_medium_hard_guarded_success_smoke_inspection.csv`
- `results/image_expert_medium_guarded_success_50k_inspection.md`
- `results/image_expert_medium_guarded_success_50k_inspection.csv`
- `results/image_expert_medium_hard_guarded_success_50k_inspection.md`
- `results/image_expert_medium_hard_guarded_success_50k_inspection.csv`

## Interpretation

The standard medium bucket is collectible with the guarded oracle, but it still
has a substantial failure rate. The hard-control medium bucket is much harder:
the full 50k hard bucket required 8096 attempted episodes and collided in
64.7% of attempts. Success-only filtering is still necessary, but the resulting
BC data contains only the successful subset and does not teach the policy how
to recover from the many near-failure states.

## Next Training Direction

Two weighted BC continuations were tested from the current crop-enabled 750k
model:

| Model | Medium weights | Epochs | LR | Clean | Visual camera | Visual camera control | Full light | Full contact |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `medium_replay_850k_oracle_e4` | 0.20 | 4 | 0.000002 | 0.960 | 0.970 | 0.860 | 0.540 | 0.570 |
| `medium_replay_light_850k_oracle_e2` | 0.15 | 2 | 0.000001 | 0.970 | 0.980 | 0.900 | 0.550 | 0.660 |

Neither model should replace the current 750k recommendation. The light replay
improves `full_contact_light`, but standard `full_light_geometry` remains below
the 750k baseline (`0.580`) and the wide/medium hard buckets are not improved
enough in the targeted clearance scan.

The next iteration should not simply increase medium replay weight. It should
diagnose why medium success-only actions are not transferring: compare action
and state distributions against failed policy rollouts, then either rebalance
toward near-failure correction data or use DAgger/guarded corrective rollouts
instead of only cloning successful guarded-oracle trajectories.
