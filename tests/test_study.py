"""Analysis invariants using small in-memory records, not model observations."""
import copy
import importlib.util
from pathlib import Path
import unittest

from behavior_lab.metrics import METRIC_VERSION
from behavior_lab.protocol import load_plan

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('study_reproduce', ROOT/'studies/standard-benchmarks/reproduce.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class StudyAnalysisTests(unittest.TestCase):
    def test_complete_plan_and_score_integrity(self):
        plan = load_plan(ROOT/'studies/standard-benchmarks/protocol.json')
        cases = {c['id']:c for c in plan['spec']['cases']}
        rows = []
        for job in plan['jobs']:
            case = cases[job['case']]
            row = {**job,'category':case['category'],'plan_sha256':plan['sha256'],
                   'valid':True,'observed_models':[job['model']],'complete':True,'raw_complete':True,
                   'exit_code':0,'base_text_matches_protocol':True,'metric_version':METRIC_VERSION,
                   'malformed_lines':0,'calls':[],'inline_script':False,'awk_code':False,
                   'aux_code_with_awk':False,'answer':'FINAL: '+case['target'],
                   'correct':True,'format_compliant':True,'parsed_answer':case['target'],
                   'observed_efforts':['high'],'observed_sandbox_types':['workspace-write'],
                   'session_cli_version':'0.153.4'}
            rows.append(row)
        study.validate_rows(plan,rows)
        with self.assertRaises(AssertionError): study.validate_rows(plan,rows[:-1])
        bad = copy.deepcopy(rows)
        bad[0]['correct'] = False
        with self.assertRaises(AssertionError): study.validate_rows(plan,bad)
        bad = copy.deepcopy(rows)
        bad[0]['observed_efforts'] = ['low']
        with self.assertRaises(AssertionError): study.validate_rows(plan,bad)
        bad = copy.deepcopy(rows)
        bad[0]['valid'] = False
        with self.assertRaises(AssertionError): study.validate_rows(plan,bad)
        for k in study.METRICS: bad[0][k] = None
        study.validate_rows(plan,bad)

    def test_zero_events_do_not_imply_zero_uncertainty(self):
        lower,upper = study.wilson(0,24)
        self.assertAlmostEqual(lower,0)
        self.assertGreater(upper,.13)
        self.assertLess(upper,.14)
        lower_one,upper_one = study.wilson(24,24)
        self.assertAlmostEqual(lower_one,1-upper)
        self.assertAlmostEqual(upper_one,1)

    def test_interaction_sign_and_missingness(self):
        # Case 1: A changes +1, B changes 0. Case 2: A changes 0, B +1.
        values = {'q1':((False,False,True),(True,False,True)),
                  'q2':((False,False,False),(False,False,True))}
        rows = [{'case':case,'model':m,'condition':c,'valid':True,'aux_code_with_awk':values[case][mi][ci]}
                for case in values for mi,m in enumerate(study.MODELS) for ci,c in enumerate(study.CONDITIONS)]
        result = study.interactions(rows)['code_preferred']
        self.assertEqual(result['interaction_b_minus_a'],0)
        self.assertEqual(result['a_change'],.5)
        self.assertEqual(result['b_change'],.5)
        next(r for r in rows if r['case']=='q2' and r['model']==study.MODELS[1] and r['condition']=='code_preferred')['valid']=False
        result = study.interactions(rows)['code_preferred']
        self.assertEqual(result['interaction_b_minus_a'],-1)
        self.assertEqual(result['excluded_questions'],['q2'])
        self.assertEqual(result['matched_questions'],1)
        bounds = study.missing_data_bounds(rows)['code_preferred']
        self.assertEqual(bounds['difference_b_minus_a_bounds'],[0,.5])


if __name__=='__main__':
    unittest.main()
