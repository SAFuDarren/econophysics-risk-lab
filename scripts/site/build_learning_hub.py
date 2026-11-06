"""Build the local learning payload and maintain its existing-site entry points."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[2];WEB=ROOT/'web'

def b(en,zh):return f'<span data-en>{en}</span><span data-zh hidden>{zh}</span>'

def main():
    data=json.loads((ROOT/'docs/learning/lessons.json').read_text())
    data['calibration_demo']=json.loads((ROOT/'docs/learning/calibration-demo.json').read_text())
    ids=[x['id'] for x in data['lessons']];assert len(ids)==len(set(ids))
    (WEB/'assets/data/learning-content.js').write_text('window.LearningContent='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    learning=WEB/'learn.html'
    if learning.exists():
        s=learning.read_text();anchors='<div hidden aria-hidden="true" id="learning-topic-anchors">'+''.join('<span id="'+x+'"></span>' for x in ids)+'</div>'
        s=re.sub(r'<div hidden aria-hidden="true"(?: id="learning-topic-anchors")?>.*?</div>(?=</main>)',lambda m:anchors,s,flags=re.S)
        s=re.sub(r'(<progress id="learning-progress" value="0" max=")\d+(\")',lambda m:m.group(1)+str(len(ids))+m.group(2),s)
        learning.write_text(s)
    for page in WEB.rglob('*.html'):
        s=page.read_text();m=re.search(r'<nav\b[^>]*id="main-nav"[^>]*>.*?</nav>',s,re.S)
        if not m:
            if page.parent.name=='advanced':
                s=re.sub(r'<a href="\.\./learn.html[^"]*"[^>]*>.*?</a>','',s,flags=re.S)
                marker='<span>策略重叠与配置</span>'
                if marker in s:s=s.replace(marker,'<a href="../learn.html#diversification">学习区：分散化与共同风险</a>'+marker,1)
                page.write_text(s)
            continue
        prefix='../' if page.parent.name=='advanced' else ''
        link=f'<a href="{prefix}learn.html"'+(' aria-current="page"' if page.name=='learn.html' else '')+'>'+b('Learn','学习')+'</a>'
        nav=m.group();nav=re.sub(r'<a\b[^>]*href="(?:\.\./)?learn.html"[^>]*>.*?</a>','',nav,flags=re.S)
        first=nav.find('</a>');assert first>=0;nav=nav[:first+4]+link+nav[first+4:]
        s=s[:m.start()]+nav+s[m.end():]
        if page.name=='index.html':
            section='<section class="section wrap learning-home-entry" id="learning-entry"><div><h2>'+b('Learn the ideas behind the experiments','学习实验背后的知识')+'</h2><p>'+b('A guided learning room connects market economics, the mathematical foundations and the inference-to-risk pipeline. Each topic combines intuition, an equation, a model you can manipulate and a short reasoning check.','学习区将市场经济学、数学基础和推断到风险的链条连起来。每个主题结合直觉、公式、可操作模型与简短自测。')+'</p><a class="text-link" href="learn.html">'+b('Enter the learning room','进入学习区')+'</a></div><div class="learning-topic-example"><p>'+b('Why can the same order move a thin market more?','为什么同一笔订单对薄盘口影响更大？')+'</p><p>'+b('When does shared information become shared risk?','共同信息怎样变成共同风险？')+'</p><p>'+b('What can aggregate data actually identify?','宏观数据究竟能识别什么？')+'</p></div></section>'
            s=re.sub(r'<section\b[^>]*id="learning-entry"[^>]*>.*?</section>','',s,flags=re.S)
            marker='<section class="research-intro">';assert marker in s;s=s.replace(marker,section+marker,1)
            if 'assets/learning.css' not in s:s=s.replace('</head>','<link rel="stylesheet" href="assets/learning.css?v=1"></head>')
        # Active command examples follow the reorganisation; historical records stay intact.
        mapping=json.loads((ROOT/'docs/repository-migration-map.json').read_text())['mapping']
        for old,new in mapping.items():s=s.replace(old,new)
        page.write_text(s)
    print(json.dumps({'learning_topics':len(ids),'payload':'web/assets/data/learning-content.js','navigation_pages':len(list(WEB.rglob('*.html')))},indent=2))

if __name__=='__main__':main()
