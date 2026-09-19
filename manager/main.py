import hashlib
import hmac
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

try:
    from .database import Base, engine, get_db, DATABASE_URL
    from .models import CatalogoBrainrot, Cuenta, InventarioCuenta, Usuario
except ImportError:
    from database import Base, engine, get_db, DATABASE_URL
    from models import CatalogoBrainrot, Cuenta, InventarioCuenta, Usuario

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR.parent / "static"
SESSION_SECRET = os.getenv("SESSION_SECRET", "brainrot-manager-local-secret").encode()
SESSION_COOKIE = "brainrot_session"

RAREZAS = [
    {"nombre": "Normal", "color": "#30363d", "texto": "#f0f6fc"},
    {"nombre": "Oro", "color": "#8a6500", "texto": "#ffe08a"},
    {"nombre": "Diamante", "color": "#075985", "texto": "#a5f3fc"},
    {"nombre": "Arco iris", "color": "#7c3aed", "texto": "#f5d0fe"},
    {"nombre": "Cristal", "color": "#155e75", "texto": "#cffafe"},
    {"nombre": "Fantasma", "color": "#475569", "texto": "#e2e8f0"},
    {"nombre": "Cíber", "color": "#115e59", "texto": "#99f6e4"},
    {"nombre": "Divino", "color": "#9a3412", "texto": "#fed7aa"},
    {"nombre": "Maldito", "color": "#7f1d1d", "texto": "#fecaca"},
    {"nombre": "Radioactivo", "color": "#3f6212", "texto": "#d9f99d"},
    {"nombre": "Yin y Yang", "color": "#f8fafc", "texto": "#111827"},
    {"nombre": "Galaxia", "color": "#312e81", "texto": "#ddd6fe"},
    {"nombre": "Lava", "color": "#991b1b", "texto": "#fed7aa"},
    {"nombre": "Caramelos", "color": "#9d174d", "texto": "#fbcfe8"},
]

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.middleware("http")
async def normalize_vercel_api_path(request, call_next):
    path = request.scope["path"]
    api_prefixes = ("/auth", "/cuentas", "/inventario", "/rarezas", "/health")
    if path.startswith("/api/index.py/"):
        path = path[len("/api/index.py"):]
        request.scope["path"] = "/api" + path
        return await call_next(request)
    if not path.startswith("/api/") and any(
        path == prefix or path.startswith(prefix + "/") for prefix in api_prefixes
    ):
        request.scope["path"] = "/api" + path
    return await call_next(request)


@app.get("/")
def read_root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/rarezas")
def list_rarezas():
    return RAREZAS


@app.get("/api/health")
def health():
    return {"ok": True, "database_configured": bool(DATABASE_URL)}


class AuthPayload(BaseModel):
    credential: str | None = None
    email: str | None = None
    name: str | None = None
    picture: str | None = None
    google_id: str | None = None


class CuentaPayload(BaseModel):
    user_cuenta: str
    espacio_maximo: int = 12


class BrainrotPayload(BaseModel):
    nombre: str
    rareza: str = "Normal"
    icono: str = "👾"
    mutacion: str = "Normal"
    generacion_dinero: int = 100


def create_session(user_id: int) -> str:
    value = str(user_id)
    signature = hmac.new(SESSION_SECRET, value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{signature}"


def get_current_user(session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
                     db: Session = Depends(get_db)) -> Usuario:
    if not session or "." not in session:
        raise HTTPException(status_code=401, detail="Sesión no iniciada")
    user_id, signature = session.split(".", 1)
    expected = hmac.new(SESSION_SECRET, user_id.encode(), hashlib.sha256).hexdigest()
    if not user_id.isdigit() or not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = db.get(Usuario, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


def user_response(user: Usuario) -> dict:
    return {"id_usuario": user.id_usuario, "email": user.email, "nombre": user.nombre,
            "avatar": user.avatar, "google_id": user.google_id}


def google_identity(payload: AuthPayload) -> dict:
    if payload.credential:
        query = urllib.parse.urlencode({"id_token": payload.credential})
        try:
            with urllib.request.urlopen(f"https://oauth2.googleapis.com/tokeninfo?{query}", timeout=5) as result:
                data = json.loads(result.read())
        except Exception as error:
            raise HTTPException(status_code=401, detail="Token de Google inválido") from error
        if not data.get("email") or data.get("email_verified") != "true":
            raise HTTPException(status_code=401, detail="La cuenta de Google no está verificada")
        return {"email": data["email"], "name": data.get("name") or data["email"],
                "picture": data.get("picture"), "google_id": data.get("sub")}
    raise HTTPException(status_code=422, detail="Se requiere un credential de Google válido")


@app.get("/api/auth/me")
def auth_me(user: Usuario = Depends(get_current_user)):
    return user_response(user)


@app.post("/api/auth/local")
def local_login(response: Response, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == "dev@local.test").first()
    if not user:
        user = Usuario(email="dev@local.test", user="dev", nombre="Usuario local")
        db.add(user)
        db.commit()
        db.refresh(user)
    response.set_cookie(SESSION_COOKIE, create_session(user.id_usuario), httponly=True,
                        samesite="lax", secure=False, max_age=60 * 60 * 24 * 7)
    return user_response(user)


@app.post("/api/auth/google")
def google_login(payload: AuthPayload, response: Response, db: Session = Depends(get_db)):
    identity = google_identity(payload)
    user = db.query(Usuario).filter(Usuario.email == identity["email"]).first()
    if not user:
        user = Usuario(email=identity["email"], user=identity["email"].split("@")[0],
                       nombre=identity["name"], avatar=identity["picture"], google_id=identity["google_id"])
        db.add(user)
    else:
        user.nombre = identity["name"]
        user.avatar = identity["picture"]
        user.google_id = identity["google_id"] or user.google_id
    db.commit()
    db.refresh(user)
    response.set_cookie(SESSION_COOKIE, create_session(user.id_usuario), httponly=True,
                        samesite="lax", secure=False, max_age=60 * 60 * 24 * 7)
    return user_response(user)


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


def account_response(account: Cuenta) -> dict:
    inventory = [{"id_inventario": item.id_inventario, "nombre": item.brainrot.nombre,
                  "rareza": item.brainrot.rareza, "icono": item.brainrot.icono,
                  "mutacion": item.mutacion, "dinero": item.brainrot.generacion_dinero}
                 for item in account.inventario if item.brainrot]
    return {"id_cuenta": account.id_cuenta, "user_cuenta": account.user_cuenta,
            "espacio_maximo": account.espacio_maximo, "inventario": inventory}


@app.get("/api/cuentas")
def list_accounts(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = (db.query(Cuenta).options(joinedload(Cuenta.inventario).joinedload(InventarioCuenta.brainrot))
                .filter(Cuenta.id_usuario == user.id_usuario).all())
    return [account_response(account) for account in accounts]


@app.post("/api/cuentas")
def create_account(payload: CuentaPayload, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.espacio_maximo < 1 or not payload.user_cuenta.strip():
        raise HTTPException(status_code=422, detail="Datos de cuenta inválidos")
    account = Cuenta(id_usuario=user.id_usuario, user_cuenta=payload.user_cuenta.strip(), espacio_maximo=payload.espacio_maximo)
    db.add(account)
    try:
        db.commit()
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ese nombre de cuenta ya existe") from error
    db.refresh(account)
    return account_response(account)


@app.post("/api/cuentas/{account_id}/inventario")
def add_brainrot(account_id: int, payload: BrainrotPayload,
                 user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    account = (db.query(Cuenta).filter(Cuenta.id_cuenta == account_id,
                                       Cuenta.id_usuario == user.id_usuario).first())
    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if len(account.inventario) >= account.espacio_maximo:
        raise HTTPException(status_code=409, detail="La cuenta no tiene espacio disponible")
    if not payload.nombre.strip() or payload.generacion_dinero < 0:
        raise HTTPException(status_code=422, detail="Datos del brainrot inválidos")
    brainrot = (db.query(CatalogoBrainrot).filter(CatalogoBrainrot.nombre == payload.nombre.strip()).first())
    if not brainrot:
        brainrot = CatalogoBrainrot(nombre=payload.nombre.strip(), rareza=payload.rareza.strip(),
                                    icono=payload.icono.strip() or "👾",
                                    generacion_dinero=payload.generacion_dinero)
        db.add(brainrot)
        db.flush()
    inventory_item = InventarioCuenta(id_cuenta=account.id_cuenta, id_brainrot=brainrot.id_brainrot,
                                      mutacion=payload.mutacion.strip() or "Normal")
    db.add(inventory_item)
    db.commit()
    db.refresh(account)
    return account_response(account)


def get_inventory_item(inventory_id: int, user: Usuario, db: Session) -> InventarioCuenta:
    item = (db.query(InventarioCuenta)
            .join(Cuenta, Cuenta.id_cuenta == InventarioCuenta.id_cuenta)
            .filter(InventarioCuenta.id_inventario == inventory_id,
                    Cuenta.id_usuario == user.id_usuario).first())
    if not item or not item.brainrot:
        raise HTTPException(status_code=404, detail="Brainrot no encontrado")
    return item


@app.put("/api/inventario/{inventory_id}")
def edit_brainrot(inventory_id: int, payload: BrainrotPayload,
                  user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_inventory_item(inventory_id, user, db)
    if not payload.nombre.strip() or payload.generacion_dinero < 0:
        raise HTTPException(status_code=422, detail="Datos del brainrot inválidos")
    item.brainrot.nombre = payload.nombre.strip()
    item.brainrot.rareza = payload.rareza.strip() or "Normal"
    item.brainrot.icono = payload.icono.strip() or "👾"
    item.brainrot.generacion_dinero = payload.generacion_dinero
    item.mutacion = payload.mutacion.strip() or "Normal"
    db.commit()
    db.refresh(item.cuenta)
    return account_response(item.cuenta)


@app.post("/api/inventario/{inventory_id}/duplicar")
def duplicate_brainrot(inventory_id: int, user: Usuario = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    item = get_inventory_item(inventory_id, user, db)
    if len(item.cuenta.inventario) >= item.cuenta.espacio_maximo:
        raise HTTPException(status_code=409, detail="La cuenta no tiene espacio disponible")
    duplicate = InventarioCuenta(id_cuenta=item.id_cuenta, id_brainrot=item.id_brainrot,
                                 mutacion=item.mutacion)
    db.add(duplicate)
    db.commit()
    db.refresh(item.cuenta)
    return account_response(item.cuenta)


@app.delete("/api/inventario/{inventory_id}")
def delete_brainrot(inventory_id: int, user: Usuario = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    item = get_inventory_item(inventory_id, user, db)
    account = item.cuenta
    db.delete(item)
    db.commit()
    db.refresh(account)
    return account_response(account)