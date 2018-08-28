FROM python:3.6
LABEL maintainer="tkukral@mirantis.com"

# prepare directory
WORKDIR /code

# install dependencies
RUN apt-get update && \
  apt-get install --no-install-recommends -y libsasl2-dev python-dev libldap2-dev libssl-dev && \
  rm -rf /var/lib/apt/lists/* && \
  mkdir /var/log/kqueen-api && \
  mkdir /opt/kqueen
# install kubespray
RUN git clone -b v2.5.0 https://github.com/kubernetes-incubator/kubespray.git && \
  pip install -r kubespray/requirements.txt

# copy app
COPY . kqueen
RUN pip install ./kqueen

ENV KQUEEN_KS_KUBESPRAY_PATH /code/kubespray
ENV KQUEEN_KS_ANSIBLE_CMD /usr/local/bin/ansible
ENV KQUEEN_KS_ANSIBLE_PLAYBOOK_CMD /usr/local/bin/ansible-playbook

# run app
WORKDIR /code/kqueen
CMD ./entrypoint.sh
