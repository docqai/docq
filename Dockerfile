ARG BUILDPLATFORM=linux/amd64
ARG BUILDTAG=3-alpine

FROM --platform=$BUILDPLATFORM python:$BUILDTAG as test

WORKDIR /home/user/app

ENV PATH=$PATH:/home/user/.local/bin

RUN pip install --no-cache poetry poethepoet
RUN poetry config --no-cache
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --no-root

COPY .pre-commit-config.yaml .
COPY README.md .
COPY features features
COPY docq docq
COPY tests tests

RUN poetry install

ARG TESTBUILD=True
ENV TESTBUILD=$TESTBUILD
RUN if [ "$TESTBUILD" = 'True' ]; then poe lint; fi
RUN if [ "$TESTBUILD" = 'True' ]; then poe test; fi


RUN poetry build --format=wheel
RUN poetry export --only main -f requirements.txt --without-hashes --output requirements.txt

ENTRYPOINT ["poe", "-q"]
CMD ["test"]

FROM --platform=$BUILDPLATFORM python:$BUILDTAG as prod

RUN addgroup --system user && adduser --system user --ingroup user
USER user

WORKDIR /home/user/app

COPY --chown=user:user --from=test /home/user/app/requirements.txt requirements.txt
COPY --chown=user:user --from=test /home/user/app/dist dist

RUN pip install --no-cache -r requirements.txt dist/*.whl --user


ENTRYPOINT ["python", "-m"]
CMD ["docq.docq"]

