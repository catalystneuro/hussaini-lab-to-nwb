import os
import struct
from pathlib import Path

import numpy as np
import spiketoolkit as st

from .utils import get_group_property_name, assert_group_names_match


def parse_generic_header(filename):
    """
    Given a binary file with phrases and line breaks, enters the
    first word of a phrase as dictionary key and the following
    string (without linebreaks) as value. Returns the dictionary.

    Parameters
    ----------
    filename : str or Path
        Full filename.
    """
    header = {}
    with open(filename, 'rb') as f:
        for bin_line in f:
            if b'data_start' in bin_line:
                break
            line = bin_line.decode('cp1252').replace('\r\n', '').replace('\r', '').strip()
            parts = line.split(' ')
            key = parts[0]
            value = ' '.join(parts[1:])
            header[key] = value

    return header


def get_set_header(set_file):
    """
    Given a .set filename, extract the first few lines up until and
    including the line with `sw_version`.

    Parameters
    ----------
    set_file : str or Path
        Full filename of .set file

    ---
    Largely based on gebaSpike implementation by Geoff Barrett
    https://github.com/GeoffBarrett/gebaSpike
    """
    header = ''
    with open(set_file, 'r+') as f:
        for line in f:
            header += line
            if 'sw_version' in line:
                break

    return header


def get_unit_group_ids(sorting):
    '''Get group ids.

    Parameters
    ----------
    sorting : SortingExtractor

    Returns
    -------
    group_ids : List
        List of groups ids for each Unit in `sorting`.
    '''
    group_property_name = get_group_property_name(sorting)

    unit_ids = sorting.get_unit_ids()
    group_ids = [sorting.get_unit_property(
        unit_id=unit_id, property_name=group_property_name) for unit_id in unit_ids
    ]

    return [int(group_id) for group_id in group_ids]


def get_waveforms(recording, sorting, unit_ids, header, waveforms_center):
    '''Get waveforms for specific tetrode.

    Parameters
    ----------
    recording : RecordingExtractor
    sorting : SortingExtractor
    unit_ids : List
        List of unit ids to extract waveforms
    header : dict
        maps parameters from .set file to their values (as strings).

    Returns
    -------
    waveforms : List
        List of np.array (n_spikes, n_channels, n_timepoints) with waveforms for each unit
    '''
    sampling_rate = recording.get_sampling_frequency()
    samples_before = int(50 * waveforms_center)
    samples_after = 50 - samples_before
    header['pretrigSamps'] = str(samples_before)
    header['spikeLockout'] = str(samples_after)

    ms_before = samples_before / (sampling_rate / 1000) + 0.001
    ms_after = samples_after / (sampling_rate / 1000) + 0.001

    group_property_name = get_group_property_name(sorting)
    
    waveforms = st.postprocessing.get_unit_waveforms(
        recording,
        sorting,
        unit_ids=unit_ids,
        max_spikes_per_unit=None,
        grouping_property=group_property_name,
        recompute_info=True,
        ms_before=ms_before,
        ms_after=ms_after,
        return_idxs=False,
        return_scaled=False,
        dtype=np.int16         
    )

    return waveforms


def write_tetrode_file_header(tetrode_file, n_spikes_chan, Fs):
    ''' Generate and write header of tetrode file

    Parameters
    ----------
    tetrode_file : str or Path
        Full filename to write to
    n_spikes_chan : int
        Number of spikes to write to file
    Fs : int
        Sampling frequency of data
    '''
    path = Path(tetrode_file).parent
    filename = Path(tetrode_file).name
    basename = filename.split('.')[0]
    set_file = path / '{}.set'.format(basename)
    
    # We are enforcing the defaults from the file format manual
    header = get_set_header(set_file)
    to_write = [
        header,
        'num_chans 4\n',
        'timebase {} hz\n'.format(96000),
        'bytes_per_timestamp {}\n'.format(4),
        'samples_per_spike {}\n'.format(50),
        'sample_rate {} hz\n'.format(int(Fs)),
        'bytes_per_sample {}\n'.format(1),
        'spike_format t,ch1,t,ch2,t,ch3,t,ch4\n',
        'num_spikes {}\n'.format(n_spikes_chan),
        'data_start'
    ]

    with open(tetrode_file, 'w') as f:
        f.writelines(to_write)


def write_tetrode_file_data(tetrode_file, all_spikes, all_waveforms, Fs):
    ''' Write binary data to tetrode file

    Parameters
    ----------
    tetrode_file : str or Path
        Full filename of tetrode file to write to
    all_spikes : np.array
        Array with all spike timestamps for tetrode (int64)
    all_waveforms : np.array
        Array with all corresponding waveforms (np.memmap) (int8)
    Fs : int
        Sampling frequency of data
    '''

    # create ordered spike times and waveforms from input dict
    spike_times = all_spikes                     # sort the spikes and use the same indexing to sort corresponding waveforms
    spike_times = np.tile(spike_times, (4, 1))
    spike_times = spike_times.flatten(order='F')

    n_spikes = spike_times.shape[0]
    spike_values = all_waveforms #/ 2**4
    spike_values = np.clip(all_waveforms, -128, 127)
    spike_values = spike_values.reshape((n_spikes, 50)).astype(np.int8)

    # re-adjust spike_times to reflect 96000 hz sampling rate
    spike_times *= 96000 // int(Fs)

    t_packed = struct.pack('>%di' % n_spikes, *spike_times)
    spike_data_pack = struct.pack('<%db' % (n_spikes * 50), *spike_values.flatten())

    # combine timestamps (4 bytes per sample) and waveforms (1 byte per sample)
    comb_list = [None] * (2 * n_spikes)
    comb_list[::2] = [t_packed[i:i + 4] for i in range(0, len(t_packed), 4)]
    comb_list[1::2] = [spike_data_pack[i:i + 50] for i in range(0, len(spike_data_pack), 50)]

    with open(tetrode_file, 'ab') as f:
        f.writelines(comb_list)
        f.writelines([bytes('\r\ndata_end\r\n', 'utf-8')])


def write_tetrode(tetrode_file, all_spikes, all_waveforms, Fs):
    ''' Write data to tetrode (`.X`) file

    Parameters
    ----------
    tetrode_file : str or Path
        Full filename of tetrode file to write to
    all_spikes : np.array
        Array with all spike timestamps for tetrode (int64)
    all_waveforms : np.array
        Array with all corresponding waveforms (np.memmap) (int8)
    Fs : int
        Sampling frequency of data
    '''
    write_tetrode_file_header(tetrode_file, len(all_spikes), Fs)
    write_tetrode_file_data(tetrode_file, all_spikes, all_waveforms, Fs)


def write_to_tetrode_files(recording, sorting, group_ids, set_file, waveforms_center=0.5):
    '''Get spike samples and waveforms for all tetrodes specified in
    `group_ids`. Note that `group_ids` is 0-indexed, whereas tetrodes are
    1-indexed (so if you want tetrodes 1+2, specify group_ids=[0, 1]).

    Parameters
    ----------
    recording : RecordingExtractor
    sorting : SortingExtractor
    group_ids : array like
        Tetrodes to include, but 0-indexed (i.e. tetrodeID - 1)
    set_file : Path or str
        .set file location. Used to determine how many samples prior to and
        post spike sample should be cut out for each waveform. .X files will have
        the same base filename as the .set file. So if you do not want to overwrite
        existing .X files in your .set file directory, copy the .set file to a new
        folder and give its new location. The new .X files will appear there.
    waveforms_center: float
            Controls the waveform peak location in the 1ms TINT cutout (e.g. 0.5: peak is at 0.5ms)
    '''

    assert_group_names_match(sorting, recording)

    sampling_rate = recording.get_sampling_frequency()
    group_ids = get_unit_group_ids(sorting)
    unit_ids = sorting.get_unit_ids()
    header = parse_generic_header(set_file)

    for group_id in np.unique(group_ids):

        # get spike samples and waveforms of this group / tetrode
        group_unit_ids = [unit_ids[i] for i, gid in enumerate(group_ids) if gid == group_id]
        group_waveforms = get_waveforms(
            recording, sorting, group_unit_ids, header, waveforms_center)
        group_spike_samples = sorting.get_units_spike_train(unit_ids=group_unit_ids)

        # concatenate all spikes and waveforms
        all_spikes = np.concatenate(group_spike_samples)
        all_waveforms = np.concatenate(group_waveforms)
        sorted_spike_idxs = np.argsort(all_spikes)
        all_spikes_sorted = all_spikes[sorted_spike_idxs]
        all_waveforms_sorted = all_waveforms[sorted_spike_idxs]

        tetrode_filename = str(set_file).split('.')[0] + '.{}'.format(group_id + 1)
        print('Writing', Path(tetrode_filename).name)

        # write to tetrode file
        write_tetrode(tetrode_filename, all_spikes_sorted, all_waveforms_sorted, sampling_rate)
