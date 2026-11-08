"""Run the real TV controller against explicit host-side Android/Leanback test doubles.
This checks selection/lifecycle logic, NOT Android rendering or APK compilation.
Requires javac + java (JAVA_HOME, PATH, or ../tools/jdk); no Gradle dependencies.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'com.archos.mediacenter.video.leanback'
STUBS = {
    'android/app/Activity.java': '''package android.app;
public class Activity {
 public String getString(int id) { return id == 1 ? "NOVA" : "Private mode"; }
 public boolean isFinishing() { return false; }
 public boolean isDestroyed() { return false; }
}''',
    'android/os/Looper.java': 'package android.os; public class Looper { public static Looper getMainLooper() { return new Looper(); } }',
    'android/os/Handler.java': '''package android.os;
import java.util.ArrayList;
public class Handler {
 public static final ArrayList<Runnable> pending = new ArrayList<>();
 public Handler(Looper l) {}
 public boolean postDelayed(Runnable r, long ms) { pending.add(r); return true; }
 public void removeCallbacksAndMessages(Object token) { pending.clear(); }
 public static void drain() { ArrayList<Runnable> copy = new ArrayList<>(pending); pending.clear(); for(Runnable r: copy) r.run(); }
}''',
    'android/view/View.java': '''package android.view;
import java.util.HashMap;
public class View {
 public final HashMap<Integer,View> children = new HashMap<>();
 @SuppressWarnings("unchecked") public <T extends View> T findViewById(int id) { return (T)children.get(id); }
 public Animator animate() { return new Animator(); }
 public static class Animator { public void cancel() {} }
}''',
    'android/widget/ImageView.java': '''package android.widget; public class ImageView extends android.view.View {
 public int clears; public void setAlpha(float f) {} public void setImageDrawable(Object o) { if(o == null) clears++; }
}''',
    'android/widget/TextView.java': '''package android.widget; public class TextView extends android.view.View {
 public String text = ""; public void setText(CharSequence s) { text = s == null ? "" : s.toString(); }
}''',
    'com/archos/mediacenter/video/R.java': '''package com.archos.mediacenter.video; public class R {
 public static class string { public static final int nova=1, private_mode=2; }
 public static class id { public static final int cinema_backdrop=3,cinema_hero_title=4,cinema_hero_overview=5,cinema_hero_category=6; }
}''',
    'com/archos/mediacenter/video/browser/adapters/object/Base.java': '''package com.archos.mediacenter.video.browser.adapters.object;
public class Base { private final String name; public Base(String n) { name=n; } public String getName() { return name; } }''',
    'com/archos/mediacenter/video/browser/adapters/object/Video.java': '''package com.archos.mediacenter.video.browser.adapters.object;
public class Video extends Base { private final String plot; public Video(String n,String p) { super(n);plot=p; } public String getDescriptionBody() { return plot; } }''',
    'com/archos/mediacenter/video/browser/adapters/object/Tvshow.java': '''package com.archos.mediacenter.video.browser.adapters.object;
public class Tvshow extends Base { private final String plot; public Tvshow(String n,String p) { super(n);plot=p; } public String getPlot() { return plot; } }''',
    'com/archos/mediacenter/video/leanback/adapter/object/Box.java': '''package com.archos.mediacenter.video.leanback.adapter.object;
public class Box { public String getName() { return "Network storage"; } }''',
    'com/archos/mediacenter/video/leanback/adapter/object/Icon.java': '''package com.archos.mediacenter.video.leanback.adapter.object;
public class Icon { public String getName() { return "Settings"; } }''',
    'com/archos/mediacenter/video/player/PrivateMode.java': '''package com.archos.mediacenter.video.player;
public class PrivateMode { public static boolean active; public static boolean isActive() { return active; } }''',
    'com/archos/mediacenter/video/leanback/BackdropTask.java': '''package com.archos.mediacenter.video.leanback;
public class BackdropTask {
 public static int loads,cancels; public static Object last;
 public BackdropTask(android.app.Activity a,android.widget.ImageView v,int c) {}
 public BackdropTask execute(Object item) { loads++;last=item;return this; }
 public void cancelAndClear() { cancels++; }
}''',
}
HARNESS = '''package com.archos.mediacenter.video.leanback;
import android.app.Activity;
import android.os.Handler;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import com.archos.mediacenter.video.R;
import com.archos.mediacenter.video.browser.adapters.object.Video;
import com.archos.mediacenter.video.browser.adapters.object.Tvshow;
import com.archos.mediacenter.video.leanback.adapter.object.Box;
import com.archos.mediacenter.video.player.PrivateMode;
public class CinemaHeroHostTest {
 static void check(boolean ok,String why) { if(!ok) throw new AssertionError(why); }
 public static void main(String[] args) {
  View root=new View(); ImageView image=new ImageView(); TextView title=new TextView(),overview=new TextView(),category=new TextView();
  root.children.put(R.id.cinema_backdrop,image); root.children.put(R.id.cinema_hero_title,title);
  root.children.put(R.id.cinema_hero_overview,overview); root.children.put(R.id.cinema_hero_category,category);
  CinemaHeroController hero=new CinemaHeroController(new Activity(),root);
  check(title.text.equals("NOVA"),"Empty library must have an app-title fallback");
  Video first=new Video("Arrival","A linguist makes contact.");
  Video second=new Video("Dune","A desert planet.");
  hero.select(first,"Movies"); check(title.text.equals("Arrival") && overview.text.contains("linguist"),"Movie metadata should render immediately");
  hero.select(second,"Movies"); check(BackdropTask.loads==0,"No loads before focus settles");
  Handler.drain(); check(BackdropTask.loads==1 && BackdropTask.last==second,"Only latest focused movie should load");
  int clears=image.clears; hero.select(second,"Movies"); Handler.drain();
  check(BackdropTask.loads==1 && image.clears==clears,"Duplicate focus events must not clear or reload displayed artwork");
  hero.select(new Box(),"Browse"); Handler.drain();
  check(BackdropTask.cancels==1 && overview.text.isEmpty() && title.text.equals("Network storage"),"Utility tiles must clear stale movie data and artwork");
  Tvshow show=new Tvshow("Severance","Work and life divided."); hero.select(show,"TV shows");
  check(overview.text.equals("Work and life divided."),"TV plot must use existing mapped field");
  hero.pause(); Handler.drain(); check(BackdropTask.loads==1 && overview.text.isEmpty(),"Pause must cancel pending work and clear metadata");
  hero.resume(); Handler.drain(); check(BackdropTask.loads==2 && BackdropTask.last==show,"Resume should restore the selected show");
  PrivateMode.active=true; hero.refresh(); Handler.drain();
  check(title.text.equals("Private mode") && overview.text.isEmpty() && BackdropTask.loads==2,"Private mode must suppress artwork and metadata");
  PrivateMode.active=false; hero.select(new Video("   ",null),"Movies");
  check(title.text.equals("NOVA") && overview.text.isEmpty(),"Missing metadata must use clean fallback");
  hero.destroy(); Handler.drain(); check(BackdropTask.loads==2,"Destroyed hero must never deliver pending artwork");
  System.out.println("PASS: fallback, mapped metadata, debounce, duplicate focus, utilities, TV plot, pause/resume, privacy, destroy");
 }
}'''


class CinemaControllerHostTest(unittest.TestCase):
    def test_real_controller_selection_and_lifecycle(self):
        candidates = [Path(os.environ.get('JAVA_HOME', '')) / 'bin', ROOT.parent / 'tools/jdk/bin']
        java = shutil.which('java')
        javac = shutil.which('javac')
        for folder in candidates:
            if (folder / 'javac.exe').exists():
                java, javac = str(folder / 'java.exe'), str(folder / 'javac.exe')
                break
        if not java or not javac:
            self.skipTest('JDK unavailable: host Java controller test was NOT run')
        scratch = Path(os.environ.get('TMPDIR', tempfile.gettempdir()))
        with tempfile.TemporaryDirectory(prefix='cinema-hero-test-', dir=scratch) as temporary:
            temp = Path(temporary)
            sources = []
            for name, content in STUBS.items():
                file = temp / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(content)
                sources.append(str(file))
            harness = temp / 'com/archos/mediacenter/video/leanback/CinemaHeroHostTest.java'
            harness.write_text(HARNESS)
            production = ROOT / 'src/main/java/com/archos/mediacenter/video/leanback/CinemaHeroController.java'
            compile_result = subprocess.run([javac, '-d', str(temp / 'classes'), *sources, str(production), str(harness)], text=True, capture_output=True)
            self.assertEqual(0, compile_result.returncode, compile_result.stdout + compile_result.stderr)
            run_result = subprocess.run([java, '-cp', str(temp / 'classes'), PACKAGE + '.CinemaHeroHostTest'], text=True, capture_output=True)
            self.assertEqual(0, run_result.returncode, run_result.stdout + run_result.stderr)
            print(run_result.stdout.strip())


if __name__ == '__main__':
    unittest.main()
