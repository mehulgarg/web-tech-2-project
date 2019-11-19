\c invest
drop table user_stocks;
drop table user_mutual_funds;
drop table user_loan;
drop table user_details;
create table user_details(user_id serial primary key,firstname varchar, lastname varchar, username varchar, email varchar, password varchar);

CREATE TABLE user_loan (
	user_id integer,
	loan_type varchar(50),
	loan_amount numeric,
	start_date date,
	tenure numeric(2,0),
	loan_balance numeric,
	interest_paid numeric,
	principal_paid numeric,
	EMIs_to_pay numeric,
	bank_name varchar(50),
	foreign key(user_id) references user_details(user_id),
	primary key(user_id,start_date,bank_name)
);
CREATE TABLE user_stocks (
    user_id integer,
    company_id varchar(100),
    timestamp_d date not null,
    buying_price numeric not null,
    quantity numeric not null,
    foreign key(user_id) references user_details(user_id),
    foreign key(company_id) references nse_stocks(company_id),
    primary key(user_id,company_id,timestamp_d)
);

CREATE TABLE user_mutual_funds (
	user_id integer,
	fund_code varchar(20),
	timestamp_d date,
	buying_price numeric,
	quantity numeric,
	foreign key(user_id) references user_details(user_id),
	foreign key(fund_code) references mutual_funds(fund_code),
    primary key(user_id, fund_code,timestamp_d)
);
