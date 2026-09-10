# -*- coding: utf-8 -*-
"""
============================================================
 TU CANTINA EXPRESS - POS & CRM LOCAL
 ------------------------------------------------------------
 Autor: Full-Stack Senior
 Stack: Python 3.10+, Streamlit, SQLite3
 Diseño: Mobile-First / Touch-Friendly
 Ejecución: streamlit run app_cantina.py
============================================================
"""

import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime
from pathlib import Path
import io
import csv

# ============================================================
# 1. CONFIGURACIÓN GLOBAL DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="Tu Cantina Express",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DB_PATH = Path("cantina.db")

# ============================================================
# 2. ESTILOS CSS PERSONALIZADOS (UI/UX MOBILE-FIRST)
# ============================================================
def inject_css():
    st.markdown(
        """
        <style>
        /* Ocultar elementos de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        [data-testid="stToolbar"] {display: none;}

        /* Contenedor principal */
        .main .block-container {
            padding: 0.6rem 0.7rem 6rem 0.7rem;
            max-width: 640px;
            margin: 0 auto;
        }

        /* Paleta corporativa */
        :root {
            --azul: #0e3a5a;
            --azul-oscuro: #082a41;
            --dorado: #f39c12;
            --verde: #27ae60;
            --rojo: #e74c3c;
            --gris-claro: #f4f6f8;
        }

        /* Header banner */
        .cantina-header {
            background: linear-gradient(135deg, #0e3a5a 0%, #14496f 100%);
            color: #fff;
            padding: 14px 16px;
            border-radius: 16px;
            box-shadow: 0 4px 14px rgba(14,58,90,0.35);
            margin-bottom: 12px;
        }
        .cantina-header h1 {
            font-size: 1.25rem;
            margin: 0;
            font-weight: 700;
            letter-spacing: .3px;
        }
        .cantina-header .sub {
            font-size: 0.78rem;
            opacity: 0.85;
            margin-top: 2px;
        }
        .tasa-pill {
            display: inline-block;
            background: rgba(243,156,18,0.18);
            color: #f39c12;
            border: 1px solid rgba(243,156,18,0.45);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            margin-right: 6px;
            margin-top: 6px;
        }
        .tasa-pill.green {
            background: rgba(39,174,96,0.18);
            color: #2ecc71;
            border-color: rgba(39,174,96,0.45);
        }

        /* Tarjetas de producto */
        .prod-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 10px 6px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #e8ecf1;
            transition: transform .12s ease;
            height: 100%;
        }
        .prod-card .emoji { font-size: 1.7rem; line-height: 1; }
        .prod-card .name {
            font-size: 0.78rem;
            font-weight: 700;
            color: #0e3a5a;
            margin-top: 4px;
            line-height: 1.1;
            min-height: 2.1em;
        }
        .prod-card .price {
            font-size: 0.82rem;
            font-weight: 800;
            color: #f39c12;
            margin-top: 4px;
        }
        .prod-card .bs {
            font-size: 0.68rem;
            color: #6c7a89;
        }

        /* Botones generales */
        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            font-weight: 700;
            border: none;
            padding: 0.55rem 0.4rem;
            font-size: 0.88rem;
        }
        div.stButton > button[kind="primary"] {
            background: #f39c12;
            color: #fff;
        }
        div.stButton > button[kind="primary"]:hover {
            background: #d68910;
            color: #fff;
        }

        /* Métricas */
        .metric-card {
            background: #fff;
            border-radius: 14px;
            padding: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-left: 4px solid #0e3a5a;
        }
        .metric-card .label {
            font-size: 0.72rem;
            color: #6c7a89;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: .5px;
        }
        .metric-card .value {
            font-size: 1.15rem;
            font-weight: 800;
            color: #0e3a5a;
            margin-top: 3px;
        }
        .metric-card.gold { border-left-color: #f39c12; }
        .metric-card.green { border-left-color: #27ae60; }
        .metric-card.red { border-left-color: #e74c3c; }

        /* Carrito items */
        .cart-item {
            background: #fff;
            border-radius: 12px;
            padding: 8px 10px;
            margin-bottom: 6px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            border: 1px solid #eef1f4;
        }
        .cart-item .titulo {
            font-size: 0.85rem;
            font-weight: 700;
            color: #0e3a5a;
        }
        .cart-item .sub {
            font-size: 0.72rem;
            color: #6c7a89;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: #eef1f4;
            padding: 4px;
            border-radius: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.82rem;
            padding: 6px 10px;
            color: #0e3a5a;
        }
        .stTabs [aria-selected="true"] {
            background: #0e3a5a !important;
            color: #fff !important;
        }

        /* Inputs */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
            border-radius: 10px !important;
        }

        /* Sección títulos */
        .sec-title {
            font-size: 0.9rem;
            font-weight: 800;
            color: #0e3a5a;
            margin: 10px 0 6px 0;
            border-left: 4px solid #f39c12;
            padding-left: 8px;
        }

        /* WhatsApp button */
        .wa-btn a {
            display: inline-block;
            background: #25D366;
            color: #fff !important;
            padding: 6px 12px;
            border-radius: 10px;
            font-weight: 700;
            text-decoration: none !important;
            font-size: 0.78rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 3. CAPA DE BASE DE DATOS (SQLite con Context Managers)
# ============================================================
def init_db():
    """Crea todas las tablas necesarias si no existen y siembra datos iniciales."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                llave TEXT PRIMARY KEY,
                valor TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emoji TEXT,
                nombre TEXT NOT NULL,
                precio_usd REAL NOT NULL,
                costo_usd REAL DEFAULT 0,
                categoria TEXT,
                sku TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                alumno TEXT,
                representante TEXT,
                telefono TEXT,
                categoria TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                cliente_id INTEGER,
                cliente_nombre TEXT,
                alumno TEXT,
                representante TEXT,
                monto_usd REAL,
                monto_bs REAL,
                tasa_usada REAL,
                estado TEXT,
                detalles TEXT
            )
        """)
        conn.commit()

        # Configuración por defecto
        defaults = {
            "tasa_bcv_usd": "36.50",
            "tasa_bcv_eur": "39.80",
            "tasa_personalizada": "0.00",
            "tasa_activa_tipo": "BCV USD",
            "negocio_nombre": "Tu Cantina Express",
            "negocio_rif": "J-00000000-0",
        }
        for k, v in defaults.items():
            cur.execute(
                "INSERT OR IGNORE INTO configuracion (llave, valor) VALUES (?, ?)",
                (k, v),
            )
        conn.commit()

        # Productos demo
        cur.execute("SELECT COUNT(*) FROM productos")
        if cur.fetchone()[0] == 0:
            demo = [
                ("🥤", "Refresco 350ml", 1.20, 0.70, "Bebidas", "BEB001"),
                ("💧", "Agua 600ml", 0.80, 0.40, "Bebidas", "BEB002"),
                ("🧃", "Jugo Natural", 1.50, 0.90, "Bebidas", "BEB003"),
                ("🍔", "Hamburguesa", 3.50, 2.00, "Comidas", "COM001"),
                ("🌭", "Perro Caliente", 2.50, 1.30, "Comidas", "COM002"),
                ("🍕", "Porción Pizza", 2.00, 1.10, "Comidas", "COM003"),
                ("🥟", "Empanada", 1.00, 0.45, "Comidas", "COM004"),
                ("🍰", "Torta de Chocolate", 1.80, 0.90, "Postres", "POS001"),
                ("🍪", "Galleta", 0.60, 0.25, "Postres", "POS002"),
                ("🍫", "Chocolate", 1.10, 0.55, "Postres", "POS003"),
            ]
            cur.executemany(
                "INSERT INTO productos (emoji, nombre, precio_usd, costo_usd, categoria, sku) VALUES (?,?,?,?,?,?)",
                demo,
            )
            conn.commit()

        # Cliente demo
        cur.execute("SELECT COUNT(*) FROM clientes")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO clientes (nombre, alumno, representante, telefono, categoria) VALUES (?,?,?,?,?)",
                ("Familia Demo", "Juan Pérez", "María Pérez", "04141234567", "Alumno"),
            )
            conn.commit()


# --- Funciones CRUD ---
def get_config() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT llave, valor FROM configuracion")
        return dict(cur.fetchall())


def set_config(llave: str, valor: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO configuracion (llave, valor) VALUES (?, ?) "
            "ON CONFLICT(llave) DO UPDATE SET valor=excluded.valor",
            (llave, str(valor)),
        )
        conn.commit()


def get_productos() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM productos ORDER BY categoria, nombre", conn
        )


def add_producto(emoji, nombre, precio_usd, costo_usd, categoria, sku):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO productos (emoji, nombre, precio_usd, costo_usd, categoria, sku) "
            "VALUES (?,?,?,?,?,?)",
            (emoji, nombre, round(precio_usd, 2), round(costo_usd, 2), categoria, sku),
        )
        conn.commit()


def get_clientes() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM clientes ORDER BY alumno COLLATE NOCASE", conn
        )


def add_cliente(nombre, alumno, representante, telefono, categoria):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO clientes (nombre, alumno, representante, telefono, categoria) "
            "VALUES (?,?,?,?,?)",
            (nombre, alumno, representante, telefono, categoria),
        )
        conn.commit()


def registrar_venta(
    cliente_id, cliente_nombre, alumno, representante,
    monto_usd, monto_bs, tasa_usada, estado, detalles
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO ventas
            (fecha, cliente_id, cliente_nombre, alumno, representante,
             monto_usd, monto_bs, tasa_usada, estado, detalles)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                cliente_id,
                cliente_nombre,
                alumno,
                representante,
                round(monto_usd, 2),
                round(monto_bs, 2),
                round(tasa_usada, 2),
                estado,
                detalles,
            ),
        )
        conn.commit()


def get_ventas() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM ventas ORDER BY id DESC", conn
        )


def get_deudas_por_cliente() -> pd.DataFrame:
    """Devuelve deuda acumulada por cliente (agrupada)."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT cliente_id, cliente_nombre, alumno, representante,
                   SUM(monto_usd) AS deuda_usd,
                   SUM(monto_bs) AS deuda_bs,
                   COUNT(*) AS num_ventas
            FROM ventas
            WHERE estado = 'Por cobrar'
            GROUP BY cliente_id, cliente_nombre, alumno, representante
            ORDER BY deuda_usd DESC
            """,
            conn,
        )


def abonar_deuda_cliente(cliente_id: int):
    """Marca como 'Pagado' todas las ventas pendientes de un cliente."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE ventas SET estado = 'Pagado' WHERE cliente_id = ? AND estado = 'Por cobrar'",
            (cliente_id,),
        )
        conn.commit()


def abonar_venta_individual(venta_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE ventas SET estado = 'Pagado' WHERE id = ?", (venta_id,)
        )
        conn.commit()


# ============================================================
# 4. UTILIDADES
# ============================================================
def sanitizar_telefono(tel: str) -> str:
    """
    Limpia el número de teléfono y devuelve formato internacional VE (58XXXXXXXXXX).
    Elimina espacios, guiones, paréntesis, signos + y ceros iniciales.
    """
    if not tel:
        return ""
    limpio = "".join(ch for ch in str(tel) if ch.isdigit())
    if not limpio:
        return ""
    # Quitar ceros iniciales (ej: 0414 -> 414)
    limpio = limpio.lstrip("0")
    # Si ya empieza con 58 y tiene 12 dígitos, lo dejamos
    if limpio.startswith("58") and len(limpio) >= 12:
        return limpio
    # Si es número local venezolano (10 dígitos) -> 58 + número
    if len(limpio) == 10:
        return "58" + limpio
    # Otros casos: prepend 58 si parece local
    return "58" + limpio


def formatear_usd(v: float) -> str:
    return f"${round(float(v or 0), 2):,.2f}"


def formatear_bs(v: float) -> str:
    return f"Bs. {round(float(v or 0), 2):,.2f}"


def obtener_tasa_activa(config: dict) -> float:
    tipo = config.get("tasa_activa_tipo", "BCV USD")
    try:
        if tipo == "BCV USD":
            return float(config.get("tasa_bcv_usd", 0))
        if tipo == "BCV EUR":
            return float(config.get("tasa_bcv_eur", 0))
        if tipo == "Personalizada":
            return float(config.get("tasa_personalizada", 0))
    except (ValueError, TypeError):
        return 0.0
    return 0.0


def generar_enlace_whatsapp(telefono: str, mensaje: str) -> str:
    tel = sanitizar_telefono(telefono)
    if not tel:
        return ""
    return f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"


def construir_mensaje_recordatorio(representante: str, alumno: str,
                                   monto_usd: float, monto_bs: float) -> str:
    rep = representante.strip() if representante else "Representante"
    alu = alumno.strip() if alumno else "su representado"
    return (
        f"Hola {rep}, le saludamos de Tu Cantina Express. "
        f"Le recordamos el saldo pendiente del día de su representado {alu}: "
        f"${round(float(monto_usd), 2):,.2f} USD "
        f"(equivalente a Bs. {round(float(monto_bs), 2):,.2f} a la tasa de hoy). "
        f"¡Muchas gracias!"
    )


# ============================================================
# 5. ESTADO DE SESIÓN
# ============================================================
def init_session_state():
    if "carrito" not in st.session_state:
        # estructura: { product_id: {"emoji","nombre","precio_usd","cantidad"} }
        st.session_state.carrito = {}
    if "busqueda" not in st.session_state:
        st.session_state.busqueda = ""
    if "categoria_filtro" not in st.session_state:
        st.session_state.categoria_filtro = "Todas"
    if "cliente_sel_id" not in st.session_state:
        st.session_state.cliente_sel_id = 0  # 0 = anónimo


def carrito_add(pid: int, prod_row: pd.Series):
    carrito = st.session_state.carrito
    key = str(pid)
    if key in carrito:
        carrito[key]["cantidad"] += 1
    else:
        carrito[key] = {
            "emoji": prod_row["emoji"],
            "nombre": prod_row["nombre"],
            "precio_usd": float(prod_row["precio_usd"]),
            "costo_usd": float(prod_row["costo_usd"] or 0),
            "cantidad": 1,
        }
    st.session_state.carrito = carrito


def carrito_sumar(key: str):
    if key in st.session_state.carrito:
        st.session_state.carrito[key]["cantidad"] += 1


def carrito_restar(key: str):
    if key in st.session_state.carrito:
        st.session_state.carrito[key]["cantidad"] -= 1
        if st.session_state.carrito[key]["cantidad"] <= 0:
            del st.session_state.carrito[key]


def carrito_eliminar(key: str):
    if key in st.session_state.carrito:
        del st.session_state.carrito[key]


def carrito_total_usd() -> float:
    return round(
        sum(v["precio_usd"] * v["cantidad"] for v in st.session_state.carrito.values()),
        2,
    )


def carrito_total_costo_usd() -> float:
    return round(
        sum(v.get("costo_usd", 0) * v["cantidad"] for v in st.session_state.carrito.values()),
        2,
    )


def carrito_vacio() -> bool:
    return len(st.session_state.carrito) == 0


def carrito_detalle_txt() -> str:
    partes = []
    for v in st.session_state.carrito.values():
        partes.append(f"{v['cantidad']}x {v['nombre']} (${v['precio_usd']:.2f})")
    return " | ".join(partes)


# ============================================================
# 6. COMPONENTES UI
# ============================================================
def render_header(config: dict):
    tasa_usd = float(config.get("tasa_bcv_usd", 0) or 0)
    tasa_eur = float(config.get("tasa_bcv_eur", 0) or 0)
    tipo = config.get("tasa_activa_tipo", "BCV USD")
    tasa_activa = obtener_tasa_activa(config)

    st.markdown(
        f"""
        <div class="cantina-header">
            <h1>🍽️ Tu Cantina Express</h1>
            <div class="sub">Punto de Venta & CRM · {datetime.now().strftime('%d/%m/%Y')}</div>
            <div>
                <span class="tasa-pill green">TASA ACTIVA ({tipo}): Bs. {tasa_activa:,.2f}</span>
                <span class="tasa-pill">USD: {tasa_usd:,.2f}</span>
                <span class="tasa-pill">EUR: {tasa_eur:,.2f}</span>
            </div>
        </div>
        """,
       
