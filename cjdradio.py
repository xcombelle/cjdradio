#!/usr/bin/env python


from time import sleep 

import random

from datetime import datetime
try: 
	from pytz import timezone
except:
	print ("Error importing pytz ! Try \"pip install pytz\"")
	exit(0)

import sys
import os


try:
	from tinytag import TinyTag
except:
	print ("Error importing TinyTag ! Try \"pip install tinytag\"")
	exit(0)
	
try:
	if len(sys.argv)==1: 
		import vlc
except:
	print ("Error importing python-vlc ! Try \"pip install python-vlc\"")
if len(sys.argv)==1: 
	import gi
	gi.require_version('Gtk', '3.0')
	from gi.repository import Gtk	

from os.path import expanduser

from threading import Thread

import urllib.request

import requests


from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import socket
def banner_daemon(g): 
	while True:
		if len(g.peers)>0:	
			for sta in g.peers:
				try: 
					OcsadURLRetriever.retrieveURL("http://["+sta+"]:55227/ping")
				except: 
					g.bannedStations.append(sta)
				finally:
					sleep (25)
		else:
			sleep(50)
class Cjdradio:
	g = None;
	h = None;
	def __init__(self):
		builder = None

		
		self.gladefile = "cjdradio.glade"
		
		builder = None
		if len(sys.argv)==1:
			builder = Gtk.Builder()
			builder.add_from_file("cjdradio.glade")
			builder.get_object("cjdradio_main_window").show_all()
		
		global g
		
		g = Gateway();
		g.set_builder(builder);
		g.load_settings_from_disk();

		h = Handler(builder, g)
		
		if len(sys.argv)==1:

			builder.connect_signals(h)
		
		
			builder.get_object("cjdradio_main_window").connect("destroy", Gtk.main_quit)
		
	def getGateway(self):
		return g


class Gateway:

	radio = None

	shared_dir = ''

	scan = None
	
	ID = 'Another random'
	
	webserver_thread = None
	bannerdaemon_thread = None
	bannedStations = []
	settings_ip6addr = "::"
	webserver = None
	
	processedPeers=[]
	peers = []
	
	h = None;

	def set_processedPeers(self, peerList):
		self.processedPeers=peerList
	def get_processedPeers(self):
		return self.processedPeers
	def set_peers(self, peerList):
		self.peers=peerList
	def get_peers(self):
		return self.peers



	def set_webserverThread(self, thread):
		self.webserver_thread=thread
	def get_webserverThread(self):
		return self.webserver_thread

	def set_webserver(self, serv):
		self.webserver=serv
	def get_webserver(self):
		return self.webserver

	
	def get_builder(self):
		return self.builder	
	def set_builder(self, gtkbuilder):
		self.builder = gtkbuilder
	
	def get_settings_ip6addr(self): 
		return self.settings_ip6addr

	def load_settings_from_disk(self):
		home = expanduser("~")
		basedir=os.path.join(home, ".cjdradio")
		
		if not os.path.isdir(basedir):
			os.makedirs(basedir)

		if os.path.exists(os.path.join(basedir, "settings_ip6addr.txt")): 
			#settings_ip6addr	
			with open(os.path.join(basedir,'settings_ip6addr.txt'), 'r') as myfile:
				self.settings_ip6addr=myfile.read()
				myfile.close()
				if len(sys.argv)==1:

					self.builder.get_object("settings_ip6addr").set_text(self.settings_ip6addr)
		
		peerList = []
		
		if os.path.exists(os.path.join(basedir, "settings_peersList.txt")): 
			#settings_ip6addr	
			with open(os.path.join(basedir,'settings_peersList.txt'), 'r') as myfile:
				peerList=myfile.read().split("\n")
				myfile.close()

		if len(sys.argv)==1:

			self.builder.get_object("cb_initial_peers").remove_all()
			for peer in peerList:
				if peer!='': 
					self.builder.get_object("cb_initial_peers").append_text(peer)

		
			self.builder.get_object("cb_initial_peers").append_text("fc71:fa3a:414d:fe82:f465:369b:141a:f8c")
			self.builder.get_object("cb_initial_peers").set_active(0)
	def shared_dir_scan(self):
		if self.scan == None:
			self.scan = os.scandir (self.shared_dir)
		return self.scan
class Handler:
	b = None
	g = None


	
	def __init__(self, builder, gateway):
		global g
		global b
		b=builder
		g=gateway
		
	def getBuilder(self):
		return b
		
	def onRadio(self, *args): 
		if g.radio==None or (g.radio!=None and not g.radio.player.is_playing()):
			ir = internetRadio(g, b.get_object("nowplaying"), True)
			g.radio = ir
			ir.play()
		else:
			g.radio.stop()
			self.onRadio(args)
	def onRadioShares(self, *args): 
		if g.radio==None or (g.radio!=None and not g.radio.player.is_playing()):
			ir = internetRadio(g, b.get_object("nowplaying"), False, g.peers[0])
			g.radio = ir
			ir.play()
		else:
			g.radio.stop()
			self.onRadioShares(args)
	def onRadioSingle(self, *args): 
		if g.radio==None or (g.radio!=None and not g.radio.player.is_playing()):
			ir = internetRadio(g, b.get_object("nowplaying"), False, b.get_object("cbsinglestation").get_active_text())
			g.radio = ir
			ir.play()
		else:
			g.radio.stop()
			self.onRadioSingle(args)
			
			
	def onSkip (self, *args):
		print("Skipping")
		if g.radio!=None:
			print("found radio")
			if g.radio.player.is_playing():
				print("radio is playing")
				g.radio.stop()
				g.radio.play()
	def onStop (self, *args):
		print("Stopping")
		if g.radio!=None:
			print("found radio")
			if g.radio.player.is_playing():
				print("radio is playing")
				g.radio.stop()
				b.get_object("nowplaying").set_text("(nothing currently)")

	def onDiscoverPeers(self, *args):
		b.get_object("discover_button").set_label("Discovering peers…")

		self.discoverPeers()


		b.get_object("cbsinglestation").remove_all()
		
		for i in g.peers:
			b.get_object("cbsinglestation").append_text(i)
		
		b.get_object("cbsinglestation").set_active(0)
		b.get_object("discover_button").set_label("Discover new stations peers")
		
		
	def discoverPeers(self):
		g.set_processedPeers([])
		g.set_peers([])
		
		newpeers = []
		
		
		
		g.peers.append(g.get_settings_ip6addr())
		
		try: 
			newpeers = OcsadURLRetriever.retrieveURL("http://["+b.get_object("cb_initial_peers").get_active_text()+"]:55227/listpeers").split("\n")
		except: 
			dialog = Gtk.MessageDialog(
				parent=b.get_object("cjdradio_main_window") ,
				modal=True,
				message_type=Gtk.MessageType.INFO,
				buttons=Gtk.ButtonsType.OK,
				text="Sorry!  "
			)
			dialog.format_secondary_text("This initial peer is currently offline")
			dialog.run()
			dialog.destroy()
		
		newnewpeers = []
		for p in newpeers:
			if not p in g.peers: 
				newnewpeers.append(p)
		
		g.set_peers(g.peers+newnewpeers)
		
		dialog = Gtk.MessageDialog(
				parent=b.get_object("cjdradio_main_window") ,
				modal=True,
				message_type=Gtk.MessageType.INFO,
				buttons=Gtk.ButtonsType.OK,
				text="Discover finished.  "
			)
		dialog.format_secondary_text(str(len(g.get_peers()))+" peers discovered")
		dialog.run()
		dialog.destroy()





	def onDestroy(self, *args):
		g.get_webserver().shutdown()
		g.get_webserverThread().join(1)
		g.bannerdaemon_thread.join(1)
		print("Stopped web server and bannerdaemon")
		Gtk.main_quit()
	def onID(self, *args):
		g.ID = b.get_object("station_id").get_text()
		print (g.ID)
	def onDownload (self, *args): 
		print("Downloading")
		if g.radio!=None:
			print("found radio")
			home = expanduser("~")
			basedir=os.path.join(home, ".cjdradio")
			
			shared_dir=os.path.join(basedir, "Shares")
			
			if not os.path.exists(os.path.join(shared_dir, g.radio.track)):
				os.rename(os.path.join(basedir, "temp.mp3"), os.path.join(shared_dir, g.radio.track))
				dialog = Gtk.MessageDialog(
							parent=b.get_object("cjdradio_main_window") ,
							modal=True,
							message_type=Gtk.MessageType.INFO,
							buttons=Gtk.ButtonsType.OK,
							text="Success.  "
						)
				dialog.format_secondary_text("Downloaded to Shares. MP3s will be reindexed upon next restart. ")
				dialog.run()
				dialog.destroy()
			else: 
				dialog = Gtk.MessageDialog(
							parent=b.get_object("cjdradio_main_window") ,
							modal=True,
							message_type=Gtk.MessageType.INFO,
							buttons=Gtk.ButtonsType.OK,
							text="Failure.  "
						)
				dialog.format_secondary_text("There is already a file of this name in Shares. Maybe you already d/l'ed it? ")
				dialog.run()
				dialog.destroy()

			
	def onAddPeerIP(self, *args): 
		newIP=b.get_object("new_peer_ip").get_text()
		home = expanduser("~")
		basedir=os.path.join(home, ".cjdradio")
		
		if not os.path.isdir(basedir):
			os.makedirs(basedir)

		peersList=''

		if os.path.exists(os.path.join(basedir, "settings_peersList.txt")): 
			with open(os.path.join(basedir,'settings_peersList.txt'), 'r') as myfile:
				peersList=myfile.read()
				myfile.close()
				
		peersList+=newIP+"\n"	
				
		with open(os.path.join(basedir,'settings_peersList.txt'), 'w') as myfile:
			peersList=myfile.write("%s" % peersList)
			myfile.close()
		g.load_settings_from_disk()
		
	def onWebserverRestart(self, *args): 
		newIP=b.get_object("settings_ip6addr").get_text()
		
		home = expanduser("~")
		basedir=os.path.join(home, ".cjdradio")
		
			
		with open(os.path.join(basedir,'settings_ip6addr.txt'), 'w') as myfile:
			myfile.write("%s" % newIP)
			myfile.close()
			
		g.load_settings_from_disk();
		
		dialog = Gtk.MessageDialog(
				parent=b.get_object("cjdradio_main_window") ,
				modal=True,
				message_type=Gtk.MessageType.INFO,
				buttons=Gtk.ButtonsType.OK,
				text="Settings saved! "
			)
		dialog.format_secondary_text("Warning ! A restart of the app is required for your changes to take effect")
		dialog.run()
		dialog.destroy()
		
		


class HTTPServerV6(ThreadingHTTPServer):
	address_family = socket.AF_INET6

class internetRadio(): 

	isMultiPeers = True
	g = None
	ips = []
	ip=''
	track = ''
	player=None;
	
	def __init__ (self, gateway, display_text_setter, isMultiPeers = True, ip = '', ):
		self.ip=ip
		self.g=gateway
		self.isMultiPeers = isMultiPeers
		self.display = display_text_setter
		
	def play(self):
		if (self.isMultiPeers): 
			self.ip = ''
			while self.ip == '':
				self.display.set_text("Selecting a station…")
				peer = ''
				while peer=='' or peer in self.g.bannedStations:
					tmpPeer = random.choice (self.g.peers)
					try: 
						pong = ''
						pong = OcsadURLRetriever.retrieveURL("http://["+tmpPeer+"]:55227/ping")
						if pong!='pong':
							raise ValueError("no replying peer on song request")
						else:
							peer = tmpPeer
							self.ip = tmpPeer
					except: 
						self.g.bannedStations.append(tmpPeer)

		self.display.set_text("Buffering, please wait…")
		
		song = ''

		try: 
			song = OcsadURLRetriever.retrieveURL("http://["+self.ip+"]:55227/random-mp3");
		except: 
			print("Could not contact IP "+self.ip)
		
		
		if song!='':
			self.track=song.split('\n')[0]
			print (self.track)
			#add metadata
			valid=True
			r = requests.get("http://["+self.ip+"]:55227/mp3?"+urllib.parse.quote(self.track, safe=''), timeout = 8, stream = True)
			char_array=b""
			for char in r.iter_content(1024):
				char_array+=char
				if len(char_array)>32000000:
					char_array=b""
					valid=False
					print("MP3 file greater than 32000 kilibytes received, aborting")
					break
			print ("Finished download")
			if valid: 
				home = expanduser("~")
				datadir=os.path.join(home, ".cjdradio")


				with open(os.path.join(datadir,'temp.mp3'), 'wb') as myfile:
					myfile.write(char_array)
					myfile.close()
				self.player = vlc.MediaPlayer(os.path.join(datadir,'temp.mp3'), 'rb')
				em = self.player.event_manager()
				em.event_attach(vlc.EventType.MediaPlayerEndReached, self.onEnded, self.player)

				

				self.display.set_text(song.split("\n")[1]+" - "+song.split("\n")[3]+" ["+song.split("\n")[2]+"]")
				
				myid = "Another random"
				
				try: 
					myid = OcsadURLRetriever.retrieveURL("http://["+self.ip+"]:55227/id")
					
				except: 
					pass
				if len(myid)>60:
					myid = myid[0-60]	
					
				self.g.get_builder().get_object("lasttuned").set_text(self.ip+"\n"+myid)
				
				self.player.play()
		
	def stop(self):
		self.player.stop()
	
	def onEnded(self, event, player): 
		self.play();


class OcsadURLRetriever:
	def retrieveURL(url):
		try: 
			r = requests.get(url, timeout=8, stream=True)
			char_array=b"";
			for char in r.iter_content(1024):
				char_array+=char
				if len(char_array)>32000:
					raise ValueError("Invalid Ocsad URL")
			return char_array.decode("utf-8")
		except(TimeoutError):
			raise ValueError("Invalid Ocsad URL")
		except: 
			raise


class WebRequestHandler(BaseHTTPRequestHandler):
	gateway = None
		
	def do_GET(self):
		

		home = expanduser("~")
		basedir=os.path.join(home, ".cjdradio")

		path = urllib.parse.urlparse(self.path).path
		query = urllib.parse.urlparse(self.path).query
	
		self.send_response(200)
		self.send_header("Server", "Cjdradio")
		if (path!="/mp3"):
			self.send_header("Content-Type", "text/plain")
		else:
			self.send_header("Content-Type", "audio/mpeg")
		
		self.end_headers()
		reply="Cjdradio\n"
		reply=reply+"Version: 0.1\n"
		

		
		if path=="/":
			self.wfile.write("Cjdradio\n0.1\nhttps://github.com/shangril/cjdradio".encode("utf-8"))
		if path=="/ping":
			self.wfile.write("pong".encode("utf-8"))

		if path=="/listpeers":
			try: 
				if not self.client_address[0] in self.gateway.peers and self.client_address!="::":
					self.gateway.get_peers().append(self.client_address[0])
			except: 
				pass
			self.wfile.write("\n".join(self.gateway.get_peers()).encode("utf-8"))
		if path=="/id":
			self.wfile.write(self.gateway.ID.encode("utf-8"))

		if path=="/random-mp3":
			if not self.client_address[0] in self.gateway.peers:
				try:
					if not self.client_address[0] in self.gateway.peers and self.client_address!="::":
						self.gateway.get_peers().append(self.client_address[0])
				except:
					pass
			reply = ''
			completed = False
			while not completed:
					mp3files=[]
					files = os.scandir(g.shared_dir)
					for mp3 in files: 
						if mp3.name.endswith(".mp3"):
							mp3files.append(mp3)
							
					if len(mp3files)>0:		
						mp3=random.choice(mp3files)
						artist=''
						album=''
						title=''
						datadir = os.path.join(basedir, "MetadataShares")
						if os.path.exists(os.path.join(datadir, mp3.name+".artist.txt")) and os.path.exists(os.path.join(datadir, mp3.name+".album.txt")) and os.path.exists(os.path.join(datadir, mp3.name+".title.txt")):
							with open(os.path.join(datadir,mp3.name+'.artist.txt'), 'r') as myfile:
								artist = myfile.read()
								myfile.close()
							with open(os.path.join(datadir,mp3.name+'.album.txt'), 'r') as myfile:
								album = myfile.read()
								myfile.close()
							with open(os.path.join(datadir,mp3.name+'.title.txt'), 'r') as myfile:
								title = myfile.read()
								myfile.close()
							if artist != '' and album != '' and title != '':
								reply = mp3.name+"\n"+artist+"\n"+album+"\n"+title
								completed = True
					else:
						reply+="No mp3 found, sorry!"
						completed = True
			self.wfile.write(reply.encode("utf-8"))
		if path=='/mp3':
			print (query)
			basename = os.path.basename(urllib.parse.unquote(query))
			filepath = os.path.join(g.shared_dir, basename)
			if basename.endswith(".mp3") and os.path.exists(filepath):
				if not os.path.getsize(filepath) > 30000000:
					with open(filepath, 'rb') as myfile:
						tmp = myfile.read()
						myfile.close()
						self.wfile.write(tmp)
				else:
					print ("Trying to serve a mp3 file greater than 30000 kilibytes, aborting")				
if __name__ == "__main__":
	if len(sys.argv)>=2:
		print ("One command line argument passed. Running in daemon mode without user interface")
		
		if len(sys.argv)!=6:
			print ("Fatal error. Mandatory arguments missing.\n Try \"python cjdradio.py nogui <station tracker peer ip address> <path to MP3 shares folder> <station ID> <your tun0 interface ip>\"")
			exit(0)
			
		
	o = Cjdradio()
	home = expanduser("~")
	basedir=os.path.join(home, ".cjdradio")
	
	if not os.path.isdir(basedir):
		os.makedirs(basedir)
	with open(os.path.join(basedir,'justtouched.txt'), 'w') as myfile:
		myfile.close()

	if len(sys.argv)==1:
		UIThread = Thread(target = Gtk.main)
		
		UIThread.start()
		
			
		print ("UI started")
	ip="::"
	
	if o.getGateway().get_settings_ip6addr()!="::": 
		o.getGateway().peers.append(o.getGateway().get_settings_ip6addr())
		ip=o.getGateway().get_settings_ip6addr()
	
	if len(sys.argv)==6: 
		ip = sys.argv[5]
	
	WebRequestHandler.gateway=o.getGateway()
	
	server = HTTPServerV6((ip, 55227), WebRequestHandler)
	o.getGateway().set_webserver(server)
	WebserverThread = Thread(target = server.serve_forever)
	o.getGateway().set_webserverThread(WebserverThread)
	
	if len(sys.argv)==1:

		WebserverThread.daemon = True
	
	WebserverThread.start()
	print ("Webserver started")
	
	o.getGateway().banner_daemon = Thread(target = banner_daemon, args = (o.getGateway(),))
	if len(sys.argv)==1:

		o.getGateway().banner_daemon.daemon = True
	
	#o.getGateway().banner_daemon.start()
	
	#print ("Banner daemon started")

	home = expanduser("~")
	basedir=os.path.join(home, ".cjdradio")

	
	if len(sys.argv)==6:
		g.shared_dir = sys.argv[3]	
		print ("Scanning "+sys.argv[3]+" directory for mp3 tags")
		g.ID=sys.argv[4]
	else: 
		print ('Scanning <$HOME>/.cjdradio directory for mp3 tags');
		g.shared_dir = os.path.join(basedir, "Shares")

	
	if os.path.isdir(basedir):
		shareddir = g.shared_dir
		if os.path.isdir(shareddir):
			datadir = os.path.join(basedir, "MetadataShares")
			if not os.path.isdir(datadir):
				os.makedirs(datadir)
			files = os.scandir(shareddir)
			for mp3 in files: 
				if mp3.name.endswith(".mp3"):
					if not os.path.exists(os.path.join(datadir, mp3.name+".artist.txt")):
						tags = TinyTag.get(os.path.join(shareddir, mp3.name))
					
						with open(os.path.join(datadir,mp3.name+'.artist.txt'), 'w') as myfile:
							myfile.write("%s" % tags.artist)
							myfile.close()
					if not os.path.exists(os.path.join(datadir, mp3.name+".album.txt")):
						tags = TinyTag.get(os.path.join(shareddir, mp3.name))
					
						with open(os.path.join(datadir,mp3.name+'.album.txt'), 'w') as myfile:
							myfile.write("%s" % tags.album)
							myfile.close()
					if not os.path.exists(os.path.join(datadir, mp3.name+".title.txt")):
						tags = TinyTag.get(os.path.join(shareddir, mp3.name))
					
						with open(os.path.join(datadir,mp3.name+'.title.txt'), 'w') as myfile:
							myfile.write("%s" % tags.title)
							myfile.close()

			dldir = os.path.join(basedir, "Downloads")
			if os.path.isdir(dldir):
				datadir = os.path.join(basedir, "MetadataDownloads")
				if not os.path.isdir(datadir):
					os.makedirs(datadir)
				files = os.scandir(dldir)
				for mp3 in files: 
					if mp3.name.endswith(".mp3"):
						if not os.path.exists(os.path.join(datadir, mp3.name+".artist.txt")):
							tags = TinyTag.get(os.path.join(shareddir, mp3.name))
					
							with open(os.path.join(datadir,mp3.name+'.artist.txt'), 'w') as myfile:
								myfile.write("%s" % tags.artist)
								myfile.close()
						if not os.path.exists(os.path.join(datadir, mp3.name+".album.txt")):
							tags = TinyTag.get(os.path.join(shareddir, mp3.name))
					
							with open(os.path.join(datadir,mp3.name+'.album.txt'), 'w') as myfile:
								myfile.write("%s" % tags.album)
								myfile.close()
						if not os.path.exists(os.path.join(datadir, mp3.name+".title.txt")):
							tags = TinyTag.get(os.path.join(shareddir, mp3.name))
					
							with open(os.path.join(datadir,mp3.name+'.title.txt'), 'w') as myfile:
								myfile.write("%s" % tags.title)
								myfile.close()



			print ("Mp3 scanning finished")

						
		else:
			print("No <$HOME>/.cjdradio/Shares directory found. Aborting mp3 scanning")
			os.makedirs(shareddir)

	else:
		print("No <$HOME>/.cjdradio directory found. Aborting mp3 scanning")
		os.makedirs(basedir)
	if len(sys.argv)==6:
		o.getGateway().settings_ip6addr=sys.argv[5]
		print ("contacting initial peer")
		g.set_processedPeers([])
		g.set_peers([])
		
		newpeers = []
		
		g.peers.append(g.get_settings_ip6addr())
		
		try: 
			newpeers = OcsadURLRetriever.retrieveURL("http://["+sys.argv[2]+"]:55227/listpeers").split("\n")
		except: 
			print("This initial peer is currently offline")
		newnewpeers = []
		for p in newpeers:
			if not p in g.peers: 
				newnewpeers.append(p)
		
		g.set_peers(g.peers+newnewpeers)

		