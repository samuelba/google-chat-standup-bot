m1 = [
    """
    CREATE TYPE "day_type" AS ENUM (
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday',
      'Saturday',
      'Sunday'
    );
    """,
    """
    CREATE TYPE "question_type" AS ENUM (
      '0_na',
      '1_retrospect',
      '2_outlook',
      '3_blocking'
    );
    """,
    """
    CREATE TABLE "__schema_version" (
      "version" int NOT NULL
    );
    """,
    """
    CREATE TABLE "teams" (
      "id" SERIAL PRIMARY KEY,
      "name" varchar UNIQUE,
      "space" varchar
    );
    """,
    """
    CREATE TABLE "users" (
      "id" SERIAL PRIMARY KEY,
      "google_id" varchar UNIQUE,
      "space" varchar UNIQUE,
      "name" varchar,
      "email" varchar UNIQUE,
      "avatar_url" varchar,
      "team_id" int,
      "active" boolean DEFAULT True
    );
    ALTER TABLE "users" ADD FOREIGN KEY ("team_id") REFERENCES "teams" ("id");
    """,
    """
    CREATE TABLE "standups" (
      "id" SERIAL PRIMARY KEY,
      "user_id" int,
      "question_type" question_type DEFAULT '0_na',
      "answer" varchar,
      "added" timestamp DEFAULT NOW(),
      "message_id" varchar
    );
    ALTER TABLE "standups" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");
    """,
    """
    CREATE TABLE "schedules" (
      "id" SERIAL PRIMARY KEY,
      "user_id" int,
      "day" day_type,
      "enabled" boolean DEFAULT True,
      "time" time DEFAULT '09:00:00'
    );
    ALTER TABLE "schedules" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");
    CREATE UNIQUE INDEX ON "schedules" ("user_id", "day");
    """,
    f"""
    INSERT INTO __schema_version VALUES(1);
    """
]

m2 = [
    """
    CREATE OR REPLACE FUNCTION create_schedules_function()
      RETURNS TRIGGER 
      LANGUAGE PLPGSQL AS
    $$
    BEGIN
      INSERT INTO schedules AS s (user_id, day, time, enabled)
        VALUES (NEW.id, 'Monday', '09:00:00', True),
               (NEW.id, 'Tuesday', '09:00:00', True),
               (NEW.id, 'Wednesday', '09:00:00', True),
               (NEW.id, 'Thursday', '09:00:00', True),
               (NEW.id, 'Friday', '09:00:00', True),
               (NEW.id, 'Saturday', '09:00:00', False),
               (NEW.id, 'Sunday', '09:00:00', False);
      RETURN NEW;
    END;
    $$;
    CREATE TRIGGER create_schedules 
      AFTER INSERT ON users
      FOR EACH ROW
        EXECUTE PROCEDURE create_schedules_function();
    """,
    """
    UPDATE __schema_version SET version = 2;
    """
]

m3 = [
    """
    CREATE TABLE "questions" (
      "id" SERIAL PRIMARY KEY,
      "team_id" int,
      "question" varchar,
      "question_order" int
    );
    ALTER TABLE "questions" ADD FOREIGN KEY ("team_id") REFERENCES "teams" ("id") ON DELETE CASCADE;
    CREATE UNIQUE INDEX ON "questions" ("team_id", "question");
    CREATE UNIQUE INDEX ON "questions" ("team_id", "question_order");
    """,
    """
    ALTER TABLE "standups" DROP COLUMN "question_type";
    ALTER TABLE "standups" ADD COLUMN "question_id" int;
    ALTER TABLE "standups" ADD FOREIGN KEY ("question_id") REFERENCES "questions" ("id") ON DELETE CASCADE;
    DROP TYPE "question_type";
    """,
    """
    CREATE OR REPLACE FUNCTION create_default_questions_function()
      RETURNS TRIGGER 
      LANGUAGE PLPGSQL AS
    $$
    BEGIN
      INSERT INTO questions AS q (team_id, question, question_order)
        VALUES (NEW.id, '', 0),
               (NEW.id, 'What did you do yesterday?', 1),
               (NEW.id, 'What will you do today?', 2),
               (NEW.id, 'What (if anything) is blocking your progress?', 3);
      RETURN NEW;
    END;
    $$;
    CREATE TRIGGER create_default_questions 
      AFTER INSERT ON teams
      FOR EACH ROW
        EXECUTE PROCEDURE create_default_questions_function();
    """,
    """
    UPDATE __schema_version SET version = 3;
    """
]

migrations = [m1, m2, m3]
