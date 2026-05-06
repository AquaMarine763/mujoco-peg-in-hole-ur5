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

Inspection files:

- `results/image_expert_medium_guarded_success_smoke_inspection.md`
- `results/image_expert_medium_guarded_success_smoke_inspection.csv`
- `results/image_expert_medium_hard_guarded_success_smoke_inspection.md`
- `results/image_expert_medium_hard_guarded_success_smoke_inspection.csv`

## Interpretation

The standard medium bucket is collectible with the guarded oracle, but it still
has a substantial failure rate. The hard-control medium bucket is much harder:
only 26 successful episodes were needed to fill 500 success-only samples, but
61 of 87 attempted episodes collided. For the next full dataset pass, keep
`--success-only`, retain diagnostics, and expect the hard-control bucket to
take materially longer than the standard medium bucket.

## Next Training Direction

Collect full `50k` medium success-only datasets for both standard and hard
control. Then continue weighted BC from the current crop-enabled 750k model,
mixing prior wide/intermediate/narrow/control data with a modest medium weight
first. Do not promote narrow/tight as the default geometry distribution until
medium hard-control success improves.
