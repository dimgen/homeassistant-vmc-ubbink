import pytest

from vmc_ubbink.select import VMCUbifluxBypassSelect, VMCUbifluxSelect


@pytest.mark.parametrize("entity_class", [VMCUbifluxSelect, VMCUbifluxBypassSelect])
def test_select_device_info_names_the_configured_model(entity_class):
    select = entity_class(None, "test-entry", "W325")

    assert select.device_info["model"] == "Vigor W325"
    assert select.device_info["identifiers"] == {("vmc_ubbink", "test-entry")}
