from nwb_conversion_tools import (
    NWBConverter,
    AxonaRecordingExtractorInterface,
    AxonaUnitRecordingExtractorInterface,
    AxonaPositionDataInterface,
    AxonaLFPDataInterface
)


class HussainiNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaRecordingExtractorInterface=AxonaRecordingExtractorInterface,
        AxonaPositionDataInterface=AxonaPositionDataInterface,
        AxonaLFPDataInterface=AxonaLFPDataInterface
    )


class HussainiUnitNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaUnitRecordingExtractorInterface=AxonaUnitRecordingExtractorInterface,
        AxonaPositionDataInterface=AxonaPositionDataInterface,
        AxonaLFPDataInterface=AxonaLFPDataInterface
    )
