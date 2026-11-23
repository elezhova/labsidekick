import pytest
from calc.ellman import calc_mass_g, calc_serial_dilution, calc_df


def test_dtnb_mass():
    # 2 мМ DTNB в 250 мл при Mr = 396.3 -> 198.15 мг
    mass_mg = calc_mass_g(2.0, 250.0, 396.3) * 1000
    assert pytest.approx(mass_mg, rel=1e-2) == 198.15


def test_cys_dilution():
    # В 7-й пробирке при разведении с 5 мМ должно быть 0.078 мМ
    rows = calc_serial_dilution(5.0, 7)
    assert rows[-1]["Концентрация, мМ"] == 0.078


def test_dilution_factors():
    # Проверка Df для человека (48.75) и крысы (97.5)
    assert pytest.approx(calc_df(0.13, 0.04, 15.0)) == 48.75
    assert pytest.approx(calc_df(0.13, 0.04, 30.0)) == 97.5


