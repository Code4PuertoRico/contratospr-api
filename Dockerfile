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

ARG PIPENV_ARGS

ENV LANG en_US.utf8
ENV PYTHONUNBUFFERED 1

# Install tesseract
RUN apt-get update && apt-get install -y \
		tesseract-ocr \
		tesseract-ocr-eng \
		tesseract-ocr-spa && \
	rm -rf /var/lib/apt/lists/*

# Add app user
RUN adduser --disabled-login app

RUN pip install pipenv==2018.11.26

WORKDIR /app/

COPY --from=builder /tmp/poppler/bin/pdftotext /usr/local/bin/
COPY --from=builder /tmp/poppler/bin/pdftoppm /usr/local/bin/
COPY --from=builder /tmp/poppler/bin/pdfinfo /usr/local/bin/
COPY Pipfile Pipfile.lock /app/

# Install application requirements
RUN pipenv install --deploy --system $PIPENV_ARGS && \
    rm -rf /root/.cache

RUN python -m spacy download es_core_news_sm && \
		python -m spacy download es_core_news_md && \
		python -m spacy download xx_ent_wiki_sm

# Bundle app source
COPY . /app/

USER app
