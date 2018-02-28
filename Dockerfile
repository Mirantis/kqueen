FROM python:3.6
LABEL maintainer="tkukral@mirantis.com"

# prepare directory
WORKDIR /code

# install dependencies
RUN apt-get update && \
  apt-get install --no-install-recommends -y libsasl2-dev python-dev libldap2-dev libssl-dev && \
  rm -rf /var/lib/apt/lists/*

# copy app
COPY . .
RUN pip install .

# run app
CMD ./entrypoint.sh
