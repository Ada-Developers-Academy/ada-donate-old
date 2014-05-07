drop table if exists donors;
create table donors (
  id integer primary key autoincrement,
  name text,
  amount integer not null
);