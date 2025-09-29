FROM python:3.10.3-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get -y update && apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python3-dev \
    python3-numpy \
    software-properties-common \
    zip \
    libx11-dev \
    libopenblas-dev \
    libboost-python-dev \
    libboost-all-dev \
    libpng-dev \
    libtiff-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libfontconfig1-dev \
    libcairo2-dev \
    libgdk-pixbuf-xlib-2.0-dev \
    libpango1.0-dev \
    && apt-get clean && rm -rf /tmp/* /var/tmp/*

RUN cmake --version

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir numpy==1.26.4

# Compiler dlib depuis les sources (version stable v19.9 comme dans l'officiel)
RUN cd ~ && \
    mkdir -p dlib && \
    git clone -b 'v19.9' --single-branch https://github.com/davisking/dlib.git dlib/ && \
    cd dlib/ && \
    python3 setup.py install --yes USE_AVX_INSTRUCTIONS

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

RUN python -c "import face_recognition; import cv2; import fastapi; print('Toutes les dépendances sont installées avec succès!')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]