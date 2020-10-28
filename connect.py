#!/usr/bin/env python3

# import libraries
import psycopg2
import os

# import additional files
import config

def db_connect():
	# establish database connection
	global db_conn
	db_conn = psycopg2.connect(config.DB_URL)
	global db_crsr
	db_crsr = db_conn.cursor()
	print('database connected')

	# print connection properties
	print('postgres connection info:')
	print(db_conn.get_dsn_parameters())

	db_crsr.execute("""SELECT COUNT(*) FROM awarded_submissions""")
	result = db_crsr.fetchone()
	print('awarded_submissions: ' + str(result[0]))

	db_crsr.execute("""SELECT COUNT(*) FROM awarded_comments""")
	result = db_crsr.fetchone()
	print('awarded_comments: ' + str(result[0]))

	return True

db_connect()

# TABLE awarded_submissions
# db_id SERIAL PRIMARY KEY
# reddit_id VARCHAR(7) NOT NULL UNIQUE
# reply_id VARCHAR(7) DEFAULT NULL
# full_link VARCHAR(200) DEFAULT NULL
# op_username VARCHAR(30) DEFAULT NULL
# subreddit_name VARCHAR(30) DEFAULT NULL
# coin_price NUMERIC(12) DEFAULT NULL
# cash_price NUMERIC(10,2) DEFAULT NULL
# coin_reward VARCHAR(12) DEFAULT NULL
# premium_reward VARCHAR(10) DEFAULT NULL
# updated_time NUMERIC(10) DEFAULT NULL

# TABLE awarded_comments
# db_id SERIAL PRIMARY KEY
# reddit_id VARCHAR(30) NOT NULL
# reply_id VARCHAR(7) DEFAULT NULL
# full_link VARCHAR(200) DEFAULT NULL
# op_username VARCHAR(30) DEFAULT NULL
# subreddit_name VARCHAR(30) DEFAULT NULL
# coin_price NUMERIC(12) DEFAULT NULL
# cash_price NUMERIC(10,2) DEFAULT NULL
# coin_reward VARCHAR(12) DEFAULT NULL
# premium_reward VARCHAR(10) DEFAULT NULL
# updated_time NUMERIC(10) DEFAULT NULL