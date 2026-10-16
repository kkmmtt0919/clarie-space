"""Three visible sleeve-top titles; creates new assets only."""
from PIL import Image, ImageDraw, ImageFont
from build_print_assets import OUT, BLACK, fpath

TITLES = {
    'about': '01·Claire/关于我',
    'projects': '02·我的作品',
    'world': '03·我的世界',
}


def build_title(topic, text):
    scale=4
    size=104
    ft=ImageFont.truetype(fpath('cjk'),size*scale)
    while ft.getlength(text)>1128*scale:
        size-=1
        ft=ImageFont.truetype(fpath('cjk'),size*scale)
    im=Image.new('RGBA',(1200*scale,140*scale))
    ImageDraw.Draw(im).text((36*scale,70*scale),text,font=ft,fill=BLACK,anchor='lm')
    im.resize((1200,140),Image.Resampling.LANCZOS).save(OUT/f'title-{topic}.png')
    (OUT/f'title-{topic}.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="140" viewBox="0 0 1200 140">'
        f'<title>Claire sleeve title / {text}</title>'
        f'<text x="36" y="74" dominant-baseline="central" font-family="Microsoft YaHei" '
        f'font-size="{size}" font-weight="700" fill="{BLACK}">{text}</text></svg>',encoding='utf-8')
    print(topic, im.size, 'font px',size)


if __name__=='__main__':
    for topic,text in TITLES.items():build_title(topic,text)
