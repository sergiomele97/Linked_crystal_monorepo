FROM ubuntu:24.04

# Avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Core and Devex dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    zip \
    unzip \
    curl \
    wget \
    sudo \
    openjdk-17-jdk \
    autoconf \
    automake \
    libltdl-dev \
    libtool \
    m4 \
    pkg-config \
    patch \
    libncurses5 \
    # Kivy dependencies
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev \
    # GStreamer (optional but in Makefile)
    libgstreamer1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    # Extra dependencies (Pillow, sounddevice, xvfb)
    libjpeg-dev \
    libfreetype6-dev \
    libportaudio2 \
    xvfb \
    libmtdev1t64 \
    libmtdev-dev \
    cmake \
    libssl-dev \
    libsqlite3-dev \
    libbz2-dev \
    libreadline-dev \
    libffi-dev \
    libncursesw5-dev \
    # Python utilities
    python3-is-python3 \
    ant \
    && rm -rf /var/lib/apt/lists/*

# Install Go 1.23 manually
RUN wget -q https://go.dev/dl/go1.23.0.linux-amd64.tar.gz \
    && rm -rf /usr/local/go && tar -C /usr/local -xzf go1.23.0.linux-amd64.tar.gz \
    && rm go1.23.0.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"

# Add a non-root user
ARG USERNAME=developer
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set environment variables for Android SDK/NDK (using home directory for permissions)
USER $USERNAME
WORKDIR /home/$USERNAME
ENV ANDROID_HOME="/home/developer/android-sdk"
ENV ANDROID_NDK_HOME="/home/developer/android-ndk-r25b"
ENV PATH="${PATH}:/home/developer/.local/bin:${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools:${ANDROID_HOME}/build-tools/31.0.0"

# Install Android SDK Command Line Tools
RUN mkdir -p ${ANDROID_HOME}/cmdline-tools \
    && wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O /tmp/cmdline-tools.zip \
    && unzip -q /tmp/cmdline-tools.zip -d ${ANDROID_HOME}/cmdline-tools \
    && mv ${ANDROID_HOME}/cmdline-tools/cmdline-tools ${ANDROID_HOME}/cmdline-tools/latest \
    && rm /tmp/cmdline-tools.zip

# Accept licenses and install platform 31 and build-tools 31.0.0
RUN yes | sdkmanager --sdk_root=${ANDROID_HOME} --licenses \
    && sdkmanager --sdk_root=${ANDROID_HOME} "platforms;android-31" "build-tools;31.0.0" "platform-tools"

# Install Android NDK r25b
RUN wget -q https://dl.google.com/android/repository/android-ndk-r25b-linux.zip -O /tmp/ndk.zip \
    && unzip -q /tmp/ndk.zip -d /home/developer \
    && rm /tmp/ndk.zip

# Pre-install key Python tools
RUN pip3 install --user --upgrade pip setuptools buildozer cython

# Ensure buildozer uses the pre-installed SDK/NDK/ANT
ENV APP_ANDROID_SDK_PATH=${ANDROID_HOME}
ENV APP_ANDROID_NDK_PATH=${ANDROID_NDK_HOME}
ENV APP_ANDROID_ANT_PATH="/usr/bin/ant"

# Create buildozer directory
RUN mkdir -p /home/developer/.buildozer
