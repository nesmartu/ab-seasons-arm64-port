"""Execute patched and original instructions with mocked game services.
These tests are not a substitute for Android installation/gameplay tests.
"""
import copy,json,sys,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'research')]
from build import transform,selected,signature_name,META
from codec import decode
from lua_chunk import parse
from lua_vm_check import run,truth
from fixes.unlock_all_levels import bound_predicates

class Behavior(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import os
  cls.apk=Path(os.environ.get('SEASONS_TEST_APK',str(ROOT/'input/AngryBirdsSeasons_v6.6.2.apk')))
  with zipfile.ZipFile(cls.apk) as z:cls.base={n:z.read(n) for n in z.namelist() if not signature_name(n)}
 def patched(self,**flags):return transform(self.base,flags,{'coins_amount':1000000})[0]
 def chunk(self,entries,name):return parse(decode(entries['assets/data/'+name]))
 def test_all_64_flag_combinations_and_idempotence(self):
  flags=['unlock_all_episodes','unlocked_all_with_coins','unlock_ragnahog_levels','quest_video','cosmetics','unlock_all_levels']
  for mask in range(64):
   f={k:bool(mask>>i&1) for i,k in enumerate(flags)}
   with self.subTest(flags=f):
    a,_,_=transform(self.base,f,{'coins_amount':1000000});b,_,new=transform(a,f,{'coins_amount':1000000})
    self.assertEqual(a,b);self.assertEqual(new,[])
    if not mask:self.assertEqual(a,self.base)
 def test_disabled_flags_do_not_undo_installed_patches(self):
  a=self.patched(unlock_all_episodes=True,unlock_ragnahog_levels=True,quest_video=True,cosmetics=True)
  b,_,_=transform(a,{}, {'coins_amount':1000000});self.assertEqual(a,b)
 def test_sequential_flags_equal_combined_content(self):
  a=self.base
  for k in ['quest_video','cosmetics','unlock_ragnahog_levels','unlocked_all_with_coins','unlock_all_levels']:
   a,_,_=transform(a,{k:True},{'coins_amount':1000000})
  self.assertEqual(a,self.patched(quest_video=True,cosmetics=True,unlock_ragnahog_levels=True,unlocked_all_with_coins=True,unlock_all_levels=True))
 def test_every_layout_gate_and_access_function(self):
  a=self.patched(unlock_all_levels=True);count=0
  for n in ['scripts/menus/seasons_layouts.lua','scripts/menus/level_selection_layouts.lua']:
   root=self.chunk(a,n)
   for path in bound_predicates(root,'isLevelOpen'):
    p=root['protos'][int(path.split('.')[-1])]
    self.assertIs(run(p,{},({'name':'test'},))[0],True);count+=1
  self.assertEqual(count,20)
  sw=self.chunk(a,'scripts/settingsWrapper.lua')
  for i in [52,84,273,275]:self.assertIs(run(sw['protos'][i],{},({},'level'))[0],True)
  self.assertIs(run(sw['protos'][344],{},({},'episode'))[0],False)
  self.assertEqual(run(sw['protos'][82],{},({},'episode')),(200.0,))
  self.assertEqual(run(self.chunk(a,'scripts/gamelogic.lua')['protos'][158],{},('level',)),(True,))
 def test_narrow_unlock_preserves_every_other_predicate(self):
  for f in [dict(unlock_all_episodes=True),dict(unlocked_all_with_coins=True),dict(unlock_all_episodes=True,unlock_ragnahog_levels=True,quest_video=True),dict(unlocked_all_with_coins=True,unlock_ragnahog_levels=True,quest_video=True,cosmetics=True)]:
   a=self.patched(**f)
   for n in ['scripts/gamelogic.lua','scripts/menus/seasons_layouts.lua','scripts/menus/level_selection_layouts.lua']:
    self.assertEqual(a['assets/data/'+n],self.base['assets/data/'+n])
   sw=self.chunk(a,'scripts/settingsWrapper.lua');old=self.chunk(self.base,'scripts/settingsWrapper.lua')
   for i in [52,54,82,84,275,344]:self.assertEqual(sw['protos'][i],old['protos'][i])
   self.assertIs(run(sw['protos'][273],{},({},'episodeTest'),({},))[0],True)
 def test_original_egg_and_star_gates_stay_locked_until_earned(self):
  a=self.patched(unlocked_all_with_coins=True,unlock_ragnahog_levels=True,quest_video=True,cosmetics=True)
  sw=self.chunk(a,'scripts/settingsWrapper.lua')
  self.assertEqual(run(sw['protos'][52],{'getLevelById':lambda _: {'name':'egg'},'settingsWrapper':{'getGoldenEgg':lambda *_:None}},({},'egg')),(False,))
  self.assertFalse(truth(run(sw['protos'][275],{},({},'bonus'),({},))[0]))
  layout=self.chunk(a,'scripts/menus/seasons_layouts.lua');ep=json.loads(decode(a['assets/data/config/episodes/episodesLatest.json']))['episodes']['episodeRagnahog']
  # Ragnahog has 25 calendar levels, a three-star egg and two hidden eggs.
  for earned in [False,True]:
   env={'getLocalEpisode':lambda _:ep,'settingsWrapper':{'isGoldenEggUnlocked':lambda *_:earned},'LSXmasLayout':{'isLevelOpen':lambda level:run(layout['protos'][21],{'settingsWrapper':{'getLastOpenLevel':lambda *_:29}},(level,))[0]}}
   for name in ['ragnahog_threestar','ragnahog_bombbasket','ragnahog_waterspout']:
    level={'episode':'episodeRagnahog','page':1,'name':name,'levelType':'golden_egg'}
    self.assertEqual(run(layout['protos'][43],env,(level,)),(earned,))
   for index,level in enumerate(ep['pages'][0]['levels'][:25],1):
    ordinary=dict(level,episode='episodeRagnahog',page=1,index_in_episode=index)
    self.assertEqual(run(layout['protos'][43],env,(ordinary,)),(True,))
  for stars in [0,44,45,75]:
   level={'episode':'episodeTest','page':1,'name':'star_bonus','stars_required':45}
   env={'calculateEpisodeStars':lambda *_:(stars,75),'settingsWrapper':{'isBonusLevelUnlocked':lambda *_:False}}
   self.assertEqual(run(layout['protos'][134],env,(level,)),(stars>=45,))
  for feathers in [0,9,10,25]:
   level={'episode':'episodeTest','page':1,'name':'feather_bonus','feathers_required':10}
   env={'calculateFeatherScore':lambda *_:(feathers,25),'settingsWrapper':{'isBonusLevelUnlocked':lambda *_:False}}
   self.assertEqual(run(layout['protos'][134],env,(level,)),(feathers>=10,))
 def test_ragnahog_only_changes_its_json_and_no_lua(self):
  a=self.patched(unlock_ragnahog_levels=True)
  self.assertEqual({n for n in self.base if a[n]!=self.base[n]},{'assets/data/config/episodes/episodesLatest.json'})
 def test_old_flag_names_keep_explicit_broad_behavior(self):
  from build import normalize_flags
  self.assertEqual(self.patched(unlocked_all=True),self.patched(unlock_all_levels=True))
  self.assertEqual(self.patched(ragnahog=True),self.patched(unlock_ragnahog_levels=True))
  with self.assertRaises(ValueError):normalize_flags({'unlocked_all':True,'unlock_all_episodes':False})
 def test_legacy_v5_metadata_migration_preserves_game_content(self):
  a=self.patched(unlock_all_levels=True,unlock_ragnahog_levels=True)
  meta=json.loads(a[META]);applied=meta['applied']
  applied['unlocked_all']=applied.pop('unlock_all_levels');applied.pop('unlock_all_episodes')
  applied['ragnahog']=applied.pop('unlock_ragnahog_levels');a[META]=json.dumps(meta).encode()
  b,_,new=transform(a,{'unlock_all_episodes':True,'unlock_ragnahog_levels':True},{'coins_amount':1000000})
  self.assertEqual(new,[])
  self.assertTrue(all(a[n]==b[n] for n in a if n!=META))
  self.assertEqual(set(json.loads(b[META])['applied']),{'unlock_all_levels','unlock_all_episodes','unlock_ragnahog_levels'})
 def test_can_add_alllevels_after_narrow_patches(self):
  a=self.patched(unlock_all_episodes=True,unlock_ragnahog_levels=True,quest_video=True)
  b,_,_=transform(a,{'unlock_all_levels':True},{'coins_amount':1000000})
  self.assertEqual(b,self.patched(unlock_all_episodes=True,unlock_ragnahog_levels=True,quest_video=True,unlock_all_levels=True))
 def test_coins_once_keep_larger_balance_and_normal_spending(self):
  p=self.chunk(self.patched(unlocked_all_with_coins=True),'scripts/settingsWrapper.lua')['protos'][277]
  for amount in [None,0,27,999999,1000000,1300000]:
   state={} if amount is None else {'IngameCurrencyAmount':amount}
   got=run(p,{},({},),(state,))[0];expected=max(amount or 0,1000000);self.assertEqual(got,expected)
   state['IngameCurrencyAmount']=expected-100
   self.assertEqual(run(p,{},({},),(state,)),(expected-100,))
  # The marker survives reload in a saved settings table.
  state=json.loads(json.dumps(state));self.assertEqual(run(p,{},({},),(state,)),(expected-100,))
 def test_cosmetics_all_108_and_unrelated_progress_preserved(self):
  sw=self.chunk(self.patched(cosmetics=True),'scripts/settingsWrapper.lua');quests=json.loads(decode(self.base['assets/data/config/quests/Quests.json']))
  journal=json.loads(decode(self.base['assets/data/config/quests/BirdJournalPages.json']))
  ids=[f['questId'] for page in journal['pages'] for bird in page for f in bird['frames'] if f.get('questId')]
  state={'completedQuests':{'unrelated':{'completed':False,'custom':13}},'highscores':{'test':123},'IngameCurrencyAmount':77}
  p=sw['protos'][258];env={};env['settingsWrapper']={'getCompletedQuests':lambda *args:run(p,env,({},),(state,))[0]}
  result=run(p,env,({},),(state,))[0]
  self.assertEqual(len(ids),108)
  for qid in ids:
   self.assertIs(result[qid]['completed'],True)
   self.assertEqual(list(result[qid]['collectedStamps'].values()),quests[qid].get('questTargets',[]))
   self.assertEqual(run(sw['protos'][255],env,({},qid),(state,)),(True,))
  self.assertEqual(result['unrelated'],{'completed':False,'custom':13});self.assertEqual(state['highscores'],{'test':123});self.assertEqual(state['IngameCurrencyAmount'],77)
  self.assertEqual(run(sw['protos'][255],env,({},'unrelated'),(state,)),(False,))
  before=copy.deepcopy(state);run(p,env,({},),(state,));self.assertEqual(state,before)
  self.assertFalse(run(sw['protos'][285],{},({},),(state,))[0])
 def test_quest_click_both_interfaces_without_video_or_cheats(self):
  a=self.patched(quest_video=True)
  for file,index in [('scripts/menus/combinedMenu/QuestLogFrame.lua',8),('scripts/quests/QuestLog.lua',14)]:
   for ready in [False,True]:
    calls=[];state={'scaleIn':False};meta={'target':'an_object','questId':'my_quest'}
    sw={'setQuestVideoWatched':lambda _,qid:calls.append(qid)}
    env={'ui':{'Frame':{'onPointerEvent':lambda *args:('WATCH_VIDEO_AND_GIVE_HINT',meta,False)}},'settingsWrapper':sw,'gamelua':{'settingsWrapper':sw,'questVideoReady':ready,'cheatsEnabled':False},'questVideoReady':ready,'cheatsEnabled':False}
    run(self.chunk(a,file)['protos'][index],env,(state,'RELEASE',0,0),(None,) if index==14 else ())
    self.assertEqual(state['levelTarget'],'an_object');self.assertEqual(state['levelTargetQuestId'],'my_quest');self.assertEqual(calls,['my_quest'])
    self.assertNotIn('questVideoTarget',state) # update cannot enter its RovioAds.show branch.
 def test_click_then_original_update_shows_level_prompt(self):
  a=self.patched(quest_video=True);p=self.chunk(a,'scripts/menus/combinedMenu/QuestLogFrame.lua');messages=[];marked=[]
  state={'getChild':lambda *_:None,'questItems':{1:{'setup':lambda *_:None}}};meta={'target':'object','questId':'quest'}
  sw={'setQuestVideoWatched':lambda _,qid:marked.append(qid),'isEpisodeUnlocked':lambda *_:True,'getActiveQuestById':lambda *_:{'index':1}}
  env={'ui':{'Frame':{'onPointerEvent':lambda *args:('WATCH_VIDEO_AND_GIVE_HINT',meta,False),'update':lambda *_:None},'ConfirmPrompt':{'new':lambda _,data:data}},'settingsWrapper':sw,'questVideoReady':False,'cheatsEnabled':False,'_G':{'type':lambda x:'string' if isinstance(x,str) else 'table'},'findRandomLevelWithQuestObject':lambda *_:({'episode':'episodeEggsFiles','name':'Eggsfiles_Ghosts','page':1,'index':2},True),'getLocalEpisode':lambda *_:{'name':'Test Episode'},'getLevelDisplayNumber':lambda *_:'1-2','notificationsFrame':{'addChild':lambda _,data:messages.append(data)}}
  run(p['protos'][8],env,(state,'RELEASE',0,0));run(p['protos'][2],env,(state,0.016,0))
  self.assertEqual(marked,['quest']);self.assertEqual(len(messages),1);self.assertIn('level 1-2',messages[0]['content']);self.assertTrue(callable(messages[0]['confirm_call']));self.assertNotIn('levelTarget',state)
 def test_original_calendar_and_startup_paths(self):
  import tempfile
  from lua_vm_check import test as calendar_test,startup_test
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for n in ['scripts/gamelogic.lua','config/episodes/episodesLatest.json']:
    f=root/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(decode(self.base['assets/data/'+n]))
   cases=calendar_test(root)+startup_test(root);self.assertEqual(len(cases),21)
 def test_original_quest_needs_readiness(self):
  p=self.chunk(self.base,'scripts/menus/combinedMenu/QuestLogFrame.lua')['protos'][8];state={};calls=[];meta={'target':'object','questId':'quest'}
  env={'ui':{'Frame':{'onPointerEvent':lambda *a:('WATCH_VIDEO_AND_GIVE_HINT',meta,False)}},'questVideoReady':True,'_G':{'res':{'stopAllAudio':lambda:calls.append('stop_audio')}}}
  run(p,env,(state,'RELEASE',0,0));self.assertNotIn('levelTarget',state);self.assertEqual(state['questVideoTarget'],'object');self.assertEqual(calls,['stop_audio'])
 def test_ragnahog_exact_semantic_change(self):
  a=self.patched(unlock_ragnahog_levels=True);n='assets/data/config/episodes/episodesLatest.json';old=json.loads(decode(self.base[n]));new=json.loads(decode(a[n]));expected=copy.deepcopy(old)
  e=expected['episodes']['episodeRagnahog'];e['manual_level_progression']=False;e['pages'][0]['all_levels_open']=True;self.assertEqual(new,expected)
 def test_no_unrequested_game_content_changes(self):
  a=self.patched(quest_video=True)
  self.assertEqual({n for n in self.base if a[n]!=self.base[n]},{'assets/data/scripts/menus/combinedMenu/QuestLogFrame.lua','assets/data/scripts/quests/QuestLog.lua'})
  self.assertEqual({n for n in a if n not in self.base},{META})

if __name__=='__main__':unittest.main(verbosity=2)
