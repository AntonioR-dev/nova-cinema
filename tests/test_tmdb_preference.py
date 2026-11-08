"""Contract checks for the shared phone/TV runtime credential preference."""
import pathlib
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANDROID = '{http://schemas.android.com/apk/res/android}'
APP = '{http://schemas.android.com/apk/res-auto}'


class TmdbPreferenceTest(unittest.TestCase):
    def test_editable_persistent_key_is_in_scraper_settings(self):
        root = ET.parse(ROOT / 'res/xml/preferences_video.xml').getroot()
        category = next(e for e in root if e.get(ANDROID + 'key') == 'scraper_category')
        matches = [e for e in category if e.get(ANDROID + 'key') == 'tmdb_api_key']
        self.assertEqual(len(matches), 1, 'missing shared TMDb API key preference')
        pref = matches[0]
        self.assertEqual(pref.tag, 'EditTextPreference')
        self.assertEqual(pref.get(ANDROID + 'persistent'), 'true')
        self.assertEqual(pref.get(ANDROID + 'defaultValue'), '')
        self.assertEqual(pref.get(ANDROID + 'summary'), '@string/preferences_tmdb_api_key_summary')
        self.assertNotEqual(pref.get(APP + 'useSimpleSummaryProvider'), 'true',
                            'never show the stored credential as the row summary')

    def test_guidance_explains_v3_key_and_fallback(self):
        path = ROOT / 'res/values/strings_tmdb_preferences.xml'
        self.assertTrue(path.exists(), 'missing TMDb preference strings')
        values = {e.get('name'): e.text for e in ET.parse(path).getroot()}
        summary = values['preferences_tmdb_api_key_summary'] or ''
        self.assertIn('v3', summary)
        self.assertIn('blank', summary)
        self.assertIn('no bundled key', summary)

    def test_tv_uses_the_same_preferences_as_phone(self):
        src = ROOT / 'src/main/java/com/archos/mediacenter/video'
        tv = (src / 'leanback/settings/VideoSettingsFragment.java').read_text()
        common = (src / 'utils/VideoPreferencesCommon.java').read_text()
        self.assertIn('extends LeanbackPreferenceFragmentCompat', tv)
        self.assertIn('mPreferencesCommon.onCreatePreferences(savedInstanceState, rootKey)', tv)
        self.assertIn('addPreferencesFromResource(R.xml.preferences_video)', common)
        self.assertNotIn('removePreference(findPreference("tmdb_api_key"))', common)


if __name__ == '__main__':
    unittest.main()
