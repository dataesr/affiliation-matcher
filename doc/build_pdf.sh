docker run --rm -v "$(pwd):/data" -u "$(id -u)" pandocscholar/alpine
cp out.pdf matcher.pdf
cp out.latex matcher.tex
