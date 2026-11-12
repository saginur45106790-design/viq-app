"""Server-enforced module rules. Monetary values are integer paisa."""
import io
from urllib.parse import urlparse
from flask import g, request, abort, send_file
from sqlalchemy import select, func, update, delete, or_
from models import *

DEFAULTS3 = {'survey_daily_limit':'5', 'video_claim_hours':'24', 'agency_fee':'1000',
 'signup_member':'10', 'signup_referrer':'5', 'agency_signup_member':'30',
 'agency_signup_referrer':'50', 'agency_commission_percent':'5',
 'live_rate':'1', 'live_daily_minutes':'60', 'live_enabled':'true'}
PLATFORMS = {
 'facebook_page':('ফেসবুক পেজ ফলো করে স্ক্রিনশট দিন।',('facebook.com','fb.com')),
 'facebook_group':('ফেসবুক গ্রুপে জয়েন করে স্ক্রিনশট দিন।',('facebook.com','fb.com')),
 'facebook_post':('ফেসবুক পোস্টে লাইক ও কমেন্ট করে স্ক্রিনশট দিন।',('facebook.com','fb.com')),
 'tiktok_video':('টিকটক ভিডিওতে লাইক ও কমেন্ট করে স্ক্রিনশট দিন।',('tiktok.com',)),
 'tiktok_profile':('টিকটক প্রোফাইল ফলো করে স্ক্রিনশট দিন।',('tiktok.com',)),
 'youtube_video':('ইউটিউব ভিডিওতে লাইক ও কমেন্ট করে স্ক্রিনশট দিন।',('youtube.com','youtu.be')),
 'youtube_channel':('ইউটিউব চ্যানেল সাবস্ক্রাইব করে স্ক্রিনশট দিন।',('youtube.com',))}
def values(obj):return {c.name:getattr(obj,c.name) for c in obj.__table__.columns}
def day_start():return ((now()+21600)//86400)*86400-21600  # Asia/Dhaka UTC+6

def referral_code(uid):
    s=''
    while uid:s=chr(65+uid%26)+s;uid//=26
    return s.rjust(4,'A')
def referral_id(code):
    code=str(code).strip().upper()
    if code.isdigit():return int(code) # old links remain valid
    if not 4<=len(code)<=8 or not code.isascii() or not code.isalpha():abort(400,'রেফার কোড ঠিক নয়।')
    result=0
    for ch in code:result=result*26+ord(ch)-65
    return result

def register_v3(app,login_required,admin_required,data,change,audit,notify,category,setting,money,number,txt,https_url):
    def agency(uid):
        return bool(g.db.scalar(select(Ticket.id).where(Ticket.user_id==uid,Ticket.kind=='agency',Ticket.status=='approved')))
    def spec(t):
        r=g.db.get(TaskRule,t.id)
        return {'proof_type':r.proof_type if r else {'social':'image','create-video':'video','voice':'audio','survey':'text'}.get(t.category,'text'),
                'platform':r.platform if r else '', 'instruction':PLATFORMS.get(r.platform,('',()))[0] if r else '',
                'sample_url':r.sample_url if r else '', 'sample_uploaded':bool(r and r.sample_data)}
    def decorate(t):
        rule=spec(t); c=g.db.get(TaskReservation,t.id)
        return {**rule,'claim_expires':c.expires if c and c.user_id==g.user.id else None}
    def visible(t):
        if t.category!='create-video':return True
        c=g.db.get(TaskReservation,t.id)
        return not c or c.user_id==g.user.id or c.expires<now()
    def start_rule(t):
        # Serialize claims on the task row; PK protects SQLite/test races too.
        g.db.scalar(select(Task).where(Task.id==t.id).with_for_update())
        if t.category=='create-video':
            c=g.db.get(TaskReservation,t.id)
            if c and c.user_id!=g.user.id and c.expires>=now():abort(409,'এই ভিডিও কাজ অন্য সদস্যের জন্য বরাদ্দ।')
            if not c:c=TaskReservation(task_id=t.id,user_id=g.user.id,expires=0);g.db.add(c)
            if c.expires<now():c.user_id=g.user.id;c.expires=now()+int(setting('video_claim_hours'))*3600
    def submit_rule(t,s,proof):
        rule=spec(t); a=g.db.scalar(select(Attachment).where(Attachment.submission_id==s.id))
        if t.category=='create-video':
            c=g.db.scalar(select(TaskReservation).where(TaskReservation.task_id==t.id).with_for_update())
            if not c or c.user_id!=g.user.id or c.expires<now():abort(409,'বরাদ্দ শেষ। কাজটি আবার শুরু করুন।')
            c.expires=4102444800 # submitted jobs never automatically go to another worker
        p=rule['proof_type']
        if p in ('image','audio') and (not a or not a.mime.startswith(p+'/')):abort(400,'নির্ধারিত '+('স্ক্রিনশট/ছবি' if p=='image' else 'ভয়েস')+' ফাইল প্রয়োজন।')
        if p=='video' and not (a and a.mime.startswith('video/')):
            if not proof or not https_url(proof):abort(400,'ভিডিও ফাইল বা শেয়ারযোগ্য HTTPS ভিডিও লিংক দিন।')
        if p=='text' and not proof:abort(400,'প্রশ্নের লিখিত উত্তর দিন।')
        if t.category=='survey':
            g.db.scalar(select(User).where(User.id==g.user.id).with_for_update())
            count=g.db.scalar(select(func.count()).select_from(Submission).join(Task,Task.id==Submission.task_id).where(Submission.user_id==g.user.id,Task.category=='survey',Submission.status!='started',Submission.created>=day_start()))
            if count>=int(setting('survey_daily_limit')):abort(409,'আজকের প্রশ্নের সীমা শেষ। বাংলাদেশ সময় রাত ১২টায় আবার শুরু হবে।')
        if not g.db.get(RewardSnapshot,s.id):g.db.add(RewardSnapshot(submission_id=s.id,reward=t.reward,referral=t.referral))
    def save_rule(t,d):
        p=d.get('proof_type','text'); platform=d.get('platform','')
        if t.category=='social':
            if platform not in PLATFORMS:abort(400,'সোশ্যাল লিংকের ধরন নির্বাচন করুন।')
            host=(urlparse(t.url).hostname or '').lower()
            if not any(host==x or host.endswith('.'+x) for x in PLATFORMS[platform][1]):abort(400,'নির্বাচিত প্ল্যাটফর্মের HTTPS লিংক দিন।')
            p='image'
        elif t.category=='create-video':p='video';t.slots=1
        elif t.category=='voice':p='audio'
        elif t.category=='survey':p='text'
        if p not in ('text','image','audio','video'):abort(400,'সঠিক প্রমাণের ধরন দিন।')
        if t.category=='daily' and p=='video':abort(400,'ডেইলি টাস্কে লেখা, ছবি বা ভয়েস নির্বাচন করুন।')
        r=g.db.get(TaskRule,t.id)
        if not r:r=TaskRule(task_id=t.id,proof_type=p);g.db.add(r)
        r.proof_type=p;r.platform=platform if t.category=='social' else '';r.sample_url=https_url(d.get('sample_url',''))
        if t.category=='create-video' and not r.sample_url and not r.sample_data:t.active=False
    def signup(u):
        if u.referrer:
            is_agency=agency(u.referrer)
            change(u.id,money(setting('agency_signup_member' if is_agency else 'signup_member'),True),0,'signup_bonus',f'signup:{u.id}:member')
            change(u.referrer,money(setting('agency_signup_referrer' if is_agency else 'signup_referrer'),True),0,'signup_referral',f'signup:{u.id}:referrer')
    def agency_hold():
        category('agency')
        g.db.scalar(select(User).where(User.id==g.user.id).with_for_update())
        if g.db.scalar(select(Ticket.id).where(Ticket.user_id==g.user.id,Ticket.kind=='agency',Ticket.status.in_(['pending','processing','approved']))):abort(409,'আপনার এজেন্সি আছে অথবা আবেদন অপেক্ষমাণ।')
        return money(setting('agency_fee'))
    def withdrawal_snapshot(t):
        if g.user.referrer and agency(g.user.referrer):
            amount=t.amount*int(setting('agency_commission_percent'))//100
            if amount:g.db.add(WithdrawalCommission(ticket_id=t.id,owner_id=g.user.referrer,amount=amount))
    def withdrawal_pay(t):
        c=g.db.get(WithdrawalCommission,t.id)
        if c:
            owner=g.db.get(User,c.owner_id)
            if owner and not owner.blocked:change(c.owner_id,c.amount,0,'agency_withdraw',f'withdrawal:{t.id}:commission','Team member #'+str(t.user_id))
    def end_live(rid):
        s=g.db.scalar(select(LiveSession).where(LiveSession.room_id==rid).with_for_update())
        if s and s.status=='active':s.status='pending';s.witnessed=False
    app.extensions['v3']={'spec':spec,'decorate':decorate,'visible':visible,'start':start_rule,'submit':submit_rule,'save':save_rule,'signup':signup,'agency_hold':agency_hold,'withdrawal_snapshot':withdrawal_snapshot,'withdrawal_pay':withdrawal_pay,'end_live':end_live}

    @app.get('/api/modules/progress')
    @login_required
    def module_progress():
        count=g.db.scalar(select(func.count()).select_from(Submission).join(Task,Task.id==Submission.task_id).where(Submission.user_id==g.user.id,Task.category=='survey',Submission.status!='started',Submission.created>=day_start()))
        return {'survey_used':count,'survey_limit':int(setting('survey_daily_limit')),'reset_at':day_start()+86400,'platforms':{k:v[0] for k,v in PLATFORMS.items()}}

    @app.get('/api/tasks/<int:tid>/sample')
    @login_required
    def sample(tid):
        t=g.db.get(Task,tid)
        if not t:abort(404)
        category(t.category);r=g.db.get(TaskRule,tid)
        if not r or not r.sample_data:abort(404)
        return send_file(io.BytesIO(r.sample_data),mimetype=r.sample_mime,download_name='sample.mp4')
    @app.post('/api/admin/tasks/<int:tid>/sample')
    @admin_required
    def sample_upload(tid):
        t=g.db.get(Task,tid)
        if not t or t.category!='create-video':abort(400,'শুধু ভিডিও তৈরির কাজের জন্য নমুনা দিন।')
        f=request.files.get('file'); blob=f.read(8*1024*1024+1) if f else b''
        if not blob or len(blob)>8*1024*1024:abort(400,'নমুনা সর্বোচ্চ ৮ MB দিন; বড় হলে HTTPS লিংক দিন।')
        mime='video/mp4' if blob[4:8]==b'ftyp' else 'video/webm' if blob.startswith(b'\x1aE\xdf\xa3') else None
        if not mime:abort(400,'MP4 অথবা WebM ভিডিও দিন।')
        r=g.db.get(TaskRule,tid)
        if not r:r=TaskRule(task_id=tid,proof_type='video');g.db.add(r)
        r.sample_data=blob;r.sample_mime=mime;t.active=True;audit('task_sample',{'id':tid});return {'ok':True}

    @app.post('/api/admin/tasks/<int:tid>/edit')
    @admin_required
    def edit_task(tid):
        t=g.db.scalar(select(Task).where(Task.id==tid).with_for_update())
        if not t:abort(404)
        d=data()
        # Work already started has immutable terms, preserving the promised price.
        if g.db.scalar(select(Submission.id).where(Submission.task_id==tid).limit(1)):abort(409,'কাজ শুরু হয়েছে। শর্ত বদলানোর বদলে বন্ধ করে নতুন কাজ প্রকাশ করুন।')
        t.title=txt(d.get('title'),160);t.description=txt(d.get('description'),10000);t.reward=money(d.get('reward'));t.url=https_url(d.get('url',''))
        t.slots=number(d.get('slots',t.slots),1,100000);save_rule(t,d);audit('task_edit',{'id':tid});return {'ok':True}

    @app.post('/api/live/start')
    @login_required
    def live_start():
        category('live')
        if setting('live_enabled')!='true':abort(403,'অডিও লাইভ এখন বন্ধ।')
        g.db.scalar(select(User).where(User.id==g.user.id).with_for_update())
        old=g.db.scalar(select(LiveSession).where(LiveSession.user_id==g.user.id,LiveSession.status=='active'))
        if old and old.last_tick>=now()-60:return {'room_id':old.room_id}
        if old:
            end_live(old.room_id);g.db.get(Room,old.room_id).active=False
        r=Room(title=txt(data().get('title',''),120),kind='live',host_id=g.user.id,audio_only=True);g.db.add(r);g.db.flush()
        s=LiveSession(room_id=r.id,user_id=g.user.id,rate=money(setting('live_rate'),True));g.db.add(s)
        audit('live_start',{'room':r.id});return {'room_id':r.id}
    @app.post('/api/live/<int:rid>/tick')
    @login_required
    def live_tick(rid):
        category('live');g.db.scalar(select(User).where(User.id==g.user.id).with_for_update())
        s=g.db.scalar(select(LiveSession).where(LiveSession.room_id==rid,LiveSession.user_id==g.user.id).with_for_update())
        r=g.db.get(Room,rid)
        if not s or s.status!='active' or not r or not r.active:abort(409,'লাইভ শেষ হয়েছে।')
        if setting('live_enabled')!='true':abort(403,'অডিও লাইভ আয় বন্ধ।')
        if s.created<day_start():
            end_live(rid);r.active=False
            return {'seconds':s.seconds,'amount':(s.seconds//60)*s.rate,'rate':s.rate,'audience':0,'status':'pending','cap_seconds':s.seconds}
        peers=list(g.db.scalars(select(Peer).where(Peer.room_id==rid,Peer.seen>now()-15)))
        witness=any(p.user_id!=g.user.id for p in peers) and any(p.user_id==g.user.id for p in peers) and data().get('mic') is True
        gap=now()-s.last_tick
        # Require witnesses at both ends, bounded gaps, and a server-side daily cap.
        used=g.db.scalar(select(func.coalesce(func.sum(LiveSession.seconds),0)).where(LiveSession.user_id==g.user.id,LiveSession.id!=s.id,LiveSession.created>=day_start()))
        cap=max(0,int(setting('live_daily_minutes'))*60-used)
        if witness and s.witnessed and 0<gap<=20:s.seconds=max(s.seconds,min(cap,s.seconds+gap))
        s.witnessed=witness;s.last_tick=now()
        return {'seconds':s.seconds,'amount':(s.seconds//60)*s.rate,'rate':s.rate,'audience':max(0,len(peers)-1),'status':s.status,'cap_seconds':cap}
    @app.post('/api/live/<int:rid>/end')
    @login_required
    def live_end(rid):
        r=g.db.get(Room,rid)
        if not r or (r.host_id!=g.user.id and g.user.role!='admin'):abort(403)
        end_live(rid);r.active=False;g.db.execute(delete(Peer).where(Peer.room_id==rid));return {'ok':True}
    @app.get('/api/live/history')
    @login_required
    def live_history():
        rows=g.db.scalars(select(LiveSession).where(LiveSession.user_id==g.user.id).order_by(LiveSession.id.desc()).limit(100))
        return {'items':[values(s)|{'amount':(s.seconds//60)*s.rate} for s in rows]}
    @app.get('/api/admin/live-reviews')
    @admin_required
    def live_reviews():
        # Recover interrupted sessions; never infer earnings for offline time.
        stale=list(g.db.scalars(select(LiveSession).where(LiveSession.status=='active',LiveSession.last_tick<now()-60).with_for_update()))
        for s in stale:end_live(s.room_id);g.db.get(Room,s.room_id).active=False
        rows=g.db.scalars(select(LiveSession).where(LiveSession.status=='pending').order_by(LiveSession.id).limit(100))
        return {'items':[values(s)|{'amount':(s.seconds//60)*s.rate} for s in rows]}
    @app.post('/api/admin/live-reviews/<int:sid>')
    @admin_required
    def live_review(sid):
        s=g.db.scalar(select(LiveSession).where(LiveSession.id==sid).with_for_update());d=data()
        if not s or s.status!='pending':abort(409,'এই লাইভ অপেক্ষমাণ নয়।')
        if d.get('action') not in ('approve','reject'):abort(400)
        s.note=txt(d.get('note',''),2000,True);s.status='approved' if d['action']=='approve' else 'rejected'
        amount=(s.seconds//60)*s.rate
        if s.status=='approved' and amount:change(s.user_id,amount,0,'audio_live',f'live:{s.id}',s.note)
        notify(s.user_id,'অডিও লাইভ রিভিউ',s.status+' — '+s.note,'#category/live');audit('live_review',{'id':sid,'action':d['action']});return {'ok':True}
