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
	
	def join (self, *(args):
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
def get_gallery_info():
	gallery_id = input ("갤러리 ID를 입력하세요(ex: pumpitup): ")
	while (check_gallery_id (gallery_id) == False):
		print ("잘못된 ID입니다.")
		gallery_id = input ("갤러리 ID를 입력하세요(ex: pumpitup): ")
	
	start_num = int(input ("첫 글번호를 입력하세요: "))
	end_num = int(input ("마지막 글번호를 입력하세요: "))
	
	return gallery_id, start_num, end_num

#
# main function.
#
def main():
	gallery_id, start_num, end_num = get_gallery_info ()

main()
