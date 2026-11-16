"""Audit an existing smoke run on CPU; never train or read official test data."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np
import torch
from torch.nn import functional as F


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN = "runs/g2_smoke/20261116T110418_330028Z"
DEFAULT_COMPARISON = "runs/g2_smoke/20261115T100414_504102Z"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inside_root(value: str) -> Path:
    path = (ROOT / value).resolve()
    path.relative_to(ROOT)
    return path


def wilson_interval(correct: int, count: int) -> list[float]:
    z = NormalDist().inv_cdf(0.975)
    p = correct / count
    divisor = 1 + z * z / count
    center = (p + z * z / (2 * count)) / divisor
    radius = z * math.sqrt(p * (1 - p) / count + z * z / (4 * count * count)) / divisor
    return [center - radius, center + radius]


def exact_mcnemar(fixed: int, broken: int) -> float:
    discordant = fixed + broken
    if not discordant:
        return 1.0
    tail = sum(math.comb(discordant, i) for i in range(min(fixed, broken) + 1))
    return min(1.0, 2 * tail / (2 ** discordant))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default=DEFAULT_RUN)
    parser.add_argument("--compare-run", default=DEFAULT_COMPARISON)
    args = parser.parse_args()
    run, previous = inside_root(args.run_dir), inside_root(args.compare_run)
    report = read_json(run / "report.json")
    if report["status"] != "success" or not all(report["checks"].values()):
        raise ValueError("Smoke report did not pass all mechanical checks")
    if report["mode"] != "smoke" or report["official_test_labels_read"]:
        raise ValueError("Only internal-development smoke data are allowed")
    torch.set_num_threads(4)
    real = read_json(run / "manifests/real.json")
    candidates = read_json(run / "manifests/candidates.json")
    selections = read_json(run / "manifests/selections.json")["selections"]
    index = read_json(run / "features/index.json")
    predictions = read_json(run / "metrics/dev_predictions.json")
    train = [row for row in real if row["split"] == "train"]
    dev = [row for row in real if row["split"] == "dev"]
    if {row["image_id"] for row in train} & {row["image_id"] for row in dev}:
        raise ValueError("Train/dev overlap")
    features = {}
    for item in index:
        path = inside_root(item["relative_cache_path"])
        if sha256(path) != item["sha256"]:
            raise ValueError("Feature cache checksum mismatch")
        with np.load(path, allow_pickle=False) as saved:
            features[item["image_id"]] = torch.from_numpy(saved["x"].copy()).float()
    by_id = {row["image_id"]: row for row in candidates}
    conditions = [row["condition_id"] for row in report["development_results"]]
    by_condition = {
        c: {row["sample_id"]: row for row in predictions if row["condition_id"] == c}
        for c in conditions
    }
    baseline = by_condition["real_only"]
    metrics = {row["condition_id"]: row for row in report["development_results"]}
    model_hashes = {row["relative_path"]: row["sha256"] for row in report["classifiers"]["models"]}

    def dataset_ce(rows: list[dict], state: dict) -> float:
        x = torch.stack([features[row["image_id"]] for row in rows])
        y = torch.tensor([row["class_id"] for row in rows])
        logits = F.linear(x, state["weight"], state["bias"])
        n, views, classes = logits.shape
        return F.cross_entropy(
            logits.reshape(n * views, classes), y.repeat_interleave(views), reduction="none"
        ).reshape(n, views).mean(1).mean().item()

    results = []
    for condition in conditions:
        records = by_condition[condition]
        if records.keys() != baseline.keys() or any(
            records[i]["true_label"] != baseline[i]["true_label"] for i in baseline
        ):
            raise ValueError("Conditions are not paired on identical dev samples")
        correct = sum(row["true_label"] == row["predicted_label"] for row in records.values())
        if correct / len(records) != metrics[condition]["accuracy"]:
            raise ValueError("Stored accuracy mismatch")
        fixed = sum(baseline[i]["true_label"] != baseline[i]["predicted_label"]
                    and records[i]["true_label"] == records[i]["predicted_label"] for i in baseline)
        broken = sum(baseline[i]["true_label"] == baseline[i]["predicted_label"]
                     and records[i]["true_label"] != records[i]["predicted_label"] for i in baseline)
        checkpoint_path = run / f"models/{condition}_seed0.pt"
        if sha256(checkpoint_path) != model_hashes[f"models/{condition}_seed0.pt"]:
            raise ValueError("Smoke checkpoint checksum mismatch")
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        selected = selections[condition]
        if checkpoint["selected_synthetic_ids"] != selected:
            raise ValueError("Checkpoint selection mismatch")
        if checkpoint["real_train_ids"] != [row["image_id"] for row in train]:
            raise ValueError("Checkpoint training IDs mismatch")
        state = checkpoint["head_state"]
        with torch.inference_mode():
            real_ce = dataset_ce(train, state)
            syn_ce = dataset_ce([by_id[i] for i in selected], state) if selected else None
        results.append({
            "condition_id": condition,
            "synthetic_per_class": len(selected) // 10,
            "synthetic_total": len(selected),
            "correct": correct, "dev_count": len(records), "accuracy": correct / len(records),
            "delta_pp_vs_real_only": 100 * (correct - sum(
                row["true_label"] == row["predicted_label"] for row in baseline.values()
            )) / len(records),
            "fixed_baseline_errors": fixed, "broke_baseline_correct": broken,
            "exact_mcnemar_two_sided_p": exact_mcnemar(fixed, broken),
            "wilson_95_interval_descriptive": wilson_interval(correct, len(records)),
            "per_class_correct": [sum(row["true_label"] == row["predicted_label"]
                for row in records.values() if row["true_label"] == c) for c in range(10)],
            "real_train_ce_all_four_views_posthoc": real_ce,
            "selected_synthetic_ce_all_four_views_posthoc": syn_ce,
            "full_training_objective_posthoc": real_ce if syn_ce is None else 0.5 * (real_ce + syn_ce),
            "logged_final_minibatch_loss": metrics[condition]["loss_checks"][-1]["loss"],
            "model_sha256": sha256(checkpoint_path),
        })
    old = read_json(previous / "report.json")
    old_metrics = {row["condition_id"]: row for row in old["development_results"]}
    stable_fields = ("sample_id", "condition_id", "seed", "true_label", "predicted_label", "prediction_split")
    normalize = lambda rows: sorted(tuple(row[k] for k in stable_fields) for row in rows)
    matches = {
        "accuracy_float64_bitwise_equal": all(struct.pack("!d", metrics[c]["accuracy"])
            == struct.pack("!d", old_metrics[c]["accuracy"]) for c in conditions),
        "logged_loss_records_equal": all(metrics[c]["loss_checks"] == old_metrics[c]["loss_checks"] for c in conditions),
        "dev_predictions_equal_ignoring_config_hash": normalize(predictions)
            == normalize(read_json(previous / "metrics/dev_predictions.json")),
    }
    if not all(matches.values()):
        raise ValueError("Historical smoke outputs differ; do not claim reproduction")
    common_errors = [i for i in baseline if all(
        by_condition[c][i]["true_label"] != by_condition[c][i]["predicted_label"] for c in conditions
    )]
    raw_sources = ["report.json", "metrics/dev_predictions.json", "manifests/real.json",
                   "manifests/candidates.json", "manifests/selections.json", "features/index.json"]
    snapshot = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "record_type": "author_self_test_posthoc_audit",
        "run_dir": args.run_dir, "config_hash": report["config_hash"],
        "scope": "Existing smoke checkpoints, cached features and saved internal-dev predictions only; CPU post-processing; no training, image generation or official test access.",
        "input_sha256": {name: sha256(run / name) for name in raw_sources},
        "audit_script_sha256": sha256(Path(__file__)),
        "training_images": len(train), "dev_images": len(dev),
        "train_per_class": [sum(row["class_id"] == c for row in train) for c in range(10)],
        "dev_per_class": [sum(row["class_id"] == c for row in dev) for c in range(10)],
        "single_dev_image_resolution_pp": 100 / len(dev),
        "source_weights": {"real_only": {"real": 1.0, "synthetic": 0.0},
                           "mixed": {"real": 0.5, "synthetic": 0.5}},
        "nested_random": set(selections["random_1"]).issubset(selections["random_2"]),
        "nested_clip": set(selections["clip_1"]).issubset(selections["clip_2"]),
        "mechanical_checks": report["checks"], "compute_seconds": report["seconds"],
        "feature_cache_hits": report["features"]["cache_hits"], "results": results,
        "common_error_count": len(common_errors), "common_error_ids": sorted(common_errors),
        "previous_run": args.compare_run, "previous_run_comparison": matches,
        "independent_repetition_added": False, "external_user_trial_demonstrated": False,
        "limitations": [
            "Wilson intervals and paired tests are descriptive diagnostics on 40 internal-dev images, not formal augmentation-effect evidence or training-seed uncertainty.",
            "CE values were recomputed post hoc over full training sources and four views; logged loss is a different, pre-update final-minibatch value.",
            "Real source coefficient is 0.5 in mixed training; no equal-real-weight control isolates a synthetic-data-only causal effect.",
            "Common errors describe these five fitted heads; they are not an irreducible error floor.",
            "No end-to-end CLI exit code, clean shutdown, closed transcript or complete user duration is inferred from report status.",
        ],
    }
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
