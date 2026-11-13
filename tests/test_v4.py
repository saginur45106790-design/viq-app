"""v4 business rules: amounts are integer paisa; no external payment is simulated as real."""
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select,func
from test_viq import env, fund, key, Client, PASSWORD
from models import *
from v4 import CURRENCIES

def seed(env):
    app,a,u,v=env
    with Session(app.extensions['engine']) as db,db.begin():
        db.add_all([Currency(code=c,name=n,flag=f,symbol=s,rate=10000,enabled=True) for c,n,f,s in CURRENCIES])
        db.add(MediaAsset(id=1,owner_id=3,mime='image/png',data=b'\x89PNG\r\n\x1a\n'))
    return app,a,u,v

def listing(v,slug='pages'):
    r=v.post('/market/'+slug,dict(title='Owned property',description='Ownership and audience details',url='https://www.facebook.com/example',image_id=1,price='100'))
    assert r.status_code==200,r.json
    return r.json['id']

def deal(u,lid):
    d=dict(key=key(),price=10000);r=u.post(f'/market/listings/{lid}/deal',d)
    assert r.status_code==200,r.json
    assert u.post(f'/market/listings/{lid}/deal',d).json==r.json
    return r.json['id']

def test_admin_aliases(env):
    app,*_=env
    for path in ['/admin','/admin/','/admin/login','/admin.html']:
        assert app.test_client().get(path).status_code==200

def test_recharge_limits(env):
    _,a,u,_=env;fund(a,u)
    for amount in ['19','501']:
        assert u.post('/tickets',dict(key=key(),kind='recharge',amount=amount,phone='01712345678',operator='GP',details='recharge')).status_code==400
    for amount in ['20','500']:
        assert u.post('/tickets',dict(key=key(),kind='recharge',amount=amount,phone='01712345678',operator='GP',details='recharge')).status_code==200

def test_coins_roundtrip_and_replay(env):
    _,a,u,_=env;fund(a,u)
    d=dict(key=key(),side='buy',coins=10000)
    assert u.post('/coins/convert',d).status_code==200
    assert u.post('/coins/convert',d).status_code==200
    assert u.get('/community/profile').json['coins']==10000
    assert u.get('/wallet').json['balance']==99000
    assert u.post('/coins/convert',dict(key=key(),side='sell',coins=10010)).status_code==409
    assert u.post('/coins/convert',dict(key=key(),side='sell',coins=10000)).status_code==200
    assert u.get('/wallet').json['balance']==100000
    assert u.get('/community/profile').json['coins']==0
    assert u.post('/coins/convert',dict(key=key(),side='buy',coins=11)).status_code==400

def test_fx_buy_hold_rate_change_sell(env):
    _,a,u,v=seed(env);fund(a,u)
    d=dict(key=key(),code='USD',quantity='1',side='buy',rate=10000)
    r=u.post('/fx/trade',d);assert r.status_code==200,r.json
    assert u.post('/fx/trade',d).json==r.json
    assert u.get('/wallet').json['balance']==90000
    assert a.post('/admin/fx/USD',dict(rate='120',enabled=True)).status_code==200
    assert u.post('/fx/trade',dict(d,key=key())).status_code==409
    assert u.post('/fx/trade',dict(key=key(),code='USD',quantity='1',side='sell',rate=12000)).status_code==200
    assert u.get('/wallet').json['balance']==102000
    assert u.post('/fx/trade',dict(key=key(),code='USD',quantity='1',side='sell',rate=12000)).status_code==409
    assert v.post('/admin/fx/USD',dict(rate='1',enabled=True)).status_code==403

def test_market_escrow_release_once(env):
    app,a,u,v=seed(env);fund(a,u);lid=listing(v);did=deal(u,lid)
    w=u.get('/wallet').json;assert (w['balance'],w['held'])==(90000,10000)
    assert u.post(f'/deals/{did}/action',dict(action='release',note='bad')).status_code==403
    assert a.post(f'/deals/{did}/action',dict(action='release',note='too early')).status_code==409
    assert v.post(f'/deals/{did}/action',dict(action='delivered',note='Transferred ownership')).status_code==200
    assert u.post(f'/deals/{did}/action',dict(action='confirm',note='Received')).status_code==200
    assert a.post(f'/deals/{did}/action',dict(action='release',note='Verified')).status_code==200
    assert a.post(f'/deals/{did}/action',dict(action='release',note='Again')).status_code==409
    assert v.get('/wallet').json['balance']==10000
    assert u.get('/wallet').json['held']==0
    assert not u.get('/market/pages').json['items']
    assert a.get('/admin/market-profiles').json['items'][0]['held']==0

def test_cancel_relist_new_deal_old_refund(env):
    _,a,u,v=seed(env);fund(a,u);lid=listing(v,'groups');did=deal(u,lid)
    assert v.post(f'/deals/{did}/action',dict(action='cancel',note='Cancel')).status_code==200
    assert u.get('/wallet').json['held']==10000
    did2=deal(u,lid)
    assert a.post(f'/deals/{did}/action',dict(action='refund',note='Refund old deal')).status_code==200
    assert u.get('/wallet').json['held']==10000
    assert not u.get('/market/groups').json['items']
    assert a.post(f'/deals/{did2}/action',dict(action='refund',note='Refund')).status_code==200
    assert len(u.get('/market/groups').json['items'])==1
    assert u.get('/wallet').json['balance']==100000

def test_deal_chat_private(env):
    app,a,u,v=seed(env);fund(a,u);did=deal(u,listing(v,'gmail'))
    with Session(app.extensions['engine']) as db,db.begin():
        from werkzeug.security import generate_password_hash
        db.add(User(id=4,name='Other',email='other@test.com',password=generate_password_hash(PASSWORD)))
    other=Client(app,'other@test.com')
    assert other.get('/deals/'+str(did)).status_code==404
    assert other.post('/deals/'+str(did)+'/message',dict(body='hi')).status_code==404
    assert u.post('/deals/'+str(did)+'/message',dict(body='<script>test</script>')).status_code==200
    assert a.get('/deals/'+str(did)).json['messages'][0]['body']=='<script>test</script>'

def test_live_seats_gift_conservation(env):
    app,a,u,v=seed(env);fund(a,u)
    rid=u.post('/live/start',dict(title='Audio community')).json['room_id']
    assert u.post(f'/rooms/{rid}/join').status_code==200
    assert v.post(f'/rooms/{rid}/join').status_code==200
    assert v.post(f'/community/rooms/{rid}/seat',dict(number=1)).status_code==409
    assert v.post(f'/community/rooms/{rid}/seat',dict(number=11)).status_code==400
    assert v.post(f'/community/rooms/{rid}/seat',dict(number=10)).status_code==200
    assert len(u.get(f'/community/rooms/{rid}').json['seats'])==2
    u.post('/coins/convert',dict(key=key(),side='buy',coins=10000))
    d=dict(key=key(),recipient=3,gift='rocket')
    assert u.post(f'/community/rooms/{rid}/gift',d).status_code==200
    assert u.post(f'/community/rooms/{rid}/gift',d).status_code==200
    assert v.get('/community/profile').json['coins']==10000
    assert u.get('/community/profile').json['coins']==0
    assert u.post(f'/community/rooms/{rid}/gift',dict(d,key=key())).status_code==409
    assert v.post(f'/community/rooms/{rid}/message',dict(body='Hello')).status_code==200
    assert len(u.get(f'/community/rooms/{rid}').json['messages'])==2

def test_watch_thirtieth_full_minute_reward(env,monkeypatch):
    app,a,u,v=env;clock=[2000000000];monkeypatch.setattr('v4.now',lambda:clock[0])
    with Session(app.extensions['engine']) as db,db.begin():
        db.add(MediaAsset(id=1,owner_id=1,mime='video/mp4',data=b'video'))
        for n in range(1,31):db.add(Clip(id=n,title='Clip',asset_id=1))
        db.flush()
        for n in range(1,30):db.add(WatchedClip(user_id=2,clip_id=n))
    token=u.post('/clips/30/start').json['token']
    for t in range(3,61,3):
        clock[0]+=3;r=u.post('/clips/30/tick',dict(token=token,position=t,playing=True,visible=True));assert r.status_code==200,r.json
    assert r.json['complete'] is True
    assert u.get('/wallet').json['balance']==1500
    assert u.post('/clips/30/start').status_code==409
    assert u.post('/clips/30/tick',dict(token=token,position=60,playing=True,visible=True)).status_code==409
    assert v.get('/wallet').json['balance']==0

def test_watch_seek_hidden_and_abandon_never_pay(env,monkeypatch):
    app,a,u,v=env;clock=[2000000000];monkeypatch.setattr('v4.now',lambda:clock[0])
    with Session(app.extensions['engine']) as db,db.begin():
        db.add(MediaAsset(id=1,owner_id=1,mime='video/mp4',data=b'video'));db.add(Clip(id=1,title='Clip',asset_id=1))
    for visible,pos in [(True,60),(False,3)]:
        token=u.post('/clips/1/start').json['token'];clock[0]+=3
        assert u.post('/clips/1/tick',dict(token=token,position=pos,playing=True,visible=visible)).json['reset']
    token=u.post('/clips/1/start').json['token'];assert u.post('/clips/abandon',dict(token=token)).status_code==200
    assert u.post('/clips/1/tick',dict(token=token,position=60,playing=True,visible=True)).status_code==409
    assert u.get('/wallet').json['balance']==0

def test_admin_video_duration_validation(env,tmp_path):
    import subprocess,io,imageio_ffmpeg
    _,a,u,_=env
    exe=imageio_ffmpeg.get_ffmpeg_exe()
    for seconds in (1,60):
        path=tmp_path/f'{seconds}.mp4'
        subprocess.run([exe,'-v','error','-f','lavfi','-i','color=c=blue:s=160x288:r=1','-t',str(seconds),'-c:v','libx264','-pix_fmt','yuv420p',str(path)],check=True,timeout=30)
        r=a.raw.post('/api/media',data={'file':(io.BytesIO(path.read_bytes()),'clip.mp4')},headers={'X-CSRF-Token':a.csrf})
        assert r.status_code==200,r.json
        d=dict(asset_id=r.json['id'],title='One minute',caption='Admin video')
        assert u.post('/admin/clips',d).status_code==403
        r=a.post('/admin/clips',d)
        assert r.status_code==(200 if seconds==60 else 400),r.json
