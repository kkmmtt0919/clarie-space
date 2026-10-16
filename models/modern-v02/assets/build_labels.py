"""Additional labels only; leaves the six approved disc/sleeve images untouched."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from build_print_assets import Vector, OUT, BLACK, RED, WHITE, fpath


def playing_badge():
    scale = 4
    im = Image.new('RGBA', (500*scale, 140*scale))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 500*scale-1, 140*scale-1), radius=12*scale, fill=RED)
    ft = ImageFont.truetype(fpath('cjk'), 74*scale)
    d.text((250*scale, 70*scale), '正在播放', fill=BLACK, font=ft, anchor='mm')
    im.resize((500, 140), Image.Resampling.LANCZOS).save(OUT/'playing-badge.png')
    (OUT/'playing-badge.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="500" height="140" viewBox="0 0 500 140">'
        '<title>Claire / 正在播放</title>'
        f'<rect x="0" y="0" width="500" height="140" rx="12" fill="{RED}"/>'
        f'<text x="250" y="74" text-anchor="middle" dominant-baseline="central" '
        f'font-family="Microsoft YaHei" font-size="74" font-weight="700" fill="{BLACK}">正在播放</text>'
        '</svg>', encoding='utf-8')


def lid_label():
    v=Vector('lid-label')
    v.torn(150,380,700,240,WHITE,82,slant=-8)
    v.text(470,500,'CLAIRE',119,BLACK,'bold',-2)
    # Six slightly irregular hand-drawn star strokes, no cartoon face.
    v.line([(762,443),(781,465),(803,448),(795,478),(818,490),(789,492),
            (782,520),(768,497),(742,505),(753,481),(735,464),(763,467),(762,443)],BLACK,5)
    v.save()
    path=OUT/'lid-label.png'
    Image.open(path).resize((1024,1024),Image.Resampling.LANCZOS).save(path)
    svg=OUT/'lid-label.svg'
    svg.write_text(svg.read_text(encoding='utf-8').replace('width="1600" height="1600"',
                   'width="1024" height="1024"'),encoding='utf-8')


if __name__=='__main__':
    playing_badge()
    lid_label()
    print('playing-badge.png (500x140) + lid-label.png (1024x1024), matching SVG sources complete.')
