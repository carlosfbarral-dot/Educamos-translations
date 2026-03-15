import anthropic
import json
import io
import pandas as pd
import streamlit as st

# ── CONFIG ────────────────────────────────────────────────
st.set_page_config(page_title="Traductor Educamos", page_icon=":mortar_board:", layout="wide")

LANGUAGES = [
    ("es",     "Español ES"),
    ("en",     "Inglés"),
    ("ca",     "Catalán"),
    ("eu",     "Euskera"),
    ("gl",     "Gallego"),
    ("es_mx",  "Español MX"),
    ("es_ar",  "Español AR"),
    ("es_cl",  "Español CH"),
    ("es_co",  "Español CO"),
    ("fr",     "Francés"),
    ("pt",     "Portugués"),
    ("es_int", "Español Internacional"),
]

SYSTEM_PROMPT = """Eres un traductor especializado en software educativo de gestión escolar.
El software se llama "Educamos" y es una plataforma usada en centros educativos.
Traduce adaptando siempre la terminología al contexto de software de gestión escolar.
Responde ÚNICAMENTE con un objeto JSON sin markdown ni backticks.
Claves exactas: es, en, ca, eu, gl, es_mx, es_ar, es_cl, es_co, fr, pt, es_int."""

# ── SESSION STATE ─────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ── STYLES ────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a4fa0, #0d2d6b);
        padding: 20px 28px; border-radius: 12px;
        color: white; margin-bottom: 24px;
    }
    .main-header h1 { color: white; margin: 0; font-size: 26px; }
    .main-header p  { color: #a8c4f0; margin: 4px 0 0; font-size: 13px; }
    .edited-cell { background: #fffbeb !important; }
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .stDownloadButton>button { background: #217346; color: white; border-radius: 8px; font-weight: 600; }
    .stDownloadButton>button:hover { background: #1a5c38; color: white; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>Traductor Educamos</h1>
  <p>Software de gestion escolar &middot; 12 idiomas &middot; Edicion manual &middot; Exportacion Excel</p>
</div>
""", unsafe_allow_html=True)

# ── API KEY ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Configuración")
    api_key = st.text_input("API Key de Anthropic", type="password",
                             value=st.session_state.api_key,
                             placeholder="sk-ant-api03-...")
    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ Clave configurada")
    else:
        st.warning("Introduce tu API Key para traducir")
        st.markdown("[Obtener clave →](https://console.anthropic.com/settings/keys)")

    st.divider()
    st.markdown("### ⚙️ Idiomas visibles")
    enabled = {}
    for key, label in LANGUAGES:
        enabled[key] = st.checkbox(label, value=True, key=f"col_{key}")

    st.divider()
    if st.session_state.history:
        st.markdown(f"### 🕐 Historial: {len(st.session_state.history)} entradas")
        if st.button("🗑️ Limpiar historial", use_container_width=True):
            st.session_state.history = []
            st.rerun()

# ── HELPER ────────────────────────────────────────────────
def translate(text, src_label):
    client = anthropic.Anthropic(api_key=st.session_state.api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Idioma origen: {src_label}\nTexto a traducir: \"{text}\""}]
    )
    return json.loads(msg.content[0].text.strip())

def to_excel(rows):
    vis = [(k, l) for k, l in LANGUAGES if enabled.get(k)]
    data = []
    for r in rows:
        row = {"Texto Original": r["original"]}
        for k, l in vis:
            row[l] = r["translations"].get(k, "")
        data.append(row)
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Traducciones")
        ws = writer.sheets["Traducciones"]
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 28
    return buf.getvalue()

def show_table(rows, editable=False, prefix=""):
    vis = [(k, l) for k, l in LANGUAGES if enabled.get(k)]
    cols = ["Texto Original"] + [l for _, l in vis]
    data = []
    for r in rows:
        row = {"Texto Original": r["original"]}
        for k, l in vis:
            val = r["translations"].get(k, "")
            row[l] = ("✎ " + val) if r.get("edited", {}).get(k) else val
        data.append(row)
    df = pd.DataFrame(data, columns=cols)
    if editable:
        edited = st.data_editor(df, use_container_width=True, key=f"editor_{prefix}",
                                 num_rows="fixed", hide_index=True)
        return edited
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        return None

# ── TABS ──────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✏️ Traducción simple", "📋 Por lotes", "🕐 Historial"])

# ── TAB 1: SIMPLE ─────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([1, 3])
    with col1:
        src_options = {l: k for k, l in LANGUAGES}
        src_label = st.selectbox("Idioma origen", list(src_options.keys()), key="single_src")
    with col2:
        text_input = st.text_input("Texto a traducir", placeholder="Ej: expediente académico, matrícula...", key="single_input")

    if st.button("🔄 Traducir", type="primary", key="single_btn"):
        if not st.session_state.api_key:
            st.error("❌ Introduce tu API Key en el panel izquierdo.")
        elif not text_input.strip():
            st.warning("Escribe un texto para traducir.")
        else:
            with st.spinner("Traduciendo..."):
                try:
                    result = translate(text_input.strip(), src_label)
                    entry = {"original": text_input.strip(), "translations": result, "edited": {}}
                    st.session_state.history.insert(0, entry)
                    st.session_state["last_single"] = entry
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    if "last_single" in st.session_state:
        entry = st.session_state["last_single"]
        st.markdown(f"**Resultado para:** `{entry['original']}`")
        edited_df = show_table([entry], editable=True, prefix="single")
        if edited_df is not None:
            vis = [(k, l) for k, l in LANGUAGES if enabled.get(k)]
            for i, (k, l) in enumerate(vis):
                new_val = edited_df.iloc[0].get(l, "")
                if new_val.startswith("✎ "): new_val = new_val[2:]
                if new_val != entry["translations"].get(k, ""):
                    entry["translations"][k] = new_val
                    entry["edited"][k] = True
        col_exp, _ = st.columns([1, 4])
        with col_exp:
            st.download_button("📥 Exportar Excel", data=to_excel([entry]),
                               file_name=f"educamos_{entry['original'][:20]}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ── TAB 2: BATCH ──────────────────────────────────────────
with tab2:
    col1, col2 = st.columns([1, 3])
    with col1:
        src_label_b = st.selectbox("Idioma origen", list(src_options.keys()), key="batch_src")
    with col2:
        batch_input = st.text_area("Términos (uno por línea)",
                                    placeholder="expediente académico\ntutor legal\nmatrícula\ncalificaciones",
                                    height=160, key="batch_input")

    # Import Excel
    uploaded = st.file_uploader("📂 O importa términos desde Excel (.xlsx)", type=["xlsx", "xls"])
    if uploaded:
        try:
            df_imp = pd.read_excel(uploaded, header=0)
            terms = df_imp.iloc[:, 0].dropna().astype(str).tolist()
            st.session_state["batch_input_val"] = "\n".join(terms)
            st.success(f"✅ {len(terms)} términos importados. Cópialos arriba si no aparecen.")
            st.write(", ".join(terms[:10]) + ("..." if len(terms) > 10 else ""))
        except Exception as e:
            st.error(f"Error al importar: {e}")

    if st.button("🔄 Traducir todo", type="primary", key="batch_btn"):
        if not st.session_state.api_key:
            st.error("❌ Introduce tu API Key en el panel izquierdo.")
        else:
            lines = [l.strip() for l in batch_input.split("\n") if l.strip()]
            if not lines:
                st.warning("Escribe al menos un término.")
            else:
                st.session_state["batch_rows"] = []
                progress = st.progress(0, text="Iniciando...")
                for i, line in enumerate(lines):
                    try:
                        result = translate(line, src_label_b)
                        st.session_state["batch_rows"].append({"original": line, "translations": result, "edited": {}})
                    except Exception as e:
                        st.session_state["batch_rows"].append({"original": line, "translations": {}, "edited": {}, "error": True})
                    progress.progress((i + 1) / len(lines), text=f"Traduciendo {i+1}/{len(lines)}...")
                st.session_state.history = st.session_state["batch_rows"] + st.session_state.history
                progress.empty()
                st.success(f"✅ {len(lines)} términos traducidos.")

    if "batch_rows" in st.session_state and st.session_state["batch_rows"]:
        rows = st.session_state["batch_rows"]
        st.markdown(f"**{len(rows)} términos** — haz clic en cualquier celda para editar")
        edited_df = show_table(rows, editable=True, prefix="batch")
        if edited_df is not None:
            vis = [(k, l) for k, l in LANGUAGES if enabled.get(k)]
            for i, r in enumerate(rows):
                for k, l in vis:
                    new_val = str(edited_df.iloc[i].get(l, ""))
                    if new_val.startswith("✎ "): new_val = new_val[2:]
                    if new_val != r["translations"].get(k, ""):
                        r["translations"][k] = new_val
                        r["edited"][k] = True
        st.download_button("📥 Exportar lote (.xlsx)", data=to_excel(rows),
                           file_name="educamos_lote.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ── TAB 3: HISTORY ────────────────────────────────────────
with tab3:
    if not st.session_state.history:
        st.info("📭 No hay traducciones en el historial todavía.")
    else:
        st.markdown(f"**{len(st.session_state.history)} entradas** — haz clic en cualquier celda para editar")
        edited_df = show_table(st.session_state.history, editable=True, prefix="hist")
        if edited_df is not None:
            vis = [(k, l) for k, l in LANGUAGES if enabled.get(k)]
            for i, r in enumerate(st.session_state.history):
                for k, l in vis:
                    new_val = str(edited_df.iloc[i].get(l, ""))
                    if new_val.startswith("✎ "): new_val = new_val[2:]
                    if new_val != r["translations"].get(k, ""):
                        r["translations"][k] = new_val
                        r["edited"][k] = True
        st.download_button("📥 Exportar historial completo (.xlsx)",
                           data=to_excel(st.session_state.history),
                           file_name="educamos_historial.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
