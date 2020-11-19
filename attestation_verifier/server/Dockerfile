FROM amazonlinux

# Install python for running the server and net-tools for modifying network config
RUN yum install python3 net-tools -y

WORKDIR /app

COPY requirements.txt ./
RUN pip3 install -r /app/requirements.txt

COPY server.py ./
COPY NsmUtil.py ./
COPY run.sh ./
COPY libnsm.so ./

RUN chmod +x run.sh

CMD ["/app/run.sh"]
