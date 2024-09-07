# Docq.AI RESTful API

## Introduction

This is a RESTful API that provides access to Docq.AI SaaS.
[Postman Collection](https://www.postman.com/spacecraft-physicist-48460084/workspace/docq-api/collection/22287507-cae373c0-bdf6-4efe-9594-f2d8fd10f924?action=share&creator=22287507)

## Authentication

The API uses JWT for authentication. You can obtain a token by sending a POST request to the `/api/{version}/token` endpoint with your username and password.

## Pattern for this API

Refactoring towards: <https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api>
