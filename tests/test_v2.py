from sqlalchemy.orm import Session
from models import User, Ledger, Base
from test_viq import env, fund, task, submit, key, Client, PASSWORD

def test_dashboard_counts_are_real(env):
    _,a,u,_=env;tid=task(a);sid=submit(u,tid)
    assert u.get('/dashboard').json['counts']['pending']==1
    a.post(f'/admin/submissions/{sid}',{'action':'approve'})
    d=u.get('/dashboard').json
    assert d['earned']==2000 and d['counts']['approved']==1 and d['unread']>=1

def test_favorites_search_and_user_isolation(env):
    _,a,u,v=env;tid=task(a,title='Record a voice script')
    assert u.post(f'/tasks/{tid}/save',{'saved':True}).status_code==200
    assert u.get('/discover?saved=1').json['total']==1
    assert v.get('/discover?saved=1').json['total']==0
    assert u.get('/discover?q=voice').json['total']==1
    assert u.get('/discover?q=unmatched').json['total']==0
    assert u.post(f'/tasks/{tid}/save',{'saved':False}).status_code==200
    assert u.get('/discover?saved=1').json['total']==0

def test_search_escapes_sql_wildcards(env):
    _,a,u,_=env;task(a,title='Ordinary work')
    assert u.get('/discover?q=%25').json['total']==0

def test_notification_privacy_and_read(env):
    _,a,u,v=env;fund(a,u)
    assert u.get('/notifications').json['items']
    assert not v.get('/notifications').json['items']
    u.post('/notifications/read')
    assert u.get('/dashboard').json['unread']==0

def test_cancel_refunds_once_and_not_after_processing(env):
    _,a,u,_=env;fund(a,u)
    rid=u.post('/tickets',{'kind':'withdraw','amount':'100','details':'destination','key':key()}).json['ticket']['id']
    assert u.post(f'/tickets/{rid}/cancel').status_code==200
    assert u.post(f'/tickets/{rid}/cancel').status_code==409
    assert a.post(f'/admin/tickets/{rid}',{'action':'approve','note':'no'}).status_code==409
    w=u.get('/wallet').json;assert w['balance']==100000 and w['held']==0
    rid=u.post('/tickets',{'kind':'withdraw','amount':'100','details':'destination','key':key()}).json['ticket']['id']
    a.post(f'/admin/tickets/{rid}',{'action':'process'})
    assert u.post(f'/tickets/{rid}/cancel').status_code==409

def test_ticket_messages_are_private(env):
    _,a,u,v=env
    rid=u.post('/tickets',{'kind':'support','details':'Need help','key':key()}).json['ticket']['id']
    assert u.post(f'/tickets/{rid}/message',{'body':'My question'}).status_code==200
    assert v.get(f'/tickets/{rid}').status_code==404
    assert v.post(f'/tickets/{rid}/message',{'body':'intrusion'}).status_code==404
    assert v.post(f'/tickets/{rid}/cancel').status_code==404
    assert a.post(f'/tickets/{rid}/message',{'body':'Admin response'}).status_code==200
    messages=u.get(f'/tickets/{rid}').json['messages']
    assert len(messages)==2 and messages[1]['role']=='admin'

def test_session_revoke_preserves_current(env):
    app,_,u,_=env;other=Client(app,'worker@test.com')
    assert len(u.get('/sessions').json['items'])==2
    assert all('token' not in x for x in u.get('/sessions').json['items'])
    u.post('/sessions/revoke-others')
    assert u.get('/wallet').status_code==200
    assert other.get('/wallet').status_code==401

def test_changed_idempotent_request_rejected(env):
    _,a,u,_=env;fund(a,u)
    payload={'key':key(),'recipient':'3','amount':'10','password':PASSWORD}
    assert u.post('/transfer',payload).status_code==200
    payload['amount']='50'
    assert u.post('/transfer',payload).status_code==409
    assert u.get('/wallet').json['balance']==99000

def test_strict_boolean_validation(env):
    _,a,u,_=env
    assert a.post('/admin/users/2',{'blocked':'false'}).status_code==400
    assert u.get('/wallet').status_code==200
    assert a.post('/admin/categories/daily',{'enabled':'true'}).status_code==400

def test_ledger_reconcile_detects_corruption(env):
    app,a,u,_=env;fund(a,u)
    assert a.get('/admin/reconciliation').json['ok'] is True
    assert u.get('/admin/reconciliation').status_code==403
    with Session(app.extensions['engine']) as db,db.begin():db.get(User,2).balance+=1
    r=a.get('/admin/reconciliation').json
    assert r['ok'] is False and r['mismatches'][0]['user_id']==2

def test_csv_export_is_private_and_formula_safe(env):
    app,a,u,v=env
    with Session(app.extensions['engine']) as db,db.begin():
        db.add(Ledger(user_id=2,amount=0,held_delta=0,kind='note',reference='csv-only',note='=HYPERLINK("https://example.com")'))
    r=u.get('/wallet/export');assert r.status_code==200
    assert "'=HYPERLINK" in r.get_data(as_text=True)
    assert 'HYPERLINK' not in v.get('/wallet/export').get_data(as_text=True)
    assert r.headers['Cache-Control']=='no-store'

def test_cross_site_header_rejected_even_without_origin(env):
    _,_,u,_=env
    r=u.raw.post('/api/logout',json={},headers={'X-CSRF-Token':u.csrf,'Sec-Fetch-Site':'cross-site'})
    assert r.status_code==403

def test_update_keeps_old_data(env):
    app,a,u,_=env;fund(a,u)
    Base.metadata.create_all(app.extensions['engine'])
    assert u.get('/wallet').json['balance']==100000
    assert u.get('/sessions').status_code==200

def test_ready_and_request_id(env):
    app,_,u,_=env
    assert app.test_client().get('/ready').json['ready'] is True
    assert len(u.get('/wallet').headers['X-Request-ID'])==16
