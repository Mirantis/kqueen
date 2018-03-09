FROM nginx
LABEL maintainer="tkukral@mirantis.com"

# environment
ENV DIR_CONF /etc/nginx/conf.d/
ENV DIR_APP /var/www/app/
ARG DEBUG
ENV DEBUG ${DEBUG:-False}
ARG VHOSTNAME
ENV VHOSTNAME ${VHOSTNAME:-demo.kqueen.net}
ARG SSL_CERTIFICATE_DIR
ENV SSL_CERTIFICATE_DIR ${SSL_CERTIFICATE_DIR:-/mnt/letsencrypt/$VHOSTNAME}
ARG SSL_CERTIFICATE_PATH
ENV SSL_CERTIFICATE_PATH ${SSL_CERTIFICATE_PATH:-$SSL_CERTIFICATE_DIR/fullchain.cer}
ARG SSL_CERTIFICATE_KEY_PATH
ENV SSL_CERTIFICATE_KEY_PATH ${SSL_CERTIFICATE_KEY_PATH:-$SSL_CERTIFICATE_DIR/$VHOSTNAME.key}
ARG SSL_TRUSTED_CERTIFICATE_PATH
ENV SSL_TRUSTED_CERTIFICATE_PATH ${SSL_TRUSTED_CERTIFICATE_PATH:-$SSL_CERTIFICATE_DIR/ca.cer}

# flush nginx config
RUN rm -v /etc/nginx/conf.d/*

# copy config
COPY vhost.conf $DIR_CONF

# edit vhost.conf
RUN sed -i "s@vhostname@$VHOSTNAME@g" "$DIR_CONF/vhost.conf" && \
    sed -i "s@ssl_certificate_path@$SSL_CERTIFICATE_PATH@g" "$DIR_CONF/vhost.conf" && \
    sed -i "s@ssl_certificate_key_path@$SSL_CERTIFICATE_KEY_PATH@g" "$DIR_CONF/vhost.conf" && \
    sed -i "s@ssl_trusted_certificate_path@$SSL_TRUSTED_CERTIFICATE_PATH@g" "$DIR_CONF/vhost.conf"

#debug mode
RUN  if [ "$DEBUG" = True ]; then (echo 'Check nginx configuration: '; cat "$DIR_CONF/vhost.conf"; echo 'Check defined environment variables: '; env); fi
