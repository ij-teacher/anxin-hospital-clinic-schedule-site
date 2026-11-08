from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

class Node:
    def __init__(self,tag='',attrs=()): self.tag=tag; self.attrs=dict(attrs); self.children=[]
    def text(self): return ''.join(c if isinstance(c,str) else c.text() for c in self.children)
    def find(self,tag=None,cls=None,id=None):
        out=[]
        for c in self.children:
            if isinstance(c,Node):
                if (tag is None or c.tag==tag) and (cls is None or cls in c.attrs.get('class','').split()) and (id is None or c.attrs.get('id')==id): out.append(c)
                out.extend(c.find(tag,cls,id))
        return out
class Parser(HTMLParser):
    def __init__(self): super().__init__();self.root=Node();self.stack=[self.root]
    def handle_starttag(self,t,a):
        n=Node(t,a); self.stack[-1].children.append(n)
        if t not in ('br','meta','link','img','input'): self.stack.append(n)
        if t=='br':n.children.append(' ')
    def handle_endtag(self,t):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==t:self.stack=self.stack[:i];break
    def handle_data(self,d):self.stack[-1].children.append(d)

base=Path(__file__).parent
p=Parser();p.feed((base/'index.html').read_text(encoding='utf-8'));root=p.root
pdfmetrics.registerFont(TTFont('JhengHei','C:/Windows/Fonts/msjh.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('JhengHeiBold','C:/Windows/Fonts/msjhbd.ttc',subfontIndex=0))
pdfmetrics.registerFontFamily('JhengHei',normal='JhengHei',bold='JhengHeiBold')
ink=colors.HexColor('#143e43');green=colors.HexColor('#edf5f0')
styles={k:ParagraphStyle(k,fontName='JhengHeiBold' if k in ('title','h2','h3') else 'JhengHei',fontSize=s,leading=l,textColor=ink,spaceAfter=a,wordWrap='CJK') for k,s,l,a in [('title',24,34,18),('h2',19,27,14),('h3',15,23,10),('body',12,21,9),('small',10,16,6)]}
story=[]
def para(t,k='body'): return Paragraph(escape(t),styles[k])
def add(t,k='body'):story.append(para(t,k))
def table(node):
    rows=node.find('tr');data=[]
    for row in rows:data.append([para(c.text(),'small') for c in row.children if isinstance(c,Node) and c.tag in ('th','td')])
    widths=[115,380] if len(data[0])==2 else [125,105,265]
    tb=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1 if node.find('thead') else 0)
    cmds=[('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#90aaa3')),('INNERGRID',(0,0),(-1,-1),.35,colors.HexColor('#b5c9c2')),('BACKGROUND',(0,0),(0,-1),green),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)]
    if node.find('thead'):cmds.append(('BACKGROUND',(0,0),(-1,0),green))
    tb.setStyle(TableStyle(cmds));return tb
def emit(n):
    if n.tag=='table':story.extend([table(n),Spacer(1,12)]);return
    if n.tag in ('h2','h3'):add(n.text(),n.tag);return
    if n.tag=='p':add(n.text());return
    for c in n.children:
        if isinstance(c,Node):emit(c)
def page():story.append(PageBreak())
add('安心醫院掛號大挑戰','title');add('生活華語｜看醫生','h3')
add('先查看門診表，再完成病人任務卡、掛號對話與突發事件練習。')
emit(root.find(id='info')[0]);page()
clinics=root.find('article',cls='clinic')
for i,c in enumerate(clinics):
    if i%2==0:add('門診表','h2')
    emit(c)
    if i%2==1:page()
game=root.find(id='game')[0]
add('閱讀理解問題','h2')
for i,li in enumerate(game.find('ol')[0].find('li'),1):
    add(f'{i}. {li.text()}');story.append(Spacer(1,27));story.append(Table([['']],colWidths=[495],style=[('LINEBELOW',(0,0),(-1,-1),.5,ink)]));story.append(Spacer(1,16))
page()
cards=[n for n in game.find('div',cls='note') if n.text().startswith('病人任務卡')]
for i,c in enumerate(cards):
    if i%2==0:add('教學遊戲｜病人任務卡','h2')
    ps=c.find('p');block=[para(ps[0].text(),'h3'),para(ps[1].text())]
    for field in c.find('p',cls='mission-answer'):
        label=field.find('span',cls='answer-label')[0].text()
        w=pdfmetrics.stringWidth(label,'JhengHei',12)+12
        row=Table([[para(label),'']],colWidths=[w,495-w],style=[('VALIGN',(0,0),(-1,-1),'BOTTOM'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('LINEBELOW',(1,0),(1,0),.5,ink),('BOTTOMPADDING',(0,0),(-1,-1),5)])
        block.extend([Spacer(1,9),row])
    block.append(Spacer(1,27));story.append(KeepTogether(block))
    if i%2==1:page()
emit(game.find('section',cls='sentence-examples')[0])
for li in game.find('section',cls='sentence-examples')[0].find('li'):add('• '+li.text())
emit(game.find('div',cls='scenario-instruction')[0])
for n in game.find('div',cls='note'):
    if n.text().startswith('突發事件'):story.append(KeepTogether([para(n.find('p')[0].text(),'h3'),para(n.find('p')[1].text()),Spacer(1,10)]))
page();add('說一句完整的話','h2')
last=game.find('div',cls='note')[-1]
for pp in last.find('p'):
    st=ParagraphStyle('example',parent=styles['body'],fontName='JhengHeiBold',fontSize=14,leading=27,spaceAfter=26)
    story.append(Paragraph(escape(pp.text()),st))
def footer(c,d):
    c.setFont('JhengHei',9);c.setFillColor(ink);c.drawString(50,27,'安心醫院掛號大挑戰');c.drawRightString(A4[0]-50,27,str(d.page))
doc=SimpleDocTemplate(str(base/'clinic-schedule.pdf'),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=42,bottomMargin=46,title='安心醫院掛號大挑戰',author='ij-teacher')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Built',base/'clinic-schedule.pdf')
