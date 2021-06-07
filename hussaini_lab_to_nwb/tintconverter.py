from .tint_conversion import write_to_tetrode_files, write_unit_labels_to_file


class TintConverter():
    '''A TintConverter class can be used to export spike sorted data to the
    `TINT` format, specifically `.cut`, `.clu` and `.X` files.

    `.cut` and `.clu` files contain unit labels for each spike.

    `.X` files contain the raw recording (from the given recording extractor
    object) for each channel keeping only data surrounding spike times of the
    discovered units (-10 to +40 samples relative to a spike). This is similar
    to the `.X` files created by the Axona acquisition system, except that the
    spike times are determined by the spike-sorting output in the given sorting
    extractor object.

    # Example1:
    tc = TintConveter(recording=my_recording_extractor,
                      sorting=my_sorting_extractor,
                      set_file='my/set/file/path/setfilename.set')
    tc.write_to_tint()

    # Example2:
    tc = TintConveter()
    tc.write_to_tint(recording=my_recording_extractor,
                     sorting=my_sorting_extractor,
                     set_file='my/set/file/path/setfilename.set')
    '''

    def __init__(self, recording=None, sorting=None, set_file=None):
        self.recording = recording
        self.sorting = sorting
        self.set_file = set_file

    def write_to_tint(self, recording=None, sorting=None, set_file=None):
        '''Given recording and sorting extractor objects, write appropriate data
        to TINT format (from Axona). Will therefore create .X (tetrode),
        .cut and .clu (spike sorting information) files.

        Parameters
        ----------
        recording : spikeextractors.RecordingExtractor
        sorting : spikeextractors.SortingExtractor
        set_file : Path or str
            .set file location. Used to determine how many samples prior to and
            post spike sample should be cut out for each waveform. .X files will have
            the same base filename as the .set file. So if you do not want to overwrite
            existing .X files in your .set file directory, copy the .set file to a new
            folder and give its new location. The new files will appear there.

        Notes
        -----
        For details about the .X file format see:
        http://space-memory-navigation.org/DacqUSBFileFormats.pdf
        '''
        if (recording is None) and (self.recording is not None):
            recording = self.recording
        if (sorting is None) and (self.sorting is not None):
            sorting = self.sorting
        if (set_file is None) and (self.set_file is not None):
            set_file = self.set_file

        # writes to .X files for each tetrode
        group_ids = recording.get_channel_groups()
        write_to_tetrode_files(recording, sorting, group_ids, set_file)

        # writes to .cut and .clu files for each tetrode
        write_unit_labels_to_file(sorting, set_file)
