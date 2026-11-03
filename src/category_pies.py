"""Pie charts for totals, with direct Lithuanian count and share labels."""
import matplotlib.pyplot as plt
from math import cos, sin, radians
from src.chart_style import contrast_text
from src.totals_yearly import save_and_show


def _labelled_pie(ax, counts, labels, style):
    colors = [style['dataColors'][0], style['dataColors'][1], style['dataColors'][5]][:len(counts)]
    wedges, _ = ax.pie(counts.to_numpy(), startangle=90, counterclock=False, colors=colors)
    for wedge, label in zip(wedges, labels):
        angle = radians((wedge.theta1 + wedge.theta2) / 2)
        text = ax.text(0, 0, label, ha='center', va='center', fontsize=12,
                       color=contrast_text(wedge.get_facecolor()))
        fits = False
        for fontsize in [12, 11]:
            text.set_fontsize(fontsize)
            for radius in [.6, .7, .5, .8, .4]:
                text.set_position((radius * cos(angle), radius * sin(angle)))
                ax.figure.canvas.draw()
                box = text.get_window_extent(ax.figure.canvas.get_renderer()).expanded(1.08, 1.12)
                points = [(x, y) for x in [box.x0, (box.x0 + box.x1) / 2, box.x1]
                          for y in [box.y0, (box.y0 + box.y1) / 2, box.y1]]
                if wedge.get_path().contains_points(points, transform=wedge.get_transform(), radius=-1).all():
                    fits = True
                    break
            if fits:
                break
        if fits:
            text.set_gid('pie-label-inside')
        else:
            text.set_position((1.1 * cos(angle), 1.1 * sin(angle)))
            text.set_ha('left' if cos(angle) >= 0 else 'right')
            text.set_fontsize(12)
            text.set_color(style['foreground'])
            text.set_gid('pie-label-outside')
            ax.annotate('', xy=(cos(angle), sin(angle)),
                        xytext=(1.075 * cos(angle), 1.075 * sin(angle)),
                        arrowprops={'arrowstyle': '-', 'linewidth': .7, 'color': style['foreground']})


def plot_sex_totals(result, root, style):
    counts = result['totals']['lytis']['Vilkų skaičius'].reindex(['Patelė', 'Patinas', 'Nežinoma'])
    total = int(counts.sum())
    assert total == len(result['data'])
    labels = [f"{name}\n{int(value):,} ({value / total * 100:.1f} %)".replace(',', ' ').replace('.', ',')
              for name, value in counts.items()]
    fig, ax = plt.subplots(figsize=(10, 7.5))
    _labelled_pie(ax, counts, labels, style)
    ax.set_aspect('equal')
    ax.set_title('Sumedžiotų vilkų pasiskirstymas pagal lytį')
    save_and_show(fig, root, 'grupe_lytis_suvestine_pie')


def plot_age_totals(result, root, style):
    categories = ['Vyresnis nei 1 metų amžiaus', 'Jauniklis iki 1 metų amžiaus', 'Nežinoma']
    counts = result['totals']['amzius']['Vilkų skaičius'].reindex(categories)
    total = int(counts.sum())
    assert total == len(result['data'])
    names = ['Vyresnis nei 1 metų\namžiaus', 'Jauniklis iki 1 metų\namžiaus', 'Nežinoma']
    labels = []
    for name, value in zip(names, counts):
        number = f'{int(value):,}'.replace(',', ' ')
        percentage = f'{value / total * 100:.1f}'.replace('.', ',')
        labels.append(f'{name}\n{number} ({percentage} %)')
    fig, ax = plt.subplots(figsize=(11, 8))
    _labelled_pie(ax, counts, labels, style)
    ax.set_aspect('equal')
    ax.set_title('Sumedžiotų vilkų pasiskirstymas pagal amžių')
    save_and_show(fig, root, 'grupe_amzius_suvestine_pie')


def plot_pack_totals(result, root, style):
    counts = result['totals']['gauja']['Vilkų skaičius'].reindex(['Taip', 'Ne', 'Nežinoma'])
    total = int(counts.sum())
    assert total == len(result['data'])
    labels = []
    for name, value in counts.items():
        number = f'{int(value):,}'.replace(',', ' ')
        percentage = f'{value / total * 100:.1f}'.replace('.', ',')
        labels.append(f'{name}\n{number} ({percentage} %)')
    fig, ax = plt.subplots(figsize=(10, 7.5))
    _labelled_pie(ax, counts, labels, style)
    ax.set_aspect('equal')
    ax.set_title('Sumedžiotų vilkų priklausymas gaujai')
    save_and_show(fig, root, 'grupe_gauja_suvestine_pie')


def plot_health_totals(result, root, style):
    all_counts = result['totals']['sveikata']['Vilkų skaičius']
    counts = all_counts.reindex(['Sveikas', 'Nesveikas'])
    known_total = int(counts.sum())
    unknown = int(all_counts.loc['Nežinoma'])
    assert known_total + unknown == len(result['data'])
    labels = []
    for name, value in counts.items():
        number = f'{int(value):,}'.replace(',', ' ')
        percentage = f'{value / known_total * 100:.1f}'.replace('.', ',')
        labels.append(f'{name}\n{number} ({percentage} %)')
    fig, ax = plt.subplots(figsize=(10, 7.5))
    _labelled_pie(ax, counts, labels, style)
    ax.text(.5, .98, f'{unknown} vilkų sveikatos būklė nežinoma',
            transform=ax.transAxes, ha='center', va='top', fontsize=10,
            color=style['foreground'])
    ax.set_aspect('equal')
    ax.set_title('Sumedžiotų vilkų pasiskirstymas pagal sveikatą', pad=45)
    save_and_show(fig, root, 'grupe_sveikata_suvestine_pie')
