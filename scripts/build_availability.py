# Builds availability.json (counts only, no names) from the tool's bikes + rentals exports.
import json, glob, os, sys, datetime as dt
src=sys.argv[1]; out=sys.argv[2]
bikes={os.path.basename(p)[:-5]:json.load(open(p)) for p in glob.glob(src+'/bikes/*.json')}
rentals=[json.load(open(p)) for p in glob.glob(src+'/rentals/*.json')]
def D(s): return dt.date.fromisoformat(s)
today=dt.date.today(); horizon=today+dt.timedelta(days=400)
BUF=16  # return transport after trips > 14 days
TYPES={'gravel','mtb','ebike'}
def key(b): return (b.get('type') or 'gravel')+'-'+(str(b.get('size') or '').strip().upper() or '?')
total={}
for bid,b in bikes.items():
    if b.get('status')=='retired' or (b.get('type') or 'gravel') not in TYPES: continue
    k=key(b); total[k]=total.get(k,0)+1
busy={}  # (bike, day) blocked
def block(bid,a,z):
    d=max(a,today)
    while d<=min(z,horizon): busy.setdefault(d,set()).add(bid); d+=dt.timedelta(days=1)
for r in rentals:
    if r.get('over') or not r.get('start') or not r.get('end'): continue
    bid=r['bikeId']; a,z=D(r['start']),D(r['end']); block(bid,a,z)
    if (z-a).days+1>14: block(bid,z+dt.timedelta(days=1),z+dt.timedelta(days=BUF))
for bid,b in bikes.items():  # bikes in workshop / at mechanic: unavailable for the next 3 days
    if b.get('status') in ('workshop','mechanic'): block(bid,today,today+dt.timedelta(days=3))
days={}
d=today
while d<=horizon:
    used={}
    for bid in busy.get(d,()):
        b=bikes.get(bid)
        if not b or b.get('status')=='retired' or (b.get('type') or 'gravel') not in TYPES: continue
        k=key(b); used[k]=used.get(k,0)+1
    free={k:total[k]-used.get(k,0) for k in total}
    if any(free[k]<total[k] for k in total): days[d.isoformat()]={k:v for k,v in free.items() if v<total[k]}
    d+=dt.timedelta(days=1)
# Keep one bike in reserve for the main sizes (website shows one less than actually free)
RESERVE={'gravel-S','gravel-M','gravel-L','gravel-XL','mtb-S','mtb-M'}
RESERVE={k for k in RESERVE if total.get(k,0)>=2}  # sizes with a single bike keep it bookable (e.g. MTB S for now)
shown_fleet={k:(max(0,v-1) if k in RESERVE else v) for k,v in total.items()}
shown_busy={}
for day,fr in days.items():
    adj={k:(max(0,v-1) if k in RESERVE else v) for k,v in fr.items()}
    adj={k:v for k,v in adj.items() if v<shown_fleet[k]}
    if adj: shown_busy[day]=adj
total,days=shown_fleet,shown_busy
json.dump({'updated':dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),'fleet':total,'busy':days},open(out,'w'),separators=(',',':'))
print(total); print(len(days),'days with bookings')
