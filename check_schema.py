from database import create_connection, DB_CONFIG

conn = create_connection()
if not conn:
    print('No database connection')
else:
    cursor = conn.cursor()
    cursor.execute(
        'SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position',
        (DB_CONFIG['database'], 'users')
    )
    cols = [row[0] for row in cursor.fetchall()]
    print('columns:', cols)
    cursor.close()
    conn.close()
