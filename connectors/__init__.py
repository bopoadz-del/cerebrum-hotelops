"""Fixture-first hospitality connectors on the normalised event bus."""

from connectors.base import BaseConnector, ConnectorError
from connectors.gaming_cms import GamingCMSConnector
from connectors.grms import GRMSConnector
from connectors.loyalty_lms import LoyaltyLMSConnector
from connectors.maximo import MaximoConnector
from connectors.micros import MicrosConnector
from connectors.opera import OperaConnector

CONNECTORS = {
    "opera": OperaConnector,
    "micros": MicrosConnector,
    "loyalty_lms": LoyaltyLMSConnector,
    "grms": GRMSConnector,
    "maximo": MaximoConnector,
    "gaming_cms": GamingCMSConnector,
}


def get_connector(name: str):
    if name not in CONNECTORS:
        raise KeyError(name)
    return CONNECTORS[name]()
