# import numpy as np
# import matplotlib.pyplot as plt
# from mpl_toolkits.axes_grid1 import make_axes_locatable
from cycler import cycler
import warnings
warnings.simplefilter('always', UserWarning)

def check_minmax(val, min_, max_):
    if val < min_:
        val = min_
        warnings.warn('Value below minimum. Set to minimum ({0:}).'.format(val))
    elif val > max_:
        val = max_
        warnings.warn('Value below maximum. Set to maximum ({0:}).'.format(val))
    return val


def light_style():
    colors = '#8dd3c7', '#feffb3', '#bfbbd9', '#fa8174', '#81b1d2', '#fdb462', '#b3de69', '#bc82bd', '#ccebc4', '#ffed6f'
    return {
        'axes.prop_cycle': cycler('color', colors),
        'axes.edgecolor': 'black',
        'axes.facecolor': 'white',
        'axes.labelcolor': 'black',
        'figure.edgecolor': 'black',
        'figure.facecolor': 'white',
        'grid.color': 'black',
        'lines.color': 'black',
        'lines.linewidth': 2,
        'patch.edgecolor': 'black',
        'savefig.edgecolor': 'black',
        'savefig.facecolor': 'white',
        'text.color': 'black',
        'xtick.color': 'black',
        'ytick.color': 'black',
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'font.family': 'sans-serif',
        'font.size':10,
        'font.sans-serif': 'Arial',
        'image.interpolation': 'none',
    }

# plt.rcParams.update(ppt_style())
def dark_style():
    colors = '#8dd3c7', '#feffb3', '#bfbbd9', '#fa8174', '#81b1d2', '#fdb462', '#b3de69', '#bc82bd', '#ccebc4', '#ffed6f'
    return {
        'axes.prop_cycle': cycler('color', colors),
        'axes.edgecolor': 'white',
        'axes.facecolor': 'black',
        'axes.labelcolor': 'white',
        'figure.edgecolor': 'white',
        'figure.facecolor': 'black',
        'grid.color': 'white',
        'lines.color': 'white',
        'lines.linewidth': 2,
        'patch.edgecolor': 'white',
        'savefig.edgecolor': 'white',
        'savefig.facecolor': 'black',
        'text.color': 'white',
        'xtick.color': 'white',
        'ytick.color': 'white',
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'font.family': 'sans-serif',
        'font.size':16,
        'font.sans-serif': 'Arial',
        'image.interpolation': 'none',
    }
