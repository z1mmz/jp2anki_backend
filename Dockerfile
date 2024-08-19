FROM python:3.10


WORKDIR /
COPY requirements.txt .
RUN apt-get update -y
RUN apt-get install -y clang build-essential cmake mercurial
RUN pip install 'setuptools<57.0.0'
RUN pip install --upgrade pip
RUN pip install cython

RUN pip install git+https://github.com/clab/dynet#egg=dynet --no-build-isolation
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn


COPY . app
WORKDIR /app
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "api:app"]
