

import streamlit as st
import tempfile

import json

import web

from pandas import DataFrame
from pathlib import Path
from typing import List
from math import degrees

from pollination_streamlit_io import (get_host, get_hbjson)
from honeybee.model import Model as HBModel
from honeybee.face import Face
from honeybee.room import Room
from ladybug_geometry.geometry2d.pointvector import Vector2D


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
        elif face.normal.z == -1:
            continue
        else:
            ref_vec = Vector2D(0, 1)
            vec = Vector2D(face.normal.x, face.normal.y)
            angle = degrees(ref_vec.angle_clockwise(vec))

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

    for key, val in room_dict.items():
        if val['faces']:
            wwr = get_wwr(val['faces'])
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

    data = get_hbjson('get-hbjson')
    if data:
        model_data = data['hbjson']
        
        hb_model = HBModel.from_dict(model_data)
        if hb_model:
            hbjson_path = st.session_state.temp_folder.joinpath(f'{hb_model.identifier}.hbjson')
            hbjson_path.write_text(json.dumps(hb_model.to_dict()))
            st.session_state.hbjson_path = hbjson_path
            if host == 'web' :
                web.show_model(hbjson_path)
      
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
