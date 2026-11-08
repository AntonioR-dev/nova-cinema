"""Fork providers must coexist with the original NOVA installation."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
ANDROID = '{http://schemas.android.com/apk/res/android}'
APP = 'dev.antonior.novacinema'

class ForkAuthorityTest(unittest.TestCase):
    def test_fork_does_not_join_upstream_shared_uid(self):
        manifest = ET.parse(ROOT / 'AndroidManifest.xml').getroot()
        self.assertNotIn(ANDROID + 'sharedUserId', manifest.attrib)
        self.assertNotIn(ANDROID + 'sharedUserMaxSdkVersion', manifest.attrib)

    def test_manifest_providers_are_scoped_to_fork(self):
        manifest = ET.parse(ROOT / 'AndroidManifest.xml').getroot()
        for provider in manifest.findall('.//provider'):
            for authority in provider.get(ANDROID + 'authorities', '').split(';'):
                expanded = authority.replace('${applicationId}', APP)
                self.assertTrue(expanded.startswith(APP + '.'), expanded)

    def test_database_constants_match_fork_manifest(self):
        source = (ROOT.parent / 'MediaLib/src/com/archos/mediaprovider/ArchosMediaCommon.java').read_text()
        for name, suffix in [('AUTHORITY_VIDEO', 'media.video'), ('AUTHORITY_SCRAPER', 'media.scraper')]:
            match = re.search(r'\b' + name + r'\s*=\s*"([^"]+)"', source)
            self.assertIsNotNone(match)
            assert match is not None
            value = match.group(1)
            self.assertEqual(APP + '.' + suffix, value)

    def test_searchable_metadata_matches_fork_providers(self):
        for filename, expected in [('searchable_video.xml', APP + '.browser.search'), ('androidtv_searchable_video.xml', APP + '.leanback.search.VideoSearchProvider')]:
            xml = ET.parse(ROOT / 'res/xml' / filename).getroot()
            self.assertEqual(expected, xml.get(ANDROID + 'searchSuggestAuthority'))

if __name__ == '__main__':
    unittest.main()
