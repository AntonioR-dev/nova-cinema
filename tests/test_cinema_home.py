"""Host-side resource contracts; no Android SDK required.
Run: python -m unittest discover -s tests -p 'test_cinema_home.py' -v
These are not device or compilation tests.
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = '{http://schemas.android.com/apk/res/android}'


class CinemaHomeLayoutTest(unittest.TestCase):
    def test_hero_and_existing_browse_have_separate_nonfocusable_regions(self):
        layout = ROOT / 'res/layout/cinema_home.xml'
        self.assertTrue(layout.exists(), 'Native cinematic home layout is missing')
        root = ET.parse(layout).getroot()
        views = {v.get(ANDROID + 'id', '').replace('@+id/', ''): v for v in root.iter()}
        for name in ('cinema_backdrop', 'cinema_hero_title', 'cinema_hero_overview',
                     'cinema_browse_content'):
            self.assertIn(name, views)
        self.assertEqual('centerCrop', views['cinema_backdrop'].get(ANDROID + 'scaleType'))
        self.assertEqual('false', views['cinema_backdrop'].get(ANDROID + 'focusable'))
        self.assertEqual('3', views['cinema_hero_overview'].get(ANDROID + 'maxLines'))
        self.assertEqual('end', views['cinema_hero_title'].get(ANDROID + 'ellipsize'))
        hero = next(v for v in root if v.tag == 'LinearLayout')
        dp = lambda view, key: float(view.get(ANDROID + key, '0dp').removesuffix('dp'))
        hero_bottom = dp(hero, 'layout_marginTop') + dp(hero, 'layout_height')
        browse_top = dp(views['cinema_browse_content'], 'layout_marginTop')
        self.assertGreaterEqual(browse_top - hero_bottom, 16,
                                'Hero and shelves need a real gap, not overlapping fixed regions')
        self.assertEqual('match_parent', hero.get(ANDROID + 'layout_width'))
        self.assertGreater(dp(hero, 'layout_marginEnd'), 0)
        self.assertEqual('match_parent', views['cinema_hero_overview'].get(ANDROID + 'layout_width'))
        self.assertEqual('0dp', views['cinema_hero_overview'].get(ANDROID + 'layout_height'))
        self.assertEqual('1', views['cinema_hero_overview'].get(ANDROID + 'layout_weight'))
        # Resource geometry at a 960x540dp TV, not a substitute for device text measurement.
        self.assertGreaterEqual(540 - browse_top, 300, 'Leave a usable first shelf viewport')
        self.assertGreaterEqual(dp(hero, 'layout_height'), 192,
                                'Allow category + two-line 32sp title + bounded overview')
        for viewport_width in (640, 960):
            available_width = viewport_width - dp(hero, 'layout_marginStart') - dp(hero, 'layout_marginEnd')
            self.assertGreater(available_width, 0)
        self.assertEqual('2', views['cinema_hero_title'].get(ANDROID + 'maxLines'))
        for name in ('cinema_scrim_start', 'cinema_scrim_bottom'):
            self.assertTrue((ROOT / 'res/drawable' / (name + '.xml')).exists())


class CinemaHomeIntegrationTest(unittest.TestCase):
    def test_focus_updates_hero_without_replacing_existing_click_or_loaders(self):
        source = (ROOT / 'src/main/java/com/archos/mediacenter/video/leanback/MainFragment.java').read_text()
        self.assertIn('R.layout.cinema_home', source, 'Home still has no cinematic native shell')
        self.assertIn('setOnItemViewSelectedListener(', source)
        self.assertIn('mCinemaHero.select(item,', source)
        self.assertIn('mCinemaHero.pause()', source)
        self.assertIn('mCinemaHero.resume()', source)
        self.assertIn('mCinemaHero.destroy()', source)
        self.assertIn('setHeadersState(HEADERS_HIDDEN)', source)
        self.assertIn('new MainViewClickedListener(mActivity)', source)
        self.assertIn('new CompatibleCursorMapperConverter(new VideoCursorMapper())', source)

    def test_backdrop_work_is_debounced_cancelled_and_private_mode_guarded(self):
        path = ROOT / 'src/main/java/com/archos/mediacenter/video/leanback/CinemaHeroController.java'
        self.assertTrue(path.exists(), 'Selection-driven hero controller is missing')
        source = path.read_text()
        self.assertIn('handler.postDelayed(', source)
        self.assertIn('handler.removeCallbacksAndMessages(null)', source)
        self.assertIn('backdropTask.cancelAndClear()', source)
        self.assertIn('PrivateMode.isActive()', source)
        self.assertIn('new BackdropTask(activity, backdrop,', source)
        self.assertIn('getDescriptionBody()', source)
        self.assertIn('getPlot()', source)
        self.assertNotIn('getFullScraperTags(', source, 'Database lookup belongs off the UI thread')
        self.assertNotIn('PlayerActivity', source, 'Home artwork must not start playback')


if __name__ == '__main__':
    unittest.main()
