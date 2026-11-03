"""Area-proportional municipality totals in the existing Honey Sage theme."""
import textwrap
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
from src.chart_style import sequential_cmap_from_style, contrast_text
from src.totals_yearly import save_and_show


def treemap_rectangles(values, x=0., y=0., width=100., height=70.):
    remaining = [float(value) * width * height / sum(values) for value in values]
    rectangles = []

    def worst(row, edge):
        total = sum(row)
        return max(edge * edge * max(row) / total**2,
                   total**2 / (edge * edge * min(row)))

    def place(row, x, y, width, height):
        total = sum(row)
        if width >= height:
            strip = total / height
            offset = y
            for area in row:
                length = area / strip
                rectangles.append((x, offset, strip, length))
                offset += length
            return x + strip, y, width - strip, height
        strip = total / width
        offset = x
        for area in row:
            length = area / strip
            rectangles.append((offset, y, length, strip))
            offset += length
        return x, y + strip, width, height - strip

    while remaining:
        row = [remaining.pop(0)]
        edge = min(width, height)
        while remaining and worst(row + [remaining[0]], edge) <= worst(row, edge):
            row.append(remaining.pop(0))
        x, y, width, height = place(row, x, y, width, height)
    return rectangles


def plot_municipality_treemap(result, root, style):
    totals = result['municipalities']
    rectangles = treemap_rectangles(totals.tolist())
    assert len(rectangles) == len(totals)
    assert abs(sum(w * h for _, _, w, h in rectangles) - 7000) < 1e-6
    fig, ax = plt.subplots(figsize=(17, 12.1))
    cmap = sequential_cmap_from_style(style)
    norm = Normalize(0, totals.max())
    abbreviations = {
        'Druskininkų sav.': 'Drusk.\nsav.',
        'Pagėgių sav.': 'Pagėg.\nsav.',
        'Marijampolės sav.': 'Marij.\nsav.',
        'Pakruojo r. sav.': 'Pakr.\nr. sav.',
        'Klaipėdos r. sav.': 'Klaip.\nr. sav.',
        'Birštono sav.': 'Biršt.\nsav. 2',
        'Alytaus m. sav.': 'Alyt.\nm. 1',
    }
    label_bounds = []
    for (name, count), (x, y, width, height) in zip(totals.items(), rectangles):
        assert abs(width * height / 7000 - count / totals.sum()) < 1e-9
        color = cmap(norm(count))
        patch = Rectangle((x, y), width, height, facecolor=color,
                          edgecolor=style['background'], linewidth=1.6)
        ax.add_patch(patch)
        # Use line artists: the shared chart finisher removes patch outlines.
        ax.plot([x, x + width, x + width, x, x],
                [y, y, y + height, y + height, y],
                color=style['background'], linewidth=1.3, marker=None, zorder=2)
        if count <= 12:
            label = abbreviations[name]
            if count > 2:
                label += f'\n{int(count)}'
            text = ax.text(x + width / 2, y + height / 2, label,
                           ha='center', va='center', fontsize=9 if count <= 2 else 11,
                           linespacing=.85 if count <= 2 else 1.2,
                           color=contrast_text(color))
        else:
            label = name.replace(' r. sav.', '\nr. sav.').replace(' m. sav.', '\nm. sav.')
            if '\n' not in label:
                label = label.replace(' sav.', '\nsav.')
            # Keep Lithuanian names intact; wrap only at spaces.
            label = '\n'.join(textwrap.fill(line, 18) for line in label.splitlines())
            text = ax.text(x + width / 2, y + height / 2, f'{label}\n{int(count)}',
                    ha='center', va='center', fontsize=11, color=contrast_text(color))
        label_bounds.append((name, patch, text))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Sumedžiotų vilkų skaičius pagal savivaldybę')
    save_and_show(fig, root, '02_savivaldybiu_treemap')
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    for name, patch, text in label_bounds:
        tile_box = patch.get_window_extent(renderer)
        text_box = text.get_window_extent(renderer)
        assert tile_box.contains(text_box.x0, text_box.y0) and tile_box.contains(text_box.x1, text_box.y1), name
    print('All 52 municipality labels fit inside their tiles.')
