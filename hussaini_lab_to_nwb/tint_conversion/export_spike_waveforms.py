import os
import struct
from pathlib import Path
import warnings

import numpy as np

import spiketoolkit as st


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
    unit_ids = sorting.get_unit_ids()

    # Guess property name that assigns units to tetrodes if possible
    property_names = sorting.get_unit_property_names(unit_id=unit_ids[0])
    group_property_name = None
    if 'group' not in property_names:
        for property_name in property_names:
            if 'group' in property_name:
                group_property_name = property_name
                warnings.warn('''Using {} property to assign units to tetrode groups,
                    because `groups` was not found'''.format(group_property_name))
                break
    else:
        group_property_name = 'group'
    if group_property_name is None:
        raise Exception('There is no group property name that assigns units to a given tetrode.')

    group_ids = [sorting.get_unit_property(
        unit_id=unit_id, property_name=group_property_name) for unit_id in unit_ids
    ]

    return [int(group_id) for group_id in group_ids]


def combine_units_on_tetrode(group_spike_samples, group_waveforms):
    '''Write all waveforms of given tetrode in dictionary with the
    corresponding spike samples being the keys (1 sample for each
    waveform).

    Parameters
    ----------
    group_spike_samples : list
        As returned by sortingextractor.get_units_spike_train()
    group_waveforms : list
        As returned by spiketoolkit.postprocessing.get_unit_waveforms()

    Returns
    -------
    tetrode_spikes : dict
        Keys are spike samples, values are waveforms (ntrls x nch x nsamp)
    '''
    tetrode_spikes = {}

    for i, (samples, waveforms) in enumerate(zip(group_spike_samples, group_waveforms)):

        for sample, waveform in zip(samples, waveforms):

            tetrode_spikes[sample] = waveform

    return tetrode_spikes


def get_waveforms(recording, sorting, unit_ids, header):
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
    samples_before = int(header['pretrigSamps'])
    samples_after = int(header['spikeLockout'])

    ms_before = samples_before / (sampling_rate / 1000) + 0.001
    ms_after = samples_after / (sampling_rate / 1000) + 0.001

    waveforms = st.postprocessing.get_unit_waveforms(
        recording,
        sorting,
        unit_ids=unit_ids,
        max_spikes_per_unit=None,
        grouping_property='group',
        recompute_info=True,
        ms_before=ms_before,
        ms_after=ms_after,
        return_idxs=False,
        return_scaled=False,
        dtype=np.int8
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
        'sample_rate {} hz\n'.format(Fs),
        'bytes_per_sample {}\n'.format(1),
        'spike_format t,ch1,t,ch2,t,ch3,t,ch4\n',
        'num_spikes {}\n'.format(n_spikes_chan),
        'data_start'
    ]

    with open(tetrode_file, 'w') as f:
        f.writelines(to_write)


def write_tetrode_file_data(tetrode_file, waveform_dict, Fs):
    ''' Write binary data to tetrode file

    Parameters
    ----------
    tetrode_file : str or Path
        Full filename of tetrode file to write to
    waveform_dict : dict
        Keys are spike timestamps, values are corresponding waveforms (np.memmap).
        Timestamps are int64, waveforms are int8
    Fs : int
        Sampling frequency of data
    '''

    # create ordered spike times and waveforms from input dict
    spike_times = np.asarray(sorted(waveform_dict.keys()))
    spike_times = np.tile(spike_times, (4, 1))
    spike_times = spike_times.flatten(order='F')

    n_spikes = spike_times.shape[0]
    spike_values = np.asarray([value for (key, value) in sorted(waveform_dict.items())])
    spike_values = spike_values.reshape((n_spikes, 50))

    # re-adjust spike_times to reflect 96000 hz sampling rate
    spike_times *= 96000 // Fs

    t_packed = struct.pack('>%di' % n_spikes, *spike_times)
    spike_data_pack = struct.pack('<%db' % (n_spikes * 50), *spike_values.flatten())

    # combine timestamps (4 bytes per sample) and waveforms (1 byte per sample)
    comb_list = [None] * (2 * n_spikes)
    comb_list[::2] = [t_packed[i:i + 4] for i in range(0, len(t_packed), 4)]
    comb_list[1::2] = [spike_data_pack[i:i + 50] for i in range(0, len(spike_data_pack), 50)]

    with open(tetrode_file, 'ab') as f:
        f.writelines(comb_list)
        f.writelines([bytes('\r\ndata_end\r\n', 'utf-8')])


def write_tetrode(tetrode_file, waveform_dict, Fs):
    ''' Write data to tetrode (`.X`) file

    Parameters
    ----------
    tetrode_file : str or Path
        Full filename of tetrode file to write to
    waveform_dict : dict
        Keys are spike timestamps, values are corresponding waveforms (np.memmap).
        Timestamps are int64, waveforms are int8
    Fs : int
        Sampling frequency of data
    '''
    write_tetrode_file_header(tetrode_file, len(waveform_dict), Fs)
    write_tetrode_file_data(tetrode_file, waveform_dict, Fs)


def write_to_tetrode_files(recording, sorting, group_ids, set_file):
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
    '''
    sampling_rate = recording.get_sampling_frequency()
    group_ids = get_unit_group_ids(sorting)
    unit_ids = sorting.get_unit_ids()
    header = parse_generic_header(set_file)

    for group_id in np.unique(group_ids):

        # get spike samples and waveforms of this group / tetrode
        group_unit_ids = [unit_ids[i] for i, gid in enumerate(group_ids) if gid == group_id]
        group_waveforms = get_waveforms(recording, sorting, group_unit_ids, header)
        group_spike_samples = sorting.get_units_spike_train(unit_ids=group_unit_ids)

        # assign each waveform to it's spike sample in a dictionary
        spike_waveform_dict = combine_units_on_tetrode(group_spike_samples, group_waveforms)

        tetrode_filename = str(set_file).split('.')[0] + '.{}'.format(group_id + 1)
        print('Writing', Path(tetrode_filename).name)

        # write to tetrode file
        write_tetrode(tetrode_filename, spike_waveform_dict, sampling_rate)
