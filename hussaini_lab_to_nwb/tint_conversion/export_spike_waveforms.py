import os
import struct
from pathlib import Path

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
    group_ids = [sorting.get_unit_property(
        unit_id=unit_id, property_name='group') for unit_id in unit_ids
    ]

    return group_ids


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


def write_tetrode(filepath, data, Fs):

    session_path, session_filename = os.path.split(filepath)
    tint_basename = os.path.splitext(session_filename)[0]
    set_filename = os.path.join(session_path, '%s.set' % tint_basename)

    n = len(data)

    header = get_set_header(set_filename)

    with open(filepath, 'w') as f:
        num_chans = 'num_chans 4'
        timebase_head = '\ntimebase %d hz' % (96000)
        bp_timestamp = '\nbytes_per_timestamp %d' % (4)
        samps_per_spike = '\nsamples_per_spike %d' % (50)
        sample_rate = '\nsample_rate %d hz' % (Fs)
        b_p_sample = '\nbytes_per_sample %d' % (1)
        spike_form = '\nspike_format t,ch1,t,ch2,t,ch3,t,ch4'
        num_spikes = '\nnum_spikes %d' % (n)
        start = '\ndata_start'

        write_order = [header, num_chans, timebase_head, bp_timestamp,
                       samps_per_spike, sample_rate, b_p_sample, spike_form, num_spikes, start]

        f.writelines(write_order)

    # rearranging the data to have a flat array of t1, waveform1, t2, waveform2,...
    spike_times = np.asarray(sorted(data.keys()))

    # the spike times are repeated for each channel
    spike_times = np.tile(spike_times, (4, 1))
    spike_times = spike_times.flatten(order='F')

    spike_values = np.asarray([value for (key, value) in sorted(data.items())])

    # this will create a (n_samples, n_channels, n_samples_per_spike) => (n, 4, 50) sized matrix,
    # create a matrix of all the samples and channels going from ch1 -> ch4 for each spike time
    # time1 ch1_data
    # time1 ch2_data
    # time1 ch3_data
    # time1 ch4_data
    # time2 ch1_data
    # time2 ch2_data
    # .
    # .
    # .

    spike_values = spike_values.reshape((n * 4, 50))  # create the 4nx50 channel data matrix

    # make the first column the time values
    spike_array = np.hstack((spike_times.reshape(len(spike_times), 1), spike_values))

    data = None
    spike_times = None
    spike_values = None

    spike_n = spike_array.shape[0]

    t_packed = struct.pack('>%di' % spike_n, *spike_array[:, 0].astype(int))
    spike_array = spike_array[:, 1:]  # removing time data from this matrix to save memory

    spike_data_pack = struct.pack('<%db' % (spike_n * 50), *spike_array.astype(int).flatten())

    spike_array = None

    # now we need to combine the lists by alternating
    comb_list = [None] * (2 * spike_n)
    comb_list[::2] = [t_packed[i:i + 4] for i in range(0, len(t_packed), 4)]
    comb_list[1::2] = [spike_data_pack[i:i + 50] for i in range(0, len(spike_data_pack), 50)]

    t_packed = None
    spike_data_pack = None

    write_order = []
    with open(filepath, 'rb+') as f:

        write_order.extend(comb_list)
        write_order.append(bytes('\r\ndata_end\r\n', 'utf-8'))

        f.seek(0, 2)
        f.writelines(write_order)


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
    header = parse_generic_header(set_file)

    for group_id in np.unique(group_ids):

        # get spike samples and waveforms of this group / tetrode
        group_unit_ids = [i for i, gid in enumerate(group_ids) if gid == group_id]
        group_waveforms = get_waveforms(recording, sorting, group_unit_ids, header)
        group_spike_samples = sorting.get_units_spike_train(unit_ids=group_unit_ids)

        # Assign each waveform to it's spike sample in a dictionary
        spike_waveform_dict = combine_units_on_tetrode(group_spike_samples, group_waveforms)

        # Set tetrode filename
        tetrode_filename = str(set_file).split('.')[0] + '.{}'.format(group_id + 1)
        print('Writing', Path(tetrode_filename).name)

        # Use `BinConverter` function to write to tetrode file
        write_tetrode(tetrode_filename, spike_waveform_dict, sampling_rate)
