import io
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_viq import env, task, fund, submit, key, PASSWORD
from models import *
from v3 import referral_code, referral_id

def upload(u,sid,blob,mime,name):
    return u.raw.post(f'/api/submissions/{sid}/attachment',data={'file':(io.BytesIO(blob),name,mime)},headers={'X-CSRF-Token':u.csrf})

def test_short_codes_roundtrip():
    for uid in (1,2,26,9999,456975,456976):assert referral_id(referral_code(uid))==uid
    assert len(referral_code(3))==4

@pytest.mark.parametrize('platform,url',[('facebook_page','https://facebook.com/page'),('facebook_group','https://facebook.com/groups/1'),('facebook_post','https://facebook.com/posts/1'),('tiktok_video','https://www.tiktok.com/@name/video/1'),('tiktok_profile','https://tiktok.com/@name'),('youtube_video','https://youtu.be/video'),('youtube_channel','https://youtube.com/@name')])
def test_social_requires_screenshot_and_review_once(env,platform,url):
    _,a,u,_=env;t=task(a,category='social',platform=platform,url=url)
    sid=u.post(f'/tasks/{t}/start').json['submission']['id']
    assert u.post(f'/tasks/{t}/submit',{'proof':'done'}).status_code==400
    assert upload(u,sid,b'\x89PNG\r\n\x1a\nTEST','image/png','proof.png').status_code==200
    assert u.post(f'/tasks/{t}/submit').status_code==200
    assert a.post(f'/admin/submissions/{sid}',{'action':'approve'}).status_code==200
    assert a.post(f'/admin/submissions/{sid}',{'action':'approve'}).status_code==409
    assert u.get('/wallet').json['balance']==2000

def test_social_rejects_wrong_domain(env):
    _,a,_,_=env
    assert a.post('/admin/tasks',dict(category='social',title='Follow',description='Follow page',url='https://facebook.com.evil.example',platform='facebook_page',reward='10',slots='1')).status_code==400

def test_exclusive_video_queue_and_reject_consumes(env):
    _,a,u,v=env;t=task(a,category='create-video',sample_url='https://example.com/sample.mp4');n=task(a,category='create-video',sample_url='https://example.com/sample2.mp4')
    assert [x['id'] for x in u.get('/tasks?category=create-video').json['tasks']]==[t]
    sid=u.post(f'/tasks/{t}/start').json['submission']['id']
    assert v.post(f'/tasks/{t}/start').status_code==409
    assert [x['id'] for x in v.get('/tasks?category=create-video').json['tasks']]==[n]
    assert u.post(f'/tasks/{t}/submit',{'proof':'just text'}).status_code==400
    assert u.post(f'/tasks/{t}/submit',{'proof':'https://example.com/output.mp4'}).status_code==200
    assert a.post(f'/admin/submissions/{sid}',{'action':'reject'}).status_code==200
    assert v.post(f'/tasks/{t}/start').status_code==409

def test_expired_video_claim_can_be_taken(env):
    app,a,u,v=env;t=task(a,category='create-video',sample_url='https://example.com/a.mp4');u.post(f'/tasks/{t}/start')
    with Session(app.extensions['engine']) as db,db.begin():db.get(TaskReservation,t).expires=now()-1
    assert v.post(f'/tasks/{t}/start').status_code==200
    assert u.post(f'/tasks/{t}/submit',{'proof':'https://example.com/my.mp4'}).status_code==409

def test_video_sample_upload_and_admin_only(env):
    _,a,u,_=env;t=task(a,category='create-video')
    assert u.post(f'/tasks/{t}/start').status_code==409
    blob=b'\x00\x00\x00\x18ftypisomTEST'
    r=a.raw.post(f'/api/admin/tasks/{t}/sample',data={'file':(io.BytesIO(blob),'sample.mp4','video/mp4')},headers={'X-CSRF-Token':a.csrf});assert r.status_code==200
    assert u.get(f'/tasks/{t}/sample').data==blob
    assert u.post(f'/tasks/{t}/start').status_code==200
    assert u.post(f'/admin/tasks/{t}/sample').status_code==403

def test_question_five_per_day_admin_limit(env):
    _,a,u,_=env
    for _ in range(5):submit(u,task(a,category='survey'))
    t=task(a,category='survey');u.post(f'/tasks/{t}/start')
    assert u.post(f'/tasks/{t}/submit',{'proof':'answer'}).status_code==409
    assert u.get('/modules/progress').json['survey_used']==5
    assert a.post('/admin/settings',{'survey_daily_limit':'6'}).status_code==200
    assert u.post(f'/tasks/{t}/submit',{'proof':'answer'}).status_code==200

@pytest.mark.parametrize('category,proof_type',[('voice','audio'),('daily','audio'),('daily','image')])
def test_typed_proof_required(env,category,proof_type):
    _,a,u,_=env;t=task(a,category=category,proof_type=proof_type);sid=u.post(f'/tasks/{t}/start').json['submission']['id']
    assert u.post(f'/tasks/{t}/submit',{'proof':'text alone'}).status_code==400
    blob=b'OggSTEST' if proof_type=='audio' else b'\x89PNG\r\n\x1a\nTEST'
    mime='audio/ogg' if proof_type=='audio' else 'image/png'
    assert upload(u,sid,blob,mime,'proof').status_code==200
    assert u.post(f'/tasks/{t}/submit').status_code==200

def test_referral_signup_bonuses_once(env):
    app,a,u,v=env
    c=app.test_client();d={'name':'New','email':'new@test.com','password':PASSWORD,'accept':True,'referrer':v.get('/team').json['code']}
    r=c.post('/api/register',json=d);assert r.status_code==200
    assert c.get('/api/wallet').json['balance']==1000
    assert v.get('/wallet').json['balance']==500
    assert c.post('/api/register',json=d,headers={'X-CSRF-Token':r.json['csrf']}).status_code==409
    assert v.get('/wallet').json['balance']==500

def test_agency_fee_refund_and_commission_once(env):
    app,a,u,v=env;fund(a,v,'1200')
    d={'kind':'agency','key':key(),'details':'My agency'}
    tid=v.post('/tickets',d).json['ticket']['id'];assert v.get('/wallet').json['held']==100000
    assert v.post('/tickets',{'kind':'agency','key':key(),'details':'again'}).status_code==409
    assert a.post(f'/admin/tickets/{tid}',{'action':'reject'}).status_code==200
    assert v.get('/wallet').json['balance']==120000
    d['key']=key();tid=v.post('/tickets',d).json['ticket']['id']
    assert a.post(f'/admin/tickets/{tid}',{'action':'approve'}).status_code==200
    assert v.get('/team').json['agency_approved'] is True
    c=app.test_client();r=c.post('/api/register',json={'name':'Agency recruit','email':'agency@test.com','password':PASSWORD,'accept':True,'referrer':v.get('/team').json['code']});assert r.status_code==200
    assert c.get('/api/wallet').json['balance']==3000
    assert v.get('/wallet').json['balance']==25000
    fund(a,u,'200');tid=u.post('/tickets',{'kind':'withdraw','key':key(),'amount':'100','details':'bkash destination'}).json['ticket']['id']
    assert a.post('/admin/settings',{'agency_commission_percent':'9'}).status_code==200
    assert a.post(f'/admin/tickets/{tid}',{'action':'approve','note':'paid'}).status_code==200
    assert v.get('/wallet').json['balance']==25500 # 5% snapshot, not new 9%
    assert u.get('/wallet').json['balance']==10000
    assert a.post(f'/admin/tickets/{tid}',{'action':'approve','note':'paid'}).status_code==409

def test_agency_cancel_refunds(env):
    _,a,u,_=env;fund(a,u)
    tid=u.post('/tickets',{'kind':'agency','key':key(),'details':'Agency'}).json['ticket']['id']
    assert u.post(f'/tickets/{tid}/cancel').status_code==200
    assert u.get('/wallet').json['balance']==100000

def test_live_witness_rate_and_duplicate_review(env,monkeypatch):
    app,a,u,v=env;clock=[now()];monkeypatch.setattr('v3.now',lambda:clock[0])
    rid=u.post('/live/start',{'title':'Audio lounge'}).json['room_id']
    assert u.post(f'/rooms/{rid}/join').json['room']['audio_only'] is True
    clock[0]+=10
    assert u.post(f'/live/{rid}/tick',{'mic':True}).json['seconds']==0
    v.post(f'/rooms/{rid}/join')
    # Keep server peer heartbeats fresh while advancing deterministic test clock.
    def tick():
        with Session(app.extensions['engine']) as db,db.begin():
            for p in db.scalars(select(Peer).where(Peer.room_id==rid)):p.seen=clock[0]
        return u.post(f'/live/{rid}/tick',{'mic':True})
    tick()
    for _ in range(6):clock[0]+=10;tick()
    assert u.get('/live/history').json['items'][0]['seconds']==60
    assert v.post(f'/live/{rid}/tick',{'mic':True}).status_code==409
    assert u.post(f'/live/{rid}/end').status_code==200
    sid=u.get('/live/history').json['items'][0]['id']
    assert a.post(f'/admin/live-reviews/{sid}',{'action':'approve','note':'Reviewed live'}).status_code==200
    assert u.get('/wallet').json['balance']==100
    assert a.post(f'/admin/live-reviews/{sid}',{'action':'approve','note':'again'}).status_code==409

def test_task_terms_cannot_change_after_start(env):
    _,a,u,_=env;t=task(a);u.post(f'/tasks/{t}/start')
    assert a.post(f'/admin/tasks/{t}/edit',{'title':'Changed','description':'Changed','reward':'1'}).status_code==409

def test_module_settings_validation(env):
    _,a,u,_=env
    for key_,value in [('survey_daily_limit','0'),('agency_fee','-1'),('agency_commission_percent','101'),('live_daily_minutes','-1'),('live_enabled','yes')]:assert a.post('/admin/settings',{key_:value}).status_code==400
    assert u.post('/admin/settings',{'live_rate':'10000'}).status_code==403
