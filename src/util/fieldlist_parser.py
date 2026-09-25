import json
import os
import re

def get_fieldlist_alt_names(fieldlist_path: str, pod_var_name: str, canonical_target_name: str) -> list[str]:
    """Directly open and parse an MDTF fieldlist file (.json / .jsonc) from disk to harvest
    configured model variable aliases (`alt_names`), targeting MDTF's 'variables' block.

    Parameters
    ----------
    fieldlist_path : str
        Absolute path to fieldlist_CMIP.jsonc.
    pod_var_name : str
        Requested POD variable key (e.g., 'u200').
    canonical_target_name : str
        Translated CMIP target variable key (e.g., 'ua').

    Returns
    -------
    list of str
        Deduplicated list of alternative variable names (e.g., ['ucomp', 'ua_unmsk']).
    """
    alts = []
    if not fieldlist_path or not os.path.exists(fieldlist_path):
        return alts

    try:
        with open(fieldlist_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Strip multi-line /* ... */ and single-line // comments (JSONC support)
        content_no_comments = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content_no_comments = re.sub(r'//.*', '', content_no_comments)

        data = json.loads(content_no_comments)

        # 1. Target MDTF standard "variables" block first
        var_dict = data.get("variables", data) if isinstance(data, dict) else {}

        def extract_from_container(container):
            if not isinstance(container, dict):
                return
            for key in (pod_var_name, canonical_target_name):
                if key in container and isinstance(container[key], dict):
                    raw_alts = container[key].get('alt_names', [])
                    if isinstance(raw_alts, str):
                        alts.append(raw_alts)
                    elif isinstance(raw_alts, (list, tuple, set)):
                        alts.extend(raw_alts)

        # Search inside "variables"
        extract_from_container(var_dict)

        # 2. Fallback: Search root dictionary if not found inside "variables"
        if not alts and isinstance(data, dict):
            extract_from_container(data)

    except Exception as exc:
        print(f"DEBUG fieldlist_parser: Exception reading fieldlist '{fieldlist_path}': {exc}")

    return list(dict.fromkeys(alts))