# QC-StrategyBacktest (Updated)

This project is forked from the original [**QC-StrategyBacktest**](https://github.com/rccannizzaro/QC-StrategyBacktest).

---

## Main Changes to the Original Codebase

1. **Splitting the Main File**
   The main file (`QuantConnect - StrategyBacktest.py`) has been split into two files because the Lean engine fails to handle the original structure.
   The new files created from the original main file are:
   - `main.py`
   - `QC_StrategyBacktest_init.py`

   You can compare the changes between these files using [**pydiff**](https://github.com/yebrahim/pydiff.git).

   **Notes for Comparing Files**:
   - To compare `main.py` with `QuantConnect - StrategyBacktest.py`, it is recommended to untabify both files.
   - To compare `QC_StrategyBacktest_init.py` with `QuantConnect - StrategyBacktest.py`, you will need to trim 3 spaces vertically from all lins to align content.
   - Both preprocessing steps can be done easily using **Visual Studio Code**.

2. **Compatibility with the Latest Lean Engine**
   - Minor changes have been made to make the code compatible with the latest Lean engine.
   - Specifically, `line_terminator` has been changed to `lineterminator`.

---

## Other Modifications/Enhancements

- **TBD**: Additional updates to be documented.

---

## Reference Pointers

- **YouTube Video**: [Using and Building on QuantConnect - Claudio (Rocco) Cannizzaro](https://www.youtube.com/watch?v=XXXXXXX)
- **Additional Files**: [QC Backtesting.pdf](https://drive.google.com/file/d/1cFeq7mdDvhTI2BXGbSYUadEVlJAn1LgC/view)
