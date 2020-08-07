import os
import rasterio
import numpy as np
from tqdm import tqdm
from rasterio.windows import Window
from math import floor

# file path
wdir = r"F:\MIDS\capstone\BPA_brasil\mapbinomas2.0\brazil" #TO MODIFY:set your working directory
wdir_updated = os.path.join(wdir,"updated")

# parameters
n_block = 10

filelist = [x for x in os.listdir(wdir) if x.endswith(".tif")] #list raster in wdr
filelist.sort()

# two helper functions
## create all possible combinations for 2 lists. This is used to generate all possible windows for a raster
def combinaion_2lists(l1, l2):
    mesh = np.array(np.meshgrid(l1, l2))
    combinations = mesh.T.reshape(-1, 2)
    return combinations
# a wrapper
def write_tiff(path, tiff, window, profile):
    # append to existing raster
    if os.path.exists(path):
        with rasterio.open(path, 'r+') as dst:
            dst.write(tiff.astype(rasterio.uint8),
                      window=window,
                      indexes=1)
    # create empty raster and write
    else:
        with rasterio.open(path, 'w', **profile) as dst:
            dst.write(tiff.astype(rasterio.uint8),
                      window=window,
                      indexes=1)

wdir_updated = os.path.join(wdir,"test")
for x in filelist:
    forest = x[37:41]
    year = x[-8:-4]
    name = forest + year #reduce form name
    rast = os.path.join(wdir, x) #path to raster
    rast_lag = os.path.join(wdir_updated,forest + str(int(year)-1)+".tif") #path to lagged raster
    rast_updated = os.path.join(wdir_updated, name+".tif")
    # get rows and cols
    data = rasterio.open(rast)
    nrow, ncol = data.shape
    del(data)
    row_batch_size = floor(nrow/n_block)
    col_batch_size = floor(ncol/n_block)
    row_list = list(range(0, nrow - row_batch_size + 1, row_batch_size))
    col_list = list(range(0, ncol - col_batch_size + 1, col_batch_size))
    if int(year) == 1985:
        for row_idx, col_idx in tqdm(combinaion_2lists(row_list,col_list)):
            window = Window.from_slices((row_idx, row_idx + row_batch_size),
                                        (col_idx, col_idx + col_batch_size))
            with rasterio.open(rast) as data:
                arr=data.read(1, window=window)
                result = (arr >= 3) & (arr<=5)
                with rasterio.Env():
                    profile = data.profile
                    profile.update(dtype=rasterio.uint8,count=1,compress='lzw')
                    write_tiff(rast_updated, result, window, profile)
    elif int(year) > 1985:
        for row_idx, col_idx in tqdm(combinaion_2lists(row_list,col_list)):
            window = Window.from_slices((row_idx, row_idx + row_batch_size),
                                        (col_idx, col_idx + col_batch_size))
            with rasterio.open(rast) as data, rasterio.open(rast_lag) as data_lag:
                arr=data.read(1, window=window)
                arr_lag=data_lag.read(1, window=window)
                result = (arr >= 3) & (arr<=5) & (arr_lag == 1)
                with rasterio.Env():
                    profile = data.profile
                    profile.update(dtype=rasterio.uint8,count=1,compress='lzw')
                    write_tiff(rast_updated, result, window, profile)
    print("{} done!".format(year))