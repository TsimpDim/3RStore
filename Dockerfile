FROM ubuntu:20.04

RUN apt-get update -y && \
    apt-get install -y python3-pip python-dev libpq-dev

# We copy just the requirements.txt first to leverage Docker cache
WORKDIR /3RStore
COPY ./requirements.txt /3RStore/requirements.txt
RUN pip3 install -r requirements.txt

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]