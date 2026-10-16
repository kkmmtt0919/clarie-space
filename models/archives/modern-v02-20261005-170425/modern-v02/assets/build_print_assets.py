"""Claire: vector-authored print assets with matching SVG and RGBA previews.

Uses only Pillow + fonts installed with Windows. No reference photo is cropped,
and no external raster assets or generated character illustrations are used.
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont, ImageChops

OUT = Path(__file__).resolve().parent
SIZE = 1600
WORK = 2400
SCALE = WORK / 1000
FONTS = Path('C:/Windows/Fonts')
BLACK = '#171719'
WHITE = '#f5f2e9'
RED = '#f14b35'
BLUE = '#2455eb'
ACID = '#cbef3b'
GRAY = '#767879'


def fpath(name):
    return str(FONTS / {'sans': 'arial.ttf', 'bold': 'arialbd.ttf',
                       'mono': 'consola.ttf', 'cjk': 'msyhbd.ttc'}[name])


def fontfamily(name):
    return {'sans': 'Arial', 'bold': 'Arial', 'mono': 'Consolas',
            'cjk': 'Microsoft YaHei'}[name]


class Vector:
    def __init__(self, name, disc=False):
        self.name, self.disc = name, disc
        self.im = Image.new('RGBA', (WORK, WORK))
        self.d = ImageDraw.Draw(self.im)
        self.svg = []

    def rect(self, x, y, w, h, fill, stroke=None, width=1):
        self.d.rectangle(tuple(v*SCALE for v in (x,y,x+w,y+h)),
                         fill=fill, outline=stroke, width=max(1, round(width*SCALE)))
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
                        + (f' stroke="{stroke}" stroke-width="{width}"' if stroke else '') + '/>')

    def poly(self, pts, fill, stroke=None, width=1):
        self.d.polygon([(x*SCALE,y*SCALE) for x,y in pts], fill=fill)
        if stroke:
            self.d.line([(x*SCALE,y*SCALE) for x,y in pts+[pts[0]]], fill=stroke,
                        width=round(width*SCALE), joint='curve')
        points=' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)
        self.svg.append(f'<polygon points="{points}" fill="{fill}"'
                        + (f' stroke="{stroke}" stroke-width="{width}"' if stroke else '') + '/>')

    def line(self, pts, fill=BLACK, width=2):
        self.d.line([(x*SCALE,y*SCALE) for x,y in pts], fill=fill,
                    width=max(1, round(width*SCALE)), joint='curve')
        points=' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)
        self.svg.append(f'<polyline points="{points}" fill="none" stroke="{fill}" '
                        f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')

    def ellipse(self, x, y, rx, ry, fill, stroke=None, width=1):
        self.d.ellipse(tuple(v*SCALE for v in (x-rx,y-ry,x+rx,y+ry)),
                       fill=fill, outline=stroke, width=max(1, round(width*SCALE)))
        self.svg.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}"'
                        + (f' stroke="{stroke}" stroke-width="{width}"' if stroke else '') + '/>')

    def text(self, x,y,s,size=30,fill=BLACK,font='sans',angle=0):
        ft=ImageFont.truetype(fpath(font), round(size*SCALE))
        bb=ft.getbbox(s)
        w,h=bb[2]-bb[0],bb[3]-bb[1]
        pad=round(12*SCALE)
        tile=Image.new('RGBA',(w+2*pad,h+2*pad))
        ImageDraw.Draw(tile).text((pad-bb[0],pad-bb[1]),s,font=ft,fill=fill)
        tile=tile.rotate(-angle,resample=Image.Resampling.BICUBIC,expand=True)
        self.im.alpha_composite(tile,(round(x*SCALE-tile.width/2),round(y*SCALE-tile.height/2)))
        self.svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="central" '
                        f'font-family="{fontfamily(font)}" font-size="{size}" '
                        f'font-weight="{"700" if font in ("bold","cjk") else "400"}" fill="{fill}" '
                        f'transform="rotate({angle} {x} {y})">{escape(s)}</text>')

    def arc(self,s,r=410,size=22,fill=BLACK,bottom=False):
        ft=ImageFont.truetype(fpath('bold'),round(size*SCALE))
        widths=[ft.getlength(c)/SCALE+1.8 for c in s]
        total=sum(widths)
        at=-total/2
        for c,w in zip(s,widths):
            theta=(at+w/2)/r
            if bottom:
                x=500+r*math.sin(theta); y=500+r*math.cos(theta)
                angle=-math.degrees(theta)
            else:
                x=500+r*math.sin(theta); y=500-r*math.cos(theta)
                angle=math.degrees(theta)
            self.text(x,y,c,size,fill,'bold',angle)
            at+=w

    def torn(self,x,y,w,h,fill=WHITE,seed=1,slant=0):
        rnd=random.Random(seed)
        pts=[]
        for i in range(15):
            xx=x+w*i/14
            pts.append((xx,y+rnd.uniform(-5,5)+slant*(i/14-.5)))
        for i in range(7):
            yy=y+h*i/6
            pts.append((x+w+rnd.uniform(-4,4),yy+slant/2))
        for i in range(15):
            xx=x+w*(1-i/14)
            pts.append((xx,y+h+rnd.uniform(-5,5)+slant*(.5-i/14)))
        for i in range(7):
            yy=y+h*(1-i/6)
            pts.append((x+rnd.uniform(-4,4),yy-slant/2))
        self.poly(pts,fill)

    def asterisk(self,x,y,r=50,fill=RED,angle=0):
        pts=[]
        for i in range(24):
            a=math.radians(i*15+angle)
            rr=r if i%4 in (0,1) else r*.28
            pts.append((x+rr*math.cos(a),y+rr*math.sin(a)))
        self.poly(pts,fill)

    def arrow(self,pts,fill=BLACK,width=5,head=24):
        self.line(pts,fill,width)
        x,y=pts[-1]; px,py=pts[-2]
        a=math.atan2(y-py,x-px)
        self.poly([(x,y),(x-head*math.cos(a-.5),y-head*math.sin(a-.5)),
                   (x-head*math.cos(a+.5),y-head*math.sin(a+.5))],fill)

    def barcode(self,x,y,w=90,h=42,seed=2):
        rnd=random.Random(seed); xx=x
        while xx<x+w:
            ww=rnd.choice([1.4,2.4,3.8])
            self.rect(xx,y,ww,h,BLACK)
            xx+=ww+rnd.choice([1.8,3.1,4.3])

    def save(self):
        if self.disc:
            mask=Image.new('L',(WORK,WORK)); md=ImageDraw.Draw(mask)
            md.ellipse((40*SCALE,40*SCALE,960*SCALE,960*SCALE),fill=255)
            md.ellipse((435*SCALE,435*SCALE,565*SCALE,565*SCALE),fill=0)
            self.im.putalpha(ImageChops.multiply(self.im.getchannel('A'),mask))
        self.im.resize((SIZE,SIZE),Image.Resampling.LANCZOS).save(OUT/(self.name+'.png'))
        defs=''
        if self.disc:
            defs='<defs><clipPath id="disc"><path fill-rule="evenodd" d="M 960 500 A 460 460 0 1 0 40 500 A 460 460 0 1 0 960 500 Z M 565 500 A 65 65 0 1 1 435 500 A 65 65 0 1 1 565 500 Z"/></clipPath></defs>'
        group=' clip-path="url(#disc)"' if self.disc else ''
        svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1600" viewBox="0 0 1000 1000">'
             f'<title>{self.name}: Claire original editorial print design</title>{defs}<g{group}>'
             +''.join(self.svg)+'</g></svg>')
        (OUT/(self.name+'.svg')).write_text(svg,encoding='utf-8')


def paper_grid(v,x,y,w,h,fill=WHITE,ink='#c9ccce',step=24):
    v.rect(x,y,w,h,fill)
    for xx in range(round(x),round(x+w),step):v.line([(xx,y),(xx,y+h)],ink,.8)
    for yy in range(round(y),round(y+h),step):v.line([(x,yy),(x+w,yy)],ink,.8)


def workflow(v,x,y,w=235,h=160):
    """A purpose-designed process clipping, not a fabricated personal screenshot."""
    v.rect(x,y,w,h,WHITE,BLACK,1)
    v.rect(x,y,w,20,BLACK)
    v.text(x+w/2,y+10,'IDEA / BUILD / REPEAT',8,WHITE,'mono')
    for i in range(3):
        xx=x+12+i*(w-24)/3
        v.rect(xx,y+40,(w-40)/3,h-59,BLUE if i==1 else '#dedfe1')
        v.text(xx+(w-40)/6,y+65,str(i+1).zfill(2),19,WHITE if i==1 else BLACK,'bold')
        for j in range(3):v.line([(xx+8,y+92+j*8),(xx+(w-40)/3-8,y+92+j*8)],WHITE if i==1 else GRAY,1)


def botanical(v,x,y,s=1):
    """Xerox-inspired flower cutout with lean stems, irregular black petals."""
    def p(px,py):return(x+px*s,y+py*s)
    for cx,cy,rr in [(0,0,54),(61,-92,33),(-66,-67,32)]:
        v.line([p(cx,cy),p(cx*.6,134),p(6,239)],BLACK,2.8*s)
        rnd=random.Random(round(cx+90))
        for k in range(11):
            a=2*math.pi*k/11
            pts=[]
            for q in range(14):
                t=2*math.pi*q/14
                rad=rr*(.43+.025*rnd.uniform(-1,1))
                uu=rr*.59+math.cos(t)*rad
                vv=math.sin(t)*rr*.14
                pts.append(p(cx+uu*math.cos(a)-vv*math.sin(a),cy+uu*math.sin(a)+vv*math.cos(a)))
            v.poly(pts,BLACK)
        v.ellipse(*p(cx,cy),rr*.22*s,rr*.22*s,WHITE)
        for k in range(17):
            a=2*math.pi*k/17
            v.ellipse(*p(cx+rr*.13*math.cos(a),cy+rr*.13*math.sin(a)),1.1*s,1.1*s,BLACK)
    v.poly([p(-3,149),p(-82,109),p(-90,112),p(-42,162)],BLACK)
    v.poly([p(4,178),p(65,141),p(88,139),p(44,185)],BLACK)


def ticket(v,x,y,w=225,h=140):
    v.poly([(x,y+9),(x+9,y),(x+w-9,y),(x+w,y+9),(x+w,y+h-9),
            (x+w-9,y+h),(x+9,y+h),(x,y+h-9)],ACID)
    for yy in range(round(y+13),round(y+h-8),9):v.line([(x+w*.72,yy),(x+w*.72,yy+3)],BLACK,1)
    v.text(x+w*.36,y+24,'SIDE C / 03',13,BLACK,'mono')
    v.text(x+w*.36,y+61,'OFF DUTY',22,BLACK,'bold')
    v.text(x+w*.36,y+91,'SOUNDS + SMALL THINGS',8,BLACK,'mono')
    v.text(x+w*.36,y+116,'ADMIT ONE • KEEP FOREVER',7,BLACK,'mono')
    v.barcode(x+w*.78,y+17,w*.12,h-34)


def pixel(v,x,y,cell=10):
    rows=['00111000','01101100','11000110','10010001','10101001','11000110','01101100','00111000']
    for j,row in enumerate(rows):
        for i,c in enumerate(row):
            v.rect(x+i*cell,y+j*cell,cell,cell,BLACK if c=='1' else WHITE)


def disc_about():
    v=Vector('disc-about',True)
    v.arc('01 / ABOUT ME • CLAIRE • NOT A FINISHED VERSION',410,21)
    v.arc('HELLO, I AM CLAIRE / KEEP IT A LITTLE STRANGE',401,18,bottom=True)
    v.asterisk(270,294,72,RED,8)
    v.torn(290,278,467,112,WHITE,34,slant=-23)
    v.text(525,335,'CLAIRE',92,BLACK,'bold',-3)
    v.torn(181,616,395,48,WHITE,55,slant=15)
    v.text(380,640,'PERSONAL / STILL BECOMING',18,BLACK,'mono',2)
    v.rect(692,585,59,102,RED)
    v.text(722,616,'01',25,BLACK,'bold')
    v.text(722,653,'A-SIDE',9,BLACK,'mono',90)
    v.line([(636,707),(718,707)],BLACK,3)
    v.text(480,750,'GOOD DAYS. WEIRD IDEAS.',17,BLACK,'mono',-3)
    v.save()


def disc_projects():
    v=Vector('disc-projects',True)
    v.arc('02 / SELECTED WORK • MAKE / TRY / LEARN',409,22)
    v.arc('PROCESS OVER PERFECTION / BACK TO THE DRAWING BOARD',400,16,bottom=True)
    v.text(286,335,'02',143,BLUE,'bold',-7)
    v.torn(500,260,284,102,WHITE,64,slant=21)
    v.text(643,300,'MAKE IT.',35,BLACK,'bold',4)
    v.text(643,337,'THEN MAKE IT BETTER.',12,BLACK,'mono',4)
    workflow(v,224,583,280,178)
    v.arrow([(590,611),(682,611),(682,722),(755,722)],BLUE,9,32)
    v.text(706,572,'VERSION 02',13,BLACK,'mono')
    v.save()


def disc_world():
    v=Vector('disc-world',True)
    v.arc('03 / MY WORLD • FLOWERS / MUSIC / LITTLE JOYS',410,20)
    v.arc('OFF DUTY / SMALL THINGS, LOUD FEELINGS',399,18,bottom=True)
    botanical(v,307,532,.79)
    ticket(v,532,267,275,159)
    pixel(v,626,633,13)
    v.text(715,762,'NO FIXED GENRE',12,BLACK,'mono')
    v.line([(400,766),(498,766)],BLACK,2)
    v.text(435,706,'PLAY IT AGAIN.',13,BLACK,'mono',-7)
    v.save()


def base_cover(name,num,title,accent):
    v=Vector(name)
    v.rect(0,0,1000,1000,WHITE)
    v.rect(27,26,946,948,WHITE,BLACK,2)
    v.rect(55,51,37,37,accent)
    v.text(73,69,num,17,BLACK,'bold')
    v.text(840,68,'CLAIRE / ARCHIVE',17,BLACK,'mono')
    v.text(500,144,title,63,BLACK,'cjk')
    v.line([(55,210),(945,210)],BLACK,2)
    return v


def cover_about():
    v=base_cover('cover-about','01','关于我',RED)
    v.text(340,285,'WHO IS',52,BLACK,'bold',-3)
    v.asterisk(760,305,103,RED,8)
    # Intentional cut-letter collage: one name, only six pieces.
    widths=[111,95,107,63,114,110]
    xx=99
    for i,(char,ww) in enumerate(zip('CLAIRE',widths)):
        yy=397+[8,-11,3,-15,10,-5][i]
        col=RED if i==1 else '#e4e0d6'
        v.torn(xx,yy,ww,154,col,60+i,slant=[-9,5,-6,8,-3,10][i])
        v.text(xx+ww/2,yy+77,char,113,BLACK,'bold',[-5,3,-2,5,-3,4][i])
        xx+=ww+9
    v.text(431,637,'NOT A FINISHED VERSION.',25,BLACK,'mono')
    v.text(399,686,'Good days. Weird ideas. Still becoming.',17,BLACK,'mono')
    v.line([(88,790),(466,790)],BLACK,2)
    v.text(278,823,'SIDE A / PERSONAL NOTES',16,BLACK,'mono')
    v.barcode(757,780,130,70)
    v.text(821,867,'CL-001',12,BLACK,'mono')
    v.text(500,934,'ABOUT ME • SAY HELLO • KEEP IT A LITTLE STRANGE',13,BLACK,'mono')
    v.save()


def cover_projects():
    v=base_cover('cover-projects','02','我的作品',BLUE)
    v.text(278,406,'02',240,BLUE,'bold',-6)
    v.text(719,315,'SELECTED',37,BLACK,'bold')
    v.text(719,365,'WORK',66,BLACK,'bold')
    v.text(713,423,'MAKE / TRY / LEARN',17,BLACK,'mono')
    workflow(v,114,602,412,238)
    v.arrow([(602,576),(602,748),(815,748)],BLUE,14,48)
    v.text(732,653,'FROM IDEA',17,BLACK,'mono')
    v.text(732,683,'TO SOMETHING REAL.',17,BLACK,'mono')
    v.text(732,816,'PROCESS > PERFECTION',14,BLACK,'mono')
    v.text(500,934,'PROJECTS / SYSTEMS / ITERATIONS • CLAIRE ARCHIVE',13,BLACK,'mono')
    v.save()


def cover_world():
    v=base_cover('cover-world','03','我的世界',ACID)
    botanical(v,273,494,1.19)
    ticket(v,548,305,315,220)
    v.text(724,572,'MY WORLD',29,BLACK,'bold')
    v.text(724,615,'NO FIXED GENRE.',17,BLACK,'mono')
    pixel(v,664,680,16)
    v.text(351,865,'SMALL THINGS, LOUD FEELINGS.',18,BLACK,'mono')
    v.text(500,934,'FLOWERS / MUSIC / HANDMADE / EVERYDAY FINDS',13,BLACK,'mono')
    v.save()


def preview():
    board=Image.new('RGB',(1800,1310),'#dddcd8')
    draw=ImageDraw.Draw(board)
    ft=ImageFont.truetype(fpath('mono'),23)
    for i,topic in enumerate(('about','projects','world')):
        disc=Image.open(OUT/f'disc-{topic}.png').resize((540,540),Image.Resampling.LANCZOS)
        # Neutral metal underlay solely for review. NOT baked into exported PNG.
        plate=Image.new('RGBA',(540,540))
        pd=ImageDraw.Draw(plate)
        pd.ellipse((22,22,518,518),fill='#c3c9cb')
        pd.ellipse((235,235,305,305),fill='#dddcd8')
        plate.alpha_composite(disc)
        board.paste(plate,(30+i*600,55),plate)
        cover=Image.open(OUT/f'cover-{topic}.png').convert('RGB').resize((540,540),Image.Resampling.LANCZOS)
        board.paste(cover,(30+i*600,680))
        draw.text((30+i*600,15),f'{i+1:02d} / {topic.upper()}',font=ft,fill=BLACK)
    board.save(OUT/'asset-review.png')


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    for func in (disc_about,disc_projects,disc_world,cover_about,cover_projects,cover_world):
        func()
        print(func.__name__+' ready',flush=True)
    preview()
    print('Six PNG + six SVG + asset-review.png complete.',flush=True)
