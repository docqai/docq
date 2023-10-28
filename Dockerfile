ARG BUILDPLATFORM=linux/amd64
ARG BUILDTAG=3.11-slim-buster
ARG PIPNOCACHE=--no-cache

FROM --platform=$BUILDPLATFORM python:$BUILDTAG as test

WORKDIR /home/user/app

ENV PATH=$PATH:/home/user/.local/bin

RUN pip install ${PIPNOCACHE} poetry poethepoet
RUN poetry config --no-cache
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --no-root

COPY .pre-commit-config.yaml .
COPY README.md .
COPY features features
COPY source source
COPY tests tests

RUN poetry install

ARG TESTBUILD=False
ENV TESTBUILD=$TESTBUILD
RUN if [ "$TESTBUILD" = 'True' ]; then poe lint; fi
RUN if [ "$TESTBUILD" = 'True' ]; then poe test; fi


RUN poetry build --format=wheel
RUN poetry export --only main -f requirements.txt --without-hashes --output requirements.txt

ENTRYPOINT ["poe", "-q"]
CMD ["test"]

FROM --platform=$BUILDPLATFORM python:$BUILDTAG as prod

RUN apt-get update && apt-get install -y bash curl && curl -1sLf \
  'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | bash \
  && apt-get update && apt-get install -y infisical

RUN addgroup --system user && adduser --system user --ingroup user
USER user

WORKDIR /home/user/app

COPY --chown=user:user --from=test /home/user/app/requirements.txt requirements.txt
COPY --chown=user:user --from=test /home/user/app/dist dist
COPY --chown=user:user web web

RUN pip install -r $PIPNOCACHE requirements.txt dist/*.whl --user

ENV INFISICAL_DISABLE_UPDATE_CHECK=true


#ENTRYPOINT ["python", "-m", "streamlit", "run"]
#CMD ["web/index.py", "--browser.gatherUsageStats", "false"]

ENTRYPOINT infisical run --env=${INFISICAL_ENV_NAME} -- python -m streamlit run web/index.py --browser.gatherUsageStats false

