#
# DCinside Gallery Trash Ranking Calculator
# Author: YSYS
#

import requests
from bs4 import BeautifulSoup
import operator
import time
import re
import os
import threading
from threading import Thread

NUM_THREAD = 16

#
# thread that has return value.
# 
class ThreadWithReturn (Thread):
	def __init__ (self, group=None, target=None, name=None, args=(), kwargs={}):
		Thread.__init__ (self, group, name, args, kwargs)
		self._return = None

	def run (self):
		if self._target is not None:
			self._return = self._target (*self._args, **self._kwargs)
	
	def join (self, *args):
		Thread.join (self, *args)
		return self._return

#
# creates HTML request for given url.
# @param url(str)	url for request
# @return(str)		requested data
#
def request (url):
	header = {
		'Accept': 'text/html, application/xhtml+xml, application/xml;q=0.9',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'gall.dcinside.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0;Win64;x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }
	
	return requests.get (url, headers=header)

#
# verifies the gallery name.
# @param gallery_id(str)	gallery id
# @return(bool)				True if valid, False if not
#
def check_gallery_id (gallery_id):
	recept = request ("http://gall.dcinside.com/board/lists/?id=%s" % gallery_id)
	print (recept.text)
	soup = BeautifulSoup (recept.text, "html.parser")
	meta_data = soup.find_all ("meta", {"name": "title"})

	comp = re.findall ("\"(.*갤러리)", str(meta_data))
	if len(comp) <= 0:
		return False

	print ("갤러리명: " + comp[0]) # print the gallery's name to user
	return True

#
# get the gallery information from user.
# @return(str, int, int)		gallery id, start number, end number
#
def get_gallery_info ():
	gallery_id = input ("갤러리 ID를 입력하세요(ex: pumpitup): ")
	while (check_gallery_id (gallery_id) == False):
		print ("잘못된 ID입니다.")
		gallery_id = input ("갤러리 ID를 입력하세요(ex: pumpitup): ")
	
	start_num = int(input ("첫 글번호를 입력하세요: "))
	end_num = int(input ("마지막 글번호를 입력하세요: "))
	
	return gallery_id, start_num, end_num

#
# per-thread function of collect_gallery_data.
# @param gallery_id(str)			id of gallery
# @param start_num(int)				starting post number
# @param end_num(int)				ending post number
# @return fixed_user_dict(dict)		(fixed user id) : (number of posts)
# @return user_dict(dict)			(non-fixed user name) : (number of posts)
# @return fixed_user_names(dict)	(fixed user id) : [fixed user's names](list)
#
def collect_gallery_data_per_thread (gallery_id, start_num, end_num):
	fixed_user_dict = dict ()
	user_dict = dict ()
	fixed_user_names = dict ()
	
	for num in range (start_num, end_num + 1):
		recept = request ("http://gall.dcinside.com/board/view/?id=%s&no=%d" % (gallery_id, num))
		soup = BeautifulSoup(recept.text, "html.parser")
		
		# parse through text, find the author
		author = soup.find ('td', {'class': "gall_writer ub-writer"})
		try:
			name = author.attrs['data-nick']
			uid = author.attrs['data-uid']
			ip = author.attrs['data-ip']
		except:
			name = None

		if name is not None:
			if uid is None or uid == '': # non-fixed user: just add 1 to user_dict
				if name in user_dict.keys ():
					user_dict[name] += 1
				else:
					user_dict[name] = 1
			else: # fixed id: add 1 to uid, add new name to user_names if not exists.
				if uid in fixed_user_dict.keys ():
					fixed_user_dict[uid] += 1
					if name not in fixed_user_names[uid]:
						fixed_user_names.append (name)
				else:
					fixed_user_dict[uid] = 1
					fixed_user_names = [name]

		# TODO parse through text, find the reply author

	return fixed_user_dict, user_dict, fixed_user_names

#
# merge 2 dictionaries.
# @param dict1, dict2(dict)			dictionaries to be merged
# @return (dict)					merged dictionary
#
def merge_dict (dict1, dict2):
	merged_dict = dict1

	for key in dict2.keys ():
		if key in merged_dict.keys ():
			merged_dict[key] = merged_dict[key] + dict2[key]
		else:
			merged_dict[key] = dict2[key]
	
	return merged_dict

#
# collect gallery's data.
# @param gallery_id(str)			id of gallery
# @param start_num(int)				starting post number
# @param end_num(int)				ending post number
# @return fixed_user_dict(dict)		(fixed user id) : (number of posts)
# @return user_dict(dict)			(non-fixed user name) : (number of posts)
# @return fixed_user_names(dict)	(fixed user id) : [fixed user's names](list)
#
def collect_gallery_data (gallery_id, start_num, end_num):
	fixed_user_dict = dict()
	user_dict = dict()
	fixed_user_names = dict()

	# get number of posts per thread.
	num_posts = end_num - start_num + 1
	posts_per_thread = num_posts / NUM_THREADS
	
	# create threads.
	thread_list = []
	post_num = start_num
	for i in range (NUM_THREADS - 1):
		thread_list.append (ThreadWithReturn \
				(target=collect_gallery_data_per_thread, args=(gallery_id, post_num, post_num + posts_per_thread - 1)))
		post_num += posts_per_thread

	# add the last thread with exact last post number.
	thread_list.append (ThreadWithReturn (target=collect_gallery_data_per_thread, \
				args=(gallery_id, post_num, end_num)))

	# wait threads, get results.
	for thread in thread_list:
		ret = thread.join ()
		fixed_user_dict = merge_dict (fixed_user_dict, ret[0])
		user_dict = merge_dict (user_dict, ret[1])
		fixed_user_names = merge_dict (fixed_user_names, ret[2])

	return fixed_user_dict, user_dict, fixed_user_names

#
# match name with fixed id.
# @param fixed_user_dict(dict)		(fixed user id) : (number of posts)
# @param fixed_user_names(dict)		(fixed user id) : [fixed user's names](list)
# @return(dict)						(fixed user names & id) : (number of posts)
#
def match_names (fixed_user_dict, fixed_user_names):
	for uid in fixed_user_dict.keys ():
		# create new key : 'nick1, nick2, ..., nickn (uid)'
		names = fixed_user_names[uid]
		new_key = ', '.join (names) + ' (%s)' % (uid)
		
		# replace uid into new key
		fixed_user_dict[new_key] = fixed_user_dict.pop (uid)

	return fixed_user_dict


#
# prints the result of calculator.
# @param fixed_user_dict(dict)		(fixed user names & id) : (number of posts)
# @param user_dict(dict)			(non-fixed user name) : (number of posts)
#
def print_result (fixed_user_dict, user_dict):
	# now we may assume that fixed user dict's key dont match with user_dict's.
	# so, we will just merge dictionary and sort altogether.
	for key in fixed_user_dict.keys ():
		user_dict[key] = fixed_user_dict[key]
	
	# sort the dictionary in the reverse order of value.
	sorted_dict = sorted (user_dict.items (), key = operator.itemgetter(1))
	sorted_dict.reverse ()

	# print the result.
	current_rank = 0
	current_value = 0
	for i in range(len(sorted_dict)):
		if current_value == 0 or current_value > nick_list[i][1]:
			current_rank += 1
			current_value = nick_list[i][1]
			print ("%d등: %d" % (current_rank, current_value))
		print (nick_list[i][0])

#
# main function.
#
def main ():
	gallery_id, start_num, end_num = get_gallery_info ()
	print ("집계 중... 다소 시간이 오래 걸릴 수 있습니다.")
	fixed_user_dict, user_dict, fixed_user_names = collect_gallery_data_per_thread (gallery_id, start_num, end_num)
	fixed_user_dict = match_names (fixed_user_dict, fixed_user_names)
	print_result (fixed_user_dict, user_dict)

main()
