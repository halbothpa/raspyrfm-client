"""Signal classification helpers for RaspyRFM payloads."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
from typing import Dict, Iterable, List, Optional, Set, Tuple

from raspyrfm_client import RaspyRFMClient
from raspyrfm_client.device_implementations.controlunit.actions import Action

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SignalFingerprint:
    """Fingerprint describing a payload independent of the channel config."""

    repetitions: int
    gap: int
    timebase: int
    pulse_count: int
    min_pulse: int
    max_pulse: int


@dataclass(slots=True)
class SignalClassification:
    """Classification result for a payload."""

    actions: Set[Action]
    suggested_type: str

    def to_dict(self) -> Dict[str, object]:
        """Return a serialisable representation."""

        return {
            "actions": sorted(action.name.lower() for action in self.actions),
            "suggested_type": self.suggested_type,
        }


def classify_payload(payload: str) -> Optional[SignalClassification]:
    """Return a best-effort classification for a payload string."""

    fingerprint = _fingerprint_from_payload(payload)
    if fingerprint is None:
        return None

    action_candidates = _fingerprint_action_map().get(fingerprint)
    if not action_candidates:
        return None

    suggested_type = _actions_to_device_type(action_candidates)
    return SignalClassification(actions=set(action_candidates), suggested_type=suggested_type)


def _actions_to_device_type(actions: Iterable[Action]) -> str:
    """Translate a collection of supported actions into a RaspyRFM device type."""

    action_set = set(actions)
    if {Action.BRIGHT, Action.DIMM} & action_set:
        return "light"
    if Action.ON in action_set and Action.OFF in action_set:
        return "switch"
    if action_set == {Action.ON}:
        return "button"
    if action_set >= {Action.PAIR} or action_set >= {Action.UNPAIR}:
        # Pairing remotes act as buttons in the Home Assistant context.
        return "button"
    return "universal"


def _fingerprint_from_payload(payload: str) -> Optional[SignalFingerprint]:
    """Parse a payload into a fingerprint for comparison with the library table."""

    if not payload:
        return None

    body = payload.strip()
    if ":" in body:
        # Strip transport prefix (e.g. ``TXP:`` or ``RXP:``)
        try:
            _, body = body.split(":", 1)
        except ValueError:
            return None

    tokens = [token for token in body.split(",") if token]
    if len(tokens) < 6:
        return None

    try:
        repetitions = int(tokens[2])
        gap = int(tokens[3])
        timebase = int(tokens[4])
        pair_count = int(tokens[5])
    except ValueError:
        return None

    pulses: List[int] = []
    for token in tokens[6:6 + pair_count * 2]:
        try:
            pulses.append(int(token))
        except ValueError:
            return None

    if len(pulses) < 2:
        return None

    min_pulse = min(pulses)
    max_pulse = max(pulses)

    return SignalFingerprint(
        repetitions=repetitions,
        gap=gap,
        timebase=timebase,
        pulse_count=int(len(pulses) / 2),
        min_pulse=min_pulse,
        max_pulse=max_pulse,
    )


@lru_cache(maxsize=1)
def _fingerprint_action_map() -> Dict[SignalFingerprint, Set[Action]]:
    """Build a lookup table for the available payload fingerprints."""

    client = RaspyRFMClient()
    mapping: Dict[SignalFingerprint, Set[Action]] = {}

    for manufacturer in client.get_supported_controlunit_manufacturers():
        for model in client.get_supported_controlunit_models(manufacturer):
            device = client.get_controlunit(manufacturer, model)
            try:
                default_config = {
                    key: _default_value(regex)
                    for key, regex in device.get_channel_config_args().items()
                }
                device.set_channel_config(**default_config)
            except Exception as err:  # pragma: no cover - defensive fallback
                LOGGER.debug(
                    "Unable to build default configuration for %s %s: %s",
                    manufacturer,
                    model,
                    err,
                )
                continue

            for action in device.get_supported_actions():
                try:
                    pulses, repetitions, timebase = device.get_pulse_data(action)
                except Exception as err:  # pragma: no cover - defensive fallback
                    LOGGER.debug(
                        "Unable to build fingerprint for %s %s action %s: %s",
                        manufacturer,
                        model,
                        action,
                        err,
                    )
                    continue

                gap = 5600  # The RaspyRFM gateways always inject this constant gap.
                min_pulse, max_pulse = _pulse_bounds(pulses)
                fingerprint = SignalFingerprint(
                    repetitions=repetitions,
                    gap=gap,
                    timebase=timebase,
                    pulse_count=len(pulses),
                    min_pulse=min_pulse,
                    max_pulse=max_pulse,
                )
                mapping.setdefault(fingerprint, set()).add(action)

    return mapping


def _pulse_bounds(pulses: Iterable[Tuple[int, int]]) -> Tuple[int, int]:
    """Return the minimum and maximum pulse length from a sequence."""

    minima: List[int] = []
    maxima: List[int] = []
    for first, second in pulses:
        minima.append(min(first, second))
        maxima.append(max(first, second))
    return (min(minima), max(maxima))


def _default_value(regex: str) -> str:
    """Return a deterministic default value that satisfies a configuration regex."""

    pattern = regex.strip().lstrip("^").rstrip("$")
    if pattern == "[01]":
        return "0"
    if pattern == "[1-4]":
        return "1"
    if pattern == "[1-3]":
        return "1"
    if pattern == "[A-D]":
        return "A"
    if pattern == "[A-C]":
        return "A"
    if pattern == "[A-E]":
        return "A"
    if pattern == "[A-P]":
        return "A"
    if pattern == "[01fF]":
        return "0"
    if pattern == "[01]{12}":
        return "0" * 12
    if pattern == "[01]{26}":
        return "0" * 26
    if pattern == "[0-9A-F]{5}":
        return "00000"
    if pattern == "([1-9]|0[1-9]|1[0-6])":
        return "01"

    # Fall back to the first character when the pattern is a simple character set.
    if pattern.startswith("[") and pattern.endswith("]"):
        characters = pattern[1:-1]
        if characters and characters[0] != "^":
            return characters[0]

    # Final resort: return zeros with a sane length so ``set_channel_config`` succeeds.
    LOGGER.debug("Falling back to generic default for pattern %s", regex)
    return "0"
