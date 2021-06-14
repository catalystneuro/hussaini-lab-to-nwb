import warnings


def get_group_property_name(sorting):
    ''' Guess property name that assigns units to tetrodes if possible

    Parameters
    ----------
    sorting : spikeextractors.sortingextractor
    '''
    unit_ids = sorting.get_unit_ids()
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

    return group_property_name


def assert_group_names_match(sorting, recording):
    ''' The 'group' property name has to be the same between `sorting`
    and `recording` extractor (ideally it should be 'group', but if it is
    'ch_group' that would still work).

    Parameters
    ----------
    sorting : spikeextractors.sortingextractor
    '''
    unit_ids = sorting.get_unit_ids()
    unit_property_names = sorting.get_unit_property_names(unit_id=unit_ids[0])
    channel_ids = recording.get_channel_ids()
    channel_property_names = recording.get_channel_property_names(channel_id=channel_ids[0])

    if ('group' not in unit_property_names) or ('group' not in channel_property_names):

        unit_group_property = [property_name for property_name in unit_property_names if 'group' in property_name]
        channel_group_property = [property_name for property_name in channel_property_names if 'group' in property_name]

        assert unit_group_property == channel_group_property, \
            'Unit group property name and channel group property name have to match'
