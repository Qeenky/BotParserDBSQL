from pgcopy import CopyManager
import pandas
import psycopg2
from Utils.config import ConnectSring
from Utils.config import User, Password, DataBase, Host, Port
import asyncpg
from io import BytesIO

async def AConnect():
    """Подключение к базе данных"""
    conn = await asyncpg.connect(
        user=User,
        password=Password,
        database=DataBase,
        host=Host,
        port=Port
    )
    return conn

async def get_data():
    """Получение DataFrame таблицы из базы данных"""
    conn = await AConnect()
    rows = await conn.fetch("SELECT * FROM titlesinformation")
    await conn.close()
    df = pandas.DataFrame([dict(row) for row in rows])
    return df

def add_column_func(dataframe, column_add):
    """
    Обновление базы данных с новым столбцом

    :param dataframe: DataFrame pandas
    :param column_add: Название столбца, который добавляем
    """
    conn = psycopg2.connect(ConnectSring)
    cursor = conn.cursor()
    # Создание временной таблицы с нужными полями
    temp_table = "temp_titles_updates"
    cursor.execute(f"""
        CREATE TEMP TABLE {temp_table} (
            title TEXT,
            {column_add} TEXT
        ) ON COMMIT DROP
    """)
    # Загрузка данных во временную таблицу
    mgr = CopyManager(conn, temp_table, ['title', f'{column_add}'])
    mgr.copy(dataframe[['title', f'{column_add}']].values)
    # Ключевое исправление - используем title для сопоставления
    update_query = f"""
    UPDATE titlesinformation t
    SET {column_add} = temp.{column_add}
    FROM {temp_table} temp
    WHERE t.title = temp.title  -- Сравниваем по названиям
    """
    cursor.execute(update_query)
    # Проверка количества обновленных строк
    print(f"Обновлено строк: {cursor.rowcount}")
    conn.commit()
    cursor.close()
    conn.close()


async def append_dataframe_to_table(dataframe: pandas.DataFrame):
    """
    Асинхронно добавляет DataFrame в существующую таблицу PostgreSQL

    :param dataframe: pandas DataFrame для добавления
    :raises ValueError: если DataFrame пуст или есть несоответствие колонок
    :raises Exception: при ошибках работы с БД
    """
    if dataframe.empty:
        raise ValueError("DataFrame пуст. Нечего добавлять.")

    table_name = "titlesinformation"
    conn = None

    try:
        conn = await AConnect()
        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = $1",
            table_name
        )
        db_columns = {col['column_name'] for col in columns}
        df_columns = set(dataframe.columns)
        if not df_columns.issubset(db_columns):
            missing = df_columns - db_columns
            raise ValueError(f"В таблице отсутствуют колонки: {missing}")
        output = BytesIO()
        dataframe.to_csv(output, sep='\t', header=False, index=False, encoding='utf-8')
        output.seek(0)
        await conn.copy_to_table(
            table_name,
            source=output,
            columns=list(dataframe.columns),
            format='csv',
            delimiter='\t'
        )
        print(f"Успешно добавлено {len(dataframe)} строк в таблицу '{table_name}'")
    except Exception as e:
        print(f"Ошибка при добавлении данных: {str(e)}")
        raise
    finally:
        if conn:
            await conn.close()

async def get_last_string():
    """Получение последней строки базы данных"""
    try:
        conn = await AConnect()
        rows = await conn.fetch("SELECT * FROM titlesinformation")
        await conn.close()
        dataframe = pandas.DataFrame([dict(row) for row in rows])
        return dataframe.iloc[-1]
    except Exception as e:
        return pandas.Series(['---'], index=['title'])


