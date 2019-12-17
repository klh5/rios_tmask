import json
import sys
from rios import applier
from datetime import datetime
from removeoutliers import RLMRemoveOutliers
import numpy as np

def gen_tmask(info, inputs, outputs, other_args):
    
    """Run per-block by RIOS. In this case each block is a 
    single pixel. Given a block of values for each band for each date, returns
    a numpy array containing a mask where screened out data = 1 and data
    to keep = 0."""
    
    dates = other_args.dates
    
    # Set up default output
    # Assumes all pixels are clear
    results = np.zeros(len(inputs.images), dtype='uint8')
      
    green_vals = np.array([[inputs.images[t][0][0][0]] for t in range(0, len(inputs.images))])
    nir_vals = np.array([[inputs.images[t][1][0][0]] for t in range(0, len(inputs.images))])
    swir1_vals = np.array([[inputs.images[t][2][0][0]] for t in range(0, len(inputs.images))])
        
    model_inputs = np.hstack((other_args.dates, green_vals, nir_vals, swir1_vals))
    
    drop_indices = np.where(np.any(model_inputs == 0, axis=1))
    
    drop_indices = np.array(drop_indices).reshape(-1)

    # Remove any rows where all band values are 0
    model_inputs =  model_inputs[np.all(model_inputs != 0, axis=1)]

    # Need a minimum of 12 observations
    if(len(model_inputs) >= 12):
               
        # Output array needs to be matched in size to input array
        output_arr = np.delete(results, drop_indices)

        tmask = RLMRemoveOutliers(model_inputs, output_arr)

        num_years = np.ceil((np.max(dates) - np.min(dates)) / 365)

        output_arr = tmask.cleanData(num_years, other_args.threshold)

        results = np.insert(output_arr, np.array(drop_indices), np.zeros(len(drop_indices)))
  
    results = results.reshape(len(results), 1, 1, 1)
    
    outputs.outimage = results

def run_tmask(json_fp, output_driver='KEA', num_processes=1, green_band=2, nir_band=4, swir_band=5, threshold=40):
    
    """Main function to run to generate the output masks. Given an input JSON file, 
    generates a mask for each date where 1=cloud/cloud shadow/snow and 0=clear.
    Opening/closing of files, generation of blocks and use of multiprocessing is 
    all handled by RIOS.
    
    Files should already have been masked using Fmask.
    
    json_fp:       Path to JSON file which provides a dictionary where for each
                   date, an input file name and an output file name are provided.
    output_driver: Short driver name for GDAL, e.g. KEA, GTiff.
    bands:         List of GDAL band numbers to use in the analysis, e.g. [2, 5, 7].
    num_processes: Number of concurrent processes to use.
    green_band:    GDAL band number for green spectral band. Defaults to 2.
    nir_band:      GDAL band number for NIR spectral band. Defaults to 4.
    swir_band:     GDAL band number for SWIR spectral band. Defaults to 5.
    threshold:     Numerical threshold for screening out cloud, cloud shadow, and snow.
                   Defaults to 40. See Zhu & Woodcock (2014) for details.
    """
    
    ip_paths = []
    op_paths = []
    dates = []
    
    try:
        # Open and read JSON file containing date:filepath pairs
        with open(json_fp) as json_file:  
            image_list = json.load(json_file)
        
            for date in image_list.items():
                dates.append([datetime.strptime(date[0], '%Y-%m-%d').toordinal()])
                ip_paths.append(date[1]['input'])
                op_paths.append(date[1]['output'])
    except FileNotFoundError:
        print('Could not find the provided JSON file.')
        sys.exit()
    except json.decoder.JSONDecodeError as e:
        print('There is an error in the provided JSON file: {}'.format(e))
        sys.exit()
        
    # Create object to hold input files    
    infiles = applier.FilenameAssociations()
    infiles.images = ip_paths
    
    # Create object to hold output file
    outfiles = applier.FilenameAssociations()
    outfiles.outimage = op_paths
    
    # ApplierControls object holds details on how processing should be done
    app = applier.ApplierControls()
    
    # Set window size to 1 because we are working per-pixel
    app.setWindowXsize(1)
    app.setWindowYsize(1)
    
    # Set output file type
    app.setOutputDriverName(output_driver)
    
    # Use Python's multiprocessing module
    app.setJobManagerType('multiprocessing')
    app.setNumThreads(num_processes)
    
    # Need to tell the applier to only use the specified bands 
    app.selectInputImageLayers([green_band, nir_band, swir_band])
    
    # Set up output layer name
    app.setLayerNames(['tmask'])
    
    # Additional arguments - have to be passed as a single object
    other_args = applier.OtherInputs()
    other_args.dates = dates
    other_args.threshold = threshold
    
    try:
        applier.apply(gen_tmask, infiles, outfiles, otherArgs=other_args, controls=app)
    except RuntimeError as e:
        print('There was an error processing the images: {}'.format(e))
        print('Do all images in the JSON file exist?')

run_tmask(json_fp='example.json', num_processes=4)
