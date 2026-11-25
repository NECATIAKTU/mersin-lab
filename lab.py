"""Independent historical research. No network, no writes to input, no live betting selections."""
import argparse, json, math, hashlib, statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LINES=range(1,7)
NAMES=['PUSULA X','ATLAS X','RADAR X','MATRIX X','TEMPO X','MERSİN']
def dt(s):
    d=datetime.fromisoformat(s.replace('Z','+00:00'))
    if d.tzinfo is None: raise ValueError('Timezone required')
    return d

def tail(mu,r=None):
    if not math.isfinite(mu) or mu<0: raise ValueError('Invalid mean')
    if mu==0:return [0.]*6
    p=math.exp(-mu) if r is None else (r/(r+mu))**r
    c=p; out=[]
    for k in LINES:
        p*=mu/k if r is None else (r+k-1)*mu/(k*(r+mu))
        c+=p;out.append(max(0,min(1,1-c)))
    return out

def pusula(p, league, global_history):
    if len(global_history)<30:return None
    base=[(sum(e[3]>k for e in global_history)+40*p[k-1])/(len(global_history)+40) for k in LINES]
    return [(sum(e[3]>k for e in league)+40*base[k-1])/(len(league)+40) for k in LINES]

def atlas(league, home, away):
    if len(league)<20 or len(home)<5 or len(away)<5:return None
    mh=statistics.mean(e[1] for e in league);ma=statistics.mean(e[2] for e in league)
    def shrink(xs, prior):return (sum(xs)+10*prior)/(len(xs)+10)
    # Home scoring + away conceding, and reverse; venue-specific, shrunk.
    h=(shrink([e[1] for e in home],mh)+shrink([e[1] for e in away],mh))/2
    a=(shrink([e[2] for e in home],ma)+shrink([e[2] for e in away],ma))/2
    return tail(h+a)

def radar():
    return None # No timestamped market data supplied; deliberately unavailable.

def matrix(parts):
    # Equal log-odds blend; not a learned or independent market model.
    if len(parts)<2:return None
    def logit(p):
        p=max(1e-6,min(1-1e-6,p));return math.log(p/(1-p))
    return [1/(1+math.exp(-statistics.mean(logit(x[i]) for x in parts))) for i in range(6)]

def tempo(mu,league):
    if len(league)<30:return None
    gs=[e[3] for e in league];m=statistics.mean(gs);v=statistics.variance(gs)
    return tail(mu,m*m/(v-m)) if v>m and m>0 else tail(mu)

def replay(rows):
    seen=set(); valid=[]; events=[]
    for r in rows:
        uid=r['kimlik'];m=r['mac'];lg=m['lig_kodu']
        if uid in seen:raise ValueError('Duplicate match ID')
        seen.add(uid)
        if lg.startswith('uefa.'):continue
        t=dt(r['kilit_zamani_utc']);start=dt(m['tarih'])
        if not dt(m['hesaplama_zamani_utc'])<=t<start:continue
        p=[float(r['olasiliklar'][f'{k}.5_ust'])/100 for k in LINES]
        if not all(math.isfinite(x) and 0<=x<=1 for x in p) or any(a<b for a,b in zip(p,p[1:])):raise ValueError('Invalid probabilities')
        valid.append((t,uid,m,p))
        s=r.get('sonuc') or {};v=r.get('sonuc_dogrulama_zamani_utc')
        if r.get('durum')=='DOGRULANDI' and s.get('durum')=='TAMAMLANDI' and v and dt(v)>=start:
            h,a=s['ev_gol'],s['dep_gol'];g=s['toplam_gol']
            if not all(type(x)==int and x>=0 for x in (h,a,g)) or h+a!=g:raise ValueError('Invalid score')
            events.append((dt(v),uid,m,h,a,g))
    events.sort(key=lambda e:e[0]);valid.sort(key=lambda e:e[0]); cursor=0
    hist=defaultdict(list);teams=defaultdict(list);glob=[];done={e[1]:e[5] for e in events}; stats=defaultdict(lambda:[0,0.,0.]); counts=defaultdict(int); output=[]
    for t,uid,m,p in valid:
        while cursor<len(events) and events[cursor][0]<t:
            v,i,em,h,a,g=events[cursor];cursor+=1;lg=em['lig_kodu'];e=(i,h,a,g);glob.append(e);hist[lg].append(e);teams[(lg,'h',em['ev_sahibi'])].append(e);teams[(lg,'a',em['deplasman'])].append(e)
        lg=m['lig_kodu']; league=hist[lg];mu=float(m['tahmin']['beklenen_gol'])
        parts={'PUSULA X':pusula(p,league,glob),'ATLAS X':atlas(league,teams[(lg,'h',m['ev_sahibi'])],teams[(lg,'a',m['deplasman'])]),'RADAR X':radar(),'TEMPO X':tempo(mu,league)}
        independent=[x for x in parts.values() if x is not None]
        parts['MATRIX X']=matrix([p]+independent)
        # Avoid double-counting MATRIX (already combines the inputs). Equal weights are provisional.
        parts['MERSİN']=[statistics.mean(x[i] for x in [p]+independent) for i in range(6)] if independent else None
        for name,q in parts.items():
            if q is None:continue
            counts[name]+=1
            if uid in done:
                for i,k in enumerate(LINES):
                    y=int(done[uid]>k);s=stats[(name,k)];s[0]+=1;s[1]+=(p[i]-y)**2;s[2]+=(q[i]-y)**2
        # Only retrospective completed matches are exposed in the research report.
        if uid in done:output.append({'id':uid,'league':lg,'home':m['ev_sahibi'],'away':m['deplasman'],'cutoff':t.isoformat(),'goals':done[uid],'prior_verified':len(glob),'v18':p,'models':parts})
    return {'mode':'retrospective research; not live predictions','input_count':len(rows),'eligible':len(valid),'completed':len(done),'models':{n:{'available_rows':counts[n],'metrics':{f'{k}.5':{'n':s[0],'baseline_brier':s[1]/s[0],'model_brier':s[2]/s[0]} for (name,k),s in stats.items() if name==n}} for n in NAMES},'rows':output}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('archive');parser.add_argument('output');a=parser.parse_args();src=Path(a.archive).resolve();out=Path(a.output).resolve();raw=src.read_bytes();report=replay(json.loads(raw));report['source_sha256']=hashlib.sha256(raw).hexdigest();out.mkdir(parents=True,exist_ok=False);(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
