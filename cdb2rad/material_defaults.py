"""Default material parameters for automotive steels."""

from typing import Dict, Any

DEFAULT_STEEL_MATERIALS: Dict[str, Dict[str, float]] = {
    "LAW1": {
        "EX": 210000.0,
        "NUXY": 0.3,
        "DENS": 7800.0,
    },
    "LAW2": {
        "EX": 210000.0,
        "NUXY": 0.3,
        "DENS": 7800.0,
        "A": 220.0,
        "B": 450.0,
        "N": 0.36,
        "C": 0.01,
        "EPS0": 1.0,
    },
    "LAW27": {
        "EX": 210000.0,
        "NUXY": 0.3,
        "DENS": 7800.0,
        "SIG0": 250.0,
        "SU": 500.0,
        "EPSU": 0.2,
    },
    "LAW36": {
        "EX": 210000.0,
        "NUXY": 0.3,
        "DENS": 7800.0,
        "Fsmooth": 0.0,
        "Fcut": 0.0,
        "Chard": 1.0,
    },
    "LAW44": {
        "EX": 210000.0,
        "NUXY": 0.3,
        "DENS": 7800.0,
        "A": 6500.0,
        "B": 4.0,
        "N": 1.0,
        "C": 0.0,
    },
}


def apply_default_materials(materials: Dict[int, Dict[str, float]]) -> Dict[int, Dict[str, float]]:
    """Fill missing properties using :data:`DEFAULT_STEEL_MATERIALS`."""
    result: Dict[int, Dict[str, float]] = {}
    for mid, props in materials.items():
        law = props.get("LAW", "LAW1").upper()
        defaults = DEFAULT_STEEL_MATERIALS.get(law, DEFAULT_STEEL_MATERIALS["LAW1"])
        merged = {k: v for k, v in props.items() if v is not None}
        for key, val in defaults.items():
            if key in ("EX", "NUXY", "DENS") and key not in merged:
                # defer to global parameters if provided in writers
                continue
            merged.setdefault(key, val)
        merged["LAW"] = law
        result[mid] = merged
    return result
