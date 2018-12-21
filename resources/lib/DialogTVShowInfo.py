import os, shutil
import xbmc, xbmcgui, xbmcaddon
from resources.lib import Utils
from resources.lib import ImageTools
from resources.lib import TheMovieDB
from resources.lib.WindowManager import wm
from resources.lib.VideoPlayer import PLAYER
from resources.lib.OnClickHandler import OnClickHandler
from resources.lib.DialogBaseInfo import DialogBaseInfo

ch = OnClickHandler()

def get_tvshow_window(window_type):

	class DialogTVShowInfo(DialogBaseInfo, window_type):

		def __init__(self, *args, **kwargs):
			super(DialogTVShowInfo, self).__init__(*args, **kwargs)
			self.type = 'TVShow'
			data = TheMovieDB.extended_tvshow_info(tvshow_id=kwargs.get('tmdb_id', False), dbid=self.dbid)
			if not data:
				return None
			self.info, self.data = data
			if 'dbid' not in self.info:
				self.info['poster'] = Utils.get_file(self.info.get('poster', ''))
			self.info['ImageFilter'], self.info['ImageColor'] = ImageTools.filter_image(input_img=self.info.get('poster', ''), radius=25)
			self.listitems = [
				(250, self.data['seasons']),
				(150, self.data['similar']),
				(1150, self.data['videos']),
				(1000, self.data['actors']),
				(750, self.data['crew']),
				(550, self.data['studios']),
				(1450, self.data['networks']),
				(650, TheMovieDB.merge_with_cert_desc(self.data['certifications'], 'tv')),
				(850, self.data['genres']),
				(1250, self.data['images']),
				(1350, self.data['backdrops'])
				]

		def onInit(self):
			self.get_youtube_vids('%s tv' % self.info['title'])
			super(DialogTVShowInfo, self).onInit()
			Utils.pass_dict_to_skin(data=self.info, prefix='movie.', window_id=self.window_id)
			self.fill_lists()

		def onClick(self, control_id):
			super(DialogTVShowInfo, self).onClick(control_id)
			ch.serve(control_id, self)

		@ch.click(120)
		def browse_tvshow(self):
			url = 'plugin://plugin.video.openmeta/tv/tvdb/%s/' % self.info['tvdb_id']
			self.close()
			xbmc.executebuiltin('ActivateWindow(videos,%s,return)' % url)

		@ch.action('contextmenu', 150)
		def right_click_similar(self):
			item_id = self.listitem.getProperty('id')
			listitems = ['Play']
			if self.listitem.getProperty('dbid'):
				listitems += ['Remove from library']
			else:
				listitems += ['Add to library']
			selection = xbmcgui.Dialog().select(heading='Choose option', list=listitems)

		@ch.click(750)
		@ch.click(1000)
		def credit_dialog(self):
			selection = xbmcgui.Dialog().select(heading='Choose option', list=['Show actor information', 'Show actor TV show appearances'])
			if selection == 0:
				wm.open_actor_info(prev_window=self, actor_id=self.listitem.getProperty('id'))
			if selection == 1:
				self.open_credit_dialog(self.listitem.getProperty('credit_id'))

		@ch.click(150)
		def open_tvshow_dialog(self):
			wm.open_tvshow_info(prev_window=self, tvshow_id=self.listitem.getProperty('id'), dbid=self.listitem.getProperty('dbid'))

		@ch.click(250)
		def open_season_dialog(self):
			wm.open_season_info(prev_window=self, tvshow_id=self.info['id'], season=self.listitem.getProperty('season'), tvshow=self.info['title'])

		@ch.click(550)
		def open_company_info(self):
			filters = [
				{
					'id': self.listitem.getProperty('id'),
					'type': 'with_companies',
					'typelabel': 'Studios',
					'label': self.listitem.getLabel().decode('utf-8')
				}]
			wm.open_video_list(prev_window=self, filters=filters)

		@ch.click(850)
		def open_genre_info(self):
			filters = [
				{
					'id': self.listitem.getProperty('id'),
					'type': 'with_genres',
					'typelabel': 'Genres',
					'label': self.listitem.getLabel().decode('utf-8')
				}]
			wm.open_video_list(prev_window=self, filters=filters, media_type='tv')

		@ch.click(1450)
		def open_network_info(self):
			filters = [
				{
					'id': self.listitem.getProperty('id'),
					'type': 'with_networks',
					'typelabel': 'Networks',
					'label': self.listitem.getLabel().decode('utf-8')
				}]
			wm.open_video_list(prev_window=self, filters=filters, media_type='tv')

		@ch.click(445)
		def show_manage_dialog(self):
			manage_list = []
			manage_list.append(["OpenInfo's settings", 'Addon.OpenSettings("script.extendedinfo")'])
			manage_list.append(["OpenMeta's settings", 'Addon.OpenSettings("plugin.video.openmeta")'])
			manage_list.append(["YouTube's settings", 'Addon.OpenSettings("plugin.video.youtube")'])
			selection = xbmcgui.Dialog().select(heading='Settings', list=[i[0] for i in manage_list])
			if selection > -1:
				for item in manage_list[selection][1].split('||'):
					xbmc.executebuiltin(item)

		@ch.click(6002)
		def open_list(self):
			index = xbmcgui.Dialog().select(heading='Choose list', list=['Starred TV shows', 'Rated TV shows'])

		@ch.click(6006)
		def open_rated_items(self):
			wm.open_video_list(prev_window=self, mode='rating', media_type='tv')

		@ch.click(9)
		def play_tvshow_no_resume(self):
			url = 'plugin://plugin.video.openmeta/tv/play/%s/1/1' % self.info['tvdb_id']
			PLAYER.OpenInfoplay(url, listitem=None, window=self, dbid=0)

		@ch.click(20)
		def add_tvshow_to_library(self):
			xbmc.executebuiltin('RunPlugin(plugin://plugin.video.openmeta/tv/add_to_library/%s)' % self.info.get('tvdb_id', ''))
			Utils.notify(header='Added "%s" to library' % self.info.get('TVShowTitle', ''), message='Starting library scan now', icon=self.info['poster'], time=5000, sound=False)
			Utils.after_add(type='tv')
			Utils.notify(header='To refresh all content', message='Exit OpenInfo & re-enter', icon=self.info['poster'], time=5000, sound=False)

		@ch.click(21)
		def remove_tvshow_from_library(self):
			TVLibrary = xbmcaddon.Addon('plugin.video.openmeta').getSetting('tv_library_folder')
			tvdb_id = self.info['tvdb_id']
			if os.path.exists(xbmc.translatePath('%s%s/' % (TVLibrary, tvdb_id))):
				Utils.get_kodi_json(method='VideoLibrary.RemoveTVShow', params='{"tvshowid": %s}' % int(self.info['dbid']))
				shutil.rmtree(xbmc.translatePath('%s%s/' % (TVLibrary, tvdb_id)))
				Utils.notify(header='Removed "%s" from library' % self.info.get('TVShowTitle', ''), message='Exit & re-enter to refresh', icon=self.info['poster'], time=5000, sound=False)
				Utils.after_add(type='tv')
			else:
				Utils.notify(header='To refresh all content', message='Exit OpenInfo & re-enter', icon=self.info['poster'], time=5000, sound=False)

		@ch.click(132)
		def open_text(self):
			wm.open_textviewer(header='Overview', text=self.info['Plot'], color=self.info['ImageColor'])

		@ch.click(350)
		@ch.click(1150)
		def play_youtube_video(self):
			PLAYER.playtube(self.listitem.getProperty('youtube_id'), listitem=self.listitem, window=self)

	return DialogTVShowInfo