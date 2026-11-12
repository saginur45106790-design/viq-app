import os, re, json, secrets, hashlib, io, logging
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from functools import wraps
from flask import Flask, request, jsonify, g, send_file, render_template, abort
from sqlalchemy import create_engine, select, update, delete, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from v3 import DEFAULTS3, referral_code, referral_id, register_v3

CATEGORIES = [
 ('social','লাইক • ফলো • জয়েন','অনুমোদিত সোশ্যাল কাজ ও প্রমাণ জমা।'),
 ('create-video','ভিডিও তৈরি','ব্রিফ অনুযায়ী ভিডিও তৈরি করে লিংক জমা দিন।'),
 ('ads','বিজ্ঞাপন দেখা','স্পনসরের অনুমোদিত বিজ্ঞাপন ও ফিডব্যাক কাজ।'),
 ('watch-video','ভিডিও দেখা','ভিডিও দেখে নির্দেশিত উত্তর বা ফিডব্যাক দিন।'),
 ('team','রেফার ও টিম','আপনার রেফার করা সদস্যের অনুমোদিত কাজ থেকে নির্ধারিত কমিশন।'),
 ('calls','ভিডিও কল','অনুমোদিত কল বুকিং এবং ব্যক্তিগত কল রুম।'),
 ('agency','এজেন্সি','এজেন্সির আবেদন, কাজ ও সদস্য ব্যবস্থাপনা।'),
 ('pages','ফেসবুক পেজ বিক্রি','অ্যাডমিনের নির্ধারিত শর্তে প্রস্তাব জমা ও মালিকানা যাচাই। প্ল্যাটফর্মের অনুমোদিত হস্তান্তর ছাড়া কাজ সম্পন্ন নয়।'),
 ('gmail','জিমেইল বিক্রি','অ্যাডমিনের নির্ধারিত প্রস্তাব ও যাচাই। পাসওয়ার্ড, OTP বা অ্যাকাউন্টের প্রবেশাধিকার এখানে জমা দেবেন না।'),
 ('adult','১৮+','এই বিভাগ এখনো চালু হয়নি।'),
 ('survey','প্রশ্নের উত্তর','লিখিত অথবা ভয়েস উত্তর জমা দিন।'),
 ('groups','ফেসবুক গ্রুপ বিক্রি','অ্যাডমিনের নির্ধারিত শর্তে প্রস্তাব জমা ও যাচাই। প্ল্যাটফর্মের অনুমোদিত হস্তান্তর ছাড়া কাজ সম্পন্ন নয়।'),
 ('daily','ডেইলি টাস্ক','নতুন কাজ, সময়সীমা ও যাচাইকৃত পারিশ্রমিক।'),
 ('live','অডিও লাইভ','অডিও রুম, শ্রোতা ও মিনিটভিত্তিক পারিশ্রমিক।'),
 ('voice','লেখা থেকে ভয়েস','স্ক্রিপ্ট পড়ে নিজের কণ্ঠে রেকর্ড জমা দিন।'),
 ('cobra','Cobra ইনভেস্টিং','আপনার বিদ্যমান Cobra সাইটের বাহ্যিক লিংক।'),
 ('recharge','মোবাইল রিচার্জ','নম্বর ও অপারেটর দিয়ে রিচার্জ আবেদন করুন।'),
 ('exchange','মানি এক্সচেঞ্জ','প্রকাশিত রেট ও ফি দেখে এক্সচেঞ্জ আবেদন করুন।')]
DEFAULTS = {'notice':'VIQ-তে স্বাগতম। কাজের শর্ত পড়ে জমা দিন। অনুমোদনের পর আয় যোগ হবে।',
 'cobra_url':'', 'payment_instructions':'পেমেন্ট গ্রহণের নম্বর এখনো যোগ করা হয়নি।',
 'deposits_enabled':'false','min_withdraw':'100','support':'সাপোর্ট পেজে আপনার বার্তা দিন।',
 'privacy':'আপনার নাম, ইমেইল, জমা দেওয়া কাজ ও লেনদেনের তথ্য সেবা পরিচালনায় ব্যবহৃত হবে। অ্যাডমিন অনুমোদিত কাজের প্রমাণ দেখতে পারেন। কল/লাইভ সার্ভারে রেকর্ড করা হয় না। অ্যাকাউন্ট মুছতে সাপোর্টে আবেদন করুন; প্রয়োজনীয় লেনদেনের রেকর্ড সংরক্ষিত থাকতে পারে।',
 'terms':'আয় নির্ভর করে উপলব্ধ কাজ, কাজের মান ও অনুমোদনের ওপর। নিশ্চিত দৈনিক আয়ের প্রতিশ্রুতি নেই। অ্যাকাউন্টের পাসওয়ার্ড, OTP বা অন্যের ব্যক্তিগত তথ্য জমা দেবেন না। কাজের বিরোধে সাপোর্টে আবেদন করুন।'}

DEFAULTS.update(DEFAULTS3)

def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def money(value, allow_zero=False):
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n != n.quantize(Decimal('.01')): raise ValueError()
        p = int(n * 100)
        if p < (0 if allow_zero else 1) or p > 100_000_000: raise ValueError()
        return p
    except (ValueError, InvalidOperation, TypeError): abort(400, 'সঠিক টাকার পরিমাণ দিন (সর্বোচ্চ ১০ লাখ)।')
def txt(v, size=2000, required=True):
    if not isinstance(v, str): abort(400, 'সঠিক লেখা দিন।')
    v = v.strip()
    if len(v)>size or (required and not v): abort(400, 'লেখাটি খালি অথবা খুব বড়।')
    return v
def https_url(v):
    v = txt(v, 2000, False)
    if v:
        p = urlparse(v)
        if p.scheme != 'https' or not p.hostname or p.username or p.password: abort(400, 'HTTPS লিংক দিন।')
    return v
def number(v, lo=0, hi=100000):
    try:
        if isinstance(v, bool) or str(int(v)) != str(v): raise ValueError()
        n = int(v)
        if n < lo or n > hi: raise ValueError()
        return n
    except (ValueError,TypeError): abort(400,'সঠিক পূর্ণসংখ্যা দিন।')
def boolean(value):
    if type(value) is not bool: abort(400, "সঠিক true/false মান প্রয়োজন।")
    return value

def dump(obj, exclude=()):
    return {c.name:getattr(obj,c.name) for c in obj.__table__.columns if c.name not in exclude}

def create_app(test_config=None):
    app = Flask(__name__)
    production = os.getenv('APP_ENV') == 'production'
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or secrets.token_hex(32), MAX_CONTENT_LENGTH=9*1024*1024,
        PRODUCTION=production, PUBLIC_URL=os.getenv('PUBLIC_URL','http://127.0.0.1:5000').rstrip('/'))
    if test_config: app.config.update(test_config)
    db_url = (test_config or {}).get('DATABASE_URL') or os.getenv('DATABASE_URL','sqlite:///viq-local.db')
    if db_url.startswith('postgres://'): db_url = db_url.replace('postgres://','postgresql+psycopg://',1)
    elif db_url.startswith('postgresql://'): db_url = db_url.replace('postgresql://','postgresql+psycopg://',1)
    if production and (not db_url.startswith('postgresql') or len(os.getenv('SECRET_KEY',''))<32 or not app.config['PUBLIC_URL'].startswith('https://')):
        raise RuntimeError('Production requires PostgreSQL, SECRET_KEY (32+ characters), and HTTPS PUBLIC_URL.')
    engine = create_engine(db_url, pool_pre_ping=True, **({'connect_args':{'check_same_thread':False,'timeout':30}} if db_url.startswith('sqlite') else {'pool_size':5,'max_overflow':2,'connect_args':{'connect_timeout':10}}))
    app.extensions['engine'] = engine

    def setting(key):
        s = g.db.get(Setting,key)
        return s.value if s else DEFAULTS.get(key,'')
    def audit(action, detail):
        g.db.add(Audit(actor=g.user.id if g.user else None, action=action, detail=json.dumps(detail,ensure_ascii=False)))
    def post_data():
        d = request.get_json(silent=True)
        if not isinstance(d,dict): abort(400,'JSON object প্রয়োজন।')
        return d
    def login_required(fn):
        @wraps(fn)
        def wrapped(*a,**kw):
            if not g.user: abort(401,'আগে লগইন করুন।')
            return fn(*a,**kw)
        return wrapped
    def admin_required(fn):
        @wraps(fn)
        @login_required
        def wrapped(*a,**kw):
            if g.user.role != 'admin': abort(403,'শুধু অ্যাডমিনের অনুমতি আছে।')
            return fn(*a,**kw)
        return wrapped
    def notify(uid,title,body='',href='#wallet'):
        g.db.add(Notification(user_id=uid,title=title,body=body,href=href))

    def change(uid, amount, held, kind, ref, note=''):
        # Conditional arithmetic in the database prevents lost updates and negative balances.
        result = g.db.execute(update(User).where(User.id==uid,User.balance+amount>=0,User.held+held>=0).values(balance=User.balance+amount,held=User.held+held))
        if result.rowcount != 1: abort(409,'পর্যাপ্ত ব্যালেন্স নেই অথবা হিসাব পরিবর্তিত হয়েছে।')
        g.db.add(Ledger(user_id=uid,amount=amount,held_delta=held,kind=kind,reference=ref,note=note))
        notify(uid,'ওয়ালেট আপডেট',f'{kind}: {amount/100:.2f} BDT; hold {held/100:.2f} BDT. '+note)
    def category(slug):
        c = g.db.get(Category,slug)
        if not c or not c.enabled or slug=='adult': abort(403,'বিভাগটি এখন বন্ধ আছে।')
        return c
    def idem(d):
        key=txt(d.get('key',''),80)
        if not re.fullmatch(r'[A-Za-z0-9_-]{16,80}',key): abort(400,'Request key প্রয়োজন।')
        return f'{g.user.id}:{key}'

    @app.before_request
    def before():
        g.db = Session(engine,expire_on_commit=False)
        g.user = None
        g.login = None
        g.request_id=secrets.token_hex(8)
        g.binding=None
        if not request.path.startswith('/api/'): return
        token = request.cookies.get('viq_session','')
        if token:
            lg = g.db.get(Login,digest(token))
            if lg and lg.expires>now():
                u = g.db.get(User,lg.user_id)
                if u and not u.blocked: g.user, g.login = u, lg
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin = request.headers.get('Origin')
            if origin and origin.rstrip('/') != (app.config['PUBLIC_URL'] if app.config['PRODUCTION'] else request.host_url.rstrip('/')): abort(403,'অনুমোদিত origin নয়।')
            if g.login and not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),g.login.csrf): abort(403,'সেশন যাচাই ব্যর্থ; রিফ্রেশ করুন।')
            if request.headers.get('Sec-Fetch-Site')=='cross-site': abort(403,'Cross-site request blocked.')
            if g.user and not request.path.endswith('/signal'):
                limit_key=digest('mutation:'+str(g.user.id))
                attempts=g.db.scalar(select(func.count()).select_from(Attempt).where(Attempt.key==limit_key,Attempt.created>now()-60))
                if attempts>=90: abort(429,'অনেক অনুরোধ হয়েছে। এক মিনিট পরে চেষ্টা করুন।')
                g.db.add(Attempt(key=limit_key))
                g.db.commit()
            if g.user and request.path in ('/api/tickets','/api/transfer'):
                data=request.get_json(silent=True)
                if isinstance(data,dict) and isinstance(data.get('key'),str) and len(data['key'])<=80:
                    binding_key=str(g.user.id)+':'+request.path+':'+data['key']
                    semantic_data={k:v for k,v in data.items() if k not in ('password','old')}
                    fingerprint=digest(json.dumps(semantic_data,sort_keys=True,ensure_ascii=True,separators=(',',':')))
                    old=g.db.get(IdempotencyBinding,binding_key)
                    if old and old.fingerprint!=fingerprint: abort(409,'একই request key দিয়ে ভিন্ন তথ্য পাঠানো যাবে না।')
                    if not old:g.binding=IdempotencyBinding(key=binding_key,fingerprint=fingerprint)


    @app.after_request
    def after(response):
        response.headers['X-Request-ID']=getattr(g,'request_id','')
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        response.headers['Permissions-Policy']='camera=(self), microphone=(self), geolocation=()'
        if app.config['PRODUCTION']: response.headers['Strict-Transport-Security']='max-age=31536000'
        if request.path.startswith('/api/'): response.headers['Cache-Control']='no-store'
        if hasattr(g,'db'):
            if response.status_code < 400:
                try:
                    if getattr(g,'binding',None) is not None:g.db.add(g.binding)
                    g.db.commit()
                except IntegrityError:
                    g.db.rollback()
                    response=jsonify(error='একই অনুরোধ ইতিমধ্যে প্রক্রিয়া হয়েছে। হিসাব রিফ্রেশ করুন।')
                    response.status_code=409
                    response.headers['Cache-Control']='no-store'
                    response.headers['X-Content-Type-Options']='nosniff'
            else: g.db.rollback()
        return response

    @app.teardown_request
    def teardown(error):
        if hasattr(g,'db'): g.db.close()

    @app.errorhandler(IntegrityError)
    def conflict(error):
        g.db.rollback()
        return jsonify(error='একই তথ্য বা অনুরোধ আগে জমা হয়েছে।'),409

    from werkzeug.exceptions import HTTPException
    @app.errorhandler(HTTPException)
    def http_error(e): return jsonify(error=e.description),e.code

    @app.errorhandler(Exception)
    def unexpected(error):
        if isinstance(error,HTTPException):return http_error(error)
        if hasattr(g,'db'):g.db.rollback()
        app.logger.error('Unhandled request %s: %s',getattr(g,'request_id','unknown'),type(error).__name__)
        return jsonify(error='সার্ভারে সমস্যা হয়েছে। আবার চেষ্টা করুন।',request_id=getattr(g,'request_id','')),500

    @app.get('/health')
    def health(): return {'status':'ok'}
    @app.get('/')
    @app.get('/admin')
    @app.get('/work/<slug>')
    def home(slug=None): return render_template('index.html')
    @app.get('/api/config')
    def config(): return {'categories':[dump(c) for c in g.db.scalars(select(Category))], 'settings':{k:setting(k) for k in DEFAULTS}}
    @app.get('/api/me')
    def me(): return {'user':dump(g.user,('password','referrer')) if g.user else None,'csrf':g.login.csrf if g.login else ''}

    def throttle(identity):
        keys=[digest('identity:'+identity),digest('network:'+str(request.remote_addr))]
        for k,limit in zip(keys,(10,100)):
            n=g.db.scalar(select(func.count()).select_from(Attempt).where(Attempt.key==k,Attempt.created>now()-900))
            if n>=limit: abort(429,'অনেক চেষ্টা হয়েছে। ১৫ মিনিট পরে চেষ্টা করুন।')
            g.db.add(Attempt(key=k))
        g.db.execute(delete(Attempt).where(Attempt.created<now()-86400))
        g.db.commit()  # Persist failed attempts too.
    def set_login(u):
        token=secrets.token_urlsafe(32)
        lg=Login(token=digest(token),user_id=u.id,csrf=secrets.token_hex(32),expires=now()+7*86400)
        if g.login: g.db.delete(g.login)
        g.db.add(lg)
        response=jsonify(user=dump(u,('password','referrer')),csrf=lg.csrf)
        response.set_cookie('viq_session',token,httponly=True,secure=app.config['PRODUCTION'],samesite='Lax',max_age=7*86400,path='/')
        return response
    @app.post('/api/register')
    def register():
        d=post_data(); email=txt(d.get('email',''),254).lower(); throttle(email)
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email): abort(400,'ইমেইল ঠিক নয়।')
        pw=txt(d.get('password',''),200)
        if len(pw)<12: abort(400,'পাসওয়ার্ড কমপক্ষে ১২ অক্ষরের দিন।')
        if not d.get('accept'): abort(400,'শর্তে সম্মতি প্রয়োজন।')
        ref=None
        if d.get('referrer'):
            ref=referral_id(d['referrer'])
            u=g.db.get(User,ref)
            if not u or u.blocked: abort(400,'রেফার আইডি ঠিক নয়।')
        u=User(name=txt(d.get('name',''),100),email=email,password=generate_password_hash(pw),referrer=ref)
        g.db.add(u); g.db.flush()
        app.extensions['v3']['signup'](u)
        return set_login(u)
    @app.post('/api/login')
    def login():
        d=post_data(); email=txt(d.get('email',''),254).lower(); throttle(email)
        u=g.db.scalar(select(User).where(User.email==email))
        if not u or not check_password_hash(u.password,str(d.get('password',''))) or u.blocked: abort(401,'ইমেইল বা পাসওয়ার্ড ভুল, অথবা অ্যাকাউন্ট বন্ধ।')
        if d.get('admin') and u.role!='admin': abort(403,'এটি অ্যাডমিন অ্যাকাউন্ট নয়।')
        return set_login(u)
    @app.post('/api/logout')
    def logout():
        if g.login: g.db.delete(g.login)
        r=jsonify(ok=True); r.delete_cookie('viq_session',path='/'); return r
    @app.post('/api/password')
    @login_required
    def password():
        d=post_data(); throttle('password:'+str(g.user.id)); pw=txt(d.get('password',''),200)
        if not check_password_hash(g.user.password,str(d.get('old',''))) or len(pw)<12: abort(400,'পুরোনো পাসওয়ার্ড যাচাই করুন; নতুনটি ১২+ অক্ষর দিন।')
        g.user.password=generate_password_hash(pw)
        g.db.execute(delete(Login).where(Login.user_id==g.user.id))
        g.login=None
        return set_login(g.user)
    @app.get('/api/tasks')
    @login_required
    def tasks():
        slug=request.args.get('category','daily'); category(slug)
        rows=g.db.scalars(select(Task).where(Task.category==slug).order_by(Task.id.desc()).limit(200))
        result=[]
        for t in rows:
            s=g.db.scalar(select(Submission).where(Submission.user_id==g.user.id,Submission.task_id==t.id))
            if app.extensions['v3']['visible'](t):result.append(dict(dump(t),submission=dump(s) if s else None,**app.extensions['v3']['decorate'](t)))
        if slug=='create-video':
            own=[t for t in result if t['submission']]
            fresh=[t for t in result if not t['submission'] and t['active'] and t['used']<t['slots'] and (not t['deadline'] or t['deadline']>=now())]
            result=own+sorted(fresh,key=lambda t:t['id'])[:1]
        return {'tasks':result}
    @app.post('/api/tasks/<int:tid>/start')
    @login_required
    def start(tid):
        t=g.db.scalar(select(Task).where(Task.id==tid).with_for_update())
        if not t: abort(404)
        category(t.category)
        if not t.active or (t.deadline and t.deadline<now()) or t.used>=t.slots: abort(409,'কাজটি বন্ধ, মেয়াদ শেষ অথবা স্থান পূর্ণ।')
        s=g.db.scalar(select(Submission).where(Submission.user_id==g.user.id,Submission.task_id==tid))
        if not s:
            s=Submission(user_id=g.user.id,task_id=tid); g.db.add(s); g.db.flush()
        if s.status=='started':app.extensions['v3']['start'](t)
        return {'submission':dump(s)}
    @app.post('/api/tasks/<int:tid>/submit')
    @login_required
    def submit(tid):
        d=post_data(); t=g.db.get(Task,tid)
        if not t: abort(404)
        category(t.category)
        s=g.db.scalar(select(Submission).where(Submission.user_id==g.user.id,Submission.task_id==tid).with_for_update())
        if not s or s.status!='started': abort(409,'কাজ শুরু করুন; একই কাজ আবার জমা দেওয়া যাবে না।')
        if s.started+t.min_seconds>now(): abort(400,'নির্ধারিত সময় এখনো শেষ হয়নি।')
        proof=txt(d.get('proof',''),10000,False)
        if not proof and not g.db.scalar(select(Attachment.id).where(Attachment.submission_id==s.id)): abort(400,'উত্তর অথবা ফাইল দিন।')
        app.extensions['v3']['submit'](t,s,proof)
        result=g.db.execute(update(Task).where(Task.id==tid,Task.active==True,Task.used<Task.slots,or_(Task.deadline==0,Task.deadline>=now())).values(used=Task.used+1))
        if not result.rowcount: abort(409,'কাজের স্থান পূর্ণ অথবা মেয়াদ শেষ।')
        s.proof=proof; s.status='pending'; s.created=now()
        return {'ok':True}
    @app.post('/api/submissions/<int:sid>/attachment')
    @login_required
    def upload(sid):
        s=g.db.get(Submission,sid)
        if not s or s.user_id!=g.user.id or s.status!='started': abort(403)
        f=request.files.get('file')
        if not f: abort(400,'ফাইল দিন।')
        data=f.read(8*1024*1024+1)
        if not data or len(data)>8*1024*1024: abort(400,'ফাইল সর্বোচ্চ ৮ MB। বড় ভিডিওর HTTPS লিংক জমা দিন।')
        # Do not trust the browser-supplied MIME or file extension.
        mime=None
        if data.startswith(b'\x89PNG\r\n\x1a\n'): mime='image/png'
        elif data.startswith(b'\xff\xd8\xff'): mime='image/jpeg'
        elif data.startswith(b'\x1aE\xdf\xa3'): mime='video/webm' if f.mimetype=='video/webm' else 'audio/webm'
        elif data.startswith(b'OggS'): mime='audio/ogg'
        elif data.startswith(b'RIFF') and data[8:12]==b'WAVE': mime='audio/wav'
        elif data[4:8]==b'ftyp': mime='video/mp4' if f.mimetype=='video/mp4' else 'audio/mp4'
        if not mime: abort(400,'PNG, JPG, WebM, MP4, OGG অথবা WAV ফাইল দিন।')
        g.db.scalar(select(User).where(User.id==g.user.id).with_for_update())
        total=g.db.scalar(select(func.coalesce(func.sum(func.length(Attachment.data)),0)).where(Attachment.user_id==g.user.id))
        a=g.db.scalar(select(Attachment).where(Attachment.submission_id==sid))
        if total-(len(a.data) if a else 0)+len(data)>64*1024*1024:abort(400,'আপনার ৬৪ MB ফাইল সীমা পূর্ণ। বড় কাজের লিংক দিন বা সাপোর্টে লিখুন।')
        if not a: a=Attachment(submission_id=sid,user_id=g.user.id); g.db.add(a)
        a.data=data; a.mime=mime
        return {'ok':True}
    @app.get('/api/attachments/<int:sid>')
    @login_required
    def attachment(sid):
        a=g.db.scalar(select(Attachment).where(Attachment.submission_id==sid))
        if not a or (a.user_id!=g.user.id and g.user.role!='admin'): abort(404)
        ext={'image/png':'png','image/jpeg':'jpg','audio/webm':'webm','video/webm':'webm','audio/ogg':'ogg','audio/wav':'wav','audio/mp4':'m4a','video/mp4':'mp4'}[a.mime]
        return send_file(io.BytesIO(a.data),mimetype=a.mime,as_attachment=request.args.get('download')=='1',download_name=f'viq-proof-{sid}.{ext}')
    @app.get('/api/history')
    @login_required
    def history():
        rows=g.db.execute(select(Submission,Task.title).join(Task,Task.id==Submission.task_id).where(Submission.user_id==g.user.id).order_by(Submission.created.desc()).limit(200))
        return {'submissions':[dict(dump(s),title=title) for s,title in rows]}
    @app.get('/api/wallet')
    @login_required
    def wallet():
        return {'balance':g.user.balance,'held':g.user.held,'ledger':[dump(x) for x in g.db.scalars(select(Ledger).where(Ledger.user_id==g.user.id).order_by(Ledger.id.desc()).limit(200))], 'tickets':[dump(x) for x in g.db.scalars(select(Ticket).where(Ticket.user_id==g.user.id).order_by(Ticket.id.desc()).limit(200))]}
    @app.get('/api/exchange-routes')
    @login_required
    def routes(): return {'routes':[dump(x) for x in g.db.scalars(select(ExchangeRoute).where(ExchangeRoute.enabled==True))]}
    @app.post('/api/tickets')
    @login_required
    def ticket():
        d=post_data(); key=idem(d)
        old=g.db.scalar(select(Ticket).where(Ticket.idem==key))
        if old: return {'ticket':dump(old)}
        kind=d.get('kind'); details=txt(d.get('details',''),4000)
        if kind not in ('deposit','withdraw','recharge','exchange','agency','call','support','report'): abort(400)
        amount=0; receipt=None
        if kind in ('deposit','withdraw','recharge','exchange'): amount=money(d.get('amount'))
        if kind=='deposit':
            if setting('deposits_enabled')!='true': abort(403,'ডিপোজিট এখন বন্ধ আছে।')
            receipt=txt(d.get('receipt',''),100).upper()
            if not re.fullmatch(r'[A-Z0-9:_-]{5,100}',receipt): abort(400,'লেনদেনের reference ঠিক নয়।')
            receipt='deposit:'+receipt
        if kind=='withdraw' and amount<money(setting('min_withdraw')): abort(400,'সর্বনিম্ন উত্তোলনের পরিমাণ পূরণ হয়নি।')
        if kind=='recharge':
            category('recharge'); phone=txt(d.get('phone',''),11)
            if not re.fullmatch(r'01[3-9][0-9]{8}',phone): abort(400,'বাংলাদেশের ১১ সংখ্যার মোবাইল নম্বর দিন।')
            operator=txt(d.get('operator',''),30)
            if operator not in ('GP','Robi','Airtel','Banglalink','Teletalk'): abort(400,'অপারেটর নির্বাচন করুন।')
            details=json.dumps({'phone':phone,'operator':operator,'note':details},ensure_ascii=False)
        if kind=='exchange':
            category('exchange'); rt=g.db.get(ExchangeRoute,number(d.get('route'),1))
            if not rt or not rt.enabled: abort(400,'রুট বন্ধ আছে।')
            if amount<=rt.fee: abort(400,'টাকার পরিমাণ ফি থেকে বেশি হতে হবে।')
            # Quote locked into ticket; later rate changes never alter existing requests.
            quoted=((Decimal(amount-rt.fee)/100)*Decimal(rt.rate)/10000).quantize(Decimal('.0001'))
            details=json.dumps({'route':rt.name,'rate':str(Decimal(rt.rate)/10000),'fee_paisa':rt.fee,'receive':str(quoted),'unit':rt.unit,'destination':details},ensure_ascii=False)
        if kind=='agency': amount=app.extensions['v3']['agency_hold']()
        if kind=='call': category('calls')
        t=Ticket(user_id=g.user.id,kind=kind,amount=amount,details=details,receipt=receipt,idem=key)
        g.db.add(t); g.db.flush()
        if kind in ('withdraw','recharge','exchange','agency'): change(g.user.id,-amount,amount,kind+'_hold',f'ticket:{t.id}:hold')
        if kind=='withdraw':app.extensions['v3']['withdrawal_snapshot'](t)
        audit('ticket_created',{'id':t.id,'kind':kind})
        return {'ticket':dump(t)}
    @app.post('/api/transfer')
    @login_required
    def transfer():
        d=post_data(); key=idem(d); ref='transfer:'+key
        if g.db.scalar(select(Ledger.id).where(Ledger.reference==ref+':out')): return {'ok':True,'duplicate':True}
        throttle('transfer:'+str(g.user.id))
        if not check_password_hash(g.user.password,str(d.get('password',''))): abort(403,'পাসওয়ার্ড ঠিক নয়।')
        recipient=number(d.get('recipient'),1); amount=money(d.get('amount'))
        if recipient==g.user.id: abort(400,'নিজেকে টাকা পাঠানো যাবে না।')
        target=g.db.get(User,recipient)
        if not target or target.blocked: abort(400,'প্রাপক পাওয়া যায়নি।')
        # Stable lock order prevents reciprocal-transfer deadlocks.
        list(g.db.scalars(select(User).where(User.id.in_([g.user.id,recipient])).order_by(User.id).with_for_update()))
        change(g.user.id,-amount,0,'transfer_out',ref+':out',f'To #{recipient}')
        change(recipient,amount,0,'transfer_in',ref+':in',f'From #{g.user.id}')
        audit('transfer',{'to':recipient,'amount':amount})
        return {'ok':True}
    @app.get('/api/team')
    @login_required
    def team():
        members=g.db.scalars(select(User).where(User.referrer==g.user.id).order_by(User.id.desc()).limit(200))
        total=g.db.scalar(select(func.coalesce(func.sum(Ledger.amount),0)).where(Ledger.user_id==g.user.id,Ledger.kind.in_(['referral','signup_referral','agency_withdraw'])))
        agency=g.db.scalar(select(Ticket).where(Ticket.user_id==g.user.id,Ticket.kind=='agency',Ticket.status=='approved'))
        return {'referral_url':app.config['PUBLIC_URL']+'/?ref='+referral_code(g.user.id),'code':referral_code(g.user.id),'commission':total,'agency_approved':bool(agency),'members':[{'id':u.id,'name':u.name,'created':u.created} for u in members]}

    @app.get('/api/admin/overview')
    @admin_required
    def overview():
        return {'users':g.db.scalar(select(func.count()).select_from(User)), 'balance':g.db.scalar(select(func.coalesce(func.sum(User.balance),0))), 'held':g.db.scalar(select(func.coalesce(func.sum(User.held),0))), 'submissions':g.db.scalar(select(func.count()).select_from(Submission).where(Submission.status=='pending')), 'tickets':g.db.scalar(select(func.count()).select_from(Ticket).where(Ticket.status.in_(['pending','processing'])))}
    @app.get('/api/admin/<section>')
    @admin_required
    def admin_list(section):
        page=number(request.args.get('page','1'),1,100000); offset=(page-1)*100
        if section=='users':
            q=select(User).order_by(User.id.desc()).offset(offset).limit(100)
            return {'items':[dump(u,('password',)) for u in g.db.scalars(q)]}
        if section=='submissions':
            q=select(Submission,Task.title,User.name).join(Task,Task.id==Submission.task_id).join(User,User.id==Submission.user_id).where(Submission.status=='pending').order_by(Submission.created).offset(offset).limit(100)
            out=[]
            for s,title,name in g.db.execute(q):
                a=g.db.scalar(select(Attachment).where(Attachment.submission_id==s.id))
                out.append(dict(dump(s),title=title,name=name,mime=a.mime if a else None))
            return {'items':out}
        model={'tickets':Ticket,'tasks':Task,'audit':Audit,'rooms':Room,'exchange-routes':ExchangeRoute}.get(section)
        if not model: abort(404)
        q=select(model)
        q=q.order_by(model.id.desc()).offset(offset).limit(100)
        return {'items':[dict(dump(x),**app.extensions['v3']['spec'](x)) if section=='tasks' else dump(x) for x in g.db.scalars(q)]}
    @app.post('/api/admin/tasks')
    @admin_required
    def new_task():
        d=post_data(); slug=d.get('category'); category(slug)
        if slug in ('cobra','exchange','recharge','team','agency','live'): abort(400,'এই বিভাগে সাধারণ কাজ নয়, নিজস্ব ফিচার ব্যবহার করুন।')
        t=Task(category=slug,title=txt(d.get('title',''),160),description=txt(d.get('description',''),10000),url=https_url(d.get('url','')),reward=money(d.get('reward')),referral=money(d.get('referral','0'),True),slots=number(d.get('slots'),1,100000),min_seconds=number(d.get('min_seconds','0'),0,86400),deadline=number(d.get('deadline','0'),0,4102444800))
        g.db.add(t);g.db.flush();app.extensions['v3']['save'](t,d);audit('task_create',{'id':t.id});return {'task':dump(t)}
    @app.post('/api/admin/tasks/<int:tid>')
    @admin_required
    def task_state(tid):
        t=g.db.get(Task,tid)
        if not t: abort(404)
        enabled=boolean(post_data().get('active'))
        if enabled and t.category=='create-video':
            spec=app.extensions['v3']['spec'](t)
            if not spec['sample_url'] and not spec['sample_uploaded']:abort(400,'আগে নমুনা ভিডিও দিন।')
        t.active=enabled;audit('task_state',{'id':tid,'active':t.active});return {'ok':True}
    @app.post('/api/admin/submissions/<int:sid>')
    @admin_required
    def review(sid):
        d=post_data(); action=d.get('action')
        if action not in ('approve','reject'): abort(400)
        s=g.db.scalar(select(Submission).where(Submission.id==sid).with_for_update())
        if not s or s.status!='pending': abort(409,'এই জমাটি আর অপেক্ষমাণ নেই।')
        t=g.db.get(Task,s.task_id);u=g.db.get(User,s.user_id)
        s.note=txt(d.get('note',''),2000,False)
        notify(u.id,'কাজের রিভিউ সম্পন্ন',t.title+' — '+action,'#history')
        if action=='approve':
            snapshot=g.db.get(RewardSnapshot,s.id)
            reward=snapshot.reward if snapshot else t.reward
            referral=snapshot.referral if snapshot else t.referral
            s.status='approved';change(u.id,reward,0,'task',f'submission:{sid}',t.title)
            if u.referrer and referral:
                ref=g.db.get(User,u.referrer)
                if ref and not ref.blocked: change(ref.id,referral,0,'referral',f'referral:{sid}',f'Member #{u.id}')
        else:
            s.status='rejected'
            if t.category!='create-video':g.db.execute(update(Task).where(Task.id==t.id,Task.used>0).values(used=Task.used-1))
        audit('submission_'+action,{'id':sid});return {'ok':True}
    @app.post('/api/admin/tickets/<int:tid>')
    @admin_required
    def review_ticket(tid):
        d=post_data(); action=d.get('action'); t=g.db.scalar(select(Ticket).where(Ticket.id==tid).with_for_update())
        if not t or t.status not in ('pending','processing'): abort(409,'অনুরোধটি ইতিমধ্যে নিষ্পত্তি হয়েছে।')
        note=txt(d.get('note',''),2000,False)
        if action=='process': t.status='processing'; t.note=note
        elif action in ('approve','reject'):
            if action=='approve' and t.kind in ('deposit','withdraw','recharge','exchange') and not note: abort(400,'যাচাই/পেমেন্ট reference লিখুন।')
            if action=='approve' and t.kind=='deposit': change(t.user_id,t.amount,0,'deposit',f'ticket:{tid}:credit',note)
            if t.kind in ('withdraw','recharge','exchange','agency'):
                change(t.user_id,t.amount if action=='reject' else 0,-t.amount,t.kind+'_'+action,f'ticket:{tid}:settle',note)
            if action=='approve' and t.kind=='withdraw':app.extensions['v3']['withdrawal_pay'](t)
            t.status='approved' if action=='approve' else 'rejected';t.note=note
        else: abort(400)
        notify(t.user_id,'অনুরোধ #'+str(tid)+' আপডেট',action+' — '+note,'#ticket/'+str(tid))
        audit('ticket_'+action,{'id':tid,'note':note});return {'ok':True}
    @app.post('/api/admin/users/<int:uid>')
    @admin_required
    def user_control(uid):
        u=g.db.get(User,uid)
        if not u or u.role=='admin': abort(400,'অ্যাডমিন অ্যাকাউন্ট এখানে পরিবর্তন করা যাবে না।')
        d=post_data();u.blocked=boolean(d.get('blocked'))
        if u.blocked: g.db.execute(delete(Login).where(Login.user_id==uid))
        audit('user_block',{'id':uid,'blocked':u.blocked});return {'ok':True}
    @app.post('/api/admin/settings')
    @admin_required
    def settings():
        d=post_data()
        for key,value in d.items():
            if key not in DEFAULTS: abort(400,'অজানা সেটিং।')
            value=txt(value,10000,False)
            if key=='cobra_url': value=https_url(value)
            if key in ('min_withdraw','agency_fee'): money(value)
            if key in ('signup_member','signup_referrer','agency_signup_member','agency_signup_referrer','live_rate'):money(value,True)
            if key=='survey_daily_limit':number(value,1,100)
            if key=='video_claim_hours':number(value,1,168)
            if key=='agency_commission_percent':number(value,0,100)
            if key=='live_daily_minutes':number(value,1,1440)
            if key=='live_enabled' and value not in ('true','false'):abort(400)
            if key=='deposits_enabled' and value not in ('true','false'): abort(400)
            s=g.db.get(Setting,key)
            if not s:s=Setting(key=key);g.db.add(s)
            s.value=value
        audit('settings',{'keys':list(d)});return {'ok':True}
    @app.post('/api/admin/categories/<slug>')
    @admin_required
    def category_control(slug):
        c=g.db.get(Category,slug)
        if not c: abort(404)
        d=post_data()
        if slug=='adult' and d.get('enabled'): abort(400,'১৮+ বিভাগের কার্যক্রম এখনো নির্ধারিত হয়নি।')
        c.enabled=boolean(d.get('enabled'));c.description=txt(d.get('description',c.description),2000,False)
        audit('category',{'slug':slug,'enabled':c.enabled});return {'ok':True}
    @app.post('/api/admin/exchange-routes')
    @admin_required
    def exchange_route():
        d=post_data()
        if d.get('id'):
            r=g.db.get(ExchangeRoute,number(d['id'],1))
            if not r:abort(404)
            r.enabled=boolean(d.get('enabled'))
        else:
            try:
                rate=Decimal(str(d.get('rate','')))
                if not rate.is_finite() or rate<=0 or rate>100000 or rate*10000!=int(rate*10000):raise ValueError()
            except (InvalidOperation,ValueError):abort(400,'রেট সর্বোচ্চ ৪ দশমিক ঘরসহ দিন।')
            r=ExchangeRoute(name=txt(d.get('name',''),120),rate=int(rate*10000),fee=money(d.get('fee','0'),True),unit=txt(d.get('unit','BDT'),20));g.db.add(r)
        audit('exchange_route',{'name':r.name});return {'ok':True}

    def room_access(r):
        if not r or not r.active: abort(404,'রুমটি বন্ধ।')
        category('calls' if r.kind=='call' else 'live')
        if r.kind=='call' and g.user.id not in (r.host_id,r.guest_id): abort(403)
    @app.get('/api/rooms')
    @login_required
    def rooms():
        rows=g.db.scalars(select(Room).where(Room.active==True,or_(Room.kind=='live',Room.host_id==g.user.id,Room.guest_id==g.user.id)))
        return {'rooms':[dump(r) for r in rows]}
    @app.post('/api/admin/rooms')
    @admin_required
    def new_room():
        d=post_data(); kind=d.get('kind')
        if kind not in ('call','live'):abort(400)
        host=number(d.get('host_id'),1);guest=number(d.get('guest_id'),1) if kind=='call' else None
        if not g.db.get(User,host) or (guest and not g.db.get(User,guest)) or guest==host:abort(400,'সঠিক সদস্য আইডি দিন।')
        r=Room(title=txt(d.get('title',''),120),kind=kind,host_id=host,guest_id=guest,audio_only=True if kind=='live' else boolean(d.get('audio_only',False)));g.db.add(r);g.db.flush()
        if kind=='live':g.db.add(LiveSession(room_id=r.id,user_id=host,rate=money(setting('live_rate'),True)))
        audit('room_create',{'id':r.id});return {'room':dump(r)}
    @app.post('/api/admin/rooms/<int:rid>/close')
    @admin_required
    def close_room(rid):
        r=g.db.get(Room,rid)
        if not r:abort(404)
        app.extensions['v3']['end_live'](rid)
        r.active=False;g.db.execute(delete(Signal).where(Signal.room_id==rid));g.db.execute(delete(Peer).where(Peer.room_id==rid));audit('room_close',{'id':rid});return {'ok':True}
    @app.post('/api/rooms/<int:rid>/join')
    @login_required
    def join_room(rid):
        r=g.db.scalar(select(Room).where(Room.id==rid).with_for_update());room_access(r)
        p=g.db.scalar(select(Peer).where(Peer.room_id==rid,Peer.user_id==g.user.id))
        peers=list(g.db.scalars(select(Peer).where(Peer.room_id==rid,Peer.seen>now()-45)))
        if (not p or p.seen<=now()-45) and len(peers)>=(2 if r.kind=='call' else 5):abort(409,'রুম পূর্ণ। লাইভে সর্বোচ্চ ৫ জন।')
        if not p:p=Peer(room_id=rid,user_id=g.user.id);g.db.add(p)
        p.seen=now()
        g.db.execute(delete(Signal).where(Signal.created<now()-300))
        ice=[{'urls':os.getenv('STUN_URL','stun:stun.l.google.com:19302')}]
        if os.getenv('TURN_URL'):ice.append({'urls':os.environ['TURN_URL'],'username':os.getenv('TURN_USERNAME',''),'credential':os.getenv('TURN_PASSWORD','')})
        cursor=g.db.scalar(select(func.coalesce(func.max(Signal.id),0)).where(Signal.room_id==rid,Signal.recipient==g.user.id))
        return {'room':dump(r),'iceServers':ice,'cursor':cursor}
    @app.get('/api/rooms/<int:rid>/events')
    @login_required
    def room_events(rid):
        r=g.db.get(Room,rid);room_access(r)
        p=g.db.scalar(select(Peer).where(Peer.room_id==rid,Peer.user_id==g.user.id))
        if not p or p.seen<now()-45:abort(403,'রুমে পুনরায় যোগ দিন।')
        p.seen=now(); after=number(request.args.get('after','0'),0,2**63-1)
        events=g.db.scalars(select(Signal).where(Signal.room_id==rid,Signal.recipient==g.user.id,Signal.id>after).order_by(Signal.id).limit(200))
        peers=g.db.scalars(select(Peer).where(Peer.room_id==rid,Peer.seen>now()-45))
        return {'peers':[p.user_id for p in peers],'events':[dump(s) for s in events]}
    @app.post('/api/rooms/<int:rid>/signal')
    @login_required
    def signal(rid):
        r=g.db.get(Room,rid);room_access(r);d=post_data();recipient=number(d.get('recipient'),1)
        for uid in (g.user.id,recipient):
            p=g.db.scalar(select(Peer).where(Peer.room_id==rid,Peer.user_id==uid,Peer.seen>now()-45))
            if not p:abort(403,'সদস্য রুমে নেই।')
        if r.kind=='live' and r.host_id not in (g.user.id,recipient):abort(403)
        payload=d.get('payload')
        if not isinstance(payload,dict) or payload.get('type') not in ('offer','answer','ice'):abort(400)
        encoded=json.dumps(payload)
        if len(encoded)>50000:abort(400)
        n=g.db.scalar(select(func.count()).select_from(Signal).where(Signal.sender==g.user.id,Signal.created>now()-60))
        if n>300:abort(429)
        g.db.add(Signal(room_id=rid,sender=g.user.id,recipient=recipient,payload=encoded));return {'ok':True}
    @app.post('/api/rooms/<int:rid>/leave')
    @login_required
    def leave_room(rid):
        r=g.db.get(Room,rid)
        if r and r.kind=='live' and r.host_id==g.user.id:
            app.extensions['v3']['end_live'](rid);r.active=False
        g.db.execute(delete(Peer).where(Peer.room_id==rid,Peer.user_id==g.user.id))
        return {'ok':True}
    register_v3(app,login_required,admin_required,post_data,change,audit,notify,category,setting,money,number,txt,https_url)
    from v2 import register_v2
    register_v2(app,login_required,admin_required,post_data,change,audit,notify,category)
    return app

app=create_app()
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',default='0.0.0.0')
    parser.add_argument('--port',type=int,default=int(os.getenv('PORT','5000')))
    args,_=parser.parse_known_args()
    app.run(host=args.host,port=args.port)
