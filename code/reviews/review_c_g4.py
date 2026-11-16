"""B-side independent statistics review; stdlib only, no C/A statistics imports.

Reads the released G4 ZIP and committed C CSVs without modifying either.
All comparisons use declared CSV rounding tolerances, not inference tolerances.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import platform
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CONDITIONS = ('real_only', 'random_50', 'clip_50', 'random_150', 'clip_150')
CLASSES = ('airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def moments(values):
    """Explicit sample SD with n-1 denominator; values already in % or pp."""
    require(len(values) == 3, 'Exactly three paired seeds required')
    avg = math.fsum(values) / 3
    return avg, math.sqrt(math.fsum((x - avg) ** 2 for x in values) / 2)


def compare_table(path, keys, expected, decimals):
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig'))))
    lookup = {tuple(row[k] for k in keys): row for row in rows}
    require(len(lookup) == len(rows), f'{path.name}: duplicate keys')
    require(set(lookup) == set(expected), f'{path.name}: missing/extra rows')
    errors = []
    for key, columns in expected.items():
        for col, value in columns.items():
            actual = float(lookup[key][col])
            error = abs(actual - value)
            require(math.isfinite(actual) and error <= 0.5 * 10 ** -decimals + 1e-10,
                    f'{path.name}/{key}/{col}: {actual} != {value}')
            errors.append(error)
    return {'rows': len(rows), 'numeric_cells': len(errors), 'decimal_places': decimals,
            'max_absolute_rounding_error': max(errors), 'status': 'pass'}


def review(repo, bundle, out):
    out.mkdir(parents=True, exist_ok=True)
    delivery = json.loads((repo / 'shared/synthetic_v2/g4/delivery.json').read_text())
    raw_zip = bundle.read_bytes()
    require(len(raw_zip) == delivery['bytes'] and sha(raw_zip) == delivery['sha256'], 'ZIP integrity')
    scores, class_scores, per_run = {}, {}, []
    files = []
    common_labels = None
    expected_runs = {(c, s) for c in CONDITIONS for s in range(3)} | {('clip_zero_shot', None)}
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as z:
        index_raw = z.read('handoff/prediction_index.json')
        require(index_raw == (repo / 'shared/synthetic_v2/g4/prediction_index.json').read_bytes(),
                'Published and committed prediction indexes differ')
        ix = json.loads(index_raw)
        require(ix['config_hash'] == delivery['config_hash'], 'Index config hash')
        require(ix['model_seal_sha256'] == delivery['model_seal_sha256'], 'Model seal hash')
        require(tuple(ix['official_classes']) == CLASSES and ix['rows_total'] == 160000, 'Index scope')
        report_raw = z.read('handoff/report.json')
        require(report_raw == (repo / 'shared/synthetic_v2/g4/report.json').read_bytes(), 'Report bytes')
        a_report = json.loads(report_raw)
        for entry in ix['predictions']:
            key = (entry['condition_id'], entry['seed'])
            require(key in expected_runs and key not in scores, f'Unexpected/duplicate run: {key}')
            data = z.read(entry['relative_path'])
            require(sha(data) == entry['sha256'] == a_report['prediction_sha256'][entry['relative_path']],
                    f'Prediction hash: {key}')
            rows = json.loads(data)
            require(len(rows) == entry['rows'] == 10000, f'Run size: {key}')
            labels, counts, hits = {}, Counter(), Counter()
            for row in rows:
                sid, truth, pred = row['sample_id'], row['true_label'], row['predicted_label']
                require(sid not in labels, f'Duplicate sample: {key}/{sid}')
                require(type(truth) is int and type(pred) is int and 0 <= truth < 10 and 0 <= pred < 10,
                        'Label range/type')
                if key[0] == 'clip_zero_shot':
                    # The original single CLIP reference uses a three-column schema;
                    # its run/config identity is bound by the hashed index and report.
                    require(set(row) == {'sample_id', 'true_label', 'predicted_label'}, 'CLIP row schema')
                else:
                    require((row['condition_id'], row['seed']) == key, 'Row run identity')
                    require(row['config_hash'] == delivery['config_hash'], 'Row config hash')
                labels[sid] = truth
                counts[truth] += 1
                hits[truth] += int(truth == pred)
            require(set(labels) == {f'real_test_{i:05d}' for i in range(10000)}, 'Test ID coverage')
            require(counts == Counter({k: 1000 for k in range(10)}), 'Test class balance')
            if common_labels is None:
                common_labels = labels
            require(labels == common_labels, 'Cross-file truth mismatch')
            scores[key] = sum(hits.values()) / 100  # 100 * correct / 10000
            class_scores[key] = {CLASSES[k]: hits[k] / 10 for k in range(10)}
            require(abs(scores[key] / 100 - entry['accuracy_recomputed']) < 1e-12, 'A index accuracy')
            files.append({'condition': key[0], 'seed': key[1], 'rows': len(rows), 'sha256': sha(data)})
            per_run.append({'condition': key[0], 'seed': key[1], 'correct': sum(hits.values()),
                            'accuracy_pct': scores[key], 'class_correct': dict(hits)})
    require(set(scores) == expected_runs and len(files) == 16, 'Run matrix')
    summary, per_class = {}, {}
    paired = {}
    for cond in CONDITIONS:
        acc = [scores[cond, s] for s in range(3)]
        gains = [scores[cond, s] - scores['real_only', s] for s in range(3)]
        avg, sd = moments(acc)
        gain, gain_sd = moments(gains)
        summary[cond,] = dict(mean_accuracy_pct=avg, sd_accuracy_pct=sd, paired_gain_pp=gain, sd_gain_pp=gain_sd)
        paired[cond] = gains
        for cls in CLASSES:
            avg, sd = moments([class_scores[cond, s][cls] for s in range(3)])
            gain, gain_sd = moments([class_scores[cond, s][cls] - class_scores['real_only', s][cls] for s in range(3)])
            per_class[cond, cls] = dict(mean_accuracy_pct=avg, sd_accuracy_pp=sd, mean_gain_pp=gain, sd_gain_pp=gain_sd)
    contrasts = {}
    for name, a, b in [('CLIP vs Random (50)', 'clip_50', 'random_50'),
                       ('CLIP vs Random (150)', 'clip_150', 'random_150'),
                       ('150 vs 50 (Random)', 'random_150', 'random_50'),
                       ('150 vs 50 (CLIP)', 'clip_150', 'clip_50')]:
        delta = [scores[a, s] - scores[b, s] for s in range(3)]
        avg, sd = moments(delta)
        contrasts[name, a, b] = {**{f'seed_{s}_delta_pp': delta[s] for s in range(3)},
                                 'mean_delta_pp': avg, 'sample_sd_pp': sd}
    costs = json.loads((repo / 'shared/synthetic_v2/stage_costs.json').read_text())
    require(abs(math.fsum(x['seconds'] for x in costs['generation_invocations'])
                - costs['candidate_pool_production_seconds']) < 1e-9, 'Generation cost sum')
    stages = [('G3', 'SD1.5 generation', costs['candidate_pool_production_seconds']),
              ('G3', 'CLIP selection', costs['stages']['select']['seconds']),
              ('G3', 'ResNet features', costs['stages']['features']['seconds']),
              ('G3', 'Classifier training', costs['stages']['train']['seconds']),
              ('G4', 'Final evaluation', a_report['seconds'])]
    cost_rows = {(phase, stage): {'seconds': seconds, 'minutes': seconds / 60} for phase, stage, seconds in stages}
    tables = repo / 'shared/synthetic_v2/c_evaluation/tables'
    checks = {}
    for name, keys, expected, precision in [
        ('07_g4_summary.csv', ('condition',), summary, 4),
        ('08_g4_per_class.csv', ('condition', 'class_name'), per_class, 3),
        ('13_g4_direct_comparisons.csv', ('comparison', 'condition_a', 'condition_b'), contrasts, 4),
        ('12_g4_cost_summary.csv', ('phase', 'stage'), cost_rows, 4)]:
        checks[name] = compare_table(tables / name, keys, expected, precision)
    # Compare A's per-run/per-class results as a second reference, after raw recounting.
    for item in a_report['results']:
        key = item['condition_id'], item['seed']
        require(abs(scores[key] / 100 - item['accuracy']) < 1e-12, 'A per-run accuracy')
        for cls in CLASSES:
            require(abs(class_scores[key][cls] / 100 - item['per_class_accuracy'][cls]) < 1e-12, 'A per-class accuracy')
    require(abs(scores['clip_zero_shot', None] - 88.21) < 1e-12, 'Single zero-shot reference')
    # Negative controls prove that the comparator rejects wrong seed pairing and ddof=0.
    controls = {}
    for name, bad in [('wrong_seed_pairing', dict(summary[('clip_50',)])),
                      ('population_sd', dict(summary[('clip_50',)]))]:
        if name == 'wrong_seed_pairing':
            wrong = [scores['clip_50', s] - scores['real_only', (s + 1) % 3] for s in range(3)]
            bad['sd_gain_pp'] = moments(wrong)[1]
        else:
            bad['sd_accuracy_pct'] *= math.sqrt(2 / 3)
        altered = {**summary, ('clip_50',): bad}
        try:
            compare_table(tables / '07_g4_summary.csv', ('condition',), altered, 4)
        except ValueError:
            controls[name] = 'rejected_as_expected'
        else:
            raise ValueError(f'Negative control undetected: {name}')
    protected = list((repo / 'code').glob('*.py')) + [repo / 'configs/study.json', repo / 'shared/synthetic_v2/models/frozen.json']
    inputs = [repo / 'report/C_results_evaluation.md', repo / 'shared/synthetic_v2/stage_costs.json',
              repo / 'shared/synthetic_v2/g4/report.json', repo / 'shared/synthetic_v2/g4/prediction_index.json',
              repo / 'shared/synthetic_v2/g4/delivery.json']
    inputs += list(tables.glob('*.csv')) + list((repo / 'shared/synthetic_v2/c_evaluation/figures').glob('*.png'))
    total = math.fsum(x[2] for x in stages)
    result = {'status': 'pass', 'scope': 'B independent recount of released predictions; not independent GPU inference',
              'created_utc': datetime.now(timezone.utc).isoformat(), 'source_commit': subprocess.check_output(
                  ['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
              'environment': {'python': sys.version, 'platform': platform.platform(), 'dependencies': 'stdlib only'},
              'command': 'python code/reviews/review_c_g4.py --bundle runs/b_c_cross_review/input/g4_predictions_and_run_records.zip --out runs/b_c_cross_review/results',
              'zip_sha256': sha(raw_zip), 'zip_bytes': len(raw_zip), 'rows_verified': 160000, 'files': files,
              'table_checks': checks, 'negative_controls': controls,
              'paired_seed_gains_pp': paired, 'clip_zero_shot_accuracy_pct': scores['clip_zero_shot', None],
              'recorded_stage_seconds': total, 'generation_share_pct': stages[0][2] / total * 100,
              'input_sha256': {str(p.relative_to(repo)).replace('\\', '/'): sha(p.read_bytes()) for p in inputs},
              'protected_sha256': {str(p.relative_to(repo)).replace('\\', '/'): sha(p.read_bytes()) for p in protected},
              'limits': ['No model training, image generation, GPU inference or parameter changes.',
                         'Shared test truth consistency checked, not independently redownloaded CIFAR test labels.',
                         '3 seeds; sample SD is not a confidence interval or significance test.',
                         'Existing B strict feature mismatch remains unresolved globally.',
                         'No human annotations or non-author trial performed by this review.']}
    (out / 'review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'per_run.json').write_text(json.dumps(per_run, indent=2) + '\n', encoding='utf-8')
    for name, keynames, data in [('summary.csv', ('condition',), summary),
                                 ('per_class.csv', ('condition', 'class_name'), per_class),
                                 ('contrasts.csv', ('comparison', 'condition_a', 'condition_b'), contrasts)]:
        with (out / name).open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[*keynames, *next(iter(data.values()))])
            writer.writeheader()
            for key, row in data.items():
                writer.writerow({**dict(zip(keynames, key)), **row})
    print(json.dumps({'status': 'pass', 'rows': 160000, 'table_checks': checks,
                      'negative_controls': controls, 'out': str(out)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    review(args.repo.resolve(), args.bundle, args.out)
