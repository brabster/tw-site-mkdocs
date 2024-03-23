FROM alpine

COPY bash-script.sh .

RUN ./bash-script.sh
