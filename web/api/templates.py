"""HTML page templates."""

BASE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link
    rel="stylesheet"
    href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"
  />
</head>
{body}
</html>"""

LOGIN_PAGE_TEMPLATE = BASE_HTML_TEMPLATE.format(
title="Login",
body="""
<body>
  <h1 class="text-center mt-5">Login</h1>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-body">
            <form action="/api/auth/login" method="post">
              <div class="form-group">
                <label for="username"> Username </label>
                <input type="text" class="form-control" id="username" name="username" placeholder="Username" autocomplete="username" />
              </div>
              <div class="form-group">
                <label for="password"> Password </label>
                <input type="password" class="form-control" id="password" name="password" placeholder="Password" autocomplete="current-password" />
              </div>
              <div class="row justify-content-center">
                <input type="submit" class="btn btn-danger px-5" value="Login"/>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
  </body>"""
)

LOGIN_SUCCESS_PAGE_TEMPLATE = BASE_HTML_TEMPLATE.format(
title="Login Success",
body="""
<body>
  <h1 class="text-center mt-5">Login Success</h1>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-body mt-5">
            <h3 class="text-success text-center">Success</h1>
          </div>
        </div>
      </div>
    </div>
  </div>
  </body>"""
)

LOGIN_ERROR_TEMPLATE = BASE_HTML_TEMPLATE.format(
title="Error",
body="""
<body>
  <h1 class="text-center mt-5">Login Failure</h1>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-body">
            <p class="text-danger text-center">{reason}</p>
            <div class="row justify-content-center">
              <a href="/api/auth/login" class="mt-5">Try again</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  </body>"""
)
