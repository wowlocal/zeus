"""The engine tests share the dry-run tests' fixtures: a temp ``ZEUS_HOME`` and the standard-root pin."""

from tests.zeus_cli.test_gateway_migrate_backends_apply import (  # the fixtures, imported for pytest
    _standard_root,
    home,
)
