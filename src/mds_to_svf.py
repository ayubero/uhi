import subprocess
import os

def dem_to_svf(dem_path, output_folder):
    '''
    Transform a digital elevation model (DEM) into a sky view factor (SVF) raster
    
    saga_cmd io_gdal 0 -TRANSFORM 1 -RESAMPLING 3 -GRIDS "MDS.sgrd" -FILES "MDS.tif"
    saga_cmd ta_lighting "Sky View Factor" -DEM "MDS.sgrd" -RADIUS 10000 -METHOD 0 -DLEVEL 3.0 -NDIRS 8 -SVF "SVF.sdat"
    gdal_translate "SVF.sdat" "SVF.tif"
    '''
    mds_sgrd_path = os.path.join(output_folder, 'MDS.sgrd')
    svf_sdat_path = os.path.join(output_folder, 'MDS.sdat')
    svf_tif_path = os.path.join(output_folder, 'SVF.tif')

    # First command: Convert TIFF to SAGA Grid
    subprocess.run(['saga_cmd', 'io_gdal', '0', '-TRANSFORM', '1', '-RESAMPLING', '3', '-GRIDS', mds_sgrd_path, '-FILES', dem_path])

    # Second command: Compute Sky View Factor
    subprocess.run(['saga_cmd', 'ta_lighting', 'Sky View Factor', '-DEM', mds_sgrd_path, '-RADIUS', '10000', '-METHOD', '0', '-DLEVEL', '3.0', '-NDIRS', '8', '-SVF', svf_sdat_path])

    # Third command: Convert SAGA grid to TIFF
    subprocess.run(['gdal_translate', svf_sdat_path, svf_tif_path])
