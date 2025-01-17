from typing import List, Optional

from uaclient.api.api import APIEndpoint
from uaclient.api.data_types import AdditionalInfo, ErrorWarningObject
from uaclient.api.u.pro.status.is_attached.v1 import _is_attached
from uaclient.config import UAConfig
from uaclient.data_types import (
    BoolDataValue,
    DataObject,
    Field,
    StringDataValue,
    data_list,
)


class EnabledService(DataObject):
    fields = [
        Field("name", StringDataValue, doc="Name of the service"),
        Field(
            "variant_enabled",
            BoolDataValue,
            doc="If a variant of the service is enabled",
        ),
        Field(
            "variant_name",
            StringDataValue,
            False,
            doc="Name of the variant, if a variant is enabled",
        ),
    ]

    def __init__(
        self,
        *,
        name: str,
        variant_enabled: bool = False,
        variant_name: Optional[str] = None
    ):
        self.name = name
        self.variant_enabled = variant_enabled
        self.variant_name = variant_name


class EnabledServicesResult(DataObject, AdditionalInfo):
    fields = [
        Field(
            "enabled_services",
            data_list(EnabledService),
            doc="A list of ``EnabledService`` objects",
        ),
    ]

    def __init__(self, *, enabled_services: List[EnabledService]):
        self.enabled_services = enabled_services


def enabled_services() -> EnabledServicesResult:
    return _enabled_services(UAConfig())


def _enabled_services(cfg: UAConfig) -> EnabledServicesResult:
    """
    This endpoint shows the Pro services that are enabled on the machine.
    """
    from uaclient.entitlements import ENTITLEMENT_CLASSES
    from uaclient.entitlements.entitlement_status import UserFacingStatus

    if not _is_attached(cfg).is_attached:
        return EnabledServicesResult(enabled_services=[])

    enabled_services = []  # type: List[EnabledService]
    warnings = []  # type: List[ErrorWarningObject]
    for ent_cls in ENTITLEMENT_CLASSES:
        ent = ent_cls(cfg)
        ent_status, details = ent.user_facing_status()

        if ent_status in (UserFacingStatus.ACTIVE, UserFacingStatus.WARNING):
            ent_name = ent.presentation_name
            enabled_service = EnabledService(name=ent_name)

            for _, variant_cls in ent.variants.items():
                variant = variant_cls(cfg)

                if variant.user_facing_status()[0] == UserFacingStatus.ACTIVE:
                    enabled_service = EnabledService(
                        name=ent_name,
                        variant_enabled=True,
                        variant_name=variant.variant_name,
                    )
                    break

            enabled_services.append(enabled_service)

            if ent_status == UserFacingStatus.WARNING and details:
                warnings.append(
                    ErrorWarningObject(
                        title=details.msg or "",
                        code=details.name or "",
                        meta={"service": ent_name},
                    )
                )

    result = EnabledServicesResult(
        enabled_services=sorted(enabled_services, key=lambda x: x.name),
    )
    result.warnings = warnings

    return result


endpoint = APIEndpoint(
    version="v1",
    name="EnabledServices",
    fn=_enabled_services,
    options_cls=None,
)

_doc = {
    "introduced_in": "28",
    "example_python": """
from uaclient.api.u.pro.status.enabled_services.v1 import enabled_services

result = enabled_services()
""",  # noqa: E501
    "result_class": EnabledServicesResult,
    "exceptions": [],
    "example_cli": "pro api u.pro.status.enabled_services.v1",
    "example_json": """
{
    "enabled_services": [
        {
            "name": "esm-apps",
            "variant_enabled": false,
            "variant_name": null
        },
        {
            "name": "esm-infra",
            "variant_enabled": false,
            "variant_name": null
        },
        {
            "name": "realtime-kernel",
            "variant_enabled": true,
            "variant_name": "raspi"
        }
    ]
}
""",
}
