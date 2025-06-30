-- Drop tables if they exist (with cascade constraints to avoid dependency issues)
begin
   execute immediate 'DROP TABLE reports CASCADE CONSTRAINTS';
exception
   when others then
      null;
end;
/

begin
   execute immediate 'DROP TABLE appointments CASCADE CONSTRAINTS';
exception
   when others then
      null;
end;
/

begin
   execute immediate 'DROP TABLE doctors CASCADE CONSTRAINTS';
exception
   when others then
      null;
end;
/

begin
   execute immediate 'DROP TABLE patients CASCADE CONSTRAINTS';
exception
   when others then
      null;
end;
/

-- Drop sequences if they exist
begin
   execute immediate 'DROP SEQUENCE doctor_seq';
exception
   when others then
      null;
end;
/

begin
   execute immediate 'DROP SEQUENCE patient_seq';
exception
   when others then
      null;
end;
/

begin
   execute immediate 'DROP SEQUENCE appointment_seq';
exception
   when others then
      null;
end;
/

begin
   execute immediate 'DROP SEQUENCE report_seq';
exception
   when others then
      null;
end;
/

-- Create doctors table
create table doctors (
   id             number primary key,
   name           varchar2(100) not null,
   email          varchar2(100) unique not null,
   password       varchar2(255) not null, -- Increased length for hashed passwords
   specialization varchar2(100) not null,
   phone          varchar2(15) not null,
   license_number varchar2(50) unique,
   created_at     timestamp default systimestamp,
   last_updated   timestamp default systimestamp
);

-- Create patients table
create table patients (
   id                 number primary key,
   name               varchar2(100) not null,
   email              varchar2(100) unique not null,
   password           varchar2(255) not null,
   phone              varchar2(15) not null,
   dob                date,
   gender             varchar2(10),
   blood_group        varchar2(5),
   created_at         timestamp default systimestamp,
   last_updated       timestamp default systimestamp,
   blood_type         varchar2(10),
   allergies          varchar2(200),
   medical_history    varchar2(1000),
   medications        varchar2(1000),
   chronic_conditions varchar2(100)
);

-- Create a sequence for patient IDs if not exists
create sequence patient_seq start with 1 increment by 1 nocache nocycle;
-- Create appointments table
create table appointments (
   id               number primary key,
   doctor_id        number not null,
   patient_id       number not null,
   appointment_date timestamp not null,
   end_time         timestamp,
   status           varchar2(20) default 'SCHEDULED', -- SCHEDULED, CONFIRMED, COMPLETED, CANCELLED, NOSHOW
   reason           varchar2(200),
   notes            clob,
   diagnosis        clob,
   created_at       timestamp default systimestamp,
   last_updated     timestamp default systimestamp,
   constraint fk_appt_doctor foreign key ( doctor_id )
      references doctors ( id )
         on delete cascade,
   constraint fk_appt_patient foreign key ( patient_id )
      references patients ( id )
         on delete cascade
);



-- Create sequences for auto-incrementing IDs
create sequence doctor_seq start with 1 increment by 1 nocache nocycle;
create sequence patient_seq start with 1 increment by 1 nocache nocycle;
create sequence appointment_seq start with 1 increment by 1 nocache nocycle;
create sequence report_seq start with 1 increment by 1 nocache nocycle;

-- Add indexes to improve query performance
create index idx_doctor_specialization on
   doctors (
      specialization
   );
create index idx_doctor_email on
   doctors (
      email
   );
create index idx_patient_email on
   patients (
      email
   );
create index idx_appointment_date on
   appointments (
      appointment_date
   );
create index idx_appointment_doctor on
   appointments (
      doctor_id
   );
create index idx_appointment_patient on
   appointments (
      patient_id
   );
create index idx_appointment_status on
   appointments (
      status
   );
create index idx_report_appointment on
   reports (
      appointment_id
   );
create index idx_report_patient on
   reports (
      patient_id
   );
create index idx_report_doctor on
   reports (
      doctor_id
   );

-- Create triggers for automatic timestamps
create or replace trigger doctors_update_timestamp before
   update on doctors
   for each row
begin
   :new.last_updated := systimestamp;
end;
/

create or replace trigger patients_update_timestamp before
   update on patients
   for each row
begin
   :new.last_updated := systimestamp;
end;
/

create or replace trigger appointments_update_timestamp before
   update on appointments
   for each row
begin
   :new.last_updated := systimestamp;
end;
/

create or replace trigger reports_update_timestamp before
   update on reports
   for each row
begin
   :new.last_updated := systimestamp;
end;
/

-- Insert sample data
insert into doctors (
   id,
   name,
   email,
   password,
   specialization,
   phone,
   license_number
) values ( doctor_seq.nextval,
           'Dr. John Smith',
           'john.smith@example.com',
           '$2a$10$xJwL5v5Jz5U5Z5b5X5b5Oe', -- Sample hashed password
           'Cardiology',
           '555-123-4567',
           'MD123456' );

insert into doctors (
   id,
   name,
   email,
   password,
   specialization,
   phone,
   license_number
) values ( doctor_seq.nextval,
           'Dr. Sarah Johnson',
           'sarah.johnson@example.com',
           '$2a$10$xJwL5v5Jz5U5Z5b5X5b5Oe',
           'Pediatrics',
           '555-234-5678',
           'MD234567' );

insert into patients (
   id,
   name,
   email,
   password,
   phone,
   dob,
   gender,
   blood_group
) values ( patient_seq.nextval,
           'Michael Brown',
           'michael.brown@example.com',
           '$2a$10$xJwL5v5Jz5U5Z5b5X5b5Oe',
           '555-345-6789',
           to_date('1985-05-15','YYYY-MM-DD'),
           'Male',
           'O+' );

insert into patients (
   id,
   name,
   email,
   password,
   phone,
   dob,
   gender,
   blood_group
) values ( patient_seq.nextval,
           'Emily Davis',
           'emily.davis@example.com',
           '$2a$10$xJwL5v5Jz5U5Z5b5X5b5Oe',
           '555-456-7890',
           to_date('1990-08-22','YYYY-MM-DD'),
           'Female',
           'A-' );

-- Insert appointments (one week from now)
insert into appointments (
   id,
   doctor_id,
   patient_id,
   appointment_date,
   end_time,
   status,
   reason
) values ( appointment_seq.nextval,
           1,
           1,
           systimestamp + interval '7' day,
           systimestamp + interval '7' day + interval '30' minute,
           'SCHEDULED',
           'Annual cardiac checkup' );

insert into appointments (
   id,
   doctor_id,
   patient_id,
   appointment_date,
   end_time,
   status,
   reason
) values ( appointment_seq.nextval,
           2,
           2,
           systimestamp + interval '8' day,
           systimestamp + interval '8' day + interval '45' minute,
           'CONFIRMED',
           'Child vaccination' );



commit;