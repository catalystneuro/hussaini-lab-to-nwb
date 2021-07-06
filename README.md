# hussaini-lab-to-nwb

Repository for converting data used by the Hussaini lab to NWB format. 
Specifically, `Axona` and `Intan` system extracellular electrophysiological recordings.

The package illustrates how to run [spike sorting pipelines](https://github.com/catalystneuro/hussaini-lab-to-nwb/tree/tintconverter/hussaini_lab_to_nwb/tutorials) for either `Axona` or `Intan` data with [spikeinterface](https://github.com/SpikeInterface) in two jupyter notebooks.

In addition, it includes tools for converting spike sorting output to the `TINT` format, which can be ingested with [gebaSpike](https://pypi.org/project/gebaSpike) or TINT. 


# Installation

To install, clone this git repo and do `pip install -e hussaini-lab-to-nwb`. This will install a development version of the package locally. That means that if you make local changes, the package will automatically reflect them. Note that, while some spike sorters are already included in this installation, it is difficult to ensure that their installation runs smoothly on any given setup. An overview of how to install a varity of spike sorters that are supported by `spikeinterface` can be found [here](https://spikeinterface.readthedocs.io/en/latest/sortersinfo.html). 


# Details `Axona` data

It is expected that `Axona` data is read either from `.bin` + `.set` files (raw data), or from `.X` + `.set` files (unit data). Depending on the input data a different `recordingextractor` is used, either `AxonaRecordingExtractor` (raw data) or `AxonaUnitRecordingExtractor` (unit data). 

# TINT conversion

`Axona` data can be converted to the `TINT` format after spike sorting. Note that when using an `AxonaUnitRecordingExtractor` (i.e. unit data with `.X` files), it can be problematic to export the sorting output to `TINT`. This is because the pruned `.X` files only contain data surrounding threshold crossings based on a thresholding procedure applied ot the continuous recording. In-between these pre-selected epochs there is no data. However, since continuous data is needed for spike sorting, we generate Gaussian noise to fill the time periods between epochs. The problem is that the spike sorter might detect spikes at different timestamps than the original thresholding procedure, and the selected epochs can therefore contain samples that are purely noise.

Hence, when unit data is used, it can be useful to assess the mismatch between the original `.X` files and the exported `.X` files. This can be accomplished as follows:

First, you need to copy the `.set` file into a new folder, where you want to create the exported `.X` files after spike sorting. Then, you can run:
```
# Export spike sorted data to TINT format
tc = TintConveter()
tc.write_to_tint(recording=my_recording_extractor,
                 sorting=my_sorting_extractor,
                 set_file='my/output_data/set/file/path/setfilename.set')
                 
# Assess mismatch between original `.X` files and `.X` files from spike sorting output
tc.compare_timestamps_after_conversion(
    filename_old='my/set/file/path/setfilename.set',
    filename_new='my/output_data/set/file/path/setfilename.set'
)
```
