"""Open the 2016 calendar through normal startup progression; safe to reapply."""
import json,copy
from codec import encode
NAME='unlock_ragnahog_levels'
TARGET='config/episodes/episodesLatest.json'
def apply(ctx,options):
 raw=ctx.raw(TARGET);obj=json.loads(raw);ep=obj['episodes']['episodeRagnahog'];page=ep['pages'][0]
 if page.get('calendar')!={'month':12,'year':2016} or page.get('layout')!='xmas2016' or len(page['levels'])!=28:
  raise ValueError('Unsupported Ragnahog calendar structure')
 expected=copy.deepcopy(obj);expected['episodes']['episodeRagnahog']['pages'][0]['all_levels_open']=True;expected['episodes']['episodeRagnahog']['manual_level_progression']=False
 text=raw.decode();dec=json.JSONDecoder();start=text.index('{',text.index('"episodeRagnahog":'));segment,end=dec.raw_decode(text[start:]);segment=expected['episodes']['episodeRagnahog']
 changed=(text[:start]+json.dumps(segment,separators=(',',':'),ensure_ascii=False)+text[start+end:]).encode()
 if json.loads(changed)!=expected:raise ValueError('Unexpected calendar edits')
 if obj!=expected:ctx.entries['assets/data/'+TARGET]=encode(changed)
