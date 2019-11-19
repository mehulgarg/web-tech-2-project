To run this you need PostgreSQL with a user called postgres and password root<br/>
Initially run the command psql -U postgres invest < dbexport.pgsql<br/>
Then run psql -U postgres -f user_detail.sql<br/>
To run the actual code run python/python3 main.py<br/>
Install all the libraries it says are missing and the run the same command [python/python3 main.py] again.<br/>
