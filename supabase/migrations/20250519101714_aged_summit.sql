/*
  # Initial Database Schema

  1. New Tables
    - users
      - id (uuid, primary key)
      - username (text, unique)
      - email (text, unique)
      - phone (text, unique)
      - password_hash (text)
      - height (float)
      - weight (float)
      - birth_date (date)
      - gender (text)
      - activity_level (text)
      - created_at (timestamptz)
      - updated_at (timestamptz)

    - health_records
      - id (uuid, primary key)
      - user_id (uuid, foreign key)
      - record_date (date)
      - record_type (text)
      - weight (float)
      - height (float)
      - bmi (float)
      - blood_pressure_systolic (integer)
      - blood_pressure_diastolic (integer)
      - heart_rate (integer)
      - blood_sugar (float)
      - body_fat (float)
      - sleep_hours (float)
      - steps (integer)
      - food_name (text)
      - meal_type (text)
      - food_amount (float)
      - exercise_type (text)
      - duration (integer)
      - intensity (text)
      - calories_burned (float)
      - distance (float)
      - water_amount (integer)
      - water_type (text)
      - intake_time (time)
      - medication_name (text)
      - dosage (float)
      - dosage_unit (text)
      - frequency (text)
      - time_taken (time)
      - with_food (boolean)
      - effectiveness (integer)
      - side_effects (text)
      - notes (text)
      - created_at (timestamptz)
      - updated_at (timestamptz)

    - foods
      - id (uuid, primary key)
      - name (text)
      - category (text)
      - calories (float)
      - protein (float)
      - fat (float)
      - carbohydrate (float)
      - fiber (float)
      - sugar (float)
      - sodium (float)
      - serving_size (float)

    - exercise_types
      - id (uuid, primary key)
      - name (text, unique)
      - category (text)
      - calories_per_hour (float)
      - description (text)
      - benefits (text)

    - medication_types
      - id (uuid, primary key)
      - name (text, unique)
      - category (text)
      - description (text)
      - common_dosage (text)
      - side_effects (text)
      - precautions (text)
      - created_at (timestamptz)
      - updated_at (timestamptz)

    - health_goals
      - id (uuid, primary key)
      - user_id (uuid, foreign key)
      - goal_type (text)
      - target_value (float)
      - current_value (float)
      - start_date (date)
      - end_date (date)
      - status (text)
      - notes (text)
      - created_at (timestamptz)
      - updated_at (timestamptz)

    - health_reports
      - id (uuid, primary key)
      - user_id (uuid, foreign key)
      - title (text)
      - report_type (text)
      - start_date (date)
      - end_date (date)
      - health_summary (text)
      - diet_summary (text)
      - exercise_summary (text)
      - medication_summary (text)
      - recommendations (text)
      - created_at (timestamptz)
      - updated_at (timestamptz)

    - reminders
      - id (uuid, primary key)
      - user_id (uuid, foreign key)
      - reminder_type (text)
      - title (text)
      - description (text)
      - reminder_date (date)
      - reminder_time (time)
      - recurrence (text)
      - is_completed (boolean)
      - notes (text)
      - created_at (timestamptz)
      - updated_at (timestamptz)

    - shares
      - id (uuid, primary key)
      - user_id (uuid, foreign key)
      - content_type (text)
      - content_id (uuid)
      - description (text)
      - visibility (text)
      - created_at (timestamptz)
      - updated_at (timestamptz)

    - likes
      - id (uuid, primary key)
      - user_id (uuid, foreign key)
      - share_id (uuid, foreign key)
      - created_at (timestamptz)

    - comments
      - id (uuid, primary key)
      - user_id (uuid, foreign key)
      - share_id (uuid, foreign key)
      - content (text)
      - parent_id (uuid, foreign key)
      - created_at (timestamptz)
      - updated_at (timestamptz)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users

  3. Changes
    - Initial schema creation
*/

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  username text UNIQUE,
  email text UNIQUE,
  phone text UNIQUE,
  password_hash text,
  height float,
  weight float,
  birth_date date,
  gender text,
  activity_level text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create health_records table
CREATE TABLE IF NOT EXISTS health_records (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  record_date date NOT NULL,
  record_type text NOT NULL,
  weight float,
  height float,
  bmi float,
  blood_pressure_systolic integer,
  blood_pressure_diastolic integer,
  heart_rate integer,
  blood_sugar float,
  body_fat float,
  sleep_hours float,
  steps integer,
  food_name text,
  meal_type text,
  food_amount float,
  exercise_type text,
  duration integer,
  intensity text,
  calories_burned float,
  distance float,
  water_amount integer,
  water_type text,
  intake_time time,
  medication_name text,
  dosage float,
  dosage_unit text,
  frequency text,
  time_taken time,
  with_food boolean,
  effectiveness integer,
  side_effects text,
  notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create foods table
CREATE TABLE IF NOT EXISTS foods (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  category text,
  calories float,
  protein float,
  fat float,
  carbohydrate float,
  fiber float,
  sugar float,
  sodium float,
  serving_size float
);

-- Create exercise_types table
CREATE TABLE IF NOT EXISTS exercise_types (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text UNIQUE NOT NULL,
  category text,
  calories_per_hour float,
  description text,
  benefits text
);

-- Create medication_types table
CREATE TABLE IF NOT EXISTS medication_types (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text UNIQUE NOT NULL,
  category text,
  description text,
  common_dosage text,
  side_effects text,
  precautions text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create health_goals table
CREATE TABLE IF NOT EXISTS health_goals (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  goal_type text NOT NULL,
  target_value float NOT NULL,
  current_value float,
  start_date date NOT NULL,
  end_date date,
  status text NOT NULL,
  notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create health_reports table
CREATE TABLE IF NOT EXISTS health_reports (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  title text NOT NULL,
  report_type text NOT NULL,
  start_date date NOT NULL,
  end_date date NOT NULL,
  health_summary text,
  diet_summary text,
  exercise_summary text,
  medication_summary text,
  recommendations text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create reminders table
CREATE TABLE IF NOT EXISTS reminders (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  reminder_type text NOT NULL,
  title text NOT NULL,
  description text,
  reminder_date date NOT NULL,
  reminder_time time NOT NULL,
  recurrence text,
  is_completed boolean DEFAULT false,
  notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create shares table
CREATE TABLE IF NOT EXISTS shares (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  content_type text NOT NULL,
  content_id uuid NOT NULL,
  description text,
  visibility text DEFAULT 'public',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create likes table
CREATE TABLE IF NOT EXISTS likes (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  share_id uuid REFERENCES shares(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, share_id)
);

-- Create comments table
CREATE TABLE IF NOT EXISTS comments (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  share_id uuid REFERENCES shares(id) ON DELETE CASCADE,
  content text NOT NULL,
  parent_id uuid REFERENCES comments(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE foods ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercise_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Users can read and update their own data
CREATE POLICY "Users can read own data" ON users
  FOR SELECT TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
  FOR UPDATE TO authenticated
  USING (auth.uid() = id);

-- Health records policies
CREATE POLICY "Users can CRUD own health records" ON health_records
  FOR ALL TO authenticated
  USING (auth.uid() = user_id);

-- Foods are readable by all authenticated users
CREATE POLICY "Foods are readable by authenticated users" ON foods
  FOR SELECT TO authenticated
  USING (true);

-- Exercise types are readable by all authenticated users
CREATE POLICY "Exercise types are readable by authenticated users" ON exercise_types
  FOR SELECT TO authenticated
  USING (true);

-- Medication types are readable by all authenticated users
CREATE POLICY "Medication types are readable by authenticated users" ON medication_types
  FOR SELECT TO authenticated
  USING (true);

-- Health goals policies
CREATE POLICY "Users can CRUD own health goals" ON health_goals
  FOR ALL TO authenticated
  USING (auth.uid() = user_id);

-- Health reports policies
CREATE POLICY "Users can CRUD own health reports" ON health_reports
  FOR ALL TO authenticated
  USING (auth.uid() = user_id);

-- Reminders policies
CREATE POLICY "Users can CRUD own reminders" ON reminders
  FOR ALL TO authenticated
  USING (auth.uid() = user_id);

-- Shares policies
CREATE POLICY "Users can CRUD own shares" ON shares
  FOR ALL TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can read public shares" ON shares
  FOR SELECT TO authenticated
  USING (visibility = 'public' OR auth.uid() = user_id);

-- Likes policies
CREATE POLICY "Users can manage own likes" ON likes
  FOR ALL TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can read likes on visible shares" ON likes
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM shares s
      WHERE s.id = share_id
      AND (s.visibility = 'public' OR s.user_id = auth.uid())
    )
  );

-- Comments policies
CREATE POLICY "Users can CRUD own comments" ON comments
  FOR ALL TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can read comments on visible shares" ON comments
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM shares s
      WHERE s.id = share_id
      AND (s.visibility = 'public' OR s.user_id = auth.uid())
    )
  );