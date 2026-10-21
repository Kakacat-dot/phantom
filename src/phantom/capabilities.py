"""Phantom Capability Model.

Defines fine-grained capabilities required for runtime operations,
such as stdio, event dispatch, diagnostics, counters, and metadata.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum

from phantom.ir import InstructionType


class Capability(Enum):
    """Runtime capabilities required by instructions and runtime operations."""

    STDIO = "cap.stdio"  # Read/write to stdout/stderr
    EVENTS = "cap.events"  # Event declaration and dispatch
    DIAGNOSTICS = "cap.diagnostics"  # Diagnostic collection
    COUNTERS = "cap.counters"  # Counter operations
    METADATA = "cap.metadata"  # Metadata declarations


DEFAULT_CAPABILITIES = frozenset(
    {
        Capability.STDIO,
        Capability.EVENTS,
        Capability.DIAGNOSTICS,
        Capability.COUNTERS,
        Capability.METADATA,
    }
)


# Map instruction types to required capabilities
INSTRUCTION_CAPABILITIES: dict[InstructionType, frozenset[Capability]] = {
    InstructionType.EVENT_DECLARE: frozenset({Capability.EVENTS}),
    InstructionType.EVENT_ON: frozenset({Capability.EVENTS}),
    InstructionType.DIAGNOSTIC_NOTE: frozenset({Capability.DIAGNOSTICS}),
    InstructionType.COUNTER_CREATE: frozenset({Capability.COUNTERS}),
    InstructionType.COUNTER_INCREMENT: frozenset({Capability.COUNTERS}),
    InstructionType.META_AUTHOR: frozenset({Capability.METADATA}),
    InstructionType.META_VERSION: frozenset({Capability.METADATA}),
    InstructionType.META_LICENSE: frozenset({Capability.METADATA}),
}


def get_required_capabilities(instruction_type: InstructionType) -> frozenset[Capability]:
    """Return the set of capabilities required for an instruction type."""
    return INSTRUCTION_CAPABILITIES.get(instruction_type, frozenset())


class PhantomError(Exception):
    """Base exception for all Phantom language runtime and capability errors."""


class CapabilityError(PhantomError):
    """Raised when an operation is attempted without the required capability."""

    def __init__(
        self,
        capability_or_message: Capability | str,
        capability: Capability | None = None,
    ) -> None:
        if isinstance(capability_or_message, Capability):
            self.capability: Capability | None = capability_or_message
            msg = f"Capability '{capability_or_message.value}' is required but not granted."
        else:
            self.capability = capability
            msg = str(capability_or_message)
        super().__init__(msg)


class CapabilityGrant:
    """Represents a set of capabilities granted to a Phantom runtime execution context."""

    def __init__(self, granted: Iterable[Capability] | None = None) -> None:
        if granted is None:
            self.granted: frozenset[Capability] = DEFAULT_CAPABILITIES
        else:
            self.granted = frozenset(granted)

    def check(self, capability: Capability) -> bool:
        """Check whether a specific capability is granted."""
        return capability in self.granted

    def require(self, capability: Capability) -> None:
        """Assert that a capability is granted, raising CapabilityError if not."""
        if not self.check(capability):
            raise CapabilityError(
                capability,
                f"Missing required capability: {capability.value}",
            )

    def check_instruction(self, instruction_type: InstructionType) -> bool:
        """Check whether all capabilities required for an instruction type are granted."""
        required = get_required_capabilities(instruction_type)
        return required.issubset(self.granted)

    def require_instruction(self, instruction_type: InstructionType) -> None:
        """Assert that all capabilities for an instruction type are granted."""
        required = get_required_capabilities(instruction_type)
        missing = required - self.granted
        if missing:
            missing_str = ", ".join(sorted(c.value for c in missing))
            raise CapabilityError(
                next(iter(missing)),
                f"Instruction '{instruction_type.value}' requires capabilities [{missing_str}], which are not granted.",
            )

    def __contains__(self, item: Capability) -> bool:
        return item in self.granted

    def __repr__(self) -> str:
        caps = ", ".join(sorted(c.name for c in self.granted))
        return f"CapabilityGrant({caps})"
