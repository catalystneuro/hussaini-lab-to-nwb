from nwb_conversion_tools import (
    NWBConverter, AxonaRawRecordingExtractorInterface,
    AxonaRawSortingExtractorInterface
)

from .expodatainterface import ExpoDataInterface


class HussainiRawNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaRawExtractorInterface=AxonaRawRecordingExtractorInterface, 
        AxonaRawSortingExtractorInterface=AxonaRawSortingExtractorInterface
    )


# eof

