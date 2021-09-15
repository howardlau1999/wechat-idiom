# encoding:utf-8
import itchat,time
from itchat.content import *
from threading import Timer

import pypinyin
from pypinyin import pinyin
import random

data = []
pys = {}
words = []
exp = {}

def get_pinyin(word):
	py = pinyin(word, style = pypinyin.NORMAL)
	ret = []
	for i in py:
		ret.append(i[0])
	return ret

def get_all_starts_with(letter):
	result = []
	target_pinyin = get_pinyin(letter)
	target_pinyin_first = target_pinyin[-1]
	for i in words:
		data_pinyin = pys[i]
		data_pinyin_first = data_pinyin[0]
		if data_pinyin_first == target_pinyin_first:
			result.append([i, "meaningless"])
	return result


def get_random_result(data):
	return random.choice(data)

def format_data(data):
	return "[%s] : [%s]" % (data[0], data[1])

def init():
	with open("exp.txt", "r", encoding = "utf-8") as f:
		counter = 0
		for line in f:
			line = line.replace('\n', '')
			arr = line.split('|')
			if len(arr) != 2:
				continue
			exp[arr[0]] = arr[1]
		f.close()
	with open("idiom.txt", "r", encoding = "UTF-8") as f:
		counter = 0
		for line in f:
			line = line.replace('\n', '')
			words.append(line)
			pys[line] = get_pinyin(line)
			counter += 1
		print("[+] Init finished! [%d] words." % (counter))

def guess(word):
	all_data_matched = get_all_starts_with(word)
	if len(all_data_matched) == 0:
		return None
	result_data = get_random_result(all_data_matched)
	return result_data[0]

def check(word):
	for w in words:
		if word == w:
			return True
	return False

def check_py(a, b):
	pya = get_pinyin(a)[-1]
	pyb = get_pinyin(b)[0]
	return pya == pyb

init()

isPlaying = {};
retryTimes = {};
gameHistory = {};
lastActicity = {};
score = {};

def check_dead():
	for i in lastActicity:
		if isPlaying[i] is True:
			if time.time() - lastActicity[i] >= 120:
				game_end(i)
	t = Timer(1, check_dead)
	t.start()

def game_end(username):
	if isPlaying[username] is True:
			isPlaying[username] = False
			print("End game for user %s" % username)
			itchat.send(u'接龙结束！\n本次接龙长度： %d 个成语！\n接龙得分：%d' % (len(gameHistory[username]), score[username]), username)

@itchat.msg_register(TEXT, isFriendChat=True, isGroupChat=True)
def simple_reply(msg):
	isPlaying.setdefault(msg['FromUserName'], False)
	retryTimes.setdefault(msg['FromUserName'], 8)
	lastActicity.setdefault(msg['FromUserName'], time.time())
	lastActicity[msg['FromUserName']] = time.time()
	if msg['Text'] == u'不玩了':
		game_end(msg['FromUserName'])
	if msg['Text'] == u'解释一下':
		if isPlaying[msg['FromUserName']] is True:
			py = pinyin(gameHistory[msg['FromUserName']][-1])
			pystr = ''
			w = gameHistory[msg['FromUserName']][-1]
			for i in py:
				pystr += (i[0] + ' ')
			itchat.send(u"【成语】%s\n【拼音】%s\n【释义】%s" %(w, pystr, exp.get(w, '抱歉，该成语无解释')), msg['FromUserName'] )
			return
	if isPlaying[msg['FromUserName']] is True:
		if check(msg['Text']):
			if check_py(gameHistory[msg['FromUserName']][-1], msg['Text']):
				retryTimes[msg['FromUserName']] = 8;
				gameHistory[msg['FromUserName']].append(msg['Text'])
				reply = guess(msg['Text'])
				if reply is None:
					itchat.send('接不下去了，认输', msg['FromUserName'])
					game_end(msg['FromUserName'])
					return
				score[msg['FromUserName']] += 1
				delta = 1
				if pinyin(gameHistory[msg['FromUserName']][-2])[-1][0] == pinyin(msg['Text'])[0][0]:
					score[msg['FromUserName']] += 2
					delta += 2
				if gameHistory[msg['FromUserName']][-2][-1] == msg['Text'][0]:
					score[msg['FromUserName']] += 3
					delta += 3
				gameHistory[msg['FromUserName']].append(reply)
				print("Sent word %s" % reply)
				itchat.send(reply + " +" + str(delta), msg['FromUserName'])
			else:
				retryTimes[msg['FromUserName']] = retryTimes[msg['FromUserName']] - 1;
				if(retryTimes[msg['FromUserName']]==0):
					game_end(msg['FromUserName'])
					return
				itchat.send(u'首尾不对，请接龙：\n' + gameHistory[msg['FromUserName']][-1] + (u'\n还有 %d 次机会' % retryTimes[msg['FromUserName']]), msg['FromUserName'])
		else:
			retryTimes[msg['FromUserName']] = retryTimes[msg['FromUserName']] - 1;
			if(retryTimes[msg['FromUserName']]==0):
				game_end(msg['FromUserName'])
				return
			itchat.send(u'词库没有这个词，请接龙：\n' + gameHistory[msg['FromUserName']][-1] + (u'\n还有 %d 次机会' % retryTimes[msg['FromUserName']]), msg['FromUserName'])
	
	if msg['Text'] == u'成语接龙':
		if isPlaying[msg['FromUserName']] is False:
			print("Begin game for user %s" % msg['FromUserName'])
			retryTimes[msg['FromUserName']] = 8;
			isPlaying[msg['FromUserName']] = True
			gameHistory[msg['FromUserName']] = []
			first = get_random_result(words)
			gameHistory[msg['FromUserName']].append(first)
			score[msg['FromUserName']] = 0
			print("Sent word %s" % first)
			itchat.send(u'开始接龙！\n游戏规则：\n1、只要拼音相同即可接\n2、回复“不玩了”结束游戏\n3、回复“解释一下”获取成语拼音以及解释', msg['FromUserName'])
			itchat.send(first, msg['FromUserName'])
			

check_dead()
itchat.auto_login(hotReload=True, enableCmdQR = 2)
itchat.run()
itchat.dump_login_status()
