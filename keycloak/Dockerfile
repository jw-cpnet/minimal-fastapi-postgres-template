ARG KC_VERSION=latest
# Stage 1: Install packages using a UBI base image
FROM registry.access.redhat.com/ubi9 AS ubi-micro-build

# Create a chroot environment for installation
RUN mkdir -p /mnt/rootfs

# Install openssl (replace with your desired packages)
RUN dnf install --installroot /mnt/rootfs \
                openssl \
                --releasever 9 \
                --setopt install_weak_deps=false \
                --nodocs -y \
   && dnf --installroot /mnt/rootfs clean all \
   && rpm --root /mnt/rootfs -e --nodeps setup

# Stage 2: Use the Keycloak base image
ARG KC_VERSION
FROM quay.io/keycloak/keycloak:${KC_VERSION}

# Copy the installed packages from the previous stage
COPY --from=ubi-micro-build /mnt/rootfs /

# Switch to root user (to ensure correct permissions for the next step)
USER root

# Make any necessary configuration changes in the Keycloak environment
# For example, if you installed a new theme or provider, you might need to add configuration here

# Switch back to the default Keycloak user
USER 1000
