# Near-Hole Correction Experiment Summary

Generated: 2026-05-06

## Goal

Test whether DAgger-style corrective samples from policy-visited failure
windows can improve the current UR5e adapter image policy on medium-clearance
geometry without regressing clean, visual, or control robustness.

Baseline model:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip
```

## Correction Dataset

Dataset:

```text
datasets\image_correction_ur5e_adapter_medium_targeted_near_hole_failure_window_10k_min006_oracle.npz
```

Collection settings:

| Setting | Value |
| --- | --- |
| scenario preset | `targeted` |
| tier preset | `medium` |
| selection | `near_hole_failure_window` |
| failure window steps | `10` |
| min correction norm | `0.006` |
| max samples per episode | `6` |
| requested samples | `10000` |
| collected samples | `8405` |
| episodes completed | `16003` |

Correction signals:

| Signal | 2k failure-window pass | near-hole 8k pass |
| --- | ---: | ---: |
| samples | 2000 | 8405 |
| unique source episodes | 492 | 2616 |
| near-hole rate | 0.5405 | 1.0000 |
| opposed-action rate | 0.2855 | 0.4700 |
| policy down / oracle up | 0.1890 | 0.1945 |
| mean correction norm | 0.00775 | 0.00960 |

The new dataset is much more targeted: all samples are near-hole failure-window
states, and nearly half have policy/oracle actions pointing against each other.

## Training Variants

All variants start from the 750k baseline and mix the 8k correction dataset into
the existing replay mix.

| Variant | Correction weight | Epochs | LR | Output |
| --- | ---: | ---: | ---: | --- |
| w08 e1 | 0.08 | 1 | 0.0000008 | `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1\sac_image_bc.zip` |
| w05 e2 | 0.05 | 2 | 0.0000008 | `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w05_replay_858k_oracle_e2\sac_image_bc.zip` |
| w08 e2 | 0.08 | 2 | 0.0000008 | `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e2\sac_image_bc.zip` |

## Standard Matrix

100 episodes per scenario, seed `90000`.

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| 750k baseline | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |
| 2k correction w05 e2 | 0.980 | 0.960 | 0.910 | 0.550 | 0.620 |
| 8k correction w08 e1 | 0.980 | 0.980 | 0.900 | 0.590 | 0.630 |
| 8k correction w05 e2 | 0.980 | 0.970 | 0.930 | 0.570 | 0.630 |
| 8k correction w08 e2 | 0.960 | 0.950 | 0.910 | 0.590 | 0.630 |

## Geometry Scan

30 episodes per combination, seed `960000`, targeted wide/medium tiers.

| Model | Wide FLG no guard | Wide hard no guard | Medium FLG no guard | Medium hard no guard |
| --- | ---: | ---: | ---: | ---: |
| 750k baseline | 0.533 | 0.333 | 0.400 | 0.367 |
| 8k correction w08 e1 | 0.500 | 0.367 | 0.433 | 0.333 |
| 8k correction w05 e2 | 0.467 | 0.333 | 0.433 | 0.333 |
| 8k correction w08 e2 | 0.533 | 0.300 | 0.467 | 0.333 |

## Conclusion

Do not promote any correction model yet.

The 8k near-hole correction data is useful and more diagnostic than the first
2k pass, but the BC updates still trade improvements between buckets rather
than producing a robust overall gain. The best candidate is w08 e1 because it
keeps clean and visual-camera performance at baseline and improves
`full_contact_light`, but it slightly hurts `visual_camera_control` and the
geometry scan remains mixed.

Follow-up done: collision-window and timeout-window correction datasets were
collected and trained separately. They did not outperform the 750k baseline or
the near-hole 8k w08 e1 candidate. See
`results\correction_outcome_split_6k_experiment_summary.md`.

Next step: stop increasing pure BC correction mixes for this failure mode and
return to the deployment-time guarded insert path for the last few millimeters.
