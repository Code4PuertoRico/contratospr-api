FROM python:3.7 as builder

ENV POPPLER_VERION 0.74.0

# Install pdftotext
RUN apt-get update && \
  apt-get install -y cmake && \
  cd /tmp && \
  curl -L "https://poppler.freedesktop.org/poppler-${POPPLER_VERION}.tar.xz" | tar xJ && \
  cd "poppler-${POPPLER_VERION}" && \
	mkdir build && \
	cd build && \
	cmake .. \
		-DCMAKE_INSTALL_PREFIX=/tmp/poppler \
		-DCMAKE_BUILD_TYPE=release \
		-DBUILD_SHARED_LIBS=OFF \
		-DENABLE_LIBOPENJPEG=none && \
	make && \
	make install && \
  rm -rf /var/lib/apt/lists/*

FROM python:3.7

ENV LANG en_US.utf8

RUN pip install pipenv==2018.11.26

WORKDIR /app/

COPY --from=builder /tmp/poppler/bin/pdftotext /usr/local/bin/
COPY Pipfile Pipfile.lock /app/

# Install application requirements
RUN pipenv install --deploy --system && \
    rm -rf /root/.cache

# Bundle app source
COPY . /app/

RUN adduser --disabled-login app
USER app
