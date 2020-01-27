#!/usr/bin/env python3

# import libraries
import praw
from unidecode import unidecode
from math import ceil
from time import time

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
	if len(root_submission.all_awardings) > 0:
		response = 'Okay, nice'
	# write a response
	response = 'Yep, this works :)'
	mention.reply(response)
	print('responded to a mention')