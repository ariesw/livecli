# -*- coding: utf-8 -*-
import re

from livecli import PluginError
from livecli.compat import urljoin
from livecli.exceptions import NoStreamsError
from livecli.plugin import Plugin
from livecli.plugin import PluginOptions
from livecli.plugin.api import http
from livecli.plugin.api import useragents
from livecli.plugin.api import validate
from livecli.stream import HLSStream
from livecli.utils import parse_json

__livecli_docs__ = {
    "domains": [
        "sketch.pixiv.net",
    ],
    "geo_blocked": [],
    "notes": "",
    "live": True,
    "vod": False,
    "last_update": "2018-03-15",
}


class Pixiv(Plugin):
    """Plugin for https://sketch.pixiv.net/lives"""

    _url_re = re.compile(r"https?://sketch\.pixiv\.net/[^/]+(?P<videopage>/lives/\d+)?")

    _videopage_re = re.compile(r"""["']live-button["']><a\shref=["'](?P<path>[^"']+)["']""")
    _data_re = re.compile(r"""<script\sid=["']state["']>[^><{]+(?P<data>{[^><]+})</script>""")
    _post_key_re = re.compile(r"""name=["']post_key["']\svalue=["'](?P<data>[^"']+)["']""")

    _data_schema = validate.Schema(
        validate.all(
            validate.transform(_data_re.search),
            validate.any(
                None,
                validate.all(
                    validate.get("data"),
                    validate.transform(parse_json),
                    validate.get("context"),
                    validate.get("dispatcher"),
                    validate.get("stores"),
                )
            )
        )
    )

    login_url_get = "https://accounts.pixiv.net/login"
    login_url_post = "https://accounts.pixiv.net/api/login"

    options = PluginOptions({
        "username": None,
        "password": None
    })

    @classmethod
    def can_handle_url(cls, url):
        return cls._url_re.match(url) is not None

    def find_videopage(self):
        self.logger.debug("Not a videopage")
        res = http.get(self.url)

        m = self._videopage_re.search(res.text)
        if not m:
            self.logger.debug("No stream path, stream might be offline or invalid url.")
            raise NoStreamsError(self.url)

        path = m.group("path")
        self.logger.debug("Found new path: {0}".format(path))
        return urljoin(self.url, path)

    def _login(self, username, password):
        res = http.get(self.login_url_get)
        m = self._post_key_re.search(res.text)
        if not m:
            raise PluginError("Missing post_key, no login posible.")

        post_key = m.group("data")
        data = {
            "lang": "en",
            "source": "sketch",
            "post_key": post_key,
            "pixiv_id": username,
            "password": password,
        }

        res = http.post(self.login_url_post, data=data)
        res = http.json(res)

        if res["body"].get("success"):
            return True
        else:
            return False

    def _get_streams(self):
        http.headers = {"User-Agent": useragents.FIREFOX}

        login_username = self.get_option("username")
        login_password = self.get_option("password")
        if login_username and login_password:
            self.logger.debug("Attempting login as {0}".format(login_username))
            if self._login(login_username, login_password):
                self.logger.info("Successfully logged in as {0}".format(login_username))
            else:
                self.logger.info("Failed to login as {0}".format(login_username))

        videopage = self._url_re.match(self.url).group("videopage")
        if not videopage:
            self.url = self.find_videopage()

        data = http.get(self.url, schema=self._data_schema)

        if not data.get("LiveStore"):
            self.logger.debug("No video url found, stream might be offline.")
            return

        data = data["LiveStore"]["lives"]

        # get the unknown user-id
        for _key in data.keys():
            video_data = data.get(_key)

        owner = video_data["owner"]
        self.logger.info("Owner ID: {0}".format(owner["user_id"]))
        self.logger.debug("HLS URL: {0}".format(owner["hls_movie"]))
        for n, s in HLSStream.parse_variant_playlist(self.session, owner["hls_movie"]).items():
            yield n, s

        performers = video_data.get("performers")
        if performers:
            for p in performers:
                self.logger.info("CO-HOST ID: {0}".format(p["user_id"]))
                hls_url = p["hls_movie"]
                self.logger.debug("HLS URL: {0}".format(hls_url))
                for n, s in HLSStream.parse_variant_playlist(self.session, hls_url).items():
                    _n = "{0}_{1}".format(n, p["user_id"])
                    yield _n, s


__plugin__ = Pixiv
