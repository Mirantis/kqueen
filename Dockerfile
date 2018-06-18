FROM python:3.6
LABEL maintainer="tkukral@mirantis.com"

# prepare directory
WORKDIR /code

# install dependencies
RUN apt-get update && \
  apt-get install --no-install-recommends -y libsasl2-dev python-dev libldap2-dev libssl-dev && \
  rm -rf /var/lib/apt/lists/* && \
  mkdir /var/log/kqueen-api

# install aws dependencies
RUN curl -o heptio-authenticator-aws https://amazon-eks.s3-us-west-2.amazonaws.com/1.10.3/2018-06-05/bin/linux/amd64/heptio-authenticator-aws && \
  chmod +x ./heptio-authenticator-aws && \
  mkdir -p $HOME/bin && \
  cp ./heptio-authenticator-aws $HOME/bin/heptio-authenticator-aws && export PATH=$HOME/bin:$PATH && \
  echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc

# copy app
COPY . .
RUN pip install .

# run app
CMD ./entrypoint.sh
