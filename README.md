# Django SQL to REST

Quick and easy REST framework. 

The aim of this project is to provide an easy way to create a REST API. All you need is a SQL database. In it's simplest way, you just have to GET a table name and it will return the data as JSON.

## Requirements
* Python 3.6.+ I didn't try with earlier versions. Please check requirements for Django 2.1.7.
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
* *SQL Query*: Query used by `GET` method. If you need to pass any arguments into your query, use the python string format notation with named parameters. Example: `select * from people where age >= {min_age}`. When calling a persistent query, you can still apply `columns`, `where` and `order` parameters the same way you can do with adhoc queries.
* *SQl Insert*: Query used by `POST` method to insert data. You can declare parameters the same way you do with *SQL Query*. The query formatter will quote string values automatically when replacing parameters, so you must not quote the string parameters in yor query. See the example below: 
```
insert into people (name, age) values ({name}, {age})
```

If your primary key is not generated and you have to provide a value, you can use the `{pk}` parameter instead of a parameter with the column name. 

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

### Query Builder
*SQL Insert*, *SQL Update* and *SQL Delete* fields may be left empty. When any of these fields is empty, corresponding statements will be built by the query builder based on data from *Insert PK* field.


### Executing persistent queries
#### GET
Pass all the arguments in the URL as query parameters. You **must** pass the query id as part of the URL. This will tell the endpoint wich persistent query ID it should search for. You must also pass arguments corresponding to any parameters you have declared into your query. Suppose you have a persistent query with ID `people` with a get query like `select * from people where age >= {min_age}`. The get URL must be something like
```
http://127.0.0.1:8000/query/persistent/people/?min_age=21
```

You can still pass the same parameters used in adhoc queries, as in
```
http://127.0.0.1:8000/query/persistent/people/?min_age=21&columns=first_name~last_name~age&order=age desc
```

#### POST
The `POST` method executes the insert query. As in GET method, the requested URL must include the query id. The request body **must** contain `data` attribute with data to be inserted. Optionally it may contain a `pk` attribute if your query doesn't have a serial integer field as primary key. If some argument is not provided, the query formatter will assign `null` to the corresponding column. To insert a new record into people persistent query, do something like this:

```
curl -X POST "http://127.0.0.1:8000/query/persistent/people/" \
    -d '{"data": {"first_name": "John", "last_name": "Doe", "age": 34}}'
```

If it goes all right, the response will be the last record inserted. In this case, supposing the PK is an autoincrement integer field called `id`, the response will be the result from 

```
select * from public.people where id = (select max(id) from public.people)
```


#### PUT
The `PUT` method executes the update query. It works just like `POST` except that the `pk` **is mandatory** and it must be part of the URL. The update query must refer to the primary key in it's where clause.

If you keep the params names exactly the same as the columns names in your update clause, you can pass only the fields that you want to change. The parameters that don't receive corresponding arguments will be replaced by the parameter name, so the column will be assigned to itself when updating. 

Supposing the update query is

```
update public.people
set first_name = {first_name}, last_name = {last_name}, age = {age} 
where id = {pk}
```

The following request

```
curl -X PUT "http://127.0.0.1:8000/query/persistent/people/2/" \
    -d '{"data": {"first_name": "Jack"}}'
```

will execute an update statement like this:

```
update public.people
set first_name = 'Jack', last_name = last_name, age = age 
where id = 2
```

### DELETE
The `DELETE` method executes the delete query. Just like in `PUT`, you must pass the `pk`. For now, only one record at a time can be deleted. There are no additional parameters that can be passed in the url query.

The request
```
curl -X DELETE "http://127.0.0.1:8000/query/persistent/people/2/" 
```

will run the delete statement.

### Master detail relationships

Persistent queries may include children queries. In the persistent query administration form, add a persistent nested query and fill in the following fields:
* **Child query** - any persistent query object which *SQL Query* field contains a `{parent_pk}` parameter in it's where clause.
* **Attribute name** - an attribute to receive the child data. It should not clash with any column name from the current query. Otherwise, the original attribute will be overriden.
* **Related field** - the field in the child query that relates to the current (parent) query pk. When getting child data, the `{parent_pk}` parameter will be replaced by the current pk.

#### Requesting nested data
Currently, it's only possible to GET nested data. The GET request must include `depth` (default = 0) in the query arguments to inform how many levels of nesting depth must be included in the response.
In the following example, the request for sales orders will return an order and it's items.

```
curl -X GET "http://127.0.0.1:8000/query/persistent/orders/?where=id=1&depth=1"
```

```
{
    "status": "OK", 
    "query": "Orders", 
    "data": [
        {
            "id": 1, 
            "number": 19, 
            "customer": 2, 
            "items": [
                {"id": 1, "order": 1, "description": "First item"}, 
                {"id": 3, "order": 1, "description": "Second item"}
            ]
        }
    ]
}
```
