from pathlib import Path
import re, html, json, zipfile, uuid, base64, textwrap
from xml.etree import ElementTree as ET
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, KeepTogether, CondPageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from pypdf import PdfReader
from PIL import Image as PILImage, ImageOps, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
text = (ROOT/'manuscrito.md').read_text(encoding='utf-8')
parts = re.split(r'^### (.+)$',text,flags=re.M)
chapters = [(parts[i],parts[i+1].strip()) for i in range(1,len(parts),2)]
assert len(chapters)==10
words = len(re.findall(r'\b[\wÀ-ÿ]+\b','\n'.join(b for _,b in chapters)))
chapdir=ROOT/'capitulos'; chapdir.mkdir(exist_ok=True)
for i,(title,body) in enumerate(chapters,1):
    (chapdir/f'{i:02}.md').write_text(f'# {title}\n\n{body}\n',encoding='utf-8')
plain='A ÁGUA DO DESPERTAR\nO encontro\nLivro 1\n\n'+'\n\n'.join(f'{a}\n\n{b}' for a,b in chapters)
(ROOT/'texto-para-caderno.txt').write_text(plain+'\n',encoding='utf-8')
presentation=(ROOT/'apresentacao.md').read_text(encoding='utf-8')
back=presentation.split('## Texto de contracapa\n\n')[1].split('\n## ')[0].strip()
synopsis=presentation.split('## Síntese da história\n\n')[1].split('\n## ')[0].strip()
cover=ROOT/'capa-conceitual.png'
with PILImage.open(cover) as im:
    im.convert('RGB').save(ROOT/'capa-frontal.jpg',quality=97)
cover_b64=base64.b64encode(cover.read_bytes()).decode()
def paras(body):
    return ''.join('<p>'+html.escape(p).replace('\n',' ')+'</p>' for p in body.split('\n\n') if p.strip())
css='body{font-family:Georgia,serif;line-height:1.6;max-width:42em;margin:auto;padding:2em;color:#172731}h1,h2{text-align:center;line-height:1.25}section{break-before:page;margin-top:3em}p{text-align:justify}img{max-width:100%;height:auto}.cover{max-width:28em;display:block;margin:auto}nav li{margin:.4em 0}@media print{body{padding:0}a{color:inherit;text-decoration:none}}'
nav=''.join(f'<li><a href="#c{i}">{html.escape(a)}</a></li>' for i,(a,_) in enumerate(chapters,1))
reader='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>A Água do Despertar — O encontro</title><style>'+css+'</style><body><img class="cover" alt="Capa: uma garrafa de água é entregue numa rua ao anoitecer" src="data:image/png;base64,'+cover_b64+'"><h1>A Água do Despertar</h1><h2>O encontro</h2><p style="text-align:center">Livro 1</p><nav><h2>Sumário</h2><ol>'+nav+'</ol></nav>'
for i,(a,b) in enumerate(chapters,1):reader+=f'<section id="c{i}"><h2>{html.escape(a)}</h2>{paras(b)}</section>'
reader+='<section><h2>Contracapa</h2>'+paras(back)+'</section></body></html>'
(ROOT/'livro.html').write_text(reader,encoding='utf-8')

fonts=Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Book',str(fonts/'georgia.ttf')))
pdfmetrics.registerFont(TTFont('BookBold',str(fonts/'georgiab.ttf')))
pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='Book',boldItalic='BookBold')
body_style=ParagraphStyle('body',fontName='Book',fontSize=11.3,leading=15.4,alignment=TA_JUSTIFY,spaceAfter=6,allowWidows=0,allowOrphans=0)
title_style=ParagraphStyle('title',fontName='BookBold',fontSize=27,leading=34,alignment=TA_CENTER,spaceAfter=20,textColor='#123540')
head_style=ParagraphStyle('heading',fontName='BookBold',fontSize=18,leading=25,spaceAfter=22,textColor='#123540')
small=ParagraphStyle('small',fontName='Book',fontSize=10,leading=16,alignment=TA_CENTER,spaceAfter=12)
page=(419.528,595.276)
pdf=ROOT/'A Agua do Despertar - leitura.pdf'
def footer(canvas,doc):
    if doc.page>1:
        canvas.saveState();canvas.setFont('Book',8);canvas.setFillColorRGB(.35,.4,.42)
        canvas.drawCentredString(page[0]/2,23,str(doc.page-1));canvas.restoreState()
doc=SimpleDocTemplate(str(pdf),pagesize=page,rightMargin=43,leftMargin=47,topMargin=43,bottomMargin=43,title='A Água do Despertar — O encontro',author='',pageCompression=1)
story=[Spacer(1,18),Image(str(cover),width=300,height=450),PageBreak(),Spacer(1,60),Paragraph('A Água do Despertar',title_style),Paragraph('O encontro',head_style),Paragraph('Livro 1',small),Spacer(1,30),Paragraph('Uma novela de ficção científica e suspense',small),PageBreak(),Paragraph('Sumário',head_style)]
for a,_ in chapters:story.append(Paragraph(html.escape(a),body_style))
story.append(PageBreak())
for i,(a,b) in enumerate(chapters):
    if i:story.extend([CondPageBreak(210),Spacer(1,26)])
    story.append(Paragraph(html.escape(a),head_style))
    for p in b.split('\n\n'):
        if p.strip():story.append(Paragraph(html.escape(p).replace('\n',' '),body_style))
story.extend([PageBreak(),Paragraph('Contracapa',head_style)])
for p in back.split('\n\n'):story.append(Paragraph(html.escape(p),body_style))
doc.build(story,onFirstPage=footer,onLaterPages=footer)

# Contracapa editável, composição tipográfica original em SVG.
lines=[]
for p in back.split('\n\n'):
    lines.extend(textwrap.wrap(p,width=46));lines.append('')
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="2560" viewBox="0 0 1600 2560">','<rect width="1600" height="2560" fill="#0b202c"/>','<path d="M150 220H1450" stroke="#c5a566" stroke-width="3"/>','<text x="150" y="360" fill="#eedbb1" font-family="Georgia,serif" font-size="58">A ÁGUA DO DESPERTAR</text>','<text x="150" y="455" fill="#a4c9d7" font-family="Georgia,serif" font-size="42">O encontro · Livro 1</text>']
y=650
for line in lines:
    if line:svg.append(f'<text x="150" y="{y}" fill="#f5f0e6" font-family="Georgia,serif" font-size="42">{html.escape(line)}</text>')
    y+=64
svg.append('</svg>')
(ROOT/'contracapa-editavel.svg').write_text('\n'.join(svg),encoding='utf-8')
# Visualização tipográfica da contracapa sem modificar a arte frontal.
im=PILImage.new('RGB',(1600,2560),'#0b202c');d=ImageDraw.Draw(im)
f=ImageFont.truetype(str(fonts/'georgia.ttf'),42);ft=ImageFont.truetype(str(fonts/'georgiab.ttf'),58)
d.line((150,220,1450,220),fill='#c5a566',width=3)
d.text((150,300),'A ÁGUA DO DESPERTAR',font=ft,fill='#eedbb1')
d.text((150,410),'O encontro · Livro 1',font=f,fill='#a4c9d7')
y=605
for line in lines:
    d.text((150,y),line,font=f,fill='#f5f0e6');y+=64
im.save(ROOT/'contracapa.png')

identifier='urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,'a-agua-do-despertar-o-encontro-2026-10-07'))
ns='http://www.w3.org/1999/xhtml'
def xhtml(title,body):
    return '<?xml version="1.0" encoding="utf-8"?><html xmlns="'+ns+'" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="pt-BR" lang="pt-BR"><head><title>'+html.escape(title)+'</title><link rel="stylesheet" type="text/css" href="style.css"/></head><body>'+body+'</body></html>'
files={'style.css':'body{font-family:serif;line-height:1.45}h1,h2{text-align:center}p{margin:.6em 0;text-indent:1.2em}img{max-width:100%;height:auto}.cover{text-align:center}.cover p{text-indent:0}',
'cover.xhtml':xhtml('Capa','<div class="cover"><img src="cover.jpg" alt="A Água do Despertar — O encontro. Livro 1. Uma garrafa de água é entregue numa rua ao anoitecer."/></div>'),
'title.xhtml':xhtml('A Água do Despertar','<h1>A Água do Despertar</h1><h2>O encontro</h2><p>Livro 1</p>')}
for i,(a,b) in enumerate(chapters,1):files[f'c{i:02}.xhtml']=xhtml(a,'<h1>'+html.escape(a)+'</h1>'+paras(b))
files['back.xhtml']=xhtml('Contracapa','<h1>Contracapa</h1>'+paras(back))
navitems=''.join(f'<li><a href="c{i:02}.xhtml">{html.escape(a)}</a></li>' for i,(a,_) in enumerate(chapters,1))
files['nav.xhtml']=xhtml('Sumário','<nav epub:type="toc" id="toc"><h1>Sumário</h1><ol>'+navitems+'<li><a href="back.xhtml">Contracapa</a></li></ol></nav>')
manifest='<item id="img" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>'
for name in files:
    prop=' properties="nav"' if name=='nav.xhtml' else ''
    mt='text/css' if name.endswith('.css') else 'application/xhtml+xml'
    manifest+=f'<item id="{name.split(".")[0]}" href="{name}" media-type="{mt}"{prop}/>'
order=['cover','title','nav']+[f'c{i:02}' for i in range(1,11)]+['back']
spine=''.join(f'<itemref idref="{i}"/>' for i in order)
opf='<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="pt-BR"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">'+identifier+'</dc:identifier><dc:title>A Água do Despertar — O encontro</dc:title><dc:language>pt-BR</dc:language><meta property="dcterms:modified">2026-10-07T12:00:00Z</meta></metadata><manifest>'+manifest+'</manifest><spine>'+spine+'</spine></package>'
epub=ROOT/'A Agua do Despertar.epub'
with zipfile.ZipFile(epub,'w') as z:
    z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
    z.writestr('META-INF/container.xml','<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
    z.writestr('OEBPS/content.opf',opf)
    for name,data in files.items():z.writestr('OEBPS/'+name,data.encode('utf-8'),compress_type=zipfile.ZIP_DEFLATED)
    z.write(ROOT/'capa-frontal.jpg','OEBPS/cover.jpg',compress_type=zipfile.ZIP_DEFLATED)

def normalize(t):return re.sub(r'\s+','',t)
extracted='\n'.join(re.sub(r'^\d+\s*\n','',p.extract_text() or '') for p in PdfReader(pdf).pages)
for title,body in chapters:
    assert normalize(title) in normalize(extracted),title
    for p in body.split('\n\n'):
        assert normalize(p) in normalize(extracted),p[:100]
with zipfile.ZipFile(epub) as z:
    assert z.testzip() is None
    assert z.infolist()[0].filename=='mimetype' and z.infolist()[0].compress_type==0
    names=set(z.namelist())
    for n in names:
        if n.endswith(('.xhtml','.xml','.opf')):
            e=ET.fromstring(z.read(n))
            for item in e.iter():
                for attr in ('href','src'):
                    target=item.attrib.get(attr)
                    if target and not target.startswith(('http','#')):
                        assert str(Path(n).parent/target).replace('\\','/').split('#')[0] in names,(n,target)
    for i,(_,body) in enumerate(chapters,1):
        e=ET.fromstring(z.read(f'OEBPS/c{i:02}.xhtml'))
        actual=''.join(''.join(p.itertext()) for p in e.iter('{'+ns+'}p'))
        assert normalize(actual)==normalize(body)
validation={'date':'2026-10-07','chapters':len(chapters),'narrative_words':words,'reading_minutes_at_190_wpm':round(words/190,1),'pdf_pages':len(PdfReader(pdf).pages),'pdf_all_paragraphs_preserved':True,'epub_zip_xml_links_spine_text':True,'pdf_visual_review':'pending','epubcheck':'not executed','kindle_previewer':'not executed','print_kdp_preview':'not executed','public_backup':'pending: GitHub CLI authentication invalid; network connection failed'}
(ROOT/'validacao.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(validation,ensure_ascii=False,indent=2))
