FROM nginx

# environment
ENV DIR_CONF /etc/nginx/conf.d/
ENV DIR_APP /var/www/app/
ENV VHOSTNAME demo.kqueen.net

# flush nginx config
RUN rm -v /etc/nginx/conf.d/*

# copy config
COPY vhost.conf $DIR_CONF

# edit vhost.conf
RUN sed -i "s/vhostname/$VHOSTNAME/g" $DIR_CONF/vhost.conf
