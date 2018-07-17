from numba import jit
import numpy as np

@jit(nopython=True)
def jit_ma(input_array, k):
    output_array = np.zeros(len(input_array))
    for i in range(k, len(input_array)+1):
        output_array[i-1] = input_array[i-k:i].mean()
    return output_array
