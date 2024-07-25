import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
import io
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='/var/www/packaging/whpackaging/debug.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')

# Initialize an empty DataFrame for package sizes
package_data = pd.DataFrame(columns=["Package Name", "Width", "Height", "Depth", "Quantity"])


def add_package(package_name, width, height, depth, quantity):
    global package_data
    logging.debug(f"Adding package: {package_name}, {width}, {height}, {depth}, {quantity}")
    new_package = pd.DataFrame([{
        "Package Name": package_name,
        "Width": width,
        "Height": height,
        "Depth": depth,
        "Quantity": quantity
    }])
    package_data = pd.concat([package_data, new_package], ignore_index=True)
    logging.debug(f"Updated package data: \n{package_data}")
    return package_data


def draw_layer(packages, layer_number, pallet_width=100, pallet_depth=100):
    fig, ax = plt.subplots()
    start_x = 0
    start_y = 0

    layer_packages = []

    for index, package in packages.iterrows():
        width = package["Width"]
        depth = package["Depth"]
        quantity = package["Quantity"]
        package_name = package["Package Name"]

        for _ in range(quantity):
            if start_x + width > pallet_width:
                start_x = 0
                start_y += depth

            if start_y + depth > pallet_depth:
                break  # Move to next layer

            rect = plt.Rectangle((start_x, start_y), width, depth, edgecolor='black', facecolor='none')
            ax.add_patch(rect)
            ax.text(start_x + width / 2, start_y + depth / 2, package_name, fontsize=8, ha='center', va='center')

            layer_packages.append({
                "Package Name": package_name,
                "Width": width,
                "Height": package["Height"],
                "Depth": depth,
                "Start X": start_x,
                "Start Y": start_y
            })

            start_x += width
            if start_x + width > pallet_width:  # Move to next row if it exceeds the pallet width
                start_x = 0
                start_y += depth

    ax.set_xlim(0, pallet_width)
    ax.set_ylim(0, pallet_depth)
    ax.set_aspect('equal')
    plt.gca().invert_yaxis()
    plt.axis('off')

    plt.title(f"Pallet Layer {layer_number}")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = Image.open(buf)
    plt.close(fig)
    return img, layer_packages


def plan_pallet(height_limit, pallet_width=100, pallet_depth=100):
    global package_data
    layer_height = package_data["Height"].max()
    num_layers = int(height_limit // layer_height)

    images = []
    remaining_packages = package_data.copy()

    for layer in range(1, num_layers + 1):
        # Draw current layer
        img, layer_packages = draw_layer(remaining_packages, layer, pallet_width, pallet_depth)
        images.append(img)

        # Debug: Print remaining packages before updating
        logging.debug("Remaining packages before updating quantities:")
        logging.debug(f"\n{remaining_packages}")

        # Update quantities of remaining packages
        for package in layer_packages:
            idx = remaining_packages.index[(remaining_packages["Package Name"] == package["Package Name"]) &
                                           (remaining_packages["Width"] == package["Width"]) &
                                           (remaining_packages["Height"] == package["Height"]) &
                                           (remaining_packages["Depth"] == package["Depth"])].tolist()[0]
            remaining_packages.at[idx, "Quantity"] -= 1
            if remaining_packages.at[idx, "Quantity"] == 0:
                remaining_packages.drop(idx, inplace=True)
                remaining_packages.reset_index(drop=True, inplace=True)

        # Debug: Print remaining packages after updating
        logging.debug("Remaining packages after updating quantities:")
        logging.debug(f"\n{remaining_packages}")

    return images


# Define the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("## Package Planning App")

    with gr.Tab("Add Package"):
        package_name = gr.Textbox(label="Package Name")
        width = gr.Number(label="Width")
        height = gr.Number(label="Height")
        depth = gr.Number(label="Depth")
        quantity = gr.Number(label="Quantity")
        add_button = gr.Button("Add Package")
        package_table = gr.Dataframe(headers=["Package Name", "Width", "Height", "Depth", "Quantity"])

        add_button.click(add_package, [package_name, width, height, depth, quantity], package_table)

    with gr.Tab("Plan Pallet"):
        height_limit = gr.Number(label="Pallet Height Limit")
        pallet_width = gr.Number(label="Pallet Width", value=100)
        pallet_depth = gr.Number(label="Pallet Depth", value=100)
        plan_button = gr.Button("Plan Pallet")
        planned_pallet = gr.Gallery(label="Pallet Layers")

        plan_button.click(plan_pallet, [height_limit, pallet_width, pallet_depth], planned_pallet)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
