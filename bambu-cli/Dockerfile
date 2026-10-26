FROM --platform=linux/amd64 ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN sed -i "s|http://archive.ubuntu.com|http://mirror.kakao.com|g; s|http://security.ubuntu.com|http://mirror.kakao.com|g" /etc/apt/sources.list.d/ubuntu.sources
RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends xvfb xauth libgl1 libegl1 libgtk-3-0t64 libwebkit2gtk-4.1-0 libgstreamer1.0-0 libgstreamer-plugins-base1.0-0 libosmesa6 libglu1-mesa locales ca-certificates squashfs-tools python3 && rm -rf /var/lib/apt/lists/*
COPY bs.AppImage /opt/bs.AppImage
# binfmt can't exec an AppImage under emulation (its magic sits in the ELF header), so unpack the squashfs directly
RUN cd /opt && off=$(python3 -c "import struct;d=open('bs.AppImage','rb').read(64);sh,=struct.unpack_from('<Q',d,0x28);es,n=struct.unpack_from('<HH',d,0x3A);print(sh+es*n)") \
    && unsquashfs -q -o $off -d squashfs-root bs.AppImage && rm bs.AppImage
ENTRYPOINT ["xvfb-run", "-a", "/opt/squashfs-root/AppRun"]
