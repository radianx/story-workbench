FROM rust:1-bookworm@sha256:9a73a5088750b4c95158ab26629c854c3d6fc4b173cb7bc8079ad252d8ed7bfa
RUN apt-get update && apt-get install -y --no-install-recommends libwebkit2gtk-4.1-dev libssl-dev librsvg2-dev libxdo-dev xvfb dbus-x11 nsis llvm lld clang nodejs npm && rm -rf /var/lib/apt/lists/*
RUN rustup target add x86_64-pc-windows-msvc && cargo install --locked cargo-xwin --version 0.23.1
RUN npm install --global @tauri-apps/cli@2.11.4
WORKDIR /workspace
