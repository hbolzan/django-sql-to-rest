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

To create a persistent query, point your browser to `http://127.0.0.1:8000/admin/db_query/persistentquery/` and add a new persistent query. PersistentQuery object has the following attributes:
* *Query name*: a descriptive name to your persistent query.
* *Query ID*: slugified version of query name. It will be filed automatically so you don't have to care about this.
* *Insert PK*: this is the PK field that will be used to retrieve the inserted row after a POST. It must be qualified with schema and table name. If you will be inserting data into `people` table at `public` schema and the field `id` is the primary key you should fill Insert PK with `public.people/id`. If the table is in the default schema you really don't need to specify the schema.
* *Query PK*: DEPRECATED
* *Description*: That's what the name says. Only a description.
* *SQL Query*: Query used by `GET` method. If you need to pass any arguments into your query, use the python string format notation with named parameters. Example: `select * from people where age >= {min_age}`. When calling a persistente query, you can still apply `columns`, `where` and `order` parameters the same way you can do with adhoc queries.
* *SQl Insert*: Query used by `POST` method to insert data. You can declare parameters the same way you do with *SQL Query*. The query formatter will quote string values automatically when replacing arguments, so you should not quote the string arguments in yor query. See the example below: 
```
insert into people (name, age) values ({name}, {age})
```

If your primary key is not a serial integer and you have to provide a value, you can use the `{pk}` parameter instead of a parameter with the column name. 

```
insert into people (id, name, age) values ({pk}, {name}, {age})
```

* *SQL Update*: Query used by `PUT` method. Fill this field with a SQL update statement with parameters following the same rules applied to *SQL Insert*.

```
update people
set first_name = {first_name}, last_name = {last_name}, age = {age} 
where id = {pk}
```

* *SQL Delete*: Query user by `DELETE` method. Declare your delete statement in this field.
```
delete from people where id = {id}
```

### Executing persistent queries
#### GET
Pass all the arguments in the URL as query parameters. You **must** pass `query` that will tell the endpoint wich persistent query ID it should search for. You must also pass arguments corresponding to any parameters you have declared into your query. Suppose you have a persistent query with ID `people` with a get query like `select * from people where age >= {min_age}`. The get URL must be something like
```
http://127.0.0.1:8000/query/persistent/?query=people&min_age=21
```

You can still pass the same parameters used in adhoc queries, as in
```
http://127.0.0.1:8000/query/persistent/?query=people&min_age=21&columns=first_name~last_name~age&order=age desc
```

#### POST
The `POST` method executes the insert query. Pass the arguments as json data in the request body. The request body **must** contain `query` attribute with query ID and `data` attribute with data to be inserted. Optionally it may contain a `pk` attribute if your query doesn't have a serial integer field as primary key. If some argument is not provided, the query formatter will assign `null` to the corresponding column. To insert a new record into people persistent query, do something like this:
```
curl -X POST "http://127.0.0.1:8000/query/persistent/" \
    -d '{"query": "people", "data": {"first_name": "John", "last_name": "Doe", "age": 34}}'
```
If it goes all right, the response will be the last record inserted. In this case, supposing the PK is an autoincrement integer field called `id`, the response will be the result from `select * from public.people where id = (select max(id) from public.people)`.


#### PUT
The `PUT` method executes the update query. It works just like `POST` except that the `pk` attribute **is mandatory**. The update query must refer to the primary key in it's where clause.

Supposing the update query is
```
update people_table 
set first_name = {first_name}, last_name = {last_name}, age = {age} 
where id = {pk}
```

If you keep the params names exactly the same as the columns names in your update clause, you can pass only the fields that you want to change. The parameters that don't receive corresponding arguments will be replaced by the parameter name, so the column will be assigned to itself when updating.

```
curl -X PUT "http://127.0.0.1:8000/query/persistent/" \
    -d '{"query": "people", "pk": 2, "data": {"id": 2, "first_name": "Jack"}}'
```


### Master detail relationships

Not implemented yet.
