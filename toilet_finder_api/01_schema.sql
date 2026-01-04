DROP TABLE IF EXISTS toilet_strategies CASCADE;
DROP TABLE IF EXISTS toilets CASCADE;
DROP TABLE IF EXISTS line_stations CASCADE;
DROP TABLE IF EXISTS stations CASCADE;
DROP TABLE IF EXISTS lines CASCADE;
DROP TABLE IF EXISTS congestion_reports CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;

CREATE TABLE public.lines (id uuid NOT NULL DEFAULT gen_random_uuid(), name text NOT NULL UNIQUE, color text, max_cars integer DEFAULT 10, PRIMARY KEY (id));
CREATE TABLE public.stations (id uuid NOT NULL DEFAULT gen_random_uuid(), name text NOT NULL UNIQUE, lat double precision, lng double precision, PRIMARY KEY (id));
CREATE TABLE public.line_stations (
        line_id uuid REFERENCES public.lines(id) ON DELETE CASCADE,
        station_id uuid REFERENCES public.stations(id) ON DELETE CASCADE,
        station_order integer,
        dir_1_label text, dir_m1_label text,
        dir_1_next_station_id uuid REFERENCES public.stations(id),
        dir_1_next_next_station_id uuid REFERENCES public.stations(id),
        dir_m1_next_station_id uuid REFERENCES public.stations(id),
        dir_m1_next_next_station_id uuid REFERENCES public.stations(id),
        PRIMARY KEY (line_id, station_id));
CREATE TABLE public.toilets (
        id text NOT NULL PRIMARY KEY,
        station_name text,
        line_name text,
        name text, -- toilet_name
        lat double precision,
        lng double precision,
        floor text,
        wheelchair boolean DEFAULT false,
        baby_chair boolean DEFAULT false,
        ostomate boolean DEFAULT false,
        description text, -- notes
        platform_name text -- CSVにあるplatform_name(場所の詳細など)
        );
CREATE TABLE public.toilet_strategies (
        id uuid NOT NULL DEFAULT gen_random_uuid(), line_name text, station_id uuid REFERENCES public.stations(id) ON DELETE CASCADE,
        direction integer, platform_name text, car_pos double precision, facility_type text, available_time text,
        crowd_level integer, target_toilet_id text REFERENCES public.toilets(id) ON DELETE SET NULL, route_memo text, PRIMARY KEY (id));
CREATE TABLE public.profiles (
        id uuid REFERENCES auth.users ON DELETE CASCADE,
        is_premium boolean DEFAULT false,
        updated_at timestamp with time zone DEFAULT now(),
        PRIMARY KEY (id));
CREATE TABLE public.congestion_reports (
        id uuid NOT NULL DEFAULT gen_random_uuid(),
        toilet_id text REFERENCES public.toilets(id) ON DELETE CASCADE,
        congestion_level integer NOT NULL,
        user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
        reported_at timestamp with time zone DEFAULT now(),
        PRIMARY KEY (id));
ALTER TABLE public.lines DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.stations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.line_stations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.toilets DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.toilet_strategies DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.congestion_reports DISABLE ROW LEVEL SECURITY;