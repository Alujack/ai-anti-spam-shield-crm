FROM kong:3.4-alpine

# Copy declarative config
COPY kong.yml /etc/kong/kong.yml

# Validate config on build
RUN kong config parse /etc/kong/kong.yml

USER kong
