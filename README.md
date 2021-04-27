# Powerplant coding challenge

This is my submission for the [powerplant-coding-challenge](https://github.com/gem-spaas/powerplant-coding-challenge).
The original README.md was moved to [doc/README.md](doc/README.md).


## Assumptions

This guide assumes that you are working with a Unix command line, and that you have already install Python (minimal version : 3.6)

## Setup

Clone the repository from github and enter the project directory:

`git clone https://github.com/karimelhajoui63/powerplant-coding-challenge.git`

`cd powerplant-coding-challenge`

Set up a new virtual environment and activate it:

`python -m venv .venv`

`source .venv/bin/activate`

Install the minimum requirements:

`pip install -r requirements.txt`


## How to run


Host the server locally:

`python src/api.py`

The application will start on `http://localhost:8888`.

## Send payload

Open Postman (or every other API testing tool), select a POST request and add the url of the API : `http://localhost:8888/productionplan`. 
Copy/Paste your json file contents in the body (choose 'raw' and 'JSON') and hit the Send button.
The response json will then be sent back if a solution if possible.
If it's not the case, a message indicating that no solution has been found will be returned.

You can also submit a chosen payload by using the following CURL command:
`curl -X POST -d @test/example_payloads/payload1.json -H "Content-Type: application/json" http://localhost:8888/productionplan`


## Logging

Every request and every error is logged in [log/api.log](log/api.log).