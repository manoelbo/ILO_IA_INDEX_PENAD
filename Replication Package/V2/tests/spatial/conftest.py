from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
for path in (
    PACKAGE_ROOT / "code",
    PACKAGE_ROOT / "code" / "spatial",
    PACKAGE_ROOT / "code" / "caged" / "models",
    PACKAGE_ROOT / "code" / "caged" / "panel",
    PACKAGE_ROOT / "code" / "common",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

package_path = PACKAGE_ROOT / "code" / "spatial"
spec = importlib.util.spec_from_file_location(
    "v2_spatial",
    package_path / "__init__.py",
    submodule_search_locations=[str(package_path)],
)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load the V2 spatial test package")
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
