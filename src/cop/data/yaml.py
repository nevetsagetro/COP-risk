"""Dataset-neutral strict YAML loading primitives."""

from __future__ import annotations

from typing import Any

import yaml


class StrictYamlError(ValueError):
    """Raised when generic strict-YAML invariants are violated."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate string mapping keys."""


def _construct_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)  # type: ignore[no-untyped-call]
        if not isinstance(key, str):
            raise StrictYamlError("configuration keys must be strings")
        if key in mapping:
            raise StrictYamlError(f"duplicate configuration key: {key}")
        mapping[key] = loader.construct_object(  # type: ignore[no-untyped-call]
            value_node, deep=deep
        )
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)
