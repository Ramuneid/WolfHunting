"""Count-weighted ribbons linking yearly rankings of the selected top five."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, Rectangle, Patch
from matplotlib.ticker import MaxNLocator
from src.chart_style import contrast_text
from src.totals_yearly import save_and_show


def plot_top5_ribbon(result, root, style):
    top5 = result['municipalities'].head(5)
    table = result['municipal_yearly'].loc[:, top5.index]
    assert table.sum().to_dict() == top5.to_dict()
    names, years = list(table.columns), list(table.index)
    palette = [style['dataColors'][0], style['dataColors'][1], style['dataColors'][2],
               style['sequentialColors'][-1], style['dataColors'][3]]
    colors = dict(zip(names, palette))
    bounds = {}
    for year in years:
        # Stable tie order follows the overall-period ranking, not random order.
        ordered = sorted(names, key=lambda name: (-int(table.loc[year, name]), names.index(name)))
        cursor = float(table.loc[year].sum())
        for name in ordered:
            count = int(table.loc[year, name])
            bounds[year, name] = (cursor - count, cursor)
            cursor -= count
        assert abs(cursor) < 1e-9
    fig, ax = plt.subplots(figsize=(15, 10))
    half_width = .19
    for left_year, right_year in zip(years[:-1], years[1:]):
        x0, x1 = left_year + half_width, right_year - half_width
        mid = (x0 + x1) / 2
        for name in names:
            lo0, hi0 = bounds[left_year, name]
            lo1, hi1 = bounds[right_year, name]
            vertices = [(x0, lo0), (mid, lo0), (mid, lo1), (x1, lo1),
                        (x1, hi1), (mid, hi1), (mid, hi0), (x0, hi0), (x0, lo0)]
            codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
                     MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4, MplPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MplPath(vertices, codes), facecolor=colors[name],
                                   edgecolor='none', alpha=.32, zorder=1))
    for year in years:
        for index, name in enumerate(names):
            count = int(table.loc[year, name])
            low, high = bounds[year, name]
            if count:
                ax.add_patch(Rectangle((year - half_width, low), 2 * half_width, count,
                                       facecolor=colors[name], edgecolor='none', zorder=3))
                ax.hlines([low, high], year - half_width, year + half_width,
                          color=style['background'], linewidth=1, zorder=4)
                x = year + ((-.085 if index % 2 else .085) if count <= 2 else 0)
                ax.text(x, (low + high) / 2, str(count), ha='center', va='center',
                        fontsize=9, fontweight='bold', color=contrast_text(colors[name]), zorder=5,
                        bbox={'facecolor': colors[name], 'edgecolor': 'none', 'pad': .15})
            else:
                ax.text(year, -1.8, '0', ha='center', va='center', fontsize=9,
                        fontweight='bold', color=colors[name], zorder=5)
    ax.set_xticks(years, [f'{year}\npreliminarūs' if year == 2026 else str(year) for year in years])
    ax.set_xlim(years[0] - .45, years[-1] + .45)
    ax.set_ylim(-3.5, table.sum(axis=1).max() * 1.08)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, prune='lower'))
    fig.suptitle('Penkios pirmaujančios savivaldybės', x=.02, ha='left',
                 fontfamily=plt.rcParams['font.serif'], fontsize=16)
    ax.legend(handles=[Patch(facecolor=colors[name], label=f'{name} ({int(top5[name])})') for name in names],
              loc='lower left', bbox_to_anchor=(0, 1.02), ncol=3, fontsize=10)
    table.to_csv(Path(root) / 'outputs/tables/totals_yearly/top5_savivaldybes_pagal_metus.csv', encoding='utf-8-sig')
    save_and_show(fig, root, '04_top5_savivaldybes_ribbon')
