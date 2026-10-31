import os,sqlite3,time,secrets,hashlib,hmac
from pathlib import Path
from datetime import date
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import HTMLResponse,JSONResponse
from pydantic import BaseModel,Field
from itsdangerous import URLSafeTimedSerializer,BadSignature
from fastapi.staticfiles import StaticFiles

USER=os.getenv("ADMIN_USER","")
PASSWORD=os.getenv("ADMIN_PASSWORD","")
SECRET=os.getenv("SESSION_SECRET","")
if not USER or len(PASSWORD)<12 or len(SECRET)<32: raise RuntimeError("Configure ADMIN_USER, ADMIN_PASSWORD and SESSION_SECRET")
secure=os.getenv("COOKIE_SECURE","true").lower()=="true"
signer=URLSafeTimedSerializer(SECRET,salt="fitness-v1")
dbpath=os.getenv("DB_PATH","/tmp/fitness.db")
Path(dbpath).parent.mkdir(parents=True,exist_ok=True)
app=FastAPI()
def connect():
 c=sqlite3.connect(dbpath);c.row_factory=sqlite3.Row;return c
with connect() as c:
 c.execute("CREATE TABLE IF NOT EXISTS sets(id INTEGER PRIMARY KEY,date TEXT,exercise TEXT,weight REAL,reps INTEGER)")
 c.execute("CREATE TABLE IF NOT EXISTS checkins(date TEXT PRIMARY KEY,weight REAL,sleep REAL,fatigue INTEGER)")
 if not c.execute("SELECT 1 FROM sets WHERE date='2026-10-30'").fetchone():
  c.executemany("INSERT INTO sets(date,exercise,weight,reps) VALUES('2026-10-30','史密斯卧推',30,?)",[(12,),(10,),(10,),(8,)])
def auth(r):
 try: return signer.loads(r.cookies.get("fitness_session",""),max_age=604800)==USER
 except BadSignature:return False
@app.middleware("http")
async def guard(r,call_next):
 p=r.url.path
 if p not in ("/login","/api/login","/favicon.ico") and not auth(r):
  if p.startswith("/api/"):return JSONResponse({"error":"unauthorized"},status_code=401)
  return HTMLResponse('<meta name="viewport" content="width=device-width"><form action="/api/login" method="post" style="font:18px system-ui;max-width:360px;margin:60px auto"><h2>自然健美 AI · 私人登录</h2><input name="user" placeholder="用户名" required><p><input name="password" type="password" placeholder="密码" required></p><button>登录</button></form>',status_code=200)
 return await call_next(r)
from fastapi import Form
from fastapi.responses import RedirectResponse
@app.post("/api/login")
def login(user:str=Form(...),password:str=Form(...)):
 if not (hmac.compare_digest(user,USER) and hmac.compare_digest(password,PASSWORD)):raise HTTPException(401,"账号或密码错误")
 r=RedirectResponse("/",status_code=303)
 r.set_cookie("fitness_session",signer.dumps(USER),max_age=604800,httponly=True,secure=secure,samesite="lax")
 return r
@app.post("/api/logout")
def logout():
 r=RedirectResponse("/",status_code=303);r.delete_cookie("fitness_session");return r
class SetIn(BaseModel):
 date:date;exercise:str=Field(min_length=1,max_length=80);weight:float=Field(ge=0,le=1000);reps:int=Field(ge=1,le=200)
class CheckIn(BaseModel):
 date:date;weight:float|None=Field(None,gt=0,lt=500);sleep:float|None=Field(None,ge=0,le=24);fatigue:int|None=Field(None,ge=1,le=10)
@app.get("/api/sets")
def sets():
 with connect() as c:return [dict(x) for x in c.execute("SELECT * FROM sets ORDER BY date DESC,id DESC LIMIT 200")]
@app.post("/api/sets")
def add_set(x:SetIn):
 with connect() as c:
  c.execute("INSERT INTO sets(date,exercise,weight,reps) VALUES(?,?,?,?)",(x.date.isoformat(),x.exercise,x.weight,x.reps))
 return {"ok":True}
@app.get("/api/checkins")
def checkins():
 with connect() as c:return [dict(x) for x in c.execute("SELECT * FROM checkins ORDER BY date DESC LIMIT 60")]
@app.post("/api/checkins")
def add_checkin(x:CheckIn):
 with connect() as c:
  c.execute("INSERT OR REPLACE INTO checkins VALUES(?,?,?,?)",(x.date.isoformat(),x.weight,x.sleep,x.fatigue))
 return {"ok":True}
app.mount("/",StaticFiles(directory=str(Path(__file__).parent/"static"),html=True),name="static")
