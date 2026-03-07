import pandas as pd
import numpy as np

def calculate_weighted_average(data, value_col, weight_col, scale_factor=1.0, fallback_to_mean=False):
    total_weight = data[weight_col].sum()
    
    if total_weight == 0:
        if fallback_to_mean:
            return data[value_col].mean()
        return np.nan
        
    weighted_sum = (data[value_col] * data[weight_col]).sum()
    return (weighted_sum / total_weight) * scale_factor
