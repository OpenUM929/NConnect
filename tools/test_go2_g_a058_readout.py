import tempfile
import unittest
from pathlib import Path
import go2_g_a058_readout as r

class ReadoutTests(unittest.TestCase):
    def test_individual_boundaries(self):
        self.assertEqual(r.individual(50,5),'JOINT_CANDIDATE_FOR_REVIEW')
        for a,b in [(49,5),(50,6)]: self.assertEqual(r.individual(a,b),'NOT_JOINT_CANDIDATE')
        self.assertEqual(r.individual(None,0),'INCONCLUSIVE_MISSING')
    def test_setting_boundaries(self):
        for a,b,want in [(50,50,'REPRODUCED'),(10,10,'DEGRADED'),(10,11,'INCONCLUSIVE'),(77,0,'INCONCLUSIVE'),(77,None,'NOT_YET')]:
            self.assertEqual(r.setting(a,b),want)
    def test_individual_survives_mixed_seeds(self):
        self.assertEqual(r.individual(77,0),'JOINT_CANDIDATE_FOR_REVIEW')
        self.assertEqual(r.setting(77,0),'INCONCLUSIVE')
    def test_yaw_boundaries(self):
        self.assertEqual([r.yaw_band(v) for v in [5,6,14,15,None]],['PROTECTED','PARTIAL','PARTIAL','REPRODUCED','MISSING'])
    def test_missing_partial_and_marker_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); key='a043_seed43'
            self.assertEqual(r.read(key,p)['run_state'],'NOT_RECOVERED')
            arm=p/f'go2_g_a058_{key}';arm.mkdir()
            self.assertEqual(r.read(key,p)['run_state'],'UNREADABLE_RUN')
            (arm/'RESULT_STATUS.txt').write_text('RESULT_STATE=FULL\nCOLLECTION_STATUS=FULL_69_COMPLETE\n')
            self.assertEqual(r.read(key,p)['run_state'],'INCOMPLETE_DATA')

if __name__=='__main__': unittest.main()
