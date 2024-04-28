# AiMatrixScraper Project: db_ops.py
import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    """ Create a database connection to the SQLite database specified by db_file. """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn

def execute_sql(conn, sql, data=None, fetch_one=False, fetch_all=False):
    try:
        c = conn.cursor()
        if data:
            c.execute(sql, data)
        else:
            c.execute(sql)
        if fetch_one:
            return c.fetchone()
        if fetch_all:
            return c.fetchall()
        conn.commit()
    except Error as e:
        print(f"Error executing SQL: {e}")
        print(f"ALL INFO: {conn}, {sql}, {data}, {fetch_one}, {fetch_all}")
    return None


def create_table(conn, create_table_sql):
    """ Create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        print("Table created successfully")
    except Error as e:
        print(f"Error creating table: {e}")


def main():
    database = "ame_scraper.db"

    sql_create_scrape_method_table = """\
        CREATE TABLE IF NOT EXISTS scrape_methods (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            UNIQUE(name)
        );"""

    sql_create_domain_table = """\
    CREATE TABLE IF NOT EXISTS domains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        server_type TEXT,
        robots_txt TEXT,
        rate_limit_info TEXT,
        security_policies TEXT,
        redirection_patterns TEXT,
        last_updated TIMESTAMP
    );"""

    sql_create_domain_scrape_method_table = """\
        CREATE TABLE IF NOT EXISTS domain_scrape_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_url TEXT NOT NULL,
            scrape_method_id INTEGER NOT NULL,
            FOREIGN KEY (domain_url) REFERENCES domains (url),
            FOREIGN KEY (scrape_method_id) REFERENCES scrape_methods (id),
            UNIQUE (domain_url, scrape_method_id)
        );"""

    sql_create_sitemap_urls_table = """\
        CREATE TABLE IF NOT EXISTS sitemap_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            FOREIGN KEY (domain_id) REFERENCES domains (rowid)
        );"""

    sql_create_sitemap_contents_table = """\
        CREATE TABLE IF NOT EXISTS sitemap_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            last_fetched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (domain_id) REFERENCES domains (rowid)
        );"""

    sql_create_webpages_table = """\
        CREATE TABLE IF NOT EXISTS webpages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            domain_id INTEGER NOT NULL,
            http_status INTEGER NOT NULL DEFAULT 200,  -- Assuming default HTTP status
            access_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            meta_tags TEXT,
            content_type TEXT,
            page_load_time REAL,
            page_size INTEGER,
            language TEXT,
            page_specific_cookies TEXT,
            redirection_info TEXT,
            link_headers TEXT,
            last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (domain_id) REFERENCES domains(ROWID)
        );"""

    sql_create_links_table = """\
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            text TEXT,
            href TEXT NOT NULL,
            class_attr TEXT,
            id_attr TEXT,
            FOREIGN KEY (page_id) REFERENCES webpages (id) ON DELETE CASCADE
        );"""

    sql_create_images_table = """\
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            src TEXT NOT NULL,
            alt TEXT,
            class_attr TEXT,
            id_attr TEXT,
            FOREIGN KEY (page_id) REFERENCES webpages (id) ON DELETE CASCADE
        );"""

    sql_create_scrape_task_table = """\
    CREATE TABLE IF NOT EXISTS scrape_tasks (
        id INTEGER PRIMARY KEY,
        url_to_scrape TEXT NOT NULL,
        force_new_scrape BOOLEAN NOT NULL DEFAULT 0,
        priority INTEGER NOT NULL DEFAULT 5,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        preprocess_status TEXT NOT NULL DEFAULT 'pending',
        scrape_status TEXT NOT NULL DEFAULT 'pending',
        webpage_id INTEGER,
        scrape_result_id INTEGER,
        FOREIGN KEY (webpage_id) REFERENCES webpages (id) ON DELETE SET NULL,
        FOREIGN KEY (scrape_result_id) REFERENCES scrape_results (id) ON DELETE SET NULL
    );"""

    sql_create_scrape_result_table = """\
        CREATE TABLE IF NOT EXISTS scrape_results (
            id INTEGER PRIMARY KEY,
            webpage_id INTEGER NOT NULL UNIQUE,
            title TEXT,
            content TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            content_length INTEGER DEFAULT 0,
            content_hash TEXT,
            FOREIGN KEY (webpage_id) REFERENCES webpages (id)
        );"""

    sql_create_heading_structures_table = """\
    CREATE TABLE IF NOT EXISTS heading_structures (
        id INTEGER PRIMARY KEY,
        result_id INTEGER UNIQUE NOT NULL,
        data TEXT NOT NULL,  -- JSON data for heading hierarchy and content
        FOREIGN KEY (result_id) REFERENCES scrape_results (id) ON DELETE CASCADE
    );"""

    sql_create_structured_data_table = """\
    CREATE TABLE IF NOT EXISTS structured_data (
        id INTEGER PRIMARY KEY,
        result_id INTEGER UNIQUE NOT NULL,
        schema_org_data TEXT NOT NULL,  -- JSON data for schema.org information
        FOREIGN KEY (result_id) REFERENCES scrape_results (id) ON DELETE CASCADE
    );"""

    sql_create_scrape_histories_table = """\
    CREATE TABLE IF NOT EXISTS scrape_histories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL,  -- Could refine to use limited choices as in Django
        FOREIGN KEY (task_id) REFERENCES scrape_tasks (id) ON DELETE CASCADE
    );"""

    sql_create_scrape_combinations_table = """\
    CREATE TABLE IF NOT EXISTS scrape_combinations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    );"""

    sql_create_combination_methods_table = """\
    CREATE TABLE IF NOT EXISTS combination_methods (
        combination_id INTEGER NOT NULL,
        method_id INTEGER NOT NULL,
        FOREIGN KEY (combination_id) REFERENCES scrape_combinations (id),
        FOREIGN KEY (method_id) REFERENCES scrape_methods (id),
        UNIQUE (combination_id, method_id)
    );"""

    sql_create_apis_table = """\
    CREATE TABLE IF NOT EXISTS apis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        details TEXT NOT NULL,
        documentation_url TEXT
    );"""

    sql_create_technology_stacks_table = """\
    CREATE TABLE IF NOT EXISTS technology_stacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain_id INTEGER NOT NULL,
        cms_technology TEXT,
        category TEXT NOT NULL,
        version TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (domain_id) REFERENCES domains (rowid),
        UNIQUE (domain_id, category)
    );"""

    # Create a database connection
    conn = create_connection(database)

    # Create tables if connection is established
    if conn is not None:
        create_table(conn, sql_create_scrape_method_table)
        create_table(conn, sql_create_domain_table)
        create_table(conn, sql_create_domain_scrape_method_table)
        create_table(conn, sql_create_sitemap_urls_table)
        create_table(conn, sql_create_sitemap_contents_table)
        create_table(conn, sql_create_webpages_table)
        create_table(conn, sql_create_links_table)
        create_table(conn, sql_create_images_table)
        create_table(conn, sql_create_scrape_task_table)
        create_table(conn, sql_create_scrape_result_table)
        create_table(conn, sql_create_heading_structures_table)
        create_table(conn, sql_create_structured_data_table)
        create_table(conn, sql_create_scrape_histories_table)
        create_table(conn, sql_create_scrape_combinations_table)
        create_table(conn, sql_create_combination_methods_table)
        create_table(conn, sql_create_apis_table)
        create_table(conn, sql_create_technology_stacks_table)

        conn.close()
    else:
        print("Error! Cannot create the database connection.")


if __name__ == '__main__':
    main()
