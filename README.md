# Django SQL to REST

Quick and easy REST framework. 

The aim of this project is provide an easy way to create an REST API. All you need is a PostgreSQL database. In it's simplest way, you just have to GET a table name and it will return the data as JSON.

## Requirements
* Python 3.6. I didn't try with earlier versions. Please check requirements for Django 2.1.4.
* Pip Python package manager.
* Virtualenv (recommended).

## To run it:

1. Clone this repository: `git clone https://github.com/hbolzan/django-sql-to-rest.git`.
2. Switch to the project directory: `cd django-sql-to-rest`
3. Install project requirements: `pip install -r requirements.txt`
4. Run the development server: `python manage.py runserver`
5. Open a browser to `http://127.0.0.1:8000/`


## How to use

### Simple query
To run a simple query over a single table, pass the table name as query parameter to `/query/simple/` endpoint.
```
http://127.0.0.1:8000/query/simple/?table=my_table_name
```
