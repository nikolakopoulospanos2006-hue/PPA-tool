import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io

def export_excel(results: dict, params: dict) -> bytes:
    """
    Δημιουργεί Excel report με τα αποτελέσματα του PPA.
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Sheet 1: Summary
        summary_data = {
            "Metric": [
                "Proposed Strike Price (€/MWh)",
                "Min Viable Strike P50 (€/MWh)",
                "Min Viable Strike P90 (€/MWh)",
                "Capture Price (€/MWh)",
                "Baseload Price (€/MWh)",
                "Cannibalization Discount (%)",
                "Offtaker Discount (€/MWh)",
                "Risk Premium (€/MWh)",
                "Developer Margin (€/MWh)",
            ],
            "Value": [
                results["strike_price_proposed"],
                results["min_viable_strike"],
                results["min_viable_strike_p90"],
                results["capture_price"],
                results["baseload_price"],
                results["cannibalization_discount_pct"],
                results["offtaker_discount_eur"],
                results["risk_premium_eur"],
                results["developer_margin_eur"],
            ]
        }
        pd.DataFrame(summary_data).to_excel(
            writer, sheet_name="Strike Price Summary", index=False
        )

        # Sheet 2: Project Parameters
        params_data = {
            "Parameter": [
                "Capacity (MW)",
                "Capacity Factor P50 (%)",
                "Annual Volume (MWh)",
                "PPA Duration (years)",
                "LCOE (€/MWh)",
                "WACC (%)",
                "Indexation Rate (%)",
                "Degradation Rate (%/year)",
            ],
            "Value": [
                params["capacity_mw"],
                params["capacity_factor"],
                params["annual_volume"],
                params["years"],
                params["lcoe"],
                params["discount_rate"],
                params["indexation_rate"],
                params["degradation_rate"],
            ]
        }
        pd.DataFrame(params_data).to_excel(
            writer, sheet_name="Project Parameters", index=False
        )

    return output.getvalue()


def export_pdf(results: dict, params: dict) -> bytes:
    """
    Δημιουργεί PDF summary report.
    """
    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "PPA Strike Price Report", ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Solar Pay-as-Produced | Greek Market | {datetime.now().strftime('%d/%m/%Y')}", 
             ln=True, align="C")
    pdf.ln(8)

    # Strike Price Results
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Strike Price Results", ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 120, 80)
    pdf.cell(0, 8, f"Proposed Strike Price: EUR {results['strike_price_proposed']} /MWh", ln=True)
    
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Min Viable Strike (P50): EUR {results['min_viable_strike']} /MWh", ln=True)
    pdf.cell(0, 7, f"Min Viable Strike (P90): EUR {results['min_viable_strike_p90']} /MWh", ln=True)
    pdf.ln(6)

    # Price Breakdown
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Price Breakdown", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    breakdown = [
        ("Capture Price", f"EUR {results['capture_price']} /MWh"),
        ("Baseload Price", f"EUR {results['baseload_price']} /MWh"),
        ("Cannibalization Discount", f"{results['cannibalization_discount_pct']}%"),
        ("Offtaker Discount", f"EUR {results['offtaker_discount_eur']} /MWh"),
        ("Risk Premium", f"EUR {results['risk_premium_eur']} /MWh"),
        ("Developer Margin", f"EUR {results['developer_margin_eur']} /MWh"),
    ]

    pdf.set_font("Helvetica", "", 10)
    for label, value in breakdown:
        pdf.cell(100, 7, label)
        pdf.cell(0, 7, value, ln=True)
    pdf.ln(6)

    # Project Parameters
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Project Parameters", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    parameters = [
        ("Capacity", f"{params['capacity_mw']} MW"),
        ("Capacity Factor P50", f"{params['capacity_factor']}%"),
        ("Annual Volume", f"{params['annual_volume']:,.0f} MWh"),
        ("PPA Duration", f"{params['years']} years"),
        ("LCOE", f"EUR {params['lcoe']} /MWh"),
        ("WACC", f"{params['discount_rate']}%"),
        ("Indexation Rate", f"{params['indexation_rate']}%"),
        ("Degradation Rate", f"{params['degradation_rate']}%/year"),
    ]

    pdf.set_font("Helvetica", "", 10)
    for label, value in parameters:
        pdf.cell(100, 7, label)
        pdf.cell(0, 7, value, ln=True)

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "* Based on real ENTSO-E Day-Ahead Prices 2024 (Greek Market).", ln=True)
    return bytes(pdf.output())