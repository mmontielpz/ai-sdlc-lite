"""Deterministic checks for the checkpoint interface and installed guidance."""

import importlib.util
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('micro_installer', ROOT / 'scripts/install_skill.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class MicroCycleGuidanceTests(unittest.TestCase):
    def test_checkpoint_has_all_seven_fields_in_order(self):
        text = (ROOT / 'WORKFLOW.md').read_text()
        section = text.split('### Timeboxed BOV micro-cycles\n', 1)[1].split('\n## ', 1)[0]
        template = re.search(r'```text\n(.*?)\n```', section, re.S).group(1)
        self.assertEqual([line.split(':', 1)[0] for line in template.splitlines()],
                         ['MICRO-SLICE', 'ELAPSED', 'STATUS', 'CHANGES',
                          'VERIFICATION', 'NEXT', 'RISKS'])
        self.assertIn('measured / UNKNOWN', template)
        self.assertIn('PASS / PARTIAL / BLOCKED', template)

    def test_budget_and_retry_boundaries_are_explicit(self):
        text = (ROOT / 'WORKFLOW.md').read_text()
        section = text.split('### Timeboxed BOV micro-cycles\n', 1)[1].split('\n## ', 1)[0]
        self.assertIn('**3 minutes**', section)
        self.assertIn('**5 minutes per cycle**', section)
        self.assertIn('two unsuccessful retries of the same failure', section)
        self.assertIn('three failed attempts', section)
        self.assertIn('Timing is **advisory**', section)
        self.assertIn('Final human delivery acceptance remains separate', section)

    def test_installed_workflow_is_current_and_reachable_from_skill(self):
        bundle = installer.payload()
        self.assertEqual(bundle['framework/WORKFLOW.md'], (ROOT / 'WORKFLOW.md').read_bytes())
        links = installer.LINK.findall(bundle['SKILL.md'].decode())
        self.assertIn('framework/WORKFLOW.md', links)
        self.assertIn(b'### Timeboxed BOV micro-cycles', bundle['framework/WORKFLOW.md'])
        # The existing native entry delegates to WORKFLOW without changing permissions.
        source = ROOT / '.agents/skills/ai-sdlc-lite/SKILL.md'
        self.assertIn('../../../WORKFLOW.md', installer.LINK.findall(source.read_text()))
        self.assertEqual((source.parent / '../../../WORKFLOW.md').resolve(), ROOT / 'WORKFLOW.md')


if __name__ == '__main__':
    unittest.main()
