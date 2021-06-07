from nwb_conversion_tools import (
    NWBConverter, AxonaRecordingExtractorInterface, AxonaPositionDataInterface
)


class HussainiNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaRecordingExtractorInterface=AxonaRecordingExtractorInterface,
        AxonaPositionDataInterface=AxonaPositionDataInterface
    )
