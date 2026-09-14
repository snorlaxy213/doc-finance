"""Regression checks for publication ordering independent of checkout timestamps."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_report_hub as hub


class PublicationOrderTests(unittest.TestCase):
    def test_legacy_snapshot_survives_touch_and_style_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            latest = root / '公司_000001_基本面分析_最新.html'
            latest.write_text('<title>公司</title>new style', encoding='utf-8')
            latest.with_suffix('.md').write_text('same research', encoding='utf-8')
            snapshot = root / '公司_000001_基本面分析_20260913_140000.html'
            snapshot.write_text('old style', encoding='utf-8')
            snapshot.with_suffix('.md').write_text('same research', encoding='utf-8')
            before = hub.report_timestamp(latest, latest.read_text(encoding='utf-8'))
            os.utime(latest, (1, 1))
            self.assertEqual(before, hub.report_timestamp(latest, latest.read_text(encoding='utf-8')))
            self.assertEqual(before, ('2026-09-13T14:00:00+08:00', 'minute'))

    def test_republication_moves_existing_company_first_and_keeps_one_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidates = []
            for code, name, stamp in [('000001', 'old', '2026-09-10T10:00:00+08:00'),
                                      ('000002', 'other', '2026-09-12T10:00:00+08:00'),
                                      ('000001', 'new', '2026-09-13T10:00:00+08:00')]:
                source = root / f'{name}_{code}_基本面分析_最新.html'
                source.write_text(f'<head><title>{name}</title><meta name="report-generated-at" content="{stamp}"></head><body>{name}</body>', encoding='utf-8')
                candidates.append((code, source))
            with patch.object(hub, 'REPO_ROOT', root), patch.object(hub, 'report_candidates', return_value=candidates):
                catalog = hub.build_catalog({'financial_disclaimer': '', 'publication': {
                    'access_mode': 'public', 'included_root': 'reports', 'included_variant': 'latest'
                }}, root / 'output')
            self.assertEqual([item['code'] for item in catalog['items']], ['000001', '000002'])
            self.assertIn('<title>new</title>', (root / 'output/reports/000001/index.html').read_text(encoding='utf-8'))

    def test_missing_timestamp_is_not_fabricated(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(hub.report_timestamp(Path(directory) / 'latest.html', '<head></head>'), ('', 'unknown'))


if __name__ == '__main__':
    unittest.main()
