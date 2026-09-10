
# -*- coding: utf-8 -*-
"""
Tu Cantina Express - POS & CRM Local
Optimizado para móvil, alta velocidad y producción.
"""
import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import io
import csv
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================
st.set_page_config(
    page_title="Tu Cantina Express",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DB_PATH = Path("cantina.db")
TIPOS_TASA = ("BCV USD", "BCV EUR", "Personalizada")

# ============================================================
# CSS COMPACTO MOBILE-FIRST
# ============================================================
def inject_css():
    st.markdown(
        """<style>
        #MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"],
        [data-testid="stStatusWidget"],[data-testid="stDecoration"]{display:none!important;}
        .main .block-container{padding:.35rem .55rem 5rem .55rem;max-width:520px;margin:auto;}
        .stApp{background:#f6f8fa;}
        * {font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}

        /* Header */
        .hdr{background:linear-gradient(135deg,#0e3a5a,#14496f);color:#fff;
             padding:9px 12px;border-radius:12px;box-shadow:0 3px 8px rgba(14,58,90,.28);
             margin-bottom:8px;}
        .hdr h1{font-size:1rem;margin:0;font-weight:800;letter-spacing:.2px;}
        .hdr .sub{font-size:.62rem;opacity:.82;margin-top:1px;}
        .pill{display:inline-block;background:rgba(243,156,18,.2);color:#f39c12;
              border:1px solid rgba(243,156,18,.5);padding:2px 7px;border-radius:20px;
              font-size:.6rem;font-weight:800;margin-right:4px;margin-top:4px;}
        .pill.g{background:rgba(39,174,96,.2);color:#27ae60;border-color:rgba(39,174,96,.5);}

        /* Secciones */
        .sec{font-size:.76rem;font-weight:800;color:#0e3a5a;margin:6px 0 4px;
             border-left:3px solid #f39c12;padding-left:6px;}

        /* Tarjeta de producto (2 columnas) */
        .pcard{background:#fff;border-radius:10px;padding:6px 4px 5px;text-align:center;
               box-shadow:0 1px 4px rgba(0,0,0,.07);border:1px solid #e8ecf1;
               margin-bottom:3px;position:relative;overflow:hidden;}
        .pcard .e{font-size:1.35rem;line-height:1;}
        .pcard .n{font-size:.68rem;font-weight:800;color:#0e3a5a;margin-top:2px;
                  line-height:1.05;min-height:1.5em;
                  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
                  overflow:hidden;text-overflow:ellipsis;}
        .pcard .p{font-size:.74rem;font-weight:900;color:#f39c12;margin-top:2px;}
        .pcard .b{font-size:.6rem;color:#7a8794;}

        /* Botones compactos */
        div.stButton>button{
            width:100%;border-radius:8px;font-weight:800;border:none;
            padding:.32rem .2rem;font-size:.76rem;line-height:1;min-height:0;
        }
        div.stButton>button[kind="primary"]{background:#f39c12;color:#fff;}
        div.stButton>button[kind="primary"]:hover{background:#d68910;color:#fff;}

        /* Métricas */
        .mc{background:#fff;border-radius:10px;padding:7px 5px;text-align:center;
            box-shadow:0 1px 4px rgba(0,0,0,.06);border-left:3px solid #0e3a5a;
            margin-bottom:4px;}
        .mc .l{font-size:.58rem;color:#6c7a89;text-transform:uppercase;font-weight:800;letter-spacing:.3px;}
        .mc .v{font-size:.92rem;font-weight:900;color:#0e3a5a;margin-top:1px;}
        .mc.gold{border-left-color:#f39c12;}
        .mc.green{border-left-color:#27ae60;}
        .mc.red{border-left-color:#e74c3c;}

        /* Items del carrito y CRM */
        .ci{background:#fff;border-radius:9px;padding:5px 8px;margin-bottom:4px;
            box-shadow:0 1px 3px rgba(0,0,0,.05);border:1px solid #eef1f4;}
        .ci .t{font-size:.76rem;font-weight:800;color:#0e3a5a;}
        .ci .s{font-size:.64rem;color:#6c7a89;line-height:1.25;}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"]{gap:2px;background:#eef1f4;padding:2px;border-radius:9px;}
        .stTabs [data-baseweb="tab"]{border-radius:7px;font-weight:800;font-size:.7rem;
                                     padding:4px 6px;color:#0e3a5a;min-height:0;}
        .stTabs [aria-selected="true"]{background:#0e3a5a!important;color:#fff!important;}
        .stTabs [data-baseweb="tab-highlight"]{display:none;}

        /* Inputs compactos */
        .stTextInput input,.stNumberInput input,
        .stSelectbox div[data-baseweb="select"]>div{
            border-radius:8px!important;font-size:.82rem!important;
        }

        /* WhatsApp link */
        .wa{display:block;text-align:center;background:#25D366;color:#fff!important;
            padding:5px 4px;border-radius:8px;font-weight:800;text-decoration:none;
            font-size:.68rem;line-height:1.1;}

        /* Carrito: integrado con botones */
        .car-total{background:#0e3a5a;color:#fff;border-radius:11px;
                   padding:9px 12px;margin-top:5px;box-shadow:0 3px 9px rgba(14,58,90,.25);}
        .car-total .row{display:flex;justify-content:space-between;font-size:.82rem;}
        .car-total .row.big{font-size:.98rem;font-weight:900;}
        </style>""",
        unsafe_allow_html=True,
    )


# ============================================================
# CONEXIÓN SQLITE OPTIMIZADA
# ============================================================
@contextmanager
def db(commit=False):
    """Context manager de conexión SQLite con WAL, timeout y foreign_keys."""
    conn = sqlite3.connect(str(DB_PATH), timeout=15, isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA temp_store=MEMORY")
        yield conn
        if commit:
            conn.execute("BEGIN")
            conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def init_db():
    """Crea tablas y configuración por defecto. Catálogo INICIALMENTE VACÍO."""
    with db(commit=True) as c:
        cur = c.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS configuracion(
            llave TEXT PRIMARY KEY, valor TEXT NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS productos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emoji TEXT DEFAULT '',
            nombre TEXT NOT NULL COLLATE NOCASE,
            precio_usd REAL NOT NULL CHECK(precio_usd>=0),
            costo_usd REAL NOT NULL DEFAULT 0 CHECK(costo_usd>=0),
            categoria TEXT DEFAULT 'General' COLLATE NOCASE,
            sku TEXT DEFAULT '')""")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prod_cat ON productos(categoria)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prod_nom ON productos(nombre)")
        cur.execute("""CREATE TABLE IF NOT EXISTS clientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL COLLATE NOCASE,
            alumno TEXT DEFAULT '' COLLATE NOCASE,
            representante TEXT DEFAULT '' COLLATE NOCASE,
            telefono TEXT DEFAULT '',
            categoria TEXT DEFAULT 'Alumno')""")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cli_alumno ON clientes(alumno)")
        cur.execute("""CREATE TABLE IF NOT EXISTS ventas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            cliente_id INTEGER DEFAULT 0,
            cliente_nombre TEXT DEFAULT '',
            alumno TEXT DEFAULT '',
            representante TEXT DEFAULT '',
            monto_usd REAL NOT NULL,
            monto_bs REAL NOT NULL,
            tasa_usada REAL NOT NULL,
            estado TEXT NOT NULL CHECK(estado IN ('Pagado','Por cobrar')),
            detalles TEXT DEFAULT '')""")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas(estado)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha)")

        defaults = {
            "tasa_bcv_usd": "0.00",
            "tasa_bcv_eur": "0.00",
            "tasa_personalizada": "0.00",
            "tasa_activa_tipo": "BCV USD",
            "negocio_nombre": "Tu Cantina Express",
            "negocio_rif": "",
        }
        cur.executemany(
            "INSERT OR IGNORE INTO configuracion(llave,valor) VALUES(?,?)",
            list(defaults.items()),
        )


# ============================================================
# CONSULTAS CRUD
# ============================================================
@st.cache_data(ttl=3, show_spinner=False)
def get_config() -> dict:
    with db() as c:
        rows = c.execute("SELECT llave,valor FROM configuracion").fetchall()
    return {k: v for k, v in rows}


def set_config(llave: str, valor: str) -> None:
    with db(commit=True) as c:
        c.execute(
            "INSERT INTO configuracion(llave,valor) VALUES(?,?) "
            "ON CONFLICT(llave) DO UPDATE SET valor=excluded.valor",
            (llave, str(valor)),
        )
    get_config.clear()


@st.cache_data(ttl=2, show_spinner=False)
def get_productos() -> pd.DataFrame:
    with db() as c:
        return pd.read_sql_query(
            "SELECT id,emoji,nombre,precio_usd,costo_usd,categoria,sku "
            "FROM productos ORDER BY categoria COLLATE NOCASE, nombre COLLATE NOCASE",
            c,
        )


def add_producto(emoji, nombre, precio_usd, costo_usd, categoria, sku) -> None:
    with db(commit=True) as c:
        c.execute(
            "INSERT INTO productos(emoji,nombre,precio_usd,costo_usd,categoria,sku) "
            "VALUES(?,?,?,?,?,?)",
            (
                (emoji or "")[:8],
                nombre.strip(),
                round(float(precio_usd), 2),
                round(float(costo_usd), 2),
                (categoria or "General").strip(),
                (sku or "").strip(),
            ),
        )
    get_productos.clear()


@st.cache_data(ttl=2, show_spinner=False)
def get_clientes() -> pd.DataFrame:
    with db() as c:
        return pd.read_sql_query(
            "SELECT id,nombre,alumno,representante,telefono,categoria "
            "FROM clientes ORDER BY alumno COLLATE NOCASE, nombre COLLATE NOCASE",
            c,
        )


def add_cliente(nombre, alumno, representante, telefono, categoria) -> None:
    with db(commit=True) as c:
        c.execute(
            "INSERT INTO clientes(nombre,alumno,representante,telefono,categoria) "
            "VALUES(?,?,?,?,?)",
            (
                nombre.strip(),
                (alumno or "").strip(),
                (representante or "").strip(),
                sanitizar_telefono(telefono, con_prefijo=False),
                (categoria or "Alumno").strip(),
            ),
        )
    get_clientes.clear()


def registrar_venta(cliente_id, cliente_nombre, alumno, representante,
                    monto_usd, monto_bs, tasa_usada, estado, detalles) -> None:
    with db(commit=True) as c:
        c.execute(
            "INSERT INTO ventas(fecha,cliente_id,cliente_nombre,alumno,"
            "representante,monto_usd,monto_bs,tasa_usada,estado,detalles) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                int(cliente_id or 0),
                cliente_nombre or "Anónimo",
                alumno or "",
                representante or "",
                round(float(monto_usd), 2),
                round(float(monto_bs), 2),
                round(float(tasa_usada), 2),
                estado,
                detalles or "",
            ),
        )
    get_ventas.clear()
    get_deudas.clear()


@st.cache_data(ttl=2, show_spinner=False)
def get_ventas() -> pd.DataFrame:
    with db() as c:
        return pd.read_sql_query(
            "SELECT id,fecha,cliente_id,cliente_nombre,alumno,representante,"
            "monto_usd,monto_bs,tasa_usada,estado,detalles FROM ventas "
            "ORDER BY id DESC",
            c,
        )


@st.cache_data(ttl=2, show_spinner=False)
def get_deudas() -> pd.DataFrame:
    with db() as c:
        return pd.read_sql_query(
            "SELECT cliente_id, MAX(cliente_nombre) AS cliente_nombre, "
            "MAX(alumno) AS alumno, MAX(representante) AS representante, "
            "ROUND(SUM(monto_usd),2) AS deuda_usd, "
            "ROUND(SUM(monto_bs),2) AS deuda_bs, "
            "COUNT(*) AS num_ventas "
            "FROM ventas WHERE estado='Por cobrar' "
            "GROUP BY cliente_id "
            "HAVING deuda_usd > 0 "
            "ORDER BY deuda_usd DESC",
            c,
        )


def abonar_cliente(cliente_id: int) -> None:
    with db(commit=True) as c:
        c.execute(
            "UPDATE ventas SET estado='Pagado' "
            "WHERE cliente_id=? AND estado='Por cobrar'",
            (int(cliente_id),),
        )
    get_ventas.clear()
    get_deudas.clear()


def abonar_venta(venta_id: int) -> None:
    with db(commit=True) as c:
        c.execute("UPDATE ventas SET estado='Pagado' WHERE id=?", (int(venta_id),))
    get_ventas.clear()
    get_deudas.clear()


def eliminar_producto(pid: int) -> None:
    with db(commit=True) as c:
        c.execute("DELETE FROM productos WHERE id=?", (int(pid),))
    get_productos.clear()


# ============================================================
# UTILIDADES
# ============================================================
def sanitizar_telefono(tel: str, con_prefijo: bool = True) -> str:
    """
    Limpia teléfono eliminando espacios, guiones, paréntesis, +.
    Si con_prefijo=True, devuelve formato internacional VE (58XXXXXXXXXX).
    Si con_prefijo=False, devuelve solo dígitos sin ceros iniciales (para guardar).
    """
    if tel is None:
        return ""
    d = "".join(ch for ch in str(tel) if ch.isdigit())
    if not d:
        return ""
    d = d.lstrip("0")
    if not d:
        return ""
    if not con_prefijo:
        return d
    if d.startswith("58") and len(d) >= 12:
        return d
    if len(d) == 10:
        return "58" + d
    return "58" + d


def obtener_tasa_activa(cfg: dict) -> float:
    tipo = cfg.get("tasa_activa_tipo", "BCV USD")
    llave = {
        "BCV USD": "tasa_bcv_usd",
        "BCV EUR": "tasa_bcv_eur",
        "Personalizada": "tasa_personalizada",
    }.get(tipo, "tasa_bcv_usd")
    try:
        return round(float(cfg.get(llave, 0) or 0), 2)
    except (ValueError, TypeError):
        return 0.0


def generar_enlace_whatsapp(telefono: str, mensaje: str) -> str:
    t = sanitizar_telefono(telefono, con_prefijo=True)
    if not t:
        return ""
    return f"https://wa.me/{t}?text={urllib.parse.quote(mensaje)}"


def construir_mensaje_recordatorio(representante, alumno,
                                   monto_usd, monto_bs) -> str:
    rep = (representante or "").strip() or "Representante"
    alu = (alumno or "").strip() or "su representado"
    return (
        f"Hola {rep}, le saludamos de Tu Cantina Express. "
        f"Le recordamos el saldo pendiente del día de su representado {alu}: "
        f"${round(float(monto_usd), 2):,.2f} USD "
        f"(equivalente a Bs. {round(float(monto_bs), 2):,.2f} a la tasa de hoy). "
        f"¡Muchas gracias!"
    )


# ============================================================
# CALLBACKS DEL CARRITO (rápidos, sin rerun manual)
# ============================================================
def _car_key(pid) -> str:
    return f"p{int(pid)}"


def cb_add(pid: int, emoji: str, nombre: str, precio: float):
    """Callback: añade 1 unidad al carrito."""
    k = _car_key(pid)
    car = st.session_state.carrito
    if k in car:
        car[k]["qty"] += 1
    else:
        car[k] = {"emoji": emoji, "nombre": nombre,
                  "precio": round(float(precio), 2), "qty": 1}


def cb_inc(k: str):
    if k in st.session_state.carrito:
        st.session_state.carrito[k]["qty"] += 1


def cb_dec(k: str):
    car = st.session_state.carrito
    if k in car:
        car[k]["qty"] -= 1
        if car[k]["qty"] <= 0:
            del car[k]


def cb_del(k: str):
    st.session_state.carrito.pop(k, None)


def cb_clear():
    st.session_state.carrito = {}
    st.session_state.cliente_sel = 0


# ============================================================
# HELPERS DE CARRITO
# ============================================================
def carrito_total_usd() -> float:
    return round(
        sum(v["precio"] * v["qty"] for v in st.session_state.carrito.values()),
        2,
    )


def carrito_detalle_txt() -> str:
    return " | ".join(
        f"{v['qty']}x {v['nombre']} (${v['precio']:.2f})"
        for v in st.session_state.carrito.values()
    )


# ============================================================
# UI: HEADER Y MÉTRICAS
# ============================================================
def render_header(cfg: dict):
    t = obtener_tasa_activa(cfg)
    usd = float(cfg.get("tasa_bcv_usd", 0) or 0)
    eur = float(cfg.get("tasa_bcv_eur", 0) or 0)
    tipo = cfg.get("tasa_activa_tipo", "BCV USD")
    st.markdown(
        f"""<div class="hdr">
        <h1>🍽️ Tu Cantina Express</h1>
        <div class="sub">POS & CRM · {datetime.now().strftime('%d/%m/%Y')}</div>
        <div>
            <span class="pill g">TASA ({tipo}): Bs. {t:,.2f}</span>
            <span class="pill">USD {usd:,.2f}</span>
            <span class="pill">EUR {eur:,.2f}</span>
        </div></div>""",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, variante: str = ""):
    st.markdown(
        f'<div class="mc {variante}"><div class="l">{label}</div>'
        f'<div class="v">{value}</div></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# MÓDULO POS
# ============================================================
def _finalizar_venta(estado: str, tasa: float):
    car = st.session_state.carrito
    if not car:
        st.warning("El carrito está vacío.")
        return
    total_usd = carrito_total_usd()
    total_bs = round(total_usd * tasa, 2)
    cid = int(st.session_state.get("cliente_sel", 0) or 0)

    if cid > 0:
        df = get_clientes()
        row = df[df["id"] == cid]
        if not row.empty:
            r = row.iloc[0]
            cn = r["nombre"]
            al = r["alumno"] or ""
            rep = r["representante"] or ""
        else:
            cid, cn, al, rep = 0, "Anónimo", "", ""
    else:
        cid, cn, al, rep = 0, "Anónimo", "", ""

    registrar_venta(cid, cn, al, rep, total_usd, total_bs,
                    tasa, estado, carrito_detalle_txt())

    st.session_state.carrito = {}
    st.session_state.cliente_sel = 0
    msg = f"{'✅ PAGADO' if estado == 'Pagado' else '🔴 FIADO'}: ${total_usd:.2f} / Bs. {total_bs:,.2f}"
    (st.success if estado == "Pagado" else st.warning)(msg)


def modulo_pos(cfg: dict):
    tasa = obtener_tasa_activa(cfg)
    pdf = get_productos()

    # --- Filtros ---
    if not pdf.empty:
        cats = ["Todas"] + sorted(pdf["categoria"].dropna().unique().tolist())
        c1, c2 = st.columns([3, 2])
        with c1:
            st.text_input(
                "🔍", key="busqueda", placeholder="Buscar producto...",
                label_visibility="collapsed",
            )
        with c2:
            if st.session_state.get("cat_fil") not in cats:
                st.session_state.cat_fil = "Todas"
            st.selectbox(
                "Cat", cats, key="cat_fil", label_visibility="collapsed",
            )

    # --- Grid 2 columnas ---
    st.markdown('<div class="sec">📦 Catálogo</div>', uns
