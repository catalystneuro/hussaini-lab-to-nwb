import os
from pathlib import Path

import numpy as np

from .utils import get_group_property_name


def convert_spike_train_to_label_array(spike_train):
    '''Takes a list of arrays, where each array is a series of
    sample points at which a spike occured for a given unit
    (each list item is a unit). Converts to .cut array, i.e.
    orders spike samples from all units and labels each sample
    with the appropriate unit ID.

    Parameters
    ----------
    spike_train : List of np.arrays
        Output of `get_units_spike_train()` method of sorting extractor

    Return
    ------
    unit_labels_sorted : np.array
        Each entry is the unit ID corresponding to the spike sample that
        occured at this ordinal position
    '''

    # Generate Index array (indexing the unit for a given spike sample)
    unit_labels = []
    for i, l in enumerate(spike_train):
        unit_labels.append(np.ones((len(l),), dtype=int) * i)

    # Flatten lists and sort them
    spike_train_flat = np.concatenate(spike_train).ravel()
    unit_labels_flat = np.concatenate(unit_labels).ravel()

    sort_index = np.argsort(spike_train_flat)

    unit_labels_sorted = unit_labels_flat[sort_index]

    return unit_labels_sorted


def write_to_cut_file(cut_filename, unit_labels):
    '''Write spike sorting output to .cut file.

    Parameters
    ----------
    cut_filename : str or Path
        Full filename of .cut file to write to. A given .cut file belongs
        to a given tetrode file. For example, for tetrode `my_file.1`, the
        corresponding cut_filename should be `my_file_1.cut`.
    unit_labels : np.array
        Vector of unit labels for each spike sample (ordered by time of
        occurence)

    Example
    -------
    # Given a sortingextractor called sorting_nwb:
    spike_train = sorting_nwb.get_units_spike_train()
    unit_labels = convert_spike_train_to_label_array(spike_train)
    write_to_cut_file(cut_filename, unit_labels)

    ---
    Largely based on gebaSpike implementation by Geoff Barrett
    https://github.com/GeoffBarrett/gebaSpike
    '''
    basename = os.path.basename(os.path.splitext(cut_filename)[0])

    n_clusters = len(np.unique(unit_labels))
    n_spikes = len(unit_labels)

    write_list = []

    tab = '    '
    spaces = '               '

    write_list.append('n_clusters: {}\n'.format(n_clusters))
    write_list.append('n_channels: 4\n')
    write_list.append('n_params: 2\n')
    write_list.append('times_used_in_Vt:{}'.format((tab + '0') * 4 + '\n'))

    zero_line = (tab + '0') * 8 + '\n'

    for cell_i in np.arange(n_clusters):
        write_list.append(' cluster: {} center:{}'.format(cell_i, zero_line))
        write_list.append('{}min:{}'.format(spaces, zero_line))
        write_list.append('{}max:{}'.format(spaces, zero_line))
    write_list.append('\nExact_cut_for: {} spikes: {}\n'.format(basename, n_spikes))

    # 25 unit labels per row
    n_rows = int(np.floor(n_spikes / 25))
    remaining = int(n_spikes - n_rows * 25)

    cut_string = ('%3u' * 25 + '\n') * n_rows + '%3u' * remaining

    write_list.append(cut_string % (tuple(unit_labels)))

    with open(cut_filename, 'w') as f:
        f.writelines(write_list)


def write_to_clu_file(clu_filename, unit_labels):
    ''' .clu files are pruned .cut files, containing only a long vector of unit
    labels, which are 1-indexed, instead of 0-indexed. In addition, the very first
    entry is the total number of units.

    Parameters
    ----------
    clu_filename : str or Path
        Full filename of .clu file to write to. A given .clu file belongs
        to a given tetrode file. For example, for tetrode `my_file.1`, the
        corresponding clu_filename should be `my_file_1.clu`.
    unit_labels : np.array
        Vector of unit labels for each spike sample (ordered by time of
        occurence)

    ---
    Largely based on gebaSpike implementation by Geoff Barrett
    https://github.com/GeoffBarrett/gebaSpike
    '''
    unit_labels = np.asarray(unit_labels).astype(int)

    n_clu = len(np.unique(unit_labels))
    unit_labels = np.concatenate(([n_clu], unit_labels))

    np.savetxt(clu_filename, unit_labels, fmt='%d', delimiter='\n')


def set_cut_filename_from_basename(filename, tetrode_id):
    '''Given a str or Path object, assume the last entry after a slash
    is a filename, strip any file suffix, add tetrode ID label, and
    .cut suffix to name.

    Parameters
    ----------
    filename : str or Path
    tetrode_id : int
    '''
    return Path(str(filename).split('.')[0] + '_{}'.format(tetrode_id) + '.cut')


def write_unit_labels_to_file(sorting_extractor, filename):
    '''Write spike sorting output to .cut and .clu file, separately for each
    tetrode.

    Parameters
    ----------
    sorting_extractor : spikeextractors.SortingExtractor
    filename : str or Path
        Full filename of .set file or base-filename (i.e. the part of the
        filename all Axona files have in common). A given .cut file belongs
        to a given tetrode file. For example, for tetrode `my_file.1`, the
        corresponding cut_filename should be `my_file_1.cut`. This will be
        set automatically given the base-filename or set file.
    '''
    group_property_name = get_group_property_name(sorting_extractor)
    tetrode_ids = sorting_extractor.get_units_property(property_name=group_property_name)
    tetrode_ids = np.array(tetrode_ids)

    unit_ids = np.array(sorting_extractor.get_unit_ids())

    for i in np.unique(tetrode_ids):

        print('Write unit labels for tetrode {} to .cut and .clu'.format(i))

        spike_train = sorting_extractor.get_units_spike_train(unit_ids=unit_ids[tetrode_ids == i])
        unit_labels = convert_spike_train_to_label_array(spike_train)
        unit_labels += 1

        # We use Axona conventions for filenames (tetrodes are 1 indexed)
        cut_filename = set_cut_filename_from_basename(filename, i + 1)
        clu_filename = Path(str(cut_filename).replace('.cut', '.clu'))

        write_to_cut_file(cut_filename, unit_labels)
        write_to_clu_file(clu_filename, unit_labels)
