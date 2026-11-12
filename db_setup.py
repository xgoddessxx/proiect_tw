import pymysql







def initialize_database():


    fisier_secret = "secretraufrate.txt"
    try:
        with open(fisier_secret, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.read().splitlines() if line.strip()]
            host, database, user, password = lines[:4]
    except Exception as e:

        exit(1)

    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW DATABASES LIKE '{database}';")
            db_exists = cursor.fetchone()

            if db_exists:
                print(f"Baza de date exista deja.")
            else:
                print(f"Baza de date se creaza")

            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS `{database}`
                CHARACTER SET utf8mb4
                COLLATE utf8mb4_unicode_ci;
            """)

            cursor.execute(f"USE `{database}`;")


            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shows (
                  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                  title VARCHAR(255) NOT NULL,
                  author VARCHAR(255) NULL,
                  director VARCHAR(255) NULL,
                  description TEXT NULL,
                  productie_proprie BOOLEAN NOT NULL DEFAULT TRUE,
                  genre VARCHAR(255) NULL,
                  language VARCHAR(255) NULL,
                  duration_minutes INT UNSIGNED NULL,
                  duration_text VARCHAR(255) NULL,
                  age_recommendation VARCHAR(255) NULL,
                  premiere_date DATE NULL,
                  cast_json JSON NULL,
                  team_json JSON NULL,
                  poster_storage ENUM('file', 'base64') NULL,
                  poster_path VARCHAR(1024) NULL,
                  poster_base64 LONGTEXT NULL,
                  poster_mime_type VARCHAR(100) NULL,
                  poster_source_url VARCHAR(2048) NULL,
                  poster_hash CHAR(64) NULL,
                  source_url VARCHAR(512) UNIQUE NOT NULL,
                  last_seen_at TIMESTAMP NULL,
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                  INDEX idx_shows_title (title),
                  INDEX idx_shows_author (author),
                  INDEX idx_shows_director (director),
                  INDEX idx_shows_premiere_date (premiere_date)
                ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
            """)


            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performances (
                  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                  show_id BIGINT UNSIGNED NOT NULL,
                  start_at TIMESTAMP NOT NULL,
                  end_at TIMESTAMP NULL,
                  venue VARCHAR(255) NULL,
                  performance_type VARCHAR(100) NULL,
                  status VARCHAR(50) NULL,
                  notes TEXT NULL,
                  source_url VARCHAR(2048) NULL,
                  last_seen_at TIMESTAMP NULL,
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                  CONSTRAINT fk_performances_show
                    FOREIGN KEY (show_id)
                    REFERENCES shows(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                  INDEX idx_performances_show_id (show_id),
                  INDEX idx_performances_start_at (start_at),
                  INDEX idx_performances_venue (venue),
                  INDEX idx_performances_show_date (show_id, start_at)
                ) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
            """)

        connection.commit()
        print("Baza e gata")

    except Exception as e:
        print(f"Eroare: {e}")
    finally:
        connection.close()


