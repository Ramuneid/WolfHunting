"""Offline municipality map, based on reviewed GISCO boundaries and CSV counts."""
from pathlib import Path
import base64
import html
import json
import math

import pandas as pd
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely import wkt
from pyproj import Transformer
from src.data_loading import load_data


def prepare_map_data(root):
    root = Path(root)
    raw = load_data(root)
    assert raw['ID'].is_unique and raw['ID'].ne('').all()
    dates = pd.to_datetime(raw['Medžioklės laikas'], errors='raise')
    assert dates.notna().all()
    keep = ~dates.dt.year.isin([1979, 2003])
    data = raw.loc[keep].copy()
    data['Metai'] = dates.loc[keep].dt.year.astype(int)
    transformer = Transformer.from_crs('EPSG:4326', 'EPSG:3346', always_xy=True)
    points = []
    for _, row in data.iterrows():
        geometry = wkt.loads(row['Geometrija'])
        if geometry.geom_type != 'Point' or geometry.is_empty or not geometry.is_valid:
            raise ValueError(f"Invalid hunting point: {row['ID']}")
        lon, lat = geometry.x, geometry.y
        assert 20 < lon < 28 and 53 < lat < 57
        east, north = transformer.transform(lon, lat)
        assert math.isfinite(east) and math.isfinite(north)
        points.append({'id': row['ID'], 'year': int(row['Metai']),
                       'date': pd.Timestamp(row['Medžioklės laikas']).strftime('%Y-%m-%d'),
                       'municipality': row['Savivaldybė'], 'month': int(pd.Timestamp(row['Medžioklės laikas']).month),
                       'gender': row['Lytis'] or 'unknown', 'age': row['Amžius'] or 'unknown',
                       'health': {'TRUE': 'Nesveikas', 'FALSE': 'Sveikas', '': 'unknown'}[row['sveikatos sutrikimai']],
                       'packSize': row['Viso gaujoje, vnt.'] or 'unknown',
                       'packMember': {'TRUE': 'Taip', 'FALSE': 'Ne', '': 'unknown'}[row['Ar priklausė gaujai']],
                       'lon': lon, 'lat': lat,
                       'east': east, 'north': north})
    boundaries = json.loads((root / 'assets/geography/lt_savivaldybes_2024_3035.geojson').read_text(encoding='utf-8'))
    boundary_transformer = Transformer.from_crs('EPSG:3035', 'EPSG:3346', always_xy=True)
    features = [{**feature, 'geometry': mapping(transform(boundary_transformer.transform, shape(feature['geometry'])))}
                for feature in boundaries['features']]
    assert len(features) == 60
    names = {feature['properties']['name']: feature['properties']['code'] for feature in features}
    assert len(names) == 60
    unmatched = sorted(set(data['Savivaldybė']) - set(names))
    if unmatched:
        raise ValueError(f'Unmatched municipalities: {unmatched}')
    data['GISCO_ID'] = data['Savivaldybė'].map(names)
    metadata = pd.DataFrame([{'GISCO_ID': f['properties']['code'], 'Savivaldybė': f['properties']['name'],
                              'Pilnas pavadinimas': f['properties']['official_name']} for f in features]).set_index('GISCO_ID')
    years = list(range(int(data.Metai.min()), int(data.Metai.max()) + 1))
    annual = pd.crosstab(data.GISCO_ID, data.Metai).reindex(index=metadata.index, columns=years, fill_value=0)
    total = annual.sum(axis=1).astype(int)
    totals = metadata.copy()
    totals['Vilkų skaičius'] = total
    expected = data.groupby('Metai').size().reindex(years, fill_value=0)
    assert annual.sum(axis=0).to_dict() == expected.to_dict()
    assert int(total.sum()) == len(data)
    assert all(shape(f['geometry']).is_valid for f in features)
    folder = root / 'outputs/tables/regional_map'
    folder.mkdir(parents=True, exist_ok=True)
    totals.to_csv(folder / 'savivaldybiu_suvestine.csv', encoding='utf-8-sig')
    totals.join(annual).to_csv(folder / 'savivaldybes_pagal_metus.csv', encoding='utf-8-sig')
    summary = {'included_rows': len(data), 'excluded_rows': len(raw) - len(data), 'municipalities': len(totals),
               'municipalities_with_records': int(total.gt(0).sum()),
               'municipalities_without_records': totals.loc[total.eq(0), 'Savivaldybė'].tolist(),
               'yearly_totals': {str(year): int(expected[year]) for year in years},
               'latest_hunting_date': dates.loc[keep].max().strftime('%Y-%m-%d'),
               'unmatched_municipalities': unmatched, 'boundary_crs': 'EPSG:3035', 'display_crs': 'EPSG:3346', 'boundary_year': 2024,
               'valid_hunting_points': len(points),
               'distinct_hunting_locations': len({(p['lon'], p['lat']) for p in points}),
               'coordinate_crs_assumption': 'EPSG:4326; longitude then latitude, inferred from source coordinate values'}
    (folder / 'validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'features': features, 'metadata': metadata, 'annual': annual, 'totals': totals,
            'summary': summary, 'years': years, 'points': points}


def _svg_projection(features):
    geometries = [shape(f['geometry']) for f in features]
    minx = min(g.bounds[0] for g in geometries)
    miny = min(g.bounds[1] for g in geometries)
    maxx = max(g.bounds[2] for g in geometries)
    maxy = max(g.bounds[3] for g in geometries)
    scale = min(950 / (maxx - minx), 700 / (maxy - miny))
    offset_x = (1000 - (maxx - minx) * scale) / 2
    offset_y = (750 - (maxy - miny) * scale) / 2

    def point(x, y):
        return (offset_x + (x - minx) * scale, offset_y + (maxy - y) * scale)
    return point


def _svg_geometry(features):
    geometries = [shape(f['geometry']) for f in features]
    point = _svg_projection(features)

    result = []
    for feature, geometry in zip(features, geometries):
        pieces = list(geometry.geoms) if geometry.geom_type == 'MultiPolygon' else [geometry]
        paths = []
        for polygon in pieces:
            for ring in [polygon.exterior, *polygon.interiors]:
                coordinates = [point(x, y) for x, y in ring.coords]
                paths.append('M' + 'L'.join(f'{x:.2f},{y:.2f}' for x, y in coordinates) + 'Z')
        largest = max(pieces, key=lambda g: g.area)
        position = largest.representative_point()
        assert geometry.covers(position)
        label_x, label_y = point(position.x, position.y)
        result.append({**feature['properties'], 'path': ''.join(paths), 'x': round(label_x, 2), 'y': round(label_y, 2)})
    return result


def build_map_html(result, root):
    root = Path(root)
    style = json.loads((root / 'config/chart_style.json').read_text(encoding='utf-8'))
    regions = _svg_geometry(result['features'])
    project = _svg_projection(result['features'])
    points = []
    for source in result['points']:
        x, y = project(source['east'], source['north'])
        assert 0 <= x <= 1000 and 0 <= y <= 750
        points.append({k: v for k, v in source.items() if k not in ('east', 'north')} | {'x': round(x, 3), 'y': round(y, 3)})
    annual = result['annual']
    codes = {r['name']: r['code'] for r in regions}
    for point in points:
        point['code'] = codes[point['municipality']]
    for region in regions:
        code = region['code']
        region['counts'] = {'all': int(annual.loc[code].sum()),
                            **{str(year): int(annual.loc[code, year]) for year in result['years']}}
    to_wgs84 = Transformer.from_crs('EPSG:3346', 'EPSG:4326', always_xy=True)
    boundaries = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'code': feature['properties']['code'],
                                          'name': feature['properties']['name']},
         'geometry': mapping(transform(to_wgs84.transform, shape(feature['geometry'])))}
        for feature in result['features']
    ]}
    payload = {'municipalityBoundaries': boundaries,
               'regions': regions, 'points': points, 'years': result['years'], 'latest': result['summary']['latest_hunting_date'],
               'annualMax': int(annual.to_numpy().max()), 'overallMax': max(r['counts']['all'] for r in regions),
               'colors': style['sequentialColors'], 'categoryColors': style['dataColors'], 'zero': '#F0EEE2'}
    fonts = []
    for filename, family, weight in [('publicsans/PublicSans-Regular.ttf', 'Wolf Sans', 400),
                                      ('publicsans/PublicSans-Bold.ttf', 'Wolf Sans', 700),
                                      ('slabo13px/Slabo13px-Regular.ttf', 'Wolf Title', 400)]:
        encoded = base64.b64encode((root / 'assets/fonts' / filename).read_bytes()).decode('ascii')
        fonts.append(f"@font-face{{font-family:'{family}';font-weight:{weight};src:url(data:font/ttf;base64,{encoded}) format('truetype');}}")
    template = (root / 'src/regional_map_template.html').read_text(encoding='utf-8')
    template = template.replace('__DETAILED_MAP__', (root / 'src/detailed_map.js').read_text(encoding='utf-8'))
    template = template.replace('__DASHBOARD__', (root / 'src/municipality_dashboard.js').read_text(encoding='utf-8'))
    document = template.replace('__FONTS__', '\n'.join(fonts)).replace('__DATA__', json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c'))
    document = document.replace('__BACKGROUND__', style['background']).replace('__FOREGROUND__', style['foreground']).replace('__HONEY__', style['dataColors'][0])
    # Initial paths/counts are also present before JavaScript executes.
    paths = []
    labels = []
    for region in regions:
        code, count = region['code'], region['counts']['all']
        paths.append(f'<path class="municipality" data-code="{code}" d="{region["path"]}" tabindex="0" role="button" '
                     f'aria-label="{html.escape(region["name"])}: {count}. Visi metai." fill="#EBCEAE" fill-rule="evenodd"/>')
        labels.append(f'<text class="count-label" data-label="{code}" x="{region["x"]}" y="{region["y"]}" aria-hidden="true">{count}</text>')
    document = document.replace('__PATHS__', ''.join(paths)).replace('__LABELS__', ''.join(labels))
    output = root / 'outputs/03_savivaldybiu_zemelapis.html'
    output.write_text(document, encoding='utf-8')
    (root / 'outputs/tables/regional_map/map_payload.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return document


def notebook_map(document):
    from IPython.display import HTML
    return HTML('<iframe title="Interaktyvus Lietuvos savivaldybių žemėlapis" '
                'style="width:100%;height:1100px;border:0;background:#F7F5E7" '
                'sandbox="allow-scripts allow-same-origin" referrerpolicy="strict-origin-when-cross-origin" srcdoc="' + html.escape(document, quote=True) + '"></iframe>')
