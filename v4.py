"""VIQ v4 marketplaces, money accounting, short-video rewards and audio community."""
import io,json,secrets,hashlib,subprocess,tempfile,os
from decimal import Decimal,InvalidOperation
from flask import g,request,abort,send_file
from sqlalchemy import select,func,update,delete,or_
from models import *
from v3 import values
CURRENCIES=[('USD','US Dollar','🇺🇸','$'),('EUR','Euro','🇪🇺','€'),('GBP','British Pound','🇬🇧','£'),('CHF','Swiss Franc','🇨🇭','Fr'),('JPY','Japanese Yen','🇯🇵','¥'),('CAD','Canadian Dollar','🇨🇦','C$'),('AUD','Australian Dollar','🇦🇺','A$'),('NZD','New Zealand Dollar','🇳🇿','NZ$'),('SGD','Singapore Dollar','🇸🇬','S$'),('HKD','Hong Kong Dollar','🇭🇰','HK$'),('CNY','Chinese Yuan','🇨🇳','¥'),('KRW','South Korean Won','🇰🇷','₩'),('AED','UAE Dirham','🇦🇪','د.إ'),('SAR','Saudi Riyal','🇸🇦','﷼'),('KWD','Kuwaiti Dinar','🇰🇼','د.ك'),('BHD','Bahraini Dinar','🇧🇭','د.ب'),('OMR','Omani Rial','🇴🇲','ر.ع.'),('QAR','Qatari Riyal','🇶🇦','ر.ق'),('SEK','Swedish Krona','🇸🇪','kr'),('NOK','Norwegian Krone','🇳🇴','kr')]
GIFTS={'rose':{'name':'Rose','coins':100,'icon':'🌹'},'heart':{'name':'Love','coins':500,'icon':'💖'},'crown':{'name':'Crown','coins':2000,'icon':'👑'},'rocket':{'name':'Rocket','coins':10000,'icon':'🚀'},'galaxy':{'name':'Galaxy','coins':50000,'icon':'🌌'}}
MARKETS={'pages':'Facebook Page','groups':'Facebook Group','gmail':'Gmail'}
SETTLED=('completed','refunded')

def register_v4(app,login_required,admin_required,data,change,audit,notify,category,money,number,txt,https_url):
    def lock_users(*ids):
        return list(g.db.scalars(select(User).where(User.id.in_(sorted(set(ids)))).order_by(User.id).with_for_update()))
    def operation(d,scope):
        key=txt(d.get('key',''),80)
        if len(key)<16 or not all(c.isalnum() or c in '-_' for c in key):abort(400,'সঠিক request key প্রয়োজন।')
        key=f'{g.user.id}:{scope}:{key}'
        fp=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        old=g.db.get(Operation,key)
        if old and old.fingerprint!=fp:abort(409,'একই অনুরোধের তথ্য পরিবর্তিত হয়েছে।')
        return key,fp,json.loads(old.result) if old else None
    def receipt(key,fp,result):g.db.add(Operation(key=key,fingerprint=fp,result=json.dumps(result)));return result
    def image_owned(aid):
        a=g.db.get(MediaAsset,number(aid,1))
        if not a or a.owner_id!=g.user.id or not a.mime.startswith('image/'):abort(400,'নিজের আপলোড করা ছবি নির্বাচন করুন।')
        return a.id
    def coin_wallet(uid):
        w=g.db.get(CoinWallet,uid)
        if not w:w=CoinWallet(user_id=uid,balance=0);g.db.add(w);g.db.flush()
        return w
    def coins(uid,delta,ref,note):
        w=coin_wallet(uid)
        if w.balance+delta<0:abort(409,'পর্যাপ্ত কয়েন নেই।')
        w.balance+=delta;g.db.add(CoinEntry(user_id=uid,delta=delta,reference=ref,note=note))
    def profile(uid):
        p=g.db.get(LiveProfile,uid);u=g.db.get(User,uid)
        return {'id':uid,'name':p.name if p else u.name,'bio':p.bio if p else '', 'avatar_id':p.avatar_id if p else None}
    def room(rid):
        r=g.db.get(Room,rid)
        if not r or not r.active or r.kind!='live':abort(404,'লাইভ রুম বন্ধ।')
        category('live');return r
    def present(rid):
        r=room(rid)
        if not g.db.scalar(select(Peer.id).where(Peer.room_id==rid,Peer.user_id==g.user.id,Peer.seen>now()-45)):abort(403,'আগে রুমে যোগ দিন।')
        return r
    def deal_access(did,lock=False):
        q=select(Deal).where(Deal.id==did)
        d=g.db.scalar(q.with_for_update() if lock else q)
        if not d or (g.user.role!='admin' and g.user.id not in (d.buyer_id,d.seller_id)):abort(404)
        return d

    @app.post('/api/media')
    @login_required
    def upload_media():
        f=request.files.get('file');blob=f.read(8*1024*1024+1) if f else b''
        if not blob or len(blob)>8*1024*1024:abort(400,'ফাইল ৮ MB-এর মধ্যে দিন।')
        mime='image/png' if blob.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg' if blob.startswith(b'\xff\xd8\xff') else None
        if not mime and g.user.role=='admin' and blob[4:8]==b'ftyp':mime='video/mp4'
        if not mime:abort(400,'PNG/JPG ছবি; অ্যাডমিন ভিডিওর জন্য MP4 দিন।')
        lock_users(g.user.id)
        size=g.db.scalar(select(func.coalesce(func.sum(func.length(MediaAsset.data)),0)).where(MediaAsset.owner_id==g.user.id))
        if size+len(blob)>256*1024*1024:abort(400,'মিডিয়ার ২৫৬ MB সীমা পূর্ণ।')
        a=MediaAsset(owner_id=g.user.id,data=blob,mime=mime);g.db.add(a);g.db.flush();return {'id':a.id,'mime':mime}
    @app.get('/api/media/<int:aid>')
    @login_required
    def media(aid):
        a=g.db.get(MediaAsset,aid)
        if not a:abort(404)
        # Public-to-members assets only after attached to a visible application record.
        linked=g.db.scalar(select(Listing.id).where(Listing.image_id==aid,Listing.status!='hidden').limit(1)) or g.db.scalar(select(LiveProfile.user_id).where(LiveProfile.avatar_id==aid).limit(1)) or g.db.scalar(select(Clip.id).where(Clip.asset_id==aid,Clip.active==True).limit(1))
        if a.owner_id!=g.user.id and g.user.role!='admin' and not linked:abort(404)
        return send_file(io.BytesIO(a.data),mimetype=a.mime,conditional=True,etag=hashlib.sha256(a.data).hexdigest(),download_name='viq-media.'+('mp4' if a.mime.startswith('video') else 'png' if a.mime=='image/png' else 'jpg'))

    @app.post('/api/admin/clips')
    @admin_required
    def create_clip():
        d=data();a=g.db.get(MediaAsset,number(d.get('asset_id'),1))
        if not a or a.owner_id!=g.user.id or a.mime!='video/mp4':abort(400,'নিজের MP4 ভিডিও আপলোড করুন।')
        # Validate duration on server; never trust a browser-supplied duration.
        path=None
        try:
            import imageio_ffmpeg
            with tempfile.NamedTemporaryFile(suffix='.mp4',delete=False) as f:f.write(a.data);path=f.name
            result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-i',path],capture_output=True,text=True,timeout=20)
            import re
            match=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',result.stderr)
            duration=int(match[1])*3600+int(match[2])*60+float(match[3]) if match else 0
            if not 60<=duration<=61:abort(400,'ভিডিও ৬০ থেকে ৬১ সেকেন্ডের MP4 হতে হবে।')
        finally:
            if path:os.unlink(path)
        c=Clip(title=txt(d.get('title'),160),caption=txt(d.get('caption',''),2000,False),asset_id=a.id);g.db.add(c);g.db.flush();audit('clip_publish',{'id':c.id});return {'id':c.id}
    @app.get('/api/clips')
    @login_required
    def clips():
        category('watch-video')
        seen=list(g.db.scalars(select(WatchedClip.clip_id).where(WatchedClip.user_id==g.user.id)))
        rows=g.db.scalars(select(Clip).where(Clip.active==True,Clip.id.not_in(seen)).order_by(Clip.id).limit(100))
        return {'items':[values(c) for c in rows],'completed':len(seen),'batch_progress':len(seen)%30,'earned':len(seen)//30*1500}
    @app.post('/api/admin/clips/<int:cid>')
    @admin_required
    def clip_toggle(cid):
        c=g.db.get(Clip,cid)
        if not c:abort(404)
        c.active=not c.active;audit('clip_toggle',{'id':cid,'active':c.active});return {'ok':True}
    @app.get('/api/admin/clips')
    @admin_required
    def clip_list():return {'items':[values(c) for c in g.db.scalars(select(Clip).order_by(Clip.id.desc()).limit(200))]}
    @app.post('/api/clips/<int:cid>/start')
    @login_required
    def watch_start(cid):
        category('watch-video');lock_users(g.user.id);c=g.db.get(Clip,cid)
        if not c or not c.active:abort(404)
        if g.db.scalar(select(WatchedClip.id).where(WatchedClip.user_id==g.user.id,WatchedClip.clip_id==cid)):abort(409,'এই ভিডিও আগেই গণনা হয়েছে।')
        w=g.db.get(WatchSession,g.user.id)
        if not w:w=WatchSession(user_id=g.user.id,clip_id=cid,token=secrets.token_urlsafe(24));g.db.add(w)
        w.clip_id=cid;w.token=secrets.token_urlsafe(24);w.seconds=0;w.position=0;w.last_tick=now();w.started=now()
        return {'token':w.token}
    @app.post('/api/clips/<int:cid>/tick')
    @login_required
    def watch_tick(cid):
        category('watch-video');lock_users(g.user.id);d=data();w=g.db.get(WatchSession,g.user.id)
        if not w or w.clip_id!=cid or not secrets.compare_digest(w.token,str(d.get('token',''))):abort(409,'ভিডিও সেশন বদলেছে। আবার শুরু করুন।')
        c=g.db.get(Clip,cid)
        if not c or not c.active:abort(409,'ভিডিও বন্ধ করা হয়েছে।')
        pos=number(d.get('position'),0,61);gap=now()-w.last_tick;delta=pos-w.position
        if d.get('playing') is not True or d.get('visible') is not True or gap>8 or delta<0 or delta>gap+2:
            g.db.delete(w);return {'reset':True,'seconds':0}
        if gap>0:w.seconds=min(pos,now()-w.started)
        w.position=pos;w.last_tick=now()
        if w.seconds>=60 and pos>=60 and now()-w.started>=60:
            if not g.db.scalar(select(WatchedClip.id).where(WatchedClip.user_id==g.user.id,WatchedClip.clip_id==cid)):
                g.db.add(WatchedClip(user_id=g.user.id,clip_id=cid));g.db.flush()
                total=g.db.scalar(select(func.count()).select_from(WatchedClip).where(WatchedClip.user_id==g.user.id))
                if total%30==0:change(g.user.id,1500,0,'watch_reward',f'watch:{g.user.id}:batch:{total//30}','৩০টি সম্পূর্ণ ভিডিও')
            g.db.delete(w);return {'complete':True,'seconds':60}
        return {'seconds':w.seconds,'complete':False}
    @app.post('/api/clips/abandon')
    @login_required
    def watch_abandon():
        lock_users(g.user.id);w=g.db.get(WatchSession,g.user.id)
        if w and secrets.compare_digest(w.token,str(data().get('token',''))):g.db.delete(w)
        return {'ok':True}

    @app.get('/api/fx')
    @login_required
    def fx():
        category('exchange');hold=list(g.db.scalars(select(Holding).where(Holding.user_id==g.user.id)))
        return {'currencies':[values(c) for c in g.db.scalars(select(Currency).order_by(Currency.code))], 'holdings':[values(h) for h in hold],'trades':[values(t) for t in g.db.scalars(select(CurrencyTrade).where(CurrencyTrade.user_id==g.user.id).order_by(CurrencyTrade.id.desc()).limit(100))]}
    @app.post('/api/admin/fx/<code>')
    @admin_required
    def set_rate(code):
        c=g.db.scalar(select(Currency).where(Currency.code==code).with_for_update())
        if not c:abort(404)
        d=data();c.rate=money(d.get('rate'));c.enabled=d.get('enabled') is True
        audit('fx_rate',{'code':code,'rate':c.rate,'enabled':c.enabled});return {'ok':True}
    @app.post('/api/fx/trade')
    @login_required
    def trade():
        category('exchange');d=data();lock_users(g.user.id);key,fp,old=operation(d,'fx')
        if old:return old
        c=g.db.scalar(select(Currency).where(Currency.code==d.get('code')).with_for_update())
        if not c or not c.enabled or c.rate<=0:abort(400,'এই কারেন্সি এখন বন্ধ।')
        if number(d.get('rate'),1,100000000)!=c.rate:abort(409,'রেট বদলেছে। নতুন রেট দেখে নিশ্চিত করুন।')
        try:
            q=Decimal(str(d.get('quantity')));u=q*1000000
            if not q.is_finite() or u!=int(u) or not 0<u<=10**12:raise ValueError()
            units=int(u)
        except (ValueError,InvalidOperation,OverflowError):abort(400,'সর্বোচ্চ ৬ দশমিক ঘরসহ পরিমাণ দিন।')
        h=g.db.scalar(select(Holding).where(Holding.user_id==g.user.id,Holding.code==c.code))
        if not h:h=Holding(user_id=g.user.id,code=c.code,units=0,cost=0);g.db.add(h)
        side=d.get('side')
        if side=='buy':
            amount=(units*c.rate+999999)//1000000
            change(g.user.id,-amount,0,'fx_buy',key,c.code);h.units+=units;h.cost+=amount
        elif side=='sell':
            if h.units<units:abort(409,'পর্যাপ্ত কারেন্সি নেই।')
            amount=units*c.rate//1000000
            if amount<=0:abort(400,'বিক্রির পরিমাণ অন্তত ১ পয়সা হতে হবে।')
            h.cost-=h.cost*units//h.units;h.units-=units
            change(g.user.id,amount,0,'fx_sell',key,c.code)
        else:abort(400)
        t=CurrencyTrade(user_id=g.user.id,code=c.code,side=side,units=units,amount=amount,rate=c.rate);g.db.add(t);g.db.flush();audit('fx_trade',{'id':t.id})
        return receipt(key,fp,{'id':t.id,'amount':amount})

    @app.get('/api/community/profile')
    @login_required
    def own_profile():
        w=g.db.get(CoinWallet,g.user.id)
        return {'profile':profile(g.user.id),'coins':w.balance if w else 0,'gifts':GIFTS,'ledger':[values(x) for x in g.db.scalars(select(CoinEntry).where(CoinEntry.user_id==g.user.id).order_by(CoinEntry.id.desc()).limit(100))]}
    @app.post('/api/community/profile')
    @login_required
    def update_profile():
        d=data();lock_users(g.user.id);p=g.db.get(LiveProfile,g.user.id)
        if not p:p=LiveProfile(user_id=g.user.id,name=g.user.name);g.db.add(p)
        p.name=txt(d.get('name'),80);p.bio=txt(d.get('bio',''),300,False)
        if d.get('avatar_id'):p.avatar_id=image_owned(d['avatar_id'])
        return {'ok':True}
    @app.post('/api/coins/convert')
    @login_required
    def convert():
        d=data();lock_users(g.user.id);key,fp,old=operation(d,'coins')
        if old:return old
        n=number(d.get('coins'),10,10**9)
        if n%10:abort(400,'কয়েনের পরিমাণ ১০-এর গুণিতক দিন।')
        side=d.get('side')
        if side=='buy':change(g.user.id,-n//10,0,'coin_buy',key);coins(g.user.id,n,key,'BDT → coins')
        elif side=='sell':coins(g.user.id,-n,key,'Coins → BDT');change(g.user.id,n//10,0,'coin_sell',key)
        else:abort(400)
        return receipt(key,fp,{'coins':n,'amount':n//10})
    @app.get('/api/community/rooms')
    @login_required
    def live_rooms():
        category('live');out=[]
        for r in g.db.scalars(select(Room).where(Room.kind=='live',Room.active==True).order_by(Room.id.desc()).limit(100)):
            n=g.db.scalar(select(func.count()).select_from(Peer).where(Peer.room_id==r.id,Peer.seen>now()-45))
            if n:out.append(values(r)|{'host':profile(r.host_id),'online':n})
        return {'items':out}
    @app.get('/api/community/rooms/<int:rid>')
    @login_required
    def stage(rid):
        r=present(rid);peers=list(g.db.scalars(select(Peer).where(Peer.room_id==rid,Peer.seen>now()-45)));ids=[p.user_id for p in peers]
        seats=list(g.db.scalars(select(Seat).where(Seat.room_id==rid,Seat.user_id.in_(ids))))
        after=number(request.args.get('after','0'),0,2**63-1)
        msgs=list(g.db.scalars(select(RoomMessage).where(RoomMessage.room_id==rid,RoomMessage.id>after).order_by(RoomMessage.id.desc()).limit(100)))
        return {'room':values(r),'people':[profile(uid) for uid in ids],'seats':[values(s) for s in seats],'messages':[values(m)|{'name':profile(m.sender)['name']} for m in reversed(msgs)],'gifts':GIFTS}
    @app.post('/api/community/rooms/<int:rid>/seat')
    @login_required
    def seat(rid):
        r=g.db.scalar(select(Room).where(Room.id==rid).with_for_update());present(rid);n=number(data().get('number'),0,10)
        active=list(g.db.scalars(select(Peer.user_id).where(Peer.room_id==rid,Peer.seen>now()-45)))
        g.db.execute(delete(Seat).where(Seat.room_id==rid,Seat.user_id.not_in(active)))
        old=g.db.scalar(select(Seat).where(Seat.room_id==rid,Seat.user_id==g.user.id))
        if n==0:
            if old:g.db.delete(old)
        else:
            taken=g.db.scalar(select(Seat).where(Seat.room_id==rid,Seat.number==n))
            if taken and taken.user_id!=g.user.id:abort(409,'এই আসনটি পূর্ণ।')
            if old:old.number=n
            else:g.db.add(Seat(room_id=rid,number=n,user_id=g.user.id))
        return {'ok':True}
    @app.post('/api/community/rooms/<int:rid>/message')
    @login_required
    def room_message(rid):
        present(rid);d=data();m=RoomMessage(room_id=rid,sender=g.user.id,body=txt(d.get('body'),1000));g.db.add(m);return {'ok':True}
    @app.post('/api/community/rooms/<int:rid>/gift')
    @login_required
    def gift(rid):
        present(rid);d=data();uid=number(d.get('recipient'),1);lock_users(g.user.id,uid);key,fp,old=operation(d,'gift')
        if old:return old
        if uid==g.user.id or not g.db.scalar(select(Peer.id).where(Peer.room_id==rid,Peer.user_id==uid,Peer.seen>now()-45)):abort(400,'রুমের অন্য সদস্য নির্বাচন করুন।')
        gift=d.get('gift')
        if gift not in GIFTS:abort(400)
        n=GIFTS[gift]['coins'];coins(g.user.id,-n,key+':out',gift);coins(uid,n,key+':in',gift)
        m=RoomMessage(room_id=rid,sender=g.user.id,recipient=uid,gift=gift,kind='gift',amount=n,body=GIFTS[gift]['name']);g.db.add(m);g.db.flush()
        return receipt(key,fp,{'id':m.id,'coins':n})

    @app.get('/api/market/<slug>')
    @login_required
    def market(slug):
        if slug not in MARKETS:abort(404)
        category(slug);q=select(Listing).where(Listing.category==slug,Listing.status=='live')
        term=request.args.get('q','')[:100].strip()
        if term:q=q.where(Listing.title.ilike('%'+term.replace('%','\\%').replace('_','\\_')+'%',escape='\\'))
        page=number(request.args.get('page','1'),1,100000)
        rows=g.db.scalars(q.order_by(Listing.id.desc()).offset((page-1)*30).limit(30))
        return {'items':[values(l)|{'seller':g.db.get(User,l.seller_id).name} for l in rows],'page':page}
    @app.post('/api/market/<slug>')
    @login_required
    def listing(slug):
        if slug not in MARKETS:abort(404)
        category(slug);d=data();url=https_url(d.get('url',''))
        if slug in ('pages','groups'):
            from urllib.parse import urlparse
            host=(urlparse(url).hostname or '').lower()
            if host!='facebook.com' and not host.endswith('.facebook.com'):abort(400,'Facebook লিংক দিন।')
        l=Listing(seller_id=g.user.id,category=slug,title=txt(d.get('title'),160),description=txt(d.get('description'),5000),url=url,image_id=image_owned(d.get('image_id')),price=money(d.get('price')));g.db.add(l);g.db.flush();audit('listing_create',{'id':l.id});return {'id':l.id}
    @app.post('/api/market/listings/<int:lid>/hide')
    @login_required
    def hide(lid):
        l=g.db.scalar(select(Listing).where(Listing.id==lid).with_for_update())
        if not l or (l.seller_id!=g.user.id and g.user.role!='admin'):abort(403)
        if l.status!='live':abort(409,'চলমান ডিল থাকলে পোস্ট সরানো যাবে না।')
        l.status='hidden';audit('listing_hide',{'id':lid});return {'ok':True}
    @app.post('/api/market/listings/<int:lid>/deal')
    @login_required
    def start_deal(lid):
        d=data();l=g.db.scalar(select(Listing).where(Listing.id==lid).with_for_update());lock_users(g.user.id)
        key,fp,old=operation(d,'deal')
        if old:return old
        if not l or l.status!='live':abort(409,'পোস্টটি আর বিক্রির জন্য খোলা নেই।')
        category(l.category)
        if l.seller_id==g.user.id:abort(400,'নিজের পোস্ট কেনা যাবে না।')
        if g.db.get(User,l.seller_id).blocked:abort(409,'বিক্রেতার অ্যাকাউন্ট বন্ধ।')
        if number(d.get('price'),1,100000000)!=l.price:abort(409,'দাম পরিবর্তিত হয়েছে।')
        deal=Deal(listing_id=l.id,buyer_id=g.user.id,seller_id=l.seller_id,category=l.category,title=l.title,amount=l.price);g.db.add(deal);g.db.flush()
        change(g.user.id,-l.price,l.price,'deal_escrow',f'deal:{deal.id}:hold',l.title);l.status='reserved'
        notify(l.seller_id,'নতুন ডিল',l.title,'#deal/'+str(deal.id));audit('deal_start',{'id':deal.id})
        return receipt(key,fp,{'id':deal.id})
    @app.get('/api/deals')
    @login_required
    def deals():
        q=select(Deal)
        if g.user.role!='admin':q=q.where(or_(Deal.buyer_id==g.user.id,Deal.seller_id==g.user.id))
        slug=request.args.get('category')
        if slug in MARKETS:q=q.where(Deal.category==slug)
        rows=g.db.scalars(q.order_by(Deal.id.desc()).limit(200));return {'items':[values(d) for d in rows]}
    @app.get('/api/deals/<int:did>')
    @login_required
    def get_deal(did):
        d=deal_access(did);msgs=g.db.scalars(select(DealMessage).where(DealMessage.deal_id==did).order_by(DealMessage.id.desc()).limit(200))
        return {'deal':values(d),'buyer':g.db.get(User,d.buyer_id).name,'seller':g.db.get(User,d.seller_id).name,'admin_profile':MARKETS[d.category]+' Admin','messages':[values(m)|{'name':MARKETS[d.category]+' Admin' if g.db.get(User,m.sender).role=='admin' else g.db.get(User,m.sender).name,'admin':g.db.get(User,m.sender).role=='admin'} for m in reversed(list(msgs))]}
    @app.post('/api/deals/<int:did>/message')
    @login_required
    def deal_message(did):
        d=deal_access(did)
        body=txt(data().get('body'),4000);g.db.add(DealMessage(deal_id=did,sender=g.user.id,body=body));return {'ok':True}
    @app.post('/api/deals/<int:did>/action')
    @login_required
    def deal_action(did):
        d=deal_access(did,True);l=g.db.scalar(select(Listing).where(Listing.id==d.listing_id).with_for_update());body=data();act=body.get('action');note=txt(body.get('note',''),2000,True)
        if d.status in SETTLED:abort(409,'ডিল নিষ্পত্তি হয়েছে।')
        if act in ('release','refund'):
            if g.user.role!='admin':abort(403,'শুধু অ্যাডমিন টাকা ছাড়তে পারেন।')
            if act=='release' and d.status not in ('delivered','confirmed','disputed'):abort(409,'হস্তান্তর যাচাই ছাড়া টাকা ছাড়া যাবে না।')
            lock_users(d.buyer_id,d.seller_id)
            if act=='release':
                change(d.buyer_id,0,-d.amount,'deal_settle',f'deal:{did}:settle',note);change(d.seller_id,d.amount,0,'deal_sale',f'deal:{did}:sale',note);d.status='completed';l.status='sold'
            else:
                change(d.buyer_id,d.amount,-d.amount,'deal_refund',f'deal:{did}:settle',note)
                # A cancelled listing may already have a different active deal. Do not overwrite it.
                if d.status!='cancel_requested':l.status='live'
                d.status='refunded'
        elif act=='cancel':
            if d.status=='cancel_requested':abort(409,'বাতিলের অনুরোধ আছে।')
            d.status='cancel_requested';l.status='live'
        elif act=='delivered' and g.user.id==d.seller_id and d.status in ('pending','processing'):d.status='delivered'
        elif act=='confirm' and g.user.id==d.buyer_id and d.status=='delivered':d.status='confirmed'
        elif act=='dispute' and d.status!='cancel_requested':d.status='disputed'
        elif act=='process' and g.user.role=='admin' and d.status=='pending':d.status='processing'
        else:abort(400,'এই অবস্থায় কাজটি করা যাবে না।')
        g.db.add(DealMessage(deal_id=did,sender=g.user.id,body=act+' — '+note));audit('deal_'+act,{'id':did});return {'ok':True}
    @app.get('/api/admin/market-profiles')
    @admin_required
    def admin_profiles():
        out=[]
        for slug,name in MARKETS.items():
            counts=dict(g.db.execute(select(Deal.status,func.count()).where(Deal.category==slug).group_by(Deal.status)).all())
            held=g.db.scalar(select(func.coalesce(func.sum(Deal.amount),0)).where(Deal.category==slug,Deal.status.not_in(SETTLED)))
            out.append({'slug':slug,'name':name+' Admin','counts':counts,'held':held})
        return {'items':out}
