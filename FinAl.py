

import xml.etree.ElementTree as ET

def analyze_financial_data(file_path):
    """
    Parses an XBRL XML file to extract financial data, calculate key ratios,
    and print them in a tabulated format.

    Args:
        file_path (str): The absolute path to the XBRL XML file.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Define namespaces to correctly parse the XBRL file
        namespaces = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'in-capmkt': 'http://www.sebi.gov.in/xbrl/2025-01-31/in-capmkt'
        }

        # Extract all numerical data into a dictionary for easy lookups
        data = {}
        for elem in root.findall('.//', namespaces=namespaces):
            # Check if the element is a financial data point from the specified namespace
            if elem.tag.startswith('{http://www.sebi.gov.in/xbrl/2025-01-31/in-capmkt}'):
                tag_name = elem.tag.split('}')[-1]
                try:
                    # Convert the text content to a float and store it
                    value = float(elem.text)
                    data[tag_name] = value
                except (ValueError, TypeError):
                    # Ignore elements that do not have a numeric value
                    continue

        # --- Key Ratio Calculations ---

        # Retrieve necessary figures from the extracted data
        net_profit = data.get('ProfitLossForPeriod', 0)
        shares_outstanding = data.get('WeightedAverageNumberOfEquitySharesOutstanding', 0)
        total_equity = data.get('Equity', 0)
        
        # A simplified way to calculate total debt for this example
        total_liabilities = data.get('Liabilities', 0)
        total_debt = total_liabilities - total_equity

        # Calculate the ratios, handling potential division by zero
        eps = net_profit / shares_outstanding if shares_outstanding else 0
        bvps = total_equity / shares_outstanding if shares_outstanding else 0
        debt_to_equity = total_debt / total_equity if total_equity else 0

        # --- Formatted Output ---

        print("-------------------------------------------------")
        print("            Key Financial Ratios")
        print("-------------------------------------------------")
        print(f"{'Earnings Per Share (EPS)':<40} | {eps:.2f}")
        print(f"{'Weighted Average Shares Outstanding':<40} | {int(shares_outstanding):,}")
        print(f"{'Book Value Per Share (BVPS)':<40} | {bvps:.2f}")
        print(f"{'Debt-to-Equity Ratio':<40} | {debt_to_equity:.2f}")
        print("-------------------------------------------------")
        print("\nNote: P/E Ratio cannot be calculated as the current")
        print("market price is not available in this file.")
        print("-------------------------------------------------")

    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
    except FileNotFoundError:
        print(f"Error: The file was not found at the specified path: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # Prompt the user to enter the path to the XML file
    xml_file_path = input("Please enter the full path to your financial XML file: ")
    
    # It's good practice to remove quotes if the user pastes a path wrapped in them
    xml_file_path = xml_file_path.strip('\'\"')
    
    analyze_financial_data(xml_file_path)

