import unittest,json,copy
from pathlib import Path
from lab import *
class Tests(unittest.TestCase):
 def test_tail(self):
  for p in (tail(2.5),tail(2.5,2)):
   self.assertTrue(all(0<=x<=1 for x in p));self.assertEqual(p,sorted(p,reverse=True))
 def test_pusula(self):
  self.assertIsNone(pusula([.5]*6,[],[]));self.assertEqual(len(pusula([.5]*6,[],[(1,1,1,2)]*30)),6)
 def test_atlas(self):
  e=[(1,2,1,3)]*30;self.assertIsNone(atlas(e,[],[]));self.assertEqual(len(atlas(e,e,e)),6)
 def test_radar(self):self.assertIsNone(radar())
 def test_matrix(self):
  self.assertIsNone(matrix([[.5]*6]));self.assertAlmostEqual(matrix([[.2]*6,[.8]*6])[0],.5)
 def test_tempo(self):self.assertIsNone(tempo(2,[]));self.assertEqual(len(tempo(2,[(1,2,1,3)]*30)),6)
 def test_time(self):
  with self.assertRaises(ValueError):dt('2026-01-01T00:00:00')
 def test_replay(self):
  def row(i,lock,start,verify):
   return {'kimlik':i,'mac':{'lig_kodu':'eng.1','ev_sahibi':'A','deplasman':'B','tarih':start,'hesaplama_zamani_utc':lock,'tahmin':{'beklenen_gol':2}},'kilit_zamani_utc':lock,'olasiliklar':{f'{k}.5_ust':50 for k in LINES},'durum':'DOGRULANDI','sonuc':{'durum':'TAMAMLANDI','ev_gol':1,'dep_gol':1,'toplam_gol':2},'sonuc_dogrulama_zamani_utc':verify}
  r=row('1','2026-01-01T00:00:00Z','2026-01-02T00:00:00Z','2026-01-03T00:00:00Z');s=copy.deepcopy(r);s['kimlik']='2';s['kilit_zamani_utc']='2026-01-01T01:00:00Z';before=copy.deepcopy([r,s]);a=replay([r,s]);self.assertEqual([x['prior_verified'] for x in a['rows']],[0,0]);self.assertEqual([r,s],before)
  with self.assertRaises(ValueError):replay([r,r])
if __name__=='__main__':unittest.main()
