from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
# PNADc and RAIS intentionally keep separate stage-zero modules. Remove a
# previously collected sibling module before importing this component's tests.
sys.modules.pop("stage0", None)
for path in (
    PACKAGE_ROOT / "code",
    PACKAGE_ROOT / "code" / "rais",
    PACKAGE_ROOT / "code" / "caged" / "models",
    PACKAGE_ROOT / "code" / "caged" / "panel",
    PACKAGE_ROOT / "code" / "common",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

package_path = PACKAGE_ROOT / "code" / "rais"
spec = importlib.util.spec_from_file_location(
    "v2_rais",
    package_path / "__init__.py",
    submodule_search_locations=[str(package_path)],
)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load the V2 RAIS test package")
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
