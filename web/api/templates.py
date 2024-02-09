"""HTML page templates."""

LOGIN_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Login</title>
  <link
    rel="stylesheet"
    href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"
  />
</head>
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
  </body>
</html>"""
