"""Static handoff compatibility checks; these do not prove agent compliance."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('delivery_installer', ROOT / 'scripts/install_skill.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class DeliveryReportingTests(unittest.TestCase):
    def test_default_reporting_and_explicit_acceptance_remain_distinct(self):
        workflow = (ROOT / 'WORKFLOW.md').read_text()
        result = (ROOT / 'RESULT.md').read_text()
        for text in (workflow, result):
            self.assertIn('without an interactive acceptance prompt', text)
            self.assertIn('requested by the owner or required by project policy for high-risk delivery', text)
        self.assertIn('human acceptance PENDING', workflow)
        self.assertIn('**Decision:** PENDING', result)
        self.assertIn('only from an explicit human decision', result)
        self.assertIn('Acceptance does not authorize push', result)
        self.assertIn('One initial human plan approval covers all in-scope micro-slices', workflow)

    def test_prompt_and_interval_attribution_require_observation(self):
        for name in ('WORKFLOW.md', 'RESULT.md'):
            text = (ROOT / name).read_text()
            self.assertIn('active execution', text)
            self.assertIn('human waiting', text)
            self.assertIn('native CLI permission prompts separately from BOV plan-approval prompts', text)
            self.assertIn('UNKNOWN', text)
        self.assertIn('complete observed window', (ROOT / 'WORKFLOW.md').read_text())
        for name in ('WORKFLOW.md', 'RESULT.md'):
            text = (ROOT / name).read_text()
            self.assertIn('complete operator-maintained count or CLI trace', text)
            self.assertIn('UNKNOWN', text)

    def test_bundle_carries_updated_handoff_without_changing_pending_templates(self):
        bundle = installer.payload()
        for name in ('WORKFLOW.md', 'RESULT.md'):
            self.assertEqual(bundle['framework/' + name], (ROOT / name).read_bytes())
        self.assertIn(b'without an interactive acceptance prompt', bundle['framework/WORKFLOW.md'])
        self.assertIn(b'**Decision:** PENDING', bundle['framework/RESULT.md'])


if __name__ == '__main__':
    unittest.main()
