"""Assemble actual frame renders into shareable GIFs and contact sheets."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
out = root/'previews'
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
for mode in ('opening','hover'):
    folder = out/mode
    metadata = json.loads((folder/'frames.json').read_text(encoding='utf-8'))
    paths = sorted(folder.glob('*.png'))
    assert len(paths) == len(metadata['frames'])
    # One common palette per clip prevents per-frame color-map flicker.
    palette = Image.open(paths[len(paths)//2]).convert('RGB').quantize(colors=256)
    images = [Image.open(path).convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE) for path in paths]
    images[0].save(out/(mode+'-v3.gif'), save_all=True, append_images=images[1:], duration=[67]*len(images), loop=0, disposal=2, optimize=False)
    indices = [round(i*(len(paths)-1)/11) for i in range(12)]
    sheet = Image.new('RGB',(1200,3*249),'#f1f1f1')
    draw = ImageDraw.Draw(sheet)
    for slot,index in enumerate(indices):
        x,y=(slot%3)*400,(slot//3)*249
        image = Image.open(paths[index]).convert('RGB').resize((400,225),Image.Resampling.LANCZOS)
        sheet.paste(image,(x,y))
        draw.text((x+8,y+228),f'{mode} / frame {metadata["frames"][index]:03d}',font=font,fill='#222222')
    # Four rows for twelve frames.
    if len(indices) == 12:
        sheet = Image.new('RGB',(1200,4*249),'#f1f1f1')
        draw = ImageDraw.Draw(sheet)
        for slot,index in enumerate(indices):
            x,y=(slot%3)*400,(slot//3)*249
            sheet.paste(Image.open(paths[index]).convert('RGB').resize((400,225),Image.Resampling.LANCZOS),(x,y))
            draw.text((x+8,y+228),f'{mode} / frame {metadata["frames"][index]:03d}',font=font,fill='#222222')
    sheet.save(out/(mode+'-contact-sheet.jpg'),quality=92)
keys=out/'keys'
paths=sorted(keys.glob('*.png'))
frames=json.loads((keys/'frames.json').read_text(encoding='utf-8'))['frames']
sheet=Image.new('RGB',(1200,5*249),'#f1f1f1')
draw=ImageDraw.Draw(sheet)
for slot,(path,frame) in enumerate(zip(paths,frames)):
    x,y=(slot%3)*400,(slot//3)*249
    sheet.paste(Image.open(path).convert('RGB').resize((400,225),Image.Resampling.LANCZOS),(x,y))
    draw.text((x+8,y+228),f'V3 / frame {frame:03d}',font=font,fill='#222222')
sheet.save(out/'keyframes-contact-sheet.jpg',quality=92)
print('PREVIEWS_ASSEMBLED',out)
