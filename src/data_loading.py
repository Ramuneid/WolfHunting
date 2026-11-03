"""Load only the approved columns, preserving source values as strings."""
from pathlib import Path
import pandas as pd

COLUMNS = [
    'ID', 'Medžioklės laikas', 'Savivaldybė', 'Medžiojimo būdas',
    'Amžius', 'Lytis', 'Ar pažeistas niežų', 'Ar kiti defektai',
    'sveikatos sutrikimai',
    'Ar priklausė gaujai', 'Viso gaujoje, vnt.',
    'Jauniklių gaujoje, vnt.', 'Geometrija',
]

def load_data(project_root: Path) -> pd.DataFrame:
    path = Path(project_root) / 'Vilkas_analizei_sveikata.csv'
    data = pd.read_csv(path, encoding='utf-8-sig', dtype='string',
                       keep_default_na=False)
    if list(data.columns) != COLUMNS:
        raise ValueError('CSV columns differ from the approved 13-column schema.')
    return data
