### PostgreSQL
```
docker volume create pgdata
docker run -it --net host -v pgdata:/var/lib/postgresql/data --name orchids-db -e POSTGRES_PASSWORD=Money -d postgres:13
```

Create database
```
docker exec -it orchids-db bash

root@donghm:/# psql -U postgres

postgres=# create database orchids;
CREATE DATABASE
```
**pgadmin**: if needed
```
docker run --net host --name pgadmin4 \
    -e 'PGADMIN_DEFAULT_EMAIL=user@domain.com' \
    -e 'PGADMIN_DEFAULT_PASSWORD=SuperSecret' \
    -d dpage/pgadmin4
```

### Create venv and Init db
We're using python3.6
```
cd ~/git/orchids-lover
virtualenv -p python3 env
source env/bin/activate
pip install -r requirements-pgsql.txt

python manage.py db init
python manage.py db migrate -m "Init db"
python manage.py db upgrade
```

**To run app:**
```
python manage.py runserver 
```