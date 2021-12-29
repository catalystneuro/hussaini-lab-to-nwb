from spikeextractors.extractors.axonaunitrecordingextractor import AxonaUnitRecordingExtractor

from .tint_conversion import (
    write_to_tetrode_files, write_unit_labels_to_file,
    compare_spike_samples_between_recordings
)
from .tint_conversion.utils import assert_group_names_match


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

    It might be desirable to not overwrite existing `.X` files. In that case
    it is recommended to copy the `.set` file to a new folder, since converted
    recordings are saved in the same folder (and with the same file basename)
    as the given `.set` file.

    This approach has the added advantage that it is possible to directly compare
    the timestamps of the old tetrode `.X` files and the new ones (see example 3).

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

    # Example3:
    tc = TintConveter()
    tc.write_to_tint(recording=my_recording_extractor,
                     sorting=my_sorting_extractor,
                     set_file='my/output_data/set/file/path/setfilename.set')
    tc.compare_timestamps_after_conversion(
        filename_old='my/set/file/path/setfilename.set',
        filename_new='my/output_data/set/file/path/setfilename.set'
    )
    '''

    def __init__(self, recording=None, sorting=None, set_file=None):
        self.recording = recording
        self.sorting = sorting
        self.set_file = set_file

    def write_to_tint(self, recording=None, sorting=None, set_file=None, 
                      waveforms_center=0.5):
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
        waveforms_center: float
            Controls the waveform peak location in the 1ms TINT cutout (e.g. 0.5: peak is at 0.5)

        Notes
        -----
        For details about the .X file format see:
        http://space-memory-navigation.org/DacqUSBFileFormats.pdf
        '''
        if (recording is None) and (self.recording is not None):
            recording = self.recording
        else:
            self.recording = recording
        if (sorting is None) and (self.sorting is not None):
            sorting = self.sorting
        else:
            self.sorting = sorting
        if (set_file is None) and (self.set_file is not None):
            set_file = self.set_file
        else:
            self.set_file = set_file

        assert_group_names_match(self.sorting, self.recording)

        # writes to .X files for each tetrode
        group_ids = recording.get_channel_groups()
        write_to_tetrode_files(recording, sorting, group_ids, set_file, waveforms_center)

        # writes to .cut and .clu files for each tetrode
        write_unit_labels_to_file(sorting, set_file)

    def compare_timestamps_after_conversion(self, filename_old, filename_new):
        ''' Given two AxonaUnitRecordingExtractor objects, one based on .X files
        created from the raw recording using a thresholding method, and one created
        from the .X files using a spike sorting algorithm, compute comparison metrics
        of how well spike times correspond for each tetrode.

        Parameters
        ----------
        filename_old, filename_new : str or Path
            Old and new full filenames of pre- and post- conversion `.set` files.

        Returns
        -------
        df : pandas.DataFrame
        '''
        rec1 = AxonaUnitRecordingExtractor(filename=filename_old, noise_std=0)
        rec2 = AxonaUnitRecordingExtractor(filename=filename_new, noise_std=0)

        df = compare_spike_samples_between_recordings(rec1, rec2, sorting=self.sorting)

        return df
