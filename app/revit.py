"""Get HBJSON from Revit."""


import json
from pathlib import Path
from honeybee.model import Model
from pollination_streamlit_io import get_hbjson


def get_model(target_folder: Path) -> Path:

    data = get_hbjson('revit-hbjson')

    if data:
        model_data = data['hbjson']
        hb_model = Model.from_dict(model_data)
        hbjson_path = target_folder.joinpath(f'{hb_model.identifier}.hbjson')
        hbjson_path.write_text(json.dumps(hb_model.to_dict()))

        return hbjson_path
