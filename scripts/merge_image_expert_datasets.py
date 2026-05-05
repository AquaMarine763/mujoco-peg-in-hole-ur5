from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge image expert NPZ datasets by concatenating matching arrays.")
    parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compressed", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if len(args.inputs) < 2:
        raise ValueError("At least two input datasets are required.")

    loaded = [np.load(path) for path in args.inputs]
    try:
        keys = set(loaded[0].files)
        for dataset in loaded[1:]:
            if set(dataset.files) != keys:
                raise ValueError("All input datasets must contain the same array keys.")

        arrays: dict[str, np.ndarray] = {}
        episode_offset = 0
        for key in sorted(keys):
            chunks = []
            for dataset in loaded:
                chunk = dataset[key]
                if key == "episode_id":
                    chunk = chunk + episode_offset
                    episode_offset += int(dataset[key].max()) + 1
                chunks.append(chunk)
            arrays[key] = np.concatenate(chunks, axis=0)

        sample_counts = [int(dataset["actions"].shape[0]) for dataset in loaded]
        output_samples = int(arrays["actions"].shape[0])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.compressed:
            np.savez_compressed(args.output, **arrays)
        else:
            np.savez(args.output, **arrays)

        metadata = {
            "inputs": [str(path) for path in args.inputs],
            "input_samples": sample_counts,
            "output_samples": output_samples,
            "compressed": bool(args.compressed),
        }
        metadata_path = args.output.with_suffix(args.output.suffix + ".json")
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        print(f"saved merged dataset to {args.output}")
        print(f"saved metadata to {metadata_path}")
        print(f"output_samples={output_samples}")
    finally:
        for dataset in loaded:
            dataset.close()


if __name__ == "__main__":
    main()
