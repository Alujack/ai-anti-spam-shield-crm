FROM kong/kong:3.9

# Copy declarative config
COPY --chown=kong:kong kong.yml /etc/kong/kong.yml

USER kong
