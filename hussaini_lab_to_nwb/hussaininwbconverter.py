from nwb_conversion_tools import (
    NWBConverter,
    AxonaRecordingExtractorInterface,
    AxonaUnitRecordingExtractorInterface,
    AxonaPositionDataInterface,
    AxonaLFPDataInterface
)


# Make NWBConverters from datainterfaces for sensible combinations of datainterfaces
class HussainiBinNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaRecordingExtractorInterface=AxonaRecordingExtractorInterface
    )


class HussainiBinPosLfpNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaRecordingExtractorInterface=AxonaRecordingExtractorInterface,
        AxonaPositionDataInterface=AxonaPositionDataInterface,
        AxonaLFPDataInterface=AxonaLFPDataInterface
    )


class HussainiTetrodeNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaUnitRecordingExtractorInterface=AxonaUnitRecordingExtractorInterface
    )


class HussainiPosNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaPositionDataInterface=AxonaPositionDataInterface
    )


class HussainiLfpNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaLFPDataInterface=AxonaLFPDataInterface
    )


class HussainiUnitNWBConverter(NWBConverter):
    data_interface_classes = dict(
        AxonaUnitRecordingExtractorInterface=AxonaUnitRecordingExtractorInterface,
        AxonaPositionDataInterface=AxonaPositionDataInterface,
        AxonaLFPDataInterface=AxonaLFPDataInterface
    )
