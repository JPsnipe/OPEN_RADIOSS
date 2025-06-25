"""Default material and failure parameters for automotive steels."""

from typing import Dict

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

# Typical parameters for common failure models used in automotive steels
# Values are taken from published impact test data (e.g. DP600 sheet)
DEFAULT_FAILURE_MODELS: Dict[str, Dict[str, float]] = {
    "FAIL/JOHNSON": {
        "D1": 0.54,
        "D2": 3.03,
        "D3": -2.12,
        "D4": 0.002,
        "D5": 0.61,
    },
    "FAIL/BIQUAD": {
        "C1": 0.9,
        "C2": 2.0,
        "C3": 2.0,
    },
    "FAIL/TAB1": {
        "Dcrit": 1.0,
    },
}


def apply_default_materials(materials: Dict[int, Dict[str, float]]) -> Dict[int, Dict[str, float]]:
    """Fill missing properties using :data:`DEFAULT_STEEL_MATERIALS`.

    Failure model parameters are also completed when ``FAIL`` blocks are
    provided. Only keys not already present will be inserted.
    """
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
        if "FAIL" in merged:
            fail = merged["FAIL"]
            if isinstance(fail, dict):
                ftype = fail.get("TYPE", "FAIL/JOHNSON").upper()
                fdef = DEFAULT_FAILURE_MODELS.get(ftype)
                if fdef:
                    for key, val in fdef.items():
                        fail.setdefault(key, val)
                fail["TYPE"] = ftype
                merged["FAIL"] = fail
        merged["LAW"] = law
        result[mid] = merged
    return result
