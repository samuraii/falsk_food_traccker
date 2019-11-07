create table log_date (
    id integer primary key autoincrement,
    entry_data date not null,
    pretty_format varchar not null,
    timestamp datetime default CURRENT_TIMESTAMP
);

create table food (
    id integer primary key autoincrement,
    name text not null,
    protein integer not null,
    carbohydrates integer not null,
    fat integer not null,
    calories integer not null,
    timestamp datetime default CURRENT_TIMESTAMP
);

create table food_date (
    id integer primary key autoincrement,
    food_id integer not null,
    log_date date not null,
    timestamp datetime default CURRENT_TIMESTAMP
);
