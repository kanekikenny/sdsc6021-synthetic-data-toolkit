"""Compare two completed candidate-label forms without changing their answers."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path

FIELDS = ('blind_id', 'target_class', 'image_path', 'judgment', 'note')
CHOICES = ('correct', 'wrong', 'uncertain')


def read_form(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f'Unexpected columns: {path.name}')
        rows = list(reader)
    expected_ids = {f'R{index:03d}' for index in range(1, 101)}
    ids = [row['blind_id'] for row in rows]
    if len(rows) != 100 or set(ids) != expected_ids or len(set(ids)) != 100:
        raise ValueError(f'Expected 100 unique R001-R100 records: {path.name}')
    for row in rows:
        if row['judgment'] not in CHOICES:
            raise ValueError(f'Blank/invalid judgment: {path.name}/{row["blind_id"]}')
        if row['image_path'] != f'images/{row["blind_id"]}.png':
            raise ValueError(f'Unexpected image path: {path.name}/{row["blind_id"]}')
    classes = Counter(row['target_class'] for row in rows)
    if len(classes) != 10 or set(classes.values()) != {10}:
        raise ValueError(f'Expected ten images per class: {path.name}')
    return {row['blind_id']: row for row in rows}


def calculate(first: Path, second: Path, out: Path) -> dict:
    a, b = read_form(first), read_form(second)
    counts_a, counts_b = Counter(), Counter()
    confusion = {label: {other: 0 for other in CHOICES} for label in CHOICES}
    paired, classwise = [], {}
    for blind_id in sorted(a):
        x, y = a[blind_id], b[blind_id]
        if any(x[field] != y[field] for field in FIELDS[:3]):
            raise ValueError(f'Form metadata mismatch: {blind_id}')
        label_a, label_b = x['judgment'], y['judgment']
        counts_a[label_a] += 1
        counts_b[label_b] += 1
        confusion[label_a][label_b] += 1
        agreed = label_a == label_b
        cls = x['target_class']
        detail = classwise.setdefault(cls, {'images': 0, 'agreements': 0})
        detail['images'] += 1
        detail['agreements'] += int(agreed)
        paired.append({'blind_id': blind_id, 'target_class': cls, 'image_path': x['image_path'],
                       'judgment_1': label_a, 'judgment_2': label_b, 'agreement': str(agreed).lower(),
                       'note_1': x['note'], 'note_2': y['note']})
    n = len(paired)
    agreements = sum(confusion[label][label] for label in CHOICES)
    observed = Fraction(agreements, n)
    expected = Fraction(sum(counts_a[label] * counts_b[label] for label in CHOICES), n * n)
    kappa = None if expected == 1 else float((observed - expected) / (1 - expected))
    for detail in classwise.values():
        detail['agreement_rate'] = detail['agreements'] / detail['images']
    result = {
        'schema_version': 1,
        'status': 'computed_from_two_completed_forms',
        'images': n,
        'judgments_total': n * 2,
        'agreement_count': agreements,
        'disagreement_count': n - agreements,
        'agreement_rate': float(observed),
        'agreement_percent': 100 * float(observed),
        'judgment_counts': {'annotator_1': {key: counts_a[key] for key in CHOICES},
                            'annotator_2': {key: counts_b[key] for key in CHOICES}},
        'notes_nonempty': {'annotator_1': sum(bool(row['note'].strip()) for row in a.values()),
                           'annotator_2': sum(bool(row['note'].strip()) for row in b.values())},
        'confusion_matrix': confusion,
        'per_class': classwise,
        'disagreement_ids': [row['blind_id'] for row in paired if row['agreement'] == 'false'],
        'chance_agreement': float(expected),
        'cohen_kappa': kappa,
        'cohen_kappa_status': ('undefined_expected_agreement_is_one' if kappa is None else 'defined'),
        'input_sha256': {'annotator_1': hashlib.sha256(first.read_bytes()).hexdigest(),
                         'annotator_2': hashlib.sha256(second.read_bytes()).hexdigest()},
        'scope': 'Agreement of target-class recognizability judgments on the same 100 sampled candidates.',
        'limits': [
            'Correct means recognizable target class, including images with structural defects.',
            'Optional free-text notes are retained; their counts are not exhaustive defect rates.',
            'When both forms use only correct, perfect observed agreement does not show ability to distinguish wrong/uncertain cases; kappa is undefined.',
            'This computation does not verify how independently the forms were completed.',
            'No training-data curation, model change, final evaluation or non-author usability trial is performed.'
        ],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / 'agreement.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    with (out / 'paired_annotations.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(paired[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(paired)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first', type=Path, required=True)
    parser.add_argument('--second', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    summary = calculate(args.first, args.second, args.out)
    print(json.dumps({key: summary[key] for key in ['images', 'agreement_count', 'disagreement_count',
                                                   'agreement_percent', 'notes_nonempty', 'cohen_kappa_status']}, ensure_ascii=False))
