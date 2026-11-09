"""VIQ v2 additions. Additive tables; no destructive v1 migration."""
import io, csv, json
from flask import g, request, jsonify, abort, Response
from sqlalchemy import select, update, delete, func, or_, case
from models import *

def register_v2(app,login_required,admin_required,data,change,audit,notify,category):
    def integer(v,default=1):
        try:n=int(v or default)
        except (TypeError,ValueError):abort(400,'সঠিক সংখ্যা দিন।')
        if n<1 or n>100000:abort(400,'সঠিক সংখ্যা দিন।')
        return n
    def ticket_access(tid):
        t=g.db.get(Ticket,tid)
        if not t or (t.user_id!=g.user.id and g.user.role!='admin'):abort(404)
        return t
    def task_item(t,favorites):
        return {c.name:getattr(t,c.name) for c in t.__table__.columns}|{'saved':t.id in favorites}

    @app.get('/ready')
    def ready():
        try:
            g.db.scalar(select(func.count()).select_from(Category))
            return {'ready':True,'version':'2.0.0'}
        except Exception:return {'ready':False},503

    @app.get('/api/dashboard')
    @login_required
    def dashboard():
        counts=dict(g.db.execute(select(Submission.status,func.count()).where(Submission.user_id==g.user.id).group_by(Submission.status)).all())
        earnings=g.db.scalar(select(func.coalesce(func.sum(Ledger.amount),0)).where(Ledger.user_id==g.user.id,Ledger.kind.in_(['task','referral'])))
        today=g.db.scalar(select(func.coalesce(func.sum(Ledger.amount),0)).where(Ledger.user_id==g.user.id,Ledger.kind.in_(['task','referral']),Ledger.created>=now()-86400))
        unread=g.db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id==g.user.id,Notification.read==False))
        active=g.db.scalar(select(func.count()).select_from(Task).join(Category,Category.slug==Task.category).where(Category.enabled==True,Task.active==True,Task.used<Task.slots,or_(Task.deadline==0,Task.deadline>=now())))
        return {'counts':counts,'earned':earnings,'last_24h':today,'unread':unread,'available':active}

    @app.get('/api/discover')
    @login_required
    def discover():
        page=integer(request.args.get('page')); q=request.args.get('q','').strip()[:100]
        favorites=set(g.db.scalars(select(Favorite.task_id).where(Favorite.user_id==g.user.id)))
        query=select(Task).join(Category,Category.slug==Task.category).where(Category.enabled==True,Task.category!='adult',Task.active==True,Task.used<Task.slots,or_(Task.deadline==0,Task.deadline>=now()))
        if q:
            escaped=q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
            query=query.where(or_(Task.title.ilike('%'+escaped+'%',escape='\\'),Task.description.ilike('%'+escaped+'%',escape='\\')))
        slug=request.args.get('category')
        if slug:query=query.where(Task.category==slug)
        if request.args.get('saved')=='1':query=query.where(Task.id.in_(favorites))
        order={'reward':Task.reward.desc(),'ending':case((Task.deadline==0,4102444800),else_=Task.deadline).asc(),'new':Task.id.desc()}.get(request.args.get('sort'),Task.id.desc())
        total=g.db.scalar(select(func.count()).select_from(query.subquery()))
        rows=g.db.scalars(query.order_by(order,Task.id.desc()).offset((page-1)*20).limit(20))
        return {'items':[task_item(t,favorites) for t in rows],'total':total,'page':page}

    @app.post('/api/tasks/<int:tid>/save')
    @login_required
    def save_task(tid):
        t=g.db.get(Task,tid)
        if not t:abort(404)
        category(t.category)
        value=data().get('saved')
        if type(value)is not bool:abort(400,'true/false প্রয়োজন।')
        f=g.db.scalar(select(Favorite).where(Favorite.user_id==g.user.id,Favorite.task_id==tid))
        if value and not f:g.db.add(Favorite(user_id=g.user.id,task_id=tid))
        if not value and f:g.db.delete(f)
        return {'saved':value}

    @app.get('/api/notifications')
    @login_required
    def notifications():
        page=integer(request.args.get('page'))
        rows=g.db.scalars(select(Notification).where(Notification.user_id==g.user.id).order_by(Notification.id.desc()).offset((page-1)*50).limit(50))
        return {'items':[{c.name:getattr(n,c.name) for c in n.__table__.columns} for n in rows]}

    @app.post('/api/notifications/read')
    @login_required
    def read_notifications():
        g.db.execute(update(Notification).where(Notification.user_id==g.user.id).values(read=True))
        return {'ok':True}

    @app.get('/api/tickets/<int:tid>')
    @login_required
    def ticket_detail(tid):
        t=ticket_access(tid)
        rows=g.db.execute(select(TicketMessage,User.name,User.role).join(User,User.id==TicketMessage.user_id).where(TicketMessage.ticket_id==tid).order_by(TicketMessage.id.desc()).limit(100)).all()
        return {'ticket':{c.name:getattr(t,c.name) for c in t.__table__.columns},'messages':[{'id':m.id,'name':name,'role':role,'body':m.body,'mine':m.user_id==g.user.id,'created':m.created} for m,name,role in reversed(rows)]}

    @app.post('/api/tickets/<int:tid>/message')
    @login_required
    def message(tid):
        t=ticket_access(tid); body=data().get('body')
        if not isinstance(body,str) or not 1<=len(body.strip())<=2000:abort(400,'১–২০০০ অক্ষরের বার্তা দিন।')
        g.db.add(TicketMessage(ticket_id=tid,user_id=g.user.id,body=body.strip()))
        if g.user.role=='admin':notify(t.user_id,'সাপোর্ট উত্তর দিয়েছে',body[:120],'#ticket/'+str(tid))
        else:
            for uid in g.db.scalars(select(User.id).where(User.role=='admin',User.blocked==False)):notify(uid,'নতুন সাপোর্ট বার্তা',f'অনুরোধ #{tid}','#ticket/'+str(tid))
        return {'ok':True}

    @app.post('/api/tickets/<int:tid>/cancel')
    @login_required
    def cancel(tid):
        t=g.db.scalar(select(Ticket).where(Ticket.id==tid,Ticket.user_id==g.user.id).with_for_update())
        if not t:abort(404)
        if t.status!='pending':abort(409,'শুধু অপেক্ষমাণ অনুরোধ বাতিল করা যায়।')
        if t.kind in ('withdraw','recharge','exchange'):change(t.user_id,t.amount,-t.amount,t.kind+'_cancel',f'ticket:{tid}:settle','সদস্য বাতিল করেছেন')
        t.status='cancelled';t.note='সদস্য নিজে বাতিল করেছেন।'
        audit('ticket_cancel',{'id':tid});notify(t.user_id,'অনুরোধ বাতিল হয়েছে',f'#{tid}','#ticket/'+str(tid))
        return {'ok':True}

    @app.get('/api/sessions')
    @login_required
    def sessions():
        rows=g.db.scalars(select(Login).where(Login.user_id==g.user.id,Login.expires>now()).order_by(Login.expires.desc()))
        return {'items':[{'current':r.token==g.login.token,'expires':r.expires} for r in rows]}

    @app.post('/api/sessions/revoke-others')
    @login_required
    def revoke():
        g.db.execute(delete(Login).where(Login.user_id==g.user.id,Login.token!=g.login.token))
        audit('revoke_other_sessions',{})
        return {'ok':True}

    @app.get('/api/wallet/export')
    @login_required
    def export_wallet():
        # User-controlled notes are protected against spreadsheet formula injection.
        def safe(v):
            v=str(v or '')
            return "'"+v if v.lstrip().startswith(('=','+','-','@','\t','\r')) else v
        out=io.StringIO();writer=csv.writer(out)
        writer.writerow(['ID','UTC epoch','Type','Balance change BDT','Held change BDT','Note'])
        for l in g.db.scalars(select(Ledger).where(Ledger.user_id==g.user.id).order_by(Ledger.id.desc()).limit(10000)):
            writer.writerow([l.id,l.created,l.kind,f'{l.amount/100:.2f}',f'{l.held_delta/100:.2f}',safe(l.note)])
        return Response('\ufeff'+out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename="VIQ-transactions.csv"'})

    @app.get('/api/admin/reconciliation')
    @admin_required
    def reconcile():
        sums=select(Ledger.user_id,func.sum(Ledger.amount).label('balance'),func.sum(Ledger.held_delta).label('held')).group_by(Ledger.user_id).subquery()
        rows=g.db.execute(select(User.id,User.balance,User.held,func.coalesce(sums.c.balance,0),func.coalesce(sums.c.held,0)).outerjoin(sums,sums.c.user_id==User.id)).all()
        mismatch=[{'user_id':u,'balance':b,'held':h,'ledger_balance':lb,'ledger_held':lh} for u,b,h,lb,lh in rows if b!=lb or h!=lh]
        return {'checked':len(rows),'mismatches':mismatch,'ok':not mismatch,'checked_at':now()}

    @app.get('/api/admin/search-users')
    @admin_required
    def search_users():
        q=request.args.get('q','').strip()[:100]
        if not q:return {'items':[]}
        escaped=q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        conditions=[User.name.ilike('%'+escaped+'%',escape='\\'),User.email.ilike('%'+escaped+'%',escape='\\')]
        if q.isdigit():conditions.append(User.id==int(q))
        users=g.db.scalars(select(User).where(or_(*conditions)).limit(30))
        return {'items':[{'id':u.id,'name':u.name,'email':u.email,'blocked':u.blocked,'balance':u.balance,'held':u.held} for u in users]}
