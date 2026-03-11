import pandas as pd
import os
import matplotlib.patches as mpatches

CATEGORY_THRESHOLDS = [
    ('Hub',    100000, float('inf')),
    ('Large',  40000,  99999),
    ('Medium', 5000,   39999),
    ('Small',  0,      4999),
]

CATEGORY_COLORS = {
    'Hub':    '#e74c3c',
    'Large':  '#f39c12',
    'Medium': '#3498db',
    'Small':  '#2ecc71',
}

def get_airport_category_and_color(total_flights):
    if pd.isna(total_flights):
        return 'Small', CATEGORY_COLORS['Small']
    for name, low, high in CATEGORY_THRESHOLDS:
        if low <= total_flights <= high:
            return name, CATEGORY_COLORS[name]
    return 'Small', CATEGORY_COLORS['Small']

def load_airport_colors(volume_summary_path):
    color_dict = {}
    if os.path.exists(volume_summary_path):
        df = pd.read_csv(volume_summary_path)
        for _, row in df.iterrows():
            code = row['airport_code']
            flights = pd.to_numeric(row['total_flights'], errors='coerce')
            _, color = get_airport_category_and_color(flights)
            color_dict[code] = color
    return color_dict

def draw_colored_y_labels(fig, ax, codes_at_y, color_dict, line_spacing=0.35, wrap_threshold=10):
    from matplotlib.transforms import offset_copy
    import matplotlib.transforms as mtransforms

    ax.set_yticklabels([])
    ax.set_ylabel("")
    
    transform = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    
    for y_idx, codes in enumerate(codes_at_y):
        lines = []
        current_line = []
        for code in codes:
            if len(current_line) >= wrap_threshold:
                lines.append(current_line)
                current_line = [code]
            else:
                current_line.append(code)
        if current_line:
            lines.append(current_line)
            
        start_y = y_idx + (len(lines) - 1) * line_spacing / 2.0
        
        for i, line_elements in enumerate(lines):
            line_y = start_y - i * line_spacing
            
            for j, code in enumerate(reversed(line_elements)):
                color = color_dict.get(code, CATEGORY_COLORS['Small'])
                
                x_offset = -10 - j * 30 
                
                trans_offset = offset_copy(transform, fig=fig, x=x_offset, y=0, units='points')
                
                ax.text(0, line_y, code, color=color, ha='right', va='center', 
                        fontsize=10, fontweight='bold', transform=trans_offset)

def add_category_legend(ax, loc='best'):
    handles = []
    for name, low, high in CATEGORY_THRESHOLDS:
        color = CATEGORY_COLORS[name]
        label = f"{name}" if high == float('inf') else f"{name}"
        patch = mpatches.Patch(color=color, label=label)
        handles.append(patch)
    
    ax.legend(handles=handles, loc=loc, title="Airport Categories", framealpha=0.95)
