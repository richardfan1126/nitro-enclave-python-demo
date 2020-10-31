FROM amazonlinux

RUN yum install python3 -y

WORKDIR /app

COPY server.py ./

CMD ["python3", "/app/server.py"]