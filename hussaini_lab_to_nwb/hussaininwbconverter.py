from nwb_conversion_tools import (
    AxonaRecordingExtractorInterface,
    AxonaUnitRecordingExtractorInterface,
    AxonaPositionDataInterface,
    AxonaLFPDataInterface,
    IntanRecordingInterface,
    NWBConverter,
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


class HussainiIntanNWBConverter(NWBConverter):
    data_interface_classes = dict(
        IntanRecordingInterface=IntanRecordingInterface,
        AxonaPositionDataInterface=AxonaPositionDataInterface
    )
