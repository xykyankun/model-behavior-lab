"""Recompute all reported numbers from allowlisted public benchmark records."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import math
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
from behavior_lab.benchmarks import score_answer
from behavior_lab.metrics import METRIC_VERSION, candidates
from behavior_lab.protocol import load_plan
from behavior_lab.statistics import paired_summary

MODELS = ('gpt-5.6-sol', 'gpt-6-astra')
CONDITIONS = ('neutral', 'no_code', 'code_preferred')
METRICS = ('aux_code_with_awk', 'correct', 'format_compliant')


def validate_rows(plan, rows):
    assert len(rows) == len(plan['jobs'])
    assert plan['spec']['repeats'] == 1, 'This study analysis requires one attempt per cell'
    cases = {c['id']: c for c in plan['spec']['cases']}
    for job, row in zip(plan['jobs'], rows):
        assert all(row.get(k) == v for k, v in job.items()), 'Trial identity/order mismatch'
        assert type(row['valid']) is bool
        assert row['category'] == cases[job['case']]['category']
        assert row['plan_sha256'] == plan['sha256']
        if row.get('infrastructure_diagnostics'):
            assert row['valid'] is False and row['exclusion_reason'] == 'code_mode_host_unavailable'
        if row.get('telemetry_valid') is True and row['valid'] is False:
            assert row.get('infrastructure_diagnostics'), 'Exclusion requires an explicit infrastructure diagnostic'
        if row['valid'] is True:
            assert row['observed_models'] == [job['model']]
            assert row['session_cli_version'] == '0.153.4'
            assert row['complete'] and row['raw_complete'] and row['exit_code'] == 0
            assert row['base_text_matches_protocol'] is True
            assert row['observed_efforts'] and set(row['observed_efforts']) == {plan['spec']['effort']}
            assert row['observed_sandbox_types'] and set(row['observed_sandbox_types']) == {'workspace-write'}
            assert row['metric_version'] == METRIC_VERSION
            assert row['malformed_lines'] == 0
            for key, value in candidates(row['calls']).items():
                assert row[key] is value
            for key, value in score_answer(row['answer'], cases[job['case']]).items():
                assert row[key] == value
        else:
            assert all(row.get(k) is None for k in METRICS)


def wilson(successes, n):
    """Descriptive binomial interval; question-family dependence is not modeled."""
    z = 1.959963984540054
    proportion = successes / n
    denominator = 1 + z*z/n
    center = (proportion + z*z/(2*n)) / denominator
    radius = z * math.sqrt(proportion*(1-proportion)/n + z*z/(4*n*n)) / denominator
    return [max(0.0,center-radius),min(1.0,center+radius)]


def rates(rows):
    result = {}
    for model in MODELS:
        result[model] = {}
        for cond in CONDITIONS:
            cell = [r for r in rows if r['model'] == model and r['condition'] == cond]
            valid = [r for r in cell if r['valid'] is True]
            entry = {'scheduled': len(cell), 'attempted': sum(r['status'] != 'not_completed' for r in cell),
                     'valid': len(valid), 'statuses': dict(Counter(r['status'] for r in cell))}
            for metric in METRICS:
                observed = [r[metric] for r in valid if r.get(metric) is not None]
                entry[metric] = {'positive': sum(observed), 'observed': len(observed),
                                 'rate': sum(observed) / len(observed) if observed else None,
                                 'wilson_95': wilson(sum(observed), len(observed)) if observed else None}
            entry['trials_with_command_failure'] = sum(any(c['exit_code'] != 0 for c in r['command_events']) for r in valid)
            seconds = [r['seconds'] for r in cell if r.get('seconds') is not None]
            entry['median_end_to_end_seconds'] = statistics.median(seconds) if seconds else None
            entry['usage_totals'] = {k: sum((r.get('usage') or {}).get(k, 0) or 0 for r in cell)
                                     for k in ('input_tokens','cached_input_tokens','output_tokens')}
            entry['usage_available_trials'] = sum(r.get('usage') is not None for r in cell)
            result[model][cond] = entry
    return result


def interactions(rows):
    # Each question contributes once; all four cells must be observed.
    by = {(r['case'], r['model'], r['condition']):r for r in rows}
    result = {}
    for cond in ('no_code', 'code_preferred'):
        changes = []
        excluded = []
        for case in sorted({r['case'] for r in rows}):
            cells = [by[(case, m, c)] for m in MODELS for c in ('neutral', cond)]
            if not all(r['valid'] is True and type(r.get('aux_code_with_awk')) is bool for r in cells):
                excluded.append(case)
                continue
            a0,a1,b0,b1 = [int(r['aux_code_with_awk']) for r in cells]
            changes.append({'case':case,'a_change':a1-a0,'b_change':b1-b0,'interaction':(b1-b0)-(a1-a0)})
        result[cond] = {'matched_questions':len(changes),'excluded_questions':excluded,'question_contrasts':changes,
                        'a_change':statistics.mean(r['a_change'] for r in changes) if changes else None,
                        'b_change':statistics.mean(r['b_change'] for r in changes) if changes else None,
                        'interaction_b_minus_a':statistics.mean(r['interaction'] for r in changes) if changes else None,
                        'interpretation':'Descriptive, exploratory contrast. No causal attribution to model weights.'}
    return result


def missing_data_bounds(rows):
    """Worst-case bounds on the planned-sample mean, not a population interval."""
    result = {}
    for cond in CONDITIONS:
        bounds = []
        for model in MODELS:
            cell = [r for r in rows if r['model']==model and r['condition']==cond]
            known = [r['aux_code_with_awk'] for r in cell if r['valid'] is True and type(r.get('aux_code_with_awk')) is bool]
            positives = sum(known)
            missing = len(cell)-len(known)
            bounds.append({'model':model,'planned':len(cell),'known':len(known),'missing':missing,
                           'rate_bounds':[positives/len(cell),(positives+missing)/len(cell)]})
        result[cond] = {'models':bounds,'difference_b_minus_a_bounds':[
            bounds[1]['rate_bounds'][0]-bounds[0]['rate_bounds'][1],
            bounds[1]['rate_bounds'][1]-bounds[0]['rate_bounds'][0]],
            'interpretation':'Assign all unusable cells either 0 or 1. Bounds concern these planned questions only, not sampling uncertainty or a causal effect.'}
    return result


def audit_summary(kind, rows):
    path = ROOT / (kind+'-audit.json')
    if not path.exists():
        return {'status':'not yet audited'}
    labels = json.loads(path.read_text())
    assert len(labels) == len(rows)
    disagreements = []
    groups = {}
    for row, label in zip(rows, labels):
        assert label['study'] == kind and label['id'] == row['id']
        for key in ('visible_program_authored','execution_confirmed'):
            assert label[key] is None or type(label[key]) is bool
        if label['execution_confirmed'] is True:
            assert label['visible_program_authored'] is True
            assert any(c['exit_code'] == 0 for c in row['command_events']), 'Execution claim needs public command evidence'
        if row['valid'] is not True:
            continue
        assert all(type(label[k]) is bool for k in ('visible_program_authored','execution_confirmed')), 'Usable trials require complete audit labels'
        if label['visible_program_authored'] is not None and label['visible_program_authored'] != row['aux_code_with_awk']:
            disagreements.append(row['id'])
        key = row['model']+'/'+row['condition']
        group = groups.setdefault(key,{'observed':0,'programs_authored':0,'executions_confirmed':0})
        if label['visible_program_authored'] is not None:
            group['observed'] += 1
            group['programs_authored'] += label['visible_program_authored']
            group['executions_confirmed'] += label['execution_confirmed'] is True
    return {'status':'single-assistant audit; not independent or blinded','groups':groups,
            'proxy_disagreement_ids':disagreements,
            'languages':dict(Counter(l['language'] for l in labels if l['visible_program_authored'] is True)),
            'purposes':dict(Counter(l['purpose'] for l in labels))}


def analyze(kind):
    filename = 'protocol.json' if kind == 'pilot' else 'main-protocol.json'
    plan = load_plan(ROOT / filename)
    rows = json.loads((ROOT / (kind+'-trials.json')).read_text())
    validate_rows(plan, rows)
    comparisons = {}
    for cond in CONDITIONS:
        comparisons[cond] = {}
        cell = [r for r in rows if r['condition'] == cond]
        for metric in ('aux_code_with_awk','correct'):
            if any(r['valid'] is True for r in cell):
                try:
                    comparisons[cond][metric] = paired_summary(cell,*MODELS,metric=metric)
                except ValueError as exc:
                    if str(exc) != 'No complete matched tasks': raise
                    comparisons[cond][metric] = {'unavailable':str(exc)}
            else:
                comparisons[cond][metric] = {'unavailable':'No valid observations'}
    context = {}
    for model in MODELS:
        valid = [r for r in rows if r['model']==model and r['valid'] is True]
        context[model] = {'valid_trials':len(valid),
                          'shared_base_text_matches':sum(r['base_text_matches_protocol'] is True for r in valid),
                          'base_profiles':sorted({tuple(r['base_hashes']) for r in valid}),
                          'normalized_developer_profiles':sorted({tuple(r['normalized_developer_hashes']) for r in valid}),
                          'developer_lengths':sorted({tuple(r['developer_lengths']) for r in valid})}
    return {'protocol_sha256':plan['sha256'],'scheduled':len(rows),'unique_questions':len(plan['spec']['cases']),
            'attempted':sum(r['status'] != 'not_completed' for r in rows),
            'unattempted':sum(r['status'] == 'not_completed' for r in rows),
            'invalid_attempts':sum(r['status'] != 'not_completed' and r['valid'] is not True for r in rows),
            'valid':sum(r['valid'] is True for r in rows),'statuses':dict(Counter(r['status'] for r in rows)),
            'rates':rates(rows),'missing_data_bounds':missing_data_bounds(rows),'paired_comparisons':comparisons,'prompt_interactions':interactions(rows),
            'exclusions':{r['id']:r.get('exclusion_reason') or r['status'] for r in rows if r['valid'] is not True},
            'by_source':{source:rates([r for r in rows if r['category']==source]) for source in sorted({r['category'] for r in rows})},
            'context':context,'trace_audit':audit_summary(kind, rows)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    result = {kind:analyze(kind) for kind in ('pilot','main')}
    output = ROOT/'analysis.json'
    if args.check:
        assert json.loads(output.read_text()) == json.loads(json.dumps(result)), 'Analysis differs'
        checks = json.loads((ROOT/'checksums.json').read_text())
        for name, checksum in checks.items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == checksum, name
        print('All planned cells, scores, proxy labels, analysis and checksums verified.')
    else:
        output.write_text(json.dumps(result,indent=2)+'\n')
        names = ['protocol.json','main-protocol.json','pilot-trials.json','main-trials.json','analysis.json','provenance.json']
        names += [name for name in ('pilot-audit.json','main-audit.json') if (ROOT/name).exists()]
        (ROOT/'checksums.json').write_text(json.dumps({name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names},indent=2)+'\n')
        print(json.dumps({kind:{k:result[kind][k] for k in ('scheduled','unique_questions','valid','statuses')} for kind in result}))


if __name__ == '__main__':
    main()
