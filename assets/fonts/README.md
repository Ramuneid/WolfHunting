# Chart typography

Fonts identified from https://wondering.app/ on 30 September 2026:
Slabo 13px for the main heading, Public Sans for body text, and Share Tech Mono
for button labels. The site's Rubik logo font and course-specific decorative
fonts are not needed for the chart theme.

Official, unmodified TTF files are bundled from Google Fonts:
- https://github.com/google/fonts/tree/main/ofl/slabo13px
- https://github.com/google/fonts/tree/main/ofl/publicsans
- https://github.com/google/fonts/tree/main/ofl/sharetechmono

Public Sans also includes static Regular and Bold instances generated locally
by build_public_sans.py with fontTools. These are weight instances of the
original variable font, not a redesign. Matplotlib uses these static files.

Each directory includes its SIL Open Font License in OFL.txt. Keep these
licences with redistributed fonts. No system-wide installation or network
request is required when rendering charts.

Honey Sage uses Slabo 13px for chart titles and Public Sans for labels, values,
legends and notes. Share Tech Mono is optional via fontfamily="monospace".
Public Sans and DejaVu Sans provide fallback glyphs, including for Lithuanian.
Font choices live in config/chart_style.json and config/chart_style_honey_sage.json.
apply_chart_style registers the local fonts; finish_chart applies the title font.
Restart the kernel and rerun charts after updating. Existing saved outputs and
website styling are not rewritten by this change.
