#The fpdf library does not give good pdf output instead of that we can used reportlab library
#This code is able to generate pallet plot along with container pallet loading and loose loading
#loose loading code in now added

import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
import rectpack


def place_cases_greedy_max_3d(pallet_length, pallet_width, max_stacking_height, case_length, case_width, case_height, pallet_height=5.5):
    best_positions = []

    def overlaps(positions, x, y, length, width):
        for (px, py, r) in positions:
            if r == 0:
                if not (x + length <= px or px + case_length <= x or y + width <= py or py + case_width <= y):
                    return True
            else:
                if not (x + length <= px or px + case_width <= x or y + width <= py or py + case_length <= y):
                    return True
        return False

    def place_case(positions):
        for x in range(pallet_length + 1):
            for y in range(pallet_width + 1):
                if x + case_length <= pallet_length and y + case_width <= pallet_width:
                    if not overlaps(positions, x, y, case_length, case_width):
                        positions.append((x, y, 0))
                        return True
                if x + case_width <= pallet_length and y + case_length <= pallet_width:
                    if not overlaps(positions, x, y, case_width, case_length):
                        positions.append((x, y, 1))
                        return True
        return False

    while place_case(best_positions):
        pass

    max_cases_per_layer = len(best_positions)
    total_case_area = max_cases_per_layer * case_length * case_width
    pallet_area = pallet_length * pallet_width
    area_utilization = (total_case_area / pallet_area) * 100

    available_height = max_stacking_height - pallet_height
    max_layers = int(available_height / case_height)
    max_cases_per_load = max_cases_per_layer * max_layers
    total_case_volume = max_cases_per_load * case_length * case_width * case_height
    pallet_volume = pallet_length * pallet_width * available_height
    volume_utilization = (total_case_volume / pallet_volume) * 100

    return max_cases_per_layer, max_layers, max_cases_per_load, area_utilization, volume_utilization, best_positions

def calculate_pallet_load(max_stacking_height, case_height, pallet_height, max_cases_per_layer, case_net_weight, case_gross_weight, max_pallet_weight):
    available_height = max_stacking_height - pallet_height
    max_layers = int(available_height / case_height)
    max_cases_per_load = max_cases_per_layer * max_layers

    total_net_weight = max_cases_per_load * case_net_weight
    total_gross_weight = max_cases_per_load * case_gross_weight
    load_height = pallet_height + (max_layers * case_height)
    load_gross_weight = total_gross_weight + 50  # Including pallet weight

    # Check if load exceeds pallet maximum weight capacity
    while load_gross_weight > max_pallet_weight and max_layers > 0:
        max_layers -= 1
        max_cases_per_load = max_cases_per_layer * max_layers
        total_net_weight = max_cases_per_load * case_net_weight
        total_gross_weight = max_cases_per_load * case_gross_weight
        load_height = pallet_height + (max_layers * case_height)
        load_gross_weight = total_gross_weight + 50

    return max_layers, max_cases_per_load, total_net_weight, total_gross_weight, load_height, load_gross_weight

def calculate_container_loadability(container_length, container_width, container_height, container_max_weight, container_tare_weight, pallet_length, pallet_width, load_height, load_gross_weight, max_cases_per_load, case_net_weight, case_gross_weight):
    def fit_pallets(container_length, container_width, pallet_length, pallet_width):
        orientations = [
            (pallet_length, pallet_width),
            (pallet_width, pallet_length)
        ]
        max_pallets = 0
        best_orientation = (0, 0)
        for length, width in orientations:
            pallets_lengthwise = container_length // length
            pallets_widthwise = container_width // width
            pallets = pallets_lengthwise * pallets_widthwise
            if pallets > max_pallets:
                max_pallets = pallets
                best_orientation = (length, width)
        return max_pallets, best_orientation

    pallets_per_layer, best_orientation = fit_pallets(container_length, container_width, pallet_length, pallet_width)
    max_layers = container_height // load_height
    max_pallets_per_container = pallets_per_layer * max_layers

    total_cases_per_container = max_pallets_per_container * max_cases_per_load

    pallet_area = best_orientation[0] * best_orientation[1]
    container_area = container_length * container_width
    container_area_utilization = (pallets_per_layer * pallet_area / container_area) * 100

    pallet_volume = pallet_area * load_height
    container_volume = container_length * container_width * container_height
    container_volume_utilization = (pallets_per_layer * pallet_volume * max_layers / container_volume) * 100

    product_net_weight = max_pallets_per_container * max_cases_per_load * case_net_weight
    product_gross_weight = max_pallets_per_container * load_gross_weight

    container_net_weight = product_gross_weight
    container_gross_weight = container_net_weight + container_tare_weight

    return {
        "container_area_utilization": container_area_utilization,
        "container_volume_utilization": container_volume_utilization,
        "total_cases_per_container": total_cases_per_container,
        "max_pallets_per_container": max_pallets_per_container,
        "product_length": container_length,
        "product_width": container_width,
        "product_height": max_layers * load_height,
        "product_net_weight": product_net_weight,
        "product_gross_weight": product_gross_weight,
        "container_length": container_length,
        "container_width": container_width,
        "container_height": container_height,
        "container_net_weight": container_net_weight,
        "container_gross_weight": container_gross_weight
    }

def calculate_container_loadability_loose(container_length, container_width, container_height, container_max_weight, container_tare_weight, case_length, case_width, case_height, case_net_weight, case_gross_weight):
    def fit_cases(container_length, container_width, case_length, case_width):
        orientations = [
            (case_length, case_width),
            (case_width, case_length)
        ]
        max_cases = 0
        best_orientation = (0, 0)
        for length, width in orientations:
            cases_lengthwise = container_length // length
            cases_widthwise = container_width // width
            cases = cases_lengthwise * cases_widthwise
            if cases > max_cases:
                max_cases = cases
                best_orientation = (length, width)
        return max_cases, best_orientation

    cases_per_layer, best_orientation = fit_cases(container_length, container_width, case_length, case_width)
    max_layers = container_height // case_height
    max_cases_per_container = cases_per_layer * max_layers
    
    # Check if total gross weight exceeds container maximum weight capacity
    product_gross_weight = max_cases_per_container * case_gross_weight
    container_gross_weight = product_gross_weight + container_tare_weight
    while container_gross_weight > container_max_weight and max_layers > 0:
        max_layers -= 1
        max_cases_per_container = cases_per_layer * max_layers
        product_gross_weight = max_cases_per_container * case_gross_weight
        container_gross_weight = product_gross_weight + container_tare_weight
    
     # Check if more cases can be added to the top layer if weight allows
    remaining_weight_capacity = container_max_weight - container_gross_weight
    extra_cases = 0
    while remaining_weight_capacity > case_gross_weight and max_layers * case_height + case_height <= container_height:
        if remaining_weight_capacity >= case_gross_weight:
            extra_cases += 1
            remaining_weight_capacity -= case_gross_weight
        else:
            break

    max_cases_per_container += extra_cases

    case_area = best_orientation[0] * best_orientation[1]
    container_area = container_length * container_width
    container_area_utilization = (cases_per_layer * case_area / container_area) * 100

    case_volume = case_area * case_height
    container_volume = container_length * container_width * container_height
    container_volume_utilization = (cases_per_layer * case_volume * max_layers / container_volume) * 100

    product_net_weight = max_cases_per_container * case_net_weight

    container_net_weight = product_gross_weight + extra_cases * case_gross_weight

    case_area = best_orientation[0] * best_orientation[1]
    container_area = container_length * container_width
    container_area_utilization = (cases_per_layer * case_area / container_area) * 100

    case_volume = case_area * case_height
    container_volume = container_length * container_width * container_height
    container_volume_utilization = (cases_per_layer * case_volume * max_layers / container_volume) * 100

    product_net_weight = max_cases_per_container * case_net_weight
    product_gross_weight = max_cases_per_container * case_gross_weight

    container_net_weight = product_gross_weight
    container_gross_weight = container_net_weight + container_tare_weight

    return {
        "container_area_utilization": container_area_utilization,
        "container_volume_utilization": container_volume_utilization,
        "total_cases_per_container": max_cases_per_container,
        "cases_per_layer": cases_per_layer,
        "layers_per_load": max_layers,
        "extra_cases_top_layer": extra_cases,
        "product_length": container_length,
        "product_width": container_width,
        "product_height": max_layers * case_height,
        "product_net_weight": product_net_weight,
        "product_gross_weight": product_gross_weight,
        "container_length": container_length,
        "container_width": container_width,
        "container_height": container_height,
        "container_net_weight": container_net_weight,
        "container_gross_weight": container_gross_weight
    }


'''def plot_pallet(pallet_length, pallet_width, positions, case_length, case_width, case_height):
    fig, ax = plt.subplots()
    for x, y, rotation in positions:
        if rotation == 0:
            rect = plt.Rectangle((x, y), case_length, case_width, edgecolor='r', facecolor='none')
        else:
            rect = plt.Rectangle((x, y), case_width, case_length, edgecolor='r', facecolor='none')
        ax.add_patch(rect)
    plt.xlim(0, pallet_length)
    plt.ylim(0, pallet_width)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.title(f"Pallet Layout - {len(positions)} cases")
    plt.show()'''

#pdf creation code 
def create_pdf_report(sku, pallet_length, pallet_width, positions, case_length, case_width, case_height, df_main, df_summary, df_container_40, df_container_summary_40, df_container_20, df_container_summary_20, df_container_loose_40, df_container_summary_loose_40, df_container_loose_20, df_container_summary_loose_20):
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", 'B', 12)
            self.cell(200, 10, txt="Unilever International Pallet Loading Report", ln=True, align='C')
            self.ln(10)

    pdf = PDF()
    pdf.add_page()

    # Adding the pallet plot
    fig, ax = plt.subplots()
    for x, y, rotation in positions:
        if rotation == 0:
            rect = plt.Rectangle((x, y), case_length, case_width, edgecolor='r', facecolor='none')
        else:
            rect = plt.Rectangle((x, y), case_width, case_length, edgecolor='r', facecolor='none')
        ax.add_patch(rect)
    plt.xlim(0, pallet_length)
    plt.ylim(0, pallet_width)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.title(f"Pallet Layout - {len(positions)} cases")
    plt.savefig("pallet_layout.png")
    plt.close()

    pdf.image("pallet_layout.png", x=10, y=30, w=190)
    pdf.ln(85)
    
    # Add a page
    pdf.add_page()
    
    # Adding the tables
    def add_table(pdf, title, df):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=title, ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 10)
        col_width = pdf.w / (len(df.columns) + 1)
        for col in df.columns:
            pdf.cell(col_width, 10, col, border=1, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=10)
        for index, row in df.iterrows():
            for col in row:
                pdf.cell(col_width, 10, txt=str(col), border=1, align='C')
            pdf.ln(10)
        pdf.ln(10)
    add_table(pdf, "Details", df_main)
    add_table(pdf, "Summary", df_summary)
    add_table(pdf, "Container Loadability Details for 40-STD-S Container", df_container_40)
    add_table(pdf, "Container Loadability Summary for 40-STD-S Container", df_container_summary_40)
    add_table(pdf, "Container Loadability Details for 20-STD-S Container", df_container_20)
    add_table(pdf, "Container Loadability Summary for 20-STD-S Container", df_container_summary_20)
    add_table(pdf, "Container Loose Loading details for 40-STD-S Container", df_container_loose_40)
    add_table(pdf, "Container Loose Loading summary for 40-STD-S Container", df_container_summary_loose_40)
    add_table(pdf, "Container Loose Loading Details for 20-STD-S Container", df_container_loose_20)
    add_table(pdf, "Container Loadability Summary for 20-STD-S Container", df_container_summary_loose_20)

    pdf.output(sku+".pdf")
    print("\nPDF report has been created.")

#Function for taking input from the excel
def main():
    # Read input data from Excel file
    input_file = 'input_data.xlsx'
    df = pd.read_excel(input_file, sheet_name='Sheet1')

    for index, row in df.iterrows():
        sku = row["SKU"]
        case_length = row['case_length']
        case_width = row['case_width']
        case_height = row['case_height']
        case_net_weight = row['case_net_weight']
        case_gross_weight = row['case_gross_weight']
        max_stacking_height = row['max_stacking_height']

        # Pallet dimensions
        pallet_length = 48
        pallet_width = 40
        pallet_height = 5.5
        max_pallet_weight = 2000

        # Calculate the maximum number of cases per layer on the pallet
        max_cases_per_layer, max_layers, max_cases_per_load, area_utilization, volume_utilization, positions = place_cases_greedy_max_3d(
            pallet_length, pallet_width, max_stacking_height, case_length, case_width, case_height, pallet_height)

        # Calculate the pallet load details
        max_layers, max_cases_per_load, total_net_weight, total_gross_weight, load_height, load_gross_weight = calculate_pallet_load(
            max_stacking_height, case_height, pallet_height, max_cases_per_layer, case_net_weight, case_gross_weight, max_pallet_weight)

        # Plotting the pallet layout
        #plot_pallet(pallet_length, pallet_width, positions, case_length, case_width, case_height)

        # Data for the main details table
        data_main = {
            "": ["Case", "Product", "Load"],
            "Length (in)": [case_length, pallet_length, pallet_length],
            "Width (in)": [case_width, pallet_width, pallet_width],
            "Height (in)": [case_height, max_layers * case_height, load_height],
            "Net Weight (lbs)": [case_net_weight, total_net_weight, total_gross_weight],
            "Gross Weight (lbs)": [case_gross_weight, total_gross_weight, load_gross_weight]
        }
        
        df_main = pd.DataFrame(data_main)

        # Data for the summary table
        data_summary = {
            "Summary": ["Number of cases per layer", "Number of layers per load", "Number of cases per load", 
                        "Area utilization by the cases (%)", "Cube (volume) utilization by the cases (%)"],
            "Value": [max_cases_per_layer, max_layers, max_cases_per_load, f"{area_utilization:.2f}", f"{volume_utilization:.2f}"]
        }
        df_summary = pd.DataFrame(data_summary)

        # Container dimensions and weight limits for 40-STD-S container
        container_length_40 = 476
        container_width_40 = 92
        container_height_40 = 102
        container_tare_weight_40 = 8000
        container_max_weight_40 = 55000

        container_stats_40 = calculate_container_loadability(
            container_length_40, container_width_40, container_height_40, container_max_weight_40, container_tare_weight_40,
            pallet_length, pallet_width, load_height, load_gross_weight, max_cases_per_load,
            case_net_weight, case_gross_weight
        )

        container_stats_loose_40 = calculate_container_loadability_loose(
            container_length_40, container_width_40, container_height_40, container_max_weight_40, container_tare_weight_40,
            case_length, case_width, case_height, case_net_weight, case_gross_weight
        )


        # Data for the container loadability table for 40-STD-S container
        data_container_40 = {
            "": ["Product", "40-STD container"],
            "Length (in)": [container_stats_40["product_length"], container_stats_40["container_length"]],
            "Width (in)": [container_stats_40["product_width"], container_stats_40["container_width"]],
            "Height (in)": [container_stats_40["product_height"], container_stats_40["container_height"]],
            "Net Weight (lbs)": [container_stats_40["product_net_weight"], container_stats_40["container_net_weight"]],
            "Gross Weight (lbs)": [container_stats_40["product_gross_weight"], container_stats_40["container_gross_weight"]]
        }
        df_container_40 = pd.DataFrame(data_container_40)

        data_container_summary_40 = {
            "Summary": ["Container area used in %", "Container cube used in %", "Number of cases per 40-STD-S container", "Number of loads per 40-STD-S container"],
            "Value": [f"{container_stats_40['container_area_utilization']:.2f}", f"{container_stats_40['container_volume_utilization']:.2f}", container_stats_40["total_cases_per_container"], container_stats_40["max_pallets_per_container"]]
        }
        df_container_summary_40 = pd.DataFrame(data_container_summary_40)

        # Data for the container loose loadability table for 40-STD-S container
        data_container_loose_40 = {
            "": ["Loose Loading (40-STD container)", "40-STD container"],
            "Length (in)": [container_stats_loose_40["product_length"], container_stats_loose_40["container_length"]],
            "Width (in)": [container_stats_loose_40["product_width"], container_stats_loose_40["container_width"]],
            "Height (in)": [container_stats_loose_40["product_height"], container_stats_loose_40["container_height"]],
            "Net Weight (lbs)": [container_stats_loose_40["product_net_weight"], container_stats_loose_40["container_net_weight"]],
            "Gross Weight (lbs)": [container_stats_loose_40["product_gross_weight"], container_stats_loose_40["container_gross_weight"]]
        }
        df_container_loose_40 = pd.DataFrame(data_container_loose_40)

        data_container_summary_loose_40 = {
            "Summary": ["Container area used in %", "Container cube used in %", "Number of cases per 40-STD-S container", "Extra cases on top layer"],
            "Value": [f"{container_stats_loose_40['container_area_utilization']:.2f}", f"{container_stats_loose_40['container_volume_utilization']:.2f}", container_stats_loose_40["total_cases_per_container"], container_stats_loose_40["extra_cases_top_layer"]]
        }
        df_container_summary_loose_40 = pd.DataFrame(data_container_summary_loose_40)


        # Container dimensions and weight limits for 20-STD-S container
        container_length_20 = 240
        container_width_20 = 91.3386
        container_height_20 = 92.5197
        container_tare_weight_20 = 5511.5
        container_max_weight_20 = 55000

        container_stats_20 = calculate_container_loadability(
            container_length_20, container_width_20, container_height_20, container_max_weight_20, container_tare_weight_20,
            pallet_length, pallet_width, load_height, load_gross_weight, max_cases_per_load,
            case_net_weight, case_gross_weight
        )

        container_stats_loose_20 = calculate_container_loadability_loose(
            container_length_20, container_width_20, container_height_20, container_max_weight_20, container_tare_weight_20,
            case_length, case_width, case_height, case_net_weight, case_gross_weight
        )

        # Data for the container loadability table for 20-STD-S container
        data_container_20 = {
            "": ["Product", "20-STD container"],
            "Length (in)": [container_stats_20["product_length"], container_stats_20["container_length"]],
            "Width (in)": [container_stats_20["product_width"], container_stats_20["container_width"]],
            "Height (in)": [container_stats_20["product_height"], container_stats_20["container_height"]],
            "Net Weight (lbs)": [container_stats_20["product_net_weight"], container_stats_20["container_net_weight"]],
            "Gross Weight (lbs)": [container_stats_20["product_gross_weight"], container_stats_20["container_gross_weight"]]
        }
        df_container_20 = pd.DataFrame(data_container_20)

        data_container_summary_20 = {
            "Summary": ["Container area used in %", "Container cube used in %", "Number of cases per 20-STD-S container", "Number of loads per 20-STD-S container"],
            "Value": [f"{container_stats_20['container_area_utilization']:.2f}", f"{container_stats_20['container_volume_utilization']:.2f}", container_stats_20["total_cases_per_container"], container_stats_20["max_pallets_per_container"]]
        }
        df_container_summary_20 = pd.DataFrame(data_container_summary_20)
        
         # Data for the container loose loadability table for 20-STD-S container
        data_container_loose_20 = {
            "": ["Loose Loading (20-STD container)", "20-STD container"],
            "Length (in)": [container_stats_loose_20["product_length"], container_stats_loose_20["container_length"]],
            "Width (in)": [container_stats_loose_20["product_width"], container_stats_loose_20["container_width"]],
            "Height (in)": [container_stats_loose_20["product_height"], container_stats_loose_20["container_height"]],
            "Net Weight (lbs)": [container_stats_loose_20["product_net_weight"], container_stats_loose_20["container_net_weight"]],
            "Gross Weight (lbs)": [container_stats_loose_20["product_gross_weight"], container_stats_loose_20["container_gross_weight"]]
        }
        df_container_loose_20 = pd.DataFrame(data_container_loose_20)

        data_container_summary_loose_20 = {
            "Summary": ["Container area used in %", "Container cube used in %", "Number of cases per 20-STD-S container", "Extra cases on top layer"],
            "Value": [f"{container_stats_loose_20['container_area_utilization']:.2f}", f"{container_stats_loose_20['container_volume_utilization']:.2f}", container_stats_loose_20["total_cases_per_container"], container_stats_loose_20["extra_cases_top_layer"]]
        }
        df_container_summary_loose_20 = pd.DataFrame(data_container_summary_loose_20)
        
        # Generate PDF report
        create_pdf_report(
            sku, pallet_length, pallet_width, positions, case_length, case_width, case_height, 
            df_main, df_summary, df_container_40, df_container_summary_40, 
            df_container_20, df_container_summary_20, df_container_loose_40, 
            df_container_summary_loose_40, df_container_loose_20, df_container_summary_loose_20
        )
        
if __name__ == "__main__":
    main()
        