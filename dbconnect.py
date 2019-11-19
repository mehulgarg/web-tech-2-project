import psycopg2


def connection():
    conn = psycopg2.connect(host = 'localhost', user = 'postgres', password = 'root', database = 'invest')
    conn.autocommit = True
    c = conn.cursor()

    return c, conn
