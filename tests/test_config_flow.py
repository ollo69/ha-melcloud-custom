"""Test the MELCloud config flow."""

import asyncio
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

from aiohttp import ClientError, ClientResponseError
import pymelcloud
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries, data_entry_flow

from custom_components.melcloud_custom.const import DOMAIN

CONFIG_USER = "test-email@test-domain.com"
CONFIG_DATA = {
    "username": CONFIG_USER,
    "password": "test-password",
    "language": "EN",
}

PATCH_SETUP = patch(
    "custom_components.melcloud_custom.async_setup",
    return_value=True,
)

PATCH_SETUP_ENTRY = patch(
    "custom_components.melcloud_custom.async_setup_entry",
    return_value=True,
)


@pytest.fixture(name="connect")
def mock_controller_connect():
    """Mock a successful connection."""
    with patch(
        "custom_components.melcloud_custom.config_flow.MelCloudAuthentication",
    ) as service_mock:
        service_mock.return_value.login = AsyncMock(return_value=True)
        service_mock.return_value.auth_token = "test-token"
        yield service_mock


@pytest.fixture(name="get_devices")
def mock_get_devices():
    """Mock pymelcloud get_devices."""
    with patch(
        "custom_components.melcloud_custom.config_flow.pymelcloud.get_devices"
    ) as mock:
        mock.return_value = {
            pymelcloud.DEVICE_TYPE_ATA: [],
            pymelcloud.DEVICE_TYPE_ATW: [],
        }
        yield mock


@pytest.fixture(name="request_info")
def mock_request_info():
    """Mock RequestInfo to create ClientResponseErrors."""
    with patch("aiohttp.RequestInfo") as mock_ri:
        mock_ri.return_value.real_url.return_value = ""
        yield mock_ri


async def test_form(hass, connect, get_devices):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with PATCH_SETUP as mock_setup, PATCH_SETUP_ENTRY as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONFIG_DATA
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == CONFIG_USER
    assert result2["data"] == {
        "token": "test-token",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    "error,reason",
    [(ClientError(), "cannot_connect"), (asyncio.TimeoutError(), "cannot_connect")],
)
async def test_form_errors(hass, connect, error, reason):
    """Test we handle cannot connect error."""
    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert flow_result["type"] == data_entry_flow.FlowResultType.FORM

    connect.return_value.login = AsyncMock(side_effect=error)

    result = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"], user_input=CONFIG_DATA
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": reason}


@pytest.mark.parametrize(
    "error,message",
    [
        (HTTPStatus.UNAUTHORIZED, "invalid_auth"),
        (HTTPStatus.FORBIDDEN, "invalid_auth"),
        (HTTPStatus.INTERNAL_SERVER_ERROR, "cannot_connect"),
    ],
)
async def test_form_response_errors(hass, connect, request_info, error, message):
    """Test we handle response errors."""
    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert flow_result["type"] == data_entry_flow.FlowResultType.FORM

    connect.return_value.login = AsyncMock(
        side_effect=ClientResponseError(request_info(), (), status=error)
    )

    result = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"], user_input=CONFIG_DATA
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": message}


async def test_import_with_token(hass, connect, get_devices):
    """Test successful import."""
    with PATCH_SETUP as mock_setup, PATCH_SETUP_ENTRY as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=CONFIG_DATA,
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == CONFIG_USER
    assert result["data"] == {
        "token": "test-token",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_token_refresh(hass, connect, get_devices):
    """Re-configuration with existing username should refresh token."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"token": "test-original-token"},
        unique_id=CONFIG_USER,
    )
    mock_entry.add_to_hass(hass)

    with PATCH_SETUP as mock_setup, PATCH_SETUP_ENTRY as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=CONFIG_DATA
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    await hass.async_block_till_done()
    assert len(mock_setup.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 0

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    entry = entries[0]
    assert entry.data["token"] == "test-token"
