# Outcome-Split Correction Experiment Summary

Generated: 2026-05-07

## Goal

Follow up the 8k near-hole correction experiment by separating collision-window
and timeout-window corrective samples. The hypothesis was that timeout samples
carry a different correction signal and should not be mixed blindly with
collision samples.

Baseline model:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip
```

## Script Change

`scripts\collect_image_correction_dataset.py` now accepts:

```text
--episode-outcome-filter any|collision|timeout|terminated_failure
```

This keeps the existing sample-level selectors, such as
`near_hole_failure_window`, but restricts selected rows to episodes with the
requested final outcome.

## Datasets

Both datasets use:

| Setting | Value |
| --- | --- |
| scenario preset | `targeted` |
| tier preset | `wide_medium` |
| selection | `near_hole_failure_window` |
| failure window steps | `10` |
| min correction norm | `0.006` |
| max samples per episode | `6` |

### Collision Window

```text
datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_collision_window_4k_min006_oracle.npz
```

| Tier | Scenario | Samples | Episodes |
| --- | --- | ---: | ---: |
| wide_current | full_light_geometry | 1000 | 3065 |
| wide_current | hard_full_light_bucket | 1000 | 4142 |
| medium | full_light_geometry | 1000 | 2986 |
| medium | hard_full_light_bucket | 1000 | 4797 |

Signals: near-hole rate `1.000`, opposed-action rate `0.258`, policy down /
oracle up rate `0.287`, mean correction norm `0.00870`.

### Timeout Window

```text
datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_timeout_window_4k_min006_oracle.npz
```

Timeout rows were much rarer in wide-current buckets, so collection stopped at
the per-config max episode budget before reaching 4k samples.

| Tier | Scenario | Samples | Episodes |
| --- | --- | ---: | ---: |
| wide_current | full_light_geometry | 267 | 5000 |
| wide_current | hard_full_light_bucket | 152 | 5000 |
| medium | full_light_geometry | 1000 | 3150 |
| medium | hard_full_light_bucket | 931 | 5000 |

Signals: near-hole rate `1.000`, opposed-action rate `0.653`, policy down /
oracle up rate `0.230`, mean correction norm `0.01055`.

## Training Variants

All variants start from the 750k baseline and use one low-step weighted BC
epoch with `200000` samples per epoch and learning rate `0.0000008`.

| Variant | Collision weight | Timeout weight | Output |
| --- | ---: | ---: | --- |
| w04w04 e1 | 0.04 | 0.04 | `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_outcome_split_6k_w04w04_replay_856k_oracle_e1\sac_image_bc.zip` |
| w06w02 e1 | 0.06 | 0.02 | `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_outcome_split_6k_w06w02_replay_856k_oracle_e1\sac_image_bc.zip` |

## Standard Matrix

100 episodes per scenario, seed `90000`.

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| 750k baseline | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |
| near-hole 8k w08 e1 | 0.980 | 0.980 | 0.900 | 0.590 | 0.630 |
| outcome split w04w04 e1 | 0.980 | 0.980 | 0.910 | 0.560 | 0.600 |
| outcome split w06w02 e1 | 0.980 | 0.980 | 0.900 | 0.580 | 0.590 |

## Geometry Scan

30 episodes per combination, seed `960000`, targeted wide/medium tiers.

| Model | Wide FLG no guard | Wide hard no guard | Medium FLG no guard | Medium hard no guard |
| --- | ---: | ---: | ---: | ---: |
| 750k baseline | 0.533 | 0.333 | 0.400 | 0.367 |
| near-hole 8k w08 e1 | 0.500 | 0.367 | 0.433 | 0.333 |
| outcome split w04w04 e1 | 0.500 | 0.333 | 0.400 | 0.333 |
| outcome split w06w02 e1 | 0.500 | 0.267 | 0.400 | 0.333 |

## Conclusion

Do not promote either outcome-split model.

Outcome separation is useful diagnostically: timeout corrections are much more
opposed to the policy than collision corrections, but directly oversampling
them in BC conflicts with the successful replay data. The best overall model
from correction experiments remains the near-hole 8k w08 e1 candidate, but it
is still not strong enough to replace the 750k baseline.

Next step: stop trying larger BC mixes for this failure mode. The data suggests
the deployment-time guarded insert path is a cleaner way to handle the last few
millimeters, while learned visual policy should stay responsible for approach
and coarse alignment.
