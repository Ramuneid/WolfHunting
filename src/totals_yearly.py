"""Reproducible counts from the approved wolf dataset. No source writes."""
from pathlib import Path
import math
import json

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter
from src.data_loading import load_data
from src.chart_style import load_chart_style, apply_chart_style, finish_chart

EXCLUDED_YEARS = [1979, 2003]
GROUPS = {
    'lytis': ('Lytis', ['Patelė', 'Patinas', 'Nežinoma']),
    'amzius': ('Amžius', ['Vyresnis nei 1 metų amžiaus', 'Jauniklis iki 1 metų amžiaus', 'Nežinoma']),
    'niezai': ('Ar pažeistas niežų', ['Taip', 'Ne', 'Nežinoma']),
    'defektai': ('Ar kiti defektai', ['Taip', 'Ne', 'Nežinoma']),
    'gauja': ('Ar priklausė gaujai', ['Taip', 'Ne', 'Nežinoma']),
    'sveikata': ('sveikatos sutrikimai', ['Sveikas', 'Nesveikas', 'Nežinoma']),
}
TITLES = {
    'lytis': 'Sumedžiotų vilkų skaičius pagal lytį',
    'amzius': 'Sumedžiotų vilkų skaičius pagal amžių',
    'niezai': 'Sumedžiotų vilkų skaičius pagal niežų požymį',
    'defektai': 'Sumedžiotų vilkų skaičius pagal kitų defektų požymį',
    'gauja': 'Sumedžiotų vilkų skaičius pagal priklausymą gaujai',
    'sveikata': 'Sumedžiotų vilkų skaičius pagal sveikatą',
}


def prepare(root):
    raw = load_data(root)
    if raw['ID'].eq('').any() or raw['ID'].duplicated().any():
        raise ValueError('ID must be present and unique before counting wolves.')
    dates = pd.to_datetime(raw['Medžioklės laikas'], errors='raise')
    if dates.isna().any():
        raise ValueError('Missing hunting date.')
    keep = ~dates.dt.year.isin(EXCLUDED_YEARS)
    excluded = raw.loc[~keep].copy()
    data = raw.loc[keep].copy()
    data['Metai'] = dates.loc[keep].dt.year.astype(int)
    data['Savivaldybė'] = data['Savivaldybė'].str.strip().replace('', 'Nežinoma')
    for key, (column, order) in GROUPS.items():
        values = data[column].str.strip()
        if key == 'sveikata':
            if set(values.unique()) - {'TRUE', 'FALSE', ''}:
                raise ValueError('Unexpected health status values.')
            values = values.map({'TRUE': 'Nesveikas', 'FALSE': 'Sveikas', '': 'Nežinoma'})
        elif key in ['niezai', 'defektai', 'gauja']:
            unexpected = set(values.unique()) - {'TRUE', 'FALSE', ''}
            if unexpected:
                raise ValueError(f'Unexpected boolean values in {column}: {unexpected}')
            values = values.map({'TRUE': 'Taip', 'FALSE': 'Ne', '': 'Nežinoma'})
        else:
            values = values.replace('', 'Nežinoma')
            if set(values.unique()) - set(order):
                raise ValueError(f'Unexpected categories in {column}')
        data[column] = values
    years = pd.Index(range(int(data.Metai.min()), int(data.Metai.max()) + 1), name='Metai')
    yearly = data.groupby('Metai').size().reindex(years, fill_value=0).rename('Vilkų skaičius')
    annual = {}
    totals = {}
    for key, (column, order) in GROUPS.items():
        annual[key] = pd.crosstab(data.Metai, data[column]).reindex(index=years, columns=order, fill_value=0)
        totals[key] = annual[key].sum().rename('Vilkų skaičius').to_frame()
        totals[key]['Dalis, %'] = (totals[key]['Vilkų skaičius'] / len(data) * 100).round(2)
        assert annual[key].sum(axis=1).equals(yearly)
        assert int(totals[key]['Vilkų skaičius'].sum()) == len(data)
    municipalities = data['Savivaldybė'].value_counts().sort_values(ascending=False, kind='stable')
    municipalities.name = 'Vilkų skaičius'
    municipal_yearly = pd.crosstab(data.Metai, data['Savivaldybė']).reindex(index=years, columns=municipalities.index, fill_value=0)
    assert municipal_yearly.sum(axis=1).equals(yearly)
    assert int(yearly.sum()) == len(data)
    latest = dates.loc[keep].max().strftime('%Y-%m-%d')
    return {'raw': raw, 'data': data, 'excluded': excluded, 'yearly': yearly,
            'annual': annual, 'totals': totals, 'municipalities': municipalities,
            'municipal_yearly': municipal_yearly, 'latest': latest}


def export_tables(result, root):
    destination = Path(root) / 'outputs/tables/totals_yearly'
    destination.mkdir(parents=True, exist_ok=True)
    result['yearly'].to_csv(destination / 'metines_suvestines.csv', encoding='utf-8-sig')
    result['municipalities'].to_csv(destination / 'savivaldybiu_suvestine.csv', encoding='utf-8-sig')
    result['municipal_yearly'].to_csv(destination / 'savivaldybes_pagal_metus.csv', encoding='utf-8-sig')
    result['excluded'].to_csv(destination / 'neitraukti_irasai.csv', index=False, encoding='utf-8-sig')
    for key in GROUPS:
        result['annual'][key].to_csv(destination / f'{key}_pagal_metus.csv', encoding='utf-8-sig')
        result['totals'][key].to_csv(destination / f'{key}_suvestine.csv', encoding='utf-8-sig')
    summary = {'source_rows': len(result['raw']), 'included_rows': len(result['data']),
               'excluded_rows': len(result['excluded']), 'excluded_years': EXCLUDED_YEARS,
               'latest_hunting_date': result['latest'],
               'yearly_counts': {str(k): int(v) for k, v in result['yearly'].items()},
               'category_totals': {k: {str(label): int(value) for label, value in table['Vilkų skaičius'].items()}
                                   for k, table in result['totals'].items()}}
    (destination / 'analysis_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary


def setup_style(root):
    style = load_chart_style(Path(root))
    apply_chart_style(style)
    return style


def scope_note(result):
    return (f"Šaltinis: Vilkas_analizei.csv. Neįtraukti 1979 ir 2003 m.; n = {len(result['data']):,}. "
            f"Paskutinė medžioklės data: {result['latest']}. Kraštiniai metai gali būti nepilni.").replace('1,703', '1 703')


def save_and_show(fig, root, name, note='', *, point_labels=False):
    # The source helper displays the finished chart in notebook outputs.
    for ax in fig.axes:
        if ax.get_visible():
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.minorticks_off()
            ax.tick_params(labelbottom=True, labelleft=True)
            label_line_values(ax)
    finish_chart(fig, note='', point_labels=False, zero_reference=False)
    folder = Path(root) / 'outputs/figures/totals_yearly'
    folder.mkdir(parents=True, exist_ok=True)
    for extension in ['png', 'svg']:
        fig.savefig(folder / f'{name}.{extension}', bbox_inches='tight')
    plt.close(fig)


def label_line_values(ax):
    """Label each series observation, including coincident zero observations."""
    lines = [line for line in ax.lines if line.get_visible()
             and line.get_transform() == ax.transData
             and line.get_marker() not in (None, '', ' ', 'None', 'none')]
    if not lines:
        return
    ax.figure.canvas.draw()
    by_year = {}
    for line in lines:
        xs, ys = line.get_data(orig=False)
        for index, (x, y) in enumerate(zip(xs, ys)):
            by_year.setdefault(float(x), []).append((float(y), line, index, len(xs)))
    for x, points in by_year.items():
        previous_label_y = None
        for y, line, index, length in sorted(points, key=lambda point: point[0]):
            point_y = ax.transData.transform((x, y))[1]
            label_y = point_y + 7 * ax.figure.dpi / 72
            if previous_label_y is not None:
                label_y = max(label_y, previous_label_y + 12 * ax.figure.dpi / 72)
            previous_label_y = label_y
            offset = (label_y - point_y) * 72 / ax.figure.dpi
            annotation = ax.annotate(
                f'{y:,.0f}'.replace(',', ' '), (x, y),
                xytext=(4 if index == 0 else -4 if index == length - 1 else 0, offset),
                textcoords='offset points',
                ha='left' if index == 0 else 'right' if index == length - 1 else 'center',
                va='bottom', fontsize=9, color=line.get_color(),
            )
            annotation.set_gid('point-value-label')


def annual_axis(ax, years):
    ax.set_xticks(years, [f'{year}\npreliminarūs' if year == 2026 else str(year) for year in years])
    ax.set_xlim(min(years) - .3, max(years) + .3)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:,.0f}'.replace(',', ' ')))


def plot_total(result, root, style):
    series = result['yearly']
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.plot(series.index, series, color=style['dataColors'][0], marker='o')
    annual_axis(ax, list(series.index))
    ax.set_ylim(0, series.max() * 1.16)
    ax.set_title('Sumedžiotų vilkų skaičius pagal metus')
    save_and_show(fig, root, '01_is_viso_pagal_metus', scope_note(result), point_labels=True)


def plot_group(result, root, style, key):
    table = result['annual'][key]
    if key == 'sveikata':
        table = table.loc[:, ['Sveikas', 'Nesveikas']]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    styles = [('o', '-'), ('s', '--'), ('^', ':')]
    colors = [style['dataColors'][0], style['dataColors'][1], style['semanticColors']['muted']]
    for (label, series), (marker, linestyle), color in zip(table.items(), styles, colors):
        ax.plot(table.index, series, label=label, marker=marker, linestyle=linestyle, color=color)
    annual_axis(ax, list(table.index))
    ax.set_ylim(0, max(1, table.to_numpy().max()) * 1.22)
    fig.suptitle(TITLES[key], x=.02, ha='left',
                 fontfamily=plt.rcParams['font.serif'], fontsize=16)
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1.02),
              ncol=1 if key == 'amzius' else 3, fontsize=10)
    if key == 'sveikata':
        unknown = int(result['totals']['sveikata'].loc['Nežinoma', 'Vilkų skaičius'])
        ax.text(.99, 1.04, f'{unknown} vilkų sveikatos būklė nežinoma',
                transform=ax.transAxes, ha='right', va='bottom', fontsize=10)
    note = scope_note(result) + ' Tušti laukai: Nežinoma; tai nėra Ne.'
    save_and_show(fig, root, f'grupe_{key}_pagal_metus', note)


def plot_municipality_totals(result, root, style, page):
    totals = result['municipalities']
    subset = totals.iloc[page * 26:(page + 1) * 26]
    fig, ax = plt.subplots(figsize=(11, 12))
    bars = ax.barh(subset.index, subset.values, color=style['dataColors'][0])
    ax.invert_yaxis()
    ax.set_xlim(0, totals.max() * 1.16)
    ax.bar_label(bars, padding=5, fontsize=10)
    ax.set_xlabel('Vilkų skaičius')
    ax.set_title(f'Sumedžiotų vilkų skaičius pagal savivaldybę ({page + 1}/2)')
    ax.tick_params(axis='y', labelsize=10)
    save_and_show(fig, root, f'02_savivaldybiu_suvestine_{page + 1}', scope_note(result))


def plot_municipality_years(result, root, style, page):
    table = result['municipal_yearly']
    columns = list(table.columns[page * 9:(page + 1) * 9])
    fig, axes = plt.subplots(3, 3, figsize=(15, 11), sharex=True, sharey=True)
    for ax, municipality in zip(axes.flat, columns):
        ax.plot(table.index, table[municipality], color=style['dataColors'][0], marker='o', markersize=4)
        ax.set_title(municipality, fontsize=11)
        ax.set_ylim(0, table.to_numpy().max() + 4)
        ax.set_xlim(table.index.min() - .4, table.index.max() + .4)
        years = list(table.index)
        ax.set_xticks(years, [f'{year}\npreliminarūs' if year == 2026 else str(year) for year in years])
        ax.tick_params(labelsize=9, labelbottom=True, labelleft=True)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        ax.text(.03, .91, f'Iš viso: {int(table[municipality].sum())}', transform=ax.transAxes, fontsize=9)
    for ax in list(axes.flat)[len(columns):]:
        ax.set_visible(False)
    fig.suptitle(f'Sumedžioti vilkai savivaldybėse pagal metus ({page + 1}/6)',
                 x=.02, ha='left', fontfamily=plt.rcParams['font.serif'], fontsize=16)
    note = scope_note(result) + ' Visose diagramose ta pati skalė. X: metai; Y: vilkų skaičius. 0 = šiame faile nėra įrašų.'
    save_and_show(fig, root, f'03_savivaldybes_pagal_metus_{page + 1}', note)


def plot_top5_municipalities(result, root, style):
    """Compare the same five municipalities, ranked over the included period."""
    top5 = result['municipalities'].head(5)
    table = result['municipal_yearly'].loc[:, top5.index]
    assert table.sum().to_dict() == top5.to_dict()
    fig, ax = plt.subplots(figsize=(13, 8))
    encodings = [('o', '-'), ('s', '--'), ('^', '-.'), ('D', ':'), ('v', '--')]
    colors = [style['dataColors'][0], style['dataColors'][1],
              style['dataColors'][2], style['sequentialColors'][-1], style['dataColors'][3]]
    for (municipality, values), color, (marker, line_style) in zip(table.items(), colors, encodings):
        ax.plot(table.index, values, color=color, marker=marker, linestyle=line_style,
                label=f'{municipality} ({int(top5[municipality])})')
    annual_axis(ax, list(table.index))
    ax.set_ylim(0, max(1, table.to_numpy().max()) * 1.45)
    fig.suptitle('Penkios savivaldybės, kuriose sumedžiota daugiausia vilkų',
                 x=.02, ha='left', fontfamily=plt.rcParams['font.serif'], fontsize=16)
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1.02), ncol=3, fontsize=10)
    table.to_csv(Path(root) / 'outputs/tables/totals_yearly/top5_savivaldybes_pagal_metus.csv', encoding='utf-8-sig')
    save_and_show(fig, root, '04_top5_savivaldybes_pagal_metus')
