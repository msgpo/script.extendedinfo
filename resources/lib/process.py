import os, shutil
import xbmc, xbmcgui, xbmcplugin
from resources.lib import Utils
from resources.lib import local_db
from resources.lib import TheMovieDB
from resources.lib.WindowManager import wm
from resources.lib.VideoPlayer import PLAYER

def start_info_actions(infos, params):
	if 'imdbid' in params and 'imdb_id' not in params:
		params['imdb_id'] = params['imdbid']
	for info in infos:
		data = [], ''
		if info == 'libraryallmovies':
			return wm.open_video_list(media_type='movie', mode='filter', listitems=local_db.get_db_movies('"sort": {"order": "descending", "method": "dateadded"}'))
		elif info == 'libraryalltvshows':
			return wm.open_video_list(media_type='tv', mode='filter', listitems=local_db.get_db_tvshows('"sort": {"order": "descending", "method": "dateadded"}'))
		elif info == 'comingsoonmovies':
			return wm.open_video_list(media_type='movie', mode='filter', listitems=TheMovieDB.get_tmdb_movies('upcoming'))
		elif info == 'popularmovies':
			return wm.open_video_list(media_type='movie', mode='filter', listitems=TheMovieDB.get_tmdb_movies('popular'))
		elif info == 'onairtvshows':
			return wm.open_video_list(media_type='tv', mode='filter', listitems=TheMovieDB.get_tmdb_shows('on_the_air'))
		elif info == 'populartvshows':
			return wm.open_video_list(media_type='tv', mode='filter', listitems=TheMovieDB.get_tmdb_shows('popular'))
		elif info == 'allmovies':
			return wm.open_video_list(media_type='movie',mode='filter')
		elif info == 'alltvshows':
			return wm.open_video_list(media_type='tv',mode='filter')
		elif info == 'studio':
			if 'id' in params and params['id']:
				return wm.open_video_list(media_type='tv', mode='filter', listitems=TheMovieDB.get_company_data(params['id']))
			elif 'studio' in params and params['studio']:
				company_data = TheMovieDB.search_company(params['studio'])
				if company_data:
					return wm.open_video_list(media_type='tv', mode='filter', listitems=TheMovieDB.get_company_data(company_data[0]['id']))
		elif info == 'set':
			if params.get('dbid') and 'show' not in str(params.get('type', '')):
				name = get_set_name_from_db(params['dbid'])
				if name:
					params['setid'] = TheMovieDB.get_set_id(name)
			if params.get('setid'):
				set_data, _ = TheMovieDB.get_set_movies(params['setid'])
				if set_data:
					return wm.open_video_list(media_type='movie', mode='filter', listitems=set_data)
		elif info == 'keywords':
			movie_id = params.get('id', False)
			if not movie_id:
				movie_id = TheMovieDB.get_movie_tmdb_id(imdb_id=params.get('imdb_id', False), dbid=params.get('dbid', False))
			if movie_id:
				return wm.open_video_list(media_type='movie', mode='filter', listitems=TheMovieDB.get_keywords(movie_id))
		elif info == 'directormovies':
			if params.get('director'):
				director_info = TheMovieDB.get_person_info(person_label=params['director'])
				if director_info and director_info.get('id'):
					movies = TheMovieDB.get_person_movies(director_info['id'])
					for item in movies:
						del item['credit_id']
					return wm.open_video_list(media_type='movie', mode='filter', listitems=Utils.merge_dict_lists(movies, key='department'))
		elif info == 'writermovies':
			if params.get('writer') and not params['writer'].split(' / ')[0] == params.get('director', '').split(' / ')[0]:
				writer_info = TheMovieDB.get_person_info(person_label=params['writer'])
				if writer_info and writer_info.get('id'):
					movies = TheMovieDB.get_person_movies(writer_info['id'])
					for item in movies:
						del item['credit_id']                    
					return wm.open_video_list(media_type='movie', mode='filter', listitems=Utils.merge_dict_lists(movies, key='department'))
		elif info == 'playmovie':
			resolve_url(params.get('handle'))
			Utils.get_kodi_json(method='Player.Open', params='{"item": {"movieid": %s}, "options": {"resume": true}}' % params.get('dbid'))
		elif info == 'playepisode':
			resolve_url(params.get('handle'))
			Utils.get_kodi_json(method='Player.Open', params='{"item": {"episodeid": %s}, "options": {"resume": true}}' % params.get('dbid'))
		elif info == 'playmusicvideo':
			resolve_url(params.get('handle'))
			Utils.get_kodi_json(method='Player.Open', params='{"item": {"musicvideoid": %s}}' % params.get('dbid'))
		elif info == 'playalbum':
			resolve_url(params.get('handle'))
			Utils.get_kodi_json(method='Player.Open', params='{"item": {"albumid": %s}}' % params.get('dbid'))
		elif info == 'playsong':
			resolve_url(params.get('handle'))
			Utils.get_kodi_json(method='Player.Open', params='{"item": {"songid": %s}}' % params.get('dbid'))
		elif info == 'openinfodialog':
			resolve_url(params.get('handle'))
			container_id = xbmc.getInfoLabel('Container(%s).ListItem.label' % xbmc.getInfoLabel('System.CurrentControlID'))
			dbid = xbmc.getInfoLabel('%sListItem.DBID' % container_id)
			if not dbid:
				dbid = xbmc.getInfoLabel('%sListItem.Property(dbid)' % container_id)
			db_type = xbmc.getInfoLabel('%sListItem.DBType' % container_id)
			if db_type == 'movie':
				xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedinfo,dbid=%s,id=%s,imdb_id=%s,name=%s)' % (dbid, xbmc.getInfoLabel('ListItem.Property(id)'), xbmc.getInfoLabel('ListItem.IMDBNumber'), xbmc.getInfoLabel('ListItem.Title')))
			elif db_type == 'tvshow':
				xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedtvinfo,dbid=%s,id=%s,name=%s)' % (dbid, xbmc.getInfoLabel('ListItem.Property(id)'), xbmc.getInfoLabel('ListItem.TVShowTitle')))
			elif db_type == 'season':
				xbmc.executebuiltin('RunScript(script.extendedinfo,info=seasoninfo,tvshow=%s,season=%s)' % (xbmc.getInfoLabel('ListItem.TVShowTitle'), xbmc.getInfoLabel('ListItem.Season')))
			elif db_type == 'episode':
				xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedepisodeinfo,tvshow=%s,season=%s,episode=%s)' % (xbmc.getInfoLabel('ListItem.TVShowTitle'), xbmc.getInfoLabel('ListItem.Season'), xbmc.getInfoLabel('ListItem.Episode')))
			elif db_type in ['actor', 'director']:
				xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedactorinfo,name=%s)' % xbmc.getInfoLabel('ListItem.Label'))
			else:
				Utils.notify('Error', 'Could not find valid content type')
		elif info == 'afteradd':
			return Utils.after_add(params.get('type'))
		elif info == 'string':
			resolve_url(params.get('handle'))
			xbmcgui.Window(10000).setProperty('infodialogs.active', 'true')
			dialog = xbmcgui.Dialog()
			if params.get('type', '') == 'movie':
				moviesearch = dialog.input('MovieSearch')
				xbmc.executebuiltin('Skin.SetString(MovieSearch,' + moviesearch + ')')
				xbmc.executebuiltin('Container.Refresh')
			elif params.get('type', '') == 'tv':
				showsearch = dialog.input('ShowSearch')
				xbmc.executebuiltin('Skin.SetString(ShowSearch,' + showsearch + ')')
				xbmc.executebuiltin('Container.Refresh')
			elif params.get('type', '') == 'youtube':
				youtubesearch = dialog.input('YoutubeSearch')
				xbmc.executebuiltin('Skin.SetString(YoutubeSearch,' + youtubesearch + ')')
				xbmc.executebuiltin('Container.Refresh')
			xbmcgui.Window(10000).clearProperty('infodialogs.active')
		elif info == 'moviedbbrowser':
			if xbmcgui.Window(10000).getProperty('infodialogs.active'):
				return None
			xbmcgui.Window(10000).setProperty('infodialogs.active', 'true')
			search_str = params.get('id', '')
			if not search_str and params.get('search'):
				result = xbmcgui.Dialog().input(heading='Enter search string', type=xbmcgui.INPUT_ALPHANUM)
				if result and result > -1:
					search_str = result
				else:
					xbmcgui.Window(10000).clearProperty('infodialogs.active')
					return None
			wm.open_video_list(search_str=search_str, mode='search')
			xbmcgui.Window(10000).clearProperty('infodialogs.active')
		elif info == 'extendedinfo':
			resolve_url(params.get('handle'))
			xbmcgui.Window(10000).setProperty('infodialogs.active', 'true')
			wm.open_movie_info(movie_id=params.get('id', ''), dbid=params.get('dbid', None), imdb_id=params.get('imdb_id', ''), name=params.get('name', ''))
			xbmcgui.Window(10000).clearProperty('infodialogs.active')
		elif info == 'extendedactorinfo':
			resolve_url(params.get('handle'))
			xbmcgui.Window(10000).setProperty('infodialogs.active', 'true')
			wm.open_actor_info(actor_id=params.get('id', ''), name=params.get('name', ''))
			xbmcgui.Window(10000).clearProperty('infodialogs.active')
		elif info == 'extendedtvinfo':
			resolve_url(params.get('handle'))
			xbmcgui.Window(10000).setProperty('infodialogs.active', 'true')
			wm.open_tvshow_info(tvshow_id=params.get('id', ''), tvdb_id=params.get('tvdb_id', ''), dbid=params.get('dbid', None), imdb_id=params.get('imdb_id', ''), name=params.get('name', ''))
			xbmcgui.Window(10000).clearProperty('infodialogs.active')
		elif info == 'seasoninfo':
			resolve_url(params.get('handle'))
			xbmcgui.Window(10000).setProperty('infodialogs.active', 'true')
			wm.open_season_info(tvshow_id=params.get('id'), tvshow=params.get('tvshow'), dbid=params.get('dbid'), season=params.get('season'))
			xbmcgui.Window(10000).clearProperty('infodialogs.active')
		elif info == 'extendedepisodeinfo':
			resolve_url(params.get('handle'))
			xbmcgui.Window(10000).setProperty('infodialogs.active', 'true')
			wm.open_episode_info(tvshow=params.get('tvshow'), tvshow_id=params.get('tvshow_id'), dbid=params.get('dbid'), season=params.get('season'), episode=params.get('episode'))
			xbmcgui.Window(10000).clearProperty('infodialogs.active')
		elif info == 'albuminfo':
			resolve_url(params.get('handle'))
			if params.get('id', ''):
				album_details = get_album_details(params.get('id', ''))
				Utils.pass_dict_to_skin(album_details, params.get('prefix', ''))
		elif info == 'artistdetails':
			resolve_url(params.get('handle'))
			artist_details = get_artist_details(params['artistname'])
			Utils.pass_dict_to_skin(artist_details, params.get('prefix', ''))
		elif info == 'setfocus':
			resolve_url(params.get('handle'))
			xbmc.executebuiltin('SetFocus(22222)')
		elif info == 'slideshow':
			resolve_url(params.get('handle'))
			window_id = xbmcgui.getCurrentwindow_id()
			window = xbmcgui.Window(window_id)
			itemlist = window.getFocus()
			num_items = itemlist.getSelectedPosition()
			for i in range(0, num_items):
				Utils.notify(item.getProperty('Image'))
		elif info == 'action':
			resolve_url(params.get('handle'))
			for builtin in params.get('id', '').split('$$'):
				xbmc.executebuiltin(builtin)
			return None
		elif info == 'youtubevideo':
			resolve_url(params.get('handle'))
			xbmc.executebuiltin('Dialog.Close(all,true)')
			PLAYER.play_youtube_video(params.get('id', ''))
		elif info == 'playtrailer':
			resolve_url(params.get('handle'))
			if params.get('id', ''):
				movie_id = params.get('id', '')
			elif int(params.get('dbid', -1)) > 0:
				movie_id = get_imdb_id_from_db(media_type='movie', dbid=params['dbid'])
			elif params.get('imdb_id', ''):
				movie_id = TheMovieDB.get_movie_tmdb_id(params.get('imdb_id', ''))
			else:
				movie_id = ''
			if movie_id:
				trailer = TheMovieDB.get_trailer(movie_id)
				if trailer:
					PLAYER.play_youtube_video(trailer)
		elif info == 'playtvtrailer':
			resolve_url(params.get('handle'))
			if params.get('id', ''):
				tvshow_id = params.get('id', '')
			elif int(params.get('dbid', -1)) > 0:
				tvshow_id = get_imdb_id_from_db(media_type='show', dbid=params['dbid'])
			elif params.get('tvdb_id', ''):
				tvshow_id = TheMovieDB.get_movie_tmdb_id(params.get('tvdb_id', ''))
			else:
				tvshow_id = ''
			if tvshow_id:
				trailer = TheMovieDB.get_tvtrailer(tvshow_id)
				if trailer:
					PLAYER.play_youtube_video(trailer)
		elif info == 'deletecache':
			resolve_url(params.get('handle'))
			xbmcgui.Window(10000).clearProperties()
			ADDON_DATA_PATH = xbmc.translatePath('special://profile/addon_data/script.extendedinfo').decode('utf-8')
			for rel_path in os.listdir(ADDON_DATA_PATH):
				path = os.path.join(ADDON_DATA_PATH, rel_path)
				try:
					if os.path.isdir(path):
						shutil.rmtree(path)
				except Exception as e:
					Utils.log(e)
			Utils.notify('Cache deleted')
		listitems, prefix = data
		if params.get('handle'):
			xbmcplugin.addSortMethod(params.get('handle'), xbmcplugin.SORT_METHOD_TITLE)
			xbmcplugin.addSortMethod(params.get('handle'), xbmcplugin.SORT_METHOD_VIDEO_YEAR)
			xbmcplugin.addSortMethod(params.get('handle'), xbmcplugin.SORT_METHOD_DURATION)
			if info.endswith('shows'):
				xbmcplugin.setContent(params.get('handle'), 'tvshows')
			else:
				xbmcplugin.setContent(params.get('handle'), 'movies')
		Utils.pass_list_to_skin(name=prefix, data=listitems, prefix=params.get('prefix', ''), handle=params.get('handle', ''), limit=params.get('limit', 20))

def resolve_url(handle):
	if handle:
		xbmcplugin.setResolvedUrl(int(handle), False, xbmcgui.ListItem())