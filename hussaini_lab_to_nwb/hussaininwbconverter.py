from nwb_conversion_tools import (
    NWBConverter, AxonaRawRecordingExtractorInterface,
    AxonaRawSortingExtractorInterface
)


class HussainiRawNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaRawExtractorInterface=AxonaRawRecordingExtractorInterface, 
        AxonaRawSortingExtractorInterface=AxonaRawSortingExtractorInterface
    )


# eof

