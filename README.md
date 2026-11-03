# Vilkų medžioklės analizė su Python

Parengtas pradinis projektas. Analizė dar nepradėta.

## Paleidimas

Atidarykite PowerShell šiame aplanke ir vykdykite:

```powershell
.\.venv\Scripts\python.exe -m jupyterlab notebooks/01_pradzia.ipynb
```

Pasirinkite **Run > Run All Cells**. Taip pat galite paleisti `start_notebook.ps1`.

## Duomenys

`Vilkas_analizei_sveikata.csv` – vienintelis analizės įvesties failas: 12 pradinių stulpelių ir vienas išvestinis stulpelis su lietuviškais pavadinimais. `ID` laikomas tekstu. Tušti laukai
išlieka tušti; FALSE ir 0 nėra laikomi trūkstamomis reikšmėmis.
Pirminis `Vilkas.csv` nekeičiamas. Šaltinio reikšmės neperrašomos.

Datos, loginės reikšmės ir skaičiai kol kas įkeliami kaip tekstas.
Tipų keitimas, trūkstamų reikšmių tvarkymas, medžioklės sezonų apibrėžimas
ir geometrijos koordinačių sistema bus tikrinami analizės etape.
Duomenų eilutės nelaikomos unikaliais vilkais, kol tai nepatvirtinta.

## Struktūra

- `notebooks/01_pradzia.ipynb`: duomenų įkėlimas ir stiliaus peržiūra.
- `src/data_loading.py`: patvirtintų stulpelių patikra.
- `src/chart_style.py`: originalūs Matplotlib stiliaus pagalbiniai įrankiai.
- `config/chart_style.json`: Honey Sage spalvos ir šriftai.
- `assets/fonts/`: šriftai ir jų licencijos.
- `outputs/figures/`: diagramų failai.
- `outputs/tables/`: būsimų analizės lentelių failai.
- `requirements-lock.txt`: patikrintos aplinkos paketų versijos.

## Diagramos

Honey Sage tema perkelta iš projekto „1,2% GPM Analysis with Python“.
Šaltiniai: `config/chart_style.json`, `src/chart_style.py`, `assets/fonts/`.
Fonui naudojama #F7F5E7, tekstui #4B574B. Pagrindiniai šriftai:
Public Sans ir Slabo 13px. Didesnės reikšmės žymimos tamsesne spalva.
Spalvų vaidmenys pritaikomi konkrečiam klausimui; sveikatos būklės
automatiškai nesiejamos su finansinių rodiklių teigiamomis ar neigiamomis spalvomis.
Diagramos pavadinimai ir ašių žymos rašomi lietuviškai.

## Aplinkos atkūrimas

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Toliau: pasirinkti analizės klausimus ir atlikti duomenų kokybės patikrą.

Monospace šriftui naudojamas DejaVu Sans Mono: originalus Share Tech Mono nepalaiko visų lietuviškų raidžių.

## Suvestinės ir metinis pasiskirstymas

`notebooks/02_suvestines_ir_metai.ipynb` – 2018–2026 m. analizė. Naudotojo nurodymu 1979 ir 2003 m. įrašai neįtraukti. Kalendoriniai metai nustatomi pagal medžioklės laiką; tušti kategorijų laukai žymimi Nežinoma. 2026 m. duomenys baigiasi kovo 21 d.; kraštiniai metai gali būti nepilni. HTML peržiūra: `outputs/02_suvestines_ir_metai.html`. Suvestinės: `outputs/tables/totals_yearly/`. Diagramos PNG ir SVG: `outputs/figures/totals_yearly/`.

## Sveikatos sutrikimų stulpelis

`sveikatos sutrikimai`: TRUE, jei bent vienas iš dviejų sveikatos požymių TRUE; tuščia, jei abu tušti; kitu atveju FALSE. Pirminiai stulpeliai išsaugoti. CSV dabar turi 13 stulpelių.

## Interaktyvus savivaldybių žemėlapis

`notebooks/03_savivaldybiu_zemelapis.ipynb` – visos 60 savivaldybių ir interaktyvus metų pasirinkimas. Peržiūra: `outputs/03_savivaldybiu_zemelapis.html`. Naudojamos Eurostat–GISCO LAU 2024 ribos (EPSG:3035). Administracinės ribos © EuroGeographics; ribų naudojimas pagal GISCO nekomercinio naudojimo sąlygas. Šriftai ir valdiklis veikia neprisijungus prie interneto.

## Diagramų žymėjimas

Visose linijinėse diagramose pateikti visų ašies padalų užrašus ir kiekvieno taško skaitinę reikšmę. Skritulinių diagramų kategorijas, skaičius ir procentus rodyti skiltyse tik tada, kai tekstas telpa su tarpu iki kraštų. Kitus užrašus rodyti išorėje su jungiamąja linija. Išlaikyti šias taisykles atnaujinant diagramas.
