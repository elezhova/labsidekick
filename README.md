# LabSidekick

**[Open Live App (Streamlit)](https://streamlit.app)** | **Tests:** Passing | **Python:** 3.11+ | **License:** MIT

**LabSidekick** is a lightweight, mobile-friendly web assistant built for neuroscience and biochemistry wet-lab workflows. It turns static lab protocols into interactive calculators with automated reagent prep, serial dilution tables, and 96-well plate reader batch processing.

> **Live App:** [labsidekick-gj3vvxqmyskkcbqdufnwwe.streamlit.app](https://streamlit.app)  
> Built for the **Laboratory of Comparative Physiology and Pathology of the CNS (IEPhB RAS)**.

---

## Key Features

* **Protocol-as-Data (`YAML`):** Protocols are decoupled from the UI logic. Add or update lab protocols simply by dropping a new `.yaml` file into `protocols/` or uploading it directly via the web interface.
* **Reagent & Calibration Prep:** Automated mass calculations (`m = (M * V * Mr) / 1000`) and 1:1 serial dilution tables (e.g., Cysteine standard curves for DTNB assays).
* **Plate Pipetting Assistant:** Calculates exact working solution and reagent volumes for any number of wells with customizable pipetting dead-volume reserves.
* **Single-Well & 96-Well Batch Processing:**
  * Supports **Modified Ellman's Method** for total Cholinesterase (ChE), Acetylcholinesterase (AChE with ethopropazine), and Butyrylcholinesterase (BChE).
  * Parses **8x12 plate matrices** and flat well lists from `.xlsx` / `.csv` plate reader exports and generates ready-to-download Excel reports.
* **Cross-Platform Access:** Responsive interface works seamlessly on desktop computers, tablets, and smartphones in the lab.

---

## Project Structure

```text
labsidekick/
├── .github/workflows/
│   └── test.yml            # Automated CI pipeline (pytest)
├── calc/
│   ├── __init__.py
│   └── ellman.py           # Core biochemical formulas & 96-well parser
├── protocols/
│   └── ache_bche.yaml      # Modified Ellman's method protocol config
├── tests/
│   └── test_ellman.py      # Unit tests verified against bench reference values
├── app.py                  # Streamlit web application
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Quick Start

### Run Locally
```bash
git clone https://github.com
cd labsidekick
pip install -r requirements.txt
streamlit run app.py
```

### Run Tests
```bash
python -m pytest
```

---

## Adding a New Protocol

Create a new `.yaml` file inside the `protocols/` directory following this structure:

```yaml
title: "Protocol Title"
description: "Short assay description and wavelength."

notes:
  - "Critical bench warning (e.g., add SDS before substrate in control wells)."

reagents:
  - id: "reagent_1"
    name: "Reagent Name"
    mr: 396.3
    molarity_mm: 2.0
    volume_ml: 250.0

modes:
  - name: "Assay Mode 1"
    components:
      "Diluted sample": 40.0
      "Working reagent": 90.0

activity_params:
  v_total_ml: 0.13
  v_sample_ml: 0.04
  time_min: 5.0
  epsilon: 13600.0
  optical_path_cm: 0.43
  dilutions:
    "Human plasma (15x)": 15.0
    "Rat plasma (30x)": 30.0
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
