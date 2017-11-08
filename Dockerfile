FROM python:3.6-slim

# prepare directory
WORKDIR /code

# copy app
COPY . .

# install from local file
# TODO: use pypi instead
RUN python setup.py install

# run app
CMD ./entrypoint.sh
