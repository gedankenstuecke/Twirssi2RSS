#!/usr/bin/python
import re
import datetime
import urllib
from operator import itemgetter
import PyRSS2Gen																# download at http://www.dalkescientific.com/Python/PyRSS2Gen.html
import pickle
from glob import glob

# This script reads the logfile written by twirssi, fetches all the links posted at the current day and republishes the 
# links posted most as a simple RSS-feed. To enable twirssi-logging use "/set twirssi_logfile_path" in irssi.  

# enter the location of the logfile, where the backup shall be stored and where the feed shall be published
logfile = "/home/bastian/irclogs/twitter"
backup = "/home/bastian/twitter.bak"
feed_output = "/var/www/toplinks.xml"

def logload(infile):															# open twirssi-logfile, location is specified in line 
	log = open(infile,"r")
	tweets = log.readlines()
	log.close()
	
	return tweets

def datefinder(tweets):															# get tweets which include links for the current day
	new_tweets = []
	expression = re.compile("(http|https)\S*\s")
	
	today = datetime.date(2011,2,27).ctime()
	#today = datetime.date.today().ctime()
	today = today[:11]+today[20:24]
	
	for i in tweets:
		date = i[:11]+i[20:24]
		if date == today:
			result = expression.search(i)
			if result != None:
				new_tweets.append(result.group(0).replace("\n",""))
				
	return new_tweets

def long_url(links):															# unshorten links
	long_links = []
	done_links = {}
	for link in links:
		if done_links.has_key(link):											# check if this shortlink was already checked (don't stress the longurl-API!)
			long_links.append(done_links[link])
		else:
			url_entry = "http://api.longurl.org/v2/expand?url=" + link			# unshorten link, if not already done
			long_url_return = urllib.urlopen(url_entry)
			for i in long_url_return:
				if i.find("<long-url>") != -1:				
					start = i.find("<long-url><![CDATA[") + 19
					stop = i.find("]]></long-url>")
					print i[start:stop]
					long_links.append(i[start:stop])
					done_links[link] = i[start:stop]		
	return long_links

def url_counter(longlinks):														# count all those links
	url_hash = {}
	out_list = []
	for link in longlinks:
		if url_hash.has_key(link):
			url_hash[link] += 1
		else:
			url_hash[link] = 1
	sorted_urls = sorted(url_hash.iteritems(), key=itemgetter(1))
	sorted_urls.reverse()
	
	for i in sorted_urls:
		item = [i[0],i[1],datetime.datetime.today()]
		out_list.append(item)
	return out_list[:11]

def itemcreator(all_urls):														# create rss-feed-items out of those links
	items = []
	for url in all_urls:
		urlinfo = urllib.urlopen(url[0])
		
		for line in urlinfo:
			if line.find("<title>") != -1:
				start = line.find("<title>") + 7
				stop = line.find("</title>")
				heading = line[start:stop]
		if heading != "":
			item = PyRSS2Gen.RSSItem(title = heading)	
		else:
			item = PyRSS2Gen.RSSItem(title = url[0])
		item.description = "<b>"+heading+"</b> was posted "+str(url[1])+" times."
		item.link = url[0]
		item.pubDate = url[2]
		item.guid = PyRSS2Gen.Guid(url[0])
		items.append(item)
	return items	

def old_import(new_items,backstore):											# import existing rss-items of older days
	if glob(backstore) != []:													
		pikl_in = open(backstore,"rb")
		old_items = pickle.load(pikl_in)
		for i in old_items:
			new_items.append(i)
		pikl_in.close()
		
		pikl_out = open(backstore,"wb")
		old_items = new_items
		pickle.dump(old_items,pikl_out)
		
		pikl_out.close()
		
	else:																		# if this is the first run of the script, create backup-file and store first rss-items
		pikl_out = open(backstore,"wb")
		old_items = new_items
		pickle.dump(old_items,pikl_out)
		
		pikl_out.close()
	return new_items	

def createfeed(feeditems,feed_location):										# create & publish rss-feed						
	rss = PyRSS2Gen.RSS2(
		title = "Top-Links out of the Twitter-timeline of @gedankenstuecke",
		link = "http://gedankenstuecke.de",
		description = "A daily updated list of top tweets posted in the Twitter-timeline of @gedankenstuecke",
		lastBuildDate = datetime.datetime.utcnow(),
		items = feeditems,
		)
		
	rss.write_xml(open(feed_location,"w"))


tweets = logload(logfile)
links = datefinder(tweets)
longlinks = long_url(links)
sorted_urls = url_counter(longlinks)
new_feeditems = itemcreator(sorted_urls)
all_feeditems = old_import(new_feeditems,backup)
createfeed(all_feeditems,feed_output)
