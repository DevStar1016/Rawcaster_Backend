FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# WORKDIR /app/
WORKDIR /app/app/

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock*  # in case it doesn't exist in the repo
# Copy poetry.lock*  

COPY ./app/pyproject.toml ./app/poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"

# For development, Jupyter remote kernel, Hydrogen
# Using inside the container:
# jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.custom_display_url=http://127.0.0.1:8888
ARG INSTALL_JUPYTER=false
RUN bash -c "if [ $INSTALL_JUPYTER == 'true' ] ; then pip install jupyterlab ; fi"

RUN bash -c "pip3 install python-jose[cryptography]"

RUN bash -c "pip3 install pymysql"
RUN bash -c "pip3 install fastapi"
RUN bash -c "pip3 install fastapi-pagination==0.8.3"
RUN bash -c "pip3 install fastapi-mail"
RUN bash -c "pip3 install pyfcm"
RUN bash -c "pip3 install twilio"
RUN bash -c "pip3 install crc16"
RUN bash -c "pip3 install moviepy"
RUN bash -c "pip3 install boto3"
RUN bash -c "pip3 install pytz"
RUN bash -c "pip3 install pybase64"
RUN bash -c "pip3 install regex"
RUN bash -c "pip3 install --force-reinstall httpcore==0.15"
RUN bash -c "pip3 uninstall sqlalchemy"
RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt .
RUN pip3 install -r requirements.txt
# COPY ./app /app
COPY ./app /app
ENV PYTHONPATH=/app