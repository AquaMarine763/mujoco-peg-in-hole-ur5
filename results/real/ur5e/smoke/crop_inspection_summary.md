# Real Camera Crop Inspection

- Verdict: **PASS**
- Input: `synthetic_smoke`
- Frames loaded: `3`
- Candidates: `160`
- Output dir: `results\real\ur5e\smoke\crop_inspection`
- Stats CSV: `results\real\ur5e\smoke\crop_inspection_stats.csv`
- Policy image size: `100x100`
- Near-hole crop size: `64`

## Preview Sheets

- `crop_candidates_first_frame_sheet`: `results\real\ur5e\smoke\crop_inspection\crop_candidates_first_frame_sheet.png`
- `processed_candidates_first_frame_sheet`: `results\real\ur5e\smoke\crop_inspection\processed_candidates_first_frame_sheet.png`
- Per-candidate frame sheets are saved under each `cNNN` output directory.

## Candidate Ranking

Rank is only a heuristic based on near-hole crop contrast. Pick the final config by inspecting the preview sheets.

| Rank | Candidate | crop_xywh | rotate_k | flip_h | flip_v | mean | std | near_std | sheet |
| ---: | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| 1 | `c096` | `45,24,192,192` | 0 | False | False | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c096\frames_sheet.png` |
| 2 | `c097` | `45,24,192,192` | 0 | True | False | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c097\frames_sheet.png` |
| 3 | `c098` | `45,24,192,192` | 0 | False | True | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c098\frames_sheet.png` |
| 4 | `c099` | `45,24,192,192` | 0 | True | True | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c099\frames_sheet.png` |
| 5 | `c100` | `45,24,192,192` | 1 | False | False | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c100\frames_sheet.png` |
| 6 | `c101` | `45,24,192,192` | 1 | True | False | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c101\frames_sheet.png` |
| 7 | `c102` | `45,24,192,192` | 1 | False | True | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c102\frames_sheet.png` |
| 8 | `c103` | `45,24,192,192` | 1 | True | True | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c103\frames_sheet.png` |
| 9 | `c104` | `45,24,192,192` | 2 | False | False | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c104\frames_sheet.png` |
| 10 | `c105` | `45,24,192,192` | 2 | True | False | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c105\frames_sheet.png` |
| 11 | `c106` | `45,24,192,192` | 2 | False | True | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c106\frames_sheet.png` |
| 12 | `c107` | `45,24,192,192` | 2 | True | True | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c107\frames_sheet.png` |
| 13 | `c108` | `45,24,192,192` | 3 | False | False | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c108\frames_sheet.png` |
| 14 | `c109` | `45,24,192,192` | 3 | True | False | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c109\frames_sheet.png` |
| 15 | `c110` | `45,24,192,192` | 3 | False | True | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c110\frames_sheet.png` |
| 16 | `c111` | `45,24,192,192` | 3 | True | True | 123.578033 | 41.8064588 | 39.8008002 | `results\real\ur5e\smoke\crop_inspection\c111\frames_sheet.png` |
| 17 | `c016` | `74,48,144,144` | 0 | False | False | 124.355533 | 39.4497161 | 39.4469146 | `results\real\ur5e\smoke\crop_inspection\c016\frames_sheet.png` |
| 18 | `c017` | `74,48,144,144` | 0 | True | False | 124.355533 | 39.4497161 | 39.4469146 | `results\real\ur5e\smoke\crop_inspection\c017\frames_sheet.png` |
| 19 | `c018` | `74,48,144,144` | 0 | False | True | 124.355533 | 39.4497161 | 39.4469146 | `results\real\ur5e\smoke\crop_inspection\c018\frames_sheet.png` |
| 20 | `c019` | `74,48,144,144` | 0 | True | True | 124.355533 | 39.4497161 | 39.4469146 | `results\real\ur5e\smoke\crop_inspection\c019\frames_sheet.png` |

## Config Snippet

Copy these values only after visual inspection confirms the candidate is correct:

```yaml
crop_xywh: [45, 24, 192, 192]
rotate_k: 0
flip_horizontal: false
flip_vertical: false
include_near_hole_crop: true
near_hole_crop_size: 64
```

## Issues

| Severity | Code | Count | Details |
| --- | --- | ---: | --- |
| INFO | `no_issues` | 0 | No issues detected. |
