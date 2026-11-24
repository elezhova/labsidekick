def calc_mass_g(molarity_mm: float, volume_ml: float, mr: float) -> float:
    """Расчет навески в граммах: m = (M * V * Mr) / 1000."""
    molarity_m = molarity_mm / 1000.0
    return (molarity_m * volume_ml * mr) / 1000.0


def calc_serial_dilution(start_mm: float, tubes: int, well_vol_ul: float = 12.5) -> list[dict]:
    """Серийное разведение 1:1 в пробирках и расчет переноса в лунку."""
    rows = []
    conc = start_mm
    for i in range(1, tubes + 1):
        rows.append({
            "Пробирка": f"Пробирка №{i}",
            "Концентрация в пробирке, мМ": round(conc, 3),
            "В лунку из пробирки, мкл": well_vol_ul,
            "В лунке цистеина, нмоль": round(conc * well_vol_ul, 3),
        })
        conc /= 2.0
    return rows



def calc_df(v_total_ml: float, v_sample_ml: float, plasma_dilution: float) -> float:
    """Итоговый коэффициент разведения Df."""
    return (v_total_ml / v_sample_ml) * plasma_dilution


def calc_activity(
    od_0: float,
    od_t: float,
    v_total_ml: float,
    v_sample_ml: float,
    df: float,
    time_min: float,
    epsilon: float,
    optical_path_cm: float,
) -> tuple[float, float]:
    """Расчет ΔOD и удельной активности фермента в Ед/мл (моль/мин*л)."""
    delta_od = abs(od_t - od_0)
    activity = (delta_od * v_total_ml * df * 1_000_000.0) / (
        time_min * epsilon * optical_path_cm * v_sample_ml
    )
    return delta_od, activity
