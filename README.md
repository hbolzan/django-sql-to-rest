# Django SQL to REST

Quick and easy REST framework. 

The aim of this project is provide an easy way to create a REST API. All you need is a SQL database. In it's simplest way, you just have to GET a table name and it will return the data as JSON.

## Requirements
* Python 3.6. I didn't try with earlier versions. Please check requirements for Django 2.1.4.
* Pip Python package manager.
* Virtualenv (recommended).

## Getting started

1. Clone this repository: `git clone https://github.com/hbolzan/django-sql-to-rest.git`.
2. Switch to the project directory: `cd django-sql-to-rest`.
3. Install project requirements: `pip install -r requirements.txt`
4. Create a new database in your database server for the default django connection.
5. Create a `local_settings.py` file or modify the project `settings.py` `DATABASES` section to point to the project database and the query database.
6. Run migrate to start system database: `python manage.py migrate`
7. Set django superuser: `python manage.py createsuperuser`
8. Run the development server: `python manage.py runserver`
9. Point a browser to `http://127.0.0.1:8000/`


## How to use

### Ad hoc queries
To run the simplest ad hoc query over a single table, pass the table name as query parameter to `/query/adhoc/` endpoint.
```
http://127.0.0.1:8000/query/adhoc/?table=my_table_name
```

### Ad hoc query options
*columns* - list of column names separeted by `~`. Limits the query result to specified columns.
```
http://127.0.0.1:8000/query/adhoc/?table=my_table_name&columns=id~name~age
```

*order* - list of column names separeted by `~`. Defines `order by` columns.
```
http://127.0.0.1:8000/query/adhoc/?table=my_table_name&columns=id~name~age&order=age~name
```
 
*where* - filter condition form query.
```
http://127.0.0.1:8000/query/adhoc/?table=my_table_name&columns=id~name~age&order=age~name&where=age > 18
```

### Persistent queries

This is a work in progress. Create complex queries and their corresponding insert, update and delete queries.


### Master detail relationships

Not implemented yet.
