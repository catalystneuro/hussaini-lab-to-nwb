import pandas as pd
import numpy as np
from collections import Counter, deque


def compare_spike_samples_between_recordings(rec1, rec2, sorting=None):
    ''' Given two AxonaUnitRecordingExtractor objects, one based on .X files
    created from the raw recording using a thresholding method, and one created
    from the .X files using a spike sorting algorithm, compute comparison metrics
    of how well spike times correspond for each tetrode.

    Parameters
    ----------
    rec1, rec2 : AxonaUnitRecordingExtractor
        The recording extractor used for the tint conversion and the recording
        extractor from reading the converted data back in.
    sorting : SortingExtractor or None, default=None (optional)
        The sorting extractor used for the tint conversion. When not provided
        there is no information about how many units were deteced per tetrode.

    Returns
    -------
    df : pandas.DataFrame
    '''
    assert (rec1.neo_reader.spike_channels_count() > 0) and (rec2.neo_reader.spike_channels_count() > 0), \
        'No spikes found in at least one specified recording extractor. Maybe there are no `.X` files?'

    channel_groups = np.unique(rec1.get_channel_groups())

    if sorting:
        unit_group_ids = sorting.get_units_property(property_name='group')
        num_units_per_group = Counter(unit_group_ids)
    else:
        num_units_per_group = [np.nan] * len(channel_groups)

    for i, group_id in enumerate(channel_groups):

        # Note: `spike_channel_index` is actually the group id (i.e. tetrode id - 1)
        # Note: Spiketimes are sampled at twice the signal's frequency
        old_timestamps = deque(rec1.neo_reader.get_spike_timestamps(spike_channel_index=group_id) // 2)
        new_timestamps = deque(rec2.neo_reader.get_spike_timestamps(spike_channel_index=group_id) // 2)

        paired_spikes, noise_spikes = compare_spike_samples(old_timestamps, new_timestamps)

        metrics = compute_timestamp_comparison_metrics(paired_spikes)
        metrics['group_id'] = group_id
        metrics['num_units'] = num_units_per_group[group_id]
        metrics['num_spikes_thresh'] = len(old_timestamps)
        metrics['num_spikes_sort'] = len(new_timestamps)
        metrics['num_spikes_in_noise'] = noise_spikes

        if i == 0:
            df = pd.DataFrame(metrics)
        else:
            df = df.append(pd.DataFrame(metrics), ignore_index=True)

    return df


def compare_spike_samples(threshold_timestamps, sorting_timestamps):
    ''' Compare overlap between timestamps from original TINT conversion (using only
    a threshold to find spike-times) and timestamps from spike sorting.

    Parameters
    ----------
    threshold_timestamps, sorting_timestamps : deque

    Returns
    -------
    paired_spikes : dict
        Keys are threshold timestamps. Values are lists of tuples of sorting timestamps and the
        timestamp difference between each sorting timestamps and threshold timestamp.
    noise_spikes : int
        Number of sorting timestamps identified in the noise.
    '''
    paired_spikes = {}
    noise_spikes = 0
    get_new = True

    while sorting_timestamps and threshold_timestamps:

        old_ts = threshold_timestamps.popleft()
        if get_new:
            new_ts = sorting_timestamps.popleft()
            get_new = False
        t_diff = new_ts - old_ts

        while t_diff < -50 and sorting_timestamps:
            new_ts = sorting_timestamps.popleft()
            t_diff = new_ts - old_ts
            noise_spikes += 1

        new_spikes = []
        while (abs(t_diff) <= 50) and (sorting_timestamps):
            new_spikes.append((new_ts, t_diff))
            new_ts = sorting_timestamps.popleft()
            t_diff = new_ts - old_ts

        paired_spikes[old_ts] = new_spikes

    return paired_spikes, noise_spikes


def compute_timestamp_comparison_metrics(paired_spikes):
    ''' Given a dictionary from `compare_thresholding_vs_sorting_spike_samples`,
    compute descriptive metrics to evaluate correspondence of the two timestamp series
    and return them in a pandas.DataFrame.

    Parameters
    ----------
    paired_spikes : dict
        Keys are threshold timestamps. Values are lists of tuples of sorting timestamps and the
        timestamp difference between each sorting timestamps and threshold timestamp.

    Returns
    -------
    dict
    '''
    multiple_spikes = 0
    missing_spikes = 0
    non_overlap, abs_non_overlap = [], []
    for k, v in paired_spikes.items():
        if not v:
            missing_spikes += 1
        if len(v) > 1:
            multiple_spikes += 1
        if len(v) >= 1:
            non_overlap.append(sum([el[1] for el in v]))
            abs_non_overlap.append(sum([abs(el[1]) for el in v]))

    stderr_non_overlap = np.std(non_overlap) / np.sqrt(len(non_overlap))
    mean_non_overlap = sum(abs_non_overlap) / len(non_overlap)

    return {
        'num_signal_snippets_found_by_sorter': [len(non_overlap)],
        'num_signal_snippets_with_multiple_spikes': [multiple_spikes],
        'mean_non_overlapping_samples': [mean_non_overlap],
        'stderr_non_overlapping_samples': [stderr_non_overlap]
    }
