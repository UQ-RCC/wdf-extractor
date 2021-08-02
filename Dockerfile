FROM python:3.7-slim as BUILDER

RUN apt-get -y update
RUN apt install -y -qq python3-pip

COPY * /home/

RUN pip3 install -r /home/requirements.txt

CMD ["python3", "/home/raman_wdf.py"]