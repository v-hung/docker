FROM dpage/pgadmin4

USER root

COPY servers.json /pgadmin4/servers.json
COPY .pgpass /var/lib/pgadmin/storage/admin_admin.com/.pgpass

RUN chmod 600 /var/lib/pgadmin/storage/admin_admin.com/.pgpass

EXPOSE 80