drop table if exists donors;
create table donors (
  id integer primary key autoincrement,
  name text,
  email text not null,
  success boolean not null,
  stripe_id text not null,
  status text not null,
  message text not null,
  amount integer not null
);