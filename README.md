This repository contains a set of functions and classes allowing you to use RIOS to apply the Tmask algorithm to a stack of Top-of-Atmosphere radiance images. The Tmask algorithm uses a season-trend modelling approach along with a threshold to remove additional cloud, cloud shadow, and snow contaminated pixels. This implementation is based on the following paper:

Zhu, Z. and Woodcock, C.E. Automated cloud, cloud shadow, and snow detection in multitemporal Landsat data: An algorithm designed specifically for monitoring land cover change. *Remote Sensing of Environment.* **2014**, *152*, 217–234. doi:10.1016/j.rse.2014.06.012.

The script outputs a binary mask for each date where 0 = clear and 1 = contaminated.

The input is a JSON file containing an input and output file path for each date, e.g:

{"2017-01-13": {"input": "/path/to.input/file/1.kea", "output": "mask1.kea"},
"2017-01-29": {"input": "/path/to.input/file/2.kea", "output": "mask2.kea"},
"2017-02-14": {"input": "/path/to.input/file/3.kea", "output": "mask3.kea"}}

See also the included file example.json. **Images should be listed in date order**.

Tmask uses three input bands: Green, NIR, and SWIR. For Landsat 7, these are bands 2, 4, and 5 and the script will default to these bands. For other satellites, the appropriate bands can be input as arguments (GDAL band numbering).


