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

        .hdr{background:linear-gradient(135deg,#0e3a5a,#14496f);color:#fff;
             padding:9px 12px;border-radius:12px;box-shadow:0 3px 8px rgba(14,58,90,.28);
             margin-bottom:8px;}
        .hdr h1{font-size:1rem;margin:0;font-weight:800;letter-spacing:.2px;}
        .hdr .sub{font-size:.62rem;opacity:.82;margin-top:1px;}
        .pill{display:inline-block;background:rgba(243,156,18,.2);color:#f39c12;
              border:1px solid rgba(243,156,18,.5);padding:2px 7px;border-radius:20px;
              font-size:.6rem;font-weight:800;margin-right:4px;margin-top:4px;}
        .pill.g{background:rgba(39,174,96,.2);color:#27ae60;border-color:rgba(39,174,96,.5);}

        .sec{font-size:.76rem;font-weight:800;color:#0e3a5a;margin:6px 0 4px;
             border-left:3px solid #f39c12;padding-left:6px;}

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

        div.stButton>button{
            width:100%;border-radius:8px;font-weight:800;border:none;
            padding:.32rem .2rem;font-size:.76rem;line-height:1;min-height:0;
        }
        div.stButton>button[kind="primary"]{background:#f39c12;color:#fff;}
        div.stButton>button[kind="primary"]:hover{background:#d68910;color:#fff;}

        .mc{background:#fff;border-radius:10px;padding:7px 5px;text-align:center;
            box-shadow:0 1px 4px rgba(0,0,0,.06);border-left:3px solid #0e3a5a;
            margin-bottom:4px;}
        .mc .l{font-size:.58rem;color:#6c7a89;text-transform:uppercase;font-weight:800;letter-spacing:.3px;}
        .mc .v{font-size:.92rem;font-weight:900;color:#0e3a5a;margin-top:1px;}
        .mc.gold{border-left-color:#f39c12;}
        .mc.green{border-left-color:#27ae60;}
        .mc.red{border-left-color:#e74c3c;}

        .ci{background:#fff;border-radius:9px;padding:5px 8px;margin-bottom:4px;
            box-shadow:0 1px 3px rgba(0,0,0,.05);border:1px solid #eef1f4;}
        .ci .t{font-size:.76rem;font-weight:800;color:#0e3a5a;}
        .ci .s{font-size:.64rem;color:#6c7a89;line-height:1.25;}

        .stTabs [data-baseweb="tab-list"]{gap:2px;background:#eef1f4;padding:2px;border-radius:9px;}
        .stTabs [data-baseweb="tab"]{border-radius:7px;font-weight:800;font-size:.7rem;
                                     padding:4px 6px;color:#0e3a5a;min-height:0;}
        .stTabs [aria-selected="true"]{background:#0e3a5a!important;color:#fff!important;}
        .stTabs [data-baseweb="tab-highlight"]{display:none;}

        .stTextInput input,.stNumberInput input,
        .stSelectbox div[data-baseweb="select"]>div{
            border-radius:8px!important;font-size:.82rem!important;
        }

        .wa{display:block;text-align:center;background:#25D366;color:#fff!important;
            padding:5px 4px;border-radius:8px;font-weight:800;text-decoration:none;
            font-size:.68rem;line-height:1.1;}

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
    """Limpia teléfono. con_prefijo=True -> formato 58XXXXXXXXXX para wa.me"""
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
        )# ============================================================
# CALLBACKS DEL CARRITO
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
    st.session_state["_reset_cliente"] = True


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
# POS: FINALIZAR VENTA (sin tocar widgets ya instanciados)
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

    # Banderas de reset (NO tocar st.session_state.carrito ni cliente_sel aquí)
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

    # --- Filtros ---
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

    # --- Grid 2 columnas ---
    st.markdown('<div class="sec">📦 Catálogo</div>', unsafe_allow_html=True)

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
                        f'<div class="e">{r["emoji"] or "🍴"}</div>'
                        f'<div class="n">{r["nombre"]}</div>'
                        f'<div class="p">${float(r["precio_usd"]):.2f}</div>'
                        f'<div class="b">Bs. {pb:,.2f}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.button(
                        "➕ Agregar",
                        key=f"add_{r['id']}",
                        on_click=cb_add,
                        args=(int(r["id"]), r["emoji"] or "",
                              r["nombre"], float(r["precio_usd"])),
                        use_container_width=True,
                    )

    # --- Carrito ---
    st.markdown('<div class="sec">🛒 Carrito</div>', unsafe_allow_html=True)
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
                f'<div class="s">{item["qty"]}× ${item["precio"]:.2f} = '
                f'<b>${sub_usd:.2f}</b> · Bs. {sub_bs:,.2f}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            b1, b2 = st.columns(2, gap="small")
            with b1:
                st.button("➖", key=f"r_{k}", on_click=cb_dec, args=(k,),
                          use_container_width=True)
            with b2:
                st.button("➕", key=f"s_{k}", on_click=cb_inc, args=(k,),
                          use_container_width=True)
        with c3:
            st.button("🗑️", key=f"d_{k}", on_click=cb_del, args=(k,),
                      use_container_width=True)

    total_usd = carrito_total_usd()
    total_bs = round(total_usd * tasa, 2)

    st.markdown(
        f'<div class="car-total">'
        f'<div class="row"><span>Total USD</span><b>${total_usd:.2f}</b></div>'
        f'<div class="row big"><span>Total Bs.</span><b>Bs. {total_bs:,.2f}</b></div>'
        f'<div style="font-size:.6rem;opacity:.7;margin-top:3px">'
        f'Tasa aplicada: Bs. {tasa:,.2f}</div></div>',
        unsafe_allow_html=True,
    )

    # --- Asignación de cliente ---
    st.markdown('<div class="sec">👤 Cliente</div>', unsafe_allow_html=True)
    cdf = get_clientes()
    opciones = {0: "🧑 Venta Anónima"}
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
        if st.button("✅ Registrar Pago", type="primary", use_container_width=True):
            _finalizar_venta("Pagado", tasa)
            st.rerun()
    with cB:
        if st.button("🔴 Fiar", use_container_width=True):
            _finalizar_venta("Por cobrar", tasa)
            st.rerun()# ============================================================
# MÓDULO CRM
# ============================================================
def modulo_crm(cfg: dict):
    tasa = obtener_tasa_activa(cfg)
    st.markdown('<div class="sec">📇 Directorio</div>', unsafe_allow_html=True)

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
                f'<div class="s" style="margin-top:2px">Deuda: '
                f'<b style="color:{"#e74c3c" if tiene else "#27ae60"}">'
                f'${de["usd"]:.2f}</b> · Bs. {dbs:,.2f}</div></div>',
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns([2, 2, 1], gap="small")
            with c1:
                if tiene and st.button("💰 Abonar", key=f"ab_{cid}",
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
                            f'💬 WhatsApp</a>',
                            unsafe_allow_html=True,
                        )
            with c3:
                if tiene:
                    vk = f"vv_{cid}"
                    if st.button("📜", key=f"v_{cid}", use_container_width=True):
                        st.session_state[vk] = not st.session_state.get(vk, False)

            if tiene and st.session_state.get(f"vv_{cid}", False):
                vdf = get_ventas()
                pend = vdf[(vdf["cliente_id"] == cid)
                           & (vdf["estado"] == "Por cobrar")]
                for _, v in pend.iterrows():
                    s1, s2 = st.columns([5, 1], gap="small")
                    with s1:
                        st.markdown(
                            f'<div style="font-size:.62rem;color:#555;padding:2px 4px">'
                            f'🗓️ {v["fecha"][:16]} · ${float(v["monto_usd"]):.2f} · '
                            f'{v["detalles"]}</div>',
                            unsafe_allow_html=True,
                        )
                    with s2:
                        if st.button("✅", key=f"pv_{v['id']}",
                                     use_container_width=True):
                            abonar_venta(int(v["id"]))
                            st.rerun()

    st.markdown('<div class="sec">➕ Nuevo Cliente</div>', unsafe_allow_html=True)
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
        if st.form_submit_button("💾 Guardar Cliente", use_container_width=True):
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
    st.markdown('<div class="sec">➕ Nuevo Producto</div>', unsafe_allow_html=True)

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
        if st.form_submit_button("💾 Guardar Producto", use_container_width=True):
            if not nom.strip():
                st.error("El nombre es obligatorio.")
            elif pr <= 0:
                st.error("El precio debe ser mayor a 0.")
            else:
                add_producto(em, nom, pr, co, cat, sku)
                st.success(f"'{nom.strip()}' agregado.")
                st.rerun()

    st.markdown('<div class="sec">📦 Catálogo Actual</div>', unsafe_allow_html=True)
    pdf = get_productos()
    if pdf.empty:
        st.info("No hay productos registrados todavía.")
    else:
        v = pdf.copy()
        v["Precio Bs."] = (v["precio_usd"] * tasa).round(2)
        v = v.rename(columns={
            "emoji": "🎨", "nombre": "Producto", "precio_usd": "$",
            "costo_usd": "Costo $", "categoria": "Categoría", "sku": "SKU",
        })
        st.dataframe(
            v[["🎨", "Producto", "Categoría", "$", "Precio Bs.", "Costo $", "SKU"]],
            use_container_width=True, hide_index=True,
        )
        st.markdown('<div class="sec">🗑️ Eliminar Producto</div>',
                    unsafe_allow_html=True)
        opciones = {int(r["id"]): f"{r['emoji']} {r['nombre']}"
                    for _, r in pdf.iterrows()}
        pid = st.selectbox("Selecciona un producto", list(opciones.keys()),
                           format_func=lambda x: opciones[x],
                           label_visibility="collapsed")
        if st.button("🗑️ Eliminar definitivamente", use_container_width=True):
            eliminar_producto(pid)
            st.success("Producto eliminado.")
            st.rerun()


# ============================================================
# MÓDULO REPORTES
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
        metric_card("Ganancia Est.", f"${gan:,.2f}", "green")
    c3, c4 = st.columns(2, gap="small")
    with c3:
        metric_card("Deuda", f"${deu:,.2f}", "red")
    with c4:
        metric_card("Operaciones", f"{n}")

    st.markdown(
        f'<div style="text-align:center;font-size:.62rem;color:#6c7a89;'
        f'margin-top:2px">Facturado Bs. {tb:,.2f} · Tasa Bs. {tasa:,.2f}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sec">📊 Historial</div>', unsafe_allow_html=True)
    if vdf.empty:
        st.info("Sin ventas registradas.")
        return

    v = vdf.rename(columns={
        "id": "ID", "fecha": "Fecha", "alumno": "Alumno",
        "representante": "Rep", "monto_usd": "USD", "monto_bs": "Bs.",
        "tasa_usada": "Tasa", "estado": "Estado", "detalles": "Productos",
    })
    st.dataframe(
        v[["ID", "Fecha", "Alumno", "Rep", "USD", "Bs.", "Tasa",
           "Estado", "Productos"]],
        use_container_width=True, hide_index=True,
    )

    st.markdown('<div class="sec">⬇️ Exportar</div>', unsafe_allow_html=True)
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
            "📄 CSV", buf.getvalue().encode("utf-8-sig"),
            f"ventas_{hoy}.csv", "text/csv", use_container_width=True,
        )
    with cB:
        st.download_button(
            "📝 TXT", _reporte_txt(vdf, cfg).encode("utf-8"),
            f"reporte_{hoy}.txt", "text/plain", use_container_width=True,
        )


# ============================================================
# MÓDULO CONFIGURACIÓN
# ============================================================
def modulo_config(cfg: dict):
    st.markdown('<div class="sec">⚙️ Ajustes de Tasas</div>', unsafe_allow_html=True)
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

        st.markdown("**Datos del negocio**")
        neg = st.text_input("Nombre del negocio",
                            value=cfg.get("negocio_nombre", "Tu Cantina Express"))
        rif = st.text_input("RIF / Identificación",
                            value=cfg.get("negocio_rif", ""))

        if st.form_submit_button("💾 Guardar Configuración",
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
        f'<div style="font-size:.7rem;color:#6c7a89;margin-top:6px">'
        f'<b>Sistema</b><br>DB: <code>cantina.db</code><br>'
        f'Productos: {len(get_productos())} · '
        f'Clientes: {len(get_clientes())} · '
        f'Ventas: {len(get_ventas())}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# INICIALIZACIÓN DE ESTADO + RESET PENDIENTE
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
    """Aplica resets ANTES de instanciar widgets en el nuevo ciclo."""
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

    t1, t2, t3, t4, t5 = st.tabs(
        ["🛒 POS", "👥 CRM", "➕ Prod", "📊 Rep", "⚙️ Ajustes"]
    )
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
