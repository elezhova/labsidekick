import io
import os
import yaml
import pandas as pd
import streamlit as st
from calc.ellman import (
    calc_mass_g,
    calc_serial_dilution,
    calc_df,
    calc_activity,
)

st.set_page_config(page_title="LabSidekick",layout="centered")

PROTOCOLS_DIR = "protocols"
protocols = {}

if os.path.exists(PROTOCOLS_DIR):
    for fname in sorted(os.listdir(PROTOCOLS_DIR)):
        if fname.endswith((".yaml", ".yml")):
            with open(os.path.join(PROTOCOLS_DIR, fname), "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    protocols[data.get("title", fname)] = data

st.sidebar.header("Протоколы")
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

st.title(f"{proto['title']}")
if "description" in proto:
    st.caption(proto["description"])

for note in proto.get("notes", []):
    st.warning(f"{note}")

if "steps" in proto:
    with st.expander("📋 Пошаговый протокол для новичков", expanded=False):
        for step in proto["steps"]:
            st.markdown(step)

tab1, tab2, tab3, tab4 = st.tabs([

    "1. Навески",
    "2. Раскапывание",
    "3. Одиночный расчет",
    "4. Серия проб (таблица)",
])

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
        st.subheader("Калибровочная серия цистеина (разведение 1:1 в пробирках)")
        cal = proto["calibration"]
        sample_ul = float(cal.get("well_sample_ul", 12.5))

        c1, c2 = st.columns(2)
        tubes = c1.slider("Количество пробирок", 2, 10, int(cal.get("tubes_count", 7)))
        step_vol = c2.number_input("Объем шага разведения в пробирке (мкл)", value=500, step=100, min_value=50)

        st.info(
            f"**Как готовить серию в пробирках (шаг 1:1):**\n"
            f"1. В пробирку №1 налейте исходный раствор цистеина ({float(cal['start_molarity_mm']):g} мМ).\n"
            f"2. В пробирки №2–№{tubes} заранее налейте по **{step_vol} мкл** дист. воды.\n"
            f"3. Перенесите **{step_vol} мкл** из пробирки №1 в пробирку №2, перемешайте пипетированием. Повторите цепочку до пробирки №{tubes}.\n\n"
            f"Расчет объемов для внесения в планшет смотрите на вкладке **«2. Раскапывание»** (режим *«Калибровка по цистеину»*)."
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

# ВКЛАДКА 3: ОДИНОЧНЫЙ РАСЧЕТ АКТИВНОСТИ
with tab3:
    params = proto.get("activity_params")
    if params:
        dil_map = params["dilutions"]
        choice = st.selectbox("Материал исследования", list(dil_map.keys()) + ["Другое разведение"], key="single_dil")
        plasma_dil = (
            st.number_input("Кратность разведения пробы", value=15.0, min_value=1.0, key="single_custom_dil")
            if choice == "Другое разведение"
            else float(dil_map[choice])
        )

        df_val = calc_df(params["v_total_ml"], params["v_sample_ml"], plasma_dil)
        st.metric("Коэффициент разведения (Df)", f"{df_val:.2f}")

        c1, c2 = st.columns(2)
        od0 = c1.number_input("OD0 (контроль)", value=0.120, format="%.4f", step=0.005)
        od5 = c2.number_input("OD 5 мин (опыт)", value=0.450, format="%.4f", step=0.005)

        delta, act = calc_activity(
            od0, od5, params["v_total_ml"], params["v_sample_ml"],
            df_val, params["time_min"], params["epsilon"], params["optical_path_cm"]
        )
        st.success(f"Удельная активность: **{act:.2f} Ед/мл** (ΔOD = {delta:.4f})")

# ВКЛАДКА 4: РУЧНОЙ ВВОД СЕРИИ ПРОБ (ИЛИ ВСТАВКА ИЗ EXCEL)
with tab4:
    params = proto.get("activity_params")
    if not params:
        st.info("Для выбранного протокола не заданы параметры расчета активности.")
    else:
        st.subheader("Расчет серии проб")
        st.caption("Введите значения OD вручную (можно добавлять строки внизу таблицы) или вставьте столбцы из Excel через Ctrl+V.")

        dil_map = params["dilutions"]
        batch_choice = st.selectbox("Материал исследования", list(dil_map.keys()) + ["Другое разведение"], key="batch_dil")
        batch_dil = (
            st.number_input("Кратность разведения", value=15.0, min_value=1.0, key="batch_custom_dil")
            if batch_choice == "Другое разведение"
            else float(dil_map[batch_choice])
        )
        df_batch = calc_df(params["v_total_ml"], params["v_sample_ml"], batch_dil)
        st.caption(f"Используемый коэффициент разведения: **Df = {df_batch:.2f}**")

        default_df = pd.DataFrame([
            {"Проба": "Проба 1", "OD0 (контроль)": 0.120, "OD 5 мин (опыт)": 0.450},
            {"Проба": "Проба 2", "OD0 (контроль)": 0.125, "OD 5 мин (опыт)": 0.410},
            {"Проба": "Проба 3", "OD0 (контроль)": 0.000, "OD 5 мин (опыт)": 0.000},
        ])

        edited_df = st.data_editor(
            default_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Проба": st.column_config.TextColumn("Проба / № лунки"),
                "OD0 (контроль)": st.column_config.NumberColumn("OD0 (контроль)", format="%.4f", step=0.001),
                "OD 5 мин (опыт)": st.column_config.NumberColumn("OD 5 мин (опыт)", format="%.4f", step=0.001),
            },
        )

        results = []
        for _, row in edited_df.iterrows():
            od0_val = row.get("OD0 (контроль)")
            od5_val = row.get("OD 5 мин (опыт)")
            if pd.notna(od0_val) and pd.notna(od5_val) and (od0_val != 0 or od5_val != 0):
                d_od, act_val = calc_activity(
                    float(od0_val), float(od5_val),
                    params["v_total_ml"], params["v_sample_ml"],
                    df_batch, params["time_min"], params["epsilon"], params["optical_path_cm"]
                )
                results.append({
                    "Проба": row.get("Проба", ""),
                    "OD0": round(float(od0_val), 4),
                    "OD 5 мин": round(float(od5_val), 4),
                    "ΔOD": round(d_od, 4),
                    "Активность (Ед/мл)": round(act_val, 2),
                })

        if results:
            res_df = pd.DataFrame(results)
            st.divider()
            st.markdown("**Результаты расчета:**")
            st.dataframe(res_df, use_container_width=True, hide_index=True)

            mean_act = res_df["Активность (Ед/мл)"].mean()
            sd_act = res_df["Активность (Ед/мл)"].std() if len(res_df) > 1 else 0.0
            st.info(f"Среднее по серии: **{mean_act:.2f} ± {sd_act:.2f} Ед/мл** (n = {len(res_df)})")

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                res_df.to_excel(writer, index=False, sheet_name="Results")
            st.download_button(
                "Скачать таблицу в Excel (.xlsx)",
                buf.getvalue(),
                "ellman_results.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
