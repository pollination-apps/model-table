

import streamlit as st
import tempfile

import web
import rhino
import revit

from pandas import DataFrame
from pathlib import Path
from typing import List

from pollination_streamlit_io import get_host
from honeybee.model import Model as HBModel
from honeybee.face import Face
from honeybee.room import Room


def get_wwr(faces: List[Face]) -> float:
    """Calculate WWR for a list of Honeybee faces.

    Args:
        faces: A list of Honeybee Face objects.

    Returns:
        WWR
    """
    face_area = 0
    aperture_area = 0
    for face in faces:
        face_area += face.area
        if face.apertures:
            for aperture in face.apertures:
                aperture_area += aperture.area
    if aperture_area == 0:
        return 0
    return (aperture_area * 100) / face_area


def add_wwr(room: Room, model_dict: dict) -> None:
    """Add WWR to the model_dict.

    Args:
        room: The Honeybee Room object for which the WWR will be calculated.
        model_dict: The dictionary in which the WWR will be added.
    """
    room_dict = {
        't': {'faces': [], 'key': 'roof-wwr'},
        'e': {'faces': [], 'key': 'east-wwr'},
        'w': {'faces': [], 'key': 'west-wwr'},
        'n': {'faces': [], 'key': 'north-wwr'},
        's': {'faces': [], 'key': 'south-wwr'},
        'ne': {'faces': [], 'key': 'north-east-wwr'},
        'se': {'faces': [], 'key': 'south-east-wwr'},
        'sw': {'faces': [], 'key': 'south-west-wwr'},
        'nw': {'faces': [], 'key': 'north-west-wwr'},
    }

    for face in room.faces:
        if face.normal.z == 1:
            room_dict['t']['faces'].append(face)
        elif face.normal.x == 1:
            room_dict['e']['faces'].append(face)
        elif face.normal.x == -1:
            room_dict['w']['faces'].append(face)
        elif face.normal.y == 1:
            room_dict['n']['faces'].append(face)
        elif face.normal.y == -1:
            room_dict['s']['faces'].append(face)
        elif 0 < face.normal.x < 1 and 0 < face.normal.y < 1:
            room_dict['ne']['faces'].append(face)
        elif 0 < face.normal.x < 1 and face.normal.y < 0:
            room_dict['se']['faces'].append(face)
        elif face.normal.x < 0 and face.normal.y < 0:
            room_dict['sw']['faces'].append(face)
        elif face.normal.x < 0 and 0 < face.normal.y < 1:
            room_dict['nw']['faces'].append(face)

    for key, val in room_dict.items():
        if val['faces']:
            wwr = get_wwr(val['faces'])
            print(wwr)
            if wwr > 0:
                model_dict[val['key']].append(wwr)
            else:
                model_dict[val['key']].append(0)
        else:
            model_dict[val['key']].append(0)


def get_dataframe(hbjson_path: Path) -> DataFrame:
    """Extract model data as a Pandas Dataframe.

    This function generates a Pandas Dataframe from a selected number of properties
    of the rooms in the model.

    Args:
        hbjson_path: Path to the HBJSON file.

    Returns:
        A Pandas Dataframe.
    """
    model = HBModel.from_hbjson(hbjson_path)

    model_dict = {
        'display_name': [],
        'volume (m3)': [],
        'floor_area (m2)': [],
        'exterior-wall-area (m2)': [],
        'exterior-aperture-area (m2)': [],
        'exterior-skylight-aperture-area (m2)': [],
        'roof-wwr': [],
        'north-wwr': [],
        'east-wwr': [],
        'south-wwr': [],
        'west-wwr': [],
        'north-east-wwr': [],
        'south-east-wwr': [],
        'south-west-wwr': [],
        'north-west-wwr': [],
    }

    for room in model.rooms:
        model_dict['display_name'].append(room.display_name)
        model_dict['volume (m3)'].append(room.volume)
        model_dict['floor_area (m2)'].append(room.floor_area)
        model_dict['exterior-wall-area (m2)'].append(room.exterior_wall_area)
        model_dict['exterior-aperture-area (m2)'].append(room.exterior_aperture_area)
        model_dict['exterior-skylight-aperture-area (m2)'].append(
            room.exterior_skylight_aperture_area)
        add_wwr(room, model_dict)

    return DataFrame.from_dict(model_dict)


def main():

    st.title('Export Table')
    st.markdown('An app to extract zone data from a honeybee-model in the CSV format.')

    # Get host
    host = get_host()
    if not host:
        host = 'web'

    # Folder to write data
    if 'temp_folder' not in st.session_state:
        st.session_state.temp_folder = Path(tempfile.mkdtemp())

    # web
    if host.lower() == 'web':

        hbjson_file = st.file_uploader(
            'Upload an HBJSON file.', type='hbjson', key='upload_hbjson')

        if hbjson_file:
            hbjson_path = st.session_state.temp_folder.joinpath(hbjson_file.name)
            hbjson_path.write_bytes(hbjson_file.read())
            web.show_model(hbjson_path)
            st.session_state.hbjson_path = hbjson_path

    # rhino
    elif host.lower() == 'rhino':
        hbjson_path = rhino.get_model(st.session_state.temp_folder)
        st.session_state.hbjson_path = hbjson_path

    # revit
    elif host.lower() == 'revit':
        hbjson_path = revit.get_model(st.session_state.temp_folder)
        st.session_state.hbjson_path = hbjson_path

    # table
    if 'hbjson_path' in st.session_state and st.session_state.hbjson_path:
        df = get_dataframe(st.session_state.hbjson_path)

        st.write('Review the data.')
        st.dataframe(df)

        if len(df.columns) > 0:
            csv = df.to_csv(index=False, float_format='%.2f')
            st.markdown('Download data as CSV')
            st.download_button('Download', csv, "file.csv",
                               "text/csv", key="download-csv")


if __name__ == '__main__':
    main()
