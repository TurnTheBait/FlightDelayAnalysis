import pandas as pd
import numpy as np

def calculate_weighted_average(data, value_col, weight_col, scale_factor=1.0, fallback_to_mean=False):
    """
    Calculates the weighted average of a value column based on a weight column.
    
    Args:
        data (pd.DataFrame or pd.Series): The data containing values and weights.
        value_col (str): The name of the column containing values to average.
        weight_col (str): The name of the column containing weights.
        scale_factor (float, optional): Multiplier for the final result. Defaults to 1.0.
        fallback_to_mean (bool, optional): If True, returns the simple mean if total weight is 0. 
                                           If False, returns np.nan if total weight is 0. Defaults to False.
    
    Returns:
        float: The weighted average, or np.nan/mean based on fallback logic.
    """
    total_weight = data[weight_col].sum()
    
    if total_weight == 0:
        if fallback_to_mean:
            return data[value_col].mean()
        return np.nan
        
    weighted_sum = (data[value_col] * data[weight_col]).sum()
    return (weighted_sum / total_weight) * scale_factor
