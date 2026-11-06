"""Verify the current static site, including the conditional-environment instrument."""

from pathlib import Path as _ProjectPath
import sys as _project_sys
_project_sys.path.insert(0, str(_ProjectPath(__file__).resolve().parents[1]))
from _bootstrap import ROOT as PROJECT_ROOT, script_path, resolve_recorded_path
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import re,json,hashlib
ROOT=PROJECT_ROOT;WEB=ROOT/'web'
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.duplicates=[];self.links=[];self.runtime=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:
   if a['id'] in self.ids:self.duplicates.append(a['id'])
   self.ids.add(a['id'])
  for k in ['href','src']:
   if k in a:self.links.append(a[k])
  if tag in ['script','img'] and 'src' in a:self.runtime.append(a['src'])
  if tag=='link' and a.get('rel')=='stylesheet':self.runtime.append(a.get('href',''))
def main():
 pages={p:Page() for p in WEB.rglob('*.html')}
 for p,parser in pages.items():parser.feed(p.read_text())
 errors=[];links=0
 for p,parser in pages.items():
  for duplicate in parser.duplicates:errors.append(f'{p.relative_to(WEB)}: duplicate id {duplicate}')
  for url in parser.links:
   u=urlsplit(url)
   if u.scheme or u.netloc:continue
   path=(p.parent/unquote(u.path)).resolve() if u.path else p.resolve();links+=1
   if not path.exists():errors.append(f'{p.name}: missing {url}')
   elif u.fragment and path in pages and u.fragment not in pages[path].ids:errors.append(f'{p.name}: missing anchor {url}')
  for url in parser.runtime:
   if urlsplit(url).scheme:errors.append(f'{p.name}: external runtime resource {url}')
 for css in WEB.rglob('*.css'):
  for url in re.findall(r'url\([\"\']?([^\)\"\']+)',css.read_text()):
   if url.startswith(('data:','#','http')):continue
   if not (css.parent/url).exists():errors.append(f'{css}: missing {url}')
 for p in WEB.glob('*.html'):
  if any(x in p.read_text() for x in ['__DATA__','__SCRIPT__','__STYLE__','Lorem ipsum']):errors.append(f'{p.name}: unresolved placeholder')
 for p in (ROOT/'notebooks').glob('*.ipynb'):
  n=json.loads(p.read_text());assert n['nbformat']==4
  if not (WEB/'downloads'/p.name).exists():errors.append('Notebook download missing: '+p.name)
 required={'index.html','lab.html','findings.html','methods.html','reproduce.html','trading.html','advanced/index.html'}
 found={str(p.relative_to(WEB)) for p in pages}
 assert required <= found and found-required <= {'learn.html','risk-environment.html','strategy-ecology.html'}, ('Unexpected page set',found)
 report={'status':'pass' if not errors else 'fail','pages':len(pages),'local_links':links,'errors':errors}
 print(json.dumps(report,indent=2))
 if errors:raise SystemExit(1)
if __name__=='__main__':main()
