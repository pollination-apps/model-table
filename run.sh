echo pwd
docker build -f /Users/nicolasschmidt/Documents/Pollination/model-table/Dockerfile -t nicolas/model-table:latest /Users/nicolasschmidt/Documents/Pollination/model-table/
docker run -t -i --expose 8501 -p 8501:8501 -v /Users/nicolasschmidt/Documents/Pollination/model-table/:/app nicolas/model-table:latest streamlit run app.py