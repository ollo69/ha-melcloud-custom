"""Config flow for the MELCloud platform."""
import asyncio
import logging
from typing import Optional

from aiohttp import ClientError, ClientResponseError
from async_timeout import timeout

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback

from .const import DOMAIN, CONF_LANGUAGE, LANGUAGES  # pylint: disable=unused-import
from . import MELCLOUD_SCHEMA, MelCloudAuthentication

_LOGGER = logging.getLogger(__name__)


class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def _create_entry(self, user_input):
        """Register new entry."""
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        await self.async_set_unique_id(username)
        self._abort_if_unique_id_configured({CONF_PASSWORD: password})
        return self.async_create_entry(
            title=username, data=user_input,
        )

    async def _create_client(
        self,
        user_input
    ):
        """Create client."""
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        language = user_input[CONF_LANGUAGE]

        if password is None: #and token is None:
            raise ValueError(
                "Invalid internal state. Called without password",
            )

        try:
            with timeout(10):
                result = await self._test_authorization(username, password, language)
                if result == False:
                    return self._show_form({"base": "invalid_auth"})

        except ClientResponseError as err:
            if err.status == 401 or err.status == 403:
                return self._show_form({"base": "invalid_auth"})
            return self._show_form({"base": "cannot_connect"})
        except (asyncio.TimeoutError, ClientError):
            return self._show_form({"base": "cannot_connect"})

        return await self._create_entry(user_input)

    async def _test_authorization(self, username, password, language):
        mcauth = MelCloudAuthentication(username, password, LANGUAGES[language])
        return await mcauth.login(self.hass.helpers.aiohttp_client.async_get_clientsession())

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        if user_input is None:
            return self._show_form()

        return await self._create_client(user_input)

    async def async_step_import(self, import_config):
        """Import a config entry."""
        return await self._create_client(import_config)

    @callback
    def _show_form(self, errors=None):
        """Show the form to the user."""

        return self.async_show_form(
            step_id="user",
            data_schema=MELCLOUD_SCHEMA,
            errors=errors if errors else {},
        )
