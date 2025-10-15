import xml.etree.ElementTree as ET
import streamlit as st

def analyze_financial_data(uploaded_file):
    """
    Parses an uploaded XBRL XML file to extract financial data, 
    calculate key ratios, and display them in a Streamlit app.

    Args:
        uploaded_file: The file-like object from Streamlit's file_uploader.
    """
    try:
        # Streamlit's uploaded file object can be parsed directly
        tree = ET.parse(uploaded_file)
        root = tree.getroot()

        namespaces = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'in-capmkt': 'http://www.sebi.gov.in/xbrl/2025-01-31/in-capmkt'
        }

        data = {}
        for elem in root.findall('.//', namespaces=namespaces):
            if elem.tag.startswith('{http://www.sebi.gov.in/xbrl/2025-01-31/in-capmkt}'):
                tag_name = elem.tag.split('}')[-1]
                try:
                    value = float(elem.text)
                    data[tag_name] = value
                except (ValueError, TypeError):
                    continue

        net_profit = data.get('ProfitLossForPeriod', 0)
        shares_outstanding = data.get('WeightedAverageNumberOfEquitySharesOutstanding', 0)
        total_equity = data.get('Equity', 0)
        total_liabilities = data.get('Liabilities', 0)
        total_debt = total_liabilities - total_equity

        eps = net_profit / shares_outstanding if shares_outstanding else 0
        bvps = total_equity / shares_outstanding if shares_outstanding else 0
        debt_to_equity = total_debt / total_equity if total_equity else 0

        # --- Display Results in Streamlit ---
        st.header("Key Financial Ratios")
        
        # Create a dictionary for the ratios to display in a table
        ratio_data = {
            "Metric": ["Earnings Per Share (EPS)", "Weighted Average Shares Outstanding", "Book Value Per Share (BVPS)", "Debt-to-Equity Ratio"],
            "Value": [f"{eps:.2f}", f"{int(shares_outstanding):,}", f"{bvps:.2f}", f"{debt_to_equity:.2f}"]
        }
        st.table(ratio_data)

        st.info("Note: P/E Ratio cannot be calculated as the current market price is not available in the file.")

    except ET.ParseError as e:
        st.error(f"Error parsing XML file: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# --- Streamlit Web App Interface ---
st.title("Financial Ratio Analyzer")
st.write("Upload your financial XBRL (.xml) file to see key ratios.")

# Create the file uploader widget
uploaded_xml = st.file_uploader("Choose an XML file", type="xml")

if uploaded_xml is not None:
    # If a file is uploaded, pass it to the analysis function
    analyze_financial_data(uploaded_xml)