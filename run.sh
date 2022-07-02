echo pwd
docker build -f {docker_file} -t {owner}/{slug}:{tag} /Users/nicolasschmidt/Documents/Pollination/model-table/
docker run -t -i --expose 8501 -p 8501:8501 -v {path}:/app {owner}/{slug}:{tag} streamlit run app.py