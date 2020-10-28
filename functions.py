#!/usr/bin/env python3

# function to translate days into years/months/days
def day_string(days):
	y, d = divmod(days, 365)
	mt, d = divmod(d, 91)
	m, d = divmod(d, 31)
	m += mt * 3
	final_string = ''
	if y > 0:
		final_string += f'{int(y)}y, '
	if m > 0:
		final_string += f'{int(m)}m, '
	if d > 0:
		final_string += f'{int(d)}d'
	return final_string.rstrip(', ')

# function to translate seconds into months/days/hours/minutes
def second_string(seconds):
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	if d > 0:
		return f'{int(d)}d'
	elif h > 0:
		return f'{int(h)}h'
	elif m > 0:
		return f'{int(m)}m'
	return '< 1m'