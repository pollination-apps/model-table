while getopts o:s:t: flag
do
    case "${flag}" in
        o) owner=${OPTARG};;
        s) slug=${OPTARG};;
        t) tag=${OPTARG};;
    esac
done

echo "Owner: $owner"
echo "Slug: $slug"
echo "Tag: $tag"

pwd=$(pwd)

echo "Path $pwd"

echo "docker run -t -i --expose 8501 -p 8501:8501 -v $pwd:/app $owner/$slug:$tag streamlit run app.py"

docker build -f $pwd/Dockerfile -t $owner/$slug:$tag $pwd
docker run -t -i --expose 8501 -p 8501:8501 -v $pwd/:/app $owner/$slug:$tag streamlit run app.py