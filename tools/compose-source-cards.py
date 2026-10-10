from pathlib import Path
import json, shutil, subprocess
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'design/art'
MARKS=ROOT/'design/marks'
SOURCES=[
('3isk','قصة عشق ١','3isk','qissat-eshq-1','https://3esk.onl'),
('eseek','قصة عشق ٢','Eseek','qissat-eshq-2','https://qeseh.net'),
('Krmzy','قرمزي','Krmzy','krmzy','https://krmzi.org'),
('MyCimaProvider','ماي سيما','MyCima','mycima','https://mycima.living'),
('Topcinema','توب سينما','TopCinema','topcinema','https://web8.topcinema.cam'),
('TukTukcima','توك توك سيما','TukTukCima','tuktukcima','https://tuktukhd.com'),
('Tuniflix','تونيفليكس','TuniFlix','tuniflix','https://tuniflix.site'),
('Wecima','وي سيما','WeCima','wecima','https://wecima.ac'),
]
def write(name,text):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
assets=ROOT/"src/LatchiWatching.App/wwwroot/assets"
fontdir=Path('/usr/share/fonts/truetype/dejavu')
def font(n,bold=False):return ImageFont.truetype(str(fontdir/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),n)
for idx,(key,ar,en,stem,url) in enumerate(SOURCES,1):
 im=ImageOps.fit(Image.open(ART/(stem+'.jpg')).convert('RGB'),(1800,600),method=Image.Resampling.LANCZOS).convert('RGBA')
 overlay=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(overlay)
 # Add accurate native branding, not hallucinated AI lettering or a white mockup canvas.
 for x in range(650,1800):
  alpha=round(135*min(1,(x-650)/600));d.line((x,0,x,600),fill=(7,11,20,alpha))
 d.rounded_rectangle((114,134,448,466),radius=74,fill=(10,15,28,220),outline=(242,193,78,110),width=3)
 mark=Image.open(MARKS/(key+'.png')).convert('RGBA');mark=ImageOps.contain(mark,(235,235),Image.Resampling.LANCZOS)
 if key=='Topcinema':
  mark=Image.new('RGBA',(235,235),(8,13,22,255));md=ImageDraw.Draw(mark)
  md.text((118,30),'TOP',font=font(78,True),fill=(239,60,76),anchor='ma')
  md.text((118,126),'CINEMA',font=font(43,True),fill=(226,232,243),anchor='ma')
 # ImageOps.contain also enlarges low-resolution favicons to a usable visual size.
 alpha=mark.getchannel('A');mask=Image.new('L',mark.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,mark.width-1,mark.height-1),radius=24,fill=255)
 from PIL import ImageChops
 mark.putalpha(ImageChops.multiply(alpha,mask));overlay.alpha_composite(mark,(281-mark.width//2,300-mark.height//2))
 d.text((1668,100),f'{idx:02d}  /  LATCHI WATCHING',font=font(29),fill=(177,183,197,255),anchor='ra')
 d.text((1668,195),ar,font=font(105,True),fill=(247,247,251,255),anchor='ra',direction='rtl',language='ar')
 d.text((1668,355),en,font=font(66,True),fill=(242,193,78,255),anchor='ra')
 d.line((1400,447,1668,447),fill=(242,193,78,200),width=4)
 d.text((1668,526),'أفلام • مسلسلات',font=font(42),fill=(177,188,209,255),anchor='ra',direction='rtl',language='ar')
 Image.alpha_composite(im,overlay).convert('RGB').save(assets/'sources'/(stem+'.jpg'),quality=94,subsampling=0,optimize=True)
ImageOps.fit(Image.open(ART/'background.jpg').convert('RGB'),(1800,600),method=Image.Resampling.LANCZOS).save(assets/'background.jpg',quality=94,subsampling=0,optimize=True)
