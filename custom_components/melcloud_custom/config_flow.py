"""Config flow for the MELCloud platform."""
import asyncio
from http import HTTPStatus
import logging

from aiohttp import ClientError, ClientResponseError
from async_timeout import timeout
import pymelcloud

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_TOKEN, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import MELCLOUD_SCHEMA, MelCloudAuthentication
from .const import CONF_LANGUAGE, DOMAIN, LANGUAGES  # pylint: disable=unused-import

_LOGGER = logging.getLogger(__name__)


class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def _create_entry(self, username: str, token: str):
        """Register new entry."""
        await self.async_set_unique_id(username)
        self._abort_if_unique_id_configured({CONF_TOKEN: token})
        return self.async_create_entry(
            title=username,
            data={CONF_TOKEN: token},
        )

    async def _create_client(self, user_input):
        """Create client."""
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        language = user_input[CONF_LANGUAGE]

        if password is None:  # and token is None:
            raise ValueError(
                "Invalid internal state. Called without password",
            )

        try:
            async with timeout(10):
                token = await self._test_authorization(username, password, language)
                if not token:
                    return self._show_form({"base": "invalid_auth"})
                await pymelcloud.get_devices(
                    token,
                    async_get_clientsession(self.hass),
                )

        except ClientResponseError as err:
            if err.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                return self._show_form({"base": "invalid_auth"})
            return self._show_form({"base": "cannot_connect"})
        except (asyncio.TimeoutError, ClientError):
            return self._show_form({"base": "cannot_connect"})

        return await self._create_entry(username, token)

    async def _test_authorization(self, username, password, language):
        mcauth = MelCloudAuthentication(username, password, LANGUAGES[language])
        if await mcauth.login(self.hass):
            return mcauth.auth_token
        return None

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        if user_input is None:
            return self._show_form()

        return await self._create_client(user_input)

    async def async_step_import(self, import_config):
        """Import a config entry."""
        username = import_config[CONF_USERNAME]
        for unique_id in self._async_current_ids():
            if unique_id == username:
                return self.async_abort(reason="already_imported")
        return await self._create_client(import_config)

    @callback
    def _show_form(self, errors=None):
        """Show the form to the user."""

        return self.async_show_form(
            step_id="user",
            data_schema=MELCLOUD_SCHEMA,
            errors=errors if errors else {},
        )
