"""Draw the review plan from the same traced coordinates as Blender."""
import json
from pathlib import Path

directory = Path(__file__).resolve().parent
plan = json.loads((directory / 'plan-trace.json').read_text(encoding='utf-8'))
layers = ["""<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.05 -3.15 16.5 21" role="img" aria-labelledby="title">
<title id="title">按新图建立的户型核对图</title>
<style>
text{font-family:"Microsoft YaHei","PingFang SC",sans-serif;fill:#263b33}
.label{font-size:.28px;text-anchor:middle}
.minor{fill:#627870;font-size:.25px}
</style>
<rect x="-1.05" y="-3.15" width="16.5" height="21" fill="#f8f7f2"/>
<text x="0" y="-2.43" font-size=".51" font-weight="700">2-21101 · 户型核对图</text>
<text x="0" y="-1.93" class="minor">2026-11-21 · 照片校正 · 除标注总尺寸外均为描摹估算</text>
<text x="12.85" y="-2.40" font-size=".38" text-anchor="end">北 ↑</text>"""]


def path_points(points):
    return ' '.join(f'{x},{y}' for x, y in points)


def shape(tag, points, style):
    layers.append(f'<{tag} points="{path_points(points)}" {style}/>')


def line(coords, style):
    x1, y1, x2, y2 = coords
    layers.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {style}/>')


shape('polygon', plan['footprint'], 'fill="#e7e2d6"')
shape('polygon', plan['terrace'], 'fill="#e0e8dc"')
for key in ('MasterBath', 'CommonBath', 'Housekeeping'):
    shape('polygon', plan['rooms'][key], 'fill="#dfe7e8"')
for pts in plan['planAnnotations']['structuralCantilevers']:
    shape('polygon', pts, 'fill="#e6d6aa" fill-opacity=".48" stroke="#a28b54" stroke-width=".025"')
for pts in plan['planAnnotations']['upperPlatformProjection']:
    shape('polyline', pts, 'fill="none" stroke="#7b837e" stroke-width=".04" stroke-dasharray=".25 .13"')
shape('polyline', plan['rail'], 'fill="none" stroke="#55745d" stroke-width=".065"')
for _, coords, thickness, *status in plan['walls']:
    color = '#858f86' if status == ['heightUnconfirmed'] else '#364842'
    line(coords, f'stroke="{color}" stroke-width="{thickness}" stroke-linecap="square"')
for coords, _, _ in plan['glazing'].values():
    line(coords, 'stroke="#5b8490" stroke-width=".10"')
for coords in plan['doors'].values():
    line(coords, 'stroke="#a4683d" stroke-width=".064" stroke-dasharray=".13 .07"')

for label, x, y in [
    ('次卧1', 2.38, 2.92), ('书房', 5.38, 2.92), ('厨房', 8.05, 2.82),
    ('客卫', 1.81, 5.70), ('主卫', 2.02, 7.45), ('玄关', 9.77, 5.55),
    ('家政间', 10.08, 7.50), ('主卧', 2.02, 10.60), ('客餐厅', 6.55, 9.03),
    ('次卧3', 11.23, 10.14), ('南向露台', 8.08, 14.42),
]:
    layers.append(f'<text x="{x}" y="{y}" class="label">{label}</text>')

dimension = 'stroke="#61756e" stroke-width=".025"'
for coords in [(0,16.41,12.85,16.41),(0,16.10,0,16.58),(12.85,16.10,12.85,16.58),
               (13.68,0,13.68,12.65),(13.43,0,13.95,0),(13.43,12.65,13.95,12.65)]:
    line(coords, dimension)
layers.append('<text x="6.425" y="16.85" class="label">12.85 米</text>')
layers.append('<text x="14.06" y="6.33" class="label" transform="rotate(90 14.06 6.33)">12.65 米 · 厨房北边至厅南边</text>')
layers.append('<text x="0" y="17.50" class="minor">橙虚线＝门洞　蓝线＝窗或玻璃门　灰虚线＝上层投影　浅黄＝结构挑板</text></svg>')
(directory / 'plan-check.svg').write_text('\n'.join(layers), encoding='utf-8')
