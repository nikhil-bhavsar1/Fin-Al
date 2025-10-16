#!/usr/bin/env python3
# streamlit_app.py
# ===========================================================
# Comprehensive Financial Metrics – Streamlit web frontend
# ===========================================================
import os
import sys
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
from io import StringIO, BytesIO

# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------
def safe_divide(numer, denom, err_msg=None):
    """Return numer/denom safely – None if denom==0."""
    if denom in (0, np.nan, None):
        if err_msg:
            error_log.append(err_msg)
        return None
    try:
        return numer / denom
    except Exception as e:
        error_log.append(f"Division failed: {e}")
        return None

def extract_float(row, key, source_name=""):
    try:
        val = None
        if isinstance(row, pd.Series):
            if key in row.index:
                val = row[key]
        else:  # dict (XML)
            val = row.get(key)
        if pd.isna(val):
            val = None
        if val is not None:
            val = float(val)
    except Exception as e:
        error_log.append(f"{source_name}: Could not parse '{key}': {e}")
        val = None
    return val

def read_file(file_uploader, path_str=""):
    """Handle Streamlit upload or path string → pandas DataFrame or dict."""
    if file_uploader is not None:
        content = file_uploader.getvalue()
        ext = os.path.splitext(file_uploader.name)[1].lower()
        try:
            if ext in ['.csv']:
                return pd.read_csv(BytesIO(content))
            elif ext in ['.xls', '.xlsx']:
                return pd.read_excel(BytesIO(content))
            elif ext in ['.xml']:
                tree = ET.parse(BytesIO(content))
                root = tree.getroot()
                if len(root) == 0:
                    raise ValueError("XML has no child elements")
                rec = {}
                for child in root[0]:
                    rec[child.tag] = child.text
                return rec
            else:
                raise ValueError(f"Unsupported upload format: {ext}")
        except Exception as e:
            raise RuntimeError(f"Failed to read uploaded file: {e}")
    else:
        if not os.path.isfile(path_str):
            raise FileNotFoundError(f"No such file: {path_str}")
        ext = os.path.splitext(path_str)[1].lower()
        try:
            if ext in ['.csv']:
                return pd.read_csv(path_str)
            elif ext in ['.xls', '.xlsx']:
                return pd.read_excel(path_str)
            elif ext in ['.xml']:
                tree = ET.parse(path_str)
                root = tree.getroot()
                if len(root) == 0:
                    raise ValueError("XML has no child elements")
                rec = {}
                for child in root[0]:
                    rec[child.tag] = child.text
                return rec
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            raise RuntimeError(f"Failed to read file '{path_str}': {e}")

# ------------------------------------------------------------------
# Metric computation class (same logic as earlier)
# ------------------------------------------------------------------
class FinanceMetrics:
    def __init__(self, data, market_price):
        self.data = data
        self.market_price = market_price
        self.metrics = {}
        self.metrics["Market Price"] = market_price

    def compute(self):
        # Valuation
        self.compute_pe_ratio()
        self.compute_pb_ratio()
        self.compute_ps_ratio()
        self.compute_peg_ratio()
        # Profitability
        self.compute_gross_margin()
        self.compute_operating_margin()
        self.compute_net_margin()
        # Liquidity
        self.compute_current_ratio()
        # Leverage
        self.compute_debt_to_equity()
        # Returns
        self.compute_roe()
        self.compute_roa()

    def compute_pe_ratio(self):
        eps = extract_float(self.data_row, "EPS", "P/E")
        if eps is None:
            return
        val = safe_divide(self.market_price, eps,
                          "P/E: EPS is zero or missing")
        self.metrics["P/E Ratio"] = val

    def compute_pb_ratio(self):
        bvps = extract_float(self.data_row, "Book Value Per Share", "P/B")
        if bvps is None:
            return
        val = safe_divide(self.market_price, bvps,
                          "P/B: Book Value Per Share is zero or missing")
        self.metrics["P/B Ratio"] = val

    def compute_ps_ratio(self):
        rps = extract_float(self.data_row, "Revenue Per Share", "P/S")
        if rps is None:
            return
        val = safe_divide(self.market_price, rps,
                          "P/S: Revenue Per Share is zero or missing")
        self.metrics["P/S Ratio"] = val

    def compute_peg_ratio(self):
        p_e = self.metrics.get("P/E Ratio")
        growth = extract_float(self.data_row, "EPS Growth Rate (%)", "PEG")
        if p_e is None or growth is None:
            return
        val = safe_divide(p_e, growth,
                          "PEG: Growth rate is zero or missing")
        self.metrics["PEG Ratio"] = val

    def compute_gross_margin(self):
        rev = extract_float(self.data_row, "Revenue", "Gross Margin")
        cogs = extract_float(self.data_row, "COGS", "Gross Margin")
        if rev is None or cogs is None:
            return
        val = safe_divide(rev - cogs, rev,
                          "Gross Margin: Revenue zero")
        self.metrics["Gross Profit Margin (%)"] = val * 100 if val is not None else None

    def compute_operating_margin(self):
        op_inc = extract_float(self.data_row, "Operating Income", "Operating Margin")
        rev = extract_float(self.data_row, "Revenue", "Operating Margin")
        if op_inc is None or rev is None:
            return
        val = safe_divide(op_inc, rev, "Operating Margin: Revenue zero")
        self.metrics["Operating Margin (%)"] = val * 100 if val is not None else None

    def compute_net_margin(self):
        net_inc = extract_float(self.data_row, "Net Income", "Net Margin")
        rev = extract_float(self.data_row, "Revenue", "Net Margin")
        if net_inc is None or rev is None:
            return
        val = safe_divide(net_inc, rev, "Net Margin: Revenue zero")
        self.metrics["Net Profit Margin (%)"] = val * 100 if val is not None else None

    def compute_current_ratio(self):
        ca = extract_float(self.data_row, "Current Assets", "Current Ratio")
        cl = extract_float(self.data_row, "Current Liabilities", "Current Ratio")
        if ca is None or cl is None:
            return
        val = safe_divide(ca, cl, "Current Ratio: Liabilities zero")
        self.metrics["Current Ratio"] = val

    def compute_debt_to_equity(self):
        debt = extract_float(self.data_row, "Total Debt", "Debt/Equity")
        equity = extract_float(self.data_row, "Total Equity", "Debt/Equity")
        if debt is None or equity is None:
            return
        val = safe_divide(debt, equity, "Debt/Equity: Equity zero")
        self.metrics["Debt to Equity Ratio"] = val

    def compute_roe(self):
        net_inc = extract_float(self.data_row, "Net Income", "ROE")
        avg_eq = extract_float(self.data_row, "Average Shareholders Equity", "ROE")
        if net_inc is None or avg_eq is None:
            return
        val = safe_divide(net_inc, avg_eq, "ROE: Equity zero")
        self.metrics["Return on Equity (%)"] = val * 100 if val is not None else None

    def compute_roa(self):
        net_inc = extract_float(self.data_row, "Net Income", "ROA")
        avg_assets = extract_float(self.data_row, "Average Total Assets", "ROA")
        if net_inc is None or avg_assets is None:
            return
        val = safe_divide(net_inc, avg_assets, "ROA: Assets zero")
        self.metrics["Return on Assets (%)"] = val * 100 if val is not None else None

    @property
    def data_row(self):
        """Convenience – first row of DataFrame or the dict itself."""
        if isinstance(self.data, pd.DataFrame):
            return self.data.iloc[0]
        else:
            return self.data

# ------------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------------
st.set_page_config(page_title="Financial Metrics Generator",
                   layout="wide")
st.title("📈 Comprehensive Financial Metrics")

# ------------------------------------------------------------------
# Step 1: File upload / path
# ------------------------------------------------------------------
st.subheader("1️⃣ Upload your data file")

col1, col2 = st.columns([1, 1])
with col1:
    uploaded_file = st.file_uploader("Choose CSV / Excel / XML", type=['csv', 'xlsx', 'xls', 'xml'])
    file_path = None
with col2:
    file_path = st.text_input("Or paste a local file path", value="")
    st.caption("Leave blank if you use the file upload")

data = None
data_error = None
if uploaded_file or file_path:
    try:
        data = read_file(uploaded_file, file_path)
    except Exception as e:
        data_error = str(e)

if data_error:
    st.error(data_error)
else:
    st.success("✅ File read successfully")
    # Show preview
    if isinstance(data, pd.DataFrame):
        st.write("📄 *Data preview* (first 5 rows):")
        st.dataframe(data.head())
    else:
        st.write("📄 *Data preview* (XML key/value):")
        st.json(data)

# ------------------------------------------------------------------
# Step 2: Market price
# ------------------------------------------------------------------
st.subheader("2️⃣ Market Price")
market_price = st.number_input("Enter current market price per share",
                               min_value=0.0,
                               step=0.01,
                               value=0.0,
                               format="%.2f")

# ------------------------------------------------------------------
# Step 3: Compute
# ------------------------------------------------------------------
if st.button("🔍 Compute Metrics"):
    if data is None:
        st.error("No data – upload a file or provide a path first.")
    else:
        # reset error log
        error_log = []
        fin = FinanceMetrics(data, market_price)
        fin.compute()

        # ------------------------------------------------------------------
        # 3a: Display results table
        # ------------------------------------------------------------------
        with st.expander("📊 Calculated Metrics", expanded=True):
            metrics_df = pd.DataFrame.from_dict(fin.metrics,
                                                orient="index",
                                                columns=["Value"])
            metrics_df["Value"] = metrics_df["Value"].apply(
                lambda x: f"{x:.4f}" if isinstance(x, float) else (x if x is not None else "N/A")
            )
            st.dataframe(metrics_df.sort_index())

        # ------------------------------------------------------------------
        # 3b: Show errors
        # ------------------------------------------------------------------
        with st.expander("⚠️ Errors / Missing Data", expanded=False):
            if error_log:
                st.write("- " + "\n- ".join(error_log))
            else:
                st.write("✅ No errors detected.")

        # ------------------------------------------------------------------
        # 3c: Download text file
        # ------------------------------------------------------------------
        txt_output = io.StringIO()
        txt_output.write(f"Financial Metrics Report\n")
        txt_output.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        txt_output.write(f"Input source: {file_path if file_path else uploaded_file.name if uploaded_file else 'unknown'}\n\n")
        txt_output.write("=== Calculated Metrics ===\n")
        for k, v in fin.metrics.items():
            val = v if v is not None else "N/A"
            txt_output.write(f"{k}: {val}\n")
        txt_output.write("\n=== Errors & Missing Data ===\n")
        if error_log:
            txt_output.write("\n".join(error_log))
        else:
            txt_output.write("No errors detected.\n")

        txt_bytes = txt_output.getvalue().encode("utf-8")
        st.download_button(
            label="📥 Download financial_metrics.txt",
            data=txt_bytes,
            file_name="financial_metrics.txt",
            mime="text/plain",
        )