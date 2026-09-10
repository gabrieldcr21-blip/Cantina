# -*- coding: utf-8 -*-
import streamlit as st, sqlite3, pandas as pd, urllib.parse, io, csv
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Tu Cantina Express", page_icon="🍽️", layout="centered")
DB_PATH = Path("cantina.db")

# ---------- CSS ----------
def inject_css():
    st.markdown("""<style>
    #MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"]{display:none!important;}
    .main .block-container{padding:.5rem .7rem 6rem .7rem;max-width:640px;margin:auto;}
    .hdr{background:linear-gradient(135deg,#0e3a5a,#14496f);color:#fff;padding:12px 14px;
         border-radius:14px;box-shadow:0 4px 12px rgba(14,58,90,.3);margin-bottom:10px;}
    .hdr h1{font-size:1.15rem;margin:0;font-weight:700;}
    .hdr .sub{font-size:.72rem;opacity:.85;margin-top:2px;}
    .pill{display:inline-block;background:rgba(243,156,18,.18);color:#f39c12;
          border:1px solid rgba(243,156,18,.45);padding:3px 9px;border-radius:20px;
          font-size:.68rem;font-weight:700;margin-right:5px;margin-top:5px;}
    .pill.g{background:rgba(39,174,96,.18);color:#2ecc71;border-color:rgba(39,174,96,.45);}
    .pcard{background:#fff;border-radius:12px;padding:8px 4px;text-align:center;
           box-shadow:0 2px 6px rgba(0,0,0,.08);border:1px solid #e8ecf1;}
    .pcard .e{font-size:1.6rem;}
    .pcard .n{font-size:.74rem;font-weight:700;color:#0e3a5a;margin-top:3px;line-height:1.1;min-height:2em;}
    .pcard .p{font-size:.8rem;font-weight:800;color:#f39c12;margin-top:3px;}
    .pcard .b{font-size:.66rem;color:#6c7a89;}
    div.stButton>button{width:100%;border-radius:10px;font-weight:700;border:none;padding:.5rem .3rem;font-size:.85rem;}
    div.stButton>button[kind="primary"]{background:#f39c12;color:#fff;}
    .mc{background:#fff;border-radius:12px;padding:10px;text-align:center;
        box-shadow:0 2px 6px rgba(0,0,0,.06);border-left:4px solid #0e3a5a;margin-bottom:6px;}
    .mc .l{font-size:.68rem;color:#6c7a89;text-transform:uppercase;font-weight:700;}
    .mc .v{font-size:1.1rem;font-weight:800;color:#0e3a5a;margin-top:2px;}
    .mc.gold{border-left-color:#f39c12;}.mc.green{border-left-color:#27ae60;}.mc.red{border-left-color:#e74c3c;}
    .ci{background:#fff;border-radius:10px;padding:6px 9px;margin-bottom:5px;
        box-shadow:0 1px 3px rgba(0,0,0,.06);border:1px solid #eef1f4;}
    .ci .t{font-size:.82rem;font-weight:700;color:#0e3a5a;}
    .ci .s{font-size:.7rem;color:#6c7a89;}
    .stTabs [data-baseweb="tab-list"]{gap:3px;background:#eef1f4;padding:3px;border-radius:10px;}
    .stTabs [data-baseweb="tab"]{border-radius:8px;font-weight:700;font-size:.78rem;padding:5px 8px;color:#0e3a5a;}
    .stTabs [aria-selected="true"]{background:#0e3a5a!important;color:#fff!important;}
    .sec{font-size:.86rem;font-weight:800;color:#0e3a5a;margin:8px 0 5px;border-left:3px solid #f39c12;padding-left:7px;}
    .wa{display:block;text-align:center;background:#25D366;color:#fff!important;padding:7px 6px;
        border-radius:9px;font-weight:700;text-decoration:none;font-size:.76rem;}
    </style>""", unsafe_allow_html=True)

# ---------- DB ----------
def init_db():
    with sqlite3.connect(DB_PATH) as c:
        cur = c.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS configuracion(llave TEXT PRIMARY KEY,valor TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS productos(id INTEGER PRIMARY KEY AUTOINCREMENT,emoji TEXT,nombre TEXT NOT NULL,precio_usd REAL NOT NULL,costo_usd REAL DEFAULT 0,categoria TEXT,sku TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS clientes(id INTEGER PRIMARY KEY AUTOINCREMENT,nombre TEXT NOT NULL,alumno TEXT,representante TEXT,telefono TEXT,categoria TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS ventas(id INTEGER PRIMARY KEY AUTOINCREMENT,fecha TEXT,cliente_id INTEGER,cliente_nombre TEXT,alumno TEXT,representante TEXT,monto_usd REAL,monto_bs REAL,tasa_usada REAL,estado TEXT,detalles TEXT)")
        for k,v in {"tasa_bcv_usd":"36.50","tasa_bcv_eur":"39.80","tasa_personalizada":"0.00","tasa_activa_tipo":"BCV USD","negocio_nombre":"Tu Cantina Express","negocio_rif":""}.items():
            cur.execute("INSERT OR IGNORE INTO configuracion VALUES(?,?)",(k,v))
        c.commit()
        if cur.execute("SELECT COUNT(*) FROM productos").fetchone()[0]==0:
            demo=[("🥤","Refresco 350ml",1.20,0.70,"Bebidas","BEB001"),("💧","Agua 600ml",0.80,0.40,"Bebidas","BEB002"),("🧃","Jugo Natural",1.50,0.90,"Bebidas","BEB003"),("🍔","Hamburguesa",3.50,2.00,"Comidas","COM001"),("🌭","Perro Caliente",2.50,1.30,"Comidas","COM002"),("🍕","Porción Pizza",2.00,1.10,"Comidas","COM003"),("🥟","Empanada",1.00,0.45,"Comidas","COM004"),("🍰","Torta Chocolate",1.80,0.90,"Postres","POS001"),("🍪","Galleta",0.60,0.25,"Postres","POS002"),("🍫","Chocolate",1.10,0.55,"Postres","POS003")]
            cur.executemany("INSERT INTO productos(emoji,nombre,precio_usd,costo_usd,categoria,sku)VALUES(?,?,?,?,?,?)",demo); c.commit()
        if cur.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]==0:
            cur.execute("INSERT INTO clientes(nombre,alumno,representante,telefono,categoria)VALUES(?,?,?,?,?)",("Familia Demo","Juan Pérez","María Pérez","04141234567","Alumno")); c.commit()

def get_config():
    with sqlite3.connect(DB_PATH) as c: return dict(c.execute("SELECT llave,valor FROM configuracion").fetchall())
def set_config(k,v):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT INTO configuracion VALUES(?,?)ON CONFLICT(llave)DO UPDATE SET valor=excluded.valor",(k,str(v))); c.commit()
def get_productos():
    with sqlite3.connect(DB_PATH) as c: return pd.read_sql_query("SELECT * FROM productos ORDER BY categoria,nombre",c)
def add_producto(e,n,p,co,cat,sku):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT INTO productos(emoji,nombre,precio_usd,costo_usd,categoria,sku)VALUES(?,?,?,?,?,?)",(e,n,round(p,2),round(co,2),cat,sku)); c.commit()
def get_clientes():
    with sqlite3.connect(DB_PATH) as c: return pd.read_sql_query("SELECT * FROM clientes ORDER BY alumno COLLATE NOCASE",c)
def add_cliente(n,a,r,t,cat):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT INTO clientes(nombre,alumno,representante,telefono,categoria)VALUES(?,?,?,?,?)",(n,a,r,t,cat)); c.commit()
def registrar_venta(cid,cn,al,rep,mu,mb,ta,es,det):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT INTO ventas(fecha,cliente_id,cliente_nombre,alumno,representante,monto_usd,monto_bs,tasa_usada,estado,detalles)VALUES(?,?,?,?,?,?,?,?,?,?)",(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),cid,cn,al,rep,round(mu,2),round(mb,2),round(ta,2),es,det)); c.commit()
def get_ventas():
    with sqlite3.connect(DB_PATH) as c: return pd.read_sql_query("SELECT * FROM ventas ORDER BY id DESC",c)
def get_deudas():
    with sqlite3.connect(DB_PATH) as c:
        return pd.read_sql_query("SELECT cliente_id,cliente_nombre,alumno,representante,SUM(monto_usd)deuda_usd,SUM(monto_bs)deuda_bs,COUNT(*)num_ventas FROM ventas WHERE estado='Por cobrar' GROUP BY cliente_id,cliente_nombre,alumno,representante ORDER BY deuda_usd DESC",c)
def abonar_cliente(cid):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("UPDATE ventas SET estado='Pagado' WHERE cliente_id=? AND estado='Por cobrar'",(cid,)); c.commit()
def abonar_venta(vid):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("UPDATE ventas SET estado='Pagado' WHERE id=?",(vid,)); c.commit()

# ---------- Utils ----------
def sanit_tel(t):
    if not t: return ""
    d="".join(ch for ch in str(t) if ch.isdigit()).lstrip("0")
    if not d: return ""
    if d.startswith("58") and len(d)>=12: return d
    if len(d)==10: return "58"+d
    return "58"+d
def tasa_activa(cfg):
    t=cfg.get("tasa_activa_tipo","BCV USD")
    try:
        if t=="BCV USD": return float(cfg.get("tasa_bcv_usd",0) or 0)
        if t=="BCV EUR": return float(cfg.get("tasa_bcv_eur",0) or 0)
        if t=="Personalizada": return float(cfg.get("tasa_personalizada",0) or 0)
    except: return 0.0
    return 0.0
def wa_link(tel,msg):
    t=sanit_tel(tel)
    return "" if not t else "https://wa.me/"+t+"?text="+urllib.parse.quote(msg)
def msg_recordatorio(rep,al,mu,mb):
    return f"Hola {rep or 'Representante'}, le saludamos de Tu Cantina Express. Le recordamos el saldo pendiente del día de su representado {al or 'su representado'}: ${round(float(mu),2):,.2f} USD (equivalente a Bs. {round(float(mb),2):,.2f} a la tasa de hoy). ¡Muchas gracias!"

# ---------- State ----------
def init_state():
    for k,v in {"carrito":{},"busqueda":"","categoria_filtro":"Todas","cliente_sel_id":0}.items():
        if k not in st.session_state: st.session_state[k]=v
def c_add(pid,row):
    k=str(pid); car=st.session_state.carrito
    if k in car: car[k]["cantidad"]+=1
    else: car[k]={"emoji":row["emoji"],"nombre":row["nombre"],"precio_usd":float(row["precio_usd"]),"cantidad":1}
    st.session_state.carrito=car
def c_mas(k):
    if k in st.session_state.carrito: st.session_state.carrito[k]["cantidad"]+=1
def c_menos(k):
    if k in st.session_state.carrito:
        st.session_state.carrito[k]["cantidad"]-=1
        if st.session_state.carrito[k]["cantidad"]<=0: del st.session_state.carrito[k]
def c_del(k):
    if k in st.session_state.carrito: del st.session_state.carrito[k]
def c_total(): return round(sum(v["precio_usd"]*v["cantidad"] for v in st.session_state.carrito.values()),2)
def c_detalle(): return " | ".join(f"{v['cantidad']}x {v['nombre']} (${v['precio_usd']:.2f})" for v in st.session_state.carrito.values())

# ---------- UI helpers ----------
def render_header(cfg):
    t=tasa_activa(cfg)
    st.markdown(f"""<div class="hdr"><h1>🍽️ Tu Cantina Express</h1>
    <div class="sub">POS & CRM · {datetime.now().strftime('%d/%m/%Y')}</div>
    <div><span class="pill g">TASA ({cfg.get('tasa_activa_tipo','')}): Bs. {t:,.2f}</span>
    <span class="pill">USD: {float(cfg.get('tasa_bcv_usd',0) or 0):,.2f}</span>
    <span class="pill">EUR: {float(cfg.get('tasa_bcv_eur',0) or 0):,.2f}</span></div></div>""",unsafe_allow_html=True)
def metric(l,v,cls=""):
    st.markdown(f'<div class="mc {cls}"><div class="l">{l}</div><div class="v">{v}</div></div>',unsafe_allow_html=True)

# ---------- POS ----------
def finalizar_venta(estado,tasa,tu,tb):
    cid=st.session_state.cliente_sel_id
    if cid and cid!=0:
        df=get_clientes(); r=df[df["id"]==cid]
        if not r.empty:
            rr=r.iloc[0]; cn,al,rep=rr["nombre"],rr["alumno"],rr["representante"]
        else: cid,cn,al,rep=0,"Anónimo","",""
    else: cid,cn,al,rep=0,"Anónimo","",""
    registrar_venta(cid,cn,al,rep,tu,tb,tasa,estado,c_detalle())
    st.session_state.carrito={}; st.session_state.cliente_sel_id=0
    (st.success if estado=="Pagado" else st.warning)(f"{'✅ Pagado' if estado=='Pagado' else '🔴 Fiado'}: ${tu:.2f} / Bs. {tb:,.2f}")

def modulo_pos(cfg):
    tasa=tasa_activa(cfg); pdf=get_productos()
    if pdf.empty: st.warning("Sin productos."); return
    cats=["Todas"]+sorted(pdf["categoria"].dropna().unique().tolist())
    c1,c2=st.columns([3,2])
    with c1: st.session_state.busqueda=st.text_input("🔍",value=st.session_state.busqueda,placeholder="Buscar...",label_visibility="collapsed")
    with c2:
        i=cats.index(st.session_state.categoria_filtro) if st.session_state.categoria_filtro in cats else 0
        st.session_state.categoria_filtro=st.selectbox("Cat",cats,index=i,label_visibility="collapsed")
    df=pdf.copy()
    if st.session_state.busqueda.strip(): df=df[df["nombre"].str.lower().str.contains(st.session_state.busqueda.strip().lower(),na=False)]
    if st.session_state.categoria_filtro!="Todas": df=df[df["categoria"]==st.session_state.categoria_filtro]
    st.markdown('<div class="sec">📦 Catálogo</div>',unsafe_allow_html=True)
    if df.empty: st.info("Sin resultados.")
    else:
        cols=st.columns(3)
        for i,(_,r) in enumerate(df.iterrows()):
            with cols[i%3]:
                pb=round(r["precio_usd"]*tasa,2)
                st.markdown(f'<div class="pcard"><div class="e">{r["emoji"] or "🍴"}</div><div class="n">{r["nombre"]}</div><div class="p">${r["precio_usd"]:.2f}</div><div class="b">Bs. {pb:,.2f}</div></div>',unsafe_allow_html=True)
                if st.button("➕",key=f"a_{r['id']}"): c_add(int(r["id"]),r); st.rerun()
    st.markdown("---"); st.markdown('<div class="sec">🛒 Carrito</div>',unsafe_allow_html=True)
    if not st.session_state.carrito: st.info("Carrito vacío."); return
    for k,it in list(st.session_state.carrito.items()):
        sub=round(it["precio_usd"]*it["cantidad"],2); sbs=round(sub*tasa,2)
        c1,c2,c3=st.columns([5,3,2])
        with c1: st.markdown(f'<div class="ci"><div class="t">{it["emoji"]} {it["nombre"]}</div><div class="s">{it["cantidad"]}×${it["precio_usd"]:.2f}=<b>${sub:.2f}</b> · Bs. {sbs:,.2f}</div></div>',unsafe_allow_html=True)
        with c2:
            b1,b2,b3=st.columns(3)
            with b1:
                if st.button("➖",key=f"r_{k}"): c_menos(k); st.rerun()
            with b2:
                if st.button("➕",key=f"s_{k}"): c_mas(k); st.rerun()
            with b3:
                if st.button("🗑️",key=f"d_{k}"): c_del(k); st.rerun()
        with c3: st.markdown(f'<div style="text-align:right;font-weight:800;color:#0e3a5a;padding-top:8px">${sub:.2f}</div>',unsafe_allow_html=True)
    tu=c_total(); tb=round(tu*tasa,2)
    st.markdown(f'<div style="background:#0e3a5a;color:#fff;border-radius:12px;padding:12px 14px;margin-top:6px"><div style="display:flex;justify-content:space-between"><span>Total USD</span><b>${tu:.2f}</b></div><div style="display:flex;justify-content:space-between;margin-top:3px"><span>Total Bs.</span><b>Bs. {tb:,.2f}</b></div><div style="font-size:.68rem;opacity:.7;margin-top:5px">Tasa: Bs. {tasa:,.2f}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="sec">👤 Cliente</div>',unsafe_allow_html=True)
    cdf=get_clientes(); op={0:"🧑 Anónimo"}
    for _,cc in cdf.iterrows():
        et=f"{cc['alumno'] or cc['nombre']}"
        if cc["representante"]: et+=f" — Rep: {cc['representante']}"
        op[int(cc["id"])]=et
    ids=list(op.keys()); ix=ids.index(st.session_state.cliente_sel_id) if st.session_state.cliente_sel_id in ids else 0
    st.session_state.cliente_sel_id=st.selectbox("Cliente",ids,format_func=lambda x:op[x],index=ix,label_visibility="collapsed")
    cA,cB=st.columns(2)
    with cA:
        if st.button("✅ Registrar Pago",type="primary",use_container_width=True): finalizar_venta("Pagado",tasa,tu,tb); st.rerun()
    with cB:
        if st.button("🔴 Fiar / Crédito",use_container_width=True): finalizar_venta("Por cobrar",tasa,tu,tb); st.rerun()

# ---------- CRM ----------
def modulo_crm(cfg):
    tasa=tasa_activa(cfg)
    st.markdown('<div class="sec">📇 Directorio</div>',unsafe_allow_html=True)
    cdf=get_clientes(); ddf=get_deudas()
    dm={}
    if not ddf.empty:
        for _,d in ddf.iterrows(): dm[int(d["cliente_id"])]={"usd":float(d["deuda_usd"]),"bs":float(d["deuda_bs"])}
    if cdf.empty: st.info("Sin clientes.")
    else:
        for _,c in cdf.iterrows():
            cid=int(c["id"]); de=dm.get(cid,{"usd":0.0,"bs":0.0}); tie=de["usd"]>0.005; dbs=round(de["usd"]*tasa,2)
            st.markdown(f'<div class="ci"><div class="t">👤 {c["alumno"] or c["nombre"]}</div><div class="s">Rep: {c["representante"] or "—"} · 📱 {c["telefono"] or "—"}</div><div class="s" style="margin-top:3px">Deuda: <b style="color:{"#e74c3c" if tie else "#27ae60"}">${de["usd"]:.2f}</b> · Bs. {dbs:,.2f}</div></div>',unsafe_allow_html=True)
            c1,c2,c3=st.columns([2,2,2])
            with c1:
                if tie and st.button("💰 Abonar",key=f"ab_{cid}"): abonar_cliente(cid); st.success("Deuda cancelada."); st.rerun()
            with c2:
                if tie and c["telefono"]:
                    msg=msg_recordatorio(c["representante"] or "",c["alumno"] or c["nombre"] or "",de["usd"],dbs)
                    lnk=wa_link(c["telefono"],msg)
                    if lnk: st.markdown(f'<a href="{lnk}" target="_blank" class="wa">💬 WhatsApp</a>',unsafe_allow_html=True)
            with c3:
                if tie and st.button("📜 Ver",key=f"v_{cid}"): st.session_state[f"vv_{cid}"]=not st.session_state.get(f"vv_{cid}",False)
            if tie and st.session_state.get(f"vv_{cid}",False):
                vdf=get_ventas(); pd_=vdf[(vdf["cliente_id"]==cid)&(vdf["estado"]=="Por cobrar")]
                for _,v in pd_.iterrows():
                    s1,s2=st.columns([5,2])
                    with s1: st.markdown(f'<div style="font-size:.72rem;color:#555;padding:3px 6px">🗓️ {v["fecha"]} · ${v["monto_usd"]:.2f} · {v["detalles"]}</div>',unsafe_allow_html=True)
                    with s2:
                        if st.button("✅",key=f"pv_{v['id']}"): abonar_venta(int(v["id"])); st.rerun()
            st.markdown("---")
    st.markdown('<div class="sec">➕ Nuevo Cliente</div>',unsafe_allow_html=True)
    with st.form("fc",clear_on_submit=True):
        c1,c2=st.columns(2)
        with c1:
            al=st.text_input("Alumno *"); rep=st.text_input("Representante")
        with c2:
            tel=st.text_input("Teléfono"); cat=st.selectbox("Categoría",["Alumno","Docente","Administrativo","Otro"])
        nom=st.text_input("Nombre (opcional)")
        if st.form_submit_button("💾 Guardar",use_container_width=True):
            if not al.strip(): st.error("Alumno obligatorio.")
            else: add_cliente(nom.strip() or al.strip(),al.strip(),rep.strip(),tel.strip(),cat); st.success("Guardado."); st.rerun()

# ---------- Productos ----------
EMOJIS=["🍔","🌭","🍕","🥟","🍟","🌮","🌯","🥪","🍗","🍖","🥗","🍝","🍜","🍲","🍛","🍱","🥘","🥤","💧","🧃","☕","🍵","🧋","🍺","🥛","🍹","🍰","🍪","🍫","🍩","🍦","🧁","🍮","🥧","🍎","🍌","🍓","🍊","🍇","🥭","🍉","🍴","🥄","🧂","🍿","🥨","🥐"]

def modulo_productos(cfg):
    tasa=tasa_activa(cfg)
    st.markdown('<div class="sec">➕ Crear Producto</div>',unsafe_allow_html=True)
    with st.form("fp",clear_on_submit=True):
        em=st.selectbox("Emoji",EMOJIS,index=0); nom=st.text_input("Nombre *")
        c1,c2=st.columns(2)
        with c1: pr=st.number_input("Precio $ *",min_value=0.0,step=0.10,format="%.2f")
        with c2: co=st.number_input("Costo $",min_value=0.0,step=0.10,format="%.2f")
        c3,c4=st.columns(2)
        with c3: cat=st.text_input("Categoría",value="General")
        with c4: sku=st.text_input("SKU")
        if st.form_submit_button("💾 Guardar",use_container_width=True):
            if not nom.strip(): st.error("Nombre obligatorio.")
            elif pr<=0: st.error("Precio debe ser >0.")
            else: add_producto(em,nom.strip(),pr,co,cat.strip() or "General",sku.strip()); st.success("Agregado."); st.rerun()
    st.markdown('<div class="sec">📦 Catálogo</div>',unsafe_allow_html=True)
    pdf=get_productos()
    if pdf.empty: st.info("Vacío.")
    else:
        v=pdf.copy(); v["Precio Bs."]=(v["precio_usd"]*tasa).round(2)
        v=v.rename(columns={"emoji":"🎨","nombre":"Producto","precio_usd":"$","costo_usd":"Costo $","categoria":"Categoría","sku":"SKU"})
        st.dataframe(v[["🎨","Producto","Categoría","$","Precio Bs.","Costo $","SKU"]],use_container_width=True,hide_index=True)

# ---------- Reportes ----------
def reporte_txt(vdf,cfg):
    t=tasa_activa(cfg)
    L=["="*60,"    TU CANTINA EXPRESS - REPORTE","="*60,f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",f"Tasa activa: Bs. {t:,.2f} ({cfg.get('tasa_activa_tipo','')})","-"*60]
    if vdf.empty: L.append("Sin operaciones."); return "\n".join(L)
    tot=round(vdf["monto_usd"].sum(),2); tbs=round(vdf["monto_bs"].sum(),2)
    pag=vdf[vdf["estado"]=="Pagado"]; pc=vdf[vdf["estado"]=="Por cobrar"]
    L+=[f"Operaciones: {len(vdf)}",f"Facturado USD: ${tot:,.2f}",f"Facturado Bs.: Bs. {tbs:,.2f}",f"Cobrado: ${round(pag['monto_usd'].sum(),2):,.2f}",f"Por cobrar: ${round(pc['monto_usd'].sum(),2):,.2f}","","DETALLE:","-"*60]
    for _,v in vdf.sort_values("id").iterrows():
        L+=[f"\n#{v['id']} · {v['fecha']}",f"  Tasa: Bs. {float(v['tasa_usada']):,.2f}",f"  Cliente: {v['cliente_nombre'] or 'Anónimo'}",f"  Alumno: {v['alumno'] or '—'}",f"  Rep: {v['representante'] or '—'}",f"  USD: ${float(v['monto_usd']):,.2f}",f"  Bs.: Bs. {float(v['monto_bs']):,.2f}",f"  Estado: {v['estado']}",f"  Productos: {v['detalles']}"]
    L+=["","="*60,"Fin."]
    return "\n".join(L)

def modulo_reportes(cfg):
    tasa=tasa_activa(cfg); vdf=get_ventas(); pdf=get_productos()
    tu=round(vdf["monto_usd"].sum(),2) if not vdf.empty else 0.0
    tb=round(vdf["monto_bs"].sum(),2) if not vdf.empty else 0.0
    deu=round(vdf.loc[vdf["estado"]=="Por cobrar","monto_usd"].sum(),2) if not vdf.empty else 0.0
    n=len(vdf)
    if not pdf.empty and tu>0:
        m=((pdf["precio_usd"]-pdf["costo_usd"])/pdf["precio_usd"]).replace([float("inf"),-float("inf")],0).fillna(0).mean()
        gan=round(tu*m,2)
    else: gan=0.0
    c1,c2=st.columns(2)
    with c1: metric("Ingresos",f"${tu:,.2f}","gold")
    with c2: metric("Ganancia Est.",f"${gan:,.2f}","green")
    c3,c4=st.columns(2)
    with c3: metric("Deuda",f"${deu:,.2f}","red")
    with c4: metric("Operaciones",f"{n}","")
    st.markdown(f'<div style="text-align:center;font-size:.72rem;color:#6c7a89;margin-top:4px">Facturado Bs. {tb:,.2f} · Tasa Bs. {tasa:,.2f}</div>',unsafe_allow_html=True)
    st.markdown('<div class="sec">📊 Historial</div>',unsafe_allow_html=True)
    if vdf.empty: st.info("Sin ventas."); return
    v=vdf.rename(columns={"id":"ID","fecha":"Fecha","alumno":"Alumno","representante":"Rep","monto_usd":"USD","monto_bs":"Bs.","tasa_usada":"Tasa","estado":"Estado","detalles":"Productos"})
    st.dataframe(v[["ID","Fecha","Alumno","Rep","USD","Bs.","Tasa","Estado","Productos"]],use_container_width=True,hide_index=True)
    st.markdown('<div class="sec">⬇️ Exportar</div>',unsafe_allow_html=True)
    buf=io.StringIO(); w=csv.writer(buf,delimiter=";")
    w.writerow(["ID","Fecha","Cliente","Alumno","Rep","USD","Bs","Tasa","Estado","Detalles"])
    for _,r in vdf.iterrows():
        w.writerow([r["id"],r["fecha"],r["cliente_nombre"],r["alumno"],r["representante"],f"{float(r['monto_usd']):.2f}",f"{float(r['monto_bs']):.2f}",f"{float(r['tasa_usada']):.2f}",r["estado"],r["detalles"]])
    hoy=datetime.now().strftime("%Y%m%d_%H%M")
    cA,cB=st.columns(2)
    with cA: st.download_button("📄 CSV",buf.getvalue().encode("utf-8-sig"),f"ventas_{hoy}.csv","text/csv",use_container_width=True)
    with cB: st.download_button("📝 TXT",reporte_txt(vdf,cfg).encode("utf-8"),f"reporte_{hoy}.txt","text/plain",use_container_width=True)

# ---------- Config ----------
def modulo_config(cfg):
    st.markdown('<div class="sec">⚙️ Ajustes</div>',unsafe_allow_html=True)
    with st.form("cfg"):
        c1,c2=st.columns(2)
        with c1: usd=st.number_input("BCV USD",min_value=0.0,value=float(cfg.get("tasa_bcv_usd",0) or 0),step=0.10,format="%.2f")
        with c2: eur=st.number_input("BCV EUR",min_value=0.0,value=float(cfg.get("tasa_bcv_eur",0) or 0),step=0.10,format="%.2f")
        per=st.number_input("Tasa Personalizada",min_value=0.0,value=float(cfg.get("tasa_personalizada",0) or 0),step=0.10,format="%.2f")
        tipos=["BCV USD","BCV EUR","Personalizada"]
        itip=tipos.index(cfg.get("tasa_activa_tipo","BCV USD")) if cfg.get("tasa_activa_tipo") in tipos else 0
        ta=st.selectbox("Tasa activa",tipos,index=itip)
        neg=st.text_input("Negocio",value=cfg.get("negocio_nombre","Tu Cantina Express"))
        rif=st.text_input("RIF",value=cfg.get("negocio_rif",""))
        if st.form_submit_button("💾 Guardar",type="primary",use_container_width=True):
            set_config("tasa_bcv_usd",f"{round(float(usd),2):.2f}"); set_config("tasa_bcv_eur",f"{round(float(eur),2):.2f}")
            set_config("tasa_personalizada",f"{round(float(per),2):.2f}"); set_config("tasa_activa_tipo",ta)
            set_config("negocio_nombre",neg.strip()); set_config("negocio_rif",rif.strip())
            st.success("Guardado."); st.rerun()
    st.markdown(f'<div style="font-size:.78rem;color:#6c7a89"><b>Sistema</b><br>DB: <code>cantina.db</code><br>Productos: {len(get_productos())} · Clientes: {len(get_clientes())} · Ventas: {len(get_ventas())}</div>',unsafe_allow_html=True)

# ---------- Main ----------
def main():
    inject_css(); init_db(); init_state()
    cfg=get_config(); render_header(cfg)
    t1,t2,t3,t4,t5=st.tabs(["🛒 POS","👥 CRM","➕ Productos","📊 Reportes","⚙️ Ajustes"])
    with t1: modulo_pos(cfg)
    with t2: modulo_crm(cfg)
    with t3: modulo_productos(cfg)
    with t4: modulo_reportes(cfg)
    with t5: modulo_config(cfg)

if __name__=="__main__": main()
