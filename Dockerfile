FROM nexus.cloud:8890/centos/python-36-centos7:1

ENV FLASK_APP run.py

COPY run.py requirements.txt config.py /vsa2/
COPY app /vsa2/app

WORKDIR /vsa2

RUN pip install -r requirements.txt

USER root

ENTRYPOINT [ "python" ]

CMD [ "run.py" ]

