# -*- coding: utf-8 -*-
"""
Tu Cantina Express v4
POS & CRM local, mobile-first, tema claro forzado, UI/UX pulida.
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
# CSS PULIDO — SIN BORDES, CON JERARQUÍA, ESPACIADO 8PX
# ============================================================
def inject_css():
    st.markdown(
        """<style>
        /* ===== Reset / ocultar ===== */
        #MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"],
        [data-testid="stStatusWidget"],[data-testid="stDecoration"]{display:none!important;}

        :root{
            --azul:#0e3a5a;
            --azul-2:#14496f;
            --ambar:#f39c12;
            --verde:#27ae60;
            --rojo:#e74c3c;
            --tx:#0f172a;
            --tx-2:#475569;
            --tx-3:#94a3b8;
            --fondo:#f6f8fa;
            --card:#ffffff;
            --linea:#e2e8f0;
            --sombra:0 2px 6px rgba(15,23,42,.06);
            --sombra-sm:0 1px 4px rgba(15,23,42,.05);
        }

        * {font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}

        .main .block-container{
            padding:.5rem .7rem 5rem .7rem;
            max-width:520px;
            margin:auto;
        }
        .stApp{background:var(--fondo);}

        /* Reducir gaps verticales */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]{gap:.45rem;}
        .element-container{margin-bottom:0 !important;}
        hr{display:none;}

        /* ===== LABELS E INPUTS ===== */
        .stTextInput label, .stNumberInput label, .stSelectbox label,
        .stTextArea label, .stMultiSelect label, .stRadio label,
        .stCheckbox label, .stSlider label, .stFileUploader label,
        div[data-testid="stWidgetLabel"] label,
        div[data-testid="stWidgetLabel"] p{
            color:var(--tx) !important;
            font-weight:600 !important;
            font-size:.78rem !important;
            opacity:1 !important;
            letter-spacing:.1px;
        }
        .stTextInput input::placeholder,
        .stNumberInput input::placeholder{
            color:var(--tx-3) !important;
            opacity:1 !important;
        }
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea{
            background:var(--card) !important;
            color:var(--tx) !important;
            border:1px solid var(--linea) !important;
            border-radius:10px !important;
            font-size:.88rem !important;
            padding:8px 12px !important;
            box-shadow:none !important;
        }
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus{
            border-color:var(--azul) !important;
            box-shadow:0 0 0 3px rgba(14,58,90,.1) !important;
        }
        div[data-baseweb="select"] > div{
            background:var(--card) !important;
            color:var(--tx) !important;
            border:1px solid var(--linea) !important;
            border-radius:10px !important;
            min-height:38px;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div[aria-selected],
        div[data-baseweb="select"] input{color:var(--tx) !important;}
        ul[data-baseweb="menu"], div[data-baseweb="popover"]{
            background:var(--card) !important;
            color:var(--tx) !important;
            border-radius:10px !important;
            box-shadow:var(--sombra) !important;
            border:1px solid var(--linea) !important;
        }
        ul[data-baseweb="menu"] li{
            color:var(--tx) !important;
            background:transparent !important;
            font-size:.85rem;
        }
        ul[data-baseweb="menu"] li:hover{background:#f1f5f9 !important;}
        .stNumberInput button{
            background:#f1f5f9 !important;
            color:var(--tx) !important;
            border:none !important;
        }
        .stNumberInput button:hover{background:#e2e8f0 !important;}

        /* ===== HEADER ===== */
        .hdr{
            background:linear-gradient(135deg,var(--azul),var(--azul-2));
            color:#fff;padding:14px 16px;border-radius:16px;
            margin-bottom:12px;
            box-shadow:0 6px 16px rgba(14,58,90,.18);
        }
        .hdr-top{display:flex;justify-content:space-between;align-items:center;
                 font-size:.88rem;font-weight:800;letter-spacing:.1px;}
        .hdr-top .date{font-size:.64rem;opacity:.72;font-weight:500;}
        .hdr-tasa{margin-top:10px;display:flex;align-items:baseline;gap:10px;}
        .hdr-tasa .lbl{font-size:.58rem;opacity:.65;text-transform:uppercase;
                       letter-spacing:.7px;font-weight:700;}
        .hdr-tasa .val{font-size:1.5rem;font-weight:900;color:var(--ambar);
                       letter-spacing:-.5px;line-height:1;}
        .hdr-alt{margin-top:6px;font-size:.66rem;opacity:.65;}
        .hdr-alt .dot{margin:0 8px;opacity:.4;}

        /* ===== SECCIONES (títulos discretos) ===== */
        .sec{
            font-size:.68rem;font-weight:800;color:var(--tx-3);
            letter-spacing:.7px;text-transform:uppercase;
            margin:14px 0 6px;padding:0;
            border:none;
        }

        /* ===== TARJETA PRODUCTO ===== */
        .pcard{
            background:var(--card);
            border-radius:12px;
            padding:10px 8px 8px;
            text-align:center;
            box-shadow:var(--sombra);
            margin-bottom:6px;
            transition:transform .12s ease;
        }
        .pcard .e{font-size:1.6rem;line-height:1;display:block;}
        .pcard .n{
            font-size:.78rem;font-weight:700;color:var(--tx);
            margin-top:6px;line-height:1.15;
            display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
            overflow:hidden;min-height:1.8em;
        }
        .pcard .p{
            font-size:.92rem;font-weight:900;color:var(--ambar);
            margin-top:6px;letter-spacing:-.3px;
        }
        .pcard .b{font-size:.66rem;color:var(--tx-3);margin-top:2px;font-weight:500;}

        /* ===== BOTONES ===== */
        div.stButton>button{
            width:100%;
            border-radius:10px;
            font-weight:700;
            border:1px solid var(--linea);
            background:var(--card);
            color:var(--tx);
            padding:.5rem .35rem;
            font-size:.8rem;
            line-height:1.1;
            min-height:0;
            box-shadow:0 1px 2px rgba(15,23,42,.04);
            transition:all .12s ease;
        }
        div.stButton>button:hover{border-color:#cbd5e1;background:#f8fafc;}
        div.stButton>button:active{transform:scale(.98);}
        div.stButton>button[kind="primary"]{
            background:var(--verde);color:#fff;border:none;
            box-shadow:0 3px 8px rgba(39,174,96,.25);
        }
        div.stButton>button[kind="primary"]:hover{background:#229954;}

        /* Botón "fiar" (rojo outline) */
        .btn-fiar button{
            background:var(--card) !important;
            color:var(--rojo) !important;
            border:1.5px solid var(--rojo) !important;
        }
        .btn-fiar button:hover{background:#fef2f2 !important;}

        /* ===== MÉTRICAS ===== */
        .mc{
            background:var(--card);border-radius:12px;padding:10px 8px;
            text-align:center;box-shadow:var(--sombra);margin-bottom:6px;
            border-left:none;position:relative;overflow:hidden;
        }
        .mc::before{
            content:"";position:absolute;left:0;top:0;bottom:0;width:3px;
            background:var(--azul);
        }
        .mc.gold::before{background:var(--ambar);}
        .mc.green::before{background:var(--verde);}
        .mc.red::before{background:var(--rojo);}
        .mc .l{
            font-size:.6rem;color:var(--tx-3);text-transform:uppercase;
            font-weight:800;letter-spacing:.6px;
        }
        .mc .v{
            font-size:1rem;font-weight:900;color:var(--tx);
            margin-top:3px;letter-spacing:-.3px;
        }

        /* ===== ITEMS (carrito / CRM / historial) ===== */
        .ci{
            background:var(--card);border-radius:11px;padding:8px 11px;
            margin-bottom:5px;box-shadow:var(--sombra-sm);border:none;
        }
        .ci .t{font-size:.82rem;font-weight:700;color:var(--tx);line-height:1.25;}
        .ci .s{font-size:.68rem;color:var(--tx-3);line-height:1.35;margin-top:2px;}
        .ci .row{display:flex;justify-content:space-between;align-items:baseline;}
        .ci .estado{font-size:.68rem;font-weight:800;}
        .ci .estado.ok{color:var(--verde);}
        .ci .estado.pend{color:var(--rojo);}

        /* ===== TABS (tab bar limpio) ===== */
        .stTabs [data-baseweb="tab-list"]{
            gap:0;
            background:transparent;
            padding:0;
            border-bottom:1px solid var(--linea);
            border-radius:0;
            overflow-x:auto !important;
            overflow-y:hidden;
            flex-wrap:nowrap !important;
            justify-content:space-between;
            scrollbar-width:none;
            -ms-overflow-style:none;
            -webkit-overflow-scrolling:touch;
        }
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar{display:none;}
        .stTabs [data-baseweb="tab"]{
            border-radius:0;
            font-weight:700;
            font-size:1.05rem;
            padding:8px 14px;
            color:var(--tx-3) !important;
            background:transparent !important;
            min-height:0;
            white-space:nowrap !important;
            flex:0 0 auto !important;
            border-bottom:2px solid transparent;
            transition:all .15s ease;
        }
        .stTabs [data-baseweb="tab"]:hover{color:var(--tx-2) !important;}
        .stTabs [aria-selected="true"]{
            color:var(--azul) !important;
            border-bottom:2px solid var(--azul) !important;
            background:transparent !important;
        }
        .stTabs [data-baseweb="tab-highlight"]{display:none;}
        .stTabs [data-baseweb="tab-border"]{display:none;}

        /* ===== DATAFRAMES (claro) ===== */
        div[data-testid="stDataFrame"]{
            background:var(--card) !important;
            border-radius:11px !important;
            overflow:hidden !important;
            box-shadow:var(--sombra-sm) !important;
            border:none !important;
        }
        div[data-testid="stDataFrame"] *{color:var(--tx) !important;}
        div[data-testid="stDataFrame"] [role="columnheader"]{
            background:#f8fafc !important;color:var(--tx-2) !important;
            font-weight:800 !important;font-size:.68rem !important;
            text-transform:uppercase;letter-spacing:.4px;
        }
        div[data-testid="stDataFrame"] [role="gridcell"]{
            font-size:.76rem !important;
        }

        /* ===== ALERTS ===== */
        div[data-testid="stAlert"]{
            background:#eff6ff !important;color:var(--tx) !important;
            border-radius:10px !important;border-left:3px solid var(--azul) !important;
            padding:8px 12px !important;
        }
        div[data-testid="stAlert"] *{color:var(--tx) !important;font-size:.78rem;}
        div[data-testid="stAlert"][data-baseweb="notification"] svg{display:none;}

        /* ===== WHATSAPP ===== */
        .wa{
            display:block;text-align:center;background:#25D366;color:#fff !important;
            padding:8px 6px;border-radius:10px;font-weight:700;text-decoration:none;
            font-size:.76rem;line-height:1.1;margin-top:2px;
            box-shadow:0 2px 6px rgba(37,211,102,.28);
        }
        .wa:hover{background:#1faa52;}

        /* ===== CARRITO TOTAL ===== */
        .car-total{
            background:linear-gradient(135deg,var(--azul),var(--azul-2));
            color:#fff;border-radius:14px;padding:12px 14px;margin-top:8px;
            box-shadow:0 6px 16px rgba(14,58,90,.2);
        }
        .car-total .row{display:flex;justify-content:space-between;align-items:baseline;
                        font-size:.8rem;opacity:.9;}
        .car-total .row.big{
            font-size:1.15rem;font-weight:900;opacity:1;margin-top:3px;
            letter-spacing:-.4px;
        }
        .car-total .tasa-note{
            font-size:.6rem;opacity:.6;margin-top:6px;
            text-transform:uppercase;letter-spacing:.4px;
        }

        /* ===== EXPANDER ===== */
        details, summary{background:transparent;}
        details > summary{
            list-style:none;padding:8px 10px !important;
            font-size:.8rem;font-weight:700;color:var(--tx);
            background:var(--card);border-radius:10px;
            box-shadow:var(--sombra-sm);
        }
        details[open] > summary{border-radius:10px 10px 0 0;}

        /* ===== FORMULARIOS ===== */
        [data-testid="stForm"]{
            border:none !important;background:transparent !important;
            padding:0 !important;
        }
        [data-testid="stForm"] label,
        [data-testid="stForm"] p{
            color:var(--tx) !important;font-weight:700 !important;
        }

        /* Info blue (aviso tasa 0) */
        div[data-testid="stAlert"][data-baseweb="notification"]{
            margin-bottom:8px;
        }
        </style>""",
        unsafe_allow_html=True,
    )


# ============================================================
# SQLITE
# ============================================================
@contextmanager
def db(commit=False):
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
# CRUD
# ============================================================
@st.cache_data(ttl=3, show_spinner=False)
def get_config() -> dict:
    with db() as c:
        rows = c.execute("SELECT llave,valor FROM configuracion").fetchall()
    return dict(rows)


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


def eliminar_producto(pid: int) -> None:
    with db(commit=True) as c:
        c.execute("DELETE FROM productos WHERE id=?", (int(pid),))
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


def eliminar_venta(venta_id: int) -> None:
    with db(commit=True) as c:
        c.execute("DELETE FROM ventas WHERE id=?", (int(venta_id),))
    get_ventas.clear()
    get_deudas.clear()


def eliminar_todas_ventas() -> None:
    with db(commit=True) as c:
        c.execute("DELETE FROM ventas")
        c.execute("DELETE FROM sqlite_sequence WHERE name='ventas'")
    get_ventas.clear()
    get_deudas.clear()


# ============================================================
# UTILIDADES
# ============================================================
def sanitizar_telefono(tel: str, con_prefijo: bool = True) -> str:
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


def fecha_corta(f: str) -> str:
    """YYYY-MM-DD HH:MM:SS -> DD/MM HH:MM"""
    try:
        dt = datetime.strptime(f, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m · %H:%M")
    except Exception:
        return f[:16]# ============================================================
# CALLBACKS CARRITO
# ============================================================
def _car_key(pid) -> str:
    return f"p{int(pid)}"


def cb_add(pid: int, emoji: str, nombre: str, precio: float):
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


# ============================================================
# HELPERS CARRITO
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
# HEADER PULIDO
# ============================================================
def render_header(cfg: dict):
    t = obtener_tasa_activa(cfg)
    tipo = cfg.get("tasa_activa_tipo", "BCV USD")
    usd = float(cfg.get("tasa_bcv_usd", 0) or 0)
    eur = float(cfg.get("tasa_bcv_eur", 0) or 0)
    st.markdown(
        f"""<div class="hdr">
            <div class="hdr-top">
                <span>🍽️ Tu Cantina Express</span>
                <span class="date">{datetime.now().strftime('%d/%m/%Y')}</span>
            </div>
            <div class="hdr-tasa">
                <span class="lbl">{tipo}</span>
                <span class="val">Bs. {t:,.2f}</span>
            </div>
            <div class="hdr-alt">
                USD {usd:,.2f}<span class="dot">·</span>EUR {eur:,.2f}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, variante: str = ""):
    st.markdown(
        f'<div class="mc {variante}"><div class="l">{label}</div>'
        f'<div class="v">{value}</div></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# POS: FINALIZAR VENTA
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

    st.session_state["_reset_venta"] = True
    st.session_state["_venta_msg"] = (
        f"{'✅ PAGADO' if estado == 'Pagado' else '🔴 FIADO'}: "
        f"${total_usd:.2f} / Bs. {total_bs:,.2f}"
    )
    st.session_state["_venta_estado"] = estado


# ============================================================
# MÓDULO POS
# ============================================================
def modulo_pos(cfg: dict):
    tasa = obtener_tasa_activa(cfg)
    pdf = get_productos()

    if not pdf.empty:
        cats = ["Todas"] + sorted(pdf["categoria"].dropna().unique().tolist())
        c1, c2 = st.columns([3, 2], gap="small")
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

    st.markdown('<div class="sec">Catálogo</div>', unsafe_allow_html=True)

    if pdf.empty:
        st.info("Catálogo vacío. Agrega productos en la pestaña ➕.")
    else:
        df = pdf
        q = (st.session_state.get("busqueda") or "").strip().lower()
        if q:
            df = df[df["nombre"].str.lower().str.contains(q, na=False, regex=False)]
        cat = st.session_state.get("cat_fil", "Todas")
        if cat != "Todas":
            df = df[df["categoria"] == cat]

        if df.empty:
            st.info("Sin resultados.")
        else:
            cols = st.columns(2, gap="small")
            for i, (_, r) in enumerate(df.iterrows()):
                with cols[i % 2]:
                    pb = round(float(r["precio_usd"]) * tasa, 2)
                    st.markdown(
                        f'<div class="pcard">'
                        f'<span class="e">{r["emoji"] or "🍴"}</span>'
                        f'<div class="n">{r["nombre"]}</div>'
                        f'<div class="p">${float(r["precio_usd"]):.2f}</div>'
                        f'<div class="b">Bs. {pb:,.2f}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.button(
                        "Agregar",
                        key=f"add_{r['id']}",
                        on_click=cb_add,
                        args=(int(r["id"]), r["emoji"] or "",
                              r["nombre"], float(r["precio_usd"])),
                        use_container_width=True,
                    )

    st.markdown('<div class="sec">Carrito</div>', unsafe_allow_html=True)
    car = st.session_state.carrito
    if not car:
        st.info("Carrito vacío.")
        return

    for k, item in list(car.items()):
        sub_usd = round(item["precio"] * item["qty"], 2)
        sub_bs = round(sub_usd * tasa, 2)
        c1, c2, c3 = st.columns([5, 3, 1], gap="small")
        with c1:
            st.markdown(
                f'<div class="ci">'
                f'<div class="t">{item["emoji"]} {item["nombre"]}</div>'
                f'<div class="s">{item["qty"]}× ${item["precio"]:.2f} · '
                f'<b>${sub_usd:.2f}</b> · Bs. {sub_bs:,.2f}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            b1, b2 = st.columns(2, gap="small")
            with b1:
                st.button("−", key=f"r_{k}", on_click=cb_dec, args=(k,),
                          use_container_width=True)
            with b2:
                st.button("+", key=f"s_{k}", on_click=cb_inc, args=(k,),
                          use_container_width=True)
        with c3:
            st.button("✕", key=f"d_{k}", on_click=cb_del, args=(k,),
                      use_container_width=True)

    total_usd = carrito_total_usd()
    total_bs = round(total_usd * tasa, 2)

    st.markdown(
        f'<div class="car-total">'
        f'<div class="row"><span>Total USD</span><span>${total_usd:.2f}</span></div>'
        f'<div class="row big"><span>Total Bs.</span><span>Bs. {total_bs:,.2f}</span></div>'
        f'<div class="tasa-note">Tasa aplicada Bs. {tasa:,.2f}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sec">Cliente</div>', unsafe_allow_html=True)
    cdf = get_clientes()
    opciones = {0: "🧑 Venta anónima"}
    for _, cc in cdf.iterrows():
        etq = cc["alumno"] or cc["nombre"]
        if cc["representante"]:
            etq += f" · {cc['representante']}"
        opciones[int(cc["id"])] = etq
    ids = list(opciones.keys())
    if st.session_state.get("cliente_sel") not in ids:
        st.session_state.cliente_sel = 0
    st.selectbox(
        "Cliente", ids, format_func=lambda x: opciones[x],
        key="cliente_sel", label_visibility="collapsed",
    )

    cA, cB = st.columns(2, gap="small")
    with cA:
        if st.button("Registrar pago", type="primary", use_container_width=True):
            _finalizar_venta("Pagado", tasa)
            st.rerun()
    with cB:
        st.markdown('<div class="btn-fiar">', unsafe_allow_html=True)
        if st.button("Fiar a crédito", use_container_width=True):
            _finalizar_venta("Por cobrar", tasa)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)# ============================================================
# MÓDULO CRM
# ============================================================
def modulo_crm(cfg: dict):
    tasa = obtener_tasa_activa(cfg)
    st.markdown('<div class="sec">Directorio</div>', unsafe_allow_html=True)

    cdf = get_clientes()
    ddf = get_deudas()
    deuda_map = {}
    if not ddf.empty:
        for _, d in ddf.iterrows():
            deuda_map[int(d["cliente_id"])] = {
                "usd": float(d["deuda_usd"]),
                "num": int(d["num_ventas"]),
            }

    if cdf.empty:
        st.info("Sin clientes registrados.")
    else:
        for _, c in cdf.iterrows():
            cid = int(c["id"])
            de = deuda_map.get(cid, {"usd": 0.0, "num": 0})
            tiene = de["usd"] > 0.005
            dbs = round(de["usd"] * tasa, 2)

            st.markdown(
                f'<div class="ci">'
                f'<div class="t">👤 {c["alumno"] or c["nombre"]}</div>'
                f'<div class="s">Rep: {c["representante"] or "—"} · '
                f'📱 {c["telefono"] or "—"}</div>'
                f'<div class="s" style="margin-top:3px">Deuda: '
                f'<b style="color:{"#e74c3c" if tiene else "#27ae60"}">'
                f'${de["usd"]:.2f}</b> · Bs. {dbs:,.2f}</div></div>',
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns([2, 2, 1], gap="small")
            with c1:
                if tiene and st.button("Abonar", key=f"ab_{cid}",
                                       use_container_width=True):
                    abonar_cliente(cid)
                    st.success("Deuda cancelada.")
                    st.rerun()
            with c2:
                if tiene and c["telefono"]:
                    msg = construir_mensaje_recordatorio(
                        c["representante"], c["alumno"] or c["nombre"],
                        de["usd"], dbs,
                    )
                    link = generar_enlace_whatsapp(c["telefono"], msg)
                    if link:
                        st.markdown(
                            f'<a href="{link}" target="_blank" class="wa">'
                            f'Recordar por WhatsApp</a>',
                            unsafe_allow_html=True,
                        )
            with c3:
                if tiene:
                    vk = f"vv_{cid}"
                    if st.button("···", key=f"v_{cid}", use_container_width=True):
                        st.session_state[vk] = not st.session_state.get(vk, False)

            if tiene and st.session_state.get(f"vv_{cid}", False):
                vdf = get_ventas()
                pend = vdf[(vdf["cliente_id"] == cid)
                           & (vdf["estado"] == "Por cobrar")]
                for _, v in pend.iterrows():
                    s1, s2 = st.columns([5, 1], gap="small")
                    with s1:
                        st.markdown(
                            f'<div style="font-size:.66rem;color:#475569;padding:3px 6px">'
                            f'{fecha_corta(v["fecha"])} · '
                            f'${float(v["monto_usd"]):.2f} · {v["detalles"]}</div>',
                            unsafe_allow_html=True,
                        )
                    with s2:
                        if st.button("✓", key=f"pv_{v['id']}",
                                     use_container_width=True):
                            abonar_venta(int(v["id"]))
                            st.rerun()

    st.markdown('<div class="sec">Nuevo cliente</div>', unsafe_allow_html=True)
    with st.form("form_cliente", clear_on_submit=True):
        c1, c2 = st.columns(2, gap="small")
        with c1:
            al = st.text_input("Alumno *")
            rep = st.text_input("Representante")
        with c2:
            tel = st.text_input("Teléfono")
            cat = st.selectbox("Categoría",
                               ["Alumno", "Docente", "Administrativo", "Otro"])
        nom = st.text_input("Nombre alterno (opcional)")
        if st.form_submit_button("Guardar cliente", use_container_width=True):
            if not al.strip():
                st.error("El nombre del alumno es obligatorio.")
            else:
                add_cliente(nom.strip() or al.strip(), al.strip(),
                            rep.strip(), tel.strip(), cat)
                st.success("Cliente agregado.")
                st.rerun()


# ============================================================
# MÓDULO PRODUCTOS
# ============================================================
EMOJIS = ["🍔", "🌭", "🍕", "🥟", "🍟", "🌮", "🌯", "🥪", "🍗", "🍖",
          "🥗", "🍝", "🍜", "🍲", "🍛", "🍱", "🥘", "🥤", "💧", "🧃",
          "☕", "🍵", "🧋", "🍺", "🥛", "🍹", "🍰", "🍪", "🍫", "🍩",
          "🍦", "🧁", "🍮", "🥧", "🍎", "🍌", "🍓", "🍊", "🍇", "🥭",
          "🍉", "🍴", "🥄", "🧂", "🍿", "🥨", "🥐", "🍳", "🥞", "🧇"]


def modulo_productos(cfg: dict):
    tasa = obtener_tasa_activa(cfg)
    st.markdown('<div class="sec">Nuevo producto</div>', unsafe_allow_html=True)

    with st.form("form_prod", clear_on_submit=True):
        em = st.selectbox("Emoji", EMOJIS, index=0)
        nom = st.text_input("Nombre *")
        c1, c2 = st.columns(2, gap="small")
        with c1:
            pr = st.number_input("Precio $ *", min_value=0.0, step=0.10,
                                 format="%.2f")
        with c2:
            co = st.number_input("Costo $", min_value=0.0, step=0.10,
                                 format="%.2f")
        c3, c4 = st.columns(2, gap="small")
        with c3:
            cat = st.text_input("Categoría", value="General")
        with c4:
            sku = st.text_input("SKU")
        if st.form_submit_button("Guardar producto", use_container_width=True):
            if not nom.strip():
                st.error("El nombre es obligatorio.")
            elif pr <= 0:
                st.error("El precio debe ser mayor a 0.")
            else:
                add_producto(em, nom, pr, co, cat, sku)
                st.success(f"'{nom.strip()}' agregado.")
                st.rerun()

    st.markdown('<div class="sec">Catálogo actual</div>', unsafe_allow_html=True)
    pdf = get_productos()
    if pdf.empty:
        st.info("No hay productos registrados todavía.")
    else:
        for _, r in pdf.iterrows():
            pb = round(float(r["precio_usd"]) * tasa, 2)
            st.markdown(
                f'<div class="ci"><div class="row">'
                f'<div>'
                f'<div class="t">{r["emoji"] or "🍴"} {r["nombre"]}</div>'
                f'<div class="s">{r["categoria"] or "General"}'
                f'{" · " + r["sku"] if r["sku"] else ""}</div>'
                f'</div>'
                f'<div style="text-align:right">'
                f'<div class="t" style="color:#f39c12">${float(r["precio_usd"]):.2f}</div>'
                f'<div class="s">Bs. {pb:,.2f}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="sec">Eliminar producto</div>',
                    unsafe_allow_html=True)
        opciones = {int(r["id"]): f"{r['emoji']} {r['nombre']}"
                    for _, r in pdf.iterrows()}
        pid = st.selectbox("Selecciona un producto", list(opciones.keys()),
                           format_func=lambda x: opciones[x],
                           label_visibility="collapsed")
        if st.button("Eliminar producto", use_container_width=True):
            eliminar_producto(pid)
            st.success("Producto eliminado.")
            st.rerun()


# ============================================================
# REPORTES
# ============================================================
def _reporte_txt(vdf: pd.DataFrame, cfg: dict) -> str:
    t = obtener_tasa_activa(cfg)
    L = ["=" * 62,
         "      TU CANTINA EXPRESS · REPORTE DE OPERACIONES",
         "=" * 62,
         f"Generado : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
         f"Tasa     : Bs. {t:,.2f} por USD ({cfg.get('tasa_activa_tipo','')})",
         f"Negocio  : {cfg.get('negocio_nombre','')}",
         "-" * 62, ""]
    if vdf.empty:
        L.append("Sin operaciones registradas.")
        return "\n".join(L)

    tot_usd = round(float(vdf["monto_usd"].sum()), 2)
    tot_bs = round(float(vdf["monto_bs"].sum()), 2)
    pag = vdf[vdf["estado"] == "Pagado"]
    pc = vdf[vdf["estado"] == "Por cobrar"]
    L += [f"Operaciones      : {len(vdf)}",
          f"Total facturado  : ${tot_usd:,.2f} / Bs. {tot_bs:,.2f}",
          f"Cobrado          : ${round(float(pag['monto_usd'].sum()),2):,.2f}",
          f"Por cobrar       : ${round(float(pc['monto_usd'].sum()),2):,.2f}",
          "", "-" * 62, "DETALLE DE OPERACIONES", "-" * 62]
    for _, v in vdf.sort_values("id").iterrows():
        L += ["",
              f"#{v['id']} · {v['fecha']}",
              f"  Tasa usada    : Bs. {float(v['tasa_usada']):,.2f}",
              f"  Cliente       : {v['cliente_nombre'] or 'Anónimo'}",
              f"  Alumno        : {v['alumno'] or '—'}",
              f"  Representante : {v['representante'] or '—'}",
              f"  Monto USD     : ${float(v['monto_usd']):,.2f}",
              f"  Monto Bs.     : Bs. {float(v['monto_bs']):,.2f}",
              f"  Estado        : {v['estado']}",
              f"  Productos     : {v['detalles']}"]
    L += ["", "=" * 62, "Fin del reporte.", "=" * 62]
    return "\n".join(L)


def modulo_reportes(cfg: dict):
    tasa = obtener_tasa_activa(cfg)
    vdf = get_ventas()
    pdf = get_productos()

    tu = round(float(vdf["monto_usd"].sum()), 2) if not vdf.empty else 0.0
    tb = round(float(vdf["monto_bs"].sum()), 2) if not vdf.empty else 0.0
    deu = (round(float(vdf.loc[vdf["estado"] == "Por cobrar", "monto_usd"].sum()), 2)
           if not vdf.empty else 0.0)
    n = len(vdf)

    if not pdf.empty and tu > 0:
        m = ((pdf["precio_usd"] - pdf["costo_usd"]) / pdf["precio_usd"])
        m = m.replace([float("inf"), -float("inf")], 0).fillna(0).mean()
        gan = round(tu * float(m), 2)
    else:
        gan = 0.0

    c1, c2 = st.columns(2, gap="small")
    with c1:
        metric_card("Ingresos", f"${tu:,.2f}", "gold")
    with c2:
        metric_card("Ganancia est.", f"${gan:,.2f}", "green")
    c3, c4 = st.columns(2, gap="small")
    with c3:
        metric_card("Deuda", f"${deu:,.2f}", "red")
    with c4:
        metric_card("Operaciones", f"{n}")

    st.markdown(
        f'<div style="text-align:center;font-size:.64rem;color:#94a3b8;'
        f'margin-top:4px">Facturado Bs. {tb:,.2f} · Tasa Bs. {tasa:,.2f}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sec">Historial</div>', unsafe_allow_html=True)
    if vdf.empty:
        st.info("Sin ventas registradas.")
        return

    # Mostrar últimas 30 como cards HTML (limpio en móvil)
    for _, r in vdf.head(30).iterrows():
        pendiente = r["estado"] == "Por cobrar"
        cls = "pend" if pendiente else "ok"
        etiqueta = "Por cobrar" if pendiente else "Pagado"
        alumno = r["alumno"] or r["cliente_nombre"] or "Anónimo"
        st.markdown(
            f'<div class="ci">'
            f'<div class="row">'
            f'<span class="t">#{int(r["id"])} · {alumno}</span>'
            f'<span class="estado {cls}">{etiqueta}</span>'
            f'</div>'
            f'<div class="s">{fecha_corta(r["fecha"])} · '
            f'<b>${float(r["monto_usd"]):.2f}</b> · '
            f'Bs. {float(r["monto_bs"]):,.2f} · '
            f'{r["detalles"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    if len(vdf) > 30:
        st.caption(f"Mostrando las últimas 30 de {len(vdf)} operaciones.")

    # ============ ELIMINAR VENTA ============
    st.markdown('<div class="sec">Eliminar venta</div>',
                unsafe_allow_html=True)
    with st.expander("Eliminar una venta del historial", expanded=False):
        opciones_v = {}
        for _, r in vdf.iterrows():
            etq = (f"#{int(r['id'])} · {fecha_corta(r['fecha'])} · "
                   f"${float(r['monto_usd']):.2f} · "
                   f"{r['alumno'] or r['cliente_nombre'] or 'Anónimo'} · "
                   f"{r['estado']}")
            opciones_v[int(r["id"])] = etq
        vid = st.selectbox(
            "Selecciona la venta a eliminar",
            list(opciones_v.keys()),
            format_func=lambda x: opciones_v[x],
            key="elim_venta_sel",
        )
        fila = vdf[vdf["id"] == vid].iloc[0]
        st.markdown(
            f'<div class="ci" style="margin-top:6px">'
            f'<div class="t">Venta #{int(fila["id"])}</div>'
            f'<div class="s">{fila["fecha"]}</div>'
            f'<div class="s">Cliente: {fila["alumno"] or fila["cliente_nombre"] or "Anónimo"}</div>'
            f'<div class="s">Monto: ${float(fila["monto_usd"]):.2f} / Bs. {float(fila["monto_bs"]):,.2f}</div>'
            f'<div class="s">Estado: {fila["estado"]}</div>'
            f'<div class="s">Productos: {fila["detalles"]}</div></div>',
            unsafe_allow_html=True,
        )
        confirmar = st.checkbox(
            "Confirmo eliminar esta venta permanentemente",
            key="elim_venta_conf",
        )
        if st.button("Eliminar esta venta",
                     use_container_width=True,
                     disabled=not confirmar):
            eliminar_venta(vid)
            st.success(f"Venta #{vid} eliminada.")
            st.rerun()

    with st.expander("⚠️ Zona peligrosa", expanded=False):
        st.caption("Estas acciones no se pueden deshacer.")
        if st.button("Borrar TODAS las ventas",
                     use_container_width=True, key="wipe_ventas"):
            eliminar_todas_ventas()
            st.success("Historial borrado.")
            st.rerun()

    st.markdown('<div class="sec">Exportar</div>', unsafe_allow_html=True)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["ID", "Fecha", "Cliente", "Alumno", "Rep", "USD",
                "Bs", "Tasa", "Estado", "Detalles"])
    for _, r in vdf.iterrows():
        w.writerow([
            r["id"], r["fecha"], r["cliente_nombre"], r["alumno"],
            r["representante"], f"{float(r['monto_usd']):.2f}",
            f"{float(r['monto_bs']):.2f}", f"{float(r['tasa_usada']):.2f}",
            r["estado"], r["detalles"],
        ])

    hoy = datetime.now().strftime("%Y%m%d_%H%M")
    cA, cB = st.columns(2, gap="small")
    with cA:
        st.download_button(
            "Descargar CSV", buf.getvalue().encode("utf-8-sig"),
            f"ventas_{hoy}.csv", "text/csv", use_container_width=True,
        )
    with cB:
        st.download_button(
            "Descargar TXT", _reporte_txt(vdf, cfg).encode("utf-8"),
            f"reporte_{hoy}.txt", "text/plain", use_container_width=True,
)# ============================================================
# CONFIGURACIÓN
# ============================================================
def modulo_config(cfg: dict):
    st.markdown('<div class="sec">Tasas del día</div>', unsafe_allow_html=True)

    if obtener_tasa_activa(cfg) == 0:
        st.warning("⚠️ La tasa activa está en Bs. 0.00. Configúrala antes de vender.")

    with st.form("form_cfg"):
        c1, c2 = st.columns(2, gap="small")
        with c1:
            usd = st.number_input(
                "BCV USD (Bs/USD)", min_value=0.0,
                value=float(cfg.get("tasa_bcv_usd", 0) or 0),
                step=0.10, format="%.2f",
            )
        with c2:
            eur = st.number_input(
                "BCV EUR (Bs/EUR)", min_value=0.0,
                value=float(cfg.get("tasa_bcv_eur", 0) or 0),
                step=0.10, format="%.2f",
            )
        per = st.number_input(
            "Personalizada (Bs/USD)", min_value=0.0,
            value=float(cfg.get("tasa_personalizada", 0) or 0),
            step=0.10, format="%.2f",
        )
        tipo_actual = cfg.get("tasa_activa_tipo", "BCV USD")
        idx = TIPOS_TASA.index(tipo_actual) if tipo_actual in TIPOS_TASA else 0
        ta = st.selectbox("Tasa activa del día", list(TIPOS_TASA), index=idx)

        st.markdown('<div class="sec">Datos del negocio</div>',
                    unsafe_allow_html=True)
        neg = st.text_input("Nombre del negocio",
                            value=cfg.get("negocio_nombre", "Tu Cantina Express"))
        rif = st.text_input("RIF / Identificación",
                            value=cfg.get("negocio_rif", ""))

        if st.form_submit_button("Guardar configuración",
                                 type="primary", use_container_width=True):
            set_config("tasa_bcv_usd", f"{round(float(usd), 2):.2f}")
            set_config("tasa_bcv_eur", f"{round(float(eur), 2):.2f}")
            set_config("tasa_personalizada", f"{round(float(per), 2):.2f}")
            set_config("tasa_activa_tipo", ta)
            set_config("negocio_nombre", neg.strip())
            set_config("negocio_rif", rif.strip())
            st.success("Configuración guardada.")
            st.rerun()

    st.markdown(
        f'<div style="font-size:.68rem;color:#94a3b8;margin-top:10px;'
        f'text-align:center">Productos {len(get_productos())} · '
        f'Clientes {len(get_clientes())} · Ventas {len(get_ventas())}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# ESTADO / RESET
# ============================================================
def init_state():
    defaults = {
        "carrito": {},
        "busqueda": "",
        "cat_fil": "Todas",
        "cliente_sel": 0,
        "_reset_venta": False,
        "_reset_cliente": False,
        "_venta_msg": None,
        "_venta_estado": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def aplicar_reset_pendiente():
    if st.session_state.pop("_reset_venta", False):
        st.session_state.carrito = {}
        st.session_state.cliente_sel = 0

    if st.session_state.pop("_reset_cliente", False):
        st.session_state.cliente_sel = 0

    msg = st.session_state.pop("_venta_msg", None)
    est = st.session_state.pop("_venta_estado", None)
    if msg and est:
        if est == "Pagado":
            st.success(msg)
        else:
            st.warning(msg)


# ============================================================
# MAIN
# ============================================================
def main():
    inject_css()
    init_db()
    init_state()
    aplicar_reset_pendiente()

    cfg = get_config()
    render_header(cfg)

    t1, t2, t3, t4, t5 = st.tabs(["🛒", "👥", "➕", "📊", "⚙️"])
    with t1:
        modulo_pos(cfg)
    with t2:
        modulo_crm(cfg)
    with t3:
        modulo_productos(cfg)
    with t4:
        modulo_reportes(cfg)
    with t5:
        modulo_config(cfg)


if __name__ == "__main__":
    main()
