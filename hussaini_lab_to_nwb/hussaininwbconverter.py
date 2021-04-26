from nwb_conversion_tools import (
    NWBConverter, AxonaRecordingExtractorInterface
)


class HussainiNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaRecordingExtractorInterface=AxonaRecordingExtractorInterface
    )
