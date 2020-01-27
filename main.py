#!/usr/bin/env python3

# import libraries
import praw
import time
from unidecode import unidecode
from math import ceil

# import additional files
import config

def initialize_reddit():
	reddit = praw.Reddit(client_id=config.R_CLIENT_ID,
		client_secret=config.R_CLIENT_SECRET,
		password=config.R_PASSWORD,
		username=config.R_USERNAME,
		user_agent=config.R_USER_AGENT)
	print('reddit object initialized')
	return reddit

def format_time(number, letter):
	if letter == 'm':
		word = 'minute'
	elif letter == 'h':
		word = 'hour'
	elif letter == 'd':
		word = 'day'

	if number == 1:
		number_string = f'1 {word}'
	elif number > 1:
		number_string = f'{number} {word}s'
	else:
		number_string = ''

	return number_string

reddit = initialize_reddit()

mentions = reddit.inbox.mentions
# iterate through all mentions, indefinitely
for mention in praw.models.util.stream_generator(mentions, skip_existing=True):
	# mark any new mention as read
	reddit.inbox.mark_read([mention])
	# parse the mention so that we can search for keywords
	mention_body = unidecode(mention.body.casefold().strip())

	# check to see if the root submission has any awards
	root_submission = mention.submission
	time_since_submission = time.time() - root_submission.created_utc
	m, s = divmod(time_since_submission, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	h_string = format_time(int(h), 'h')
	d_string = format_time(int(d), 'd')
	if d_string == '' or h_string == '':
		time_string = f'{d_string}{h_string}'
		if time_string == '':
			time_string = format_time(int(m), 'm')
	else:
		time_string = f'{d_string}, {h_string}'

	# make sure there are awards on the given root submission
	if len(root_submission.all_awardings) > 0:
		coin_total = 0
		for award in root_submission.all_awardings:
			coin_total += int(award['coin_price']) * int(award['count'])

		cash_total = ceil(coin_total / config.COIN_QUANT) * config.QUANT_PRICE
		response = f'The estimated price of awards on this submission is ${cash_total} ({time_string} since submission).'
	else:
		response = f'As of {time_string} since this submission, it doesn\'t look like it has any awards. Feel free to try again later!'

	response_tail = '\n\n^^^Please ^^^DM ^^^me ^^^if ^^^there ^^^is ^^^a ^^^problem! ^^^A ^^^human ^^^will ^^^receive ^^^direct ^^^messages.'
	response += response_tail
	# send the given response
	mention.reply(response)
	print('responded to a mention')