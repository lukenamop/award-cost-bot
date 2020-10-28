#!/usr/bin/env python3

# import libraries
import praw
import prawcore
import time
from time import strftime
from unidecode import unidecode
from math import ceil
from datetime import datetime, timezone
from multiprocessing import Process

# import additional files
import config
import connect
from functions import day_string, second_string
from sql_functions import execute_sql

# PRAW stream of all username mentions
def mention_reply_stream(reddit):
	print('mention_reply_stream started')
	try:
		mentions = reddit.inbox.mentions
		# iterate through all mentions, indefinitely
		for mention in praw.models.util.stream_generator(mentions, skip_existing=True):
			# make sure the mention is actually new
			respond_to_mention = True
			if mention.created_utc < (time.time() - 60 * 30):
				respond_to_mention = False

			if respond_to_mention:
				# mark any new mention as read
				reddit.inbox.mark_read([mention])
				# parse the mention so that we can search for keywords
				mention_body = unidecode(mention.body.casefold().strip())

				# check to see if the root has any awards
				root = mention.parent()
				if isinstance(root, praw.models.Submission):
					root_type = 'submission'
				elif isinstance(root, praw.models.Comment):
					root_type = 'comment'

				# check for an existing record
				original_reply_id = None
				query = f'SELECT cash_price, reply_id FROM awarded_{root_type}s WHERE reddit_id = %s'
				q_args = [root.id]
				execute_sql(query, q_args)
				result = connect.db_crsr.fetchone()
				if result is not None:
					original_reply_id = result[1]

				# make sure there are awards on the given root
				if len(root.all_awardings) > 0:
					# check to see if golds given to this root are legacy
					legacy_gold = False
					if int(root.created_utc) < config.GOLD_LEGACY_TIMESTAMP:
						legacy_gold = True
						print(f'this {root_type} has legacy gold')

					coin_total = 0
					rewarded_premium = 0
					rewarded_coins = 0
					for award in root.all_awardings:
						normal_award = True
						if legacy_gold:
							# only adjust pricing on gold awards
							if award['coin_price'] == 500 and award['days_of_premium'] == 7 and award['coin_reward'] == 100:
								normal_award = False
								coin_total += config.GOLD_LEGACY_QUANT * int(award['count'])
								rewarded_premium += config.GOLD_LEGACY_PREMIUM * int(award['count'])

						if normal_award:
							coin_total += int(award['coin_price']) * int(award['count'])
							rewarded_premium += int(award['days_of_premium']) * int(award['count'])
							rewarded_coins += int(award['coin_reward']) * int(award['count'])

					cash_total = round(((coin_total / config.COIN_QUANT) * config.QUANT_PRICE), 2)
					response = f'Awards on this {root_type} cost {coin_total:,} coins, the estimated cash price of which is ${cash_total:,.2f}.'
					message_response = f'Awards on [this {root_type}](https://reddit.com{root.permalink}) cost {coin_total:,} coins, the estimated cash price of which is ${cash_total:,.2f}.'

					# add a new record or update the existing record
					query = f'INSERT INTO awarded_{root_type}s (reddit_id, full_link, op_username, subreddit_name, coin_price, cash_price, coin_reward, premium_reward, updated_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (reddit_id) DO UPDATE SET full_link = %s, op_username = %s, subreddit_name = %s, coin_price = %s, cash_price = %s, coin_reward = %s, premium_reward = %s, updated_time = %s'
					q_args = [root.id, f'https://reddit.com{root.permalink}', str(root.author), root.subreddit.display_name, int(coin_total), cash_total, rewarded_coins, rewarded_premium, int(time.time()), f'https://reddit.com{root.permalink}', str(root.author), root.subreddit.display_name, int(coin_total), cash_total, rewarded_coins, rewarded_premium, int(time.time())]
					execute_sql(query, q_args)
					connect.db_conn.commit()
					print(f'awarded_{root_type}s database entry added')

					# pull the current root back out of the database with its rank intact
					query = f'WITH cte_cash_price_rank AS (SELECT reddit_id, RANK () OVER (ORDER BY cash_price DESC) cash_price_rank FROM awarded_{root_type}s) SELECT cash_price_rank FROM cte_cash_price_rank WHERE reddit_id = %s'
					q_args = [root.id]
					execute_sql(query, q_args)
					result = connect.db_crsr.fetchone()
					cash_price_rank = 'NULL'
					if result is not None:
						cash_price_rank = result[0]

					# append the root's rank
					response += f' This is the #{cash_price_rank} highest priced {root_type} I have seen.'
					message_response += f' It is the #{cash_price_rank} highest priced {root_type} I have seen.'

					if rewarded_coins > 0 and rewarded_premium > 0:
						response += f'\n\nFrom these awards, the OP has been rewarded with {rewarded_coins:,} coins and {day_string(rewarded_premium)} of Reddit Premium.'
						message_response += f'\n\nFrom those awards, the OP has been rewarded with {rewarded_coins:,} coins and {day_string(rewarded_premium)} of Reddit Premium.'
					elif rewarded_coins > 0:
						response += f'\n\nFrom these awards, the OP has been rewarded with {rewarded_coins:,} coins.'
						message_response += f'\n\nFrom those awards, the OP has been rewarded with {rewarded_coins:,} coins.'
					elif rewarded_premium > 0:
						response += f'\n\nFrom these awards, the OP has been rewarded with {day_string(rewarded_premium)} of Reddit Premium.'
						message_response += f'\n\nFrom those awards, the OP has been rewarded with {day_string(rewarded_premium)} of Reddit Premium.'

				else:
					# if no awards were found, send a default message
					response = f'It doesn\'t look like this {root_type} has any awards. Feel free to try again later!'
					message_response = f'It doesn\'t look like [this {root_type}](https://reddit.com{root.permalink}) has any awards. Feel free to try again later!'

				# add some info about contacting the developer
				response += f'\n\n^^^Please ^^^DM ^^^me ^^^if ^^^there ^^^is ^^^a ^^^problem! ^^^A ^^^human ^^^will ^^^receive ^^^any ^^^direct ^^^messages.'
				message_response += f'\n\n^^^Please ^^^DM ^^^me ^^^if ^^^there ^^^is ^^^a ^^^problem! ^^^A ^^^human ^^^will ^^^receive ^^^any ^^^direct ^^^messages.'

				if root.subreddit.display_name in config.LINK_BL_SUB_IDS:
					# in specific subreddits, don't include any links
					response += f'\n\n^^^View ^^^leaderboards ^^^of ^^^the ^^^highest ^^^priced ^^^submissions ^^^and ^^^comments ^^^on ^^^my ^^^profile!'
				else:
					# in any other subreddit, link directly to the related leaderboard
					if root_type == 'submission':
						response += f'\n\n^^^Highest ^^^priced ^^^submissions: ^^^https://redd.it/{config.SUBMISSION_LB_ID}/'
					elif root_type == 'comment':
						response += f'\n\n^^^Highest ^^^priced ^^^comments: ^^^https://redd.it/{config.COMMENT_LB_ID}/'

				# always link directly to the leaderboard in messages
				if root_type == 'submission':
					message_response += f'\n\n^^^Highest ^^^priced ^^^submissions: ^^^https://redd.it/{config.SUBMISSION_LB_ID}/'
				elif root_type == 'comment':
					message_response += f'\n\n^^^Highest ^^^priced ^^^comments: ^^^https://redd.it/{config.COMMENT_LB_ID}/'

				# double check for an existing record
				if original_reply_id is None:
					query = f'SELECT cash_price, reply_id FROM awarded_{root_type}s WHERE reddit_id = %s'
					q_args = [root.id]
					execute_sql(query, q_args)
					result = connect.db_crsr.fetchone()
					if result is not None:
						original_reply_id = result[1]

				# try to send the response
				if root.subreddit.display_name in config.BANNED_SUB_IDS:
					try:
						mention.author.message('Award Cost Estimate', message_response)
						print('DMed response (banned sub)')
					except:
						print('failed to DM response')
				else:
					make_new_reply = True
					if root.subreddit.display_name not in config.LINK_BL_SUB_IDS:
						if original_reply_id is not None:
							make_new_reply = False
							original_reply = reddit.comment(id=original_reply_id)
							try:
								# edit the original reply
								time_since_string = second_string(time.time() - original_reply.created_utc).replace(' ', ' ^^^')
								original_reply.edit(response + f'\n\n^^^Most ^^^recently ^^^updated ^^^when ^^^this ^^^comment ^^^was ^^^{time_since_string} ^^^old.')
								# DM the author of the new mention
								mention.author.message('Updated Award Cost Estimate', f'Thanks for mentioning me! I just updated my award cost estimate on the {root_type} you were looking at. You can view the updated estimate here: https://reddit.com{original_reply.permalink}\n\n^^^Please ^^^reply ^^^to ^^^this ^^^message ^^^if ^^^there ^^^is ^^^a ^^^problem! ^^^A ^^^human ^^^will ^^^receive ^^^any ^^^direct ^^^messages.')
								print(f'edited a previous response to a mention (sub: {root.subreddit.display_name})')
							except prawcore.exceptions.ServerError:
								print('failed to respond to a mention due to a ServerError')
							except praw.exceptions.APIException:
								print('failed to respond to a mention due to a RateLimit')
							except prawcore.exceptions.Forbidden:
								print('failed to respond to a mention due to being Forbidden')
								try:
									mention.author.message('Award Cost Estimate', message_response)
									print('DMed response')
								except:
									print('failed to DM response')

					if make_new_reply:
						try:
							# reply to the new mention
							reply = mention.reply(response)
							# add the reply's ID to the database
							query = f'UPDATE awarded_{root_type}s SET reply_id = %s WHERE reddit_id = %s AND reply_id IS NULL'
							q_args = [reply.id, root.id]
							execute_sql(query, q_args)
							connect.db_conn.commit()
							print(f'added a new response to a mention (sub: {root.subreddit.display_name})')
						except prawcore.exceptions.ServerError:
							print('failed to respond to a mention due to a ServerError')
						except praw.exceptions.APIException:
							print('failed to respond to a mention due to a RateLimit')
						except prawcore.exceptions.Forbidden:
							print('failed to respond to a mention due to being Forbidden')
							try:
								mention.author.message('Award Cost Estimate', message_response)
								print('DMed response')
							except:
								print('failed to DM response')

				# pull the #10 root from the database
				query = f'WITH cte_cash_price_rank AS (SELECT cash_price, RANK () OVER (ORDER BY cash_price DESC) cash_price_rank FROM awarded_{root_type}s) SELECT cash_price FROM cte_cash_price_rank WHERE cash_price_rank = %s'
				q_args = [config.AWARD_LB_LENGTH]
				execute_sql(query, q_args)
				result = connect.db_crsr.fetchone()

				update_lb = False
				if result is None:
					update_lb = True
				elif cash_total > result[0]:
					update_lb = True
				else:
					print(f'the {root_type} leaderboard was not updated')

				# update the leaderboard message
				if update_lb:
					print(f'updating the {root_type} leaderboard...')
					# build the new leaderboard message
					leaderboard_message = f'This is a list of the top {config.AWARD_LB_LENGTH} most expensive {root_type}s that I have seen on reddit. Want me to check another {root_type}? Just summon me with `u/award-cost-bot` and I\'ll check it out.'
					leaderboard_message += '\n\nIf you need to contact my developer for any reason, just send me a DM!'
					leaderboard_message += f'\n\nRank | {root_type.capitalize()} link | Coin price | Cash price | Coin reward | Premium Reward | Updated\n---|---|---|---|---|---|---'

					# pull the top 10 of whatever we're working with from the database
					query = f'SELECT reddit_id, reply_id, full_link, op_username, subreddit_name, coin_price, cash_price, coin_reward, premium_reward, updated_time, RANK () OVER (ORDER BY cash_price DESC) cash_price_rank FROM awarded_{root_type}s ORDER BY cash_price_rank ASC LIMIT %s'
					q_args = [config.AWARD_LB_LENGTH]
					execute_sql(query, q_args)
					results = connect.db_crsr.fetchall()
					if results is not None:
						for result in results:
							# declare necessary variables
							reddit_id, reply_id, full_link, op_username, subreddit_name, coin_price, cash_price, coin_reward, premium_reward, updated_time, cash_price_rank = result
							full_link = full_link if full_link is not None else 'NULL'
							if full_link == 'NULL':
								if root_type == 'submission':
									full_link = reddit.submission(id=reddit_id).permalink
								elif root_type == 'comment':
									full_link = reddit.comment(id=reddit_id).permalink
							reply_id = reply_id if reply_id is not None else 'NULL'
							op_username = op_username if op_username is not None else 'NULL'
							subreddit_name = subreddit_name if subreddit_name is not None else 'NULL'
							coin_price = f'{int(coin_price):,}' if coin_price is not None else 'NULL'
							cash_price = f'${float(cash_price):,.2f}' if cash_price is not None else 'NULL'
							coin_reward = f'{int(coin_reward):,}' if coin_reward is not None and int(coin_reward) != 0 else 'none'
							premium_reward = day_string(int(premium_reward)) if premium_reward is not None and int(premium_reward) != 0 else 'none'
							updated_time = datetime.fromtimestamp(int(updated_time), timezone.utc).strftime('%d %b %Y') if updated_time is not None else 'NULL'

							# declare cell variables
							link_piece = f'u/{op_username} in r/{subreddit_name}' if op_username != 'None' else f'deleted user in r/{subreddit_name}'
							link_string = f'[{link_piece}]({full_link})' if full_link != 'NULL' else link_piece
							if root_type == 'comment':
								new_full_link = ''
								for link_piece in full_link.split('/')[:-2]:
									new_full_link += f'{link_piece}/'
								full_link = new_full_link
							updated_string = f'[{updated_time}]({full_link}{reply_id}/)' if full_link != 'NULL' and reply_id != 'NULL' else updated_time

							# add a line to the leaderboard
							leaderboard_message += f'\n**#{cash_price_rank}** | {link_string} | {coin_price} | {cash_price} | {coin_reward} | {premium_reward} | {updated_string}'

					# update the leaderboard
					if root_type == 'submission':
						submission_lb = reddit.submission(id=config.SUBMISSION_LB_ID)
						submission_lb.edit(leaderboard_message)
					elif root_type == 'comment':
						comment_lb = reddit.submission(id=config.COMMENT_LB_ID)
						comment_lb.edit(leaderboard_message)

					print(f'updated the {root_type} leaderboard')

	except prawcore.exceptions.ServerError:
		print(f'mention_reply_stream crashed due to a ServerError, sleeping for {config.CRASH_SLEEP_LENGTH} seconds and then restarting')
		time.sleep(config.CRASH_SLEEP_LENGTH)
		mention_reply_stream(reddit)


##### START THE BOT #####

# initialize a reddit object
reddit = praw.Reddit(client_id=config.R_CLIENT_ID,
	client_secret=config.R_CLIENT_SECRET,
	password=config.R_PASSWORD,
	username=config.R_USERNAME,
	user_agent=config.R_USER_AGENT)
reddit.validate_on_submit = True
print('u/award-cost-bot reddit object initialized')

# start the reply stream process
mention_reply_stream_process = Process(target=mention_reply_stream, args=(reddit,))
mention_reply_stream_process.start()