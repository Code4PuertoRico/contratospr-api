FROM python:3.7

ENV LANG en_US.utf8

RUN pip install pipenv==2018.5.18

WORKDIR /app/

COPY Pipfile Pipfile.lock /app/

# Install application requirements
RUN pipenv install --deploy --system && \
    rm -rf /root/.cache

# Bundle app source
COPY . /app/
