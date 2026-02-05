# SPDX-FileCopyrightText: 2026 InOrbit, Inc.
#
# SPDX-License-Identifier: MIT

"""Configuration models for FLOWCore connector."""

# Third Party
from pydantic import (
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


# InOrbit
from inorbit_connector.models import ConnectorConfig, RobotConfig

CONNECTOR_TYPE = "flowcore"

# Default environment file, relative to the directory the connector is executed from. If using a
# different .env file, make sure to source it before running the connector.
DEFAULT_ENV_FILE = "config/.env"


class FlowcoreRobotConfig(RobotConfig):
    """Robot configuration with FLOWCore-specific fields.

    Extends base RobotConfig to include Fleet robot ID.

    Attributes:
        robot_id (str): InOrbit robot ID
        fleet_robot_id (int): Robot ID in FLOWCore
        cameras (list): Camera configurations (inherited)
    """

    fleet_robot_id: int


class FlowcoreConfig(BaseSettings):
    """Custom configuration fields for FLOWCore connector.

    These are fleet-wide settings shared by all robots.

    Attributes:
        fleet_host (str): Fleet server IP or hostname
        fleet_port (int): Fleet server port
        fleet_username (str): Fleet API username
        fleet_password (str): Fleet API password

    If any field is missing, the initializer will attempt to replace it by reading from the
    environment. Values are set in the environment with the prefix INORBIT_FLOWCORE_
        (e.g. fleet_host -> INORBIT_FLOWCORE_FLEET_HOST)
    """

    model_config = SettingsConfigDict(
        env_prefix=f"INORBIT_{CONNECTOR_TYPE.upper()}_",
        env_ignore_empty=True,
        case_sensitive=False,
        env_file=DEFAULT_ENV_FILE,
        extra="allow",
    )

    fleet_host: str
    fleet_port: int = 80
    fleet_username: str
    fleet_password: str


class FlowcoreConnectorConfig(ConnectorConfig):
    """Configuration for FLOWCore connector.

    Inherits from ConnectorConfig and adds FLOWCore-specific fields.

    Attributes:
        connector_config (FlowcoreConfig): FLOWCore-specific configuration
        fleet (list[FlowcoreRobotConfig]): List of robot configurations
    """

    connector_config: FlowcoreConfig  # type: ignore[assignment]
    fleet: list[FlowcoreRobotConfig]  # type: ignore[assignment]

    @field_validator("connector_type")
    def check_connector_type(cls, connector_type: str) -> str:
        """Validate the connector type.

        Args:
            connector_type (str): The connector type from config

        Returns:
            str: The validated connector type

        Raises:
            ValueError: If connector type doesn't match expected value
        """
        if connector_type != CONNECTOR_TYPE:
            raise ValueError(
                f"Expected connector type '{CONNECTOR_TYPE}' not '{connector_type}'"
            )
        return connector_type

    @model_validator(mode="after")
    def validate_unique_fleet_robot_ids(self) -> "FlowcoreConnectorConfig":
        """Validate that fleet_robot_id values are unique across the fleet.

        Returns:
            FlowcoreConnectorConfig: The validated configuration

        Raises:
            ValueError: If fleet_robot_id values are not unique
        """
        fleet_ids = [robot.fleet_robot_id for robot in self.fleet]
        if len(fleet_ids) != len(set(fleet_ids)):
            raise ValueError("fleet_robot_id values must be unique")
        return self
