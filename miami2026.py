import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import mplcursors
import pandas as pd
import os

os.makedirs('cache_f1', exist_ok=True)                        # Create cache folder if it doesn't exist
fastf1.Cache.enable_cache('cache_f1')                         # Enable cache (avoids re-downloading)
fastf1.plotting.setup_mpl(mpl_timedelta_support=True)         # Enable team colors

# 2026 Miami Grand Prix - Race
session = fastf1.get_session(2026, 'Miami', 'R')
session.load()
print(session.event['EventName'])

# ── PIASTRI ───────────────────────────────────────────────────────────────────
pia = session.laps.pick_driver('PIA')                         # All laps (used for events)
piaClean = pia.pick_quicklaps().reset_index(drop=True)        # Clean laps (used for pace)
piaClean['LapTimeSeconds'] = piaClean['LapTime'].dt.total_seconds()

pit_lap_pia = pia[pia['PitInTime'].notna()]['LapNumber'].values[0]
stint1_pia = pia[pia['Stint'] == 1]['Compound'].mode()[0]
stint2_pia = pia[pia['Stint'] == 2]['Compound'].mode()[0]

# ── ANTONELLI ─────────────────────────────────────────────────────────────────
ant = session.laps.pick_driver('ANT')                         # All laps
antClean = ant.pick_quicklaps().reset_index(drop=True)        # Clean laps
antClean['LapTimeSeconds'] = antClean['LapTime'].dt.total_seconds()

pit_lap_ant = ant[ant['PitInTime'].notna()]['LapNumber'].values[0]
stint1_ant = ant[ant['Stint'] == 1]['Compound'].mode()[0]
stint2_ant = ant[ant['Stint'] == 2]['Compound'].mode()[0]

# ── GRAPHIC ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 6))

# Piastri line
pia_line, = ax.plot(piaClean['LapNumber'], piaClean['LapTimeSeconds'],
                    color='#FF8000', linewidth=2, label='Piastri')
pia_scatter = ax.scatter(piaClean['LapNumber'], piaClean['LapTimeSeconds'],
                         color='#FF8000', s=40, zorder=5)

# Antonelli line
ant_line, = ax.plot(antClean['LapNumber'], antClean['LapTimeSeconds'],
                    color='#27F4D2', linewidth=2, label='Antonelli')
ant_scatter = ax.scatter(antClean['LapNumber'], antClean['LapTimeSeconds'],
                         color='#27F4D2', s=40, zorder=5)

# Pit stop lines
ax.axvline(x=pit_lap_pia, color='#FF8000', linestyle='--', alpha=0.5,
           label=f'PIA pit stop lap {int(pit_lap_pia)}')
ax.axvline(x=pit_lap_ant, color='#27F4D2', linestyle='--', alpha=0.5,
           label=f'ANT pit stop lap {int(pit_lap_ant)}')

# Labels and title
ax.set_xlabel('Lap Number')
ax.set_ylabel('Lap Time (seconds)')
ax.set_title('Piastri vs Antonelli — Lap Time Evolution | Miami GP 2026')
ax.legend()

# X axis ticks every 1 lap
ax.set_xticks(range(0, int(max(piaClean['LapNumber'].max(),
                               antClean['LapNumber'].max())) + 1, 1))
plt.xticks(fontsize=7)

# Invert Y axis — lower time = faster = better
ax.invert_yaxis()

# Compound labels — after invert_yaxis so position is correct
ax.text(pit_lap_pia / 2, 91.9,
        stint1_pia, ha='center', fontsize=9, color='#FF8000')
ax.text(pit_lap_pia + (piaClean['LapNumber'].max() - pit_lap_pia) / 2, 91.9,
        stint2_pia, ha='center', fontsize=9, color='#FF8000')
ax.text(pit_lap_ant / 2, 92.1,
        stint1_ant, ha='center', fontsize=9, color='#27F4D2')
ax.text(pit_lap_ant + (antClean['LapNumber'].max() - pit_lap_ant) / 2, 92.1,
        stint2_ant, ha='center', fontsize=9, color='#27F4D2')

# Tooltips on hover — shows lap number and exact lap time
def format_tooltip(sel):
    x = int(sel.target[0])
    y = sel.target[1]
    minutes = int(y // 60)
    seconds = y % 60
    driver = 'Piastri' if sel.artist == pia_scatter else 'Antonelli'
    sel.annotation.set_text(f'{driver}\nLap {x}\n{minutes}:{seconds:06.3f}')

cursor = mplcursors.cursor([pia_scatter, ant_scatter], hover=True)
cursor.connect('add', format_tooltip)

plt.tight_layout()
plt.show()