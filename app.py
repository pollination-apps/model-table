

import streamlit as st
import tempfile

import json
import math

import web

from pandas import DataFrame
from pathlib import Path
from typing import List

from pollination_streamlit_io import get_host, get_hbjson
from honeybee.model import Model as HBModel
from honeybee.face import Face, Outdoors
from honeybee.room import Room
from honeybee.units import UNITS_ABBREVIATIONS, UNITS
from ladybug_geometry.geometry2d.pointvector import Vector2D


def get_wwr(faces: List[Face]) -> float:
    """Calculate WWR for a list of Honeybee faces.

    Args:
        faces: A list of Honeybee Face objects.

    Returns:
        WWR
    """
    return sum(f.aperture_ratio for f in faces)


def add_wwr(room: Room, model_dict: dict, north_vector: Vector2D) -> None:
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
        face: Face
        if not isinstance(face.boundary_condition, Outdoors):
            continue
        if face.normal.z == 1:
            room_dict['t']['faces'].append(face)
        elif face.normal.z == -1:
            continue
        else:
            angle = face.horizontal_orientation(north_vector=north_vector)
            if angle <= 22.5 or angle >= 337.5:
                room_dict['n']['faces'].append(face)

            elif 22.5 < angle <= 67.5:
                room_dict['ne']['faces'].append(face)

            elif 67.5 < angle <= 112.5:
                room_dict['e']['faces'].append(face)

            elif 112.5 < angle <= 157.5:
                room_dict['se']['faces'].append(face)

            elif 157.5 < angle <= 202.5:
                room_dict['s']['faces'].append(face)

            elif 202.5 < angle <= 247.5:
                room_dict['sw']['faces'].append(face)

            elif 247.5 < angle <= 292.5:
                room_dict['w']['faces'].append(face)

            elif 292.5 < angle < 337.5:
                room_dict['nw']['faces'].append(face)

    for val in room_dict.values():
        if val['faces']:
            wwr = get_wwr(val['faces'])
            if wwr > 0:
                model_dict[val['key']].append(wwr)
            else:
                model_dict[val['key']].append(0)
        else:
            model_dict[val['key']].append(0)


def get_dataframe(model: HBModel, north_vector: Vector2D) -> DataFrame:
    """Extract model data as a Pandas Dataframe.

    This function generates a Pandas Dataframe from a selected number of
    properties of the rooms in the model.

    Args:
        model: A valid Honeybee model

    Returns:
        A Pandas Dataframe.
    """
    units = model.units
    units_short = UNITS_ABBREVIATIONS[model.UNITS.index(units)]

    model_dict = {
        'display_name': [],
        f'volume ({units_short}3)': [],
        f'floor_area ({units_short}2)': [],
        f'exterior-wall-area ({units_short}2)': [],
        f'exterior-aperture-area ({units_short}2)': [],
        f'exterior-skylight-aperture-area ({units_short}2)': [],
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
        model_dict[f'volume ({units_short}3)'].append(room.volume)
        model_dict[f'floor_area ({units_short}2)'].append(room.floor_area)
        model_dict[f'exterior-wall-area ({units_short}2)'].append(room.exterior_wall_area)
        model_dict[f'exterior-aperture-area ({units_short}2)'].append(room.exterior_aperture_area)
        model_dict[f'exterior-skylight-aperture-area ({units_short}2)'].append(
            room.exterior_skylight_aperture_area)
        add_wwr(room, model_dict, north_vector)

    return DataFrame.from_dict(model_dict)


def main():

    st.title('Facade Area Takeoff')
    st.info(
        'This app calculates the window-to-wall ratio for the exterior facade of '
        'the input model and provides a breakdown per orientation. You must ensure '
        'that the adjacency between the rooms is solved correctly. Otherwise, the '
        'values also includes the interior windows.'
    )

    # Get host
    host = get_host() or 'web'

    # Folder to write data
    if 'temp_folder' not in st.session_state:
        st.session_state.temp_folder = Path(tempfile.mkdtemp())

    st.markdown('## 1. Upload your model')
    data = get_hbjson('get-hbjson')
    hb_model: HBModel = None
    if data:
        model_data = data['hbjson']

        hb_model: HBModel = HBModel.from_dict(model_data)
        if hb_model:
            hbjson_path = st.session_state.temp_folder.joinpath(f'{hb_model.identifier}.hbjson')
            hbjson_path.write_text(json.dumps(hb_model.to_dict()))
            st.session_state.hbjson_path = hbjson_path
            if host == 'web':
                web.show_model(hbjson_path)

    # table
    if hb_model:

        st.markdown('## 2. Review the data')
        c1, c2 = st.columns(2)
        units = c1.selectbox('Select report units', options=UNITS)
        north_angle = c2.number_input(
            'North Rotation', min_value=-360.0, max_value=360.0, value=0.0, step= 0.5,
            help='The counterclockwise difference between true North and the Y-axis in '
            'degrees: 90: West, -90: East.'
        )
        north_vector = Vector2D(0, 1)
        if north_angle != 0:
            north_vector = north_vector.rotate(math.radians(north_angle))
        hb_model.convert_to_units(units)
        df = get_dataframe(hb_model, north_vector)
        st.dataframe(df)

        if len(df.columns) > 0:
            csv = df.to_csv(index=False, float_format='%.2f')
            try:
                st.download_button(
                    'Download data as a CSV file', csv, 'file.csv', 'text/csv',
                    key='download-csv', type='primary')
            except TypeError:
                # backwards compatibility
                st.download_button(
                    'Download data as a CSV file', csv, 'file.csv', 'text/csv',
                    key='download-csv')


if __name__ == '__main__':
    main()
