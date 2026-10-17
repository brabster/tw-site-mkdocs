FROM alpine

COPY sh-script.sh .

RUN ./sh-script.sh
