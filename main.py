from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_entrypoint_path = Path(__file__).parent / "app" / "main.py" / "main.py"
_spec = spec_from_file_location("hospital_app_main", _entrypoint_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load ASGI entrypoint: {_entrypoint_path}")

_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)
app = _module.app
