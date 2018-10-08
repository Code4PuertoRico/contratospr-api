FROM python:3.7

ENV LANG en_US.utf8

RUN pip install pipenv

WORKDIR /app/

COPY Pipfile Pipfile.lock /app/

# Install application requirements
RUN pip install pipenv && \
    pipenv install --deploy --system && \
    pip uninstall -y pipenv && \
    rm -rf /root/.cache

# Bundle app source
COPY . /app/
