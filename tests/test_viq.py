import os, uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
from app import create_app, CATEGORIES, DEFAULTS
from models import Base, User, Category, Setting, Ledger, Ticket, Submission

PASSWORD='A-unique-test-password-123'

class Client:
    def __init__(self, app, email):
        self.raw=app.test_client()
        result=self.raw.post('/api/login',json={'email':email,'password':PASSWORD})
        assert result.status_code==200,result.json
        self.csrf=result.json['csrf']
    def get(self,path):return self.raw.get('/api'+path)
    def post(self,path,data=None):return self.raw.post('/api'+path,json=data or {},headers={'X-CSRF-Token':self.csrf})

@pytest.fixture
def env(tmp_path):
    app=create_app({'TESTING':True,'DATABASE_URL':os.getenv('TEST_DATABASE_URL') or 'sqlite:///'+str(tmp_path/'test.db')})
    eng=app.extensions['engine'];Base.metadata.drop_all(eng);Base.metadata.create_all(eng)
    with Session(eng) as db,db.begin():
        for slug,name,desc in CATEGORIES:db.add(Category(slug=slug,name=name,description=desc,enabled=slug!='adult'))
        for k,v in DEFAULTS.items():db.add(Setting(key=k,value='true' if k=='deposits_enabled' else v))
        db.add_all([User(id=1,name='Owner',email='admin@test.com',password=generate_password_hash(PASSWORD),role='admin'),User(id=2,name='Worker',email='worker@test.com',password=generate_password_hash(PASSWORD),referrer=3),User(id=3,name='Team',email='team@test.com',password=generate_password_hash(PASSWORD))])
    return app,Client(app,'admin@test.com'),Client(app,'worker@test.com'),Client(app,'team@test.com')

def key():return str(uuid.uuid4())
def fund(admin,user,amount='1000'):
    r=user.post('/tickets',{'key':key(),'kind':'deposit','amount':amount,'receipt':uuid.uuid4().hex,'details':'bkash verified payment'})
    assert r.status_code==200,r.json
    rid=r.json['ticket']['id']
    r=admin.post('/admin/tickets/'+str(rid),{'action':'approve','note':'Verified external receipt'})
    assert r.status_code==200,r.json
    return rid
def task(admin,**kw):
    data=dict(category='daily',title='Useful task',description='Create original work.',reward='20',referral='2',slots='10',min_seconds='0',deadline='0');data.update(kw)
    r=admin.post('/admin/tasks',data);assert r.status_code==200,r.json
    return r.json['task']['id']
def submit(user,tid):
    r=user.post(f'/tasks/{tid}/start');assert r.status_code==200
    sid=r.json['submission']['id'];r=user.post(f'/tasks/{tid}/submit',{'proof':'Completed original work'});assert r.status_code==200,r.json
    return sid

def test_eighteen_categories_and_adult_closed(env):
    _,a,u,_=env;c=u.get('/config').json['categories'];assert len(c)==18
    assert u.get('/tasks?category=adult').status_code==403
    assert a.post('/admin/categories/adult',{'enabled':True}).status_code==400
def test_only_admin_can_publish(env):
    _,a,u,_=env;assert u.post('/admin/tasks',{}).status_code==403
    assert u.get('/admin/users').status_code==403
def test_csrf_and_origin(env):
    _,_,u,_=env
    assert u.raw.post('/api/logout',json={}).status_code==403
    assert u.raw.post('/api/logout',json={},headers={'X-CSRF-Token':u.csrf,'Origin':'https://evil.example'}).status_code==403
def test_session_logout_revokes(env):
    _,_,u,_=env
    assert u.post('/logout').status_code==200
    assert u.get('/wallet').status_code==401
def test_invalid_password_and_registration(env):
    app,_,_,_=env;c=app.test_client()
    assert c.post('/api/login',json={'email':'worker@test.com','password':'wrong'}).status_code==401
    assert c.post('/api/register',json={'name':'Test','email':'hello@test.com','password':'short','accept':True}).status_code==400
def test_deposit_approved_once(env):
    _,a,u,_=env;rid=fund(a,u)
    assert a.post(f'/admin/tickets/{rid}',{'action':'approve','note':'again'}).status_code==409
    assert u.get('/wallet').json['balance']==100000
def test_deposit_receipt_reuse(env):
    _,_,u,v=env;data={'key':key(),'kind':'deposit','amount':'50','receipt':'UNIQUE-REFERENCE','details':'Payment'}
    assert u.post('/tickets',data).status_code==200
    data['key']=key();assert v.post('/tickets',data).status_code==409
def test_hold_refund_and_repeated_decision(env):
    _,a,u,_=env;fund(a,u)
    r=u.post('/tickets',{'key':key(),'kind':'withdraw','amount':'150','details':'Nagad number'});rid=r.json['ticket']['id']
    w=u.get('/wallet').json;assert (w['balance'],w['held'])==(85000,15000)
    assert a.post(f'/admin/tickets/{rid}',{'action':'reject','note':'Wrong number'}).status_code==200
    assert a.post(f'/admin/tickets/{rid}',{'action':'reject'}).status_code==409
    w=u.get('/wallet').json;assert (w['balance'],w['held'])==(100000,0)
def test_withdraw_settlement(env):
    _,a,u,_=env;fund(a,u)
    r=u.post('/tickets',{'key':key(),'kind':'withdraw','amount':'100','details':'bKash account'});rid=r.json['ticket']['id']
    assert a.post(f'/admin/tickets/{rid}',{'action':'approve'}).status_code==400
    assert a.post(f'/admin/tickets/{rid}',{'action':'process'}).status_code==200
    assert a.post(f'/admin/tickets/{rid}',{'action':'approve','note':'Actual payment ref'}).status_code==200
    w=u.get('/wallet').json;assert (w['balance'],w['held'])==(90000,0)
def test_insufficient_balance(env):
    _,_,u,_=env
    assert u.post('/tickets',{'key':key(),'kind':'withdraw','amount':'100','details':'number'}).status_code==409
    assert not u.get('/wallet').json['tickets']
def test_transfer_conservation_and_idempotency(env):
    app,a,u,v=env;fund(a,u);d={'key':key(),'recipient':'3','amount':'10.25','password':PASSWORD}
    assert u.post('/transfer',d).status_code==200
    assert u.post('/transfer',d).status_code==200
    assert u.get('/wallet').json['balance']==98975
    assert v.get('/wallet').json['balance']==1025
    with Session(app.extensions['engine']) as db:
        assert db.scalar(select(func.sum(Ledger.amount)).where(Ledger.kind.in_(['transfer_in','transfer_out'])))==0
def test_transfer_negative_self_wrong_password(env):
    _,a,u,_=env;fund(a,u)
    for recipient,amount,pw in [('3','-1',PASSWORD),('2','1',PASSWORD),('3','1','wrong'),('3','0.001',PASSWORD),('3','NaN',PASSWORD)]:
        assert u.post('/transfer',{'key':key(),'recipient':recipient,'amount':amount,'password':pw}).status_code in (400,403)
def test_task_reward_and_referral_exactly_once(env):
    _,a,u,v=env;tid=task(a);sid=submit(u,tid)
    assert a.post(f'/admin/submissions/{sid}',{'action':'approve'}).status_code==200
    assert a.post(f'/admin/submissions/{sid}',{'action':'approve'}).status_code==409
    assert u.get('/wallet').json['balance']==2000
    assert v.get('/wallet').json['balance']==200
    assert u.post(f'/tasks/{tid}/submit',{'proof':'again'}).status_code==409
def test_task_slot_limit_and_rejection(env):
    _,a,u,v=env;tid=task(a,slots='1');sid=submit(u,tid)
    assert v.post(f'/tasks/{tid}/start').status_code==409
    assert a.post(f'/admin/submissions/{sid}',{'action':'reject'}).status_code==200
    assert v.post(f'/tasks/{tid}/start').status_code==200
def test_task_timer_and_deadline(env):
    _,a,u,_=env;tid=task(a,min_seconds='3600')
    assert u.post(f'/tasks/{tid}/start').status_code==200
    assert u.post(f'/tasks/{tid}/submit',{'proof':'too early'}).status_code==400
    tid=task(a,deadline='1');assert u.post(f'/tasks/{tid}/start').status_code==409
def test_attachment_private_and_content_type(env):
    import io
    _,a,u,v=env;tid=task(a);sid=u.post(f'/tasks/{tid}/start').json['submission']['id']
    url=f'/api/submissions/{sid}/attachment'
    assert u.raw.post(url,data={'file':(io.BytesIO(b'<script>evil()</script>'),'evil.png')},headers={'X-CSRF-Token':u.csrf}).status_code==400
    png=b'\x89PNG\r\n\x1a\n'+bytes(50)
    assert u.raw.post(url,data={'file':(io.BytesIO(png),'proof.png')},headers={'X-CSRF-Token':u.csrf}).status_code==200
    assert u.get(f'/attachments/{sid}').status_code==200
    assert a.get(f'/attachments/{sid}').status_code==200
    assert v.get(f'/attachments/{sid}').status_code==404
def test_exchange_quote_and_hold(env):
    _,a,u,_=env;fund(a,u)
    assert a.post('/admin/exchange-routes',{'name':'VIQ to Nagad','rate':'1','fee':'5','unit':'BDT'}).status_code==200
    rid=u.get('/exchange-routes').json['routes'][0]['id']
    r=u.post('/tickets',{'key':key(),'kind':'exchange','route':str(rid),'amount':'100','details':'recipient'})
    assert r.status_code==200
    import json
    assert json.loads(r.json['ticket']['details'])['receive']=='95.0000'
    assert u.get('/wallet').json['held']==10000
def test_recharge_number_and_idempotency(env):
    _,a,u,_=env;fund(a,u);d={'key':key(),'kind':'recharge','amount':'20','details':'prepaid','phone':'01712345678','operator':'GP'}
    assert u.post('/tickets',d).status_code==200
    assert u.post('/tickets',d).status_code==200
    assert u.get('/wallet').json['held']==2000
    d.update(key=key(),phone='0000');assert u.post('/tickets',d).status_code==400
def test_blocked_user_session_revoked(env):
    _,a,u,_=env
    assert a.post('/admin/users/2',{'blocked':True}).status_code==200
    assert u.get('/wallet').status_code==401
def test_call_room_privacy(env):
    _,a,u,v=env
    r=a.post('/admin/rooms',{'title':'Private call','kind':'call','host_id':'1','guest_id':'2'})
    rid=r.json['room']['id']
    assert v.post(f'/rooms/{rid}/join').status_code==403
    assert not v.get('/rooms').json['rooms']
    assert u.post(f'/rooms/{rid}/join').status_code==200
    assert u.post(f'/rooms/{rid}/signal',{'recipient':'3','payload':{'type':'ice'}}).status_code==403
def test_urls_must_be_https(env):
    _,a,_,_=env
    assert a.post('/admin/settings',{'cobra_url':'javascript:alert(1)'}).status_code==400
    assert a.post('/admin/settings',{'cobra_url':'https://cobra.example'}).status_code==200
def test_wallet_ledger_reconciles(env):
    app,a,u,v=env;fund(a,u);tid=task(a);sid=submit(u,tid);a.post(f'/admin/submissions/{sid}',{'action':'approve'})
    u.post('/transfer',{'key':key(),'recipient':'3','amount':'15','password':PASSWORD})
    u.post('/tickets',{'key':key(),'kind':'withdraw','amount':'100','details':'number'})
    with Session(app.extensions['engine']) as db:
        for person in db.scalars(select(User)):
            amount,held=db.execute(select(func.coalesce(func.sum(Ledger.amount),0),func.coalesce(func.sum(Ledger.held_delta),0)).where(Ledger.user_id==person.id)).one()
            assert (person.balance,person.held)==(amount,held)
def test_postgres_concurrent_withdrawals_do_not_overspend(env):
    app,a,u,_=env
    if app.extensions['engine'].dialect.name!='postgresql':pytest.skip('Requires PostgreSQL; CI workflow runs this test.')
    fund(a,u,'100')
    clients=[Client(app,'worker@test.com') for _ in range(2)]
    def withdraw(c):return c.post('/tickets',{'key':key(),'kind':'withdraw','amount':'100','details':'destination'}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(withdraw,clients))
    assert sorted(results)==[200,409]
    w=u.get('/wallet').json;assert (w['balance'],w['held'])==(0,10000)
