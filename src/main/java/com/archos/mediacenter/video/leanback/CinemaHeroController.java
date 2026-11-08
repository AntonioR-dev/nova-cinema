package com.archos.mediacenter.video.leanback;

import android.app.Activity;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;

import com.archos.mediacenter.video.R;
import com.archos.mediacenter.video.browser.adapters.object.Base;
import com.archos.mediacenter.video.browser.adapters.object.Tvshow;
import com.archos.mediacenter.video.browser.adapters.object.Video;
import com.archos.mediacenter.video.leanback.adapter.object.Box;
import com.archos.mediacenter.video.leanback.adapter.object.Icon;
import com.archos.mediacenter.video.player.PrivateMode;

import java.util.Objects;

/** TV home decoration only. All navigation and playback stay owned by the existing browser. */
final class CinemaHeroController {
    private static final int BACKGROUND_COLOR = 0xff080b12;
    private static final long FOCUS_SETTLE_MS = 240;

    private final Activity activity;
    private final ImageView backdrop;
    private final TextView title;
    private final TextView overview;
    private final TextView category;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private BackdropTask backdropTask;
    private Object selectedItem;
    private String selectedCategory;
    private boolean paused;
    private boolean destroyed;
    private boolean renderedPrivateMode;

    CinemaHeroController(Activity activity, View root) {
        this.activity = activity;
        backdrop = root.findViewById(R.id.cinema_backdrop);
        title = root.findViewById(R.id.cinema_hero_title);
        overview = root.findViewById(R.id.cinema_hero_overview);
        category = root.findViewById(R.id.cinema_hero_category);
        refresh();
    }

    void select(Object item, String rowTitle) {
        if (selectedItem == item && Objects.equals(selectedCategory, rowTitle)
                && renderedPrivateMode == PrivateMode.isActive()) return;
        selectedItem = item;
        selectedCategory = rowTitle;
        refresh();
    }

    void refresh() {
        cancelArtwork();
        if (destroyed || paused) return;
        renderedPrivateMode = PrivateMode.isActive();
        category.setText(PrivateMode.isActive() ? "" : selectedCategory);
        overview.setText("");
        title.setText(activity.getString(PrivateMode.isActive() ? R.string.private_mode : R.string.nova));
        if (PrivateMode.isActive()) return;

        final Object item = selectedItem;
        if (item instanceof Base) {
            String name = ((Base) item).getName();
            if (name != null && !name.trim().isEmpty()) title.setText(name);
            // These are already cursor-mapped fields: no database/network work on the UI thread.
            if (item instanceof Video) overview.setText(((Video) item).getDescriptionBody());
            else if (item instanceof Tvshow) overview.setText(((Tvshow) item).getPlot());

            // Reuse NOVA's cancellable background lookup + Picasso pipeline, including its fallback.
            // Fast D-pad movement never starts a lookup for each card it passes.
            if (item instanceof Video || item instanceof Tvshow) {
                handler.postDelayed(() -> {
                    if (destroyed || paused || PrivateMode.isActive() || selectedItem != item
                            || activity.isFinishing() || activity.isDestroyed()) return;
                    backdropTask = new BackdropTask(activity, backdrop, BACKGROUND_COLOR).execute(item);
                }, FOCUS_SETTLE_MS);
            }
        } else if (item instanceof Box) {
            title.setText(((Box) item).getName());
        } else if (item instanceof Icon) {
            title.setText(((Icon) item).getName());
        }
    }

    void pause() {
        paused = true;
        cancelArtwork();
        // Do not leave library metadata in the activity window while away from home.
        title.setText(activity.getString(R.string.nova));
        category.setText("");
        overview.setText("");
    }

    void resume() {
        paused = false;
        refresh();
    }

    void destroy() {
        destroyed = true;
        cancelArtwork();
        selectedItem = null;
        selectedCategory = null;
    }

    private void cancelArtwork() {
        handler.removeCallbacksAndMessages(null);
        if (backdropTask != null) {
            backdropTask.cancelAndClear();
            backdropTask = null;
        }
        // Also clear when a selection was cancelled during the debounce interval.
        backdrop.animate().cancel();
        backdrop.setAlpha(0f);
        backdrop.setImageDrawable(null);
    }
}
