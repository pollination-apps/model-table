
from requests import session
import streamlit as st
import tempfile

from pandas import DataFrame
from pathlib import Path

from pollination_streamlit_io import get_host
from honeybee.model import Model as HBModel
import web
import rhino
import revit


def get_dataframe(hbjson_path) -> DataFrame:
    model = HBModel.from_hbjson(hbjson_path)

    dict = {'identifier': [], 'display_name': [], 'floor_area (m2)': []}
    for room in model.rooms:
        print("**********")
        print(room.display_name)
        faces = room.faces
        for face in faces:
            if face.apertures:
                for aperture in face.apertures:
                    print(aperture.normal)
        print("\n")
        dict['identifier'].append(room.identifier)
        dict['display_name'].append(room.display_name)
        dict['floor_area (m2)'].append(room.floor_area)

    return DataFrame.from_dict(dict)


def main():
    st.title('Export Table')

    host = get_host()
    if not host:
        host = 'web'

    if 'temp_folder' not in st.session_state:
        st.session_state.temp_folder = Path(tempfile.mkdtemp())

    if host.lower() == 'web':

        hbjson_file = st.file_uploader(
            'Upload an HBJSON file.', type='hbjson', key='upload_hbjson')

        if hbjson_file:
            hbjson_path = st.session_state.temp_folder.joinpath(hbjson_file.name)
            hbjson_path.write_bytes(hbjson_file.read())
            web.show_model(hbjson_path)
            st.session_state.hbjson_path = hbjson_path

    elif host.lower() == 'rhino':
        hbjson_path = rhino.get_model(st.session_state.temp_folder)
        st.session_state.hbjson_path = hbjson_path

    elif host.lower() == 'revit':
        hbjson_path = revit.get_model(st.session_state.temp_folder)
        st.session_state.hbjson_path = hbjson_path

    if 'hbjson_path' in st.session_state and st.session_state.hbjson_path:
        if 'df' not in st.session_state:
            st.session_state.df = get_dataframe(st.session_state.hbjson_path)

        df = st.session_state.df
        st.dataframe(df)

        if len(df.columns) > 0:
            csv = df.to_csv(index=False)
            st.download_button('Download CSV', csv, "file.csv",
                               "text/csv", key="download-csv")


if __name__ == '__main__':
    main()
