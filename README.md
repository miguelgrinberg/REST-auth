REST-auth
=========

Companion application to my [RESTful Authentication with Flask](http://blog.miguelgrinberg.com/restful-authentication-with-flask) article.

Installation
------------

After cloning, create a virtual environment and install the requirements. For Linux and Mac users:

    $ virtualenv venv
    $ source venv/bin/activate
    (venv) $ pip install -r requirements.txt

If you are on Windows, then use the following commands instead:

    $ virtualenv venv
    $ venv\Scripts\activate
    (venv) $ pip install -r requirements.txt

Running
-------

To run the server use the following command:

    (venv) $ python api.py
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader

Then from a different terminal window you can send requests.

API Documentation
-----------------

- POST **/users**

    Register a new user.<br>
    The body must contain a JSON object that defines `username` and `password` fields.<br>
    On success a JSON object is returned with a field `result` set to `true`.<br>
    On failure status code 400 (bad request) is returned.<br>
    Notes:
    - The password is hashed before it is stored in the database. Once hashed, the original password is discarded.
    - In a production deployment secure HTTP must be used to protect the password in transit.

- GET **/token**

    Return an authentication token.<br>
    This request must be authenticated using a HTTP Basic Authentication header.<br>
    On success a JSON object is returned with a field `token` set to the authentication token for the user. This token is valid for 10 minutes from the time it was issued.<br>
    On failure status code 401 (unauthorized) is returned.

- GET **/resource**

    Return a protected resource.<br>
    This request must be authenticated using a HTTP Basic Authentication header. Instead of username and password, the client can provide a valid authentication token in the username field. If using an authentication token the password field is not used and can be set to any value.<br>
    On success a JSON object with data for the authenticated user is returned.<br>
    On failure status code 401 (unauthorized) is returned.

Example
-------

The following `curl` command registers a new user with username `miguel` and password `python`:

    $ curl -X POST -H "Content-Type: application/json" -d '{"username":"miguel","password":"python"}' http://localhost:5000/api/users
    {
      "result": true
    }

These credentials can now be used to access protected resources:

    $ curl -u miguel:python -X GET http://localhost:5000/api/resource
    {
      "data": "Hello, miguel!"
    }

Using the wrong credentials the request is refused:

    $ curl -u miguel:ruby -X GET http://localhost:5000/api/resource
    Unauthorized Access

Finally, to avoid sending username and password with every request an authentication token can be requested:

    $ curl -u miguel:python -X GET http://localhost:5000/api/token
    {
      "token": "eyJleHAiOjEzODU1OTM3MzIsImlhdCI6MTM4NTU5MzEzMiwiYWxnIjoiSFMyNTYifQ.eyJpZCI6MX0.uc92MTwiB0vnyFG68PzCziwnPqCTFq_QwLOz5btOSgg"
    }

And now during the token validity period there is no need to send username and password to authenticate anymore:

    $ curl -u eyJleHAiOjEzODU1OTM3MzIsImlhdI6MTM4NTU5MzEzMiwiYWxnIjoiSFMyNTYifQ.eyJpZCI6MX0.uc92MTwiB0vnyFG68PzCziwnPqCTFq_QwLOz5btOSgg:x -X GET http://localhost:5000/api/resource
    {
      "data": "Hello, miguel!"
    }

Once the token expires it cannot be used anymore and the client needs to request a new one. Note that in this last example the password is arbitrarily set to `x`, since the password isn't used for token authentication.

An interesting side effect of this implementation is that it is possible to use an unexpired token as authentication to request a new token that extends the expiration time. This effectively allows the client to change from one token to the next and never need to send username and password after the initial token was obtained.


