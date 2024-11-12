import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pykrige.ok import OrdinaryKriging

def calculate_and_plot():
    # Load data from file
    file_path = filedialog.askopenfilename(title="Select data file", 
                                           filetypes=(("CSV files", "*.csv"), 
                                                     ("Excel files", "*.xlsx *.xls"),
                                                     ("All files", "*.*")))
    if not file_path:
        return
    
    # Determine file type and load data
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        messagebox.showerror("Error", "Unsupported file format")
        return
    
    # Perform calculations
    df['Gnorm'] = 978032.53359 * ((1 + (0.00193185265241 * (np.sin(np.radians(df['Lintang'])))**2)) / 
                                  (np.sqrt(1 - (0.00669437999014 * (np.sin(np.radians(df['Lintang'])))**2))))
    df['FAC'] = -0.3085672 * df['Elevation']
    df['FAA'] = df['Gobs'] - (df['Gnorm'] + df['FAC'])
    df['BC'] = 0.04192 * df['Elevation'] * 2.45
    df['ABS'] = df['FAA'] - df['BC']
    df['ABL'] = df['ABS'] + df['TC']

    # Plot original bed histogram
    plt.figure(figsize=(6, 4))
    plt.hist(df['ABL'], facecolor='red', bins=50, alpha=0.2, edgecolor='black')
    plt.xlim([-50, 100])
    plt.xlabel('ABL')
    plt.ylabel('Frequency')
    plt.title('ABL Histogram')
    plt.grid(True)
    plt.show()

    # Set up figure with two subplots side by side for measurement points and kriging plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)

    # Scatter Plot of Measurement Points
    ax1 = axes[0]
    sc = ax1.scatter(df['Easting'], df['Northing'], c=df['ABL'], vmin=-50, vmax=100,
                     marker='o', s=0.5, cmap='viridis')
    ax1.set_title('Plot Titik ABL')
    ax1.set_xlabel('X [m]')
    ax1.set_ylabel('Y [m]')
    ax1.axis('scaled')
    ax1.locator_params(nbins=10)

    # Color bar for Scatter Plot
    divider1 = make_axes_locatable(ax1)
    cax1 = divider1.append_axes('right', size='5%', pad=0.1)
    cbar1 = plt.colorbar(sc, ticks=np.linspace(-50, 100, 16), cax=cax1)
    cbar1.set_label("ABL", rotation=270, labelpad=8)

    # Define grid bounds based on data range for kriging
    res = 100
    xmin, xmax = df['Easting'].min(), df['Easting'].max()
    ymin, ymax = df['Northing'].min(), df['Northing'].max()

    # Generate grid points
    grid_x = np.linspace(xmin, xmax, int((xmax - xmin) / res))
    grid_y = np.linspace(ymin, ymax, int((ymax - ymin) / res))

    # Apply Ordinary Kriging to interpolate ABL values
    OK = OrdinaryKriging(
        df['Easting'], df['Northing'], df['ABL'],
        variogram_model='gaussian',
        verbose=False,
        enable_plotting=False
    )
    # Perform kriging on the grid
    grid_matrix, ss = OK.execute('grid', grid_x, grid_y)

    # Gridded ABL Plot (Kriging Interpolation)
    ax2 = axes[1]
    im = ax2.imshow(grid_matrix, extent=(xmin, xmax, ymin, ymax), cmap='gist_earth', vmin=-50, vmax=100,
                    interpolation='none', origin='upper')
    ax2.set_title('(Kriging Interpolation)')
    ax2.set_xlabel('X [m]')
    ax2.set_ylabel('Y [m]')
    ax2.axis('scaled')

    # Color bar for Kriged Plot
    divider2 = make_axes_locatable(ax2)
    cax2 = divider2.append_axes('right', size='5%', pad=0.1)
    cbar2 = plt.colorbar(im, ticks=np.linspace(-50, 100, 16), cax=cax2)
    cbar2.set_label("ABL", rotation=270, labelpad=8)

    # Display plot in GUI
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Create GUI window
window = tk.Tk()
window.title("ABL Plotter")
window.geometry("800x600")

# Add button to select file and calculate plot
btn_load = tk.Button(window, text="Load Data and Plot ABL", command=calculate_and_plot)
btn_load.pack()

# Run the GUI loop
window.mainloop()