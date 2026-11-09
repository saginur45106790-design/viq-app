import os, sys, getpass
from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
from app import app, CATEGORIES, DEFAULTS
from models import Base, User, Category, Setting, Login

def init():
    engine=app.extensions['engine'];Base.metadata.create_all(engine)
    with Session(engine) as db, db.begin():
        for slug,name,desc in CATEGORIES:
            if not db.get(Category,slug): db.add(Category(slug=slug,name=name,description=desc,enabled=slug!='adult'))
        for k,v in DEFAULTS.items():
            if not db.get(Setting,k):db.add(Setting(key=k,value=v))
        if not db.scalar(select(User).where(User.role=='admin')):
            email=os.getenv('ADMIN_EMAIL','').strip().lower(); pw=os.getenv('ADMIN_PASSWORD','')
            if '@' not in email or len(pw)<16:raise RuntimeError('Set ADMIN_EMAIL and ADMIN_PASSWORD (16+ characters) first.')
            if db.scalar(select(User).where(User.email==email)):raise RuntimeError('Admin email already belongs to an existing user.')
            db.add(User(name='VIQ Admin',email=email,password=generate_password_hash(pw),role='admin'))
    print('VIQ schema and administrator ready. Existing passwords were not changed.')

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='reset-password':
        email=input('Account email: ').strip().lower();pw=getpass.getpass('New password (16+ characters): ')
        if len(pw)<16:raise SystemExit('Password too short')
        with Session(app.extensions['engine']) as db,db.begin():
            u=db.scalar(select(User).where(User.email==email))
            if not u:raise SystemExit('Not found')
            u.password=generate_password_hash(pw)
            from sqlalchemy import delete
            db.execute(delete(Login).where(Login.user_id==u.id))
        print('Password reset; sessions revoked.')
    else:init()
