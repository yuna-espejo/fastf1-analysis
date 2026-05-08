import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import mplcursors
import pandas as pd
import os

os.makedirs('cache_f1', exist_ok=True)
fastf1.Cache.enable_cache('cache_f1')
fastf1.plotting.setup_mpl(mpl_timedelta_support=True)

# ── LOAD SESSION ──────────────────────────────────────────────────────────────
session = fastf1.get_session(2026, 'Miami', 'R')
session.load()

# Get all available drivers with their abbreviation and team
driver_list = []
for drv in session.drivers:
    info = session.get_driver(drv)
    driver_list.append({
        'abbr': info['Abbreviation'],
        'name': f"{info['Abbreviation']} — {info['TeamName']}"
    })
driver_list = sorted(driver_list, key=lambda x: x['abbr'])
driver_names = [d['name'] for d in driver_list]

# ── TEAM COLORS ───────────────────────────────────────────────────────────────
TEAM_COLORS = {
    'McLaren': '#FF8000',
    'Mercedes': '#27F4D2',
    'Red Bull Racing': '#3671C6',
    'Ferrari': '#E8002D',
    'Aston Martin': '#358C75',
    'Alpine': '#FF87BC',
    'Williams': '#64C4FF',
    'Racing Bulls': '#6692FF',
    'Kick Sauber': '#52E252',
    'Haas F1 Team': '#B6BABD',
    'Audi': '#E8D403',
    'Cadillac': '#FFFFFF',
}

ALTERNATE_COLORS = {
    'McLaren': '#FF4081',
    'Ferrari': '#FF8A65',
    'Mercedes': '#00838F',
    'Red Bull Racing': '#1565C0',
    'Aston Martin': '#1B5E20',
    'Alpine': '#C51162',
    'Williams': '#0D47A1',
    'Racing Bulls': '#283593',
    'Haas F1 Team': '#757575',
    'Audi': '#F9A825',
    'Cadillac': '#BDBDBD',
}

# ── ANALYSIS FUNCTION ─────────────────────────────────────────────────────────
def analyze(abbr1, abbr2=None):
    drivers = [abbr1] if abbr2 == 'NONE' else [abbr1, abbr2]

    ax_lap.cla()
    ax_speed.cla()

    # Remove previous tooltips
    for crs in getattr(analyze, '_cursors', []):
        crs.remove()
    analyze._cursors = []

    def get_driver_color(abbr, index):
        info = session.get_driver(abbr)
        team = info['TeamName']
        if index == 1 and len(drivers) == 2:
            info0 = session.get_driver(drivers[0])
            if info0['TeamName'] == team:
                return ALTERNATE_COLORS.get(team, '#AAAAAA')
        return TEAM_COLORS.get(team, '#FFFFFF')

    for i, abbr in enumerate(drivers):
        color = get_driver_color(abbr, i)

        # ── LAP TIME EVOLUTION ────────────────────────────────────────────────
        laps_all = session.laps.pick_driver(abbr)
        laps_clean = laps_all.pick_quicklaps().reset_index(drop=True)
        laps_clean['LapTimeSeconds'] = laps_clean['LapTime'].dt.total_seconds()

        # Filter out laps 7% slower than median (pit laps that slipped through)
        median = laps_clean['LapTimeSeconds'].median()
        laps_clean = laps_clean[laps_clean['LapTimeSeconds'] < median * 1.07].reset_index(drop=True)

        ax_lap.plot(laps_clean['LapNumber'], laps_clean['LapTimeSeconds'],
                    color=color, linewidth=2, label=abbr)
        scatter = ax_lap.scatter(laps_clean['LapNumber'], laps_clean['LapTimeSeconds'],
                                 color=color, s=40, zorder=5)

        # Pit stop lines
        pit_laps = laps_all[laps_all['PitInTime'].notna()]['LapNumber'].values
        for pit in pit_laps:
            ax_lap.axvline(x=pit, color=color, linestyle='--', alpha=0.4)

        # Compound labels per stint
        for stint_num in sorted(laps_all['Stint'].unique()):
            stint_data = laps_all[laps_all['Stint'] == stint_num]
            compound = stint_data['Compound'].mode()
            if len(compound) > 0:
                mid_lap = stint_data['LapNumber'].median()
                offset = 92.0 if i == 0 else 92.3
                ax_lap.text(mid_lap, offset, compound[0],
                            ha='center', fontsize=8, color=color, alpha=0.8)

        # Tooltip
        def make_tooltip(sc, ab):
            def format_tooltip(sel):
                x = int(sel.target[0])
                y = sel.target[1]
                m = int(y // 60)
                s = y % 60
                sel.annotation.set_text(f'{ab}\nLap {x}\n{m}:{s:06.3f}')
            return format_tooltip

        crs = mplcursors.cursor(scatter, hover=True)
        crs.connect('add', make_tooltip(scatter, abbr))
        analyze._cursors.append(crs)

        # ── SPEED TRACE ───────────────────────────────────────────────────────
        fast_lap = laps_all.pick_fastest()
        tel = fast_lap.get_telemetry().add_distance()
        ax_speed.plot(tel['Distance'], tel['Speed'],
                      color=color, linewidth=1.5, label=abbr)

    # ── LAP TIME FORMATTING ───────────────────────────────────────────────────
    ax_lap.invert_yaxis()
    ax_lap.set_xlabel('Lap Number')
    ax_lap.set_ylabel('Lap Time (s)')
    title = ' vs '.join(drivers)
    ax_lap.set_title(f'{title} — Lap Time Evolution | Miami GP 2026')
    ax_lap.legend(facecolor='#2a2a2a', labelcolor='white')
    ax_lap.set_xticks(range(0, 65, 1))
    plt.setp(ax_lap.get_xticklabels(), fontsize=7)

    # ── SPEED TRACE FORMATTING ────────────────────────────────────────────────
    ax_speed.set_xlabel('Distance (m)')
    ax_speed.set_ylabel('Speed (km/h)')
    ax_speed.set_title(f'{title} — Speed Trace | Fastest Lap | Miami GP 2026')
    ax_speed.legend(facecolor='#2a2a2a', labelcolor='white')

    # Dark style for both charts
    for ax in [ax_lap, ax_speed]:
        ax.set_facecolor('#1a1a1a')
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
        for spine in ax.spines.values():
            spine.set_edgecolor('#444444')

    fig.canvas.draw_idle()

analyze._cursors = []

# ── BUILD UI ──────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor('#1a1a1a')

# Chart areas
ax_lap   = fig.add_axes([0.28, 0.55, 0.70, 0.38])
ax_speed = fig.add_axes([0.28, 0.08, 0.70, 0.38])

# ── COMPARE BUTTON ────────────────────────────────────────────────────────────
ax_btn = fig.add_axes([0.01, 0.94, 0.22, 0.04])
btn = widgets.Button(ax_btn, '▶  COMPARE', color='#E8002D', hovercolor='#FF4444')
btn.label.set_fontsize(11)
btn.label.set_fontweight('bold')
btn.label.set_color('white')

# ── DRIVER 1 SELECTOR ─────────────────────────────────────────────────────────
fig.text(0.02, 0.91, 'Driver 1', fontsize=10, fontweight='bold', color='white')
ax_radio1 = fig.add_axes([0.01, 0.50, 0.22, 0.40])
ax_radio1.set_facecolor('#1a1a1a')
radio1 = widgets.RadioButtons(
    ax=ax_radio1,
    labels=driver_names,
    activecolor='#FF8000'
)
for label in radio1.labels:
    label.set_color('white')
    label.set_fontsize(8)

# ── DRIVER 2 SELECTOR ─────────────────────────────────────────────────────────
fig.text(0.02, 0.47, 'Driver 2', fontsize=10, fontweight='bold', color='white')
ax_radio2 = fig.add_axes([0.01, 0.08, 0.22, 0.38])
ax_radio2.set_facecolor('#1a1a1a')
radio2 = widgets.RadioButtons(
    ax=ax_radio2,
    labels=['NONE'] + driver_names,
    activecolor='#27F4D2'
)
for label in radio2.labels:
    label.set_color('white')
    label.set_fontsize(8)

# ── BUTTON HANDLER ────────────────────────────────────────────────────────────
def on_compare(event):
    sel1 = radio1.value_selected.split(' — ')[0]
    sel2 = radio2.value_selected.split(' — ')[0]
    analyze(sel1, sel2)

btn.on_clicked(on_compare)

# Load default view on startup
analyze('PIA', 'ANT')

# Add before plt.show()
plt.savefig('assets/miami2026_selector.png', dpi=150, bbox_inches='tight',
            facecolor='#1a1a1a')

plt.show()