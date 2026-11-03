"""Data-free checks of projection mathematics and archived table arithmetic."""
from pathlib import Path
import ast, csv, hashlib, json, unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

class ReproductionChecks(unittest.TestCase):
    def test_projection_against_matrix_propagation(self):
        tree=ast.parse((ROOT/'src/run_final.py').read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='projection')
        namespace={'np':np,'R':.03}
        exec(compile(ast.Module(body=[function],type_ignores=[]),'projection','exec'),namespace)
        for rates in [[0,0],[1,1],[0,1],[1,0],[.23738540123965116,.4884411781316796],*np.random.default_rng(27).uniform(0,1,(30,2))]:
            r,p=rates; matrix=np.array([[1-r,r],[1-p,p]])
            lo=np.array([1.,0.]);hi=np.array([0.,1.]);expected=[]
            for k in range(5):
                expected.append((hi[1]-lo[1])/1.03**(k+.5));lo=lo@matrix;hi=hi@matrix
            factor,annual=namespace['projection'](rates)
            np.testing.assert_allclose(annual,expected,atol=1e-14)
            self.assertAlmostEqual(float(factor),sum(expected),places=13)

    def test_archived_rate_arithmetic(self):
        with (ROOT/'results/primary/FINAL_100_75_50_AND_BREAKEVEN.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),12)
        for r in rows:
            expected=float(r['annual_symptom_state_diff_2024usd'])*float(r['discounted_state_year_multiplier'])*(1-float(r['spontaneous_remission_assumption']))*float(r['recognition_pct'])/100
            self.assertAlmostEqual(float(r['signed_model_credit_usd']),expected,places=7)
            self.assertAlmostEqual(float(r['nonnegative_payment_candidate_usd']),max(0,expected),places=7)

    def test_recorded_result_files_preserved(self):
        manifest=json.loads((ROOT/'docs/audit/REORGANIZATION_MANIFEST.json').read_text())
        for r in manifest['files']:
            if r['destination'] and '/results/' in r['original']:
                self.assertEqual(hashlib.sha256((ROOT/r['destination']).read_bytes()).hexdigest(),r['original_sha256'],r['destination'])

if __name__=='__main__':unittest.main()
