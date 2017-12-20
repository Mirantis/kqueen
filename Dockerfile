FROM python:3.6

# prepare directory
WORKDIR /code

# copy app
COPY . .

# install from local file
RUN pip install .

# run app
CMD ./entrypoint.sh
