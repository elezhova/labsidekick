import os
import yaml
import pandas as pd
import streamlit as st
from calc.ellman import calc_mass_g, calc_serial_dilution, calc_df, calc_activity

st.set_page_config(page_title="LabSidekick", page_icon="🧪", layout="centered")

PROTOCOLS_DIR = "protocols"
protocols = {}

# 1. Загружаем все постоянные протоколы из папки protocols/
if os.path.exists(PROTOCOLS_DIR):
    for fname in sorted(os.listdir(PROTOCOLS_DIR)):
        if fname.endswith((".yaml", ".yml")):
            with open(os.path.join(PROTOCOLS_DIR, fname), "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    protocols[data.get("title", fname)] = data

# 2. Боковое меню: выбор протокола и временная подгрузка нового файла
st.sidebar.header("📂 Протоколы")
uploaded = st.sidebar.file_uploader("Подгрузить протокол (.yaml)", type=["yaml", "yml"])
if uploaded is not None:
    temp_data = yaml.safe_load(uploaded.getvalue().decode("utf-8"))
    if temp_data:
        title = temp_data.get("title", uploaded.name)
        protocols[title] = temp_data
        st.sidebar.success(f"Загружен: {title}")

if not protocols:
    st.error("Добавьте хотя бы один .yaml файл в папку protocols/ или загрузите его слева.")
    st.stop()

selected_title = st.sidebar.selectbox("Активный протокол", list(protocols.keys()))
proto = protocols[selected_title]

# --- ОСНОВНОЙ ЭКРАН ---
st.title(f"🧪 {proto['title']}")
if "description" in proto:
    st.caption(proto["description"])

for note in proto.get("notes", []):
    st.warning(f"⚠️ {note}")

tab1, tab2, tab3 = st.tabs(["1. Навески и калибровка", "2. Раскапывание", "3. Расчет активности"])

# ВКЛАДКА 1: НАВЕСКИ И СЕРИЙНЫЕ РАЗВЕДЕНИЯ
with tab1:
    for item in proto.get("reagents", []):
        st.subheader(item["name"])
        c1, c2, c3 = st.columns(3)
        mr = c1.number_input("Mr (г/моль)", value=float(item["mr"]), key=f"mr_{item['id']}")
        m_mm = c2.number_input("Молярность (мМ)", value=float(item["molarity_mm"]), key=f"m_{item['id']}")
        v_ml = c3.number_input("Объем (мл)", value=float(item["volume_ml"]), key=f"v_{item['id']}")

        mass_g = calc_mass_g(m_mm, v_ml, mr)
        st.success(f"Навеска: **{mass_g:.4f} г** ({mass_g * 1000:.1f} мг)")
    if "calibration" in proto:
        st.divider()
        st.subheader("Калибровочная кривая по цистеину (разведение 1:1 в пробирках)")
        cal = proto["calibration"]
        
        sample_ul = float(cal.get("well_sample_ul", 12.5))
        h2o_ul = float(cal.get("well_h2o_ul", 80.0))
        dtnb_ul = float(cal.get("well_dtnb_ul", 25.0))
        sds_ul = float(cal.get("well_sds_ul", 12.5))
        total_ul = sample_ul + h2o_ul + dtnb_ul + sds_ul

        c1, c2 = st.columns(2)
        tubes = c1.slider("Количество пробирок", 2, 10, int(cal.get("tubes_count", 7)))
        step_vol = c2.number_input("Объем шага разведения в пробирке (мкл)", value=500, step=100, min_value=50)

        st.info(
            f"**Как готовить серию в пробирках (шаг 1:1):**\n"
            f"1. В пробирку №1 налейте исходный раствор цистеина ({float(cal['start_molarity_mm']):g} мМ).\n"
            f"2. В пробирки №2–№{tubes} заранее налейте по **{step_vol} мкл** дист. воды.\n"
            f"3. Перенесите **{step_vol} мкл** из пробирки №1 в пробирку №2, перемешайте пипетированием. Повторите цепочку до пробирки №{tubes}.\n\n"
            f"**Как раскапывать в планшет (итого {total_ul:g} мкл в лунке):**\n"
            f"В каждую лунку внесите **{h2o_ul:g} мкл** H₂O дист. + **{sample_ul:g} мкл** раствора из соответствующей пробирки + **{dtnb_ul:g} мкл** DTNB + **{sds_ul:g} мкл** SDS."
        )

        dil_rows = calc_serial_dilution(float(cal["start_molarity_mm"]), tubes, sample_ul)
        st.dataframe(pd.DataFrame(dil_rows), use_container_width=True, hide_index=True)


# ВКЛАДКА 2: СМЕСИ НА ПЛАНШЕТ
with tab2:
    modes = proto.get("modes", [])
    if modes:
        mode_name = st.selectbox("Выберите режим анализа", [m["name"] for m in modes])
        mode_data = next(m for m in modes if m["name"] == mode_name)

        c1, c2 = st.columns(2)
        wells = c1.number_input("Всего лунок (опыт + контроль)", min_value=1, value=24, step=1)
        reserve = c2.slider("Запас на пипетирование (%)", 0, 30, 10)

        factor = wells * (1.0 + reserve / 100.0)
        table_rows = [
            {
                "Компонент": comp,
                "На 1 лунку (мкл)": vol,
                f"Всего +{reserve}% (мкл)": round(vol * factor, 1),
            }
            for comp, vol in mode_data["components"].items()
        ]
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

# ВКЛАДКА 3: ОБСЧЕТ АКТИВНОСТИ
with tab3:
    params = proto.get("activity_params")
    if params:
        dil_map = params["dilutions"]
        choice = st.selectbox("Материал исследования", list(dil_map.keys()) + ["Другое разведение"])

        if choice == "Другое разведение":
            plasma_dil = st.number_input("Кратность разведения пробы", value=15.0, min_value=1.0)
        else:
            plasma_dil = float(dil_map[choice])

        df_val = calc_df(params["v_total_ml"], params["v_sample_ml"], plasma_dil)
        st.metric("Коэффициент разведения (Df)", f"{df_val:.2f}")

        c1, c2 = st.columns(2)
        od0 = c1.number_input("OD0 (контроль)", value=0.120, format="%.4f", step=0.005)
        od5 = c2.number_input("OD 5 мин (опыт)", value=0.450, format="%.4f", step=0.005)

        delta, act = calc_activity(
            od0,
            od5,
            params["v_total_ml"],
            params["v_sample_ml"],
            df_val,
            params["time_min"],
            params["epsilon"],
            params["optical_path_cm"],
        )
        st.success(f"Удельная активность: **{act:.2f} Ед/мл** (ΔOD = {delta:.4f})")
